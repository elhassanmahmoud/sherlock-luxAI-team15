"""Kandidat gegen V11 auf Dev A je verstecktem Parameter (gepaart, gleiche Karten/Seiten/Gegner)."""
import sys
import pandas as pd
R = "/Users/elhassanmahmoud/Documents/AKI_LuxAgent15/"
mp = pd.read_csv(R + "experiments/analysis/battle_params_20261030/map_params.csv")
base = pd.read_csv(R + "experiments/compare/battle/D_mix36c_as.csv")
cand = pd.read_csv(sys.argv[1])
j = cand.merge(base, on=["seed", "side", "opponent"], suffixes=("", "_v11")).merge(mp, on="seed")
j["d"] = j["result"] - j["result_v11"]
for col in ("unit_sap_dropoff_factor", "unit_sap_range", "unit_sensor_range", "pairs"):
    t = j.groupby(["opponent", col]).agg(n=("d", "size"), cand=("result", "mean"), v11=("result_v11", "mean"), delta=("d", "mean"))
    t[["cand", "v11", "delta"]] *= 100
    print(t.round(1).to_string()); print()
print("geaenderte Spiele:", int((j.d != 0).sum()), "von", len(j))
