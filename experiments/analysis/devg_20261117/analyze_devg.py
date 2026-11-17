"""Auswertung des Dev-G-Vergleichs nach der vorab festgelegten Regel (PLAN.md, 17.11.2026).

    python experiments/analysis/devg_20261117/analyze_devg.py

Gepaart nach Karte (beide Seiten zusammen), 10.000 Ziehungen, Seed 2711. Eine Variante besteht, wenn
1. gegenüber PS: Punkteanteil gegen Kaggle Mittel >= +1,0 und untere Grenze > 0,
2. gegenüber PS: Spiele gegen Solution Mittel >= -1,0,
3. gegenüber R3: Punkteanteil gegen Kaggle Mittel >= +2,0 und untere Grenze > 0, Spiele gegen Solution >= -1,0,
4. fehlerfrei über 303 Schritte (prüft load()).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from experiments.analysis.r3t_20261117.analyze import diff, per_map, share  # noqa: E402
from experiments.analysis.umbau_20261115.tools.compare_dev import load  # noqa: E402

D = Path(__file__).resolve().parent
AGENTS = ("R3", "PS", "E10", "E3", "PS05")
VARIANTS = ("E10", "E3", "PS05")
cell = lambda r: f"{r[0]:+.2f} [{r[1]:+.2f}; {r[2]:+.2f}]"  # noqa: E731


def main() -> None:
    frames = {n: load(str(D / f"{n.lower()}_devG.csv")) for n in AGENTS if (D / f"{n.lower()}_devG.csv").is_file()}
    print("| Agent | Solution | Kaggle | Matches Kaggle | Punkteanteil Kaggle | Stehen gegen Kaggle |")
    print("|---|---:|---:|---:|---:|---:|")
    for name, f in frames.items():
        s, k = f[f.opp == "solution92"], f[f.opp == "kaggle3"]
        sh = k.our_points.sum() / max(k.our_points.sum() + k.opp_points.sum(), 1)
        print(f"| {name} | {int(s.game_win.sum())}/{len(s)} | {int(k.game_win.sum())}/{len(k)} | "
              f"{int(k.our_wins.sum())}/{3 * len(k)} | {100 * sh:.1f} % | {100 * k.wait_frac.mean():.1f} % |")
    passed = []
    for ref in ("R3", "PS"):
        if ref not in frames:
            continue
        print(f"\nGepaart gegen {ref} (Prozentpunkte, 95-%-Kartenintervall):")
        print("| Agent | Punkteanteil Kaggle | Spiele Solution | Spiele Kaggle |")
        print("|---|---:|---:|---:|")
        for name, f in frames.items():
            if name in ("R3", ref):
                continue
            sh = diff(share(f), share(frames[ref]))
            sol = diff(per_map(f, ("solution92",), "game_win"), per_map(frames[ref], ("solution92",), "game_win"))
            kag = diff(per_map(f, ("kaggle3",), "game_win"), per_map(frames[ref], ("kaggle3",), "game_win"))
            print(f"| {name} | {cell(sh)} | {cell(sol)} | {cell(kag)} |")
    if "PS" not in frames:
        return
    for name in VARIANTS:
        if name not in frames:
            continue
        f, pb, r3 = frames[name], frames["PS"], frames["R3"]
        s_pb, sol_pb = diff(share(f), share(pb)), diff(per_map(f, ("solution92",), "game_win"),
                                                         per_map(pb, ("solution92",), "game_win"))
        s_r3, sol_r3 = diff(share(f), share(r3)), diff(per_map(f, ("solution92",), "game_win"),
                                                         per_map(r3, ("solution92",), "game_win"))
        ok = (s_pb[0] >= 1.0 and s_pb[1] > 0 and sol_pb[0] >= -1.0 and s_r3[0] >= 2.0 and s_r3[1] > 0
              and sol_r3[0] >= -1.0)
        print(f"{name}: {'besteht' if ok else 'besteht nicht'}")
        if ok:
            passed.append((name, s_r3[0], int(f[f.opp == "kaggle3"].our_wins.sum())))
    if not passed:
        print("\nKeine Variante besteht: keine weitere Bestätigung.")
        return
    passed.sort(key=lambda t: -t[1])
    best = passed[0]
    close = [p for p in passed[1:] if best[1] - p[1] <= 0.5]
    if close:
        best = max([best] + close, key=lambda t: t[2])
    print(f"\nAusgewählt für die Bestätigung auf 7265000-7265399: {best[0]}")


if __name__ == "__main__":
    main()
