"""Fixed network-breadth study (SOLO28 and FO42). Only `run --plan FILE --start` launches games.

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
_spec = importlib.util.spec_from_file_location('_breadth_prior_driver', _PRIOR_PATH)
prior = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prior)
require, digest, new_path = prior.require, prior.digest, prior.new_path
atomic_json, read_json, load_tools = prior.atomic_json, prior.read_json, prior.load_tools
validate_output, validate_csv = prior.validate_output, prior.validate_csv
parse_power, power_allowed, current_power = prior.parse_power, prior.power_allowed, prior.current_power
job_args, job_command, stamp = prior.job_args, prior.job_command, prior.stamp
PANEL, DIRECT, SIDES, SOURCE_SHA = prior.PANEL, prior.DIRECT, prior.SIDES, prior.SOURCE_SHA
INITIAL_RATES = dict(combined_panel=2.6, direct=3.5)
GAME_END = datetime(2026, 11, 4, 13, 30, tzinfo=timezone.utc).timestamp()
RESERVE = 1200  # Internal setup/data-review transitions, in addition to game-end cap.
STOP_FILE = Path('/tmp/sherlock-breadth-20261104/STOP')
USAGE_FILE = STOP_FILE.parent / 'watch/usage.json'
ANALYSIS = Path('experiments/analysis/network_breadth_20261104')
PROTOCOL = 'docs/superpowers/plans/2026-11-04-network-breadth.md'
NET_COUNTS = dict(SOLO28=1, FO42=42)
EPS = 1e-9


def analysis_output(root, path):
    target = new_path(path)
    allowed = (Path(root) / ANALYSIS).resolve()
    require(target.is_relative_to(allowed), 'Study outputs must stay in the network_breadth_20261104 analysis directory')
    return target


def study_reservation(root):
    return Path(root) / ANALYSIS / 'study.reservation.json'


def reserve_study(root, freeze_path):
    path = new_path(study_reservation(root))
    with path.open('x') as handle:
        json.dump(dict(freeze_path=str(Path(freeze_path).resolve())), handle, indent=2)
        handle.write('\n')


def effective_rates(observed):
    require(set(observed) == set(INITIAL_RATES), 'Unknown/missing timing class')
    require(all(isinstance(values, list) and all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in values)
                for values in observed.values()), 'Invalid observed WALL seconds/game')
    maxima = {name: max(values, default=0.) for name, values in observed.items()}
    slowdown = max(1., *(maxima[name] / initial for name, initial in INITIAL_RATES.items()))
    return {name: max(maxima[name], initial * slowdown) for name, initial in INITIAL_RATES.items()}, slowdown


def project_seconds(games, observed):
    require(set(games) == set(INITIAL_RATES) and all(type(n) is int and n >= 0 for n in games.values()),
            'Invalid remaining class counts')
    rates, _ = effective_rates(observed)
    return 1.2 * sum(games[name] * rates[name] for name in INITIAL_RATES)


def observed_receipt_rates(receipt):
    observed = {name: [] for name in INITIAL_RATES}
    for record in receipt['jobs']:
        require(record['status'] == 'complete' and record['timing_class'] in INITIAL_RATES
                and type(record['actual_games']) is int and record['actual_games'] > 0
                and type(record['wall_seconds']) in (int, float)
                and math.isfinite(record['wall_seconds']) and record['wall_seconds'] > 0,
                'Invalid completed WALL-time receipt')
        observed[record['timing_class']].append(record['wall_seconds'] / record['actual_games'])
    effective_rates(observed)
    return observed


def merge_rates(left, right):
    effective_rates(left)
    effective_rates(right)
    return {key: [*left[key], *right[key]] for key in INITIAL_RATES}


def pilot_rates(receipt):
    require(receipt.get('status') == 'complete', 'Pilot incomplete')
    observed = observed_receipt_rates(receipt)
    require(sorted((job['timing_class'], job['actual_games']) for job in receipt['jobs']) ==
            [('combined_panel', 12)] * 3 + [('direct', 4)] * 2, 'Expected exactly 44 technical pilot games')
    return observed


def check_usage(path, *, now):
    try:
        usage = read_json(path)
        when = datetime.fromisoformat(usage['at'].replace('Z', '+00:00'))
        require(when.tzinfo is not None and math.isfinite(now)
                and 0 <= now - when.timestamp() <= 900, 'Quota receipt stale or from future')
        values = [window['used_percent'] for window in usage['windows']]
        require(values and all(type(value) in (int, float) and math.isfinite(value)
                               and 0 <= value <= 100 for value in values), 'Unknown quota windows')
        used = usage['max_used_percent']
        require(type(used) in (int, float) and math.isfinite(used) and used == max(values), 'Inconsistent quota receipt')
        require(usage['ordinary_usage_allowed'] is True and used < 65, 'Quota >=65%; no new phase')
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError('Missing or malformed quota receipt; phase blocked') from exc
    return usage


def combined_solution(frames, phase):
    import pandas as pd
    from scripts.compare_report import validated_results
    panel = frames['panel'].loc[frames['panel'].opponent == 'solution92']
    first, count = (861000, 20) if phase == 'selection' else (862000, 400)
    parts = [panel] if phase == 'selection' else [panel, frames['solution_extra']]
    combined = validated_results(pd.concat(parts, ignore_index=True), 'Complete Solution blocks')
    expected = {(seed, side, 'solution92') for seed in range(first, first + count) for side in SIDES}
    actual = set(combined[['seed', 'side', 'opponent']].itertuples(index=False, name=None))
    require(actual == expected and len(combined) == 2 * count, 'Solution blocks missing, duplicate or extra keys')
    return combined


def candidate_roles(weights):
    require(isinstance(weights, dict) and set(weights) == {'baseline', *NET_COUNTS},
            'Freeze exactly baseline, SOLO28 and FO42')
    require(all(isinstance(p, (str, Path)) and str(p) for p in weights.values()), 'Invalid weight path')
    return tuple(NET_COUNTS)


def build_jobs(root, out, weights, phase, *, candidate=None):
    require(phase in ('selection', 'confirmation'), 'Unknown fixed phase')
    roles = candidate_roles(weights)
    require(candidate is None if phase == 'selection' else candidate in roles, 'Invalid nominee')
    root, out = Path(root), Path(out)
    selected = ('baseline', *roles) if phase == 'selection' else ('baseline', candidate)
    jobs = []
    for role in selected:
        blocks = [('panel', [*PANEL, 'default'], 861000, 20)] if phase == 'selection' else [
            ('panel', [*PANEL, 'default'], 862000, 80), ('solution_extra', ['solution92'], 862080, 320)]
        if role != 'baseline':
            blocks.append(('direct', [DIRECT], 861000 if phase == 'selection' else 863000,
                           20 if phase == 'selection' else 160))
        for kind, opponents, first, count in blocks:
            jobs.append(dict(name=f'{role}_{kind}', role=role, kind=kind, engine='par_eval',
                timing_class='direct' if kind == 'direct' else 'combined_panel', root=str(root),
                weights=str(weights[role]), first_seed=first, n_maps=count, opponents=opponents,
                overrides=[], workers=2, games=2 * count * len(opponents),
                out=str(out / f'{role}_{kind}.csv'), log=str(out / f'{role}_{kind}.log')))
    require(len(jobs) == 5 and sum(j['games'] for j in jobs) == (920 if phase == 'selection' else 3840),
            'Wrong fixed game count')
    return jobs


def gates(phase, panel, solution, default, direct):
    if phase == 'selection':
        return dict(panel_delta=panel['delta'] >= .005-EPS, solution_delta=solution['delta'] >= -EPS,
                    default=default['winrate'] >= .99-EPS, direct=direct['winrate'] >= .5-EPS)
    require(phase == 'confirmation', 'Unknown gate phase')
    return dict(panel_delta=panel['delta'] >= .01-EPS, panel_lower=panel['low'] > EPS,
                solution_delta=solution['delta'] >= -EPS, solution_lower=solution['low'] > -.01+EPS,
                default=default['winrate'] >= .99-EPS, default_delta=default['delta'] >= -.01-EPS,
                direct_lower=direct['low'] > .5+EPS)


def nominee(results):
    valid = [name for name, value in results.items()
             if name in NET_COUNTS and value['passed']]

    def half_win_delta(name, opponents):
        # Every screen role has identical validated denominators. Integer
        # half-wins preserve mathematical ties despite per-map float rounding.
        counts = results[name]['counts']
        return sum(2 * (counts[opponent]['candidate']['wins'] - counts[opponent]['baseline']['wins'])
                   + counts[opponent]['candidate']['draws'] - counts[opponent]['baseline']['draws']
                   for opponent in opponents)

    return min(valid, key=lambda name: (-half_win_delta(name, PANEL),
               -half_win_delta(name, ('solution92',)), NET_COUNTS[name], name)) if valid else None


def admit(games, observed, *, now, deadline=GAME_END):
    projected = project_seconds(games, observed)
    require(math.isfinite(now) and now + projected + RESERVE < deadline,
            'Insufficient time for ALL remaining games +20% and 20-minute internal transitions')
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
    require(read_json(study_reservation(frozen['root'])) == dict(freeze_path=str(path)),
            'Not the single reserved study freeze')
    require(frozen['pilot_observed_seconds_per_game'] == pilot_rates(read_json(frozen['pilot_receipt_path'])),
            'Pilot timing evidence changed')
    candidate_roles(frozen['weights'])
    require(frozen['driver']['path'] == str(Path(__file__).resolve()), 'Use recorded network-breadth driver')
    require(re.fullmatch('[0-9a-f]{40}', frozen['expected_head']), 'Invalid full HEAD pin')
    tools = tools or load_tools(frozen['root'])
    require(frozen['identity']['source']['head'] == frozen['expected_head'], 'Wrong frozen source HEAD')
    require(identity(frozen, tools) == frozen['identity'],
            'Shared source/HEAD/interpreter/engine/protocol/weights/statistics freeze changed')
    return frozen


def create_freeze(root, out, weights, *, python, expected_head, pilot_receipt,
                  protocols=(), candidate_manifest=None):
    root = Path(root).resolve(strict=True)
    out = analysis_output(root, out)
    require(out.suffix == '.json' and out.parent.is_dir(), 'Use new JSON in an existing directory')
    candidate_roles(weights)
    tools = load_tools(root)
    models = {role: str((root / path).resolve(strict=True)) for role, path in weights.items()}
    manifest_path = Path(candidate_manifest or Path(models['FO42']).parent / 'manifest.json').resolve(strict=True)
    manifest = read_json(manifest_path)
    require(manifest['status'] == 'BUILT_VERIFIED' and set(manifest['candidates']) == set(NET_COUNTS),
            'Candidate manifest is incomplete')
    for role, count in NET_COUNTS.items():
        entry = manifest['candidates'][role]
        require(Path(entry['path']).resolve(strict=True) == Path(models[role])
                and entry['sha256'] == digest(models[role]) and entry['net_count'] == count
                and entry['unique_tensor_count'] == count
                and len(entry['ordered_tensor_sha256']) == len(set(entry['ordered_tensor_sha256'])) == count,
                'Candidate manifest/model identity mismatch')
    require(manifest['candidates']['SOLO28']['configuration'] == manifest['candidates']['FO42']['configuration'],
            'Candidate configurations differ')
    paths = set(map(Path, models.values()))
    paths.update((root / o[5:]).resolve(strict=True) for o in (*PANEL, DIRECT) if o.startswith('self:'))
    active = [(root / f'agents/sherlock/weights/agent_p{i}.pth').resolve(strict=True) for i in (0, 1)]
    paths.update(active)
    for path, sha in manifest['sources'].items():
        require(digest(path) == sha, 'Candidate build source changed')
        paths.add(Path(path).resolve(strict=True))
    require(all(path.is_file() for path in paths), 'Missing model input; random fallback forbidden')
    for path in [Path(models['baseline']), root / DIRECT[5:], *active]:
        require(digest(path) == SOURCE_SHA, f'Wrong fixed V14 SHA: {path}')
    pilot_path = Path(pilot_receipt).resolve(strict=True)
    pilot = read_json(pilot_path)
    observations = pilot_rates(pilot)
    pilot_paths = []
    for job in pilot['jobs']:
        path = Path(job['out']).resolve(strict=True)
        require(digest(path) == job['output_sha256'] and job['exit_code'] == 0, 'Pilot output changed or failed')
        pilot_paths.append(path)
    frozen = dict(schema_version=1, root=str(root), python=str(Path(python).absolute()),
                  expected_head=expected_head, weights=models,
                  pilot_receipt_path=str(pilot_path), pilot_observed_seconds_per_game=observations,
                  protocols=sorted({str((root / path).resolve(strict=True)) for path in
                                    (PROTOCOL, manifest_path, pilot_path, *pilot_paths, *protocols)}),
                  frozen_weights=tools.early.hashes(paths),
                  driver=dict(path=str(Path(__file__).resolve()), sha256=digest(__file__)))
    frozen['identity'] = identity(frozen, tools)
    require(frozen['identity']['source']['head'] == expected_head, 'Actual HEAD differs from reviewed expected HEAD')
    require(re.fullmatch('[0-9a-f]{40}', expected_head), 'Invalid full HEAD pin')
    reserve_study(root, out)
    with out.open('x') as handle:
        json.dump(frozen, handle, indent=2, allow_nan=False)
        handle.write('\n')
    check_freeze(out, tools=tools)
    return frozen


def future_games(phase):
    return dict(combined_panel=3520, direct=320) if phase == 'selection' else dict(combined_panel=0, direct=0)


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
    require(plan['game_end_utc'] == '2026-11-04T13:30:00+00:00' and plan['reserve_seconds'] == RESERVE
            and plan['future_confirmation_games'] == future_games(plan['phase'])
            and plan['initial_seconds_per_game'] == INITIAL_RATES, 'Deadline/reserve/future-work binding changed')
    observed = {name: list(values) for name, values in frozen['pilot_observed_seconds_per_game'].items()}
    if plan['phase'] == 'confirmation':
        require(digest(plan['selection_state_path']) == plan['selection_state_sha256']
                and digest(plan['selection_summary_path']) == plan['selection_summary_sha256'], 'Selection evidence changed')
        receipt = check_selection(plan['selection_state_path'], plan['selection_summary_path'],
                                  plan['candidate'], plan['study_freeze_sha256'])
        observed = merge_rates(observed, observed_receipt_rates(receipt))
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
    frames, hashes = {}, {}
    for job, done in zip(plan['jobs'], state['jobs']):
        frames.setdefault(job['role'], {})[job['kind']] = pd.read_csv(job['out'])
        hashes[job['out']] = done['output_sha256']
    phase = plan['phase']
    roles = candidate_roles(frozen['weights']) if phase == 'selection' else (plan['candidate'],)
    results = {}
    for role in roles:
        candidate, baseline = frames[role]['panel'], frames['baseline']['panel']
        rows = {r['opponent']: r for r in compare_results(candidate, baseline)}
        panel = panel_delta(candidate, baseline, panel=PANEL)
        direct = direct_result(frames[role]['direct'], DIRECT)
        solution_frames = {name: combined_solution(frames[name], phase) for name in ('baseline', role)}
        rows['solution92'] = compare_results(solution_frames[role], solution_frames['baseline'])[0]
        panel_maps, solution_maps, direct_maps = (20, 20, 20) if phase == 'selection' else (80, 400, 160)
        require(panel['maps'] == panel_maps and direct['maps'] == direct_maps
                and rows['solution92']['maps'] == solution_maps and rows['default']['maps'] == panel_maps,
                'Incomplete expected maps')
        require(all(row['excluded_candidate'] == row['excluded_reference'] == 0 for row in rows.values()),
                'Subset comparison forbidden')
        checks = gates(phase, panel, rows['solution92'], rows['default'], direct)
        counts = {}
        for opponent in (*PANEL, 'default'):
            counts[opponent] = {}
            for name in ('baseline', role):
                frame = solution_frames[name] if opponent == 'solution92' else frames[name]['panel']
                values = frame.loc[frame.opponent == opponent, 'result']
                counts[opponent]['baseline' if name == 'baseline' else 'candidate'] = dict(
                    games=len(values), wins=int((values == 1).sum()), draws=int((values == .5).sum()),
                    losses=int((values == 0).sum()))
        values = frames[role]['direct']['result']
        direct.update(wins=int((values == 1).sum()), draws=int((values == .5).sum()), losses=int((values == 0).sum()))
        results[role] = dict(panel=panel, direct=direct, opponents=rows, counts=counts,
                            gates={key: bool(value) for key, value in checks.items()}, passed=all(checks.values()))
    return dict(schema_version=1, phase=phase, status='complete',
                study_freeze_sha256=plan['study_freeze_sha256'], plan_path=str(Path(plan_path).resolve()),
                plan_sha256=digest(plan_path), state_sha256=digest(state_path), csv_sha256=hashes,
                candidates=results, nominee=nominee(results) if phase == 'selection' else plan['candidate'],
                promotion_qualified=bool(phase == 'confirmation' and results[plan['candidate']]['passed']),
                completed_games=state['completed_games'], bootstrap_samples=5000, bootstrap_rng_seed=0,
                bootstrap_cluster='whole map, paired sides and all panel opponents',
                map_counts=dict(panel=panel_maps, solution=solution_maps, default=panel_maps, direct=direct_maps))


def check_selection(state_path, summary_path, candidate, freeze_sha):
    receipt = read_json(state_path)
    require(receipt['phase'] == 'selection' and receipt['status'] == 'complete', 'Selection incomplete')
    require(receipt['study_freeze_sha256'] == freeze_sha, 'Wrong shared study freeze')
    # Recompute from the complete pinned plan/state and every original CSV.
    # A user-written JSON claiming passed/nominee is never an admission token.
    computed = summary_data(receipt['plan_path'], state_path)
    require(read_json(summary_path) == computed, 'Selection summary differs from complete recomputation')
    require(computed['nominee'] == candidate and candidate in NET_COUNTS, 'No matching eligible nominee')
    return receipt


def summarize(plan_path, state_path, out):
    plan = read_json(plan_path)
    frozen = read_json(plan['study_freeze_path'])
    out = analysis_output(frozen['root'], out)
    result = summary_data(plan_path, state_path)
    with out.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    return result


def prepare_phase(freeze_path, out, phase, *, candidate=None, selection_state=None, selection_summary=None):
    freeze_path = Path(freeze_path).resolve(strict=True)
    frozen = check_freeze(freeze_path)
    out = analysis_output(frozen['root'], out)
    jobs = build_jobs(frozen['root'], out, frozen['weights'], phase, candidate=candidate)
    plan = dict(schema_version=1, phase=phase, candidate=candidate,
                study_freeze_path=str(freeze_path), study_freeze_sha256=digest(freeze_path),
                initial_seconds_per_game=dict(INITIAL_RATES),
                prior_observed_seconds_per_game={name: list(values) for name, values in frozen['pilot_observed_seconds_per_game'].items()},
                game_end_utc='2026-11-04T13:30:00+00:00', reserve_seconds=RESERVE,
                future_confirmation_games=future_games(phase), jobs=jobs)
    if phase == 'confirmation':
        require(selection_state and selection_summary, 'Confirmation requires complete selection state and summary')
        receipt = check_selection(selection_state, selection_summary, candidate, plan['study_freeze_sha256'])
        plan.update(prior_observed_seconds_per_game=merge_rates(plan['prior_observed_seconds_per_game'], observed_receipt_rates(receipt)),
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
    if not args or not re.fullmatch(r'python(?:\d+(?:\.\d+)*)?', Path(args[0]).name, flags=re.IGNORECASE):
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
            if module in ('scripts.final_battle_study', 'scripts.network_breadth_study'):
                return bool(options and options[0] == 'run')
            return module in ('scripts.final_rescue_train', 'scripts.final_training_supervisor') or module.startswith('scripts.targeting_adapt')
        if flag not in ('-B', '-I', '-u', '-E', '-s', '-S'):
            return False
    if rest and Path(rest[0]).name in ('final_battle_study.py', 'network_breadth_study.py'):
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
            state['usage_at_start'] = check_usage(USAGE_FILE, now=time.time())
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
    freeze.add_argument('--pilot-receipt', type=Path, required=True)
    freeze.add_argument('--candidate-manifest', type=Path)
    prepare = commands.add_parser('prepare')
    for name in ('freeze', 'out'):
        prepare.add_argument('--' + name, type=Path, required=True)
    prepare.add_argument('--phase', choices=('selection', 'confirmation'), required=True)
    prepare.add_argument('--candidate', choices=tuple(NET_COUNTS))
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
                               pilot_receipt=args.pilot_receipt, candidate_manifest=args.candidate_manifest)
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
