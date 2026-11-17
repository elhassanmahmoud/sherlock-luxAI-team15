"""Auswertung des Dev-H-Vergleichs nach der vorab festgelegten Regel (PLAN.md, 17.11.2026, 19:41).

    python experiments/analysis/devh_20261117/analyze_devh.py

Gepaart nach Karte gegen K (beide Seiten zusammen), 10.000 Ziehungen, Seed 2711. Ein Modul hilft, wenn
1. Punkteanteil gegen Kaggle im Mittel >= +0,5 Prozentpunkte,
2. Spiele gegen Solution im Mittel >= -1,0,
3. Spiele gegen Solution und Kaggle zusammen im Mittel >= -0,5,
4. fehlerfrei über 303 Schritte (prüft load(); par_eval bricht bei abgefangenen Fehlern ab).
Beast = K + alle helfenden Module (von ENDE10/ENDE20/ENDE10F und GRANATE/NEBEL jeweils das mit dem höchsten
Punkteanteil; ENDE10F laut Nachtrag 20:08).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from experiments.analysis.r3t_20261117.analyze import diff, per_map, share  # noqa: E402
from experiments.analysis.umbau_20261115.tools.compare_dev import load  # noqa: E402

D = Path(__file__).resolve().parent
ORDER = ("K", "ENDE10", "ENDE20", "ENDE10F", "ALLE", "ENDSAP", "GRANATE", "NEBEL", "SOG", "FOCUS", "SPAREN", "WECHSEL",
         "EROBERN", "TANKEN", "COVER", "SAPBIAS", "MASKFREI", "BEAST")
SINGLE = tuple(n for n in ORDER if n not in ("K", "ALLE", "BEAST"))
SWITCHES = {"ENDE10": ["imit_end_fill=10"], "ENDE20": ["imit_end_fill=20"],
            "ENDE10F": ["imit_end_fill=10", "imit_end_force=true"], "ENDSAP": ["end_sap=10"],
            "GRANATE": ["t:granate"], "NEBEL": ["t:granate", "t:nebel"], "SOG": ["t:sog"],
            "FOCUS": ["focus_sap=true"], "SPAREN": ["t:sparen"], "WECHSEL": ["t:wechsel"],
            "EROBERN": ["t:erobern"], "TANKEN": ["t:tanken"], "COVER": ["imit_cover=0.5"],
            "SAPBIAS": ["imit_sap_bias=0.5"], "MASKFREI": ["safe_moves=false", "collision_guard=false"]}
cell = lambda r: f"{r[0]:+.2f} [{r[1]:+.2f}; {r[2]:+.2f}]"  # noqa: E731


def evaluate(f, k) -> dict:
    out = {"share": diff(share(f), share(k)),
           "sol": diff(per_map(f, ("solution92",), "game_win"), per_map(k, ("solution92",), "game_win")),
           "both": diff(per_map(f, ("solution92", "kaggle3"), "game_win"),
                        per_map(k, ("solution92", "kaggle3"), "game_win")),
           "kag": diff(per_map(f, ("kaggle3",), "game_win"), per_map(k, ("kaggle3",), "game_win"))}
    out["helps"] = out["share"][0] >= 0.5 and out["sol"][0] >= -1.0 and out["both"][0] >= -0.5
    return out


def beast(helpers: list[str], res: dict) -> tuple[list[str], list[str]]:
    """Helfende Module zusammenlegen; liefert (Module, --set-Angaben)."""
    chosen = set(helpers)
    for family in (("ENDE10", "ENDE20", "ENDE10F"), ("GRANATE", "NEBEL")):  # je Familie nur die beste Variante
        members = [n for n in family if n in chosen]
        for n in members:
            if n != max(members, key=lambda m: res[m]["share"][0]):
                chosen.discard(n)
    tactics, sets = [], []
    for name in ORDER:
        if name not in chosen:
            continue
        for s in SWITCHES[name]:
            if s.startswith("t:"):
                if s[2:] not in tactics:
                    tactics.append(s[2:])
            else:
                sets.append(s)
    if tactics:
        sets.append("imit_tactics=" + "+".join(tactics))
    return [n for n in ORDER if n in chosen], sets


def main() -> None:
    frames = {n: load(str(D / f"{n.lower()}_devH.csv")) for n in ORDER if (D / f"{n.lower()}_devH.csv").is_file()}
    print("| Agent | Solution | Kaggle | Matches gegen Kaggle | Punkteanteil gegen Kaggle | Punkte je Match gegen Kaggle (wir / Kaggle) |")
    print("|---|---:|---:|---:|---:|---:|")
    for name, f in frames.items():
        s, k = f[f.opp == "solution92"], f[f.opp == "kaggle3"]
        ours, theirs = k.our_points.sum(), k.opp_points.sum()
        print(f"| {name} | {int(s.game_win.sum())}/{len(s)} | {int(k.game_win.sum())}/{len(k)} | "
              f"{int(k.our_wins.sum())}/{3 * len(k)} | {100 * ours / max(ours + theirs, 1):.1f} % | "
              f"{ours / (3 * len(k)):.0f} / {theirs / (3 * len(k)):.0f} |")
    if "K" not in frames:
        return
    res = {n: evaluate(f, frames["K"]) for n, f in frames.items() if n != "K"}
    print("\nGepaart gegen K (Prozentpunkte, 95-%-Kartenintervall):")
    print("| Agent | Punkteanteil Kaggle | Spiele Solution | Spiele Solution + Kaggle | Spiele Kaggle | hilft |")
    print("|---|---:|---:|---:|---:|---|")
    for n, r in res.items():
        print(f"| {n} | {cell(r['share'])} | {cell(r['sol'])} | {cell(r['both'])} | {cell(r['kag'])} | "
              f"{'ja' if r['helps'] else 'nein'} |")
    missing = [n for n in SINGLE + ("ALLE",) if n not in res]
    if missing:
        print(f"\nNoch nicht gespielt: {', '.join(missing)}")
        return
    helpers = [n for n in SINGLE if res[n]["helps"]]
    mods, sets = beast(helpers, res)
    print(f"\nHelfende Module: {', '.join(helpers) or 'keine'}")
    if not mods:
        if res["ALLE"]["helps"]:
            print("Kandidat für Bestätigung 5: ALLE")
        else:
            print("Nichts hilft: keine Bestätigung, K bleibt empfohlen.")
        return
    if len(mods) == 1:
        print(f"Kandidat für Bestätigung 5: {mods[0]} ({' '.join('--set ' + s for s in sets)})")
        return
    print(f"Beast = K + {' + '.join(mods)}: {' '.join('--set ' + s for s in sets)}")
    if "BEAST" not in res:
        print("Beast muss noch einmal auf Dev H spielen (beast_devH.csv).")
        return
    if res["BEAST"]["helps"]:
        print("Beast hilft auch als Kombination: Kandidat für Bestätigung 5 ist BEAST.")
    else:
        best = max(mods, key=lambda n: res[n]["share"][0])
        print(f"Beast hilft als Kombination nicht: Kandidat für Bestätigung 5 ist {best}.")


if __name__ == "__main__":
    main()
