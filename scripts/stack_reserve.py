"""Hold the lower-energy half (rounded up) of each visible friendly stack in place on moves."""
from collections import Counter, defaultdict

import numpy as np

from agents.sherlock import geometry as geo
from agents.sherlock.main import Agent_x
from scripts.combat_teacher_counterfactual import substitute


def held_movers(public, team, base):
    """Choose UIDs from own observed world positions and current energies."""
    positions = np.asarray(public["units"]["position"])[team]
    energies = np.asarray(public["units"]["energy"])[team].reshape(-1)
    by_cell = defaultdict(list)
    for uid in np.flatnonzero(np.asarray(public["units_mask"])[team]):
        by_cell[tuple(positions[uid])].append(int(uid))

    held = []
    for stack in by_cell.values():
        if len(stack) < 2:
            continue
        # All present ships consume a rank, including negative-energy remnants.
        stack.sort(key=lambda uid: (-float(energies[uid]), uid))
        for uid in stack[len(stack) // 2:]:
            if energies[uid] >= 0 and 1 <= base[uid, 0] <= 4:
                held.append(uid)
    return held


class StackReserveAgent(Agent_x):
    def _reset_episode_state(self):
        super()._reset_episode_state()
        self.study_stats = Counter()

    def _act(self, step, obs):
        base = super()._act(step, obs)
        if self.training or int(obs["match_steps"]) == 0:
            return base
        held = held_movers(obs, self.team_id, base)
        if not held:
            return base
        advice = base.copy()
        advice[held] = [geo.STAY, 0, 0]
        return substitute(self, obs, base, advice, "movement", self.study_stats)
