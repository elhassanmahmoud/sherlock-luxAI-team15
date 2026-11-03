"""Fixed final Battle study. Only `run --plan FILE --start` launches games.

Preparation and statistics never load models or promote weights. One immutable
freeze binds the complete screen and its single optional confirmation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time

# Reuse reviewed, generic stdlib helpers, not the prior P/PT schedules or gates.
_PRIOR_PATH = Path(__file__).resolve().parents[1] / 'experiments/analysis/continuation_20261102/performance/targeting_eval_driver.py'
_spec = importlib.util.spec_from_file_location('_final_battle_prior_driver', _PRIOR_PATH)
prior = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prior)
require, digest, new_path = prior.require, prior.digest, prior.new_path
atomic_json, read_json, load_tools = prior.atomic_json, prior.read_json, prior.load_tools
validate_output, validate_csv = prior.validate_output, prior.validate_csv
parse_power, power_allowed, current_power = prior.parse_power, prior.power_allowed, prior.current_power
effective_rates, project_seconds = prior.effective_rates, prior.project_seconds
observed_receipt_rates = prior.observed_receipt_rates
job_args, job_command, stamp = prior.job_args, prior.job_command, prior.stamp
PANEL, DIRECT, SIDES, SOURCE_SHA = prior.PANEL, prior.DIRECT, prior.SIDES, prior.SOURCE_SHA
INITIAL_RATES = dict(prior.INITIAL_RATES)
GAME_END = datetime(2026, 11, 4, 12, 30, tzinfo=timezone.utc).timestamp()
RESERVE = 3600  # Internal setup/data-review transitions, in addition to game-end cap.
STOP_FILE = Path('/tmp/sherlock-final-20261103/STOP')
PROTOCOL = 'docs/superpowers/plans/2026-11-03-final-battle.md'
NET_COUNTS = dict(PAIR18=18, PAIR24=24, FT18=18, Z36=36, C36=36, R36=36)
BASE_ROLES = ('PAIR18', 'PAIR24', 'FT18', 'Z36')
EPS = 1e-9


def candidate_roles(weights):
    require(isinstance(weights, dict), 'Weights must be a role-to-path mapping')
    allowed = {'baseline', *BASE_ROLES}
    require(set(weights) in (allowed, allowed | {'C36', 'R36'}),
            'Freeze baseline+PAIR18/PAIR24/FT18/Z36; optional C36 and R36 must appear together')
    require(all(isinstance(p, (str, Path)) and str(p) for p in weights.values()), 'Invalid weight path')
    return (*BASE_ROLES, 'C36', 'R36') if 'R36' in weights else BASE_ROLES


def build_jobs(root, out, weights, phase, *, candidate=None):
    require(phase in ('selection', 'confirmation'), 'Unknown fixed phase')
    roles = candidate_roles(weights)
    require(candidate is None if phase == 'selection' else candidate in roles and candidate != 'C36',
            'Invalid nominee; C36 is only a methodological control')
    root, out = Path(root), Path(out)
    selected = ('baseline', *roles) if phase == 'selection' else ('baseline', candidate)
    first, n = (851000, 80) if phase == 'selection' else (852000, 400)
    jobs = []
    for role in selected:
        for kind, opponents, seed in [('panel', [*PANEL, 'default'], first),
                                      *([('direct', [DIRECT], 851000 if phase == 'selection' else 853000)]
                                        if role != 'baseline' else [])]:
            jobs.append(dict(name=f'{role}_{kind}', role=role, engine='par_eval',
                timing_class='combined_panel' if kind == 'panel' else 'direct', root=str(root),
                weights=str(weights[role]), first_seed=seed, n_maps=n, opponents=opponents,
                overrides=[], workers=2, games=2 * n * len(opponents),
                out=str(out / f'{role}_{kind}.csv'), log=str(out / f'{role}_{kind}.log')))
    require(sum(j['games'] for j in jobs) == (1120 + 1280 * len(roles) if phase == 'selection' else 12000),
            'Wrong fixed game count')
    return jobs


def gates(phase, panel, solution, default, direct, *, control_panel=None, control_solution=None):
    if phase == 'selection':
        checks = dict(panel_delta=panel['delta'] >= .005-EPS, solution_delta=solution['delta'] >= -EPS,
                      default=default['winrate'] >= .99-EPS, direct=direct['winrate'] >= .5-EPS)
        if control_panel is not None or control_solution is not None:
            require(control_panel is not None and control_solution is not None, 'Incomplete R36 control comparison')
            checks.update(control_panel=panel['delta'] >= control_panel['delta']-EPS,
                          control_solution=solution['delta'] >= control_solution['delta']-EPS)
        return checks
    require(phase == 'confirmation', 'Unknown gate phase')
    return dict(panel_delta=panel['delta'] >= .01-EPS, panel_lower=panel['low'] > EPS,
                solution_delta=solution['delta'] >= -EPS, solution_lower=solution['low'] > -.01+EPS,
                default=default['winrate'] >= .99-EPS, default_delta=default['delta'] >= -.01-EPS,
                direct_lower=direct['low'] > .5+EPS)


def nominee(results):
    valid = [name for name, value in results.items()
             if name in NET_COUNTS and name != 'C36' and value['passed']]
    return min(valid, key=lambda name: (-results[name]['panel']['delta'],
               -results[name]['opponents']['solution92']['delta'], NET_COUNTS[name], name)) if valid else None


def admit(games, observed, *, now, deadline=GAME_END):
    projected = project_seconds(games, observed)
    require(math.isfinite(now) and now + projected + RESERVE < deadline,
            'Insufficient time for ALL remaining games +20% and 60-minute internal transitions')
    return projected


def check_runtime(*, start):
    require(not STOP_FILE.exists(), f'STOP requested: {STOP_FILE}')
    require(time.time() < GAME_END, 'Hard game deadline reached')
    require(power_allowed(current_power(), start=start),
            'Battery below 35%; no new phase' if start else 'Battery <=25%; stop owned jobs')


def identity(frozen, tools):
    return dict(source=tools.early.source_identity(frozen['root'], frozen['python'], frozen['protocols']),
                weights=tools.early.hashes(frozen['frozen_weights']),
                driver=dict(path=str(Path(__file__).resolve()), sha256=digest(__file__)))


def check_freeze(path, *, expected_sha=None, tools=None):
    path = Path(path).resolve(strict=True)
    require(expected_sha is None or digest(path) == expected_sha, 'Study freeze SHA mismatch')
    frozen = read_json(path)
    require(frozen['schema_version'] == 1, 'Invalid shared study freeze')
    candidate_roles(frozen['weights'])
    require(frozen['driver']['path'] == str(Path(__file__).resolve()), 'Use recorded final study driver')
    require(re.fullmatch('[0-9a-f]{40}', frozen['expected_head']), 'Invalid full HEAD pin')
    tools = tools or load_tools(frozen['root'])
    require(frozen['identity']['source']['head'] == frozen['expected_head'], 'Wrong frozen source HEAD')
    require(identity(frozen, tools) == frozen['identity'],
            'Shared source/HEAD/interpreter/engine/protocol/weights/statistics freeze changed')
    return frozen


def create_freeze(root, out, weights, *, python, expected_head, protocols=(), training_omission_reason=None):
    root, out = Path(root).resolve(strict=True), new_path(out)
    require(out.suffix == '.json' and out.parent.is_dir(), 'Use new JSON in an existing directory')
    candidate_roles(weights)
    require('R36' in weights or (isinstance(training_omission_reason, str) and training_omission_reason.strip()),
            'Reduced roster requires a technical training omission reason before outcomes')
    tools = load_tools(root)
    models = {role: str((root / path).resolve(strict=True)) for role, path in weights.items()}
    paths = set(map(Path, models.values()))
    paths.update((root / o[5:]).resolve(strict=True) for o in (*PANEL, DIRECT) if o.startswith('self:'))
    active = [(root / f'agents/sherlock/weights/agent_p{i}.pth').resolve(strict=True) for i in (0, 1)]
    paths.update(active)
    require(all(p.is_file() for p in paths), 'Missing model input; random fallback forbidden')
    for path in [Path(models['baseline']), root / DIRECT[5:], *active]:
        require(digest(path) == SOURCE_SHA, f'Wrong fixed V14 SHA: {path}')
    frozen = dict(schema_version=1, root=str(root), python=str(Path(python).absolute()),
                  expected_head=expected_head, weights=models,
                  training_omission_reason=training_omission_reason,
                  protocols=sorted({str((root / p).resolve(strict=True)) for p in (PROTOCOL, *protocols)}),
                  frozen_weights=tools.early.hashes(paths),
                  driver=dict(path=str(Path(__file__).resolve()), sha256=digest(__file__)))
    frozen['identity'] = identity(frozen, tools)
    require(frozen['identity']['source']['head'] == expected_head, 'Actual HEAD differs from reviewed expected HEAD')
    require(re.fullmatch('[0-9a-f]{40}', expected_head), 'Invalid full HEAD pin')
    with out.open('x') as handle:
        json.dump(frozen, handle, indent=2, allow_nan=False)
        handle.write('\n')
    check_freeze(out, tools=tools)
    return frozen


def future_games(phase):
    return dict(combined_panel=11200, direct=800) if phase == 'selection' else dict(combined_panel=0, direct=0)


def reservation_path(freeze_path, phase):
    freeze_path = Path(freeze_path)
    return freeze_path.with_name(f'{freeze_path.stem}.{phase}.reservation.json')


def reservation(plan_path, plan):
    return dict(plan_path=str(Path(plan_path).resolve()), phase=plan['phase'],
                study_freeze_sha256=plan['study_freeze_sha256'])


def check_plan(path, tools=None):
    path = Path(path).resolve(strict=True)
    plan = read_json(path)
    require(path.name == 'plan.json' and plan['schema_version'] == 1, 'Invalid phase plan')
    frozen = check_freeze(plan['study_freeze_path'], expected_sha=plan['study_freeze_sha256'], tools=tools)
    require(read_json(reservation_path(plan['study_freeze_path'], plan['phase'])) == reservation(path, plan),
            'Phase is not the single reserved plan for this study')
    require(plan['jobs'] == build_jobs(frozen['root'], path.parent, frozen['weights'], plan['phase'], candidate=plan['candidate']),
            'Fixed phase roles/commands/paths/opponents/counts changed')
    require(plan['game_end_utc'] == '2026-11-04T12:30:00+00:00' and plan['reserve_seconds'] == RESERVE
            and plan['future_confirmation_games'] == future_games(plan['phase'])
            and plan['initial_seconds_per_game'] == INITIAL_RATES, 'Deadline/reserve/future-work binding changed')
    observed = {name: [] for name in INITIAL_RATES}
    if plan['phase'] == 'confirmation':
        require(digest(plan['selection_state_path']) == plan['selection_state_sha256']
                and digest(plan['selection_summary_path']) == plan['selection_summary_sha256'], 'Selection evidence changed')
        receipt = check_selection(plan['selection_state_path'], plan['selection_summary_path'],
                                  plan['candidate'], plan['study_freeze_sha256'])
        observed = observed_receipt_rates(receipt)
    require(plan['prior_observed_seconds_per_game'] == observed, 'Prior WALL-time observations changed')
    return plan, frozen


def validate_state(plan_path, state_path):
    plan_path, state_path = map(lambda p: Path(p).resolve(strict=True), (plan_path, state_path))
    plan, frozen = check_plan(plan_path)
    state = read_json(state_path)
    require(state['status'] == 'complete' and state['phase'] == plan['phase'], 'Phase incomplete')
    require(Path(state['plan_path']).resolve() == plan_path and state['plan_sha256'] == digest(plan_path)
            and state['study_freeze_sha256'] == plan['study_freeze_sha256'], 'Unbound state/plan/freeze')
    require(state['source_before'] == state['source_after'] == frozen['identity'], 'Source changed across phase')
    require(len(state['jobs']) == len(plan['jobs']), 'Incomplete fixed jobs')
    total = 0
    for job, done in zip(plan['jobs'], state['jobs']):
        require(done['status'] == 'complete' and done['exit_code'] == 0
                and done['name'] == job['name'] and done['out'] == job['out']
                and done['timing_class'] == job['timing_class'] and done['actual_games'] == job['games']
                and digest(job['out']) == done['output_sha256'], 'Incomplete/corrupt output receipt')
        total += validate_output(job['out'], job)
    require(state['completed_games'] == total, 'Wrong phase game total')
    return plan, frozen, state


def summary_data(plan_path, state_path):
    import pandas as pd
    from scripts.compare_report import compare_results
    from scripts.league_gates import panel_delta, direct_result
    plan, frozen, state = validate_state(plan_path, state_path)
    frames, directs, hashes = {}, {}, {}
    for job, done in zip(plan['jobs'], state['jobs']):
        frame = pd.read_csv(job['out'])
        (frames if job['timing_class'] == 'combined_panel' else directs)[job['role']] = frame
        hashes[job['out']] = done['output_sha256']
    roles = candidate_roles(frozen['weights']) if plan['phase'] == 'selection' else (plan['candidate'],)
    results = {}
    for role in roles:
        rows = {r['opponent']: r for r in compare_results(frames[role], frames['baseline'])}
        panel = panel_delta(frames[role], frames['baseline'], panel=PANEL)
        direct = direct_result(directs[role], DIRECT)
        require(panel['maps'] == direct['maps'] == (80 if plan['phase'] == 'selection' else 400), 'Incomplete maps')
        checks = gates(plan['phase'], panel, rows['solution92'], rows['default'], direct)
        counts = {}
        for opponent in (*PANEL, 'default'):
            counts[opponent] = {}
            for name in ('baseline', role):
                values = frames[name].loc[frames[name].opponent == opponent, 'result']
                counts[opponent]['baseline' if name == 'baseline' else 'candidate'] = dict(
                    games=len(values), wins=int((values == 1).sum()), draws=int((values == .5).sum()),
                    losses=int((values == 0).sum()))
        values = directs[role]['result']
        direct.update(wins=int((values == 1).sum()), draws=int((values == .5).sum()), losses=int((values == 0).sum()))
        results[role] = dict(panel=panel, direct=direct, opponents=rows, counts=counts,
                             gates={key: bool(value) for key, value in checks.items()}, passed=all(checks.values()))
    if plan['phase'] == 'selection' and 'R36' in results:
        r, c = results['R36'], results['C36']
        checks = gates('selection', r['panel'], r['opponents']['solution92'], r['opponents']['default'], r['direct'],
                       control_panel=c['panel'], control_solution=c['opponents']['solution92'])
        r.update(gates={key: bool(value) for key, value in checks.items()}, passed=all(checks.values()))
    return dict(schema_version=1, phase=plan['phase'], status='complete',
                study_freeze_sha256=plan['study_freeze_sha256'], plan_path=str(Path(plan_path).resolve()),
                plan_sha256=digest(plan_path), state_sha256=digest(state_path), csv_sha256=hashes,
                candidates=results, nominee=nominee(results) if plan['phase'] == 'selection' else plan['candidate'],
                promotion_qualified=bool(plan['phase'] == 'confirmation' and results[plan['candidate']]['passed']),
                completed_games=state['completed_games'], bootstrap_samples=5000, bootstrap_rng_seed=0,
                bootstrap_cluster='whole map, paired sides and all panel opponents')


def check_selection(state_path, summary_path, candidate, freeze_sha):
    receipt = read_json(state_path)
    require(receipt['phase'] == 'selection' and receipt['status'] == 'complete', 'Selection incomplete')
    require(receipt['study_freeze_sha256'] == freeze_sha, 'Wrong shared study freeze')
    # Recompute from the complete pinned plan/state and every original CSV.
    # A user-written JSON claiming passed/nominee is never an admission token.
    computed = summary_data(receipt['plan_path'], state_path)
    require(read_json(summary_path) == computed, 'Selection summary differs from complete recomputation')
    require(computed['nominee'] == candidate and candidate != 'C36', 'No matching eligible nominee')
    return receipt


def summarize(plan_path, state_path, out):
    out = new_path(out)
    result = summary_data(plan_path, state_path)
    with out.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    return result


def prepare_phase(freeze_path, out, phase, *, candidate=None, selection_state=None, selection_summary=None):
    freeze_path, out = Path(freeze_path).resolve(strict=True), new_path(out)
    frozen = check_freeze(freeze_path)
    jobs = build_jobs(frozen['root'], out, frozen['weights'], phase, candidate=candidate)
    plan = dict(schema_version=1, phase=phase, candidate=candidate,
                study_freeze_path=str(freeze_path), study_freeze_sha256=digest(freeze_path),
                initial_seconds_per_game=dict(INITIAL_RATES),
                prior_observed_seconds_per_game={name: [] for name in INITIAL_RATES},
                game_end_utc='2026-11-04T12:30:00+00:00', reserve_seconds=RESERVE,
                future_confirmation_games=future_games(phase), jobs=jobs)
    if phase == 'confirmation':
        require(selection_state and selection_summary, 'Confirmation requires complete selection state and summary')
        receipt = check_selection(selection_state, selection_summary, candidate, plan['study_freeze_sha256'])
        plan.update(prior_observed_seconds_per_game=observed_receipt_rates(receipt),
                    selection_state_path=str(Path(selection_state).resolve(strict=True)),
                    selection_state_sha256=digest(selection_state),
                    selection_summary_path=str(Path(selection_summary).resolve(strict=True)),
                    selection_summary_sha256=digest(selection_summary))
    else:
        require(not selection_state and not selection_summary, 'Selection cannot consume outcome evidence')
    # Reserve once per freeze, not merely once per output folder. An incomplete
    # screen/confirmation cannot be restarted under another directory name.
    reserved = new_path(reservation_path(freeze_path, phase))
    with reserved.open('x') as handle:
        json.dump(reservation(out / 'plan.json', plan), handle, indent=2, allow_nan=False)
        handle.write('\n')
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'plan.json').open('x') as handle:
        json.dump(plan, handle, indent=2, allow_nan=False)
        handle.write('\n')
    return plan


def model_supervisor_command(command):
    """Recognize real Python argv; shell snippets/`python -c` text aren't jobs."""
    try:
        args = shlex.split(command)
    except ValueError:
        return False
    if not args or not re.fullmatch(r'python(?:\d+(?:\.\d+)*)?', Path(args[0]).name):
        return False
    rest = args[1:]
    while rest and rest[0].startswith('-'):
        flag = rest.pop(0)
        if flag == '-c':
            return False
        if flag == '-m':
            if not rest:
                return False
            module, *options = rest
            if module == 'scripts.final_battle_study':
                return bool(options and options[0] == 'run')
            return module in ('scripts.final_rescue_train', 'scripts.final_training_supervisor') or module.startswith('scripts.targeting_adapt')
        if flag not in ('-B', '-I', '-u', '-E', '-s', '-S'):
            return False
    if rest and Path(rest[0]).name == 'final_battle_study.py':
        return len(rest) > 1 and rest[1] == 'run'
    return bool(rest and (Path(rest[0]).name in ('train_supervisor.py', 'final_training_supervisor.py',
                                               'final_rescue_train.py')
                          or Path(rest[0]).name.startswith('targeting_adapt')))


def check_foreign_jobs(tools):
    tools.early.check_resources()
    snapshot = subprocess.check_output(['ps', '-axo', 'pid=,args='], text=True)
    for line in snapshot.splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2 and parts[0].isdigit() and int(parts[0]) != os.getpid():
            require(not model_supervisor_command(parts[1]), 'Another training/final study supervisor is active')


def run_job(job, plan_path, plan, frozen, tools, *, record, save):
    """Own the child process group even on signals, deadline, STOP or failure."""
    for key in ('out', 'log'):
        new_path(job[key])
    tools.jobs.validate_inputs(job_args(job), frozen['frozen_weights'])
    check_runtime(start=True)
    check_freeze(plan['study_freeze_path'], expected_sha=plan['study_freeze_sha256'], tools=tools)
    command = job_command(job, frozen['python'])
    record.update(name=job['name'], timing_class=job['timing_class'], status='running', command=command,
                  out=job['out'], log=job['log'], started_at=stamp(), exit_code=None)
    started, process = time.monotonic(), None
    try:
        with Path(job['log']).open('x') as log:
            blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGHUP, signal.SIGINT, signal.SIGTERM})
            try:
                launcher = ('import os, signal, sys; '
                    f'signal.pthread_sigmask(signal.SIG_SETMASK, {sorted(map(int, blocked))!r}); '
                    'os.execvpe(sys.argv[1], sys.argv[1:], os.environ)')
                launch = [frozen['python'], '-B', '-c', launcher, *command]
                process = subprocess.Popen(launch, cwd=frozen['root'], env={**os.environ, **tools.early.THREAD_ENV},
                                           stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                tools.early.CURRENT = dict(process=process, owner_pid=os.getpid(), pgid=process.pid)
                record.update(pid=process.pid, pgid=process.pid, owner_pid=os.getpid(), launch_command=launch)
                save()
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
            while process.poll() is None:
                check_runtime(start=False)
                require(digest(plan_path) == record['plan_sha256'], 'Phase plan changed during child')
                check_freeze(plan['study_freeze_path'], expected_sha=plan['study_freeze_sha256'], tools=tools)
                try:
                    # Leave headroom for identity hashing while checking STOP
                    # and battery at least every 15 seconds in normal operation.
                    process.wait(timeout=min(10, max(.01, GAME_END - time.time())))
                except subprocess.TimeoutExpired:
                    pass
        require(process.returncode == 0, f'Evaluation child failed: {job["log"]}')
        check_runtime(start=False)
        require(digest(plan_path) == record['plan_sha256'], 'Phase plan changed during child')
        check_freeze(plan['study_freeze_path'], expected_sha=plan['study_freeze_sha256'], tools=tools)
        record.update(actual_games=validate_csv(job['out'], job, tools), output_sha256=digest(job['out']), status='complete')
    except BaseException as exc:
        record.update(status='incomplete', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGHUP, signal.SIGINT, signal.SIGTERM})
        try:
            try:
                if process is not None and tools.early.group_exists(process.pid):
                    tools.early.stop_group(process)
            except BaseException as exc:
                record.update(status='incomplete', error=f'Cleanup {type(exc).__name__}: {exc}')
                raise
            finally:
                tools.early.CURRENT = None
                record.update(exit_code=process.returncode if process is not None else None,
                              wall_seconds=time.monotonic()-started, finished_at=stamp())
                save()
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
    return record


def run_phase(plan_path, *, start=False):
    require(start, 'Explicit --start required')
    plan_path = Path(plan_path).resolve(strict=True)
    plan, frozen = check_plan(plan_path)
    tools = load_tools(frozen['root'])
    state_path = new_path(plan_path.parent / 'state.json')
    for job in plan['jobs']:
        new_path(job['out']); new_path(job['log'])
        tools.jobs.validate_inputs(job_args(job), frozen['frozen_weights'])
    state = dict(schema_version=1, phase=plan['phase'], status='running', started_at=stamp(),
                 plan_path=str(plan_path), plan_sha256=digest(plan_path),
                 study_freeze_sha256=plan['study_freeze_sha256'], source_before=frozen['identity'], jobs=[])
    observed = {name: list(values) for name, values in plan['prior_observed_seconds_per_game'].items()}
    state['observed_seconds_per_game'] = observed
    signals = {sig: signal.getsignal(sig) for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)}
    owns_state = False

    def interrupted(sig, frame):
        raise InterruptedError(f'Own supervisor received signal {sig}')

    try:
        with tools.early.resource_lock(frozen['root']):
            new_path(state_path)
            with state_path.open('x') as handle:
                owns_state = True
                json.dump(state, handle, indent=2, allow_nan=False)
                handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
            check_foreign_jobs(tools)
            for sig in signals:
                signal.signal(sig, interrupted)
            for index, job in enumerate(plan['jobs']):
                require(digest(plan_path) == state['plan_sha256'], 'Phase plan changed')
                check_plan(plan_path, tools=tools)
                check_runtime(start=True)
                remaining = {name: sum(j['games'] for j in plan['jobs'][index:] if j['timing_class'] == name)
                             + plan['future_confirmation_games'][name] for name in INITIAL_RATES}
                rates, slowdown = effective_rates(observed)
                state['projection'] = dict(remaining_games=remaining, initial_wall_seconds_per_game=INITIAL_RATES,
                    effective_wall_seconds_per_game=rates, global_slowdown_factor=slowdown,
                    seconds_plus_twenty_percent=admit(remaining, observed, now=time.time()),
                    internal_transition_reserve_seconds=RESERVE, checked_at=stamp())
                state['jobs'].append(dict(name=job['name'], status='running', out=job['out'], log=job['log'],
                                          plan_sha256=state['plan_sha256']))
                atomic_json(state_path, state)
                result = run_job(job, plan_path, plan, frozen, tools, record=state['jobs'][-1],
                                 save=lambda: atomic_json(state_path, state))
                observed[job['timing_class']].append(result['wall_seconds'] / result['actual_games'])
                atomic_json(state_path, state)
            state['source_after'] = identity(frozen, tools)
            require(state['source_after'] == state['source_before'], 'Source/HEAD/weights changed across phase')
            require(digest(plan_path) == state['plan_sha256'], 'Phase plan changed during last child')
            check_plan(plan_path, tools=tools)
            check_runtime(start=False)
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
        for sig, handler in signals.items():
            signal.signal(sig, handler)
    return state


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    freeze = commands.add_parser('freeze')
    for name in ('root', 'out', 'weights', 'python'):
        freeze.add_argument('--' + name, type=Path, required=True)
    freeze.add_argument('--expected-head', required=True)
    freeze.add_argument('--protocol', type=Path, action='append', default=[])
    freeze.add_argument('--training-omission-reason')
    prepare = commands.add_parser('prepare')
    for name in ('freeze', 'out'):
        prepare.add_argument('--' + name, type=Path, required=True)
    prepare.add_argument('--phase', choices=('selection', 'confirmation'), required=True)
    prepare.add_argument('--candidate', choices=tuple(name for name in NET_COUNTS if name != 'C36'))
    prepare.add_argument('--selection-state', type=Path)
    prepare.add_argument('--selection-summary', type=Path)
    run = commands.add_parser('run')
    run.add_argument('--plan', type=Path, required=True)
    run.add_argument('--start', action='store_true', required=True)
    summary = commands.add_parser('summarize')
    for name in ('plan', 'state', 'out'):
        summary.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == 'freeze':
        result = create_freeze(args.root, args.out, read_json(args.weights), python=args.python,
                               expected_head=args.expected_head, protocols=[*args.protocol, args.weights.resolve(strict=True)],
                               training_omission_reason=args.training_omission_reason)
    elif args.command == 'prepare':
        result = prepare_phase(args.freeze, args.out, args.phase, candidate=args.candidate,
                               selection_state=args.selection_state, selection_summary=args.selection_summary)
    elif args.command == 'run':
        result = run_phase(args.plan, start=args.start)
    else:
        result = summarize(args.plan, args.state, args.out)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
