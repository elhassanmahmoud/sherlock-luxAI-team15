"""Synthetic checks of matched reward arms; no production games."""
import copy
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet


def module():
    from scripts import student_reward_train
    return student_reward_train


@pytest.fixture
def student(tmp_path):
    torch.set_num_threads(1)
    cfg = AgentConfig(hidden=512, canonical=True, frozen=True).to_dict()
    q = QNet(79, 6, hidden=512, dueling=cfg['dueling']).state_dict()
    path = tmp_path / 'student.pth'
    torch.save(dict(q=q, target_q=copy.deepcopy(q), cfg=cfg, feature_dim=79,
                    n_actions=6, ensemble=[], ensemble_dims=[], env_steps=60000, learn_steps=0), path)
    return path


def test_prepare_preserves_full_config_and_only_reward_differs(student, tmp_path):
    m = module()
    manifest = m.prepare(student, tmp_path / 'prepared')
    a, b = (manifest['arms'][arm] for arm in ('control', 'sap0'))
    assert {k for k in a['config'] if a['config'][k] != b['config'][k]} == {'w_sap_hit'}
    original = torch.load(student, weights_only=True)['cfg']
    for k, v in original.items():
        if k not in {'frozen', 'lr', 'rules_in_training', 'rules_in_training_all'}:
            assert a['config'][k] == v
    assert a['config']['frozen'] is False
    assert a['config']['rules_in_training'] is a['config']['rules_in_training_all'] is True
    assert b['config']['w_sap_hit'] == 0
    assert a['tensor_sha256'] == b['tensor_sha256']
    assert a['rollout_plan'] == b['rollout_plan']
    assert a['rollout_plan'][0]['seed'] == 495000
    assert a['rollout_plan'][40]['seed'] == 493000
    assert len(a['rollout_plan']) == 200


def test_prepare_drops_optimizer_and_replay_and_checks_mutation(student, tmp_path):
    m = module()
    # Extra optimizer is forbidden at the distilled checkpoint contract boundary.
    cp = torch.load(student, weights_only=True)
    cp['opt'] = {'state': {}}
    torch.save(cp, student)
    with pytest.raises(ValueError, match='optimizer|contract'):
        m.prepare(student, tmp_path / 'bad')
    del cp['opt']
    torch.save(cp, student)
    student.with_suffix('.buffer.npz').write_bytes(b'historical replay must not be copied')
    prepared = tmp_path / 'prepared'
    m.prepare(student, prepared)
    for arm in ('control', 'sap0'):
        _, _, init = m.check_prepared(prepared, arm)
        assert [p.name for p in (init / 'weights').iterdir()] == ['agent.pth']
        assert 'opt' not in torch.load(init / 'weights/agent.pth', weights_only=True)
    with student.open('ab') as f:
        f.write(b'changed')
    with pytest.raises(ValueError, match='changed|hash|SHA'):
        m.check_prepared(prepared, 'control')


def test_protected_and_occupied_outputs_refused(student, tmp_path):
    m = module()
    protected = tmp_path / 'protected'
    protected.mkdir()
    m_protected = m.PROTECTED_DIRS
    try:
        m.PROTECTED_DIRS = (protected,)
        with pytest.raises(ValueError):
            m.prepare(student, protected / 'run')
        alias = tmp_path / 'alias'
        alias.symlink_to(protected, target_is_directory=True)
        with pytest.raises(ValueError):
            m.prepare(student, alias / 'run')
        occupied = tmp_path / 'occupied'
        occupied.mkdir()
        with pytest.raises(FileExistsError):
            m.prepare(student, occupied)
    finally:
        m.PROTECTED_DIRS = m_protected


def reward_context():
    return dict(ally_ids=np.array([0, 1]), ally_pos=np.array([[0, 0], [1, 1]]),
                ally_ene=np.array([100., 100.]), W=2, H=2, assigned={},
                point_tiles=np.zeros((2, 2), bool), first_on_tile={},
                own_wins=0, opp_wins=0, match_step=1,
                belief=SimpleNamespace(newly_explored=0, newly_proven=0, opp_gain=0))


@pytest.mark.parametrize('weight', [.3, 0.])
def test_reward_counterfactual_is_signed_and_restores_binding(weight):
    m = module()
    from agents.sherlock import main
    original = main.unit_rewards
    cfg = AgentConfig(w_sap_hit=weight)
    ctx = reward_context()
    with m.reward_audit(.3) as proof:
        rewards = main.unit_rewards(cfg, ctx, ctx, {0: 5, 1: 5}, {0: 2, 1: 0})
    assert main.unit_rewards is original
    assert rewards == pytest.approx({0: 2 * weight, 1: -weight})
    assert proof['removed_signed'] == pytest.approx(.3)
    assert proof['removed_absolute'] == pytest.approx(.9)
    assert proof['sap_transitions'] == 2
    assert proof['positive_to_nonpositive'] == 1
    assert proof['actual_reward'] == pytest.approx(weight)
    with pytest.raises(RuntimeError):
        with m.reward_audit(.3):
            raise RuntimeError('stop')
    assert main.unit_rewards is original


def test_incomplete_run_never_receives_success_receipt(student, tmp_path):
    m = module()
    prepared = tmp_path / 'prepared'
    m.prepare(student, prepared)
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    with pytest.raises(TimeoutError):
        m.run_arm(prepared, 'control', past.isoformat())
    run = prepared / 'runs/control'
    assert json.loads((run / 'status.json').read_text())['status'] == 'incomplete'
    assert not (run / 'final_receipt.json').exists()
    with pytest.raises(ValueError):
        m.validate_receipt(run)


def test_full_action_state_transcript_detects_sap_aim_difference():
    m = module()
    deadline = datetime.now(timezone.utc) + timedelta(minutes=1)
    class Actor:
        def __init__(self):
            self.aim = 1
            self._prev_feats = {0: np.zeros(79, np.float32)}
        def act(self):
            return np.array([[5, self.aim, 0]])
    a = Actor()
    proofs = []
    for aim in (1, 2):
        a.aim = aim
        proof = {}
        with m._act_deadline(a, deadline, proof):
            a.act()
        proofs.append(proof['action_state_sha256'])
    assert proofs[0] != proofs[1]
    assert 'act' not in vars(a)


@pytest.mark.parametrize('fail', [False, True])
def test_isolated_validation_preserves_gameplay_and_learning(student, tmp_path, monkeypatch, fail):
    m = module()
    from scripts import experiment
    from scripts.variants import VARIANTS
    prepared = tmp_path / 'prepared'
    manifest = m.prepare(student, prepared)
    entry = manifest['arms']['control']
    monkeypatch.setitem(VARIANTS, m.VARIANT, ('sherlock', entry['config']))
    learners = experiment.Learners(m.VARIANT, prepared / 'init/control', 29, load=True)
    a = learners.agents['player_0']
    a.learn_enabled = True
    before = m.learner_identity(learners)
    seen = []
    def game(env, agent, opp, seed, side, train):
        seen.append(agent.cfg.to_dict())
        assert not train and not agent.training and not agent.learn_enabled
        assert agent.epsilon == 0
        if fail:
            raise RuntimeError('synthetic validation failure')
        return dict(seed=seed, side=side)
    monkeypatch.setattr(experiment, 'play_game', game)
    monkeypatch.setattr(experiment, 'make_opponent', lambda *args: object())
    completed = []
    deadline = datetime.now(timezone.utc) + timedelta(minutes=1)
    if fail:
        with pytest.raises(RuntimeError, match='synthetic validation'):
            m._isolated_validation(None, learners, [500000], ['default'], deadline, completed)
    else:
        assert len(m._isolated_validation(None, learners, [500000], ['default'], deadline, completed)) == 2
    assert seen[0] == entry['config']
    assert before == m.learner_identity(learners)
    assert a.training is True


def test_run_failure_restores_hooks_variant_and_arg_parser(student, tmp_path, monkeypatch):
    m = module()
    from scripts import finetune
    import sys
    prepared = tmp_path / 'prepared'
    m.prepare(student, prepared)
    old = {k: getattr(finetune, k) for k in ('Learners', 'play_game', 'play_set', 'make_opponent', 'RUNS')}
    argv = sys.argv
    def fail_main():
        # Fail after the actual fresh learner constructor and save interception.
        run = finetune.RUNS / 'control'
        import shutil
        shutil.copytree(prepared / 'init/control', run)
        finetune.Learners(m.VARIANT, run, 29, load=True)
        raise RuntimeError('synthetic rollout failure')
    monkeypatch.setattr(finetune, 'main', fail_main)
    with pytest.raises(RuntimeError, match='synthetic rollout'):
        m.run_arm(prepared, 'control', (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat())
    assert all(getattr(finetune, k) is value for k, value in old.items())
    assert sys.argv is argv
    assert m.VARIANT not in m.VARIANTS
    run = prepared / 'runs/control'
    assert json.loads((run / 'status.json').read_text())['status'] == 'incomplete'
    assert not (run / 'final_receipt.json').exists()


def test_real_finetune_loop_emits_only_fixed_final_receipt(student, tmp_path, monkeypatch):
    """Actual finetune orchestration; synthetic episodes, no game/gradient claim."""
    m = module()
    from contextlib import contextmanager
    from tests.test_targeting_adapt import simulated_finetune
    finetune = simulated_finetune.__wrapped__(m, monkeypatch)
    @contextmanager
    def action_evidence(agent):
        yield dict(act_calls=303, update_calls=303, checked_replay_transitions=303,
                   transcript_sha256='0' * 64)
    @contextmanager
    def reward_evidence(weight):
        yield dict(transitions=303, sap_transitions=1, removed_signed=.3,
                   removed_absolute=.3, actual_reward=.3)
    monkeypatch.setattr(m, 'action_audit', action_evidence)
    monkeypatch.setattr(m, 'reward_audit', reward_evidence)
    prepared = tmp_path / 'prepared'
    m.prepare(student, prepared)
    record = m.run_arm(prepared, 'control', (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat())
    run = prepared / 'runs/control'
    receipt = m.validate_receipt(run)
    assert record['status'] == 'done'
    assert (receipt['actual_prefill_games'], receipt['actual_train_games'], receipt['actual_validation_games']) == (40, 160, 32)
    assert receipt['end']['learning']['learn_steps'] == 24000
    assert receipt['end']['learning']['env_steps'] == 120600
    assert receipt['end']['reload_verified'] is True
    assert len(list((run / 'weights').glob('*.pth'))) == 1
    assert not (run / 'weights_best').exists()
    m.run_arm(prepared, 'sap0', (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat())
    assert m.compare_prefill(prepared)['status'] == 'matched'
    assert json.loads((prepared / 'paired_prefill.json').read_text())['prefill_games'] == 40
    # Rehashing cannot legitimize missing initial live learning evidence.
    audit_path = run / 'training_audit.json'
    audit = json.loads(audit_path.read_text())
    audit['initial'] = {}
    audit_path.write_text(json.dumps(audit))
    receipt['evidence_sha256']['training_audit.json'] = m.file_sha256(audit_path)
    (run / 'final_receipt.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match='proof|evidence|malformed'):
        m.validate_receipt(run)


def test_concurrent_atomic_writers_use_independent_tempfiles(tmp_path, monkeypatch):
    """Both workers reach replace together; shared .tmp deterministically fails."""
    m = module()
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path
    from threading import Barrier
    barrier = Barrier(2)
    original_replace = Path.replace
    def simultaneous_replace(self, target):
        barrier.wait(timeout=5)
        return original_replace(self, target)
    monkeypatch.setattr(Path, 'replace', simultaneous_replace)
    path = tmp_path / 'paired_prefill.json'
    values = [dict(worker=0, payload='a' * 1000), dict(worker=1, payload='b' * 1000)]
    with ThreadPoolExecutor(max_workers=2) as workers:
        futures = [workers.submit(m._write, path, value) for value in values]
        for future in futures:
            future.result(timeout=10)
    assert json.loads(path.read_text()) in values
    assert list(tmp_path.iterdir()) == [path]


def test_atomic_writer_failure_cleans_temporary_file(tmp_path, monkeypatch):
    m = module()
    from pathlib import Path
    path = tmp_path / 'status.json'
    path.write_text('{"status":"previous"}')
    def fail_replace(self, target):
        raise OSError('synthetic rename failure')
    monkeypatch.setattr(Path, 'replace', fail_replace)
    with pytest.raises(OSError, match='synthetic rename'):
        m._write(path, dict(status='new'))
    assert json.loads(path.read_text()) == dict(status='previous')
    assert list(tmp_path.iterdir()) == [path]


def test_actual_distillation_export_is_accepted_without_training_state(tmp_path, monkeypatch):
    m = module()
    from tests.test_student_distill import fixture as distilled_fixture
    sd, teacher, buffers = distilled_fixture(tmp_path, monkeypatch)
    out = tmp_path / 'actual_student'
    sd.run_distillation(teacher, buffers, out,
                       datetime.now(timezone.utc) + timedelta(minutes=2), row_cap=20)
    student_path = out / 'weights/agent.pth'
    cp = torch.load(student_path, weights_only=True)
    assert (cp['distillation_updates'], cp['distillation_epochs'], cp['distillation_seed']) == (3, 3, 20261104)
    prepared = tmp_path / 'prepared'
    m.prepare(student_path, prepared)
    for arm in ('control', 'sap0'):
        _, _, init = m.check_prepared(prepared, arm)
        initialized = torch.load(init / 'weights/agent.pth', weights_only=True)
        assert initialized['distillation_updates'] == 3
        assert initialized['learn_steps'] == 0
        assert not {'opt', 'replay', 'buffer'} & initialized.keys()


@pytest.mark.parametrize('metadata', [
    {'distillation_updates': -1, 'distillation_epochs': 3, 'distillation_seed': 20261104},
    {'distillation_updates': 3, 'distillation_epochs': True, 'distillation_seed': 20261104},
    {'distillation_updates': 3, 'distillation_epochs': 3, 'distillation_seed': 1.5},
    {'distillation_updates': 3, 'distillation_epochs': 3, 'distillation_seed': -1},
    {'distillation_updates': 3},
    {'unknown_provenance': 3},
])
def test_student_rejects_invalid_or_unknown_provenance(student, metadata):
    m = module()
    cp = torch.load(student, weights_only=True)
    cp.update(metadata)
    torch.save(cp, student)
    with pytest.raises(ValueError, match='contract|provenance'):
        m._student(student)
