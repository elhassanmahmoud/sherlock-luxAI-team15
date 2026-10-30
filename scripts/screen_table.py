"""Dev-A-Screens nebeneinander (Plan docs/superpowers/plans/2026-10-29-battle-push.md, Nachtraege 29.10., 23:55
und 30.10.): Siegquote je Gegner, Mittel ueber die 6 Gegner gepaart gegen V10 und gegen den Massstab
(Standard mix36b) auf denselben Karten, Direktduell gegen V10. Wertet nur vorhandene CSVs von
scripts/battle_screen.sh aus und spielt nichts. Ausgabe als Markdown-Tabelle.

    python -m scripts.screen_table mix36b mix36c mixrl36 mixrl54 mix30v8 mix48 [--base mix36b]
    python -m scripts.screen_table --admit mix36c mixrl36 mixrl54 mix30v8 mix48   (Zulassung Runde 2)
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.league_gates import direct_result, panel_delta

DIR = Path("experiments/compare/battle")
R = "self:experiments/releases"
SIX = {  # die 6 Gegner des Screens in Tabellenreihenfolge
    "solution92": "Sol92",
    "sol92_sq": "sq",
    f"{R}/20261022_all18_v3/agent_p0.pth": "V3",
    f"{R}/20261022_v7_Bsnpd/agent_p0.pth": "V7",
    "self:experiments/ensembles/league_nets6.pth": "league6",
    "self:experiments/ensembles/threat6.pth": "threat6",
}


def screen(name: str, d: Path = DIR) -> pd.DataFrame | None:
    """Alle Spiele eines Screens gegen die 6 Gegner; None, solange ein Teil fehlt."""
    parts = (("B_V10_dev800", "B_V10_rl", "B_V10_hold") if name == "V10"
             else tuple(f"D_{name}{s}" for s in ("", "_rl", "_hold")))
    files = [d / f"{p}.csv" for p in parts]
    if not all(f.exists() for f in files):
        return None
    df = pd.concat([pd.read_csv(f) for f in files])
    return df[df["opponent"].isin(SIX)]


def _pct(x: float) -> str:
    return f"{x * 100:.1f}"


def _delta(p: dict) -> str:
    return f"{p['delta'] * 100:+.2f} [{p['low'] * 100:+.2f}; {p['high'] * 100:+.2f}]"


def table(names: list[str], base: str = "mix36b", d: Path = DIR) -> list[str]:
    ref, ref_base = screen("V10", d), screen(base, d)
    if ref is None:
        raise SystemExit("V10-Basis fehlt (bash scripts/battle_screen.sh V10)")
    lines = ["| Kandidat | " + " | ".join(SIX.values()) + f" | Mittel 6 | Δ V10 | Δ {base} | direkt V10 |",
             "|---" * (len(SIX) + 5) + "|"]
    for name in ["V10", *names]:
        cand = screen(name, d)
        if cand is None:
            lines.append(f"| {name} | " + " | ".join(["fehlt"] * (len(SIX) + 4)) + " |")
            continue
        rates = cand.groupby("opponent")["result"].mean()
        p = panel_delta(cand, ref, panel=tuple(SIX))
        cells = [_pct(rates[o]) for o in SIX] + [_pct(p["winrate"])]
        cells.append(_delta(p) if name != "V10" else "–")
        same = ref_base is None or name in ("V10", base)
        cells.append("–" if same else _delta(panel_delta(cand, ref_base, panel=tuple(SIX))))
        direct = d / f"D_{name}_direct.csv"
        if name != "V10" and direct.exists():
            r = direct_result(pd.read_csv(direct))
            cells.append(f"{_pct(r['winrate'])} [{_pct(r['low'])}; {_pct(r['high'])}]")
        else:
            cells.append("–")
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return lines


def admitted(names: list[str], base: str = "mix36b", k: int = 3, d: Path = DIR) -> list[str]:
    """Zulassung zur Auswahl Runde 2 (Plan-Nachtrag 30.10., 04:09): Mittel ueber die 6 Gegner und Direktduell
    gegen V10 jeweils mindestens wie beim Massstab (Punktschaetzungen); hoechstens k mit dem hoechsten Mittel."""
    score = {}
    for name in [base, *names]:
        cand, direct = screen(name, d), d / f"D_{name}_direct.csv"
        if cand is None or not direct.exists():
            raise SystemExit(f"Screen von {name} unvollstaendig")
        score[name] = (cand["result"].mean(), direct_result(pd.read_csv(direct))["winrate"])
    ok = [n for n in names if score[n][0] >= score[base][0] and score[n][1] >= score[base][1]]
    return sorted(ok, key=lambda n: -score[n][0])[:k]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="+")
    ap.add_argument("--base", default="mix36b", help="Massstab fuer den gepaarten Vergleich")
    ap.add_argument("--dir", type=Path, default=DIR)
    ap.add_argument("--admit", action="store_true", help="nur die zugelassenen Kandidaten ausgeben")
    args = ap.parse_args()
    if args.admit:
        print(" ".join(admitted(args.names, args.base, d=args.dir)) or "keine")
        return
    print("\n".join(table(args.names, args.base, args.dir)))


if __name__ == "__main__":
    main()
