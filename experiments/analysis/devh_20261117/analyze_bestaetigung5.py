"""Auswertung der frischen Bestätigung 5 (PLAN.md, Abschnitt "Danach: frische Bestätigung 5").

    python experiments/analysis/devh_20261117/analyze_bestaetigung5.py

Liest bestaetigung5_kandidat.csv, bestaetigung5_k.csv, bestaetigung5_r3.csv und (nur Information) bestaetigung5_direkt.csv.
Gepaart nach Karte (beide Seiten zusammen), 10.000 Ziehungen, Seed 2711. Bedingungen 1-4 gegenüber K, 5 gegenüber R3
(Regel aus ../deve_20261117/BESTAETIGUNG_PLAN.md), 6 Technik (load prüft 303 Schritte; par_eval bricht bei Fehlern ab).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from experiments.analysis.r3t_20261117.analyze import diff, per_map, share  # noqa: E402
from experiments.analysis.umbau_20261115.tools.compare_dev import load  # noqa: E402

D = Path(__file__).resolve().parent


def matches(f):
    return f[f.opp == "kaggle3"].groupby("seed")["our_wins"].mean() / 100


def compare(cand, ref):
    return {"share": diff(share(cand), share(ref)),
            "both": diff(per_map(cand, ("solution92", "kaggle3"), "game_win"),
                         per_map(ref, ("solution92", "kaggle3"), "game_win")),
            "sol": diff(per_map(cand, ("solution92",), "game_win"), per_map(ref, ("solution92",), "game_win")),
            "mt": diff(matches(cand), matches(ref))}


def fmt(r, unit=2):
    return f"{r[0]:+.{unit}f} [{r[1]:+.{unit}f}; {r[2]:+.{unit}f}]"


def main() -> None:
    frames = {n: load(str(D / f"bestaetigung5_{f}.csv")) for n, f in (("Kandidat", "kandidat"), ("K", "k"), ("R3", "r3"))
              if (D / f"bestaetigung5_{f}.csv").is_file()}
    for name, f in frames.items():
        s, k = f[f.opp == "solution92"], f[f.opp == "kaggle3"]
        sh = k.our_points.sum() / max(k.our_points.sum() + k.opp_points.sum(), 1)
        print(f"{name}: Solution {int(s.game_win.sum())}/{len(s)}, Kaggle {int(k.game_win.sum())}/{len(k)}, "
              f"Matches Kaggle {int(k.our_wins.sum())}/{3 * len(k)}, Punkteanteil Kaggle {100 * sh:.1f} %")
    direct = D / "bestaetigung5_direkt.csv"
    if direct.is_file():
        g = load(str(direct))
        print(f"direkt gegen K (Information): {int(g.game_win.sum())}/{len(g)} Spiele, "
              f"{int(g.our_wins.sum())}/{3 * len(g)} Matches")
    if len(frames) < 3:
        print("\nNoch nicht vollständig.")
        return
    vk, vr = compare(frames["Kandidat"], frames["K"]), compare(frames["Kandidat"], frames["R3"])
    c = [
        ("1. gegen K: Punkteanteil gegen Kaggle", "Mittel >= +1,0, untere Grenze > 0", fmt(vk["share"]),
         vk["share"][0] >= 1.0 and vk["share"][1] > 0),
        ("2. gegen K: Spiele Solution + Kaggle", "Mittel >= -0,5, untere Grenze >= -1,5", fmt(vk["both"]),
         vk["both"][0] >= -0.5 and vk["both"][1] >= -1.5),
        ("3. gegen K: Spiele Solution", "Mittel >= -0,5", fmt(vk["sol"]), vk["sol"][0] >= -0.5),
        ("4. gegen K: Matches je Spiel gegen Kaggle", "Mittel > 0", fmt(vk["mt"], 3), vk["mt"][0] > 0),
        ("5a. gegen R3: Punkteanteil gegen Kaggle", "Mittel >= +2,0, untere Grenze > 0", fmt(vr["share"]),
         vr["share"][0] >= 2.0 and vr["share"][1] > 0),
        ("5b. gegen R3: Spiele Solution + Kaggle", "Mittel >= -0,5, untere Grenze >= -1,5", fmt(vr["both"]),
         vr["both"][0] >= -0.5 and vr["both"][1] >= -1.5),
        ("5c. gegen R3: Spiele Solution", "Mittel >= -0,5", fmt(vr["sol"]), vr["sol"][0] >= -0.5),
        ("5d. gegen R3: Matches je Spiel gegen Kaggle", "Mittel > 0", fmt(vr["mt"], 3), vr["mt"][0] > 0),
    ]
    print("\n| Bedingung | verlangt | gemessen | erfüllt |\n|---|---|---|---|")
    for label, need, val, ok in c:
        print(f"| {label} | {need} | {val} | {'ja' if ok else 'nein'} |")
    print("| 6. Technik | keine Fehler, 303 Schritte | geprüft beim Laden (load) | ja |")
    vkr = compare(frames["K"], frames["R3"])
    print(f"\nK gegen R3 (Information): Punkteanteil {fmt(vkr['share'])}, Spiele zusammen {fmt(vkr['both'])}")
    print("\nBESTANDEN" if all(ok for *_, ok in c) else "\nNICHT BESTANDEN")


if __name__ == "__main__":
    main()
