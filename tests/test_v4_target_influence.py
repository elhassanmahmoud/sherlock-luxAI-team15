"""Stage-one target influence: legal selection and actual isolated V3 actions."""
import copy
import random
from pathlib import Path

import numpy as np
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.features import FEATURE_DIM, FEATURE_NAMES
from agents.sherlock.main import Agent_x
from tests.conftest import ENV_CFG, make_obs


def probe():
    from experiments.analysis.v4_target_pilot_20261021 import influence
    return influence


def selection_ctx():
    points = np.zeros((24, 24), bool)
    for tile in [(8, 5), (9, 5), (5, 4), (6, 5), (5, 6), (4, 5), (5, 3), (12, 5)]:
        points[tile] = True
    return dict(W=24, H=24, ally_ids=np.arange(2),
                ally_pos=np.array([(5, 5), (6, 6)]), ally_ene=np.array([3., 50.]),
                assigned={0: (8, 5), 1: (9, 5)}, point_tiles=points,
                passable=np.ones((24, 24), bool), move_cost=3.)


def test_selection_orders_candidates_by_bfs_then_coordinates_and_selects_farthest_uid():
    # Taking nearest unit, Manhattan routes, or >3 candidates breaks this contract.
    choices, selected = probe().select_choices(selection_ctx())
    assert selected['uid'] == 1  # baseline distances 3 and 4
    assert choices[0]['alternatives'] == [
        {'target': [4, 5], 'distance': 1},
        {'target': [5, 4], 'distance': 1},
        {'target': [5, 6], 'distance': 1},
    ]
    assert selected['alternatives'][0] == {'target': [5, 6], 'distance': 1}


def test_selection_excludes_blocked_occupied_assigned_and_unreachable_targets():
    ctx = selection_ctx()
    ctx['passable'][4, 5] = False  # distance_map(goal) alone would accept this
    ctx['ally_pos'][1] = (5, 4)
    ctx['assigned'][1] = (5, 6)
    ctx['ally_ene'][1] = 0  # still occupies its tile, cannot be selected
    ctx['passable'][5, 2:4] = False
    ctx['passable'][4, 3] = ctx['passable'][6, 3] = False
    choices, selected = probe().select_choices(ctx)
    assert selected['uid'] == 0
    assert choices[0]['alternatives'] == [{'target': [6, 5], 'distance': 1},
                                          {'target': [9, 5], 'distance': 4}]
    assert (12, 5) not in [tuple(x['target']) for x in choices[0]['alternatives']]


@pytest.mark.parametrize('change', ['energy', 'position', 'on_point', 'baseline_not_point'])
def test_unusable_unit_is_never_selected(change):
    ctx = selection_ctx()
    ctx['ally_ids'] = np.array([0])
    if change == 'energy':
        ctx['ally_ene'][0] = 2
    elif change == 'position':
        ctx['ally_pos'][0] = (-1, 5)
    elif change == 'on_point':
        ctx['point_tiles'][5, 5] = True
    else:
        ctx['point_tiles'][8, 5] = False
    assert probe().select_choices(ctx) == ([], None)


def test_bfs_uses_known_raster_and_fixed_up_right_down_left_ties():
    grid = np.ones((8, 8), bool)
    assert probe().bounded_paths(grid, (3, 3))[(4, 2)] == [(3, 2), (4, 2)]
    grid[4, 3] = False
    paths = probe().bounded_paths(grid, (3, 3))
    assert (4, 3) not in paths
    assert paths[(5, 3)] == [(3, 2), (4, 2), (5, 2), (5, 3)]
    assert (7, 7) not in paths  # >6 steps


class AssignedDxPolicy(torch.nn.Module):
    """Deterministic small policy: RIGHT for right target, LEFT for left target."""
    def __init__(self, fail_left=False, constant_right=False):
        super().__init__()
        self.fail_left = fail_left
        self.constant_right = constant_right

    def forward(self, feats):
        random.random()
        np.random.random()
        torch.rand(1)
        dx = feats[:, FEATURE_NAMES.index('assigned_dx')]
        if self.fail_left and bool(dx[0] < 0):
            raise RuntimeError('deliberate shadow failure')
        out = torch.full((len(feats), 6), -10.)
        out[:, 2] = 1. if self.constant_right else dx
        out[:, 4] = 0. if self.constant_right else -dx
        return out


def agent_obs(side, **policy_kwargs):
    team = int(side[-1])
    agent = Agent_x(side, cfg=AgentConfig(hidden=8, buffer_capacity=4, canonical=True),
                    train=False, seed=17)
    agent.set_env_cfg(ENV_CFG)
    agent.q = AssignedDxPolicy(**policy_kwargs).eval()
    agent.target_q.eval()
    agent.extra_q = []
    # Keep known points without inferring extra ones from a fabricated score gain.
    agent.belief.point_tiles[6, 5] = agent.belief.point_tiles[3, 5] = True
    agent.belief.point_tiles[0, 1] = True
    agent.belief._cache.clear()
    pos = (5, 5) if team == 0 else (18, 18)
    other = (1, 1) if team == 0 else (22, 22)
    obs = make_obs(126, 25, team=team, units=[(*pos, 100), (*other, 100)])
    return agent, obs


def test_clone_preserves_internal_aliases_and_isolates_every_dynamic_object():
    agent, obs = agent_obs('player_0')
    agent.act(126, obs)
    clone = probe().clone_agent(agent)
    for attr in ['q', 'target_q', 'opt', 'buffer']:
        assert getattr(clone, attr) is getattr(agent, attr)
    assert clone.extra_q[0:] == agent.extra_q[0:]
    assert clone.belief is clone.feat_belief
    assert clone._cache[1]['belief'] is clone.belief
    assert clone._prev_ctx is clone._cache[1]
    clone.belief.point_tiles[6, 5] = False
    clone._cache[3][0][0] = 91
    clone._paths.maps[(6, 5)] = np.zeros((24, 24))
    clone.rng.random()
    assert agent.belief.point_tiles[6, 5]
    assert agent._cache[3][0][0] != 91
    assert (6, 5) not in agent._paths.maps
    assert clone.rng.bit_generator.state != agent.rng.bit_generator.state


@pytest.mark.parametrize('side', ['player_0', 'player_1'])
def test_passive_probe_changes_real_final_actions_without_changing_live_state_or_rng(side):
    api = probe()
    live, obs = agent_obs(side)
    control = copy.deepcopy(live)
    globals_before = api.capture_rng()
    expected = control.act(126, copy.deepcopy(obs))
    expected_rng = api.capture_rng()
    api.restore_rng(globals_before)
    wrapped = api.InfluenceAgent(live)
    actual = wrapped.act(126, obs)
    assert np.array_equal(actual, expected)
    assert api.dynamic_digest(live) == api.dynamic_digest(control)
    assert api.rng_digest() == api.rng_digest(expected_rng)
    record = wrapped.records[0]
    assert record['selected_unit'] == 0
    assert record['baseline_target'] == [6, 5]
    assert record['alternatives'][0]['target'] == [3, 5]
    expected_direction = 4 if side == 'player_0' else 3
    assert record['alternatives'][0]['actions'][0] == [expected_direction, 0, 0]
    assert record['alternatives'][0]['changed_units'] == [0]
    assert record['distinct_changed_arrays'] == 1


def test_real_rule_override_can_change_action_even_with_constant_network_output():
    agent, obs = agent_obs('player_0', constant_right=True)
    agent.cfg.pt_walk = True
    wrapped = probe().InfluenceAgent(agent)
    assert wrapped.act(126, obs)[0, 0] == 2
    assert wrapped.records[0]['alternatives'][0]['actions'][0] == [4, 0, 0]


def test_failed_shadow_restores_global_rng_and_keeps_live_and_observation_unchanged():
    api = probe()
    agent, obs = agent_obs('player_0', fail_left=True)
    pre = api.clone_agent(agent)
    baseline_rng = api.capture_rng()
    agent.act(126, obs)
    state, obs_state, rng_state = api.dynamic_digest(agent), api.value_digest(obs), api.rng_digest()
    with pytest.raises(RuntimeError, match='deliberate shadow failure'):
        api.shadow_action(pre, obs, 126, 0, (3, 5), baseline_rng, live=agent)
    assert api.dynamic_digest(agent) == state
    assert api.value_digest(obs) == obs_state
    assert api.rng_digest() == rng_state


def test_shadow_rejects_training_joint_cnn_or_nonempty_buffer():
    api = probe()
    for bad in ['training', 'joint', 'cnn', 'buffer']:
        agent, _ = agent_obs('player_0')
        if bad == 'training': agent.training = True
        if bad == 'joint': agent.cfg.joint_moves = True
        if bad == 'cnn': agent.cnn_policy = object()
        if bad == 'buffer': agent.buffer.size = 1
        with pytest.raises(ValueError):
            api.clone_agent(agent)


def test_only_fixed_match_two_three_windows_create_shadow_records():
    api = probe()
    agent, _ = agent_obs('player_0')
    wrapped = api.InfluenceAgent(agent)
    for step, ms in [(25, 25), (125, 24), (126, 25), (202, 0), (227, 25), (303, 0)]:
        wrapped.act(step, make_obs(step, ms, units=[]))
    assert [(r['match_idx'], r['match_step']) for r in wrapped.records] == [(1, 25), (2, 25)]
    assert all(r['selected_unit'] is None and r['distinct_changed_arrays'] == 0
               for r in wrapped.records)


def test_trajectory_comparison_rejects_any_action_observation_or_non_time_summary_difference():
    api = probe()
    left = dict(summary={'secs': 1., 'result': 1., 'steps': 303},
                traces={'ours': [{'observation': 'abc', 'actions': [[0, 0, 0]]}], 'opponent': []})
    right = copy.deepcopy(left)
    right['summary']['secs'] = 90.
    api.assert_same_game(left, right)
    for field in ['action', 'observation', 'summary']:
        bad = copy.deepcopy(right)
        if field == 'action': bad['traces']['ours'][0]['actions'][0][0] = 5
        if field == 'observation': bad['traces']['ours'][0]['observation'] = 'different'
        if field == 'summary': bad['summary']['steps'] = 302
        with pytest.raises(AssertionError): api.assert_same_game(left, bad)


def test_budget_and_protected_files_abort_before_overwrite(tmp_path):
    api = probe()
    weights = tmp_path / 'weights.pth'
    weights.write_bytes(b'original')
    with api.protect_files([weights]):
        pass
    with pytest.raises(RuntimeError, match='changed'):
        with api.protect_files([weights]): weights.write_bytes(b'changed')
    out = tmp_path / 'new'
    api.fresh_output(out)
    with pytest.raises(FileExistsError): api.fresh_output(out)
    (out / 'oversized').write_bytes(b'12345')
    with pytest.raises(RuntimeError, match='budget'): api.check_data_budget(out, limit=4)


def test_late_contest_sap_override_is_included_in_full_final_array():
    agent, obs = agent_obs('player_0', constant_right=True)
    agent.cfg.contest_sap = True
    obs['units']['position'][1, 0] = [3, 5]
    obs['units']['energy'][1, 0] = 200
    obs['units_mask'][1, 0] = True
    wrapped = probe().InfluenceAgent(agent)
    assert wrapped.act(126, obs)[0].tolist() == [2, 0, 0]
    assert wrapped.records[0]['alternatives'][0]['actions'][0] == [5, -2, 0]
    assert wrapped.records[0]['alternatives'][0]['other_units_changed'] == []


def runner():
    from experiments.analysis.v4_target_pilot_20261021 import run_influence
    return run_influence


def test_runner_only_schedules_four_pairs_and_requires_all_eight_timepoints():
    api = runner()
    assert api.GAMES == ((524000, 'player_0'), (524000, 'player_1'),
                         (524001, 'player_0'), (524001, 'player_1'))
    records = [dict(match_idx=m, match_step=s, distinct_changed_arrays=int(m == 1))
               for m in (1, 2) for s in (25, 45, 65, 85)]
    assert api.influence_gate([records] * 4) == dict(
        scheduled_states=32, action_changing_states=16, threshold=8, passed=True)
    with pytest.raises(AssertionError): api.influence_gate([records[:-1]] * 4)
    assert not api.influence_gate([[dict(r, distinct_changed_arrays=0) for r in records]] * 4)['passed']


def test_runner_deadline_raises_and_restores_signal_handler():
    import signal
    import time
    api = runner()
    before = signal.getsignal(signal.SIGALRM)
    with pytest.raises(TimeoutError):
        with api.hard_deadline(.02): time.sleep(.1)
    assert signal.getsignal(signal.SIGALRM) == before
    assert signal.getitimer(signal.ITIMER_REAL) == (0., 0.)


def test_runner_writes_bounded_json_and_refuses_changed_v3(tmp_path):
    api = runner()
    output = tmp_path / 'out'
    output.mkdir()
    with pytest.raises(RuntimeError, match='budget'):
        api.write_json(output / 'x.json', {'data': 'x' * 20}, limit=8)
    assert not (output / 'x.json').exists()
    fake = tmp_path / 'fake.pth'
    fake.write_bytes(b'not V3')
    with pytest.raises(ValueError, match='V3'):
        api.validate_v3(fake)


def test_shared_ensemble_modules_and_dynamic_aliases_remain_consistent():
    agent, obs = agent_obs('player_0')
    agent.extra_q = [copy.deepcopy(agent.q).eval()]
    agent.act(126, obs)
    clone = probe().clone_agent(agent)
    assert clone.extra_q[0] is agent.extra_q[0]
    assert clone.opt is agent.opt and clone.buffer is agent.buffer
    clone._prev_ctx['assigned'][0] = (1, 8)
    assert agent._prev_ctx['assigned'][0] == (6, 5)
    assert clone._cache[1]['assigned'][0] == (1, 8)


def test_unit_distance_tie_uses_smallest_uid_and_six_steps_is_included():
    ctx = selection_ctx()
    ctx['ally_pos'][1] = (6, 5)
    ctx['point_tiles'][6, 5] = False  # both baseline distances three
    choices, selected = probe().select_choices(ctx)
    assert selected['uid'] == 0
    ctx['ally_ids'] = np.array([0])
    ctx['point_tiles'][:] = False
    ctx['point_tiles'][8, 5] = ctx['point_tiles'][11, 5] = ctx['point_tiles'][12, 5] = True
    choices, _ = probe().select_choices(ctx)
    assert choices[0]['alternatives'] == [{'target': [11, 5], 'distance': 6}]


def test_duplicate_complete_alternative_arrays_count_once():
    agent, obs = agent_obs('player_0')
    agent.belief.point_tiles[2, 5] = agent.belief.point_tiles[4, 5] = True
    agent.belief._cache.clear()
    class NearLeftBaselinePolicy(torch.nn.Module):
        def forward(self, feats):
            dx = feats[:, FEATURE_NAMES.index('assigned_dx')]
            baseline = (dx < 0) & (dx > -.05)
            out = torch.full((len(feats), 6), -10.)
            out[:, 2], out[:, 4] = baseline.float(), (~baseline).float()
            return out
    agent.q = NearLeftBaselinePolicy().eval()
    wrapped = probe().InfluenceAgent(agent)
    wrapped.act(126, obs)
    record = wrapped.records[0]
    # Baseline takes (4,5) by stable coordinate order. Every alternative produces
    # the same LEFT action, so three changed proposals count as one array.
    assert len(record['alternatives']) == 3
    assert record['distinct_changed_arrays'] == 1
    assert sum(bool(a['changed_units']) for a in record['alternatives']) == 3


def test_trace_records_complete_arrays_and_pre_act_legal_observation():
    agent, obs = agent_obs('player_0')
    wrapped = probe().TraceAgent(agent)
    obs_digest = probe().value_digest(obs)
    actions = wrapped.act(126, obs)
    assert wrapped.trace[0]['observation'] == obs_digest
    assert wrapped.trace[0]['actions'] == actions.tolist()
    assert len(wrapped.trace[0]['actions']) == 16
