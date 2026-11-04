"""Training adapter checks; synthetic replay only, no rollout claims."""
import copy
import json
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x
from scripts import experiment


def module():
    from scripts import student_anchor_train
    return student_anchor_train


def agent():
    torch.set_num_threads(1)
    torch.manual_seed(10)
    a = Agent_x('player_0', cfg=AgentConfig(hidden=8, batch_size=4,
                buffer_capacity=16, target_update_every=2), seed=91)
    rng = np.random.default_rng(40)
    for i in range(10):
        a.buffer.push(rng.normal(size=79), i % 6, i / 10,
                      rng.normal(size=79), i % 2, np.array([1, 1, 0, 1, 0, 1], bool))
    return a


def data():
    m = module()
    rng = np.random.default_rng(30)
    arrays = dict(s=rng.normal(size=(9, 79)).astype('float32'),
                  teacher_q=rng.normal(size=(9, 6)).astype('float32'),
                  mask=np.tile(np.array([1, 1, 0, 1, 0, 1], bool), (9, 1)),
                  is_train=np.array([1, 0, 1, 1, 0, 1, 1, 0, 1], bool))
    return m.AnchorData(arrays, 2.)


@pytest.mark.parametrize('double', [True, False])
def test_zero_weight_matches_original_parameters_optimizer_target_and_rng(double):
    m = module()
    original = agent()
    original.cfg.double_dqn = double
    wrapped = copy.deepcopy(original)
    sampler = data()
    before_data_rng = experiment.state_sha256(np.random.default_rng(20261129).bit_generator.state)
    with m.attach_anchor(wrapped, sampler, 25, weight=0.) as proof:
        for _ in range(3):
            original._learn()
            wrapped._learn()
        assert proof['updates'] == 3
        assert proof['sample_count'] == 0
        assert proof['sampler_rng_sha256'] == before_data_rng
    assert '_learn' not in vars(wrapped)
    for name in ('q', 'target_q', 'opt'):
        assert experiment.state_sha256(getattr(original, name).state_dict()) == experiment.state_sha256(getattr(wrapped, name).state_dict())
    assert original.learn_steps == wrapped.learn_steps == 3
    assert original.recent_losses == wrapped.recent_losses
    assert experiment.state_sha256(original.rng.bit_generator.state) == experiment.state_sha256(wrapped.rng.bit_generator.state)


def test_anchor_has_one_optimizer_step_own_rng_and_no_diagnostic_samples():
    m = module()
    baseline = agent()
    anchored = copy.deepcopy(baseline)
    rows, indices = [], []
    with m.attach_anchor(anchored, data(), 25, emit=lambda row, ix: (rows.append(row), indices.append(ix.copy()))) as proof:
        for _ in range(3):
            baseline._learn()
            anchored._learn()
        assert proof['updates'] == 3 and proof['sample_count'] == 768
    assert experiment.state_sha256(baseline.rng.bit_generator.state) == experiment.state_sha256(anchored.rng.bit_generator.state)
    assert all(torch.equal(state['step'], torch.tensor(3.)) for state in anchored.opt.state.values())
    assert not torch.equal(next(baseline.q.parameters()), next(anchored.q.parameters()))
    assert set(np.concatenate(indices)) <= {0, 2, 3, 5, 6, 8}
    expected = np.random.default_rng(20261129).choice(np.array([0, 2, 3, 5, 6, 8]), size=768, replace=True)
    assert np.array_equal(np.concatenate(indices), expected)
    for row in rows:
        assert row['total_loss'] == pytest.approx(row['td_loss'] + .1 * row['anchor_loss'])
        assert row['anchor_output_gradient_norm'] > 0
        assert row['optimizer_steps'] == 1


def test_anchor_loss_only_changes_student_legal_centered_preferences():
    m = module()
    prediction = torch.tensor([[1., 3., 5., 7., 9., 11.]], requires_grad=True)
    teacher = torch.tensor([[2., 0., 8., 4., 2., 12.]], requires_grad=True)
    mask = torch.tensor([[True, True, False, False, False, False]])
    loss = m.action_loss(prediction, teacher, mask, 2.)
    loss.backward()
    assert teacher.grad is None
    assert torch.count_nonzero(prediction.grad[:, 2:]) == 0
    assert prediction.grad.sum().item() == pytest.approx(0., abs=1e-7)
    assert m.action_loss(prediction.detach() + 100, teacher, mask, 2.).item() == pytest.approx(loss.item())
    single = torch.tensor([[True, False, False, False, False, False]])
    assert m.action_loss(prediction, teacher, single, 2.).item() == 0.


def test_adapter_restores_prior_binding_after_exception():
    m = module()
    a = agent()
    prior = a._learn
    a._learn = prior
    with pytest.raises(RuntimeError, match='stop'):
        with m.attach_anchor(a, data(), 25):
            a._learn()
            raise RuntimeError('stop')
    assert vars(a)['_learn'] is prior


@pytest.mark.parametrize('bad', [True, 24, 27, 25., '25', None])
def test_invalid_seed_refused_before_preparing_output(tmp_path, bad):
    m = module()
    with pytest.raises(ValueError, match='seed'):
        m.prepare(tmp_path / 'missing', [], tmp_path / 'out', bad)
    assert not (tmp_path / 'out').exists()


@pytest.fixture
def prepared_inputs(tmp_path, monkeypatch):
    m = module()
    from tests.test_student_action_distill import source_student, dataset_fixture
    student = source_student(tmp_path)
    first, _, _ = dataset_fixture(tmp_path, student, 'r1')
    second, _, _ = dataset_fixture(tmp_path, student, 'r2')
    monkeypatch.setattr(m, 'A2_SHA256', engine_hash(student))
    monkeypatch.setattr(m, 'DATASET_SHA256', tuple(engine_hash(p / 'dataset.npz') for p in (first, second)), raising=False)
    monkeypatch.setattr(m, 'TRAIN_ROWS', 8)
    monkeypatch.setattr(m, 'EXCLUDED_ROWS', 8)
    monkeypatch.setattr(m, 'FIXED_SCALE', np.sqrt(35 / 12), raising=False)
    return m, student, [first, second]


def engine_hash(path):
    from scripts.student_reward_train import file_sha256
    return file_sha256(path)


def test_preparation_has_distinct_public_arms_and_original_control_configs(prepared_inputs, tmp_path):
    m, student, datasets = prepared_inputs
    prepared = tmp_path / 'prepared'
    manifest = m.prepare(student, datasets, prepared, 25)
    assert manifest['arms']['control']['weight'] == 0.
    assert manifest['arms']['anchor']['weight'] == .1
    assert manifest['arms']['control']['engine_prepared'] != manifest['arms']['anchor']['engine_prepared']
    for arm in ('control', 'anchor'):
        checked, entry, anchor = m.check_prepared(prepared, arm)
        assert checked == manifest
        assert entry['engine_arm'] == 'control'
        assert entry['config'] == manifest['arms']['control']['config']
        assert entry['config']['w_sap_hit'] == .3
        assert len(anchor.indices) == 8
    assert manifest['dataset_contract']['excluded_rows'] == 8
    assert not (prepared / 'audits').exists()


@pytest.mark.parametrize('where', ['source', 'dataset', 'script_pin', 'arm_weight', 'engine_init'])
def test_prepared_contract_refuses_mutation(prepared_inputs, tmp_path, where):
    m, student, datasets = prepared_inputs
    prepared = tmp_path / 'prepared'
    manifest = m.prepare(student, datasets, prepared, 26)
    if where == 'source':
        with student.open('ab') as f:
            f.write(b'changed')
    elif where == 'dataset':
        with (datasets[0] / 'dataset.npz').open('ab') as f:
            f.write(b'changed')
    elif where == 'engine_init':
        with (prepared / 'engine/anchor/init/control/weights/agent.pth').open('ab') as f:
            f.write(b'changed')
    else:
        if where == 'script_pin':
            manifest['pins']['code']['scripts/student_anchor_train.py'] = '0' * 64
        else:
            manifest['arms']['anchor']['weight'] = 0.
        (prepared / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='changed|hash|contract|differ'):
        m.check_prepared(prepared, 'control')


def test_protected_alias_and_occupied_output_refused(prepared_inputs, tmp_path, monkeypatch):
    m, student, datasets = prepared_inputs
    protected = tmp_path / 'protected'
    protected.mkdir()
    alias = tmp_path / 'alias'
    alias.symlink_to(protected, target_is_directory=True)
    from scripts import student_reward_train
    monkeypatch.setattr(student_reward_train, 'PROTECTED_DIRS', (protected,))
    with pytest.raises(ValueError):
        m.prepare(student, datasets, alias / 'forbidden', 25)
    occupied = tmp_path / 'occupied'
    occupied.mkdir()
    with pytest.raises((ValueError, FileExistsError)):
        m.prepare(student, datasets, occupied, 25)
    assert not (protected / 'forbidden').exists()


def test_incomplete_original_run_restores_constructor_and_instance_hooks(prepared_inputs, tmp_path, monkeypatch):
    m, student, datasets = prepared_inputs
    from scripts import finetune
    prepared = tmp_path / 'prepared'
    m.prepare(student, datasets, prepared, 25)
    original_constructor = finetune.Learners
    original_main = finetune.main
    constructed = []
    def fail_main():
        import shutil
        destination = finetune.RUNS / 'control'
        shutil.copytree(prepared / 'engine/anchor/init/control', destination)
        learners = finetune.Learners(m.engine.VARIANT, destination, 25, load=True)
        constructed.append(learners.agents['player_0'])
        raise RuntimeError('synthetic rollout failure')
    monkeypatch.setattr(finetune, 'main', fail_main)
    with pytest.raises(RuntimeError, match='synthetic rollout'):
        m.run_arm(prepared, 'anchor', (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat())
    assert finetune.Learners is original_constructor
    assert all('_learn' not in vars(a) and 'save_agent' not in vars(a) for a in constructed)
    assert not (prepared / 'audits/anchor/anchor_receipt.json').exists()
    assert json.loads((prepared / 'audits/anchor/status.json').read_text())['status'] == 'incomplete'
    with pytest.raises(ValueError, match='Incomplete|incomplete'):
        m.validate(prepared, 'anchor')


@pytest.mark.parametrize('weight', [0., .1])
def test_actual_update_sidecars_verify_samples_losses_rng_and_reject_rehashed_lies(tmp_path, monkeypatch, weight):
    m = module()
    monkeypatch.setattr(m, 'UPDATES', 3)
    a, anchor = agent(), data()
    audit = tmp_path / 'audit'
    audit.mkdir()
    with (audit / 'updates.jsonl').open('w') as metrics, (audit / 'samples.u32').open('wb') as samples:
        def emit(row, ix):
            metrics.write(json.dumps(row) + '\n')
            samples.write(ix.tobytes())
        with m.attach_anchor(a, anchor, 25, weight, emit) as proof:
            for _ in range(3):
                a._learn()
    (audit / 'summary.json').write_text(json.dumps(proof))
    manifest, entry = dict(run_seed=25), dict(weight=weight)
    m._validate_updates(audit, manifest, entry, anchor)
    rows = [json.loads(line) for line in (audit / 'updates.jsonl').read_text().splitlines()]
    rows[0]['td_loss'] += .5
    (audit / 'updates.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
    with pytest.raises(ValueError, match='loss|evidence'):
        m._validate_updates(audit, manifest, entry, anchor)


def test_sidecar_validation_refuses_diagnostic_or_wrong_random_samples(tmp_path, monkeypatch):
    m = module()
    monkeypatch.setattr(m, 'UPDATES', 1)
    a, anchor = agent(), data()
    rows, selected = [], []
    with m.attach_anchor(a, anchor, 25, emit=lambda row, ix: (rows.append(row), selected.append(ix.copy()))) as proof:
        a._learn()
    selected[0][0] = 1  # held-out row
    rows[0]['sample_sha256'] = __import__('hashlib').sha256(selected[0].tobytes()).hexdigest()
    (tmp_path / 'updates.jsonl').write_text(json.dumps(rows[0])+'\n')
    (tmp_path / 'samples.u32').write_bytes(selected[0].tobytes())
    (tmp_path / 'summary.json').write_text(json.dumps(proof))
    with pytest.raises(ValueError, match='sample|training'):
        m._validate_updates(tmp_path, dict(run_seed=25), dict(weight=.1), anchor)


def test_cli_validate_is_read_only_and_refuses_missing_completion(prepared_inputs, tmp_path, monkeypatch):
    m, student, datasets = prepared_inputs
    prepared = tmp_path / 'prepared'
    m.prepare(student, datasets, prepared, 25)
    before = {str(p): engine_hash(p) for p in prepared.rglob('*') if p.is_file()}
    with pytest.raises(ValueError, match='Incomplete|incomplete'):
        m.main(['validate', '--prepared', str(prepared), '--arm', 'anchor'])
    assert before == {str(p): engine_hash(p) for p in prepared.rglob('*') if p.is_file()}


def test_prefill_audit_hashes_actual_replay_before_first_learning_write_and_restores():
    m = module()
    a = agent()
    a.buffer.size = a.buffer.pos = 0
    a.learn_enabled = False
    with m.prefill_replay_audit(a) as proof:
        a.buffer.push(np.ones(79), 2, -.5, np.zeros(79), False, np.ones(6, bool))
        a.learn_enabled = True
        a.buffer.push(np.ones(79) * 2, 3, 9., np.zeros(79), True, np.ones(6, bool))
    assert 'push' not in vars(a.buffer)
    assert proof['size'] == 1 and proof['pos'] == 1
    expected = experiment.state_sha256(dict(s=np.ones((1, 79), np.float32),
        a=np.array([2], np.int64), r=np.array([-.5], np.float32),
        ns=np.zeros((1, 79), np.float32), done=np.array([0], np.float32),
        mask=np.ones((1, 6), bool)))
    assert proof['content_sha256'] == expected


def test_prefill_audit_exception_restores_push():
    m = module()
    a = agent()
    with pytest.raises(RuntimeError, match='stop'):
        with m.prefill_replay_audit(a):
            raise RuntimeError('stop')
    assert 'push' not in vars(a.buffer)


def test_output_inside_dataset_is_refused_without_writes(prepared_inputs):
    m, student, datasets = prepared_inputs
    out = datasets[0] / 'new-output'
    with pytest.raises(ValueError, match='input|dataset'):
        m.prepare(student, datasets, out, 25)
    assert not out.exists()


def test_audit_alias_cannot_escape_prepared_directory(prepared_inputs, tmp_path, monkeypatch):
    m, student, datasets = prepared_inputs
    prepared = tmp_path / 'prepared'
    m.prepare(student, datasets, prepared, 25)
    (prepared / 'audits').symlink_to(datasets[0], target_is_directory=True)
    def forbidden_engine(*args, **kwargs):
        raise AssertionError('Output guards must reject before invoking any engine')
    from scripts import finetune
    monkeypatch.setattr(finetune, 'main', forbidden_engine)
    monkeypatch.setattr(m.engine, 'run_arm', forbidden_engine)
    with pytest.raises(ValueError, match='escape|outside|alias'):
        m.run_arm(prepared, 'anchor', (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat())
    assert not (datasets[0] / 'anchor').exists()


@pytest.mark.parametrize('wrong_csv', [False, True])
def test_outer_completion_publishes_rounded_csv_and_rejects_material_difference(tmp_path, monkeypatch, wrong_csv):
    """Real outer validation/publication; mocked engine and update-evidence boundaries, zero games."""
    from types import SimpleNamespace
    from scripts import finetune
    m = module()
    prepared = tmp_path / 'prepared'
    nested = prepared / 'engine/control'
    run = nested / 'runs/control'
    prepared.mkdir()
    (prepared / 'manifest.json').write_text('{"synthetic_outer_boundary": true}')
    manifest = dict(run_seed=25)
    entry = dict(engine_prepared=str(nested), weight=0.)
    anchor = data()
    monkeypatch.setattr(m, 'check_prepared', lambda *args: (manifest, entry, anchor))
    monkeypatch.setattr(finetune, 'main', lambda: pytest.fail('No real engine entrypoint allowed'))
    constructed = []
    def constructor(*args, **kwargs):
        a = agent()
        a.buffer.size = a.buffer.pos = 0
        constructed.append(a)
        return SimpleNamespace(agents={'player_0': a, 'player_1': a})
    monkeypatch.setattr(finetune, 'Learners', constructor)
    # The independently tested update-sidecar boundary supplies 160 groups of
    # 150 full-precision losses; outer CSV matching and publication remain real.
    losses = [0.123456789 if game % 2 == 0 else 0.987654321 for game in range(160)]
    updates = [dict(total_loss=value) for value in losses for _ in range(150)]
    monkeypatch.setattr(m, '_validate_updates', lambda *args: updates)
    inner = {}
    def synthetic_engine(*args, **kwargs):
        learners = finetune.Learners('synthetic', run, 25, load=True)
        a = learners.agents['player_0']
        a.learn_enabled = False
        a.buffer.push(np.ones(79), 2, -.5, np.zeros(79), False, np.ones(6, bool))
        a.learn_enabled = True
        a.buffer.push(np.zeros(79), 1, 0., np.zeros(79), False, np.ones(6, bool))
        run.mkdir(parents=True)
        checkpoint = run / 'synthetic-checkpoint'
        checkpoint.write_bytes(b'only an engine boundary fixture')
        inner.update(final_checkpoint=str(checkpoint), final_checkpoint_sha256=engine_hash(checkpoint))
        (run / 'final_receipt.json').write_text(json.dumps(inner))
        (run / 'training_audit.json').write_text(json.dumps(dict(prefill=dict(
            learning=dict(replay=dict(size=1, pos=1))))))
        means = [round(value, 5) for value in losses]
        if wrong_csv:
            means[0] += .001
        (run / 'train.csv').write_text('mean_loss\n' + ''.join(f'{value}\n' for value in means))
    monkeypatch.setattr(m.engine, 'run_arm', synthetic_engine)
    monkeypatch.setattr(m.engine, 'validate_receipt', lambda *args: inner)
    original_write = m.engine._write
    observed = []
    def observe_publication(path, value):
        original_write(path, value)
        if path.name == 'anchor_receipt.json':
            # Immediate observers must receive a fully valid completed arm.
            observed.append(m.validate(prepared, 'control'))
            assert finetune.Learners is constructor
            assert all('_learn' not in vars(a) and 'push' not in vars(a.buffer) for a in constructed)
    monkeypatch.setattr(m.engine, '_write', observe_publication)
    deadline = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
    if wrong_csv:
        with pytest.raises(ValueError, match='combined losses differ'):
            m.run_arm(prepared, 'control', deadline)
        assert observed == []
        assert not (prepared / 'audits/control/anchor_receipt.json').exists()
        assert json.loads((prepared / 'audits/control/status.json').read_text())['status'] == 'incomplete'
    else:
        receipt = m.run_arm(prepared, 'control', deadline)
        assert observed == [receipt]
        before = {str(p): engine_hash(p) for p in prepared.rglob('*') if p.is_file()}
        assert m.validate(prepared, 'control') == receipt
        assert before == {str(p): engine_hash(p) for p in prepared.rglob('*') if p.is_file()}
    assert finetune.Learners is constructor
