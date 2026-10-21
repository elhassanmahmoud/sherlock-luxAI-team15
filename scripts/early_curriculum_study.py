"""Exclusive, sequential fresh-pair study. Nothing starts on import.

Start only after independent review with --run-id ID --start. Resume accepts
only completely audited phase boundaries, retaining the original 12h deadline.
Tensor loading lives in an explicitly scheduled child, never the supervisor.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time

from scripts import protocol as P

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (47, 48, 49)
ARMS = ('control', 'early')
PLANS = ('docs/superpowers/plans/2026-10-21-early-opponent-curriculum.md',
         'docs/NAECHSTER_TRAININGSVERSUCH_20261021.md', 'docs/EXPERIMENT_PROTOKOLL.md')
THREAD_ENV = {key: '1' for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
    'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')}
THREAD_ENV.update(PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1')
CURRENT = None


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def hashes(paths):
    return {str(path): digest(path) for path in sorted(map(Path, paths))}


def layout(root, run_id):
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', run_id), 'Invalid study run ID')
    root = Path(root).absolute()
    base = root / 'experiments/analysis' / f'early_curriculum_{run_id}'
    arms = {str(seed): {arm: {
        'run': str(root / 'experiments/runs' / f'{run_id}_early_curriculum_s{seed}_{arm}'),
        'eval': str(base / f's{seed}_{arm}_final.csv')}
        for arm in ARMS} for seed in SEEDS}
    return {'analysis': str(base), 'state_path': str(base / 'state.json'), 'arms': arms,
            'candidate': str(base / 'candidate21.pth'),
            'comparisons': {name: str(base / f'{name}.csv') for name in (
                'development_v3', 'development_candidate', 'fresh_v3', 'fresh_candidate', 'direct')}}


def source_identity(root, python, plans):
    root, python = Path(root), Path(python).absolute()
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z',
                                     '--cached', '--others', '--exclude-standard', '--', '*.py']).split(b'\0')
    paths = {root / os.fsdecode(name) for name in names if name}
    # Include ignored Python files in the actual executable source trees too.
    for name in ('scripts', 'agents', 'lux'):
        paths.update((root / name).rglob('*.py'))
    paths.update(map(Path, plans))
    for name in ('requirements.txt', 'pyproject.toml'):
        if (root / name).is_file():
            paths.add(root / name)
    venv = python.parent.parent
    if (venv / 'pyvenv.cfg').is_file():
        paths.add(venv / 'pyvenv.cfg')
    for engine in (venv / 'lib').glob('python*/site-packages/luxai_s3'):
        paths.update(engine.rglob('*.py'))
    head = subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', 'HEAD'],
                          capture_output=True, text=True)
    return {'head': head.stdout.strip(), 'python': str(python),
            'executable': str(python.resolve()), 'executable_sha256': digest(python),
            'files': hashes(paths)}


def check_paths(state):
    expected = layout(state['root'], state['run_id'])
    require(all(state.get(k) == v for k, v in expected.items()), 'Study output path binding changed')
    for target in [state['analysis'], *(a['run'] for pair in state['arms'].values() for a in pair.values())]:
        path = Path(target)
        require(not any(p.is_symlink() for p in (path, *path.parents)), 'Symlink output path')


def check_inputs(state):
    check_paths(state)
    require(source_identity(state['root'], state['python'], state['plans']) == state['source'],
            'Frozen source, plan or interpreter changed')
    require(all(Path(p).resolve() == Path(p) and Path(p).stat().st_nlink == 1
                for p in state['protected']), 'Use real frozen worktree inputs')
    require(hashes(state['protected']) == state['protected'], 'Protected weights changed')


def new_output(state, target):
    """Validate before any writer with overwrite semantics is invoked."""
    check_paths(state)
    path = Path(target).absolute()
    allowed = [Path(state['analysis']), *(Path(a['run']) for pair in state['arms'].values() for a in pair.values())]
    require(any(path == base or base in path.parents for base in allowed), 'Foreign output path')
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'Symlink output path')
    require(not path.exists(), f'Output already exists: {path}')
    # Existing hardlinks are rejected above, including aliases of protected files.
    return path


def save_state(state):
    path = Path(state['state_path'])
    check_paths(state)
    require(not path.is_symlink() and (not path.exists() or path.stat().st_nlink == 1), 'Unsafe state path')
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(state, stream, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def reserve_study(root, run_id, python, plans, protected, *, now):
    root = Path(root).resolve()
    state = dict(run_id=run_id, root=str(root), python=str(Path(python).absolute()),
                 plans=list(map(lambda p: str(Path(p).absolute()), plans)),
                 started_at=now, deadline=now + 12 * 3600, phases={}, active=None,
                 timings={'training': [3344.0], 'validation_game': [1.2],
                          'single_game': [.6], 'ensemble_game': [202 / 240],
                          'direct_game': [202 / 240]}, **layout(root, run_id))
    state['protected'] = hashes(protected)
    require(all(root in Path(p).parents and Path(p).resolve() == Path(p)
                and Path(p).stat().st_nlink == 1 for p in state['protected']),
            'Use real frozen worktree input weights')
    state['source'] = source_identity(root, state['python'], state['plans'])
    check_paths(state)
    for pair in state['arms'].values():
        for arm in pair.values():
            new_output(state, arm['run'])
    admit_phase(state, remaining_work(state), now)
    base = Path(state['analysis'])
    base.parent.mkdir(parents=True, exist_ok=True)
    base.mkdir()  # Atomic reservation: never adopt an existing study ID.
    save_state(state)
    return state


def resume_study(path):
    state = json.loads(Path(path).read_text())
    require(Path(path).absolute() == Path(state['state_path']), 'Wrong state path')
    check_inputs(state)
    require(state.get('active') is None, 'Active or incomplete process')
    require(state['deadline'] == state['started_at'] + 43200, 'Original deadline changed')
    for phase in state['phases'].values():
        require(phase.get('status') == 'complete', 'Cannot resume an incomplete phase')
        require(phase.get('outputs'), 'Missing audited output hashes')
        require(hashes(phase['outputs']) == phase['outputs'], 'Audited output changed')
    return state


def training_command(state, run_seed, arm):
    require(run_seed in SEEDS and arm in ARMS, 'Unknown pair')
    check_paths(state)
    return [state['python'], '-B', '-m', 'scripts.experiment', '--variant', 'full_rules_v3',
            '--run-seed', str(run_seed), '--games', '3000', '--sol92-frac', '0.7',
            '--pool-frac', '0', '--val-every', '750', '--val-seeds', '8',
            '--val-seed-start', '500720', '--isolate-validation', '--no-test',
            '--tag', state['run_id'], '--opponent-plan', 'standard' if arm == 'control' else 'early_sol100',
            '--out', state['arms'][str(run_seed)][arm]['run']]


def remaining_work(state):
    complete = lambda label: state['phases'].get(label, {}).get('status') == 'complete'
    training = sum(not complete(f'train_{s}_{a}') for s in SEEDS for a in ARMS)
    evaluation = sum(not complete(f'eval_{s}_{a}') for s in SEEDS for a in ARMS)
    return dict(training=training, validation_games=training * 160, single_games=evaluation * 240,
                ensemble_games=2080, direct_games=400)


def admit_phase(state, remaining, now):
    rates = state['timings']
    require(set(remaining) == {'training', 'validation_games', 'single_games', 'ensemble_games', 'direct_games'},
            'Incomplete remaining work budget')
    require(all(isinstance(n, int) and n >= 0 for n in remaining.values()), 'Invalid remaining work')
    require(all(v and all(math.isfinite(x) and x > 0 for x in v) for v in rates.values()), 'Invalid measured time')
    estimate = remaining['training'] * max(rates['training'])
    for jobs, rate in [('validation_games', 'validation_game'), ('single_games', 'single_game'),
                       ('ensemble_games', 'ensemble_game'), ('direct_games', 'direct_game')]:
        estimate += remaining[jobs] * max(rates[rate])
    require(math.isfinite(now) and now + 1.25 * estimate + 900 < state['deadline'],
            'Insufficient study budget for ALL remaining work and technical reserve')


def read_json(path):
    return json.loads(Path(path).read_text())


def read_rows(path, *, games=True):
    with Path(path).open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames and len(reader.fieldnames) == len(set(reader.fieldnames)), 'Invalid CSV header')
        rows = list(reader)
    require(rows, 'Empty CSV')
    for row in rows:
        require(None not in row and all(value not in (None, '') for value in row.values()), 'Incomplete CSV row')
        require(row.get('point_counting_version') == '2', 'Wrong point counting version')
        for key, value in row.items():
            if key in ('side', 'opponent', 'mean_loss'):
                continue
            require(math.isfinite(float(value)), f'Non-finite {key}')
        if not games:
            continue
        own, other = float(row['our_wins']), float(row['opp_wins'])
        require(own.is_integer() and other.is_integer() and min(own, other) >= 0 and own + other <= 3,
                'Invalid match wins')
        result = 1. if own > other else 0. if own < other else .5
        require(float(row['result']) == result and float(row['game_win']) == int(own > other),
                'Inconsistent game result')
        our_points, opp_points = float(row['our_points']), float(row['opp_points'])
        require(min(our_points, opp_points) >= 0, 'Invalid points')
        point_result = 1. if our_points > opp_points else 0. if our_points < opp_points else .5
        require(float(row['point_win']) == point_result, 'Inconsistent point result')
        require(int(row['steps']) == 303, 'Incomplete course game')
    return rows


def validate_keys(rows, seeds, *, after=None):
    expected = {(s, side, opp) for s in seeds for side in P.SIDES for opp in P.EVAL_OPPONENTS}
    key = lambda r: (int(r['seed']), r['side'], r['opponent'])
    if after is not None:
        expected = {(n, *k) for n in after for k in expected}
        key = lambda r: (int(r['after_games']), int(r['seed']), r['side'], r['opponent'])
    actual = [key(r) for r in rows]
    require(len(actual) == len(expected) and set(actual) == expected, 'Incomplete or duplicated game keys')


def validate_initial(initial):
    require(initial.get('schema_version') == 1 and len(initial.get('learners', [])) == 1,
            'Missing actual initial identity')
    entry = initial['learners'][0]
    require(set(initial['rng_sha256']) >= {'python', 'numpy', 'torch_cpu'}, 'Missing initial RNG identity')
    for value in [*initial['rng_sha256'].values(), *(entry.get(k, '') for k in (
            'q_sha256', 'target_q_sha256', 'optimizer_sha256', 'agent_rng_sha256'))]:
        require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'Invalid identity hash')
    require(entry['q_sha256'] == entry['target_q_sha256'], 'Initial target differs')
    require(entry['env_steps'] == entry['learn_steps'] == 0 and entry['recent_losses'] == [], 'Not a fresh learner')
    require(entry['sides'] == list(P.SIDES) and entry['device'] == 'cpu', 'Wrong learner/device')
    replay = entry['replay']
    require(replay['pos'] == replay['size'] == 0 and replay['_mask_dim'] == 1
            and replay['logical_content'] == 'empty-replay-v1' and replay['arrays'], 'Nonempty initial replay')
    cfg = entry['config']
    require(cfg['eps_decay_steps'] == 60000 and all(not cfg.get(k, False) for k in
            ('terminal_death_potential', 'active_targets', 'sap_geometry')), 'Wrong study configuration')
    require(replay['capacity'] == cfg['buffer_capacity'], 'Wrong replay capacity')
    return cfg


def checkpoint_identity(path):
    """Heavy operation: the CLI invokes this in a separate, owned audit child."""
    import torch
    from scripts.experiment import state_sha256
    ckpt = torch.load(path, map_location='cpu', weights_only=False)
    require(not ckpt.get('ensemble') and ckpt['env_steps'] == 909000 and ckpt['learn_steps'] > 0,
            'Expected a final, learned 3000-game single checkpoint')
    require(ckpt['q'] and set(ckpt['q']) == set(ckpt['target_q']), 'Invalid q/target keys')
    for network, peer in (('q', 'target_q'), ('target_q', 'q')):
        for key, tensor in ckpt[network].items():
            require(isinstance(tensor, torch.Tensor) and bool(torch.isfinite(tensor).all()),
                    f'Non-finite tensor: {network}.{key}')
            require(tensor.shape == ckpt[peer][key].shape and tensor.dtype == ckpt[peer][key].dtype,
                    'q/target shape or dtype mismatch')
    return dict(file_sha256=digest(path), q_sha256=state_sha256(ckpt['q']),
                target_q_sha256=state_sha256(ckpt['target_q']), config=ckpt['cfg'],
                env_steps=ckpt['env_steps'], learn_steps=ckpt['learn_steps'],
                q_finite=True, target_q_finite=True)


def audit_training(state, run_seed, arm):
    run = Path(state['arms'][str(run_seed)][arm]['run'])
    require(read_json(run / 'study.json') == dict(run_id=state['run_id'], run_seed=run_seed,
            arm=arm, source=state['source']), 'Wrong run ID/source ownership')
    rows = read_rows(run / 'train.csv')
    require(len(rows) == 3000, 'Incomplete training rows')
    mode = 'standard' if arm == 'control' else 'early_sol100'
    schedule = P.opponent_schedule(3000, .7, 0., mode)
    previous_learn = 0
    nan_losses = 0
    for g, row in enumerate(rows):
        require((int(row['game']), int(row['seed']), row['side'], row['opponent']) ==
                (g, P.train_seed(run_seed, g), P.train_side(g), schedule[g]), 'Wrong training key/schedule')
        learn = int(row['learn_steps'])
        require(int(row['env_steps']) == (g + 1) * 303 and learn >= previous_learn, 'Wrong learning counters')
        loss = float(row['mean_loss'])
        require(math.isfinite(loss) or (math.isnan(loss) and learn == 0), 'Invalid training loss')
        nan_losses += int(math.isnan(loss))
        previous_learn = learn
    require(previous_learn > 0 and math.isfinite(float(rows[-1]['mean_loss'])), 'No final learning')
    initial = read_json(run / 'initial_identity.json')
    cfg = validate_initial(initial)
    final = read_json(run / 'final_identity.json')
    require(final['config'] == cfg and final['env_steps'] == 909000
            and final['learn_steps'] == previous_learn, 'Wrong final identity/config/counters')
    require(final.get('q_finite') is True and final.get('target_q_finite') is True, 'Missing finite tensor audit')
    require(final['file_sha256'] == digest(run / 'weights/agent.pth'), 'Final checkpoint hash changed')
    manifest = read_json(run / 'manifest.json')
    expected = dict(status='done', variant='full_rules_v3', config=cfg, run_seed=run_seed,
        train_games=3000, train_seeds=[run_seed * 10000, run_seed * 10000 + 1499],
        separate_side_networks=False, val_every=750, val_seeds=list(range(500720, 500728)),
        isolate_validation=True, test_seeds=[], eval_opponents=list(P.EVAL_OPPONENTS),
        sides=list(P.SIDES), eval_epsilon=0., learner_devices=['cpu'], opponent_plan=mode,
        opponent_schedule=schedule, opponent_schedule_sha256=hashlib.sha256(
            json.dumps(schedule, separators=(',', ':')).encode()).hexdigest())
    require(all(manifest.get(k) == v for k, v in expected.items()), 'Wrong/incomplete training manifest')
    require(manifest['git']['commit'] == state['source']['head'] and manifest.get('finished'), 'Wrong source/completion')
    require(manifest['argv'][1:] == training_command(state, run_seed, arm)[4:], 'Wrong manifest argv')
    val = read_rows(run / 'val_games.csv')
    times = (0, 750, 1500, 2250, 3000)
    validate_keys(val, range(500720, 500728), after=times)
    aggregates = read_rows(run / 'val.csv', games=False)
    require(len(aggregates) == 10 and {(int(r['after_games']), r['opponent']) for r in aggregates}
            == {(n, opp) for n in times for opp in P.EVAL_OPPONENTS}, 'Wrong validation aggregate keys')
    for agg in aggregates:
        group = [r for r in val if r['after_games'] == agg['after_games'] and r['opponent'] == agg['opponent']]
        own = sum(float(r['our_wins']) for r in group)
        total = sum(float(r['our_wins']) + float(r['opp_wins']) for r in group)
        expected = {'games': 16, 'match_winrate': own / max(1, total)}
        for key, column in [('winrate', 'result'), ('point_winrate', 'point_win'),
                            ('avg_points', 'our_points'), ('avg_opp_points', 'opp_points')]:
            expected[key] = sum(float(r[column]) for r in group) / 16
        require(all(math.isclose(float(agg[k]), v, rel_tol=1e-12, abs_tol=1e-12)
                    for k, v in expected.items()), 'Validation aggregate differs from raw games')
    return dict(training_rows=len(rows), validation_rows=len(val), initial=initial, final=final,
                nan_losses_before_learning=nan_losses)


def audit_evaluation(path):
    rows = read_rows(path)
    validate_keys(rows, range(500720, 500780))
    return {'evaluation_rows': len(rows)}


def audit_pair(state, run_seed):
    require(CURRENT is None and state.get('active') is None, 'Audit requires no active child')
    check_inputs(state)
    require(run_seed in SEEDS, 'Unknown pair seed')
    result = {}
    for arm in ARMS:
        for kind in ('train', 'eval'):
            phase = state['phases'].get(f'{kind}_{run_seed}_{arm}', {})
            require(phase.get('status') == 'complete' and phase.get('jobs')
                    and all(job.get('returncode') == 0 for job in phase['jobs']), 'Incomplete/failed phase')
            require(phase.get('outputs') and hashes(phase['outputs']) == phase['outputs'], 'Output hashes differ')
        run = Path(state['arms'][str(run_seed)][arm]['run'])
        expected_files = {str(p) for p in run.rglob('*') if p.is_file()}
        require(expected_files == set(state['phases'][f'train_{run_seed}_{arm}']['outputs'])
                and {state['arms'][str(run_seed)][arm]['eval']}
                == set(state['phases'][f'eval_{run_seed}_{arm}']['outputs']), 'Incomplete artifact hash coverage')
        require(all(not Path(p).is_symlink() and Path(p).stat().st_nlink == 1
                    and Path(p).resolve() == Path(p) for p in expected_files), 'Unsafe output artifact alias')
        result[arm] = {**audit_training(state, run_seed, arm),
                       **audit_evaluation(state['arms'][str(run_seed)][arm]['eval'])}
    require(result['control']['initial'] == result['early']['initial'], 'Paired initial identity differs')
    return dict(run_id=state['run_id'], run_seed=run_seed, complete=True, arms=result)


def interrupted(signum, frame):
    raise InterruptedError(f'Received signal {signum}')


def group_exists(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False


def stop_group(process):
    """Terminate only the live Popen object registered by this supervisor."""
    require(CURRENT is not None and CURRENT['process'] is process
            and CURRENT['owner_pid'] == os.getpid() and CURRENT['pgid'] == process.pid,
            'Refusing to signal a process not owned by this supervisor')
    try:
        require(os.getpgid(process.pid) == CURRENT['pgid'], 'Owned process group changed')
    except ProcessLookupError:
        pass  # The registered leader may have exited while its workers remain.
    for sig in (signal.SIGTERM, signal.SIGKILL):
        if group_exists(process.pid):
            os.killpg(process.pid, sig)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            continue
        until = time.monotonic() + 2
        while group_exists(process.pid) and time.monotonic() < until:
            time.sleep(.05)
        if not group_exists(process.pid):
            return
    process.wait(timeout=2)
    require(not group_exists(process.pid), 'Owned process group did not stop')


def check_resources():
    """Admission is exclusive across visible model jobs, not just this runner."""
    text = subprocess.check_output(['ps', '-axo', 'pid=,args='], text=True)
    pattern = re.compile(r'(?:-m\s+scripts\.|scripts/)(?:experiment|par_eval|train|finetune|evaluate|compare_weights|train_ppo|distill)(?:\s|\.py\b)')
    foreign = [line for line in text.splitlines() if pattern.search(line)]
    require(not foreign, 'Another model job is active; resource admission refused')


def run_process(state, phase, command):
    global CURRENT
    require(CURRENT is None and state.get('active') is None, 'A child is already active')
    check_inputs(state)
    check_resources()
    require(time.time() < state['deadline'] - 10, 'Study deadline reached')
    log = new_output(state, Path(state['analysis']) / f"job_{sum(len(p.get('jobs', [])) for p in state['phases'].values())}_{len(phase['jobs'])}.log")
    job = dict(argv=command, started_at=time.time(), log=str(log), returncode=None)
    phase['jobs'].append(job)
    save_state(state)
    process = None
    try:
        with log.open('xb') as stream:
            blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGHUP, signal.SIGINT, signal.SIGTERM})
            try:
                process = subprocess.Popen(command, cwd=state['root'], env={**os.environ, **THREAD_ENV},
                    start_new_session=True, stdout=stream, stderr=subprocess.STDOUT)
                CURRENT = dict(process=process, owner_pid=os.getpid(), pgid=process.pid)
                state['active'] = dict(owner_pid=os.getpid(), pid=process.pid, pgid=process.pid)
                job.update(pid=process.pid, pgid=process.pid)
                save_state(state)
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
            next_check = time.monotonic() + 30
            while process.poll() is None:
                require(time.time() < state['deadline'] - 10, 'Study deadline reached')
                if time.monotonic() >= next_check:
                    check_inputs(state)
                    next_check = time.monotonic() + 30
                time.sleep(.1)
            job['returncode'] = process.wait()
            require(job['returncode'] == 0, f'Child failed: returncode {job["returncode"]}')
            require(not group_exists(process.pid), 'Child left active workers')
        check_inputs(state)
    finally:
        # A second termination signal must not interrupt our bounded cleanup.
        blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGHUP, signal.SIGINT, signal.SIGTERM})
        try:
            if process is not None:
                if process.poll() is None or group_exists(process.pid):
                    stop_group(process)
                job['returncode'] = process.wait()
            CURRENT = None
            state['active'] = None
            job['finished_at'] = time.time()
            save_state(state)
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, blocked)


def run_phase(state, label, execute, audit):
    if label in state['phases']:
        phase = state['phases'][label]
        require(phase.get('status') == 'complete', 'Cannot continue an incomplete phase')
        require(phase.get('outputs') and hashes(phase['outputs']) == phase['outputs'], 'Audited outputs changed')
        return
    check_inputs(state)
    admit_phase(state, remaining_work(state), time.time())
    check_resources()
    phase = dict(status='running', started_at=time.time(), jobs=[], protected_before=hashes(state['protected']))
    state['phases'][label] = phase
    save_state(state)
    execute(phase)
    require(CURRENT is None and state.get('active') is None, 'Phase audit requires all children stopped')
    result, paths = audit()
    check_inputs(state)
    output_hashes = hashes(paths)
    require(output_hashes, 'No audited outputs')
    phase.update(audit=result, outputs=output_hashes, finished_at=time.time(),
                 protected_after=hashes(state['protected']), status='complete')
    save_state(state)  # Atomic publication only after successful exit, audit, hashes.


def train_arm(state, seed, arm):
    paths = state['arms'][str(seed)][arm]
    run = Path(paths['run'])
    def execute(phase):
        new_output(state, run)
        run.mkdir(parents=True)
        with (run / 'study.json').open('x') as stream:
            json.dump(dict(run_id=state['run_id'], run_seed=seed, arm=arm, source=state['source']), stream)
        run_process(state, phase, training_command(state, seed, arm))
        run_process(state, phase, [state['python'], '-B', '-m', 'scripts.early_curriculum_study',
            '--checkpoint-audit', state['state_path'], str(seed), arm])
    def audit():
        result = audit_training(state, seed, arm)
        aggregates = read_rows(run / 'val.csv', games=False)
        validation_times = [max(float(r['secs']) for r in aggregates if int(r['after_games']) == n)
                            for n in (0, 750, 1500, 2250, 3000)]
        job = state['phases'][f'train_{seed}_{arm}']['jobs'][0]
        # The observed training wall includes validation: separate components.
        state['timings']['training'].append(max(.001, job['finished_at'] - job['started_at'] - sum(validation_times)))
        state['timings']['validation_game'].extend(v / 32 for v in validation_times if v > 0)
        return result, [p for p in run.rglob('*') if p.is_file()]
    run_phase(state, f'train_{seed}_{arm}', execute, audit)


def evaluate_arm(state, seed, arm):
    paths = state['arms'][str(seed)][arm]
    out = Path(paths['eval'])
    def execute(phase):
        new_output(state, out)
        training = state['phases'].get(f'train_{seed}_{arm}', {})
        require(training.get('status') == 'complete' and hashes(training['outputs']) == training['outputs'],
                'Final checkpoint has not passed training audit')
        run_process(state, phase, [state['python'], '-B', '-m', 'scripts.par_eval',
            '--weights', str(Path(paths['run']) / 'weights/agent.pth'), '--first', '720', '--n', '60',
            '--workers', '2', '--opponents', 'default,solution92', '--out', str(out)])
    def audit():
        result = audit_evaluation(out)
        job = state['phases'][f'eval_{seed}_{arm}']['jobs'][0]
        state['timings']['single_game'].append((job['finished_at'] - job['started_at']) / 240)
        return result, [out]
    run_phase(state, f'eval_{seed}_{arm}', execute, audit)


def finish_pair(state, seed):
    path = Path(state['analysis']) / f'pair_s{seed}_audit.json'
    def audit():
        result = audit_pair(state, seed)
        new_output(state, path)
        with path.open('x') as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
        return result, [path]
    run_phase(state, f'pair_{seed}', lambda phase: None, audit)


def run_pairs(state):
    for seed in SEEDS:
        for arm in ARMS:
            train_arm(state, seed, arm)
        for arm in ARMS:
            evaluate_arm(state, seed, arm)
        finish_pair(state, seed)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id')
    parser.add_argument('--start', action='store_true')
    parser.add_argument('--resume-audited', metavar='ID')
    parser.add_argument('--checkpoint-audit', nargs=3, metavar=('STATE', 'SEED', 'ARM'), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.checkpoint_audit:
        path, seed, arm = args.checkpoint_audit
        state = read_json(path)
        check_inputs(state)
        require(int(seed) in SEEDS and arm in ARMS, 'Invalid checkpoint audit pair')
        run = Path(state['arms'][seed][arm]['run'])
        final = checkpoint_identity(run / 'weights/agent.pth')
        from scripts.variants import variant_cfg
        require(final['config'] == variant_cfg('full_rules_v3').to_dict(), 'Final config differs from frozen variant')
        out = new_output(state, run / 'final_identity.json')
        with out.open('x') as stream:
            json.dump(final, stream, indent=2, allow_nan=False)
        return
    require((args.start and args.run_id and not args.resume_audited)
            or (args.resume_audited and not args.start and not args.run_id),
            'Use --run-id ID --start or --resume-audited ID')
    for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, interrupted)
    if args.start:
        protected = [ROOT / 'experiments/candidates/all18_v3.pth']
        protected += [ROOT / f'agents/sherlock/weights/agent_p{s}.pth' for s in (0, 1)]
        protected += [ROOT / f'experiments/releases/20261020_old3_sym3/agent_p{s}.pth' for s in (0, 1)]
        for index, path in enumerate(protected):
            expected = ('aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935' if index < 3
                        else '3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158')
            require(digest(path) == expected, 'Frozen V3/rollback identity differs')
        check_resources()
        state = reserve_study(ROOT, args.run_id, sys.executable, [ROOT / p for p in PLANS],
                              protected, now=time.time())
    else:
        state = resume_study(layout(ROOT, args.resume_audited)['state_path'])
    import fcntl
    with (Path(state['analysis']) / 'supervisor.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Re-read under the lock: another supervisor may have advanced meanwhile.
        state = resume_study(state['state_path'])
        run_pairs(state)
        state['status'] = 'pairs_audited'
        save_state(state)


if __name__ == '__main__':
    main()
