"""Single-use, two-worker supervisor for the six November diversity arms.

Quota is monitored by the root operator through STOP, never inferred here.
This module imports no model stack and never evaluates or promotes candidates.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from scripts.early_curriculum_study import (
    THREAD_ENV, digest, group_exists, hashes, require, resource_lock, source_identity,
)
from scripts.final_training_supervisor import (
    admit_power, block_signals, check_foreign, read_power, safe_path, save_state,
)

ROOT = Path(__file__).resolve().parents[1]
ARMS = ('A0', 'B0', 'A1', 'B1', 'A2', 'B2')
SOURCE_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
STOP_FILE = Path('/tmp/sherlock-diversity-20261107/STOP')
LOCK_FILE = Path('/tmp/sherlock-model-resource.lock')
PLANS = ('docs/superpowers/specs/2026-11-07-ensemble-diversity.md',
         'docs/superpowers/plans/2026-11-07-ensemble-diversity.md')
CHECK_INTERVAL = 10
GRACE_SECONDS = 180
DEFAULT_RUN_PREFIX = '20261107_diversity'


class StopRequested(Exception):
    pass


def request_stop(path=STOP_FILE):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('x') as stream:
            stream.write(f'Stop requested at {time.time()}\n')
    except FileExistsError:
        pass


@contextmanager
def compute_lock(root, path=LOCK_FILE):
    # Existing helper takes a repository root, not an arbitrary lock path.
    with resource_lock(root):
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError('External model resource lock is held') from exc
            yield


def run_name(state, arm):
    require(arm in ARMS, 'Unknown training arm')
    prefix = state.get('run_prefix', DEFAULT_RUN_PREFIX)
    require(isinstance(prefix, str) and
            re.fullmatch(r'20261107_diversity(?:_[a-z0-9]{1,24})?', prefix) is not None,
            'Invalid study run prefix')
    return f'{prefix}_{arm}'


def training_command(state, arm):
    name = run_name(state, arm)
    return [state['python'], '-B', '-m', 'scripts.ensemble_diversity_train', 'run',
            '--prepared', state['prepared'], '--arm', arm,
            '--name', name]


def build_state(prepared, out, python, expected_head, stop_file=STOP_FILE,
                run_prefix=DEFAULT_RUN_PREFIX):
    require(Path.cwd().resolve() == ROOT, 'Use the intended worktree')
    require(re.fullmatch('[0-9a-f]{40}', expected_head) is not None, 'Expected HEAD must be full')
    prepared, out = safe_path(prepared), safe_path(out)
    require(not out.exists() and prepared.is_dir(), 'Prepared inputs missing or output already exists')
    require(out != ROOT and ROOT / 'agents' not in out.parents
            and out != prepared and prepared not in out.parents, 'Unsafe output destination')
    python = Path(python).absolute()
    require(python.is_file() and os.access(python, os.X_OK), 'Python unavailable')
    manifest = json.loads((prepared / 'manifest.json').read_text())
    require(manifest.get('source_sha256') == SOURCE_SHA
            and set(manifest.get('arms', {})) == set(ARMS)
            and not manifest.get('smoke', False), 'Prepared production arms/source differ')
    require(not (prepared / 'supervisor_launch.json').exists(), 'Prepared study already launched')
    runs = [ROOT / 'experiments/runs' / run_name({'run_prefix': run_prefix}, arm) for arm in ARMS]
    require(all(not path.exists() for path in runs), 'A training run already exists; no restart')
    plans = [str(ROOT / name) for name in PLANS]
    source = source_identity(ROOT, python, plans)
    require(source['head'] == expected_head, 'Expected HEAD changed')
    protected = hashes([safe_path(ROOT / f'agents/sherlock/weights/agent_p{i}.pth') for i in (0, 1)])
    require(set(protected.values()) == {SOURCE_SHA}, 'Protected V14 weights differ')
    protected.update(hashes([safe_path(ROOT / 'Gruppe15.zip')]))
    return dict(schema_version=1, root=str(ROOT), prepared=str(prepared), out=str(out),
                python=str(python), expected_head=expected_head, plans=plans, source=source,
                protected=protected, inputs=hashes(safe_path(p) for p in prepared.rglob('*') if p.is_file()),
                status='prepared', owner_pid=os.getpid(), stop_file=str(Path(stop_file).absolute()),
                queue=list(ARMS), jobs={}, active=[], receipts={}, run_prefix=run_prefix,
                quota_control='External root monitoring; STOP inhibits and gracefully stops work')


def check_inputs(state):
    require(source_identity(state['root'], state['python'], state['plans']) == state['source']
            and state['source']['head'] == state['expected_head'], 'Frozen source/HEAD changed')
    require(hashes(state['protected']) == state['protected'], 'Protected V14/ZIP changed')
    require(hashes(state['inputs']) == state['inputs'], 'Prepared inputs changed')


def check_model_processes(owned):
    groups = {child['pgid'] for child in owned.values()}
    check_foreign(groups)
    # The older shared check predates student/diversity modules.
    snapshot = subprocess.check_output(['ps', '-axo', 'pid=,pgid=,args='], text=True, timeout=5)
    for line in snapshot.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) != 3:
            continue
        pid, pgid, command = int(fields[0]), int(fields[1]), fields[2]
        if pid == os.getpid() or pgid in groups:
            continue
        module = re.search(r'(?:-m\s+scripts\.|scripts/)([a-zA-Z0-9_]+)', command)
        if module and 'python' in Path(command.split()[0]).name.lower():
            require(not any(word in module[1] for word in ('train', 'eval', 'distill', 'study', 'supervisor')),
                    f'Foreign model process is active: {pid}')


def guard(state, owned):
    if Path(state['stop_file']).exists():
        raise StopRequested('External STOP requested')
    power = read_power()
    admit_power(power, starting=False)
    check_inputs(state)
    check_model_processes(owned)
    state.update(last_guard_at=time.time(), last_power=power)
    return power


def spawn_owned(state, arm, command, owned):
    require(arm not in state['jobs'] and len(owned) < 2, 'Duplicate/excess child')
    log_path = safe_path(Path(state['out']) / f'{arm}.log')
    with log_path.open('xb') as log, block_signals() as previous:
        launcher = ('import os,signal,sys; '
                    f'signal.pthread_sigmask(signal.SIG_SETMASK,{sorted(map(int, previous))!r}); '
                    'os.execvpe(sys.argv[1],sys.argv[1:],os.environ)')
        process = subprocess.Popen([state['python'], '-B', '-c', launcher, *command],
            cwd=state['root'], env={**os.environ, **THREAD_ENV}, start_new_session=True,
            stdout=log, stderr=subprocess.STDOUT)
        owned[arm] = dict(process=process, owner_pid=os.getpid(), pgid=process.pid)
        state['jobs'][arm] = dict(pid=process.pid, pgid=process.pid, owner_pid=os.getpid(),
            argv=command, log=str(log_path), started_at=time.time(), returncode=None)
        state['active'] = list(owned)
        save_state(state)


def group_alive(pgid):
    """EPERM is not disappearance unless an independent process snapshot proves it."""
    try:
        return group_exists(pgid)
    except PermissionError:
        snapshot = subprocess.check_output(['ps', '-axo', 'pgid='], text=True, timeout=5)
        groups = {int(line.strip()) for line in snapshot.splitlines() if line.strip()}
        if pgid in groups:
            raise
        return False

def shutdown_owned(owned, *, grace=GRACE_SECONDS):
    """Reap before probing and signal only registered process groups; never restart."""
    def live_groups():
        live = []
        for child in owned.values():
            child['process'].poll()
            if group_alive(child['pgid']):
                live.append(child['pgid'])
        return live
    for child in owned.values():
        p = child['process']
        require(child['owner_pid'] == os.getpid() and child['pgid'] == p.pid,
                  'Refusing to signal an unowned process')
        if p.poll() is None:
            try:
                require(os.getpgid(p.pid) == p.pid, 'Owned process group changed')
            except ProcessLookupError:
                pass
        if group_alive(p.pid):
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            except PermissionError:
                if group_alive(p.pid):
                    raise
    deadline = time.monotonic() + grace
    while live_groups() and time.monotonic() < deadline:
        time.sleep(1)
    for pgid in live_groups():
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError:
            if group_alive(pgid):
                raise
    for child in owned.values():
        child['process'].wait(timeout=10)
    deadline = time.monotonic() + 10
    while live_groups() and time.monotonic() < deadline:
        time.sleep(1)
    require(not live_groups(), 'Owned process group did not stop')


def verify_receipt(state, arm):
    """Check lightweight completion evidence; root separately audits tensors after training."""
    name = run_name(state, arm)
    run = Path(state['root']) / 'experiments/runs' / name
    progress = json.loads((run / 'progress.json').read_text())
    path = run / 'final_receipt.json'
    receipt = json.loads(path.read_text())
    require(progress.get('status') == 'done' and progress.get('eligible') is True,
            'Training progress is not complete/eligible')
    expected = dict(schema_version=1, status='done', eligible=True, smoke=False, arm=arm, name=name,
                    source_sha256=SOURCE_SHA, actual_prefill_games=120, actual_train_games=3000,
                    actual_validation_games=128, learn_steps=450000, env_steps=1005360)
    require(all(receipt.get(k) == v for k, v in expected.items()), 'Final receipt role/counts differ')
    for key, relative in (('final_checkpoint_sha256', 'weights/agent.pth'),
                          ('rollouts_sha256', 'rollouts.jsonl'),
                          ('validation_sha256', 'validation_games.jsonl'),
                          ('audit_sha256', 'training_audit.json')):
        require(digest(run / relative) == receipt.get(key), f'Final receipt hash mismatch: {relative}')
    return dict(path=str(path), sha256=digest(path), final_checkpoint_sha256=receipt['final_checkpoint_sha256'])


def run_queue(state):
    owned = {}
    state.update(status='running', started_at=time.time(), queue=list(ARMS))
    save_state(state)
    try:
        while state['queue'] or owned:
            if Path(state['stop_file']).exists():
                raise StopRequested('External STOP requested')
            power = guard(state, owned)
            for arm, child in list(owned.items()):
                code = child['process'].poll()
                if code is None:
                    continue
                state['jobs'][arm].update(returncode=code, finished_at=time.time())
                require(code == 0, f'Training arm {arm} failed with exit {code}')
                require(not group_alive(child['pgid']), f'Training arm {arm} left descendants')
                state['receipts'][arm] = verify_receipt(state, arm)
                del owned[arm]
            can_start = power['ac'] or power['percent'] >= 35
            state['status'] = 'running' if can_start or owned else 'waiting_for_power'
            while can_start and state['queue'] and len(owned) < 2:
                # Recheck STOP/source/power immediately before each launch.
                power = guard(state, owned)
                if not (power['ac'] or power['percent'] >= 35):
                    break
                arm = state['queue'][0]
                spawn_owned(state, arm, training_command(state, arm), owned)
                state['queue'].pop(0)
            state['active'] = list(owned)
            save_state(state)
            if state['queue'] or owned:
                time.sleep(CHECK_INTERVAL)
        guard(state, owned)
        state['status'] = 'complete'
    except BaseException as exc:
        state.update(status='stopped' if isinstance(exc, StopRequested) else 'failed',
                     error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        try:
            shutdown_owned(owned)
            for arm, child in owned.items():
                state['jobs'][arm].update(returncode=child['process'].poll(), finished_at=time.time())
            state['active'] = []
        except BaseException as exc:
            state.update(status='failed', cleanup_error=f'{type(exc).__name__}: {exc}', active=list(owned))
            raise
        finally:
            state['finished_at'] = time.time()
            save_state(state)
    return state


def run_supervisor(prepared, out, python, expected_head, stop_file=STOP_FILE,
                   run_prefix=DEFAULT_RUN_PREFIX):
    if Path(stop_file).exists():
        raise StopRequested('Existing STOP inhibits start')
    signals = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
    handlers = {sig: signal.getsignal(sig) for sig in signals}
    wake = None
    state = None
    try:
        for sig in signals:
            signal.signal(sig, lambda *_: request_stop(stop_file))
        with compute_lock(ROOT):
            check_model_processes({})
            state = build_state(prepared, out, python, expected_head, stop_file, run_prefix)
            Path(state['out']).parent.mkdir(parents=True, exist_ok=True)
            Path(state['out']).mkdir()
            with (Path(state['prepared']) / 'supervisor_launch.json').open('x') as stream:
                json.dump(dict(owner_pid=os.getpid(), out=state['out'], started_at=time.time()), stream)
                stream.flush()
                os.fsync(stream.fileno())
            state['inputs'].update(hashes([Path(state['prepared']) / 'supervisor_launch.json']))
            wake_command = ['/usr/bin/caffeinate', '-i', '-w', str(os.getpid())]
            wake = subprocess.Popen(wake_command, start_new_session=True,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            state['wake'] = dict(pid=wake.pid, argv=wake_command, owner_pid=os.getpid())
            save_state(state)
            return run_queue(state)
    finally:
        if wake is not None:
            if wake.poll() is None:
                wake.terminate()
                try:
                    wake.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    wake.kill()
                    wake.wait(timeout=5)
            if state is not None:
                state['wake']['returncode'] = wake.returncode
                save_state(state)
        for sig, handler in handlers.items():
            signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest='command', required=True)
    start = commands.add_parser('start')
    for name in ('prepared', 'out', 'python', 'expected-head'):
        start.add_argument('--' + name, required=True)
    start.add_argument('--stop-file', type=Path, default=STOP_FILE)
    start.add_argument('--run-prefix', default=DEFAULT_RUN_PREFIX,
                       help='Explicit fresh attempt; existing run directories are never reused')
    commands.add_parser('stop').add_argument('--stop-file', type=Path, default=STOP_FILE)
    args = parser.parse_args()
    if args.command == 'stop':
        request_stop(args.stop_file)
        print(f'STOP recorded: {args.stop_file}')
        return
    try:
        state = run_supervisor(args.prepared, args.out, args.python, args.expected_head,
                               args.stop_file, args.run_prefix)
    except Exception as exc:
        print(f'Supervisor stopped: {type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(dict(status=state['status'], out=state['out'])))


if __name__ == '__main__':
    main()
