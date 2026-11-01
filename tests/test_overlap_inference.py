"""Exact observation algebra; no environment games or hidden state required."""
from itertools import product
from time import perf_counter

import numpy as np
import pytest

from agents.sherlock.belief import Belief, MAX_RECORDS
from agents.sherlock.config import AgentConfig


def _infer(belief, tiles, gain, match_step=60):
    positions = np.full((16, 2), -1, dtype=np.int32)
    mask = np.zeros(16, dtype=bool)
    for i, tile in enumerate(tiles):
        positions[i] = divmod(tile, belief.H)
        mask[i] = True
    belief._infer_point_tiles(positions, np.full(16, 100), mask, gain, match_step)


def _enabled(**kwargs):
    belief = Belief(0, **kwargs)
    # Setting the flag also lets the regression reach the old implementation.
    belief.overlap_infer = True
    return belief


@pytest.mark.parametrize("reverse", [False, True])
def test_partial_overlap_proves_both_exclusive_tiles(reverse):
    belief = _enabled(subset_infer=True)
    equations = [((100, 101, 102), 2), ((101, 102, 103), 1)]
    for tiles, gain in reversed(equations) if reverse else equations:
        _infer(belief, tiles, gain)
    assert 100 in belief._point
    assert 103 in belief._dead
    assert not ({101, 102} & (belief._point | belief._dead))


def test_overlap_does_not_require_subset_inference():
    belief = _enabled()
    _infer(belief, (100, 101, 102), 2)
    _infer(belief, (101, 102, 103), 1)
    assert belief._point == {100}
    assert belief._dead == {103}


def test_default_off_keeps_partial_overlap_unresolved():
    belief = Belief(0, subset_infer=True)
    assert getattr(belief, "overlap_infer", False) is False
    _infer(belief, (100, 101, 102), 2)
    _infer(belief, (101, 102, 103), 1)
    assert not belief._point and not belief._dead


def test_non_extreme_overlap_stays_unknown():
    belief = _enabled(subset_infer=True)
    _infer(belief, (100, 101, 102), 1)
    _infer(belief, (101, 102, 103), 1)
    assert not belief._point and not belief._dead


def test_overlap_obeys_spawn_window_and_match_reset():
    belief = _enabled(subset_infer=True)
    _infer(belief, (100, 101, 102), 2, match_step=20)
    _infer(belief, (101, 102, 103), 1, match_step=21)
    assert not belief.records and not belief._point and not belief._dead
    _infer(belief, (100, 101, 102), 2)
    belief.reset_match()
    _infer(belief, (101, 102, 103), 1)
    assert not belief._point and not belief._dead


def test_overlap_uses_existing_symmetry_and_preserves_points_on_reset():
    belief = _enabled(symmetry=True, subset_infer=True)
    _infer(belief, (100, 101, 102), 2)
    _infer(belief, (101, 102, 103), 1)
    assert belief._point == {100, belief._mirror_idx(100)}
    assert belief._dead == {103, belief._mirror_idx(103)}
    belief.reset_match()
    assert belief._point == {100, belief._mirror_idx(100)}
    assert not belief._dead and not belief.records


def test_config_roundtrip_and_agent_wiring():
    cfg = AgentConfig.from_dict({"overlap_infer": True})
    assert getattr(cfg, "overlap_infer", False) is True
    assert cfg.to_dict()["overlap_infer"] is True
    assert AgentConfig.from_dict({}).overlap_infer is False
    from agents.sherlock.main import Agent_x

    agent = Agent_x("player_0", cfg=cfg, train=False)
    assert agent.belief.overlap_infer is True


def test_belief_accepts_opt_in_constructor_without_changing_subset_default():
    belief = Belief(0, overlap_infer=True)
    assert belief.overlap_infer is True
    assert belief.subset_infer is False


def test_overlap_normalizes_previously_proven_tiles():
    belief = _enabled()
    belief._mark_point(104)
    belief._mark_dead(105)
    belief.records = [((101, 102, 103, 104, 105), 2)]
    derived = belief._overlap_differences(((100, 101, 102, 104, 105), 3))
    assert set(derived) == {((100,), 1), ((103,), 0)}


@pytest.mark.parametrize("old,new", [
    (((101, 102, 103), 0), ((100, 101, 102), 2)),  # empty common-sum interval
    (((101, 102, 103), -1), ((100, 101, 102), 2)),
    (((101, 102, 103), 4), ((100, 101, 102), 2)),
    (((101, 102, 103), 1), ((100, 101, 102), -1)),
    (((101, 102, 103), 1), ((100, 101, 102), 4)),
    (((100, 101), 1), ((100, 101), 0)),
    (((), 0), ((), 0)),
])
def test_incompatible_or_empty_equations_produce_no_overlap_facts(old, new):
    belief = _enabled()
    belief.records = [old]
    assert belief._overlap_differences(new) == []


def test_conflicting_batch_deductions_are_suppressed():
    belief = _enabled()
    belief.records = [((101, 102, 103), 1), ((101, 102, 103), 3)]
    assert belief._overlap_differences(((100, 101, 102), 2)) == []


def test_symmetric_conflicting_batch_deductions_are_suppressed():
    belief = _enabled(symmetry=True)
    mirrored = belief._mirror_idx(100)
    # First equation forces 100 positive; the second forces its mirror null.
    belief.records = [((101, 102, 103), 1), ((100, 102, mirrored), 1)]
    assert belief._overlap_differences(((100, 101, 102), 2)) == []


def test_exhaustive_four_tile_binary_assignments_validate_all_deductions():
    # Independent oracle enumerates every possible binary map, including
    # impossible pairs; it does not reuse any production inference algebra.
    universe = tuple(range(4))
    assignments = list(product((0, 1), repeat=4))
    subsets = [tuple(t for t in universe if mask & (1 << t)) for mask in range(16)]
    belief = _enabled()
    checked = 0
    nonempty = 0
    for old_tiles in subsets:
        for new_tiles in subsets:
            for old_sum in range(len(old_tiles) + 1):
                for new_sum in range(len(new_tiles) + 1):
                    belief.records = [(old_tiles, old_sum)]
                    derived = belief._overlap_differences((new_tiles, new_sum))
                    possible = [v for v in assignments
                                if sum(v[t] for t in old_tiles) == old_sum
                                and sum(v[t] for t in new_tiles) == new_sum]
                    assert possible or not derived
                    for tiles, rest in derived:
                        assert rest in (0, len(tiles))
                        assert all(sum(v[t] for t in tiles) == rest for v in possible)
                    checked += 1
                    nonempty += bool(derived)
    assert checked == 2304
    assert nonempty > 0


def test_oversize_records_and_records_past_cap_are_not_inspected():
    class OversizeTuple(tuple):
        def __iter__(self):
            raise AssertionError("oversize record was expanded")

    belief = _enabled()
    oversized = OversizeTuple(range(17))
    belief.records = [(oversized, 8)]
    assert belief._overlap_differences(((100, 101, 102), 2)) == []
    assert belief._overlap_differences((oversized, 8)) == []
    belief.records = [((0, 1), 1)] * MAX_RECORDS + [((101, 102, 103), 1)]
    assert belief._overlap_differences(((100, 101, 102), 2)) == []


def test_dense_maximum_records_aggregate_facts_without_record_explosion():
    belief = _enabled()
    common = tuple(range(15))
    belief.records = [(common + (tile,), 7) for tile in range(100, 100 + MAX_RECORDS)]
    before = list(belief.records)
    start = perf_counter()
    for _ in range(50):
        derived = belief._overlap_differences((common + (30,), 8))
    elapsed = perf_counter() - start
    assert set(derived) == {((30,), 1), (tuple(range(100, 100 + MAX_RECORDS)), 0)}
    assert belief.records == before
    assert len(derived) == 2
    assert elapsed < 5.0, f"50 bounded 400x16 comparisons took {elapsed:.3f}s"


def test_integrated_inference_retains_record_cap_after_aggregated_facts():
    belief = _enabled()
    common = tuple(range(15))
    belief.records = [(common + (tile,), 7) for tile in range(100, 100 + MAX_RECORDS)]
    _infer(belief, common + (30,), 8)
    assert belief._point == {30}
    assert belief._dead == set(range(100, 100 + MAX_RECORDS))
    assert len(belief.records) <= MAX_RECORDS


def test_disabled_flag_preserves_existing_record_and_fact_sequences():
    default = Belief(0, subset_infer=True, symmetry=True)
    explicit_off = Belief(0, subset_infer=True, symmetry=True)
    explicit_off.overlap_infer = False
    rng = np.random.default_rng(17)
    truth = {100, 103, 105}
    for _ in range(30):
        tiles = tuple(sorted(rng.choice(np.arange(100, 107), size=3, replace=False)))
        gain = sum(tile in truth for tile in tiles)
        for belief in (default, explicit_off):
            _infer(belief, tiles, gain)
        assert default.records == explicit_off.records
        assert default._point == explicit_off._point
        assert default._dead == explicit_off._dead
