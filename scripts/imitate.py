"""Imitation Learning (15.11.2026): Sherlock lernt die Zuege des Kaggle-Platz-3-Agenten.

    # 1) Lehrer-Daten: der Lehrer spielt, ein Schatten-Sherlock baut fuer seine Seite die Netzeingaben
    python -m scripts.imitate collect --out experiments/imitation/k3_v1 --games 400 --workers 12
    # 2) Nachahmen: PolicyNet lernt die Lehrer-Aktion je Unit (maskierte Kreuzentropie)
    python -m scripts.imitate train --data experiments/imitation/k3_v1 --out experiments/imitation/k3_v1/student.pth
    # 3) Spielen/Messen: par_eval laedt Checkpoints mit kind="imitation" als ImitationAgent

Der Lehrer (scripts/kaggle3_opponent.py) ist nur Lehrer und Testgegner, nie Teil der Abgabe. Trainings-Seeds
ab 7200000 (getrennt von Dev A/B 7150000/7151000 und der Bestaetigung 7158000). Ausgaben nur unter
experiments/imitation/ (die Abgabe-Gewichte werden nie geschrieben).
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import random
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
V14 = ROOT / "agents" / "sherlock" / "weights" / "agent_p0.pth"
OUT_BASE = ROOT / "experiments" / "imitation"
PLANE_SCALE = 127.0
TRAIN_SEED0 = 7_200_000


def _check_out(path: Path) -> Path:
    path = path.resolve()
    weights = (ROOT / "agents" / "sherlock" / "weights").resolve()
    if weights == path or weights in path.parents:
        raise SystemExit("Ausgabe darf nicht im Abgabe-Gewichteordner liegen")
    return path


def v14_cfg():
    from agents.sherlock.main import Agent_x
    return Agent_x._cfg_from_checkpoint(str(V14))


def make_shadow(side: str, cfg):
    """Sherlock ohne eigenes Netz, nur fuer Gedaechtnis und Netzeingaben auf der Seite des Lehrers."""
    from agents.sherlock.imitation_agent import ImitationAgent
    shadow = ImitationAgent(side, agent_path=None, cfg=cfg, train=False, seed=0)
    shadow.set_to_eval_mode()
    return shadow


def make_player(kind: str, side: str):
    from scripts.common import make_opponent
    if kind == "v14":
        from agents.sherlock.main import Agent_x
        from scripts.par_eval import build_cfg
        p = Agent_x(side, agent_path=str(V14), cfg=build_cfg(str(V14), []), train=False, seed=0)
        p.set_to_eval_mode()
        p.autosave_on_terminate = False
        return p
    return make_opponent(kind, side)


class SideRecord:
    """Lehrer-Daten einer Seite eines Spiels."""

    def __init__(self) -> None:
        self.planes, self.step, self.pos, self.uid = [], [], [], []
        self.feats, self.mask, self.act, self.sdx, self.sdy, self.mstep = [], [], [], [], [], []

    def add(self, fz, teacher_actions, mirrored: bool) -> None:
        from agents.sherlock.imitation_agent import canonical_action
        ctx, ids, feats, masks, _, planes, pos = fz
        si = len(self.planes)
        self.planes.append(np.round(planes * PLANE_SCALE).astype(np.int8))
        for k, u in enumerate(ids):
            a, dx, dy = canonical_action(teacher_actions[u], mirrored)
            self.step.append(si)
            self.pos.append(pos[k])
            self.uid.append(u)
            self.feats.append(feats[k])
            self.mask.append(masks[k])
            self.act.append(a)
            self.sdx.append(dx)
            self.sdy.append(dy)
            self.mstep.append(int(ctx["match_step"]))

    def save(self, path: Path, meta: dict) -> int:
        if not self.act:
            return 0
        np.savez_compressed(
            path, planes=np.stack(self.planes), step=np.array(self.step, np.int32),
            pos=np.array(self.pos, np.int8), uid=np.array(self.uid, np.int8),
            feats=np.array(self.feats, np.float16), mask=np.array(self.mask, bool),
            act=np.array(self.act, np.int8), sdx=np.array(self.sdx, np.int8), sdy=np.array(self.sdy, np.int8),
            mstep=np.array(self.mstep, np.int16), meta=json.dumps(meta))
        return len(self.act)


def _collect_worker(job) -> list[dict]:
    games, out_dir = job
    from scripts.experiment import limit_threads
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.kaggle3_opponent import Kaggle3Opponent

    env = LuxAIS3GymEnv(numpy_output=True)
    cfg = v14_cfg()
    done_meta = []
    for seed, tside, opp_kind in games:
        oside = "player_1" if tside == "player_0" else "player_0"
        players = {tside: Kaggle3Opponent(tside), oside: make_player(opp_kind, oside)}
        teacher_sides = [tside] + ([oside] if opp_kind == "kaggle3" else [])
        shadows = {s: make_shadow(s, cfg) for s in teacher_sides}
        for s_, p in list(players.items()) + list(shadows.items()):
            if hasattr(p, "new_game"):
                p.new_game(s_)
        obs, info = env.reset(seed=seed)
        for p in list(players.values()) + list(shadows.values()):
            if hasattr(p, "set_env_cfg"):
                p.set_env_cfg(info["params"])
        recs = {s: SideRecord() for s in teacher_sides}
        step, done = 0, False
        while not done:
            fzs = {s: featurize_safe(shadows[s], obs[s]) for s in teacher_sides}
            acts = {s: np.asarray(players[s].act(step, obs[s])) for s in players}
            for s, fz in fzs.items():
                if fz is not None:
                    recs[s].add(fz, acts[s], shadows[s].belief.mirrored)
            obs, _, term, trunc, info = env.step(acts)
            done = bool(np.asarray(term[tside])) or bool(np.asarray(trunc[tside]))
            step += 1
        wins = np.asarray(obs[tside]["team_wins"]).tolist()
        for s in teacher_sides:
            team = 0 if s == "player_0" else 1
            meta = dict(seed=seed, side=s, opponent=opp_kind, teacher_wins=int(wins[team]),
                        opp_wins=int(wins[1 - team]), sap_range=int(info["params"]["unit_sap_range"])
                        if "params" in info else None)
            n = recs[s].save(Path(out_dir) / f"g{seed}_{s}_{opp_kind}.npz", meta)
            done_meta.append({**meta, "samples": n})
    env.close()
    return done_meta


def _dagger_worker(job) -> list[dict]:
    """DAgger: der Schueler spielt selbst, ein Schatten-Lehrer auf seiner Seite sagt fuer genau diese Lagen,
    was er getan haette. So lernt das Netz auch Zustaende, in die nur seine eigenen Fehler fuehren."""
    games, out_dir, student_path = job
    from scripts.experiment import limit_threads
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.imitation_agent import ImitationAgent
    from scripts.kaggle3_opponent import Kaggle3Opponent

    env = LuxAIS3GymEnv(numpy_output=True)
    done_meta = []
    for seed, sside, opp_kind in games:
        oside = "player_1" if sside == "player_0" else "player_0"
        student = ImitationAgent(sside, agent_path=student_path, train=False)
        student.set_to_eval_mode()
        opp = make_player(opp_kind, oside)
        teacher = Kaggle3Opponent(sside)
        for s_, p in ((sside, student), (oside, opp)):
            if hasattr(p, "new_game"):
                p.new_game(s_)
        obs, info = env.reset(seed=seed)
        for p in (student, opp, teacher):
            if hasattr(p, "set_env_cfg"):
                p.set_env_cfg(info["params"])
        rec = SideRecord()
        step, done = 0, False
        while not done:
            label = np.asarray(teacher.act(step, obs[sside]))
            acts = {sside: np.asarray(student.act(step, obs[sside])), oside: np.asarray(opp.act(step, obs[oside]))}
            if student.last_fz is not None:
                rec.add(student.last_fz, label, student.belief.mirrored)
            obs, _, term, trunc, info = env.step(acts)
            teacher.remember_played_actions(acts[sside])
            done = bool(np.asarray(term[sside])) or bool(np.asarray(trunc[sside]))
            step += 1
        wins = np.asarray(obs[sside]["team_wins"]).tolist()
        team = 0 if sside == "player_0" else 1
        meta = dict(seed=seed, side=sside, opponent=opp_kind, dagger=True, student=str(student_path),
                    teacher_history="played_student_actions",
                    student_wins=int(wins[team]), opp_wins=int(wins[1 - team]))
        n = rec.save(Path(out_dir) / f"g{seed}_{sside}_{opp_kind}_dagger.npz", meta)
        done_meta.append({**meta, "samples": n})
    env.close()
    return done_meta


def cmd_dagger(a) -> None:
    out = _check_out(Path(a.out))
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed0)
    mix = [(k, float(v)) for k, v in (kv.split(":") for kv in a.mix.split(","))]
    kinds, weights = zip(*mix)
    games = [(a.seed0 + i, rng.choice(["player_0", "player_1"]), rng.choices(kinds, weights)[0])
             for i in range(a.games)]
    chunks = [games[i::a.workers] for i in range(a.workers) if games[i::a.workers]]
    t0 = time.time()
    student = str(Path(a.student).resolve())
    with mp.get_context("spawn").Pool(len(chunks)) as pool:
        metas = [m for part in pool.map(_dagger_worker, [(c, str(out), student) for c in chunks]) for m in part]
    (out / "collect.json").write_text(json.dumps(dict(
        games=a.games, seed0=a.seed0, mix=a.mix, dagger=True, student=student, teacher="kaggle3 lux3-bot 0.4.8_fn",
        samples=sum(m["samples"] for m in metas), secs=round(time.time() - t0)), indent=1))
    by = {}
    for m in metas:
        w, n = by.get(m["opponent"], (0, 0))
        by[m["opponent"]] = (w + int(m["student_wins"] > m["opp_wins"]), n + 1)
    print(f"DAgger: {len(metas)} Spiele, {sum(m['samples'] for m in metas)} Entscheidungen in {time.time() - t0:.0f}s; "
          "Schueler gewinnt " + ", ".join(f"{k} {w}/{n}" for k, (w, n) in by.items()))


def featurize_safe(shadow, obs):
    from agents.sherlock.imitation_agent import featurize
    return featurize(shadow, obs)


def cmd_collect(a) -> None:
    out = _check_out(Path(a.out))
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed0)
    mix = [(k, float(v)) for k, v in (kv.split(":") for kv in a.mix.split(","))]
    kinds, weights = zip(*mix)
    games = []
    for i in range(a.games):
        seed = a.seed0 + i
        games.append((seed, rng.choice(["player_0", "player_1"]), rng.choices(kinds, weights)[0]))
    chunks = [games[i::a.workers] for i in range(a.workers) if games[i::a.workers]]
    t0 = time.time()
    with mp.get_context("spawn").Pool(len(chunks)) as pool:
        metas = [m for part in pool.map(_collect_worker, [(c, str(out)) for c in chunks]) for m in part]
    (out / "collect.json").write_text(json.dumps(dict(
        games=a.games, seed0=a.seed0, mix=a.mix, teacher="kaggle3 lux3-bot 0.4.8_fn", shadow_cfg="V14 agent_p0.pth",
        samples=sum(m["samples"] for m in metas), files=len(metas), secs=round(time.time() - t0)), indent=1))
    tw = sum(m["teacher_wins"] > m["opp_wins"] for m in metas if m["opponent"] != "kaggle3")
    nk = sum(1 for m in metas if m["opponent"] != "kaggle3")
    print(f"{len(metas)} Lehrer-Seiten, {sum(m['samples'] for m in metas)} Unit-Entscheidungen in "
          f"{time.time() - t0:.0f}s; Lehrer gewinnt {tw}/{nk} Spiele gegen andere Gegner")


# ------------------------------------------------------------------ Training
def load_data(dirs: list[str], val_frac: float, seed: int):
    files = sorted(f for d in dirs for f in Path(d).glob("g*.npz"))
    rng = random.Random(seed)
    games = sorted({f.name.split("_")[0] for f in files})
    val_games = set(rng.sample(games, max(1, int(len(games) * val_frac))))
    parts = {"train": [], "val": []}
    for f in files:
        parts["val" if f.name.split("_")[0] in val_games else "train"].append(f)

    def cat(fs):
        planes, rows = [], {k: [] for k in ("step", "pos", "feats", "mask", "act", "sdx", "sdy")}
        off = 0
        for f in fs:
            z = np.load(f)
            planes.append(z["planes"])
            rows["step"].append(z["step"].astype(np.int64) + off)
            off += len(z["planes"])
            for k in ("pos", "feats", "mask", "act", "sdx", "sdy"):
                rows[k].append(z[k])
        return np.concatenate(planes), {k: np.concatenate(v) for k, v in rows.items()}

    return cat(parts["train"]), cat(parts["val"]), len(parts["train"]), len(parts["val"])


def train_student(train, val, a, log):
    import torch
    import torch.nn.functional as F

    from agents.sherlock.features import FEATURE_DIM
    from agents.sherlock.imitation_net import ImitationNet, window_mask

    dev = torch.device(a.device if a.device != "auto" else ("mps" if torch.backends.mps.is_available() else "cpu"))
    torch.manual_seed(a.seed)
    net = ImitationNet(feat_dim=FEATURE_DIM, n_actions=6, ch=a.ch, blocks=a.blocks, hidden=a.hidden,
                       detach_value=True, sap_head=True).to(dev)

    def to_dev(planes, rows):
        return (torch.as_tensor(planes).to(dev),
                {k: torch.as_tensor(v.astype(np.float32) if k == "feats" else v).to(dev) for k, v in rows.items()})

    P, R = to_dev(*train)
    Pv, Rv = to_dev(*val)
    for T in (R, Rv):
        T["act"], T["pos"] = T["act"].long(), T["pos"].long()
        # Wie im Spiel (imitation_agent.sap_legal): schiessen darf, wer die Sap-Kosten bezahlen kann.
        # Energie, Kosten und Reichweite stehen in den Merkmalen 2, 7, 8 (energy/400, cost/50, range/7).
        energy, cost = T["feats"][:, 2] * 400.0, T["feats"][:, 7] * 50.0
        T["mask"][:, 5] = energy >= cost - 0.5
        T["rng"] = torch.round(T["feats"][:, 8] * 7.0).long()
        T["tgt"] = (T["pos"][:, 0] + T["sdx"].long()) * 24 + (T["pos"][:, 1] + T["sdy"].long())
    n = len(R["act"])
    counts = torch.bincount(R["act"], minlength=6).float()
    log(f"Trainingsdaten: {n} Unit-Entscheidungen, Verteilung " +
        ", ".join(f"{nm} {100 * c / n:.1f} %" for nm, c in zip(("stay", "up", "right", "down", "left", "sap"), counts.tolist())))
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=1e-4)
    train_step_np, val_step_np = train[1]["step"], val[1]["step"]
    n_steps = len(np.unique(train_step_np))
    k_steps = max(8, int(round(a.mb * n_steps / max(1, n))))
    steps_total = a.epochs * ((n_steps + k_steps - 1) // k_steps)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=steps_total, pct_start=0.1)

    def step_batches(Rt_step_np, k, shuffle):
        """Minibatches aus k Spielschritten mit allen Units (Zeilen eines Schritts liegen zusammen).
        Liefert (Zeilenindex, Schritte, inverse Zuordnung Zeile -> Schritt im Batch)."""
        steps_all = np.unique(Rt_step_np)
        starts = np.searchsorted(Rt_step_np, steps_all, side="left")
        ends = np.searchsorted(Rt_step_np, steps_all, side="right")
        order = np.random.permutation(len(steps_all)) if shuffle else np.arange(len(steps_all))
        for b in range(0, len(order), k):
            sel = order[b:b + k]
            counts = ends[sel] - starts[sel]
            idx = np.repeat(starts[sel] - np.concatenate([[0], np.cumsum(counts)[:-1]]), counts) + np.arange(counts.sum())
            inv = np.repeat(np.arange(len(sel)), counts)
            yield (torch.as_tensor(idx, device=dev), torch.as_tensor(steps_all[sel], device=dev),
                   torch.as_tensor(inv, device=dev))

    def batch_logits(Pt, Rt, idx, uniq=None, inv=None):
        """(Logits mit erzwungen erlaubter Lehreraktion, rohe Logits, Maske, Ziel-Logits der Schuesse, Ziele)."""
        if uniq is None:
            uniq, inv = torch.unique(Rt["step"][idx], return_inverse=True)
        planes = Pt[uniq].float() / PLANE_SCALE
        logits, _, smap = net.forward_all(planes, inv, Rt["pos"][idx], Rt["feats"][idx])
        mask = Rt["mask"][idx].clone()
        mask[torch.arange(len(idx), device=dev), Rt["act"][idx]] = True  # Lehreraktion immer erlaubt
        sel = Rt["act"][idx] == 5
        s_logits, s_tgt = None, None
        if bool(sel.any()):
            pos_s = Rt["pos"][idx][sel]
            win = window_mask(pos_s, Rt["rng"][idx][sel], 24, 24)
            win[torch.arange(len(pos_s), device=dev), pos_s[:, 0], pos_s[:, 1]] = False
            s_tgt = Rt["tgt"][idx][sel]
            win.view(len(pos_s), -1)[torch.arange(len(pos_s), device=dev), s_tgt] = True
            s_logits = smap[inv[sel]].masked_fill(~win, -1e4).view(len(pos_s), -1)
        return logits.masked_fill(~mask, -1e4), logits, Rt["mask"][idx], s_logits, s_tgt

    def evaluate():
        net.eval()
        correct = torch.zeros(6, device=dev)
        total = torch.zeros(6, device=dev)
        legal_correct = 0
        sap_n = sap_hit = sap_near = 0
        with torch.no_grad():
            for idx, uniq, inv in step_batches(val_step_np, 512, False):
                lg, raw, m, s_lg, s_tgt = batch_logits(Pv, Rv, idx, uniq, inv)
                if s_lg is not None:
                    pred_t = s_lg.argmax(1)
                    sap_n += len(s_tgt)
                    sap_hit += int((pred_t == s_tgt).sum())
                    sap_near += int((((pred_t // 24) - (s_tgt // 24)).abs().maximum(
                        ((pred_t % 24) - (s_tgt % 24)).abs()) <= 1).sum())
                pred = lg.argmax(1)
                y = Rv["act"][idx]
                for c in range(6):
                    sel = y == c
                    total[c] += sel.sum()
                    correct[c] += (pred[sel] == c).sum()
                # wie im Spiel: nur Sherlocks Maske, Lehreraktion nicht erzwungen
                legal_correct += int((raw.masked_fill(~m, -1e4).argmax(1) == y).sum())
        net.train()
        acc = float(correct.sum() / total.sum())
        per = [float(correct[c] / total[c]) if total[c] > 0 else float("nan") for c in range(6)]
        return acc, per, legal_correct / max(1, len(Rv["act"])), sap_hit / max(1, sap_n), sap_near / max(1, sap_n)

    log(f"Minibatch: {k_steps} Spielschritte (im Mittel etwa {a.mb} Unit-Entscheidungen), Geraet {dev}")
    for ep in range(a.epochs):
        tot, cnt, t0 = 0.0, 0, time.time()
        for idx, uniq, inv in step_batches(train_step_np, k_steps, True):
            lg, _, _, s_lg, s_tgt = batch_logits(P, R, idx, uniq, inv)
            loss = F.cross_entropy(lg, R["act"][idx])  # keine Glaettung: gesperrte Aktionen bekaemen sonst Masse
            if s_lg is not None:
                loss = loss + a.sap_weight * F.cross_entropy(s_lg, s_tgt)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            opt.step()
            sched.step()
            tot += loss.item() * len(idx)
            cnt += len(idx)
        acc, per, acc_game, s_acc, s_near = evaluate()
        log(f"Epoche {ep + 1}/{a.epochs}: Loss {tot / cnt:.4f} | Validierung Trefferquote {100 * acc:.1f} % "
            f"(wie im Spiel {100 * acc_game:.1f} %) | je Aktion " +
            " ".join(f"{nm} {100 * p:.0f}" for nm, p in zip(("stay", "up", "right", "down", "left", "sap"), per)) +
            f" | Schussziel exakt {100 * s_acc:.0f} %, +-1 Feld {100 * s_near:.0f} % | {time.time() - t0:.0f}s")
    return net.to("cpu").eval()


def cmd_train(a) -> None:
    from agents.sherlock.ppo_agent import save_policy

    out = _check_out(Path(a.out))
    if out.exists():
        raise SystemExit(f"{out} existiert schon")
    out.parent.mkdir(parents=True, exist_ok=True)
    log_path = out.with_suffix(".log")

    def log(msg):
        print(msg, flush=True)
        with open(log_path, "a") as fh:
            fh.write(msg + "\n")

    t0 = time.time()
    train, val, nt, nv = load_data(a.data, a.val_frac, a.seed)
    log(f"Dateien: {nt} Training, {nv} Validierung (getrennt nach Spiel), geladen in {time.time() - t0:.0f}s")
    net = train_student(train, val, a, log)
    cfg = v14_cfg()
    save_policy(str(out), net, cfg, extra={"kind": "imitation", "teacher": "kaggle3 lux3-bot 0.4.8_fn",
                                           "data": a.data, "epochs": a.epochs})
    log(f"gespeichert: {out} ({sum(p.numel() for p in net.parameters())} Parameter)")


def cmd_ensemble(a) -> None:
    """Mehrere Schueler zu einem Checkpoint buendeln (erster = Hauptnetz, Rest = imitation_ensemble)."""
    import torch
    out = _check_out(Path(a.out))
    if out.exists():
        raise SystemExit(f"{out} existiert schon")
    cks = [torch.load(p, map_location="cpu", weights_only=False) for p in a.students]
    main_ck = dict(cks[0])
    main_ck["imitation_ensemble"] = [{"arch": c["arch"], "policy": c["policy"]} for c in cks[1:]]
    main_ck["members"] = [str(p) for p in a.students]
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(main_ck, out)
    print(f"Ensemble mit {len(cks)} Schuelern: {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--out", required=True)
    c.add_argument("--games", type=int, default=200)
    c.add_argument("--workers", type=int, default=12)
    c.add_argument("--seed0", type=int, default=TRAIN_SEED0)
    c.add_argument("--mix", default="kaggle3:0.5,v14:0.25,solution92:0.25")
    d = sub.add_parser("dagger")
    d.add_argument("--student", required=True)
    d.add_argument("--out", required=True)
    d.add_argument("--games", type=int, default=200)
    d.add_argument("--workers", type=int, default=12)
    d.add_argument("--seed0", type=int, default=TRAIN_SEED0 + 50_000)
    d.add_argument("--mix", default="kaggle3:0.5,v14:0.25,solution92:0.25")
    e = sub.add_parser("ensemble")
    e.add_argument("--students", nargs="+", required=True)
    e.add_argument("--out", required=True)
    t = sub.add_parser("train")
    t.add_argument("--data", nargs="+", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--epochs", type=int, default=4)
    t.add_argument("--mb", type=int, default=2048)
    t.add_argument("--lr", type=float, default=2e-3)
    t.add_argument("--ch", type=int, default=64)
    t.add_argument("--blocks", type=int, default=6)
    t.add_argument("--hidden", type=int, default=256)
    t.add_argument("--val-frac", type=float, default=0.08)
    t.add_argument("--seed", type=int, default=0)
    t.add_argument("--device", default="auto")
    t.add_argument("--sap-weight", type=float, default=0.5)
    a = ap.parse_args()
    {"collect": cmd_collect, "dagger": cmd_dagger, "ensemble": cmd_ensemble, "train": cmd_train}[a.cmd](a)


if __name__ == "__main__":
    main()
