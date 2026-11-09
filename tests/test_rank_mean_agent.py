"""Synthetic tensors and a small core double; no real QNet, archive, or game."""
from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from agents.sherlock.main import Agent_x
from agents.sherlock.config import AgentConfig
from scripts.rank_mean_agent import RankMeanAgent, legal_midrank_mean


@pytest.fixture(autouse=True)
def forbid_real_models(monkeypatch):
    import agents.sherlock.main as core
    def forbidden(*args, **kwargs):
        raise AssertionError("No real model construction or tensor archive IO")
    monkeypatch.setattr(core, "QNet", forbidden)
    monkeypatch.setattr(torch, "load", forbidden)
    monkeypatch.setattr(torch, "save", forbidden)


class SyntheticMember(torch.nn.Module):
    def __init__(self, index, width):
        super().__init__()
        self.index, self.feat_dim = index, width
        self.inputs = []

    def forward(self, inputs):
        self.inputs.append(inputs.detach().clone())
        values = [1000., 0., 0., 0., 0., 0.] if self.index == 0 else [0., 1., 0., 0., 0., 0.]
        return inputs.new_tensor(values).expand(len(inputs), -1)


@pytest.fixture
def synthetic_core(monkeypatch):
    def init(self, player, agent_path=None, name="test", cfg=None, train=True, seed=None):
        self.cfg = cfg or AgentConfig(frozen=False, art_splash=True)
        self.training = bool(train)
        self.device = torch.device("cpu")
        self.feat_dim, self.n_actions = 4, 6
        self.q = SyntheticMember(0, 4)
        self.extra_q = [SyntheticMember(i, 2 if i % 2 else 4) for i in range(1, 36)]
        self.cnn_policy = None
        self.team_id = int(player[-1]); self.player = player
        self.belief = self.feat_belief = SimpleNamespace(reset_game=lambda: None, set_team=lambda team: None)
        self.env_cfg = {}
        self.core_calls = 0
        self._reset_episode_state()

    def act(self, step, obs):
        self.core_calls += 1
        if obs["match_steps"] == 0:
            return np.zeros((4, 3), int)
        ctx = dict(step=obs["steps"], match_step=obs["match_steps"], ally_ids=np.array(obs["ids"]))
        ids = obs["ids"]
        feats = {u: row for u, row in zip(ids, obs["features"])}
        masks = {u: row for u, row in zip(ids, obs["masks"])}
        self._cache = (obs["steps"], ctx, ids, feats, masks, {})
        self._prev_ctx = ctx
        if not ids:
            return np.zeros((4, 3), int)
        inputs = torch.as_tensor(obs["features"], dtype=torch.float32)
        if obs.get("fault") == "stale": self._cache = (obs["steps"]-1, *self._cache[1:])
        if obs.get("fault") == "context": self._prev_ctx = dict(ctx)
        if obs.get("fault") == "order": inputs = inputs.flip(0)
        if obs.get("fault") == "width": inputs = inputs[:, :-1]
        if obs.get("fault") == "ids": ctx["ally_ids"] = np.array(ids[::-1])
        with torch.no_grad():
            result = self.q(inputs)
            if self.extra_q:
                result = torch.stack([result]+[m(inputs[:, :m.feat_dim]) for m in self.extra_q]).mean(0)
            if obs.get("fault") == "second_forward": self.q(inputs)
        scores = result.cpu().numpy()
        scores[~obs["masks"]] = -np.inf  # Original core mutates its returned score view.
        commands = np.zeros((4, 3), int)
        commands[ids, 0] = scores.argmax(1)
        if obs.get("rule") is not None: commands[ids, 0] = obs["rule"]
        self._prev_actions = {u: int(commands[u, 0]) for u in ids}
        return commands
    monkeypatch.setattr(Agent_x, "__init__", init)
    monkeypatch.setattr(Agent_x, "_act", act)


def frame(step=10):
    return dict(steps=step, match_steps=step, ids=[3, 1],
                features=np.array([[3., 4., 5., 6.], [7., 8., 9., 10.]], np.float32),
                masks=np.array([[True, True, False, False, False, False]]*2))


def test_exact_legal_midranks_singleton_and_indifference():
    q = torch.tensor([[[10., 10., 20., -999., 1000., -2.],
                       [7., 7., 7., 7., 7., 7.],
                       [20., 30., 40., 50., 60., 70.]]])
    mask = torch.tensor([[1, 1, 1, 0, 0, 1], [1, 0, 1, 0, 1, 0], [0, 0, 0, 1, 0, 0]], dtype=torch.bool)
    want = torch.tensor([[.5, .5, 1., -1., -1., 0.], [.5, -1., .5, -1., .5, -1.], [-1., -1., -1., .5, -1., -1.]])
    torch.testing.assert_close(legal_midrank_mean(q, mask), want, rtol=0, atol=0)


def test_large_scales_do_not_outvote_ranks_and_affine_transforms_preserve_them():
    q = torch.tensor([[[1000., 0., -999., -1., 1e20, 1e10]],
                      [[0., 1., 999., 7., 0., -1.]], [[0., 1., 100., 100., 100., 100.]]], dtype=torch.float64)
    mask = torch.tensor([[True, True, False, False, False, False]])
    expected = torch.tensor([[1/3, 2/3, -1., -1., -1., -1.]], dtype=torch.float64)
    torch.testing.assert_close(legal_midrank_mean(q, mask), expected)
    transformed = q*torch.tensor([2., 30., .5])[:, None, None]+torch.tensor([4., -10., 7.])[:, None, None]
    torch.testing.assert_close(legal_midrank_mean(transformed, mask), expected)
    assert q.mean(0)[:, :2].argmax().item() == 0


def test_member_order_does_not_break_exact_midrank_ties():
    q = torch.tensor([[[0., 1., 2., 3., 4., 5.]], [[5., 4., 3., 2., 1., 0.]]]*18)
    masks = torch.ones((1, 6), dtype=torch.bool)
    result = legal_midrank_mean(q, masks)
    torch.testing.assert_close(result, torch.full((1, 6), .5), rtol=0, atol=0)
    torch.testing.assert_close(legal_midrank_mean(q.flip(0), masks), result, rtol=0, atol=0)
    assert result.argmax(1).tolist() == [0]


@pytest.mark.parametrize("fault", ["nan_legal", "inf_illegal", "empty_mask", "shape", "mask_dtype"])
def test_invalid_values_and_masks_are_technical_errors(fault):
    q = torch.zeros((2, 1, 6))
    masks = torch.tensor([[True, True, False, False, False, False]])
    if fault == "nan_legal": q[0, 0, 0] = float("nan")
    if fault == "inf_illegal": q[0, 0, 5] = float("inf")
    if fault == "empty_mask": masks[:] = False
    if fault == "shape": q = q[:, :, :5]
    if fault == "mask_dtype": masks = masks.float()
    with pytest.raises(ValueError): legal_midrank_mean(q, masks)


def test_on_uses_original_members_once_and_records_actual_order_and_legal_proposals(synthetic_core):
    a = RankMeanAgent("player_0", rank_enabled=True)
    members = a.aggregation_members
    obs = frame()
    result = a._act(10, obs)
    assert result[[3, 1], 0].tolist() == [1, 1] and a.core_calls == 1
    assert len(members) == len({id(m) for m in members}) == 36 and a.extra_q == []
    for m in members:
        assert len(m.inputs) == 1
        np.testing.assert_array_equal(m.inputs[0], obs["features"][:, :m.feat_dim])
    info = a.aggregation_last
    assert info["step"] == 10 and info["ids"] == (3, 1)
    assert tuple(info["member_q"].shape) == (36, 2, 6)
    assert info["raw_greedy"].tolist() == [0, 0] and info["rank_greedy"].tolist() == [1, 1]
    assert info["rank_mean"][:, 2:].eq(-1).all()  # Unaffected by core's -inf mask mutation.
    assert dict(a.aggregation_stats) == dict(calls=1, proposal_changes=2, proposal_changed_steps=1)


def test_off_is_original_path_and_instance_local(synthetic_core):
    off = RankMeanAgent("player_0")
    on = RankMeanAgent("player_0", rank_enabled=True)
    baseline = Agent_x("player_0", train=False)
    original_q = off.q
    obs = frame()
    np.testing.assert_array_equal(off._act(10, deepcopy(obs)), baseline._act(10, deepcopy(obs)))
    assert off.q is original_q is off.aggregation_members[0] and len(off.extra_q) == 35
    assert off.aggregation_last is None and not any(off.aggregation_stats.values())
    on._act(10, obs)
    assert all(len(m.inputs) == 1 for m in off.aggregation_members)
    assert not set(map(id, on.aggregation_members)) & set(map(id, off.aggregation_members))


@pytest.mark.parametrize("fault", ["stale", "context", "order", "width", "ids", "second_forward"])
def test_cache_and_actual_feature_binding_fail_closed(synthetic_core, fault):
    a = RankMeanAgent("player_0", rank_enabled=True)
    obs = frame(); obs["fault"] = fault
    with pytest.raises((ValueError, RuntimeError)): a._act(10, obs)
    expected_calls = 1 if fault == "second_forward" else 0
    assert all(len(m.inputs) == expected_calls for m in a.aggregation_members)


def test_reset_no_units_and_new_game_clear_diagnostics_without_replacing_members(synthetic_core):
    a = RankMeanAgent("player_0", rank_enabled=True)
    aggregator, members = a.q, a.aggregation_members
    a._act(10, frame())
    reset = frame(11); reset["match_steps"] = 0
    a._act(11, reset)
    assert a.aggregation_last is None and a.aggregation_stats["calls"] == 1
    empty = frame(12); empty["ids"] = []
    a._act(12, empty)
    assert a.aggregation_last is None and all(len(m.inputs) == 1 for m in members)
    a.new_game("player_1")
    assert a.team_id == 1 and a.q is aggregator and a.aggregation_members == members
    assert a.aggregation_last is None and not any(a.aggregation_stats.values())
    a._act(10, frame())
    assert all(len(m.inputs) == 2 for m in members)


def test_original_remember_and_downstream_rule_use_the_actual_final_commands(synthetic_core):
    a = RankMeanAgent("player_0", rank_enabled=True)
    events = []
    def observe(*args): events.append("observe")
    def remember(obs, team, commands):
        events.append("remember")
        np.testing.assert_array_equal(commands[[3, 1], 0], [3, 3])
    a.param_est = SimpleNamespace(observe=observe, remember=remember)
    obs = frame(); obs["rule"] = 3
    result = a._act_est(10, obs)
    assert events == ["observe", "remember"] and a.core_calls == 1
    assert result[[3, 1], 0].tolist() == [3, 3]
    assert a.aggregation_last["rank_greedy"].tolist() == [1, 1]


def test_training_saving_and_post_construction_reload_are_forbidden(synthetic_core):
    with pytest.raises(ValueError): RankMeanAgent("player_0", train=True)
    a = RankMeanAgent("player_0", rank_enabled=True)
    assert not a.learn_enabled and not a.autosave_on_terminate
    for method, args in [(a.set_to_train_mode, ()), (a.update, ()),
                         (a.save_agent, ("forbidden.pth",)), (a.save_buffer, ("forbidden.npz",)),
                         (a.load_agent, ("forbidden.pth",)), (a.q.train, ())]:
        with pytest.raises(RuntimeError): method(*args)
    a.training = True
    with pytest.raises(RuntimeError): a._act(10, frame())
    assert a.core_calls == 0


@pytest.mark.parametrize("fault", ["count", "duplicate", "width", "first_width", "frozen"])
def test_constructor_rejects_non_v14_member_contract_and_silent_error_mode(synthetic_core, monkeypatch, fault):
    original_init = Agent_x.__init__
    def init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        if fault == "count": self.extra_q.pop()
        if fault == "duplicate": self.extra_q[0] = self.q
        if fault == "width": self.extra_q[0].feat_dim = 5
        if fault == "first_width": self.q.feat_dim = 2
        if fault == "frozen": self.cfg.frozen = True
    monkeypatch.setattr(Agent_x, "__init__", init)
    with pytest.raises(ValueError): RankMeanAgent("player_0", rank_enabled=True)
