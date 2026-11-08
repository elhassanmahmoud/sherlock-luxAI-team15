"""Single-use supervisor for the fixed November ensemble comparison jobs.

No model imports, automatic restart, nomination, promotion, or partial-CSV reuse.
The shared STOP inhibits the whole study. A fresh live quota file is mandatory.
Never run tests concurrently with model jobs: the shared guard rejects them.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import importlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = Path('experiments/analysis/ensemble_diversity_20261107')
SOURCE_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
STOP_FILE = Path('/tmp/sherlock-diversity-20261107/STOP')
PLANS = ('docs/superpowers/specs/2026-11-07-ensemble-diversity.md',
         'docs/superpowers/plans/2026-11-07-ensemble-comparison.md')
CHECK_INTERVAL = 10


class StopRequested(Exception):
    pass

def helpers():
    """Reuse the existing stdlib-only ownership/resource safeguards lazily."""
    return importlib.import_module('scripts.ensemble_diversity_supervisor')

def validate_plan(plan, root, *, phase, nominee, profile='full20261107'):
    return importlib.import_module('scripts.ensemble_diversity_compare').validate_plan(
        plan, root, phase=phase, nominee=nominee, profile=profile)

def validate_job_csv(path, job, seeds):
    return importlib.import_module('scripts.ensemble_diversity_compare').validate_job_csv(path, job, seeds)

def request_stop(path=STOP_FILE):
    helpers().request_stop(path)

def validate_quota_ceiling(max_used_percent):
    helpers().require(type(max_used_percent) in (int, float)
        and math.isfinite(max_used_percent) and 0 < max_used_percent <= 100,
        'Quota ceiling must be a finite number greater than 0 and at most 100')

def check_usage(path, *, now, max_used_percent=65):
    validate_quota_ceiling(max_used_percent)
    h = helpers()
    try:
        usage = json.loads(h.safe_path(path).read_text())
        when = datetime.fromisoformat(usage['timestamp'].replace('Z', '+00:00'))
        used = usage['usedPercent']
        h.require(when.tzinfo is not None and math.isfinite(now)
                  and 0 <= now - when.timestamp() <= 1200, 'Quota receipt stale or from future')
        h.require(type(used) in (int, float) and math.isfinite(used) and 0 <= used <= 100,
                  'Unknown quota usage')
        h.require(usage['ordinaryUsageAllowed'] is True and used < max_used_percent,
                  f'Quota disallowed or >={max_used_percent}%; stopping comparison')
    except (OSError, KeyError, TypeError, AttributeError, json.JSONDecodeError) as exc:
        raise ValueError('Missing or malformed quota receipt') from exc
    return usage

def repo_path(root, relative):
    h = helpers()
    h.require(isinstance(relative, str) and relative and not Path(relative).is_absolute(),
              'Input path must be repository relative')
    path = h.safe_path(Path(root) / relative)
    h.require(path.is_relative_to(root), 'Input path escapes repository')
    return path

def build_state(jobs, admission, out, python, expected_head, *, usage_file,
                phase='selection', nominee=None, stop_file=STOP_FILE, max_used_percent=65,
                profile='full20261107'):
    validate_quota_ceiling(max_used_percent)
    h = helpers()
    h.require(Path.cwd().resolve() == ROOT, 'Use the intended checkout')
    h.require(re.fullmatch('[0-9a-f]{40}', expected_head) is not None, 'Expected HEAD must be full')
    h.require(phase in ('selection', 'confirmation'), 'Unknown comparison phase')
    jobs_path, admission_path, out = map(h.safe_path, (jobs, admission, out))
    comparison = importlib.import_module('scripts.ensemble_diversity_compare')
    spec = comparison.comparison_profile(profile)
    plan = json.loads(jobs_path.read_text())
    comparison.plan_profile(plan, profile)
    base = h.safe_path(ROOT / spec.analysis)
    h.require(out != base and out.is_relative_to(base) and not out.exists(),
              'Use a fresh study analysis output directory')
    reservation = h.safe_path(base / f'{phase}_launch.json')
    h.require(not reservation.exists(), 'Phase already launched; no automatic restart')
    python = Path(python).absolute()
    h.require(python.is_file() and os.access(python, os.X_OK), 'Python unavailable')
    admission_data = json.loads(admission_path.read_text())
    h.require(admission_data.get('status') == 'admitted', 'Models have not been admitted')
    models, paths = {}, [jobs_path, admission_path]
    for role, relative in plan['roles'].items():
        item = admission_data.get('roles', {}).get(role, {})
        path = repo_path(ROOT, relative)
        value = h.digest(path)
        h.require(item.get('path') == relative and item.get('sha256') == value,
                  f'Admitted model path/hash differs: {role}')
        models[role] = value
        paths.append(path)
    h.require(models.get('V14') == SOURCE_SHA, 'Admitted V14 differs')
    for relative, value in plan['opponent_sha256'].items():
        path = repo_path(ROOT, relative)
        h.require(h.digest(path) == value, 'Opponent hash differs')
        paths.append(path)
    plans = [str(repo_path(ROOT, name)) for name in (PLANS[0], spec.protocol)]
    source = h.source_identity(ROOT, python, plans)
    h.require(source['head'] == expected_head, 'Expected HEAD changed')
    protected = h.hashes([repo_path(ROOT, f'agents/sherlock/weights/agent_p{i}.pth') for i in (0, 1)])
    h.require(set(protected.values()) == {SOURCE_SHA}, 'Protected V14 weights differ')
    protected.update(h.hashes([repo_path(ROOT, 'Gruppe15.zip')]))
    if phase == 'confirmation':
        paths.extend(selection_evidence(nominee, source, models, profile=profile))
    # Confirmation seed files remain unread until a completed nomination is bound.
    job_list = validate_plan(plan, ROOT, phase=phase, nominee=nominee, profile=profile)
    for job in job_list:
        h.require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', job['name']), 'Unsafe job name')
        paths.append(repo_path(ROOT, job['seed_list']))
    h.require(len({job['name'] for job in job_list}) == len(job_list) and job_list,
              'Duplicate or empty fixed job queue')
    h.require(all(out != path and out not in path.parents for path in paths),
              'An input overlaps output')
    provenance = dict(model_sha256=models, source_identity=source)
    if profile != 'full20261107':
        provenance['profile'] = profile
    return dict(schema_version=1, profile=profile, root=str(ROOT), out=str(out), python=str(python),
        phase=phase, nominee=nominee, jobs_path=str(jobs_path), expected_head=expected_head, source=source, plans=plans,
        protected=protected, inputs=h.hashes(paths), admission_sha256=h.digest(admission_path),
        model_sha256=models, opponent_sha256=plan['opponent_sha256'],
        provenance=provenance,
        usage_file=str(h.safe_path(usage_file)), max_used_percent=max_used_percent,
        stop_file=str(Path(stop_file).absolute()),
        reservation=str(reservation), expected_games=sum(job['expected_games'] for job in job_list),
        job_plan={job['name']: job for job in job_list}, queue=[job['name'] for job in job_list],
        jobs={}, active=[], receipts={}, status='prepared', owner_pid=os.getpid())


def selection_evidence(nominee, source, models, *, profile='full20261107'):
    """Bind the single confirmation to the completed, externally analyzed selection."""
    h = helpers()
    comparison = importlib.import_module('scripts.ensemble_diversity_compare')
    spec = comparison.comparison_profile(profile)
    reservation = h.safe_path(ROOT / spec.analysis / 'selection_launch.json')
    launch = json.loads(reservation.read_text())
    out = h.safe_path(launch['out'])
    h.require(out.is_relative_to(ROOT / spec.analysis), 'Selection output escapes study')
    summary_path, state_path, provenance_path = (h.safe_path(out / name) for name in
                                               ('summary.json', 'state.json', 'provenance.json'))
    summary = json.loads(summary_path.read_text())
    completed = json.loads(state_path.read_text())
    provenance = json.loads(provenance_path.read_text())
    h.require(all(record.get('profile', 'full20261107') == profile
                  for record in (launch, summary, completed, provenance)), 'Selection profile differs')
    h.require(summary.get('status') == 'complete' and summary.get('phase') == 'selection'
              and summary.get('jobs') == 39 and summary.get('games') == spec.total('selection')
              and completed.get('status') == 'complete' and completed.get('completed_games') == spec.total('selection'),
              'Selection is not complete')
    h.require(nominee in ('A39', 'B39', 'ALL42') and summary.get('nominee') == nominee,
              'Confirmation nominee differs from completed selection')
    h.require(launch['source_identity'] == source and provenance['source_identity'] == source
              and all(provenance['model_sha256'].get(role) == value for role, value in models.items()),
              'Selection source/model provenance differs')
    expected = summary['input_sha256']
    plan_path = h.safe_path(launch['jobs_path'])
    h.require(h.digest(plan_path) == expected['plan']
              and h.digest(provenance_path) == expected['provenance'], 'Selection plan/provenance hash differs')
    csv_hashes, receipts = expected['csv'], expected['receipts']
    h.require(len(csv_hashes) == 39 and set(csv_hashes) == set(receipts), 'Incomplete selection evidence')
    paths = [reservation, summary_path, state_path, provenance_path, plan_path]
    for name, value in csv_hashes.items():
        h.require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', name), 'Unsafe selection job name')
        csv_path, receipt_path = h.safe_path(out / f'{name}.csv'), h.safe_path(out / 'receipts' / f'{name}.json')
        h.require(h.digest(csv_path) == value and h.digest(receipt_path) == receipts[name],
                  'Selection CSV/receipt hash differs')
        paths.extend((csv_path, receipt_path))
    comparison.plan_profile(comparison._load_json(plan_path), profile)
    recomputed = comparison.analyze(
        plan_path, out, root=ROOT, phase='selection', provenance=provenance_path)
    h.require(summary == recomputed and recomputed['nominee'] == nominee,
              'Saved selection differs from the deterministically recomputed report/nominee')
    return paths

def check_inputs(state):
    h = helpers()
    h.require(h.source_identity(state['root'], state['python'], state['plans']) == state['source']
              and state['source']['head'] == state['expected_head'], 'Frozen source/HEAD changed')
    for group, message in (('protected', 'Protected V14/ZIP changed'), ('inputs', 'Frozen inputs changed')):
        for path in state[group]:
            h.safe_path(path)
        h.require(h.hashes(state[group]) == state[group], message)

def guard(state, owned):
    h = helpers()
    if Path(state['stop_file']).exists():
        raise StopRequested('External STOP requested')
    usage = check_usage(state['usage_file'], now=time.time(),
                        max_used_percent=state.get('max_used_percent', 65))
    power = h.read_power()
    h.admit_power(power, starting=False)
    check_inputs(state)
    h.check_model_processes(owned)
    state.update(last_guard_at=time.time(), last_power=power, last_usage=usage)
    return power

def job_command(state, name):
    h = helpers()
    job = state['job_plan'][name]
    output = h.safe_path(Path(state['out']) / f'{name}.csv')
    h.require(not output.exists(), 'Job CSV already exists; never resume incomplete output')
    return [state['python'], '-B', '-m', 'scripts.par_eval',
        '--weights', str(repo_path(state['root'], job['weights'])),
        '--seed-list', str(repo_path(state['root'], job['seed_list'])),
        '--workers', '1', '--opponents', job['opponent'], '--out', str(output)]

def exclusive_json(path, value):
    with helpers().safe_path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())

def reserve_launch(state):
    h = helpers()
    exclusive_json(state['reservation'], dict(owner_pid=os.getpid(), out=state['out'],
        phase=state['phase'], profile=state.get('profile', 'full20261107'), jobs_path=state.get('jobs_path'),
        max_used_percent=state.get('max_used_percent', 65), started_at=time.time(), source_identity=state['source']))
    path = Path(state['out']) / 'provenance.json'
    exclusive_json(path, state['provenance'])
    state['inputs'].update(h.hashes([state['reservation'], path]))

def spawn_owned(state, name, command, owned):
    # Existing helper records PID/PGID under blocked signals and caps children at two.
    helpers().spawn_owned(state, name, command, owned)

def write_receipt(state, name):
    h = helpers()
    job, record = state['job_plan'][name], state['jobs'][name]
    h.require(record['returncode'] == 0, 'A failed exit cannot have a complete receipt')
    check_inputs(state)
    path = h.safe_path(Path(state['out']) / f'{name}.csv')
    csv_hash = h.digest(path)
    rows = validate_job_csv(path, job, job['seeds'])
    h.require(len(rows) == job['expected_games'], 'Incomplete CSV row count')
    h.require(h.digest(path) == csv_hash, 'CSV changed during validation')
    receipt = dict(status='complete', returncode=0, job_name=name, phase=state['phase'],
        role=job['role'], opponent=job['opponent'], weights=job['weights'],
        model_sha256=state['model_sha256'][job['role']], opponent_sha256=state['opponent_sha256'],
        seed_list_sha256=h.digest(repo_path(state['root'], job['seed_list'])),
        source_identity=state['source'], csv_sha256=csv_hash, rows=len(rows), command=record['argv'])
    if state.get('profile', 'full20261107') != 'full20261107':
        receipt['profile'] = state['profile']
    target = Path(state['out']) / 'receipts' / f'{name}.json'
    exclusive_json(target, receipt)
    state['inputs'].update(h.hashes([path, target]))
    return dict(path=str(target), sha256=h.digest(target), rows=len(rows))


def group_alive(pgid):
    """EPERM is not disappearance unless an independent process snapshot proves it."""
    try:
        return helpers().group_exists(pgid)
    except PermissionError:
        snapshot = subprocess.check_output(['ps', '-axo', 'pgid='], text=True, timeout=5)
        groups = {int(line.strip()) for line in snapshot.splitlines() if line.strip()}
        if pgid in groups:
            raise
        return False

def shutdown_owned(owned, *, grace=180):
    """Reap before probing and signal only registered process groups; never restart."""
    h = helpers()
    def live_groups():
        live = []
        for child in owned.values():
            child['process'].poll()
            if group_alive(child['pgid']):
                live.append(child['pgid'])
        return live
    for child in owned.values():
        p = child['process']
        h.require(child['owner_pid'] == os.getpid() and child['pgid'] == p.pid,
                  'Refusing to signal an unowned process')
        if p.poll() is None:
            try:
                h.require(os.getpgid(p.pid) == p.pid, 'Owned process group changed')
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
    h.require(not live_groups(), 'Owned process group did not stop')

def run_queue(state):
    h = helpers()
    owned = {}
    h.require(not state['jobs'] and not state['receipts'], 'No restart or resume')
    state.update(status='running', started_at=time.time())
    h.save_state(state)
    try:
        while state['queue'] or owned:
            power = guard(state, owned)
            for name, child in list(owned.items()):
                code = child['process'].poll()
                if code is None:
                    continue
                state['jobs'][name].update(returncode=code, finished_at=time.time())
                h.require(code == 0, f'Comparison job {name} failed with exit {code}')
                h.require(not group_alive(child['pgid']), f'Job {name} left descendants')
                state['receipts'][name] = write_receipt(state, name)
                del owned[name]
            can_start = power['ac'] or power['percent'] >= 35
            state['status'] = 'running' if can_start or owned else 'waiting_for_power'
            while can_start and state['queue'] and len(owned) < 2:
                power = guard(state, owned)
                if not (power['ac'] or power['percent'] >= 35):
                    break
                name = state['queue'][0]
                spawn_owned(state, name, job_command(state, name), owned)
                state['queue'].pop(0)
                print(f'Started {name}: PID {state["jobs"][name].get("pid")}', flush=True)
            state['active'] = list(owned)
            h.save_state(state)
            if state['queue'] or owned:
                time.sleep(CHECK_INTERVAL)
        guard(state, owned)
        total = sum(receipt['rows'] for receipt in state['receipts'].values())
        h.require(set(state['receipts']) == set(state['job_plan']) and total == state['expected_games'],
                  'Incomplete fixed comparison block')
        state.update(status='complete', completed_games=total)
    except BaseException as exc:
        state.update(status='stopped' if isinstance(exc, StopRequested) else 'failed',
                     error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        try:
            shutdown_owned(owned)
            for name, child in owned.items():
                state['jobs'][name].update(returncode=child['process'].poll(), finished_at=time.time())
            state['active'] = []
        except BaseException as exc:
            state.update(status='failed', cleanup_error=f'{type(exc).__name__}: {exc}', active=list(owned))
            raise
        finally:
            state['finished_at'] = time.time()
            h.save_state(state)
    return state

def run_supervisor(jobs, admission, out, python, expected_head, *, usage_file,
                   phase='selection', nominee=None, stop_file=STOP_FILE, max_used_percent=65,
                   profile='full20261107'):
    validate_quota_ceiling(max_used_percent)
    h = helpers()
    if Path(stop_file).exists():
        raise StopRequested('Existing STOP inhibits start')
    handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    wake, state = None, None
    try:
        for sig in handlers:
            signal.signal(sig, lambda *_: request_stop(stop_file))
        with h.compute_lock(ROOT):
            h.check_model_processes({})
            state = build_state(jobs, admission, out, python, expected_head, usage_file=usage_file,
                                phase=phase, nominee=nominee, stop_file=stop_file,
                                max_used_percent=max_used_percent, profile=profile)
            guard(state, {})
            target = h.safe_path(state['out'])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.mkdir()
            (target / 'receipts').mkdir()
            with (target / 'controller.log').open('x', buffering=1) as log, redirect_stdout(log), redirect_stderr(log):
                try:
                    reserve_launch(state)
                    guard(state, {})
                    # Signal handlers only set STOP, so registration cannot be interrupted
                    # by a raised signal; caffeinate must inherit an unblocked TERM.
                    command = ['/usr/bin/caffeinate', '-i', '-w', str(os.getpid())]
                    wake = subprocess.Popen(command, start_new_session=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    state['wake'] = dict(pid=wake.pid, pgid=wake.pid, argv=command, owner_pid=os.getpid())
                    h.save_state(state)
                    return run_queue(state)
                except BaseException as exc:
                    state.update(status='stopped' if isinstance(exc, StopRequested) else 'failed',
                                 error=f'{type(exc).__name__}: {exc}', finished_at=time.time())
                    print(state['error'], file=sys.stderr, flush=True)
                    h.save_state(state)
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
                state['wake']['returncode'] = wake.returncode
                h.save_state(state)
        finally:
            for sig, handler in handlers.items():
                signal.signal(sig, handler)

def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest='command', required=True)
    start = commands.add_parser('start')
    for name in ('jobs', 'admission', 'out', 'python', 'expected-head', 'usage-file'):
        start.add_argument('--' + name, required=True)
    start.add_argument('--profile', choices=('full20261107', 'compact20261108'), default='full20261107')
    start.add_argument('--phase', choices=('selection', 'confirmation'), default='selection')
    start.add_argument('--max-used-percent', type=float, default=65,
        help='Stop at this quota usage percentage (default: 65; maximum: 100)')
    start.add_argument('--nominee', choices=('A39', 'B39', 'ALL42'))
    commands.add_parser('stop')
    args = parser.parse_args()
    if args.command == 'stop':
        request_stop()
        print(f'STOP recorded: {STOP_FILE}')
        return
    try:
        state = run_supervisor(args.jobs, args.admission, args.out, args.python, args.expected_head,
            usage_file=args.usage_file, phase=args.phase, nominee=args.nominee,
            max_used_percent=args.max_used_percent, profile=args.profile)
    except Exception as exc:
        print(f'Comparison stopped: {type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(dict(status=state['status'], out=state['out'], games=state['completed_games'])))


if __name__ == '__main__':
    main()
