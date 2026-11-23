"""Choose the length of one safe public scout route using its learned whole-game value."""
from functools import lru_cache
import json
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import (
    DELTA, PAIR_END, PACKAGE, Scout,
)

HERE = Path(__file__).resolve().parent
BUDGETS = (0, 1, 3)
NAMES = (
    "turn", "front", "off_axis", "energy", "move_cost", "sap_cost", "sap_range",
    "peers", "distance_nearest_peer", "free_directions", "known_map", "local_novelty",
    "local_cloud", "local_rock", "straight", "along_front", "base_stay", "diff_first",
    "crowding_base_step", "crowding_scout_step", "mass_near", "mass_on_route",
    "probability_concentration", "seen_enemy", "enemy_points",
)


def choose(features, model):
    x = (np.asarray(features) - model["center"]) / model["scale"]
    gains = np.asarray(model["weights"]) @ x + model["bias"]
    if not np.isfinite(gains).all():
        raise ValueError("Invalid predicted value")
    best = int(np.argmax(gains))
    return (1, 3)[best] if gains[best] >= 0.30 else 0


def utility(row, base):
    def share(record):
        return np.mean([(m["points"][0] + 1) / (sum(m["points"]) + 2) for m in record["matches"]])
    return float(12*(row["win"] - base["win"]) + 3*(row["wins"] - base["wins"])
                 + 1.5*(share(row) - share(base))
                 + .06*np.clip(base["sight"] - row["sight"], -35, 35)
                 + .03*np.clip(base["credit"] - row["credit"], -35, 35))


@lru_cache(maxsize=1)
def parameters():
    model = json.loads((HERE / "modell.json").read_text())
    if tuple(model["features"]) != NAMES:
        raise ValueError("Wrong feature order")
    return model


class ShortCourse(Scout):
    def __init__(self, base, forced=None):
        self.forced = forced
        if forced not in (*BUDGETS, None):
            raise ValueError("Unknown route length")
        super().__init__(base)

    def reset(self):
        super().reset()
        self.features = self.budget = None
        self.tick = self.enemy_points = self.seen_enemy = 0

    def act(self, step, obs):
        self.tick = int(step)
        if self.budget is not None and self.changes >= self.budget:
            self.last = None
            return self.base.act(step, obs)
        self.enemy_points = int(obs["team_points"][1-self.team])
        self.seen_enemy = int(np.asarray(obs["units_mask"][1-self.team], bool).sum())
        return super().act(step, obs)

    def plan(self, x, y, base_dir, allowed, board, peer_dest, projected, probabilities):
        route = super().plan(x, y, base_dir, allowed, board, peer_dest, projected, probabilities)
        if not route or self.features is not None:
            return route
        pos = np.array([x, y], int)
        path = pos + DELTA[route].cumsum(0)
        to_cell = np.abs(PAIR_END - pos).max(axis=2).min(axis=1)
        to_path = np.abs(PAIR_END[:, :, None] - path).max(axis=3).min(axis=(1, 2))
        total = max(float(probabilities.sum()), 1e-12)
        norm = probabilities / total
        local = np.indices((24, 24)).transpose(1, 2, 0)
        neighborhood = np.abs(local - pos).max(2) <= 4
        tiles = board.reshape(24, 24)[neighborhood]
        peer_dist = np.abs(peer_dest - pos).sum(axis=1)
        def crowded(cell):
            return int((np.abs(peer_dest - cell).sum(axis=1) <= 2).sum())
        cfg = self.base.env_cfg
        ctx = self.base._imitation.last_fz[0]
        self.features = list(map(float, (
            self.tick, x+y, abs(x-y), ctx["ally_ene"][self.ship], cfg["unit_move_cost"],
            cfg["unit_sap_cost"], cfg["unit_sap_range"], len(peer_dest),
            peer_dist.min() if len(peer_dist) else 24, allowed.sum(), np.mean(board >= 0),
            np.mean(tiles < 0), np.mean(tiles == 1), np.mean(tiles == 2),
            len(set(route)) == 1, (path[-1] - pos).sum(), base_dir == 0, route[0] != base_dir,
            crowded(pos + DELTA[base_dir]), crowded(path[0]), norm[to_cell <= 6].sum(),
            norm[to_path <= 1].sum(), np.square(norm).sum(), self.seen_enemy, self.enemy_points,
        )))
        if len(self.features) != len(NAMES) or not np.isfinite(self.features).all():
            raise ValueError("Invalid route context")
        self.budget = self.forced if self.forced is not None else choose(self.features, parameters())
        return route if self.budget else []


def create(side, forced=None):
    from scripts.r3_package import r3_package_agent
    return ShortCourse(r3_package_agent(side, PACKAGE), forced=forced)
