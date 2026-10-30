"""Schaetzung des Streufaktors mit und ohne Gegner-Evidenz im selben Spiel (V10 + art_splash + drop_enemy_est
gegen solution92). Gibt je Spiel den ersten sicheren Schritt und den Wert beider Schaetzer aus.
Lief am 30.10. mit dem Entwurfsschalter drop_enemy_est (Gegner-Evidenz in param_est), der danach verworfen
wurde (nur 4 von 48 Spielen frueher sicher); im Hauptstand laeuft das Skript deshalb nicht mehr."""
import multiprocessing as mp
import random
import sys

import numpy as np
import pandas as pd

W = "/Users/elhassanmahmoud/Documents/AKI_LuxAgent15/experiments/releases/20261022_v10_baseline/agent_p0.pth"


def run(job):
    seed, truth = job
    sys.path.insert(0, ".")
    from scripts.experiment import limit_threads
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.main import Agent_x
    from agents.sherlock.param_est import ParamEstimator
    from scripts.common import make_opponent
    from scripts.par_eval import build_cfg
    env = LuxAIS3GymEnv(numpy_output=True)
    agent = Agent_x("player_0", agent_path=W, cfg=build_cfg(W, ["art_splash=true", "drop_enemy_est=true"]), train=False)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    out = []
    for side in ("player_0", "player_1"):
        opp_side = "player_1" if side == "player_0" else "player_0"
        opp = make_opponent("solution92", opp_side)
        agent.new_game(side)
        shadow = ParamEstimator()
        team = 0 if side == "player_0" else 1
        random.seed(seed)
        np.random.seed(seed % 2**32)
        obs, info = env.reset(seed=seed)
        agent.set_env_cfg(info["params"])
        opp.set_env_cfg(info["params"])
        step, done = 0, False
        first = {"neu": None, "alt": None}
        val = {"neu": None, "alt": None}
        while not done:
            shadow.observe(obs[side], team, None, info["params"] if step == 0 else cfg)
            a = agent.act(step, obs[side])
            cfg = agent.env_cfg or {}
            shadow.remember(obs[side], team, a)
            for name, est in (("neu", agent.param_est), ("alt", shadow)):
                d = est.dropoff(default=0.0)
                if d != 0.0 and first[name] is None:
                    first[name], val[name] = step, d
            act = {side: a, opp_side: opp.act(step, obs[opp_side])}
            obs, r, term, trunc, info2 = env.step(act)
            done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
            step += 1
        out.append((seed, side, truth, first["neu"], val["neu"], agent.param_est.dropoff(default=0.0),
                    first["alt"], val["alt"], shadow.dropoff(default=0.0)))
    return out


if __name__ == "__main__":
    mp_ = pd.read_csv(sys.argv[1])
    n = int(sys.argv[2])
    b = mp_[(mp_.seed >= 801000) & (mp_.seed < 801300)]
    jobs = []
    for d in (0.25, 0.5, 1.0):
        jobs += [(int(s), d) for s in b[b.unit_sap_dropoff_factor == d].seed.tolist()[-n:]]
    with mp.get_context("spawn").Pool(int(sys.argv[3])) as pool:
        for res in pool.imap_unordered(run, jobs):
            for r in res:
                print(*r, flush=True)
