"""Schalter opp_point_infer (29.10.2026): Punkte-Gleichungen aus dem Punktgewinn des Gegners."""
import numpy as np

from agents.sherlock.belief import Belief
from tests.conftest import make_obs


def _belief(flag=True):
    b = Belief(0, symmetry=True, early_inference=True, relic_filter=True, subset_infer=True)
    b.opp_point_infer = flag
    return b


def _steps(b, enemies_b, opp_points_b, hide=None):
    """Step 60 ohne Gegner, Step 61 mit Gegnern und Gegnerpunkten; Relic-Paar (11,11)/(12,12)."""
    b.observe(make_obs(60, 60, units=[(0, 0, 100)], enemies=[], points=(0, 0), relics=[(11, 11)]))
    obs = make_obs(61, 61, units=[(0, 0, 100)], enemies=enemies_b, points=(0, opp_points_b), relics=[(11, 11)])
    if hide is not None:
        obs["sensor_mask"][hide] = False
    b.observe(obs)
    return b


def test_enemy_gain_proves_point_tile_when_zone_visible():
    b = _steps(_belief(), [(10, 10, 50)], 1)
    assert b.point_tiles[10, 10] and b.point_tiles[13, 13]   # mit Spiegeltile
    assert b.opp_point_records == 1
    off = _steps(_belief(False), [(10, 10, 50)], 1)
    assert not off.point_tiles.any()


def test_no_inference_while_a_possible_point_tile_is_hidden():
    b = _steps(_belief(), [(10, 10, 50)], 1, hide=(13, 9))     # ein Zonen-Tile unsichtbar
    assert not b.point_tiles.any() and b.opp_point_records == 0


def test_zero_gain_marks_enemy_tiles_dead_and_ignores_tiles_outside_zone():
    b = _steps(_belief(), [(10, 10, 50), (3, 20, 50)], 0)
    assert b.dead_tiles[10, 10] and not b.point_tiles.any()
    assert not b.dead_tiles[3, 20]                            # ausserhalb jeder Relic-Zone


def test_negative_energy_enemy_does_not_count():
    b = _steps(_belief(), [(10, 10, -5), (10, 11, 40)], 1)
    assert b.point_tiles[10, 11] and not b.point_tiles[10, 10]
