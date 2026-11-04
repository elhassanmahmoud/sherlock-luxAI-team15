"""Tiny real-QNet checks for excluded-row retention diagnostics."""
import importlib.util
import json

import numpy as np
import pytest
import torch

from agents.sherlock.model import QNet
from scripts.student_distill import V14_SHA256, sha256


@pytest.fixture(autouse=True)
def one_thread():
    torch.set_num_threads(1)


def module():
    assert importlib.util.find_spec('scripts.student_retention') is not None
    from scripts import student_retention
    return student_retention


def checkpoint(tmp_path, name='exact', *, reverse=False, dueling=True):
    net = QNet(79, 6, hidden=8, dueling=dueling)
    with torch.no_grad():
        for parameter in net.parameters():
            parameter.zero_()
        bias = net.adv[-1].bias if dueling else net.head.bias
        bias.copy_(torch.tensor([5., 3., 1., -1., -3., -5.]) * (-1 if reverse else 1))
    path = tmp_path / f'{name}.pth'
    # Sparse config is a supported legacy format; width is inferred from q.
    torch.save(dict(q=net.state_dict(), cfg={'dueling': dueling},
                    feature_dim=79, n_actions=6, ensemble=[], ensemble_dims=[]), path)
    return path


def dataset(tmp_path):
    out = tmp_path / 'collection'
    out.mkdir()
    plan = [dict(game_index=i, env_seed=865100+i//2, side=i % 2,
                 side_name=f'player_{i % 2}', opponent='solution92', is_train=i < 2)
            for i in range(4)]
    q = np.tile(np.array([5, 3, 1, -1, -3, -5], np.float32), (8, 1))
    q[:4] *= -100  # Train rows would expose accidental split mixing.
    arrays = dict(s=np.zeros((8, 79), np.float32), mask=np.ones((8, 6), bool),
                  teacher_q=q, student_q=np.zeros((8, 6), np.float32),
                  final_action=np.zeros(8, np.int8), world_action=np.zeros((8, 3), np.int16),
                  game_index=np.repeat(np.arange(4, dtype=np.int32), 2),
                  env_seed=np.repeat(np.array([865100, 865100, 865101, 865101], np.int64), 2),
                  side=np.repeat(np.array([0, 1, 0, 1], np.int8), 2),
                  env_step=np.tile(np.array([1, 2], np.int16), 4),
                  match_step=np.tile(np.array([1, 2], np.int16), 4), uid=np.zeros(8, np.int8),
                  is_train=np.repeat(np.array([True, True, False, False]), 2))
    manifest = dict(schema_version=1, status='done', teacher_sha256=V14_SHA256,
                    teacher_members=36, student_sha256='a'*64, game_plan=plan, rows=8)
    (out / 'games.jsonl').write_text(''.join(json.dumps(dict(p, status='done'))+'\n' for p in plan))
    (out / 'status.json').write_text('{"status":"done"}')
    rewrite_dataset(out, arrays, manifest)
    return out, arrays, manifest


def rewrite_dataset(out, arrays, manifest):
    np.savez(out / 'dataset.npz', **arrays)
    manifest['files_sha256'] = {name: sha256(out / name) for name in ('dataset.npz', 'games.jsonl')}
    (out / 'manifest.json').write_text(json.dumps(manifest))


def test_exact_teacher_only_scores_excluded_rows_and_writes_provenance(tmp_path):
    m = module()
    source = checkpoint(tmp_path)
    data, arrays, _ = dataset(tmp_path)
    before = sha256(source)
    report = m.run_retention([data], {'A2': source}, tmp_path / 'report', batch_size=3)
    assert report['status'] == 'complete'
    assert report['split']['diagnostic_rows'] == 4
    assert report['split']['excluded_training_rows'] == 4
    assert report['split']['diagnostic_seeds'] == [865101]
    metrics = report['models']['A2']['metrics']
    assert metrics['rows'] == 4
    assert metrics['masked_argmax_agreement'] == 1
    assert metrics['legal_regret'] == metrics['centered_legal_q_mse'] == 0
    assert metrics['legal_q_mean'] == 0
    assert metrics['legal_q_std'] == pytest.approx(np.std(arrays['teacher_q'][4:]))
    assert metrics['top_two_gap_mean'] == 2
    assert report['teacher_metrics']['top_two_gap_mean'] == 2
    assert report['models']['A2']['sha256'] == before == sha256(source)
    assert len(report['inputs_before']) == 5  # checkpoint + complete collector package
    assert report['inputs_before'] == report['inputs_after']
    assert report['sources_before'] == report['sources_after']
    assert report['runtime']['torch_threads'] == 1
    assert json.loads((tmp_path / 'report/report.json').read_text()) == report


def test_independent_models_batched_nograd_and_rng_unchanged(tmp_path, monkeypatch):
    m = module()
    first, second = checkpoint(tmp_path), checkpoint(tmp_path, 'wrong', reverse=True)
    data, _, _ = dataset(tmp_path)
    original = QNet.forward
    calls = []
    def observed(net, rows):
        assert not torch.is_grad_enabled()
        assert not net.training
        calls.append(len(rows))
        return original(net, rows)
    monkeypatch.setattr(QNet, 'forward', observed)
    rng = torch.random.get_rng_state().clone()
    report = m.run_retention([data], {'exact': first, 'wrong': second}, tmp_path / 'report', batch_size=3)
    assert torch.equal(torch.random.get_rng_state(), rng)
    assert calls == [3, 1, 3, 1]
    assert report['models']['exact']['metrics']['masked_argmax_agreement'] == 1
    assert report['models']['wrong']['metrics']['masked_argmax_agreement'] == 0
    assert report['models']['wrong']['metrics']['legal_regret'] == 10
    assert report['models']['wrong']['metrics']['centered_legal_q_mse'] > 0


@pytest.mark.parametrize('bad', ['empty', 'dtype', 'shape'])
def test_malformed_masks_rejected_by_validated_loader(tmp_path, bad):
    m = module()
    source = checkpoint(tmp_path)
    data, arrays, manifest = dataset(tmp_path)
    if bad == 'empty':
        arrays['mask'][4] = False
    elif bad == 'dtype':
        arrays['mask'] = arrays['mask'].astype(np.int8)
    else:
        arrays['mask'] = arrays['mask'][:, :5]
    rewrite_dataset(data, arrays, manifest)
    with pytest.raises(ValueError, match='mask'):
        m.run_retention([data], {'A2': source}, tmp_path / 'report')
    assert not (tmp_path / 'report/report.json').exists()


@pytest.mark.parametrize('dueling', [True, False])
def test_checkpoint_infers_architecture_and_checks_config(tmp_path, dueling):
    m = module()
    source = checkpoint(tmp_path, dueling=dueling)
    net, metadata = m.load_model(source)
    assert net.feat_dim == 79 and not net.training
    assert metadata['hidden'] == 8 and metadata['dueling'] is dueling
    cp = torch.load(source, weights_only=True)
    cp['cfg']['hidden'] = 99
    torch.save(cp, source)
    with pytest.raises(ValueError, match='config|hidden'):
        m.load_model(source)


@pytest.mark.parametrize('bad', ['nonfinite', 'ensemble', 'feature_dim', 'actions', 'shape'])
def test_invalid_checkpoints_rejected(tmp_path, bad):
    m = module()
    source = checkpoint(tmp_path)
    cp = torch.load(source, weights_only=True)
    if bad == 'nonfinite':
        cp['q']['body.0.bias'][0] = float('nan')
    elif bad == 'ensemble':
        cp['ensemble'] = [cp['q']]
        cp['ensemble_dims'] = [79]
    elif bad == 'feature_dim':
        cp['feature_dim'] = 78
    elif bad == 'actions':
        cp['n_actions'] = 7
    else:
        cp['q']['adv.2.weight'] = torch.zeros(5, 128)
    torch.save(cp, source)
    with pytest.raises(ValueError):
        m.load_model(source)


def test_nonfinite_inference_does_not_publish_report(tmp_path, monkeypatch):
    m = module()
    source = checkpoint(tmp_path)
    data, _, _ = dataset(tmp_path)
    monkeypatch.setattr(QNet, 'forward', lambda net, x: torch.full((len(x), 6), float('inf')))
    with pytest.raises(ValueError, match='finite'):
        m.run_retention([data], {'A2': source}, tmp_path / 'report')
    assert not (tmp_path / 'report/report.json').exists()


def test_single_legal_action_has_no_top_two_gap_and_illegal_values_ignored():
    m = module()
    q = np.array([[7., 1000, -2000, 90, 60, 30]], np.float32)
    mask = np.array([[True, False, False, False, False, False]])
    metrics = m.q_summary(q, mask)
    assert metrics['legal_q_mean'] == 7 and metrics['legal_q_std'] == 0
    assert metrics['top_two_gap_rows'] == 0
    assert metrics['top_two_gap_mean'] is None


@pytest.mark.parametrize('bad', ['empty', 'dtype', 'shape', 'nonfinite'])
def test_q_summary_rejects_bad_q_or_mask(bad):
    m = module()
    q, mask = np.ones((2, 6), np.float32), np.ones((2, 6), bool)
    if bad == 'empty':
        mask[0] = False
    elif bad == 'dtype':
        mask = mask.astype(int)
    elif bad == 'shape':
        mask = mask[:, :5]
    else:
        q[0, 0] = np.nan
    with pytest.raises(ValueError):
        m.q_summary(q, mask)


@pytest.mark.parametrize('occupied', [True, False])
def test_output_guard_rejects_occupied_and_protected_before_creation(tmp_path, occupied):
    m = module()
    data, _, _ = dataset(tmp_path)
    source = checkpoint(tmp_path)
    out = tmp_path / 'occupied' if occupied else m.ROOT / 'agents/Gruppe15/retention-forbidden'
    if occupied:
        out.mkdir()
        (out / 'keep').write_text('untouched')
    with pytest.raises(ValueError, match='occupied|geschuetzt|protected'):
        m.run_retention([data], {'A2': source}, out)
    if occupied:
        assert (out / 'keep').read_text() == 'untouched'
    else:
        assert not out.exists()


def test_model_cli_rejects_duplicate_or_missing_names_and_bad_batch(tmp_path):
    m = module()
    assert m.parse_models(['A2=/tmp/a.pth', 'C=/tmp/b.pth']) == {'A2': '/tmp/a.pth', 'C': '/tmp/b.pth'}
    for entries in (['A2=/a', 'A2=/b'], ['=/a'], ['A2='], ['bad']):
        with pytest.raises(ValueError):
            m.parse_models(entries)
    with pytest.raises(ValueError, match='batch'):
        m.run_retention([], {}, tmp_path / 'report', batch_size=0)
    assert not (tmp_path / 'report').exists()


def test_cli_writes_reusable_named_role_report(tmp_path, capsys):
    m = module()
    source = checkpoint(tmp_path)
    data, _, _ = dataset(tmp_path)
    out = tmp_path / 'cli-report'
    m.main(['--datasets', str(data), '--model', f'A2={source}',
            '--out', str(out), '--batch-size', '3'])
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'complete' and result['diagnostic_rows'] == 4
    assert result['models'] == ['A2']
    assert result['report'] == str(out / 'report.json')
    report = json.loads((out / 'report.json').read_text())
    assert report['datasets'][0]['diagnostic_rows'] == 4


def test_changed_input_is_detected_before_complete_report(tmp_path, monkeypatch):
    m = module()
    source = checkpoint(tmp_path)
    data, _, _ = dataset(tmp_path)
    original = m._predict
    def changed_input(*args):
        result = original(*args)
        with source.open('ab') as handle:
            handle.write(b'changed')
        return result
    monkeypatch.setattr(m, '_predict', changed_input)
    with pytest.raises(ValueError, match='changed'):
        m.run_retention([data], {'A2': source}, tmp_path / 'report')
    assert not (tmp_path / 'report/report.json').exists()


def test_two_legal_actions_ignore_illegal_high_q_for_top_two_gap():
    m = module()
    q = np.array([[1., 5., 1000, 1000, 1000, 1000],
                  [7., 7., 1000, 1000, 1000, 1000]], np.float32)
    mask = np.array([[True, True, False, False, False, False]] * 2)
    metrics = m.q_summary(q, mask)
    assert metrics['top_two_gap_rows'] == 2
    assert metrics['top_two_gap_mean'] == 2
    assert metrics['top_two_gap_std'] == 2
    assert metrics['top_two_gap_zero_rate'] == .5
    assert metrics['legal_q_mean'] == 5
    assert metrics['mean_row_legal_q_std'] == 1


@pytest.mark.parametrize('alias', [False, True])
def test_output_inside_input_archive_is_rejected_without_mutation(tmp_path, alias):
    m = module()
    source = checkpoint(tmp_path)
    data, _, _ = dataset(tmp_path)
    before = {p.name: sha256(p) for p in data.iterdir()}
    parent = data
    if alias:
        parent = tmp_path / 'collector-alias'
        parent.symlink_to(data, target_is_directory=True)
    out = parent / 'retention-report'
    with pytest.raises(ValueError, match='dataset|archive'):
        m.run_retention([data], {'A2': source}, out)
    assert not out.exists()
    assert {p.name: sha256(p) for p in data.iterdir()} == before
