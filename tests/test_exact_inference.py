"""Pure Fraction/Belief tests: no Torch, engine, games or hidden-state inputs."""
from importlib import import_module
from itertools import combinations, permutations, product

import numpy as np
import pytest

from agents.sherlock.belief import Belief
from agents.sherlock.config import AgentConfig
from tests.conftest import make_obs


def _records(last=2):
    return [((0, 3, 4), last), ((0, 1), 1), ((1, 2), 1), ((2, 3), 1)]


def _solve(records, touched=(0, 1, 2, 3, 4), **kwargs):
    return import_module("agents.sherlock.exact_infer").exact_facts(records, touched, **kwargs)


def _infer(belief, tiles, gain, clock):
    positions = np.full((16, 2), -1, dtype=np.int32)
    mask = np.zeros(16, dtype=bool)
    for i, tile in enumerate(tiles):
        positions[i] = divmod(tile, belief.H)
        mask[i] = True
    belief._gauss_observations = clock
    belief._infer_point_tiles(positions, np.full(16, 100), mask, gain, 60)


@pytest.mark.parametrize("last,want", [(1, 0), (2, 1)])
def test_five_tile_fact_is_new_beyond_subset_and_overlap(last, want):
    baseline = Belief(0, subset_infer=True, overlap_infer=True)
    enabled = Belief(0, subset_infer=True, overlap_infer=True)
    enabled.gauss_infer = True
    for i, (tiles, gain) in enumerate(_records(last)):
        for belief in (baseline, enabled):
            _infer(belief, tiles, gain, i * 8)
    assert not baseline._point and not baseline._dead
    assert 4 in (enabled._point if want else enabled._dead)
    assert not ({0, 1, 2, 3} & (enabled._point | enabled._dead))


def test_config_and_constructor_default_off():
    assert getattr(AgentConfig.from_dict({"gauss_infer": True}), "gauss_infer", False)
    assert AgentConfig.from_dict({}).gauss_infer is False
    assert AgentConfig(gauss_infer=True).to_dict()["gauss_infer"] is True
    assert Belief(0, gauss_infer=True).gauss_infer is True
    assert Belief(0).gauss_infer is False


@pytest.mark.parametrize("last,want", [(1, 0), (2, 1)])
def test_order_invariant_exact_facts_without_arbitrary_free_variables(last, want):
    for ordered in permutations(_records(last)):
        assert _solve(list(ordered)) == {4: want}
    assert _solve([((0, 1), 1)], touched=(0,)) == {}


def test_exhaustive_three_variable_binary_compatible_systems_are_sound():
    # Every compatible system of three distinct subsets; expectations come
    # only from all eight independent binary assignments, never row algebra.
    assignments = list(product((0, 1), repeat=3))
    subsets = [tuple(i for i in range(3) if mask & (1 << i)) for mask in range(8)]
    checked = 0
    deductions = 0
    for groups in combinations(subsets, 3):
        totals = {tuple(sum(v[i] for i in group) for group in groups) for v in assignments}
        for rests in totals:
            records = list(zip(groups, rests))
            valid = [v for v in assignments if all(sum(v[i] for i in group) == rest
                                                   for group, rest in records)]
            facts = _solve(records, touched=(0, 1, 2))
            assert valid
            assert all(value in (0, 1) and all(v[tile] == value for v in valid)
                       for tile, value in facts.items())
            checked += 1
            deductions += bool(facts)
    assert checked > 200 and deductions > 0


def test_symmetry_counts_two_physical_tiles_and_known_multiplicity():
    mirror = lambda tile: 15 - tile
    assert _solve([((0, 15, 1), 2), ((1,), 0)], touched=(0,), mirror=mirror) == {0: 1, 1: 0}
    assert _solve([((0, 15, 1), 1), ((1,), 1)], touched=(0,), mirror=mirror) == {0: 0, 1: 1}
    assert _solve([((0, 15, 1), 2)], touched=(1,), point={0, 15}, mirror=mirror) == {1: 0}
    assert _solve([((7,), 1)], touched=(7,), mirror=lambda tile: 14 - tile) == {7: 1}


def test_symmetry_conflicting_known_facts_reject_atomically():
    assert _solve([((1,), 1)], touched=(1,), point={0}, dead={15},
                  mirror=lambda tile: 15 - tile) == {}


def test_exhaustive_two_orbit_physical_equations_preserve_binary_soundness():
    assignments = list(product((0, 1), repeat=2))
    physical_orbit = (0, 1, 1, 0)
    subsets = [tuple(i for i in range(4) if mask & (1 << i)) for mask in range(16)]
    for groups in combinations(subsets, 2):
        totals = {tuple(sum(v[physical_orbit[i]] for i in group) for group in groups)
                  for v in assignments}
        for rests in totals:
            records = list(zip(groups, rests))
            valid = [v for v in assignments
                     if all(sum(v[physical_orbit[i]] for i in group) == rest
                            for group, rest in records)]
            facts = _solve(records, touched=(0, 1, 2, 3), mirror=lambda tile: 3 - tile)
            assert all(t in (0, 1) and all(v[t] == value for v in valid)
                       for t, value in facts.items())


@pytest.mark.parametrize("records", [
    [((), 1)],
    [((0,), -1)],
    [((0,), 2)],
    [((0, 1), 0), ((0, 1), 1)],
    [((0, 1), 1), ((1, 2), 1), ((0, 2), 1), ((0, 1, 3), 2)],
])
def test_inconsistent_or_nonbinary_fixed_components_return_no_partial_facts(records):
    assert _solve(records) == {}


def test_empty_disconnected_and_single_component_selection():
    assert _solve([]) == {}
    assert _solve([((100,), 1)], touched=(0,)) == {}
    assert _solve([((100,), 1), ((0,), 0)], touched=(100, 0)) == {0: 0}


def test_oversized_component_is_skipped_without_truncation():
    chain = [((i, i + 1), 1) for i in range(24)] + [((24,), 1)]
    assert _solve(chain, touched=(0,)) == {}
    truth = (0, 1, 0, 1, 0, 1)
    rows = []
    for mask in range(1, 42):
        group = tuple(i for i in range(6) if mask & (1 << i))
        rows.append((group, sum(truth[i] for i in group)))
    assert _solve(rows, touched=(0,)) == {}


def test_input_record_and_total_record_limits():
    class TooLarge(tuple):
        def __iter__(self):
            raise AssertionError("oversize record expanded")

    assert _solve([(TooLarge(range(17)), 1)], touched=(0,)) == {}
    assert _solve([((100, 101), 1)] * 400 + [((0,), 1)], touched=(0,)) == {}


def test_operation_and_fraction_bit_limits_abort_without_partial_facts(monkeypatch):
    module = import_module("agents.sherlock.exact_infer")
    monkeypatch.setattr(module, "MAX_CELL_OPS", 1)
    assert _solve(_records()) == {}
    monkeypatch.setattr(module, "MAX_CELL_OPS", 4096)
    monkeypatch.setattr(module, "MAX_BITS", 1)
    assert _solve(_records()) == {}


def test_real_dense_bounded_component_exhausts_default_operation_cap_atomically():
    module = import_module("agents.sherlock.exact_infer")
    assert (module.MAX_RECORDS, module.MAX_RAW_TILES, module.MAX_VARIABLES,
            module.MAX_ROWS, module.MAX_CELL_OPS, module.MAX_BITS) == (400, 16, 24, 40, 4096, 256)
    # The 16x16 core J-I is invertible; the other eight variables each have
    # their own equation. This explicit dense row order exhausts the work cap;
    # exact_facts uses its own deterministic ordering, which may be cheaper.
    groups = [tuple(j for j in range(16) if j != i) for i in range(16)]
    groups += [tuple(range(15)) + (i,) for i in range(16, 24)]
    with pytest.raises(module._Abort):
        module._reduce([(dict.fromkeys(group, 1), 0) for group in groups], list(range(24)))


def test_inputs_are_not_mutated_and_duplicates_do_not_exhaust_row_limit():
    records = _records() * 20
    before = list(records)
    point, dead = set(), set()
    assert _solve(records, point=point, dead=dead) == {4: 1}
    assert records == before and not point and not dead


def test_no_gauss_in_spawn_window_or_with_window_options():
    for option in (None, "window_infer", "window_infer_all"):
        belief = Belief(0)
        belief.gauss_infer = True
        belief.records = _records()
        if option:
            setattr(belief, option, True)
        belief._try_gauss(_records()[-1], 20 if option is None else 60)
        assert not belief._point and not belief._dead
        assert belief._gauss_attempts == 0


def test_attempt_limit_spacing_and_reopening_dead_do_not_refill_budget():
    belief = Belief(0, gauss_infer=True)
    for i in range(12):
        belief.records = [((100 + i, 200 + i), 1)]
        belief._gauss_observations = i * 8
        belief._try_gauss(belief.records[0], 60)
        belief._reopen_dead()
    assert belief._gauss_attempts == 8
    belief.reset_match()
    assert belief._gauss_attempts == 0
    belief.records = [((100, 200), 1)]
    belief._try_gauss(belief.records[0], 60)
    assert belief._gauss_attempts == 1
    last_clock = belief._gauss_last_observation
    belief._reopen_dead()
    belief.records = [((101, 201), 1)]
    belief._gauss_observations = last_clock + 7
    belief._try_gauss(belief.records[0], 60)
    assert belief._gauss_attempts == 1
    belief.records = [((102, 202), 1)]
    belief._gauss_observations = last_clock + 8
    belief._try_gauss(belief.records[0], 60)
    assert belief._gauss_attempts == 2
    belief.reset_game()
    assert belief._gauss_attempts == 0


def test_real_observations_count_only_fresh_nonreset_steps():
    belief = Belief(0, gauss_infer=True)
    points = 0
    equations = dict(zip((50, 58, 66, 74), _records()))
    for step in range(50, 75):
        tiles, gain = equations.get(step, ((), 0))
        points += gain
        obs = make_obs(step, step, units=[(*divmod(t, 24), 100) for t in tiles], points=(points, 0))
        belief.observe(obs)
        belief.observe(obs)
    assert belief._gauss_observations == 25
    assert 4 in belief._point
    assert belief._gauss_attempts == 4
    belief.observe(make_obs(101, 0))
    assert belief._gauss_observations == 0 and belief._gauss_attempts == 0


def test_new_relic_invalidates_seen_equations_but_not_attempts():
    belief = Belief(0, gauss_infer=True)
    belief.records = [((100, 200), 1)]
    belief._try_gauss(belief.records[0], 60)
    assert belief._gauss_seen
    belief._add_relic(5, 5)
    assert not belief._gauss_seen and belief._gauss_attempts == 1


def test_belief_uses_existing_mirror_marking_and_skips_duplicate_attempts():
    belief = Belief(0, gauss_infer=True, symmetry=True)
    for i, (tiles, gain) in enumerate(_records()):
        _infer(belief, tiles, gain, i * 8)
    assert belief._point == {4, belief._mirror_idx(4)}
    before = belief._gauss_attempts
    belief._gauss_observations += 8
    belief._try_gauss(_records()[-1], 60)
    assert belief._gauss_attempts == before
