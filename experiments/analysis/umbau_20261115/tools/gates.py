"""Hürden aus docs/superpowers/plans/2026-11-15-umbau-imitation.md auf dem Bestätigungssatz auswerten (15.11.2026).

    python experiments/analysis/umbau_20261115/tools/gates.py \
        experiments/analysis/umbau_20261115/confirm/v14_ref.csv experiments/analysis/umbau_20261115/confirm/v15_candidate.csv

Gepaarter Bootstrap über Karten (beide Seiten einer Karte zusammen), 10.000 Ziehungen, Seed 2711.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

B, SEED = 10_000, 2711


def per_map(df: pd.DataFrame, opp_prefix: str) -> pd.DataFrame:
    d = df[df["opponent"].str.startswith(opp_prefix)]
    g = d.groupby("seed").agg(n=("result", "size"), res=("result", "mean"), our_m=("our_wins", "sum"),
                              opp_m=("opp_wins", "sum"), our_p=("our_points", "sum"), opp_p=("opp_points", "sum"))
    return g[g["n"] == 2]


def boot_mean(x: np.ndarray, rng) -> tuple[float, float]:
    idx = rng.integers(0, len(x), size=(B, len(x)))
    m = x[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main(ref_path: str, cand_path: str) -> None:
    ref, cand = pd.read_csv(ref_path), pd.read_csv(cand_path)
    rng = np.random.default_rng(SEED)
    rows, passed = [], {}

    # 1) kaggle3: Spielsiege höher als V14, untere Grenze > 0
    r, c = per_map(ref, "kaggle3"), per_map(cand, "kaggle3")
    common = r.index.intersection(c.index)
    diff = (c.loc[common, "res"] - r.loc[common, "res"]).to_numpy()
    lo, hi = boot_mean(diff, rng)
    m_r = (r.loc[common, "our_m"] / (r.loc[common, "our_m"] + r.loc[common, "opp_m"])).to_numpy()
    m_c = (c.loc[common, "our_m"] / (c.loc[common, "our_m"] + c.loc[common, "opp_m"])).to_numpy()
    mlo, mhi = boot_mean(m_c - m_r, rng)
    passed[1] = diff.mean() > 0 and lo > 0
    rows.append(f"1 kaggle3 ({len(common)} Karten): V14 {100 * r.loc[common, 'res'].mean():.2f} %, Kandidat "
                f"{100 * c.loc[common, 'res'].mean():.2f} %, Δ {100 * diff.mean():+.2f} pp [{100 * lo:+.2f}; {100 * hi:+.2f}]"
                f" | Matches {100 * m_r.mean():.2f} → {100 * m_c.mean():.2f} %, Δ {100 * (m_c - m_r).mean():+.2f} pp "
                f"[{100 * mlo:+.2f}; {100 * mhi:+.2f}] -> {'bestanden' if passed[1] else 'verfehlt'}")

    # 2) solution92: höchstens 3 pp schlechter als V14 (Punktschätzer)
    r, c = per_map(ref, "solution92"), per_map(cand, "solution92")
    common = r.index.intersection(c.index)
    diff = (c.loc[common, "res"] - r.loc[common, "res"]).to_numpy()
    lo, hi = boot_mean(diff, rng)
    passed[2] = diff.mean() >= -0.03
    rows.append(f"2 solution92 ({len(common)} Karten): V14 {100 * r.loc[common, 'res'].mean():.2f} %, Kandidat "
                f"{100 * c.loc[common, 'res'].mean():.2f} %, Δ {100 * diff.mean():+.2f} pp [{100 * lo:+.2f}; {100 * hi:+.2f}]"
                f" -> {'bestanden' if passed[2] else 'verfehlt'}")

    # 3) direkt gegen V14: > 50 %, untere Grenze > 50 %
    c = per_map(cand, "self:")
    x = c["res"].to_numpy()
    lo, hi = boot_mean(x, rng)
    passed[3] = x.mean() > 0.5 and lo > 0.5
    rows.append(f"3 direkt gegen V14 ({len(c)} Karten): {100 * x.mean():.2f} % [{100 * lo:.2f}; {100 * hi:.2f}], "
                f"Matches {int(c['our_m'].sum())}:{int(c['opp_m'].sum())} -> {'bestanden' if passed[3] else 'verfehlt'}")

    # 4) default: mindestens 98 %
    c = per_map(cand, "default")
    r = per_map(ref, "default")
    passed[4] = c["res"].mean() >= 0.98
    rows.append(f"4 default ({len(c)} Karten): Kandidat {100 * c['res'].mean():.2f} % (V14 {100 * r['res'].mean():.2f} %)"
                f" -> {'bestanden' if passed[4] else 'verfehlt'}")

    print("\n".join(rows))
    print("Hürden 1-4:", ", ".join(f"{k}: {'ja' if v else 'nein'}" for k, v in passed.items()),
          "| Hürde 5 (Technik) wird getrennt geprüft.")


if __name__ == "__main__":
    main(*sys.argv[1:3])
