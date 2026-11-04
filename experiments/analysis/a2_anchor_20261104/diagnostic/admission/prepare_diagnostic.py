#!/usr/bin/env python3
"""Admit/freeze the fixed A2-anchor diagnostic; never run models or games.

Run only after the independent learning auditor has accepted all four arms.
Stdlib only. Existing candidate/output/preparation artifacts are never overwritten.
A failed partial publication requires explicit review, never an automatic retry.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
TMP = Path('/tmp/sherlock-a2-anchor-20261104')
SOURCE = '09c69349afc020a7b2418c249657a5698c472964'
A2_SHA = '1baec85605e2b7aaad8c0beaa416d0489d2b9faa1362a9b361bbb63f04cc14bd'
V14_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
OUT = ROOT / 'experiments/analysis/a2_anchor_20261104/diagnostic'
CANDIDATES = ROOT / 'experiments/candidates/a2_anchor_20261104'
RUNS = ROOT / 'experiments/runs/20261104_a2_anchor'
OLD = ROOT / 'experiments/analysis/action_student_20261104/diagnostic'
ROLES = ('V14', 'A2', 'CONTROL25', 'CONTROL26', 'ANCHOR25', 'ANCHOR26')
ARMS = ('CONTROL25', 'CONTROL26', 'ANCHOR25', 'ANCHOR26')
SINGLE_OLD = ('A2', 'S30', 'CONTROL27', 'CONTROL28', 'SAP027', 'SAP028')
OPPONENTS = ('solution92', 'default', 'self:experiments/releases/20261101_v13_neb/agent_p0.pth')
DIRECT_OPPONENT = 'self:agents/sherlock/weights/agent_p0.pth'
DEADLINE = '2026-11-04T22:00:00Z'
SPEC = ROOT / 'docs/superpowers/specs/2026-11-04-a2-teacher-anchor.md'
EVIDENCE = ('updates.jsonl', 'samples.u32', 'summary.json', 'prefill_replay.json')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    path = Path(path)
    before = path.stat()
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            h.update(block)
    after = path.stat()
    require((before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), f'Changed while hashing: {path}')
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def stamp(value):
    result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None, 'Timestamp must include timezone')
    return result


def exclusive_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        handle.write(json.dumps(data, indent=2) + '\n')
        handle.flush()
        os.fsync(handle.fileno())


def exclusive_copy(source, target, expected):
    require(sha(source) == expected, f'Source changed before copy: {source}')
    target.parent.mkdir(parents=True, exist_ok=True)
    with Path(source).open('rb') as src, target.open('xb') as dest:
        shutil.copyfileobj(src, dest, 4 * 1024 * 1024)
        dest.flush()
        os.fsync(dest.fileno())
    require(sha(source) == sha(target) == expected, f'Copy/source mismatch: {target}')


def head():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def assert_dead_pid(pid, label, group=False):
    require(type(pid) is int and pid > 1, f'Invalid recorded PID: {label}')
    try:
        (os.killpg if group else os.kill)(pid, 0)
    except ProcessLookupError:
        return
    raise ValueError(f'Recorded process still exists or PID was reused: {label} {pid}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-ready', action='store_true', help='Explicit four-arm completion handoff')
    parser.add_argument('--account-used-percent', type=float, required=True)
    parser.add_argument('--battery-percent', type=float, required=True)
    args = parser.parse_args()
    require(args.data_ready, 'Explicit --data-ready required; no artifacts written')
    require(math.isfinite(args.account_used_percent) and 0 <= args.account_used_percent < 65,
            'No new phase at 65% account usage; preserve at least 30%')
    require(math.isfinite(args.battery_percent) and 35 <= args.battery_percent <= 100,
            'No new heavy phase below 35% battery')
    require(head() == SOURCE, 'Source HEAD changed; never update the active freeze')
    admission_path = TMP / 'training_admission.json'
    admission = read(admission_path)
    require(admission['status'] == 'admitted' and admission['source_commit'] == SOURCE,
            'Wrong training admission/source')
    require(admission['seeds'] == [25, 26] and admission['arms'] == ['control', 'anchor'] and
            admission['games_per_arm'] == 232 and admission['updates_per_arm'] == 24000 and
            admission['total_expected_games'] == 928 and admission['max_workers'] == 2 and
            admission['model_job_end_limit_utc'] == DEADLINE, 'Training admission budget differs')
    inputs = {}

    def pin(path, expected=None):
        path = Path(path)
        require(path.is_absolute() and path.is_file(), f'Missing absolute input: {path}')
        digest = sha(path)
        require(expected is None or digest == expected, f'Input pin differs: {path}')
        require(str(path) not in inputs or inputs[str(path)] == digest, f'Conflicting pin: {path}')
        inputs[str(path)] = digest
        return digest

    pin(admission_path)
    for rel, digest in admission['source_sha256'].items():
        require(sha(ROOT / rel) == digest, f'Training source differs: {rel}')
    for path, digest in admission['protected_sha256'].items():
        pin(Path(path), digest)
    # Freeze every tracked Python file, not just the imported trainer/agent subset.
    tracked = subprocess.check_output(['git', 'ls-files', '-z', '*.py'], cwd=ROOT).decode().split('\0')
    source_paths = {ROOT / rel for rel in tracked if rel}
    for directory in ('agents', 'scripts', 'lux'):
        source_paths.update((ROOT / directory).rglob('*.py'))
    source_hashes = {str(path.relative_to(ROOT)): sha(path) for path in sorted(source_paths)}
    require(set(admission['source_sha256']).issubset(source_hashes), 'Training source inventory lost entries')
    changed = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD', '--', '*.py'], cwd=ROOT, text=True)
    require(not changed.strip(), 'Tracked Python source differs from frozen HEAD')
    for rel in ('main.py', 'Paths.csv', 'pyproject.toml', 'requirements.txt'):
        if (ROOT / rel).is_file():
            pin(ROOT / rel)
    pin(SPEC)
    for name in ('prepare_diagnostic.py', 'run_guarded.py', 'run_diagnostic.py', 'audit_results.py',
                 'learning_completion_auditor.py', 'crosscheck_diagnostic.py'):
        pin(TMP / name)
    learning_path = TMP / 'learning_completion_audit.json'
    pin(learning_path)
    learning = read(learning_path)
    require(learning.get('schema_version') == 1 and learning.get('status') == 'passed' and
            learning.get('independent') is True and learning.get('source_commit') == SOURCE and
            learning.get('training_admission_sha256') == inputs[str(admission_path)],
            'Independent learning completion audit missing or invalid')
    require(Path(learning.get('auditor_script', '')).resolve() == (TMP / 'learning_completion_auditor.py').resolve() and
            learning.get('auditor_sha256') == inputs[str(TMP / 'learning_completion_auditor.py')],
            'Independent learning auditor identity/hash differs')
    require(set(learning['arms']) == set(ARMS) and
            learning.get('pair_prefill_equal') == {'25': True, '26': True}, 'Incomplete four-arm/pair audit')
    # Optional independent auxiliary evidence is frozen too, when supplied.
    for path, digest in learning.get('evidence_sha256', {}).items():
        pin(Path(path), digest)
    inventory_path = TMP / 'seed_inventory/seed_freshness.json'
    pin(inventory_path)
    inventory = read(inventory_path)
    require(inventory['schema'] == 'local_seed_freshness_v1' and
            inventory['verdict'] == 'NO_OBSERVED_CONSUMPTION_OR_JSON_OVERLAP_WITH_REPORTED_SCHEMA_LIMITS' and
            inventory['ranges_inclusive'] == {'anchor_diagnostic': [867000, 867019], 'anchor_direct': [867100, 867119]} and
            all(not inventory[k] for k in ('consumption_overlaps', 'json_seed_or_numeric_mentions',
                'json_interval_overlaps', 'json_string_mentions', 'errors', 'mutations')),
            'Local seed inventory has unresolved consumption/mentions/errors')
    pin(TMP / 'seed_inventory/short.md')
    # Existing study only: this historical local inventory has documented gaps.
    # No external/global freshness or absence of undocumented trials is claimed.
    role_paths = {'V14': 'agents/sherlock/weights/agent_p0.pth',
                  'A2': 'experiments/candidates/action_student_20261104/A2.pth'}
    role_manifest = {
        'V14': {'path': role_paths['V14'], 'sha256': pin(ROOT / role_paths['V14'], V14_SHA), 'original': True},
        'A2': {'path': role_paths['A2'], 'sha256': pin(ROOT / role_paths['A2'], A2_SHA), 'original': True},
    }
    pin(ROOT / 'experiments/releases/20261101_v13_neb/agent_p0.pth')
    copies = []
    for seed in (25, 26):
        prepared = RUNS / f'seed{seed}'
        manifest_path = prepared / 'manifest.json'
        manifest_sha = pin(manifest_path)
        manifest = read(manifest_path)
        require(manifest['schema_version'] == 1 and manifest['study'] == 'a2_teacher_anchor_20261104' and
                manifest['run_seed'] == seed and manifest['prepared'] == str(prepared) and
                manifest['student_sha256'] == A2_SHA and manifest['expected_updates'] == 24000 and
                manifest['batch_size'] == 256 and manifest['sampler_seed'] == 20261104 + seed,
                f'Unexpected outer manifest seed{seed}')
        pin(Path(manifest['student']), A2_SHA)
        require(Path(admission['python']).resolve() == Path(manifest['pins']['interpreter']),
                f'Prepared interpreter differs: seed{seed}')
        contract = manifest['dataset_contract']
        require(contract['train_rows'] == 356415 and contract['excluded_rows'] == 68687 and
                contract['scale'] == 1.4293522257922757, 'Dataset contract differs')
        for dataset in contract['datasets']:
            for name, digest in dataset['files_sha256'].items():
                pin(Path(dataset['path']) / name, digest)
        for rel, digest in manifest['pins']['code'].items():
            require(source_hashes[rel] == digest, f'Outer manifest code differs: {rel}')
        for path, digest in manifest['pins']['protected'].items():
            pin(Path(path), digest)
        for arm, weight in (('control', 0.0), ('anchor', 0.1)):
            role = f'{arm.upper()}{seed}'
            entry = manifest['arms'][arm]
            require(entry['weight'] == weight and entry['engine_arm'] == 'control' and
                    entry['excluded_engine_arms'] == ['sap0'], f'Wrong outer role {role}')
            engine = prepared / 'engine' / arm
            require(entry['engine_prepared'] == str(engine), f'Unexpected inner prepared path {role}')
            pin(engine / 'manifest.json', entry['engine_manifest_sha256'])
            audit_dir = prepared / 'audits' / arm
            receipt_path = audit_dir / 'anchor_receipt.json'
            receipt_sha = pin(receipt_path)
            receipt = read(receipt_path)
            pin(audit_dir / 'status.json')
            status = read(audit_dir / 'status.json')
            require(status['status'] == 'done' and status['arm'] == arm and status['run_seed'] == seed,
                    f'Outer arm is not complete: {role}')
            require(receipt['schema_version'] == 1 and receipt['status'] == 'done' and
                    receipt['arm'] == arm and receipt['run_seed'] == seed and receipt['prepared'] == str(prepared) and
                    receipt['weight'] == weight and receipt['manifest_sha256'] == manifest_sha and
                    receipt['adapter_restored'] is True and receipt['constructor_restored'] is True,
                    f'Outer receipt mismatch: {role}')
            require(set(receipt['evidence_sha256']) == set(EVIDENCE), f'Outer evidence set differs: {role}')
            for name, digest in receipt['evidence_sha256'].items():
                pin(audit_dir / name, digest)
            nested = engine / 'runs/control'
            inner_path = nested / 'final_receipt.json'
            pin(inner_path, receipt['inner_receipt_sha256'])
            inner = read(inner_path)
            expected_final = nested / 'weights/agent.pth'
            require(receipt['final_checkpoint'] == inner['final_checkpoint'] == str(expected_final) and
                    receipt['checkpoint_sha256'] == inner['final_checkpoint_sha256'], f'Not fixed final checkpoint: {role}')
            require(inner['schema_version'] == 1 and inner['status'] == 'done' and inner['arm'] == 'control' and
                    inner['run_seed'] == seed and inner['prepared'] == str(engine) and
                    inner['student_sha256'] == A2_SHA and inner['config'] == entry['config'] and
                    (inner['actual_prefill_games'], inner['actual_train_games'], inner['actual_validation_games']) == (40, 160, 32) and
                    inner['end']['learning']['learn_steps'] == 24000 and
                    inner['end']['learning']['env_steps'] == 120600, f'Inner budget/config differs: {role}')
            checkpoint_sha = pin(expected_final, receipt['checkpoint_sha256'])
            require(set(inner['evidence_sha256']) == {'training_audit.json', 'rollouts.jsonl', 'validation_games.jsonl', 'train.csv'},
                    f'Inner evidence set differs: {role}')
            for name, digest in inner['evidence_sha256'].items():
                pin(nested / name, digest)
            pin(nested / 'status.json')
            require(read(nested / 'status.json')['status'] == 'done', f'Inner not complete: {role}')
            guard_path = TMP / f'seed{seed}_{arm}_guard.json'
            guard_sha = pin(guard_path)
            guard = read(guard_path)
            expected_command = [admission['python'], '-B', '-m', 'scripts.student_anchor_train', 'run',
                '--prepared', f'experiments/runs/20261104_a2_anchor/seed{seed}', '--arm', arm,
                '--deadline-utc', admission['deadline_utc']]
            require(guard['status'] == 'completed' and guard['returncode'] == 0 and
                    guard['cwd'] == str(ROOT) and guard['command'] == expected_command and
                    guard['guard_sha256'] == inputs[str(TMP / 'run_guarded.py')] and
                    'stop_reason' not in guard and 'error' not in guard and
                    stamp(guard['finished_utc']) >= stamp(guard['started_utc']), f'Guard incomplete or command differs: {role}')
            require(guard['child_process_group'] == guard['child_pid'], f'Inconsistent owned process group: {role}')
            assert_dead_pid(guard['launcher_pid'], role + ' guard')
            assert_dead_pid(guard['child_pid'], role + ' child')
            assert_dead_pid(guard['child_process_group'], role + ' group', group=True)
            independent = learning['arms'][role]
            require(independent['prepared'] == str(prepared) and independent['receipt_sha256'] == receipt_sha and
                    independent['checkpoint_sha256'] == checkpoint_sha and independent['guard_sha256'] == guard_sha and
                    independent.get('public_validate_passed') is True and independent.get('independent_checks_passed') is True and
                    (arm == 'control' or independent.get('anchor_active_verified') is True), f'Independent audit binding differs: {role}')
            target = CANDIDATES / f'{role}.pth'
            role_paths[role] = str(target.relative_to(ROOT))
            role_manifest[role] = dict(path=role_paths[role], sha256=checkpoint_sha, original=False,
                source_final_checkpoint=str(expected_final), outer_receipt=str(receipt_path), receipt_sha256=receipt_sha,
                run_seed=seed, arm=arm, weight=weight, final_only=True, ensemble=False,
                public_validate_passed=True, independent_checks_passed=True, promoted=False)
            copies.append((expected_final, target, checkpoint_sha))
    # Preserve role insertion order: run_diagnostic.py queues all panels first.
    roles = {role: role_paths[role] for role in ROLES}
    role_manifest = {role: role_manifest[role] for role in ROLES}
    old_state_path = OLD / 'state.json'
    pin(old_state_path)
    old_state = read(old_state_path)
    require(old_state['status'] == 'complete' and old_state['completed'] == 17 and
            not old_state['running'] and old_state['pins_after_equal'] is True,
            'Historical action-student diagnostic incomplete')
    timing = {}
    for kind, old_roles in (('panel', ('V14',) + SINGLE_OLD), ('direct', SINGLE_OLD)):
        for role in old_roles:
            name = f'{kind}_{role}'
            job = next(j for j in old_state['jobs'] if j['name'] == name)
            path = OLD / kind / f'{role}.csv'
            guard_path = OLD / 'guards' / f'{name}.json'
            csv_sha = pin(path, job['csv_sha256'])
            pin(guard_path)
            guard = read(guard_path)
            require(job['status'] == guard['status'] == 'completed' and job['returncode'] == guard['returncode'] == 0,
                    f'Historical timing job not complete: {name}')
            wall = (stamp(guard['finished_utc']) - stamp(guard['started_utc'])).total_seconds()
            require(math.isfinite(wall) and wall > 0, f'Invalid historical wall time: {name}')
            # Read only timing and key columns, never historical outcome columns.
            with path.open(newline='') as handle:
                rows = [{k: r[k] for k in ('seed', 'side', 'opponent', 'secs')} for r in csv.DictReader(handle)]
            expected_opps = OPPONENTS if kind == 'panel' else (DIRECT_OPPONENT,)
            expected_seeds = range(866000, 866020) if kind == 'panel' else range(866100, 866120)
            keys = {(int(r['seed']), r['side'], r['opponent']) for r in rows}
            expected_keys = {(s, side, opp) for s in expected_seeds for side in ('player_0', 'player_1') for opp in expected_opps}
            require(len(rows) == len(expected_keys) and keys == expected_keys, f'Historical timing keys differ: {name}')
            require(all(math.isfinite(float(r['secs'])) and float(r['secs']) > 0 for r in rows), f'Invalid timing: {name}')
            means = {opp: sum(float(r['secs']) for r in rows if r['opponent'] == opp) / 40 for opp in expected_opps}
            timing[name] = dict(csv=str(path), sha256=csv_sha, guard=str(guard_path), guard_sha256=inputs[str(guard_path)],
                               mean_seconds_by_opponent=means, wall_seconds=wall)
    single_means = {opp: max(timing[f'panel_{role}']['mean_seconds_by_opponent'][opp] for role in SINGLE_OLD) for opp in OPPONENTS}
    panel_single = max(40 * sum(single_means.values()), max(timing[f'panel_{r}']['wall_seconds'] for r in SINGLE_OLD))
    panel_v14 = max(40 * sum(timing['panel_V14']['mean_seconds_by_opponent'].values()), timing['panel_V14']['wall_seconds'])
    direct_single = max(max(40 * timing[f'direct_{r}']['mean_seconds_by_opponent'][DIRECT_OPPONENT] for r in SINGLE_OLD),
                        max(timing[f'direct_{r}']['wall_seconds'] for r in SINGLE_OLD))
    queue = [0.0, 0.0]
    schedule = []
    for kind, current_roles in (('panel', ROLES), ('direct', ROLES[1:])):
        for role in current_roles:
            base = panel_v14 if role == 'V14' else (panel_single if kind == 'panel' else direct_single)
            seconds = base * 1.15 + 12
            worker = min(range(2), key=lambda w: queue[w])
            start = queue[worker]
            queue[worker] += seconds
            schedule.append(dict(name=f'{kind}_{role}', kind=kind, role=role, worker=worker,
                                 games=120 if kind == 'panel' else 40, unpadded_seconds=base,
                                 duration_seconds=seconds, start_s=start, end_s=queue[worker]))
    require(len(schedule) == 11 and sum(j['games'] for j in schedule) == 920, 'Fixed diagnostic schedule differs')
    now = dt.datetime.now(dt.timezone.utc)
    projected = now + dt.timedelta(seconds=max(queue))
    require(projected < stamp(DEADLINE), 'Full fixed diagnostic does not fit deadline; no files/games written')
    runtime = dict(status='admitted', created_utc=now.isoformat(), historical_study='action_student_20261104/diagnostic only',
        historical_timing_sources=timing, single_net_bound_by_opponent=single_means,
        base_panel_single_seconds=panel_single, base_panel_V14_seconds=panel_v14, base_direct_single_seconds=direct_single,
        explanation='512-wide single roles use maxima over completed earlier 512-wide single roles. For each class use the greater of summed per-opponent maxima and observed completed guard wall time. Direct games use actual earlier single-vs-V14 timing. No fresh outcomes used. All bases padded 15% plus 12 seconds per job. Two-worker greedy queue in controller order. Estimate, not a guaranteed worst case.',
        multiplier=1.15, startup_seconds_per_job=12, workers=2, schedule=schedule,
        two_worker_queue_seconds=max(queue), deadline_utc=DEADLINE, projected_finish_utc=projected.isoformat(),
        latest_estimated_launch_utc=(stamp(DEADLINE) - dt.timedelta(seconds=max(queue))).isoformat(),
        account_used_percent=args.account_used_percent, battery_percent=args.battery_percent,
        model_jobs_end_by_23_Berlin=True, closure_target_UTC='2026-11-04T22:20:00Z', admitted=True)
    # Discover installed engine and versions using stdlib only in admitted Python.
    python = Path(admission['python'])
    pin(python)
    pin(python.resolve())
    query = "import importlib.util,importlib.metadata,json;from pathlib import Path;print(json.dumps({'engine':str(Path(importlib.util.find_spec('luxai_s3').origin).parent),'versions':{p:importlib.metadata.version(p) for p in ['torch','numpy','luxai-s3','jax','jaxlib']}}))"
    dependencies = json.loads(subprocess.check_output([str(python), '-B', '-c', query], cwd=ROOT, text=True))
    engine = Path(dependencies['engine'])
    require(engine.is_dir(), 'Engine package missing')
    engine_files = sorted(engine.rglob('*.py'))
    require(engine_files, 'Engine Python inventory empty')
    for path in engine_files:
        pin(path)
    panel_seeds, direct_seeds = list(range(867000, 867020)), list(range(867100, 867120))
    temp_targets = [TMP / name for name in ('panel_seeds.json', 'direct_seeds.json', 'role_manifest.json',
                        'diagnostic_runtime_admission.json', 'diagnostic_protocol.json')]
    require(not OUT.exists() and not OUT.is_symlink(), f'Diagnostic archive already exists: {OUT}')
    require(not CANDIDATES.exists() and not CANDIDATES.is_symlink(), f'Candidate directory already exists: {CANDIDATES}')
    require(all(not p.exists() and not p.is_symlink() for p in temp_targets), 'Preparation targets already exist; review rather than overwrite')
    # Final check before the first mutation. Only hashes/statuses, never models.
    require(head() == SOURCE, 'HEAD changed during preparation')
    for rel, digest in source_hashes.items():
        require(sha(ROOT / rel) == digest, f'Source changed during preparation: {rel}')
    for path, digest in inputs.items():
        require(sha(path) == digest, f'Input changed during preparation: {path}')
    OUT.mkdir(parents=True, exist_ok=False)
    CANDIDATES.mkdir(parents=True, exist_ok=False)
    for source, target, digest in copies:
        exclusive_copy(source, target, digest)
        pin(target, digest)
    exclusive_json(TMP / 'panel_seeds.json', panel_seeds)
    exclusive_json(TMP / 'direct_seeds.json', direct_seeds)
    manifest = dict(schema_version=1, study='a2_teacher_anchor_20261104', source_commit=SOURCE,
        roles=role_manifest, no_ensemble=True, final_only=True, learning_audit=str(learning_path),
        learning_audit_sha256=inputs[str(learning_path)], promotion_from_diagnostic=False)
    exclusive_json(TMP / 'role_manifest.json', manifest)
    exclusive_copy(TMP / 'role_manifest.json', CANDIDATES / 'manifest.json', sha(TMP / 'role_manifest.json'))
    pin(CANDIDATES / 'manifest.json')
    exclusive_json(TMP / 'diagnostic_runtime_admission.json', runtime)
    for path in temp_targets[:-1]:
        pin(path)
        archive = OUT / path.name
        exclusive_copy(path, archive, inputs[str(path)])
        pin(archive)
    for name in ('prepare_diagnostic.py', 'run_guarded.py', 'run_diagnostic.py', 'audit_results.py',
                 'learning_completion_auditor.py', 'crosscheck_diagnostic.py', 'learning_completion_audit.json', 'training_admission.json'):
        path = TMP / name
        archive = OUT / 'admission' / name
        exclusive_copy(path, archive, inputs[str(path)])
        pin(archive)
    protocol = dict(schema_version=1, study='a2_teacher_anchor_20261104', status='admitted_frozen_before_first_game',
        root=str(ROOT), output_directory=str(OUT), source_commit=SOURCE, source_sha256=source_hashes,
        inputs_sha256=inputs, roles=roles, role_manifest=str(TMP / 'role_manifest.json'),
        panel_seeds=panel_seeds, direct_seeds=direct_seeds, opponents=list(OPPONENTS), direct_opponent=DIRECT_OPPONENT,
        panel_games=720, direct_games=200, total_games=920, jobs=11, max_workers=2, threads_per_worker=1,
        panel_seed_file=str(TMP / 'panel_seeds.json'), direct_seed_file=str(TMP / 'direct_seeds.json'),
        python=str(python), guard_script=str(TMP / 'run_guarded.py'), controller=str(TMP / 'run_diagnostic.py'),
        recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(), deadline_utc=DEADLINE,
        runtime_admission=runtime, dependency_versions=dependencies['versions'],
        evaluation_overrides=['frozen=false'], statistical_unit='whole card across sides and opponents',
        bootstrap_replicates=5000, bootstrap_seed=0, bootstrap_interval='explorative percentile 95%',
        primary_method_contrast='ANCHOR minus CONTROL, separately per training seed',
        secondary_contrasts=['A2 minus V14', 'ANCHOR minus A2'],
        confirmation_screen='ANCHOR only: panel >= A2, Solution >= A2, panel > paired CONTROL, >=24/40 strict direct wins; rank panel, Solution, smaller training seed',
        no_fallback_after_failed_confirmation=True, no_ensembles=True, no_hyperparameter_search=True,
        selection_after_observing_games=False, confirmation=False, promotion_from_diagnostic=False,
        seed_inventory=str(inventory_path), seed_inventory_sha256=inputs[str(inventory_path)],
        seed_freshness_limits=inventory['limits'], learning_audit=str(learning_path),
        notes=['Diagnostic qualifies no submission; full later confirmation/course/package checks remain required.',
               'Training-seed effects remain separate; only two starts and 20 diagnostic cards.',
               'Keep all frozen sources, helpers, inputs, engine files and HEAD unchanged until the controller and audit finish.',
               'No games are launched by this preparation helper. Root performs the separate guarded launch after current operational checks.'])
    # Recheck all pins and budget after copies/hashing, before publishing admission.
    require(head() == SOURCE, 'HEAD changed before protocol publication')
    for rel, digest in source_hashes.items():
        require(sha(ROOT / rel) == digest, f'Source changed before admission: {rel}')
    for path, digest in inputs.items():
        require(sha(path) == digest, f'Input changed before admission: {path}')
    require(dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=max(queue)) < stamp(DEADLINE),
            'Admission preparation consumed runtime reserve; no protocol published')
    exclusive_json(TMP / 'diagnostic_protocol.json', protocol)
    exclusive_copy(TMP / 'diagnostic_protocol.json', OUT / 'diagnostic_protocol.json', sha(TMP / 'diagnostic_protocol.json'))
    print(json.dumps(dict(status='admitted', protocol=str(TMP / 'diagnostic_protocol.json'),
        protocol_sha256=sha(TMP / 'diagnostic_protocol.json'), archive=str(OUT), games=920, jobs=11,
        duration_minutes=max(queue) / 60, projected_finish_utc=runtime['projected_finish_utc'], no_games_started=True)))


if __name__ == '__main__':
    main()
