"""Bounded tests for exact eval-state collection; no Lux games are started."""
from datetime import datetime, timedelta, timezone
import importlib.util
from types import SimpleNamespace

import numpy as np
import pytest
import torch


def module():
    assert importlib.util.find_spec('scripts.student_collect') is not None, 'Collector is not implemented'
    from scripts import student_collect
    torch.set_num_threads(1)
    return student_collect


class FakeAgent:
    """Reproduce the actual CPU tensor/numpy alias and late rule overrides."""
    def __init__(self, mirrored=True):
        self.q = torch.nn.Linear(79, 6).eval()
        with torch.no_grad():
            self.q.weight.zero_()
            self.q.bias.copy_(torch.arange(6))
        self.cfg = SimpleNamespace(frozen=False)
        self.training = False
        self.autosave_on_terminate = False
        self.belief = SimpleNamespace(mirrored=mirrored)
        self._prev_feats, self._prev_masks = {}, {}
        self.calls = 0

    def act(self, step, obs):
        self.calls += 1
        self._prev_feats, self._prev_masks = {}, {}
        actions = np.zeros((16, 3), int)
        if obs['match_steps'] == 0 or obs.get('empty'):
            return actions
        x = torch.full((2, 79), 3., dtype=torch.float32)
        masks = np.array([[True, True, False, False, False, False],
                          [True, False, False, False, False, False]])
        with torch.no_grad():
            output = self.q(x)
        output.numpy()[~masks] = -np.inf
        self._prev_feats = {7: x.numpy()[0], 2: x.numpy()[1]}
        self._prev_masks = {7: masks[0], 2: masks[1]}
        self._prev_actions = {7: 0, 2: 0}  # Not authoritative final actions.
        actions[7] = [2, 0, 0]  # world RIGHT -> canonical UP
        actions[2] = [5, -3, 1]  # legal late SAP override outside network mask
        return actions


def test_copies_before_numpy_mask_mutation_and_uses_final_world_actions():
    sc = module()
    agent = FakeAgent()
    with sc.ExactCollector(agent) as capture:
        capture.set_game(dict(game_index=4, env_seed=865102, side=1, is_train=True))
        actions = agent.act(11, {'match_steps': 12})
        agent._prev_feats[7][:] = 99
        agent._prev_masks[7][:] = False
        actions[7][:] = 0
    data = capture.arrays()
    assert agent.calls == 1
    assert np.array_equal(data['student_q'], [[0, 1, 2, 3, 4, 5]] * 2)
    assert np.all(data['s'] == 3)
    assert np.array_equal(data['mask'][0], [True, True, False, False, False, False])
    assert data['uid'].tolist() == [7, 2]
    assert data['final_action'].tolist() == [1, 5]
    assert data['world_action'].tolist() == [[2, 0, 0], [5, -3, 1]]
    assert data['env_step'].tolist() == [11, 11]
    assert data['match_step'].tolist() == [12, 12]
    assert capture.counts['final_outside_network_mask_rows'] == 1
    assert len(agent.q._forward_hooks) == 0
    assert 'act' not in vars(agent)


def test_reset_and_no_unit_steps_never_reuse_previous_network_rows():
    sc = module()
    agent = FakeAgent(False)
    with sc.ExactCollector(agent) as capture:
        capture.set_game(dict(game_index=0, env_seed=1, side=0, is_train=True))
        agent.act(1, {'match_steps': 1})
        agent.act(2, {'match_steps': 0})
        agent.act(3, {'match_steps': 3, 'empty': True})
    assert len(capture.arrays()['s']) == 2
    assert capture.counts['reset_steps'] == 1
    assert capture.counts['no_unit_steps'] == 1
    assert capture.counts['no_network_steps'] == 2
    assert capture.arrays()['final_action'].tolist() == [2, 5]


def test_hook_removed_and_act_restored_when_original_act_raises():
    sc = module()
    agent = FakeAgent()
    original = lambda step, obs: (_ for _ in ()).throw(RuntimeError('act failed'))
    agent.act = original
    with pytest.raises(RuntimeError, match='act failed'):
        with sc.ExactCollector(agent):
            agent.act(1, {'match_steps': 1})
    assert agent.act is original
    assert len(agent.q._forward_hooks) == 0


def test_feature_alignment_failure_is_not_silently_dropped():
    sc = module()
    agent = FakeAgent()
    original = agent.act
    def wrong(step, obs):
        result = original(step, obs)
        agent._prev_feats[7] = np.zeros(79, np.float32)
        return result
    agent.act = wrong
    with pytest.raises(ValueError, match='feature'):
        with sc.ExactCollector(agent):
            agent.act(1, {'match_steps': 1})
    assert len(agent.q._forward_hooks) == 0


def test_plan_holds_out_whole_maps_and_preserves_fixed_opponents():
    sc = module()
    plan = sc.game_plan(865100, 30)
    assert len(plan) == 60
    assert [row['opponent'] for row in plan[:10:2]] == ['solution92'] * 3 + ['default', 'self']
    assert [row['env_seed'] for row in plan if not row['is_train']][::2] == list(range(865125, 865130))
    small = sc.game_plan(2, 5)
    assert [(r['side'], r['is_train']) for r in small[-2:]] == [(0, False), (1, False)]
    assert sum(r['is_train'] for r in small) == 8


@pytest.mark.parametrize('maps', [0, 1, True, 2.5])
def test_invalid_plan_cannot_have_empty_train_split(maps):
    with pytest.raises(ValueError):
        module().game_plan(2, maps)


def test_output_guards_reject_occupied_and_protected_paths(tmp_path):
    sc = module()
    occupied = tmp_path / 'occupied'
    occupied.mkdir()
    with pytest.raises(ValueError):
        sc.reserve_output(occupied, [])
    with pytest.raises(ValueError):
        sc.reserve_output(sc.ROOT / 'agents/sherlock/weights/collect', [])
    source = tmp_path / 'source' / 'student.pth'
    with pytest.raises(ValueError):
        sc.reserve_output(source.parent, [source])


def test_deadline_checked_before_every_act_and_removes_hook():
    sc = module()
    agent = FakeAgent()
    def expired():
        raise TimeoutError('deadline')
    with pytest.raises(TimeoutError):
        with sc.ExactCollector(agent, check=expired):
            agent.act(1, {'match_steps': 1})
    assert agent.calls == 0
    assert len(agent.q._forward_hooks) == 0


def test_rejects_uid_outside_course_sixteen_unit_limit():
    sc = module()
    agent = FakeAgent()
    original = agent.act
    def wrong(step, obs):
        actions = original(step, obs)
        agent._prev_feats[17] = agent._prev_feats.pop(2)
        agent._prev_masks[17] = agent._prev_masks.pop(2)
        return np.pad(actions, ((0, 16), (0, 0)))
    agent.act = wrong
    with pytest.raises(ValueError, match='unit IDs'):
        with sc.ExactCollector(agent) as capture:
            capture.set_game(dict(game_index=0, env_seed=1, side=0, is_train=True))
            agent.act(1, {'match_steps': 1})


def checkpoint_file(tmp_path):
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.model import QNet
    torch.set_num_threads(1)
    net = QNet(79, 6, 512, True)
    state = net.state_dict()
    cp = dict(q=state, target_q={k: v.clone() for k, v in state.items()},
              cfg=AgentConfig(hidden=512).to_dict(), feature_dim=79, n_actions=6,
              ensemble=[], ensemble_dims=[], env_steps=60000, learn_steps=0)
    path = tmp_path / 'student.pth'
    torch.save(cp, path)
    return path, cp


@pytest.mark.parametrize('mutation', ['ensemble', 'optimizer', 'width', 'target', 'nan'])
def test_student_rejects_incompatible_or_mutated_checkpoint(tmp_path, mutation):
    sc = module()
    path, cp = checkpoint_file(tmp_path)
    if mutation == 'ensemble':
        cp['ensemble'] = [cp['q']]
    elif mutation == 'optimizer':
        cp['opt'] = {}
    elif mutation == 'width':
        cp['cfg']['hidden'] = 256
    elif mutation == 'target':
        next(iter(cp['target_q'].values())).add_(1)
    else:
        next(iter(cp['q'].values())).flatten()[0] = float('nan')
    torch.save(cp, path)
    with pytest.raises((ValueError, RuntimeError)):
        sc.load_student(path)


def collect_fixture(tmp_path, monkeypatch, *, mutation=False):
    sc = module()
    path, cp = checkpoint_file(tmp_path)
    teacher, v13 = tmp_path / 'teacher.pth', tmp_path / 'v13.pth'
    teacher.write_bytes(b'teacher')
    v13.write_bytes(b'v13')
    monkeypatch.setattr(sc, 'TEACHER', teacher)
    monkeypatch.setattr(sc, 'V13', v13)
    monkeypatch.setattr(sc, 'V13_SHA256', sc.sha256(v13))
    monkeypatch.setattr(sc, '_pins', lambda: {'sources': {'fixed': 'hash'}, 'protected': {}})
    agent = FakeAgent()
    agent.target_q = torch.nn.Linear(79, 6)
    agent.opt = torch.optim.Adam(agent.q.parameters())
    agent.env_steps, agent.learn_steps = 60000, 0
    agent.buffer, agent.recent_losses = [], []
    monkeypatch.setattr(sc, '_agent', lambda student, checkpoint: agent)
    net = torch.nn.Linear(79, 6)
    with torch.no_grad():
        net.weight.zero_()
        net.bias.fill_(8)
    monkeypatch.setattr(sc, 'load_teacher', lambda path: ([net], {'hidden': 512}))
    monkeypatch.setattr(sc, '_env', lambda: object())
    monkeypatch.setattr(sc, 'make_opponent', lambda *args, **kwargs: object())
    def play(env, a, opp, seed, side, train):
        assert train is False
        a.act(0, {'match_steps': 0})
        a.act(1, {'match_steps': 1})
        a.act(2, {'match_steps': 2, 'empty': True})
        if mutation:
            a.env_steps += 1
        return dict(seed=seed, side=side, steps=303, result=1., optional=float('nan'))
    monkeypatch.setattr(sc, 'play_game', play)
    return sc, path, agent


def test_complete_collection_serializes_exact_schema_and_hash_receipts(tmp_path, monkeypatch):
    import json
    sc, path, agent = collect_fixture(tmp_path, monkeypatch)
    out = tmp_path / 'out'
    manifest = sc.collect(path, out, 865100, 5, datetime.now(timezone.utc) + timedelta(minutes=1))
    assert manifest['status'] == 'done'
    assert manifest['games_completed'] == 10
    assert manifest['rows'] == 20
    assert manifest['train_rows'] == 16
    assert manifest['diagnostic_rows'] == 4
    assert manifest['learning_state_before'] == manifest['learning_state_after']
    assert manifest['files_sha256'] == {name: sc.sha256(out / name) for name in ['dataset.npz', 'games.jsonl']}
    with np.load(out / 'dataset.npz', allow_pickle=False) as data:
        assert set(data.files) == {'s', 'mask', 'teacher_q', 'student_q', 'final_action', 'world_action',
                                   'game_index', 'env_seed', 'side', 'env_step', 'match_step', 'uid', 'is_train'}
        assert data['teacher_q'].dtype == np.float32
        assert np.all(data['teacher_q'] == 8)
        assert data['world_action'].dtype == np.int16
        assert data['env_seed'].dtype == np.int64
        assert data['is_train'].tolist() == [True] * 16 + [False] * 4
    games = [json.loads(line) for line in (out / 'games.jsonl').read_text().splitlines()]
    assert len(games) == 10
    assert games[-1]['env_seed'] == 865104
    assert games[-1]['optional'] is None
    assert json.loads((out / 'status.json').read_text())['status'] == 'done'
    assert len(agent.q._forward_hooks) == 0


@pytest.mark.parametrize('failure', ['deadline', 'learning_mutation', 'source_mutation'])
def test_failure_never_publishes_partial_dataset_success(tmp_path, monkeypatch, failure):
    import json
    sc, path, agent = collect_fixture(tmp_path, monkeypatch, mutation=failure == 'learning_mutation')
    if failure == 'source_mutation':
        calls = iter([{'source': 'before'}, {'source': 'after'}])
        monkeypatch.setattr(sc, '_pins', lambda: next(calls))
    deadline = datetime.now(timezone.utc) + timedelta(minutes=-1 if failure == 'deadline' else 1)
    out = tmp_path / 'failed'
    with pytest.raises((ValueError, TimeoutError)):
        sc.collect(path, out, 865100, 5, deadline)
    assert not (out / 'dataset.npz').exists()
    assert not (out / 'dataset.pending.npz').exists()
    assert json.loads((out / 'status.json').read_text())['status'] == 'failed'
    assert json.loads((out / 'manifest.json').read_text())['status'] == 'failed'
    assert len(agent.q._forward_hooks) == 0


def test_real_load_is_single_failfast_eval_and_preserves_input(tmp_path):
    sc = module()
    path, cp = checkpoint_file(tmp_path)
    before = sc.sha256(path)
    loaded = sc.load_student(path)
    agent = sc._agent(path, loaded)
    assert agent.cfg.hidden == 512
    assert not agent.cfg.frozen and not agent.training and not agent.q.training
    assert not agent.autosave_on_terminate and not agent.learn_enabled
    assert not agent.extra_q and agent.cnn_policy is None
    assert len(agent.q._forward_hooks) == 0
    assert sc.sha256(path) == before
    for key, value in agent.q.state_dict().items():
        assert torch.equal(value.cpu(), cp['q'][key])


@pytest.mark.parametrize('corruption', ['nonfinite_q', 'empty_mask', 'duplicate_forward'])
def test_bad_current_decisions_fail_instead_of_dropping_rows(corruption):
    sc = module()
    agent = FakeAgent()
    if corruption == 'nonfinite_q':
        with torch.no_grad():
            agent.q.bias[0] = float('nan')
    original = agent.act
    def wrong(step, obs):
        actions = original(step, obs)
        if corruption == 'empty_mask':
            agent._prev_masks[7][:] = False
        if corruption == 'duplicate_forward':
            agent.q(torch.zeros(2, 79))
        return actions
    agent.act = wrong
    with pytest.raises(ValueError):
        with sc.ExactCollector(agent) as capture:
            capture.set_game(dict(game_index=0, env_seed=1, side=0, is_train=True))
            agent.act(1, {'match_steps': 1})
    assert len(agent.q._forward_hooks) == 0


def test_output_aliases_and_deadline_without_timezone_are_rejected(tmp_path):
    sc = module()
    alias = tmp_path / 'alias'
    alias.symlink_to(sc.ROOT / 'agents/sherlock/weights', target_is_directory=True)
    with pytest.raises(ValueError):
        sc.reserve_output(alias / 'new', [])
    with pytest.raises(ValueError, match='UTC offset'):
        sc.collect(tmp_path / 'missing.pth', tmp_path / 'out', 865100, 5, datetime.now())
    assert not (tmp_path / 'out').exists()


def test_legacy_provenance_must_be_complete_and_have_positive_training_counts(tmp_path):
    sc = module()
    path, cp = checkpoint_file(tmp_path)
    cp.update(distillation_updates=0, distillation_epochs=30, distillation_seed=20261104)
    torch.save(cp, path)
    with pytest.raises(ValueError, match='provenance'):
        sc.load_student(path)
