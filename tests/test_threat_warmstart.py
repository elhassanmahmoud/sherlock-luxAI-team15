"""Small synthetic checks only; no released checkpoints or engine games."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x
from scripts import threat_warmstart as s


@pytest.fixture(autouse=True)
def no_archive_io(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No tensor archive loading or engine game in this suite")
    monkeypatch.setattr(torch, "load", forbidden)
    from scripts import common
    monkeypatch.setattr(common, "play_game", forbidden)


def test_expand_preserves_all_original_values_and_zeros_only_new_columns():
    original = {"body.0.weight": torch.arange(256*79, dtype=torch.float32).reshape(256, 79),
                "body.0.bias": torch.arange(256, dtype=torch.float32), "head": torch.tensor([3., 4.])}
    expanded = s.expand_state(original)
    assert expanded["body.0.weight"].shape == (256, 101)
    torch.testing.assert_close(expanded["body.0.weight"][:, :79], original["body.0.weight"], rtol=0, atol=0)
    assert expanded["body.0.weight"][:, 79:].count_nonzero() == 0
    torch.testing.assert_close(expanded["head"], original["head"], rtol=0, atol=0)
    expanded["head"][0] = 0
    assert original["head"][0] == 3


@pytest.mark.parametrize("fault", ["width", "nan"])
def test_expand_rejects_wrong_source(fault):
    original = {"body.0.weight": torch.zeros((256, 79))}
    if fault == "width": original["body.0.weight"] = torch.zeros((256, 78))
    else: original["body.0.weight"][0, 0] = float("nan")
    with pytest.raises(ValueError): s.expand_state(original)


def test_fixed_plan_and_config_change_only_specified_fields():
    a, b = s.rollout_plan(), s.rollout_plan()
    assert a == b and len(a) == 440
    assert [(r["seed"], r["side"]) for r in a[:40]] == [
        (seed, side) for seed in range(9950300, 9950320) for side in ("player_0", "player_1")]
    assert [(r["seed"], r["side"]) for r in a[40:]] == [
        (seed, side) for seed in range(9950000, 9950200) for side in ("player_0", "player_1")]
    expected = np.random.default_rng(47).choice(["solution92", "sol92_sq", "default", "rush"],
                                             size=440, p=[.6, .2, .1, .1]).tolist()
    assert [r["opponent"] for r in a] == expected
    cfg = AgentConfig().to_dict(); cfg.update(hidden=256, dueling=True, eps_end=.05, eps_decay_steps=60000)
    result = s.training_config(cfg)
    changed = {key for key in result if result[key] != cfg[key]}
    assert changed <= {"threat_feats", "frozen", "lr", "rules_in_training", "rules_in_training_all",
                       "rescue_in_training", "fog_unknown_reward_neutral", "art_splash_in_training"}
    assert result["threat_feats"] and result["lr"] == .00005 and result["rescue_in_training"]


def public_context(step=1):
    return dict(step=step, match_step=step, W=6, H=6, ally_ids=np.array([0]),
                ally_pos=np.array([[2, 2]]), enemy_coords=np.array([[3, 2]]),
                enemy_energies=np.array([40.]), sap_range=3, sap_cost=20,
                point_tiles=np.zeros((6, 6), bool))


@pytest.mark.parametrize("role", s.ARMS)
def test_adapter_preserves_prefix_and_checks_public_tail_even_on_cache_hits(monkeypatch, role):
    a = object.__new__(s.ThreatAgent); a.role = role
    a.cfg = AgentConfig(threat_feats=True); a.belief = a.feat_belief = object()
    ctx = public_context(); prefix = np.arange(79, dtype=np.float32)
    from agents.sherlock.features import threat_features
    tail = threat_features(ctx, 0)
    a._cache = (1, ctx, [0], {0: np.r_[prefix, tail]}, {0: np.ones(6, bool)}, {0: None})
    monkeypatch.setattr(Agent_x, "_decide", lambda self, obs: self._cache[1:])
    for _ in range(2):
        result = a._decide({"steps": 1})
        np.testing.assert_array_equal(result[2][0][:79], prefix)
        np.testing.assert_array_equal(result[2][0][79:], np.zeros(22) if role == "control" else tail)
        np.testing.assert_array_equal(a._public_features[0][79:], tail)
    assert np.count_nonzero(tail) > 0


def synthetic_agent(role):
    cfg = AgentConfig(hidden=256, threat_feats=True, buffer_capacity=32, batch_size=4,
                      learn_start=4, train_every=2, frozen=False, rules_in_training_all=True)
    agent = s.ThreatAgent("player_0", cfg=cfg, train=True, seed=47, role=role)
    with torch.no_grad(): agent.q.body[0].weight[:, 79:] = 0
    agent.target_q.load_state_dict(agent.q.state_dict())
    agent.begin_game()
    return agent


@pytest.mark.parametrize("role", s.ARMS)
def test_actual_learning_consumes_101_columns_and_control_columns_stay_zero(role):
    torch.manual_seed(47)
    a = synthetic_agent(role)
    values = np.ones(101, dtype=np.float32)
    if role == "control": values[79:] = 0
    # Seed the real replay directly; this test isolates sampling/learning, not push chronology.
    from agents.sherlock.replay_buffer import ReplayBuffer
    for i in range(8): ReplayBuffer.push(a.buffer, values, 2, 1., values, False, np.ones(6, bool))
    a.learn_enabled = True
    a._learn()
    assert a.learn_steps == 1 and a.learning_audit["sampled_batches"] == 1
    if role == "control":
        assert a.q.body[0].weight[:, 79:].count_nonzero() == 0
        assert a.learning_audit["sampled_exposed_rows"] == 0
    else:
        assert a.learning_audit["sampled_exposed_rows"] == 4
        assert a.learning_audit["tail_gradient_steps"] == 1
        assert a.q.body[0].weight[:, 79:].count_nonzero() > 0


def test_replay_check_binds_final_labels_masks_and_actual_next_features(monkeypatch):
    a = synthetic_agent("control")
    current, following = public_context(), public_context(2)
    a._prev_ctx = current; a._prev_feats = {0: np.r_[np.ones(79), np.zeros(22)].astype(np.float32)}
    a._prev_masks = {0: np.ones(6, bool)}; a._prev_actions = {0: 2}
    a._native_actions = np.array([[2, 0, 0]])
    a._action_public = {0: np.ones(101, np.float32)}
    a._public_features = {0: np.r_[np.full(79, 2), np.ones(22)].astype(np.float32)}
    nxt = np.r_[np.full(79, 2), np.zeros(22)].astype(np.float32)
    a._cache = (2, following, [0], {0: nxt}, {0: np.ones(6, bool)}, {})
    a._transition_uids = [0]; a._transition_terminated = False
    monkeypatch.setattr(s, "surviving", lambda *args: {0})
    with pytest.raises(ValueError): a.buffer.push(a._prev_feats[0], 1, .5, nxt, False, np.ones(6, bool))
    a._transition_uids = [0]
    bad = nxt.copy(); bad[80] = 1
    with pytest.raises(ValueError): a.buffer.push(a._prev_feats[0], 2, .5, bad, False, np.ones(6, bool))
    a._transition_uids = [0]
    a.buffer.push(a._prev_feats[0], 2, .5, nxt, False, np.ones(6, bool))
    assert a.game_audit["replay_rows"] == 1 and len(a.buffer) == 1


def test_fog_sap_final_label_is_valid_even_when_original_network_mask_excluded_sap(monkeypatch):
    a = synthetic_agent("control")
    current, following = public_context(), public_context(2)
    values = np.r_[np.ones(79), np.zeros(22)].astype(np.float32)
    a._prev_ctx = current; a._prev_feats = {0: values}
    a._prev_masks = {0: np.array([True, True, True, True, True, False])}
    a._prev_actions = {0: 5}; a._native_actions = np.array([[5, 1, 0]])
    a._action_public = a._public_features = {0: np.ones(101, np.float32)}
    a._cache = (2, following, [0], {0: values}, {0: np.ones(6, bool)}, {})
    a._transition_uids = [0]; a._transition_terminated = False
    monkeypatch.setattr(s, "surviving", lambda *args: {0})
    a.buffer.push(values, 5, .5, values, False, np.ones(6, bool))
    assert a.buffer.a[0] == 5 and a.game_audit["masked_final_rule_actions"] == 1


def proof(role):
    return dict(status="prefill_ready", role=role, profile=s.PROFILE, games=40,
                initial={"q": "q", "target": "q", "optimizer": "o"},
                current={"q": "q", "target": "q", "optimizer": "o"},
                env_steps=72120, learn_steps=0, replay_size=6000,
                replay_prefix_sha256="same", public_nonzero_rows=10,
                actual_nonzero_rows=0 if role == "control" else 10,
                paired_rows=[dict(key=r, native_sha256="a", trajectory_sha256="t", replay_prefix_sha256="r")
                             for r in s.rollout_plan()[:40]])


def test_prefill_pair_requires_actual_equality_and_no_gradients():
    c, t = proof("control"), proof("threat")
    s.compare_prefills(c, t)
    for field, value in [("learn_steps", 1), ("replay_prefix_sha256", "different"), ("public_nonzero_rows", 0)]:
        bad = deepcopy(t); bad[field] = value
        with pytest.raises(ValueError): s.compare_prefills(c, bad)
    bad = deepcopy(t); bad["paired_rows"][0]["trajectory_sha256"] = "changed"
    with pytest.raises(ValueError): s.compare_prefills(c, bad)


def test_release_requires_exact_two_prefill_pins_and_explicit_root_acceptance(tmp_path):
    release = dict(profile=s.PROFILE, status="approved", admission_sha256="admit",
                   prefill_sha256={"control": "c", "threat": "t"}, root_review_sha256="review")
    assert s.validate_release(release, "admit", {"control": "c", "threat": "t"}) == release
    for field, value in [("status", "prefill_ready"), ("admission_sha256", "other"),
                         ("prefill_sha256", {"control": "c"})]:
        bad = deepcopy(release); bad[field] = value
        with pytest.raises(ValueError): s.validate_release(bad, "admit", {"control": "c", "threat": "t"})


@pytest.mark.parametrize("role", s.ARMS)
def test_original_update_pushes_checked_mirrored_label_and_following_feature_cache(monkeypatch, role):
    import agents.sherlock.main as core
    from agents.sherlock.features import threat_features
    a = synthetic_agent(role)
    current, following = public_context(), public_context(2)
    tail = threat_features(current, 0)
    actual_tail = np.zeros(22) if role == "control" else tail
    a._prev_ctx = current; a._prev_feats = {0: np.r_[np.ones(79), actual_tail].astype(np.float32)}
    a._prev_actions = {0: 2}; a._prev_masks = {0: np.ones(6, bool)}
    a._action_public = {0: np.r_[np.ones(79), tail].astype(np.float32)}
    a._native_actions = np.array([[1, 0, 0]])  # Canonical east mirrors to native north.
    a.belief.mirrored = True
    monkeypatch.setattr(a.belief, "observe", lambda obs: None)
    next_mask = np.array([True, True, False, False, False, False])
    next_public = np.r_[np.full(79, 2), threat_features(following, 0)].astype(np.float32)
    a._cache = (2, following, [0], {0: next_public}, {0: next_mask}, {})
    monkeypatch.setattr(Agent_x, "_decide", lambda self, obs: self._cache[1:])
    monkeypatch.setattr(core, "unit_rewards", lambda *args: {0: .75})
    monkeypatch.setattr(core, "surviving", lambda *args: {0})
    monkeypatch.setattr(s, "surviving", lambda *args: {0})
    a._update(1, {"steps": 1}, 0., a._native_actions, False, {"steps": 2})
    assert len(a.buffer) == 1 and a.buffer.a[0] == 2 and a.buffer.r[0] == .75
    np.testing.assert_array_equal(a.buffer.mask[0], next_mask)
    np.testing.assert_array_equal(a.buffer.ns[0][:79], np.full(79, 2))
    np.testing.assert_array_equal(a.buffer.ns[0][79:], actual_tail)
    assert a.learn_steps == 0


@pytest.mark.parametrize("fault", [None, "pid", "argv", "source", "battery", "roles"])
def test_worker_ownership_checks_actual_process_and_frozen_admission(fault):
    a = dict(stage="training", python="/python", root="/root", out="/out", plans=["plan"], source={"head": "h"},
             protected={}, stop_file="/stop", allow_battery=True)
    command = s.worker_command(a, "/admission", "sha", "/state", "control")
    state = dict(a, profile=s.PROFILE, status="running", owner_pid=10, active=list(s.ARMS), admission_sha256="sha",
                 jobs={"control": dict(pid=20, pgid=20, owner_pid=10, argv=command)})
    if fault == "pid": state["jobs"]["control"]["pid"] = 21
    if fault == "argv": state["jobs"]["control"]["argv"] = command[:-1]+["threat"]
    if fault == "source": state["source"] = {"head": "changed"}
    if fault == "battery": state["allow_battery"] = False
    if fault == "roles": state["active"].append("third")
    kwargs = dict(pid=20, pgid=20, ppid=10, executable="/python", actual=["/framework-python", *command[1:]])
    if fault:
        with pytest.raises(ValueError): s.check_worker(state, a, "sha", "control", command, **kwargs)
    else: s.check_worker(state, a, "sha", "control", command, **kwargs)


def test_root_approval_is_bound_to_two_waiting_prefills_and_is_single_use(tmp_path, monkeypatch):
    a = dict(out=str(tmp_path), source={"head": "h"}, config={"lr": .00005})
    for role in s.ARMS:
        folder = tmp_path/role; folder.mkdir()
        document = dict(proof(role), source=a["source"], config=a["config"], admission_sha256="sha")
        s.write(folder/"prefill.json", document)
    s.write(tmp_path/"state.json", dict(status="running", active=list(s.ARMS), admission_sha256="sha"))
    monkeypatch.setattr(s, "validate_prefill_file", lambda p: json.loads(Path(p).read_text()))
    pins = {role: s.digest(tmp_path/role/"prefill.json") for role in s.ARMS}
    review = tmp_path/"review.json"
    s.write(review, dict(profile=s.PROFILE, status="PASS", source=a["source"], admission_sha256="sha", prefill_sha256=pins))
    result = s.approve_prefill(a, "sha", review, s.digest(review))
    assert result["prefill_sha256"] == pins and result["root_review_sha256"] == s.digest(review)
    with pytest.raises(FileExistsError): s.approve_prefill(a, "sha", review, s.digest(review))


def test_saved_prefill_replay_is_recomputed_and_control_tail_cannot_hide_behind_hash(tmp_path):
    data = dict(s=np.zeros((4, 101), np.float32), ns=np.zeros((4, 101), np.float32),
                a=np.zeros(4, np.int64), r=np.zeros(4, np.float32), done=np.zeros(4, np.float32), mask=np.ones((4, 6), bool))
    replay = tmp_path/"prefill.npz"; proof_path = tmp_path/"prefill.json"
    for corrupt in (False, True):
        if corrupt: data["s"][0, 80] = 1
        np.savez(replay, **data)
        p = dict(role="control", replay_file=str(replay), replay_sha256=s.digest(replay), replay_size=4,
                 replay_full_sha256=s.state_sha256(data),
                 replay_prefix_sha256=s.state_sha256(dict(data, s=data["s"][:, :79], ns=data["ns"][:, :79])))
        proof_path.write_text(json.dumps(p))
        if corrupt:
            with pytest.raises(ValueError): s.validate_prefill_file(proof_path)
        else: assert s.validate_prefill_file(proof_path) == p


def test_interrupted_save_keeps_explicit_incomplete_status_and_never_overwrites(tmp_path, monkeypatch):
    a = synthetic_agent("control")
    captured = []
    original_save = torch.save
    def record(payload, stream):
        captured.append(payload["threat_warmstart"])
        original_save(payload, stream)
    monkeypatch.setattr(torch, "save", record)
    files = s.save_artifacts(tmp_path, a, "incomplete", {"source": {"head": "h"}}, 3)
    assert set(Path(p).name for p in files) == {"incomplete.pth", "incomplete_replay.npz"}
    assert captured[0]["status"] == "incomplete" and captured[0]["completed_games"] == 3
    with pytest.raises(ValueError): s.save_artifacts(tmp_path, a, "incomplete", {"source": {}}, 3)


def test_make_learner_accepts_original_epsilon_rounding_with_identical_fresh_101_arms():
    from agents.sherlock.model import QNet
    # Artificial all-zero state; no files and no released model data.
    initial = {name: torch.zeros_like(value) for name, value in QNet(101, 6, 256, True).state_dict().items()}
    cfg = AgentConfig(threat_feats=True, hidden=256, dueling=True, buffer_capacity=32,
                      frozen=False, eps_start=1., eps_end=.05, eps_decay_steps=60000).to_dict()
    identities = []
    for role in s.ARMS:
        agent = s.make_learner({"config": cfg}, initial, role)
        # This is Agent_x's unchanged epsilon property, not a mocked shortcut.
        assert agent.epsilon == 0.050000000000000044
        assert agent.env_steps == 60000 and agent.learn_steps == 0
        assert not agent.opt.state and len(agent.buffer) == 0 and not agent.learn_enabled
        identities.append(s.model_identity(agent))
    assert identities[0] == identities[1]
    assert identities[0]["q"] == identities[0]["target"] == s.state_sha256(initial)


def test_exclusive_json_is_visible_only_after_complete_synced_content(tmp_path, monkeypatch):
    target = tmp_path/"release.json"
    synced = []
    original_sync, original_link = s.os.fsync, s.os.link
    def split_dump(document, stream, **kwargs):
        assert not target.exists()
        stream.write('{"value":')
        stream.flush()
        assert not target.exists()
        stream.write('1}')
    def sync(fd):
        original_sync(fd); synced.append(fd)
    def publish(source, destination):
        assert synced and not target.exists()
        assert json.loads(Path(source).read_text()) == {"value": 1}
        original_link(source, destination)
    monkeypatch.setattr(s.json, "dump", split_dump)
    monkeypatch.setattr(s.os, "fsync", sync)
    monkeypatch.setattr(s.os, "link", publish)
    s.write(target, {"value": 1})
    assert json.loads(target.read_text()) == {"value": 1}
    assert list(tmp_path.iterdir()) == [target]


def test_exclusive_json_never_replaces_an_existing_target(tmp_path):
    target = tmp_path/"prefill.json"; target.write_bytes(b"existing exact bytes")
    with pytest.raises(FileExistsError): s.write(target, {"replacement": True})
    assert target.read_bytes() == b"existing exact bytes"
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize("failure", ["json", "fsync", "link"])
def test_exclusive_json_cleans_temporary_file_without_publishing_on_failure(tmp_path, monkeypatch, failure):
    target = tmp_path/"release.json"
    def fail(*args, **kwargs): raise OSError("synthetic write failure")
    if failure in ("fsync", "link"): monkeypatch.setattr(s.os, failure, fail)
    value = {"bad": object()} if failure == "json" else {"good": 1}
    with pytest.raises((TypeError, OSError)): s.write(target, value)
    assert not target.exists() and list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("fail_at", [None, 2])
def test_worker_reuses_one_environment_resets_each_game_and_closes_once(tmp_path, monkeypatch, fail_at):
    from scripts import common, experiment
    instances, used = [], []
    class FakeEnv:
        def __init__(self, *, numpy_output):
            assert numpy_output is True
            self.seeds = []; self.closed = 0; instances.append(self)
        def reset(self, seed):
            self.seeds.append(seed)
            return {"public": seed}, {}
        def close(self): self.closed += 1
    class FakeGuard:
        def __init__(self, *args): self.command = ["synthetic"]; self.release_sha = None
        def __call__(self): pass
    def make_agent(a, initial, role):
        return SimpleNamespace(role=role, env_steps=60000, learn_steps=0, learn_enabled=False,
            caught_errors=0, cfg=SimpleNamespace(train_every=2), epsilon=.05, buffer=[], learning_audit={},
            begin_game=lambda: None, pop_mean_loss=lambda: float("nan"),
            game_proof=lambda: dict(replay_rows=1, replay_prefix_sha256="same",
                                   actual_nonzero_rows=int(role == "threat")))
    def play_game(traced, agent, opponent, seed, side, train):
        assert train is True
        used.append(traced.env)
        traced.reset(seed=seed)  # Preserve common.play_game's per-game reset contract.
        if len(used) == fail_at: raise RuntimeError("synthetic game failure")
        agent.env_steps += 303
        return dict(steps=303, point_counting_version=2, our_wins=1, opp_wins=0,
                    our_points=1, opp_points=0, result=1.)
    monkeypatch.setitem(sys.modules, "luxai_s3.wrappers", SimpleNamespace(LuxAIS3GymEnv=FakeEnv))
    monkeypatch.setattr(experiment, "limit_threads", lambda: None)
    monkeypatch.setattr(s, "WorkerGuard", FakeGuard)
    monkeypatch.setattr(s, "load_initial", lambda a: {})
    monkeypatch.setattr(s, "make_learner", make_agent)
    monkeypatch.setattr(s, "model_identity", lambda a: {"q": "q", "target": "q", "optimizer": "o"})
    monkeypatch.setattr(s, "replay_identity", lambda b: {"size": 0, "full": "f", "prefix": "p"})
    monkeypatch.setattr(s, "save_artifacts", lambda *args: {})
    monkeypatch.setattr(common, "make_opponent", lambda *args: object())
    monkeypatch.setattr(common, "play_game", play_game)
    state = tmp_path/"state.json"; state.write_text(json.dumps({"jobs": {"technical": {}}}))
    a = dict(stage="technical", out=str(tmp_path), config={}, source={"head": "synthetic"})
    if fail_at:
        with pytest.raises(RuntimeError, match="synthetic game failure"):
            s.run_worker(a, tmp_path/"admission.json", "sha", state, "technical")
        assert json.loads((tmp_path/"technical/incomplete.json").read_text())["status"] == "incomplete"
    else:
        assert s.run_worker(a, tmp_path/"admission.json", "sha", state, "technical")["status"] == "complete"
    assert len(instances) == 1 and instances[0].closed == 1
    assert used == [instances[0]]*(fail_at or 4)
    assert instances[0].seeds == [831006, 831000, 831006, 831000][:(fail_at or 4)]
