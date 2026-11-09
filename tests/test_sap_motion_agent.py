"""Public synthetic frames only: no QNet, weight load, forward, or game."""
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from tests.test_sap_leading_agent import forbid_real_models, frame
from agents.sherlock.main import Agent_x
from sap_motion_agent import SapMotionAgent


def agent(*, enabled=True, mirrored=False):
    result = SapMotionAgent("player_1" if mirrored else "player_0", lead_enabled=enabled)
    result.param_est.log_drop = np.array([0., -50., -50.])
    result.param_est.n_drop = 1
    return result


def observe(a, step, position, **kwargs):
    obs = frame(step, enemy=position, **kwargs)
    obs["actions"][:] = 0  # Learning must not depend on a SAP being attempted.
    a._act(step, obs)
    return obs


def ready(a, counts=(32, 0, 0, 0, 0)):
    observe(a, 9, (2, 2), mirrored=a.belief.mirrored)
    a.motion_counts[:] = counts


def test_disabled_matches_core_actions_and_productive_state():
    a = SapMotionAgent("player_0")
    baseline = Agent_x("player_0", train=False)
    for obs in (frame(8, enemy=(1, 2)), frame(9, enemy=(2, 2)), frame()):
        np.testing.assert_array_equal(a._act(obs["steps"], deepcopy(obs)),
                                      baseline._act(obs["steps"], deepcopy(obs)))
    for name in ("_sap_hits", "_sap_unknown", "_prev_actions", "_pred_pending", "_shape_pending", "ep_stats"):
        assert getattr(a, name) == getattr(baseline, name)
    assert a.core_calls == 3 and not a.leading_stats
    assert a.motion_counts.sum() == 0 and a.leading_last is None
    assert not a.autosave_on_terminate and not a.learn_enabled
    with pytest.raises(ValueError, match="eval"):
        SapMotionAgent("player_0", train=True)
    with pytest.raises(RuntimeError):
        a.update(None)


@pytest.mark.parametrize("kind", range(5))
def test_labels_are_relative_for_all_four_previous_directions(kind):
    # Literal vectors independently specify forward/right/back/left/stay.
    directions = [((1, 0), [(1, 0), (0, 1), (-1, 0), (0, -1), (0, 0)]),
                  ((0, 1), [(0, 1), (-1, 0), (0, -1), (1, 0), (0, 0)]),
                  ((-1, 0), [(-1, 0), (0, -1), (1, 0), (0, 1), (0, 0)]),
                  ((0, -1), [(0, -1), (1, 0), (0, 1), (-1, 0), (0, 0)])]
    for (dx, dy), next_vectors in directions:
        a = agent()
        observe(a, 1, (2-dx, 2-dy))
        observe(a, 2, (2, 2), energy=3)
        nx, ny = next_vectors[kind]
        observe(a, 3, (2+nx, 2+ny), energy=0)
        expected = np.zeros(5, dtype=int); expected[kind] = 1
        np.testing.assert_array_equal(a.motion_counts, expected)
        assert a.leading_stats["motion_labels"] == 1


@pytest.mark.parametrize("case", ["gap", "hidden", "jump", "diagonal", "match", "mirror",
                                  "low_energy", "negative_energy", "nan_energy"])
def test_ineligible_public_triplets_never_become_training_labels(case):
    a = agent()
    observe(a, 1, (1, 2))
    middle = frame(2, enemy=(2, 2))
    current = frame(3, enemy=(3, 2))
    middle["actions"][:] = current["actions"][:] = 0
    if case == "gap":
        current["steps"] = current["ctx"]["step"] = 4
        current["match_steps"] = current["ctx"]["match_step"] = 4
    if case == "hidden": middle["ctx"]["enemy_vis_ids"][0] = 6
    if case == "jump": middle["ctx"]["enemy_coords"][0] = (4, 2)
    if case == "diagonal": current["ctx"]["enemy_coords"][0] = (3, 3)
    if case == "match": current["ctx"]["match_idx"] = 1
    if case == "low_energy": middle["ctx"]["enemy_energies"][0] = 2
    if case == "negative_energy": current["ctx"]["enemy_energies"][0] = -1
    if case == "nan_energy": current["ctx"]["enemy_energies"][0] = np.nan
    a._act(2, middle)
    if case == "mirror": a.belief.mirrored = True
    a._act(current["steps"], current)
    assert a.motion_counts.sum() == 0


def test_visible_units_pool_labels_and_copied_history_has_no_future_positions():
    a = agent()
    for step in (1, 2, 3):
        obs = frame(step, enemy=(step, 2))
        obs["ctx"]["enemy_coords"][1] = (step, 4)
        obs["actions"][:] = 0
        a._act(step, obs)
        if step < 3:
            assert a.motion_counts.sum() == 0
        obs["ctx"]["enemy_coords"][:] = (5, 5)
        obs["ctx"]["enemy_energies"][:] = -1
    np.testing.assert_array_equal(a.motion_counts, [2, 0, 0, 0, 0])


def test_match_reset_preserves_counts_but_new_game_clears_them():
    a = agent()
    for step in (1, 2, 3): observe(a, step, (step, 2))
    a._act(4, frame(4, ms=0))
    observe(a, 5, (1, 2), ms=1, match=1)
    observe(a, 6, (2, 2), ms=2, match=1)
    np.testing.assert_array_equal(a.motion_counts, [1, 0, 0, 0, 0])
    observe(a, 7, (3, 2), ms=3, match=1)
    np.testing.assert_array_equal(a.motion_counts, [2, 0, 0, 0, 0])
    a.belief = a.feat_belief = SimpleNamespace(reset_game=Mock(), set_team=Mock())
    a.new_game()
    assert a.motion_counts.sum() == 0 and not a.leading_stats
    assert a._motion_history == [] and a.leading_last is None


@pytest.mark.parametrize("prior_count,changes", [(30, 0), (31, 1)])
def test_threshold_counts_only_completed_transitions_before_current_action(prior_count, changes):
    a = agent()
    observe(a, 8, (1, 2))
    observe(a, 9, (2, 2))
    a.motion_counts[0] = prior_count
    obs = frame()
    result = a._act(10, obs)
    assert a.motion_counts.sum() == prior_count+1
    assert a.leading_stats["changes"] == changes
    assert result[1, 1] == (3 if changes else 2)
    if changes:
        assert a.leading_last["sample_count"] == 32
        assert a.leading_last["counts"] == (32, 0, 0, 0, 0)
        np.testing.assert_allclose(a.leading_last["probabilities"], [33/37, 1/37, 1/37, 1/37, 1/37])


@pytest.mark.parametrize("mirrored,want", [(False, [5, 3, 0]), (True, [5, 0, -3])])
def test_positive_model_changes_only_smallest_uid_with_exact_score(mirrored, want):
    a = agent(mirrored=mirrored); ready(a)
    obs = frame(mirrored=mirrored)
    result = a._act(10, obs)
    assert result[1].tolist() == want
    np.testing.assert_array_equal(result[[0, 2, 3]], obs["actions"][[0, 2, 3]])
    assert a.core_calls == 2 and a.leading_stats["changes"] == 1
    details = a.leading_last
    assert details["focus_gains"] == (.75, 0., -.25, 0., -.75)
    assert details["other_gain"] == -.25
    assert details["mean"] == pytest.approx(14.5/37)
    assert details["variance"] == pytest.approx(((19.1875/37)-(23.75/37)**2)/38)
    assert details["lower_bound"] > 0
    assert a.leading_stats["eligible_saps"] == 2
    assert a.leading_stats["capped_eligible_saps"] == 1


def test_positive_mean_without_uncertainty_margin_is_rejected():
    a = agent(); ready(a, counts=(18, 0, 0, 0, 14))
    obs = frame(); obs["ctx"]["enemy_coords"][1] = (0, 0)
    # Focus mean is +2.75/37, but its two-standard-deviation lower bound is negative.
    np.testing.assert_array_equal(a._act(10, obs), obs["actions"])
    assert a.leading_stats["excluded_gain"] == 2 and a.leading_last is None


def test_lost_other_hits_block_lead_and_negative_energy_is_not_counted():
    a = agent(); ready(a)
    obs = frame()
    obs["ctx"]["enemy_vis_ids"] = np.array([7, 8, 9, 10])
    obs["ctx"]["enemy_coords"] = np.array([(3, 2), (2, 1), (2, 2), (2, 3)])
    obs["ctx"]["enemy_energies"] = np.full(4, 20.)
    np.testing.assert_array_equal(a._act(10, obs), obs["actions"])
    assert a.leading_stats["excluded_gain"] == 2
    a = agent(); ready(a)
    obs["ctx"]["enemy_energies"][1:] = [-1., np.nan, -1.]
    assert a._act(10, obs)[1].tolist() == [5, 3, 0]
    assert a.leading_last["other_gain"] == 0


def test_rejected_lower_uid_does_not_hide_a_profitable_higher_uid():
    a = agent()
    previous = frame(9, enemy=(2, 2))
    current = frame()
    for obs in (previous, current):
        obs["ctx"]["enemy_vis_ids"] = np.array([7, 8, 9, 10, 11])
        obs["ctx"]["enemy_energies"] = np.full(5, 20.)
    previous["ctx"]["enemy_coords"] = np.array([(2, 2), (2, 1), (2, 2), (2, 3), (3, 4)])
    current["ctx"]["enemy_coords"] = np.array([(3, 2), (2, 1), (2, 2), (2, 3), (4, 4)])
    previous["actions"][:] = 0
    current["actions"][3] = [5, 3, 2]
    a._act(9, previous); a.motion_counts[0] = 32
    result = a._act(10, current)
    assert result[1].tolist() == [5, 2, 0]
    assert result[3].tolist() == [5, 4, 2]
    assert a.leading_last["uid"] == 3
    assert a.leading_stats["excluded_gain"] == a.leading_stats["eligible_saps"] == 1


def test_next_positions_use_only_visible_obstacles_and_known_edges():
    a = agent(); ready(a)
    obs = frame()
    # Side step (3,3) is currently blocked; (3,1) is unknown and must not
    # be called blocked merely because remembered passability says false.
    obs["ctx"]["passable"][3, 3] = False
    obs["ctx"]["passable"][3, 1] = False
    obs["sensor_mask"][3, 1] = False
    a._act(10, obs)
    details = a.leading_last
    assert details["next_positions"] == ((4, 2), (3, 2), (2, 2), (3, 1), (3, 2))
    assert details["blocked_classes"] == (1,)
    assert details["unknown_classes"] == (3,)
    a = agent()
    observe(a, 9, (2, 0)); a.motion_counts[0] = 32
    edge = frame(enemy=(3, 0)); edge["actions"][[1, 3], 1:] = (2, -2)
    a._act(10, edge)
    assert a.leading_last["next_positions"][3] == (3, 0)
    assert a.leading_last["blocked_classes"] == (3,)


def test_original_estimator_remembers_changed_native_command_once_and_keeps_bookkeeping():
    a = agent(mirrored=True); ready(a)
    events = []
    original_remember = a.param_est.remember
    def observe_dropoff(*args):
        events.append("observe")
        a.param_est.log_drop[:] = [0, -50, -50]
    def remember(obs, team, actions):
        events.append("remember")
        original_remember(obs, team, actions)
    a.param_est.observe = observe_dropoff
    a.param_est.remember = remember
    before = dict(a.ep_stats)
    obs = frame(mirrored=True); obs["old_hits"] = 0
    result = a._act_est(10, obs)
    assert result[1].tolist() == [5, 0, -3]
    np.testing.assert_array_equal(a.param_est._prev["act"], result)
    assert events == ["observe", "remember"] and a.core_calls == 2
    assert a._sap_hits == {1: 1, 3: 2} and a._sap_unknown == {3}
    assert a.ep_stats["sap_attempts"]-before["sap_attempts"] == 2
    assert a.ep_stats["sap_hits_est"]-before["sap_hits_est"] == 2
    assert a._prev_actions == {1: 5, 3: 5, 0: 2}
    assert a._pred_pending == [(1, 1, 2, 40., True)]
    assert a._shape_pending == [(1, 1, 2, 40., True, "man")]
    np.testing.assert_array_equal(a._prev_feats[1], [2., 3.])
    assert a._prev_masks[1].all()
