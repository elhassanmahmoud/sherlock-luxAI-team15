"""Opt-in training exposure to the existing artillery splash rule; no games."""
from copy import deepcopy

import numpy as np
import pytest

from agents.sherlock import geometry as geo
from agents.sherlock.config import AgentConfig
from tests.conftest import make_obs
from tests.test_art_splash import NEAR
from tests.test_rules_1910 import _stay_agent
from tests.test_rules_2110 import PAIR


def _agent(enabled=False, training=True, team=0, dropoff=1.0, **overrides):
    cfg = dict(hidden=16, buffer_capacity=64, eps_start=0, eps_end=0,
               art_sap=True, art_min_hits=3, art_splash=True)
    cfg.update(overrides)
    agent = _stay_agent(**cfg)
    agent.rng = np.random.default_rng(7)
    agent.cfg.art_splash_in_training = enabled
    if training:
        agent.set_to_train_mode()
    if team:
        agent.new_game("player_1")
    if dropoff is not None:
        agent.param_est.log_drop = np.array([
            0.0 if value == dropoff else -50.0 for value in (0.25, 0.5, 1.0)
        ])
        agent.param_est.n_drop = 5
    return agent


def _obs(step=10, team=0, energy=100, enemies=NEAR):
    units, relics = [(5, 5, energy)], [(12, 12)]
    if team:
        units = [(*geo.mirror_xy(x, y), e) for x, y, e in units]
        enemies = [(*geo.mirror_xy(x, y), e) for x, y, e in enemies]
        relics = [geo.mirror_xy(x, y) for x, y in relics]
    return make_obs(step, step, team=team, units=units, enemies=enemies, relics=relics)


@pytest.mark.parametrize("stored_flag", [{}, {"art_splash_in_training": False}])
def test_legacy_or_explicit_false_config_keeps_training_artillery_off(stored_flag):
    cfg = AgentConfig.from_dict({"art_splash": True, **stored_flag})
    assert getattr(cfg, "art_splash_in_training", None) is False
    agent = _agent(enabled=cfg.art_splash_in_training)
    assert agent.act(10, _obs())[0].tolist() == [geo.STAY, 0, 0]
    assert agent._prev_actions == {0: geo.STAY}
    assert agent.param_est._prev is None


@pytest.mark.parametrize("enabled,want", [(False, geo.STAY), (True, geo.SAP)])
@pytest.mark.parametrize("team", [0, 1])
def test_training_opt_in_changes_final_native_action_and_stored_action(enabled, want, team):
    agent = _agent(enabled=enabled, team=team)
    result = agent.act(10, _obs(team=team))
    expected_delta = (-3, -3) if team else (3, 3)
    expected = [geo.SAP, *expected_delta] if want == geo.SAP else [geo.STAY, 0, 0]
    assert result[0].tolist() == expected
    assert agent._prev_actions == {0: want}
    assert agent._sap_hits == ({0: 2} if want == geo.SAP else {})


@pytest.mark.parametrize("dropoff,min_drop,want", [
    (None, 1.0, geo.STAY), (0.25, 1.0, geo.STAY),
    (0.5, 1.0, geo.STAY), (1.0, 1.0, geo.SAP),
    (None, 0.5, geo.STAY), (0.25, 0.5, geo.STAY),
    (0.5, 0.5, geo.SAP), (1.0, 0.5, geo.SAP),
])
def test_training_splash_keeps_confidence_and_dropoff_threshold(dropoff, min_drop, want):
    agent = _agent(enabled=True, dropoff=dropoff, splash_min_drop=min_drop)
    assert int(agent.act(10, _obs(enemies=PAIR))[0, 0]) == want


@pytest.mark.parametrize("enabled", [False, True])
def test_flag_has_no_training_effect_without_art_splash(enabled):
    agent = _agent(enabled=enabled, art_splash=False)
    assert agent.act(10, _obs())[0].tolist() == [geo.STAY, 0, 0]
    assert agent.param_est._prev is None


@pytest.mark.parametrize("dropoff,enemy_energy,want", [
    (0.5, 39, geo.SAP), (0.5, 40, geo.STAY), (1.0, 40, geo.SAP),
])
def test_training_keeps_safety_below_full_splash_and_armed_boundary(dropoff, enemy_energy, want):
    agent = _agent(enabled=True, dropoff=dropoff,
                   splash_min_drop=0.5, splash_safe_below=1.0)
    enemies = PAIR + [(7, 6, enemy_energy)]
    assert int(agent.act(10, _obs(enemies=enemies))[0, 0]) == want


@pytest.mark.parametrize("energy,want", [(69, geo.STAY), (70, geo.SAP)])
def test_training_splash_keeps_sap_cost_multiplier_and_artillery_reserve(energy, want):
    # 40 * (1 + 0.5) + 10 = 70: equality is allowed.
    agent = _agent(enabled=True, sap_reserve_k=0.5, art_reserve=10)
    assert int(agent.act(10, _obs(energy=energy))[0, 0]) == want


def test_training_splash_still_requires_two_hits():
    agent = _agent(enabled=True)
    assert int(agent.act(10, _obs(enemies=PAIR[:1]))[0, 0]) == geo.STAY


def test_training_splash_leaves_point_tile_holder_to_existing_rules():
    agent = _agent(enabled=True)
    agent.belief.point_tiles[5, 5] = True
    assert int(agent.act(10, _obs())[0, 0]) == geo.STAY


@pytest.mark.parametrize("team", [0, 1])
@pytest.mark.parametrize("enabled,art_splash,rules_all,want_samples", [
    (False, True, False, 0), (True, True, False, 1),
    (True, False, False, 0), (False, True, True, 1),
])
def test_estimator_observes_and_remembers_in_training_without_broad_rule_flag(
        team, enabled, art_splash, rules_all, want_samples):
    agent = _agent(enabled=enabled, team=team, dropoff=None,
                   art_splash=art_splash, rules_in_training_all=rules_all)
    first = agent.act(10, _obs(team=team))
    assert first[0].tolist() == [geo.STAY, 0, 0]
    final = agent.act(11, _obs(step=11, team=team, energy=90))
    # Ten energy lost near an armed enemy is one real estimator observation.
    assert agent.param_est.n_drop == want_samples
    if want_samples:
        np.testing.assert_array_equal(agent.param_est._prev["act"], final)
        assert agent.param_est._prev["ene"][0] == 90
        assert agent.param_est._prev["pos"][0] == ((18, 18) if team else (5, 5))
        assert not np.array_equal(agent.param_est.log_drop, np.zeros(3))
    else:
        assert agent.param_est._prev is None


@pytest.mark.parametrize("team", [0, 1])
@pytest.mark.parametrize("dropoff,want", [
    (None, geo.STAY), (0.25, geo.STAY), (0.5, geo.STAY), (1.0, geo.SAP),
])
def test_inference_is_identical_for_both_training_flag_values(team, dropoff, want):
    baseline = _agent(enabled=False, training=False, team=team, dropoff=dropoff)
    aligned = _agent(enabled=True, training=False, team=team, dropoff=dropoff)
    rng_before = deepcopy(baseline.rng.bit_generator.state)
    obs = _obs(team=team)
    baseline_action, aligned_action = baseline.act(10, obs), aligned.act(10, obs)
    assert int(baseline_action[0, 0]) == want
    np.testing.assert_array_equal(aligned_action, baseline_action)
    assert aligned._prev_actions == baseline._prev_actions == {0: want}
    np.testing.assert_array_equal(aligned._prev_feats[0], baseline._prev_feats[0])
    np.testing.assert_array_equal(aligned._prev_masks[0], baseline._prev_masks[0])
    np.testing.assert_array_equal(aligned.param_est._prev["act"], baseline_action)
    np.testing.assert_array_equal(aligned.param_est.log_drop, baseline.param_est.log_drop)
    assert aligned.rng.bit_generator.state == baseline.rng.bit_generator.state == rng_before
    assert aligned.ep_stats == baseline.ep_stats


def test_enabled_training_flag_survives_config_roundtrip():
    cfg = AgentConfig.from_dict({"art_splash": True, "art_splash_in_training": True})
    restored = AgentConfig.from_dict(cfg.to_dict())
    assert getattr(restored, "art_splash_in_training", None) is True
    agent = _agent(enabled=restored.art_splash_in_training)
    assert agent.act(10, _obs())[0].tolist() == [geo.SAP, 3, 3]
