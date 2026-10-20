"""Prepared only: install in experiments/analysis/autonomous_20261020/tools/.
Run with --run after review and after all other evaluation/training jobs finish.
Three sequential inference evaluations; no training, promotion, or outcome selection.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import selectors
import shlex
import re
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = Path(__file__).resolve()
PYTHON = ROOT / '.venv/bin/python'
OUT = ROOT / 'experiments/compare/autonomous_20261020/inference_development2'
REFERENCE = ROOT / 'experiments/compare/autonomous_20261020/dev_reference.csv'
STATE_PATH = OUT / 'state.json'
WEIGHTS = ROOT / 'experiments/candidates/all18_v3.pth'
V3_SHA = 'aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935'
CUTOFF = datetime(2026, 10, 21, 3, tzinfo=timezone.utc).timestamp()
DEADLINE = datetime(2026, 10, 21, 4, tzinfo=timezone.utc).timestamp()
STOP_AT = DEADLINE - 10
THREAD_ENV = {k: '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
    'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')}
THREAD_ENV.update(PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1')
CURRENT = None
STATE = None
BASELINE = None


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def snapshot():
    head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    names = set()
    for options in (['--cached'], ['--others', '--exclude-standard']):
        raw = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z', *options, '--', '*.py'])
        names.update(p.decode() for p in raw.split(b'\0') if p)
    files = {str(ROOT / n): digest(ROOT / n) for n in sorted(names)}
    for name in ('env.py', 'params.py', 'wrappers.py'):
        p = ROOT / '.venv/lib/python3.13/site-packages/luxai_s3' / name
        files[str(p)] = digest(p)
    files[str(SCRIPT)] = digest(SCRIPT)
    protected = [WEIGHTS, REFERENCE]
    for side in (0, 1):
        protected += [ROOT / f'agents/sherlock/weights/agent_p{side}.pth',
                      ROOT / f'experiments/releases/20261020_old3_sym3/agent_p{side}.pth']
    hashes = {str(p): digest(p) for p in protected}
    require(hashes[str(WEIGHTS)] == V3_SHA, 'Fixed V3 candidate hash mismatch')
    return dict(head=head, python_path=str(PYTHON.resolve()), python_sha256=digest(PYTHON.resolve()),
                python_sources=files, protected_sha256=hashes)


def heavy_python_command(command):
    """Inspect executable and exact invocation, never arbitrary command text."""
    try:
        args = shlex.split(command)
    except ValueError:
        return False
    if not args or not re.fullmatch(r'python(?:\d+(?:\.\d+)*)?', Path(args[0]).name, re.I):
        return False
    modules = {'scripts.par_eval', 'scripts.experiment', 'scripts.train', 'scripts.ppo_train',
               'scripts.evaluate', 'scripts.compare_weights', 'scripts.finetune'}
    scripts = {'reward_pilot.py', 'sherlock-reward-pilot-20261020.py',
               'reward_replication.py', 'sherlock-reward-replication-20261020.py',
               'inference_development2.py', 'sherlock-inference-development2-20261020.py',
               'sherlock-target-diagnosis-20261020.py',
               'par_eval.py', 'experiment.py', 'train.py', 'ppo_train.py',
               'evaluate.py', 'compare_weights.py', 'finetune.py'}
    # Interpreter options can precede the execution target. Stop at that target:
    # a read-only script's later arguments must never be interpreted as runners.
    i = 1
    while i < len(args):
        value = args[i]
        if value == '-m':
            return i + 1 < len(args) and args[i + 1] in modules
        if value == '-c':
            # multiprocessing uses -c with this standard bootstrap, not a script.
            return (i + 1 < len(args) and args[-1] == '--multiprocessing-fork'
                and re.match(r'^from multiprocessing\.spawn import spawn_main;\s*spawn_main\(',
                             ' '.join(args[i + 1:-1])) is not None)
        if value == '--':
            return i + 1 < len(args) and Path(args[i + 1]).name in scripts
        if value in ('-W', '-X', '--check-hash-based-pycs'):
            i += 2
            continue
        if value.startswith('-') and value != '-':
            i += 1
            continue
        return Path(value).name in scripts
    return False


def no_other_jobs():
    """Conservative read-only admission check; never terminate another job."""
    raw = subprocess.check_output(['ps', '-axo', 'pid=,pgid=,args='], text=True)
    allowed_groups = {os.getpgrp()}
    if CURRENT is not None:
        allowed_groups.add(CURRENT.pid)
    conflicts = []
    for line in raw.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) != 3:
            continue
        pid, group, command = parts
        if int(group) in allowed_groups or int(pid) == os.getpid():
            continue
        if heavy_python_command(command):
            conflicts.append({'pid': int(pid), 'command': command})
    require(not conflicts, f'Other training/evaluation jobs detected: {conflicts}')


def invariants():
    require(snapshot() == BASELINE, 'Frozen HEAD, Python/source, reference or protected weights changed')
    no_other_jobs()


def save_state():
    STATE['updated_at'] = now()
    with tempfile.NamedTemporaryFile(mode='w', dir=OUT, prefix='state.', suffix='.tmp', delete=False) as f:
        json.dump(STATE, f, indent=2, allow_nan=False)
        f.write('\n')
        temporary = Path(f.name)
    os.replace(temporary, STATE_PATH)  # Own state in exclusively created output directory.


def read_rows(path):
    with Path(path).open(newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        require(fields is not None and len(fields) == len(set(fields)), 'Missing/duplicate CSV columns')
        rows = list(reader)
    expected = {(str(seed), side, opp) for seed in range(500720, 500780)
                for side in ('player_0', 'player_1') for opp in ('default', 'solution92')}
    indexed = {}
    for row in rows:
        require(None not in row and all(v is not None for v in row.values()), 'Malformed CSV row')
        key = tuple(row[k] for k in ('seed', 'side', 'opponent'))
        require(key not in indexed, f'Duplicate game key {key}')
        require(row['steps'] == '303' and row['point_counting_version'] == '2', 'Incomplete/wrong scoring game')
        for k, value in row.items():
            if k in ('side', 'opponent'):
                continue
            require(math.isfinite(float(value)), f'Nonfinite numeric field {k}')
        own, opp = float(row['our_wins']), float(row['opp_wins'])
        require(own.is_integer() and opp.is_integer() and 0 <= own <= 3 and 0 <= opp <= 3
                and own + opp <= 3, 'Invalid match wins')
        require(float(row['result']) == (1 if own > opp else 0 if own < opp else .5), 'Inconsistent result')
        indexed[key] = row
    require(len(rows) == 240 and set(indexed) == expected, 'Expected exact 240 development game keys')
    return fields, indexed


def stop_group(process):
    if process is None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    until = time.monotonic() + min(5, max(0, DEADLINE - time.time()))
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


def run_job(label, overrides):
    global CURRENT
    require(time.time() < CUTOFF, 'No new heavy job after 05:00 Berlin')
    invariants()
    output = OUT / f'phase2_{label}.csv'
    command = [str(PYTHON), '-B', '-m', 'scripts.par_eval', '--weights', str(WEIGHTS),
               '--first', '720', '--n', '60', '--workers', '2',
               '--opponents', 'default,solution92', '--out', str(output)]
    for value in overrides:
        command += ['--set', value]
    require(not output.exists(), 'Refusing existing CSV')
    job = dict(label=label, command=command, started_at=now(), complete=False,
               output=str(output), log=str(OUT / f'phase2_{label}.log'))
    STATE['jobs'].append(job)
    save_state()
    try:
        with Path(job['log']).open('xb') as log, selectors.DefaultSelector() as selector:
            require(time.time() < CUTOFF, 'Heavy job cutoff reached before spawn')
            CURRENT = subprocess.Popen(command, cwd=ROOT, env={**os.environ, **THREAD_ENV},
                start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            job['pid'] = CURRENT.pid
            save_state()
            selector.register(CURRENT.stdout, selectors.EVENT_READ)
            next_check = time.monotonic() + 30
            while selector.get_map():
                require(time.time() < STOP_AT, '06:00 Berlin deadline approaching')
                for key, _ in selector.select(timeout=1):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if data:
                        log.write(data); log.flush()
                        sys.stdout.buffer.write(data); sys.stdout.buffer.flush()
                    else:
                        selector.unregister(key.fileobj)
                if time.monotonic() >= next_check:
                    invariants()
                    next_check = time.monotonic() + 30
            job['returncode'] = CURRENT.wait(timeout=max(.1, STOP_AT - time.time()))
            require(job['returncode'] == 0, f'{label} process failed')
        invariants()
        fields, rows = read_rows(output)
        if label == 'reference':
            old_fields, old_rows = read_rows(REFERENCE)
            require(set(fields) == set(old_fields), 'Baseline CSV schema changed')
            for key, row in rows.items():
                require({k: v for k, v in row.items() if k != 'secs'} ==
                        {k: v for k, v in old_rows[key].items() if k != 'secs'},
                        f'Baseline non-time fields differ: {key}')
            job['baseline_non_time_exact'] = True
        job.update(complete=True, rows=240, exact_keys_valid=True, csv_sha256=digest(output))
    finally:
        if CURRENT is not None:
            if not job['complete']:
                stop_group(CURRENT)
            CURRENT.stdout.close()
            CURRENT = None
        job['finished_at'] = now()
        save_state()


def interrupted(signum, frame):
    raise InterruptedError(f'Received signal {signum}')


def main():
    global STATE, BASELINE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    require(args.run, 'Prepared only: explicit --run required')
    require((ROOT / 'scripts/par_eval.py').is_file(), 'Install at the documented portable path first')
    require(time.time() < CUTOFF, 'No new heavy jobs after 05:00 Berlin')
    no_other_jobs()
    read_rows(REFERENCE)
    BASELINE = snapshot()
    OUT.mkdir(exist_ok=False)  # Refuse every previous/partial run; never resume or overwrite.
    STATE = dict(started_at=now(), status='running', complete=False, baseline=BASELINE,
                 deadline_utc='2026-10-21T04:00:00Z', new_work_cutoff_utc='2026-10-21T03:00:00Z',
                 reference=str(REFERENCE), thread_env=THREAD_ENV, jobs=[])
    save_state()
    signal.signal(signal.SIGINT, interrupted)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    try:
        run_job('reference', ['active_targets=false', 'sap_geometry=false'])
        run_job('active', ['active_targets=true', 'sap_geometry=false'])
        run_job('sap', ['active_targets=false', 'sap_geometry=true'])
        invariants()
        STATE.update(status='complete', complete=True, final_identity=snapshot())
    except BaseException as exc:
        stop_group(CURRENT)
        STATE.update(status='incomplete', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        STATE['finished_at'] = now()
        save_state()


if __name__ == '__main__':
    main()
