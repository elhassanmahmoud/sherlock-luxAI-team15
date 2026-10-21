"""Validation must not advance training state, even after a failed game."""
import copy
import random

import numpy as np
import pytest
import torch

from agents.sherlock.main import Agent_x
from scripts import experiment as E
from scripts.variants import seed_everything, variant_cfg
from tests.conftest import ENV_CFG, make_obs


@pytest.fixture
def learners():
    seed_everything(47)
    cfg = variant_cfg('full_rules_v3')
    cfg.buffer_capacity, cfg.hidden = 5, 8
    a = Agent_x('player_1', cfg=cfg, seed=4700)
    a.set_env_cfg(dict(ENV_CFG))
    a.autosave_on_terminate = False
    # Populated optimizer, gradients and circular replay distinguish true preservation.
    loss = sum(p.sum() for p in a.q.parameters())
    loss.backward()
    a.opt.step()
    for i in range(7):
        a.buffer.push(np.full(a.buffer.obs_dim, i), i % a.n_actions, i / 10,
                      np.full(a.buffer.obs_dim, i + 1), False, np.ones(a.n_actions, bool))
    a.env_steps, a.learn_steps, a.recent_losses = 19, 3, [.2, .4]
    a.q.eval()  # Deliberately different agent/q/target modes.
    a.target_q.train()
    learners = E.Learners.__new__(E.Learners)
    learners.agents = {'player_0': a, 'player_1': a}
    return learners


def draws(a):
    return [random.random(), np.random.random(), torch.rand(4), a.rng.random(4)]


def assert_draws(actual, expected):
    assert actual[:2] == expected[:2]
    assert torch.equal(actual[2], expected[2])
    np.testing.assert_array_equal(actual[3], expected[3])


def dirty_episode(a):
    a.new_game('player_0')
    a.set_env_cfg({**ENV_CFG, 'unit_move_cost': 9})
    a.belief.point_tiles[2, 2] = True
    a._prev_feats[0] = np.ones(a.buffer.obs_dim)
    a._prev_actions[0] = 1
    a._cache = ('validation',)
    a._paths.step, a._paths.maps = 111, {(1, 1): np.ones((2, 2))}
    draws(a)


@pytest.mark.parametrize('raises', [False, True])
def test_restores_rng_modes_context_and_exact_small_learning_state(learners, monkeypatch, raises):
    a = learners.agents['player_0']
    arrays = {k: v.copy() for k, v in vars(a.buffer).items() if isinstance(v, np.ndarray)}
    q = copy.deepcopy(a.q.state_dict())
    target = copy.deepcopy(a.target_q.state_dict())
    opt = copy.deepcopy(a.opt.state_dict())
    gradients = [p.grad.clone() for p in a.q.parameters()]
    rngs = (random.getstate(), np.random.get_state(), torch.get_rng_state(), copy.deepcopy(a.rng.bit_generator.state))
    expected = draws(a)
    random.setstate(rngs[0]); np.random.set_state(rngs[1]); torch.set_rng_state(rngs[2]); a.rng.bit_generator.state = rngs[3]
    calls = []
    original_new_game = a.new_game
    def new_game(side=None):
        calls.append(side)
        original_new_game(side)
    monkeypatch.setattr(a, 'new_game', new_game)
    def validation(*args):
        assert not a.training and not a.q.training
        dirty_episode(a)
        if raises:
            raise LookupError('synthetic game failed')
        return [{'raw': 'kept'}]
    monkeypatch.setattr(E, 'play_set', validation)
    if raises:
        with pytest.raises(LookupError, match='synthetic'):
            E.run_validation(None, learners, [500720], ['default'], isolate=True)
    else:
        assert E.run_validation(None, learners, [500720], ['default'], isolate=True) == [{'raw': 'kept'}]
    assert_draws(draws(a), expected)
    assert (a.training, a.q.training, a.target_q.training) == (True, False, True)
    assert a.player == 'player_1' and a.env_cfg == ENV_CFG
    assert calls == ['player_0', 'player_1']  # aliased learner cleaned once
    assert not a.belief.point_tiles.any() and not a._prev_feats and not a._prev_actions
    assert a._cache is None and a._paths.maps == {} and a._paths.step is None
    assert (a.env_steps, a.learn_steps, a.recent_losses) == (19, 3, [.2, .4])
    assert (a.buffer.pos, a.buffer.size) == (2, 5)
    for k, v in arrays.items():
        np.testing.assert_array_equal(getattr(a.buffer, k), v)
        assert getattr(a.buffer, k).flags.writeable
    for k, v in q.items():
        assert torch.equal(a.q.state_dict()[k], v)
    for k, v in target.items():
        assert torch.equal(a.target_q.state_dict()[k], v)
    assert a.opt.state_dict()['param_groups'] == opt['param_groups']
    for key, state in opt['state'].items():
        for name, value in state.items():
            assert torch.equal(a.opt.state_dict()['state'][key][name], value)
    assert all(torch.equal(p.grad, old) for p, old in zip(a.q.parameters(), gradients))


@pytest.mark.parametrize('method', ['update', '_learn', 'save_agent', 'pop_mean_loss', 'push', 'sample', 'step'])
def test_forbids_learning_or_buffer_calls_before_any_side_effect(learners, monkeypatch, method):
    a = learners.agents['player_0']
    owner = a.buffer if method in ('push', 'sample') else a.opt if method == 'step' else a
    def validation(*args):
        getattr(owner, method)()
    monkeypatch.setattr(E, 'play_set', validation)
    with pytest.raises(RuntimeError, match='validation'):
        E.run_validation(None, learners, [], [], isolate=True)
    assert a.env_steps == 19 and a.training and a.player == 'player_1'


@pytest.mark.parametrize('mutation', ['array', 'replacement', 'counter', 'weight', 'optimizer'])
def test_rejects_mutation_and_restores_cleanup_not_corrupted_learning_data(learners, monkeypatch, mutation):
    a = learners.agents['player_0']
    def validation(*args):
        dirty_episode(a)
        if mutation == 'array':
            a.buffer.s[0, 0] = 999
        elif mutation == 'replacement':
            a.buffer.s = a.buffer.s.copy()
        elif mutation == 'counter':
            a.env_steps += 1
        elif mutation == 'weight':
            with torch.no_grad():
                next(a.q.parameters()).add_(1)
        else:
            a.opt.param_groups[0]['lr'] *= 2
        return []
    monkeypatch.setattr(E, 'play_set', validation)
    with pytest.raises((RuntimeError, ValueError)):
        E.run_validation(None, learners, [], [], isolate=True)
    assert a.training and a.player == 'player_1' and a._cache is None


def test_next_training_game_resets_seed_and_episode(learners, monkeypatch):
    a = learners.agents['player_0']
    monkeypatch.setattr(E, 'play_set', lambda *args: (dirty_episode(a), [])[1])
    E.run_validation(None, learners, [], [], isolate=True)
    class StopAtTrainingReset(Exception):
        pass
    class Env:
        def reset(self, seed):
            assert seed == 470375
            assert a.player == 'player_0' and not a._prev_feats and a._cache is None
            assert not a.belief.point_tiles.any()
            raise StopAtTrainingReset
    from scripts.common import play_game
    with pytest.raises(StopAtTrainingReset):
        play_game(Env(), a, object(), 470375, 'player_0', train=True)


def test_identity_hash_distinguishes_nested_state_structure():
    assert E.state_sha256([[1], 2]) != E.state_sha256([[1, 2]])


@pytest.mark.parametrize('seed', [47, 48, 49])
def test_actual_fresh_pair_identity_is_equal_and_binds_tensors_rng_and_config(tmp_path, monkeypatch, seed):
    from tests.test_early_curriculum import install_tiny_cli
    install_tiny_cli(monkeypatch)
    seed_everything(seed)
    left = E.Learners('full_rules_v3', tmp_path / 'control', seed)
    first = E.initial_identity(left)
    seed_everything(seed)
    right = E.Learners('full_rules_v3', tmp_path / 'early', seed)
    assert E.initial_identity(right) == first
    a = right.agents['player_0']
    entry = first['learners'][0]
    assert entry['sides'] == ['player_0', 'player_1']
    assert (entry['env_steps'], entry['learn_steps']) == (0, 0)
    assert entry['replay']['logical_content'] == 'empty-replay-v1'
    assert (entry['replay']['size'], entry['replay']['pos'], entry['replay']['_mask_dim']) == (0, 0, 1)
    for array in vars(a.buffer).values():
        if isinstance(array, np.ndarray):
            np.testing.assert_array_equal(array, np.ones_like(array) if array.dtype == bool else np.zeros_like(array))
    a.rng.random()
    assert E.initial_identity(right)['learners'][0]['agent_rng_sha256'] != entry['agent_rng_sha256']
    a.cfg.eps_decay_steps += 1
    assert E.initial_identity(right)['learners'][0]['config'] != entry['config']
    with torch.no_grad():
        next(a.q.parameters()).add_(1)
    assert E.initial_identity(right)['learners'][0]['q_sha256'] != entry['q_sha256']
    a.buffer.pos = 1
    with pytest.raises(ValueError, match='fresh'):
        E.initial_identity(right)


def test_readonly_buffer_flags_and_original_eval_modes_are_preserved(learners, monkeypatch):
    a = learners.agents['player_0']
    a.set_to_eval_mode()
    a.target_q.eval()
    a.buffer.s.flags.writeable = False
    monkeypatch.setattr(E, 'play_set', lambda *args: [])
    E.run_validation(None, learners, [], [], isolate=True)
    assert (a.training, a.q.training, a.target_q.training) == (False, False, False)
    assert not a.buffer.s.flags.writeable


def test_real_validation_path_never_updates_and_next_real_game_starts_clean(learners, monkeypatch):
    """Production play_set/play_game/act execute; bounded synthetic env is one step."""
    a = learners.agents['player_0']
    class OneStepEnv:
        seeds = []
        def reset(self, seed):
            self.seeds.append(seed)
            return {side: make_obs(1, 1, team=i, units=[(i * 23, i * 23, 100)])
                    for i, side in enumerate(('player_0', 'player_1'))}, {'params': ENV_CFG}
        def step(self, actions):
            obs = {side: make_obs(2, 2, team=i, units=[(i * 23, i * 23, 100)], wins=(1, 0))
                   for i, side in enumerate(('player_0', 'player_1'))}
            return obs, dict(player_0=0., player_1=0.), dict(player_0=True, player_1=True), dict(player_0=False, player_1=False), {}
    env = OneStepEnv()
    # real default opponent and real Sherlock act, with all runtime write guards
    rows = E.run_validation(env, learners, [500720], ['default'], isolate=True)
    assert [(r['seed'], r['side'], r['opponent']) for r in rows] == [
        (500720, 'player_0', 'default'), (500720, 'player_1', 'default')]
    assert env.seeds == [500720, 500720]
    assert a.env_steps == 19 and a.learn_steps == 3 and a._cache is None
    from scripts.common import play_game, make_opponent
    # Disable learning for this one-step training-path check; update still counts the step.
    a.learn_enabled = False
    play_game(env, a, make_opponent('default', 'player_1'), 470375, 'player_0', train=True)
    assert env.seeds[-1] == 470375 and a.env_steps == 20


def test_historical_validation_remains_opt_in(learners, monkeypatch):
    a = learners.agents['player_0']
    before = copy.deepcopy(a.rng.bit_generator.state)
    def validation(*args):
        assert not a.training
        a.rng.random()
        a.buffer.sample(1, a.rng)  # permitted by the unguarded historical path
        return []
    monkeypatch.setattr(E, 'play_set', validation)
    E.run_validation(None, learners, [], [], isolate=False)
    assert a.rng.bit_generator.state != before
    assert a.training and a.q.training
