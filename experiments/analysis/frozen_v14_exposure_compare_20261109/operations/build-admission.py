"""Build one frozen-V14-exposure comparison admission; never launch work.

Default mode is check-only. This file is intentionally an unexecuted draft and
must not be imported or run before the actual exposure training closure has
been accepted by Root. --training-closure-sha256 must be supplied from that
actual closure, and --expected-head must be the exact committed source HEAD.
--write is reserved for a later explicit Root invocation.

Only JSON, Git/source metadata, and byte hashes are read. Model checkpoints are
hashed as files but never deserialized or loaded into a model.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

DEFAULT_ROOT = Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
PROFILE = 'frozen_v14_exposure_compare_20261109'
EXPOSURE = 'frozen_v14_exposure_20261109'
BEHAVIOR = 'ensemble_behavior_20261109'
REFERENCE = 'ensemble_behavior_compare_20261109'
REFERENCE_ACCEPTANCE_SHA = '73fdf5eabd99380882d2f13d9c7575c41bae8d2726e342b1ba801525ddd16c43'
STARTS = [48, 49]
TRAINING_ACTUAL = dict(technical_games=4, prefill_games=80, learning_games=800, optimizer_updates=120000)
SEED_COHORTS = {
    'solution': list(range(10010000, 10010020)),
    'direct_v14': list(range(10010100, 10010120)),
    'direct_behavior': list(range(10010200, 10010220)),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage', choices=('technical', 'performance'), required=True)
    ap.add_argument('--expected-head', required=True, help='Exact full lowercase committed source HEAD')
    ap.add_argument('--training-closure-sha256', required=True,
                    help='Exact SHA-256 of the actual Root-accepted exposure training closure')
    ap.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    ap.add_argument('--stop-file', type=Path, required=True)
    ap.add_argument('--write', action='store_true', help='Root-authorized exclusive admission publication')
    args = ap.parse_args()
    root = args.root.resolve(strict=True)
    if root != Path.cwd().resolve():
        raise ValueError('Run from the exact admitted study checkout')
    if len(args.expected_head) != 40 or any(c not in '0123456789abcdef' for c in args.expected_head):
        raise ValueError('An exact full committed HEAD is required')
    if len(args.training_closure_sha256) != 64 or any(c not in '0123456789abcdef' for c in args.training_closure_sha256):
        raise ValueError('An exact SHA-256 from the actual training closure is required')

    # These imports occur only when this draft is later explicitly run.
    sys.path.insert(0, str(root))
    from scripts.early_curriculum_study import digest, require, source_identity
    from scripts.final_training_supervisor import safe_path

    base = root / 'experiments/analysis' / PROFILE
    output = safe_path(base / f'{args.stage}_v1')
    admission_path = safe_path(base / f'{args.stage}-v1-admission.json')
    stop_root = Path('/private/tmp/frozen-v14-exposure-compare-20261109')
    stop = safe_path(args.stop_file)
    require(stop == stop_root / f'{args.stage}.STOP', 'Wrong phase-specific STOP path')
    require(not output.exists() and not admission_path.exists(), 'Existing output/admission; no overwrite or resume')
    require(not stop.exists(), 'STOP already exists; Root must resolve it explicitly')

    inputs = {}

    def bind(path, expected=None):
        path = safe_path(path)
        actual = digest(path)
        require(expected is None or actual == expected, f'Bound file SHA-256 differs: {path}')
        key = str(path)
        require(key not in inputs or inputs[key] == actual, f'Conflicting bindings: {path}')
        inputs[key] = actual
        return path

    def read(path, expected=None):
        path = bind(path, expected)
        return json.loads(path.read_text())

    def bind_manifest(manifest):
        require(isinstance(manifest, dict), 'Expected a path-to-SHA256 file manifest')
        for path, sha in manifest.items():
            require(isinstance(path, str) and isinstance(sha, str) and len(sha) == 64,
                    'Malformed file manifest entry')
            bind(path, sha)

    # Actual frozen-V14 exposure training closure: supplied SHA is mandatory,
    # and all closure-listed receipts/files are rebound before any admission.
    expbase = root / 'experiments/analysis' / EXPOSURE
    closure_path = expbase / 'operations/training-completion.json'
    closure = read(closure_path, args.training_closure_sha256)
    require(closure.get('profile') == EXPOSURE
            and closure.get('status') == 'COMPLETE_TRAINING_NO_STRENGTH_CLAIM'
            and closure.get('original_processes_ended') is True
            and closure.get('source_and_input_bindings_valid') is True
            and closure.get('no_strength_claim') is True
            and closure.get('actual') == TRAINING_ACTUAL,
            'Exposure training closure is not the actual complete accepted run')
    bind_manifest(closure.get('files'))
    train_adm_path = Path(closure['admission'])
    train_adm = read(train_adm_path, closure['admission_sha256'])
    train_state_path = Path(closure['state'])
    train_state = read(train_state_path, closure['state_sha256'])
    require(train_adm.get('profile') == EXPOSURE and train_adm.get('stage') == 'training'
            and train_state.get('status') == 'complete' and train_state.get('active') == []
            and train_state.get('source') == closure.get('source')
            and train_adm.get('source') == closure.get('source'),
            'Exposure admission/state/source does not match closure')
    require(train_adm.get('starts') == STARTS and train_adm.get('protected') == closure.get('protected'),
            'Exposure training roles/protected inputs differ')
    bind_manifest(train_adm.get('inputs'))
    train_technical_acceptance = read(train_adm['technical_acceptance'])
    train_technical_receipt = read(train_adm['technical_receipt'])
    require(train_technical_acceptance.get('status') == 'PASS'
            and train_technical_acceptance.get('profile') == EXPOSURE
            and train_technical_acceptance.get('source') == closure.get('source')
            and train_technical_acceptance.get('original_processes_ended') is True
            and train_technical_receipt.get('status') == 'complete'
            and train_technical_receipt.get('profile') == EXPOSURE
            and train_technical_receipt.get('stage') == 'technical'
            and isinstance(train_technical_receipt.get('games'), list)
            and len(train_technical_receipt['games']) == 4,
            'Accepted exposure technical evidence differs')
    exposure_final_q = []
    for role in ('e48', 'e49'):
        model = closure.get('models', {}).get(role)
        require(isinstance(model, dict), f'Missing accepted final model record: {role}')
        bind(model['path'], model['sha256'])
        receipt = read(model['receipt'], model['receipt_sha256'])
        require(receipt.get('status') == 'complete' and receipt.get('role') == role,
                f'Final model receipt is incomplete: {role}')
        exposure_final_q.append(receipt['final_identity']['q'])
        prefill_path = Path(model['path']).parent / 'prefill.json'
        require(str(prefill_path) in closure.get('files', {}), f'Prefill evidence absent from closure: {role}')

    # Preserve the previously accepted ON-training provenance and exact old
    # schema. In particular, the old technical acceptance stores a PID list.
    behbase = root / 'experiments/analysis' / BEHAVIOR
    behavior_closure_path = behbase / 'operations/training-completion.json'
    behavior_closure = read(behavior_closure_path)
    require(behavior_closure.get('profile') == BEHAVIOR
            and behavior_closure.get('status') == 'COMPLETE_TRAINING_NO_STRENGTH_CLAIM'
            and behavior_closure.get('actual') == dict(technical_games=4, prefill_games=80,
                                                        learning_games=800, optimizer_updates=120000)
            and behavior_closure.get('original_processes_ended') is True,
            'Historical behavior training closure differs')
    bind_manifest(behavior_closure.get('files'))
    behavior_adm_path = Path(behavior_closure['admission'])
    behavior_adm = read(behavior_adm_path, behavior_closure['admission_sha256'])
    behavior_state = read(behavior_closure['state'], behavior_closure['state_sha256'])
    require(behavior_adm.get('profile') == BEHAVIOR and behavior_adm.get('stage') == 'training'
            and behavior_state.get('status') == 'complete' and behavior_state.get('active') == []
            and behavior_adm.get('protected') == behavior_closure.get('protected'),
            'Historical behavior run is incomplete or mismatched')
    bind_manifest(behavior_adm.get('inputs'))
    behavior_final_q = []
    for role, model in behavior_closure.get('models', {}).items():
        bind(model['path'], model['sha256'])
        receipt = read(model['receipt'], model['receipt_sha256'])
        require(receipt.get('status') == 'complete' and receipt.get('role') == role,
                f'Historical behavior final receipt differs: {role}')
        behavior_final_q.append(receipt['final_identity']['q'])

    # Accepted 200-game reference performance run, including its Root closure,
    # final summary, owner state and every closure-listed artifact.
    refbase = root / 'experiments/analysis' / REFERENCE
    ref_completion_path = refbase / 'operations/completion.json'
    ref_completion = read(ref_completion_path)
    require(ref_completion.get('profile') == REFERENCE
            and ref_completion.get('status') == 'COMPLETE_NO_NOMINATION'
            and ref_completion.get('games') == 200
            and ref_completion.get('nominated') is False
            and ref_completion.get('original_processes_ended') is True
            and ref_completion.get('source_and_input_bindings_valid') is True
            and ref_completion.get('original_analysis_exactly_reproduced') is True,
            'Historical reference performance closure is not accepted')
    bind_manifest(ref_completion.get('files'))
    ref_perf_adm_path = Path(ref_completion['admission'])
    ref_perf_adm = read(ref_perf_adm_path, ref_completion['admission_sha256'])
    ref_perf_state = read(ref_completion['state'], ref_completion['state_sha256'])
    require(ref_perf_adm.get('profile') == REFERENCE and ref_perf_adm.get('stage') == 'performance'
            and ref_perf_state.get('status') == 'complete' and ref_perf_state.get('active') == []
            and ref_perf_adm.get('source') == ref_completion.get('source'),
            'Reference performance admission/state differs from closure')
    bind_manifest(ref_perf_adm.get('inputs'))
    ref_tech_adm_path = Path(ref_perf_adm['technical_admission'])
    ref_tech_state_path = Path(ref_perf_adm['technical_state'])
    ref_tech_receipt_path = Path(ref_perf_adm['technical_receipt'])
    ref_tech_acceptance_path = Path(ref_perf_adm['technical_acceptance'])
    ref_tech_adm = read(ref_tech_adm_path)
    ref_tech_acceptance = read(ref_tech_acceptance_path, REFERENCE_ACCEPTANCE_SHA)
    ref_tech_state = read(ref_tech_state_path, ref_tech_acceptance['owner_state_sha256'])
    ref_tech_receipt = read(ref_tech_receipt_path, ref_tech_acceptance['technical_receipt_sha256'])
    require(ref_tech_adm.get('profile') == REFERENCE and ref_tech_adm.get('stage') == 'technical'
            and ref_tech_acceptance.get('profile') == REFERENCE and ref_tech_acceptance.get('status') == 'PASS'
            and ref_tech_acceptance.get('actual_assembly_and_stock_loader_pass') is True
            and ref_tech_acceptance.get('original_processes_ended') is True
            and ref_tech_state.get('status') == 'complete' and ref_tech_state.get('active') == []
            and ref_tech_receipt.get('profile') == REFERENCE and ref_tech_receipt.get('games') == 0,
            'Historical behavior montage acceptance differs')
    require(ref_tech_receipt['models']['behavior']['member_sha256'][36:] == behavior_final_q,
            'Historical behavior member suffix differs from accepted final identities')
    ref_summary = read(refbase / 'performance_v1/summary.json', ref_completion['summary_sha256'])
    require(ref_summary.get('profile') == REFERENCE
            and ref_summary.get('source') == ref_perf_adm.get('source'),
            'Reference final summary differs')

    # Link accepted original and new groups. The exposure closure is the only
    # source of the two new exposure finals; old inputs remain historical.
    protected = closure['protected']
    require(behavior_adm.get('protected') == protected
            and ref_perf_adm.get('protected') == protected,
            'Protected model/ZIP inputs differ across phases')
    for path, sha in protected.items():
        bind(path, sha)
    require(behavior_adm.get('config') == train_adm.get('config'),
            'Exposure training changed historical ON config')

    prep = expbase / 'preparation'
    seed_acceptance_path = prep / 'seed-acceptance.json'
    seed_acceptance = read(seed_acceptance_path)
    require(seed_acceptance.get('profile') == EXPOSURE and seed_acceptance.get('status') == 'PASS'
            and seed_acceptance.get('cohorts') == SEED_COHORTS,
            'Accepted seed/cohort metadata differs from fixed 60-card scope')
    bind_manifest(seed_acceptance.get('files'))
    cohort_paths = {name: str(bind(prep / f'{name}.json')) for name in SEED_COHORTS}
    cohorts = {name: read(path) for name, path in cohort_paths.items()}
    # JSON cohort shapes may include metadata; require exact same cohort records
    # captured by seed acceptance, without synthesizing or widening IDs.
    require(cohorts == seed_acceptance.get('cohorts'),
            'Prepared cohort JSON differs from seed acceptance')

    # All prior input supersets are carried forward, preserving their hashes.
    plans = set(behavior_adm.get('plans', [])) | set(ref_perf_adm.get('plans', [])) | set(train_adm.get('plans', []))
    new_plans = [
        root / 'docs/superpowers/specs/2026-11-09-frozen-v14-exposure.md',
        root / 'docs/superpowers/plans/2026-11-09-frozen-v14-exposure.md',
    ]
    plans.update(str(p) for p in new_plans)
    plans = sorted(plans)
    for plan in plans:
        bind(plan)
    for hist in (behavior_adm, ref_perf_adm, train_adm):
        require(hist.get('root') == str(root) and hist.get('python') == sys.executable,
                'Historical root/interpreter differs')
        bind_manifest(hist.get('inputs'))

    # Comparison source files are bound into this future source identity. Their
    # exact list is checked against the finalized committed implementation.
    comparison_sources = (
        'scripts/frozen_v14_exposure_compare.py',
        'scripts/frozen_v14_exposure_compare_owner.py',
        'tests/test_frozen_v14_exposure_compare.py',
    )
    for rel in comparison_sources:
        bind(root / rel)
    source = source_identity(root, sys.executable, plans)
    require(source.get('head') == args.expected_head, 'Expected committed HEAD differs')
    for hist in (behavior_adm, ref_perf_adm, train_adm):
        old = hist.get('source', {})
        require(all(source.get(k) == old.get(k) for k in ('python', 'executable', 'executable_sha256'))
                and all(source.get('files', {}).get(p) == h for p, h in old.get('files', {}).items()),
                'Historical source is not an unchanged subset')

    v14_source = str(root / 'agents/sherlock/weights/agent_p0.pth')
    v14_model = ref_perf_adm.get('models', {}).get('v14')
    behavior_model = ref_perf_adm.get('models', {}).get('behavior')
    require(v14_model and behavior_model, 'Reference performance admission lacks V14/BEHAVIOR38 models')
    models = {'v14': str(bind(v14_model)), 'behavior': str(bind(behavior_model))}
    bind(v14_source, protected.get(v14_source))

    admission = dict(
        schema_version=1, profile=PROFILE, stage=args.stage,
        start_authorized=True, allow_battery=True,
        root=str(root), out=str(output), python=sys.executable, plans=plans,
        source=source, protected=protected, inputs=inputs, stop_file=str(stop),
        training_completion=str(closure_path),
        training_completion_sha256=args.training_closure_sha256,
        reference_performance_admission=str(ref_perf_adm_path),
        v14_source=v14_source, cohorts=cohort_paths,
        seed_acceptance=str(seed_acceptance_path),
    )
    if args.stage == 'performance':
        technical_adm_path = base / 'technical-v1-admission.json'
        technical_receipt_path = base / 'technical_v1/technical-receipt.json'
        technical_state_path = base / 'technical_v1/state.json'
        technical_acceptance_path = base / 'operations/technical-acceptance.json'
        technical_adm = read(technical_adm_path)
        technical_receipt = read(technical_receipt_path)
        technical_state = read(technical_state_path)
        technical_acceptance = read(technical_acceptance_path)
        bind_manifest(technical_adm.get('inputs'))
        require(technical_adm.get('profile') == PROFILE and technical_adm.get('stage') == 'technical'
                and technical_adm.get('source') == source and technical_adm.get('training_completion_sha256') == args.training_closure_sha256,
                'Technical admission does not match actual source/training closure')
        require(technical_state.get('profile') == PROFILE and technical_state.get('stage') == 'technical'
                and technical_state.get('status') == 'complete' and technical_state.get('active') == []
                and technical_state.get('source') == source
                and technical_state.get('admission_sha256') == digest(technical_adm_path)
                and technical_state.get('jobs', {}).get('technical', {}).get('returncode') == 0,
                'Technical owner state is not complete')
        require(technical_receipt.get('profile') == PROFILE and technical_receipt.get('status') == 'complete'
                and technical_receipt.get('games') == 0 and technical_receipt.get('source') == source
                and technical_receipt.get('admission_sha256') == digest(technical_adm_path)
                and technical_receipt.get('training_completion_sha256') == args.training_closure_sha256
                and technical_receipt.get('reference_performance_admission_sha256') == digest(ref_perf_adm_path)
                and technical_receipt.get('no_strength_claim') is True,
                'Technical assembly receipt is incomplete or mismatched')
        require(technical_acceptance.get('profile') == PROFILE and technical_acceptance.get('status') == 'PASS'
                and technical_acceptance.get('source') == source
                and technical_acceptance.get('admission_sha256') == digest(technical_adm_path)
                and technical_acceptance.get('technical_receipt_sha256') == digest(technical_receipt_path)
                and technical_acceptance.get('owner_state_sha256') == digest(technical_state_path)
                and technical_acceptance.get('actual_assembly_and_stock_loader_pass') is True
                and technical_acceptance.get('original_processes_ended') is True,
                'Separate Root technical acceptance missing/stale')
        exposure_model = technical_receipt.get('models', {}).get('exposure')
        require(isinstance(exposure_model, dict), 'Technical receipt lacks exposure checkpoint binding')
        models['exposure'] = str(bind(exposure_model['path'], exposure_model['sha256']))
        require(set(models) == {'v14', 'behavior', 'exposure'}, 'Wrong three-model comparison set')
        records = technical_receipt.get('models', {})
        require(set(records) == {'v14', 'behavior', 'exposure'}, 'Technical receipt model roles differ')
        v14_members = records['v14'].get('member_sha256')
        behavior_members = records['behavior'].get('member_sha256')
        exposure_members = records['exposure'].get('member_sha256')
        require(records['v14'].get('members') == 36 and records['behavior'].get('members') == 38
                and records['exposure'].get('members') == 38
                and isinstance(v14_members, list) and isinstance(behavior_members, list)
                and isinstance(exposure_members, list) and len(v14_members) == 36
                and len(behavior_members) == len(exposure_members) == 38
                and behavior_members[:36] == v14_members == exposure_members[:36]
                and behavior_members[36:] == behavior_final_q
                and exposure_members[36:] == exposure_final_q,
                'Three-model member lineage/counts do not match accepted final identities')
        require(records['v14'] == ref_tech_receipt['models']['v14']
                and records['behavior'] == ref_tech_receipt['models']['behavior'],
                'The two reused model records differ from the accepted original assembly')
        for role in ('v14', 'behavior', 'exposure'):
            model_rec = records[role]
            require(models.get(role) == model_rec.get('path'),
                    f'Performance admission model path differs: {role}')
            bind(model_rec['path'], model_rec['sha256'])
        admission.update(
            technical_admission=str(technical_adm_path),
            technical_receipt=str(technical_receipt_path),
            technical_state=str(technical_state_path),
            technical_acceptance=str(technical_acceptance_path),
            models=models,
        )

    # Run the production adapter's PURE metadata validators on the exact
    # preview object before claiming PASS. These functions read/rehash bound
    # metadata and CSV/JSONL evidence only; they do not load tensors or start work.
    from scripts import frozen_v14_exposure_compare as adapter
    adapter.accepted_references(admission)
    adapter.accepted_training(admission)
    adapter.fixed_cohorts(admission)
    if args.stage == 'performance':
        adapter.accepted_assembly(admission)

    require(str(admission_path) not in inputs and
            all(output != Path(path) and output not in Path(path).parents for path in inputs),
            'Admission/output overlaps a bound input')
    if args.write:
        admission_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile('w', dir=admission_path.parent,
                                             prefix='.admission-', delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(admission, stream, sort_keys=True, indent=2, allow_nan=False)
                stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
            os.link(temporary, admission_path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    print(json.dumps(dict(status='PASS', profile=PROFILE, stage=args.stage,
                          head=source['head'], inputs=len(inputs),
                          source_files=len(source['files']), admission_written=args.write,
                          started=False, admission=str(admission_path),
                          sha256=digest(admission_path) if args.write else None), sort_keys=True))


if __name__ == '__main__':
    main()
