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


def test_cand_probs_from_zone_overlap_and_open_equations():
    from agents.sherlock.features import OVERLAP_POINT_P, cand_probs
    b = Belief(0)
    b.relic_positions = {(5, 5), (7, 5)}
    c = np.array([[3, 5], [6, 5], [9, 5]])
    p = cand_probs(b, c)
    assert p[0] == OVERLAP_POINT_P[1] and p[1] == OVERLAP_POINT_P[2] and p[2] == OVERLAP_POINT_P[1]
    b.records = [((3 * 24 + 5, 4 * 24 + 5), 1)]
    p = cand_probs(b, c)
    assert p[0] == 0.5 and p[1] == OVERLAP_POINT_P[2]


def test_cand_post_prefers_the_likelier_candidate_and_is_off_by_default():
    assert AgentConfig().cand_post == 0.0
    b = Belief(0)
    b._add_relic(10, 10)
    b._add_relic(12, 10)   # Tiles mit x in 10..12 liegen in beiden Zonen
    b._refresh_candidates()
    unit = np.array([[7, 10]])
    base = assign_targets(b, np.array([0]), unit, 24, 24)
    assert assign_targets(b, np.array([0]), unit, 24, 24, cand_post=0.0) == base
    assert base[0] == (8, 10)   # naechster Kandidat, nur in einer Zone
    post = assign_targets(b, np.array([0]), unit, 24, 24, cand_post=30.0)
    assert 10 <= post[0][0] <= 12   # doppelt ueberdeckt, 34 % statt 20 %


def _obs_points(team_points, units, energies=None, match_steps=60, steps=None):
    """Minimale Beobachtung fuer Belief.observe (Team 0, kanonisch, nichts sichtbar ausser den eigenen Units)."""
    n = 16
    pos = -np.ones((2, n, 2), dtype=np.int32)
    mask = np.zeros((2, n), dtype=bool)
    ene = np.zeros((2, n), dtype=np.int32)
    for i, (x, y) in enumerate(units):
        pos[0, i] = (x, y)
        mask[0, i] = True
        ene[0, i] = 50 if energies is None else energies[i]
    return {"steps": steps, "match_steps": match_steps, "sensor_mask": np.zeros((24, 24), dtype=bool),
            "map_features": {"tile_type": -np.ones((24, 24), dtype=np.int32), "energy": np.zeros((24, 24), dtype=np.int32)},
            "relic_nodes": -np.ones((6, 2), dtype=np.int32), "relic_nodes_mask": np.zeros(6, dtype=bool),
            "units": {"position": pos, "energy": ene}, "units_mask": mask,
            "team_points": np.array(team_points), "team_wins": np.array([0, 0])}


def test_spawn_proof_unblocks_the_inference_after_an_unexplainable_point():
    b = Belief(0, symmetry=True, early_inference=True, relic_filter=True, subset_infer=True, keep_dead_fast=True)
    b.spawn_proof = True
    # Match 1 (Index 1): Paar 0 bekannt, Paar 1 nicht; Schritt 110 = match_step 9
    b.observe(_obs_points([0, 0], [(1, 1)], match_steps=0, steps=101))
    b._add_relic(5, 5)
    b._add_relic(23 - 5, 23 - 5)
    assert b.match_idx == 1 and b.known_pairs() == 1
    assert not b._stable(9)
    # Unit weit weg von jeder bekannten Zone punktet -> Paar 1 muss gespawnt sein
    b.observe(_obs_points([0, 0], [(1, 1)], match_steps=8, steps=109))
    b.observe(_obs_points([1, 0], [(1, 1)], match_steps=9, steps=110))
    assert b._spawn_proven and b._stable(9)
    # neues Match: Beweis verfaellt
    b.observe(_obs_points([0, 0], [(1, 1)], match_steps=0, steps=202))
    assert not b._spawn_proven


def test_spawn_proof_ignores_points_that_known_zones_can_explain():
    b = Belief(0, symmetry=True, early_inference=True, relic_filter=True, subset_infer=True, keep_dead_fast=True)
    b.spawn_proof = True
    b.observe(_obs_points([0, 0], [(5, 6)], match_steps=0, steps=101))
    b._add_relic(5, 5)
    b._add_relic(18, 18)
    b.observe(_obs_points([0, 0], [(5, 6)], match_steps=8, steps=109))
    b.observe(_obs_points([1, 0], [(5, 6)], match_steps=9, steps=110))   # (5, 6) liegt in der bekannten Zone
    assert not b._spawn_proven and not b._stable(9)
    # aus: nie
    c = Belief(0, symmetry=True, early_inference=True)
    c.observe(_obs_points([0, 0], [(1, 1)], match_steps=0, steps=101))
    c._add_relic(5, 5)
    c.observe(_obs_points([1, 0], [(1, 1)], match_steps=9, steps=110))
    assert not c._spawn_proven
