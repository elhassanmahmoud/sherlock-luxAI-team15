"""Contract tests for exclusive, fail-closed curriculum orchestration."""
import copy
import csv
import importlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest


@pytest.fixture
def study():
    assert importlib.util.find_spec('scripts.early_curriculum_study'), 'Study runner is missing'
    return importlib.import_module('scripts.early_curriculum_study')


@pytest.fixture
def state(tmp_path, study):
    root = tmp_path / 'repo'
    root.mkdir()
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    (root / 'scripts').mkdir()
    (root / 'scripts/source.py').write_text('source = 1\n')
    (root / 'plan.md').write_text('frozen study')
    weights = root / 'input.pth'
    weights.write_bytes(b'protected')
    return study.reserve_study(root, 'test-study', sys.executable,
                               [root / 'plan.md'], [weights], now=time.time())


def test_import_is_lightweight(study):
    result = subprocess.run([sys.executable, '-c',
        "import sys; import scripts.early_curriculum_study; assert 'torch' not in sys.modules; assert 'scripts.experiment' not in sys.modules"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_six_commands_fix_every_factor_except_opponent_plan(state, study):
    for seed in (47, 48, 49):
        commands = [study.training_command(state, seed, arm) for arm in ('control', 'early')]
        for arm, cmd in zip(('control', 'early'), commands):
            assert cmd[0] == sys.executable
            assert cmd[cmd.index('-m') + 1] == 'scripts.experiment'
            for key, value in {'--variant': 'full_rules_v3', '--run-seed': str(seed),
                 '--games': '3000', '--sol92-frac': '0.7', '--pool-frac': '0',
                 '--val-every': '750', '--val-seeds': '8', '--val-seed-start': '500720',
                 '--opponent-plan': 'standard' if arm == 'control' else 'early_sol100'}.items():
                assert cmd[cmd.index(key) + 1] == value
            assert '--isolate-validation' in cmd and '--no-test' in cmd
            assert cmd[cmd.index('--out') + 1] == state['arms'][str(seed)][arm]['run']
        normalized = []
        for cmd in commands:
            cmd = cmd.copy()
            for flag in ('--out', '--opponent-plan'):
                cmd[cmd.index(flag) + 1] = '<controlled>'
            normalized.append(cmd)
        assert normalized[0] == normalized[1]


def test_exclusive_reservation_and_path_binding(state, study):
    with pytest.raises((FileExistsError, ValueError)):
        study.reserve_study(Path(state['root']), state['run_id'], state['python'],
                            state['plans'], list(state['protected']), now=time.time())
    changed = copy.deepcopy(state)
    changed['arms']['47']['control']['run'] = str(Path(state['root']) / 'elsewhere')
    with pytest.raises(ValueError, match='path'):
        study.check_inputs(changed)
    target = Path(state['arms']['47']['control']['run'])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(Path(state['root']))
    with pytest.raises(ValueError):
        study.new_output(state, target)


@pytest.mark.parametrize('change', ['source', 'new_source', 'plan', 'weight', 'python'])
def test_frozen_inputs_detect_changes(state, study, change):
    paths = {'source': Path(state['root']) / 'scripts/source.py',
             'new_source': Path(state['root']) / 'scripts/extra.py',
             'plan': Path(state['plans'][0]), 'weight': Path(next(iter(state['protected'])))}
    if change == 'python':
        state['python'] = '/different/python'
    else:
        paths[change].write_text('changed')
    with pytest.raises((ValueError, FileNotFoundError)):
        study.check_inputs(state)


def test_admission_includes_all_jobs_and_original_deadline(state, study):
    remaining = study.remaining_work(state)
    assert remaining == {'training': 6, 'validation_games': 960, 'single_games': 1440,
                         'ensemble_games': 2080, 'direct_games': 400}
    assert state['deadline'] - state['started_at'] == 43200
    study.admit_phase(state, remaining, state['started_at'])
    with pytest.raises(ValueError, match='budget'):
        study.admit_phase(state, remaining, state['started_at'] + 4 * 3600)
    state['timings']['training'].append(10000)
    with pytest.raises(ValueError, match='budget'):
        study.admit_phase(state, remaining, state['started_at'])


def test_resume_rejects_any_incomplete_phase_and_changed_outputs(state, study):
    study.save_state(state)
    resumed = study.resume_study(Path(state['state_path']))
    assert resumed['deadline'] == state['deadline']
    state['phases']['train_47_control'] = {'status': 'running'}
    study.save_state(state)
    with pytest.raises(ValueError, match='incomplete'):
        study.resume_study(Path(state['state_path']))
    state['phases']['train_47_control'] = {'status': 'complete', 'outputs': {str(Path(state['root']) / 'missing'): 'abc'}}
    study.save_state(state)
    with pytest.raises((ValueError, FileNotFoundError)):
        study.resume_study(Path(state['state_path']))


def write_json(path, data):
    Path(path).write_text(json.dumps(data))


def write_csv(path, rows):
    with Path(path).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def game(seed, side, opponent, **extra):
    return dict(seed=seed, side=side, opponent=opponent, result=1., game_win=1,
                point_win=1., our_wins=2, opp_wins=1, our_points=100,
                opp_points=50, point_counting_version=2, steps=303, secs=.1,
                wait_frac=.2, invalid_frac=0., greedy_masked_frac=.1, sap_attempts=2,
                sap_hits=1, stack_frac=.1, relics_found=2, relics_seen=2,
                known_point_tiles=3, belief_contradictions=0, unit_steps=100, **extra)


@pytest.fixture
def pair(state, study):
    # Complete artificial logs: expected labels generated independently of protocol.
    from scripts.variants import variant_cfg
    cfg = variant_cfg('full_rules_v3').to_dict()
    initial = {'schema_version': 1, 'rng_sha256': {k: 'a' * 64 for k in ('python', 'numpy', 'torch_cpu')},
               'learners': [dict(config=cfg, device='cpu', env_steps=0, learn_steps=0,
                    q_sha256='b' * 64, target_q_sha256='b' * 64, optimizer_sha256='c' * 64,
                    agent_rng_sha256='d' * 64, sides=['player_0', 'player_1'],
                    recent_losses=[], learn_enabled=True, autosave_on_terminate=False,
                    replay=dict(size=0, pos=0, _mask_dim=1, logical_content='empty-replay-v1',
                                capacity=cfg['buffer_capacity'], obs_dim=42, arrays={'x': {'dtype': '<f4', 'shape': [1]}}))]}
    for arm in ('control', 'early'):
        paths = state['arms']['47'][arm]
        run = Path(paths['run'])
        (run / 'weights').mkdir(parents=True)
        (run / 'weights/agent.pth').write_bytes(b'fake-checkpoint-' + arm.encode())
        labels = ['default' if g < 750 or ((g // 2) * .6180339887) % 1 >= .7 else 'solution92' for g in range(3000)]
        if arm == 'early':
            late = [g for g in range(750, 3000, 2) if labels[g] == 'solution92'][:50]
            labels[100:200] = ['solution92'] * 100
            for g in late:
                labels[g:g + 2] = ['default', 'default']
        train = [game(470000 + g // 2, f'player_{g % 2}', labels[g], game=g,
                      epsilon=.05, mean_loss='nan' if g == 0 else .2,
                      env_steps=(g + 1) * 303, learn_steps=g, winrate_50=1.) for g in range(3000)]
        write_csv(run / 'train.csv', train)
        val = [game(s, side, opp, after_games=after) for after in (0, 750, 1500, 2250, 3000)
               for opp in ('default', 'solution92') for s in range(500720, 500728)
               for side in ('player_0', 'player_1')]
        write_csv(run / 'val_games.csv', val)
        write_csv(run / 'val.csv', [dict(after_games=after, opponent=opp, games=16,
            winrate=1., match_winrate=2 / 3, point_winrate=1., avg_points=100., avg_opp_points=50.,
            point_counting_version=2, secs=1.) for after in (0, 750, 1500, 2250, 3000)
            for opp in ('default', 'solution92')])
        write_csv(paths['eval'], [game(s, side, opp) for opp in ('default', 'solution92')
            for s in range(500720, 500780) for side in ('player_0', 'player_1')])
        write_json(run / 'initial_identity.json', initial)
        write_json(run / 'study.json', {'run_id': state['run_id'], 'run_seed': 47, 'arm': arm,
                                      'source': state['source']})
        write_json(run / 'manifest.json', dict(status='done', train_games=3000, run_seed=47,
            variant='full_rules_v3', config=cfg, separate_side_networks=False,
            train_seeds=[470000, 471499], val_seeds=list(range(500720, 500728)), val_every=750,
            test_seeds=[], eval_opponents=['default', 'solution92'], sides=['player_0', 'player_1'],
            eval_epsilon=0., isolate_validation=True, learner_devices=['cpu'],
            opponent_plan='standard' if arm == 'control' else 'early_sol100', opponent_schedule=labels,
            opponent_schedule_sha256=study.hashlib.sha256(json.dumps(labels, separators=(',', ':')).encode()).hexdigest(),
            argv=['experiment.py'] + study.training_command(state, 47, arm)[4:],
            git={'commit': state['source']['head']}, train_secs=3000., runtime_secs=3000., finished='done'))
        write_json(run / 'final_identity.json', dict(file_sha256=study.digest(run / 'weights/agent.pth'),
            q_sha256='e' * 64, target_q_sha256='f' * 64, config=cfg,
            env_steps=909000, learn_steps=2999, q_finite=True, target_q_finite=True))
        for kind in ('train', 'eval'):
            output = list(run.rglob('*')) if kind == 'train' else [Path(paths['eval'])]
            output = [p for p in output if p.is_file()]
            state['phases'][f'{kind}_47_{arm}'] = dict(status='complete',
                jobs=[{'returncode': 0}], outputs=study.hashes(output))
    return state


def test_full_pair_audit_accepts_exact_rows_and_initial_identity(pair, study):
    result = study.audit_pair(pair, 47)
    assert result['complete'] is True
    assert result['arms']['control']['training_rows'] == 3000
    assert result['arms']['early']['validation_rows'] == 160
    assert result['arms']['early']['evaluation_rows'] == 240


@pytest.mark.parametrize('filename,mutation', [
    ('train.csv', 'missing'), ('train.csv', 'duplicate'), ('train.csv', 'wrong_opponent'),
    ('train.csv', 'loss_nan'), ('train.csv', 'loss_inf'), ('train.csv', 'steps'),
    ('train.csv', 'result'), ('train.csv', 'version'),
    ('val_games.csv', 'missing'), ('val_games.csv', 'duplicate'), ('val_games.csv', 'wrong_seed'),
    ('val.csv', 'aggregate'), ('val.csv', 'missing'), ('eval', 'missing'), ('eval', 'duplicate'),
])
def test_pair_audit_rejects_bad_data_even_when_hashes_match(pair, study, filename, mutation):
    paths = pair['arms']['47']['early']
    path = Path(paths['eval']) if filename == 'eval' else Path(paths['run']) / filename
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    if mutation == 'missing':
        rows.pop()
    elif mutation == 'duplicate':
        rows[-1] = rows[0].copy()
    else:
        key, value = {'wrong_opponent': ('opponent', 'default'), 'loss_nan': ('mean_loss', 'nan'),
             'loss_inf': ('mean_loss', 'inf'), 'steps': ('steps', '302'),
             'result': ('result', '0'), 'version': ('point_counting_version', '1'),
             'wrong_seed': ('seed', '900000'), 'aggregate': ('winrate', '.9')}[mutation]
        rows[100 if mutation == 'wrong_opponent' else -1][key] = value
    write_csv(path, rows)
    phase = pair['phases']['eval_47_early' if filename == 'eval' else 'train_47_early']
    phase['outputs'] = study.hashes(phase['outputs'])
    with pytest.raises(ValueError):
        study.audit_pair(pair, 47)


@pytest.mark.parametrize('change', ['initial_missing', 'initial_rng', 'final_config', 'final_hash',
                                    'returncode', 'run_id', 'manifest', 'active'])
def test_pair_audit_rejects_wrong_provenance(pair, study, change):
    run = Path(pair['arms']['47']['early']['run'])
    if change == 'active':
        pair['active'] = {'pid': 123}
    elif change == 'returncode':
        pair['phases']['train_47_early']['jobs'][0]['returncode'] = 1
    elif change == 'initial_missing':
        (run / 'initial_identity.json').unlink()
    else:
        filename = {'initial_rng': 'initial_identity.json', 'final_config': 'final_identity.json',
                    'final_hash': 'final_identity.json', 'run_id': 'study.json', 'manifest': 'manifest.json'}[change]
        data = json.loads((run / filename).read_text())
        if change == 'initial_rng': data['rng_sha256']['python'] = '0' * 64
        if change == 'final_config': data['config']['eps_decay_steps'] = 12
        if change == 'final_hash': data['file_sha256'] = '0' * 64
        if change == 'run_id': data['run_id'] = 'historical'
        if change == 'manifest': data['val_seeds'] = []
        write_json(run / filename, data)
        phase = pair['phases']['train_47_early']
        phase['outputs'] = study.hashes(phase['outputs'])
    with pytest.raises((ValueError, FileNotFoundError)):
        study.audit_pair(pair, 47)


def test_checkpoint_finite_tensor_audit(tmp_path, study):
    import torch
    cfg = {'eps_decay_steps': 60000}
    path = tmp_path / 'checkpoint.pth'
    checkpoint = dict(cfg=cfg, q={'w': torch.ones(2)}, target_q={'w': torch.zeros(2)},
                      env_steps=909000, learn_steps=200, ensemble=[])
    torch.save(checkpoint, path)
    assert study.checkpoint_identity(path)['q_finite'] is True
    for network in ('q', 'target_q'):
        changed = copy.deepcopy(checkpoint)
        changed[network]['w'][0] = float('nan')
        torch.save(changed, path)
        with pytest.raises(ValueError, match='finite'):
            study.checkpoint_identity(path)


def test_process_failure_keeps_phase_incomplete(state, study):
    with pytest.raises(ValueError):
        study.run_phase(state, 'failed', lambda phase: study.run_process(
            state, phase, [sys.executable, '-c', 'raise SystemExit(3)']), lambda: ({}, []))
    saved = json.loads(Path(state['state_path']).read_text())
    assert saved['phases']['failed']['status'] == 'running'
    assert saved['phases']['failed']['jobs'][0]['returncode'] == 3
    assert saved['active'] is None


def test_phase_commits_only_after_successful_audit_and_rehashes(state, study):
    output = Path(state['analysis']) / 'proof.txt'
    def execute(phase):
        study.run_process(state, phase, [sys.executable, '-c',
                          'from pathlib import Path; Path(' + repr(str(output)) + ').write_text("ok")'])
    with pytest.raises(ValueError, match='audit failed'):
        study.run_phase(state, 'bad_audit', execute,
                        lambda: (_ for _ in ()).throw(ValueError('audit failed')))
    assert state['phases']['bad_audit']['status'] == 'running'
    output.unlink()
    study.run_phase(state, 'good', execute, lambda: ({'verified': True}, [output]))
    phase = state['phases']['good']
    assert phase['status'] == 'complete' and phase['audit'] == {'verified': True}
    assert phase['outputs'][str(output)] == study.digest(output)
    assert phase['jobs'][0]['pid'] == phase['jobs'][0]['pgid']
    with pytest.raises(ValueError, match='incomplete'):
        study.resume_study(Path(state['state_path']))


def test_deadline_terminates_and_reaps_only_owned_child(state, study):
    foreign = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)
    try:
        with pytest.raises(ValueError, match='owned'):
            study.stop_group(foreign)
        state['deadline'] = time.time() + 10.3
        phase = {'jobs': []}
        with pytest.raises(ValueError, match='deadline'):
            study.run_process(state, phase, [sys.executable, '-c', 'import time; time.sleep(60)'])
        assert foreign.poll() is None
        assert phase['jobs'][0]['returncode'] is not None
        assert state['active'] is None and study.CURRENT is None
        with pytest.raises(ProcessLookupError):
            os.kill(phase['jobs'][0]['pid'], 0)
    finally:
        foreign.terminate()
        foreign.wait(timeout=5)


@pytest.mark.parametrize('sig', [signal.SIGHUP, signal.SIGINT, signal.SIGTERM])
def test_signals_stop_owned_process_and_block_resume(state, study, sig):
    # Real signal delivery in an isolated supervisor, not in pytest itself.
    code = '''
import json, signal
from pathlib import Path
from scripts import early_curriculum_study as s
state = json.loads(Path(STATE).read_text())
for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM): signal.signal(sig, s.interrupted)
try:
    s.run_phase(state, 'signal', lambda phase: s.run_process(state, phase,
        [state['python'], '-c', 'import time; time.sleep(60)']), lambda: ({}, []))
except InterruptedError:
    pass
'''.replace('STATE', repr(state['state_path']))
    supervisor = subprocess.Popen([sys.executable, '-c', code], cwd=Path(study.__file__).parents[1])
    try:
        until = time.time() + 5
        active = None
        while time.time() < until:
            active = json.loads(Path(state['state_path']).read_text()).get('active')
            if active: break
            time.sleep(.02)
        assert active
        supervisor.send_signal(sig)
        assert supervisor.wait(timeout=5) == 0
        saved = json.loads(Path(state['state_path']).read_text())
        assert saved['active'] is None
        assert saved['phases']['signal']['status'] == 'running'
        with pytest.raises(ProcessLookupError): os.kill(active['pid'], 0)
        with pytest.raises(ValueError, match='incomplete'):
            study.resume_study(Path(state['state_path']))
    finally:
        if supervisor.poll() is None:
            supervisor.kill()
            supervisor.wait()


def test_pair_order_is_fixed_and_audits_precede_next_seed(state, study, monkeypatch):
    events = []
    # Training/evaluation are slow external boundaries; retain the actual scheduler.
    monkeypatch.setattr(study, 'train_arm', lambda st, seed, arm: events.append(('train', seed, arm)))
    monkeypatch.setattr(study, 'evaluate_arm', lambda st, seed, arm: events.append(('eval', seed, arm)))
    monkeypatch.setattr(study, 'finish_pair', lambda st, seed: events.append(('audit', seed)))
    study.run_pairs(state)
    assert events == [item for seed in (47, 48, 49) for item in (
        ('train', seed, 'control'), ('train', seed, 'early'), ('eval', seed, 'control'),
        ('eval', seed, 'early'), ('audit', seed))]


def test_protected_inputs_must_be_real_frozen_worktree_files(tmp_path, study):
    root = tmp_path / 'repo'
    root.mkdir()
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    external = tmp_path / 'mutable-main.pth'
    external.write_bytes(b'live')
    linked = root / 'frozen.pth'
    linked.symlink_to(external)
    with pytest.raises(ValueError, match='frozen'):
        study.reserve_study(root, 'linked', sys.executable, [], [linked], now=time.time())


def test_pair_requires_hash_coverage_for_every_audited_artifact(pair, study):
    phase = pair['phases']['train_47_early']
    phase['outputs'].pop(str(Path(pair['arms']['47']['early']['run']) / 'train.csv'))
    with pytest.raises(ValueError, match='coverage'):
        study.audit_pair(pair, 47)


def test_existing_hardlink_cannot_be_an_output(state, study):
    target = Path(state['candidate'])
    os.link(next(iter(state['protected'])), target)
    with pytest.raises(ValueError):
        study.new_output(state, target)
    assert Path(next(iter(state['protected']))).read_bytes() == b'protected'


def test_resource_admission_rejects_foreign_model_jobs(study, monkeypatch):
    monkeypatch.setattr(study.subprocess, 'check_output', lambda *args, **kwargs:
                        '345 /python -m scripts.par_eval --workers 2 --weights frozen.pth\n')
    with pytest.raises(ValueError, match='resource admission'):
        study.check_resources()


def test_actual_small_learner_identity_and_saved_checkpoint_schema(tmp_path, study):
    from dataclasses import replace
    from agents.sherlock.main import Agent_x
    from scripts.experiment import initial_identity, Learners
    from scripts.variants import variant_cfg
    cfg = replace(variant_cfg('full_rules_v3'), hidden=8, buffer_capacity=8)
    learner = Agent_x('player_0', cfg=cfg, seed=4700)
    learner.autosave_on_terminate = False
    learners = Learners.__new__(Learners)
    learners.agents = {'player_0': learner, 'player_1': learner}
    snapshot = initial_identity(learners)
    assert study.validate_initial(snapshot) == cfg.to_dict()
    learner.env_steps, learner.learn_steps = 909000, 7
    path = tmp_path / 'actual.pth'
    learner.save_agent(str(path))
    identity = study.checkpoint_identity(path)
    assert identity['config'] == cfg.to_dict()
    assert identity['q_sha256'] == snapshot['learners'][0]['q_sha256']


def test_checkpoint_audit_is_detected_as_heavy_work(study, monkeypatch):
    monkeypatch.setattr(study.subprocess, 'check_output', lambda *args, **kwargs:
        '345 /python -B -m scripts.early_curriculum_study --checkpoint-audit state.json 47 control\n')
    with pytest.raises(ValueError, match='resource admission'):
        study.check_resources()


def test_shared_resource_lock_excludes_other_worktree_supervisor(tmp_path, study):
    root = tmp_path / 'main'
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    subprocess.run(['git', '-C', str(root), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                    'commit', '--allow-empty', '-qm', 'fixture'], check=True)
    worktree = tmp_path / 'worktree'
    subprocess.run(['git', '-C', str(root), 'worktree', 'add', '--detach', '-q', str(worktree)], check=True)
    code = "from scripts.early_curriculum_study import resource_lock; import sys\nwith resource_lock(sys.argv[1]): print('acquired')"
    with study.resource_lock(root):
        contender = subprocess.run([sys.executable, '-c', code, str(worktree)], capture_output=True, text=True)
        assert contender.returncode != 0 and 'resource lock' in contender.stderr
        assert 'acquired' not in contender.stdout
    released = subprocess.run([sys.executable, '-c', code, str(worktree)], capture_output=True, text=True)
    assert released.returncode == 0 and released.stdout.strip() == 'acquired'


def test_cli_keeps_shared_lock_during_pair_execution(state, study, monkeypatch):
    monkeypatch.setattr(study, 'ROOT', Path(state['root']))
    def pairs(st):
        code = "from scripts.early_curriculum_study import resource_lock; import sys\nwith resource_lock(sys.argv[1]): pass"
        contender = subprocess.run([sys.executable, '-c', code, st['root']], capture_output=True, text=True)
        assert contender.returncode != 0 and 'resource lock' in contender.stderr
    monkeypatch.setattr(study, 'run_pairs', pairs)
    monkeypatch.setattr(study, 'run_gated_confirmation', pairs)
    study.main(['--resume-audited', state['run_id']])


@pytest.mark.parametrize('filename,column', [('train.csv', 'epsilon'), ('train.csv', 'winrate_50'),
    ('train.csv', 'invalid_frac'), ('val_games.csv', 'after_games'), ('val_games.csv', 'secs'),
    ('val.csv', 'secs'), ('eval', 'sap_attempts'), ('eval', 'unit_steps'), ('eval', 'secs')])
def test_audit_rejects_missing_required_columns(pair, study, filename, column):
    paths = pair['arms']['47']['control']
    path = Path(paths['eval']) if filename == 'eval' else Path(paths['run']) / filename
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        del row[column]
    write_csv(path, rows)
    phase = pair['phases']['eval_47_control' if filename == 'eval' else 'train_47_control']
    phase['outputs'] = study.hashes(phase['outputs'])
    with pytest.raises(ValueError, match='schema'):
        study.audit_pair(pair, 47)


def test_audit_consumes_complete_production_schemas(pair, study):
    from scripts.experiment import GAME_FIELDS, TRAIN_FIELDS, VAL_FIELDS
    paths = pair['arms']['47']['control']
    for path, fields in [(Path(paths['run']) / 'train.csv', TRAIN_FIELDS),
                         (Path(paths['run']) / 'val.csv', VAL_FIELDS),
                         (Path(paths['run']) / 'val_games.csv', ['after_games'] + GAME_FIELDS),
                         (Path(paths['eval']), GAME_FIELDS)]:
        with path.open() as stream:
            assert set(csv.DictReader(stream).fieldnames) == set(fields)
    assert study.audit_pair(pair, 47)['complete']


@pytest.mark.parametrize('prior', [set(), {signal.SIGUSR1}])
def test_child_restores_prelaunch_signal_mask(state, study, prior):
    output = Path(state['analysis']) / 'child_mask.json'
    code = ('import json, signal; from pathlib import Path; Path(' + repr(str(output)) +
            ').write_text(json.dumps(sorted(map(int, signal.pthread_sigmask(signal.SIG_BLOCK, [])))))')
    original = signal.pthread_sigmask(signal.SIG_SETMASK, prior)
    try:
        study.run_process(state, {'jobs': []}, [sys.executable, '-c', code])
        assert set(json.loads(output.read_text())) == {int(sig) for sig in prior}
        assert signal.pthread_sigmask(signal.SIG_BLOCK, []) == prior
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, original)


@pytest.fixture
def all_pairs(pair, study):
    import shutil
    for seed in (48, 49):
        for arm in ('control', 'early'):
            original = pair['arms']['47'][arm]
            paths = pair['arms'][str(seed)][arm]
            run = Path(paths['run'])
            shutil.copytree(original['run'], run)
            shutil.copyfile(original['eval'], paths['eval'])
            rows = list(csv.DictReader((run / 'train.csv').open()))
            for row in rows:
                row['seed'] = str(int(row['seed']) + (seed - 47) * 10000)
            write_csv(run / 'train.csv', rows)
            manifest = study.read_json(run / 'manifest.json')
            manifest.update(run_seed=seed, train_seeds=[seed * 10000, seed * 10000 + 1499],
                            argv=['experiment.py'] + study.training_command(pair, seed, arm)[4:])
            write_json(run / 'manifest.json', manifest)
            owner = study.read_json(run / 'study.json')
            owner['run_seed'] = seed
            write_json(run / 'study.json', owner)
            for kind in ('train', 'eval'):
                outputs = [p for p in run.rglob('*') if p.is_file()] if kind == 'train' else [Path(paths['eval'])]
                pair['phases'][f'{kind}_{seed}_{arm}'] = dict(status='complete', jobs=[{'returncode': 0}],
                    outputs=study.hashes(outputs))
    return pair


def set_wins(path, won, study):
    rows = study.read_rows(path)
    for row in rows:
        row.update(result=str(int(won)), game_win=str(int(won)),
                   our_wins='2' if won else '1', opp_wins='1' if won else '2')
    write_csv(path, rows)


@pytest.fixture
def confirmation(all_pairs, study):
    import torch
    from scripts.experiment import state_sha256
    state = all_pairs
    cfg = study.read_json(Path(state['arms']['47']['early']['run']) / 'final_identity.json')['config']
    # Different historical learning configuration is legitimate for V3.
    base_cfg = dict(cfg, gamma=.98)
    def network(index):
        # Inert audit/build fixture: retain its identity marker and real input width.
        return {'w': torch.tensor([float(index)]), 'body.0.weight': torch.zeros(1, 79)}
    base = dict(cfg=base_cfg, feature_dim=79, n_actions=6, q=network(0),
                ensemble=[network(i) for i in range(1, 18)])
    v3 = Path(state['root']) / 'experiments/candidates/all18_v3.pth'
    v3.parent.mkdir(parents=True)
    torch.save(base, v3)
    state['protected'].update(study.hashes([v3]))
    for index, seed in enumerate((47, 48, 49)):
        for arm in ('control', 'early'):
            run = Path(state['arms'][str(seed)][arm]['run'])
            q = network(18 + index)
            checkpoint = dict(cfg=cfg, feature_dim=79, n_actions=6, q=q, target_q=q,
                              env_steps=909000, learn_steps=2999)
            torch.save(checkpoint, run / 'weights/agent.pth')
            identity = study.checkpoint_identity(run / 'weights/agent.pth')
            write_json(run / 'final_identity.json', identity)
            set_wins(state['arms'][str(seed)][arm]['eval'], arm == 'early', study)
            for kind in ('train', 'eval'):
                phase = state['phases'][f'{kind}_{seed}_{arm}']
                phase['outputs'] = study.hashes(phase['outputs'])
        study.finish_pair(state, seed)
    study.save_state(state)
    return state


def fake_confirmation_jobs(study, monkeypatch, *, fail_stage=None, wrong_direct=False):
    commands = []
    def process(state, phase, command, *, input_hashes=None):
        assert input_hashes and study.hashes(input_hashes) == input_hashes
        if '--weights' in command:
            assert command[command.index('--weights') + 1] in input_hashes
        else:
            assert str(study.frozen_v3(state)) in input_hashes
            assert all(str(Path(state['arms'][str(seed)]['early']['run']) / 'weights/agent.pth')
                       in input_hashes for seed in (47, 48, 49))
        commands.append(command)
        phase['jobs'].append(dict(argv=command, returncode=0, started_at=1., finished_at=2.))
        if '--build-candidate' in command:
            study.build_fixed_candidate(state, Path(state['candidate']))
            return
        assert command[command.index('-m') + 1] == 'scripts.par_eval'
        assert command[command.index('--workers') + 1] == '2'
        out = Path(command[command.index('--out') + 1])
        first = int(command[command.index('--first') + 1]) + 500000
        n = int(command[command.index('--n') + 1])
        opponents = command[command.index('--opponents') + 1].split(',')
        candidate = command[command.index('--weights') + 1] == state['candidate']
        won = candidate and not (fail_stage and out.stem.startswith(fail_stage))
        if wrong_direct and out.stem == 'direct':
            opponents = ['self:/wrong/frozen.pth']
        rows = [game(seed, side, opponent) for seed in range(first, first + n)
                for side in ('player_0', 'player_1') for opponent in opponents]
        write_csv(out, rows)
        set_wins(out, won, study)
    monkeypatch.setattr(study, 'run_process', process)
    return commands


def test_confirmation_refuses_unverified_pair_before_any_summary(all_pairs, study):
    with pytest.raises(ValueError, match='pair'):
        study.run_gated_confirmation(all_pairs)
    assert not Path(all_pairs['candidate']).exists()


def test_negative_method_stops_before_candidate_or_fresh_cards(confirmation, study, monkeypatch):
    state = confirmation
    for seed in (47, 48, 49):
        path = state['arms'][str(seed)]['early']['eval']
        set_wins(path, False, study)
        phase = state['phases'][f'eval_{seed}_early']
        phase['outputs'] = study.hashes(phase['outputs'])
        # Recreate completed pair reports for this distinct synthetic study.
        state['phases'].pop(f'pair_{seed}')
        (Path(state['analysis']) / f'pair_s{seed}_audit.json').unlink()
        study.finish_pair(state, seed)
    commands = fake_confirmation_jobs(study, monkeypatch)
    result = study.run_gated_confirmation(state)
    assert result['status'] == 'method_rejected'
    assert not result['ready_for_technical_review'] and not result['release_ready']
    assert commands == [] and not Path(state['candidate']).exists()
    assert study.remaining_work(state)['ensemble_games'] == 0
    assert study.remaining_work(state)['direct_games'] == 0


@pytest.mark.parametrize('failed,expected_count,status', [
    ('development', 2, 'development_rejected'), ('fresh', 4, 'fresh_rejected'),
    ('direct', 5, 'direct_rejected'), (None, 5, 'ready_for_technical_review')])
def test_confirmation_obeys_gates_counts_and_exact_seed_labels(confirmation, study, monkeypatch, failed, expected_count, status):
    commands = fake_confirmation_jobs(study, monkeypatch, fail_stage=failed)
    result = study.run_gated_confirmation(confirmation)
    evals = [c for c in commands if '--weights' in c]
    assert len(evals) == expected_count and result['status'] == status
    assert result['ready_for_technical_review'] == (failed is None)
    assert result['release_ready'] is False
    assert [int(c[c.index('--first') + 1]) for c in evals] == [720, 720, 11000, 11000, 11200][:expected_count]
    assert [int(c[c.index('--n') + 1]) for c in evals] == [60, 60, 200, 200, 200][:expected_count]
    if expected_count == 5:
        assert evals[-1][evals[-1].index('--opponents') + 1] == 'self:' + str(Path(confirmation['root']) / 'experiments/candidates/all18_v3.pth')
    assert study.remaining_work(confirmation) == dict(training=0, validation_games=0,
        single_games=0, ensemble_games=0, direct_games=0)
    before = len(commands)
    study.run_gated_confirmation(study.resume_study(confirmation['state_path']))
    assert len(commands) == before  # Resume cannot rerun a finished job or consume more cards.


def test_direct_confirmation_rejects_other_self_reference(confirmation, study, monkeypatch):
    fake_confirmation_jobs(study, monkeypatch, wrong_direct=True)
    with pytest.raises(ValueError):
        study.run_gated_confirmation(confirmation)
    assert confirmation.get('ready_for_technical_review') is not True


def test_confirmation_detects_changed_report_and_raw_data_on_resume(confirmation, study, monkeypatch):
    fake_confirmation_jobs(study, monkeypatch)
    study.run_gated_confirmation(confirmation)
    phase = confirmation['phases']['fresh']
    assert confirmation['comparisons']['fresh_candidate'] in phase['outputs']
    assert confirmation['comparisons']['fresh_v3'] in phase['outputs']
    path = Path(confirmation['analysis']) / 'fresh.json'
    assert str(path) in phase['outputs']
    path.write_text('{}')
    with pytest.raises(ValueError, match='changed'):
        study.resume_study(confirmation['state_path'])


def test_all_future_jobs_remain_reserved_until_verified_negative_gate(state, study):
    state['phases']['development_v3'] = dict(status='complete')
    assert study.remaining_work(state)['ensemble_games'] == 1840
    state['phases']['method'] = dict(status='running', audit={'passed': False})
    assert study.remaining_work(state)['direct_games'] == 400


@pytest.mark.parametrize('flag', ['--build-candidate'])
def test_candidate_child_is_detected_as_heavy_work(study, monkeypatch, flag):
    monkeypatch.setattr(study.subprocess, 'check_output', lambda *a, **k:
        f'345 /python -B -m scripts.early_curriculum_study {flag} state.json\n')
    with pytest.raises(ValueError, match='resource admission'):
        study.check_resources()


def test_fixed_candidate_contains_all_21_sources_and_preserves_base_config(confirmation, study, monkeypatch):
    import torch
    from scripts.experiment import state_sha256
    fake_confirmation_jobs(study, monkeypatch, fail_stage='development')
    study.run_gated_confirmation(confirmation)
    candidate = torch.load(confirmation['candidate'], weights_only=False)
    base = torch.load(Path(confirmation['root']) / 'experiments/candidates/all18_v3.pth', weights_only=False)
    assert candidate['cfg'] == base['cfg']
    assert [q['w'].item() for q in [candidate['q'], *candidate['ensemble']]] == list(range(21))
    report = study.read_json(Path(confirmation['analysis']) / 'candidate_identity.json')
    assert report['q_sha256'] == [state_sha256(q) for q in [candidate['q'], *candidate['ensemble']]]
    assert report['network_count'] == 21
    assert len(report['sources']) == 4
    assert all('control' not in p for p in report['sources'])
    before = study.digest(confirmation['candidate'])
    with pytest.raises(ValueError, match='exists'):
        study.build_fixed_candidate(confirmation, Path(confirmation['candidate']))
    assert study.digest(confirmation['candidate']) == before


@pytest.mark.parametrize('mutation', ['duplicate', 'nonfinite', 'dimension', 'play_key', 'shape'])
def test_fixed_candidate_rejects_bad_base_before_build(confirmation, study, monkeypatch, mutation):
    import torch
    path = Path(confirmation['root']) / 'experiments/candidates/all18_v3.pth'
    checkpoint = torch.load(path, weights_only=False)
    if mutation == 'duplicate': checkpoint['ensemble'][0] = checkpoint['q']
    elif mutation == 'nonfinite': checkpoint['q']['w'][0] = float('nan')
    elif mutation == 'dimension': checkpoint['feature_dim'] = 80
    elif mutation == 'play_key': checkpoint['cfg']['canonical'] = not checkpoint['cfg']['canonical']
    elif mutation == 'shape': checkpoint['q']['w'] = torch.ones(2)
    torch.save(checkpoint, path)
    confirmation['protected'].update(study.hashes([path]))
    fake_confirmation_jobs(study, monkeypatch)
    with pytest.raises(ValueError):
        study.run_gated_confirmation(confirmation)
    assert not Path(confirmation['candidate']).exists()


def test_real_owned_child_build_accepts_supervisor_active_registration(confirmation, study):
    # No training/evaluation: build the tiny synthetic tensors in a real owned child.
    from scripts import early_curriculum_analysis as analysis
    pairs = {str(seed): {arm: confirmation['arms'][str(seed)][arm]['eval'] for arm in ('control', 'early')}
             for seed in (47, 48, 49)}
    study.report_phase(confirmation, 'method', study.method_inputs(confirmation),
                       lambda: analysis.summarize_method(pairs))
    # Fixture source root is deliberately isolated; make this child import the actual code.
    code = ('import sys; sys.path.insert(0, ' + repr(str(Path(study.__file__).parents[1])) + '); '
            'from scripts.early_curriculum_study import main; main(["--build-candidate", '
            + repr(confirmation['state_path']) + '])')
    phase = {'jobs': []}
    study.run_process(confirmation, phase, [sys.executable, '-B', '-c', code])
    assert phase['jobs'][0]['returncode'] == 0
    assert study.read_json(Path(confirmation['analysis']) / 'candidate_identity.json')['network_count'] == 21


def test_resume_rejects_state_only_method_gate_tampering(confirmation, study, monkeypatch):
    fake_confirmation_jobs(study, monkeypatch, fail_stage='development')
    study.run_gated_confirmation(confirmation)
    confirmation['phases']['method']['audit']['passed'] = False
    study.save_state(confirmation)
    with pytest.raises(ValueError, match='audit|decision|gate'):
        study.run_gated_confirmation(study.resume_study(confirmation['state_path']))


@pytest.mark.parametrize('stage,first', [('fresh_candidate', 11000), ('direct', 11200)])
def test_later_evaluation_requires_its_positive_predecessor(confirmation, study, monkeypatch, stage, first):
    fake_confirmation_jobs(study, monkeypatch, fail_stage='development')
    study.run_gated_confirmation(confirmation)
    opponents = 'default,solution92' if stage != 'direct' else 'self:' + str(study.frozen_v3(confirmation))
    with pytest.raises(ValueError, match='gate|phase'):
        study.run_confirmation_evaluation(confirmation, stage, Path(confirmation['candidate']), first, 200, opponents)
    assert not Path(confirmation['comparisons'][stage]).exists()


def test_supervisor_method_pipeline_keeps_torch_unloaded(all_pairs, study):
    for seed in (47, 48, 49):
        study.finish_pair(all_pairs, seed)
    code = ('import sys, json; from pathlib import Path; from scripts import early_curriculum_study as s; '
            'state=json.loads(Path(' + repr(all_pairs['state_path']) + ').read_text()); '
            'assert s.run_gated_confirmation(state)["status"] == "method_rejected"; '
            'assert "torch" not in sys.modules; assert "scripts.experiment" not in sys.modules')
    child = subprocess.run([sys.executable, '-B', '-c', code], capture_output=True, text=True)
    assert child.returncode == 0, child.stderr


def test_fixed_candidate_rejects_different_full_training_configs(confirmation, study, monkeypatch):
    import torch
    for arm in ('control', 'early'):
        run = Path(confirmation['arms']['49'][arm]['run'])
        initial = study.read_json(run / 'initial_identity.json')
        initial['learners'][0]['config']['gamma'] = .97
        write_json(run / 'initial_identity.json', initial)
        manifest = study.read_json(run / 'manifest.json')
        manifest['config']['gamma'] = .97
        write_json(run / 'manifest.json', manifest)
        checkpoint = torch.load(run / 'weights/agent.pth', weights_only=False)
        checkpoint['cfg']['gamma'] = .97
        torch.save(checkpoint, run / 'weights/agent.pth')
        write_json(run / 'final_identity.json', study.checkpoint_identity(run / 'weights/agent.pth'))
        phase = confirmation['phases'][f'train_49_{arm}']
        phase['outputs'] = study.hashes(phase['outputs'])
    confirmation['phases'].pop('pair_49')
    (Path(confirmation['analysis']) / 'pair_s49_audit.json').unlink()
    study.finish_pair(confirmation, 49)
    fake_confirmation_jobs(study, monkeypatch)
    with pytest.raises(ValueError, match='training configs'):
        study.run_gated_confirmation(confirmation)
    assert not Path(confirmation['candidate']).exists()


def test_evaluation_rejects_candidate_changed_while_job_runs(confirmation, study, monkeypatch):
    fake_confirmation_jobs(study, monkeypatch)
    original = study.run_process
    def mutate(state, phase, command, *, input_hashes=None):
        original(state, phase, command, input_hashes=input_hashes)
        if '--out' in command and command[command.index('--out') + 1].endswith('development_v3.csv'):
            with Path(state['candidate']).open('ab') as stream:
                stream.write(b'changed-during-job')
    monkeypatch.setattr(study, 'run_process', mutate)
    with pytest.raises(ValueError, match='changed|provenance'):
        study.run_gated_confirmation(confirmation)
    assert not Path(confirmation['comparisons']['development_candidate']).exists()
    assert confirmation['phases']['development_v3']['status'] == 'running'


def test_periodic_check_stops_owned_job_when_generated_dependency_changes(state, study, monkeypatch):
    from types import SimpleNamespace
    dependency = Path(state['analysis']) / 'generated-checkpoint.pth'
    dependency.write_bytes(b'original checkpoint')
    binding = study.hashes([dependency])
    completed = Path(state['analysis']) / 'completed.txt'
    clock = {'now': 0., 'mutated': False}
    real_sleep = time.sleep
    def advance(seconds):
        if not clock['mutated']:
            dependency.write_bytes(b'changed checkpoint')
            clock.update(now=31., mutated=True)
        else:
            clock['now'] += seconds
        real_sleep(min(seconds, .01))
    monkeypatch.setattr(study, 'time', SimpleNamespace(time=time.time,
        monotonic=lambda: clock['now'], sleep=advance))
    command = [sys.executable, '-c', 'import time; from pathlib import Path; time.sleep(.5); Path('
               + repr(str(completed)) + ').write_text("finished")']
    with pytest.raises(ValueError, match='Job input.*changed'):
        study.run_phase(state, 'periodic_dependency', lambda phase: study.run_process(
            state, phase, command, input_hashes=binding), lambda: ({}, [completed]))
    phase = state['phases']['periodic_dependency']
    assert clock['mutated'] and phase['status'] == 'running'
    assert phase['jobs'][0]['input_hashes'] == binding
    assert phase['jobs'][0]['returncode'] != 0
    assert not completed.exists()
    assert state['active'] is None and study.CURRENT is None
    with pytest.raises(ProcessLookupError):
        os.kill(phase['jobs'][0]['pid'], 0)


def test_single_arm_evaluation_passes_completed_training_bindings(pair, study, monkeypatch):
    pair['phases'].pop('eval_47_early')
    Path(pair['arms']['47']['early']['eval']).unlink()
    observed = []
    def stop_at_boundary(state, phase, command, *, input_hashes=None):
        observed.append(input_hashes)
        raise RuntimeError('Test stops before model job')
    monkeypatch.setattr(study, 'run_process', stop_at_boundary)
    with pytest.raises(RuntimeError, match='Test stops'):
        study.evaluate_arm(pair, 47, 'early')
    assert observed == [pair['phases']['train_47_early']['outputs']]


def test_checkpoint_audit_passes_finalized_run_bindings(state, study, monkeypatch):
    run = Path(state['arms']['47']['early']['run'])
    observed = []
    def stop_at_audit(state, phase, command, *, input_hashes=None):
        if '--checkpoint-audit' not in command:
            (run / 'weights').mkdir()
            (run / 'weights/agent.pth').write_bytes(b'final checkpoint')
        else:
            observed.append(input_hashes)
            raise RuntimeError('Test stops before tensor audit')
    monkeypatch.setattr(study, 'run_process', stop_at_audit)
    with pytest.raises(RuntimeError, match='Test stops'):
        study.train_arm(state, 47, 'early')
    assert observed == [study.hashes([run / 'study.json', run / 'weights/agent.pth'])]
