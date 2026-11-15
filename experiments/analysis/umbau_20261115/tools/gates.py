"""Hürden aus docs/superpowers/plans/2026-11-15-umbau-imitation.md auf dem Bestätigungssatz auswerten (15.11.2026).

    python experiments/analysis/umbau_20261115/tools/gates.py \
        experiments/analysis/umbau_20261115/confirm/v14_ref.csv experiments/analysis/umbau_20261115/confirm/v15_candidate.csv

Gepaarter Bootstrap über Karten (beide Seiten einer Karte zusammen), 10.000 Ziehungen, Seed 2711.
Im Direktduell sind die relativen par_eval-Pfade agents/sherlock/weights/agent_p0.pth oder
agent_p1.pth erlaubt. Beide bezeichnen V14. Absolute Pfade müssen hier lesbar sein und dessen
SHA-256 ergeben. Die CSV enthält nur den Gegnernamen; der Gewichtsstand beim Spiel braucht
zusätzlich das Laufprotokoll.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys

import numpy as np
import pandas as pd

B, SEED = 10_000, 2711

EXTERNAL = ("kaggle3", "solution92", "default")
MAPS = range(7158000, 7158400)
SEATS = ("player_0", "player_1")
V14_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
V14_PATHS = {Path("agents/sherlock/weights") / f"agent_p{side}.pth" for side in (0, 1)}


def opponent_key(label):
    """Relative opponent labels are the ones emitted by par_eval. Verify portable absolute aliases by bytes."""
    if isinstance(label, str) and label.startswith("self:"):
        path = Path(label[5:])
        if path in V14_PATHS:
            return "self:V14"
        if (path.is_absolute() and Path(*path.parts[-4:]) in V14_PATHS and path.is_file()
                and sha256(path.read_bytes()).hexdigest() == V14_SHA):
            return "self:V14"
    if label not in EXTERNAL:
        raise ValueError(f"Unbekannter Gegner oder fremder V14-Pfad: {label!r}")
    return label


def validate_panel(df, *, candidate):
    role = "Kandidat" if candidate else "Referenz"
    opponents = (*EXTERNAL, "self:V14") if candidate else EXTERNAL
    required = {"opponent","seed","side","steps","result","our_wins","opp_wins","our_points","opp_points"}
    if missing := required.difference(df.columns):
        raise ValueError(f"{role}: Fehlende CSV-Spalten {sorted(missing)}")
    labels = {v: opponent_key(v) for v in df["opponent"].drop_duplicates()}
    keys = pd.MultiIndex.from_arrays([df["opponent"].map(labels), df["seed"], df["side"]])
    expected = pd.MultiIndex.from_product([opponents, MAPS, SEATS])
    if not keys.is_unique or len(keys) != len(expected) or not keys.isin(expected).all():
        raise ValueError(f"{role}: Unvollständiger, doppelter oder fremder Gegner/Karten/Sitz-Schlüssel")
    wins, losses = df["our_wins"], df["opp_wins"]
    if (not (df["steps"].eq(303) & wins.isin(range(4)) & losses.isin(range(4))).all()
            or not ((wins + losses).eq(3) & df["result"].eq(wins.gt(losses).astype(int))).all()):
        raise ValueError(f"{role}: Jeder Lauf braucht 303 Schritte, drei Matches und den passenden Spielausgang")
    for name in ("our_points", "opp_points"):
        v = pd.to_numeric(df[name], errors="coerce")
        if not (v.ge(0) & v.mod(1).eq(0)).all():
            raise ValueError(f"{role}: Ungültige Feldpunktzahl in {name}")


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
    validate_panel(ref, candidate=False)
    validate_panel(cand, candidate=True)
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
