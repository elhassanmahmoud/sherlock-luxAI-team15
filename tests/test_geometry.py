"""Spiegelung kanonisch <-> echt: invertierbar und fuer beide Seiten korrekt."""
import numpy as np
import pytest

from agents.sherlock import geometry as geo
from agents.sherlock.belief import Belief
from tests.conftest import H, W, make_obs


def test_mirror_xy_is_involution_on_all_tiles():
    for x in range(W):
        for y in range(H):
            assert geo.mirror_xy(*geo.mirror_xy(x, y)) == (x, y)


def test_spawn_corners_swap():
    assert geo.mirror_xy(0, 0) == (W - 1, H - 1)


def test_mirror_positions_keeps_invisible_and_inverts():
    pos = np.array([[3, 5], [-1, -1], [23, 0]])
    m = geo.mirror_positions(pos)
    assert (m[1] == -1).all()
    np.testing.assert_array_equal(geo.mirror_positions(m), pos)


def test_mirror_map_matches_pointwise_definition_and_inverts():
    rng = np.random.default_rng(0)
    arr = rng.integers(0, 100, size=(W, H))
    m = geo.mirror_map(arr)
    for x in range(W):
        for y in range(H):
            mx, my = geo.mirror_xy(x, y)
            assert m[mx, my] == arr[x, y]
    np.testing.assert_array_equal(geo.mirror_map(m), arr)


@pytest.mark.parametrize("d", range(5))
def test_move_direction_commutes_with_mirror(d):
    """Zug d im kanonischen Raum == Zug mirror_dir(d) im echten Raum."""
    x, y = 7, 11
    cx, cy = geo.mirror_xy(x, y)
    real_d = geo.mirror_dir(d)
    rx, ry = x + geo.DIR_DX[real_d], y + geo.DIR_DY[real_d]
    assert geo.mirror_xy(rx, ry) == (cx + geo.DIR_DX[d], cy + geo.DIR_DY[d])
    assert geo.mirror_dir(geo.mirror_dir(d)) == d


def test_sap_delta_commutes_with_mirror():
    x, y = 10, 4
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            cx, cy = geo.mirror_xy(x, y)
            rdx, rdy = geo.mirror_delta(dx, dy)  # kanonisch -> echt
            assert geo.mirror_xy(x + rdx, y + rdy) == (cx + dx, cy + dy)
            assert geo.mirror_delta(*geo.mirror_delta(dx, dy)) == (dx, dy)


@pytest.mark.parametrize("seed", [0, 1, 7, 123])
def test_real_maps_are_antidiagonal_symmetric(env, seed):
    """Voraussetzung der kanonischen Features: Karte ist symmetrisch unter M."""
    env.reset(seed=seed)
    mf = env.state.map_features
    for arr in (np.asarray(mf.tile_type), np.asarray(mf.energy)):
        np.testing.assert_array_equal(geo.mirror_map(arr), arr)


@pytest.mark.parametrize("team", [0, 1])
def test_belief_puts_own_spawn_at_canonical_origin(team):
    """Beide Seiten sehen sich im kanonischen Raum auf (0,0)-Seite."""
    spawn = (0, 0) if team == 0 else (W - 1, H - 1)
    b = Belief(team)
    b.observe(make_obs(5, 5, team=team, units=[(*spawn, 100)], relics=[spawn]))
    assert (0, 0) in b.relic_positions


def test_no_canonical_disables_mirroring():
    b = Belief(1, canonical=False)
    assert not b.mirrored
    b.observe(make_obs(5, 5, team=1, units=[(23, 23, 100)], relics=[(20, 21)]))
    assert (20, 21) in b.relic_positions
