"""Niederlagen aus einer par_eval-CSV parallel mit Ground Truth vermessen (29.10.2026).

    python -m scripts.par_losses --weights W --games experiments/compare/battle/B_V10_dev800.csv \
        --opponent sol92_sq --which lost --out experiments/analysis/battle/losses_sq.csv

Spielt genau die Spiele (Karte, Seite, Gegner) der Eingabe-CSV noch einmal (gleiche Seeds wie
par_eval: random/np.random werden vor env.reset gesetzt) und misst je Match und Team mit
scripts.analyze_losses.play_and_measure: Punkte, erster Punkt, Belegung der echten Punktefelder,
umkaempfte Felder, Einheiten, Energie, Tode, Gedaechtnis richtig/falsch. Gewichte nur lesen.
--which all|lost|won waehlt die Spiele nach dem Ergebnis in der Eingabe-CSV.
"""
from __future__ import annotations

import argparse
import csv
import multiprocessing as mp
from pathlib import Path

import pandas as pd

from scripts.analyze_losses import FIELDS
from scripts.experiment import limit_threads


def opponent_for(kind: str, side: str):
    from scripts.common import make_opponent
    if kind.startswith("self:"):
        return make_opponent("self", side, self_play_path=kind.split(":", 1)[1])
    return make_opponent(kind, side)


def _worker(job):
    weights, overrides, games = job
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x
    from scripts.analyze_losses import play_and_measure
    from scripts.par_eval import build_cfg

    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=weights, cfg=build_cfg(weights, overrides), train=False)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    rows = []
    for seed, side, opponent in games:
        opp = opponent_for(opponent, "player_1" if side == "player_0" else "player_0")
        for r in play_and_measure(env, agent, opp, int(seed), side):
            rows.append({**r, "opponent": opponent})
    env.close()
    return rows


def select_games(df: pd.DataFrame, opponent: str | None, which: str) -> list[tuple]:
    if opponent:
        df = df[df["opponent"] == opponent]
    if which == "lost":
        df = df[df["result"] < 0.5]
    elif which == "won":
        df = df[df["result"] >= 0.5]
    return [(int(r.seed), r.side, r.opponent) for r in df.itertuples()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--games", required=True, help="par_eval-CSV mit seed, side, opponent, result")
    ap.add_argument("--opponent", default=None)
    ap.add_argument("--which", choices=("all", "lost", "won"), default="lost")
    ap.add_argument("--limit", type=int, default=0, help="hoechstens so viele Spiele (0 = alle)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"{out} existiert schon - neuen Namen waehlen")
    games = select_games(pd.read_csv(args.games), args.opponent, args.which)
    if args.limit:
        games = games[:args.limit]
    if not games:
        raise SystemExit("keine passenden Spiele")
    chunks = [games[i::args.workers] for i in range(args.workers)]
    jobs = [(args.weights, args.set, c) for c in chunks if c]
    with mp.get_context("spawn").Pool(len(jobs)) as pool:
        results = pool.map(_worker, jobs)
    rows = sorted((r for rs in results for r in rs), key=lambda r: (r["seed"], r["side"], r["match"], r["team"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS + ["opponent"])
        w.writeheader()
        w.writerows(rows)
    print(f"{out}: {len(games)} Spiele, {len(rows)} Zeilen")


if __name__ == "__main__":
    main()
