"""Short observer tests; no live Lux games."""
import importlib.util
from types import SimpleNamespace

import numpy as np
import pytest
import torch


def module():
    assert importlib.util.find_spec('scripts.student_failure_trace') is not None, 'Loss tracer is not implemented'
    from scripts import student_failure_trace
    torch.set_num_threads(1)
    return student_failure_trace


class Agent:
    def __init__(self, ensemble=False):
        self.q = torch.nn.Linear(79, 6).eval()
        self.extra_q = [torch.nn.Linear(79, 6).eval()] if ensemble else []
        for index, net in enumerate([self.q, *self.extra_q]):
            net.feat_dim = 79
            with torch.no_grad():
                net.weight.zero_()
                net.bias.copy_(torch.tensor([0., 3., 2., 1., 5., 9.]) + index * 4)
        self.cfg = SimpleNamespace(frozen=False)
        self.training = self.autosave_on_terminate = False
        self.cnn_policy = None
        self.belief = SimpleNamespace(mirrored=True, match_idx=0,
                                      relic_positions={(2, 3)}, point_tiles=np.eye(3, dtype=bool))
        self.calls = self.context_calls = 0
        self.caught_errors = 0
        self._prev_ctx = None
        self._prev_feats, self._prev_masks = {}, {}

    def act(self, step, obs):
        self.calls += 1
        self._prev_feats, self._prev_masks = {}, {}
        self._prev_ctx = None
        actions = np.zeros((16, 3), int)
        if obs['match_steps'] == 0 or obs.get('empty'):
            return actions
        self.context_calls += 1
        self._prev_ctx = dict(assigned={7: (3, 4)}, ally_pos=np.zeros((16, 2), int),
                              ally_ene=np.full(16, 42.), match_idx=self.belief.match_idx)
        x = torch.full((1, 79), 3.)
        mask = np.array([[True, True, False, False, False, False]])
        with torch.no_grad():
            outputs = [self.q(x), *[net(x) for net in self.extra_q]]
            q = torch.stack(outputs).mean(0) if self.extra_q else outputs[0]
        q.numpy()[~mask] = -np.inf
        self._prev_feats, self._prev_masks = {7: x.numpy()[0]}, {7: mask[0]}
        actions[7] = [5, -3, 1]
        return actions


def obs(match_step=1):
    return dict(match_steps=match_step, team_points=np.array([3, 1]),
                team_wins=np.array([0, 0]), steps=match_step)


def test_trace_copies_raw_ensemble_mean_and_single_normal_context():
    st = module()
    agent = Agent(ensemble=True)
    rows = []
    with st.FailureTrace(agent, rows.append):
        action = agent.act(1, obs())
        agent._prev_feats[7][:] = 99
        agent._prev_masks[7][:] = False
        agent._prev_ctx['assigned'][7] = (99, 99)
        action[7] = 0
    unit = rows[0]['units'][0]
    assert agent.calls == agent.context_calls == 1
    assert unit['raw_q'] == [2., 5., 4., 3., 7., 11.]
    assert unit['features'] == [3.] * 79
    assert unit['mask'] == [True, True, False, False, False, False]
    assert unit['network_action'] == 1
    assert unit['final_world_action'] == [5, -3, 1]
    assert unit['final_canonical_action'] == [5, -1, 3]
    assert unit['override_observed'] is True
    assert rows[0]['context']['assigned']['7'] == [3, 4]
    assert 'rule_reason' not in unit
    assert all(not net._forward_hooks for net in [agent.q, *agent.extra_q])
    assert 'act' not in vars(agent)


def test_reset_ghosts_and_match_counter_are_not_reused():
    st = module()
    agent, rows = Agent(), []
    with st.FailureTrace(agent, rows.append):
        agent.act(1, obs())
        agent.belief.match_idx = 1
        agent.act(101, obs(0))
        agent.act(102, obs())
    assert rows[1]['units'] == []
    assert rows[1]['context'] is None
    assert rows[1]['kind'] == 'reset'
    assert rows[2]['match_counts'] == dict(act_steps=2, network_steps=1, unit_rows=1, overrides=1)
    assert rows[0]['match_counts']['act_steps'] == 1
    assert len(rows[0]['discoveries']['new_relics']) == 1
    assert rows[2]['discoveries']['new_relics'] == []


def test_existing_instance_method_and_all_hooks_restored_on_failure():
    st = module()
    agent = Agent(True)
    def fail(step, obs):
        raise RuntimeError('act failed')
    agent.act = fail
    with pytest.raises(RuntimeError, match='act failed'):
        with st.FailureTrace(agent, lambda row: None):
            agent.act(1, obs())
    assert agent.act is fail
    assert all(not net._forward_hooks for net in [agent.q, *agent.extra_q])


def test_movement_mirror_and_sap_delta_involution():
    st = module()
    world = np.array([[2, 0, 0], [3, 0, 0], [5, -3, 1]])
    result = st.canonical_actions(world, True)
    assert result.tolist() == [[1, 0, 0], [4, 0, 0], [5, -1, 3]]
    assert np.array_equal(st.canonical_actions(result, True), world)
    assert np.array_equal(st.canonical_actions(world, False), world)


def test_deadline_failure_occurs_before_act_and_restores_hooks():
    st = module()
    agent = Agent()
    def expired():
        raise TimeoutError('deadline')
    with pytest.raises(TimeoutError):
        with st.FailureTrace(agent, lambda row: None, check=expired):
            agent.act(1, obs())
    assert agent.calls == 0
    assert not agent.q._forward_hooks


def test_complete_action_digest_covers_both_sides_and_sap_deltas():
    st = module()
    actions = {'player_0': np.zeros((16, 3), int), 'player_1': np.zeros((16, 3), int)}
    baseline = st.action_digest(actions)
    assert st.action_digest(dict(reversed(list(actions.items())))) == baseline
    actions['player_1'][15, 2] = 1
    assert st.action_digest(actions) != baseline


def test_env_observer_uses_terminal_points_and_resets_match_totals(monkeypatch):
    st = module()
    class Env:
        def reset(self, seed):
            self.index = 0
            self.current = dict(player_0=obs(99), player_1=obs(99))
            return self.current, {'params': {}}
        def step(self, actions):
            self.index += 1
            current = obs(0 if self.index in (1, 3) else 1)
            current['team_points'] = np.array([0, 0])
            self.current = dict(player_0=current, player_1=current)
            return self.current, {}, {}, {}, {'terminal_points': [9 + self.index, 2]}
    monkeypatch.setattr(st, 'match_points_after_step',
                        lambda previous, next_, info: np.array(info['terminal_points']))
    rows = []
    env = st.ObservedEnv(Env(), 'player_0', rows.append)
    env.reset(seed=1)
    actions = dict(player_0=np.zeros((16, 3), int), player_1=np.zeros((16, 3), int))
    env.step(actions)
    env.step(actions)
    env.step(actions)
    assert [row['points'] for row in env.matches] == [[10, 2], [12, 2]]
    assert [row['match_index'] for row in env.matches] == [0, 1]
    assert len(env.step_digests) == 3
    assert rows[0]['terminal_points_external_only'] == [10, 2]


def test_pair_uses_original_play_path_and_rejects_different_actions(tmp_path, monkeypatch):
    """A changed action in either player must fail even with matching metrics."""
    from datetime import datetime, timedelta, timezone
    st = module()
    model = tmp_path / 'model.pth'
    model.write_bytes(b'fixture')
    calls, agents = [], []
    def create_agent(path, side, seed):
        agent = Agent()
        agents.append(agent)
        calls.append(('agent', seed))
        return agent
    class Env:
        def reset(self, seed):
            self.index = 0
            return {'player_0': obs(), 'player_1': obs()}, {}
        def step(self, actions):
            self.index += 1
            next_ = obs(self.index % 101)
            return {'player_0': next_, 'player_1': next_}, {}, {}, {}, {}
        def close(self):
            pass
    def play(env, agent, opp, seed, side, train):
        calls.append(('play', seed, side, train))
        env.reset(seed=seed)
        for index in range(303):
            actions = {'player_0': agent.act(index, obs()), 'player_1': np.zeros((16, 3), int)}
            if len(agents) == 2 and index == 301:
                actions['player_1'][15, 1] = 2
            env.step(actions)
        return {'steps': 303, 'secs': 0, 'result': 1, 'unused_nan': float('nan')}
    monkeypatch.setattr(st, '_agent', create_agent)
    monkeypatch.setattr(st, '_env', Env)
    monkeypatch.setattr(st, 'make_opponent', lambda *args, **kw: object())
    monkeypatch.setattr(st, 'play_game', play)
    monkeypatch.setattr(st, 'match_points_after_step', lambda *args: np.array([0, 0]))
    monkeypatch.setattr(st, '_learning_digest', lambda agent: 'unchanged')
    monkeypatch.setattr(st, '_pins', lambda: {})
    monkeypatch.setattr(st, '_hashes', lambda paths: {'model': 'fixed'})
    monkeypatch.setattr(st, 'reserve_output', lambda out, inputs: (out.mkdir() or out))
    with pytest.raises(ValueError, match='actions or results differ'):
        st.trace_pair(model, 'solution92', 866000, 'player_0', tmp_path / 'out',
                      datetime.now(timezone.utc) + timedelta(minutes=1))
    assert calls[0] == ('agent', 0)
    assert calls[1] == ('play', 866000, 'player_0', False)
    assert calls[2] == ('agent', 0)
    import json
    summary = json.loads((tmp_path / 'out/summary.json').read_text())
    assert summary['status'] == 'failed'
    assert summary['actions_equal'] is False
    assert summary['results_equal'] is True
    assert all(not net._forward_hooks for agent in agents for net in [agent.q, *agent.extra_q])


@pytest.mark.parametrize('team', [0, 1])
def test_real_agent_context_and_belief_are_evaluated_once(team, monkeypatch):
    """Use the actual policy, belief and feature pipeline without a simulator."""
    import copy
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.main import Agent_x
    from agents.sherlock.model import QNet
    from tests.conftest import ENV_CFG, make_obs
    st = module()
    plain = Agent_x(f'player_{team}', cfg=AgentConfig(hidden=8, dueling=False, buffer_capacity=8), train=False)
    plain.extra_q = [QNet(79, 6, hidden=8, dueling=False)]
    plain.autosave_on_terminate = False
    plain.set_env_cfg(ENV_CFG)
    plain.set_to_eval_mode()
    traced = copy.deepcopy(plain)
    counts = dict(context=0, belief=0)
    original_decide, original_observe = traced._decide, traced.belief.observe
    def decide(observation):
        counts['context'] += 1
        return original_decide(observation)
    def observe(observation):
        counts['belief'] += 1
        return original_observe(observation)
    monkeypatch.setattr(traced, '_decide', decide)
    monkeypatch.setattr(traced.belief, 'observe', observe)
    observation = make_obs(10, 10, team=team, units=[(5, 5, 100)], relics=[(12, 12)])
    expected = plain.act(10, observation)
    rows = []
    with st.FailureTrace(traced, rows.append):
        actual = traced.act(10, observation)
    assert np.array_equal(actual, expected)
    assert counts == dict(context=1, belief=1)
    assert rows[0]['context']['ally_ene'][0] == 100
    assert len(rows[0]['units'][0]['features']) == 79
    assert rows[0]['ensemble_members'] == 2
    assert not plain.q._forward_hooks and not traced.q._forward_hooks
