"""Bounded real-network tests of masked action fitting and value calibration."""
from datetime import datetime, timedelta, timezone
import importlib.util
import json

import numpy as np
import pytest
import torch


@pytest.fixture(autouse=True)
def one_thread():
    torch.set_num_threads(1)


def module():
    assert importlib.util.find_spec('scripts.student_action_distill') is not None
    from scripts import student_action_distill
    return student_action_distill


def test_masked_loss_ignores_illegal_q_and_independent_row_offsets():
    sd = module()
    mask = torch.tensor([[True, True, False, False, False, False],
                         [True, False, True, False, True, False]])
    teacher = torch.tensor([[1., 3., 100., 0., 0., 0.], [3., 4., 2., 4., 1., 4.]])
    student = teacher.clone()
    student[0, 0] += 2
    student[1, 4] -= 1
    original = sd.action_loss(student, teacher, mask, 2.)
    changed_teacher = teacher + torch.tensor([[17.], [-3.]])
    changed_student = student + torch.tensor([[-9.], [6.]])
    changed_teacher[~mask] = -1e8
    changed_student[~mask] = 1e8
    torch.testing.assert_close(sd.action_loss(changed_student, changed_teacher, mask, 2.), original)
    assert original > 0


def test_one_legal_action_is_exact_finite_zero_and_teacher_has_no_gradient():
    sd = module()
    student = torch.tensor([[1., -9., 300., 100., 2., 4.]], requires_grad=True)
    teacher = torch.tensor([[3., 4., 5., 6., 7., 8.]], requires_grad=True)
    mask = torch.tensor([[False, True, False, False, False, False]])
    loss = sd.action_loss(student, teacher, mask, .001)
    assert loss.item() == 0 and torch.isfinite(loss)
    loss.backward()
    assert teacher.grad is None
    assert torch.equal(student.grad, torch.zeros_like(student))


def test_teacher_scale_uses_train_legal_centered_entries_only():
    sd = module()
    teacher = np.array([[0, 4, 100, 100, 100, 100], [3, 3, 3, 3, 3, 3],
                        [-10000, 10000, 0, 0, 0, 0]], np.float32)
    mask = np.array([[1, 1, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0],
                     [1, 1, 0, 0, 0, 0]], bool)
    train = np.array([True, True, False])
    assert sd.teacher_scale(teacher, mask, train) == pytest.approx(np.sqrt(8/3))
    assert sd.teacher_scale(np.ones((1, 6), np.float32), np.ones((1, 6), bool),
                            np.ones(1, bool)) == .001
    teacher += np.array([[800], [-500], [130]], np.float32)
    teacher[~mask] = 1e6
    assert sd.teacher_scale(teacher, mask, train) == pytest.approx(np.sqrt(8/3))


def test_objective_is_legal_row_mse_plus_teacher_to_student_kl():
    sd = module()
    # Row 1: teacher [-1,1], student [0,0], scale2: MSE=.25;
    # row 2 has exactly one legal action and contributes zero.
    mask = torch.tensor([[True, True, False, False, False, False],
                         [True, False, False, False, False, False]])
    target = torch.tensor([[-1., 1., 0., 0., 0., 0.], [8., 0., 0., 0., 0., 0.]])
    student = torch.zeros_like(target)
    probability = 1/(1+np.exp(1))
    kl = probability*np.log(2*probability)+(1-probability)*np.log(2*(1-probability))
    assert sd.action_loss(student, target, mask, 2.).item() == pytest.approx((.25+kl)/2)


def test_metrics_detect_wrong_legal_ranking_and_label_recorded_rule_overrides():
    sd = module()
    teacher = np.array([[1., 5., 100, 0, 0, 0], [1., 5., 100, 0, 0, 0]], np.float32)
    student = np.array([[5., 1., -100, 0, 0, 0], [1., 5., 100, 0, 0, 0]], np.float32)
    mask = np.array([[1, 1, 0, 0, 0, 0]] * 2, bool)
    metrics = sd.action_metrics(student, teacher, mask, np.array([2, 0], np.int8), student)
    assert metrics['masked_argmax_agreement'] == .5
    assert metrics['legal_regret'] == 2
    assert metrics['legal_q_mse'] == 8
    assert metrics['recorded_collector_final_outside_mask_rate'] == .5
    assert metrics['recorded_collector_rule_override_rate'] == 1


@pytest.mark.parametrize('bad', ['empty_mask', 'nonfinite', 'dtype'])
def test_action_helpers_reject_invalid_data(bad):
    sd = module()
    q = torch.ones(2, 6)
    mask = torch.ones(2, 6, dtype=torch.bool)
    if bad == 'empty_mask':
        mask[0] = False
    elif bad == 'nonfinite':
        q[0, 5] = float('nan')
    else:
        mask = mask.float()
    with pytest.raises(ValueError):
        sd.action_loss(q, q, mask, 1.)


def source_student(tmp_path):
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.model import QNet
    torch.manual_seed(71)
    net = QNet(79, 6, 512, True)
    cfg = AgentConfig(hidden=512).to_dict()
    source = tmp_path / 'start.pth'
    torch.save(dict(q=net.state_dict(), target_q=net.state_dict(), cfg=cfg,
                    ensemble=[], ensemble_dims=[], feature_dim=79, n_actions=6,
                    env_steps=60000, learn_steps=0, distillation_updates=90,
                    distillation_epochs=30, distillation_seed=20261104), source)
    return source


def dataset_fixture(tmp_path, student, name='dataset', *, flipped=False):
    """Two complete seeds/sides, tiny rows; diagnostics deliberately extreme."""
    sd = module()
    out = tmp_path / name
    out.mkdir()
    rng = np.random.default_rng(12)
    plan = [dict(game_index=i, env_seed=865100+i//2, side=i % 2,
                 side_name=f'player_{i % 2}', opponent='solution92', is_train=(i < 2) ^ flipped)
            for i in range(4)]
    q = np.tile(np.array([-2, -1, 0, 1, 2, 3], np.float32), (8, 1))
    q[4:] *= 100
    arrays = dict(s=rng.normal(size=(8, 79)).astype(np.float32),
                  mask=np.ones((8, 6), bool), teacher_q=q,
                  student_q=np.zeros((8, 6), np.float32),
                  final_action=np.zeros(8, np.int8), world_action=np.zeros((8, 3), np.int16),
                  game_index=np.repeat(np.arange(4, dtype=np.int32), 2),
                  env_seed=np.repeat(np.array([865100, 865100, 865101, 865101], np.int64), 2),
                  side=np.repeat(np.array([0, 1, 0, 1], np.int8), 2),
                  env_step=np.tile(np.array([1, 2], np.int16), 4),
                  match_step=np.tile(np.array([1, 2], np.int16), 4),
                  uid=np.zeros(8, np.int8),
                  is_train=np.repeat(np.array([p['is_train'] for p in plan], bool), 2))
    np.savez(out / 'dataset.npz', **arrays)
    (out / 'games.jsonl').write_text(''.join(json.dumps(dict(p, status='done'))+'\n' for p in plan))
    manifest = dict(schema_version=1, status='done', teacher_sha256=sd.V14_SHA256,
                    teacher_members=36, student_sha256=sd.sha256(student), game_plan=plan,
                    rows=8, files_sha256={name: sd.sha256(out / name)
                                          for name in ('dataset.npz', 'games.jsonl')})
    (out / 'manifest.json').write_text(json.dumps(manifest))
    (out / 'status.json').write_text(json.dumps(dict(status='done')))
    return out, arrays, manifest


def rewrite_dataset(out, arrays, manifest):
    sd = module()
    np.savez(out / 'dataset.npz', **arrays)
    manifest['files_sha256']['dataset.npz'] = sd.sha256(out / 'dataset.npz')
    (out / 'manifest.json').write_text(json.dumps(manifest))


def test_loader_validates_hash_schema_plan_and_consistent_whole_seed_split(tmp_path):
    sd = module()
    student = source_student(tmp_path)
    a, _, _ = dataset_fixture(tmp_path, student)
    b, _, _ = dataset_fixture(tmp_path, student, 'round2')
    arrays, metadata = sd.load_datasets([a, b])
    assert len(arrays['s']) == 16
    assert arrays['is_train'].sum() == 8
    assert [item['rows'] for item in metadata] == [8, 8]
    c, _, _ = dataset_fixture(tmp_path, student, 'leak', flipped=True)
    with pytest.raises(ValueError, match='split'):
        sd.load_datasets([a, c])


@pytest.mark.parametrize('bad', ['status', 'hash', 'shape', 'dtype', 'empty_mask',
                                 'nonfinite', 'row_plan', 'plan_split', 'teacher', 'members',
                                 'missing_side', 'rows', 'duplicate_row'])
def test_loader_refuses_incomplete_tampered_or_inconsistent_datasets(tmp_path, bad):
    sd = module()
    student = source_student(tmp_path)
    out, arrays, manifest = dataset_fixture(tmp_path, student)
    if bad == 'status':
        (out / 'status.json').write_text('{"status":"incomplete"}')
    elif bad == 'hash':
        (out / 'games.jsonl').write_text('tampered')
    elif bad == 'shape':
        arrays['s'] = arrays['s'][:, :78]
    elif bad == 'dtype':
        arrays['mask'] = arrays['mask'].astype(np.int8)
    elif bad == 'empty_mask':
        arrays['mask'][0] = False
    elif bad == 'nonfinite':
        arrays['student_q'][-1, 5] = np.nan
    elif bad == 'row_plan':
        arrays['env_seed'][0] += 7
    elif bad == 'plan_split':
        manifest['game_plan'][1]['is_train'] = False
    elif bad == 'teacher':
        manifest['teacher_sha256'] = '0'*64
    elif bad == 'members':
        manifest['teacher_members'] = 35
    elif bad == 'missing_side':
        manifest['game_plan'] = manifest['game_plan'][:-1]
    elif bad == 'rows':
        manifest['rows'] = 100
    elif bad == 'duplicate_row':
        for column in ('env_step', 'match_step'):
            arrays[column][1] = arrays[column][0]
    if bad not in ('status', 'hash'):
        rewrite_dataset(out, arrays, manifest)
    with pytest.raises(ValueError):
        sd.load_datasets([out])


def test_complete_run_has_exact_schedule_frozen_calibration_and_compatible_export(tmp_path):
    sd = module()
    student = source_student(tmp_path)
    data, _, _ = dataset_fixture(tmp_path, student)
    before = sd.sha256(student)
    out = tmp_path / 'fit'
    result = sd.run_distillation(student, [data], out, datetime.now(timezone.utc)+timedelta(minutes=2))
    assert result['status'] == 'complete'
    assert result['action_epochs_completed'] == 30
    assert result['value_epochs_completed'] == 5
    assert result['action_updates'] == 30 and result['value_updates'] == 5
    assert result['updates'] == 35 and result['cumulative_updates'] == 125
    assert result['training_rows_seen'] == 140
    assert result['calibration']['body_adv_unchanged'] is True
    assert result['calibration']['non_tie_pair_rank_changes'] == 0
    assert result['reload_exact'] is True
    assert result['scale'] == pytest.approx(np.sqrt(35/12))
    assert result['inputs_before'] == result['inputs_after']
    assert result['sources_before'] == result['sources_after']
    assert sd.sha256(student) == before
    cp = torch.load(out / 'weights/agent.pth', weights_only=True)
    assert set(cp) == {'q', 'target_q', 'cfg', 'feature_dim', 'n_actions', 'ensemble',
                       'ensemble_dims', 'env_steps', 'learn_steps',
                       'distillation_updates', 'distillation_epochs', 'distillation_seed'}
    assert cp['distillation_updates'] == 125
    from scripts.student_reward_train import _student
    _student(out / 'weights/agent.pth')
    from agents.sherlock.main import Agent_x
    loaded = Agent_x('player_0', agent_path=str(out / 'weights/agent.pth'), train=False)
    assert loaded.extra_q == []
    assert all(torch.equal(value, cp['target_q'][key]) for key, value in cp['q'].items())
    metrics = json.loads((out / 'metrics.json').read_text())
    assert metrics['before']['train']['rows'] == metrics['after']['train']['rows'] == 4
    assert metrics['before']['diagnostic']['rows'] == metrics['after']['diagnostic']['rows'] == 4
    assert metrics['after']['train']['legal_mean_q_mse'] < metrics['after_action']['train']['legal_mean_q_mse']


def test_deadline_never_exports_partial_checkpoint(tmp_path):
    sd = module()
    student = source_student(tmp_path)
    data, _, _ = dataset_fixture(tmp_path, student)
    out = tmp_path / 'partial'
    result = sd.run_distillation(student, [data], out, datetime.now(timezone.utc)-timedelta(seconds=1))
    assert result['status'] == 'incomplete'
    assert not (out / 'weights/agent.pth').exists()


def test_output_protection_and_collecting_student_identity(tmp_path):
    sd = module()
    student = source_student(tmp_path)
    data, _, manifest = dataset_fixture(tmp_path, student)
    deadline = datetime.now(timezone.utc)+timedelta(minutes=2)
    for out in (data, sd.ROOT / 'Gruppe15/new-fit', tmp_path):
        with pytest.raises(ValueError):
            sd.run_distillation(student, [data], out, deadline)
    manifest['student_sha256'] = '0'*64
    (data / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='student'):
        sd.run_distillation(student, [data], tmp_path / 'mismatch', deadline)
    assert not (tmp_path / 'mismatch/weights/agent.pth').exists()


@pytest.mark.parametrize('base', ['current', 'primary', 'historical'])
def test_output_guard_rejects_packaged_submission_paths_before_any_creation(base, monkeypatch):
    sd = module()
    from pathlib import Path
    roots = dict(current=sd.ROOT,
                 primary=Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15'),
                 historical=Path('/Users/moayedshawesh/Desktop/KI/sherlock-november-followup'))

    def creation_is_a_bug(*args, **kwargs):
        pytest.fail('Protected submission path reached directory creation')

    monkeypatch.setattr(Path, 'mkdir', creation_is_a_bug)
    with pytest.raises(ValueError, match='geschuetzt|protected'):
        sd.reserve_output(roots[base]/'agents/Gruppe15/action-fit-regression', [])


def test_output_guard_rejects_symlink_alias_of_packaged_submission(tmp_path):
    sd = module()
    from pathlib import Path
    # A temporary ancestor alias points at the existing repository. Creating
    # the alias itself is harmless; no directory under agents is touched.
    alias = tmp_path/'repository-alias'
    alias.symlink_to(sd.ROOT, target_is_directory=True)
    with pytest.raises(ValueError, match='geschuetzt|protected'):
        sd.reserve_output(alias/'agents/Gruppe15/action-fit-regression', [])


def test_diagnostic_labels_never_affect_scale_or_either_training_phase(tmp_path):
    sd = module()
    student = source_student(tmp_path)
    a, _, _ = dataset_fixture(tmp_path, student)
    b, arrays, manifest = dataset_fixture(tmp_path, student, 'other-diagnostics')
    arrays['teacher_q'][~arrays['is_train']] *= -1000
    rewrite_dataset(b, arrays, manifest)
    deadline = datetime.now(timezone.utc)+timedelta(minutes=2)
    first = sd.run_distillation(student, [a], tmp_path/'first', deadline)
    second = sd.run_distillation(student, [b], tmp_path/'second', deadline)
    cp_a = torch.load(tmp_path/'first/weights/agent.pth', weights_only=True)
    cp_b = torch.load(tmp_path/'second/weights/agent.pth', weights_only=True)
    assert first['scale'] == second['scale']
    assert all(torch.equal(value, cp_b['q'][key]) for key, value in cp_a['q'].items())


def test_interrupted_value_phase_refuses_final_checkpoint_after_complete_action_phase(tmp_path, monkeypatch):
    sd = module()
    student = source_student(tmp_path)
    data, _, _ = dataset_fixture(tmp_path, student)
    out = tmp_path/'interrupted'
    real_datetime = datetime
    deadline = real_datetime.now(timezone.utc)+timedelta(minutes=2)

    class DeadlineDuringCalibration(real_datetime):
        @classmethod
        def now(cls, tz=None):
            if (out/'status.json').exists():
                status = json.loads((out/'status.json').read_text())
                if status['value_epochs_completed'] >= 1:
                    return deadline+timedelta(seconds=1)
            return real_datetime.now(tz)

    # The fake clock keeps datetime type checking valid while crossing the
    # deadline at the first completed value epoch.
    monkeypatch.setattr(sd, 'datetime', DeadlineDuringCalibration)
    deadline = DeadlineDuringCalibration.fromisoformat(deadline.isoformat())
    result = sd.run_distillation(student, [data], out, deadline)
    assert result['status'] == 'incomplete'
    assert result['action_epochs_completed'] == 30
    assert result['value_epochs_completed'] == 1
    assert result['updates'] == 31
    assert not list((out/'weights').glob('*.pth'))


def test_calibration_checks_reject_body_mutation_and_non_tie_rank_changes():
    sd = module()
    from agents.sherlock.model import QNet
    net = QNet(79, 6, 512, True)
    frozen = {name: value.clone() for name, value in net.state_dict().items()
              if name.startswith(('body.', 'adv.'))}
    before = np.array([[1, 2, 3, 4, 5, 6]], np.float32)
    mask = np.ones((1, 6), bool)
    sd._calibration_checks(net, frozen, before, before+4, mask)
    with pytest.raises(ValueError, match='calibration'):
        sd._calibration_checks(net, frozen, before, before[:, ::-1], mask)
    with torch.no_grad():
        net.body[0].weight[0, 0] += 1
    with pytest.raises(ValueError, match='calibration'):
        sd._calibration_checks(net, frozen, before, before, mask)
