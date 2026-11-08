"""TEXT PREPARATION ONLY: authored before implementation; never run during freeze.

After authorization, run from the project checkout. No engine/game imports.
Tests intentionally exercise submitted commands and the unchanged Core terminal
heuristic, not biological unit identity or command effectiveness.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x
from agents.sherlock.replay_buffer import ReplayBuffer
from agents.sherlock.reward import surviving

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "sampled_target_agent.py"
spec = importlib.util.spec_from_file_location("sampled_target_agent_staging", MODULE)
pilot = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pilot
spec.loader.exec_module(pilot)
Frame = pilot.ActionFrame
SuccessorReplay = pilot.SuccessorReplay
SampledTargetAgent = pilot.SampledTargetAgent


def feat(value=0):
    return np.full(79, value, dtype=np.float32)


def mask():
    return np.ones(6, dtype=bool)


def frame(step, actions, *, episode=0, match=0, clock=60000, features=None,
          masks=None, native=None):
    features = features or {uid: feat(step + uid) for uid in actions}
    masks = masks or {uid: mask() for uid in actions}
    if native is None:
        native = np.zeros((16, 3), dtype=np.int64)
        for uid, action in actions.items():
            native[uid, 0] = action
    return Frame(episode, match, step, clock, native, features, masks,
                 dict(actions), f"obs-{step}")


def capture(buffer, current, next_frame, *, done=None):
    done = done or {uid: False for uid in current.actions}
    source = {uid: (current.features[uid], action)
              for uid, action in current.actions.items()}
    buffer.begin_capture(source, dict(episode_id=current.episode_id,
        source_step=current.step, match_idx=current.match_idx,
        next_step=current.step + 1))
    for uid, action in current.actions.items():
        buffer.push(current.features[uid], action, float(uid),
                    next_frame.features.get(uid, feat()), done[uid],
                    next_frame.masks.get(uid, mask()))
    buffer.finish_capture(dict(step=current.step + 1,
        match_idx=next_frame.match_idx, match_step=next_frame.step))


def committed(buffer, step=1, *, action=1, next_action=2, episode=0):
    current = frame(step, {0: action}, episode=episode)
    successor = frame(step + 1, {0: next_action}, episode=episode,
                      clock=60000 + step)
    capture(buffer, current, successor)
    buffer.attach_successor(successor)
    buffer.commit_confirmed(successor.native, successor.key)


def test_submitted_successor_commits_only_after_update():
    b = SuccessorReplay(8, 79)
    old, nxt = frame(1, {2: 3}), frame(2, {2: 4}, clock=60001)
    capture(b, old, nxt)
    assert len(b) == 0
    b.attach_successor(nxt)
    assert len(b) == 0  # chosen, not yet acknowledged by successful env.step
    b.commit_confirmed(nxt.native, nxt.key)
    assert len(b) == 1
    assert (b.a[0], b.next_action[0], b.uid[0]) == (3, 4, 2)
    assert b.next_action_env_steps[0] == 60001


def test_submitted_command_kept_without_engine_effect():
    b = SuccessorReplay(8, 79)
    old = frame(1, {0: 1}, features={0: feat(7)})
    nxt = frame(2, {0: 4}, features={0: feat(7)}, clock=60001)
    capture(b, old, nxt)
    b.attach_successor(nxt)
    b.commit_confirmed(nxt.native, nxt.key)
    assert b.next_action[0] == 4  # no movement/effect predicate


def test_mixed_batch_preserves_uid_order():
    b = SuccessorReplay(8, 79)
    old = frame(1, {3: 1, 1: 0, 2: 2})
    nxt = frame(2, {3: 4, 2: 1}, clock=60001)
    capture(b, old, nxt, done={3: False, 1: True, 2: False})
    assert len(b) == 0
    b.attach_successor(nxt)
    b.commit_confirmed(nxt.native, nxt.key)
    assert b.uid[:3].tolist() == [3, 1, 2]
    assert b.next_action[:3].tolist() == [4, -1, 1]
    assert b.next_action_env_steps[:3].tolist() == [60001, -1, 60001]


def test_terminal_successor_action_still_labels_previous():
    b = SuccessorReplay(8, 79)
    old, nxt = frame(1, {0: 1}), frame(2, {0: 5}, clock=60001)
    capture(b, old, nxt)
    b.attach_successor(nxt)
    b.commit_confirmed(nxt.native, nxt.key)
    capture(b, nxt, frame(3, {}), done={0: True})
    assert b.done[:2].tolist() == [0, 1]
    assert b.next_action[:2].tolist() == [5, -1]
    b.assert_idle()


@pytest.mark.parametrize("change", ["episode", "match", "step", "uid", "feature", "mask"])
def test_missing_or_different_successor_aborts(change):
    b = SuccessorReplay(8, 79)
    old, nxt = frame(1, {0: 1}), frame(2, {0: 2}, clock=60001)
    capture(b, old, nxt)
    bad = copy.deepcopy(nxt)
    if change == "episode": bad.episode_id = 1
    if change == "match": bad.match_idx = 1
    if change == "step": bad.step = 3
    if change == "uid": bad.actions = {}; bad.features = {}; bad.masks = {}
    if change == "feature": bad.features[0][0] = 99
    if change == "mask": bad.masks[0][4] = False
    with pytest.raises(ValueError):
        b.attach_successor(bad)
    assert len(b) == 0


def test_repeated_successor_and_wrong_native_command_abort():
    b = SuccessorReplay(8, 79)
    nxt = frame(2, {0: 2}, clock=60001)
    capture(b, frame(1, {0: 1}), nxt)
    b.attach_successor(nxt)
    with pytest.raises(ValueError): b.attach_successor(nxt)
    wrong = nxt.native.copy(); wrong[0, 0] = 3
    with pytest.raises(ValueError): b.commit_confirmed(wrong, nxt.key)
    assert len(b) == 0


def test_actual_action_outside_mask_kept():
    b = SuccessorReplay(8, 79)
    m = mask(); m[5] = False
    nxt = frame(2, {0: 5}, masks={0: m}, clock=60001)
    capture(b, frame(1, {0: 0}), nxt)
    b.attach_successor(nxt)
    b.commit_confirmed(nxt.native, nxt.key)
    assert b.next_action[0] == 5 and not b.mask[0, 5]


def test_core_detected_terminal_and_match_reset_do_not_link():
    b = SuccessorReplay(8, 79)
    capture(b, frame(99, {0: 1}), frame(100, {}, match=1), done={0: True})
    assert b.done[0] == 1 and b.next_action[0] == -1
    b.assert_idle()


def test_core_unrecognized_adjacent_respawn_keeps_core_done():
    cfg = AgentConfig(reward_fix=True)
    before = {"ally_pos": np.array([[0, 0]])}
    after = {"ally_ids": np.array([0]), "ally_pos": np.array([[1, 0]])}
    assert surviving(cfg, before, after) == {0}  # inherited limit, not life identity
    b = SuccessorReplay(8, 79)
    committed(b)
    assert b.done[0] == 0


def test_empty_capture_needs_no_context():
    b = SuccessorReplay(8, 79)
    b.begin_capture({}, dict(episode_id=0, source_step=0, match_idx=0, next_step=1))
    b.finish_capture(None)
    assert len(b) == 0
    b.assert_idle()


def make_agent(mode="double_dqn"):
    return SampledTargetAgent("player_0", cfg=AgentConfig(hidden=8, frozen=False,
        buffer_capacity=8, batch_size=2, learn_start=99), bootstrap_mode=mode, seed=3)


def start(agent, episode=0):
    agent.bind_episode(dict(episode_id=episode, seed=100 + episode, side="player_0",
                            phase="prefill", game=episode, opponent="default"))
    agent.new_game("player_0")


def test_reset_with_pending_aborts():
    a = make_agent(); start(a)
    capture(a.buffer, frame(1, {0: 1}), frame(2, {0: 2}))
    with pytest.raises(ValueError): a.new_game("player_0")
    with pytest.raises(ValueError): a.set_to_eval_mode()


def test_one_parent_act_and_update_noop_without_fresh_cache(monkeypatch):
    a = make_agent(); start(a)
    calls = {"act": 0, "update": 0}
    def parent_act(self, step, obs):
        calls["act"] += 1
        self._prev_feats = {}; self._prev_actions = {}; self._prev_masks = {}
        self._prev_ctx = None; self._cache = (999, {"step": 999})
        return np.zeros((16, 3), dtype=np.int64)
    def parent_update(self, *args):
        calls["update"] += 1; self.env_steps += 1
    monkeypatch.setattr(Agent_x, "_act_est", parent_act)
    monkeypatch.setattr(Agent_x, "_update", parent_update)
    obs = {"steps": 0, "match_steps": 0}
    native = a._act_est(0, obs)
    a._update(0, obs, 0, native, True, {"steps": 1, "match_steps": 1})
    assert calls == {"act": 1, "update": 1}
    assert len(a.buffer) == 0
    a.assert_boundary()


def test_update_action_differs_aborts_before_parent(monkeypatch):
    a = make_agent(); start(a)
    def parent_act(self, step, obs):
        self._prev_feats = {}; self._prev_actions = {}; self._prev_masks = {}
        self._prev_ctx = None
        return np.zeros((16, 3), dtype=np.int64)
    def forbidden(*args): raise AssertionError("parent update must not run")
    monkeypatch.setattr(Agent_x, "_act_est", parent_act)
    monkeypatch.setattr(Agent_x, "_update", forbidden)
    obs = {"steps": 0, "match_steps": 0}
    native = a._act_est(0, obs); native[0, 0] = 1
    with pytest.raises(ValueError):
        a._update(0, obs, 0, native, False, {"steps": 1, "match_steps": 1})


@pytest.mark.parametrize("mirrored,canonical,native", [(False, 1, 1), (True, 1, 2), (True, 2, 1)])
def test_canonical_mirror_and_sap_fallback(monkeypatch, mirrored, canonical, native):
    a = make_agent(); start(a)
    def parent_act(self, step, obs):
        self.belief.mirrored = mirrored
        self._prev_ctx = dict(step=step, match_idx=0, sap_range=3)
        self._prev_feats = {0: feat()}; self._prev_masks = {0: mask()}
        self._prev_actions = {0: canonical}
        result = np.zeros((16, 3), dtype=np.int64); result[0, 0] = native
        return result
    monkeypatch.setattr(Agent_x, "_act_est", parent_act)
    result = a._act_est(0, {"steps": 0, "match_steps": 1})
    assert result[0, 0] == native


def test_sap_without_target_mismatch_aborts(monkeypatch):
    a = make_agent(); start(a)
    def parent_act(self, step, obs):
        self._prev_ctx = dict(step=step, match_idx=0, sap_range=3)
        self._prev_feats = {0: feat()}; self._prev_masks = {0: mask()}
        self._prev_actions = {0: 5}
        return np.zeros((16, 3), dtype=np.int64)  # Core fallback emits STAY
    monkeypatch.setattr(Agent_x, "_act_est", parent_act)
    with pytest.raises(ValueError): a._act_est(0, {"steps": 0, "match_steps": 1})


def test_successor_counter_is_pre_update_value():
    b = SuccessorReplay(8, 79)
    for episode, clock, learning_clock in [(0, 60001, 60002), (1, 60002, 60004)]:
        nxt = frame(2, {0: 2}, episode=episode, clock=clock)
        capture(b, frame(1, {0: 1}, episode=episode), nxt)
        b.attach_successor(nxt); b.commit_confirmed(nxt.native, nxt.key)
        assert learning_clock - b.next_action_env_steps[episode] == episode + 1


def test_real_core_update_releases_only_confirmed_batch_before_learning():
    # Small public observations, no engine/game: exercises the real Parent update.
    from tests.conftest import make_obs
    a = make_agent()
    a.cfg.learn_start = 1; a.cfg.batch_size = 1
    a.env_steps = 60000
    start(a)
    observations = [make_obs(step, step, units=[(5, 5, 100)]) for step in (10, 11, 12)]
    first = a.act(10, observations[0])
    a.update(10, observations[0], 0, first, False, observations[1])
    assert len(a.buffer) == 0 and a.learn_steps == 0
    second = a.act(11, observations[1])
    assert len(a.buffer) == 0 and a.env_steps == 60001
    second_class = int(a._prev_actions[0])
    a.update(11, observations[1], 0, second, True, observations[2])
    assert len(a.buffer) == 2 and a.learn_steps == 1
    assert a.buffer.next_action[0] == second_class
    assert a.buffer.next_action_env_steps[0] == 60001
    assert a.bootstrap_stats["label_age_sum"] == 1
    assert a.buffer.done[:2].tolist() == [0., 1.]
    assert a.buffer.next_action[1] == -1
    a.assert_boundary()


def test_valid_native_sap_target_outside_proposal_mask(monkeypatch):
    a = make_agent(); start(a)
    def parent_act(self, step, obs):
        self._prev_ctx = dict(step=step, match_idx=0, sap_range=3)
        self._prev_feats = {0: feat()}; self._prev_actions = {0: 5}
        self._prev_masks = {0: mask()}; self._prev_masks[0][5] = False
        self._sap_hits = {0: 0}
        result = np.zeros((16, 3), dtype=np.int64); result[0] = [5, 1, -1]
        return result
    monkeypatch.setattr(Agent_x, "_act_est", parent_act)
    assert a._act_est(0, {"steps": 0, "match_steps": 1})[0].tolist() == [5, 1, -1]


def test_ring_wrap_keeps_all_columns_aligned(tmp_path):
    b = SuccessorReplay(3, 79)
    for step in range(1, 6): committed(b, step, next_action=step % 6)
    path = tmp_path / "b.npz"; b.save(path)
    with np.load(path, allow_pickle=False) as data:
        assert data["source_step"].tolist() == [3, 4, 5]
        assert data["next_action"].tolist() == [3, 4, 5]
        assert data["next_action_env_steps"].tolist() == [60003, 60004, 60005]
    restored = SuccessorReplay(3, 79)
    assert restored.load(path) == 3
    assert restored.pos == 0
    assert restored.source_step.tolist() == [3, 4, 5]
    np.testing.assert_array_equal(restored.ns[:, 0], [4, 5, 6])


def test_pending_save_rejected(tmp_path):
    b = SuccessorReplay(3, 79)
    capture(b, frame(1, {0: 1}), frame(2, {0: 2}))
    with pytest.raises(ValueError): b.save(tmp_path / "bad.npz")
    assert not (tmp_path / "bad.npz").exists()


def test_direct_legacy_load_entrypoints_rejected(tmp_path):
    a = make_agent()
    with pytest.raises(ValueError): a.load_agent(str(tmp_path / "old.pth"))
    with pytest.raises(ValueError): a.load_buffer(tmp_path / "old.npz")


@pytest.mark.parametrize("fault", ["legacy", "missing", "dtype", "label", "version"])
def test_invalid_buffer_rejected_before_mutation(tmp_path, fault):
    b = SuccessorReplay(3, 79); committed(b)
    path = tmp_path / "good.npz"; b.save(path)
    with np.load(path, allow_pickle=False) as z:
        data = {k: z[k].copy() for k in z.files}
    if fault == "legacy": data = {k: data[k] for k in ("s", "a", "r", "ns", "done", "mask")}
    if fault == "missing": del data["uid"]
    if fault == "dtype": data["next_action"] = data["next_action"].astype(np.int64)
    if fault == "label": data["next_action"][0] = -1
    if fault == "version": data["schema_version"] = np.array(99, dtype=np.int64)
    broken = tmp_path / "bad.npz"; np.savez(broken, **data)
    restored = SuccessorReplay(3, 79)
    with pytest.raises(ValueError): restored.load(broken)
    assert restored.size == restored.pos == 0


def test_targets_masked_ddqn_sampled_and_terminal():
    online = torch.tensor([[1., 9., 4., 0., 0., 0.], [1., 0., 0., 0., 0., 0.]])
    target = torch.tensor([[2., 20., 7., 0., 0., 13.], [99., 0., 0., 0., 0., 0.]])
    m = torch.tensor([[True, False, True, True, True, False], [True] * 6])
    r = torch.tensor([[3.], [11.]]); done = torch.tensor([[0.], [1.]])
    ctrl, sampled, best = pilot.bootstrap_targets(online, target, r, done, m,
                                                 torch.tensor([5, -1]), .5)
    assert best[:, 0].tolist() == [2, 0]
    assert ctrl[:, 0].tolist() == [6.5, 11.]
    assert sampled[:, 0].tolist() == [9.5, 11.]  # SAP despite network mask
    with pytest.raises(ValueError):
        pilot.bootstrap_targets(online, target, r, done, m, torch.tensor([-1, -1]), .5)


def assert_tree_equal(x, y):
    if isinstance(x, torch.Tensor): assert torch.equal(x, y)
    elif isinstance(x, np.ndarray): np.testing.assert_array_equal(x, y)
    elif isinstance(x, dict):
        assert x.keys() == y.keys()
        for k in x: assert_tree_equal(x[k], y[k])
    elif isinstance(x, (list, tuple)):
        assert len(x) == len(y)
        for a, b in zip(x, y): assert_tree_equal(a, b)
    else: assert x == y


@pytest.mark.parametrize("initial_updates", [0, 499])
def test_control_update_matches_core_on_committed_batch(initial_updates):
    torch.manual_seed(4)
    cfg = AgentConfig(hidden=8, frozen=False, buffer_capacity=8, batch_size=2)
    core = Agent_x("player_0", cfg=copy.deepcopy(cfg), seed=7)
    candidate = SampledTargetAgent("player_0", cfg=copy.deepcopy(cfg), seed=7)
    candidate.q.load_state_dict(core.q.state_dict())
    candidate.target_q.load_state_dict(core.target_q.state_dict())
    for step in (1, 2):
        committed(candidate.buffer, step)
        i = step - 1
        core.buffer.push(candidate.buffer.s[i], candidate.buffer.a[i], candidate.buffer.r[i],
                         candidate.buffer.ns[i], candidate.buffer.done[i], candidate.buffer.mask[i])
    core.learn_steps = candidate.learn_steps = initial_updates
    core.env_steps = candidate.env_steps = 60010
    core._learn(); candidate._learn()
    for name in ("q", "target_q", "opt"):
        assert_tree_equal(getattr(core, name).state_dict(), getattr(candidate, name).state_dict())
    assert core.learn_steps == candidate.learn_steps
    assert core.recent_losses == candidate.recent_losses
    assert_tree_equal(core.rng.bit_generator.state, candidate.rng.bit_generator.state)


def test_same_successor_as_argmax_gives_identical_updates():
    torch.manual_seed(4)
    control, sampled = make_agent(), make_agent("sampled_successor")
    with torch.no_grad():
        for parameter in control.q.parameters(): parameter.zero_()
        control.q.adv[-1].bias[2] = 3.
    control.target_q.load_state_dict(control.q.state_dict())
    sampled.q.load_state_dict(control.q.state_dict())
    sampled.target_q.load_state_dict(control.target_q.state_dict())
    for step in (1, 2):
        committed(control.buffer, step, next_action=2)
        committed(sampled.buffer, step, next_action=2)
    control.env_steps = sampled.env_steps = 60010
    control._learn(); sampled._learn()
    assert_tree_equal(control.q.state_dict(), sampled.q.state_dict())
    assert_tree_equal(control.opt.state_dict(), sampled.opt.state_dict())


def test_target_delta_sign_counts_survive_cancellation():
    # Exercise the real learner/replay with one sample of each sign, zero and terminal.
    # Summing deltas alone would lose both nonzero observations in this batch.
    a = make_agent(); a.cfg.batch_size = 4
    with torch.no_grad():
        for network in (a.q, a.target_q):
            for parameter in network.parameters(): parameter.zero_()
        a.q.adv[-1].bias[0] = 4.
        a.target_q.adv[-1].bias[1] = 2.
        a.target_q.adv[-1].bias[2] = -2.
    for step, next_action in enumerate((1, 2, 0), 1):
        committed(a.buffer, step, next_action=next_action)
    capture(a.buffer, frame(4, {0: 1}), frame(5, {0: 0}), done={0: True})
    class FixedBatchRng:
        def integers(self, low, high, *, size):
            assert (low, high, size) == (0, 4, 4)
            return np.array([0, 1, 2, 3], dtype=np.int64)
    a.rng = FixedBatchRng()
    a.env_steps = 60010
    a._learn()
    assert a.bootstrap_stats["nonterminal"] == 3
    assert a.bootstrap_stats["different_target"] == 2
    assert a.bootstrap_stats["target_delta_positive"] == 1
    assert a.bootstrap_stats["target_delta_negative"] == 1
    assert a.bootstrap_stats["target_delta_sum"] == pytest.approx(0.)


def finished_agent(monkeypatch):
    a = make_agent(); start(a)
    def parent_act(self, step, obs):
        self._prev_feats = {}; self._prev_actions = {}; self._prev_masks = {}
        self._prev_ctx = None
        return np.zeros((16, 3), dtype=np.int64)
    def parent_update(self, *args): self.env_steps += 1
    monkeypatch.setattr(Agent_x, "_act_est", parent_act)
    monkeypatch.setattr(Agent_x, "_update", parent_update)
    obs = {"steps": 0, "match_steps": 0}
    command = a._act_est(0, obs)
    a._update(0, obs, 0, command, True, {"steps": 1, "match_steps": 1})
    return a


@pytest.mark.parametrize("fault", ["arm", "mode", "hash", "state_hash"])
def test_bundle_wrong_mode_hash_arm_rejected(tmp_path, monkeypatch, fault):
    a = finished_agent(monkeypatch)
    directory = tmp_path / "bundle"
    metadata = dict(arm="control", input_hashes={}, rollout_progress={"games": 1})
    pilot.save_pilot_bundle(a, directory, metadata)
    expected = dict(arm="control", bootstrap_mode="double_dqn",
                    state_sha256=pilot.file_hash(directory / "pilot_state.json"))
    if fault == "arm": expected["arm"] = "other"
    if fault == "mode": expected["bootstrap_mode"] = "sampled_successor"
    if fault == "hash":
        with (directory / "agent.buffer.npz").open("ab") as sink: sink.write(b"changed")
    if fault == "state_hash":
        with (directory / "pilot_state.json").open("a") as sink: sink.write(" ")
    fresh = make_agent()
    before = copy.deepcopy(fresh.q.state_dict())
    with pytest.raises(ValueError): pilot.load_pilot_bundle(fresh, directory, expected)
    assert_tree_equal(before, fresh.q.state_dict())
    assert len(fresh.buffer) == 0


@pytest.mark.parametrize("fault", ["empty_state", "missing_parameter", "missing_step",
    "missing_exp_avg", "missing_exp_avg_sq", "wrong_step", "negative_step",
    "nonfinite_step", "nonscalar_step"])
def test_bundle_incomplete_adam_rejected_before_mutation(tmp_path, monkeypatch, fault):
    a = finished_agent(monkeypatch)
    for step in (1, 2): committed(a.buffer, step)
    a.env_steps = 60010
    a._learn()
    directory = tmp_path / "bundle"
    state = pilot.save_pilot_bundle(a, directory,
        dict(arm="control", input_hashes={}, rollout_progress={"games": 1}))
    checkpoint_path = directory / "agent.pth"
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    optimizer_state = checkpoint["opt"]["state"]
    first = next(iter(optimizer_state))
    if fault == "empty_state": optimizer_state.clear()
    elif fault == "missing_parameter": del optimizer_state[first]
    elif fault.startswith("missing_"): del optimizer_state[first][fault.removeprefix("missing_")]
    elif fault == "wrong_step": optimizer_state[first]["step"] = torch.tensor(2.)
    elif fault == "negative_step": optimizer_state[first]["step"] = torch.tensor(-1.)
    elif fault == "nonfinite_step": optimizer_state[first]["step"] = torch.tensor(float("nan"))
    elif fault == "nonscalar_step": optimizer_state[first]["step"] = torch.tensor([1.])
    torch.save(checkpoint, checkpoint_path)
    # Rebind both outer hashes: rejection must reach the semantic Adam preflight.
    state["files"]["agent.pth"] = pilot.file_hash(checkpoint_path)
    state_path = directory / "pilot_state.json"
    state_path.write_text(json.dumps(state, indent=2, allow_nan=False) + "\n")
    fresh = make_agent()
    before = {name: copy.deepcopy(getattr(fresh, name).state_dict())
              for name in ("q", "target_q", "opt")}
    clock = (fresh.env_steps, fresh.learn_steps, fresh._inspection_only)
    with pytest.raises(ValueError):
        pilot.load_pilot_bundle(fresh, directory,
            dict(arm="control", bootstrap_mode="double_dqn",
                 state_sha256=pilot.file_hash(state_path)))
    for name, value in before.items(): assert_tree_equal(value, getattr(fresh, name).state_dict())
    assert (fresh.env_steps, fresh.learn_steps, fresh._inspection_only) == clock
    assert len(fresh.buffer) == fresh.buffer.pos == 0


@pytest.mark.parametrize("updates", [0, 1])
def test_bundle_reload_is_inspection_only(tmp_path, monkeypatch, updates):
    a = finished_agent(monkeypatch)
    if updates:
        for step in (1, 2): committed(a.buffer, step)
        a.env_steps = 60010
        a._learn()
    directory = tmp_path / "bundle"
    pilot.save_pilot_bundle(a, directory,
        dict(arm="control", input_hashes={}, rollout_progress={"games": 1}))
    fresh = make_agent()
    pilot.load_pilot_bundle(fresh, directory,
        dict(arm="control", bootstrap_mode="double_dqn",
             state_sha256=pilot.file_hash(directory / "pilot_state.json")))
    assert_tree_equal(a.q.state_dict(), fresh.q.state_dict())
    assert_tree_equal(a.target_q.state_dict(), fresh.target_q.state_dict())
    assert_tree_equal(a.opt.state_dict(), fresh.opt.state_dict())
    assert fresh.learn_steps == updates
    with pytest.raises(ValueError): fresh.set_to_train_mode()
    with pytest.raises(ValueError): start(fresh, 1)
