"""Auswertung der dritten frischen Bestätigung (Dev-F-Sieger, PLAN.md "Danach"; Regel wie ../deve_20261117/BESTAETIGUNG_PLAN.md).

    python experiments/analysis/devf_20261117/analyze_bestaetigung3.py

Liest bestaetigung3_r3.csv, bestaetigung3_kandidat.csv und (nur Information) bestaetigung3_p9.csv und bestaetigung3_direkt.csv.
Gepaart nach Karte gegen R3 (beide Seiten zusammen), 10.000 Ziehungen, Seed 2711.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from experiments.analysis.r3t_20261117.analyze import diff, per_map, share  # noqa: E402
from experiments.analysis.umbau_20261115.tools.compare_dev import load  # noqa: E402

D = Path(__file__).resolve().parent


def main() -> None:
    r3 = load(str(D / "bestaetigung3_r3.csv"))
    cand = load(str(D / "bestaetigung3_kandidat.csv"))
    for name, f in (("R3", r3), ("Kandidat", cand)):
        s, k = f[f.opp == "solution92"], f[f.opp == "kaggle3"]
        sh = k.our_points.sum() / max(k.our_points.sum() + k.opp_points.sum(), 1)
        ssh = s.our_points.sum() / max(s.our_points.sum() + s.opp_points.sum(), 1)
        print(f"{name}: Solution {int(s.game_win.sum())}/{len(s)}, Kaggle {int(k.game_win.sum())}/{len(k)}, "
              f"Matches Kaggle {int(k.our_wins.sum())}/{3 * len(k)}, Punkteanteil Kaggle {100 * sh:.1f} %, "
              f"Punkteanteil Solution {100 * ssh:.1f} %")
    direct = D / "bestaetigung3_direkt.csv"
    if direct.is_file():
        g = load(str(direct))
        print(f"direkt gegen R3 (Information): {int(g.game_win.sum())}/{len(g)} Spiele, "
              f"{int(g.our_wins.sum())}/{3 * len(g)} Matches")
    sh = diff(share(cand), share(r3))
    both = diff(per_map(cand, ("solution92", "kaggle3"), "game_win"), per_map(r3, ("solution92", "kaggle3"), "game_win"))
    sol = diff(per_map(cand, ("solution92",), "game_win"), per_map(r3, ("solution92",), "game_win"))
    kag_m = lambda f: f[f.opp == "kaggle3"].groupby("seed")["our_wins"].mean() / 100  # noqa: E731
    mt = diff(kag_m(cand), kag_m(r3))
    c = [
        ("1. Punkteanteil gegen Kaggle", "Mittel >= +2,0, untere Grenze > 0", sh, sh[0] >= 2.0 and sh[1] > 0),
        ("2. Spiele Solution + Kaggle", "Mittel >= -0,5, untere Grenze >= -1,5", both, both[0] >= -0.5 and both[1] >= -1.5),
        ("3. Spiele Solution", "Mittel >= -0,5", sol, sol[0] >= -0.5),
        ("4. Matches je Spiel gegen Kaggle", "Mittel > 0", mt, mt[0] > 0),
    ]
    print("\n| Bedingung | verlangt | gemessen | erfüllt |\n|---|---|---|---|")
    for label, need, r, ok in c:
        unit = 3 if label.startswith("4.") else 2
        print(f"| {label} | {need} | {r[0]:+.{unit}f} [{r[1]:+.{unit}f}; {r[2]:+.{unit}f}] | {'ja' if ok else 'nein'} |")
    print("| 5. Technik | keine Fehler, 303 Schritte | geprüft beim Laden (load) | ja |")
    print("\nBESTANDEN" if all(ok for *_, ok in c) else "\nNICHT BESTANDEN")



def compare_p9() -> None:
    """Nur Information: Kandidat gegen P9 auf denselben Karten (gepaart nach Karte)."""
    p9_path = D / "bestaetigung3_p9.csv"
    if not p9_path.is_file():
        return
    p9, cand = load(str(p9_path)), load(str(D / "bestaetigung3_kandidat.csv"))
    sh = diff(share(cand), share(p9))
    both = diff(per_map(cand, ("solution92", "kaggle3"), "game_win"), per_map(p9, ("solution92", "kaggle3"), "game_win"))
    k = p9[p9.opp == "kaggle3"]
    s = p9[p9.opp == "solution92"]
    print(f"\nP9 (Information): Solution {int(s.game_win.sum())}/{len(s)}, Kaggle {int(k.game_win.sum())}/{len(k)}, "
          f"Matches Kaggle {int(k.our_wins.sum())}/{3 * len(k)}")
    print(f"Kandidat gegen P9: Punkteanteil Kaggle {sh[0]:+.2f} [{sh[1]:+.2f}; {sh[2]:+.2f}], "
          f"Spiele zusammen {both[0]:+.2f} [{both[1]:+.2f}; {both[2]:+.2f}]")


if __name__ == "__main__":
    main()
    compare_p9()
