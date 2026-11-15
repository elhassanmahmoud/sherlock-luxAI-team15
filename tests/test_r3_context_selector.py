from collections import Counter
from types import SimpleNamespace

import numpy as np

from scripts.r3_context_agent import screened_advice
from scripts.r3_context_table import cell_indices, learn_cells


def test_public_contexts_use_assignment_and_visible_enemy_and_quantize_consistently():
    f = np.zeros((4, 79), dtype=np.float32)
    f[0, 30:35] = [1/24, 0, 1/48, 1, 0]
    f[1, 30:35] = [0, 1/24, 1/48, 1, 1]
    f[2, 73] = .25
    target = cell_indices(f, [0, 2, 1, 2], [2, 0, 3, 1])
    # Where R3 brings the ship nearer, V14/R3 tie, no assignment.
    assert target.tolist() == [0, 18, 27, 26]
    assert np.array_equal(target, cell_indices(f.astype(np.float16), [0, 2, 1, 2], [2, 0, 3, 1]))


def test_largest_positive_training_map_is_removed():
    gain = np.zeros((4, 36), dtype=int)
    gain[:, 0] = [20, 0, 0, 0]
    gain[:, 1] = [2, 2, -2, 0]
    gain[:, 2] = [2, 2, -1, 0]
    assert np.flatnonzero(learn_cells(gain)).tolist() == [2]


def test_filter_uses_both_world_orientations_preserves_shots_and_skips_dead_units():
    lookup = np.zeros(36, dtype=bool)
    f = np.zeros(79)
    f[30], f[33] = 1/24, 1
    lookup[int(cell_indices(f[None], [0], [2])[0])] = True
    for team in (0, 1):
        # canonical RIGHT is world UP on p1. Opposite request is a different context.
        toward, away = (2, 4) if team == 0 else (1, 3)
        base = np.array([[0,0,0], [0,0,0], [5,-2,2], [2,0,0], [0,0,0]], dtype=int)
        proposed = np.array([[toward,0,0], [away,0,0], [2,0,0], [5,1,-1], [toward,0,0]], dtype=int)
        energy = np.full((2,5,1), 100)
        energy[team,4,0] = -1
        obs = dict(match_steps=22, units_mask=np.ones((2,5),bool),
                   units=dict(energy=energy,position=np.full((2,5,2),10)), map_features=dict(tile_type=np.zeros((24,24),int)))
        actor = SimpleNamespace(team_id=team, belief=SimpleNamespace(mirrored=bool(team)),
                                env_cfg={"unit_move_cost":1,"unit_sap_cost":20,"unit_sap_range":4},
                                selective_counts=Counter())
        feats = {k:f for k in range(5)}
        masks = {k:np.ones(6,bool) for k in range(5)}
        actual = screened_advice(actor, obs, base, proposed, feats, masks, lookup)
        assert np.array_equal(actual[0], base[0])
        assert np.array_equal(actual[1:], proposed[1:])
        assert actor.selective_counts["context_v14"] == 1
        masks[0][0] = False
        assert np.array_equal(screened_advice(actor,obs,base,proposed,feats,masks,lookup), proposed)
        masks[0][0] = True
        # A rejected world command does not count as a possible R3/V14 difference.
        obs['units']['energy'][team,0,0] = 0
        assert np.array_equal(screened_advice(actor,obs,base,proposed,feats,masks,lookup), proposed)
        obs['match_steps'] = 0
        assert np.array_equal(screened_advice(actor,obs,base,proposed,feats,masks,lookup), proposed)


def test_validation_counts_real_gains_and_losses_on_both_seats_of_each_map():
    from scripts.r3_context_study import VALID, validation_counts

    cell = np.zeros(36, dtype=bool)
    cell[7] = True
    # Five disagreements on each map, teacher liked V14 three times and R3 once.
    # A further cell favors R3 but is never retained and should not affect the gain.
    counts = np.zeros((24, 36, 3),dtype=int)
    counts[:,7] = [5,3,1]
    counts[:,8] = [2,0,2]
    judged = validation_counts(counts,cell)
    assert judged["passes"]
    r = judged["counts"]["all"]
    assert (r["maps"],r["disagreements"],r["gained"],r["lost"],r["net"]) == (24,168,72,24,48)
    assert r["mean_net_per_map_ci95"] == [2,2]
    assert [r["seed"] for r in judged["by_map"]] == list(VALID)
    # Global profit cannot hide negative net on the Solution maps.
    from scripts.collect_combat_advice import opponent_for
    for idx, seed in enumerate(VALID):
        if opponent_for(seed) == "solution92":
            counts[idx,7] = [5,1,2]
    assert not validation_counts(counts,cell)["checks"]["solution_nonnegative"]


def test_game_roster_includes_distinct_confirmation_duels():
    from scripts.r3_context_games import SEEDS, opponents
    from scripts.r3_context_study import TRAIN, VALID

    ranges = (TRAIN, VALID, *SEEDS.values())
    assert sum(map(len,ranges)) == len({s for block in ranges for s in block})
    assert opponents("screen","context") == ("kaggle3","solution92","v14")
    assert opponents("screen","r3") == ("kaggle3","solution92")
    assert opponents("direct","context") == ("v14",)


def test_collector_protocols_differ_only_in_recording_and_parent_is_always_r3():
    import hashlib
    import json
    from pathlib import Path
    from scripts.collect_combat_advice import canonical_json
    from scripts.r3_context_table import HARD_ONLY_PROTOCOL_SHA, PROTOCOL_SHA, R3_SHA

    # Published receipt for the original soft-target training dataset, from the same collector.
    from scripts import r3_context_table
    root = Path(r3_context_table.__file__).resolve().parents[1]
    receipt = root / "experiments/analysis/movement_dagger_20261115/collection_protocol.json"
    prior = json.loads(receipt.read_bytes())
    prior["student_sha256"] = R3_SHA
    def digest(v):
        return hashlib.sha256(canonical_json(v) + b"\n").hexdigest()
    assert digest(prior) == PROTOCOL_SHA
    assert prior.pop("raw_teacher_policy") == "pre_fallback_scores_v1"
    prior["source_sha256"].pop("scripts/teacher_policy_trace.py")
    assert digest(prior) == HARD_ONLY_PROTOCOL_SHA
