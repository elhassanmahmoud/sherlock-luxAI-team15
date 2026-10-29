"""Regel-Schalter der Battle-Vorbereitung (29.10.2026): Reserve statt Lauf in die Gegnerfestung."""
import numpy as np

from agents.sherlock import geometry as geo
from agents.sherlock.belief import TILE_ASTEROID, TILE_EMPTY, TILE_NEBULA, Belief
from agents.sherlock.features import assign_targets, reserve_tiles
from tests.conftest import make_obs
from tests.test_rules_1910 import _stay_agent


def _belief():
    b = Belief(0)
    b.tile_type[:, :] = TILE_EMPTY
    b.point_tiles[5, 5] = True      # eigenes Punkte-Tile
    b.point_tiles[18, 18] = True    # Punkte-Tile der Gegnerhaelfte
    b._coords_dirty = True
    return b


def test_reserve_tiles_ring_two_around_own_point_tiles():
    b = _belief()
    b.tile_type[3, 3] = TILE_ASTEROID
    b.tile_type[7, 7] = TILE_NEBULA
    r = reserve_tiles(b, 24, 24)
    xs, ys = np.nonzero(r)
    assert len(xs) == 16 - 2                              # 5x5-Ring ohne Asteroid und Nebel
    assert all(max(abs(x - 5), abs(y - 5)) == 2 for x, y in zip(xs, ys))
    assert not r[3, 3] and not r[7, 7] and not r[5, 5]
    assert not r[18, 16]                                  # nichts um Gegner-Punkte-Tiles


def test_home_reserve_replaces_far_enemy_target_only():
    units = np.array([[5, 5], [1, 0]])
    off = assign_targets(_belief(), np.array([0, 1]), units, 24, 24, far_opp=10)
    on = assign_targets(_belief(), np.array([0, 1]), units, 24, 24, far_opp=10, home_reserve=True)
    assert off == {0: (5, 5), 1: (18, 18)}
    assert on[0] == (5, 5) and on[1] == (3, 3)          # naechstes Reservetile statt Gegnerfestung
    near = np.array([[5, 5], [16, 16]])                  # Gegner-Tile in Reichweite far_opp: bleibt
    assert assign_targets(_belief(), np.array([0, 1]), near, 24, 24, far_opp=10, home_reserve=True)[1] == (18, 18)


def test_home_reserve_prefers_field_energy():
    b = _belief()
    b.energy_map[4, 3] = 20.0                            # 1 Feld weiter, aber 20 Feldenergie
    out = assign_targets(b, np.array([0, 1]), np.array([[5, 5], [3, 1]]), 24, 24, far_opp=10, home_reserve=True)
    assert out[1] == (4, 3)


def test_reserve_sap_defends_from_reserve_tile():
    for flag, want in ((False, geo.STAY), (True, geo.SAP)):
        a = _stay_agent(pt_sap=True, far_opp=10, home_reserve=True, reserve_sap=flag)
        a.belief.tile_type[:, :] = TILE_EMPTY
        a.belief.point_tiles[5, 5] = a.belief.point_tiles[18, 18] = True
        a.belief._coords_dirty = True
        act = a.act(10, make_obs(10, 10, units=[(5, 5, 100), (3, 5, 100)], enemies=[(4, 8, 80)]))
        assert a._cache[1]["assigned"][1] == (3, 5)
        assert int(act[1, 0]) == want, flag
