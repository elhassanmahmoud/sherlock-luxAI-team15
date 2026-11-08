"""Fixed conditional-HOLD study: collect, fit once, validate, or neutral-proof.

Collection uses the audited branch engine and always the original V14 policy.
Validation collection requires an already frozen fit receipt. Nothing runs on
import; every output directory is exclusive and unsuccessful attempts remain.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

from scripts.holder_rollout_probe import (ROOT, V14_SHA, PLANS as OLD_PLANS, SMOKE_KEYS,
    digest, hashes, require, source_identity, run_collection, write_json)

PROTOCOLS = ('docs/superpowers/specs/2026-11-08-holder-learning.md',
             'docs/superpowers/plans/2026-11-08-holder-learning.md')
SIDES = ('player_0', 'player_1')


def validate_plan(path, split):
    require(split in ('train', 'validation'), 'Unknown study split')
    plan = json.loads(Path(path).read_text())
    expected = dict(schema_version=1, study='holder_learning_20261108',
                    weights='agents/sherlock/weights/agent_p0.pth', baseline_sha256=V14_SHA,
                    opponent='solution92', train_seeds=list(range(6500000, 6500024)),
                    validation_seeds=list(range(6501000, 6501008)), sides=list(SIDES),
                    max_pairs_per_game=8, spacing=12, horizon=12, protocols=list(PROTOCOLS))
    require(plan == expected, 'Study plan differs from the fixed 24/8-map protocol')
    keys = [dict(seed=seed, side=side, opponent='solution92')
            for seed in plan[split + '_seeds'] for side in SIDES]
    protocols = [ROOT / p for p in PROTOCOLS]
    require(all(p.is_file() for p in protocols), 'Study protocols missing')
    return plan, keys, protocols


def _source(protocols):
    return source_identity(ROOT, sys.executable, [*OLD_PLANS, *protocols])


def collect(plan_path, out, *, split, expected_head, usage_file, stop_file, fit_receipt=None):
    plan_path = Path(plan_path).resolve()
    plan, keys, protocols = validate_plan(plan_path, split)
    inputs = [ROOT / plan['weights'], plan_path]
    metadata = dict(split=split, baseline_sha256=V14_SHA, plan_sha256=digest(plan_path))
    if split == 'validation':
        require(fit_receipt is not None, 'Validation requires a frozen fit receipt')
        receipt, head = read_fit_receipt(fit_receipt, plan_path, expected_head=expected_head)
        inputs.extend([Path(fit_receipt).resolve(), *map(Path, receipt['artifacts'])])
        inputs.extend([Path(receipt['training_manifest']), *map(Path, receipt['training_artifacts'])])
        metadata.update(fit_receipt_sha256=digest(fit_receipt), fitted_head_sha256=receipt['head_sha256'],
                        training_manifest_sha256=receipt['training_manifest_sha256'])
    else:
        require(fit_receipt is None, 'Training collection cannot consume a fitted head')
    return run_collection(ROOT / plan['weights'], out, selected=keys, all_keys=keys,
                          frozen_inputs=inputs, source_plans=[*OLD_PLANS, *protocols],
                          expected_head=expected_head, usage_file=usage_file, stop_file=stop_file,
                          kind='holder_learning_' + split, metadata=metadata)


def action_digest(actions):
    from scripts.targeting_probe import action_bytes
    return hashlib.sha256(action_bytes({k: np.asarray(v) for k, v in actions.items()})).hexdigest()


def _frames(path):
    from scripts.holder_rollout import exact_digest
    with gzip.open(path, 'rt') as stream:
        frames = [json.loads(line) for line in stream]
    require(len(frames) == 303, 'Incomplete frame trajectory')
    for step, frame in enumerate(frames):
        unsigned = {k: v for k, v in frame.items() if k != 'sha256'}
        require(frame['step'] == step and exact_digest(unsigned) == frame['sha256']
                and action_digest(frame['actions']) == frame['action_sha256'], 'Invalid trajectory frame')
        require(bool(frame['done']) == (step == 302), 'Incomplete terminal trajectory')
        if step:
            require(frame['before_state'] == frames[step-1]['after_state']
                    and frame['before_obs'] == frames[step-1]['after_obs'], 'Broken trajectory chain')
    return frames


def _branch(branch, side):
    from scripts.holder_rollout import exact_digest
    frames = branch['frames']
    require(len(frames) == 12 and exact_digest(frames) == branch['sha256'], 'Invalid branch digest/horizon')
    points = np.sum([f['points'] for f in frames], axis=0)
    team = int(side[-1])
    require(points.tolist() == branch['points']
            and int(points[team] - points[1-team]) == branch['point_differential'], 'Invalid branch point label')
    return branch['point_differential']


def artifact_hashes(state):
    result = {}
    for game in state['games']:
        for mode in ('reference', 'collector'):
            result.update(game[mode + '_artifacts'])
    return result


def read_collection(manifest_path, plan_path, split):
    """Read all complete pairs, recomputing passivity and live-baseline evidence."""
    manifest_path = Path(manifest_path).resolve()
    _, keys, _ = validate_plan(plan_path, split)
    state = json.loads(manifest_path.read_text())
    require(state['status'] == 'complete' and state['kind'] == 'holder_learning_' + split
            and state['split'] == split and state['schema_version'] == 1, 'Incomplete/wrong collection phase')
    require(state['baseline_sha256'] == V14_SHA and state['plan_sha256'] == digest(plan_path), 'Plan/baseline binding changed')
    require(state['keys'] == keys and state['all_keys'] == keys
            and [g['key'] for g in state['games']] == keys, 'Collection keys missing/reordered')
    require(state['planned_games'] == state['completed_games'] == 2*len(keys)
            and state['horizon'] == 12 and state['max_pairs_per_game'] == 8, 'Incomplete collection counts')
    require(hashes(state['inputs']) == state['inputs'] and hashes(state['protected']) == state['protected'],
            'Frozen collection input changed')
    rows, technical, diagnostic = [], 0, 0
    for game in state['games']:
        key = game['key']; seed, side = key['seed'], key['side']
        ref, col = game['reference'], game['collector']
        passivity = {k: ref[k] == col[k] for k in ref if k != 'pairs'}
        require(passivity == game['passivity'] and all(passivity.values()), 'Recomputed passivity failed')
        streams = {}
        for mode, result in (('reference', ref), ('collector', col)):
            bound = game[mode + '_artifacts']
            expected = [manifest_path.parent / f'{seed}_{side}_{mode}{suffix}'
                        for suffix in ('.frames.jsonl.gz', '.pairs.jsonl')]
            require(set(bound) == set(map(str, expected)) and hashes(bound) == bound, 'Collection artifact binding changed')
            frames = _frames(expected[0]); streams[mode] = frames
            trajectory = hashlib.sha256(b''.join(bytes.fromhex(f['sha256']) for f in frames)).hexdigest()
            require(result['seed'] == seed and result['side'] == side and result['steps'] == 303
                    and result['resets'] == 3 and len(result['matches']) == 3 and result['caught_errors'] == 0
                    and result['point_counting_version'] == 2 and result['trajectory_sha256'] == trajectory
                    and result['points'] == np.sum([f['points'] for f in frames], axis=0).tolist(), 'Incomplete game trajectory/result')
            entries = [json.loads(line) for line in expected[1].read_text().splitlines()]
            if mode == 'reference':
                require(not entries and not result['pairs'], 'Reference must have no collected pairs')
                continue
            require(len(result['pairs']) <= 8 and len(entries) == 2*len(result['pairs']), 'Incomplete live-verified pairs')
            last_step = -12
            for pair_id, summary in enumerate(result['pairs']):
                pair, receipt = entries[2*pair_id:2*pair_id+2]
                candidate = pair['candidate']; step = candidate['step']
                require(pair['pair_id'] == pair_id and pair['seed'] == seed and pair['side'] == side
                        and pair['status'] == 'pending_live_verification', 'Wrong pair identity/status')
                require(type(step) is int and step-last_step >= 12 and 1 <= candidate['match_step'] <= 89,
                        'Pair cadence/boundary mismatch')
                baseline, hold = _branch(pair['baseline'], side), _branch(pair['hold'], side)
                require(type(pair['label']) is int and pair['label'] == hold-baseline, 'Counterfactual label mismatch')
                require(pair['baseline']['frames'] == frames[step:step+12], 'Baseline branch differs from live trajectory')
                effective = pair['baseline']['frames'][0]['actions'][side] != pair['hold']['frames'][0]['actions'][side]
                require(pair['effective'] is effective and (effective or pair['baseline'] == pair['hold']), 'Invalid identical-action pair')
                reverse = pair['reverse_repeat']
                require(reverse == {'hold_repeat': True, 'baseline_reverse_repeat': True} if pair_id == 0 else reverse is None,
                        'Reverse/repeat verification missing')
                require(receipt == dict(pair_id=pair_id, status='live_verified', baseline_sha256=pair['baseline']['sha256']),
                        'Missing live-verified receipt')
                expected_summary = dict(pair_id=pair_id, step=step, uid=candidate['uid'], effective=effective,
                                        label=pair['label'], reverse_repeat=reverse, live_verified=True)
                require(summary == expected_summary, 'Pair summary not live verified or differs')
                rows.append(dict(seed=seed, side=side, candidate=candidate, label=pair['label']))
                diagnostic += 24
                if pair_id == 0: technical += 24
                last_step = step
        require(streams['reference'] == streams['collector'], 'Full trajectory passivity failure')
    require(state['completed_pairs'] == len(rows) and state['reference_steps'] == state['instrumented_steps'] == 303*len(keys)
            and state['diagnostic_steps'] == diagnostic and state['technical_extra_steps'] == technical
            and state['additional_steps'] == diagnostic+technical, 'Collection counters differ from evidence')
    return rows, state


def _new_output(path):
    path = Path(path).absolute()
    require(not path.exists(), 'Output directory already exists; no second fit/overwrite')
    path.mkdir(parents=True, exist_ok=False)
    return path


def fit(plan_path, train_manifest, out, *, expected_head):
    from scripts.holder_learning import fit_head, InsufficientTrainingData
    _, _, protocols = validate_plan(plan_path, 'train')
    rows, state = read_collection(train_manifest, plan_path, 'train')
    source = _source(protocols)
    require(source['head'] == expected_head and source == state['source'], 'Training sources/HEAD changed before fit')
    out = _new_output(out)
    provenance = dict(baseline_sha256=V14_SHA, source_identity=source,
                      training_manifest_sha256=digest(train_manifest), training_artifacts=artifact_hashes(state),
                      plan_sha256=digest(plan_path))
    try:
        head, report = fit_head(rows, provenance=provenance)
    except InsufficientTrainingData as exc:
        write_json(out / 'receipt.json', dict(schema_version=1, kind='holder_learning_fit', status='insufficient_data',
                                             error=str(exc), provenance=provenance, created_at=time.time()))
        raise
    write_json(out / 'head.json', head); write_json(out / 'fit_report.json', report)
    receipt = dict(schema_version=1, kind='holder_learning_fit', status='complete', created_at=time.time(),
                   source=source, expected_head=expected_head, plan_sha256=digest(plan_path),
                   training_manifest=str(Path(train_manifest).resolve()), training_manifest_sha256=digest(train_manifest),
                   head_path=str(out / 'head.json'), head_sha256=digest(out / 'head.json'),
                   training_artifacts=provenance['training_artifacts'],
                   artifacts=hashes([out / 'head.json', out / 'fit_report.json']))
    write_json(out / 'receipt.json', receipt)
    return receipt


def read_fit_receipt(path, plan_path, *, expected_head):
    from scripts.holder_learning import validate_head
    _, _, protocols = validate_plan(plan_path, 'train')
    receipt = json.loads(Path(path).read_text())
    require(receipt['schema_version'] == 1 and receipt['kind'] == 'holder_learning_fit'
            and receipt['status'] == 'complete', 'Incomplete fit receipt')
    require(receipt['expected_head'] == expected_head and receipt['source'] == _source(protocols)
            and receipt['source']['head'] == expected_head, 'Fit receipt sources/HEAD changed')
    require(receipt['plan_sha256'] == digest(plan_path), 'Fit receipt plan changed')
    require(hashes(receipt['artifacts']) == receipt['artifacts'] and digest(receipt['head_path']) == receipt['head_sha256']
            and receipt['artifacts'].get(receipt['head_path']) == receipt['head_sha256'], 'Frozen fitted head/report changed')
    require(digest(receipt['training_manifest']) == receipt['training_manifest_sha256'], 'Training manifest changed after fit')
    _, state = read_collection(receipt['training_manifest'], plan_path, 'train')
    require(receipt['training_artifacts'] == artifact_hashes(state) and state['source'] == receipt['source'],
            'Fit training artifact/source binding changed')
    head = validate_head(json.loads(Path(receipt['head_path']).read_text()))
    provenance = head['provenance']
    require(provenance['source_identity'] == receipt['source']
            and provenance['training_manifest_sha256'] == receipt['training_manifest_sha256']
            and provenance['training_artifacts'] == receipt['training_artifacts']
            and provenance['plan_sha256'] == receipt['plan_sha256'], 'Head provenance differs from fit receipt')
    return receipt, head


def validate(plan_path, validation_manifest, fit_receipt, out, *, expected_head):
    from scripts.holder_learning import validation_report
    # Validate/freeze the fit before opening any validation labels.
    receipt, head = read_fit_receipt(fit_receipt, plan_path, expected_head=expected_head)
    rows, state = read_collection(validation_manifest, plan_path, 'validation')
    require(state['source'] == receipt['source'] and state['fit_receipt_sha256'] == digest(fit_receipt)
            and state['fitted_head_sha256'] == receipt['head_sha256']
            and state['training_manifest_sha256'] == receipt['training_manifest_sha256'], 'Validation was not bound to this frozen fit')
    plan, _, _ = validate_plan(plan_path, 'validation')
    out = _new_output(out)
    report = validation_report(head, rows, plan['validation_seeds'])
    report['provenance'] = dict(head_sha256=receipt['head_sha256'], fit_receipt_sha256=digest(fit_receipt),
                                validation_manifest_sha256=digest(validation_manifest), source=state['source'])
    write_json(out / 'validation_report.json', report)
    return report


def neutral_proof(plan_path, out, *, expected_head, usage_file, stop_file):
    from scripts.holder_learning import FEATURE_NAMES, validate_head
    plan, _, protocols = validate_plan(plan_path, 'train')
    head = validate_head(dict(schema_version=1, feature_version='holder_public_v1', feature_names=list(FEATURE_NAMES),
        eligibility_version='holder_eligibility_v1', cadence=dict(version='scored_opportunities_v1', max_opportunities=8,
        min_step_gap=12, reset='new_game'), horizon=12, mean=[0.]*16, scale=[1.]*16, coefficients=[0.]*16,
        intercept=0., ridge_alpha=0.1, threshold=1., baseline_sha256=V14_SHA,
        provenance={'purpose': 'neutral technical proof', 'baseline_sha256': V14_SHA}))
    keys = [dict(seed=seed, side=side, opponent='solution92') for seed, side in SMOKE_KEYS]
    return run_collection(ROOT / plan['weights'], out, selected=keys, all_keys=keys,
        frozen_inputs=[ROOT / plan['weights'], Path(plan_path).resolve()], source_plans=[*OLD_PLANS, *protocols],
        expected_head=expected_head, usage_file=usage_file, stop_file=stop_file, kind='holder_learning_neutral_proof',
        max_pairs=0, head=head, metadata=dict(neutral_head=head, baseline_sha256=V14_SHA, plan_sha256=digest(plan_path)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('collect', 'fit', 'validate', 'neutral-proof'):
        command = commands.add_parser(name)
        command.add_argument('--plan', type=Path, required=True)
        command.add_argument('--out', type=Path, required=True)
        command.add_argument('--expected-head', required=True)
        if name in ('collect', 'neutral-proof'):
            command.add_argument('--usage-file', type=Path, required=True)
            command.add_argument('--stop-file', type=Path, required=True)
        if name == 'collect':
            command.add_argument('--split', choices=('train', 'validation'), required=True)
            command.add_argument('--fit-receipt', type=Path)
        if name == 'fit': command.add_argument('--train-manifest', type=Path, required=True)
        if name == 'validate':
            command.add_argument('--validation-manifest', type=Path, required=True)
            command.add_argument('--fit-receipt', type=Path, required=True)
    args = vars(parser.parse_args(argv)); command = args.pop('command'); args['plan_path'] = args.pop('plan')
    {'collect': collect, 'fit': fit, 'validate': validate, 'neutral-proof': neutral_proof}[command](**args)


if __name__ == '__main__': main()
