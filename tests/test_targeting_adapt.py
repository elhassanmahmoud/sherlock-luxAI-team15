"""Fixed adaptation protocol, with synthetic weights and no environment games."""
import importlib
import importlib.util
import json
from pathlib import Path

import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet
from scripts.night_train_pilot import file_sha256, tensor_sha256


def test_wrapper_is_available():
    assert importlib.util.find_spec("scripts.targeting_adapt") is not None


@pytest.fixture
def adapt():
    return importlib.import_module("scripts.targeting_adapt")


@pytest.fixture
def source(tmp_path, monkeypatch, adapt):
    cfg = AgentConfig(hidden=8, dueling=False, buffer_capacity=6000,
                      frozen=True, cand_rescue=True, rescue_after=30,
                      neb_cross=True, art_splash=True).to_dict()
    with torch.random.fork_rng():
        states = []
        for i in range(36):
            net = QNet(79, 6, hidden=8, dueling=False)
            with torch.no_grad():
                for p in net.parameters():
                    p.fill_(i / 100)
            states.append(net.state_dict())
    path = tmp_path / "synthetic.pth"
    torch.save(dict(q=states[0], ensemble=states[1:], cfg=cfg,
                    feature_dim=79, n_actions=6), path)
    monkeypatch.setattr(adapt, "SOURCE_SHA", file_sha256(path))
    return path, states, cfg


def test_prepare_four_arms_preserves_source_and_pair_identity(adapt, source, tmp_path):
    path, states, cfg = source
    manifest = adapt.prepare(path, tmp_path / "prepared")
    assert set(manifest["arms"]) == {"control18", "adapt18", "control19", "adapt19"}
    assert manifest["source_tensor_sha256"] == [tensor_sha256(s) for s in states]
    for name, component, seed, enabled in [
            ("control18", 18, 28, False), ("adapt18", 18, 28, True),
            ("control19", 19, 29, False), ("adapt19", 19, 29, True)]:
        entry = manifest["arms"][name]
        cp = torch.load(tmp_path / "prepared" / name / "weights" / "agent.pth",
                        weights_only=True)
        assert entry["component_index"] == component and entry["run_seed"] == seed
        assert tensor_sha256(cp["q"]) == tensor_sha256(states[component])
        assert tensor_sha256(cp["target_q"]) == tensor_sha256(states[component])
        assert not cp["ensemble"] and "opt" not in cp
        assert cp["env_steps"] == 60000 and cp["learn_steps"] == 0
        assert cp["cfg"]["point_pair_swap"] is enabled
        assert cp["cfg"]["art_move_guard"] is enabled
        assert cp["cfg"]["rules_in_training"] and cp["cfg"]["rules_in_training_all"]
        assert cp["cfg"]["neb_cross"] == cfg["neb_cross"]
        assert cp["cfg"]["fog_sap"] == cfg["fog_sap"]  # no V12 override
        assert cp["cfg"]["w_discovery"] == .5
    assert file_sha256(path) == manifest["source_sha256"]


def test_schedule_has_exact_paired_maps_and_deterministic_opponents(adapt):
    rows = adapt.rollout_plan("control18")
    assert rows == adapt.rollout_plan("adapt18")
    assert len(rows) == 720
    assert [(r["phase"], r["seed"], r["side"]) for r in (rows[0], rows[119], rows[120], rows[-1])] == [
        ("prefill", 485000, "player_0"), ("prefill", 485059, "player_1"),
        ("train", 484200, "player_0"), ("train", 484499, "player_1")]
    assert [r["opponent"] for r in rows[:8]] == [
        "solution92", "sol92_sq", "solution92", "solution92",
        "solution92", "solution92", "solution92", "solution92"]
    rows19 = adapt.rollout_plan("adapt19")
    assert (rows19[0]["seed"], rows19[-1]["seed"]) == (495000, 494499)
    with pytest.raises(ValueError):
        adapt.rollout_plan("control20")


@pytest.mark.parametrize("damage", ["hash", "count", "width", "nan", "config"])
def test_prepare_rejects_bad_source_before_output(adapt, source, tmp_path, monkeypatch, damage):
    path, _, _ = source
    cp = torch.load(path, weights_only=True)
    if damage == "hash":
        monkeypatch.setattr(adapt, "SOURCE_SHA", "0" * 64)
    else:
        if damage == "count":
            cp["ensemble"].pop()
        elif damage == "width":
            cp["ensemble"][18]["body.0.weight"] = torch.zeros(8, 78)
        elif damage == "nan":
            cp["ensemble"][0]["body.0.weight"][0, 0] = float("nan")
        else:
            cp["cfg"]["eps_decay_steps"] = 70000
        torch.save(cp, path)
        monkeypatch.setattr(adapt, "SOURCE_SHA", file_sha256(path))
    with pytest.raises(ValueError):
        adapt.prepare(path, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_prepare_rejects_existing_and_protected_outputs(adapt, source, tmp_path):
    out = tmp_path / "old"
    out.mkdir()
    (out / "sentinel").write_text("keep")
    with pytest.raises(FileExistsError):
        adapt.prepare(source[0], out)
    with pytest.raises(ValueError):
        adapt.prepare(source[0], adapt.ROOT / "agents/sherlock/weights/new_init")
    assert (out / "sentinel").read_text() == "keep"


@pytest.fixture
def loaded(adapt, source, tmp_path, monkeypatch):
    from scripts import experiment
    out = tmp_path / "prepared"
    manifest = adapt.prepare(source[0], out)
    entry = manifest["arms"]["control18"]
    monkeypatch.setitem(adapt.VARIANTS, adapt._VARIANT, ("sherlock", entry["config"]))
    learners = experiment.Learners(adapt._VARIANT, out / "control18", 28, load=True)
    return learners, entry, out


def test_actual_initial_proof_requires_loaded_tensor_target_config_and_fresh_state(adapt, loaded):
    assert hasattr(adapt, "prove_initial"), "actual learner proof is missing"
    learners, entry, _ = loaded
    proof = adapt.prove_initial(learners, entry)
    assert proof["q_tensor_sha256"] == entry["tensor_sha256"]
    assert proof["learning"]["env_steps"] == 60000
    assert proof["learning"]["replay"]["size"] == 0
    assert proof["learning"]["config"] == entry["config"]


@pytest.mark.parametrize("damage", ["q", "target", "cfg", "replay", "position", "optimizer",
                                         "loss", "env_steps", "learn_steps", "ensemble", "split",
                                         "autosave", "learn_enabled", "adam_lr"])
def test_actual_initial_proof_rejects_bad_loaded_state(adapt, loaded, damage):
    assert hasattr(adapt, "prove_initial"), "actual learner proof is missing"
    learners, entry, _ = loaded
    a = learners.agents["player_0"]
    if damage in ("q", "target"):
        with torch.no_grad():
            next((a.q if damage == "q" else a.target_q).parameters()).add_(1)
    elif damage == "cfg":
        a.cfg.w_point += 1
    elif damage == "replay":
        a.buffer.size = 1
    elif damage == "position":
        a.buffer.pos = 1
    elif damage == "optimizer":
        a.opt.state[next(a.q.parameters())]["step"] = torch.tensor(1.)
    elif damage == "loss":
        a.recent_losses.append(.1)
    elif damage == "env_steps":
        a.env_steps += 1
    elif damage == "learn_steps":
        a.learn_steps += 1
    elif damage == "ensemble":
        a.extra_q.append(a.q)
    elif damage == "split":
        learners.agents["player_1"] = object()
    elif damage == "autosave":
        a.autosave_on_terminate = True
    elif damage == "learn_enabled":
        a.learn_enabled = False
    else:
        a.opt.param_groups[0]["lr"] = .02
    with pytest.raises(ValueError):
        adapt.prove_initial(learners, entry)


@pytest.mark.parametrize("fail", [False, True])
def test_validation_restores_roles_rng_and_learning_even_on_error(adapt, loaded, monkeypatch, fail):
    assert hasattr(adapt, "isolated_validation"), "P validation wrapper is missing"
    import random
    from scripts import experiment
    learners, _, _ = loaded
    a = learners.agents["player_0"]
    before = experiment._learning_identity(a, identities=True)
    global_before = experiment.state_sha256(experiment._global_rng_state())
    rng_before = experiment.state_sha256(a.rng.bit_generator.state)
    seen = []

    def game(env, agent, opp, seed, side, train):
        seen.append((agent.cfg.point_pair_swap, agent.cfg.art_move_guard,
                     agent.training, agent.learn_enabled, agent.epsilon,
                     float(agent.rng.random())))
        random.random(); np_value = __import__("numpy").random.random(); torch.rand(1)
        assert np_value >= 0
        if fail:
            raise RuntimeError("synthetic validation failure")
        return dict(seed=seed, side=side, result=.5)

    monkeypatch.setattr(experiment, "play_game", game)
    monkeypatch.setattr(experiment, "make_opponent", lambda *args: object())
    if fail:
        with pytest.raises(RuntimeError, match="synthetic validation failure"):
            adapt.isolated_validation(None, learners, [500000], ["default"])
    else:
        rows = adapt.isolated_validation(None, learners, [500000], ["default"])
        assert len(rows) == 2 and rows[0]["seed"] == 500000
        assert "effect_counters" in rows[0]
    assert seen[0][:5] == (True, True, False, False, 0.)
    assert seen[0][5] == pytest.approx(.6789945433245914)
    assert experiment._learning_identity(a, identities=True) == before
    assert experiment.state_sha256(experiment._global_rng_state()) == global_before
    assert experiment.state_sha256(a.rng.bit_generator.state) == rng_before
    assert experiment.play_game is game


@pytest.mark.parametrize("damage", ["source", "init", "opt", "buffer", "cfg", "index", "plan"])
def test_run_preflight_rejects_corrupt_inputs_before_learner_or_game(adapt, loaded, monkeypatch, damage):
    assert hasattr(adapt, "check_prepared"), "strict arm preflight is missing"
    _, _, prepared = loaded
    manpath = prepared / "manifest.json"
    man = json.loads(manpath.read_text())
    weights = prepared / "control18/weights/agent.pth"
    if damage == "source":
        Path(man["source"]).write_bytes(b"changed")
    elif damage == "init":
        weights.write_bytes(b"changed")
    elif damage == "buffer":
        (weights.parent / "agent.buffer.npz").write_bytes(b"old replay")
    elif damage in ("opt", "cfg"):
        cp = torch.load(weights, weights_only=True)
        if damage == "opt":
            cp["opt"] = {}
        else:
            cp["cfg"]["w_point"] += 1
        torch.save(cp, weights)
        man["arms"]["control18"]["weights_sha256"] = file_sha256(weights)
        manpath.write_text(json.dumps(man))
    else:
        if damage == "index":
            man["arms"]["control18"]["component_index"] = 19
        else:
            man["arms"]["control18"]["rollout_plan"][0]["seed"] = 900000
        manpath.write_text(json.dumps(man))
    with pytest.raises(ValueError):
        adapt.check_prepared(prepared, "control18")


@pytest.fixture
def simulated_finetune(adapt, monkeypatch):
    """Real finetune loop; only environment/opponent/episode boundary is synthetic.

    No environment is created and no policy or gradient update is executed.
    The episode double writes explicit counters/tensors to test auditing.
    """
    from scripts import experiment, finetune
    import luxai_s3.wrappers

    class Env:
        def __init__(self, **kwargs):
            pass

        def close(self):
            pass

    def row(seed, side):
        return dict(seed=seed, side=side, result=.5, game_win=0, point_win=.5,
                    our_wins=1, opp_wins=1, our_points=10, opp_points=10,
                    point_counting_version=2, secs=0, steps=303)

    def rollout(env, a, opponent, seed, side, train):
        assert train
        a.env_steps += 303
        a.buffer.size = 6000
        a.buffer.pos = (a.buffer.pos + 303) % a.buffer.capacity
        if a.learn_enabled:
            a.learn_steps += 150
            with torch.no_grad():
                next(a.q.parameters()).add_(.00001)
            for p in a.q.parameters():
                a.opt.state[p] = dict(step=torch.tensor(float(a.learn_steps)),
                                      exp_avg=torch.zeros_like(p), exp_avg_sq=torch.zeros_like(p))
            a.recent_losses.append(.01)
        return row(seed, side)

    monkeypatch.setattr(luxai_s3.wrappers, "LuxAIS3GymEnv", Env)
    monkeypatch.setattr(finetune, "play_game", rollout)
    monkeypatch.setattr(finetune, "make_opponent", lambda name, side: (name, side))
    monkeypatch.setattr(experiment, "make_opponent", lambda name, side: (name, side))
    monkeypatch.setattr(experiment, "play_game", lambda env, a, opp, seed, side, train: row(seed, side))
    return finetune


def test_run_arm_records_actual_720_rollouts_96_raw_val_and_saved_end(adapt, source, tmp_path,
                                                                    monkeypatch, simulated_finetune):
    assert hasattr(adapt, "run_arm"), "instrumented fixed finetune entry point is missing"
    from scripts import experiment
    finetune = simulated_finetune
    prepared = tmp_path / "prepared"
    adapt.prepare(source[0], prepared)
    monkeypatch.setattr(finetune, "RUNS", tmp_path / "runs")
    old_hooks = (finetune.Learners, finetune.play_game, finetune.play_set, finetune.make_opponent)
    old_variant = adapt.VARIANTS.get(adapt._VARIANT)
    old_argv = __import__("sys").argv
    record = adapt.run_arm(prepared, "control18", "synthetic-control")
    run = tmp_path / "runs/synthetic-control"
    rows = [json.loads(line) for line in (run / "rollouts.jsonl").read_text().splitlines()]
    vals = [json.loads(line) for line in (run / "validation_games.jsonl").read_text().splitlines()]
    audit = json.loads((run / "adaptation_audit.json").read_text())
    assert record["status"] == "done"
    assert len(rows) == 720 and len(vals) == 96
    assert sum(r["phase"] == "prefill" for r in rows) == 120
    assert rows[120]["seed"] == 484200 and rows[-1]["seed"] == 484499
    assert rows[119]["identity"]["learning"]["learn_enabled"] is False
    assert rows[120]["identity"]["learning"]["learn_enabled"] is True
    assert {r["after_games"] for r in vals} == {0, 300, 600}
    assert all(r["config"]["point_pair_swap"] and r["config"]["art_move_guard"] for r in vals)
    assert audit["initial"]["q_tensor_sha256"] == audit["prefill"]["q_tensor_sha256"]
    assert audit["initial"]["q_tensor_sha256"] != audit["end"]["q_tensor_sha256"]
    assert audit["prefill"]["learning"]["learn_steps"] == 0
    assert audit["end"]["learning"]["learn_steps"] == 90000
    assert audit["end"]["learning"]["env_steps"] == 278160
    assert set(audit["before_train"]) == {"1", "300", "600"}
    assert (finetune.Learners, finetune.play_game, finetune.play_set, finetune.make_opponent) == old_hooks
    assert adapt.VARIANTS.get(adapt._VARIANT) == old_variant
    assert __import__("sys").argv is old_argv
    cp = torch.load(run / "weights/agent.pth", weights_only=True)
    assert tensor_sha256(cp["q"]) == audit["end"]["q_tensor_sha256"]
    assert experiment.state_sha256(cp["opt"]) == audit["end"]["learning"]["optimizer_sha256"]


def test_run_arm_rejects_existing_output_without_entering_finetune(adapt, source, tmp_path,
                                                                 monkeypatch):
    assert hasattr(adapt, "run_arm"), "instrumented fixed finetune entry point is missing"
    from scripts import finetune
    prepared = tmp_path / "prepared"
    adapt.prepare(source[0], prepared)
    monkeypatch.setattr(finetune, "RUNS", tmp_path / "runs")
    (tmp_path / "runs/existing").mkdir(parents=True)
    with pytest.raises(FileExistsError):
        adapt.run_arm(prepared, "control18", "existing")


def test_failed_validation_keeps_completed_raw_rows_and_restores_hooks(adapt, source, tmp_path,
                                                                     monkeypatch, simulated_finetune):
    from scripts import experiment
    finetune = simulated_finetune
    prepared = tmp_path / "prepared"
    adapt.prepare(source[0], prepared)
    monkeypatch.setattr(finetune, "RUNS", tmp_path / "runs")
    original = experiment.play_game
    seen = []

    def fail_second(env, a, opp, seed, side, train):
        seen.append(a)
        if len(seen) == 2:
            raise RuntimeError("second validation episode failed")
        return original(env, a, opp, seed, side, train)

    monkeypatch.setattr(experiment, "play_game", fail_second)
    old_hooks = (finetune.Learners, finetune.play_game, finetune.play_set, finetune.make_opponent)
    with pytest.raises(RuntimeError, match="second validation episode failed"):
        adapt.run_arm(prepared, "control18", "failed-val")
    run = tmp_path / "runs/failed-val"
    rows = [json.loads(line) for line in (run / "validation_games.jsonl").read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["side"] == "player_0"
    record = json.loads((prepared / "run_records/failed-val.json").read_text())
    assert record["status"] == "incomplete"
    assert record["actual_validation_games"] == 1 and record["actual_rollout_games"] == 120
    assert (finetune.Learners, finetune.play_game, finetune.play_set, finetune.make_opponent) == old_hooks
    assert experiment.play_game is fail_second
    assert seen[0].training and seen[0].learn_enabled
    assert not seen[0].cfg.point_pair_swap and not seen[0].cfg.art_move_guard


@pytest.mark.parametrize("damage", ["initial", "prefill", "saved_end", "final_q", "adam_step", "opponent"])
def test_incomplete_arm_fails_closed_and_restores_temporary_globals(adapt, source, tmp_path,
                                                                 monkeypatch, simulated_finetune, damage):
    from scripts import finetune
    prepared = tmp_path / "prepared"
    adapt.prepare(source[0], prepared)
    monkeypatch.setattr(finetune, "RUNS", tmp_path / "runs")
    if damage == "initial":
        original = finetune.Learners

        def bad_loader(*args, **kwargs):
            learners = original(*args, **kwargs)
            learners.agents["player_0"].buffer.pos = 1
            return learners

        monkeypatch.setattr(finetune, "Learners", bad_loader)
    elif damage == "opponent":
        monkeypatch.setattr(finetune, "parse_mix", lambda *args: {"rush": 1.})
    else:
        original = finetune.play_game

        def broken_episode(env, a, opp, seed, side, train):
            row = original(env, a, opp, seed, side, train)
            if damage == "prefill" and not a.learn_enabled:
                with torch.no_grad():
                    next(a.q.parameters()).add_(1)
            elif damage == "final_q" and seed == 484499 and side == "player_1":
                cp = torch.load(prepared / "control18/weights/agent.pth", weights_only=True)
                a.q.load_state_dict(cp["q"])
            elif damage == "adam_step" and a.learn_enabled:
                for state in a.opt.state.values():
                    state["step"] = torch.tensor(-1.)
            return row

        monkeypatch.setattr(finetune, "play_game", broken_episode)
        if damage == "saved_end":
            from agents.sherlock.main import Agent_x
            original_save = Agent_x.save_agent

            def corrupt_save(a, path=None):
                original_save(a, path)
                cp = torch.load(path, weights_only=True)
                cp["learn_steps"] = -1
                torch.save(cp, path)

            monkeypatch.setattr(Agent_x, "save_agent", corrupt_save)
    hooks = (finetune.Learners, finetune.play_game, finetune.play_set, finetune.make_opponent)
    old_variant = adapt.VARIANTS.get(adapt._VARIANT)
    argv = __import__("sys").argv
    with pytest.raises(ValueError):
        adapt.run_arm(prepared, "control18", "broken")
    record = json.loads((prepared / "run_records/broken.json").read_text())
    assert record["status"] == "incomplete"
    if damage in ("initial", "opponent"):
        assert record["actual_rollout_games"] == 0
    assert (finetune.Learners, finetune.play_game, finetune.play_set, finetune.make_opponent) == hooks
    assert adapt.VARIANTS.get(adapt._VARIANT) == old_variant
    assert __import__("sys").argv is argv
