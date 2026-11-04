"""Final-only A2 CONTROL/ANCHOR comparison through the original CONTROL trainer.

Each public arm owns an original prepared directory. Only its original control
arm runs; its unused sap0 initialization is explicitly outside this study.
The new-study completion marker is anchor_receipt.json, never the inner receipt.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from contextlib import contextmanager, ExitStack
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from torch import nn

from scripts import experiment, student_reward_train as engine
from scripts.student_action_distill import action_loss, load_datasets, teacher_scale, reserve_output

ARMS = ('control', 'anchor')
A2_SHA256 = '1baec85605e2b7aaad8c0beaa416d0489d2b9faa1362a9b361bbb63f04cc14bd'
TRAIN_ROWS, EXCLUDED_ROWS = 356415, 68687
DATASET_SHA256 = ('899fc77a7164b3cd1eba8fbf1f2472552a7483d9167463522a234e987618e2a0',
                  'c1f3cf232bc155c6b1018eabe701fee067cb13bf93a4ee0a085cc064a9a57df9')
FIXED_SCALE = 1.4293522257922757
WEIGHT, BATCH_SIZE, UPDATES = .1, 256, 24000
SAMPLER_SEED = 20261104


def _seed(seed):
    if type(seed) is not int or seed not in (25, 26):
        raise ValueError('run_seed must be integer 25 or 26')
    return seed


class AnchorData:
    """Only copied training rows are reachable from the sampling path."""
    def __init__(self, arrays, scale):
        train = np.asarray(arrays['is_train'])
        if (train.dtype != np.bool_ or train.ndim != 1 or not train.any()
                or not math.isfinite(scale) or scale < .001):
            raise ValueError('Anchor requires training rows and finite fixed scale')
        self.indices = np.flatnonzero(train).astype('<u4')
        self.s = torch.from_numpy(np.array(arrays['s'][train], dtype=np.float32, copy=True))
        self.teacher = torch.from_numpy(np.array(arrays['teacher_q'][train], dtype=np.float32, copy=True))
        self.mask = torch.from_numpy(np.array(arrays['mask'][train], dtype=bool, copy=True))
        if (self.s.shape != (len(self.indices), 79) or self.teacher.shape != (len(self.indices), 6)
                or self.mask.shape != self.teacher.shape or not self.mask.any(1).all()
                or not torch.isfinite(self.s).all() or not torch.isfinite(self.teacher).all()):
            raise ValueError('Invalid anchor tensor shapes, masks or values')
        self.scale = float(scale)

    def sample(self, rng, device):
        local = rng.integers(0, len(self.indices), size=BATCH_SIZE)
        return (self.s[local].to(device), self.teacher[local].to(device),
                self.mask[local].to(device), self.indices[local])


def _combined_learn(agent, data, rng, weight):
    """The original TD expressions and schedule, with one combined backward."""
    c = agent.cfg
    s, a, r, ns, done, nmask = agent.buffer.sample(c.batch_size, agent.rng)
    dev = agent.device
    s = torch.as_tensor(s, device=dev)
    ns = torch.as_tensor(ns, device=dev)
    a = torch.as_tensor(a, device=dev).unsqueeze(1)
    r = torch.as_tensor(r, device=dev).unsqueeze(1)
    done = torch.as_tensor(done, device=dev).unsqueeze(1)
    nmask = torch.as_tensor(nmask, device=dev)
    q = agent.q(s).gather(1, a)
    with torch.no_grad():
        next_online = agent.q(ns)
        next_online = next_online.masked_fill(~nmask, -float('inf'))
        if c.double_dqn:
            best = next_online.argmax(dim=1, keepdim=True)
            next_q = agent.target_q(ns).gather(1, best)
        else:
            next_q = agent.target_q(ns).masked_fill(~nmask, -float('inf')).max(dim=1, keepdim=True).values
        next_q = torch.nan_to_num(next_q, neginf=0.)
        y = r + (1. - done) * c.gamma * next_q
    td = nn.functional.smooth_l1_loss(q, y)
    features, teacher, mask, indices = data.sample(rng, dev)
    prediction = agent.q(features)
    gradient = []
    hook = prediction.register_hook(lambda grad: gradient.append(float(grad.norm().item())))
    try:
        anchor = action_loss(prediction, teacher, mask, data.scale)
        total = td + weight * anchor
        if not torch.isfinite(total):
            raise ValueError('Nonfinite combined training loss')
        agent.opt.zero_grad(set_to_none=True)
        total.backward()
        nn.utils.clip_grad_norm_(agent.q.parameters(), c.grad_clip)
        agent.opt.step()
    finally:
        hook.remove()
    agent.learn_steps += 1
    agent.recent_losses.append(float(total.item()))
    if len(agent.recent_losses) > 2000:
        agent.recent_losses = agent.recent_losses[-2000:]
    if agent.learn_steps % c.target_update_every == 0:
        agent.target_q.load_state_dict(agent.q.state_dict())
    if len(gradient) != 1:
        raise ValueError('Anchor branch did not participate in the shared backward')
    return dict(td_loss=float(td.item()), anchor_loss=float(anchor.item()),
                total_loss=float(total.item()), anchor_output_gradient_norm=gradient[0]), indices


@contextmanager
def attach_anchor(agent, data, run_seed, weight=WEIGHT, emit=lambda row, indices: None):
    """Restore the exact prior instance binding even when learning raises."""
    _seed(run_seed)
    if weight not in (0., WEIGHT) or type(weight) is bool:
        raise ValueError('Only the fixed zero/control and .1/anchor weights are allowed')
    rng = np.random.default_rng(SAMPLER_SEED + run_seed)
    missing = object()
    prior = vars(agent).get('_learn', missing)
    original = agent._learn
    proof = dict(updates=0, sample_count=0, weight=weight, positive_gradient_updates=0,
                 sampler_rng_sha256=experiment.state_sha256(rng.bit_generator.state),
                 td_loss_sum=0., anchor_loss_sum=0., total_loss_sum=0.)

    def learn():
        before = agent.learn_steps
        if weight == 0:
            # No extra forward, sample, RNG or arithmetic in the zero branch.
            original()
            loss = agent.recent_losses[-1]
            row = dict(td_loss=loss, anchor_loss=0., total_loss=loss,
                       anchor_output_gradient_norm=0.)
            indices = np.empty(0, dtype='<u4')
        else:
            row, indices = _combined_learn(agent, data, rng, weight)
        if agent.learn_steps != before + 1:
            raise ValueError('A combined update must advance the original counter once')
        proof['updates'] += 1
        proof['sample_count'] += len(indices)
        proof['positive_gradient_updates'] += int(row['anchor_output_gradient_norm'] > 0)
        proof['sampler_rng_sha256'] = experiment.state_sha256(rng.bit_generator.state)
        for name in ('td_loss', 'anchor_loss', 'total_loss'):
            proof[name + '_sum'] += row[name]
        emit(dict(row, update=proof['updates'], learn_steps=agent.learn_steps,
                  optimizer_steps=1, sample_count=len(indices), split='train',
                  sample_sha256=hashlib.sha256(indices.tobytes()).hexdigest()), indices)

    agent._learn = learn
    try:
        yield proof
    finally:
        if prior is missing:
            vars(agent).pop('_learn', None)
        else:
            agent._learn = prior


@contextmanager
def prefill_replay_audit(agent):
    """Hash actual prefill arrays once, before the first learning-phase push."""
    buffer = agent.buffer
    missing = object()
    prior = vars(buffer).get('push', missing)
    original = buffer.push
    proof = {}

    def push(*args, **kwargs):
        if agent.learn_enabled and not proof:
            proof.update(size=buffer.size, pos=buffer.pos,
                content_sha256=experiment.state_sha256({name: getattr(buffer, name)[:buffer.size]
                    for name in ('s', 'a', 'r', 'ns', 'done', 'mask')}))
        return original(*args, **kwargs)
    buffer.push = push
    try:
        yield proof
    finally:
        if prior is missing:
            vars(buffer).pop('push', None)
        else:
            buffer.push = prior


def prepare(student, datasets, out, run_seed):
    _seed(run_seed)
    student = Path(student).resolve(strict=True)
    if engine.file_sha256(student) != A2_SHA256:
        raise ValueError('Starting checkpoint must be pinned A2')
    engine._student(student)
    contract, _ = _datasets(datasets)
    pins = _pins()
    out = engine._output(out)
    if any(out.is_relative_to(Path(path).resolve()) for path in datasets):
        raise ValueError('Output must be outside every input dataset directory')
    out = reserve_output(out, [student, *map(Path, datasets)])
    manifest = dict(schema_version=1, study='a2_teacher_anchor_20261104',
                    prepared=str(out), run_seed=run_seed, student=str(student),
                    student_sha256=A2_SHA256, pins=pins, dataset_contract=contract,
                    objective='original_TD + weight * existing_masked_centered_action_loss',
                    sampler_seed=SAMPLER_SEED + run_seed, batch_size=BATCH_SIZE,
                    expected_updates=UPDATES, arms={})
    for arm in ARMS:
        nested = out / 'engine' / arm
        original = engine.prepare(student, nested, run_seed=run_seed)
        manifest['arms'][arm] = _arm_entry(nested, original, arm)
    if _pins() != pins or engine.file_sha256(student) != A2_SHA256:
        raise ValueError('Sources or starting checkpoint changed during preparation')
    contract_after, _ = _datasets(datasets)
    if contract_after != contract:
        raise ValueError('Dataset changed during preparation')
    engine._write(out / 'manifest.json', manifest)
    return manifest


def _pins():
    result = engine._pins()
    for name in ('scripts/student_anchor_train.py', 'scripts/student_action_distill.py',
                 'scripts/student_distill.py', 'scripts/output_paths.py'):
        result['code'][name] = engine.file_sha256(engine.ROOT / name)
    return result


def _datasets(paths):
    paths = [Path(p).resolve(strict=True) for p in paths]
    if len(paths) != 2:
        raise ValueError('Exactly collection rounds r1/r2 in fixed order are required')
    hashes = tuple(engine.file_sha256(p / 'dataset.npz') for p in paths)
    if hashes != DATASET_SHA256:
        raise ValueError('Dataset hashes differ from the two fixed teacher collections')
    arrays, _ = load_datasets(paths)
    count = int(arrays['is_train'].sum())
    scale = teacher_scale(arrays['teacher_q'], arrays['mask'], arrays['is_train'])
    if (count != TRAIN_ROWS or len(arrays['s']) - count != EXCLUDED_ROWS
            or not math.isclose(scale, FIXED_SCALE, rel_tol=0., abs_tol=1e-12)):
        raise ValueError('Dataset row/split/scale contract differs from A2 training')
    data = AnchorData(arrays, scale)
    contract = dict(datasets=[dict(path=str(p), files_sha256={
        name: engine.file_sha256(p / name) for name in
        ('manifest.json', 'status.json', 'dataset.npz', 'games.jsonl')}) for p in paths],
        train_rows=count, excluded_rows=len(arrays['s']) - count, scale=scale,
        train_indices_sha256=hashlib.sha256(data.indices.tobytes()).hexdigest(),
        sample_index_format='little-endian uint32 indices in concatenated r1/r2 rows')
    return contract, data


def _arm_entry(nested, original, arm):
    return dict(engine_prepared=str(nested), engine_arm='control',
                excluded_engine_arms=['sap0'], weight=0. if arm == 'control' else WEIGHT,
                engine_manifest_sha256=engine.file_sha256(nested / 'manifest.json'),
                config=original['arms']['control']['config'],
                rollout_plan=original['arms']['control']['rollout_plan'],
                initial_tensor_sha256=original['arms']['control']['tensor_sha256'])


def check_prepared(prepared, arm):
    if arm not in ARMS:
        raise ValueError('Unknown public study arm')
    prepared = engine._output(Path(prepared).resolve(strict=True))
    manifest = json.loads((prepared / 'manifest.json').read_text())
    seed = _seed(manifest['run_seed'])
    if (manifest['schema_version'] != 1 or manifest['study'] != 'a2_teacher_anchor_20261104'
            or manifest['prepared'] != str(prepared) or manifest['student_sha256'] != A2_SHA256
            or engine.file_sha256(Path(manifest['student'])) != A2_SHA256
            or manifest['pins'] != _pins() or set(manifest['arms']) != set(ARMS)
            or manifest['sampler_seed'] != SAMPLER_SEED + seed
            or manifest['batch_size'] != BATCH_SIZE or manifest['expected_updates'] != UPDATES
            or manifest['objective'] != 'original_TD + weight * existing_masked_centered_action_loss'):
        raise ValueError('Prepared source/model/config contract changed')
    contract, data = _datasets([p['path'] for p in manifest['dataset_contract']['datasets']])
    if contract != manifest['dataset_contract']:
        raise ValueError('Prepared dataset contract changed')
    for public in ARMS:
        nested = prepared / 'engine' / public
        if not nested.resolve().is_relative_to(prepared):
            raise ValueError('Engine directory alias escapes prepared directory')
        original, _, _ = engine.check_prepared(nested, 'control')
        if (original['run_seed'] != seed or original['student'] != manifest['student']
                or manifest['arms'][public] != _arm_entry(nested, original, public)):
            raise ValueError('Public arm differs from pinned original CONTROL engine')
    if manifest['arms']['control']['config'] != manifest['arms']['anchor']['config']:
        raise ValueError('Matched control/anchor configs differ')
    return manifest, manifest['arms'][arm], data


def _audit_directory(prepared, arm):
    root = Path(prepared).resolve()
    result = engine._output(root / 'audits' / arm)
    if not result.is_relative_to(root):
        raise ValueError('Audit directory alias escapes prepared directory')
    return result


def run_arm(prepared, arm, deadline_utc):
    from scripts import finetune
    manifest, entry, data = check_prepared(prepared, arm)
    prepared = Path(prepared).resolve()
    deadline = engine._deadline(deadline_utc)
    audit_dir = _audit_directory(prepared, arm)
    if audit_dir.exists():
        raise FileExistsError(audit_dir)
    audit_dir.mkdir(parents=True)
    status = dict(status='running', arm=arm, run_seed=manifest['run_seed'],
                  started_utc=datetime.now(timezone.utc).isoformat())
    engine._write(audit_dir / 'status.json', status)
    original = finetune.Learners
    instances, proofs, prefill_proofs = [], [], []
    stack = ExitStack()
    try:
        engine._check_deadline(deadline)
        with (audit_dir / 'updates.jsonl').open('x') as metrics, (audit_dir / 'samples.u32').open('xb') as samples:
            def emit(row, indices):
                engine._check_deadline(deadline)
                samples.write(indices.astype('<u4', copy=False).tobytes())
                metrics.write(json.dumps(row, allow_nan=False) + '\n')

            def learners(*args, **kwargs):
                if instances:
                    raise ValueError('Unexpected second learner construction')
                result = original(*args, **kwargs)
                a = result.agents['player_0']
                if result.agents['player_1'] is not a:
                    raise ValueError('Anchor study requires one shared learner')
                instances.append(a)
                prefill_proofs.append(stack.enter_context(prefill_replay_audit(a)))
                proofs.append(stack.enter_context(attach_anchor(
                    a, data, manifest['run_seed'], entry['weight'], emit)))
                return result

            finetune.Learners = learners
            try:
                engine.run_arm(Path(entry['engine_prepared']), 'control', deadline)
            finally:
                finetune.Learners = original
                stack.close()
            if (len(proofs) != 1 or any('_learn' in vars(a) or 'push' in vars(a.buffer) for a in instances)
                    or len(prefill_proofs) != 1 or not prefill_proofs[0]):
                raise ValueError('Learner adapter did not fully restore its instance bindings')
        engine._check_deadline(deadline)
        check_prepared(prepared, arm)
        engine._write(audit_dir / 'summary.json', proofs[0])
        engine._write(audit_dir / 'prefill_replay.json', prefill_proofs[0])
        # Inner receipt verifies all original training audits, not the public
        # intervention. Only the outer marker below accepts the complete study.
        inner = engine.validate_receipt(Path(entry['engine_prepared']) / 'runs/control')
        _validate_updates(audit_dir, manifest, entry, data)
        receipt = dict(schema_version=1, status='done', arm=arm, run_seed=manifest['run_seed'],
                       prepared=str(prepared), weight=entry['weight'],
                       manifest_sha256=engine.file_sha256(prepared / 'manifest.json'),
                       checkpoint_sha256=inner['final_checkpoint_sha256'],
                       final_checkpoint=inner['final_checkpoint'],
                       inner_receipt_sha256=engine.file_sha256(Path(entry['engine_prepared']) / 'runs/control/final_receipt.json'),
                       evidence_sha256={name: engine.file_sha256(audit_dir / name) for name in
                                        ('updates.jsonl', 'samples.u32', 'summary.json', 'prefill_replay.json')},
                       adapter_restored=True, constructor_restored=finetune.Learners is original)
        status.update(status='done', finished_utc=datetime.now(timezone.utc).isoformat())
        engine._write(audit_dir / 'status.json', status)
        _validate_completed(prepared, arm, receipt)
        engine._write(audit_dir / 'anchor_receipt.json', receipt)
        if all((_audit_directory(prepared, name) / 'anchor_receipt.json').exists() for name in ARMS):
            compare_prefill(prepared)
        return receipt
    except BaseException as exc:
        finetune.Learners = original
        try:
            stack.close()
        finally:
            (audit_dir / 'anchor_receipt.json').unlink(missing_ok=True)
            status.update(status='incomplete', error=f'{type(exc).__name__}: {exc}',
                          finished_utc=datetime.now(timezone.utc).isoformat())
            engine._write(audit_dir / 'status.json', status)
        raise


def validate(prepared, arm):
    audit_dir = _audit_directory(prepared, arm)
    if not (audit_dir / 'anchor_receipt.json').exists():
        raise ValueError('Incomplete public study arm; no anchor receipt')
    try:
        receipt = json.loads((audit_dir / 'anchor_receipt.json').read_text())
        return _validate_completed(prepared, arm, receipt)
    except (OSError, KeyError, TypeError, IndexError) as exc:
        raise ValueError('Incomplete or malformed public arm evidence') from exc


def _validate_completed(prepared, arm, receipt):
    """Validate the proposed receipt before its atomic publication."""
    audit_dir = _audit_directory(prepared, arm)
    try:
        manifest, entry, data = check_prepared(prepared, arm)
        prepared = Path(prepared).resolve()
        status = json.loads((audit_dir / 'status.json').read_text())
        nested_run = Path(entry['engine_prepared']) / 'runs/control'
        inner = engine.validate_receipt(nested_run)
        if (status['status'] != 'done' or status['arm'] != arm
                or type(status['run_seed']) is not int or status['run_seed'] != manifest['run_seed']
                or receipt['schema_version'] != 1 or receipt['status'] != 'done'
                or receipt['arm'] != arm or type(receipt['run_seed']) is not int
                or receipt['run_seed'] != manifest['run_seed'] or receipt['prepared'] != str(prepared)
                or receipt['weight'] != entry['weight'] or receipt['adapter_restored'] is not True
                or receipt['constructor_restored'] is not True
                or receipt['manifest_sha256'] != engine.file_sha256(prepared / 'manifest.json')
                or receipt['inner_receipt_sha256'] != engine.file_sha256(nested_run / 'final_receipt.json')
                or receipt['checkpoint_sha256'] != inner['final_checkpoint_sha256']
                or receipt['final_checkpoint'] != inner['final_checkpoint']
                or set(receipt['evidence_sha256']) != {'updates.jsonl', 'samples.u32', 'summary.json', 'prefill_replay.json'}
                or any(engine.file_sha256(audit_dir / name) != digest
                       for name, digest in receipt['evidence_sha256'].items())):
            raise ValueError('Public completion receipt contract/hash/config differs')
        updates = _validate_updates(audit_dir, manifest, entry, data)
        prefill = json.loads((audit_dir / 'prefill_replay.json').read_text())
        inner_audit = json.loads((nested_run / 'training_audit.json').read_text())
        replay = inner_audit['prefill']['learning']['replay']
        if (prefill['size'] != replay['size'] or prefill['pos'] != replay['pos']
                or not isinstance(prefill['content_sha256'], str) or len(prefill['content_sha256']) != 64):
            raise ValueError('Actual prefill replay evidence differs from original audit')
        with (nested_run / 'train.csv').open() as handle:
            games = list(csv.DictReader(handle))
        if len(games) != 160 or len(updates) != 24000:
            raise ValueError('Actual game/update budgets differ')
        for index, game in enumerate(games):
            actual = float(np.mean([r['total_loss'] for r in updates[index*150:(index+1)*150]]))
            # finetune serializes round(agent.pop_mean_loss(), 5). Recreate
            # that quantization before comparing the independently audited mean.
            if float(game['mean_loss']) != round(actual, 5):
                raise ValueError('Actual combined losses differ from original training CSV')
        return receipt
    except (OSError, KeyError, TypeError, IndexError) as exc:
        raise ValueError('Incomplete or malformed public arm evidence') from exc


def _validate_updates(audit_dir, manifest, entry, data):
    """Recreate every random draw; bind observed losses to one real backward."""
    audit_dir = Path(audit_dir)
    summary = json.loads((audit_dir / 'summary.json').read_text())
    rows = [json.loads(line) for line in (audit_dir / 'updates.jsonl').read_text().splitlines()]
    weight = entry['weight']
    count = BATCH_SIZE if weight else 0
    if len(rows) != UPDATES or (audit_dir / 'samples.u32').stat().st_size != UPDATES * count * 4:
        raise ValueError('Actual update/sample count evidence incomplete')
    rng = np.random.default_rng(SAMPLER_SEED + _seed(manifest['run_seed']))
    sums = dict(td_loss_sum=0., anchor_loss_sum=0., total_loss_sum=0.)
    gradients = 0
    with (audit_dir / 'samples.u32').open('rb') as samples:
        for index, row in enumerate(rows):
            raw = samples.read(count * 4)
            selected = np.frombuffer(raw, dtype='<u4')
            expected = data.indices[rng.integers(0, len(data.indices), size=count)] if count else np.empty(0, '<u4')
            if (type(row['update']) is not int or row['update'] != index + 1
                    or type(row['learn_steps']) is not int or row['learn_steps'] != index + 1
                    or row['optimizer_steps'] != 1 or row['sample_count'] != count or row['split'] != 'train'
                    or row['sample_sha256'] != hashlib.sha256(raw).hexdigest()
                    or not np.array_equal(selected, expected)):
                raise ValueError('Actual update/training sample evidence differs from independent RNG')
            values = [row[name] for name in ('td_loss', 'anchor_loss', 'total_loss', 'anchor_output_gradient_norm')]
            if (not all(type(value) in (float, int) and math.isfinite(value) and value >= -1e-6 for value in values)
                    or not math.isclose(row['total_loss'], row['td_loss'] + weight * row['anchor_loss'], rel_tol=2e-7, abs_tol=1e-6)
                    or (not weight and (row['anchor_loss'] != 0. or row['anchor_output_gradient_norm'] != 0.))):
                raise ValueError('Actual TD/anchor/total loss evidence differs')
            gradients += int(row['anchor_output_gradient_norm'] > 0)
            for name in ('td_loss', 'anchor_loss', 'total_loss'):
                sums[name + '_sum'] += row[name]
    expected = dict(updates=UPDATES, sample_count=UPDATES * count, weight=weight,
                    positive_gradient_updates=gradients,
                    sampler_rng_sha256=experiment.state_sha256(rng.bit_generator.state), **sums)
    if (summary != expected or (weight and (gradients == 0 or sums['anchor_loss_sum'] <= 0))):
        raise ValueError('Anchor was inactive or actual update/loss/RNG summary evidence differs')
    return rows


def compare_prefill(prepared):
    """Both arms use identical scalar rewards, actions, replay and learner RNG."""
    for arm in ARMS:
        validate(prepared, arm)
    projections = []
    for arm in ARMS:
        nested = Path(prepared) / 'engine' / arm / 'runs/control'
        rows = [json.loads(line) for line in (nested / 'rollouts.jsonl').read_text().splitlines()][:40]
        projections.append(dict(replay=json.loads((_audit_directory(prepared, arm) / 'prefill_replay.json').read_text()),
            rows=[dict(plan={k: row[k] for k in ('phase', 'game', 'seed', 'side', 'opponent')},
                                 actions=row['final_action_audit'], policy=row['policy_transcript'],
                                 reward=row['reward_audit'], identity=row['identity']) for row in rows]))
    if len(projections[0]['rows']) != 40 or projections[0] != projections[1]:
        raise ValueError('Paired prefill config/actions/rewards/replay/RNG differ')
    result = dict(status='matched', prefill_games=40,
                  prefill_sha256=experiment.state_sha256(projections[0]),
                  receipts_sha256=[engine.file_sha256(_audit_directory(prepared, arm) / 'anchor_receipt.json') for arm in ARMS])
    engine._write(Path(prepared) / 'paired_prefill.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Use python -m scripts.student_anchor_train prepare --student A2.pth --datasets r1 r2 --out NEW_DIR --run-seed 25\n'
               'then run --prepared NEW_DIR --arm control|anchor --deadline-utc 2026-11-04T21:00:00Z;\n'
               'validate --prepared NEW_DIR --arm control|anchor is read-only. Repeat in a new directory for seed 26.\n'
               'Only audits/ARM/anchor_receipt.json marks public-arm completion; engine SAP0 arms never run.')
    sub = parser.add_subparsers(dest='command', required=True)
    prepare_parser = sub.add_parser('prepare', help='Prepare pinned A2/datasets and matched original CONTROL configs')
    prepare_parser.add_argument('--student', type=Path, required=True)
    prepare_parser.add_argument('--datasets', nargs='+', type=Path, required=True)
    prepare_parser.add_argument('--out', type=Path, required=True)
    prepare_parser.add_argument('--run-seed', type=int, choices=(25, 26), required=True)
    for command in ('run', 'validate'):
        p = sub.add_parser(command, help='Run fixed final-only training' if command == 'run' else 'Read-only completion/provenance check')
        p.add_argument('--prepared', type=Path, required=True)
        p.add_argument('--arm', choices=ARMS, required=True)
        if command == 'run':
            p.add_argument('--deadline-utc', required=True)
    args = parser.parse_args(argv)
    experiment.limit_threads()
    if args.command == 'prepare':
        result = prepare(args.student, args.datasets, args.out, args.run_seed)
    elif args.command == 'run':
        result = run_arm(args.prepared, args.arm, args.deadline_utc)
    else:
        result = validate(args.prepared, args.arm)
    print(json.dumps(dict(command=args.command, status=result.get('status', 'prepared')), allow_nan=False))


if __name__ == '__main__':
    main()
