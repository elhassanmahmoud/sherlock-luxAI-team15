"""Wie schnell findet V11 neue Relic-Paare in Match 2/3? (Analyse 30.10.2026, nur lesen)

Je Spiel und neuem Paar j >= 1: Spawn-Schritt, erster Schritt, in dem ein Relic des Paars in unserer
Sensormaske liegt, Abstand des Paars zum naechsten frueheren Relic (oder Spiegelbild) und Abstand
unserer naechsten Unit zum Relic beim Spawn.

    cd REPO && .venv/bin/python - SEED_FROM SEED_TO OPP OUT.csv < relic_delay.py
"""
import csv
import random
import sys
from multiprocessing import Pool

import numpy as np

W = 24
V11 = "experiments/releases/20261030_v11_baseline/agent_p0.pth"


def mirror(p):
    return (W - 1 - p[1], W - 1 - p[0])


def play(job):
    import torch
    torch.set_num_threads(1)  # wie scripts.experiment.limit_threads
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
    st = env.state
    mask = np.asarray(st.relic_nodes_mask)
    nodes = np.asarray(st.relic_nodes)
    sched = np.asarray(st.relic_spawn_schedule)
    half = len(mask) // 2
    pairs = [j for j in range(half) if int(sched[j]) >= 0]  # Maske ist vor dem Spawn noch falsch
    pos = {j: (int(nodes[j][0]), int(nodes[j][1])) for j in pairs}
    found = {}
    near_unit = {}
    sensor = int(info["params"]["unit_sensor_range"])
    us = 0 if side == "player_0" else 1
    step, done = 0, False
    while not done:
        o = obs[side]
        g = int(np.asarray(o["steps"]))
        sm = np.asarray(o["sensor_mask"])
        for j in pairs:
            if j == 0 or j in found or g < int(sched[j]):
                continue
            p, q = pos[j], mirror(pos[j])
            if j not in near_unit:
                up = np.asarray(o["units"]["position"])[us]
                um = np.asarray(o["units_mask"])[us]
                d = [max(abs(int(x) - a), abs(int(y) - b)) for (x, y), m in zip(up, um) if m
                     for a, b in (p, q)]
                near_unit[j] = min(d) if d else 99
            if sm[p] or sm[q]:
                found[j] = g
        actions = {side: agent.act(step=step, obs=obs[side]), opp_side: opp.act(step=step, obs=obs[opp_side])}
        obs, _, term, trunc, _ = env.step(actions)
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        step += 1
    rows = []
    for j in pairs:
        if j == 0:
            continue
        prev = [pos[i] for i in pairs if i < j] + [mirror(pos[i]) for i in pairs if i < j]
        dist = min(max(abs(pos[j][0] - a), abs(pos[j][1] - b)) for a, b in prev)
        rows.append(dict(seed=seed, side=side, opp=opp_name, j=j, spawn=int(sched[j]),
                         found=found.get(j, -1), delay=(found[j] - int(sched[j])) if j in found else -1,
                         dist_prev=dist, near_unit=near_unit.get(j, -1), sensor=sensor))
    return rows


if __name__ == "__main__":
    a, b, opp, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
    jobs = [(s, side, opp) for s in range(a, b) for side in ("player_0", "player_1")]
    with Pool(int(sys.argv[5]) if len(sys.argv) > 5 else 6) as pool:
        res = pool.map(play, jobs, chunksize=1)
    rows = [r for rr in res for r in rr]
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "neue Paare ->", out)
