"""Ab welchem Schritt kennt param_est den Streufaktor 1,0 sicher? V10 + art_splash gegen solution92."""
import random
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from scripts.experiment import limit_threads  # noqa: E402

limit_threads()
from luxai_s3.wrappers import LuxAIS3GymEnv  # noqa: E402

from agents.sherlock.main import Agent_x  # noqa: E402
from scripts.common import make_opponent  # noqa: E402
from scripts.par_eval import build_cfg  # noqa: E402

W = "/Users/elhassanmahmoud/Documents/AKI_LuxAgent15/experiments/releases/20261022_v10_baseline/agent_p0.pth"
mp = pd.read_csv(sys.argv[1])
seeds = mp[(mp.seed >= 801000) & (mp.seed < 801300) & (mp.unit_sap_dropoff_factor == 1.0)].seed.tolist()[: int(sys.argv[2])]
env = LuxAIS3GymEnv(numpy_output=True)
agent = Agent_x("player_0", agent_path=W, cfg=build_cfg(W, ["art_splash=true"]), train=False)
agent.set_to_eval_mode()
agent.autosave_on_terminate = False
for seed in seeds:
    for side in ("player_0", "player_1"):
        opp_side = "player_1" if side == "player_0" else "player_0"
        opp = make_opponent("solution92", opp_side)
        agent.new_game(side)
        random.seed(seed)
        np.random.seed(seed % 2**32)
        obs, info = env.reset(seed=seed)
        agent.set_env_cfg(info["params"])
        opp.set_env_cfg(info["params"])
        step, done, known, wrong = 0, False, None, None
        while not done:
            act = {side: agent.act(step, obs[side]), opp_side: opp.act(step, obs[opp_side])}
            d = agent.param_est.dropoff(default=0.0)
            if d == 1.0 and known is None:
                known = step
            if d not in (0.0, 1.0) and wrong is None:
                wrong = (step, d)
            obs, r, term, trunc, info = env.step(act)
            done = bool(np.asarray(term[side])) or bool(np.asarray(trunc[side]))
            step += 1
        print(seed, side, "sicher 1,0 ab Schritt", known, "falsch:", wrong, "n_drop", agent.param_est.n_drop, flush=True)
