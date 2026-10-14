"""Winraten vergleichen: gepaarter Bootstrap ueber Karten (beide Seiten zusammen).

    python -m scripts.compare_report --ref experiments/compare/full_s0.csv experiments/compare/full_s0_120.csv

WR und Differenz beziehen sich auf dieselben gemeinsamen Karten je Gegner.
5000 Bootstrap-Stichproben, Zufallsseed 0, 95-%-Perzentilintervall fuer die
Differenz. Feste Agenten: keine Unsicherheit ueber Trainingsstarts, keine
Korrektur fuer Mehrfachvergleiche oder wiederholte Modellauswahl.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KEY = ["opponent", "seed", "side"]
SIDES = {"player_0", "player_1"}
BOOTSTRAP_SAMPLES = 5000


def validated_results(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Eine eindeutige, vollstaendige Messung pro Gegner/Karte/Seite verlangen."""
    missing = set(KEY + ["result"]) - set(df.columns)
    if missing:
        raise ValueError(f"{label}: fehlende Spalten {sorted(missing)}")
    if df.empty:
        raise ValueError(f"{label}: keine Spiele")
    df = df[KEY + ["result"]].copy()
    if df.isna().any().any():
        raise ValueError(f"{label}: fehlende Werte")
    if not df["opponent"].map(lambda x: isinstance(x, str) and bool(x.strip())).all():
        raise ValueError(f"{label}: ungueltiger Gegnername")
    if not df["side"].isin(SIDES).all():
        raise ValueError(f"{label}: Spielseite muss player_0 oder player_1 sein")
    for column in ("seed", "result"):
        try:
            df[column] = pd.to_numeric(df[column], errors="raise")
        except (ValueError, TypeError) as error:
            raise ValueError(f"{label}: {column} muss numerisch sein") from error
    seeds = df["seed"]
    if not (np.isfinite(seeds) & (seeds >= 0) & (seeds == np.floor(seeds))).all():
        raise ValueError(f"{label}: Seeds muessen endliche, nichtnegative ganze Zahlen sein")
    if not df["result"].isin([0.0, 0.5, 1.0]).all():
        raise ValueError(f"{label}: result muss 0, 0.5 oder 1 sein")
    if df.duplicated(KEY).any():
        raise ValueError(f"{label}: doppelte Spiele fuer Gegner/Seed/Seite")
    if not df.groupby(["opponent", "seed"]).size().eq(2).all():
        raise ValueError(f"{label}: jede Karte braucht beide Spielseiten")
    return df.sort_values(KEY)


def compare_results(candidate: pd.DataFrame, reference: pd.DataFrame) -> list[dict]:
    """Gepaarter Vergleich auf gemeinsamen vollstaendigen Karten je Gegner."""
    candidate = validated_results(candidate, "Kandidat")
    reference = validated_results(reference, "Referenz")
    rows = []
    for opponent, group in candidate.groupby("opponent", sort=True):
        ref = reference[reference["opponent"] == opponent]
        paired = group.merge(ref, on=KEY, suffixes=("_candidate", "_reference"),
                             validate="one_to_one")
        if paired.empty:
            raise ValueError(f"{opponent}: keine gemeinsamen Karten mit der Referenz")
        # Erst nach Gegner, Seed UND Seite paaren. Danach beide Seiten einer
        # Karte mitteln. Resampling dieser Kartenmittel ist exakt dasselbe
        # wie das gemeinsame Ziehen der zwei zugehoerigen Spielzeilen.
        maps = paired.groupby("seed", sort=True)[["result_candidate", "result_reference"]].mean()
        differences = (maps["result_candidate"] - maps["result_reference"]).to_numpy()
        n_maps = len(maps)
        low = high = None
        if n_maps >= 2:
            # Pro Vergleich neu starten: unabhaengig von CSV-/Zeilenreihenfolge.
            rng = np.random.default_rng(0)
            samples = rng.choice(differences, size=(BOOTSTRAP_SAMPLES, n_maps), replace=True)
            low, high = map(float, np.percentile(samples.mean(axis=1), [2.5, 97.5]))
        rows.append(dict(
            opponent=opponent, maps=n_maps, games=2 * n_maps,
            winrate=float(maps["result_candidate"].mean()),
            ref_winrate=float(maps["result_reference"].mean()),
            delta=float(differences.mean()), low=low, high=high,
            excluded_candidate=int(group["seed"].nunique()) - n_maps,
            excluded_reference=int(ref["seed"].nunique()) - n_maps,
        ))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", required=True)
    ap.add_argument("csvs", nargs="+")
    args = ap.parse_args()

    def load(path):
        try:
            return validated_results(pd.read_csv(path), str(path))
        except (OSError, ValueError) as error:
            ap.error(f"{path}: {error}")

    ref = load(args.ref)
    reports = []
    # Erst alle Eingaben pruefen, damit ein abgebrochener Aufruf keinen
    # scheinbar vollstaendigen Teilbericht hinterlaesst.
    for path in args.csvs:
        try:
            rows = compare_results(load(path), ref)
        except ValueError as error:
            ap.error(f"{path}: {error}")
        reports.append((Path(path).stem, rows))

    print("Gepaarter Karten-Bootstrap: 5000 Wiederholungen, Seed 0; WR/Delta auf gemeinsamen Karten.")
    print("WR = mittleres result (Remis zaehlt halb). Delta/KI in Anteilen: 0.01 = 1 Prozentpunkt.")
    print(f"{'Kandidat':28s} {'Gegner':10s} {'Karten':>6s} {'Spiele':>6s} {'WR':>6s} "
          f"{'Ref-WR':>6s} {'Delta':>7s}  95-%-KI fuer Delta")
    for name, rows in reports:
        for row in rows:
            interval = (f"[{row['low']:+.3f}; {row['high']:+.3f}]" if row["low"] is not None
                        else "nicht schaetzbar (nur 1 Karte)")
            print(f"{name:28s} {row['opponent']:10s} {row['maps']:6d} {row['games']:6d} "
                  f"{row['winrate']:6.3f} {row['ref_winrate']:6.3f} {row['delta']:+7.3f}  {interval}")
            if row["excluded_candidate"] or row["excluded_reference"]:
                print(f"Hinweis {name}/{row['opponent']}: nicht gemeinsam, ausgeschlossen: "
                      f"{row['excluded_candidate']} Kandidatenkarten, "
                      f"{row['excluded_reference']} Referenzkarten.", file=sys.stderr)
    print("Intervalle fuer feste Agenten; keine Korrektur fuer Mehrfachvergleiche/Modellauswahl.")


if __name__ == "__main__":
    main()
