"""Fixed P/PT evaluation supervisor. Import/prepare never starts model jobs.

Only `run --plan FILE --start` executes. Gates/nomination/promotion are external.
par_eval runs combined panel/default and direct jobs with two workers. Paths
derive from --root and this file's actual location, so the reviewed driver can
subsequently be committed/relocated.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
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
from types import SimpleNamespace

sys.dont_write_bytecode = True
SOURCE_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
DEADLINE = datetime(2026, 11, 3, 4, 30, tzinfo=timezone.utc).timestamp()
RESERVE = 3600
PANEL = ('solution92', 'sol92_sq',
    'self:experiments/releases/20261022_all18_v3/agent_p0.pth',
    'self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth',
    'self:experiments/releases/20261022_v10_baseline/agent_p0.pth',
    'self:experiments/releases/20261101_v13_neb/agent_p0.pth')
SIDES = ('player_0', 'player_1')
DIRECT = 'self:experiments/releases/20261101_v14_baseline/agent_p0.pth'
INITIAL_RATES = dict(combined_panel=2.22, direct=3.0)  # WALL seconds/game; already <=2-worker throughput.


def require(condition, message):
    if not condition:
        raise ValueError(message)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def new_path(path):
    path = Path(path).absolute()
    # macOS exposes these system directories through symlinks. Normalize only
    # those aliases; user-created symlink output directories remain rejected.
    for alias in (Path('/tmp'), Path('/var')):
        if alias.is_symlink() and path.is_relative_to(alias):
            path = alias.resolve() / path.relative_to(alias)
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'Symlink output path')
    if path.exists():
        raise FileExistsError(path)
    return path


def atomic_json(path, value):
    path = Path(path)
    require(not path.is_symlink() and (not path.exists() or path.stat().st_nlink == 1), 'Unsafe receipt path')
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def load_tools(root):
    """Read existing stdlib-only supervisor/CSV helpers, never the model stack."""
    root = Path(root).resolve(strict=True)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts import early_curriculum_study as early
    path = root / 'experiments/analysis/night_20261101/run_jobs.py'
    spec = importlib.util.spec_from_file_location('_targeting_prior_runner', path)
    jobs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jobs)
    jobs.ROOT = root
    return SimpleNamespace(early=early, jobs=jobs)


def build_jobs(root, out, weights, phase, *, candidate=None):
    require(phase in ('selection', 'confirmation'), 'Unknown fixed phase')
    require(candidate is None if phase == 'selection' else candidate in ('P', 'PT'), 'Invalid nominee')
    require(set(weights) == {'baseline', 'P', 'PT'}, 'Bind baseline, P and PT paths')
    root, out = Path(root), Path(out)
    roles = ('baseline', 'P', 'PT') if phase == 'selection' else ('baseline', candidate)
    first, n = (841000, 100) if phase == 'selection' else (842000, 300)
    jobs = []
    for role in roles:
        flag = 'false' if role == 'baseline' else 'true'
        jobs.append(dict(name=f'{role}_panel', role=role, engine='par_eval', timing_class='combined_panel',
            weights=str(weights[role]), first_seed=first, n_maps=n, opponents=[*PANEL, 'default'],
            overrides=[f'point_pair_swap={flag}', f'art_move_guard={flag}'],
            workers=2, games=n * 14, out=str(out / f'{role}_panel.csv'), log=str(out / f'{role}_panel.log')))
        if role != 'baseline':
            jobs.append(dict(name=f'{role}_direct', role=role, engine='par_eval', timing_class='direct',
                weights=str(weights[role]), first_seed=841000 if phase == 'selection' else 843000,
                n_maps=n, opponents=[DIRECT],
                overrides=[f'point_pair_swap={flag}', f'art_move_guard={flag}'],
                workers=2, games=2*n, out=str(out / f'{role}_direct.csv'),
                log=str(out / f'{role}_direct.log')))
    for job in jobs:
        job['root'] = str(root)
    require(sum(j['games'] for j in jobs) == (4600 if phase == 'selection' else 9000), 'Wrong fixed game count')
    return jobs


def parse_power(text):
    power = re.search(r"Now drawing from '(AC Power|Battery Power)'", text)
    percentages = re.findall(r'\b(\d{1,3})%;', text)
    require(power and len(percentages) == 1 and 0 <= int(percentages[0]) <= 100, 'Unknown power/battery state')
    return power[1] == 'AC Power', int(percentages[0])


def power_allowed(power, *, start):
    ac, percent = power
    return ac or percent >= 35 if start else ac or percent > 25


def current_power():
    return parse_power(subprocess.check_output(['pmset', '-g', 'batt'], text=True))


def effective_rates(observed):
    require(set(observed) == set(INITIAL_RATES), 'Unknown/missing timing class')
    require(all(isinstance(values, list) and all(math.isfinite(v) and v > 0 for v in values)
                for values in observed.values()), 'Invalid observed WALL seconds/game')
    maxima = {name: max(values, default=0.) for name, values in observed.items()}
    slowdown = max(1., *(maxima[name] / initial for name, initial in INITIAL_RATES.items()))
    effective = {name: max(maxima[name], initial * slowdown) for name, initial in INITIAL_RATES.items()}
    return effective, slowdown


def project_seconds(games, observed):
    require(set(games) == set(INITIAL_RATES)
            and all(type(n) is int and n >= 0 for n in games.values()), 'Invalid remaining class counts')
    rates, _ = effective_rates(observed)
    return 1.2 * sum(games[name] * rates[name] for name in INITIAL_RATES)


def admit(games, observed, *, now, deadline=DEADLINE):
    projected = project_seconds(games, observed)
    require(math.isfinite(now) and now + projected + RESERVE < deadline,
            'Insufficient time for ALL remaining games +20% and 60-minute closing reserve')
    return projected


def validate_csv(path, job, tools):
    # Existing schema, point-counting and outcome semantics; tighten integer
    # keys/counters/ranges here for the seven opponents and direct comparison.
    rows = tools.early.read_rows(path)
    with Path(path).open(newline='') as stream:
        require(csv.DictReader(stream).fieldnames == list(tools.early.GAME_FIELDS), 'Unexpected CSV schema/order')
    expected = {(seed, side, opponent)
                for seed in range(job['first_seed'], job['first_seed'] + job['n_maps'])
                for side in SIDES for opponent in job['opponents']}
    seen = set()
    for row in rows:
        seed = float(row['seed'])
        require(seed.is_integer(), 'Noninteger seed')
        key = int(seed), row['side'], row['opponent']
        require(key in expected and key not in seen, f'Unexpected/duplicate key: {key}')
        seen.add(key)
        numbers = {k: float(v) for k, v in row.items() if k not in ('side', 'opponent')}
        require(all(math.isfinite(v) for v in numbers.values()), 'Nonfinite row')
        require(numbers['secs'] >= 0 and numbers['steps'] == 303 and numbers['point_counting_version'] == 2,
                'Wrong runtime/course steps/point version')
        for name in ('sap_attempts', 'sap_hits', 'relics_found', 'relics_seen',
                     'known_point_tiles', 'belief_contradictions', 'unit_steps', 'our_points', 'opp_points'):
            require(numbers[name].is_integer() and numbers[name] >= 0, f'Invalid {name}')
        for name in ('wait_frac', 'invalid_frac', 'greedy_masked_frac', 'stack_frac'):
            require(0 <= numbers[name] <= 1, f'Invalid {name}')
    require(seen == expected and len(rows) == job['games'], 'Incomplete CSV game keys')
    return len(rows)


def validate_output(target, job):
    """Public integrity boundary used by the separate statistical audit."""
    return validate_csv(target, job, load_tools(job['root']))


def read_json(path):
    return json.loads(Path(path).read_text())


def identity(frozen, tools):
    return dict(source=tools.early.source_identity(frozen['root'], frozen['python'], frozen['protocols']),
                weights=tools.early.hashes(frozen['frozen_weights']),
                driver=dict(path=frozen['driver']['path'], sha256=digest(frozen['driver']['path'])))


def check_freeze(path, *, expected_sha=None, tools=None):
    path = Path(path).resolve(strict=True)
    require(path.is_file() and (expected_sha is None or digest(path) == expected_sha), 'Study freeze SHA mismatch')
    frozen = read_json(path)
    require(frozen['schema_version'] == 1 and set(frozen['weights']) == {'baseline', 'P', 'PT'}, 'Invalid shared study freeze')
    require(frozen['driver']['path'] == str(Path(__file__).resolve()), 'Use the recorded reviewed driver path')
    require(re.fullmatch('[0-9a-f]{40}', frozen['expected_head']), 'Invalid full HEAD pin')
    tools = tools or load_tools(frozen['root'])
    require(frozen['identity']['source']['head'] == frozen['expected_head'], 'Wrong source HEAD')
    require(identity(frozen, tools) == frozen['identity'], 'Shared source/HEAD/interpreter/protocol/weights/driver freeze changed')
    return frozen


def create_freeze(root, out, weights, *, python, protocols, expected_head):
    root, out = Path(root).resolve(strict=True), new_path(out)
    require(out.suffix == '.json' and out.parent.is_dir(), 'Use new JSON in an existing output directory')
    require(set(weights) == {'baseline', 'P', 'PT'} and protocols, 'Bind all three models and performance protocols')
    tools = load_tools(root)
    models = {role: str((root / path).resolve(strict=True)) for role, path in weights.items()}
    paths = set(map(Path, models.values()))
    paths.update((root / o[5:]).resolve(strict=True) for o in (*PANEL, DIRECT) if o.startswith('self:'))
    active = [(root / f'agents/sherlock/weights/agent_p{i}.pth').resolve(strict=True) for i in (0, 1)]
    paths.update(active)
    require(all(p.is_file() for p in paths), 'Missing actual model input; random fallback forbidden')
    for path in [Path(models['baseline']), root / DIRECT[5:], *active]:
        require(digest(path) == SOURCE_SHA, f'Wrong fixed V14 source SHA: {path}')
    frozen = dict(schema_version=1, root=str(root), python=str(Path(python).absolute()),
                  expected_head=expected_head, weights=models,
                  protocols=[str(Path(p).resolve(strict=True)) for p in protocols],
                  frozen_weights=tools.early.hashes(paths),
                  driver=dict(path=str(Path(__file__).resolve()), sha256=digest(__file__)))
    frozen['identity'] = identity(frozen, tools)
    require(frozen['identity']['source']['head'] == expected_head, 'Actual HEAD differs from expected reviewed HEAD')
    with out.open('x') as stream:
        json.dump(frozen, stream, indent=2, allow_nan=False)
        stream.write('\n')
    check_freeze(out, tools=tools)
    return frozen


def check_selection_summary(path, candidate, receipt):
    summary = read_json(path)
    require(receipt['status'] == 'complete' and receipt['phase'] == 'selection', 'Selection not complete')
    require(summary.get('status') == 'complete' and summary['phase'] == 'selection'
            and summary['nominee'] == candidate and candidate in ('P', 'PT'), 'Selection summary has no matching nominee')
    require(summary['plan_sha256'] == receipt['plan_sha256']
            and summary['study_freeze_sha256'] == receipt['study_freeze_sha256'], 'Unbound selection plan/freeze')
    expected = {r['out']: r['output_sha256'] for r in receipt['jobs']}
    require(summary['csv_sha256'] == expected and all(digest(p) == sha for p, sha in expected.items()),
            'Selection summary is not bound to every unchanged selection CSV')
    return summary


def check_complete_state(path, freeze_sha):
    state = read_json(path)
    require(state['status'] == 'complete' and state['phase'] == 'selection', 'Selection receipt incomplete')
    plan_path = Path(state['plan_path']).resolve(strict=True)
    require(digest(plan_path) == state['plan_sha256'] and state['study_freeze_sha256'] == freeze_sha,
            'Selection receipt plan/freeze changed')
    plan = read_json(plan_path)
    require(plan['phase'] == 'selection' and plan['study_freeze_sha256'] == freeze_sha, 'Wrong selection phase')
    frozen = check_freeze(plan['study_freeze_path'], expected_sha=freeze_sha)
    expected_jobs = build_jobs(frozen['root'], plan_path.parent, frozen['weights'], 'selection')
    require(plan['jobs'] == expected_jobs and len(state['jobs']) == len(expected_jobs), 'Incomplete fixed selection jobs')
    for job, record in zip(expected_jobs, state['jobs']):
        require(record['status'] == 'complete' and record['exit_code'] == 0
                and record['name'] == job['name'] and record['out'] == job['out']
                and record['timing_class'] == job['timing_class']
                and record['actual_games'] == job['games'] and digest(job['out']) == record['output_sha256'],
                'Incomplete/corrupt selection output receipt')
    require(state['source_before'] == state['source_after'] == frozen['identity'], 'Selection source freeze mismatch')
    return state


def observed_receipt_rates(receipt):
    observed = {name: [] for name in INITIAL_RATES}
    for record in receipt['jobs']:
        require(record['status'] == 'complete' and record['timing_class'] in INITIAL_RATES
                and type(record['actual_games']) is int and record['actual_games'] > 0
                and math.isfinite(record['wall_seconds']) and record['wall_seconds'] > 0,
                'Invalid completed WALL-time receipt')
        observed[record['timing_class']].append(record['wall_seconds'] / record['actual_games'])
    effective_rates(observed)
    return observed


def prepare_phase(freeze_path, out, phase, *, candidate=None,
                  selection_state=None, selection_summary=None):
    freeze_path, out = Path(freeze_path).resolve(strict=True), new_path(out)
    frozen = check_freeze(freeze_path)
    jobs = build_jobs(frozen['root'], out, frozen['weights'], phase, candidate=candidate)
    plan = dict(schema_version=1, phase=phase, candidate=candidate,
                study_freeze_path=str(freeze_path), study_freeze_sha256=digest(freeze_path),
                initial_seconds_per_game=dict(INITIAL_RATES), prior_observed_seconds_per_game={name: [] for name in INITIAL_RATES},
                deadline_utc='2026-11-03T04:30:00+00:00', reserve_seconds=RESERVE,
                future_confirmation_games=dict(combined_panel=8400, direct=600) if phase == 'selection'
                    else dict(combined_panel=0, direct=0),
                jobs=jobs)
    if phase == 'confirmation':
        require(selection_state and selection_summary, 'Confirmation requires complete selection state and pinned summary')
        receipt = check_complete_state(selection_state, plan['study_freeze_sha256'])
        check_selection_summary(selection_summary, candidate, receipt)
        plan.update(prior_observed_seconds_per_game=observed_receipt_rates(receipt),
                    selection_state_path=str(Path(selection_state).resolve(strict=True)),
                    selection_state_sha256=digest(selection_state),
                    selection_summary_path=str(Path(selection_summary).resolve(strict=True)),
                    selection_summary_sha256=digest(selection_summary))
    else:
        require(not selection_state and not selection_summary, 'Selection cannot consume an outcome summary')
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'plan.json').open('x') as stream:
        json.dump(plan, stream, indent=2, allow_nan=False)
        stream.write('\n')
    return plan


def check_plan(path, tools=None):
    path = Path(path).resolve(strict=True)
    plan = read_json(path)
    require(path.name == 'plan.json' and plan['schema_version'] == 1, 'Invalid phase plan')
    frozen = check_freeze(plan['study_freeze_path'], expected_sha=plan['study_freeze_sha256'], tools=tools)
    require(plan['jobs'] == build_jobs(frozen['root'], path.parent, frozen['weights'], plan['phase'], candidate=plan['candidate']),
            'Fixed phase commands/paths/opponents/counts changed')
    require(plan['deadline_utc'] == '2026-11-03T04:30:00+00:00' and plan['reserve_seconds'] == RESERVE
            and plan['future_confirmation_games'] == (dict(combined_panel=8400, direct=600) if plan['phase'] == 'selection'
                                                        else dict(combined_panel=0, direct=0))
            and plan['initial_seconds_per_game'] == INITIAL_RATES,
            'Deadline/reserve/future-work binding changed')
    expected_prior = {name: [] for name in INITIAL_RATES}
    if plan['phase'] == 'confirmation':
        require(digest(plan['selection_state_path']) == plan['selection_state_sha256']
                and digest(plan['selection_summary_path']) == plan['selection_summary_sha256'], 'Selection state/summary changed')
        receipt = check_complete_state(plan['selection_state_path'], plan['study_freeze_sha256'])
        check_selection_summary(plan['selection_summary_path'], plan['candidate'], receipt)
        expected_prior = observed_receipt_rates(receipt)
    require(plan['prior_observed_seconds_per_game'] == expected_prior, 'Prior study WALL-time observations changed')
    return plan, frozen


def job_args(job):
    return ['--weights', job['weights'], '--first', str(job['first_seed'] - 500000),
            '--n', str(job['n_maps']), '--opponents', ','.join(job['opponents']),
            '--workers', str(job['workers']), '--out', job['out'],
            *(item for flag in job['overrides'] for item in ('--set', flag))]


def job_command(job, python):
    require(job['engine'] == 'par_eval' and job['workers'] == 2, 'Only fixed two-worker par_eval jobs are allowed')
    return [python, '-B', '-m', 'scripts.par_eval', *job_args(job)]


def check_foreign_jobs(tools):
    tools.early.check_resources()
    text = subprocess.check_output(['ps', '-axo', 'pid=,args='], text=True)
    require(not re.search(r'(?:-m\s+scripts\.|scripts/)(?:targeting_adapt)(?:\s|\.py\b)|train_targeting\.py', text),
            'Targeting training supervisor/arm still active')


def run_job(job, plan_path, plan, frozen, tools, *, record=None, save=None):
    """Launch only the fixed child and own/stop its complete process group."""
    for key in ('out', 'log'):
        new_path(job[key])
    tools.jobs.validate_inputs(job_args(job), frozen['frozen_weights'])
    require(power_allowed(current_power(), start=True), 'Battery below 35%; no new long job')
    check_freeze(plan['study_freeze_path'], expected_sha=plan['study_freeze_sha256'], tools=tools)
    command = job_command(job, frozen['python'])
    record = record if record is not None else {}
    record.update(name=job['name'], timing_class=job['timing_class'], status='running', command=command, out=job['out'],
                  log=job['log'], started_at=stamp(), exit_code=None)
    started = time.monotonic()
    process = None
    try:
        with Path(job['log']).open('x') as log:
            blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGHUP, signal.SIGINT, signal.SIGTERM})
            try:
                # Reuse the existing study supervisor's protected registration
                # window and stdlib exec launcher. The child restores the old
                # mask while the parent cannot be interrupted before ownership.
                launcher = ('import os, signal, sys; '
                    f'signal.pthread_sigmask(signal.SIG_SETMASK, {sorted(map(int, blocked))!r}); '
                    'os.execvpe(sys.argv[1], sys.argv[1:], os.environ)')
                launch_command = [frozen['python'], '-B', '-c', launcher, *command]
                record['launch_command'] = launch_command
                process = subprocess.Popen(launch_command, cwd=frozen['root'], env={**os.environ, **tools.early.THREAD_ENV},
                                           stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                tools.early.CURRENT = dict(process=process, owner_pid=os.getpid(), pgid=process.pid)
                record.update(pid=process.pid, pgid=process.pid, owner_pid=os.getpid())
                if save:
                    save()
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
            while process.poll() is None:
                require(time.time() < DEADLINE - RESERVE, 'Hard game deadline reached; preserve 60-minute reserve')
                require(power_allowed(current_power(), start=False), 'Battery <=25%; stopping owned evaluation process group')
                check_freeze(plan['study_freeze_path'], expected_sha=plan['study_freeze_sha256'], tools=tools)
                try:
                    process.wait(timeout=min(15, max(.01, DEADLINE - RESERVE - time.time())))
                except subprocess.TimeoutExpired:
                    pass
        record.update(exit_code=process.returncode, wall_seconds=time.monotonic() - started, finished_at=stamp())
        require(process.returncode == 0, f'Evaluation child failed: {job["log"]}')
        require(time.time() < DEADLINE - RESERVE, 'Hard game deadline reached')
        check_freeze(plan['study_freeze_path'], expected_sha=plan['study_freeze_sha256'], tools=tools)
        record.update(actual_games=validate_csv(job['out'], job, tools), output_sha256=digest(job['out']), status='complete')
        return record
    except BaseException as exc:
        record.update(status='incomplete', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGHUP, signal.SIGINT, signal.SIGTERM})
        try:
            if process is not None and tools.early.group_exists(process.pid):
                tools.early.stop_group(process)
            tools.early.CURRENT = None
            record.update(exit_code=process.returncode if process is not None else None,
                          wall_seconds=time.monotonic() - started, finished_at=stamp())
            if save:
                save()
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, blocked)


def run_phase(plan_path, *, start=False):
    require(start, 'Explicit --start required; prepare/import never launches games')
    plan_path = Path(plan_path).resolve(strict=True)
    plan, frozen = check_plan(plan_path)
    tools = load_tools(frozen['root'])
    state_path = new_path(plan_path.parent / 'state.json')
    for job in plan['jobs']:
        new_path(job['out']); new_path(job['log'])
        tools.jobs.validate_inputs(job_args(job), frozen['frozen_weights'])
    state = dict(schema_version=1, phase=plan['phase'], status='running', started_at=stamp(),
                 plan_path=str(plan_path), plan_sha256=digest(plan_path),
                 study_freeze_sha256=plan['study_freeze_sha256'],
                 source_before=frozen['identity'], jobs=[])
    observed = {name: list(values) for name, values in plan['prior_observed_seconds_per_game'].items()}
    state['observed_seconds_per_game'] = observed
    old_signals = {sig: signal.getsignal(sig) for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)}
    owns_state = False

    def interrupted(sig, frame):
        raise InterruptedError(f'Own evaluation supervisor received signal {sig}')

    try:
        with tools.early.resource_lock(frozen['root']):
            # The pre-lock path check is advisory: another invocation may have
            # reserved a receipt while we acquired the shared resource lock.
            new_path(state_path)
            with state_path.open('x') as stream:
                owns_state = True
                json.dump(state, stream, indent=2, allow_nan=False)
                stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
            check_foreign_jobs(tools)
            for sig in old_signals:
                signal.signal(sig, interrupted)
            for index, job in enumerate(plan['jobs']):
                require(digest(plan_path) == state['plan_sha256'], 'Phase plan changed')
                check_plan(plan_path, tools=tools)
                require(power_allowed(current_power(), start=True), 'Battery below 35%; no new long job')
                remaining = {name: sum(j['games'] for j in plan['jobs'][index:] if j['timing_class'] == name)
                                   + plan['future_confirmation_games'][name] for name in INITIAL_RATES}
                rates, slowdown = effective_rates(observed)
                state['projection'] = dict(remaining_games=remaining, initial_wall_seconds_per_game=dict(INITIAL_RATES),
                                          effective_wall_seconds_per_game=rates, global_slowdown_factor=slowdown,
                                          seconds_plus_twenty_percent=admit(remaining, observed, now=time.time()),
                                          closing_reserve_seconds=RESERVE, checked_at=stamp())
                state['jobs'].append(dict(name=job['name'], status='running', out=job['out'], log=job['log']))
                atomic_json(state_path, state)
                result = run_job(job, plan_path, plan, frozen, tools, record=state['jobs'][-1],
                                 save=lambda: atomic_json(state_path, state))
                state['jobs'][-1] = result
                observed[job['timing_class']].append(result['wall_seconds'] / result['actual_games'])
                atomic_json(state_path, state)
            state['source_after'] = identity(frozen, tools)
            require(state['source_after'] == state['source_before'], 'Source/HEAD/weights changed across phase')
            require(digest(plan_path) == state['plan_sha256'], 'Phase plan changed during last child')
            check_plan(plan_path, tools=tools)
            require(time.time() < DEADLINE - RESERVE, 'Hard phase deadline reached')
            state.update(status='complete', completed_games=sum(r['actual_games'] for r in state['jobs']), finished_at=stamp())
            atomic_json(state_path, state)
    except BaseException as exc:
        state.update(status='incomplete', error=f'{type(exc).__name__}: {exc}', finished_at=stamp())
        if state['jobs'] and state['jobs'][-1]['status'] == 'running':
            state['jobs'][-1].update(status='incomplete', error=state['error'])
        if owns_state:
            atomic_json(state_path, state)
        raise
    finally:
        for sig, previous in old_signals.items():
            signal.signal(sig, previous)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    freeze = sub.add_parser('freeze', help='Pin one shared study; never starts games')
    freeze.add_argument('--root', type=Path, required=True)
    freeze.add_argument('--out', type=Path, required=True)
    freeze.add_argument('--python', type=Path, required=True)
    freeze.add_argument('--expected-head', required=True)
    freeze.add_argument('--protocol', type=Path, action='append', required=True)
    for role in ('baseline', 'p', 'pt'):
        freeze.add_argument('--' + role, required=True)
    prepare = sub.add_parser('prepare', help='Write one fresh fixed phase plan; never starts games')
    prepare.add_argument('--freeze', type=Path, required=True)
    prepare.add_argument('--out', type=Path, required=True)
    prepare.add_argument('--phase', choices=('selection', 'confirmation'), required=True)
    prepare.add_argument('--candidate', choices=('P', 'PT'))
    prepare.add_argument('--selection-state', type=Path)
    prepare.add_argument('--selection-summary', type=Path)
    run = sub.add_parser('run', help='Explicit execution, admission and owned process-group monitoring')
    run.add_argument('--plan', type=Path, required=True)
    run.add_argument('--start', action='store_true', required=True)
    args = parser.parse_args()
    if args.command == 'freeze':
        create_freeze(args.root, args.out, dict(baseline=args.baseline, P=args.p, PT=args.pt),
                      python=args.python, protocols=args.protocol, expected_head=args.expected_head)
    elif args.command == 'prepare':
        prepare_phase(args.freeze, args.out, args.phase,
                      candidate=args.candidate, selection_state=args.selection_state, selection_summary=args.selection_summary)
    elif args.command == 'run':
        result = run_phase(args.plan, start=args.start)
        print(json.dumps(dict(status=result['status'], completed_games=result['completed_games'])))


if __name__ == '__main__':
    main()
