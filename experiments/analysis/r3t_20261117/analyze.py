"""Auswertung des Taktiktests nach der vorab festgelegten Regel (PLAN.md, 17.11.2026).

    python experiments/analysis/r3t_20261117/analyze.py --ref R3=r3_devD.csv GRANATE=granate_devD.csv ...

Je Variante gegen die Referenz, gepaart nach Karte (beide Seiten zusammen), 10.000 Ziehungen, Seed 2711:
- gewonnene Spiele gegen Solution und Kaggle zusammen (wie compare_dev.py),
- gewonnene Spiele gegen Solution allein,
- Punkteanteil gegen Kaggle (eigene Punkte durch alle Punkte je Karte).
Regel: vielversprechend, wenn (Spiele zusammen >= +2 oder Punkteanteil Kaggle >= +3) und Solution >= -1.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from experiments.analysis.umbau_20261115.tools.compare_dev import load  # noqa: E402

B, SEED = 10_000, 2711


def boot(d: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(SEED)
    m = d[rng.integers(0, len(d), size=(B, len(d)))].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def per_map(df: pd.DataFrame, opps, col: str) -> pd.Series:
    g = df[df["opp"].isin(opps)]
    full = g.groupby("seed").size() == 2 * len(opps)
    return g[g["seed"].isin(full[full].index)].groupby("seed")[col].mean()


def share(df: pd.DataFrame) -> pd.Series:
    g = df[df["opp"] == "kaggle3"].groupby("seed")[["our_points", "opp_points"]].sum()
    return g["our_points"] / (g["our_points"] + g["opp_points"]).clip(lower=1)


def diff(a: pd.Series, b: pd.Series) -> tuple[float, float, float, int]:
    common = a.index.intersection(b.index)
    d = (a.loc[common] - b.loc[common]).to_numpy() * 100
    lo, hi = boot(d)
    return float(d.mean()), lo, hi, len(d)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("agents", nargs="+", help="NAME=CSV")
    a = ap.parse_args()
    frames = {}
    for spec in a.agents:
        name, path = spec.split("=", 1)
        frames[name] = pd.concat([load(p) for p in path.split(",")], ignore_index=True)
    ref = frames[a.ref]
    print("| Agent | Solution | Kaggle | Matches Kaggle | Punkteanteil Kaggle |")
    print("|---|---:|---:|---:|---:|")
    for name, f in frames.items():
        s, k = f[f.opp == "solution92"], f[f.opp == "kaggle3"]
        sh = k.our_points.sum() / max(k.our_points.sum() + k.opp_points.sum(), 1)
        print(f"| {name} | {int(s.game_win.sum())}/{len(s)} | {int(k.game_win.sum())}/{len(k)} | "
              f"{int(k.our_wins.sum())}/{3 * len(k)} | {100 * sh:.1f} % |")
    print(f"\nGepaart gegen {a.ref} (Prozentpunkte, 95-%-Kartenintervall):")
    print("| Agent | Spiele Solution + Kaggle | Spiele Solution | Spiele Kaggle | Punkteanteil Kaggle | vielversprechend |")
    print("|---|---:|---:|---:|---:|---|")
    for name, f in frames.items():
        if name == a.ref:
            continue
        both = diff(per_map(f, ("solution92", "kaggle3"), "game_win"), per_map(ref, ("solution92", "kaggle3"), "game_win"))
        sol = diff(per_map(f, ("solution92",), "game_win"), per_map(ref, ("solution92",), "game_win"))
        kag = diff(per_map(f, ("kaggle3",), "game_win"), per_map(ref, ("kaggle3",), "game_win"))
        sh = diff(share(f), share(ref))
        ok = (both[0] >= 2.0 or sh[0] >= 3.0) and sol[0] >= -1.0
        cell = lambda r: f"{r[0]:+.2f} [{r[1]:+.2f}; {r[2]:+.2f}]"  # noqa: E731
        print(f"| {name} | {cell(both)} | {cell(sol)} | {cell(kag)} | {cell(sh)} | {'ja' if ok else 'nein'} |")


if __name__ == "__main__":
    main()
