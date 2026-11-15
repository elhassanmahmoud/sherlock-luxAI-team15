"""React to a persistent, publicly observed enemy energy advantage."""
from collections import deque
import numpy as np
from agents.sherlock.main import Agent_x


class PressureAgent(Agent_x):
    def _reset_episode_state(self):
        super()._reset_episode_state()
        self.pressure_window = deque(maxlen=5)
        self.pressure_active = False
        self.study_stats = {'switch_step': -1, 'active_steps': 0}
        self.cfg.charge = False
        self.cfg.focus_sap = False
        self.cfg.charge_low = 125
        self.cfg.charge_high = 210

    def _decide(self, obs):
        decision = super()._decide(obs)
        ctx, ids = decision[:2]
        if not self.pressure_active:
            enemy = np.asarray(ctx['enemy_energies']).reshape(-1)
            ours = np.asarray(ctx['ally_ene'])[list(ids)].reshape(-1)
            enemy = enemy[enemy >= 0]
            ours = ours[ours >= 0]
            enough = False
            if len(enemy) >= 2 and len(ours):
                median = float(np.median(enemy))
                enough = median >= 150 and median >= float(np.median(ours)) + 40
            self.pressure_window.append(enough)
            if sum(self.pressure_window) >= 3:
                self.pressure_active = True
                self.cfg.charge = True
                self.cfg.focus_sap = True
                self.study_stats['switch_step'] = int(ctx['step'])
        self.study_stats['active_steps'] += int(self.pressure_active)
        return decision
