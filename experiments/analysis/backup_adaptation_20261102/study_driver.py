"""Conditional PT2 evaluation supervisor. Import/prepare never starts model jobs.

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
PARENT_HEAD = '03e54e267242ff642c126313fe5f512ed9d959ac'
SETUP_SECONDS = 1200
TRAINING_SECONDS = 3000
STUDY_NAME = 'conditional_backup_PT2_20261102'
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
    spec = importlib.util.spec_from_file_location('_backup_prior_runner', path)
    jobs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jobs)
    jobs.ROOT = root
    return SimpleNamespace(early=early, jobs=jobs)


def candidate_roles(weights):
    require(set(weights) == {'baseline', 'PT2'}, 'Freeze exactly baseline+PT2; no late P/PT additions')
    return ('PT2',)


def build_jobs(root, out, weights, phase, *, candidate=None):
    require(phase in ('selection', 'confirmation'), 'Unknown fixed phase')
    require(candidate is None if phase == 'selection' else candidate == 'PT2', 'Invalid nominee')
    candidate_roles(weights)
    root, out = Path(root), Path(out)
    first, n = (844000, 50) if phase == 'selection' else (842000, 300)
    jobs = []
    for role in ('baseline', 'PT2'):
        flag = 'false' if role == 'baseline' else 'true'
        jobs.append(dict(name=f'{role}_panel', role=role, engine='par_eval', timing_class='combined_panel',
            weights=str(weights[role]), first_seed=first, n_maps=n, opponents=[*PANEL, 'default'],
            overrides=[f'point_pair_swap={flag}', f'art_move_guard={flag}'],
            workers=2, games=n * 14, out=str(out / f'{role}_panel.csv'), log=str(out / f'{role}_panel.log')))
        if role == 'PT2':
            jobs.append(dict(name=f'{role}_direct', role=role, engine='par_eval', timing_class='direct',
                weights=str(weights[role]), first_seed=844000 if phase == 'selection' else 843000,
                n_maps=n, opponents=[DIRECT], overrides=[f'point_pair_swap={flag}', f'art_move_guard={flag}'],
                workers=2, games=2*n, out=str(out / f'{role}_direct.csv'), log=str(out / f'{role}_direct.log')))
    for job in jobs:
        job['root'] = str(root)
    require(sum(j['games'] for j in jobs) == (1500 if phase == 'selection' else 9000), 'Wrong fixed game count')
    return jobs


def build_parent_jobs(root, out, weights):
    """Historical P-only schedule; never import its live-HEAD guard."""
    require(set(weights) == {'baseline', 'P'}, 'Parent must be the predeclared P-only study')
    jobs = build_jobs(root, out, {'baseline': weights['baseline'], 'PT2': weights['P']}, 'selection')
    for job in jobs:
        job.update(name=job['name'].replace('PT2', 'P'), role=job['role'].replace('PT2', 'P'),
                   first_seed=841000, n_maps=100, games=job['games']*2,
                   out=job['out'].replace('PT2_', 'P_'), log=job['log'].replace('PT2_', 'P_'))
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
    projected = project_seconds(games, observed) + SETUP_SECONDS
    require(math.isfinite(now) and now + projected + RESERVE < deadline,
            'Insufficient time for ALL games +20%, 20-minute setup/audit and 60-minute reserve')
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
    require(frozen['schema_version'] == 2 and frozen['study_name'] == STUDY_NAME
            and frozen['master_path'] == str(path), 'Invalid or relocated PT2 study freeze')
    candidate_roles(frozen['weights'])
    require(frozen['driver']['path'] == str(Path(__file__).resolve()), 'Use the recorded reviewed driver path')
    require(re.fullmatch('[0-9a-f]{40}', frozen['expected_head']), 'Invalid full HEAD pin')
    tools = tools or load_tools(frozen['root'])
    require(frozen['identity']['source']['head'] == frozen['expected_head'], 'Wrong source HEAD')
    require(identity(frozen, tools) == frozen['identity'], 'Shared source/HEAD/interpreter/protocol/weights/driver freeze changed')
    expected_reservation = confirmation_receipt(path)
    require(check_parent(frozen['parent']['paths'], allowed_confirmation=expected_reservation) == frozen['parent'],
            'Historical parent archive changed')
    admission = frozen['candidate_admission']
    require(digest(admission['path']) == admission['sha256'], 'Candidate admission changed')
    check_candidate_admission(admission['path'], frozen['weights']['PT2'])
    require(frozen['phase_paths'] == {phase: str(path.parent / phase) for phase in ('selection', 'confirmation')}
            and frozen['confirmation_reservation'] == str(Path(frozen['parent']['master_path']).parent
                / 'conditional_confirmation_reservation.json'), 'Canonical study paths changed')
    return frozen


def checked_hashes(values, label):
    require(isinstance(values, dict) and values, f'Missing {label} hash manifest')
    for name, expected in values.items():
        path = Path(name)
        require(path.is_absolute() and path.is_file() and not path.is_symlink()
                and re.fullmatch('[0-9a-f]{64}', expected) and digest(path) == expected,
                f'{label} missing/changed: {path}')
    return values


def check_parent(parent, *, allowed_confirmation=None):
    """Verify an immutable closed archive, allowing later HEAD/additional sources.

    Every historical byte pin is checked. Never calls the old check_freeze or
    source_identity: those would incorrectly require the old *current* HEAD.
    """
    require(set(parent) == {'state_path', 'summary_path', 'audit_path', 'close_path'}, 'Incomplete parent archive inputs')
    paths = {name: Path(value).resolve(strict=True) for name, value in parent.items()}
    state, summary, audit, close = (read_json(paths[name]) for name in ('state_path', 'summary_path', 'audit_path', 'close_path'))
    require(state.get('status') == 'complete' and state.get('phase') == 'selection'
            and state.get('completed_games') == 3000, 'Parent selection must be fully complete (3000)')
    plan_path = Path(state['plan_path']).resolve(strict=True)
    require(plan_path.name == 'plan.json' and plan_path.parent.name == 'selection'
            and paths['state_path'] == plan_path.parent / 'state.json'
            and digest(plan_path) == state['plan_sha256'], 'Changed/noncanonical parent selection plan')
    plan = read_json(plan_path)
    master_path = Path(plan['study_freeze_path']).resolve(strict=True)
    parent_dir = master_path.parent
    require(plan_path.parent == parent_dir / 'selection', 'Noncanonical parent phase')
    for name in ('confirmation', 'confirmation_reservation.json', 'confirmation_started.json'):
        require(not (parent_dir / name).exists() and not (parent_dir / name).is_symlink(),
                'A P confirmation was already created or begun')
    conditional = parent_dir / 'conditional_confirmation_reservation.json'
    if conditional.exists() or conditional.is_symlink():
        require(conditional.is_file() and not conditional.is_symlink(), 'Unsafe shared confirmation reservation')
        require(allowed_confirmation is not None and read_json(conditional) == allowed_confirmation,
                'Independent confirmation reserve already consumed')
    master_sha = digest(master_path)
    require(plan.get('schema_version') == 1 and plan.get('phase') == 'selection' and plan.get('candidate') is None
            and plan['study_freeze_sha256'] == state['study_freeze_sha256'] == master_sha,
            'Unbound parent master/phase')
    master = read_json(master_path)
    require(master.get('schema_version') == 1 and master.get('expected_head') == PARENT_HEAD,
            'Wrong historical P source HEAD')
    require(master['identity']['source']['head'] == PARENT_HEAD
            and state['source_before'] == state['source_after'] == master['identity'], 'Parent original source freeze mismatch')
    source = master['identity']['source']
    checked_hashes(source['files'], 'parent source/protocol')
    require(source['python'] == master['python'] and digest(source['executable']) == source['executable_sha256']
            and str(Path(master['python']).resolve(strict=True)) == source['executable'], 'Parent interpreter changed')
    require(master['protocols'] and all(str(Path(p)) in source['files'] for p in master['protocols']),
            'Parent protocol pins absent')
    checked_hashes(master['frozen_weights'], 'parent weights')
    require(master['identity']['weights'] == master['frozen_weights'], 'Parent protected weight manifest differs')
    require(master['identity']['driver'] == master['driver']
            and digest(master['driver']['path']) == master['driver']['sha256']
            and source['files'].get(master['driver']['path']) == master['driver']['sha256'], 'Parent reviewed driver changed')
    expected_jobs = build_parent_jobs(master['root'], plan_path.parent, master['weights'])
    require(plan['jobs'] == expected_jobs and len(state['jobs']) == 3, 'Incomplete/changed parent selection schedule')
    require(plan['initial_seconds_per_game'] == INITIAL_RATES
            and plan['prior_observed_seconds_per_game'] == {name: [] for name in INITIAL_RATES}
            and plan['deadline_utc'] == '2026-11-03T04:30:00+00:00' and plan['reserve_seconds'] == RESERVE
            and plan['future_confirmation_games'] == dict(combined_panel=8400, direct=600), 'Parent protocol constants changed')
    paths_to_models = {Path(p) for p in master['weights'].values()}
    paths_to_models.update(Path(master['root']) / label[5:] for label in (*PANEL, DIRECT) if label.startswith('self:'))
    paths_to_models.update(Path(master['root']) / f'agents/sherlock/weights/agent_p{i}.pth' for i in (0, 1))
    require({str(p) for p in paths_to_models} == set(master['frozen_weights']), 'Parent model input coverage changed')
    require(digest(master['weights']['baseline']) == SOURCE_SHA, 'Parent baseline is not fixed V14')
    csv_hashes = {}
    for job, record in zip(expected_jobs, state['jobs']):
        require(record['status'] == 'complete' and record['exit_code'] == 0 and record['name'] == job['name']
                and record['out'] == job['out'] and record['timing_class'] == job['timing_class']
                and record['actual_games'] == job['games'] and digest(job['out']) == record['output_sha256'],
                'Incomplete/changed parent CSV receipt')
        validate_output(job['out'], job)
        csv_hashes[job['out']] = record['output_sha256']
    require(summary.get('status') == 'complete' and summary.get('phase') == 'selection'
            and summary.get('completed_games') == 3000 and 'nominee' in summary and summary['nominee'] is None
            and set(summary.get('candidates', {})) == {'P'} and summary['candidates']['P'].get('passed') is False,
            'Parent must be an accepted complete selection with nominee=null')
    require(summary['plan_path'] == str(plan_path) and summary['plan_sha256'] == digest(plan_path)
            and summary['state_sha256'] == digest(paths['state_path']) and summary['study_freeze_sha256'] == master_sha
            and summary['csv_sha256'] == csv_hashes, 'Parent summary binding changed')
    audited = audit.get('results', {}).get('selection', {})
    require(audit.get('verdict') == 'ACCEPTED' and audit.get('phase') == 'selection' and audit.get('failed') == []
            and audited.get('status') == 'complete' and 'nominee' in audited and audited['nominee'] is None
            and audited.get('passed') is False
            and audited.get('completed_games') == 3000 and audited['plan_sha256'] == digest(plan_path)
            and audited['state_sha256'] == digest(paths['state_path']) and audited['study_freeze_sha256'] == master_sha
            and audited['csv_sha256'] == csv_hashes, 'Parent independent audit absent, rejected or unbound')
    evidence = checked_hashes(audit.get('evidence_sha256'), 'parent independent audit evidence')
    required_evidence = {str(plan_path): digest(plan_path), str(master_path): master_sha,
                         str(paths['state_path']): digest(paths['state_path']),
                         str(paths['summary_path']): digest(paths['summary_path']), **csv_hashes}
    require(all(evidence.get(name) == value for name, value in required_evidence.items()),
            'Parent independent audit omits phase/master/summary/CSV evidence')
    require(close == dict(status='closed', phase='selection', head=PARENT_HEAD, master_sha256=master_sha,
                selection_state_sha256=digest(paths['state_path']), selection_summary_sha256=digest(paths['summary_path']),
                independent_audit_sha256=digest(paths['audit_path']), source_unchanged=True, weights_unchanged=True),
            'Parent root freeze-close receipt absent or unbound')
    return dict(paths={k: str(p) for k, p in paths.items()},
                sha256={k: digest(p) for k, p in paths.items()}, master_path=str(master_path), master_sha256=master_sha,
                plan_path=str(plan_path), plan_sha256=digest(plan_path), head=PARENT_HEAD,
                observed_seconds_per_game=observed_receipt_rates(state))


def check_candidate_admission(path, candidate):
    admission = read_json(path)
    require(set(admission) == {'verdict', 'source_sha256', 'candidate', 'components', 'training', 'warnings'}
            and admission.get('verdict') == 'ACCEPTED_PT2' and admission.get('source_sha256') == SOURCE_SHA
            and admission.get('warnings') == [], 'Candidate is not independently admitted PT2')
    require(admission['candidate'] == dict(path=str(Path(candidate).resolve(strict=True)), sha256=digest(candidate)),
            'PT2 candidate path/hash differs from admission')
    components, training = admission['components'], admission['training']
    require(set(components) == {'total', 'replaced', 'ordered_sha256'} and components['total'] == 36
            and components['replaced'] == [18, 19] and len(components['ordered_sha256']) == 36
            and all(re.fullmatch('[0-9a-f]{64}', value) for value in components['ordered_sha256']),
            'PT2 must preserve 36 ordered components replacing only 18/19')
    require(set(training) == {'arms', 'seeds', 'each_games', 'checkpoints', 'accepted_audit'}
            and training['arms'] == ['adapt18', 'adapt19'] and training['seeds'] == [30, 31]
            and training['each_games'] == dict(prefill=120, train=600, val=96)
            and len(training['checkpoints']) == 2, 'PT2 requires the two new complete 600-game arms')
    checked_hashes(training['checkpoints'], 'PT2 end checkpoints')
    audit = training['accepted_audit']
    require(set(audit) == {'path', 'sha256'}, 'Unbound training audit')
    checked_hashes({audit['path']: audit['sha256']}, 'PT2 training audit')
    training_audit = read_json(audit['path'])
    require(training_audit.get('verdict') == 'ACCEPTED_TWO_ARM_BACKUP'
            and training_audit.get('failed') == [] and training_audit.get('warnings') == []
            and set(training_audit.get('arms', {})) == {'adapt18', 'adapt19'}, 'PT2 training audit rejected')
    for arm, seed in [('adapt18', 30), ('adapt19', 31)]:
        record = training_audit['arms'][arm]
        require(record.get('seed') == seed and record.get('train_games') == 600
                and record.get('prefill_games') == 120 and record.get('validation_games') == 96,
                'PT2 training audit incomplete arm or wrong seed')
    evidence = checked_hashes(training_audit.get('evidence_sha256'), 'PT2 training evidence')
    require(all(evidence.get(name) == expected for name, expected in training['checkpoints'].items()),
            'PT2 training audit does not bind both end checkpoints')
    return admission


def estimate_backup(parent):
    archived = check_parent(parent)
    observed = archived['observed_seconds_per_game']
    games = dict(combined_panel=9800, direct=700)
    rates, slowdown = effective_rates(observed)
    projected = project_seconds(games, observed)
    return dict(remaining_games=games, initial_wall_seconds_per_game=dict(INITIAL_RATES),
                effective_wall_seconds_per_game=rates, global_slowdown_factor=slowdown,
                game_seconds_plus_twenty_percent=projected, training_seconds=TRAINING_SECONDS,
                setup_audit_seconds=SETUP_SECONDS, closing_reserve_seconds=RESERVE,
                total_seconds=projected + TRAINING_SECONDS + SETUP_SECONDS + RESERVE)


def admit_backup(parent, *, now, deadline=DEADLINE):
    estimate = estimate_backup(parent)
    require(math.isfinite(now) and now + estimate['total_seconds'] < deadline,
            'No time for all PT2 games +20%, fixed 50-minute training, 20-minute setup and 60-minute reserve')
    return estimate['total_seconds'] - RESERVE


def create_freeze(root, out, weights, *, python, protocols, expected_head, parent, candidate_admission):
    root, out = Path(root).resolve(strict=True), new_path(out)
    require(out.name == 'study_freeze.json' and out.parent.is_dir(), 'Use canonical study_freeze.json in a new study directory')
    candidate_roles(weights)
    require(protocols, 'Bind fixed backup performance protocols')
    archived = check_parent(parent)
    admit(dict(combined_panel=9800, direct=700), archived['observed_seconds_per_game'], now=time.time())
    tools = load_tools(root)
    models = {role: str((root / path).resolve(strict=True)) for role, path in weights.items()}
    admission_path = Path(candidate_admission).resolve(strict=True)
    admission = check_candidate_admission(admission_path, models['PT2'])
    paths = set(map(Path, models.values()))
    paths.update((root / o[5:]).resolve(strict=True) for o in (*PANEL, DIRECT) if o.startswith('self:'))
    active = [(root / f'agents/sherlock/weights/agent_p{i}.pth').resolve(strict=True) for i in (0, 1)]
    paths.update(active)
    paths.update(map(Path, admission['training']['checkpoints']))
    paths.add(Path(admission['training']['accepted_audit']['path']))
    paths.add(admission_path)
    # Keep every previously protected model byte, including P and archival inputs.
    paths.update(map(Path, read_json(archived['master_path'])['frozen_weights']))
    require(all(p.is_file() and not p.is_symlink() for p in paths), 'Missing actual frozen input; random fallback forbidden')
    for path in [Path(models['baseline']), root / DIRECT[5:], *active]:
        require(digest(path) == SOURCE_SHA, f'Wrong fixed V14 source SHA: {path}')
    frozen = dict(schema_version=2, study_name=STUDY_NAME, master_path=str(out), root=str(root),
                  python=str(Path(python).absolute()), expected_head=expected_head, weights=models,
                  protocols=[str(Path(p).resolve(strict=True)) for p in protocols],
                  frozen_weights=tools.early.hashes(paths), parent=archived,
                  candidate_admission=dict(path=str(admission_path), sha256=digest(admission_path)),
                  phase_paths={phase: str(out.parent / phase) for phase in ('selection', 'confirmation')},
                  confirmation_reservation=str(Path(archived['master_path']).parent / 'conditional_confirmation_reservation.json'),
                  driver=dict(path=str(Path(__file__).resolve()), sha256=digest(__file__)))
    frozen['identity'] = identity(frozen, tools)
    require(frozen['identity']['source']['head'] == expected_head, 'Actual HEAD differs from reviewed HEAD')
    with out.open('x') as stream:
        json.dump(frozen, stream, indent=2, allow_nan=False); stream.write('\n')
    check_freeze(out, tools=tools)
    return frozen


def check_selection_summary(path, candidate, receipt):
    summary = read_json(path)
    require(receipt['status'] == 'complete' and receipt['phase'] == 'selection', 'Selection not complete')
    require(summary.get('status') == 'complete' and summary['phase'] == 'selection'
            and summary['nominee'] == candidate and candidate == 'PT2', 'Selection summary has no matching nominee')
    require(summary.get('completed_games') == receipt.get('completed_games') == 1500
            and summary.get('state_sha256') == digest(Path(receipt['plan_path']).parent / 'state.json')
            and set(summary.get('candidates', {})) == {'PT2'}
            and summary['candidates']['PT2'].get('passed') is True
            and summary['candidates']['PT2'].get('gates') == dict(panel_delta=True, solution_delta=True, default=True, direct=True),
            'Selection nominee lacks complete passed gates or matching state')
    require(summary['plan_sha256'] == receipt['plan_sha256']
            and summary['study_freeze_sha256'] == receipt['study_freeze_sha256'], 'Unbound selection plan/freeze')
    expected = {r['out']: r['output_sha256'] for r in receipt['jobs']}
    require(summary['csv_sha256'] == expected and all(digest(p) == sha for p, sha in expected.items()),
            'Selection summary is not bound to every unchanged selection CSV')
    return summary


def check_complete_state(path, freeze_sha):
    state = read_json(path)
    require(state['status'] == 'complete' and state['phase'] == 'selection'
            and state['completed_games'] == 1500, 'Selection receipt incomplete')
    plan_path = Path(state['plan_path']).resolve(strict=True)
    require(digest(plan_path) == state['plan_sha256'] and state['study_freeze_sha256'] == freeze_sha,
            'Selection receipt plan/freeze changed')
    plan, frozen = check_plan(plan_path)
    require(plan['phase'] == 'selection' and plan['study_freeze_sha256'] == freeze_sha, 'Wrong selection phase')
    expected_jobs = build_jobs(frozen['root'], plan_path.parent, frozen['weights'], 'selection')
    require(plan['jobs'] == expected_jobs and len(state['jobs']) == len(expected_jobs), 'Incomplete fixed selection jobs')
    for job, record in zip(expected_jobs, state['jobs']):
        validate_output(job['out'], job)
        require(record['status'] == 'complete' and record['exit_code'] == 0
                and record['name'] == job['name'] and record['out'] == job['out']
                and record['timing_class'] == job['timing_class']
                and record['actual_games'] == job['games'] and digest(job['out']) == record['output_sha256'],
                'Incomplete/corrupt selection output receipt')
    require(state['source_before'] == state['source_after'] == frozen['identity'], 'Selection source freeze mismatch')
    require(Path(path).resolve(strict=True) == Path(frozen['phase_paths']['selection']) / 'state.json',
            'Noncanonical selection receipt')
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


def merge_rates(first, second):
    effective_rates(first); effective_rates(second)
    return {name: [*first[name], *second[name]] for name in INITIAL_RATES}


def confirmation_receipt(freeze_path):
    freeze_path = Path(freeze_path).resolve(strict=True)
    return dict(study_name=STUDY_NAME, master_path=str(freeze_path), master_sha256=digest(freeze_path),
                phase='confirmation', plan_path=str(freeze_path.parent / 'confirmation/plan.json'))


def reserve_confirmation(freeze_path, frozen):
    target = new_path(frozen['confirmation_reservation'])
    require(target.parent == Path(frozen['parent']['master_path']).parent, 'Noncanonical shared confirmation reserve')
    # O_EXCL persists before any directory, command, model load or game launch.
    # Never removed on exception, signal, failed child, or zero persisted games.
    with target.open('x') as stream:
        json.dump(confirmation_receipt(freeze_path), stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    directory = os.open(target.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def prepare_phase(freeze_path, out, phase, *, candidate=None,
                  selection_state=None, selection_summary=None):
    freeze_path, out = Path(freeze_path).resolve(strict=True), new_path(out)
    frozen = check_freeze(freeze_path)
    jobs = build_jobs(frozen['root'], out, frozen['weights'], phase, candidate=candidate)
    require(str(out) == frozen['phase_paths'][phase], 'Use the fixed canonical phase directory')
    plan = dict(schema_version=2, study_name=STUDY_NAME, phase=phase, candidate=candidate,
                study_freeze_path=str(freeze_path), study_freeze_sha256=digest(freeze_path),
                initial_seconds_per_game=dict(INITIAL_RATES), prior_observed_seconds_per_game={name: list(values) for name, values
                    in frozen['parent']['observed_seconds_per_game'].items()},
                deadline_utc='2026-11-03T04:30:00+00:00', reserve_seconds=RESERVE, setup_audit_seconds=SETUP_SECONDS,
                future_confirmation_games=dict(combined_panel=8400, direct=600) if phase == 'selection'
                    else dict(combined_panel=0, direct=0),
                jobs=jobs)
    if phase == 'confirmation':
        require(selection_state and selection_summary, 'Confirmation requires complete selection state and pinned summary')
        receipt = check_complete_state(selection_state, plan['study_freeze_sha256'])
        check_selection_summary(selection_summary, candidate, receipt)
        combined_prior = merge_rates(frozen['parent']['observed_seconds_per_game'], observed_receipt_rates(receipt))
        plan.update(prior_observed_seconds_per_game=combined_prior,
                    selection_state_path=str(Path(selection_state).resolve(strict=True)),
                    selection_state_sha256=digest(selection_state),
                    selection_summary_path=str(Path(selection_summary).resolve(strict=True)),
                    selection_summary_sha256=digest(selection_summary))
    else:
        require(not selection_state and not selection_summary, 'Selection cannot consume an outcome summary')
    admit({name: sum(j['games'] for j in jobs if j['timing_class'] == name)
           + plan['future_confirmation_games'][name] for name in INITIAL_RATES},
          plan['prior_observed_seconds_per_game'], now=time.time())
    if phase == 'confirmation':
        reserve_confirmation(freeze_path, frozen)
        plan['confirmation_reservation_sha256'] = digest(frozen['confirmation_reservation'])
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'plan.json').open('x') as stream:
        json.dump(plan, stream, indent=2, allow_nan=False)
        stream.write('\n')
    return plan


def check_plan(path, tools=None):
    path = Path(path).resolve(strict=True)
    plan = read_json(path)
    require(path.name == 'plan.json' and plan['schema_version'] == 2
            and plan['study_name'] == STUDY_NAME, 'Invalid PT2 phase plan')
    frozen = check_freeze(plan['study_freeze_path'], expected_sha=plan['study_freeze_sha256'], tools=tools)
    require(str(path.parent) == frozen['phase_paths'][plan['phase']], 'Noncanonical phase plan path')
    require(plan['jobs'] == build_jobs(frozen['root'], path.parent, frozen['weights'], plan['phase'], candidate=plan['candidate']),
            'Fixed phase commands/paths/opponents/counts changed')
    require(plan['deadline_utc'] == '2026-11-03T04:30:00+00:00' and plan['reserve_seconds'] == RESERVE
            and plan['setup_audit_seconds'] == SETUP_SECONDS
            and plan['future_confirmation_games'] == (dict(combined_panel=8400, direct=600) if plan['phase'] == 'selection'
                                                        else dict(combined_panel=0, direct=0))
            and plan['initial_seconds_per_game'] == INITIAL_RATES,
            'Deadline/reserve/future-work binding changed')
    expected_prior = frozen['parent']['observed_seconds_per_game']
    if plan['phase'] == 'confirmation':
        require(digest(plan['selection_state_path']) == plan['selection_state_sha256']
                and digest(plan['selection_summary_path']) == plan['selection_summary_sha256'], 'Selection state/summary changed')
        receipt = check_complete_state(plan['selection_state_path'], plan['study_freeze_sha256'])
        check_selection_summary(plan['selection_summary_path'], plan['candidate'], receipt)
        expected_prior = merge_rates(expected_prior, observed_receipt_rates(receipt))
        require(read_json(frozen['confirmation_reservation']) == confirmation_receipt(plan['study_freeze_path'])
                and digest(frozen['confirmation_reservation']) == plan['confirmation_reservation_sha256'],
                'Confirmation reservation changed')
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
    require(not re.search(r'(?:-m\s+scripts\.|scripts/)(?:targeting_adapt(?:_backup)?)(?:\s|\.py\b)|train_targeting\.py', text),
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
    state = dict(schema_version=2, study_name=STUDY_NAME, phase=plan['phase'], status='running', started_at=stamp(),
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
                                          closing_reserve_seconds=RESERVE, setup_audit_seconds=SETUP_SECONDS, checked_at=stamp())
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
    freeze = sub.add_parser('freeze', help='Pin admitted PT2 and closed parent; never starts games')
    for name in ('root', 'out', 'python', 'candidate-admission', 'parent-state', 'parent-summary', 'parent-audit', 'parent-close'):
        freeze.add_argument('--' + name, type=Path, required=True)
    freeze.add_argument('--expected-head', required=True)
    freeze.add_argument('--protocol', type=Path, action='append', required=True)
    freeze.add_argument('--baseline', required=True)
    freeze.add_argument('--pt2', required=True)
    prepare = sub.add_parser('prepare', help='Write the single canonical phase plan; never starts games')
    prepare.add_argument('--freeze', type=Path, required=True)
    prepare.add_argument('--out', type=Path, required=True)
    prepare.add_argument('--phase', choices=('selection', 'confirmation'), required=True)
    prepare.add_argument('--candidate', choices=('PT2',))
    prepare.add_argument('--selection-state', type=Path)
    prepare.add_argument('--selection-summary', type=Path)
    run = sub.add_parser('run', help='Explicit execution with owned process groups')
    run.add_argument('--plan', type=Path, required=True)
    run.add_argument('--start', action='store_true', required=True)
    args = parser.parse_args()
    if args.command == 'freeze':
        create_freeze(args.root, args.out, dict(baseline=args.baseline, PT2=args.pt2),
            python=args.python, protocols=args.protocol, expected_head=args.expected_head,
            candidate_admission=args.candidate_admission,
            parent=dict(state_path=str(args.parent_state), summary_path=str(args.parent_summary),
                        audit_path=str(args.parent_audit), close_path=str(args.parent_close)))
    elif args.command == 'prepare':
        prepare_phase(args.freeze, args.out, args.phase, candidate=args.candidate,
                      selection_state=args.selection_state, selection_summary=args.selection_summary)
    elif args.command == 'run':
        result = run_phase(args.plan, start=args.start)
        print(json.dumps(dict(status=result['status'], completed_games=result['completed_games'])))


if __name__ == '__main__':
    main()
