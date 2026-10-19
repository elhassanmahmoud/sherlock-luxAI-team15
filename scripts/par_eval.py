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


def _worker(job: tuple) -> list[dict]:
    weights, overrides, seeds, opponents = job
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent, play_game

    import torch
    env = LuxAIS3GymEnv(numpy_output=True)
    ckpt = torch.load(weights, map_location="cpu", weights_only=False)
    if isinstance(ckpt, dict) and ckpt.get("kind") == "ppo":
        from agents.sherlock.ppo_agent import PPOAgent
        agent = PPOAgent("player_0", agent_path=weights, train=False)
    else:
        agent = Agent_x("player_0", agent_path=weights, cfg=build_cfg(weights, cnn_args(overrides)[0]),
                        train=False, seed=0)
        _, cnn, w, temp = cnn_args(overrides)
        if cnn:
            from agents.sherlock.ppo_agent import PPOAgent
            agent.set_cnn_policy(PPOAgent("player_0", agent_path=cnn).net, w, temp)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    rows = []
    for opp_name in opponents:
        for seed in seeds:
            for side in P.SIDES:
                opp = make_opponent(opp_name, "player_1" if side == "player_0" else "player_0")
                r = play_game(env, agent, opp, seed, side, train=False)
                r["opponent"] = opp_name
                rows.append({k: r.get(k) for k in GAME_FIELDS})
    env.close()
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--first", type=int, required=True, help="erster Val-Seed-Index")
    ap.add_argument("--n", type=int, required=True, help="Anzahl Karten")
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--opponents", default=",".join(P.EVAL_OPPONENTS))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    build_cfg(args.weights, cnn_args(args.set)[0])  # Schalter frueh pruefen
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"{out} existiert schon - neuen Namen waehlen")
    seeds = [P.VAL_SEED_BASE + i for i in range(args.first, args.first + args.n)]
    opponents = [o for o in args.opponents.split(",") if o]
    chunks = [seeds[i::args.workers] for i in range(args.workers)]
    jobs = [(args.weights, args.set, c, opponents) for c in chunks if c]
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
