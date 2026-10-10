"""Gemeinsame Test-Helfer. Tests immer aus dem Projekt-Root starten:

    .venv/bin/python -m pytest -q
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

W = H = 24


def make_obs(step: int, match_step: int, team: int = 0, units=(), enemies=(),
             points=(0, 0), wins=(0, 0), relics=(), asteroids=(), sensor_all=True):
    """Minimale Beobachtung im Env-Format (echte Koordinaten).

    units/enemies: Liste von (x, y, energy); relics: Liste von (x, y).
    """
    pos = np.full((2, 16, 2), -1, dtype=np.int32)
    ene = np.full((2, 16), -1, dtype=np.int32)
    mask = np.zeros((2, 16), dtype=bool)
    for side, lst in ((team, units), (1 - team, enemies)):
        for i, (x, y, e) in enumerate(lst):
            pos[side, i] = (x, y)
            ene[side, i] = e
            mask[side, i] = True
    tile = np.zeros((W, H), dtype=np.int32)
    for x, y in asteroids:
        tile[x, y] = 2
    rpos = np.full((6, 2), -1, dtype=np.int32)
    rmask = np.zeros(6, dtype=bool)
    for i, (x, y) in enumerate(relics):
        rpos[i] = (x, y)
        rmask[i] = True
    return {
        "steps": np.int32(step), "match_steps": np.int32(match_step),
        "units": {"position": pos, "energy": ene}, "units_mask": mask,
        "sensor_mask": np.full((W, H), bool(sensor_all)),
        "map_features": {"tile_type": tile, "energy": np.zeros((W, H), np.int32)},
        "relic_nodes": rpos, "relic_nodes_mask": rmask,
        "team_points": np.array(points, np.int32), "team_wins": np.array(wins, np.int32),
    }


ENV_CFG = {"max_units": 16, "map_width": W, "map_height": H, "max_steps_in_match": 100,
           "unit_move_cost": 3, "unit_sap_cost": 40, "unit_sap_range": 4, "unit_sensor_range": 2}


@pytest.fixture
def env():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    e = LuxAIS3GymEnv(numpy_output=True)
    yield e
    e.close()
