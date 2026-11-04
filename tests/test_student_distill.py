"""Synthetic, bounded tests for the single-network student protocol."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet


def module():
    # Import inside tests so a missing implementation is an explicit failing assertion.
    import importlib.util
    assert importlib.util.find_spec('scripts.student_distill') is not None
    from scripts import student_distill
    return student_distill


def test_teacher_is_arithmetic_mean_and_never_uses_gradients():
    sd = module()
    nets = [QNet(79, 6, 8, False) for _ in range(3)]
    for index, net in enumerate(nets):
        with torch.no_grad():
            for parameter in net.parameters():
                parameter.zero_()
            net.head.bias.copy_(torch.arange(6) + index * 6)
    x = torch.ones(4, 79)
    result = sd.teacher_q(nets, x)
    torch.testing.assert_close(result, torch.arange(6).float().expand(4, 6) + 6)
    assert not result.requires_grad
    assert all(not net.training and all(p.grad is None for p in net.parameters()) for net in nets)


def test_analytic_mse_decomposition_and_unmasked_agreement():
    sd = module()
    target = np.array([[1, 2, 3, 4, 5, 6], [6, 5, 4, 3, 2, 1]], np.float32)
    prediction = target + np.array([[2] * 6, [-6, -4, -2, 0, 2, 4]], np.float32)
    result = sd.q_metrics(prediction, target)
    assert result['q_mse'] == pytest.approx(np.mean((prediction - target) ** 2))
    assert result['q_mse'] == pytest.approx(result['mean_value_mse'] + result['centered_action_mse'])
    assert result['unmasked_argmax_agreement'] == .5


def test_each_file_is_split_independently_and_overlap_counts_exact_rows(tmp_path):
    sd = module()
    a = np.repeat(np.arange(10, dtype=np.float32)[:, None], 79, axis=1)
    b = a + 100
    b[9] = a[0]
    paths = [tmp_path / 'a.npz', tmp_path / 'b.npz']
    for path, rows in zip(paths, (a, b)):
        np.savez(path, s=rows)
    datasets, metadata = sd.load_buffers(paths, row_cap=10)
    assert [item['split_row'] for item in metadata] == [8, 8]
    assert [item['source_rows'] for item in metadata] == [10, 10]
    assert np.array_equal(datasets[1][0][:8], b[:8])
    overlap = sd.row_overlap(datasets)
    assert overlap['shared_unique_feature_rows'] == 1
    assert overlap['train_rows_matching_diagnostic'] == 1
    assert overlap['diagnostic_rows_matching_train'] == 1


@pytest.mark.parametrize('rows', [np.zeros((10, 78), np.float32), np.zeros((10, 79), np.float64),
                                  np.full((10, 79), np.nan, np.float32), np.zeros((1, 79), np.float32)])
def test_rejects_wrong_shape_dtype_nonfinite_or_empty_split(tmp_path, rows):
    sd = module()
    path = tmp_path / 'bad.npz'
    np.savez(path, s=rows)
    with pytest.raises(ValueError):
        sd.load_buffers([path], row_cap=10)


def test_nonfinite_rows_beyond_cap_are_still_rejected(tmp_path):
    sd = module()
    rows = np.zeros((20, 79), np.float32)
    rows[-1, 0] = np.inf
    path = tmp_path / 'bad.npz'
    np.savez(path, s=rows)
    with pytest.raises(ValueError, match='finite'):
        sd.load_buffers([path], row_cap=10)


def test_rejects_occupied_protected_and_source_ancestor_outputs(tmp_path):
    sd = module()
    occupied = tmp_path / 'occupied'
    occupied.mkdir()
    with pytest.raises(ValueError):
        sd.reserve_output(occupied, [])
    with pytest.raises(ValueError):
        sd.reserve_output(sd.ROOT / 'agents/sherlock/weights/new', [])
    source = tmp_path / 'future' / 'teacher.pth'
    with pytest.raises(ValueError):
        sd.reserve_output(tmp_path / 'future', [source])


def fixture(tmp_path, monkeypatch):
    sd = module()
    torch.set_num_threads(1)
    torch.manual_seed(7)
    cfg = AgentConfig(hidden=8).to_dict()
    states = [QNet(79, 6, 8, True).state_dict() for _ in range(36)]
    source = tmp_path / 'teacher.pth'
    torch.save(dict(q=states[0], ensemble=states[1:], ensemble_dims=[79] * 35,
                    cfg=cfg, feature_dim=79, n_actions=6), source)
    monkeypatch.setattr(sd, 'V14_SHA256', sd.sha256(source))
    paths = [tmp_path / 'a.npz', tmp_path / 'b.npz']
    rng = np.random.default_rng(4)
    for path in paths:
        np.savez(path, s=rng.normal(size=(20, 79)).astype(np.float32))
    return sd, source, paths


def test_three_epoch_export_is_single_net_reload_exact_and_inputs_unchanged(tmp_path, monkeypatch):
    sd, source, paths = fixture(tmp_path, monkeypatch)
    before = [sd.sha256(path) for path in [source, *paths]]
    out = tmp_path / 'student'
    result = sd.run_distillation(source, paths, out, datetime.now(timezone.utc) + timedelta(minutes=2), row_cap=20)
    assert result['status'] == 'complete'
    checkpoint = torch.load(out / 'weights/agent.pth', weights_only=True)
    assert checkpoint['ensemble'] == checkpoint['ensemble_dims'] == []
    assert checkpoint['cfg']['hidden'] == 512
    assert checkpoint['env_steps'] == 60000 and checkpoint['learn_steps'] == 0
    assert not {'opt', 'buffer', 'replay'} & checkpoint.keys()
    assert checkpoint['distillation_updates'] == 3
    assert all(torch.equal(value, checkpoint['target_q'][key]) for key, value in checkpoint['q'].items())
    net = QNet(79, 6, 512, True).eval()
    net.load_state_dict(checkpoint['q'])
    x = torch.from_numpy(np.load(paths[0])['s'])
    predictions = net(x).detach().numpy()
    assert sd.sha256(source) == before[0]
    assert [sd.sha256(path) for path in [source, *paths]] == before
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['epochs_completed'] == 3 and manifest['updates'] == 3
    assert manifest['inputs_before'] == manifest['inputs_after']
    assert manifest['sources_before'] == manifest['sources_after']
    assert manifest['reload_exact'] is True
    metrics = json.loads((out / 'metrics.json').read_text())
    for buffer in metrics['buffers']:
        assert buffer['before']['diagnostic']['rows'] == buffer['after']['diagnostic']['rows'] == 4
    assert np.isfinite(predictions).all()
    from agents.sherlock.main import Agent_x
    loaded = Agent_x('player_0', agent_path=str(out / 'weights/agent.pth'), train=False)
    assert len(loaded.extra_q) == 0
    assert torch.equal(loaded.q(x), net(x))


@pytest.mark.parametrize('entrypoint', ['api', 'cli'])
def test_explicit_two_epochs_export_requested_count_and_reload_exact(tmp_path, monkeypatch, entrypoint):
    sd, source, paths = fixture(tmp_path, monkeypatch)
    out = tmp_path / 'two-epochs'
    deadline = datetime.now(timezone.utc) + timedelta(minutes=2)
    if entrypoint == 'api':
        result = sd.run_distillation(source, paths, out, deadline, row_cap=20, epochs=2)
        assert result['status'] == 'complete'
    else:
        assert sd.main(['--teacher', str(source), '--buffers', *map(str, paths),
                        '--out', str(out), '--deadline-utc', deadline.isoformat(),
                        '--row-cap', '20', '--epochs', '2']) == 0
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['status'] == 'complete'
    assert manifest['epochs_requested'] == manifest['epochs_completed'] == 2
    assert manifest['updates'] == 2
    assert manifest['training_rows_seen'] == 64
    assert manifest['reload_exact'] is True
    checkpoint = torch.load(out / 'weights/agent.pth', weights_only=True)
    assert checkpoint['distillation_epochs'] == checkpoint['distillation_updates'] == 2
    net = QNet(79, 6, 512, True).eval()
    net.load_state_dict(checkpoint['q'])
    from agents.sherlock.main import Agent_x
    loaded = Agent_x('player_0', agent_path=str(out / 'weights/agent.pth'), train=False)
    x = torch.from_numpy(np.load(paths[0])['s'])
    assert torch.equal(loaded.q(x), net(x))


@pytest.mark.parametrize('epochs', [True, False, 1.0, 2.5, 0, -1, 101, '2', np.int64(2)])
def test_invalid_epoch_count_rejected_before_output_reservation(tmp_path, epochs):
    sd = module()
    out = tmp_path / 'invalid-epochs'
    with pytest.raises(ValueError, match='epochs'):
        sd.run_distillation(tmp_path / 'teacher.pth', [tmp_path / 'a.npz', tmp_path / 'b.npz'],
                            out, datetime.now(timezone.utc) + timedelta(minutes=2), epochs=epochs)
    assert not out.exists()


def test_expired_deadline_has_incomplete_status_without_checkpoint(tmp_path, monkeypatch):
    sd, source, paths = fixture(tmp_path, monkeypatch)
    out = tmp_path / 'timed-out'
    result = sd.run_distillation(source, paths, out, datetime.now(timezone.utc) - timedelta(seconds=1), row_cap=20)
    assert result['status'] == 'incomplete'
    assert not (out / 'weights/agent.pth').exists()
    assert json.loads((out / 'status.json').read_text())['status'] == 'incomplete'


def test_teacher_hash_member_count_and_finite_tensors_are_guarded(tmp_path, monkeypatch):
    sd, source, paths = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(sd, 'V14_SHA256', '0' * 64)
    with pytest.raises(ValueError, match='SHA'):
        sd.load_teacher(source)
    cp = torch.load(source, weights_only=True)
    cp['ensemble'].pop()
    cp['ensemble_dims'].pop()
    torch.save(cp, source)
    monkeypatch.setattr(sd, 'V14_SHA256', sd.sha256(source))
    with pytest.raises(ValueError, match='36'):
        sd.load_teacher(source)
    cp['ensemble'].append(cp['q'])
    cp['ensemble_dims'].append(79)
    cp['q']['body.0.weight'][0, 0] = float('nan')
    torch.save(cp, source)
    monkeypatch.setattr(sd, 'V14_SHA256', sd.sha256(source))
    with pytest.raises(ValueError, match='finite'):
        sd.load_teacher(source)


def test_deadline_between_training_batches_keeps_partial_run_incomplete(tmp_path, monkeypatch):
    sd, source, paths = fixture(tmp_path, monkeypatch)
    deadline = datetime.now(timezone.utc) + timedelta(minutes=2)
    write = sd._write

    class ExpiredClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return deadline + timedelta(seconds=1)

    def expire_after_first_update(path, value):
        write(path, value)
        if value.get('updates') == 1:
            monkeypatch.setattr(sd, 'datetime', ExpiredClock)

    monkeypatch.setattr(sd, '_write', expire_after_first_update)
    out = tmp_path / 'partial'
    result = sd.run_distillation(source, paths, out, deadline, row_cap=20)
    assert result['status'] == 'incomplete'
    assert result['updates'] == 1 and result['epochs_completed'] == 1
    assert not (out / 'weights/agent.pth').exists()


def test_source_mutation_refuses_final_export(tmp_path, monkeypatch):
    sd, source, paths = fixture(tmp_path, monkeypatch)
    diagnostics = sd._diagnostics

    def mutate_after_diagnostics(*args):
        result = diagnostics(*args)
        with source.open('ab') as handle:
            handle.write(b'changed')
        return result

    monkeypatch.setattr(sd, '_diagnostics', mutate_after_diagnostics)
    out = tmp_path / 'mutated'
    with pytest.raises(ValueError, match='mutation'):
        sd.run_distillation(source, paths, out, datetime.now(timezone.utc) + timedelta(minutes=2), row_cap=20)
    assert not (out / 'weights/agent.pth').exists()
    assert not (out / 'weights/agent.pending.pth').exists()
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['status'] == 'incomplete'
    assert manifest['inputs_before'] != manifest['inputs_after']


def test_fixed_seed_repeats_exact_student_and_preserves_gameplay_cfg(tmp_path, monkeypatch):
    sd, source, paths = fixture(tmp_path, monkeypatch)
    checkpoints = []
    for index in range(2):
        out = tmp_path / f'repeat-{index}'
        sd.run_distillation(source, paths, out, datetime.now(timezone.utc) + timedelta(minutes=2), row_cap=20)
        checkpoints.append(torch.load(out / 'weights/agent.pth', weights_only=True))
    assert all(torch.equal(value, checkpoints[1]['q'][key]) for key, value in checkpoints[0]['q'].items())
    teacher_cfg = torch.load(source, weights_only=True)['cfg']
    assert checkpoints[0]['cfg'] == {**teacher_cfg, 'hidden': 512}


def test_overlap_treats_signed_zero_as_equal_without_mutating_inputs():
    sd = module()
    rows = np.zeros((10, 79), np.float32)
    rows[-1] = -0.0
    original = rows.tobytes()
    overlap = sd.row_overlap([(rows, 8)])
    assert overlap['shared_unique_feature_rows'] == 1
    assert overlap['train_rows_matching_diagnostic'] == 8
    assert overlap['diagnostic_rows_matching_train'] == 2
    assert rows.tobytes() == original


def test_distillation_restores_caller_determinism_setting(tmp_path, monkeypatch):
    sd, source, paths = fixture(tmp_path, monkeypatch)
    previous = torch.are_deterministic_algorithms_enabled()
    try:
        torch.use_deterministic_algorithms(False)
        sd.run_distillation(source, paths, tmp_path / 'flags', datetime.now(timezone.utc) + timedelta(minutes=2), row_cap=20)
        assert torch.are_deterministic_algorithms_enabled() is False
    finally:
        torch.use_deterministic_algorithms(previous)


def test_teacher_matches_deployed_stack_mean_exactly():
    sd = module()
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(835)
        nets = [QNet(79, 6, 8, True).eval() for _ in range(36)]
        x = torch.randn(9, 79)
        with torch.no_grad():
            expected = torch.stack([net(x) for net in nets]).mean(dim=0)
        assert torch.equal(sd.teacher_q(nets, x), expected)
