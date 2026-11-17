"""Warum füllt imit_end_fill kaum Felder? Ein Spiel gegen Kaggle, Protokoll je Endphasen-Schritt."""
import sys
from dataclasses import replace

import numpy as np

sys.path.insert(0, "/Users/elhassanmahmoud/Documents/AKI_LuxAgent15")
from luxai_s3.wrappers import LuxAIS3GymEnv  # noqa: E402

from agents.sherlock import geometry as geo  # noqa: E402
from agents.sherlock.config import AgentConfig  # noqa: E402
from agents.sherlock.imitation_agent import ImitationAgent  # noqa: E402
from agents.sherlock.main import Agent_x  # noqa: E402
from agents.sherlock_r3t.agent import STUDENTS  # noqa: E402
from scripts.common import make_opponent  # noqa: E402

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7256000
side = sys.argv[2] if len(sys.argv) > 2 else "player_0"
path = str(STUDENTS["ens9"])
cfg = replace(Agent_x._cfg_from_checkpoint(path) or AgentConfig(), imit_stay_bias=1.0, imit_unstack=True,
              imit_hold_points=True, imit_end_fill=10)
me = ImitationAgent(side, agent_path=path, cfg=cfg, train=False)
me.set_to_eval_mode()
other = "player_1" if side == "player_0" else "player_0"
opp = make_opponent("kaggle3", other)

orig = ImitationAgent._end_fill


def logged(self, ctx, ids, pos, logp, acts, n):
    left = int(ctx["max_match_steps"]) - int(ctx["match_step"]) + 1
    out = orig(self, ctx, ids, pos, logp, acts, n)
    if 0 < left <= n:
        points = np.asarray(self.belief.point_tiles, dtype=bool)
        first = ctx.get("first_on_tile", {})
        here = [(int(p[0]), int(p[1])) for p in pos]
        occupied = set(here)
        ec = np.asarray(ctx.get("enemy_coords", np.zeros((0, 2), dtype=int))).reshape(-1, 2)
        enemy = {(int(x), int(y)) for x, y in ec}
        free = [(int(a), int(b)) for a, b in zip(*np.nonzero(points)) if (int(a), int(b)) not in occupied]
        free_noen = [t for t in free if t not in enemy]
        holders = [k for k, t in enumerate(here) if points[t] and first.get(t) == int(ids[k])]
        sap = [k for k in range(len(ids)) if int(acts[k]) == geo.SAP]
        nonhold = [k for k in range(len(ids)) if k not in holders]
        dists = []
        for t in free_noen:
            ds = [abs(here[k][0] - t[0]) + abs(here[k][1] - t[1]) for k in nonhold if int(acts[k]) != geo.SAP]
            dists.append(min(ds) if ds else None)
        changed = int((out != acts).sum())
        energy = [float(ctx["ally_ene"][u]) for u in ids]
        print(f"m{int(ctx['match_step']):3d} left {left:2d} units {len(ids):2d} holders {len(holders)} sap {len(sap):2d} "
              f"known {int(points.sum()):2d} free {len(free)} free_ohne_gegner {len(free_noen)} "
              f"min_abstand {dists} geaendert {changed} ene<2 {sum(e < 2 for e in energy)}")
    return out


ImitationAgent._end_fill = logged
env = LuxAIS3GymEnv(numpy_output=True)
obs, info = env.reset(seed=seed)
for a, s in ((me, side), (opp, other)):
    if hasattr(a, "new_game"):
        a.new_game(s)
    if hasattr(a, "set_env_cfg"):
        a.set_env_cfg(info["params"])
for step in range(303):
    act = {side: me.act(step, obs[side]), other: opp.act(step, obs[other])}
    obs, rew, term, trunc, _ = env.step(act)
    if term[side] or trunc[side]:
        break
print("ep_stats", {k: v for k, v in me.ep_stats.items() if "end" in k})
