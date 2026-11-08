"""Single-use sampled-target pilot: separate technical and paired training stages."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from scripts.early_curriculum_study import hashes, require, source_identity
from scripts.ensemble_diversity_eval_supervisor import check_usage
from scripts.ensemble_diversity_supervisor import (
    compute_lock, group_alive, request_stop, shutdown_owned, spawn_owned,
)
from scripts.final_training_supervisor import read_power, safe_path, save_state
from scripts.fog_reward_supervisor import check_model_processes

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'sampled_target_20261108'
ARMS = ('control45', 'sampled45', 'control46', 'sampled46')
PAIRS = (ARMS[:2], ARMS[2:])
TECHNICAL_ARMS = ('technical_control_p0', 'technical_sampled_p0',
                  'technical_control_p1', 'technical_sampled_p1')
TECHNICAL_PAIRS = (TECHNICAL_ARMS[:2], TECHNICAL_ARMS[2:])
SOURCE_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
STOP_FILE = Path('/private/tmp/sherlock-sampled-target-20261108/STOP')
USAGE_FILE = ROOT/'experiments/analysis/sampled_target_20261108/operations/usage.json'
PLANS = [ROOT/f'docs/superpowers/{kind}/2026-11-08-sampled-target.md' for kind in ('specs', 'plans')]
CHECK_INTERVAL = 10
REGISTRATION_TIMEOUT = 15


def stage_arms(stage):
    require(stage in ('technical', 'study'), 'Unknown fixed stage')
    return TECHNICAL_ARMS if stage == 'technical' else ARMS


def guard(state, owned):
    require(state.get('profile') == PROFILE and state.get('stage') in ('technical', 'study'),
            'Wrong supervisor profile/stage')
    require(not Path(state['stop_file']).exists(), 'External STOP requested')
    usage = check_usage(state['usage_file'], now=time.time(), max_used_percent=100)
    power = read_power()
    require(power.get('ac') is True, 'AC power required')
    require(source_identity(ROOT, state['python'], state['plans']) == state['source'],
            'Frozen source/HEAD/plans changed')
    require(hashes(state['inputs']) == state['inputs'] and hashes(state['protected']) == state['protected'],
            'Prepared/admission input or protected V14/ZIP changed')
    active = state.get('active', [])
    require(len(active) == len(set(active)) <= 2 and len(owned) <= 2
            and set(active).issubset(stage_arms(state['stage'])), 'Maximum two fixed model workers')
    check_model_processes(state, owned)
    state.update(last_guard_at=time.time(), last_power=power, last_usage=usage)


def run_name(arm):
    require(arm in (*ARMS, *TECHNICAL_ARMS), 'Unknown fixed arm/job')
    return f'20261108_sampled_target_{arm}'


def training_command(state, arm):
    require(arm in stage_arms(state['stage']), 'Worker does not belong to this stage')
    command = 'technical' if state['stage'] == 'technical' else 'run'
    return [state['python'], '-B', '-m', 'scripts.sampled_target_study', command,
            '--prepared', state['prepared'], '--arm', arm, '--name', run_name(arm),
            '--supervisor-state', str(Path(state['out'])/'state.json')]


def worker_guard(state_path, arm, name, prepared, *, startup=False):
    """Wait only for launch registration; do no learner work before exact ownership."""
    state_path = safe_path(state_path)
    require(name == run_name(arm), 'Worker role/name differs')
    deadline = time.monotonic() + (REGISTRATION_TIMEOUT if startup else 0)
    while True:
        state = json.loads(state_path.read_text())
        require(state.get('profile') == PROFILE and state.get('status') == 'running'
                and arm in stage_arms(state.get('stage')), 'Worker stage is not running')
        require(state_path == safe_path(Path(state['out'])/'state.json')
                and Path(state['root']).resolve() == ROOT
                and Path(state['prepared']).resolve() == Path(prepared).resolve(),
                'Worker paths differ from owned launch')
        owner = state.get('owner_pid')
        require(type(owner) is int and owner > 1 and owner == os.getppid(), 'Worker owner differs')
        os.kill(owner, 0)  # Existence check only; never send a signal to a foreign process.
        require(not Path(state['stop_file']).exists(), 'External STOP requested')
        job = state.get('jobs', {}).get(arm)
        if job is not None:
            expected = training_command(state, arm)
            require(arm in state['active'] and job.get('pid') == os.getpid()
                    and job.get('pgid') == os.getpgrp() == os.getpid()
                    and job.get('owner_pid') == owner and job.get('argv') == expected
                    and getattr(sys, 'orig_argv', None) == expected,
                    'Worker lacks exact owned supervisor PID/group/command')
            # A peer can be between Popen and atomic registration. Neither worker
            # begins learner work while that peer would look like a foreign job.
            pairs = TECHNICAL_PAIRS if state['stage'] == 'technical' else PAIRS
            pair = next(pair for pair in pairs if arm in pair)
            if startup and any(peer not in state['jobs'] for peer in pair):
                require(time.monotonic() < deadline, 'Peer launch registration timed out')
                time.sleep(.05)
                continue
            guard(state, {})
            return state
        require(startup and time.monotonic() < deadline, 'Worker registration absent or timed out')
        time.sleep(.05)


def build_state(prepared, out, python, expected_head, *, usage_file=USAGE_FILE, stop_file=STOP_FILE):
    from scripts import sampled_target_study as study
    require(Path.cwd().resolve() == ROOT, 'Use the intended worktree')
    require(re.fullmatch('[0-9a-f]{40}', expected_head) is not None, 'Expected HEAD must be full')
    prepared, out = map(safe_path, (prepared, out))
    require(not out.exists() and prepared.is_dir(), 'Missing prepared/new exclusive output')
    require(out != ROOT and out != ROOT/'agents' and ROOT/'agents' not in out.parents
            and out != prepared and prepared not in out.parents, 'Unsafe supervisor output')
    require(safe_path(stop_file) == STOP_FILE and safe_path(usage_file) == USAGE_FILE,
            'Use canonical study STOP and fresh usage paths')
    python = Path(python).absolute()
    require(python.is_file() and os.access(python, os.X_OK), 'Python unavailable')
    # check_prepared validates Root review/seed admission, plus technical acceptance for study.
    manifest, _, _ = study.check_prepared(prepared)
    stage = manifest['stage']
    arms = stage_arms(stage)
    require(tuple(j['job'] for j in study.technical_plan()) == TECHNICAL_ARMS,
            'Technical job/side inventory changed')
    for arm in arms:
        checked, _, _ = study.check_prepared(prepared, arm)
        require(checked == manifest, 'Prepared manifest changed during admission')
    require(not (prepared/'supervisor_launch.json').exists(), 'Stage already launched; no resume')
    require(all(not (ROOT/'experiments/runs'/run_name(arm)).exists() for arm in arms),
            'Fixed run already exists; no restart')
    source = source_identity(ROOT, python, PLANS)
    require(source['head'] == expected_head and source == manifest['pins']['source'],
            'Expected HEAD/source differs from Root admission')
    protected = manifest['pins']['protected']
    require(all(protected.get(str(ROOT/f'agents/sherlock/weights/agent_p{i}.pth')) == SOURCE_SHA for i in (0, 1))
            and str(ROOT/'Gruppe15.zip') in protected, 'Protected V14 weights/ZIP differ or missing')
    inputs = dict(manifest['input_sha256'])
    prepared_hashes = hashes(safe_path(p) for p in prepared.rglob('*') if p.is_file())
    require(all(path not in inputs or inputs[path] == value for path, value in prepared_hashes.items()),
            'Conflicting frozen input hashes')
    inputs.update(prepared_hashes)
    state = dict(schema_version=1, profile=PROFILE, stage=stage, status='prepared', eligible=False,
        root=str(ROOT), prepared=str(prepared), out=str(out), python=str(python), expected_head=expected_head,
        plans=[str(p) for p in PLANS], source=source, protected=protected, inputs=inputs,
        usage_file=str(USAGE_FILE), stop_file=str(STOP_FILE), owner_pid=os.getpid(), jobs={}, active=[],
        paired_prefill={}, technical_pairs={}, receipts={}, queue=list(arms))
    guard(state, {})
    return state


def compare_pair(state, pair):
    from scripts import sampled_target_study as study
    require(state['stage'] == 'study' and pair in PAIRS, 'Wrong prefill pair/stage')
    paths = {arm: ROOT/'experiments/runs'/run_name(arm)/'prefill_proof.json' for arm in pair}
    before = hashes(paths.values())
    proofs = [study.validate_prefill_bundle(paths[arm].parent, state['prepared'], arm) for arm in pair]
    seed = study.ARMS[pair[0]][0]
    result = study.compare_prefill_proofs(*proofs, seed)
    require(hashes(before) == before, 'Prefill readiness proof changed during validation')
    result['proof_sha256'] = {arm: before[str(path)] for arm, path in paths.items()}
    guard(state, {})
    # The exclusive gate is the only permission for either worker to enable gradients.
    path = Path(state['out'])/f'paired_prefill_{seed}.json'
    pending = path.with_name(path.name+'.pending')
    with pending.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    # link is atomic and fails if the final name already exists; no partial gate.
    os.link(pending, path)
    pending.unlink()
    state['paired_prefill'][str(seed)] = result
    save_state(state)


def collect_pair(state, pair):
    from scripts import sampled_target_study as study
    technical = state['stage'] == 'technical'
    filename = 'technical_receipt.json' if technical else 'final_receipt.json'
    checked = {}
    for arm in pair:
        path = ROOT/'experiments/runs'/run_name(arm)/filename
        before = hashes([path])
        receipt = (study.validate_technical_receipt(path, job=arm) if technical
                   else study.validate_final_receipt(path, arm=arm))
        require(receipt['name'] == run_name(arm) and receipt['prepared'] == state['prepared']
                and receipt['command'] == state['jobs'][arm]['argv'] == training_command(state, arm),
                'Receipt does not bind the owned worker command')
        require(hashes(before) == before, 'Final receipt changed during validation')
        checked[arm] = receipt
        state['receipts'][arm] = before
    if technical:
        require(pair in TECHNICAL_PAIRS, 'Wrong technical pair')
        side = f'player_{pair[0][-1]}'
        state['technical_pairs'][side] = study.compare_technical_receipts(*(checked[arm] for arm in pair), side)
    save_state(state)


def run_queue(state):
    owned = {}
    complete = False
    state.update(status='running', started_at=time.time())
    save_state(state)
    pairs = TECHNICAL_PAIRS if state['stage'] == 'technical' else PAIRS
    try:
        for pair in pairs:
            require(not owned, 'Previous pair still active')
            for arm in pair:
                guard(state, owned)
                spawn_owned(state, arm, training_command(state, arm), owned)
                state['queue'].remove(arm)
                save_state(state)
            paired = state['stage'] == 'technical'
            while owned:
                guard(state, owned)
                if not paired and all((ROOT/'experiments/runs'/run_name(arm)/'prefill_proof.json').exists() for arm in pair):
                    compare_pair(state, pair)
                    paired = True
                for arm, child in list(owned.items()):
                    code = child['process'].poll()
                    if code is None:
                        continue
                    state['jobs'][arm].update(returncode=code, finished_at=time.time())
                    require(code == 0 and paired, f'Worker {arm} failed or exited before paired admission')
                    require(not group_alive(child['pgid']), 'Worker left descendants')
                    del owned[arm]
                    state['active'] = list(owned)
                    save_state(state)
                if owned:
                    time.sleep(CHECK_INTERVAL)
            collect_pair(state, pair)
            guard(state, owned)
        require(not state['queue'] and set(state['receipts']) == set(stage_arms(state['stage'])),
                'Incomplete fixed stage')
        if state['stage'] == 'technical':
            require(set(state['technical_pairs']) == {'player_0', 'player_1'} and not state['paired_prefill'],
                    'Incomplete four-game technical comparison')
        else:
            require(set(state['paired_prefill']) == {'45', '46'} and not state['technical_pairs'],
                    'Incomplete fixed paired training')
        complete = True
    except BaseException as exc:
        request_stop(state['stop_file'])
        state.update(status='incomplete', eligible=False, error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        try:
            shutdown_owned(owned)
            for arm, child in owned.items():
                state['jobs'][arm].update(returncode=child['process'].poll(), finished_at=time.time())
            state['active'] = []
            if complete:
                guard(state, {})
                state.update(status='done', eligible=False,
                    note='Fixed stage complete only; no automatic next stage or strength/promotion decision')
        except BaseException as exc:
            request_stop(state['stop_file'])
            state.update(status='incomplete', eligible=False, cleanup_error=f'{type(exc).__name__}: {exc}',
                         active=list(owned))
            raise
        finally:
            state['finished_at'] = time.time()
            save_state(state)
    return state


def run_supervisor(prepared, out, python, expected_head, *, usage_file=USAGE_FILE, stop_file=STOP_FILE):
    signals = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
    handlers = {sig: signal.getsignal(sig) for sig in signals}
    state = wake = None
    try:
        for sig in signals:
            signal.signal(sig, lambda *_: request_stop(STOP_FILE))
        with compute_lock(ROOT):
            state = build_state(prepared, out, python, expected_head, usage_file=usage_file, stop_file=stop_file)
            Path(state['out']).mkdir(parents=True, exist_ok=False)
            launch = Path(state['prepared'])/'supervisor_launch.json'
            with launch.open('x') as stream:
                json.dump(dict(owner_pid=os.getpid(), profile=PROFILE, stage=state['stage'],
                               out=state['out'], started_at=time.time()), stream)
                stream.flush()
                os.fsync(stream.fileno())
            state['inputs'].update(hashes([launch]))
            command = ['/usr/bin/caffeinate', '-i', '-w', str(os.getpid())]
            wake = subprocess.Popen(command, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            state['wake'] = dict(pid=wake.pid, pgid=wake.pid, owner_pid=os.getpid(), argv=command)
            save_state(state)
            return run_queue(state)
    except BaseException as exc:
        if state is not None and Path(state['out']).is_dir():
            state.update(status='incomplete', eligible=False, error=f'{type(exc).__name__}: {exc}')
            save_state(state)
        raise
    finally:
        try:
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
        except BaseException as exc:
            request_stop(STOP_FILE)
            if state is not None and Path(state['out']).is_dir():
                state.update(status='incomplete', eligible=False, cleanup_error=f'{type(exc).__name__}: {exc}')
                save_state(state)
            raise
        finally:
            for sig, handler in handlers.items():
                signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    start = commands.add_parser('start')
    for name in ('prepared', 'out', 'python', 'expected-head'):
        start.add_argument('--'+name, required=True)
    start.add_argument('--usage-file', type=Path, default=USAGE_FILE)
    start.add_argument('--stop-file', type=Path, default=STOP_FILE)
    commands.add_parser('stop')
    args = parser.parse_args()
    if args.command == 'stop':
        request_stop(STOP_FILE)
    else:
        state = run_supervisor(args.prepared, args.out, args.python, args.expected_head,
                              usage_file=args.usage_file, stop_file=args.stop_file)
        print(json.dumps(dict(status=state['status'], stage=state['stage'], out=state['out'])))


if __name__ == '__main__':
    main()
