"""Kandidat gegen V12 je verstecktem Kartenparameter, gepaart auf denselben Karten/Seiten/Gegnern (31.10.2026).

Mittel ueber die 6 Gegner des Battle-Screens; Grundlage sind nur vorhandene CSVs, es wird nichts gespielt.

    PYTHONPATH=. .venv/bin/python experiments/analysis/battle/v13_by_param.py dev NAME
        Dev-A-Screen: experiments/compare/battle/D_NAME*.csv gegen D_v12*.csv
    PYTHONPATH=. .venv/bin/python experiments/analysis/battle/v13_by_param.py conf NAME PARAMS.csv
        Battle-Bestaetigung: GD_NAME_conf.csv gegen GD_V12_conf.csv (PARAMS.csv aus map_params.py)
"""
import sys

import pandas as pd

from scripts.screen_table import SIX, screen

D = "experiments/compare/battle"
DEV_PARAMS = "experiments/analysis/battle_params_20261030/map_params.csv"


def main():
    mode, name = sys.argv[1], sys.argv[2]
    if mode == "dev":
        cand, base, params = screen(name), screen("v12"), DEV_PARAMS
    else:
        cand, base, params = pd.read_csv(f"{D}/GD_{name}_conf.csv"), pd.read_csv(f"{D}/GD_V12_conf.csv"), sys.argv[3]
        cand, base = cand[cand["opponent"].isin(SIX)], base[base["opponent"].isin(SIX)]
    mp = pd.read_csv(params)
    j = cand.merge(base, on=["seed", "side", "opponent"], suffixes=("", "_v12")).merge(mp, on="seed")
    j["d"] = j["result"] - j["result_v12"]
    print(f"{name} gegen V12, {len(j)} Spiele auf {j['seed'].nunique()} Karten, "
          f"veraendertes Ergebnis in {int((j['d'] != 0).sum())} Spielen")
    for col, label in (("unit_sensor_range", "Sichtweite"), ("unit_sap_dropoff_factor", "Streufaktor")):
        t = j.groupby(col).agg(spiele=("d", "size"), kandidat=("result", "mean"), v12=("result_v12", "mean"),
                               delta=("d", "mean"))
        t[["kandidat", "v12", "delta"]] *= 100
        print(f"\nnach {label} (Siegquote in %, Δ in pp):")
        print(t.round(2).to_string())
    t = j.groupby("opponent").agg(kandidat=("result", "mean"), v12=("result_v12", "mean"), delta=("d", "mean"))
    t.index = [SIX[o] for o in t.index]
    print("\nje Gegner:")
    print((t * 100).round(2).to_string())
    for col in ("sap_attempts", "sap_hits", "our_points", "opp_points"):
        if col in j:
            print(f"{col}: Kandidat {j[col].mean():.1f}, V12 {j[col + '_v12'].mean():.1f} je Spiel")


if __name__ == "__main__":
    main()
