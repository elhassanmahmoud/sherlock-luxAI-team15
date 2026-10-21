"""Bounded joint movement: distinct occupancy, conservative alternatives, API wiring."""
from copy import deepcopy

import numpy as np
import pytest
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x
from tests.conftest import ENV_CFG, make_obs


def fixture(positions=((5, 5), (7, 5)), points=((5, 5), (6, 5), (7, 5))):
    n = len(positions)
    ctx = dict(W=24, H=24, ally_ids=np.arange(n),
               ally_pos=np.asarray(positions, dtype=float), ally_ene=np.full(n, 100.0),
               point_tiles=np.zeros((24, 24), dtype=bool),
               passable=np.ones((24, 24), dtype=bool), move_cost=3.0,
               enemy_coords=np.empty((0, 2)), enemy_energies=np.empty(0))
    for tile in points:
        ctx['point_tiles'][tile] = True
    q = np.zeros((n, 6))
    masks = np.ones((n, 6), dtype=bool)
    q[0, [geo.RIGHT, geo.STAY]] = [10, 9.9]
    q[1, [geo.LEFT, geo.STAY]] = [10, 9.9]
    return ctx, list(range(n)), q, masks, {0: geo.RIGHT, 1: geo.LEFT}


def coordinate(*args):
    from agents.sherlock.joint_actions import coordinate_moves
    return coordinate_moves(*args)


def test_competing_units_gain_one_distinct_tile_with_stable_action_tie():
    # Without joint decoding both finish on (6,5); the smaller action tuple wins.
    assert coordinate(*fixture()) == {0: geo.STAY}


def test_outsider_occupancy_is_counted_globally():
    args = fixture(positions=((5, 5), (7, 5), (5, 5), (7, 5)))
    args[4].update({2: geo.SAP, 3: geo.SAP})
    assert coordinate(*args) == {}


def test_no_strict_gain_does_not_just_reduce_stacking():
    assert coordinate(*fixture(points=((6, 5),))) == {}


@pytest.mark.parametrize('enemy', [(5, 4), (5, 6), (4, 5)])
def test_useful_combat_stack_preserved_when_current_or_destination_near_enemy(enemy):
    args = fixture(points=((5, 5), (6, 5)))
    args[0]['enemy_coords'] = np.array([enemy])
    args[0]['enemy_energies'] = np.array([0.0])
    assert coordinate(*args) == {}


@pytest.mark.parametrize('bad', ['sap', 'negative_energy', 'nan_energy', 'nan_q',
                                 'inf_q', 'masked_base', 'bad_position'])
def test_unusable_baseline_unit_is_fixed(bad):
    ctx, ids, q, masks, base = fixture(points=((5, 5), (6, 5)))
    if bad == 'sap':
        base[0] = geo.SAP
    elif bad == 'negative_energy':
        ctx['ally_ene'][0] = -1
    elif bad == 'nan_energy':
        ctx['ally_ene'][0] = np.nan
    elif bad == 'nan_q':
        q[0, geo.RIGHT] = np.nan
    elif bad == 'inf_q':
        q[0, geo.RIGHT] = np.inf
    elif bad == 'masked_base':
        masks[0, geo.RIGHT] = False
    else:
        ctx['ally_pos'][0] = [np.nan, 5]
    assert coordinate(ctx, ids, q, masks, base) == {}


@pytest.mark.parametrize('bad', ['masked', 'nonfinite', 'regret', 'energy'])
def test_candidate_requires_legal_finite_q_and_bounded_regret_and_energy(bad):
    ctx, ids, q, masks, base = fixture(points=((5, 5), (6, 5)))
    if bad == 'masked':
        masks[0, geo.STAY] = False
    elif bad == 'nonfinite':
        q[0, geo.STAY] = np.nan
    elif bad == 'regret':
        q[0, geo.STAY] = 8.49  # >15% of span 10 below baseline
    else:
        ctx['ally_ene'][0] = 2  # baseline movement cannot yield occupancy
    assert coordinate(ctx, ids, q, masks, base) == {}


def test_regret_span_includes_finite_legal_sap_and_is_scale_invariant():
    args = fixture(points=((5, 5), (6, 5)))
    args[2][0, geo.STAY] = 8
    args[2][0, geo.SAP] = 20
    assert coordinate(*args) == {0: geo.STAY}
    args[2][:] = args[2] * 1000 + 230
    assert coordinate(*args) == {0: geo.STAY}


def test_rule_overridden_baseline_is_kept_even_outside_top_two():
    args = fixture(points=((5, 5), (6, 5)))
    args[2][1, geo.STAY] = 20
    args[2][1, geo.DOWN] = 19
    assert coordinate(*args) == {0: geo.STAY}


def test_inputs_are_not_mutated_and_uid_row_order_is_respected():
    args = fixture()
    before = deepcopy(args)
    assert coordinate(*args) == {0: geo.STAY}
    for old, new in zip(before, args):
        if isinstance(old, np.ndarray):
            np.testing.assert_array_equal(old, new)
        elif isinstance(old, dict):
            for key in old:
                np.testing.assert_equal(old[key], new[key])
        else:
            assert old == new
    ctx, ids, q, masks, base = args
    assert coordinate(ctx, ids[::-1], q[::-1], masks[::-1], base) == {0: geo.STAY}


def test_empty_ids_or_no_known_points_returns_no_changes():
    assert coordinate(*fixture(points=())) == {}
    args = fixture()
    assert coordinate(args[0], [], args[2][:0], args[3][:0], {}) == {}


class PairQ(torch.nn.Module):
    def forward(self, features):
        q = torch.zeros((len(features), 6))
        q[:2, geo.STAY] = 9.9
        q[0, geo.RIGHT] = q[1, geo.LEFT] = 10
        if len(features) > 2:
            q[2, geo.SAP] = 10
        return q


def acting_agent(team=0, joint=True, training=False):
    cfg = AgentConfig(buffer_capacity=16, hidden=8, eps_start=0, eps_end=0)
    cfg.joint_moves = joint
    agent = Agent_x(f'player_{team}', cfg=cfg, train=training, seed=1)
    agent.set_env_cfg(ENV_CFG)
    agent.q = PairQ()
    # Belief.observe only infers point tiles in a relic zone, so these known
    # point fixtures persist without manufacturing a relic observation.
    for tile in [(5, 5), (6, 5), (7, 5)]:
        agent.belief.point_tiles[tile] = True
    units = [(5, 5, 100), (7, 5, 100)]
    if team:
        units = [(*geo.mirror_xy(x, y), e) for x, y, e in units]
    return agent, make_obs(10, 10, team=team, units=units)


@pytest.mark.parametrize('team,expected', [(0, [[0, 0, 0], [4, 0, 0]]),
                                           (1, [[0, 0, 0], [3, 0, 0]])])
def test_act_applies_joint_choices_in_world_space_and_remembers_canonical(team, expected):
    agent, obs = acting_agent(team)
    np.testing.assert_array_equal(agent.act(10, obs)[:2], expected)
    assert agent._prev_actions == {0: geo.STAY, 1: geo.LEFT}


@pytest.mark.parametrize('training', [False, True])
def test_disabled_or_training_retains_baseline_actions(training):
    a, obs = acting_agent(joint=False, training=training)
    b, _ = acting_agent(joint=True, training=True)
    np.testing.assert_array_equal(a.act(10, obs)[:2], [[2, 0, 0], [4, 0, 0]])
    np.testing.assert_array_equal(b.act(10, obs)[:2], [[2, 0, 0], [4, 0, 0]])
    assert a._prev_actions == b._prev_actions == {0: geo.RIGHT, 1: geo.LEFT}


def test_accepted_pair_reserves_both_units_even_for_later_potential_gain():
    ctx, ids, q, masks, base = fixture(positions=((5, 5), (7, 5), (5, 6)),
                                     points=((5, 5), (6, 5), (6, 6)))
    q[2, [geo.UP, geo.RIGHT, geo.STAY]] = [10, 9.9, 9.8]
    base[2] = geo.STAY
    assert coordinate(ctx, ids, q, masks, base) == {0: geo.STAY}


def test_rejected_pair_does_not_reserve_units_needed_for_later_handoff():
    ctx, ids, q, masks, base = fixture(positions=((5, 5), (7, 5), (4, 5)),
                                     points=((4, 5), (5, 5), (6, 5)))
    q[2, [geo.RIGHT, geo.STAY]] = [10, 9.9]
    base[2] = geo.RIGHT
    assert coordinate(ctx, ids, q, masks, base) == {0: geo.STAY, 2: geo.STAY}


def test_nonbaseline_destination_must_also_be_away_from_enemy():
    ctx, ids, q, masks, base = fixture(points=((5, 6), (6, 5)))
    q[0, geo.DOWN] = 9.95
    ctx['enemy_coords'] = np.array([[5, 7]])  # current (5,5) is clear
    ctx['enemy_energies'] = np.array([100])
    assert coordinate(ctx, ids, q, masks, base) == {}


def test_negative_energy_enemy_does_not_block_an_alternative():
    args = fixture(points=((5, 5), (6, 5)))
    args[0]['enemy_coords'] = np.array([[5, 4]])
    args[0]['enemy_energies'] = np.array([-1])
    assert coordinate(*args) == {0: geo.STAY}


@pytest.mark.parametrize('bad', [np.nan, np.inf])
def test_nonfinite_visible_enemy_does_not_create_an_alternative(bad):
    args = fixture(points=((5, 5), (6, 5)))
    args[0]['enemy_coords'] = np.array([[5, 4]])
    args[0]['enemy_energies'] = np.array([bad])
    assert coordinate(*args) == {}


def test_movement_from_fixed_outsider_counts_only_when_energy_pays_cost():
    args = fixture(positions=((5, 5), (7, 5), (5, 6)), points=((5, 5), (6, 5)))
    args[4][2] = geo.UP
    args[2][2] = np.nan  # fixed, but nominal final position still counts
    assert coordinate(*args) == {}
    args[0]['ally_ene'][2] = 2
    assert coordinate(*args) == {0: geo.STAY}


def test_pair_more_than_two_tiles_apart_is_not_coordinated():
    args = fixture(positions=((5, 5), (7, 6)), points=((5, 5), (6, 5), (6, 6)))
    args[2][1, geo.UP] = 10.1
    assert coordinate(*args) == {}


@pytest.mark.parametrize('team', [0, 1])
def test_final_sap_row_is_preserved_while_other_pair_changes(team):
    agent, obs = acting_agent(team)
    # Add a real Sap unit and visible enemy, away from the pair's guard zone.
    pos = (12, 12) if not team else geo.mirror_xy(12, 12)
    enemy = (13, 12) if not team else geo.mirror_xy(13, 12)
    obs['units']['position'][team, 2] = pos
    obs['units']['energy'][team, 2] = 100
    obs['units_mask'][team, 2] = True
    obs['units']['position'][1 - team, 0] = enemy
    obs['units']['energy'][1 - team, 0] = 100
    obs['units_mask'][1 - team, 0] = True
    actions = agent.act(10, obs)
    expected_sap = [geo.SAP, 1, 0] if not team else [geo.SAP, 0, -1]
    np.testing.assert_array_equal(actions[2], expected_sap)
    assert actions[0, 0] == geo.STAY
    assert agent._prev_actions[2] == geo.SAP
    assert agent.ep_stats['joint_calls'] == 1
    assert agent.ep_stats['joint_changed_units'] == 1


def test_existing_rule_override_is_final_baseline_for_joint_decoding():
    agent, obs = acting_agent()
    agent.cfg.pt_hold = True
    # Unit 0's pt_hold override prevents its baseline move. Joint decoding sees
    # the resulting distinct (5,5),(6,5), so it must not undo the rule for Q gain.
    np.testing.assert_array_equal(agent.act(10, obs)[:2], [[0, 0, 0], [0, 0, 0]])
    assert agent._prev_actions == {0: geo.STAY, 1: geo.STAY}


def test_minimum_normalized_regret_precedes_action_id_tie():
    args = fixture()
    args[2][0, geo.STAY] = 9
    args[2][1, geo.STAY] = 9.9
    assert coordinate(*args) == {1: geo.STAY}


@pytest.mark.parametrize('bad_position', [[np.nan, 4], [5, np.inf], [-1, 4]])
def test_invalid_visible_enemy_position_falls_back_without_mutation(bad_position):
    args = fixture(points=((5, 5), (6, 5)))
    args[0]['enemy_coords'] = np.array([bad_position])
    args[0]['enemy_energies'] = np.array([100.0])
    before = args[0]['enemy_coords'].copy()
    assert coordinate(*args) == {}
    np.testing.assert_array_equal(args[0]['enemy_coords'], before)


def test_only_two_highest_legal_movement_options_are_considered():
    args = fixture(points=((5, 5), (6, 5)))
    args[2][0, geo.UP] = 10.1  # STAY is third: not in candidate set
    assert coordinate(*args) == {}
    args[3][0, geo.UP] = False
    assert coordinate(*args) == {0: geo.STAY}


def test_top_option_ties_use_action_id_and_fewer_changes_breaks_equal_regret():
    args = fixture()
    args[2][0, geo.STAY] = args[2][1, geo.STAY] = 10
    # Every spreading choice has zero regret; one change beats two, then (0,4).
    assert coordinate(*args) == {0: geo.STAY}
    args[2][0, geo.UP] = 10
    assert coordinate(*args) == {0: geo.STAY}


def test_illegal_sap_does_not_widen_the_q_regret_allowance():
    args = fixture(points=((5, 5), (6, 5)))
    args[2][0, geo.STAY] = 8
    args[2][0, geo.SAP] = 20
    args[3][0, geo.SAP] = False
    assert coordinate(*args) == {}


@pytest.mark.parametrize('cost', [np.nan, np.inf, -1])
def test_invalid_move_cost_cannot_create_actions(cost):
    args = fixture()
    args[0]['move_cost'] = cost
    assert coordinate(*args) == {}


def test_later_disjoint_pair_counts_earlier_accepted_destinations():
    args = fixture(positions=((5, 5), (7, 5), (5, 6), (7, 6)),
                   points=((5, 5), (6, 5), (6, 6)))
    args[2][2, [geo.RIGHT, geo.UP]] = [10, 9.9]
    args[2][3, [geo.LEFT, geo.STAY]] = [10, 9.9]
    args[4].update({2: geo.RIGHT, 3: geo.LEFT})
    # Pair (0,1) fills (5,5). Pair (2,3) must not mistake that tile for empty.
    assert coordinate(*args) == {0: geo.STAY}


def test_q_regret_is_normalized_per_unit_before_summing():
    args = fixture()
    args[2][0, [geo.RIGHT, geo.STAY]] = [100, 98]
    args[2][1, geo.STAY] = 9.7
    # Unit 0 gives up 2/100; unit 1 gives up .3/10. Absolute regret is wrong.
    assert coordinate(*args) == {0: geo.STAY}
