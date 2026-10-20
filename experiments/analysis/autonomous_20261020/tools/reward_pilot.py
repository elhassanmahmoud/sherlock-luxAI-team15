"""Prepared paired pilot. RUN ONLY AFTER ROOT REVIEW: python this_file.py --run.

The parent imports only stdlib. Torch/agent imports occur solely in short child
processes or the one active training process. No resume or overwrite is allowed.
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

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = Path(__file__).resolve()
PYTHON = ROOT / '.venv/bin/python'
ANALYSIS = ROOT / 'experiments/analysis/autonomous_20261020'
COMPARE = ROOT / 'experiments/compare/autonomous_20261020'
STATE_PATH = ANALYSIS / 'reward_pilot_state.json'
PREFLIGHT = ANALYSIS / 'reward_pilot_preflight.json'
START_CUTOFF = datetime(2026, 10, 21, 3, tzinfo=timezone.utc).timestamp()
DEADLINE = datetime(2026, 10, 21, 4, tzinfo=timezone.utc).timestamp()
STOP_AT = DEADLINE - 10  # reserve time for group termination and final state
V3_SHA = 'aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935'
OLD_SHA = '3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158'
ARMS = {
    'control': {'variant': 'full_rules_v3', 'enabled': False,
                'run': ROOT / 'experiments/runs/20261020_full_rules_v3_s46_terminal_control',
                'eval': COMPARE / 'pilot_terminal_control.csv'},
    'fix': {'variant': 'full_rules_v3_terminal', 'enabled': True,
            'run': ROOT / 'experiments/runs/20261020_full_rules_v3_terminal_s46_terminal_fix',
            'eval': COMPARE / 'pilot_terminal_fix.csv'},
}
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
        expected[ROOT / f'agents/sherlock/weights/agent_p{side}.pth'] = V3_SHA
        expected[ROOT / f'experiments/releases/20261020_old3_sym3/agent_p{side}.pth'] = OLD_SHA
    actual = {str(path): digest(path) for path in expected}
    require(all(actual[str(path)] == sha for path, sha in expected.items()),
            'Protected V3 release/candidate or old rollback hash differs from expected')
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
    return ['--variant', a['variant'], '--run-seed', '46', '--games', '400',
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
            seed_everything(46)
            agent = make_learner(a['variant'], 'player_0', None, seed=4600)
            record = agent_identity(agent)
            cfg = record['config']
            require(cfg == variant_cfg(a['variant']).to_dict(), 'Effective config mismatch')
            for key in ('active_targets', 'sap_geometry'):
                require(cfg.get(key, False) is False, f'{label}: {key} must be false or absent')
            require(cfg.get('terminal_death_potential') is a['enabled'], 'Reward flag missing/wrong')
            require(cfg.get('reward_fix') is True and cfg.get('use_shaping') is True
                    and cfg.get('canonical') is True, 'Pilot needs canonical reward_fix/shaping')
            require(record['q_sha256'] == record['target_q_sha256'], 'Initial target network mismatch')
            require(record['env_steps'] == record['learn_steps'] == 0, 'Fresh learner required')
            records[label] = record
            del agent
            gc.collect()
        left, right = records['control'], records['fix']
        diff = {k for k in left['config'].keys() | right['config'].keys()
                if left['config'].get(k) != right['config'].get(k)}
        require(diff == {'terminal_death_potential'}, f'Unexpected config difference: {diff}')
        require(left['q_sha256'] == right['q_sha256'] and left['rng_state'] == right['rng_state'],
                'Initial tensors or agent RNG differ')
        write_new(PREFLIGHT, {'created_at': utcnow(), 'seed': 46, 'agent_seed': 4600,
                             'arms': records, 'versions': {p: importlib.metadata.version(p)
                               for p in ('torch', 'numpy', 'luxai-s3', 'jax')}})
        return
    require(arm in ARMS, 'Child mode needs arm')
    a = ARMS[arm]
    expected = json.loads(PREFLIGHT.read_text())['arms'][arm]
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
    require(not checkpoint.get('ensemble'), 'Pilot must produce a fresh single network')
    require(checkpoint['env_steps'] > 0 and checkpoint['learn_steps'] > 0, 'No learning recorded')
    write_new(a['run'] / 'final_identity.json', {
        'file_sha256': digest(weights), 'q_sha256': tensor_hash(checkpoint['q']),
        'target_q_sha256': tensor_hash(checkpoint['target_q']), 'config': checkpoint['cfg'],
        'env_steps': checkpoint['env_steps'], 'learn_steps': checkpoint['learn_steps']})


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
    require(time.time() < (START_CUTOFF if heavy else STOP_AT), f'Too late to start {label}')
    check_invariants()
    log = ANALYSIS / f'reward_pilot_{label}.log'
    job = {'label': label, 'command': command, 'started_at': utcnow(),
           'complete': False, 'log': str(log)}
    STATE['jobs'].append(job)
    save_state()
    try:
        with log.open('xb') as output, selectors.DefaultSelector() as selector:
            require(time.time() < (START_CUTOFF if heavy else STOP_AT), f'Too late to spawn {label}')
            CURRENT = subprocess.Popen(command, cwd=ROOT, env={**os.environ, **THREAD_ENV},
                                       start_new_session=True, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
            job['pid'] = CURRENT.pid
            save_state()
            selector.register(CURRENT.stdout, selectors.EVENT_READ)
            next_integrity = time.monotonic() + 30
            while selector.get_map():
                require(time.time() < STOP_AT, 'Pilot deadline reached')
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
    require(len(rows) == 400, f'{arm}: expected 400 training rows')
    for game, row in enumerate(rows):
        expected_opp = 'default' if game < 100 or ((game // 2) * .6180339887) % 1 >= .7 else 'solution92'
        require((int(row['game']), int(row['seed']), row['side'], row['opponent']) ==
                (game, 460000 + game // 2, f'player_{game % 2}', expected_opp), 'Wrong training schedule/key')
    manifest = json.loads((a['run'] / 'manifest.json').read_text())
    require(manifest.get('status') == 'done' and manifest['train_games'] == 400
            and manifest['run_seed'] == 46 and manifest['variant'] == a['variant']
            and manifest['val_seeds'] == [] and manifest['test_seeds'] == [], 'Training manifest incomplete/wrong')
    expected = json.loads(PREFLIGHT.read_text())['arms'][arm]
    require(manifest['config'] == expected['config'], 'Training manifest effective config mismatch')
    initial = json.loads((a['run'] / 'initial_identity.json').read_text())
    final = json.loads((a['run'] / 'final_identity.json').read_text())
    require(initial == expected and final['config'] == expected['config'], 'Recorded model identity mismatch')
    require(int(rows[-1]['env_steps']) == final['env_steps']
            and int(rows[-1]['learn_steps']) == final['learn_steps'], 'Checkpoint does not match final training row')
    require(digest(a['run'] / 'weights/agent.pth') == final['file_sha256'], 'Checkpoint changed')
    return {'complete': True, 'rows': 400, 'map_pairs': 200,
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


def orchestrate():
    global STATE, BASELINE
    require(time.time() < START_CUTOFF, 'Pilot start cutoff has passed')
    required_new = [STATE_PATH, PREFLIGHT]
    required_new += [a['run'] for a in ARMS.values()] + [a['eval'] for a in ARMS.values()]
    required_new += [ANALYSIS / f'reward_pilot_{label}.log' for label in
                    ('preflight', 'train_control', 'train_fix', 'checkpoint_control',
                     'checkpoint_fix', 'eval_control', 'eval_fix')]
    require(not any(path.exists() for path in required_new), 'Refusing existing pilot output')
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    COMPARE.mkdir(parents=True, exist_ok=True)
    BASELINE = {'code': source_identity(), 'protected': protected_hashes()}
    STATE = {'started_at': utcnow(), 'complete': False, 'status': 'running',
             'deadline_utc': '2026-10-21T04:00:00Z', 'new_work_cutoff_utc': '2026-10-21T03:00:00Z',
             'baseline': BASELINE, 'thread_environment': THREAD_ENV,
             'jobs': [], 'arms': {k: {'variant': a['variant'], 'run': str(a['run']),
                                    'eval': str(a['eval']), 'experiment_argv': experiment_args(k)}
                                  for k, a in ARMS.items()}}
    write_new(STATE_PATH, STATE)  # persistent exclusive claim; partial runs cannot silently resume
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    try:
        run_process('preflight', [str(PYTHON), '-B', str(SCRIPT), '--child', 'preflight'])
        STATE['preflight'] = json.loads(PREFLIGHT.read_text())
        save_state()
        # Both trainings finish before evaluation; one child process tree at a time.
        for arm, a in ARMS.items():
            require(time.time() < START_CUTOFF, f'Too late to start {arm}')
            a['run'].mkdir(parents=True, exist_ok=False)
            run_process('train_' + arm, [str(PYTHON), '-B', str(SCRIPT), '--child', 'train', '--arm', arm])
            run_process('checkpoint_' + arm, [str(PYTHON), '-B', str(SCRIPT), '--child', 'checkpoint', '--arm', arm], heavy=False)
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--run', action='store_true')
    mode.add_argument('--child', choices=('preflight', 'train', 'checkpoint'))
    parser.add_argument('--arm', choices=tuple(ARMS))
    args = parser.parse_args()
    if args.child:
        child(args.child, args.arm)
    else:
        orchestrate()


if __name__ == '__main__':
    main()
