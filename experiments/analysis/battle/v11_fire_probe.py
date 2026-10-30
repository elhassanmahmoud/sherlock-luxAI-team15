"""Koennten unsere Units oefter sappen? (Analyse 30.10.2026, Gewichte nur lesen)

Je Schritt (Match 2/3): Units mit Energie >= Sap-Kosten und mindestens einem sichtbaren Gegner im Sap-Quadrat
("koennte"), davon tatsaechlich Sap, davon Halter auf Punkte-Tile, und was die uebrigen stattdessen tun.

    cd REPO && PYTHONPATH=REPO:DIESER_ORDNER .venv/bin/python -m fire_probe GAMES.csv OPP OUT.csv WORKERS
"""
import csv
import random
import sys
from multiprocessing import Pool

import numpy as np

V11 = "experiments/releases/20261030_v11_baseline/agent_p0.pth"


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
    opp = make_opponent(opp_name, opp_side)
    agent.new_game(side)
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    obs, info = env.reset(seed=seed)
    agent.set_env_cfg(info["params"])
    opp.set_env_cfg(info["params"])
    cost, R = int(info["params"]["unit_sap_cost"]), int(info["params"]["unit_sap_range"])
    us = 0 if side == "player_0" else 1
    acc = dict(could=0, did=0, could_holder=0, did_holder=0, could_stay=0, could_move=0, opp_sap=0)
    step, done = 0, False
    while not done:
        o = obs[side]
        a_us = agent.act(step=step, obs=o)
        a_op = opp.act(step=step, obs=obs[opp_side])
        ms = int(np.asarray(o["match_steps"]))
        if step >= 101 and ms > 0:
            pos = np.asarray(o["units"]["position"])
            ene = np.asarray(o["units"]["energy"])
            if ene.ndim == 3:
                ene = ene[..., 0]
            mask = np.asarray(o["units_mask"])
            ep = pos[1 - us][mask[1 - us]]
            pts = agent.belief.point_tiles
            for u in np.nonzero(mask[us])[0]:
                x, y = int(pos[us][u][0]), int(pos[us][u][1])
                if ene[us][u] < cost or not len(ep):
                    continue
                if not (np.maximum(np.abs(ep[:, 0] - x), np.abs(ep[:, 1] - y)) <= R).any():
                    continue
                a = int(np.asarray(a_us)[u][0])
                cx, cy = (x, y) if not agent.belief.mirrored else (23 - y, 23 - x)
                holder = bool(pts[cx, cy])
                acc["could"] += 1
                acc["could_holder"] += holder
                acc["did"] += a == 5
                acc["did_holder"] += (a == 5) and holder
                acc["could_stay"] += a == 0
                acc["could_move"] += 1 <= a <= 4
            acc["opp_sap"] += int((np.asarray(a_op)[:, 0] == 5).sum())
        obs, _, term, trunc, _ = env.step({side: a_us, opp_side: a_op})
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        step += 1
    return dict(seed=seed, side=side, opp=opp_name, drop=float(info["full_params"]["unit_sap_dropoff_factor"]), **acc)


if __name__ == "__main__":
    import pandas as pd
    games = pd.read_csv(sys.argv[1])
    opp, out = sys.argv[2], sys.argv[3]
    jobs = [(int(r.seed), r.side, opp) for r in games.itertuples()]
    with Pool(int(sys.argv[4]) if len(sys.argv) > 4 else 4) as pool:
        rows = pool.map(play, jobs, chunksize=1)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "Spiele ->", out)
