"""Let one stationary ship search areas that V16's remaining fleet is unlikely to see."""
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.flottenblick.flotte import (
    DIRECTIONS, DX, DY, History, MIRROR_DIR, flat, inputs, option_frame, support,
)
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import choose, load, predict
from scripts.r3_package import r3_package_agent

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parents[3] / "experiments/releases/20261117_sherlock_v16/agent.zip"


class FleetScout:
    def __init__(self, base, net, cfg, baseline=False, original_only=False):
        self.base, self.net, self.model = base, net, cfg
        self.baseline = baseline
        self.original_only = original_only
        self.reset()

    def reset(self):
        self.changes = 0
        self.history = History()
        self.uid = None
        self.expected = None
        self.route = []
        self.done = False
        self.event = None

    def __getattr__(self, name):
        return getattr(self.base, name)

    def new_game(self, player=None):
        self.base.new_game(player)
        self.reset()

    def set_env_cfg(self, env_cfg):
        self.base.set_env_cfg(env_cfg)

    def act(self, step, obs):
        original = self.base.act(step, obs)
        if self.done or step > 83 or int(self.base.env_cfg["unit_sensor_range"]) != 1:
            return original
        team = self.base.team_id
        self.history.observe(step, obs, team)
        if self.history.finished or int(obs["match_steps"]) != step:
            self.done = True
            return original
        p = self.base._imitation
        state = getattr(p, "last_fz", None)
        self.history.proposals(state, original, team)
        if step < 16:
            return original
        if self.uid is None:
            if step > 76:
                self.done = True
                return original
            frame = option_frame(state, original, self.history, team)
            if frame is None:
                return original
            ids, lengths, paths = support(frame)
            if len(np.unique(DIRECTIONS[ids, 0])) < 2:
                return original
            self.uid = frame["uid"]
            x, dist = inputs(frame, self.history, step)
            q = predict(self.net, self.model, x, dist, self.baseline)
            ctx = frame["ctx"]
            idx = choose(q, paths, self.history.last_seen, ctx["nebula"], ctx["energy_map"], int(flat(frame["start"])))
            self.event = dict(step=int(step), uid=self.uid, origin=frame["start"].tolist(),
                              choice=None if idx is None else int(ids[idx]))
            if idx is None or self.original_only:
                self.done = True
                return original
            self.route = DIRECTIONS[ids[idx], :lengths[idx]].tolist()
        else:
            frame = option_frame(state, original, self.history, team, self.uid)
        if (frame is None or not self.route or not frame["first"][self.route[0]]
                or (self.expected is not None and self.expected != tuple(frame["start"]))):
            self.done = True
            return original
        d = self.route.pop(0)
        self.expected = tuple(frame["start"] + np.asarray([DX[d], DY[d]]))
        if not self.route:
            self.done = True
        if d == frame["original"]:
            return original
        played = original.copy()
        played[self.uid] = [int(MIRROR_DIR[d]) if team else d, 0, 0]
        p._prev_actions[self.uid] = int(d)
        p._sap_hits.pop(self.uid, None)
        p.param_est.record_played_actions(played)
        self.changes += 1
        return played


def create(side):
    return FleetScout(r3_package_agent(side, PACKAGE), *load())
