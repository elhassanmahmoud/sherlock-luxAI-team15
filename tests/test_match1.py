"""Match-1-Schalter (12.10.): fruehe Schluesse, veraltete Erkundung, Raster-Ziele."""
import numpy as np

from agents.sherlock.belief import Belief
from agents.sherlock.features import grid_targets
from tests.conftest import make_obs


def test_early_inference_after_first_point_in_match0():
    b = Belief(0, early_inference=True)
    b.observe(make_obs(20, 20, units=[(5, 5, 50)], points=(1, 0)))
    assert b.point_tiles[5, 5]
    off = Belief(0)
    off.observe(make_obs(20, 20, units=[(5, 5, 50)], points=(1, 0)))
    assert not off.point_tiles.any()


def test_early_inference_from_opponent_points_in_match0():
    b = Belief(0, early_inference=True)
    b.observe(make_obs(20, 20, units=[(5, 5, 50)], points=(0, 3)))
    assert b.dead_tiles[5, 5]
    fresh = Belief(0, early_inference=True)
    fresh.observe(make_obs(20, 20, units=[(5, 5, 50)], points=(0, 0)))
    assert not fresh.dead_tiles.any()   # niemand punktet -> Paar evtl. noch nicht da


def test_early_inference_in_match1_waits_for_new_pair():
    b = Belief(0, early_inference=True)
    b.observe(make_obs(10, 10, units=[(1, 1, 100)], relics=[(8, 9)]))
    assert b.known_pairs() == 1
    b.observe(make_obs(101, 0))                                    # Match 1
    b.observe(make_obs(121, 20, units=[(5, 5, 50)], relics=[(8, 9)], points=(1, 0)))
    assert not b.point_tiles.any()   # Paar von Match 1 noch nicht bekannt
    b.observe(make_obs(122, 21, units=[(5, 5, 50)], relics=[(8, 9), (15, 3)], points=(2, 0)))
    assert b.known_pairs() == 2 and b.point_tiles[5, 5]


def test_explore_coords_stale_in_match0_until_relic_known():
    b = Belief(0)
    obs = make_obs(5, 5, units=[(1, 1, 100)])
    sensor = np.zeros((24, 24), bool)
    sensor[:5, :5] = True
    obs["sensor_mask"] = sensor
    b.observe(obs)
    later = make_obs(30, 30, units=[(20, 20, 100)])
    s2 = np.zeros((24, 24), bool)
    s2[18:, 18:] = True
    later["sensor_mask"] = s2
    b.observe(later)
    normal = {tuple(c) for c in b.unexplored_coords()}
    stale = {tuple(c) for c in b.explore_coords(20)}
    assert (2, 2) not in normal and (2, 2) in stale     # vor 25 Steps gesehen
    assert (20, 20) not in stale                          # gerade gesehen
    seen_relic = make_obs(31, 31, units=[(20, 20, 100)], relics=[(21, 21)])
    seen_relic["sensor_mask"] = s2
    b.observe(seen_relic)
    assert {tuple(c) for c in b.explore_coords(20)} == {tuple(c) for c in b.unexplored_coords()}


def test_grid_targets_one_per_block():
    coords = np.argwhere(np.ones((24, 24), bool)).astype(np.int32)
    t = grid_targets(coords, 4)
    assert len(t) == 36
    assert len({(x // 4, y // 4) for x, y in t}) == 36
    assert (1, 1) in {tuple(c) for c in t} or (2, 2) in {tuple(c) for c in t}
