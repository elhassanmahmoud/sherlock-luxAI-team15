"""Abnahmeregeln des V5-Plans (docs/superpowers/plans/2026-10-22-v5-combination.md) pruefen.

    python scripts/v5_gates.py selection REF.csv KAND.csv
    python scripts/v5_gates.py confirm REF.csv KAND.csv DIREKT.csv
Umgebungsvariable MIN_DELTA (22.10.2026, Default 0.05): Mindest-Δ der Bestaetigung gegen die Referenz
(fuer einen vorab festgelegten Plan mit anderer Referenz als V3).

Exit-Code 0 = bestanden, 1 = nicht bestanden. Gepaarter Karten-Bootstrap wie
scripts.compare_report (5000 Ziehungen, Seed 0, 95-%-Perzentile).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.compare_report import compare_results  # noqa: E402


MIN_DELTA = float(os.environ.get("MIN_DELTA", "0.05"))


def direct_interval(path: str) -> tuple[float, float, float, int]:
    d = pd.read_csv(path)
    maps = d.groupby("seed")["result"].mean().to_numpy()
    rng = np.random.default_rng(0)
    samples = rng.choice(maps, size=(5000, len(maps)), replace=True).mean(axis=1)
    low, high = np.percentile(samples, [2.5, 97.5])
    return float(maps.mean()), float(low), float(high), len(d)


def main() -> int:
    mode = sys.argv[1]
    rows = {r["opponent"]: r for r in compare_results(pd.read_csv(sys.argv[3]), pd.read_csv(sys.argv[2]))}
    sol, dfl = rows["solution92"], rows["default"]
    if mode == "selection":
        ok = sol["delta"] >= 0.03 and dfl["winrate"] >= 0.99
        print(f"GATE Auswahl: Solution_92 {sol['winrate']:.4f} vs {sol['ref_winrate']:.4f} "
              f"(Δ {sol['delta'] * 100:+.2f} pp, Ziel >= +3), default {dfl['winrate']:.4f} (Ziel >= 0,99) "
              f"-> {'BESTANDEN' if ok else 'NICHT BESTANDEN'}")
        return 0 if ok else 1
    mean, low, high, n = direct_interval(sys.argv[4])
    checks = {
        f"Solution_92 Δ >= +{MIN_DELTA * 100:.0f} pp": sol["delta"] >= MIN_DELTA,
        "Solution_92 untere 95%-Grenze > 0": sol["low"] > 0,
        "default >= 99 %": dfl["winrate"] >= 0.99,
        "default Δ >= -1 pp": dfl["delta"] >= -0.01,
        "direkt untere 95%-Grenze > 0,5": low > 0.5,
    }
    print(f"GATE Bestaetigung: Solution_92 {sol['winrate']:.4f} vs Referenz {sol['ref_winrate']:.4f}, "
          f"Δ {sol['delta'] * 100:+.2f} pp [{sol['low'] * 100:+.2f}; {sol['high'] * 100:+.2f}]; "
          f"default {dfl['winrate']:.4f} (Δ {dfl['delta'] * 100:+.2f}); direkt {mean:.4f} "
          f"[{low:.4f}; {high:.4f}] aus {n} Spielen")
    for k, v in checks.items():
        print(f"  {'OK  ' if v else 'FAIL'} {k}")
    ok = all(checks.values())
    print("GATE Bestaetigung:", "BESTANDEN" if ok else "NICHT BESTANDEN")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
