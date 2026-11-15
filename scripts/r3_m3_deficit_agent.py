"""Switch from the original R3 to V15 on the first public late deficit in a tied third match."""
import numpy as np

from scripts.r3_m3_deficit_replay import trigger
from scripts.r3_v4_contact_agent import sync
from scripts.r3_v4_wl_agent import SwitchAgent


class DeficitAgent(SwitchAgent):
    def new_game(self, player=None):
        super().new_game(player)
        self.decision = None
        self.first_different_active_step = None

    def act(self, step, obs):
        # Both native policies observe and act from the first frame, on both seats.
        base = self.r3.act(step, obs)
        shadow = self.shadow.act(step, obs)
        t = int(obs["match_steps"])
        points = obs["team_points"]
        if self.decision is None and trigger(t, obs["team_wins"], points, self.team):
            if not 252 <= step <= 302 or t != step - 202:
                raise ValueError("Public trigger was outside the third match")
            self.decision = dict(global_step=step, match_step=t, points=int(points[self.team]),
                                 opponent_points=int(points[1 - self.team]))
        final = base
        if self.decision is not None:
            final = shadow
            self.v4_steps += 1
            different = np.any(np.asarray(base) != shadow, axis=1)
            active = (np.asarray(obs["units_mask"])[self.team].astype(bool)
                      & (np.asarray(obs["units"]["energy"])[self.team].reshape(-1) >= 0))
            changed = int((different & active).sum())
            if changed and self.first_different_active_step is None:
                self.first_different_active_step = step
            self.different_orders += int(different.sum())
            self.different_active += changed
            sync(self.r3, obs, final, estimator=True)
            # Native V15 already recorded the mixed order in its estimator; the
            # underlying actors keep their original evaluation behaviour after the switch.
        else:
            sync(self.shadow.v14, obs, final, estimator=True)
            sync(self.shadow.student, obs, final, estimator=False)
        self._check_children()
        return final
