"""Varianten gegen eine Referenz vergleichen (15.11.2026): Spiele, Matches, Punkteanteil.

Gepaarter Bootstrap ueber Karten (beide Seiten einer Karte zusammen), nur gemeinsame Karten je Gegner.
Gegen sehr starke Gegner sind ganze Siege selten; Matchanteil und Punkteanteil zeigen Fortschritt frueher.
Keine Korrektur fuer Mehrfachvergleiche: Auswahl auf einem Satz, Bestaetigung auf frischen Karten.

    python -m scripts.variant_compare --ref screen1/baseline.csv screen1/*.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

B = 4000


def per_map(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["matches"] = df["our_wins"] + df["opp_wins"]
    g = df.groupby(["opponent", "seed"]).agg(
        games=("result", "size"), wins=("game_win", "sum"), result=("result", "sum"),
        our_m=("our_wins", "sum"), all_m=("matches", "sum"),
        our_p=("our_points", "sum"), opp_p=("opp_points", "sum"))
    return g[g["games"] == 2]


def boot(diff: np.ndarray, rng) -> tuple[float, float]:
    idx = rng.integers(0, len(diff), size=(B, len(diff)))
    m = diff[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("csvs", nargs="+")
    a = ap.parse_args()
    ref = per_map(pd.read_csv(a.ref))
    rng = np.random.default_rng(0)
    print(f"{'Variante':<24}{'Gegner':<11}{'Karten':>6}{'Spiele gew.':>13}{'Δ Spiele pp [95%]':>24}"
          f"{'Matches':>9}{'Δ Matches pp [95%]':>24}{'Punkte':>8}{'Δ Punkte pp':>13}")
    for path in a.csvs:
        if Path(path).resolve() == Path(a.ref).resolve():
            continue
        var = per_map(pd.read_csv(path))
        for opp in sorted(set(var.index.get_level_values(0)) & set(ref.index.get_level_values(0))):
            r, v = ref.loc[opp], var.loc[opp]
            common = r.index.intersection(v.index)
            r, v = r.loc[common], v.loc[common]
            n = len(common)
            gw_r, gw_v = r["result"].to_numpy() / 2, v["result"].to_numpy() / 2
            m_r = r["our_m"].to_numpy() / r["all_m"].to_numpy()
            m_v = v["our_m"].to_numpy() / v["all_m"].to_numpy()
            p_r = r["our_p"].to_numpy() / np.maximum(r["our_p"] + r["opp_p"], 1).to_numpy()
            p_v = v["our_p"].to_numpy() / np.maximum(v["our_p"] + v["opp_p"], 1).to_numpy()
            dg, dm = gw_v - gw_r, m_v - m_r
            lo_g, hi_g = boot(dg, rng)
            lo_m, hi_m = boot(dm, rng)
            print(f"{Path(path).stem:<24}{opp:<11}{n:>6}{100 * gw_v.mean():>12.1f}%"
                  f"{100 * dg.mean():>+9.1f} [{100 * lo_g:+.1f}; {100 * hi_g:+.1f}]"
                  f"{100 * m_v.mean():>8.1f}%{100 * dm.mean():>+9.1f} [{100 * lo_m:+.1f}; {100 * hi_m:+.1f}]"
                  f"{100 * p_v.mean():>7.1f}%{100 * (p_v - p_r).mean():>+12.1f}")


if __name__ == "__main__":
    main()
