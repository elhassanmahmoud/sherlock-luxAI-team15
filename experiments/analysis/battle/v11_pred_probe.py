"""Trefferquote des Solution_92-Gegnermodells je Gegner (Analyse 30.10.2026, Gewichte nur lesen).

V11 + dodge_distrust (lethal, Ausweichen bei jedem Streufaktor, damit genug Stichproben entstehen). Je Spiel am
Ende: Anzahl gepruefter vorhergesagter Ziele (_pred_n) und davon direkt getroffen (_pred_hit).
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
    from agents.sherlock.config import AgentConfig
    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=V11, train=False, seed=0)
    agent.cfg.dodge = True
    agent.cfg.dodge_shape = True
    agent.cfg.dodge_distrust = 0.01  # nur zaehlen, praktisch nie abschalten
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    opp_side = "player_1" if side == "player_0" else "player_0"
    if opp_name.startswith("self:"):
        opp = make_opponent("self", opp_side, self_play_path=opp_name.split(":", 1)[1])
    else:
        opp = make_opponent(opp_name, opp_side)
    agent.new_game(side)
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    obs, info = env.reset(seed=seed)
    agent.set_env_cfg(info["params"])
    opp.set_env_cfg(info["params"])
    step, done = 0, False
    while not done:
        a = {side: agent.act(step=step, obs=obs[side]), opp_side: opp.act(step=step, obs=obs[opp_side])}
        obs, _, term, trunc, _ = env.step(a)
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        step += 1
    return dict(seed=seed, side=side, opp=opp_name, n=agent._pred_n, hit=agent._pred_hit,
                shape=agent._sap_shape(), ev_man=agent._shape_ev["man"], ev_cheb=agent._shape_ev["cheb"])


if __name__ == "__main__":
    opps = sys.argv[1].split(",")
    a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    jobs = [(s, side, o) for o in opps for s in range(a, b) for side in ("player_0", "player_1")]
    with Pool(int(sys.argv[5]) if len(sys.argv) > 5 else 3) as pool:
        rows = pool.map(play, jobs, chunksize=1)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "Spiele ->", out)
