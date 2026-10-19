"""CNN + PPO trainieren: Vortraining durch Nachahmung, dann PPO.

    # 1) Lehrer-Spiele aufzeichnen (DQN-Ensemble mit Regel-Schaltern)
    python -m scripts.ppo_train collect --run R --games 400 --set early_inference=true ...
    # 2) Behaviour Cloning: CNN lernt die Zuege des Lehrers (+ Wertfunktion)
    python -m scripts.ppo_train bc --run R --epochs 4
    # 3) PPO gegen Gegner-Mix, Start bei den BC-Gewichten
    python -m scripts.ppo_train ppo --run R --iters 300

Alles landet in experiments/ppo/<run>/ (neue Ordner, die Abgabe-Gewichte unter
agents/sherlock/weights/ werden nie geschrieben). Trainings-Seeds 100 000+
(getrennt von Validierung 500 000+ und Test 900 000+).
"""
from __future__ import annotations

import argparse
import csv
import json
import multiprocessing as mp
import random
import time
from pathlib import Path

import numpy as np

from scripts.experiment import limit_threads
ROOT = Path(__file__).resolve().parent.parent

PPO_DIR = ROOT / "experiments" / "ppo"
TEACHER = ROOT / "experiments" / "ensembles" / "old3_sym3.pth"
TRAIN_SEED_BASE = 100_000
GAMMA, LAM = 0.99, 0.95


def _check_run_dir(run: str) -> Path:
    d = (PPO_DIR / run).resolve()
    weights = (ROOT / "agents" / "sherlock" / "weights").resolve()
    if weights == d or weights in d.parents:
        raise SystemExit("Ausgabe darf nicht im Abgabe-Gewichteordner liegen")
    d.mkdir(parents=True, exist_ok=True)
    return d


# ------------------------------------------------------------------ Rollouts
def _make_agent(kind: str, weights: str, overrides: list[str], seed: int):
    from scripts.par_eval import build_cfg

    if kind == "teacher":
        from agents.sherlock.main import Agent_x
        a = Agent_x("player_0", agent_path=weights,
                    cfg=build_cfg(weights, list(overrides) + ["buffer_capacity=1"]),
                    train=False, seed=seed)
        a.set_to_eval_mode()
        a.autosave_on_terminate = False
        return a
    from agents.sherlock.ppo_agent import PPOAgent
    a = PPOAgent("player_0", agent_path=weights, train=True, seed=seed)
    return a


def play_recorded(env, agent, opp, seed: int, side: str, teacher: bool):
    from agents.sherlock.ppo_agent import Recorder

    rec = Recorder()
    if not teacher:
        agent.recorder = rec
    opp_side = "player_1" if side == "player_0" else "player_0"
    agent.new_game(side)
    if hasattr(opp, "new_game"):
        opp.new_game(opp_side)
    random.seed(seed)
    np.random.seed(seed % (2**32))
    obs, info = env.reset(seed=seed)
    for a in (agent, opp):
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(info["params"])
    step, done = 0, False
    while not done:
        a_us = agent.act(step=step, obs=obs[side])
        if teacher and agent._prev_ctx is not None and agent._prev_actions:
            ids = list(agent._prev_actions)
            rec.on_act(agent._prev_ctx, ids, [agent._prev_feats[u] for u in ids],
                       [agent._prev_masks[u] for u in ids], [agent._prev_actions[u] for u in ids])
        a_op = opp.act(step=step, obs=obs[opp_side])
        obs, _r, term, trunc, info = env.step({side: a_us, opp_side: a_op})
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        rec.on_next(agent, obs[side], done)
        step += 1
    team = 0 if side == "player_0" else 1
    wins = np.asarray(obs[side]["team_wins"])
    agent.recorder = None
    result = 1.0 if wins[team] > wins[1 - team] else (0.0 if wins[team] < wins[1 - team] else 0.5)
    # Lehrer: keine Werte -> Monte-Carlo-Rueckgabe (lam = 1) als Ziel fuer den Critic
    return rec.finish(GAMMA, 1.0 if teacher else LAM), result


def _rollout_worker(job: tuple):
    kind, weights, overrides, games, wid = job
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from scripts.common import make_opponent

    env = LuxAIS3GymEnv(numpy_output=True)
    agent = _make_agent(kind, weights, overrides, seed=wid)
    out, results = [], []
    for seed, side, opp_kind, opp_path in games:
        opp_side = "player_1" if side == "player_0" else "player_0"
        if opp_kind == "teacher":
            opp = _make_agent("teacher", str(TEACHER), opp_path or [], seed=seed)
        else:
            opp = make_opponent(opp_kind, opp_side)
        data, res = play_recorded(env, agent, opp, seed, side, teacher=(kind == "teacher"))
        out.append(data)
        results.append((opp_kind, res))
    env.close()
    return out, results


def merge(datas: list[dict]) -> dict:
    keys = [k for k in datas[0] if k != "planes"]
    off, steps = 0, []
    for d in datas:
        steps.append(d["step"] + off)
        off += len(d["planes"])
    m = {k: np.concatenate([d[k] for d in datas]) for k in keys if k != "step"}
    m["step"] = np.concatenate(steps)
    m["planes"] = np.concatenate([d["planes"] for d in datas])
    return m


def run_rollouts(pool, kind, weights, overrides, game_list, workers):
    chunks = [game_list[i::workers] for i in range(workers)]
    jobs = [(kind, weights, overrides, c, i) for i, c in enumerate(chunks) if c]
    res = pool.map(_rollout_worker, jobs)
    datas = [d for r in res for d in r[0]]
    results = [x for r in res for x in r[1]]
    return datas, results


def opponent_mix(rng, n: int, start_seed: int, mix: dict[str, float], teacher_overrides):
    names = list(mix)
    p = np.array([mix[k] for k in names], dtype=float)
    p /= p.sum()
    games = []
    for i in range(n):
        o = names[rng.choice(len(names), p=p)]
        games.append((start_seed + i // 2, ("player_0", "player_1")[i % 2], o,
                      teacher_overrides if o == "teacher" else None))
    return games


# ------------------------------------------------------------------ Lernen
def device():
    import torch
    return torch.device("mps" if torch.backends.mps.is_available() else "cpu")


def to_torch(data: dict, dev):
    import torch
    t = {k: torch.as_tensor(v) for k, v in data.items() if k != "planes"}
    t = {k: v.to(dev) for k, v in t.items()}
    t["planes"] = torch.as_tensor(data["planes"]).to(dev)
    return t


def forward_mb(net, t, idx):
    import torch
    st = t["step"][idx]
    uniq, inv = torch.unique(st, return_inverse=True)
    planes = t["planes"][uniq].float() / 127.0
    logits, v = net(planes, inv, t["pos"][idx], t["feats"][idx])
    logits = logits.masked_fill(~t["mask"][idx], -1e9)
    return logits, v


def bc_train(net, data: dict, epochs: int, lr: float, mb: int, log) -> None:
    import torch
    import torch.nn.functional as F
    dev = device()
    net.to(dev).train()
    t = to_torch(data, dev)
    n = len(data["act"])
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    for ep in range(epochs):
        perm = torch.randperm(n, device=dev)
        tot, acc, cnt = 0.0, 0.0, 0
        for s in range(0, n, mb):
            idx = perm[s:s + mb]
            logits, v = forward_mb(net, t, idx)
            ce = F.cross_entropy(logits, t["act"][idx])
            vl = F.smooth_l1_loss(v, t["ret"][idx])
            loss = ce + 0.5 * vl
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            opt.step()
            tot += float(ce) * len(idx)
            acc += float((logits.argmax(1) == t["act"][idx]).float().sum())
            cnt += len(idx)
        log(f"BC Epoche {ep + 1}/{epochs}: CE {tot / cnt:.4f}, Trefferquote {acc / cnt:.3f}")
    net.to("cpu").eval()


def ppo_update(net, opt, data: dict, epochs: int, mb: int, clip: float, ent: float,
               vf: float, policy_on: bool = True) -> dict:
    import torch
    dev = device()
    net.to(dev).train()
    t = to_torch(data, dev)
    adv = t["adv"]
    t["adv"] = (adv - adv.mean()) / (adv.std() + 1e-8)
    n = len(data["act"])
    stats = {"pi": 0.0, "v": 0.0, "ent": 0.0, "kl": 0.0, "clipfrac": 0.0}
    cnt = 0
    for _ in range(epochs):
        perm = torch.randperm(n, device=dev)
        for s in range(0, n, mb):
            idx = perm[s:s + mb]
            logits, v = forward_mb(net, t, idx)
            logp_all = torch.log_softmax(logits, dim=1)
            logp = logp_all.gather(1, t["act"][idx][:, None]).squeeze(1)
            ratio = torch.exp(logp - t["logp"][idx])
            a = t["adv"][idx]
            pl = -torch.min(ratio * a, torch.clamp(ratio, 1 - clip, 1 + clip) * a).mean()
            vl = torch.nn.functional.smooth_l1_loss(v, t["ret"][idx])
            probs = logp_all.exp()
            entropy = -(probs * logp_all.masked_fill(~t["mask"][idx], 0.0)).sum(1).mean()
            loss = (pl - ent * entropy if policy_on else 0.0) + vf * vl
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5)
            opt.step()
            with torch.no_grad():
                stats["pi"] += float(pl)
                stats["v"] += float(vl)
                stats["ent"] += float(entropy)
                stats["kl"] += float((t["logp"][idx] - logp).mean())
                stats["clipfrac"] += float(((ratio - 1).abs() > clip).float().mean())
            cnt += 1
    net.to("cpu").eval()
    return {k: v / max(1, cnt) for k, v in stats.items()}


# ------------------------------------------------------------------ Befehle
def cmd_collect(args, log) -> None:
    run = _check_run_dir(args.run)
    rng = np.random.default_rng(args.seed)
    mix = {"solution92": 0.6, "default": 0.25, "teacher": 0.15}
    games = opponent_mix(rng, args.games, TRAIN_SEED_BASE + args.seed * 10_000, mix, args.set)
    ctx = mp.get_context("spawn")
    t0 = time.time()
    with ctx.Pool(args.workers) as pool:
        datas, results = run_rollouts(pool, "teacher", str(TEACHER), args.set, games, args.workers)
    data = merge(datas)
    np.savez(run / "bc_data.npz", **data)
    (run / "teacher.json").write_text(json.dumps({"weights": str(TEACHER), "set": args.set,
                                                  "games": len(games)}, indent=2))
    wr = {o: np.mean([r for k, r in results if k == o]) for o in mix}
    log(f"Lehrer: {len(games)} Spiele, {len(data['act'])} Unit-Schritte, WR {wr}, {time.time() - t0:.0f}s")


def cmd_bc(args, log) -> None:
    from agents.sherlock.cnn_model import PolicyNet
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.features import FEATURE_DIM
    from agents.sherlock.ppo_agent import save_policy
    from scripts.par_eval import build_cfg

    import torch
    run = _check_run_dir(args.run)
    torch.manual_seed(args.seed)
    data = dict(np.load(run / "bc_data.npz"))
    teacher = json.loads((run / "teacher.json").read_text())
    cfg = build_cfg(str(TEACHER), teacher["set"] + ["reward_fix=true"])
    for k in ("scripted_explore", "pt_walk", "pt_hold", "smart_sap"):
        setattr(cfg, k, False)  # Policy lernt diese Regeln selbst (Daten enthalten sie)
    net = PolicyNet(FEATURE_DIM, ch=args.ch, blocks=args.blocks)
    bc_train(net, data, args.epochs, args.lr, args.mb, log)
    save_policy(str(run / "bc.pth"), net, cfg, {"stage": "bc"})
    log(f"gespeichert: {run / 'bc.pth'}")


def cmd_ppo(args, log) -> None:
    import torch
    from agents.sherlock.ppo_agent import PPOAgent, save_policy

    run = _check_run_dir(args.run)
    start = run / (args.start or "bc.pth")
    base = PPOAgent("player_0", agent_path=str(start), train=False)
    net, cfg = base.net, base.cfg
    opt = torch.optim.Adam(net.parameters(), lr=args.lr)
    rng = np.random.default_rng(args.seed + 7)
    mix = {"solution92": args.sol92, "default": args.default, "teacher": args.teacher}
    teacher_set = json.loads((run / "teacher.json").read_text())["set"]
    cur = run / "ppo_current.pth"
    save_policy(str(cur), net, cfg, {"stage": "ppo", "iter": 0})
    logf = open(run / "ppo.csv", "a", newline="")
    w = csv.writer(logf)
    if logf.tell() == 0:
        w.writerow(["iter", "games", "wr_sol92", "wr_default", "wr_teacher", "unit_steps",
                    "pi", "v", "ent", "kl", "clipfrac", "secs"])
    ctx = mp.get_context("spawn")
    seed0 = TRAIN_SEED_BASE + 50_000 + args.seed * 20_000
    with ctx.Pool(args.workers) as pool:
        for it in range(1, args.iters + 1):
            t0 = time.time()
            games = opponent_mix(rng, args.games, seed0 + it * args.games, mix, teacher_set)
            datas, results = run_rollouts(pool, "ppo", str(cur), [], games, args.workers)
            data = merge(datas)
            st = ppo_update(net, opt, data, args.epochs, args.mb, args.clip, args.ent, args.vf,
                            policy_on=it > args.vf_warmup)
            save_policy(str(cur), net, cfg, {"stage": "ppo", "iter": it})
            if it % args.save_every == 0:
                save_policy(str(run / f"ppo_{it:04d}.pth"), net, cfg, {"stage": "ppo", "iter": it})
            wr = {o: (np.mean([r for k, r in results if k == o]) if any(k == o for k, _ in results)
                      else float("nan")) for o in mix}
            w.writerow([it, len(games), wr["solution92"], wr["default"], wr["teacher"],
                        len(data["act"]), st["pi"], st["v"], st["ent"], st["kl"], st["clipfrac"],
                        round(time.time() - t0, 1)])
            logf.flush()
            log(f"PPO {it}: WR sol92 {wr['solution92']:.2f} default {wr['default']:.2f} "
                f"teacher {wr['teacher']:.2f} | ent {st['ent']:.3f} kl {st['kl']:.4f} "
                f"clip {st['clipfrac']:.3f} | {time.time() - t0:.0f}s")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["collect", "bc", "ppo"])
    ap.add_argument("--run", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="Regel-Schalter fuer den Lehrer (collect)")
    ap.add_argument("--games", type=int, default=400)
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--mb", type=int, default=2048)
    ap.add_argument("--ch", type=int, default=32)
    ap.add_argument("--blocks", type=int, default=3)
    ap.add_argument("--iters", type=int, default=100)
    ap.add_argument("--clip", type=float, default=0.15)
    ap.add_argument("--ent", type=float, default=0.003)
    ap.add_argument("--vf", type=float, default=0.5)
    ap.add_argument("--sol92", type=float, default=0.7)
    ap.add_argument("--default", type=float, default=0.15)
    ap.add_argument("--teacher", type=float, default=0.15)
    ap.add_argument("--save-every", type=int, default=10)
    ap.add_argument("--vf-warmup", type=int, default=3, help="erste Iterationen nur Critic")
    ap.add_argument("--start", default=None, help="Startgewichte im Run-Ordner (Default bc.pth)")
    args = ap.parse_args()
    run = _check_run_dir(args.run)
    logf = open(run / "log.txt", "a", encoding="utf-8")

    def log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    log(f"{args.cmd}: {vars(args)}")
    {"collect": cmd_collect, "bc": cmd_bc, "ppo": cmd_ppo}[args.cmd](args, log)


if __name__ == "__main__":
    main()
