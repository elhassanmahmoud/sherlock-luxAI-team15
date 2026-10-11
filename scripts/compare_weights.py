"""Gewichte fair vergleichen: gleiche Validierungs-Seeds, beide Seiten, beide Gegner.

    python -m scripts.compare_weights --weights <a.pth> --out experiments/compare/a.csv

Ein CSV pro Kandidat (eine Zeile pro Spiel). Gleiche Seeds -> gepaarter
Vergleich mit scripts/compare_report.py. Nur Validierungs-Seeds (500 000+),
die Test-Seeds bleiben unberuehrt.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from scripts import protocol as P
from scripts.experiment import GAME_FIELDS, limit_threads


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-seeds", type=int, default=40)
    ap.add_argument("--first", type=int, default=0, help="erster Validierungs-Seed-Index (zum Aufteilen)")
    args = ap.parse_args()

    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent, play_game

    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=args.weights, train=False)
    agent.set_to_eval_mode()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=GAME_FIELDS)
        w.writeheader()
        for opp_name in P.EVAL_OPPONENTS:
            for seed in P.val_seeds(args.first + args.n_seeds)[args.first:]:
                for side in P.SIDES:
                    opp = make_opponent(opp_name, "player_1" if side == "player_0" else "player_0")
                    r = play_game(env, agent, opp, seed, side, train=False)
                    r["opponent"] = opp_name
                    w.writerow({k: r.get(k) for k in GAME_FIELDS})
            fh.flush()
    env.close()


if __name__ == "__main__":
    main()
