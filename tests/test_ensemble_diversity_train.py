"""New six-member wave: synthetic checkpoints/episodes, no Lux games."""
import copy
import importlib
import importlib.util
import json
import signal
import sys
from contextlib import contextmanager

import numpy as np
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet


def test_diversity_runner_exists():
    assert importlib.util.find_spec("scripts.ensemble_diversity_train") is not None


@pytest.fixture
def wave():
    assert importlib.util.find_spec("scripts.ensemble_diversity_train") is not None
    return importlib.import_module("scripts.ensemble_diversity_train")


@pytest.fixture
def source(wave, monkeypatch, tmp_path):
    cfg = AgentConfig(hidden=8, buffer_capacity=64, learn_start=4,
                      cand_rescue=True, rescue_after=30).to_dict()
    model = QNet(79, 6, hidden=8, dueling=True)
    states = []
    for index in range(36):
        state = copy.deepcopy(model.state_dict())
        state["body.0.bias"] += index / 100
        states.append(state)
    path = tmp_path / "V14.pth"
    torch.save(dict(q=states[0], target_q=states[0], cfg=cfg, feature_dim=79,
                    n_actions=6, ensemble=states[1:], ensemble_dims=[79] * 35), path)
    monkeypatch.setattr(wave, "SOURCE_SHA", wave.file_sha256(path))
    return path, states, cfg


def test_prepare_has_three_paired_origins_and_six_fresh_seed_blocks(wave, source, tmp_path):
    prepared = tmp_path / "prepared"
    manifest = wave.prepare(source[0], prepared)
    assert list(manifest["arms"]) == ["A0", "B0", "A1", "B1", "A2", "B2"]
    all_maps = set()
    for index, arm in enumerate(manifest["arms"]):
        _, entry, init = wave.check_prepared(prepared, arm)
        assert (entry["component_index"], entry["run_seed"]) == (18 + 6 * (index // 2), index)
        cp = torch.load(init / "weights/agent.pth", weights_only=True)
        assert cp["env_steps"] == 60000 and cp["learn_steps"] == 0
        assert not cp["ensemble"] and "opt" not in cp
        assert wave.tensor_sha256(cp["q"]) == wave.tensor_sha256(source[1][entry["component_index"]])
        assert wave.tensor_sha256(cp["target_q"]) == entry["tensor_sha256"]
        changed = {k for k in source[2] if source[2][k] != cp["cfg"][k]}
        assert changed == {"lr", "rules_in_training", "rules_in_training_all", "rescue_in_training"}
        assert cp["cfg"]["lr"] == 5e-5
        rows = wave.rollout_plan(arm)
        assert len(rows) == 3120
        assert [rows[i]["phase"] for i in (0, 119, 120, -1)] == ["prefill", "prefill", "train", "train"]
        assert rows[120]["seed"] == 1100000 + 10000 * index
        assert rows[-1]["seed"] == 1101499 + 10000 * index
        maps = {r["seed"] for r in rows}
        assert not (maps & all_maps)
        all_maps |= maps
    validation = wave.validation_plan()
    assert len(validation) == 128
    assert {r["after_games"] for r in validation} == {0, 1000, 2000, 3000}
    assert {r["seed"] for r in validation} == set(range(1300000, 1300008))
    assert not (all_maps & {r["seed"] for r in validation})


def test_smoke_has_separate_maps_and_cannot_run_as_production(wave, source, tmp_path):
    prepared = tmp_path / "smoke"
    manifest = wave.prepare(source[0], prepared, smoke=True)
    assert manifest["smoke"] is True
    assert len(wave.rollout_plan("A0", smoke=True)) == 4
    assert len(wave.validation_plan(smoke=True)) == 8
    assert not ({r["seed"] for r in wave.rollout_plan("A0", smoke=True)} &
                {r["seed"] for r in wave.rollout_plan("A0")})
    with pytest.raises(ValueError, match="smoke"):
        wave.run_arm(prepared, "A0", "bad-mode")


@pytest.mark.parametrize("corruption", ["source", "init", "manifest", "replay", "pins"])
def test_preflight_rejects_changed_inputs(wave, source, tmp_path, corruption):
    prepared = tmp_path / "prepared"
    wave.prepare(source[0], prepared)
    if corruption == "source":
        source[0].write_bytes(b"changed source")
    elif corruption == "init":
        (prepared / "A0/weights/agent.pth").write_bytes(b"changed init")
    elif corruption == "replay":
        (prepared / "A0/weights/agent.buffer.npz").write_bytes(b"unexpected replay")
    else:
        path = prepared / "manifest.json"
        data = json.loads(path.read_text())
        if corruption == "manifest":
            data["arms"]["A0"]["run_seed"] = 99
        else:
            data["pins"]["source_sha256"]["scripts/finetune.py"] = "changed"
        path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        wave.check_prepared(prepared, "A0")


def test_prepare_rejects_existing_protected_and_wrong_source(wave, source, tmp_path):
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        wave.prepare(source[0], existing)
    for path in ("agents/sherlock/weights/new", "agents/Gruppe15/new", "Gruppe15/new"):
        with pytest.raises(ValueError):
            wave.prepare(source[0], wave.ROOT / path)
    source[0].write_bytes(b"invalid")
    with pytest.raises(ValueError, match="source|Source"):
        wave.prepare(source[0], tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


@pytest.fixture
def loaded(wave, source, tmp_path):
    from scripts import experiment
    prepared = tmp_path / "prepared"
    wave.prepare(source[0], prepared, smoke=True)
    manifest, entry, init = wave.check_prepared(prepared, "A0", smoke=True)
    old = wave.VARIANTS.get(wave.VARIANT)
    wave.VARIANTS[wave.VARIANT] = ("sherlock", entry["config"])
    try:
        learners = experiment.Learners(wave.VARIANT, init, 0, load=True)
        learners.train_mode()
        yield learners, entry, manifest
    finally:
        if old is None:
            wave.VARIANTS.pop(wave.VARIANT, None)
        else:
            wave.VARIANTS[wave.VARIANT] = old


def test_initial_identity_requires_actual_fresh_learning_state(wave, loaded):
    learners, entry, _ = loaded
    proof = wave.prove_initial(learners, entry)
    assert proof["learning"]["learn_steps"] == 0
    assert proof["learning"]["replay"]["size"] == 0
    a = learners.agents["player_0"]
    a.buffer.size = 1
    with pytest.raises(ValueError, match="initial"):
        wave.prove_initial(learners, entry)


@pytest.mark.parametrize("fail", [False, True])
def test_validation_has_exact_v14_config_and_restores_rng_and_training_config(wave, loaded, monkeypatch, fail):
    from scripts import experiment
    learners, entry, manifest = loaded
    a = learners.agents["player_0"]
    before = wave.learner_identity(learners)
    observed = []
    def game(env, agent, opponent, seed, side, train):
        observed.append(agent.cfg.to_dict())
        assert not agent.learn_enabled and not agent.training and agent.epsilon == 0
        agent.rng.random()
        np.random.random()
        torch.rand(1)
        if fail:
            raise RuntimeError("synthetic validation error")
        return dict(seed=seed, side=side, result=.5)
    monkeypatch.setattr(experiment, "play_game", game)
    monkeypatch.setattr(experiment, "make_opponent", lambda *args: object())
    if fail:
        with pytest.raises(RuntimeError, match="synthetic validation error"):
            wave.validate_v14(None, learners, [1300000], ["default"], manifest["source_config"])
    else:
        assert len(wave.validate_v14(None, learners, [1300000], ["default"], manifest["source_config"])) == 2
    assert observed[0] == manifest["source_config"]
    assert a.cfg.to_dict() == entry["config"]
    assert wave.learner_identity(learners) == before


def test_validation_stop_preserves_completed_game_before_next_boundary(wave, loaded, monkeypatch):
    from scripts import experiment
    learners, _, manifest = loaded
    before = wave.learner_identity(learners)
    completed, calls = [], []
    def game(env, agent, opponent, seed, side, train):
        calls.append((seed, side))
        agent.rng.random()
        np.random.random()
        torch.rand(1)
        return dict(seed=seed, side=side, result=.5)
    def stop_check():
        if calls:
            raise wave.StudyInterrupted("stop before next validation game")
    monkeypatch.setattr(experiment, "play_game", game)
    monkeypatch.setattr(experiment, "make_opponent", lambda *args: object())
    with pytest.raises(wave.StudyInterrupted):
        wave.validate_v14(None, learners, [1300000, 1300001], ["default"],
                          manifest["source_config"], completed_rows=completed, stop_check=stop_check)
    assert calls == [(1300000, "player_0")]
    assert len(completed) == 1 and completed[0]["opponent"] == "default"
    assert experiment.play_game is game
    assert wave.learner_identity(learners) == before


@pytest.fixture
def synthetic_loop(wave, monkeypatch, tmp_path):
    """Exercise real finetune orchestration with synthetic games and real Adam steps."""
    from scripts import experiment, finetune
    import luxai_s3.wrappers
    class Env:
        def __init__(self, **kwargs):
            pass
        def close(self):
            pass
    monkeypatch.setattr(luxai_s3.wrappers, "LuxAIS3GymEnv", Env)
    monkeypatch.setattr(finetune, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(finetune, "make_opponent", lambda kind, side, **kwargs: object())
    monkeypatch.setattr(experiment, "make_opponent", lambda *args: object())
    def row(seed, side):
        result = {key: 0 for key in experiment.GAME_FIELDS}
        result.update(seed=seed, side=side, result=.5, our_wins=1, opp_wins=1,
                      point_counting_version=2, steps=303, secs=.01)
        return result
    def game(env, a, opponent, seed, side, train):
        a.set_to_train_mode()
        for _ in range(8):
            a.buffer.push(np.ones(79, dtype=np.float32), 0, 1., np.ones(79, dtype=np.float32),
                          False, np.ones(6, dtype=bool))
        a.env_steps += 303
        if a.learn_enabled:
            a.opt.zero_grad()
            a.q(torch.ones(2, 79)).square().mean().backward()
            a.opt.step()
            a.learn_steps += 1
        return row(seed, side)
    monkeypatch.setattr(finetune, "play_game", game)
    monkeypatch.setattr(experiment, "play_game", lambda env, a, o, seed, side, train: row(seed, side))
    @contextmanager
    def synthetic_action_evidence(agent):
        yield dict(act_calls=303, update_calls=303, checked_replay_transitions=8,
                   transcript_sha256="0" * 64)
    monkeypatch.setattr(wave, "action_audit", synthetic_action_evidence)
    return finetune


def test_smoke_runs_real_orchestration_but_never_issues_production_receipt(wave, source, tmp_path, synthetic_loop):
    from scripts import protocol
    finetune = synthetic_loop
    prepared = tmp_path / "prepared"
    wave.prepare(source[0], prepared, smoke=True)
    old_hooks = {key: getattr(finetune, key) for key in ("Learners", "play_game", "play_set", "make_opponent")}
    old_bases = finetune.FT_SEED_BASE, protocol.VAL_SEED_BASE
    old_argv, old_sigterm = sys.argv, signal.getsignal(signal.SIGTERM)
    record = wave.run_arm(prepared, "A0", "synthetic-smoke", smoke=True)
    output = tmp_path / "runs/synthetic-smoke"
    assert record["status"] == "smoke_done" and record["eligible"] is False
    assert record["actual_prefill_games"] == 2 and record["actual_train_games"] == 2
    assert record["actual_validation_games"] == 8
    assert len((output / "rollouts.jsonl").read_text().splitlines()) == 4
    assert not (output / "final_receipt.json").exists()
    assert json.loads((output / "smoke_receipt.json").read_text())["eligible"] is False
    assert all(getattr(finetune, key) is value for key, value in old_hooks.items())
    assert (finetune.FT_SEED_BASE, protocol.VAL_SEED_BASE) == old_bases
    assert sys.argv is old_argv and signal.getsignal(signal.SIGTERM) == old_sigterm


def test_sigterm_stops_at_game_boundary_saves_incomplete_and_restores_hooks(wave, source, tmp_path, synthetic_loop, monkeypatch):
    finetune = synthetic_loop
    prepared = tmp_path / "prepared"
    wave.prepare(source[0], prepared, smoke=True)
    original = finetune.play_game
    def terminate_in_game(*args, **kwargs):
        result = original(*args, **kwargs)
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        return result
    monkeypatch.setattr(finetune, "play_game", terminate_in_game)
    with pytest.raises(wave.StudyInterrupted):
        wave.run_arm(prepared, "A0", "interrupted-smoke", smoke=True)
    output = tmp_path / "runs/interrupted-smoke"
    record = json.loads((output / "progress.json").read_text())
    assert record["status"] == "incomplete" and record["actual_prefill_games"] == 1
    assert (output / "weights/agent.pth").is_file()
    assert len((output / "rollouts.jsonl").read_text().splitlines()) == 1
    assert not (output / "final_receipt.json").exists()
    assert not (output / "smoke_receipt.json").exists()


def test_sigterm_during_validation_records_one_game_and_saves_incomplete(wave, source, tmp_path, synthetic_loop, monkeypatch):
    from scripts import experiment
    prepared = tmp_path / "prepared"
    wave.prepare(source[0], prepared, smoke=True)
    original = experiment.play_game
    def terminate_in_validation(*args, **kwargs):
        result = original(*args, **kwargs)
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        return result
    monkeypatch.setattr(experiment, "play_game", terminate_in_validation)
    with pytest.raises(wave.StudyInterrupted):
        wave.run_arm(prepared, "A0", "interrupted-validation", smoke=True)
    output = tmp_path / "runs/interrupted-validation"
    record = json.loads((output / "progress.json").read_text())
    assert record["status"] == "incomplete" and record["eligible"] is False
    assert record["actual_prefill_games"] == 2 and record["actual_train_games"] == 0
    assert record["actual_validation_games"] == 1
    assert len((output / "validation_games.jsonl").read_text().splitlines()) == 1
    assert (output / "weights/agent.pth").is_file()
    assert not (output / "final_receipt.json").exists()
    assert not (output / "smoke_receipt.json").exists()
    assert experiment.play_game is terminate_in_validation


def test_short_or_no_learning_run_cannot_complete(wave, source, tmp_path, monkeypatch):
    from scripts import finetune
    monkeypatch.setattr(finetune, "RUNS", tmp_path / "runs")
    prepared = tmp_path / "prepared"
    wave.prepare(source[0], prepared)
    monkeypatch.setattr(finetune, "main", lambda: None)
    with pytest.raises(ValueError, match="count|learner|complete"):
        wave.run_arm(prepared, "A0", "no-training")
    assert not (tmp_path / "runs/no-training/final_receipt.json").exists()
