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


def test_independent_seeds_keep_matched_arms_and_distinct_plans(student, tmp_path):
    m = module()
    manifests = [m.prepare(student, tmp_path / str(seed), run_seed=seed)
                 for seed in (27, 28)]
    for seed, manifest in zip((27, 28), manifests):
        assert manifest['run_seed'] == seed
        control, sap0 = (manifest['arms'][arm] for arm in m.ARMS)
        assert control['run_seed'] == sap0['run_seed'] == seed
        assert control['rollout_plan'] == sap0['rollout_plan']
        assert {k for k in control['config'] if control['config'][k] != sap0['config'][k]} == {'w_sap_hit'}
        assert [r['phase'] for r in control['rollout_plan']].count('prefill') == 40
        assert [r['phase'] for r in control['rollout_plan']].count('train') == 160
        assert len(manifest['validation_plan']) == 32
        for arm in m.ARMS:
            assert m.check_prepared(tmp_path / str(seed), arm)[1] == manifest['arms'][arm]
    first, second = [manifest['arms']['control']['rollout_plan'] for manifest in manifests]
    assert (first[0]['seed'], first[40]['seed']) == (475000, 473000)
    assert (second[0]['seed'], second[40]['seed']) == (485000, 483000)
    assert {r['seed'] for r in first}.isdisjoint(r['seed'] for r in second)
    assert [r['opponent'] for r in first] != [r['opponent'] for r in second]
    assert manifests[0]['arms']['control']['config'] == manifests[1]['arms']['control']['config']


def test_explicit_default_and_default_plans_match(student, tmp_path):
    m = module()
    default = m.prepare(student, tmp_path / 'default')
    explicit = m.prepare(student, tmp_path / 'explicit', run_seed=29)
    assert default == explicit
    assert m.rollout_plan() == m.rollout_plan(29)


@pytest.mark.parametrize('seed', [True, False, 27., 27.5, -1, 30, 1000, '27', None])
def test_prepare_and_planner_reject_invalid_run_seed_without_writing(student, tmp_path, seed):
    m = module()
    out = tmp_path / 'invalid'
    with pytest.raises(ValueError, match='seed'):
        m.prepare(student, out, run_seed=seed)
    assert not out.exists()
    with pytest.raises(ValueError, match='seed'):
        m.rollout_plan(seed)


@pytest.mark.parametrize('seed', [0, 29])
def test_prepare_accepts_seed_boundaries(student, tmp_path, seed):
    m = module()
    out = tmp_path / 'prepared'
    m.prepare(student, out, run_seed=seed)
    assert m.check_prepared(out, 'control')[0]['run_seed'] == seed


@pytest.mark.parametrize('where,seed', [
    ('run_seed', True), ('run_seed', 27.), ('run_seed', -1), ('run_seed', 30),
    ('run_seed', 28), ('control', 27.), ('sap0', 27.), ('sap0', 28),
    ('init', 27.), ('init', True),
])
def test_check_prepared_rejects_malformed_or_tampered_seed(student, tmp_path, where, seed):
    m = module()
    out = tmp_path / 'prepared'
    manifest = m.prepare(student, out, run_seed=27)
    path = out / 'manifest.json'
    if where == 'init':
        path = out / 'init/control/manifest.json'
        manifest = json.loads(path.read_text())
        manifest['run_seed'] = seed
    elif where == 'run_seed':
        manifest[where] = seed
    else:
        manifest['arms'][where]['run_seed'] = seed
    path.write_text(json.dumps(manifest))
    before = path.read_bytes()
    with pytest.raises(ValueError, match='seed|changed'):
        m.check_prepared(out, 'control')
    assert path.read_bytes() == before


def test_prepare_cli_uses_selected_seed(student, tmp_path, monkeypatch):
    m = module()
    import sys
    out = tmp_path / 'cli'
    monkeypatch.setattr(sys, 'argv', ['student_reward_train', 'prepare', '--student', str(student),
                                    '--out', str(out), '--run-seed', '27'])
    m.main()
    manifest, entry, _ = m.check_prepared(out, 'control')
    assert manifest['run_seed'] == entry['run_seed'] == 27
    assert entry['rollout_plan'][40]['seed'] == 473000


def test_seedless_legacy_manifest_is_rejected_without_rewrite(student, tmp_path):
    m = module()
    out = tmp_path / 'prepared'
    manifest = m.prepare(student, out)
    del manifest['run_seed']
    path = out / 'manifest.json'
    path.write_text(json.dumps(manifest))
    before = path.read_bytes()
    with pytest.raises(ValueError, match='legacy|run_seed'):
        m.check_prepared(out, 'control')
    assert path.read_bytes() == before


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


@pytest.mark.parametrize('run_seed', [29, 27, 28])
def test_real_finetune_loop_emits_only_fixed_final_receipt(student, tmp_path, monkeypatch, run_seed):
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
    original_write = m._write
    peer_observations = []
    def observe_publication(path, value):
        original_write(path, value)
        if path.name == 'final_receipt.json':
            # A peer runs as soon as the marker becomes visible, before the
            # publisher can perform any subsequent status/evidence writes.
            peer_observations.append(m.validate_receipt(path.parent))
    monkeypatch.setattr(m, '_write', observe_publication)
    prepared = tmp_path / 'prepared'
    m.prepare(student, prepared, run_seed=run_seed)
    record = m.run_arm(prepared, 'control', (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat())
    run = prepared / 'runs/control'
    receipt = m.validate_receipt(run)
    assert record['status'] == 'done'
    assert record['argv'][record['argv'].index('--seed') + 1] == str(run_seed)
    assert json.loads((run / 'manifest.json').read_text())['run_seed'] == run_seed
    assert receipt['run_seed'] == run_seed
    initial_audit = json.loads((run / 'training_audit.json').read_text())
    assert initial_audit['run_seed'] == run_seed
    expected_rng = np.random.default_rng({29: 2900, 27: 2700, 28: 2800}[run_seed])
    assert initial_audit['initial']['agent_rng_sha256'] == m.experiment.state_sha256(expected_rng.bit_generator.state)
    assert (receipt['actual_prefill_games'], receipt['actual_train_games'], receipt['actual_validation_games']) == (40, 160, 32)
    assert receipt['end']['learning']['learn_steps'] == 24000
    assert receipt['end']['learning']['env_steps'] == 120600
    assert receipt['end']['reload_verified'] is True
    assert len(list((run / 'weights').glob('*.pth'))) == 1
    assert not (run / 'weights_best').exists()
    m.run_arm(prepared, 'sap0', (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat())
    peer_audit = json.loads((prepared / 'runs/sap0/training_audit.json').read_text())
    assert peer_audit['initial']['agent_rng_sha256'] == initial_audit['initial']['agent_rng_sha256']
    assert [r['arm'] for r in peer_observations] == ['control', 'sap0']
    assert all(r['status'] == 'done' for r in peer_observations)
    assert m.compare_prefill(prepared)['status'] == 'matched'
    assert json.loads((prepared / 'paired_prefill.json').read_text())['prefill_games'] == 40
    receipt_path = run / 'final_receipt.json'
    for bad_seed in (True, float(run_seed), 28 if run_seed != 28 else 27):
        receipt_path.write_text(json.dumps(dict(receipt, run_seed=bad_seed)))
        with pytest.raises(ValueError, match='seed|differ'):
            m.validate_receipt(run)
    receipt_path.write_text(json.dumps(receipt))
    audit_path = run / 'training_audit.json'
    audit = json.loads(audit_path.read_text())
    audit_path.write_text(json.dumps(dict(audit, run_seed=float(run_seed))))
    altered_receipt = copy.deepcopy(receipt)
    altered_receipt['evidence_sha256']['training_audit.json'] = m.file_sha256(audit_path)
    receipt_path.write_text(json.dumps(altered_receipt))
    with pytest.raises(ValueError, match='seed'):
        m.validate_receipt(run)
    audit_path.write_text(json.dumps(audit))
    # Rehashing cannot legitimize missing initial live learning evidence.
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


def test_sparse_legacy_producer_config_preserves_nondefaults_and_live_contract(tmp_path, monkeypatch):
    """Legacy teachers omit default keys; actual export retains that sparse cfg."""
    m = module()
    from tests.test_student_distill import fixture as distilled_fixture
    from scripts import experiment
    sd, teacher, buffers = distilled_fixture(tmp_path, monkeypatch)
    teacher_cp = torch.load(teacher, weights_only=True)
    teacher_cp['cfg'] = dict(hidden=8, dueling=True, w_opp_points=1.25,
                             w_sap_hit=.45, cand_rescue=True, frozen=True)
    torch.save(teacher_cp, teacher)
    monkeypatch.setattr(sd, 'V14_SHA256', sd.sha256(teacher))
    out = tmp_path / 'sparse_student'
    sd.run_distillation(teacher, buffers, out,
                       datetime.now(timezone.utc) + timedelta(minutes=2), row_cap=20)
    source = out / 'weights/agent.pth'
    before = m.file_sha256(source)
    saved_cfg = torch.load(source, weights_only=True)['cfg']
    assert 'rescue_in_training' not in saved_cfg
    normalized = m._student(source)
    assert normalized['cfg']['w_opp_points'] == 1.25
    assert normalized['cfg']['cand_rescue'] is True
    assert normalized['cfg']['rescue_in_training'] is False
    prepared = tmp_path / 'prepared'
    manifest = m.prepare(source, prepared)
    assert manifest['source_config']['w_sap_hit'] == .45
    for arm in ('control', 'sap0'):
        _, entry, init = m.check_prepared(prepared, arm)
        assert entry['config']['w_opp_points'] == 1.25
        assert entry['config']['cand_rescue'] is True
        assert entry['config']['rescue_in_training'] is False
        assert entry['config']['w_sap_hit'] == (.45 if arm == 'control' else 0.)
        monkeypatch.setitem(m.VARIANTS, m.VARIANT, ('sherlock', entry['config']))
        learners = experiment.Learners(m.VARIANT, init, 29, load=True)
        assert learners.agents['player_0'].cfg.to_dict() == entry['config']
        assert m.prove_initial(learners, entry)['learning']['config'] == entry['config']
    assert m.file_sha256(source) == before
    assert torch.load(source, weights_only=True)['cfg'] == saved_cfg
