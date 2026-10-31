"""Wie oft stehen unsichtbare Gegner auf Punkte-Tiles in unserer Sap-Reichweite? (Analyse 31.10.2026, Gewichte nur lesen)

Je Schritt in Match 2/3: Gegner-Units auf echten Punkte-Tiles (Env-Zustand), davon fuer uns sichtbar/unsichtbar;
je eigene Unit mit Energie >= Sap-Kosten + 30: unsichtbarer Gegner auf Punkte-Tile in Reichweite (und kein sichtbarer
Gegner in Reichweite) bzw. sichtbarer Gegner in Reichweite, und ob sie sappt.

    cd REPO && PYTHONPATH=$PWD:$PWD/experiments/analysis/battle .venv/bin/python -m v11_fog_probe SEEDS(a:b) SENSOR OPP OUT.csv WORKERS
"""
import csv
import random
import sys
from multiprocessing import Pool

import numpy as np

import os
V11 = os.environ.get("PROBE_W", "experiments/releases/20261030_v11_baseline/agent_p0.pth")


def play(job):
    import torch
    torch.set_num_threads(1)
    seed, side, opp_name = job
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent
    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=V11, train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    opp_side = "player_1" if side == "player_0" else "player_0"
    opp = make_opponent(opp_name.split(":")[0], opp_side, opp_name.split(":", 1)[1] if ":" in opp_name else None)
    agent.new_game(side)
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    obs, info = env.reset(seed=seed)
    agent.set_env_cfg(info["params"])
    opp.set_env_cfg(info["params"])
    cost, R = int(info["params"]["unit_sap_cost"]), int(info["params"]["unit_sap_range"])
    us, them = (0, 1) if side == "player_0" else (1, 0)
    acc = dict(enemy_pt_hidden=0, enemy_pt_visible=0, unit_could_hidden=0, unit_could_hidden_sap=0,
               unit_could_visible=0, unit_could_visible_sap=0)
    step, done = 0, False
    while not done:
        o, oo = obs[side], obs[opp_side]
        a_us = np.asarray(agent.act(step=step, obs=o))
        a_op = opp.act(step=step, obs=oo)
        if step >= 101 and int(np.asarray(o["match_steps"])) > 0:
            w = np.asarray(env.state.relic_nodes_map_weights) > 0
            pos_e = np.asarray(oo["units"]["position"])[them]
            ene_e = np.asarray(oo["units"]["energy"])[them]
            ene_e = ene_e[..., 0] if ene_e.ndim == 2 else ene_e
            alive_e = np.asarray(oo["units_mask"])[them] & (ene_e >= 0)
            vis_e = np.asarray(o["units_mask"])[them]
            hid_pt = [(int(p[0]), int(p[1])) for i, p in enumerate(pos_e) if alive_e[i] and not vis_e[i] and w[p[0], p[1]]]
            vis_all = [(int(p[0]), int(p[1])) for i, p in enumerate(pos_e) if alive_e[i] and vis_e[i]]
            acc["enemy_pt_hidden"] += len(hid_pt)
            acc["enemy_pt_visible"] += sum(1 for i, p in enumerate(pos_e) if alive_e[i] and vis_e[i] and w[p[0], p[1]])
            pos = np.asarray(o["units"]["position"])[us]
            ene = np.asarray(o["units"]["energy"])[us]
            ene = ene[..., 0] if ene.ndim == 2 else ene
            for u in np.nonzero(np.asarray(o["units_mask"])[us])[0]:
                if ene[u] < cost + 30:
                    continue
                x, y = int(pos[u][0]), int(pos[u][1])
                vis_in = any(max(abs(ex - x), abs(ey - y)) <= R for ex, ey in vis_all)
                hid_in = any(max(abs(ex - x), abs(ey - y)) <= R for ex, ey in hid_pt)
                sap = int(a_us[u][0]) == 5
                if vis_in:
                    acc["unit_could_visible"] += 1
                    acc["unit_could_visible_sap"] += sap
                elif hid_in:
                    acc["unit_could_hidden"] += 1
                    acc["unit_could_hidden_sap"] += sap
        obs, _, term, trunc, _ = env.step({side: a_us, opp_side: a_op})
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        step += 1
    p = info["full_params"]
    return dict(seed=seed, side=side, opp=opp_name, sensor=int(p["unit_sensor_range"]),
                drop=float(p["unit_sap_dropoff_factor"]), **acc)


if __name__ == "__main__":
    import pandas as pd
    a, b = (int(v) for v in sys.argv[1].split(":"))
    sensor, opp, out = int(sys.argv[2]), sys.argv[3], sys.argv[4]
    mp = pd.read_csv("experiments/analysis/battle_params_20261030/map_params_810400.csv")
    seeds = [int(s) for s in mp.seed[(mp.seed >= a) & (mp.seed < b) & (mp.unit_sensor_range == sensor)]]
    jobs = [(s, side, opp) for s in seeds for side in ("player_0", "player_1")]
    with Pool(int(sys.argv[5]) if len(sys.argv) > 5 else 4) as pool:
        rows = pool.map(play, jobs, chunksize=1)
    with open(out, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print(len(rows), "Spiele ->", out)
