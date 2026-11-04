"""Masked decision fitting followed by value-only Q-unit calibration.

Only complete 30+5 epoch runs export a final single-network checkpoint. Recorded
collector final actions describe the collecting policy, never a replay of this fit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import torch

from scripts.student_distill import (ROOT, SEED, BATCH_SIZE, LEARNING_RATE,
                                    V14_SHA256, _finite, _write, sha256,
                                    reserve_output as _reserve_output)
from scripts.output_paths import checked_output
from agents.sherlock.model import QNet

ACTION_EPOCHS = 30
VALUE_EPOCHS = 5
SCALE_FLOOR = .001
ARRAY_SCHEMA = {
    's': (np.dtype('float32'), (79,)), 'mask': (np.dtype('bool'), (6,)),
    'teacher_q': (np.dtype('float32'), (6,)), 'student_q': (np.dtype('float32'), (6,)),
    'final_action': (np.dtype('int8'), ()), 'world_action': (np.dtype('int16'), (3,)),
    'game_index': (np.dtype('int32'), ()), 'env_seed': (np.dtype('int64'), ()),
    'side': (np.dtype('int8'), ()), 'env_step': (np.dtype('int16'), ()),
    'match_step': (np.dtype('int16'), ()), 'uid': (np.dtype('int8'), ()),
    'is_train': (np.dtype('bool'), ()),
}
SOURCE_FILES = [Path(__file__).resolve(), *(ROOT / name for name in (
    'scripts/student_distill.py', 'scripts/student_reward_train.py', 'scripts/output_paths.py',
    'agents/sherlock/model.py', 'agents/sherlock/config.py', 'agents/sherlock/main.py'))]


def reserve_output(out, inputs):
    # Match the collector's packaged-submission boundary without importing its
    # implementation. The stable helper retains all raw-weight/input guards.
    for base in (ROOT, Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15'),
                 Path('/Users/moayedshawesh/Desktop/KI/sherlock-november-followup')):
        protected = base / 'agents/Gruppe15'
        checked_output(out, protected)
        if protected.resolve().is_relative_to(Path(out).expanduser().resolve()):
            raise ValueError('Output must not contain protected submission directory')
    return _reserve_output(out, inputs)


def _validate_q(prediction, target, mask):
    if (not isinstance(prediction, torch.Tensor) or not isinstance(target, torch.Tensor)
            or not isinstance(mask, torch.Tensor) or prediction.shape != target.shape
            or prediction.ndim != 2 or prediction.shape[1] != 6 or not len(prediction)
            or mask.shape != prediction.shape or mask.dtype != torch.bool
            or not prediction.is_floating_point() or not target.is_floating_point()
            or not torch.isfinite(prediction).all() or not torch.isfinite(target).all()
            or not mask.any(dim=1).all()):
        raise ValueError('Require finite nonempty six-action Q matrices and nonempty bool masks')


def _center(q, mask):
    legal = q.masked_fill(~mask, 0)
    mean = legal.sum(dim=1, keepdim=True) / mask.sum(dim=1, keepdim=True)
    return (legal - mean).masked_fill(~mask, 0)


def action_loss(prediction, target, mask, scale):
    """Mean per-row legal centered MSE/scale² plus KL(teacher || student)."""
    _validate_q(prediction, target, mask)
    if not np.isfinite(scale) or scale < SCALE_FLOOR:
        raise ValueError('Scale must be a finite scalar at least .001')
    target = target.detach()
    student = _center(prediction, mask) / scale
    teacher = _center(target, mask) / scale
    mse = (student - teacher).square().sum(1) / mask.sum(1)
    log_student = torch.log_softmax(student.masked_fill(~mask, -torch.inf), dim=1)
    log_teacher = torch.log_softmax(teacher.masked_fill(~mask, -torch.inf), dim=1)
    difference = log_teacher.masked_fill(~mask, 0) - log_student.masked_fill(~mask, 0)
    kl = (log_teacher.exp() * difference).sum(1)
    return (mse + kl).mean()


def teacher_scale(target, mask, is_train):
    """One global RMS of legal-centered teacher train Q; never fit diagnostics."""
    target = torch.as_tensor(target, dtype=torch.float64)
    mask = torch.as_tensor(mask)
    _validate_q(target, target, mask)
    train = np.asarray(is_train)
    if train.dtype != np.bool_ or train.shape != (len(target),) or not train.any():
        raise ValueError('Scale requires a nonempty bool train split')
    selected = torch.from_numpy(train)
    centered = _center(target[selected], mask[selected])
    return max(SCALE_FLOOR, float(torch.sqrt(centered.square().sum() / mask[selected].sum())))


def action_metrics(prediction, target, mask, final_action, collector_q):
    prediction = torch.as_tensor(prediction, dtype=torch.float64)
    target = torch.as_tensor(target, dtype=torch.float64)
    mask = torch.as_tensor(mask)
    collector = torch.as_tensor(collector_q, dtype=torch.float64)
    _validate_q(prediction, target, mask)
    _validate_q(collector, target, mask)
    final = torch.as_tensor(final_action).long()
    if final.shape != (len(target),) or not ((final >= 0) & (final < 6)).all():
        raise ValueError('Recorded final actions must lie in 0..5')
    choices = prediction.masked_fill(~mask, -torch.inf).argmax(1)
    best = target.masked_fill(~mask, -torch.inf).argmax(1)
    collecting_choices = collector.masked_fill(~mask, -torch.inf).argmax(1)
    row = torch.arange(len(target))
    delta = (prediction - target).masked_fill(~mask, 0)
    centered = _center(prediction, mask) - _center(target, mask)
    mean_delta = delta.sum(1) / mask.sum(1)
    return dict(rows=len(target), masked_argmax_agreement=float((choices == best).double().mean()),
                legal_regret=float((target[row, best] - target[row, choices]).mean()),
                legal_q_mse=float((delta.square().sum(1) / mask.sum(1)).mean()),
                centered_legal_q_mse=float((centered.square().sum(1) / mask.sum(1)).mean()),
                legal_mean_q_mse=float(mean_delta.square().mean()),
                recorded_collector_rule_override_rate=float((final != collecting_choices).double().mean()),
                recorded_collector_final_outside_mask_rate=float((~mask[row, final]).double().mean()))


def _read_object(path):
    value = json.loads(Path(path).read_text())
    if not isinstance(value, dict):
        raise ValueError(f'Expected metadata object: {path}')
    return value


def load_datasets(paths, check=lambda: None):
    """Validate completed collector packages without importing collector internals."""
    paths = [Path(path).resolve() for path in paths]
    if not paths or len(set(paths)) != len(paths):
        raise ValueError('Require distinct completed dataset directories')
    parts, metadata, seed_split = [], [], {}
    for path in paths:
        check()
        manifest = _read_object(path / 'manifest.json')
        status = _read_object(path / 'status.json')
        if (type(manifest.get('schema_version')) is not int or manifest['schema_version'] != 1
                or manifest.get('status') != 'done' or status.get('status') != 'done'):
            raise ValueError('Dataset manifest and status must be complete (done), schema 1')
        if (manifest.get('teacher_sha256') != V14_SHA256
                or type(manifest.get('teacher_members')) is not int or manifest['teacher_members'] != 36):
            raise ValueError('Dataset teacher must be pinned V14 with exactly 36 members')
        digest = manifest.get('student_sha256')
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Dataset student SHA256 missing or malformed')
        expected = manifest.get('files_sha256')
        if not isinstance(expected, dict) or set(expected) != {'dataset.npz', 'games.jsonl'}:
            raise ValueError('Dataset requires exact dataset/games hashes')
        for name in expected:
            check()
            if sha256(path / name) != expected[name]:
                raise ValueError(f'Dataset file hash mismatch: {name}')
        with np.load(path / 'dataset.npz', allow_pickle=False) as archive:
            if set(archive.files) != set(ARRAY_SCHEMA):
                raise ValueError('Dataset array columns do not match schema')
            arrays = {name: np.ascontiguousarray(archive[name]) for name in ARRAY_SCHEMA}
        rows = len(arrays['s'])
        if type(manifest.get('rows')) is not int or manifest['rows'] != rows or not rows:
            raise ValueError('Dataset row count must be positive and agree with manifest')
        for name, (dtype, dimensions) in ARRAY_SCHEMA.items():
            check()
            if arrays[name].dtype != dtype or arrays[name].shape != (rows, *dimensions):
                raise ValueError(f'Dataset shape/dtype invalid: {name}')
            if not np.isfinite(arrays[name]).all():
                raise ValueError(f'Dataset contains nonfinite values: {name}')
        if (not arrays['mask'].any(1).all()
                or not ((arrays['final_action'] >= 0) & (arrays['final_action'] < 6)).all()
                or not ((arrays['side'] >= 0) & (arrays['side'] <= 1)).all()
                or not ((arrays['uid'] >= 0) & (arrays['uid'] < 16)).all()
                or (arrays['env_step'] < 0).any() or (arrays['match_step'] < 0).any()):
            raise ValueError('Dataset has invalid masks, actions, side, uid or step identifiers')
        row_ids = np.column_stack([arrays[name] for name in ('game_index', 'env_step', 'uid')])
        if len(np.unique(row_ids, axis=0)) != rows:
            raise ValueError('Dataset contains duplicate game/step/unit row identifiers')
        plan = manifest.get('game_plan')
        if not isinstance(plan, list) or not plan:
            raise ValueError('Dataset game_plan must be a nonempty list')
        seen, sides, local_split = set(), {}, {}
        for game in plan:
            check()
            if (not isinstance(game, dict)
                    or any(type(game.get(key)) is not int for key in ('game_index', 'env_seed', 'side'))
                    or type(game.get('is_train')) is not bool or game['side'] not in (0, 1)
                    or game.get('side_name') != f"player_{game['side']}"
                    or not isinstance(game.get('opponent'), str) or not game['opponent']):
                raise ValueError('Dataset game_plan has malformed identifiers or split')
            game_index, seed, side, train = (game[key] for key in ('game_index', 'env_seed', 'side', 'is_train'))
            if game_index in seen or (seed, side) in sides:
                raise ValueError('Dataset duplicate game index or seed/side')
            seen.add(game_index)
            sides[seed, side] = game
            if seed in local_split and local_split[seed] != train:
                raise ValueError('Dataset split must hold out whole seeds across sides')
            if seed in seed_split and seed_split[seed] != train:
                raise ValueError('Dataset split conflicts across collection rounds')
            local_split[seed] = seed_split[seed] = train
            selected = arrays['game_index'] == game_index
            for column, expected_value in (('env_seed', seed), ('side', side), ('is_train', train)):
                if not np.all(arrays[column][selected] == expected_value):
                    raise ValueError(f'Dataset rows disagree with game_plan {column}/split')
        if seen != set(range(len(plan))) or not set(arrays['game_index']).issubset(seen):
            raise ValueError('Dataset game indices must cover the full contiguous plan')
        if any((seed, side) not in sides for seed in local_split for side in (0, 1)):
            raise ValueError('Dataset plan requires both sides of every complete seed')
        if not arrays['is_train'].any() or arrays['is_train'].all():
            raise ValueError('Dataset needs nonempty train and diagnostic splits')
        parts.append(arrays)
        metadata.append(dict(path=str(path), **manifest))
    return {name: np.concatenate([part[name] for part in parts]) for name in ARRAY_SCHEMA}, metadata


@torch.no_grad()
def _predict(net, rows, check):
    net.eval()
    prediction = np.empty((len(rows), 6), np.float32)
    for start in range(0, len(rows), BATCH_SIZE):
        check()
        value = net(torch.from_numpy(rows[start:start + BATCH_SIZE]))
        _finite(value)
        prediction[start:start + BATCH_SIZE] = value.numpy()
    return prediction


def _metrics(prediction, arrays):
    return {label: action_metrics(prediction[select], arrays['teacher_q'][select],
                                  arrays['mask'][select], arrays['final_action'][select],
                                  arrays['student_q'][select])
            for label, select in (('train', arrays['is_train']), ('diagnostic', ~arrays['is_train']))}


def _calibration_checks(net, frozen_state, before, after, mask):
    unchanged = all(torch.equal(net.state_dict()[key], value) for key, value in frozen_state.items())
    # A shared value changes no exact real-number rank. Float32 addition/subtraction
    # can flip numerical near-ties; count every non-tie pair separately.
    tolerance = 8 * np.finfo(np.float32).eps * np.maximum(1., np.maximum(abs(before), abs(after)).max(1))
    first = before.astype(np.float64)[:, :, None] - before.astype(np.float64)[:, None, :]
    second = after.astype(np.float64)[:, :, None] - after.astype(np.float64)[:, None, :]
    legal_pairs = mask[:, :, None] & mask[:, None, :] & np.triu(np.ones((6, 6), bool), 1)
    flips = legal_pairs & (np.sign(first) != np.sign(second))
    non_tie = (abs(first) > tolerance[:, None, None]) & (abs(second) > tolerance[:, None, None])
    result = dict(body_adv_unchanged=unchanged,
                  non_tie_pair_rank_changes=int((flips & non_tie).sum()),
                  numerical_near_tie_pair_rank_changes=int((flips & ~non_tie).sum()),
                  rank_tolerance='8*float32_eps*max(1, abs(Q_before), abs(Q_after)) per row')
    if not unchanged or result['non_tie_pair_rank_changes']:
        raise ValueError('Value calibration changed frozen body/adv or non-tie legal action ranking')
    return result


def run_distillation(student, datasets, out, deadline):
    """Fit exactly 30 action epochs plus 5 value-only epochs from S30/A1."""
    from scripts.student_reward_train import _student, _protected_hashes
    if not isinstance(deadline, datetime) or deadline.tzinfo is None:
        raise ValueError('Deadline must be a datetime with a UTC offset')
    student = Path(student).resolve()
    directories = [Path(path).resolve() for path in datasets]
    if any(Path(out).resolve().is_relative_to(directory) for directory in directories):
        raise ValueError('Output must not be inside an input dataset')
    inputs = [student, *[directory / name for directory in directories
                        for name in ('manifest.json', 'status.json', 'dataset.npz', 'games.jsonl')]]
    out = reserve_output(Path(out), inputs)
    started = time.monotonic()
    final, pending = out / 'weights/agent.pth', out / 'weights/agent.pending.pth'
    manifest = dict(status='running', seed=SEED, action_epochs_requested=ACTION_EPOCHS,
                    value_epochs_requested=VALUE_EPOCHS, action_epochs_completed=0,
                    value_epochs_completed=0, action_updates=0, value_updates=0, updates=0,
                    training_rows_seen=0, batch_size=BATCH_SIZE, learning_rate=LEARNING_RATE,
                    deadline_utc=deadline.astimezone(timezone.utc).isoformat(), cpu_threads=1,
                    started_utc=datetime.now(timezone.utc).isoformat())
    previous_determinism = torch.are_deterministic_algorithms_enabled()
    previous_warn = torch.is_deterministic_algorithms_warn_only_enabled()

    def check():
        if datetime.now(timezone.utc) >= deadline:
            raise TimeoutError('Fixed deadline reached; incomplete phases cannot export a final checkpoint')

    def progress(phase):
        manifest['phase'] = phase
        manifest['wall_seconds'] = time.monotonic() - started
        _write(out / 'status.json', manifest)

    def hashes(paths):
        return {str(path): sha256(path) for path in paths}

    try:
        progress('validation')
        check()
        torch.set_num_threads(1)
        manifest['inputs_before'] = hashes(inputs)
        manifest['sources_before'] = hashes(SOURCE_FILES)
        manifest['protected_before'] = _protected_hashes()
        manifest['starting_student_sha256'] = sha256(student)
        manifest['runtime'] = dict(python_executable=sys.executable, python_version=platform.python_version(),
                                   torch_version=str(torch.__version__), numpy_version=np.__version__,
                                   git_head=subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                                           check=True, capture_output=True, text=True).stdout.strip())
        checkpoint = _student(student)
        if not checkpoint['cfg']['dueling']:
            raise ValueError('Student must use the fixed dueling architecture')
        arrays, metadata = load_datasets(directories, check)
        if metadata[-1]['student_sha256'] != manifest['starting_student_sha256']:
            raise ValueError('Latest dataset collecting student differs from the supplied starting student')
        manifest['datasets'] = metadata
        manifest['teacher_sha256'] = V14_SHA256
        manifest['teacher_members'] = 36
        manifest['scale'] = teacher_scale(arrays['teacher_q'], arrays['mask'], arrays['is_train'])
        manifest['objective'] = dict(action='mean_rows(mean_legal((center_legal(Q)-center_legal(T))^2)/scale^2 + KL(softmax_legal(T/scale)||softmax_legal(Q/scale)))',
                                     scale='One global RMS over legal-centered teacher entries on train rows only',
                                     scale_floor=SCALE_FLOOR,
                                     calibration='mean_rows((mean_legal(Q)-mean_legal(T))^2), value head only')
        manifest['split'] = {label: sorted(set(arrays['env_seed'][select].tolist()))
                             for label, select in (('train_seeds', arrays['is_train']),
                                                   ('diagnostic_seeds', ~arrays['is_train']))}
        manifest['prior_distillation_updates'] = checkpoint.get('distillation_updates', 0)
        manifest['cumulative_updates'] = manifest['prior_distillation_updates']
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(SEED)
            torch.use_deterministic_algorithms(True)
            net = QNet(79, 6, 512, True)
            net.load_state_dict(checkpoint['q'], strict=True)
            before = _metrics(_predict(net, arrays['s'], check), arrays)
            train_index = np.flatnonzero(arrays['is_train'])
            generator = torch.Generator().manual_seed(SEED)
            optimizer = torch.optim.Adam(net.parameters(), lr=LEARNING_RATE)
            frozen_state, before_calibration = None, None
            for phase, epochs in (('action', ACTION_EPOCHS), ('value', VALUE_EPOCHS)):
                if phase == 'value':
                    before_calibration = _predict(net, arrays['s'], check)
                    frozen_state = {key: value.detach().clone() for key, value in net.state_dict().items()
                                    if key.startswith(('body.', 'adv.'))}
                    net.body.requires_grad_(False)
                    net.adv.requires_grad_(False)
                    net.zero_grad(set_to_none=True)
                    optimizer = torch.optim.Adam(net.value.parameters(), lr=LEARNING_RATE)
                for epoch in range(epochs):
                    check()
                    net.train()
                    order = train_index[torch.randperm(len(train_index), generator=generator).numpy()]
                    for start in range(0, len(order), BATCH_SIZE):
                        check()
                        index = order[start:start + BATCH_SIZE]
                        optimizer.zero_grad(set_to_none=True)
                        prediction = net(torch.from_numpy(arrays['s'][index]))
                        target = torch.from_numpy(arrays['teacher_q'][index])
                        mask = torch.from_numpy(arrays['mask'][index])
                        if phase == 'action':
                            loss = action_loss(prediction, target, mask, manifest['scale'])
                        else:
                            legal_count = mask.sum(1)
                            predicted_mean = prediction.masked_fill(~mask, 0).sum(1) / legal_count
                            teacher_mean = target.masked_fill(~mask, 0).sum(1) / legal_count
                            loss = (predicted_mean - teacher_mean).square().mean()
                        _finite(loss)
                        loss.backward()
                        _finite([p.grad for p in net.parameters()])
                        optimizer.step()
                        _finite(net.state_dict())
                        manifest[f'{phase}_updates'] += 1
                        manifest['updates'] += 1
                        manifest['cumulative_updates'] += 1
                        manifest['training_rows_seen'] += len(index)
                        manifest['last_batch_loss'] = float(loss.detach())
                        progress(f'{phase}_fitting')
                    manifest[f'{phase}_epochs_completed'] = epoch + 1
                    progress(f'{phase}_fitting')
            if (manifest['action_epochs_completed'] != ACTION_EPOCHS
                    or manifest['value_epochs_completed'] != VALUE_EPOCHS):
                raise ValueError('Both fixed training phases must finish')
            prediction = _predict(net, arrays['s'], check)
            manifest['calibration'] = _calibration_checks(net, frozen_state, before_calibration,
                                                          prediction, arrays['mask'])
            after = _metrics(prediction, arrays)
            state = {key: value.detach().clone() for key, value in net.state_dict().items()}
            exported = dict(q=state, target_q={key: value.clone() for key, value in state.items()},
                            cfg=checkpoint['cfg'], feature_dim=79, n_actions=6,
                            ensemble=[], ensemble_dims=[], env_steps=60000, learn_steps=0,
                            distillation_updates=manifest['cumulative_updates'],
                            distillation_epochs=checkpoint.get('distillation_epochs', 0)+ACTION_EPOCHS+VALUE_EPOCHS,
                            distillation_seed=SEED)
            _finite(exported)
            (out / 'weights').mkdir()
            check()
            torch.save(exported, pending)
            _student(pending)
            # Verify the actual deployment loader, not only a naked QNet reload.
            from agents.sherlock.main import Agent_x
            loaded = Agent_x('player_0', agent_path=str(pending), train=False)
            probe = torch.from_numpy(arrays['s'][:min(32, len(arrays['s']))])
            with torch.no_grad():
                manifest['reload_exact'] = not loaded.extra_q and torch.equal(loaded.q(probe), net(probe))
            if not manifest['reload_exact']:
                raise ValueError('Agent_x single-network reload changed Q predictions')
        manifest['inputs_after'] = hashes(inputs)
        manifest['sources_after'] = hashes(SOURCE_FILES)
        manifest['protected_after'] = _protected_hashes()
        for category in ('inputs', 'sources', 'protected'):
            if manifest[f'{category}_before'] != manifest[f'{category}_after']:
                raise ValueError(f'{category} changed during fitting')
        check()
        _write(out / 'metrics.json', dict(before=before, after_action=_metrics(before_calibration, arrays), after=after,
               limitations=['Development rows, not fresh policy strength evaluation.',
                            'Recorded collector rule/final-action metrics belong to the collecting policy; '
                            'they are not replayed final actions of the newly fitted policy.']))
        check()
        pending.replace(final)
        manifest['checkpoint_sha256'] = sha256(final)
        manifest['status'] = 'complete'
        manifest['completed_utc'] = datetime.now(timezone.utc).isoformat()
        progress('complete')
        _write(out / 'manifest.json', manifest)
        return manifest
    except BaseException as error:
        final.unlink(missing_ok=True)
        pending.unlink(missing_ok=True)
        manifest['status'] = 'incomplete'
        manifest['error'] = f'{type(error).__name__}: {error}'
        progress('incomplete')
        _write(out / 'manifest.json', manifest)
        if isinstance(error, TimeoutError):
            return manifest
        raise
    finally:
        torch.use_deterministic_algorithms(previous_determinism, warn_only=previous_warn)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--student', type=Path, required=True)
    parser.add_argument('--datasets', type=Path, nargs='+', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--deadline-utc', required=True)
    args = parser.parse_args(argv)
    deadline = datetime.fromisoformat(args.deadline_utc.replace('Z', '+00:00'))
    result = run_distillation(args.student, args.datasets, args.out, deadline)
    print(json.dumps(dict(status=result['status'], out=str(args.out), updates=result['updates'])))
    return 0 if result['status'] == 'complete' else 2


if __name__ == '__main__':
    raise SystemExit(main())
