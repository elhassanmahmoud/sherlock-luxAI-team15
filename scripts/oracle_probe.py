"""Diagnose (29.10.2026): Wie viel brächte perfektes Wissen über Relics und Punktefelder?

    python -m scripts.oracle_probe --weights W --first 300000 --n 300 --opponents solution92,sol92_sq \
        --out experiments/compare/battle/O_full.csv

Nach jeder Beobachtung bekommt das Gedaechtnis die WAHREN gespawnten Relics und Punktefelder aus
env.state (Formel wie scripts.mechanism_probe.point_tiles): alle Punktefelder bewiesen, alle uebrigen
Felder der Relic-Zonen als tot markiert. --mode relics: nur die Relics (Punktefelder muss der Agent
selbst finden); --mode points: nur Punktefelder und tote Felder um Relics, die der Agent schon kennt. Das ist Wissen, das kein Agent hat. Reine Obergrenze, nie
fuer Training oder Abgabe. Ausgabe wie par_eval (eine Zeile pro Spiel) -> scripts.compare_report.
"""
from __future__ import annotations

import argparse
import csv
import multiprocessing as mp
from pathlib import Path

import numpy as np

from scripts import protocol as P
from scripts.experiment import GAME_FIELDS, limit_threads


def truth_maps(state) -> tuple[np.ndarray, list[tuple[int, int]]]:
    rw = np.asarray(state.relic_nodes_map_weights).astype(int)
    rmask = np.asarray(state.relic_nodes_mask).astype(bool)
    n = int(rmask.sum()) // 2
    pts = (rw > 0) & (rw <= n)
    relics = [tuple(int(v) for v in p) for p in np.asarray(state.relic_nodes)[rmask]]
    return pts, relics


def install_oracle(agent, env, mode: str = "full") -> None:
    from agents.sherlock import geometry as geo
    b = agent.belief
    original = b.observe

    def observe(obs):
        fresh = int(np.asarray(obs["steps"])) != b._last_step
        original(obs)
        if not fresh or int(np.asarray(obs["match_steps"])) == 0:
            return
        pts, relics = truth_maps(env.state)
        W, H = b.W, b.H
        if b.mirrored:
            pts = geo.mirror_map(pts)
            relics = [geo.mirror_xy(x, y, W, H) for x, y in relics]
        if mode in ("full", "relics"):
            for x, y in relics:
                b._add_relic(int(x), int(y))
        if mode in ("full", "points"):
            for x, y in np.argwhere(pts & b.relic_zone):
                b._mark_point(int(x) * H + int(y))
            for x, y in np.argwhere(b.relic_zone & ~pts):
                b._mark_dead(int(x) * H + int(y))
        b._cand_dirty = True
        b._refresh_candidates()

    b.observe = observe


def _worker(job):
    weights, overrides, seeds, opponents, mode = job
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent, play_game
    from scripts.par_eval import build_cfg

    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=weights, cfg=build_cfg(weights, overrides), train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    install_oracle(agent, env, mode)
    rows = []
    for opp_name in opponents:
        for seed in seeds:
            for side in P.SIDES:
                opp_side = "player_1" if side == "player_0" else "player_0"
                opp = (make_opponent("self", opp_side, self_play_path=opp_name[5:])
                       if opp_name.startswith("self:") else make_opponent(opp_name, opp_side))
                r = play_game(env, agent, opp, seed, side, train=False)
                r["opponent"] = opp_name
                rows.append({k: r.get(k) for k in GAME_FIELDS})
    env.close()
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--first", type=int, required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--opponents", default="solution92,sol92_sq")
    ap.add_argument("--mode", choices=("full", "relics", "points"), default="full")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"{out} existiert schon - neuen Namen waehlen")
    seeds = [P.VAL_SEED_BASE + i for i in range(args.first, args.first + args.n)]
    opponents = [o for o in args.opponents.split(",") if o]
    jobs = [(args.weights, args.set, seeds[i::args.workers], opponents, args.mode) for i in range(args.workers)]
    with mp.get_context("spawn").Pool(len(jobs)) as pool:
        results = pool.map(_worker, [j for j in jobs if j[2]])
    rows = sorted((r for rs in results for r in rs), key=lambda r: (r["opponent"], r["seed"], r["side"]))
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=GAME_FIELDS)
        w.writeheader()
        w.writerows(rows)
    for o in opponents:
        rs = [r for r in rows if r["opponent"] == o]
        print(f"{out.name}: {o}: {np.mean([r['result'] for r in rs]):.3f} ({len(rs)} Spiele)")


if __name__ == "__main__":
    main()
