"""Passive observation contracts; distances/choices below are hand calculated."""
import copy
import importlib
import json

import numpy as np
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x
from tests.conftest import ENV_CFG, make_obs


def probe():
    return importlib.import_module("scripts.targeting_probe")


def frame_ctx(positions=((0, 0),), energies=(100,), targets=None, points=((2, 0),), width=7):
    grid = np.zeros((width, width), bool)
    for p in points:
        grid[p] = True
    first = {}
    for i, p in enumerate(positions):
        first.setdefault(p, i)
    return dict(W=width, H=width, ally_ids=np.arange(len(positions)),
                ally_pos=np.array(positions), ally_ene=np.array(energies),
                enemy_coords=np.empty((0, 2), int), enemy_energies=np.array([]),
                enemy_vis_ids=np.array([], int), first_on_tile=first,
                assigned=targets or {0: (2, 0)}, point_tiles=grid,
                candidate=np.zeros_like(grid), passable=np.ones_like(grid),
                nebula=np.zeros_like(grid), energy_map=np.zeros_like(grid, float),
                explored=np.zeros_like(grid), move_cost=3, sap_cost=40,
                sensor_range=2, step=10, match_step=10, match_idx=0,
                config=dict(home_first=False, home_penalty=0, energy_pref=0, sticky=0,
                            safe_moves=True, mask_actions=True, reach_assign=True))


def classify(ctx, masks=None, q=None, actions=None, truth=None):
    n = len(ctx["ally_ids"])
    return probe().classify_frame(
        ctx, masks or {u: np.ones(6, bool) for u in ctx["ally_ids"]},
        np.zeros((n, 6), np.float32) if q is None else q,
        np.zeros((n, 3), int) if actions is None else actions, truth)


def test_bfs_progress_uses_detour_and_actual_mask():
    ctx = frame_ctx()
    ctx["passable"][1, 0] = False
    result = classify(ctx)
    unit = result["units"][0]
    assert unit["target_bfs_distance"] == 4
    assert unit["allowed_target_progress"] == [3]
    assert result["free_own_tiles"][0]["min_bfs_mobile_nonholders"] == 4
    masks = {0: np.array([True, False, True, False, True, True])}
    assert classify(ctx, masks)["units"][0]["allowed_target_progress"] == []


def test_unreachable_is_null_not_manhattan_or_arrival_claim():
    ctx = frame_ctx()
    ctx["passable"][1, :] = False
    out = classify(ctx)
    assert out["units"][0]["target_bfs_distance"] is None
    assert out["free_own_tiles"][0]["min_bfs_living"] is None
    assert out["free_own_tiles"][0]["allowed_first_progress_units"] == []


def test_hidden_enemy_changes_only_posthoc():
    ctx = frame_ctx()
    before = classify(ctx)
    truth = dict(point_tiles=ctx["point_tiles"].copy(),
                 enemy_positions=np.array([[2, 0]]), enemy_energy=np.array([80]))
    after = classify(ctx, truth=truth)
    assert after.pop("posthoc") == dict(
        point_tiles=truth["point_tiles"].tolist(),
        enemies=[dict(position=[2, 0], energy=80.0)],
        free_own_tiles=[dict(position=[2, 0], true_point=True,
                             enemy_occupied=True, hidden_enemy_occupied=True)])
    before.pop("posthoc")
    assert after == before


def test_negative_first_entry_never_becomes_holder_and_stackers_stay_separate():
    ctx = frame_ctx(positions=((2, 0), (2, 0), (2, 0), (1, 1)),
                    energies=(-1, 0, 100, 2))
    units = classify(ctx)["units"]
    assert [u["energy_class"] for u in units] == [
        "negative", "below_move_cost", "sap_ready", "below_move_cost"]
    assert [u["holder"] for u in units] == [False, True, False, False]
    assert [u["sole_holder"] for u in units] == [False, False, False, False]
    assert units[0]["legacy_first_on_tile"] is True
    assert units[0]["stacker"] is False
    assert units[2]["stacker"] is True
    assert units[2]["mobile_nonholder"] is True
    assert units[3]["mobile_nonholder"] is False


def test_only_nonnegative_unit_is_sole_holder_even_with_negative_legacy_first():
    ctx = frame_ctx(positions=((2, 0), (2, 0)), energies=(-1, 100))
    ctx["ally_ids"] = np.array([1, 0])
    units = {u["uid"]: u for u in classify(ctx)["units"]}
    assert units[1]["holder"] and units[1]["sole_holder"]
    assert not units[1]["mobile_nonholder"]
    assert units[0]["legacy_first_on_tile"] and not units[0]["holder"]


def test_holder_uses_lowest_living_id_even_if_input_order_differs():
    ctx = frame_ctx(positions=((2, 0), (2, 0)), energies=(10, 100))
    ctx["ally_ids"] = np.array([1, 0])
    units = {u["uid"]: u for u in classify(ctx)["units"]}
    assert units[0]["holder"] and not units[1]["holder"]


def test_raw_masked_and_final_choices_and_reasons_remain_distinct():
    ctx = frame_ctx(positions=((0, 0),), energies=(20,))
    masks = {0: np.array([1, 0, 0, 1, 0, 0], bool)}
    q = np.array([[1, 0, 9, 8, 0, 10]], np.float32)
    unit = classify(ctx, masks, q, np.array([[0, 0, 0]]))["units"][0]
    assert (unit["raw_argmax"], unit["masked_argmax"], unit["final_action"]) == (5, 3, [0, 0, 0])
    assert unit["mask_reasons"]["1"] == ["map_edge"]
    assert unit["mask_reasons"]["2"] == ["later_guard_unresolved"]
    assert unit["mask_reasons"]["5"] == ["below_sap_cost"]
    assert unit["provenance"] == "inline_transitions_unresolved"


def test_classification_copies_inputs_and_is_strict_json():
    ctx = frame_ctx()
    original = copy.deepcopy(ctx)
    q = np.arange(6, dtype=np.float32)[None]
    q_before = q.copy()
    masks = {0: np.ones(6, bool)}
    actions = np.zeros((1, 3), int)
    out = classify(ctx, masks, q, actions)
    json.dumps(out, allow_nan=False)
    out["public"]["ally_pos"][0][0] = 99
    out["units"][0]["q_values"][0] = 99
    assert np.array_equal(ctx["ally_pos"], original["ally_pos"])
    assert np.array_equal(q, q_before)
    assert masks[0].all() and not actions.any()


def swap_ctx():
    return frame_ctx(positions=((0, 0), (3, 0)), energies=(100, 100),
                     targets={0: (4, 0), 1: (2, 0)}, points=((4, 0), (2, 0)))


def test_two_owner_counterfactual_keeps_target_set_and_records_five_to_three():
    out = classify(swap_ctx())["two_owner_swap"]
    assert out["admitted"] is True
    assert out["pairs_checked"] == 1
    assert out["improvements"] == [dict(units=[0, 1], old_targets=[[4, 0], [2, 0]],
                                        new_targets=[[2, 0], [4, 0]], old_bfs_sum=5,
                                        new_bfs_sum=3, saved_bfs=2)]


@pytest.mark.parametrize("obstacle", ["holder", "unreachable", "masked", "bonus", "manhattan"])
def test_two_owner_rejects_unavailable_supply_or_incompatible_costs(obstacle):
    ctx = swap_ctx()
    masks = {0: np.ones(6, bool), 1: np.ones(6, bool)}
    if obstacle == "holder":
        ctx["point_tiles"][0, 0] = True
    elif obstacle == "unreachable":
        ctx["passable"][1, :] = False
    elif obstacle == "masked":
        masks[0][1:5] = False
    elif obstacle == "bonus":
        ctx["config"]["energy_pref"] = 1
    else:
        ctx["config"]["reach_assign"] = False
    out = classify(ctx, masks)["two_owner_swap"]
    assert out["improvements"] == []
    if obstacle in ("bonus", "manhattan"):
        assert out["admitted"] is False


class FixedQ(torch.nn.Module):
    feat_dim = 79

    def __init__(self, values):
        super().__init__()
        self.values = torch.tensor(values, dtype=torch.float32)
        self.calls = 0

    def forward(self, x):
        self.calls += 1
        return self.values.repeat(x.shape[0], 1)


def agent_for(team=0):
    a = Agent_x(f"player_{team}", train=False, cfg=AgentConfig(buffer_capacity=8))
    a.set_env_cfg(ENV_CFG)
    a.set_to_eval_mode()
    a.q = FixedQ([1, 12, 6, 3, 0, 2])
    return a


@pytest.mark.parametrize("team,start,native", [(0, (0, 0), 2), (1, (23, 23), 1)])
def test_observer_captures_pre_mask_q_actual_features_and_canonical_actions(team, start, native):
    a = agent_for(team)
    a.extra_q = [FixedQ([3, 8, 4, 1, 0, 0])]
    obs = make_obs(10, 10, team=team, units=[(*start, 100)])
    with probe().DecisionObserver(a) as observer:
        actions = a.act(10, obs)
        frame = observer.last_frame
    assert a.q.calls == a.extra_q[0].calls == 1
    assert actions[0].tolist() == [native, 0, 0]
    unit = frame["units"][0]
    assert unit["q_values"] == [2, 10, 5, 2, 0, 1]
    assert unit["raw_argmax"] == 1 and unit["masked_argmax"] == 2
    assert unit["final_action"] == [2, 0, 0]
    assert unit["native_action"] == [native, 0, 0]
    assert len(unit["features"]) == 79
    assert frame["public"]["ally_pos"][0] == [0, 0]


def test_wrapper_events_copy_mutable_arguments_before_original_changes_them():
    a = agent_for()
    original = a._overkill
    planned = np.array([3.0])
    ctx = frame_ctx()
    with probe().DecisionObserver(a) as observer:
        # The real method is read-only here; mutate caller-owned memory afterwards.
        a._overkill(ctx, 0, (1, 0, 1), planned)
        planned[0] = 99
        event = observer.events[0]
    assert event["method"] == "_overkill" and event["uid"] == 0
    assert event["arguments"]["planned_dmg"] == [3.0]
    assert event["return"] is False
    assert a._overkill == original


def test_artillery_wrapper_records_actual_caller_move_then_overkill_sap():
    a = agent_for()
    a.q = FixedQ([0, 0, 10, 0, 0, 0])
    a.cfg.art_sap = 1
    a.cfg.art_min_hits = 1
    a.cfg.sap_no_overkill = True
    # Real safe artillery: one unarmed enemy, enough sap energy and safety.
    obs = make_obs(10, 10, units=[(5, 5, 200)], enemies=[(8, 5, 20)])
    with probe().DecisionObserver(a) as observer:
        a.act(10, obs)
        events = observer.last_frame["events"]
    art = next(e for e in events if e["method"] == "_artillery_ok")
    overkill = next(e for e in events if e["method"] == "_overkill")
    assert art["caller_action"] == 2 and art["return"] is True
    assert overkill["caller_action"] == 5


def test_nebula_posterior_is_copied_without_calling_estimator_again():
    a = agent_for()
    a.param_est.log_neb[:] = [0, 0, 0, 0, 0, 12]
    a.param_est.n_neb = 3
    with probe().DecisionObserver(a) as observer:
        a.act(10, make_obs(10, 10, units=[(0, 0, 100)]))
        estimate = observer.last_frame["public"]["nebula_estimate"]
    assert estimate["samples"] == 3
    assert estimate["value"] == 25 and estimate["confidence"] > .99


def test_observer_cleanup_after_agent_error_restores_instance_and_hooks():
    a = agent_for()
    original_act = a.act
    original_override = a._rule_override
    def fail(ctx, uid, mask, a):
        raise RuntimeError("original rule failed")
    a._rule_override = fail
    wrapped_names = {"act", *probe().RULE_METHODS}
    original_keys = set(a.__dict__) & wrapped_names
    with pytest.raises(RuntimeError, match="original rule failed"):
        with probe().DecisionObserver(a):
            a.act(10, make_obs(10, 10, units=[(0, 0, 100)]))
    assert set(a.__dict__) & wrapped_names == original_keys
    assert a.act == original_act and a._rule_override is fail
    assert len(a.q._forward_hooks) == 0
    a._rule_override = original_override


@pytest.mark.parametrize("kind", ["training", "five_actions", "cnn"])
def test_unsupported_policy_is_rejected_before_any_hooks(kind):
    a = agent_for()
    if kind == "training":
        a.training = True
    elif kind == "five_actions":
        a.n_actions = 5
    else:
        a.cnn_policy = object()
    with pytest.raises(ValueError):
        with probe().DecisionObserver(a):
            pass
    assert len(a.q._forward_hooks) == 0 and "act" not in a.__dict__


def test_reset_never_reuses_stale_cache_and_free_duration_restarts():
    a = agent_for()
    a.belief.point_tiles[2, 0] = True
    a.belief._coords_dirty = True
    with probe().DecisionObserver(a) as observer:
        a.act(10, make_obs(10, 10, units=[(0, 0, 100)]))
        assert observer.last_frame["free_own_tiles"][0]["free_duration"] == 1
        a.act(11, make_obs(11, 11, units=[(0, 0, 100)]))
        assert observer.last_frame["free_own_tiles"][0]["free_duration"] == 2
        a.act(101, make_obs(101, 0, units=[(0, 0, 100)]))
        assert observer.last_frame["status"] == "reset"
        assert observer.last_frame["units"] == []
        a.act(102, make_obs(102, 1, units=[(0, 0, 100)]))
        assert observer.last_frame["free_own_tiles"][0]["free_duration"] == 1


def test_missing_and_mismatched_cache_have_explicit_status():
    a = agent_for()
    a.act = lambda step, obs: np.zeros((16, 3), int)
    with probe().DecisionObserver(a) as observer:
        a.act(10, make_obs(10, 10))
        assert observer.last_frame["status"] == "missing_cache"
        a._cache = (9, frame_ctx(), [], {}, {}, {})
        a.act(10, make_obs(10, 10))
        assert observer.last_frame["status"] == "cache_mismatch"


def test_real_sensor_freshness_does_not_treat_symmetry_as_energy_observation():
    a = agent_for()
    a.belief.use_symmetry = True
    obs = make_obs(10, 10, units=[(0, 0, 100)], sensor_all=False)
    obs["sensor_mask"][0, 0] = True
    with probe().DecisionObserver(a) as observer:
        a.act(10, obs)
        age = observer.last_frame["public"]["energy_observation_age"]
        assert age[0][0] == 0 and age[23][23] is None
        obs2 = make_obs(11, 11, units=[(0, 0, 100)], sensor_all=False)
        a.act(11, obs2)
        assert observer.last_frame["public"]["energy_observation_age"][0][0] == 1


def test_native_action_digest_includes_dtype_shape_and_both_teams():
    p = probe()
    arrays = {"player_0": np.zeros((2, 3), np.int64), "player_1": np.zeros((2, 3), np.int64)}
    first = p.action_bytes(arrays)
    arrays["player_1"][0, 0] = 2
    assert first != p.action_bytes(arrays)
    assert p.action_bytes({"player_0": np.zeros((2, 3), np.int64)}) != p.action_bytes(
        {"player_0": np.zeros((3, 2), np.int64)})
    assert p.action_bytes({"player_0": np.zeros((2, 3), np.int64)}) != p.action_bytes(
        {"player_0": np.zeros((2, 3), np.float64)})


def test_player_one_sap_delta_reflection_copies_native_input():
    native = np.array([[5, -2, 3], [4, 0, 0]])
    assert probe().canonical_actions(native, True).tolist() == [[5, -3, 2], [3, 0, 0]]
    assert native.tolist() == [[5, -2, 3], [4, 0, 0]]


def test_synthetic_sequence_is_action_and_rng_passive():
    import random
    plain, watched = agent_for(), agent_for()
    observations = [make_obs(i, i, units=[(0, 0, 100)], enemies=[(3, 0, 40)]) for i in range(10, 13)]
    expected = [plain.act(i, copy.deepcopy(o)).tobytes() for i, o in enumerate(observations, 10)]
    before = (random.getstate(), np.random.get_state(), torch.get_rng_state().clone(),
              copy.deepcopy(watched.rng.bit_generator.state))
    with probe().DecisionObserver(watched):
        actual = [watched.act(i, copy.deepcopy(o)).tobytes() for i, o in enumerate(observations, 10)]
    assert actual == expected and watched._enemy_prev == plain._enemy_prev
    assert random.getstate() == before[0]
    assert np.array_equal(np.random.get_state()[1], before[1][1])
    assert torch.equal(torch.get_rng_state(), before[2])
    assert watched.rng.bit_generator.state == before[3]


@pytest.mark.parametrize("failure", [None, "bytes", "baseline", "cache"])
def test_cli_manifest_checks_both_passivity_and_original_baseline(tmp_path, monkeypatch, failure):
    import gzip
    p = probe()
    weights = tmp_path / "weights.pth"
    weights.write_bytes(b"fake weights: no model should be loaded in this CLI unit test")
    keys = tmp_path / "keys.json"
    keys.write_text(json.dumps(dict(keys=[dict(seed=831000, side="player_0", group="control")],
                                    source="experiments/analysis/night_20261101/selection_baseline.csv")))
    output = tmp_path / "output"
    row = dict(seed=831000, side="player_0", opponent="solution92", steps=303, reset_steps=3,
               decision_steps=300, our_wins=2, opp_wins=1, result=1.0, our_points=793,
               opp_points=452, point_counting_version=2, matches=[{}, {}, {}],
               config={}, caught_errors=0, action_sha256="abc", statuses={})
    def controlled_game(seed, side, path, trace_path=None):
        result = copy.deepcopy(row)
        if failure == "baseline":
            result["our_points"] = 792
        if trace_path:
            with gzip.open(trace_path, "xt") as stream:
                stream.write('{"status":"decision"}\n')
            result["statuses"] = {"reset": 3, "decision": 300}
            if failure == "bytes":
                result["action_sha256"] = "different"
            elif failure == "cache":
                result["statuses"] = {"cache_mismatch": 303}
        return result
    monkeypatch.setattr(p, "_play", controlled_game)
    if failure:
        with pytest.raises(RuntimeError, match="gate failed"):
            p.run_probe(weights, keys, output)
    else:
        p.run_probe(weights, keys, output)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == ("failed" if failure else "complete")
    assert manifest["completed_games"] == 2
    assert manifest["games"][0]["passivity"]["action_sha256"] is (failure != "bytes")
    assert manifest["games"][0]["baseline_reproduction"]["our_points"] is (failure != "baseline")


def test_cli_rejects_existing_output_missing_weights_and_unknown_opponent_before_games(tmp_path):
    keys = tmp_path / "keys.json"
    keys.write_text(json.dumps(dict(keys=[dict(seed=831000, side="player_0", group="control")],
                                    source="experiments/analysis/night_20261101/selection_baseline.csv")))
    output = tmp_path / "output"
    output.mkdir()
    with pytest.raises(FileExistsError):
        probe().run_probe(tmp_path / "missing.pth", keys, output)
    output.rmdir()
    with pytest.raises(FileNotFoundError):
        probe().run_probe(tmp_path / "missing.pth", keys, output)
    assert not output.exists()
    weights = tmp_path / "present.pth"
    weights.touch()
    document = json.loads(keys.read_text())
    document["keys"][0]["opponent"] = "default"
    keys.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="solution92"):
        probe().run_probe(weights, keys, output)
    assert not output.exists()
