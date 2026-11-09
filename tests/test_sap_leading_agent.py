"""Synthetic hook contracts: no QNet construction, weights, forward, or game."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sap_leading_agent import SapLeadingAgent
from agents.sherlock.main import Agent_x
from agents.sherlock.config import AgentConfig
from agents.sherlock import geometry as geo


@pytest.fixture(autouse=True)
def forbid_real_models(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No models, weights, or forward calls in this suite")
    import agents.sherlock.main as core
    monkeypatch.setattr(core, "QNet", forbidden)
    monkeypatch.setattr(core.torch, "load", forbidden)
    def fake_init(self, player, agent_path=None, name="test", cfg=None, train=True, seed=None):
        self.cfg = cfg or AgentConfig(art_splash=True, frozen=False)
        self.training = bool(train)
        self.team_id = int(player[-1])
        self.player = player
        self.env_cfg = {}
        self.belief = SimpleNamespace(mirrored=self.team_id == 1)
        self.autosave_on_terminate = True
        self.learn_enabled = True
        self.caught_errors = 0
        self.core_calls = 0
        self._reset_episode_state()
    def fake_act(self, step, obs):
        self.core_calls += 1
        ctx = obs["ctx"]
        self._cache = (int(obs["steps"]), ctx, [], {}, {}, {})
        self._prev_ctx = ctx
        self._sap_hits = {1: obs.get("old_hits", 2), 3: 2}
        self._sap_unknown = {1, 3}
        self._prev_actions = {1: 5, 3: 5, 0: 2}
        self._prev_feats = {1: np.array([2., 3.])}
        self._prev_masks = {1: np.ones(6, bool)}
        self._pred_pending = [(1, 1, 2, 40., True)]
        self._shape_pending = [(1, 1, 2, 40., True, "man")]
        self.ep_stats["sap_attempts"] += 2
        self.ep_stats["sap_hits_est"] += int(self._sap_hits[1] > 0) + 1
        result = obs["actions"].copy()
        self.last_core_result = result
        if obs.get("stale_cache"):
            self._cache = (int(obs["steps"])-1, ctx)
        if obs.get("missing_cache"):
            self._cache = None
        return result
    monkeypatch.setattr(Agent_x, "__init__", fake_init)
    monkeypatch.setattr(Agent_x, "_act", fake_act)


def frame(step=10, *, enemy=(3, 2), energy=20, match=0, ms=None, mirrored=False):
    pos = np.array([[0, 0], [1, 2], [-1, -1], [1, 2]])
    coords = np.array([enemy, (2, 1)], dtype=int)
    ctx = dict(step=step, match_step=step if ms is None else ms, match_idx=match,
               W=6, H=6, ally_ids=np.array([3, 1]), ally_pos=pos,
               ally_ene=np.array([20., 40., -1., 40.]),
               enemy_vis_ids=np.array([7, 8]), enemy_coords=coords,
               enemy_energies=np.array([float(energy), 20.]),
               passable=np.ones((6, 6), bool), sap_cost=20., move_cost=3., sap_range=4)
    action = np.array([[2, 0, 0], [5, 2, 0], [0, 0, 0], [5, 2, 0]])
    if mirrored:
        for uid in (1, 3): action[uid, 1:] = geo.mirror_delta(*action[uid, 1:])
    public_pos = np.full((2, 4, 2), -1)
    public_pos[0] = pos
    return dict(steps=step, match_steps=ctx["match_step"], ctx=ctx, actions=action,
                sensor_mask=np.ones((6, 6), bool),
                units={"position": public_pos, "energy": np.ones((2, 4))*40},
                units_mask=np.ones((2, 4), bool),
                map_features={"energy": np.zeros((6, 6)), "tile_type": np.zeros((6, 6))})


def agent(enabled=True, mirrored=False):
    a = SapLeadingAgent("player_1" if mirrored else "player_0", lead_enabled=enabled)
    a.param_est.log_drop = np.array([0., -50., -50.])
    a.param_est.n_drop = 1
    return a


def prime(a, **kwargs):
    old = frame(9, enemy=(2, 2), mirrored=a.belief.mirrored, **kwargs)
    a._act(9, old)
    return old


@pytest.mark.parametrize("mirrored,want", [(False, [5, 3, 0]), (True, [5, 0, -3])])
def test_known_public_lead_changes_only_smallest_uid(mirrored, want):
    a = agent(mirrored=mirrored)
    prime(a)
    obs = frame(mirrored=mirrored)
    before = obs["actions"].copy()
    result = a._act(10, obs)
    assert result[1].tolist() == want
    np.testing.assert_array_equal(result[[0, 2, 3]], before[[0, 2, 3]])
    np.testing.assert_array_equal(obs["actions"], before)
    assert a.core_calls == 2
    assert a.leading_stats["eligible_saps"] == 2
    assert a.leading_stats["changes"] == 1
    assert a.leading_last["uid"] == 1


def test_default_disabled_preserves_original_actions_and_productive_state():
    a = SapLeadingAgent("player_0")
    base = Agent_x("player_0", train=False)
    for obs in (frame(9, enemy=(2, 2)), frame()):
        x, y = a._act(obs["steps"], deepcopy(obs)), base._act(obs["steps"], deepcopy(obs))
        np.testing.assert_array_equal(x, y)
    for field in ("_sap_hits", "_sap_unknown", "_prev_actions", "_pred_pending", "_shape_pending", "ep_stats"):
        assert getattr(a, field) == getattr(base, field)
    assert a.leading_stats["changes"] == 0
    assert a.autosave_on_terminate is False and a.learn_enabled is False


@pytest.mark.parametrize("train", [True, 1])
def test_constructor_rejects_training_before_parent_initialization(train):
    with pytest.raises(ValueError, match="eval"):
        SapLeadingAgent("player_0", train=train)


def test_training_and_update_interfaces_reject():
    a = agent()
    with pytest.raises(RuntimeError): a.set_to_train_mode()
    with pytest.raises(RuntimeError): a.update(None)
    a.training = True
    with pytest.raises(RuntimeError): a._act(10, frame())
    assert a.core_calls == 0


@pytest.mark.parametrize("probs,n,want", [
    ([.901, .049, .05], 1, True), ([.899, .051, .05], 1, False),
    ([.049, .901, .05], 1, True), ([.05, .049, .901], 1, False),
    ([.99, .005, .005], 0, False),
])
def test_real_estimator_confidence_boundary(probs, n, want):
    a = agent(); prime(a)
    a.param_est.log_drop = np.log(probs)
    a.param_est.n_drop = n
    result = a._act(10, frame())
    assert (result[1, 1] == 3) == want


@pytest.mark.parametrize("confidence,want", [(0.9, True), (0.8999999999999999, False)])
def test_exact_posterior_boundary_without_log_exp_rounding(confidence, want):
    a = agent(); prime(a)
    # Keep the real dropoff method; synthetic exact posterior avoids log/exp
    # roundoff turning a requested 0.9 into 0.8999999999999999.
    a.param_est._posterior = lambda logp: np.array([confidence, .05, .05])
    result = a._act(10, frame())
    assert (result[1, 1] == 3) == want


@pytest.mark.parametrize("case", ["own_energy", "previous_energy", "current_energy", "move_energy",
    "stay", "diagonal", "jump", "missing_uid", "ambiguous", "old_range", "new_range",
    "offboard", "sensor", "passable", "step_gap", "match_gap", "matchstep_gap",
    "stale_cache", "missing_cache", "estimator_off"])
def test_public_exclusions_never_change_actions(case):
    a = agent()
    previous = frame(9, enemy=(2, 2))
    current = frame()
    p, c = previous["ctx"], current["ctx"]
    if case == "own_energy": c["ally_ene"][[1, 3]] = 19
    if case == "previous_energy": p["enemy_energies"][0] = -1
    if case == "current_energy": c["enemy_energies"][0] = -1
    if case == "move_energy": c["enemy_energies"][0] = 2
    if case == "stay": p["enemy_coords"][0] = (3, 2)
    if case == "diagonal": p["enemy_coords"][0] = (2, 1)
    if case == "jump": p["enemy_coords"][0] = (1, 2)
    if case == "missing_uid": p["enemy_vis_ids"][0] = 6
    if case == "ambiguous": c["enemy_coords"][1] = (3, 2)
    if case == "old_range": c["sap_range"] = 1
    if case == "new_range": c["sap_range"] = 2
    if case == "offboard":
        p["enemy_coords"][0] = (4, 2); c["enemy_coords"][0] = (5, 2)
        current["actions"][[1, 3], 1] = 4
    if case == "sensor": current["sensor_mask"][4, 2] = False
    if case == "passable": c["passable"][4, 2] = False
    if case == "step_gap": previous["steps"] = p["step"] = 8
    if case == "match_gap": c["match_idx"] = 1
    if case == "matchstep_gap": current["match_steps"] = c["match_step"] = 12
    if case in ("stale_cache", "missing_cache"): current[case] = True
    if case == "estimator_off":
        for key in ("nebula_avoid", "dodge_auto", "sap_dropoff_est", "art_splash", "sap_still_splash"):
            setattr(a.cfg, key, False)
    a._act(previous["steps"], previous)
    result = a._act(10, current)
    np.testing.assert_array_equal(result, current["actions"])
    assert a.leading_stats["changes"] == 0


def test_threshold_energies_equal_and_chebyshev_edge_are_allowed():
    a = agent(); prime(a)
    obs = frame(energy=3)
    obs["ctx"]["ally_ene"][[1, 3]] = 20
    obs["ctx"]["sap_range"] = 3
    assert a._act(10, obs)[1].tolist() == [5, 3, 0]


@pytest.mark.parametrize("mirrored", [False, True])
def test_current_sensor_uses_canonical_xy_and_actual_mirror_flag(mirrored):
    a = agent(mirrored=mirrored); prime(a)
    obs = frame(mirrored=mirrored)
    canonical = np.ones((6, 6), bool); canonical[2, 4] = False
    obs["sensor_mask"] = geo.mirror_map(canonical) if mirrored else canonical
    assert a._act(10, obs)[1].tolist() != obs["actions"][1].tolist()
    a = agent(mirrored=mirrored); prime(a)
    canonical[4, 2] = False
    obs["sensor_mask"] = geo.mirror_map(canonical) if mirrored else canonical
    np.testing.assert_array_equal(a._act(10, obs), obs["actions"])


def test_lower_ineligible_uid_does_not_hide_higher_eligible_shooter():
    a = agent(); prime(a)
    obs = frame(); obs["ctx"]["ally_ene"][1] = 19
    result = a._act(10, obs)
    assert result[1].tolist() == [5, 2, 0]
    assert result[3].tolist() == [5, 3, 0]
    assert a.leading_last["uid"] == 3


@pytest.mark.parametrize("old_hits", [0, 2])
def test_target_bookkeeping_is_delta_not_extra_sap(old_hits):
    a = agent(); prime(a)
    obs = frame(); obs["old_hits"] = old_hits
    stats_before = dict(a.ep_stats)
    a._act(10, obs)
    assert a._sap_hits == {1: 1, 3: 2}
    assert a._sap_unknown == {3}
    assert a.ep_stats["sap_attempts"] - stats_before["sap_attempts"] == 2
    assert a.ep_stats["sap_hits_est"] - stats_before["sap_hits_est"] == 2
    assert a._prev_actions == {1: 5, 3: 5, 0: 2}
    assert a._pred_pending == [(1, 1, 2, 40., True)]
    assert a._shape_pending == [(1, 1, 2, 40., True, "man")]
    np.testing.assert_array_equal(a._prev_feats[1], [2., 3.])
    assert a._prev_masks[1].all()


def test_original_act_est_observes_before_and_remembers_changed_native_command():
    a = agent(mirrored=True); prime(a)
    a.param_est.log_drop[:] = 0
    events = []
    def observe(*args):
        events.append("observe")
        a.param_est.log_drop[:] = [0, -50, -50]
    original_remember = a.param_est.remember
    def remember(obs, team, actions):
        events.append("remember")
        assert actions[1].tolist() == [5, 0, -3]
        original_remember(obs, team, actions)
    a.param_est.observe = observe
    a.param_est.remember = remember
    result = a._act_est(10, frame(mirrored=True))
    np.testing.assert_array_equal(a.param_est._prev["act"], result)
    assert events == ["observe", "remember"] and a.core_calls == 2


def test_previous_public_record_copies_mutable_input_and_survives_core_cache_change():
    a = agent(); previous = prime(a)
    previous["ctx"]["enemy_coords"][0] = (5, 5)
    previous["ctx"]["enemy_energies"][0] = -1
    a._enemy_prev = {7: (3, 2)}
    assert a._act(10, frame())[1].tolist() == [5, 3, 0]


def test_reset_and_episode_reset_clear_history_and_episode_counters():
    a = agent(); prime(a)
    a._act(10, frame(10, ms=0))
    current = frame(11, ms=1)
    np.testing.assert_array_equal(a._act(11, current), current["actions"])
    a._reset_episode_state()
    assert not a.leading_stats and a.leading_last is None
    np.testing.assert_array_equal(a._act(10, frame()), frame()["actions"])


def test_new_game_calls_original_reset_without_model_construction():
    a = agent(); prime(a)
    b = SimpleNamespace(reset_game=Mock(), set_team=Mock())
    a.belief = a.feat_belief = b
    a.new_game()
    b.reset_game.assert_called_once()
    assert a._leading_previous is None and not a.leading_stats


def test_no_fresh_cache_and_no_sap_do_not_invent_intervention():
    a = agent(); prime(a)
    obs = frame(); obs["actions"][[1, 3]] = [0, 0, 0]
    result = a._act(10, obs)
    np.testing.assert_array_equal(result, obs["actions"])
    assert a.leading_stats["changes"] == 0 and a.leading_last is None
