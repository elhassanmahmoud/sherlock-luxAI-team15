"""Schnelle parallele Evaluation fester Gewichte (mit optionalen Config-Schaltern).

    python -m scripts.par_eval --weights experiments/ensembles/old3_sym3.pth \
        --set early_inference=true --first 720 --n 60 --out experiments/compare/x.csv

Spielt Validierungs-Seeds 500 000 + [first, first + n) auf beiden Seiten gegen
jeden Gegner aus --opponents, verteilt auf --workers Prozesse. Ausgabe wie
compare_weights (eine Zeile pro Spiel) -> gepaart mit scripts.compare_report.
Die Gewichte werden nur gelesen (train=False, kein Autosave).
"""
from __future__ import annotations

import argparse
import csv
import multiprocessing as mp
import time
from pathlib import Path

from scripts import protocol as P
from scripts.experiment import GAME_FIELDS, limit_threads


def parse_value(v: str):
    low = v.lower()
    if low in ("true", "false"):
        return low == "true"
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return v


def cnn_args(overrides: list[str]):
    """cnn=PFAD, cnn_weight=W, cnn_temp=T aus den --set-Angaben herausziehen."""
    rest, cnn, w, temp = [], None, 1.0, 0.2
    for item in overrides:
        k, v = item.split("=", 1)
        if k == "cnn":
            cnn = v
        elif k == "cnn_weight":
            w = float(v)
        elif k == "cnn_temp":
            temp = float(v)
        else:
            rest.append(item)
    return rest, cnn, w, temp


def build_cfg(weights: str, overrides: list[str]):
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.main import Agent_x

    cfg = Agent_x._cfg_from_checkpoint(weights) or AgentConfig()
    known = set(AgentConfig.__dataclass_fields__)
    for item in overrides:
        k, v = item.split("=", 1)
        if k not in known:
            raise SystemExit(f"Unbekannter Config-Schalter: {k}")
        setattr(cfg, k, parse_value(v))
    return cfg


def require_no_agent_errors(agent, opponent) -> None:
    """A caught policy error invalidates the measurement on either side."""
    from scripts.xversion_replay import require_clean_policy

    require_clean_policy(agent, "agent")
    require_clean_policy(opponent, "opponent")


def _worker(job: tuple) -> list[dict]:
    if len(job) == 4:  # Historical callers supply this four-tuple.
        weights, overrides, seeds, opponents = job
        packed_v14 = False
    else:
        weights, overrides, seeds, opponents, packed_v14 = job
        if type(packed_v14) is not bool:
            raise ValueError("packed_v14 must be boolean")
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent, play_game

    import torch
    from scripts import r3_package
    env = LuxAIS3GymEnv(numpy_output=True)
    from agents.sherlock_r3t import agent as r3t
    if r3_package.is_spec(weights) or r3t.is_spec(weights):
        ckpt = None  # 16.11.2026: R3-Kurspaket als zu messender Spieler (scripts/r3_package.py); 17.11.: r3t: mit Taktiken
    elif packed_v14:
        from scripts import packed_v14 as backend
        ckpt = backend.load_checkpoint(weights, overrides)
    else:
        ckpt = torch.load(weights, map_location="cpu", weights_only=False)
    if r3_package.is_spec(weights):
        agent = r3_package.r3_package_agent("player_0", weights[len(r3_package.PREFIX):])
    elif r3t.is_spec(weights):  # 17.11.2026: R3 + Taktikschicht (agents/sherlock_r3t), z. B. r3t:granate,sog
        agent = r3t.make_r3t("player_0", r3t.DEFAULT_ZIP, weights[len(r3t.PREFIX):])
    elif isinstance(ckpt, dict) and ckpt.get("kind") == "hybrid" and "v14_ckpt" in ckpt:
        # 15.11.2026: gepackter Hybrid (eine agent.pth wie in der Abgabe) -> genau ueber Agent_x laden
        agent = Agent_x("player_0", agent_path=weights, train=False, seed=0)
    elif isinstance(ckpt, dict) and ckpt.get("kind") == "hybrid":
        # 15.11.2026: V14 + nachgeahmte Policy je Unit (agents/sherlock/hybrid_agent.py); --set gilt fuer den Schueler
        from agents.sherlock.hybrid_agent import HybridAgent
        agent = HybridAgent("player_0", ckpt["v14"], ckpt["student"], mode=ckpt.get("mode", "points"),
                            combat_radius=int(ckpt.get("combat_radius", 5)),
                            student_cfg=build_cfg(ckpt["student"], overrides) if overrides else None)
    elif isinstance(ckpt, dict) and ckpt.get("kind") == "imitation":
        # 15.11.2026: nachgeahmte Policy (scripts/imitate.py), gleiche Vorverarbeitung wie beim Sammeln
        from agents.sherlock.imitation_agent import ImitationAgent
        agent = ImitationAgent("player_0", agent_path=weights, train=False,
                               cfg=build_cfg(weights, overrides) if overrides else None)
    elif isinstance(ckpt, dict) and ckpt.get("kind") == "ppo":
        from agents.sherlock.ppo_agent import PPOAgent
        agent = PPOAgent("player_0", agent_path=weights, train=False,
                         cfg=build_cfg(weights, overrides) if overrides else None)
    else:
        agent = Agent_x("player_0", agent_path=weights, cfg=build_cfg(weights, cnn_args(overrides)[0]),
                        train=False, seed=0)
        _, cnn, w, temp = cnn_args(overrides)
        if cnn:
            from agents.sherlock.ppo_agent import PPOAgent
            agent.set_cnn_policy(PPOAgent("player_0", agent_path=cnn).net, w, temp)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    if packed_v14:
        backend.install(agent, ckpt)
    rows = []
    for opp_name in opponents:
        for seed in seeds:
            for side in P.SIDES:
                opp_side = "player_1" if side == "player_0" else "player_0"
                if opp_name.startswith("self:"):  # eigener Checkpoint als Gegner
                    opp = make_opponent("self", opp_side, self_play_path=opp_name[5:])
                elif opp_name.startswith("imit:"):  # 15.11.2026: nachgeahmte Policy als Gegner
                    from agents.sherlock.imitation_agent import ImitationAgent
                    opp = ImitationAgent(opp_side, agent_path=opp_name[5:], train=False)
                    opp.set_to_eval_mode()
                elif r3_package.is_spec(opp_name):  # 16.11.2026: freigegebenes R3-Finalpaket als Gegner
                    opp = r3_package.r3_package_agent(opp_side, opp_name[len(r3_package.PREFIX):])
                elif r3t.is_spec(opp_name):  # 17.11.2026: R3 + Taktikschicht als Gegner
                    opp = r3t.make_r3t(opp_side, r3t.DEFAULT_ZIP, opp_name[len(r3t.PREFIX):])
                elif opp_name.startswith("ppo:"):  # 22.10.2026: CNN-PPO-Checkpoint als Gegner
                    from agents.sherlock.ppo_agent import PPOAgent
                    opp = PPOAgent(opp_side, agent_path=opp_name[4:], train=False)
                    opp.set_to_eval_mode()
                else:
                    opp = make_opponent(opp_name, opp_side)
                r = play_game(env, agent, opp, seed, side, train=False)
                require_no_agent_errors(agent, opp)
                r["opponent"] = opp_name
                rows.append({k: r.get(k) for k in GAME_FIELDS})
    env.close()
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--first", type=int, default=None, help="erster Val-Seed-Index")
    ap.add_argument("--n", type=int, default=None, help="Anzahl Karten")
    ap.add_argument("--seed-list", default=None,
                    help="JSON-Liste absoluter Env-Seeds statt --first/--n (21.10.2026: Entwicklungs-Sets)")
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--opponents", default=",".join(P.EVAL_OPPONENTS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--packed-v14", action="store_true",
                    help="CPU: nur die 36 unveränderten Netze des V14-Kandidaten gemeinsam berechnen")
    args = ap.parse_args()

    from scripts import r3_package
    from agents.sherlock_r3t import agent as r3t
    from agents.sherlock_r3t.tactics import TacticsCfg
    if r3t.is_spec(args.weights):
        if args.set or args.packed_v14:
            raise SystemExit("r3t: unterstuetzt weder --set noch --packed-v14 (Schalter stehen hinter r3t:)")
        TacticsCfg.parse(args.weights[len(r3t.PREFIX):])  # Schalter frueh pruefen
    elif r3_package.is_spec(args.weights):
        # 16.11.2026: das R3-Paket wird unveraendert gespielt, also ohne Schalter und ohne Packed-Backend
        if args.set or args.packed_v14:
            raise SystemExit("r3zip: unterstuetzt weder --set noch --packed-v14")
        if not Path(args.weights[len(r3_package.PREFIX):]).is_file():
            raise SystemExit(f"R3-Paket fehlt: {args.weights}")
    else:
        if args.packed_v14:
            from scripts.packed_v14 import verified_bytes
            verified_bytes(args.weights, args.set)
        build_cfg(args.weights, cnn_args(args.set)[0])  # Schalter frueh pruefen
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"{out} existiert schon - neuen Namen waehlen")
    if args.seed_list:
        import json
        seeds = [int(s) for s in json.loads(Path(args.seed_list).read_text())]
    elif args.first is not None and args.n is not None:
        seeds = [P.VAL_SEED_BASE + i for i in range(args.first, args.first + args.n)]
    else:
        raise SystemExit("--first/--n oder --seed-list angeben")
    opponents = [o for o in args.opponents.split(",") if o]
    chunks = [seeds[i::args.workers] for i in range(args.workers)]
    jobs = [(args.weights, args.set, c, opponents) for c in chunks if c]
    if args.packed_v14:
        jobs = [(*job, True) for job in jobs]
    t0 = time.time()
    ctx = mp.get_context("spawn")
    with ctx.Pool(len(jobs)) as pool:
        results = pool.map(_worker, jobs)
    rows = sorted((r for rs in results for r in rs),
                  key=lambda r: (r["opponent"], r["seed"], r["side"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=GAME_FIELDS)
        w.writeheader()
        w.writerows(rows)
    by_opp: dict[str, list[float]] = {}
    for r in rows:
        by_opp.setdefault(r["opponent"], []).append(float(r["result"]))
    summary = ", ".join(f"{o}: {sum(v) / len(v):.3f} ({len(v)} Spiele)" for o, v in by_opp.items())
    print(f"{out.name}: {summary} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
