"""Spielparameter und Relic-Lage je Karten-Seed (nur env.reset, kein Spiel) -> CSV.

    .venv/bin/python experiments/analysis/battle_params_20261030/map_params.py OUT.csv 800000:800300 ...
"""
import sys

import numpy as np
import pandas as pd
from luxai_s3.wrappers import LuxAIS3GymEnv

KEEP = ["unit_move_cost", "unit_sensor_range", "nebula_tile_vision_reduction", "nebula_tile_energy_reduction",
        "unit_sap_cost", "unit_sap_range", "unit_sap_dropoff_factor", "unit_energy_void_factor",
        "nebula_tile_drift_speed", "energy_node_drift_speed", "energy_node_drift_magnitude"]


def main():
    out, ranges = sys.argv[1], sys.argv[2:]
    env = LuxAIS3GymEnv(numpy_output=True)
    rows = []
    for r in ranges:
        a, b = (int(v) for v in r.split(":"))
        for seed in range(a, b):
            _, info = env.reset(seed=seed)
            p, st = info["full_params"], env.state
            row = dict(seed=seed, **{k: p[k] for k in KEEP})
            sched = np.asarray(st.relic_spawn_schedule)
            nodes = np.asarray(st.relic_nodes)
            half = len(sched) // 2
            live = [i for i in range(half) if sched[i] != -1]
            row["pairs"] = len(live)
            # Abstand zur Symmetrieachse x + y = 23 (0 = Relic liegt auf der Achse, gleich weit von beiden Starts)
            axis = [abs(int(nodes[i][0]) + int(nodes[i][1]) - 23) for i in live]
            row["min_axis"] = min(axis)
            row["axis_relics"] = sum(a <= 2 for a in axis)
            # Abstand vom eigenen Start (0,0) zur naechsten der beiden Relics jedes Paares (Manhattan)
            near = [min(int(nodes[i][0]) + int(nodes[i][1]), 46 - int(nodes[i][0]) - int(nodes[i][1])) for i in live]
            row["near_first"] = near[0]
            row["spawn_first"] = int(sched[live[0]])
            row["spawn_steps"] = ";".join(str(int(sched[i])) for i in live)
            row["relic_xy"] = ";".join(f"{int(nodes[i][0])}-{int(nodes[i][1])}" for i in live)
            tiles = np.asarray(st.map_features.tile_type)
            row["nebula_frac"] = float((tiles == 1).mean())
            row["asteroid_frac"] = float((tiles == 2).mean())
            rows.append(row)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(len(rows), "Karten")


if __name__ == "__main__":
    main()
