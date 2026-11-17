"""Auswertung des Dev-E-Vergleichs nach der vorab festgelegten Regel (PLAN.md, 17.11.2026).

    python experiments/analysis/deve_20261117/analyze_deve.py

Liest die CSVs aus diesem Ordner. Je Kandidat gegen R3, gepaart nach Karte (beide Seiten zusammen), 10.000 Ziehungen,
Seed 2711:
1. Punkteanteil gegen Kaggle: Mittel >= +2,0 Prozentpunkte und untere 95-%-Grenze > 0,
2. gewonnene Spiele gegen Solution: Mittel >= -1,0 Prozentpunkt,
3. kein abgefangener Fehler, alle Spiele über 303 Schritte (prüft par_eval; hier zusätzlich die Spalte steps).
Auswahl: höchster Punkteanteil; liegen zwei höchstens 0,5 auseinander, entscheiden die gewonnenen Matches gegen Kaggle.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from experiments.analysis.r3t_20261117.analyze import diff, per_map, share  # noqa: E402
from experiments.analysis.umbau_20261115.tools.compare_dev import load  # noqa: E402

D = Path(__file__).resolve().parent
AGENTS = ("R3", "S8", "S9", "S9H", "P8", "P9")
CANDIDATES = ("S9", "S9H", "P8", "P9")


def per_map_matches(df: pd.DataFrame) -> pd.Series:
    return df[df["opp"] == "kaggle3"].groupby("seed")["our_wins"].mean()


def main() -> None:
    frames = {n: load(str(D / f"{n.lower()}_devE.csv")) for n in AGENTS if (D / f"{n.lower()}_devE.csv").is_file()}
    ref = frames["R3"]
    print("| Agent | Solution | Kaggle | Matches Kaggle | Punkteanteil Kaggle | direkt gegen R3 |")
    print("|---|---:|---:|---:|---:|---:|")
    for name, f in frames.items():
        s, k = f[f.opp == "solution92"], f[f.opp == "kaggle3"]
        sh = k.our_points.sum() / max(k.our_points.sum() + k.opp_points.sum(), 1)
        direct = D / f"{name.lower()}_direkt.csv"
        dcell = "–"
        if direct.is_file():
            g = load(str(direct))
            dcell = f"{int(g.game_win.sum())}/{len(g)} ({int(g.our_wins.sum())}/{3 * len(g)})"
        bad = int((f["steps"] != 303).sum()) if "steps" in f else 0
        print(f"| {name} | {int(s.game_win.sum())}/{len(s)} | {int(k.game_win.sum())}/{len(k)} | "
              f"{int(k.our_wins.sum())}/{3 * len(k)} | {100 * sh:.1f} % | {dcell} |" + (f" {bad} Spiele ≠ 303" if bad else ""))
    print("\nGepaart gegen R3 (Prozentpunkte bzw. Matches je Spiel, 95-%-Kartenintervall):")
    print("| Agent | Punkteanteil Kaggle | Spiele Solution | Spiele Kaggle | Spiele zusammen | Matches je Spiel Kaggle | besteht |")
    print("|---|---:|---:|---:|---:|---:|---|")
    cell = lambda r: f"{r[0]:+.2f} [{r[1]:+.2f}; {r[2]:+.2f}]"  # noqa: E731
    passed = []
    for name, f in frames.items():
        if name == "R3":
            continue
        sh = diff(share(f), share(ref))
        sol = diff(per_map(f, ("solution92",), "game_win"), per_map(ref, ("solution92",), "game_win"))
        kag = diff(per_map(f, ("kaggle3",), "game_win"), per_map(ref, ("kaggle3",), "game_win"))
        both = diff(per_map(f, ("solution92", "kaggle3"), "game_win"), per_map(ref, ("solution92", "kaggle3"), "game_win"))
        mt = diff(per_map_matches(f) / 100, per_map_matches(ref) / 100)  # diff() multipliziert mit 100
        steps_ok = "steps" not in f or bool((f["steps"] == 303).all())
        ok = sh[0] >= 2.0 and sh[1] > 0 and sol[0] >= -1.0 and steps_ok
        verdict = "–" if name not in CANDIDATES else ("ja" if ok else "nein")
        if name in CANDIDATES and ok:
            passed.append((name, sh[0], int(f[f.opp == "kaggle3"].our_wins.sum())))
        print(f"| {name} | {cell(sh)} | {cell(sol)} | {cell(kag)} | {cell(both)} | "
              f"{mt[0]:+.3f} [{mt[1]:+.3f}; {mt[2]:+.3f}] | {verdict} |")
    if not passed:
        print("\nKein Kandidat besteht: keine Bestätigung, R3 bleibt.")
        return
    passed.sort(key=lambda t: -t[1])
    best = passed[0]
    close = [p for p in passed[1:] if best[1] - p[1] <= 0.5]
    if close:
        best = max([best] + close, key=lambda t: t[2])
    print(f"\nBestanden: {', '.join(p[0] for p in passed)}. Ausgewählt für die Bestätigung: {best[0]}")


if __name__ == "__main__":
    main()
