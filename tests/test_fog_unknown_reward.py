"""Synthetic final Fog origin and opt-in reward contracts; no engine games."""
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from agents.sherlock import geometry as geo, rules
from agents.sherlock.config import AgentConfig
from agents.sherlock.reward import unit_rewards
from tests.conftest import make_obs
from tests.test_rules_1910 import _stay_agent
from tests.test_terminal_death_potential import context


def reward_config(enabled=False, **kw):
    cfg = AgentConfig(reward_fix=True, terminal_death_potential=True,
                      w_point=0, w_shape=0, w_energy=0, w_stack=0,
                      w_explore=0, w_discovery=0, w_match=0, w_death=0,
                      w_sap_hit=0.3)
    cfg.fog_unknown_reward_neutral = enabled
    return replace(cfg, **kw)


def test_default_and_old_checkpoint_keep_fog_miss_penalty():
    for cfg in (AgentConfig(), AgentConfig.from_dict({"w_sap_hit": 0.3})):
        assert getattr(cfg, "fog_unknown_reward_neutral", None) is False
        cfg.w_shape = cfg.w_energy = 0
        assert unit_rewards(cfg, context(), context(), {0: geo.SAP}, {0: 0})[0] == -0.3


@pytest.mark.parametrize("hits,want", [(3, 0.9), (1, 0.3), (0, -0.3), (-2, -0.3)])
def test_known_hit_estimates_keep_existing_reward(hits, want):
    cfg = reward_config(True)
    assert unit_rewards(cfg, context(), context(), {0: geo.SAP}, {0: hits},
                        unknown_sap=set())[0] == pytest.approx(want)


@pytest.mark.parametrize("enabled,marked,action,weight,shaping,want", [
    (True, True, geo.SAP, 0.3, True, 0.0),
    (False, True, geo.SAP, 0.3, True, -0.3),
    (True, False, geo.SAP, 0.3, True, -0.3),
    (True, True, geo.STAY, 0.3, True, 0.0),
    (True, True, geo.SAP, 0.0, True, 0.0),
    (True, True, geo.SAP, 0.3, False, 0.0),
])
def test_only_opted_in_final_unknown_sap_omits_hit_term(enabled, marked, action, weight, shaping, want):
    cfg = reward_config(enabled, w_sap_hit=weight, use_shaping=shaping)
    assert unit_rewards(cfg, context(), context(), {0: action}, {0: 0},
                        unknown_sap={0} if marked else set())[0] == pytest.approx(want)


def test_omitted_provenance_or_missing_flag_retains_old_reward():
    cfg = reward_config(True)
    assert unit_rewards(cfg, context(), context(), {0: geo.SAP}, {0: 0})[0] == -0.3
    old_cfg = SimpleNamespace(**{k: v for k, v in cfg.to_dict().items()
                                if k != "fog_unknown_reward_neutral"})
    assert unit_rewards(old_cfg, context(), context(), {0: geo.SAP}, {0: 0},
                        unknown_sap={0})[0] == -0.3


@pytest.mark.parametrize("alive,terminal,expected_base", [
    (True, False, 0.0125), (False, False, 0.75),
    (True, True, 1.25), (False, True, 0.75),
])
def test_unknown_delta_preserves_potential_death_and_terminal_terms(alive, terminal, expected_base):
    before = context()
    after = context(alive=alive, step=0 if terminal else 61)
    cfg = reward_config(False, w_shape=0.5, w_death=0.5)
    control = unit_rewards(cfg, before, after, {0: geo.SAP}, {0: 0}, unknown_sap={0})[0]
    neutral = unit_rewards(replace(cfg, fog_unknown_reward_neutral=True), before, after,
                           {0: geo.SAP}, {0: 0}, unknown_sap={0})[0]
    assert control == pytest.approx(expected_base - 0.3)
    assert neutral == pytest.approx(expected_base)
    assert neutral - control == pytest.approx(0.3)


def fog_agent(enabled=False, training=False, **kw):
    a = _stay_agent(hidden=16, buffer_capacity=64, learn_start=10**9,
                    eps_start=0, eps_end=0, fog_sap=True, fog_v2=True, **kw)
    a.cfg.fog_unknown_reward_neutral = enabled
    if training:
        a.set_to_train_mode()
        a.autosave_on_terminate = False
    for x, y in ((10, 11), (12, 13)):
        a.belief.point_tiles[x, y] = True
    return a


def fog_obs(step=10, match_step=10, team=0, units=((10, 11, 200),)):
    obs = make_obs(step, match_step, team=team, units=units, points=(1, 1),
                   relics=[(11, 12)], sensor_all=False)
    for x, y, _ in units:
        obs["sensor_mask"][x-1:x+2, y-1:y+2] = True
    return obs


@pytest.mark.parametrize("enabled", [False, True])
def test_real_fog_path_marks_final_uid_without_changing_numeric_hits(enabled):
    a = fog_agent(enabled)
    action = a.act(10, fog_obs())
    assert tuple(action[0]) == (geo.SAP, 2, 2)
    assert a._sap_unknown == {0}
    assert a._sap_hits == {0: 0}
    assert a._prev_actions == {0: geo.SAP}
    assert a.ep_stats["sap_attempts"] == 1 and a.ep_stats["sap_hits_est"] == 0


@pytest.mark.parametrize("replacement,want_action,want_hits", [
    ((1, 0, 2), geo.SAP, {0: 2}),
    ((2, 2, 1), geo.SAP, {0: 1}),
    ((2, 2, 0), geo.SAP, {0: 0}),
    (None, geo.STAY, {}),
])
def test_smart_replacement_even_equal_tuple_values_are_known(monkeypatch, replacement, want_action, want_hits):
    a = fog_agent(smart_sap=True)
    # Fresh tuple with the Fog coordinates must not inherit its origin.
    monkeypatch.setattr(rules, "plan_sap", lambda *args: replacement)
    action = a.act(10, fog_obs())
    assert action[0, 0] == want_action
    assert a._sap_hits == want_hits
    assert a._sap_unknown == set()


@pytest.mark.parametrize("cancellation", ["overkill", "moving_target", "holder_move"])
def test_later_safety_rules_cannot_leave_unknown_origin(monkeypatch, cancellation):
    a = fog_agent(sap_no_overkill=cancellation == "overkill",
                  sap_still_all=cancellation == "moving_target",
                  holder_guard=cancellation == "holder_move")
    monkeypatch.setattr(a, "_overkill", lambda *args: True)
    monkeypatch.setattr(a, "_sap_on_still", lambda *args: False)
    monkeypatch.setattr(a, "_holder_guard", lambda *args: geo.RIGHT)
    action = a.act(10, fog_obs())
    assert action[0, 0] == (geo.RIGHT if cancellation == "holder_move" else geo.STAY)
    assert a._sap_unknown == set() and a._sap_hits == {}


def test_origin_does_not_leak_to_next_uid_or_next_frame_or_reset(monkeypatch):
    a = fog_agent()
    original = a._fog_sap
    monkeypatch.setattr(a, "_fog_sap", lambda ctx, uid, planned: original(ctx, uid, planned) if uid == 0 else None)
    action = a.act(10, fog_obs(units=((10, 11, 200), (9, 11, 200))))
    assert action[0, 0] == geo.SAP and action[1, 0] == geo.STAY
    assert a._sap_unknown == {0}
    monkeypatch.setattr(a, "_fog_sap", lambda *args: None)
    assert a.act(11, fog_obs(11, 11))[0, 0] == geo.STAY
    assert a._sap_unknown == set()
    a._sap_unknown.add(9)
    a.act(12, fog_obs(12, 12, units=()))
    assert a._sap_unknown == set()
    a._sap_unknown.add(9)
    a.act(101, fog_obs(101, 0))
    assert a._sap_unknown == set()
    a._sap_unknown.add(9)
    a.new_game()
    assert a._sap_unknown == set()


def test_mirrored_emission_retains_canonical_uid():
    a = fog_agent()
    a.new_game("player_1")
    for x, y in ((10, 11), (12, 13)):
        a.belief.point_tiles[x, y] = True
    unit = (*geo.mirror_xy(10, 11), 200)
    action = a.act(10, fog_obs(team=1, units=(unit,)))
    assert tuple(action[0]) == (geo.SAP, *geo.mirror_delta(2, 2))
    assert a._sap_unknown == {0} and a._sap_hits == {0: 0}


def test_update_false_preserves_historical_five_argument_auditor(monkeypatch):
    from agents.sherlock import main
    a = fog_agent(training=True)
    original = main.unit_rewards
    calls = []

    def historical(cfg, before, after, actions, hits):
        calls.append(dict(actions))
        return original(cfg, before, after, actions, hits)

    monkeypatch.setattr(main, "unit_rewards", historical)
    obs = fog_obs()
    action = a.act(10, obs)
    a.update(10, obs, 0., action, False, fog_obs(11, 11))
    assert calls == [{0: geo.SAP}]
    assert a.buffer.size == 1


@pytest.mark.parametrize("terminal", [False, True])
def test_flag_changes_only_selected_replay_reward(terminal):
    control, neutral = fog_agent(False, training=True), fog_agent(True, training=True)
    obs, nxt = fog_obs(), fog_obs(11, 0 if terminal else 11)
    results = []
    for a in (control, neutral):
        action = a.act(10, obs)
        a.update(10, obs, 0., action, terminal, nxt)
        results.append(action)
    np.testing.assert_array_equal(results[0], results[1])
    assert control._prev_actions == neutral._prev_actions
    assert control._sap_hits == neutral._sap_hits == {0: 0}
    assert control._sap_unknown == neutral._sap_unknown == {0}
    assert control.ep_stats == neutral.ep_stats
    for uid in control._prev_masks:
        np.testing.assert_array_equal(control._prev_masks[uid], neutral._prev_masks[uid])
    assert control.buffer.size == neutral.buffer.size == 1
    for key in ("s", "ns", "a", "mask", "done"):
        np.testing.assert_array_equal(getattr(control.buffer, key), getattr(neutral.buffer, key))
    assert float(neutral.buffer.r[0] - control.buffer.r[0]) == pytest.approx(0.3)
