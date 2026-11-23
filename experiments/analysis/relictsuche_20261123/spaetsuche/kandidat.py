"""Choose one frozen opening policy at turn 55 from publicly observed V16 history."""
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from scripts.r3_package import r3_package_agent

PACKAGE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
PROVIDERS = {"route": HERE.parent / "routenlernen/kandidat.py", "ziel": HERE.parent / "zielschaetzer/kandidat.py"}
FEATURES = (
    "move_cost", "sap_range", "visible_fraction", "seen_fraction", "seen_frontier", "seen_home",
    "seen_upper_flank", "seen_lower_flank", "seen_behind_midline", "visits_fraction",
    "ships", "mean_energy", "free_energy_fraction", "fleet_x", "fleet_y", "furthest",
    "flank_bias", "fleet_spread", "unique_positions", "visible_enemies", "opponent_score",
    "opponent_scored", "known_asteroids", "visible_nebula", "search_concentration",
)
X, Y = np.indices((24, 24))
REGIONS = (abs(X + Y - 23) <= 4, X + Y < 13, X > Y + 6, Y > X + 6, X + Y > 23)


@lru_cache(maxsize=2)
def provider(name):
    ident = "late_search_provider_" + name
    spec = importlib.util.spec_from_file_location(ident, PROVIDERS[name])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[ident] = mod
    spec.loader.exec_module(mod)
    return mod


@lru_cache(maxsize=1)
def route_model():
    return provider("route").load_model()


@lru_cache(maxsize=1)
def learned_model():
    s = json.loads((HERE / "modell.json").read_text())
    if s["features"] != list(FEATURES):
        raise ValueError("Unexpected public feature layout")
    return s


def predict(model, x):
    x = (np.asarray(x, dtype=float) - model["mean"]) / model["scale"]
    scores = np.asarray(model["intercept"]) + x @ np.asarray(model["coef"])
    top = int(np.argmax(scores))
    return ("route", "ziel")[top] if scores[top] >= 1.0 else "reference"


class LateSearch:
    def __init__(self, side, arm):
        self.base = r3_package_agent(side, PACKAGE)
        self.arm = arm
        self.team = int(side[-1])
        self.route = provider("route").RouteAgent(self.base, route_model())
        self.ziel = provider("ziel").Scout(self.base)
        self.clear()

    def __getattr__(self, name):
        return getattr(self.base, name)

    def clear(self):
        self.route.clear()
        self.ziel.reset()
        self.closed = False
        self.seen = np.zeros((24, 24), dtype=bool)
        self.visited = np.zeros_like(self.seen)
        self.choice = None
        self.features = None
        self.changes = 0

    def new_game(self, player=None):
        self.base.new_game(player)
        self.team = int(self.base.player[-1])
        self.ziel.team = self.team
        self.clear()

    def set_env_cfg(self, cfg):
        self.base.set_env_cfg(cfg)

    def public_state(self, obs):
        team = self.team
        live = np.asarray(obs["units_mask"][team], bool) & (np.asarray(obs["units"]["energy"][team]).ravel() >= 0)
        positions = np.asarray(obs["units"]["position"][team])[live]
        canonical = positions if not team else 23 - positions[:, ::-1]
        sensor = np.asarray(obs["sensor_mask"], bool)
        view = sensor if not team else sensor[::-1, ::-1].T
        self.seen |= view
        if len(canonical):
            self.visited[tuple(canonical.T)] = True
        return live, canonical, view

    def describe(self, obs, live, pos, view):
        cfg = self.base.env_cfg
        e = np.asarray(obs["units"]["energy"][self.team]).ravel()[live]
        n = max(1, len(pos))
        avgpos = pos.sum(axis=0) / n
        spread = np.linalg.norm(pos - avgpos, axis=1).sum() / n
        opponent = int(obs["team_points"][1-self.team])
        tile = np.asarray(obs["map_features"]["tile_type"])
        prior = self.ziel.evidence.location_weights(55, horizon=8)
        mass = prior / max(1e-12, prior.sum())
        x = [cfg["unit_move_cost"], cfg["unit_sap_range"], view.mean(), self.seen.mean(),
             *(self.seen[reg].mean() for reg in REGIONS), self.visited.mean(), len(pos), e.sum()/n,
             (e >= 3*cfg["unit_move_cost"]).sum()/n, *avgpos,
             pos.sum(axis=1).max(initial=0), (pos[:, 0] - pos[:, 1]).sum()/n, spread,
             len(np.unique(pos, axis=0))/n, np.count_nonzero(obs["units_mask"][1-self.team]),
             min(opponent, 120), int(opponent > 0), (tile == 2).mean(), (tile == 1).mean(),
             np.sort(mass)[-12:].sum()]
        values = np.asarray(x, dtype=float)
        if values.shape != (len(FEATURES),) or not np.isfinite(values).all():
            raise ValueError("Invalid public decision features")
        return values.tolist()

    def act(self, step, obs):
        if self.closed or step >= 101 or int(self.base.env_cfg["unit_sensor_range"]) != 1:
            return self.base.act(step, obs)
        if np.any(obs["relic_nodes_mask"]) or int(obs["team_points"][self.team]) > 0:
            self.closed = True
            return self.base.act(step, obs)
        if step <= 55:
            live, pos, view = self.public_state(obs)
            if step < 55:
                self.route.history.observe(step, obs, self.team)
                self.ziel.evidence.observe(step, obs, self.team)
                return self.base.act(step, obs)
            self.features = self.describe(obs, live, pos, view)
            self.choice = predict(learned_model(), self.features) if self.arm == "learned" else self.arm
        if self.choice == "reference":
            self.closed = True
            return self.base.act(step, obs)
        actor = {"route": self.route, "ziel": self.ziel}[self.choice]
        command = actor.act(step, obs)
        self.changes = int(actor.changes)
        return command


def create(side):
    return LateSearch(side, "learned")
