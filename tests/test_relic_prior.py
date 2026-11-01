"""Schalter relic_prior (01.11.2026): Erkundungsziele nach der Lage-Verteilung der Relics (features.RELIC_P6)."""
import numpy as np

from agents.sherlock.belief import Belief
from agents.sherlock.config import AgentConfig
from agents.sherlock.features import RELIC_P6, assign_targets, box_sum, prior_mass, prior_targets


def test_relic_p6_is_a_distribution_symmetric_to_the_antidiagonal():
    assert abs(RELIC_P6.sum() - 1.0) < 2e-3
    # Spiegelung M(x, y) = (23 - y, 23 - x): (x % 6, y % 6) -> (5 - y % 6, 5 - x % 6), weil 23 % 6 = 5
    assert np.allclose(RELIC_P6, RELIC_P6[::-1, ::-1].T)
    # nie ein Relic, wenn beide Koordinaten % 6 in {0, 5}
    for a in (0, 5):
        for b in (0, 5):
            assert RELIC_P6[a, b] == 0.0
    m = prior_mass(24, 24)
    assert m.shape == (24, 24) and m[2, 3] == RELIC_P6[2, 3] and m[8, 9] == RELIC_P6[2, 3]


def test_box_sum_matches_a_direct_sum_also_at_the_border():
    rng = np.random.default_rng(0)
    a = rng.random((24, 24))
    for r in (0, 1, 2, 4):
        b = box_sum(a, r)
        for x, y in ((0, 0), (5, 7), (23, 23), (1, 22)):
            want = a[max(0, x - r):x + r + 1, max(0, y - r):y + r + 1].sum()
            assert abs(b[x, y] - want) < 1e-9


def test_prior_targets_pick_the_core_of_each_block_and_skip_explored_blocks():
    passable = np.ones((24, 24), dtype=bool)
    unexp = np.argwhere(np.ones((24, 24), dtype=bool)).astype(np.int32)
    goals, frac = prior_targets(unexp, passable, 1, 4)
    assert len(goals) == 36 and np.all(frac > 0) and np.all(frac <= 1.0 + 1e-9)
    # Block (0..3, 0..3): mit Sichtweite 1 sieht man von (2, 3) bzw. (3, 2) aus den Kern (2..3, 2..3)
    first = {tuple(g) for g in goals.tolist() if g[0] < 4 and g[1] < 4}
    assert first <= {(2, 2), (2, 3), (3, 2), (3, 3)}
    # erkundeter Block ohne unerkundete Wahrscheinlichkeit in Sichtweite faellt weg
    mask = np.ones((24, 24), dtype=bool)
    mask[:6, :6] = False
    goals2, _ = prior_targets(np.argwhere(mask).astype(np.int32), passable, 1, 4)
    assert not any(g[0] < 4 and g[1] < 4 for g in goals2.tolist())
    # Asteroiden sind keine Ziele
    blocked = passable.copy()
    blocked[2:4, 2:4] = False
    goals3, _ = prior_targets(unexp, blocked, 1, 4)
    assert not any(2 <= g[0] <= 3 and 2 <= g[1] <= 3 for g in goals3.tolist())
    # Nebel: weder Masse noch Ziel (bei starkem Sichtabzug bleibt er unerkundet)
    neb = np.zeros((24, 24), dtype=bool)
    neb[:6, :6] = True
    goals4, _ = prior_targets(unexp, passable, 1, 4, neb)
    assert not any(g[0] < 6 and g[1] < 6 for g in goals4.tolist())
    assert not any(g[0] < 4 and g[1] < 4 for g in goals4.tolist())


def test_assign_targets_unchanged_without_relic_prior_and_prefers_cores_with_it():
    b = Belief(0)
    units = np.array([[0, 0], [1, 0]])
    kw = dict(grid=4, seen_before_penalty=300.0)
    base = assign_targets(b, np.array([0, 1]), units, 24, 24, **kw)
    assert assign_targets(b, np.array([0, 1]), units, 24, 24, relic_prior=0.0, sensor=1, **kw) == base
    out = assign_targets(b, np.array([0, 1]), units, 24, 24, relic_prior=8.0, sensor=1, **kw)
    for t in out.values():
        assert RELIC_P6[t[0] % 6, t[1] % 6] > 0.04 or any(
            RELIC_P6[(t[0] + dx) % 6, (t[1] + dy) % 6] > 0.08 for dx in (-1, 0, 1) for dy in (-1, 0, 1))


def test_relic_prior_is_off_by_default():
    assert AgentConfig().relic_prior == 0.0
