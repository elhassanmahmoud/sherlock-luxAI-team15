"""One-shot prospective validation of the fixed diagnostic REPLACE36 artifact.

Independent outcome-motivated follow-up, never compact nomination/confirmation.
No training, automatic restart, partial result reuse, or automatic promotion.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

from scripts import ensemble_diversity_compare as C
from scripts import ensemble_diversity_eval_supervisor as S

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'replacement20261108'
ANALYSIS = Path('experiments/analysis/replacement_validation_20261108')
PROTOCOL = 'docs/superpowers/plans/2026-11-08-replacement-validation.md'
ORIGIN = ANALYSIS / 'origin.json'
ORIGIN_SHA256 = 'e63c06d87745120b7c7e46d4fc8dec264e178377c548cd0cd23a6c3dda85d02e'
ROLE_PATHS = {role: C.ROLE_PATHS[role] for role in ('V14', 'REPLACE36')}
MODEL_HASHES = {'V14': S.SOURCE_SHA,
    'REPLACE36': '5ce350a86d4ed90b319af298e64b98e7f725ed253f5df89d504e98a73a54db6b'}
PRIOR = 'experiments/analysis/ensemble_diversity_20261108_compact/selection/summary.json'
require = C.require


def origin_evidence(root):
    """Bind historical evidence as bytes, without requiring historical source=now."""
    path = S.repo_path(root, str(ORIGIN))
    require(C.digest(path) == ORIGIN_SHA256, 'Fixed origin hash changed')
    origin = C._load_json(path)
    require(origin.get('kind') == 'outcome_motivated_separate_validation'
        and origin.get('prior_selection_nominee', 'missing') is None
        and origin.get('prior_diagnostic_role') == 'REPLACE36'
        and origin.get('not_compact_protocol_confirmation') is True
        and origin.get('new_games_cap') == 3200 and origin.get('no_successor_or_topup') is True,
        'Wrong independent validation origin')
    require(origin.get('fixed_models') == {r: dict(path=p, sha256=MODEL_HASHES[r])
        for r, p in ROLE_PATHS.items()}, 'Origin fixed models differ')
    historical = origin.get('prior_files_sha256')
    require(isinstance(historical, dict) and PRIOR in historical, 'Incomplete archived discovery evidence')
    paths = [path]
    for relative, sha in historical.items():
        old = S.repo_path(root, relative)
        require(C._hex(sha) and C.digest(old) == sha, 'Archived discovery hash changed')
        paths.append(old)
    discovery = C._load_json(S.repo_path(root, PRIOR))
    require(discovery.get('status') == 'complete' and discovery.get('nominee', 'missing') is None
        and discovery.get('results', {}).get('REPLACE36', {}).get('nominable') is False,
        'Compact study must remain closed without a nominee')
    return paths


def validate_plan(plan, root):
    """Exact old job wire schema, with this independently fixed role/cohort matrix."""
    root = Path(root).resolve()
    require(plan.get('profile') == PROFILE and plan.get('protocol') == PROTOCOL
        and plan.get('phase') == 'confirmation' and plan.get('nominee', 'missing') is None,
        'Wrong validation profile/protocol/phase/nominee')
    require(plan.get('roles') == ROLE_PATHS, 'Wrong fixed role paths')
    require(type(plan.get('max_simultaneous_model_processes')) is int
        and plan['max_simultaneous_model_processes'] == 2, 'Wrong process limit')
    require(plan.get('opponent_sha256') == C.OPPONENT_SHA256, 'Wrong pinned opponent hashes')
    for relative, sha in C.OPPONENT_SHA256.items():
        require(C.digest(S.repo_path(root, relative)) == sha, 'Opponent hash changed')
    expected = {f'{role}_panel_{i}': (role, 'panel', opponent)
        for role in ROLE_PATHS for i, opponent in enumerate(C.OPPONENTS)}
    expected['REPLACE36_direct'] = ('REPLACE36', 'direct', C.V14_LABEL)
    raw = plan.get('jobs')
    require(isinstance(raw, list) and len(raw) == 15, 'Missing/extra jobs')
    fields = {'name', 'role', 'kind', 'weights', 'opponent', 'seed_list', 'expected_games', 'workers'}
    seen, jobs = set(), []
    for job in raw:
        require(isinstance(job, dict) and set(job) == fields, 'Unexpected job schema')
        name = job['name']
        require(isinstance(name, str) and name in expected and name not in seen, 'Unexpected/duplicate job')
        seen.add(name)
        role, kind, opponent = expected[name]
        require((job['role'], job['kind'], job['opponent']) == (role, kind, opponent)
            and job['weights'] == ROLE_PATHS[role], 'Job differs from fixed schedule')
        require(type(job['workers']) is int and job['workers'] == 1, 'Each job must use one worker')
        first, maps = (2100000, 200) if kind == 'direct' else (2000000, 100)
        require(type(job['expected_games']) is int and job['expected_games'] == 2 * maps, 'Wrong job game count')
        value = job['seed_list']
        require(isinstance(value, str), 'Invalid seed path')
        path = S.repo_path(root, value)
        require(path.is_relative_to(root / ANALYSIS), 'Invalid seed path')
        seeds = C._seeds(C._load_json(path))
        require(seeds == list(range(first, first + maps)), 'Wrong fixed seed block')
        jobs.append({**job, 'seeds': seeds})
    require(type(plan.get('total_games')) is int and plan['total_games'] == 3200
        and sum(j['expected_games'] for j in jobs) == 3200, 'Wrong total game count')
    return jobs


def build_state(jobs, admission, out, python, expected_head, *, usage_file,
                max_used_percent=65, stop_file=S.STOP_FILE):
    """Adapt only the admission boundary; execution stays in the shared supervisor."""
    S.validate_quota_ceiling(max_used_percent)
    h = S.helpers()
    require(Path.cwd().resolve() == ROOT, 'Use the intended checkout')
    require(isinstance(expected_head, str) and re.fullmatch('[0-9a-f]{40}', expected_head), 'Expected HEAD must be full')
    jobs_path, admission_path, out = map(h.safe_path, (jobs, admission, out))
    base = h.safe_path(ROOT / ANALYSIS)
    require(out != base and out.is_relative_to(base) and not out.exists(), 'Use a fresh study analysis output directory')
    reservation = h.safe_path(base / 'validation_launch.json')
    require(not reservation.exists(), 'Validation already launched; no automatic restart')
    python = Path(python).absolute()
    require(python.is_file() and os.access(python, os.X_OK), 'Python unavailable')
    paths = [jobs_path, admission_path, *origin_evidence(ROOT)]
    plan = C._load_json(jobs_path)
    job_list = validate_plan(plan, ROOT)
    admitted = C._load_json(admission_path)
    require(admitted.get('status') == 'admitted', 'Models have not been admitted')
    models = {}
    for role, relative in ROLE_PATHS.items():
        path = S.repo_path(ROOT, relative)
        value = C.digest(path)
        require(value == MODEL_HASHES[role]
            and admitted.get('roles', {}).get(role) == dict(path=relative, sha256=value),
            f'Admitted fixed model path/hash differs: {role}')
        models[role] = value
        paths.append(path)
    paths.extend(S.repo_path(ROOT, relative) for relative in plan['opponent_sha256'])
    paths.extend(S.repo_path(ROOT, job['seed_list']) for job in job_list)
    plans = [str(S.repo_path(ROOT, PROTOCOL))]
    paths.extend(map(Path, plans))
    source = h.source_identity(ROOT, python, plans)
    require(source['head'] == expected_head, 'Expected HEAD changed')
    protected = h.hashes([S.repo_path(ROOT, f'agents/sherlock/weights/agent_p{i}.pth') for i in (0, 1)])
    require(set(protected.values()) == {MODEL_HASHES['V14']}, 'Protected V14 weights differ')
    protected.update(h.hashes([S.repo_path(ROOT, 'Gruppe15.zip')]))
    require(all(out != path and out not in path.parents for path in paths), 'An input overlaps output')
    provenance = dict(profile=PROFILE, model_sha256=models, source_identity=source,
        origin_sha256=ORIGIN_SHA256, study_kind='outcome_motivated_separate_validation')
    return dict(schema_version=1, profile=PROFILE, root=str(ROOT), out=str(out), python=str(python),
        phase='confirmation', nominee=None, jobs_path=str(jobs_path), expected_head=expected_head,
        source=source, plans=plans, protected=protected, inputs=h.hashes(paths),
        admission_path=str(admission_path), admission_sha256=C.digest(admission_path),
        origin_sha256=ORIGIN_SHA256, model_sha256=models, opponent_sha256=plan['opponent_sha256'],
        provenance=provenance, usage_file=str(h.safe_path(usage_file)), max_used_percent=max_used_percent,
        stop_file=str(Path(stop_file).absolute()), reservation=str(reservation), expected_games=3200,
        job_plan={job['name']: job for job in job_list}, queue=[job['name'] for job in job_list],
        jobs={}, active=[], receipts={}, status='prepared', owner_pid=os.getpid())


def validation_checks(reference, candidate, direct):
    from scripts.league_gates import confirm_checks
    from scripts.compare_report import compare_results
    reference = C._checked_frame(reference, C.OPPONENTS, 2000000, 100)
    candidate = C._checked_frame(candidate, C.OPPONENTS, 2000000, 100)
    direct = C._checked_frame(direct, (C.V14_LABEL,), 2100000, 200)
    stats = confirm_checks(reference, candidate, direct, direct_opponent=C.V14_LABEL,
        panel=C.LOCAL_SIX, min_delta=.01, label='Local six score')
    result = C._report_stats(reference, candidate, direct, stats)
    for comparison in compare_results(candidate, reference):
        opponent = comparison['opponent']
        result['opponent_outcomes'][opponent] = C._score_stats(comparison,
            candidate[candidate['opponent'] == opponent], reference[reference['opponent'] == opponent])
    checks = {**stats['checks'], **C._additional_checks(result)}
    return dict(**result, checks=checks, passed=all(checks.values()), nominable=False)


def _receipt(receipt, job, csv_path, root, plan, frozen):
    expected = dict(profile=PROFILE, status='complete', returncode=0, job_name=job['name'],
        phase='confirmation', role=job['role'], opponent=job['opponent'], weights=job['weights'],
        model_sha256=MODEL_HASHES[job['role']], seed_list_sha256=C.digest(root / job['seed_list']),
        csv_sha256=C.digest(csv_path), rows=job['expected_games'],
        source_identity=frozen['source_identity'], opponent_sha256=plan['opponent_sha256'])
    require(isinstance(receipt, dict) and all(receipt.get(k) == v for k, v in expected.items())
        and type(receipt.get('returncode')) is int and type(receipt.get('rows')) is int,
        f'Invalid/unbound execution receipt: {job["name"]}')
    command = [frozen['source_identity']['python'], '-B', '-m', 'scripts.par_eval',
        '--weights', str(root / job['weights']), '--seed-list', str(root / job['seed_list']),
        '--workers', '1', '--opponents', job['opponent'], '--out', str(csv_path)]
    require(receipt.get('command') == command, f'Unexpected execution command: {job["name"]}')
    return expected['csv_sha256']


def analyze(jobs_json, result_dir, *, root=ROOT, provenance=None):
    """All state/receipt/row evidence must validate before any statistics run."""
    import pandas as pd
    h = S.helpers()
    root = h.safe_path(root)
    result_dir = h.safe_path(result_dir)
    require(result_dir != root / ANALYSIS and result_dir.is_relative_to(root / ANALYSIS), 'Wrong validation output root')
    jobs_json = h.safe_path(jobs_json)
    plan = C._load_json(jobs_json)
    jobs = validate_plan(plan, root)
    origin_paths = origin_evidence(root)
    require(provenance is not None and h.safe_path(provenance) == result_dir / 'provenance.json', 'Frozen provenance is required')
    frozen = C._load_json(provenance)
    state = C._load_json(result_dir / 'state.json')
    reservation = root / ANALYSIS / 'validation_launch.json'
    launch = C._load_json(reservation)
    require(state.get('profile') == PROFILE and frozen.get('profile') == PROFILE
        and launch.get('profile') == PROFILE and state.get('phase') == 'confirmation'
        and launch.get('phase') == 'confirmation' and state.get('nominee', 'missing') is None,
        'Validation profile/phase differs')
    require(state.get('status') == 'complete' and state.get('completed_games') == 3200
        and state.get('expected_games') == 3200 and not state.get('queue') and not state.get('active'),
        'Validation state is incomplete')
    require(state.get('root') == str(root) and state.get('out') == str(result_dir)
        and launch.get('out') == str(result_dir) and state.get('jobs_path') == str(jobs_json)
        and launch.get('jobs_path') == str(jobs_json) and state.get('reservation') == str(reservation),
        'Validation paths differ')
    require(state.get('origin_sha256') == ORIGIN_SHA256 and frozen.get('origin_sha256') == ORIGIN_SHA256
        and frozen.get('study_kind') == 'outcome_motivated_separate_validation', 'Validation origin differs')
    require(state.get('model_sha256') == MODEL_HASHES and frozen.get('model_sha256') == MODEL_HASHES,
        'Fixed model hashes differ')
    source = frozen.get('source_identity')
    require(isinstance(source, dict) and C._hex(source.get('head'), 40)
        and bool(source.get('files')) and state.get('source') == source
        and launch.get('source_identity') == source and state.get('expected_head') == source['head']
        and source.get('python') == state.get('python') and state.get('provenance') == frozen,
        'Frozen source/HEAD differs')
    protected = {str(root / f'agents/sherlock/weights/agent_p{i}.pth'): MODEL_HASHES['V14'] for i in (0, 1)}
    protected[str(root / 'Gruppe15.zip')] = C.digest(S.repo_path(root, 'Gruppe15.zip'))
    require(state.get('protected') == protected, 'Incomplete/changed protected V14/ZIP hashes')
    S.check_inputs(state)
    bound = [jobs_json, Path(provenance), reservation, *origin_paths,
        *(S.repo_path(root, p) for p in ROLE_PATHS.values()),
        *(S.repo_path(root, p) for p in plan['opponent_sha256']),
        *(S.repo_path(root, j['seed_list']) for j in jobs), S.repo_path(root, PROTOCOL)]
    admission = h.safe_path(state['admission_path'])
    admitted = C._load_json(admission)
    require(admitted.get('status') == 'admitted' and admitted.get('roles') == {
        r: dict(path=p, sha256=MODEL_HASHES[r]) for r, p in ROLE_PATHS.items()}
        and state['admission_sha256'] == C.digest(admission), 'Admitted models differ')
    bound.append(admission)
    require(all(state['inputs'].get(str(p)) == C.digest(p) for p in bound), 'Missing bound frozen inputs')
    names = {j['name'] for j in jobs}
    require(state.get('job_plan') == {j['name']: j for j in jobs}
        and set(state.get('jobs', {})) == names and set(state.get('receipts', {})) == names,
        'Incomplete fixed state jobs/receipts')
    require({p.stem for p in result_dir.glob('*.csv')} == names, 'Missing/extra result CSV jobs')
    require({p.stem for p in (result_dir / 'receipts').glob('*.json')} == names, 'Missing/extra execution receipts')
    rows, csv_hashes, receipt_hashes = {}, {}, {}
    for job in jobs:
        name = job['name']
        csv_path = h.safe_path(result_dir / f'{name}.csv')
        receipt_path = h.safe_path(result_dir / 'receipts' / f'{name}.json')
        receipt = C._load_json(receipt_path)
        csv_hashes[name] = _receipt(receipt, job, csv_path, root, plan, frozen)
        receipt_hashes[name] = C.digest(receipt_path)
        require(state['receipts'][name] == dict(path=str(receipt_path), sha256=receipt_hashes[name],
            rows=job['expected_games']) and state['jobs'][name].get('returncode') == 0
            and state['jobs'][name].get('argv') == receipt['command'], 'State receipt/command differs')
        require(all(state['inputs'].get(str(p)) == C.digest(p) for p in (csv_path, receipt_path)),
            'CSV/receipt is not bound to state')
        rows[name] = C.validate_job_csv(csv_path, job, job['seeds'])
    panels = {role: pd.DataFrame([row for j in jobs if j['role'] == role and j['kind'] == 'panel'
        for row in rows[j['name']]]) for role in ROLE_PATHS}
    result = validation_checks(panels['V14'], panels['REPLACE36'], pd.DataFrame(rows['REPLACE36_direct']))
    return dict(schema_version=1, status='complete', profile=PROFILE, phase='confirmation',
        study_kind='outcome_motivated_separate_validation', jobs=15, games=3200, nominee=None,
        passed=result['passed'], results={'REPLACE36': result},
        score_definition='Spielscore = (Siege + 0.5 * Remis) / Spiele; strict_winrate counts only wins.',
        interpretation='Separate prospectively registered outcome-motivated fixed-artifact validation. '
            'Fresh data only; whole-map paired bootstrap, 5000 PCG64 samples, seed 0, unadjusted 95% intervals. '
            'Repeated project-wide exploration provides no familywise 95% guarantee. '
            'Passing never automatically promotes; independent audit and technical release checks remain required. '
            'No successor, top-up or automatic further study after failure/inconclusive outcome.',
        input_sha256=dict(plan=C.digest(jobs_json), origin=ORIGIN_SHA256, provenance=C.digest(provenance),
            state=C.digest(result_dir / 'state.json'), reservation=C.digest(reservation),
            csv=csv_hashes, receipts=receipt_hashes))


def run_supervisor(jobs, admission, out, python, expected_head, *, usage_file,
                   max_used_percent=65, stop_file=S.STOP_FILE):
    """Shared resource lock/guard/queue/ownership/termination, isolated admission."""
    S.validate_quota_ceiling(max_used_percent)
    h = S.helpers()
    if Path(stop_file).exists():
        raise S.StopRequested('Existing STOP inhibits start')
    handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    wake, state = None, None
    try:
        for sig in handlers:
            signal.signal(sig, lambda *_: S.request_stop(stop_file))
        with h.compute_lock(ROOT):
            h.check_model_processes({})
            state = build_state(jobs, admission, out, python, expected_head,
                usage_file=usage_file, max_used_percent=max_used_percent, stop_file=stop_file)
            S.guard(state, {})
            target = h.safe_path(state['out'])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.mkdir()
            (target / 'receipts').mkdir()
            with (target / 'controller.log').open('x', buffering=1) as log, redirect_stdout(log), redirect_stderr(log):
                try:
                    S.reserve_launch(state)
                    S.guard(state, {})
                    command = ['/usr/bin/caffeinate', '-i', '-w', str(os.getpid())]
                    wake = subprocess.Popen(command, start_new_session=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    state['wake'] = dict(pid=wake.pid, pgid=wake.pid, argv=command, owner_pid=os.getpid())
                    h.save_state(state)
                    return S.run_queue(state)
                except BaseException as exc:
                    state.update(status='stopped' if isinstance(exc, S.StopRequested) else 'failed',
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    start = commands.add_parser('start')
    for name in ('jobs', 'admission', 'out', 'python', 'expected-head', 'usage-file'):
        start.add_argument('--' + name, required=True)
    start.add_argument('--max-used-percent', type=float, default=65)
    commands.add_parser('stop')
    analysis = commands.add_parser('analyze')
    for name in ('jobs', 'results', 'provenance'):
        analysis.add_argument('--' + name, required=True)
    analysis.add_argument('--root', default=str(ROOT))
    analysis.add_argument('--out')
    args = parser.parse_args(argv)
    try:
        if args.command == 'stop':
            S.request_stop()
            return 0
        if args.command == 'start':
            state = run_supervisor(args.jobs, args.admission, args.out, args.python, args.expected_head,
                usage_file=args.usage_file, max_used_percent=args.max_used_percent)
            print(json.dumps(dict(status=state['status'], out=state['out'], games=state['completed_games'])))
        else:
            report = analyze(args.jobs, args.results, root=args.root, provenance=args.provenance)
            content = json.dumps(report, indent=2, allow_nan=False) + '\n'
            if args.out:
                with S.helpers().safe_path(args.out).open('x') as stream:
                    stream.write(content)
            else:
                print(content, end='')
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
