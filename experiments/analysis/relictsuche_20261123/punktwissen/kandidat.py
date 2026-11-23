"""Expose only permanently proven public scoring pairs to the original policy before it builds its inputs."""
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import Evidence, MIRROR
from scripts.r3_package import r3_package_agent

PACKAGE = Path(__file__).resolve().parents[4] / "experiments/releases/20261117_sherlock_v16/agent.zip"


class Knowledge:
    def __init__(self, base):
        self.base = base
        self.reset()

    def reset(self):
        self.proof = Evidence()
        self.events = []
        self.last_step = -1

    def __getattr__(self, key):
        return getattr(self.base, key)

    def new_game(self, player=None):
        self.base.new_game(player)
        self.reset()

    def set_env_cfg(self, cfg):
        self.base.set_env_cfg(cfg)

    def act(self, step, obs):
        if int(self.base.env_cfg["unit_sensor_range"]) != 1:
            return self.base.act(step, obs)
        t = int(obs["steps"])
        if t == self.last_step + 1:
            self.remember(t, obs)
            self.last_step = t
        elif t != self.last_step:
            raise ValueError("Non-sequential observation in the public point memory")
        return self.base.act(step, obs)

    def remember(self, t, obs):
        team = self.base.team_id
        match, turn = divmod(t, 101)
        pos = np.asarray(obs["units"]["position"][team])
        live = np.asarray(obs["units_mask"][team], bool) & (np.asarray(obs["units"]["energy"][team]).reshape(-1) >= 0)
        occupied = sorted({int(x) * 24 + int(y) for x, y in pos[live]})
        current = dict(step=t, ms=turn, points=int(obs["team_points"][team]), occupied=occupied,
                       epoch_seen=bool(np.asarray(obs["relic_nodes_mask"])[[match, match + 3]].any()))
        positive = self.proof.observe(current)
        belief = self.base._imitation.belief
        # V16 treats a repeated observation as idempotent. Its normal decision will see this update.
        belief.observe(obs)
        corrections = []
        for world in positive:
            cell = MIRROR[world] if belief.mirrored else world
            if cell not in belief._point:
                corrections.append((world, cell, cell in belief._dead or belief._mirror_idx(cell) in belief._dead))
        if any(was_dead for _, _, was_dead in corrections):
            belief.records.clear()
        for world, cell, was_dead in corrections:
            belief._mark_point(cell)
            self.events.append(dict(t=t, world=world, was_dead=bool(was_dead)))
        if corrections:
            belief._refresh_candidates()


def create(side):
    return Knowledge(r3_package_agent(side, PACKAGE))
