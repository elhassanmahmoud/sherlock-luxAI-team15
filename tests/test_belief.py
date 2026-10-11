"""Belief: Relics ueber Matches merken, Punkte-Tiles aus Punktzuwachs ableiten."""
import numpy as np

from agents.sherlock import geometry as geo
from agents.sherlock.belief import Belief, MemorylessBelief, STABLE_FROM_MATCH_STEP
from tests.conftest import make_obs

MS = STABLE_FROM_MATCH_STEP + 5  # match_step im stabilen Bereich


def test_relic_is_remembered_across_matches():
    b = Belief(0)
    b.observe(make_obs(10, 10, units=[(1, 1, 100)], relics=[(8, 9)]))
    assert (8, 9) in b.relic_positions
    b.observe(make_obs(101, 0))                       # Matchwechsel
    b.observe(make_obs(150, 49, units=[(1, 1, 100)]))  # Relic nicht sichtbar
    assert (8, 9) in b.relic_positions
    assert b.relic_zone[8, 9] and b.relic_zone[10, 11] and not b.relic_zone[11, 11]


def test_memoryless_view_forgets_invisible_relic():
    b = MemorylessBelief(0)
    b.observe(make_obs(10, 10, units=[(1, 1, 100)], relics=[(8, 9)]))
    assert (8, 9) in b.relic_positions
    b.observe(make_obs(11, 11, units=[(1, 1, 100)]))
    assert not b.relic_positions and not b.point_tiles.any()


def test_point_tile_inferred_from_point_gain():
    b = Belief(0)
    b.observe(make_obs(MS, MS, units=[(8, 9, 50)], relics=[(8, 9)], points=(0, 0)))
    b.observe(make_obs(MS + 1, MS + 1, units=[(8, 10, 50)], relics=[(8, 9)], points=(1, 0)))
    assert b.point_tiles[8, 10]
    assert not b.point_tiles[8, 9]
    b.observe(make_obs(MS + 2, MS + 2, units=[(8, 11, 50)], relics=[(8, 9)], points=(1, 0)))
    assert b.dead_tiles[8, 11] and not b.point_tiles[8, 11]


def test_partial_information_resolved_by_propagation():
    b = Belief(0)
    # zwei Units, 1 Punkt -> unentschieden
    b.observe(make_obs(MS, MS, units=[(5, 5, 50), (6, 6, 50)], points=(1, 0)))
    assert not b.point_tiles.any()
    # nur (5,5) besetzt, kein Zuwachs -> (5,5) tot -> (6,6) muss punkten
    b.observe(make_obs(MS + 1, MS + 1, units=[(5, 5, 50)], points=(1, 0)))
    assert b.dead_tiles[5, 5] and b.point_tiles[6, 6]


def test_negative_energy_units_do_not_count():
    b = Belief(0)
    b.observe(make_obs(MS, MS, units=[(5, 5, 50), (6, 6, -5)], points=(1, 0)))
    assert b.point_tiles[5, 5] and not b.point_tiles[6, 6]


def test_no_inference_during_relic_spawn_window():
    b = Belief(0)
    b.observe(make_obs(20, 20, units=[(5, 5, 50)], points=(1, 0)))
    assert not b.point_tiles.any() and not b.dead_tiles.any()


def test_point_tile_inference_for_player_1_is_canonical():
    b = Belief(1)
    real = (15, 13)
    b.observe(make_obs(MS, MS, team=1, units=[(*real, 50)], points=(0, 1)))
    cx, cy = geo.mirror_xy(*real)
    assert b.point_tiles[cx, cy] and b.point_tiles.sum() == 1


def test_point_tiles_survive_match_change_dead_tiles_do_not():
    b = Belief(0)
    b.observe(make_obs(MS, MS, units=[(5, 5, 50)], points=(1, 0)))
    b.observe(make_obs(MS + 1, MS + 1, units=[(6, 6, 50)], points=(1, 0)))
    assert b.point_tiles[5, 5] and b.dead_tiles[6, 6]
    b.observe(make_obs(101, 0))
    assert b.point_tiles[5, 5] and not b.dead_tiles.any()


def test_symmetry_mirrors_relics_point_and_dead_tiles():
    b = Belief(0, symmetry=True)
    b.observe(make_obs(MS, MS, units=[(8, 9, 50)], relics=[(8, 9)], points=(0, 0)))
    mx, my = geo.mirror_xy(8, 9)
    assert (mx, my) in b.relic_positions and b.relic_zone[mx, my]
    b.observe(make_obs(MS + 1, MS + 1, units=[(8, 10, 50)], relics=[(8, 9)], points=(1, 0)))
    assert b.point_tiles[8, 10] and b.point_tiles[geo.mirror_xy(8, 10)]
    assert b.dead_tiles[8, 9] and b.dead_tiles[mx, my]
    assert b.explored[geo.mirror_xy(8, 10)]


def test_symmetry_off_keeps_old_behaviour():
    b = Belief(0)
    b.observe(make_obs(MS, MS, units=[(8, 9, 50)], relics=[(8, 9)], points=(0, 0)))
    assert b.relic_positions == {(8, 9)}


def test_symmetry_reopen_dead_keeps_points():
    b = Belief(0, symmetry=True)
    b.observe(make_obs(MS, MS, units=[(5, 5, 50)], points=(1, 0)))
    assert b.point_tiles[5, 5] and b.point_tiles[geo.mirror_xy(5, 5)]
    b.observe(make_obs(MS + 1, MS + 1, units=[(6, 6, 50)], points=(1, 0)))
    assert b.dead_tiles[6, 6] and b.dead_tiles[geo.mirror_xy(6, 6)]
    b.observe(make_obs(101, 0))   # Matchwechsel -> Null-Wissen verworfen
    assert not b.dead_tiles.any() and b.point_tiles[geo.mirror_xy(5, 5)]
