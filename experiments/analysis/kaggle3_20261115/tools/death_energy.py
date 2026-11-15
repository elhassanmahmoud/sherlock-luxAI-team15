"""Woran sterben unsere Units, und wie entwickelt sich die Energie? (Diagnose 15.11.2026)"""
import multiprocessing as mp
import os
import sys

import numpy as np

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
CHECK_STEPS = (5, 10, 20, 30, 50, 75, 99)


def play(job):
    seed, side = job
    sys.path.insert(0, PROJECT)
    os.chdir(PROJECT)
    from scripts.experiment import limit_threads
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent
    from scripts.par_eval import build_cfg

    w = "agents/sherlock/weights/agent_p0.pth"
    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=w, cfg=build_cfg(w, []), train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    agent.new_game(side)
    opp_side = "player_1" if side == "player_0" else "player_0"
    opp = make_opponent("kaggle3", opp_side)
    obs, info = env.reset(seed=seed)
    p = info["params"]
    agent.set_env_cfg(p)
    opp.set_env_cfg(p)
    team = 0 if side == "player_0" else 1
    sides = {team: side, 1 - team: opp_side}
    causes = {t: {"collision": 0, "sap": 0, "void": 0, "other": 0} for t in (0, 1)}
    energy_at = {t: {s: [] for s in CHECK_STEPS} for t in (0, 1)}
    on_point = {t: 0 for t in (0, 1)}
    step, done = 0, False
    while not done:
        acts = {side: agent.act(step=step, obs=obs[side]), opp_side: opp.act(step=step, obs=obs[opp_side])}
        nxt, _, term, trunc, info = env.step(acts)
        done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
        ms_now = int(np.asarray(obs[side]["match_steps"]))
        ms_next = int(np.asarray(nxt[side]["match_steps"]))
        if ms_next != 0 and not done:
            for t in (0, 1):
                o, n, en = obs[sides[t]], nxt[sides[t]], 1 - t
                m0 = np.asarray(o["units_mask"])[t].astype(bool)
                m1 = np.asarray(n["units_mask"])[t].astype(bool)
                pos0 = np.asarray(o["units"]["position"])[t]
                # Positionen des Gegners nach dem Zug (aus seiner eigenen Sicht = Wahrheit)
                eo = nxt[sides[en]]
                em = np.asarray(eo["units_mask"])[en].astype(bool)
                epos = np.asarray(eo["units"]["position"])[en][em]
                # Saps des Gegners in diesem Schritt
                ea = np.asarray(acts[sides[en]])
                eo0 = obs[sides[en]]
                em0 = np.asarray(eo0["units_mask"])[en].astype(bool)
                epos0 = np.asarray(eo0["units"]["position"])[en]
                targets = [epos0[i] + ea[i, 1:3] for i in range(len(ea)) if em0[i] and ea[i, 0] == 5]
                # gewollte Zielfelder unserer Units nach dem Zug
                our_a = np.asarray(acts[sides[t]])
                d = {0: (0, 0), 1: (0, -1), 2: (1, 0), 3: (0, 1), 4: (-1, 0), 5: (0, 0)}
                for i in np.where(m0 & ~m1)[0]:
                    tgt = pos0[i] + np.array(d[int(our_a[i, 0])])
                    if any((epos == tgt).all(axis=1)) or any((epos == pos0[i]).all(axis=1)):
                        causes[t]["collision"] += 1
                    elif any(np.abs(tt - tgt).max() <= 1 or np.abs(tt - pos0[i]).max() <= 1 for tt in targets):
                        causes[t]["sap"] += 1
                    elif any(np.abs(ep - tgt).sum() == 1 or np.abs(ep - pos0[i]).sum() == 1 for ep in epos):
                        causes[t]["void"] += 1
                    else:
                        causes[t]["other"] += 1
                if ms_next in CHECK_STEPS and step < 101:  # nur Match 1
                    e = np.asarray(n["units"]["energy"])[t][m1]
                    energy_at[t][ms_next].append(float(e.mean()) if len(e) else 0.0)
        obs = nxt
        step += 1
    env.close()
    return {0: causes[team], 1: causes[1 - team]}, {0: energy_at[team], 1: energy_at[1 - team]}


def main():
    jobs = [(s, side) for s in range(7150000, 7150012) for side in ("player_0", "player_1")]
    with mp.get_context("spawn").Pool(12) as pool:
        res = pool.map(play, jobs)
    for t, name in ((0, "Sherlock"), (1, "Kaggle")):
        tot = {k: 0 for k in ("collision", "sap", "void", "other")}
        for causes, _ in res:
            for k in tot:
                tot[k] += causes[t][k]
        n = sum(tot.values())
        print(f"{name}: {n} Tode in {len(res)} Spielen ->", ", ".join(f"{k} {v} ({100*v/max(n,1):.0f} %)" for k, v in tot.items()))
    print("Mittlere Energie pro lebender Unit in Match 1 (Sherlock : Kaggle):")
    for s in CHECK_STEPS:
        a = [x for _, e in res for x in e[0][s]]
        b = [x for _, e in res for x in e[1][s]]
        print(f"  Schritt {s:>3}: {np.mean(a):6.0f} : {np.mean(b):6.0f}")


if __name__ == "__main__":
    main()
