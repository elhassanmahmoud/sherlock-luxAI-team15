"""Final rescue alignment: synthetic observations/checkpoints, no Lux games."""
import importlib
import importlib.util
import json

import numpy as np
import pytest
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.config import AgentConfig
from tests.conftest import make_obs
from tests.test_rules_1910 import _stay_agent


def rescue_agent(enabled, *, train=True, preferred=geo.STAY, **config):
    a = _stay_agent(cand_rescue=True, rescue_after=30, buffer_capacity=64,
                    eps_start=0., eps_end=0., **config)
    # Setting the proposed flag dynamically keeps the first red test focused
    # on missing behavior, rather than failing at dataclass construction.
    a.cfg.rescue_in_training = enabled
    if preferred != geo.STAY:
        class Preferred(torch.nn.Module):
            def forward(self, x):
                q = torch.zeros((len(x), 6))
                q[:, preferred] = 1.
                return q
        a.q = Preferred()
    if train:
        a.set_to_train_mode()
    a.learn_enabled = False
    a.autosave_on_terminate = False
    a._first_relic_step = 0
    return a


@pytest.mark.parametrize("preferred", [geo.STAY, geo.LEFT])
def test_training_rescue_changes_final_action_and_replay_only_when_enabled(preferred):
    outcomes = []
    for enabled in (False, True):
        a = rescue_agent(enabled, preferred=preferred)
        obs = make_obs(40, 40, units=[(5, 9, 100)], relics=[(9, 9)])
        action = a.act(40, obs)
        outcomes.append(int(action[0, 0]))
        nx = 5 + int(geo.DIR_DX[int(action[0, 0])])
        ny = 9 + int(geo.DIR_DY[int(action[0, 0])])
        nxt = make_obs(41, 41, units=[(nx, ny, 97)], relics=[(9, 9)])
        a.update(40, obs, 0., action, False, nxt)
        assert a.buffer.size == 1
        assert int(a.buffer.a[0]) == int(action[0, 0])
    assert outcomes == [preferred, geo.RIGHT]


def test_default_is_off_and_eval_actions_ignore_training_flag():
    assert getattr(AgentConfig(), "rescue_in_training", None) is False
    obs = make_obs(40, 40, units=[(5, 9, 100)], relics=[(9, 9)])
    a, b = rescue_agent(False, train=False), rescue_agent(True, train=False)
    np.testing.assert_array_equal(a.act(40, obs), b.act(40, obs))
    assert a.act(40, obs)[0, 0] == geo.RIGHT


@pytest.mark.parametrize("blocked", ["early", "known_point", "near_enemy"])
def test_training_rescue_keeps_existing_safety_conditions(blocked):
    a = rescue_agent(True)
    if blocked == "early":
        a._first_relic_step = 39
    elif blocked == "known_point":
        a.belief.point_tiles[20, 20] = True
    enemies = [(5, 10, 100)] if blocked == "near_enemy" else []
    obs = make_obs(40, 40, units=[(5, 9, 100)], enemies=enemies, relics=[(9, 9)])
    assert a.act(40, obs)[0, 0] == geo.STAY


def test_flag_does_not_enable_standalone_eval_only_rules_in_training():
    a = rescue_agent(True, obey_target=True, neb_cand=True, idle_approach=True)
    a.cfg.cand_rescue = False
    obs = make_obs(40, 40, units=[(5, 9, 100)], relics=[(9, 9)])
    assert a.act(40, obs)[0, 0] == geo.STAY


def test_final_wrapper_available():
    assert importlib.util.find_spec("scripts.final_rescue_train") is not None


@pytest.fixture
def adapt():
    assert importlib.util.find_spec("scripts.final_rescue_train") is not None
    return importlib.import_module("scripts.final_rescue_train")


from tests.test_targeting_adapt import source, loaded  # synthetic checkpoints only
# These unchanged contract tests exercise the shared real identity proofs and
# this wrapper's separate input/output binding with synthetic model files.
from tests.test_targeting_adapt import (
    test_prepare_rejects_bad_source_before_output,
    test_prepare_rejects_existing_and_protected_outputs,
    test_actual_initial_proof_requires_loaded_tensor_target_config_and_fresh_state,
    test_actual_initial_proof_rejects_bad_loaded_state,
    test_run_preflight_rejects_corrupt_inputs_before_learner_or_game,
    test_run_arm_rejects_existing_output_without_entering_finetune,
)


def test_prepare_fixed_pair_and_training_schedule(adapt, source, tmp_path):
    from scripts.night_train_pilot import tensor_sha256
    prepared = tmp_path / "prepared"
    manifest = adapt.prepare(source[0], prepared)
    assert set(manifest["arms"]) == {"control18", "adapt18"}
    control = manifest["arms"]["control18"]
    rescue = manifest["arms"]["adapt18"]
    assert {k for k in control["config"] if control["config"][k] != rescue["config"][k]} == {"rescue_in_training"}
    for arm, enabled in (("control18", False), ("adapt18", True)):
        _, entry, init = adapt.check_prepared(prepared, arm)
        cp = torch.load(init / "weights/agent.pth", weights_only=True)
        assert entry["component_index"] == 18 and entry["run_seed"] == 29
        assert tensor_sha256(cp["q"]) == tensor_sha256(source[1][18])
        assert tensor_sha256(cp["target_q"]) == tensor_sha256(source[1][18])
        assert cp["env_steps"] == 60000 and cp["learn_steps"] == 0
        assert not cp["ensemble"] and "opt" not in cp
        assert cp["cfg"]["rescue_in_training"] is enabled
        assert not any(cp["cfg"][k] for k in ("point_pair_swap", "art_move_guard", "zone_rescue"))
        assert cp["cfg"]["cand_rescue"] and cp["cfg"]["rescue_after"] == 30
    rows = adapt.rollout_plan("control18")
    assert rows == adapt.rollout_plan("adapt18") and len(rows) == 1320
    assert [(r["phase"], r["seed"], r["side"]) for r in (rows[0], rows[119], rows[120], rows[-1])] == [
        ("prefill", 495000, "player_0"), ("prefill", 495059, "player_1"),
        ("train", 493000, "player_0"), ("train", 493599, "player_1")]
    assert len(adapt.validation_plan()) == 96
    assert {r["after_games"] for r in adapt.validation_plan()} == {0, 600, 1200}


@pytest.mark.parametrize("fail", [False, True])
def test_validation_uses_v14_flags_and_restores_learning(adapt, loaded, monkeypatch, fail):
    from scripts import experiment
    learners, _, _ = loaded
    a = learners.agents["player_0"]
    a.cfg.rescue_in_training = True
    before = adapt.learner_identity(learners)
    seen = []
    def game(env, agent, opp, seed, side, train):
        seen.append((agent.cfg.point_pair_swap, agent.cfg.art_move_guard,
                     agent.cfg.zone_rescue, agent.cfg.rescue_in_training,
                     agent.training, agent.learn_enabled, agent.epsilon))
        if fail:
            raise RuntimeError("synthetic failure")
        return dict(seed=seed, side=side, result=.5)
    monkeypatch.setattr(experiment, "play_game", game)
    monkeypatch.setattr(experiment, "make_opponent", lambda *args: object())
    if fail:
        with pytest.raises(RuntimeError, match="synthetic failure"):
            adapt.isolated_validation(None, learners, [500000], ["default"])
    else:
        assert len(adapt.isolated_validation(None, learners, [500000], ["default"])) == 2
    assert seen[0] == (False, False, False, False, False, False, 0.)
    assert adapt.learner_identity(learners) == before


def test_action_audit_checks_emission_and_actual_replay_writes(adapt):
    a = rescue_agent(True)
    obs = make_obs(40, 40, units=[(5, 9, 100)], relics=[(9, 9)])
    with adapt.action_audit(a) as proof:
        action = a.act(40, obs)
        nxt = make_obs(41, 41, units=[(6, 9, 97)], relics=[(9, 9)])
        a.update(40, obs, 0., action, False, nxt)
    assert proof["act_calls"] == proof["update_calls"] == 1
    assert proof["checked_replay_transitions"] == 1
    assert len(proof["transcript_sha256"]) == 64


def test_action_audit_rejects_corrupt_stored_action_and_restores_methods(adapt):
    a = rescue_agent(True)
    obs = make_obs(40, 40, units=[(5, 9, 100)], relics=[(9, 9)])
    original_push = a.buffer.push
    def corrupt(s, action, *args):
        return original_push(s, geo.LEFT, *args)
    a.buffer.push = corrupt
    previous = a.act, a.update
    with pytest.raises(ValueError, match="replay"):
        with adapt.action_audit(a):
            action = a.act(40, obs)
            nxt = make_obs(41, 41, units=[(6, 9, 97)], relics=[(9, 9)])
            a.update(40, obs, 0., action, False, nxt)
    assert (a.act, a.update) == previous


def test_action_audit_mirrors_world_move_and_checks_wrapped_replay(adapt):
    a = rescue_agent(True)
    a.new_game("player_1")
    a._first_relic_step = 0
    a.buffer.pos = a.buffer.capacity - 1
    unit = (*geo.mirror_xy(5, 9), 100)
    relic = geo.mirror_xy(9, 9)
    obs = make_obs(40, 40, team=1, units=[unit], relics=[relic])
    with adapt.action_audit(a) as proof:
        action = a.act(40, obs)
        assert action[0, 0] == geo.UP  # antidiagonal mirror of canonical RIGHT
        nxt = make_obs(41, 41, team=1, units=[(*geo.mirror_xy(6, 9), 97)], relics=[relic])
        a.update(40, obs, 0., action, False, nxt)
    assert a.buffer.pos == 0 and a.buffer.a[-1] == geo.RIGHT
    assert proof["checked_replay_transitions"] == 1


def test_incomplete_receipt_is_rejected(adapt, tmp_path):
    receipt = tmp_path / "final_receipt.json"
    receipt.write_text(json.dumps(dict(status="incomplete", arm="adapt18")))
    with pytest.raises(ValueError):
        adapt.validate_final_receipt(receipt, arm="adapt18")


@pytest.fixture
def simulated_final_loop(adapt, monkeypatch, tmp_path):
    """Real finetune control flow, synthetic episode/action-audit boundary.

    This tests receipts and restoration, not game mechanics or actual gradients.
    The separate observation tests exercise the real action audit and replay.
    """
    from contextlib import contextmanager
    from tests.test_targeting_adapt import simulated_finetune
    finetune = simulated_finetune.__wrapped__(adapt, monkeypatch)
    from scripts import experiment
    monkeypatch.setattr(finetune, "RUNS", tmp_path / "runs")
    original_game = finetune.play_game
    def episode(env, a, opponent, seed, side, train):
        a.ep_stats["training_rescue_unit_steps"] = int(a.cfg.rescue_in_training)
        a.ep_stats["training_rescue_action_changes"] = int(a.cfg.rescue_in_training)
        row = original_game(env, a, opponent, seed, side, train)
        for key in experiment.GAME_FIELDS:
            row.setdefault(key, 0)
        return row
    original_validation = experiment.play_game
    def validation(*args, **kwargs):
        row = original_validation(*args, **kwargs)
        for key in experiment.GAME_FIELDS:
            row.setdefault(key, 0)
        return row
    @contextmanager
    def synthetic_action_evidence(agent):
        yield dict(act_calls=303, update_calls=303, checked_replay_transitions=303,
                   transcript_sha256="0" * 64)
    monkeypatch.setattr(finetune, "play_game", episode)
    monkeypatch.setattr(experiment, "play_game", validation)
    monkeypatch.setattr(adapt, "action_audit", synthetic_action_evidence)
    return finetune


@pytest.mark.parametrize("arm", ["control18", "adapt18"])
def test_simulated_complete_loop_has_exact_counts_receipt_and_restored_hooks(
        adapt, source, tmp_path, monkeypatch, simulated_final_loop, arm):
    import sys
    finetune = simulated_final_loop
    prepared = tmp_path / "prepared"
    adapt.prepare(source[0], prepared)
    old_hooks = tuple(getattr(finetune, key) for key in ("Learners", "play_game", "play_set", "make_opponent"))
    old_argv = sys.argv
    record = adapt.run_arm(prepared, arm, "synthetic")
    receipt_path = tmp_path / "runs/synthetic/final_receipt.json"
    receipt = adapt.validate_final_receipt(receipt_path, arm=arm)
    assert record["status"] == "done" and not record["counter_review_required"]
    assert (receipt["actual_train_games"], receipt["actual_prefill_games"], receipt["actual_validation_games"]) == (1200, 120, 96)
    assert (receipt["learn_steps"], receipt["env_steps"]) == (180000, 459960)
    assert receipt["final_action_audit"]["act_calls"] == 399960
    assert receipt["rescue_action_changes"] == (1320 if arm == "adapt18" else 0)
    assert old_hooks == tuple(getattr(finetune, key) for key in ("Learners", "play_game", "play_set", "make_opponent"))
    assert sys.argv is old_argv and adapt._VARIANT not in adapt.VARIANTS
    with pytest.raises(ValueError, match="wrong-role"):
        adapt.validate_final_receipt(receipt_path, arm="adapt18" if arm == "control18" else "control18")
    checkpoint = torch.load(receipt["final_checkpoint"], weights_only=True)
    checkpoint["learn_steps"] -= 1
    torch.save(checkpoint, receipt["final_checkpoint"])
    with pytest.raises(ValueError, match="checkpoint"):
        adapt.validate_final_receipt(receipt_path, arm=arm)


@pytest.mark.parametrize("damage", ["updates", "rescue", "prefill_only", "validation"])
def test_simulated_failure_never_issues_receipt_and_restores_hooks(
        adapt, source, tmp_path, monkeypatch, simulated_final_loop, damage):
    from scripts import experiment
    finetune = simulated_final_loop
    prepared = tmp_path / "prepared"
    adapt.prepare(source[0], prepared)
    game = finetune.play_game
    def broken(env, a, opponent, seed, side, train):
        row = game(env, a, opponent, seed, side, train)
        if damage == "updates" and a.learn_enabled:
            a.learn_steps -= 1
        if damage == "rescue" or (damage == "prefill_only" and a.learn_enabled):
            a.ep_stats["training_rescue_action_changes"] = 0
        return row
    monkeypatch.setattr(finetune, "play_game", broken)
    if damage == "validation":
        def bad_validation(*args, **kwargs):
            raise RuntimeError("synthetic validation failure")
        monkeypatch.setattr(experiment, "play_game", bad_validation)
    hooks = tuple(getattr(finetune, key) for key in ("Learners", "play_game", "play_set", "make_opponent"))
    with pytest.raises((ValueError, RuntimeError)):
        adapt.run_arm(prepared, "adapt18", "failed")
    assert not (tmp_path / "runs/failed/final_receipt.json").exists()
    assert json.loads((prepared / "run_records/failed.json").read_text())["status"] == "incomplete"
    assert hooks == tuple(getattr(finetune, key) for key in ("Learners", "play_game", "play_set", "make_opponent"))


@pytest.mark.parametrize("damage", ["initial", "prefill", "validations", "before_train", "adam", "rollout", "val_steps", "csv_schema"])
def test_receipt_reader_rejects_missing_or_contradictory_learning_evidence(
        adapt, source, tmp_path, monkeypatch, simulated_final_loop, damage):
    from scripts.night_train_pilot import file_sha256
    prepared = tmp_path / "prepared"
    adapt.prepare(source[0], prepared)
    adapt.run_arm(prepared, "control18", "complete")
    directory = tmp_path / "runs/complete"
    receipt_path = directory / "final_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    audit_path = directory / "rescue_training_audit.json"
    audit = json.loads(audit_path.read_text())
    if damage in ("initial", "prefill", "validations", "before_train"):
        audit.pop(damage)
    elif damage == "adam":
        cp = torch.load(receipt["final_checkpoint"], weights_only=True)
        cp["opt"]["state"] = {}
        torch.save(cp, receipt["final_checkpoint"])
        receipt["final_checkpoint_sha256"] = file_sha256(receipt["final_checkpoint"])
        audit["end"]["saved_weights_sha256"] = receipt["final_checkpoint_sha256"]
        audit["end"]["learning"]["optimizer_sha256"] = adapt.experiment.state_sha256(cp["opt"])
    elif damage == "rollout":
        path = directory / "rollouts.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[120]["identity"]["learning"]["learn_steps"] = 0
        path.write_text("\n".join(json.dumps(row) for row in rows))
        receipt["rollouts_sha256"] = file_sha256(path)
    elif damage == "val_steps":
        path = directory / "validation_games.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[0]["steps"] = 302
        path.write_text("\n".join(json.dumps(row) for row in rows))
        receipt["validation_sha256"] = file_sha256(path)
    else:
        path = directory / "train.csv"
        path.write_text("game\n" + "\n".join(map(str, range(1200))))
        receipt["train_csv_sha256"] = file_sha256(path)
    audit_path.write_text(json.dumps(audit))
    receipt["audit_sha256"] = file_sha256(audit_path)
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        adapt.validate_final_receipt(receipt_path, arm="control18")
