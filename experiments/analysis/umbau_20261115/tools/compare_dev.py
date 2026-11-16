"""Gepaarter Vergleich mehrerer Agenten auf denselben Entwicklungskarten (16.11.2026).

    python experiments/analysis/umbau_20261115/tools/compare_dev.py \
        --ref R3=experiments/analysis/umbau_20261115/v5/r3_devA.csv \
        V15=experiments/analysis/kaggle3_20261115/student_hyb_v4_mixed.csv \
        HYB_V5=experiments/analysis/umbau_20261115/v5/hyb_v5_mixed_devA.csv

Jede CSV stammt aus scripts.par_eval (ein Agent, mehrere Gegner). Gegnernamen werden vereinheitlicht:
`r3zip:...` -> R3, `self:...agent_p0.pth` -> V14, sonst unverändert. Ausgabe je Agent und Gegner: gewonnene
Spiele und Matches; dazu für jeden Agenten die gepaarte Differenz zur Referenz (gleiche Karten, beide Sitze
gemeinsam gezogen, 10.000 Ziehungen, Seed 2711) und über Solution+Kaggle zusammen.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

B, SEED = 10_000, 2711
EXTERNAL = ("solution92", "kaggle3")


def opponent_name(label: str) -> str:
    if label.startswith("r3zip:"):
        return "R3"
    if label.startswith("self:") and Path(label[5:]).name in ("agent_p0.pth", "agent_p1.pth"):
        return "V14"
    if label.startswith("self:") and "v15_candidate" in label:
        return "V15"
    return label


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["opp"] = df["opponent"].map(opponent_name)
    bad = ~(df["steps"].eq(303) & (df["our_wins"] + df["opp_wins"]).eq(3))
    if bad.any():
        raise ValueError(f"{path}: {int(bad.sum())} unvollständige Spiele")
    if df.duplicated(["opp", "seed", "side"]).any():
        raise ValueError(f"{path}: doppelte Spiele")
    return df


def boot(diff_by_map: np.ndarray, rng) -> tuple[float, float]:
    idx = rng.integers(0, len(diff_by_map), size=(B, len(diff_by_map)))
    m = diff_by_map[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def paired(a: pd.DataFrame, b: pd.DataFrame, opps) -> tuple[int, float, float, float, int, int] | None:
    """Mittlere Differenz der Spielsiege a-b je Karte (beide Sitze, alle opps gemeinsam), in Prozentpunkten."""
    ka = a[a["opp"].isin(opps)].set_index(["opp", "seed", "side"])["game_win"]
    kb = b[b["opp"].isin(opps)].set_index(["opp", "seed", "side"])["game_win"]
    common = ka.index.intersection(kb.index)
    if len(common) == 0:
        return None
    d = (ka.loc[common] - kb.loc[common]).groupby(level="seed").mean()
    full = ka.loc[common].groupby(level="seed").size() == 2 * len(opps)
    d = d[full[full].index]
    if len(d) == 0:
        return None
    lo, hi = boot(d.to_numpy(), np.random.default_rng(SEED))
    gained = int(((ka.loc[common] == 1) & (kb.loc[common] == 0)).sum())
    lost = int(((ka.loc[common] == 0) & (kb.loc[common] == 1)).sum())
    return len(d), 100 * float(d.mean()), 100 * lo, 100 * hi, gained, lost


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, help="NAME der Referenz (muss unter den Agenten sein)")
    ap.add_argument("agents", nargs="+", help="NAME=CSV (mehrere CSVs je Name mit Komma)")
    a = ap.parse_args()
    frames = {}
    for spec in a.agents:
        name, paths = spec.split("=", 1)
        frames[name] = pd.concat([load(p) for p in paths.split(",")], ignore_index=True)
    ref = frames[a.ref]
    opps = sorted({o for f in frames.values() for o in f["opp"].unique()})
    print("| Agent | " + " | ".join(opps) + " |")
    print("|---|" + "---:|" * len(opps))
    for name, f in frames.items():
        cells = []
        for o in opps:
            g = f[f["opp"] == o]
            cells.append(f"{int(g['game_win'].sum())}/{len(g)} (M {int(g['our_wins'].sum())}/{3 * len(g)})"
                         if len(g) else "–")
        print(f"| {name} | " + " | ".join(cells) + " |")
    print(f"\nGepaarte Differenz der Spielsiege zu {a.ref} (Prozentpunkte, 95-%-Kartenintervall, +gewonnen/−verloren):")
    for name, f in frames.items():
        if name == a.ref:
            continue
        parts = []
        for o in [*EXTERNAL, "EXTERN"]:
            sel = EXTERNAL if o == "EXTERN" else (o,)
            r = paired(f, ref, sel)
            if r:
                n, m, lo, hi, gw, ls = r
                parts.append(f"{o}: {m:+.2f} [{lo:+.2f}; {hi:+.2f}] (+{gw}/−{ls}, {n} Karten)")
        print(f"- {name}: " + "; ".join(parts))


if __name__ == "__main__":
    main()
