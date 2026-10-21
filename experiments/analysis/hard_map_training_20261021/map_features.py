"""Karten-Eigenschaften aus dem wahren Startzustand (nur Analyse, kein Agentenwissen).

Fuer jede Karte der Kartensuche: Relic-Paare (Spawn-Match/-Step), Lage zur Diagonale und zu
beiden Spawns, Zahl der Punkte-Tiles je Haelfte, dazu die Ergebnisse von V3 auf beiden Seiten.

    .venv/bin/python experiments/analysis/hard_map_training_20261021/map_features.py 360000 361999 OUT.csv
"""
import csv
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def features(seed: int) -> dict:
    from luxai_s3.wrappers import LuxAIS3GymEnv
    env = LuxAIS3GymEnv(numpy_output=True)
    _, info = env.reset(seed=seed)
    st = env.state
    rel = np.asarray(st.relic_nodes)
    sched = np.asarray(st.relic_spawn_schedule)
    cfgs = np.asarray(st.relic_node_configs)
    W = 24
    pairs = []
    pt = np.zeros((W, W), dtype=bool)
    for i in range(len(rel)):
        if sched[i] < 0:
            continue
        x, y = int(rel[i][0]), int(rel[i][1])
        m = cfgs[i]
        for dx in range(5):
            for dy in range(5):
                if m[dx, dy]:
                    tx, ty = x + dx - 2, y + dy - 2
                    if 0 <= tx < W and 0 <= ty < W:
                        pt[tx, ty] = True
        if x + y <= W - 1:  # Haelfte von player_0 (Spiegelpartner liegt in der anderen)
            pairs.append((x, y, int(sched[i])))
    xs, ys = np.indices((W, W))
    d0 = xs + ys                      # Manhattan zu (0, 0)
    d1 = (W - 1 - xs) + (W - 1 - ys)  # zu (23, 23)
    diag = np.abs(xs + ys - (W - 1))  # Abstand zur Spiegelachse (in Manhattan-Schritten)
    out = dict(seed=seed, pairs=len(pairs), pt_total=int(pt.sum()),
               pt_near_diag=int((pt & (diag <= 3)).sum()),
               pt_half0=int((pt & (xs + ys < W - 1)).sum()), pt_diag=int((pt & (xs + ys == W - 1)).sum()),
               min_pair_diag=min((abs(x + y - (W - 1)) for x, y, _ in pairs), default=-1),
               first_spawn_step=min((s for _, _, s in pairs), default=-1),
               last_spawn_match=max((s // 101 for _, _, s in pairs), default=-1),
               # Wettlauf: Abstand der naechsten Punkte-Tiles zu beiden Spawns
               near0=int(d0[pt].min()) if pt.any() else -1, near1=int(d1[pt].min()) if pt.any() else -1,
               sap_cost=int(info["full_params"]["unit_sap_cost"]),
               sap_range=int(info["full_params"]["unit_sap_range"]),
               dropoff=float(info["full_params"]["unit_sap_dropoff_factor"]),
               void=float(info["full_params"]["unit_energy_void_factor"]),
               move_cost=int(info["full_params"]["unit_move_cost"]),
               sensor=int(info["full_params"]["unit_sensor_range"]),
               nebula_red=int(info["full_params"]["nebula_tile_energy_reduction"]))
    env.close()
    return out


def main():
    a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with mp.get_context("spawn").Pool(4) as pool:
        rows = pool.map(features, range(a, b + 1), chunksize=25)
    res = {}
    src = ROOT / "experiments/compare/regeln/H21_screen_v3_360000.csv"
    for r in csv.DictReader(open(src, newline="")):
        res.setdefault(int(r["seed"]), {})[r["side"]] = (float(r["result"]), int(r["our_points"]), int(r["opp_points"]))
    for row in rows:
        s = res.get(row["seed"], {})
        for side, k in (("player_0", "p0"), ("player_1", "p1")):
            if side in s:
                row[f"{k}_result"], row[f"{k}_pts"], row[f"{k}_opp_pts"] = s[side]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} Karten -> {out}")


if __name__ == "__main__":
    main()
