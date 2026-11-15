"""Consult mixed v4 in M3 only after the public own sequence win, loss."""
import numpy as np

from scripts.r3_v4_contact_agent import make_r3, make_v4, sync


class SwitchAgent:
    def __init__(self, side, enabled=True):
        self.r3 = make_r3(side)
        self.shadow = make_v4(side) if enabled else None
        self.new_game(side)

    def new_game(self, player=None):
        if player is not None:
            self.side = player
            self.team = ("player_0", "player_1").index(player)
        self.r3.new_game(self.side)
        if self.shadow is not None:
            self.shadow.new_game(self.side)
        self.first_won = None
        self.v4_steps = self.different_orders = self.different_active = 0

    def set_env_cfg(self, cfg):
        self.r3.set_env_cfg(cfg)
        if self.shadow is not None:
            self.shadow.set_env_cfg(cfg)

    def update(self, *args, **kwargs):
        # Both published course packages are in evaluation mode and observe in act.
        pass

    def act(self, step, obs):
        base = self.r3.act(step, obs)
        if self.shadow is None:
            self._check_children()
            return base
        wins = np.asarray(obs["team_wins"])
        awards = int(wins.sum())
        if awards == 1 and self.first_won is None:
            self.first_won = bool(wins[self.team])
        if awards >= 2 and self.first_won is None:
            raise ValueError("M1 award was never observed")
        v4_orders = self.shadow.act(step, obs)
        switch = self.first_won and awards == 2 and int(wins[self.team]) == 1
        if switch:
            self.v4_steps += 1
            diff = np.any(np.asarray(base) != v4_orders, axis=1)
            active = (np.asarray(obs["units_mask"])[self.team].astype(bool) &
                      (np.asarray(obs["units"]["energy"])[self.team].reshape(-1) >= 0))
            self.different_orders += int(diff.sum())
            self.different_active += int((active & diff).sum())
            # Mixed v4 has already recorded its native final decision. R3 shadows that world order.
            sync(self.r3, obs, v4_orders, estimator=True)
            final = v4_orders
        else:
            # Preserve the original R3 state. Both v4 components saw this same public frame.
            sync(self.shadow.v14, obs, base, estimator=True)
            sync(self.shadow.student, obs, base, estimator=False)
            final = base
        self._check_children()
        return final

    def _check_children(self):
        children = [self.r3]
        if self.shadow is not None:
            children.extend((self.shadow, self.shadow.v14, self.shadow.student))
        if any(getattr(child, "caught_errors", 0) for child in children):
            raise RuntimeError("An original actor caught an error")

    def episode_stats(self):
        return dict(v4_steps=self.v4_steps, different_orders=self.different_orders,
                    different_active=self.different_active)
