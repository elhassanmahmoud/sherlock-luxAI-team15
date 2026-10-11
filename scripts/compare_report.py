"""Auswertung von scripts/compare_weights.py: Winrate je Gegner + gepaarter
Bootstrap-Unterschied zu einer Referenz.

    python -m scripts.compare_report --ref experiments/compare/full_s0.csv experiments/compare/*.csv
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("csvs", nargs="+")
    args = ap.parse_args()
    rng = np.random.default_rng(0)
    key = ["opponent", "seed", "side"]
    ref = pd.read_csv(args.ref).set_index(key)["result"]
    print(f"{'Kandidat':28s} {'Gegner':10s} {'N':>4s} {'WR':>6s} {'Δ zu Ref':>9s}  95-%-KI")
    for path in args.csvs:
        df = pd.read_csv(path)
        name = path.split("/")[-1].removesuffix(".csv")
        for opp, g in df.groupby("opponent"):
            d = (g.set_index(key)["result"] - ref).dropna()
            boots = [rng.choice(d.values, len(d)).mean() for _ in range(5000)]
            lo, hi = np.percentile(boots, [2.5, 97.5])
            print(f"{name:28s} {opp:10s} {len(g):4d} {g['result'].mean():6.3f} "
                  f"{d.mean():+9.3f}  [{lo:+.3f}; {hi:+.3f}]")


if __name__ == "__main__":
    main()
