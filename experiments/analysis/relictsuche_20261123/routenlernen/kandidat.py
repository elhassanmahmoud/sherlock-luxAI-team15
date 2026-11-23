"""Single-ship, low-visibility course policy. The public wrapper owns the original V16."""
import json
from pathlib import Path

import numpy as np

if __package__ == "sherlock":
    from .routes import DIRECTIONS, DX, DY, MIRROR_DIR, NAMES, SearchHistory, current, route_features
else:
    from experiments.analysis.relictsuche_20261123.routenlernen.routes import (
        DIRECTIONS, DX, DY, MIRROR_DIR, NAMES, SearchHistory, current, route_features,
    )

HERE = Path(__file__).resolve().parent


def load_model():
    raw = json.loads((HERE / "routengewichte.json").read_text())
    if tuple(raw["features"]) != NAMES:
        raise ValueError("Incorrect route features")
    return {k: np.asarray(raw[k], np.float32) for k in ("mean", "scale", "w1", "b1", "w2", "b2")}


def values(x, model):
    normal = (x - model["mean"]) / model["scale"]
    hidden = np.maximum(normal @ model["w1"] + model["b1"], 0)
    return (hidden @ model["w2"] + model["b2"]).reshape(-1)


class RouteAgent:
    def __init__(self, base, model=None):
        self.base = base
        self.model = load_model() if model is None else model
        self.clear()

    def clear(self):
        self.history = SearchHistory()
        self.changes = 0
        self.pending = []
        self.expected = None

    def new_game(self, player=None):
        self.base.new_game(player)
        self.clear()

    def set_env_cfg(self, env_cfg):
        self.base.set_env_cfg(env_cfg)

    def __getattr__(self, name):
        return getattr(self.base, name)

    def act(self, step, obs):
        original = self.base.act(step=step, obs=obs)
        if (step > 90 or int(self.base.env_cfg.get("unit_sensor_range", 0)) != 1
                or int(obs["match_steps"]) != step or self.history.finished):
            return original
        self.history.observe(step, obs, self.base.team_id)
        if step < 10 or self.history.finished:
            return original
        frame = current(self.base, original, self.history)
        if frame is None:
            self.pending = []
            return original
        if self.pending and (self.expected != tuple(frame.origin) or not frame.first_allowed(self.pending[0])):
            self.pending = []
            return original
        if not self.pending:
            choices = route_features(frame, self.history, step)
            if choices is None:
                return original
            x, ids, lengths, _, _ = choices
            if ids[0] != 0:
                return original
            score = values(x, self.model)
            # Prefer V16's first direction for two similarly valued routes.
            rank = score + .15 * (DIRECTIONS[ids, 0] == frame.original)
            k = int(np.argmax(rank))
            if ids[k] == 0 or score[k] < score[0] + .35:
                return original
            self.history.scout = frame.uid
            self.pending = DIRECTIONS[ids[k], :lengths[k]].tolist()
        d = self.pending.pop(0)
        self.expected = tuple(frame.origin + np.array([DX[d], DY[d]]))
        if d == frame.original:
            return original
        out = original.copy()
        world = int(MIRROR_DIR[d]) if self.base._imitation.belief.mirrored else d
        out[frame.uid] = (world, 0, 0)
        policy = self.base._imitation
        policy._prev_actions[frame.uid] = d
        policy._sap_hits.pop(frame.uid, None)
        policy.param_est.record_played_actions(out)
        self.changes += 1
        return out


def create(side):
    from scripts.r3_package import r3_package_agent
    root = HERE.parents[3]
    return RouteAgent(r3_package_agent(side, root / "experiments/releases/20261117_sherlock_v16/agent.zip"))
