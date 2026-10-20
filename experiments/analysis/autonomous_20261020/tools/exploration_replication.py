"""One fresh paired exploration replication; no job is started without --run.

After Root admission (inference comparisons and measured time budget):
  .venv/bin/python -B this_file.py --run --run-seed 47 --games 3000
Optional --minimum-seconds N rejects admission if N seconds no longer fit.
The horizon is fixed at 3000 games for all three pairs; Root admits each pair.
No resume, checkpoint selection, weight installation or automatic next pair.

Run from the repository when this script is in /tmp. Its intended archived path
is experiments/analysis/autonomous_20261020/tools/exploration_replication.py, where
ROOT is resolved portably with parents[4]. --self-test uses stdlib/AST only and
creates no files. Heavy imports occur solely in scheduled child processes.
"""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

def repository_root(script, cwd):
    script = Path(script).resolve()
    return script.parents[4] if script.parent.name == 'tools' else Path(cwd).resolve()


SCRIPT = Path(__file__).resolve()
ROOT = repository_root(SCRIPT, Path.cwd())
PYTHON = ROOT / '.venv/bin/python'
ANALYSIS = ROOT / 'experiments/analysis/autonomous_20261020'
COMPARE = ROOT / 'experiments/compare/autonomous_20261020'
START_CUTOFF = datetime(2026, 10, 21, 3, tzinfo=timezone.utc).timestamp()
DEADLINE = datetime(2026, 10, 21, 4, tzinfo=timezone.utc).timestamp()
STOP_AT = DEADLINE - 10
V3_SHA = 'aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935'
OLD_SHA = '3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158'
RUN_SEED = GAMES = PREFIX = STATE_PATH = PREFLIGHT = None
ARMS = {}


def settings(root, run_seed, games):
    require(run_seed in (47, 48, 49), 'Replication seed must be 47, 48 or 49')
    require(games == 3000, 'Exploration horizon is fixed at 3000 games')
    root = Path(root)
    prefix = f'exploration_replication_s{run_seed}'
    analysis = root / 'experiments/analysis/autonomous_20261020'
    compare = root / 'experiments/compare/autonomous_20261020'
    arms = {}
    for arm, variant, decay_steps in (('control', 'full_rules_v3', 60000),
                                      ('slow', 'full_rules_v3_slowexplore', 454500)):
        arms[arm] = {'variant': variant, 'decay_steps': decay_steps,
            'run': root / f'experiments/runs/20261020_{variant}_s{run_seed}_exploration_{arm}',
            'eval': compare / f'{prefix}_{arm}.csv'}
    return prefix, analysis / f'{prefix}_state.json', analysis / f'{prefix}_preflight.json', arms


def configure(run_seed, games):
    global RUN_SEED, GAMES, PREFIX, STATE_PATH, PREFLIGHT, ARMS
    PREFIX, STATE_PATH, PREFLIGHT, ARMS = settings(ROOT, run_seed, games)
    RUN_SEED, GAMES = run_seed, games


def schedule_key(run_seed, games, game):
    require(run_seed in (47, 48, 49) and games == 3000, 'Invalid pair settings')
    require(0 <= game < games, 'Training game index out of range')
    seed = run_seed * 10000 + game // 2
    require(seed < 500000, 'Training/validation seed overlap')
    opponent = ('default' if game < games // 4 or ((game // 2) * .6180339887) % 1 >= .7
                else 'solution92')
    return game, seed, f'player_{game % 2}', opponent


def allowed_start(now, heavy=True):
    return now < (START_CUTOFF if heavy else STOP_AT)


def check_admission(now, minimum_seconds):
    require(allowed_start(now), 'Replication start cutoff has passed')
    if minimum_seconds is not None:
        require(math.isfinite(minimum_seconds) and minimum_seconds > 0,
                'minimum-seconds must be positive and finite')
        require(now + minimum_seconds < STOP_AT,
                'Admitted minimum time does not fit before the stop deadline')


def child_command(mode, arm=None):
    require(mode in ('preflight', 'train', 'checkpoint'), 'Unknown child mode')
    args = [str(PYTHON), '-B', str(SCRIPT), '--child', mode,
            '--run-seed', str(RUN_SEED), '--games', str(GAMES)]
    if arm is not None:
        require(arm in ARMS, 'Unknown arm')
        args += ['--arm', arm]
    return args


THREAD_ENV = {key: '1' for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
    'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')}
THREAD_ENV.update(PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1')
CURRENT = None
STATE = None
BASELINE = None


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def save_state():
    STATE['updated_at'] = utcnow()
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=STATE_PATH.parent,
                                     prefix=STATE_PATH.name + '.', suffix='.tmp', delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(STATE, stream, indent=2, allow_nan=False)
        stream.write('\n')
    os.replace(temporary, STATE_PATH)  # only the state file exclusively claimed by this run


def protected_hashes():
    expected = {ROOT / 'experiments/candidates/all18_v3.pth': V3_SHA}
    for side in (0, 1):
        expected[ROOT / f'experiments/releases/20261020_old3_sym3/agent_p{side}.pth'] = OLD_SHA
    actual = {str(path): digest(path) for path in expected}
    require(all(actual[str(path)] == sha for path, sha in expected.items()),
            'Protected V3 candidate or old rollback hash differs from expected')
    # A separately promoted inference winner may already be installed. Capture its
    # actual hashes at pair start, then require them unchanged during this pair.
    for side in (0, 1):
        path = ROOT / f'agents/sherlock/weights/agent_p{side}.pth'
        actual[str(path)] = digest(path)
    return actual


def source_identity():
    head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    names = set()
    for options in (['--cached'], ['--others', '--exclude-standard']):
        result = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z', *options, '--', '*.py'])
        names.update(p.decode() for p in result.split(b'\0') if p)
    files = {str(ROOT / name): digest(ROOT / name) for name in sorted(names)}
    for name in ('env.py', 'params.py', 'wrappers.py'):
        path = ROOT / '.venv/lib/python3.13/site-packages/luxai_s3' / name
        files[str(path)] = digest(path)
    files[str(SCRIPT)] = digest(SCRIPT)
    return {'head': head, 'python_path': str(PYTHON.resolve()),
            'python_sha256': digest(PYTHON.resolve()), 'python_sources': files}


def check_invariants():
    require(source_identity() == BASELINE['code'], 'Code HEAD, Python executable or Python source changed')
    require(protected_hashes() == BASELINE['protected'], 'Protected weights changed')


def tensor_hash(tensors):
    """Stable tensor identity, independent of checkpoint config/container bytes."""
    h = hashlib.sha256()
    for name, tensor in sorted(tensors.items()):
        value = tensor.detach().cpu().contiguous()
        h.update(json.dumps([name, str(value.dtype), list(value.shape)], separators=(',', ':')).encode())
        h.update(b'\0')
        h.update(value.numpy().tobytes())
    return h.hexdigest()


def agent_identity(agent):
    return {'config': agent.cfg.to_dict(), 'q_sha256': tensor_hash(agent.q.state_dict()),
            'target_q_sha256': tensor_hash(agent.target_q.state_dict()),
            'rng_state': agent.rng.bit_generator.state,
            'env_steps': agent.env_steps, 'learn_steps': agent.learn_steps}


def experiment_args(arm):
    a = ARMS[arm]
    return ['--variant', a['variant'], '--run-seed', str(RUN_SEED), '--games', str(GAMES),
            '--sol92-frac', '0.7', '--no-test', '--val-every', '0',
            '--pool-frac', '0', '--date', '20261020', '--out', str(a['run'])]


def child(mode, arm):
    # This entire function runs in a separate process, never in the orchestrator.
    sys.path.insert(0, str(ROOT))
    os.chdir(ROOT)
    os.environ.update(THREAD_ENV)
    from scripts.experiment import limit_threads
    limit_threads()
    from scripts.variants import make_learner, seed_everything, variant_cfg
    if mode == 'preflight':
        records = {}
        for label, a in ARMS.items():
            seed_everything(RUN_SEED)
            agent = make_learner(a['variant'], 'player_0', None, seed=100 * RUN_SEED)
            record = agent_identity(agent)
            cfg = record['config']
            require(cfg == variant_cfg(a['variant']).to_dict(), 'Effective config mismatch')
            for key in ('terminal_death_potential', 'active_targets', 'sap_geometry', 'contest_sap', 'opp_infer', 'smart_sap'):
                require(cfg.get(key, False) is False, f'{label}: {key} must be false or absent')
            require(cfg.get('eps_decay_steps') == a['decay_steps'], 'Exploration decay missing/wrong')
            require(cfg.get('reward_fix') is True and cfg.get('use_shaping') is True
                    and cfg.get('canonical') is True, 'Replication needs canonical reward_fix/shaping')
            require(record['q_sha256'] == record['target_q_sha256'], 'Initial target network mismatch')
            require(record['env_steps'] == record['learn_steps'] == 0, 'Fresh learner required')
            records[label] = record
            del agent
            gc.collect()
        left, right = records['control'], records['slow']
        diff = {k for k in left['config'].keys() | right['config'].keys()
                if left['config'].get(k) != right['config'].get(k)}
        require(diff == {'eps_decay_steps'}, f'Unexpected config difference: {diff}')
        require(left['q_sha256'] == right['q_sha256'] and left['rng_state'] == right['rng_state'],
                'Initial tensors or agent RNG differ')
        write_new(PREFLIGHT, {'created_at': utcnow(), 'seed': RUN_SEED, 'agent_seed': 100 * RUN_SEED, 'games': GAMES,
                             'arms': records, 'versions': {p: importlib.metadata.version(p)
                               for p in ('torch', 'numpy', 'luxai-s3', 'jax')}})
        return
    require(arm in ARMS, 'Child mode needs arm')
    a = ARMS[arm]
    preflight = json.loads(PREFLIGHT.read_text())
    require(preflight['seed'] == RUN_SEED and preflight['games'] == GAMES
            and preflight['agent_seed'] == 100 * RUN_SEED, 'Preflight pair settings mismatch')
    expected = preflight['arms'][arm]
    if mode == 'train':
        from scripts import experiment
        original_make_learner = experiment.make_learner
        def audited_make_learner(*args, **kwargs):
            learner = original_make_learner(*args, **kwargs)
            actual = agent_identity(learner)
            require(actual == expected, 'Actual training initial state differs from preflight')
            write_new(a['run'] / 'initial_identity.json', actual)
            return learner
        # Only audit initialization; return the same learner with untouched RNG/state.
        experiment.make_learner = audited_make_learner
        forbidden = ('weights', 'manifest.json', 'train.csv', 'val.csv', 'eval.csv', 'log.txt')
        require(not any((a['run'] / name).exists() for name in forbidden), 'Training output already exists')
        experiment.main(experiment_args(arm))
        return
    require(mode == 'checkpoint', 'Unknown child mode')
    import torch
    weights = a['run'] / 'weights/agent.pth'
    checkpoint = torch.load(weights, map_location='cpu', weights_only=False)
    require(checkpoint['cfg'] == expected['config'], 'Final checkpoint effective config changed')
    require(not checkpoint.get('ensemble'), 'Replication must produce a fresh single network')
    require(checkpoint['env_steps'] > 0 and checkpoint['learn_steps'] > 0, 'No learning recorded')
    require(set(checkpoint['q']) == set(checkpoint['target_q']), 'q/target tensor keys differ')
    for network in ('q', 'target_q'):
        require(bool(checkpoint[network]), f'Empty {network}')
        for name, tensor in checkpoint[network].items():
            require(isinstance(tensor, torch.Tensor) and bool(torch.isfinite(tensor).all().item()),
                    f'Invalid or non-finite {network}.{name}')
            peer = checkpoint['target_q' if network == 'q' else 'q'][name]
            require(tensor.shape == peer.shape and tensor.dtype == peer.dtype,
                    f'q/target tensor shape or dtype differs: {name}')
    write_new(a['run'] / 'final_identity.json', {
        'file_sha256': digest(weights), 'q_sha256': tensor_hash(checkpoint['q']),
        'target_q_sha256': tensor_hash(checkpoint['target_q']), 'config': checkpoint['cfg'],
        'env_steps': checkpoint['env_steps'], 'learn_steps': checkpoint['learn_steps'],
        'q_finite': True, 'target_q_finite': True})


def stop_group(process):
    if process is None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    until = min(time.monotonic() + 5, time.monotonic() + max(0, DEADLINE - time.time()))
    while time.monotonic() < until:
        process.poll()
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            return
        time.sleep(.1)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass


def interrupted(signum, frame):
    raise InterruptedError(f'Received signal {signum}')


def run_process(label, command, *, heavy=True):
    global CURRENT
    require(allowed_start(time.time(), heavy), f'Too late to start {label}')
    check_invariants()
    log = ANALYSIS / f'{PREFIX}_{label}.log'
    job = {'label': label, 'command': command, 'started_at': utcnow(),
           'complete': False, 'log': str(log)}
    STATE['jobs'].append(job)
    save_state()
    try:
        with log.open('xb') as output, selectors.DefaultSelector() as selector:
            require(allowed_start(time.time(), heavy), f'Too late to spawn {label}')
            CURRENT = subprocess.Popen(command, cwd=ROOT, env={**os.environ, **THREAD_ENV},
                                       start_new_session=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
            job['pid'] = CURRENT.pid
            save_state()
            selector.register(CURRENT.stdout, selectors.EVENT_READ)
            next_integrity = time.monotonic() + 30
            while selector.get_map():
                require(time.time() < STOP_AT, 'Replication deadline reached')
                for key, _ in selector.select(timeout=1):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if data:
                        output.write(data); output.flush()
                        sys.stdout.buffer.write(data); sys.stdout.buffer.flush()
                    else:
                        selector.unregister(key.fileobj)
                if time.monotonic() >= next_integrity:
                    check_invariants()
                    next_integrity = time.monotonic() + 30
            returncode = CURRENT.wait(timeout=max(.1, STOP_AT - time.time()))
            job['returncode'] = returncode
            require(returncode == 0, f'{label} failed with exit {returncode}')
        check_invariants()
        job['complete'] = True
    finally:
        if CURRENT is not None:
            if not job['complete']:
                stop_group(CURRENT)
            CURRENT.stdout.close()
            CURRENT = None
        job['finished_at'] = utcnow()
        save_state()


def read_rows(path):
    with Path(path).open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    require(all(row.get('point_counting_version') == '2' for row in rows), 'Wrong point version')
    for row in rows:
        require(float(row['result']) in (0, .5, 1), 'Invalid game result')
        for key in ('our_points', 'opp_points', 'our_wins', 'opp_wins'):
            require(math.isfinite(float(row[key])) and float(row[key]) >= 0, f'Invalid {key}')
        own, opp = float(row['our_wins']), float(row['opp_wins'])
        require(own.is_integer() and opp.is_integer() and 0 <= own <= 3 and 0 <= opp <= 3
                and own + opp <= 3, 'Invalid three-match win totals')
        expected_result = 1.0 if own > opp else 0.0 if own < opp else 0.5
        require(float(row['result']) == expected_result, 'Game result inconsistent with match wins')
        require(int(row['steps']) == 303, 'Expected a complete three-match course game')
    return rows


def validate_training(arm):
    a = ARMS[arm]
    rows = read_rows(a['run'] / 'train.csv')
    require(len(rows) == GAMES, f'{arm}: expected {GAMES} training rows')
    previous_env = previous_learn = 0
    warmup_nan_losses = 0
    for game, row in enumerate(rows):
        require((int(row['game']), int(row['seed']), row['side'], row['opponent']) ==
                schedule_key(RUN_SEED, GAMES, game), 'Wrong training schedule/key')
        env_steps, learn_steps = int(row['env_steps']), int(row['learn_steps'])
        require(env_steps == (game + 1) * 303 and env_steps > previous_env
                and learn_steps >= previous_learn, 'Invalid training step counters')
        loss = float(row['mean_loss'])
        if math.isnan(loss):
            require(learn_steps == 0, 'NaN mean_loss after learning began')
            warmup_nan_losses += 1
        else:
            require(math.isfinite(loss), 'Non-finite mean_loss')
        previous_env, previous_learn = env_steps, learn_steps
    require(previous_learn > 0 and math.isfinite(float(rows[-1]['mean_loss'])),
            'Final mean_loss must be finite after actual learning')
    manifest = json.loads((a['run'] / 'manifest.json').read_text())
    require(manifest.get('status') == 'done' and manifest['train_games'] == GAMES
            and manifest['run_seed'] == RUN_SEED and manifest['variant'] == a['variant']
            and manifest['val_seeds'] == [] and manifest['test_seeds'] == [], 'Training manifest incomplete/wrong')
    preflight = json.loads(PREFLIGHT.read_text())
    require(preflight['seed'] == RUN_SEED and preflight['games'] == GAMES
            and preflight['agent_seed'] == 100 * RUN_SEED, 'Preflight pair settings mismatch')
    expected = preflight['arms'][arm]
    require(manifest['config'] == expected['config'], 'Training manifest effective config mismatch')
    initial = json.loads((a['run'] / 'initial_identity.json').read_text())
    final = json.loads((a['run'] / 'final_identity.json').read_text())
    require(initial == expected and final['config'] == expected['config'], 'Recorded model identity mismatch')
    require(int(rows[-1]['env_steps']) == final['env_steps']
            and int(rows[-1]['learn_steps']) == final['learn_steps'], 'Checkpoint does not match final training row')
    require(final.get('q_finite') is True and final.get('target_q_finite') is True,
            'Final tensor finiteness not verified')
    require(digest(a['run'] / 'weights/agent.pth') == final['file_sha256'], 'Checkpoint changed')
    return {'complete': True, 'rows': GAMES, 'map_pairs': GAMES // 2,
            'nan_losses_before_learning': warmup_nan_losses, 'final_mean_loss': float(rows[-1]['mean_loss']),
            'train_csv_sha256': digest(a['run'] / 'train.csv'), 'final': final}


def validate_evaluation(arm):
    rows = read_rows(ARMS[arm]['eval'])
    keys = [(int(r['seed']), r['side'], r['opponent']) for r in rows]
    expected = {(seed, side, opponent) for seed in range(500720, 500780)
                for side in ('player_0', 'player_1') for opponent in ('default', 'solution92')}
    require(len(rows) == 240 and len(set(keys)) == 240 and set(keys) == expected,
            'Evaluation rows/keys incomplete or duplicated')
    return {'complete': True, 'rows': 240, 'csv_sha256': digest(ARMS[arm]['eval']),
            'mean_result': {opponent: sum(float(r['result']) for r in rows if r['opponent'] == opponent) / 120
                            for opponent in ('default', 'solution92')}}


def orchestrate(minimum_seconds=None):
    global STATE, BASELINE
    require((ROOT / 'agents/sherlock/main.py').is_file(), 'Run from the repository or archived tools path')
    check_admission(time.time(), minimum_seconds)
    required_new = [STATE_PATH, PREFLIGHT]
    required_new += [a['run'] for a in ARMS.values()] + [a['eval'] for a in ARMS.values()]
    required_new += [ANALYSIS / f'{PREFIX}_{label}.log' for label in
                    ('preflight', 'train_control', 'train_slow', 'checkpoint_control',
                     'checkpoint_slow', 'eval_control', 'eval_slow')]
    require(not any(path.exists() for path in required_new), 'Refusing existing replication output')
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    COMPARE.mkdir(parents=True, exist_ok=True)
    BASELINE = {'code': source_identity(), 'protected': protected_hashes()}
    STATE = {'started_at': utcnow(), 'complete': False, 'status': 'running',
             'deadline_utc': '2026-10-21T04:00:00Z', 'new_work_cutoff_utc': '2026-10-21T03:00:00Z',
             'baseline': BASELINE, 'thread_environment': THREAD_ENV,
             'run_seed': RUN_SEED, 'games_per_arm': GAMES,
             'controlled_difference': {'eps_decay_steps': {'control': 60000, 'slow': 454500}},
             'admission_minimum_seconds': minimum_seconds,
             'admission_policy': 'Root manually admits one complete pair; no automatic next pair',
             'jobs': [], 'arms': {k: {'variant': a['variant'], 'run': str(a['run']),
                                    'eval': str(a['eval']), 'experiment_argv': experiment_args(k)}
                                  for k, a in ARMS.items()}}
    write_new(STATE_PATH, STATE)  # persistent exclusive claim; partial runs cannot silently resume
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    try:
        run_process('preflight', child_command('preflight'))
        STATE['preflight'] = json.loads(PREFLIGHT.read_text())
        save_state()
        # Both trainings finish before evaluation; one child process tree at a time.
        for arm, a in ARMS.items():
            require(time.time() < START_CUTOFF, f'Too late to start {arm}')
            a['run'].mkdir(parents=True, exist_ok=False)
            run_process('train_' + arm, child_command('train', arm))
            run_process('checkpoint_' + arm, child_command('checkpoint', arm), heavy=False)
            STATE['arms'][arm]['training'] = validate_training(arm)
            save_state()
        for arm, a in ARMS.items():
            require(not a['eval'].exists(), 'Evaluation output already exists')
            frozen = STATE['arms'][arm]['training']['final']['file_sha256']
            weights = a['run'] / 'weights/agent.pth'
            require(digest(weights) == frozen, 'Checkpoint changed before evaluation')
            run_process('eval_' + arm, [str(PYTHON), '-B', '-m', 'scripts.par_eval',
                        '--weights', str(weights), '--first', '720', '--n', '60',
                        '--workers', '2', '--opponents', 'default,solution92', '--out', str(a['eval'])])
            require(digest(weights) == frozen, 'Evaluation modified checkpoint')
            STATE['arms'][arm]['evaluation'] = validate_evaluation(arm)
            save_state()
        check_invariants()
        STATE.update(status='complete', complete=True)
    except BaseException as exc:
        stop_group(CURRENT)
        STATE.update(status='incomplete', complete=False, error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        try:
            check_invariants()
            STATE['final_integrity_ok'] = True
        except Exception as exc:
            STATE.update(final_integrity_ok=False, complete=False, status='incomplete',
                         integrity_error=f'{type(exc).__name__}: {exc}')
        STATE['finished_at'] = utcnow()
        save_state()
        if not STATE['final_integrity_ok']:
            raise RuntimeError(STATE['integrity_error'])


def self_test():
    """Pure stdlib/AST fixtures: no agent imports, processes, games or file writes."""
    import ast
    import unittest

    class Fixtures(unittest.TestCase):
        def test_schedule_against_actual_protocol_ast(self):
            # Execute only the protocol's literal constants and pure scheduling
            # functions, never any repository imports or training code.
            source = ast.parse((ROOT / 'scripts/protocol.py').read_text())
            names = {'TRAIN_SEED_BASE', 'TRAIN_SEED_STRIDE', 'VAL_SEED_BASE',
                     'SIDES', 'CURRICULUM_WARMUP_FRAC'}
            functions = {'train_seed', 'train_side', 'train_opponent'}
            selected = [
                node for node in source.body
                if (isinstance(node, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id in names for t in node.targets))
                or (isinstance(node, ast.FunctionDef) and node.name in functions)
            ]
            namespace = {}
            exec(compile(ast.Module(body=selected, type_ignores=[]), 'protocol_schedule_ast', 'exec'),
                 namespace)
            for seed in (47, 48, 49):
                for games in (3000,):
                    with self.subTest(seed=seed, games=games):
                        for game in range(games):
                            expected = (game, namespace['train_seed'](seed, game),
                                        namespace['train_side'](game),
                                        namespace['train_opponent'](game, games, .7, 0))
                            self.assertEqual(schedule_key(seed, games, game), expected)

        def test_schedule_all_seeds_and_horizons(self):
            for seed in (47, 48, 49):
                for games in (3000,):
                    with self.subTest(seed=seed, games=games):
                        rows = [schedule_key(seed, games, g) for g in range(games)]
                        self.assertEqual(len(rows), games)
                        self.assertEqual(rows[0][1], seed * 10000)
                        self.assertEqual(rows[-1][1], seed * 10000 + games // 2 - 1)
                        self.assertLess(rows[-1][1], 500000)
                        self.assertTrue(all(r[3] == 'default' for r in rows[:games // 4]))
                        self.assertTrue(any(r[3] == 'solution92' for r in rows[games // 4:]))
                        for g in range(0, games, 2):
                            self.assertEqual(rows[g][1], rows[g + 1][1])
                            self.assertEqual(rows[g][3], rows[g + 1][3])
                            self.assertEqual((rows[g][2], rows[g + 1][2]), ('player_0', 'player_1'))
                        for g in (games // 4, games // 4 + 1, games - 1):
                            expected = 'solution92' if ((g // 2) * .6180339887) % 1 < .7 else 'default'
                            self.assertEqual(rows[g][3], expected)

        def test_paths_unique_and_horizon_cannot_resume(self):
            all_paths = []
            for seed in (47, 48, 49):
                first = settings('/fixture/repo', seed, 3000)
                with self.assertRaises(RuntimeError):
                    settings('/fixture/repo', seed, 2000)
                prefix, state, preflight, arms = first
                self.assertEqual(prefix, f'exploration_replication_s{seed}')
                paths = [state, preflight] + [a[k] for a in arms.values() for k in ('run', 'eval')]
                self.assertTrue(all('pilot' not in str(p) and 's46' not in str(p) for p in paths))
                all_paths.extend(paths)
            self.assertEqual(len(all_paths), len(set(all_paths)))

        def test_root_portability(self):
            self.assertEqual(repository_root('/fixture/repo/experiments/analysis/autonomous_20261020/tools/exploration_replication.py', '/ignored'), Path('/fixture/repo'))
            self.assertEqual(repository_root('/tmp/exploration_replication.py', '/fixture/repo'), Path('/fixture/repo'))

        def test_child_seed_and_horizon_forwarded(self):
            for seed in (47, 48, 49):
                for games in (3000,):
                    configure(seed, games)
                    for mode, arm in (('preflight', None), ('train', 'control'),
                                      ('train', 'slow'), ('checkpoint', 'control'), ('checkpoint', 'slow')):
                        command = child_command(mode, arm)
                        self.assertEqual(command[command.index('--run-seed') + 1], str(seed))
                        self.assertEqual(command[command.index('--games') + 1], str(games))
                    for arm in ARMS:
                        command = experiment_args(arm)
                        self.assertEqual(command[command.index('--run-seed') + 1], str(seed))
                        self.assertEqual(command[command.index('--games') + 1], str(games))
                        self.assertIn('--no-test', command)
                        self.assertEqual(command[command.index('--val-every') + 1], '0')
                        self.assertEqual(command[command.index('--pool-frac') + 1], '0')

        def test_deadlines_and_admission(self):
            self.assertTrue(allowed_start(START_CUTOFF - .001))
            self.assertFalse(allowed_start(START_CUTOFF))
            self.assertTrue(allowed_start(START_CUTOFF, heavy=False))
            self.assertFalse(allowed_start(STOP_AT, heavy=False))
            check_admission(START_CUTOFF - 100, None)
            check_admission(START_CUTOFF - 100, 100)
            for now, minimum in ((START_CUTOFF, None), (START_CUTOFF - 100, 4000),
                                 (START_CUTOFF - 100, 0), (START_CUTOFF - 100, float('nan'))):
                with self.assertRaises(RuntimeError):
                    check_admission(now, minimum)

        def test_invalid_settings(self):
            for seed, games in ((46, 3000), (50, 3000), (47, 400), (47, 2000), (47, 3001)):
                with self.assertRaises(RuntimeError):
                    settings('/fixture', seed, games)
            for game in (-1, 3000):
                with self.assertRaises(RuntimeError):
                    schedule_key(47, 3000, game)

        def test_ast_import_and_dispatch(self):
            tree = ast.parse(SCRIPT.read_text())
            for node in tree.body:
                if isinstance(node, ast.Import):
                    self.assertTrue(all(n.name.split('.')[0] in sys.stdlib_module_names for n in node.names))
                elif isinstance(node, ast.ImportFrom):
                    self.assertIn(node.module.split('.')[0], sys.stdlib_module_names)
            orchestrator = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'orchestrate')
            calls = [n for n in ast.walk(orchestrator) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Name) and n.func.id == 'child_command']
            self.assertEqual(sorted(n.args[0].value for n in calls), ['checkpoint', 'preflight', 'train'])

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Fixtures)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--run', action='store_true')
    mode.add_argument('--child', choices=('preflight', 'train', 'checkpoint'))
    mode.add_argument('--self-test', action='store_true')
    parser.add_argument('--arm', choices=('control', 'slow'))
    parser.add_argument('--run-seed', type=int, choices=(47, 48, 49))
    parser.add_argument('--games', type=int, choices=(3000,))
    parser.add_argument('--minimum-seconds', type=float, default=None,
                        help='Optional manually admitted full-pair runtime budget; not an estimate')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.run_seed is None or args.games is None:
        parser.error('--run-seed and --games are required for every run/child')
    if args.child in ('train', 'checkpoint') and args.arm is None:
        parser.error('train/checkpoint child requires --arm')
    if args.child == 'preflight' and args.arm is not None:
        parser.error('preflight covers both arms')
    if args.run and args.arm is not None:
        parser.error('--run always executes both arms')
    configure(args.run_seed, args.games)
    if args.child:
        child(args.child, args.arm)
    else:
        orchestrate(args.minimum_seconds)


if __name__ == '__main__':
    main()
