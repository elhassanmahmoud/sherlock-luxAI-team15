from copy import deepcopy
from types import SimpleNamespace

import pytest

from scripts import coverage_restore_assess as assess


@pytest.mark.parametrize(("deltas", "passes"), [
    ((2, 0, 0, 0), True),
    ((1, 0, 0, 0), False),
    ((3, -1, 0, 0), False),
    ((3, 0, -1, 0), False),
    ((3, 0, 0, -1), False),
])
def test_screen_gate_boundaries_in_whole_games(deltas, passes):
    result = assess.gates(*deltas)
    assert len(result) == 4
    assert all(type(flag) is bool for flag in result.values())
    assert all(result.values()) is passes


@pytest.mark.parametrize("pattern", ["seats_offset", "opponents_offset"])
def test_bootstrap_keeps_both_seats_and_both_opponents_on_the_same_map(pattern):
    seeds = range(40, 42)
    opponents = ("kaggle3", "solution92")
    candidate, reference = {}, {}
    for seed in seeds:
        for o, opponent in enumerate(opponents):
            for s, side in enumerate(("player_0", "player_1")):
                # Every map ties over all four games. Splitting the seats in
                # case one, or the opponents in case two, invents variation.
                won = int((s if pattern == "seats_offset" else o) == seed - 40)
                key = opponent, seed, side
                candidate[key] = dict(result=won, wins=3 if won else 1)
                reference[key] = dict(result=1-won, wins=2 if not won else 0)
    result = assess.contrast(candidate, reference, opponents, seeds)
    assert (result["games"], result["wins"], result["reference_wins"]) == (8, 4, 4)
    assert (result["match_wins"], result["reference_match_wins"]) == (16, 8)
    assert (result["rescued"], result["lost"]) == (4, 4)
    assert result["delta_rate"] == 0
    assert list(result["paired_95"]) == [0, 0]


def test_contrast_direction_and_game_denominator():
    opponents, seeds = ("solution92",), range(2)
    candidate, reference = {}, {}
    for seed in seeds:
        for side in ("player_0", "player_1"):
            key = opponents[0], seed, side
            before = int(seed == 0)
            after = int(before or side == "player_0")
            candidate[key] = dict(result=after, wins=2 if after else 1)
            reference[key] = dict(result=before, wins=3 if before else 0)
    result = assess.contrast(candidate, reference, opponents, seeds)
    assert (result["wins"], result["reference_wins"]) == (3, 2)
    assert (result["match_wins"], result["reference_match_wins"]) == (7, 6)
    assert (result["rescued"], result["lost"], result["delta_rate"]) == (1, 0, .25)


def candidate_pair():
    reference = dict(candidate="selective_movement", model=assess.R2_SHA, weights="a"*64,
                     engine={"env.py": "b"*64, "wrappers.py": "c"*64, "params.py": "d"*64},
                     sources={"scripts/final_battle_compare.py": "e"*64,
                              "scripts/selective_advice_agent.py": "f"*64},
                     first=7272300, maps=16, opponents=["kaggle3", "solution92", "v14"])
    candidate = deepcopy(reference)
    candidate["candidate"] = "coverage_restore"
    candidate["sources"].update(assess.EXTRAS)
    return SimpleNamespace(manifest=reference), SimpleNamespace(manifest=candidate)


def test_registered_candidate_accepts_exact_pair():
    assert assess.NAME == "coverage_restore"
    assert set(assess.EXTRAS) == {"scripts/coverage_restore.py", "scripts/coverage_restore_compare.py"}
    assess.verify_candidate(*candidate_pair())


@pytest.mark.parametrize("fault", [
    "candidate_name", "reference_name", "both_models_substituted", "candidate_weights", "candidate_engine",
    "shared_source", "extra_missing", "rule_spoof", "runner_spoof", "unexpected_source",
    "extra_already_in_reference",
])
def test_candidate_identity_rejects_spoofed_or_extra_sources(fault):
    ref, cand = candidate_pair()
    r, c = ref.manifest, cand.manifest
    if fault == "candidate_name":
        c["candidate"] = "selective_movement"
    elif fault == "reference_name":
        r["candidate"] = "v14"
    elif fault == "both_models_substituted":
        c["model"] = r["model"] = "0"*64
    elif fault == "candidate_weights":
        c["weights"] = "0"*64
    elif fault == "candidate_engine":
        c["engine"]["env.py"] = "0"*64
    elif fault == "shared_source":
        c["sources"]["scripts/selective_advice_agent.py"] = "0"*64
    elif fault == "extra_missing":
        del c["sources"]["scripts/coverage_restore_compare.py"]
    elif fault == "rule_spoof":
        c["sources"]["scripts/coverage_restore.py"] = "0"*64
    elif fault == "runner_spoof":
        c["sources"]["scripts/coverage_restore_compare.py"] = "0"*64
    elif fault == "unexpected_source":
        c["sources"]["scripts/unregistered_policy.py"] = "0"*64
    else:
        r["sources"]["scripts/coverage_restore.py"] = assess.EXTRAS["scripts/coverage_restore.py"]
    with pytest.raises(ValueError):
        assess.verify_candidate(ref, cand)


def test_technical_return_counts_are_separate_from_the_r2_changes():
    coverage=dict(restored_fields=1, movement=1, changed_unit_orders=1, changed_steps=1,
                  uncovered_candidate_fields=6, fields_with_visible_enemy_in_range=3, fields_with_only_last_cover=2)
    first=dict(changed_unit_orders=5)
    game=dict(study=first, selective_counts=first, coverage_counts=coverage)
    rows={("solution92",7272300,"player_0"):game}
    stats=assess.technical(rows)["solution92"]
    assert (stats["restored_fields"], stats["original_r2_changes"], stats["final_changes_vs_base"])==(1,5,4)
    coverage["restored_fields"]=2
    with pytest.raises(ValueError):
        assess.technical(rows)
