"""Original scout lifecycle with a jointly scored choice at its single route decision."""
import json
from pathlib import Path

import numpy as np
from experiments.analysis.relictsuche_20261123.flottenblick.kandidat import (
    FleetScout, DIRECTIONS, DX, DY, MIRROR_DIR, PACKAGE, flat, inputs, load, option_frame, predict, support,
)
from experiments.analysis.relictsuche_20261123.ortundflotte.richtung import score_options,take
from scripts.r3_package import r3_package_agent

HERE=Path(__file__).resolve().parent


class JointScout(FleetScout):
    def __init__(self,base,net,cfg,prior_index):
        super().__init__(base,net,cfg)
        self.prior_index=prior_index

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
            scores = score_options(q, paths, self.history.last_seen, ctx["nebula"], ctx["energy_map"], int(flat(frame["start"])))
            selected = take(scores[self.prior_index])
            idx = selected if selected < len(paths) else None
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



def create(side,prior_index=None):
    if prior_index is None:
        record=json.loads((HERE/"valid.json").read_text())
        assert record["passed"] and record["selected"] in (1,2)
        prior_index=record["selected"]
    return JointScout(r3_package_agent(side,PACKAGE),*load(),prior_index)
