"""Auswertung der Robustheitsprüfung (PLAN.md, 17.11.2026): R3 und P9 gegen sechs weitere Spielweisen.

    python experiments/analysis/robust_p9_20261117/analyze_robust.py

Warnzeichen laut Plan: P9 gewinnt gegen einen Gegner mindestens 3 Spiele weniger als R3 (von 50).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

D = Path(__file__).resolve().parent


def name(opp: str) -> str:
    return "V14" if opp.startswith("self:") else opp


def main() -> None:
    r3, p9 = pd.read_csv(D / "r3_robust.csv"), pd.read_csv(D / "p9_robust.csv")
    for f in (r3, p9):
        f["opp"] = f["opponent"].map(name)
        bad = ~(f["steps"].eq(303) & (f["our_wins"] + f["opp_wins"]).eq(3))
        if bad.any():
            raise ValueError(f"{int(bad.sum())} unvollständige Spiele")
    print("| Gegner | R3 Spiele | P9 Spiele | R3 Matches | P9 Matches | R3 Punkteanteil | P9 Punkteanteil | Warnzeichen |")
    print("|---|---:|---:|---:|---:|---:|---:|---|")
    for opp in r3["opp"].unique():
        a, b = r3[r3.opp == opp], p9[p9.opp == opp]
        sa = a.our_points.sum() / max(a.our_points.sum() + a.opp_points.sum(), 1)
        sb = b.our_points.sum() / max(b.our_points.sum() + b.opp_points.sum(), 1)
        warn = int(b.game_win.sum()) <= int(a.game_win.sum()) - 3
        print(f"| {opp} | {int(a.game_win.sum())}/{len(a)} | {int(b.game_win.sum())}/{len(b)} | "
              f"{int(a.our_wins.sum())}/{3 * len(a)} | {int(b.our_wins.sum())}/{3 * len(b)} | {100 * sa:.1f} % | "
              f"{100 * sb:.1f} % | {'ja' if warn else 'nein'} |")


if __name__ == "__main__":
    main()
