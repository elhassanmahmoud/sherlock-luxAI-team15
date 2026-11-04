"""Fixed V14 arithmetic-Q distillation into a genuine single QNet.

Only weights completing the requested epochs are exported. Historical row diagnostics have no
current action masks and do not establish unseen-map or episode generalization.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet, checkpoint_ensemble_dims
from scripts.output_paths import checked_output

ROOT = Path(__file__).resolve().parent.parent
V14_SHA256 = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
SEED = 20261104
HIDDEN = 512
EPOCHS = 3
BATCH_SIZE = 1024
LEARNING_RATE = 1e-4
SOURCE_FILES = [Path(__file__).resolve(), ROOT / 'agents/sherlock/model.py',
                ROOT / 'agents/sherlock/config.py', ROOT / 'scripts/output_paths.py']


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _hashes(paths) -> dict:
    return {str(Path(path).resolve()): sha256(path) for path in paths}


def _write(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def _finite(value) -> None:
    if isinstance(value, torch.Tensor):
        if not torch.isfinite(value).all():
            raise ValueError('Nonfinite tensor in checkpoint or model output')
    elif isinstance(value, dict):
        for item in value.values():
            _finite(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _finite(item)


def reserve_output(out: Path, inputs) -> Path:
    out = Path(out).expanduser().absolute()
    # Check local and primary/historical checkout roots, including filesystem aliases.
    roots = [ROOT, Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15'),
             Path('/Users/moayedshawesh/Desktop/KI/sherlock-november-followup')]
    for root in roots:
        for protected in (root / 'agents/sherlock/weights', root / 'Gruppe15'):
            checked_output(out, protected)
            if protected.resolve().is_relative_to(out.resolve()):
                raise ValueError('Output must not contain a protected submission directory')
    if any(Path(path).resolve().is_relative_to(out.resolve()) for path in inputs):
        raise ValueError('Output must not contain an input source')
    if out.exists() or out.is_symlink():
        raise ValueError(f'Output already occupied: {out}')
    out.mkdir(parents=True, exist_ok=False)
    return out.resolve()


def load_teacher(path: Path) -> tuple[list[QNet], dict]:
    if sha256(path) != V14_SHA256:
        raise ValueError('Teacher SHA256 does not match pinned V14')
    checkpoint = torch.load(path, map_location='cpu', weights_only=True)
    if not isinstance(checkpoint, dict) or checkpoint.get('feature_dim') != 79 or checkpoint.get('n_actions') != 6:
        raise ValueError('Teacher must have 79 features and 6 actions')
    dims = checkpoint_ensemble_dims(checkpoint, 79)
    states = [checkpoint['q'], *checkpoint.get('ensemble', [])]
    if len(states) != 36 or dims != [79] * 35:
        raise ValueError('Teacher must contain exactly 36 homogeneous 79-input networks')
    cfg = copy.deepcopy(checkpoint['cfg'])
    validated = AgentConfig(**cfg)
    if (not validated.dueling or not validated.use_sap or validated.threat_feats
            or not isinstance(validated.hidden, int) or validated.hidden <= 0):
        raise ValueError('Teacher configuration violates the 79/6 dueling architecture')
    _finite(checkpoint)
    nets = []
    # Constructing models must not perturb the seed used for the student.
    with torch.random.fork_rng(devices=[]):
        for state in states:
            net = QNet(79, 6, validated.hidden, True)
            net.load_state_dict(state, strict=True)
            net.eval().requires_grad_(False)
            nets.append(net)
    return nets, cfg


@torch.no_grad()
def teacher_q(nets: list[QNet], x: torch.Tensor) -> torch.Tensor:
    if not nets:
        raise ValueError('Teacher ensemble must not be empty')
    predictions = []
    for net in nets:
        net.eval()
        prediction = net(x)
        _finite(prediction)
        predictions.append(prediction)
    # Match Agent_x's deployed reduction order, including float32 rounding.
    mean = torch.stack(predictions).mean(dim=0)
    _finite(mean)
    return mean


def load_buffers(paths, row_cap: int | None = None, check=lambda: None) -> tuple[list, list]:
    if row_cap is not None and (isinstance(row_cap, bool) or row_cap < 2):
        raise ValueError('Technical row cap must be at least two')
    datasets, metadata = [], []
    for path in paths:
        check()
        with np.load(path, allow_pickle=False) as archive:
            if 's' not in archive:
                raise ValueError('Replay must contain s')
            rows = archive['s']
        if rows.ndim != 2 or rows.shape[1] != 79 or rows.dtype != np.float32:
            raise ValueError('Replay s must be a float32 matrix with 79 columns')
        for start in range(0, len(rows), BATCH_SIZE):
            check()
            if not np.isfinite(rows[start:start + BATCH_SIZE]).all():
                raise ValueError('Replay s must be entirely finite, including beyond any cap')
        source_rows = len(rows)
        if row_cap is None and source_rows != 300000:
            raise ValueError('Production replay must contain all 300000 source rows')
        used = source_rows if row_cap is None else min(source_rows, row_cap)
        split = used * 4 // 5
        if split == 0 or split == used:
            raise ValueError('Replay must have nonempty train and diagnostic splits')
        rows = np.ascontiguousarray(rows[:used])
        datasets.append((rows, split))
        metadata.append(dict(path=str(Path(path).resolve()), source_rows=source_rows,
                             used_rows=used, split_row=split, train_rows=split,
                             diagnostic_rows=used - split))
    return datasets, metadata


def row_overlap(datasets, check=lambda: None) -> dict:
    """Count numerical feature-row equality exactly, with +0 and -0 canonicalized."""
    unique_parts, counts_parts = [], []
    for diagnostic in (False, True):
        check()
        rows = np.concatenate([x[split:] if diagnostic else x[:split] for x, split in datasets])
        rows[rows == 0] = 0  # Numerical equality treats signed zeros as equal.
        keys = rows.view(np.dtype((np.void, rows.dtype.itemsize * 79))).reshape(-1)
        unique, counts = np.unique(keys, return_counts=True)
        unique_parts.append(unique)
        counts_parts.append(counts)
    check()
    shared, left, right = np.intersect1d(*unique_parts, assume_unique=True, return_indices=True)
    return dict(shared_unique_feature_rows=len(shared),
                train_rows_matching_diagnostic=int(counts_parts[0][left].sum()),
                diagnostic_rows_matching_train=int(counts_parts[1][right].sum()),
                train_unique_feature_rows=len(unique_parts[0]),
                diagnostic_unique_feature_rows=len(unique_parts[1]),
                definition='Exact float32 feature-row equality; signed zero normalized; pooled across both files')


def q_metrics(prediction: np.ndarray, target: np.ndarray) -> dict:
    if prediction.shape != target.shape or prediction.ndim != 2 or prediction.shape[1] != 6 or not len(prediction):
        raise ValueError('Metrics require matching nonempty six-action matrices')
    prediction, target = prediction.astype(np.float64), target.astype(np.float64)
    if not np.isfinite(prediction).all() or not np.isfinite(target).all():
        raise ValueError('Metric inputs must be finite')
    delta = prediction - target
    mean = delta.mean(axis=1, keepdims=True)
    return dict(rows=len(prediction), q_mse=float(np.mean(delta ** 2)),
                mean_value_mse=float(np.mean(mean ** 2)),
                centered_action_mse=float(np.mean((delta - mean) ** 2)),
                unmasked_argmax_agreement=float(np.mean(prediction.argmax(1) == target.argmax(1))))


@torch.no_grad()
def _predict(net, rows, check) -> np.ndarray:
    net.eval()
    result = np.empty((len(rows), 6), np.float32)
    for start in range(0, len(rows), BATCH_SIZE):
        check()
        prediction = net(torch.from_numpy(rows[start:start + BATCH_SIZE]))
        _finite(prediction)
        result[start:start + BATCH_SIZE] = prediction.numpy()
    return result


def _diagnostics(net, datasets, targets, check) -> list[dict]:
    results = []
    for (rows, split), target in zip(datasets, targets):
        prediction = _predict(net, rows, check)
        results.append(dict(train=q_metrics(prediction[:split], target[:split]),
                            diagnostic=q_metrics(prediction[split:], target[split:])))
    return results


def run_distillation(teacher: Path, buffers, out: Path, deadline: datetime, *, row_cap=None, epochs=EPOCHS) -> dict:
    if type(epochs) is not int or not 1 <= epochs <= 100:
        raise ValueError('epochs must be a plain integer between 1 and 100')
    if deadline.tzinfo is None:
        raise ValueError('Deadline must include a UTC offset')
    if len(buffers) != 2 or len({Path(path).resolve() for path in buffers}) != 2:
        raise ValueError('Exactly two distinct replay files are required')
    inputs = [Path(teacher).resolve(), *[Path(path).resolve() for path in buffers]]
    out = reserve_output(out, inputs)
    started = time.monotonic()
    prior_determinism = torch.are_deterministic_algorithms_enabled()
    prior_warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
    manifest = dict(status='running', seed=SEED, hidden=HIDDEN, epochs_requested=epochs,
                    batch_size=BATCH_SIZE, learning_rate=LEARNING_RATE, cpu_threads=1,
                    epochs_completed=0, updates=0, training_rows_seen=0,
                    technical_row_cap=row_cap, technical_test_only=row_cap is not None,
                    deadline_utc=deadline.astimezone(timezone.utc).isoformat(),
                    started_utc=datetime.now(timezone.utc).isoformat())
    final = out / 'weights/agent.pth'
    pending = out / 'weights/agent.pending.pth'

    def progress(phase):
        manifest['phase'] = phase
        manifest['wall_seconds'] = time.monotonic() - started
        _write(out / 'status.json', manifest)

    def check():
        if datetime.now(timezone.utc) >= deadline:
            raise TimeoutError('Fixed deadline reached; no completed candidate exported')

    try:
        progress('input_validation')
        check()
        torch.set_num_threads(1)
        manifest['runtime'] = dict(python_executable=sys.executable, python_version=platform.python_version(),
                                   torch_version=str(torch.__version__), numpy_version=np.__version__,
                                   git_head=subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                                           check=True, capture_output=True, text=True).stdout.strip())
        manifest['inputs_before'] = _hashes(inputs)
        manifest['sources_before'] = _hashes(SOURCE_FILES)
        nets, cfg = load_teacher(inputs[0])
        manifest['teacher_members'] = len(nets)
        manifest['teacher_config'] = cfg
        manifest['teacher_sha256'] = manifest['inputs_before'][str(inputs[0])]
        datasets, metadata = load_buffers(inputs[1:], row_cap, check)
        manifest['buffers'] = metadata
        manifest['row_overlap'] = row_overlap(datasets, check)
        targets = []
        progress('labeling')
        for rows, _ in datasets:
            target = np.empty((len(rows), 6), np.float32)
            for start in range(0, len(rows), BATCH_SIZE):
                check()
                target[start:start + BATCH_SIZE] = teacher_q(nets, torch.from_numpy(rows[start:start + BATCH_SIZE])).numpy()
                manifest['label_rows_completed'] = manifest.get('label_rows_completed', 0) + min(BATCH_SIZE, len(rows) - start)
                progress('labeling')
            targets.append(target)
        # Teacher labels are fixed; no gradient ever reaches teacher parameters.
        manifest['teacher_gradients_absent'] = all(p.grad is None for net in nets for p in net.parameters())
        del nets
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(SEED)
            torch.use_deterministic_algorithms(True)
            student = QNet(79, 6, HIDDEN, True)
            student.eval()
            initial = {key: value.clone() for key, value in student.state_dict().items()}
            progress('diagnostics_before')
            before = _diagnostics(student, datasets, targets, check)
            train_x = np.concatenate([rows[:split] for rows, split in datasets])
            train_y = np.concatenate([target[:split] for (_, split), target in zip(datasets, targets)])
            optimizer = torch.optim.Adam(student.parameters(), lr=LEARNING_RATE)
            generator = torch.Generator().manual_seed(SEED)
            for epoch in range(epochs):
                order = torch.randperm(len(train_x), generator=generator).numpy()
                student.train()
                for start in range(0, len(order), BATCH_SIZE):
                    check()
                    index = order[start:start + BATCH_SIZE]
                    optimizer.zero_grad(set_to_none=True)
                    prediction = student(torch.from_numpy(train_x[index]))
                    loss = torch.nn.functional.mse_loss(prediction, torch.from_numpy(train_y[index]))
                    _finite(loss)
                    loss.backward()
                    _finite([p.grad for p in student.parameters()])
                    optimizer.step()
                    _finite(student.state_dict())
                    manifest['updates'] += 1
                    manifest['training_rows_seen'] += len(index)
                    manifest['last_batch_mse'] = float(loss.detach())
                    progress('fitting')
                manifest['epochs_completed'] = epoch + 1
                student.eval()
                progress('fitting')
            if manifest['epochs_completed'] != epochs:
                raise ValueError('Requested epochs did not complete')
            progress('diagnostics_after')
            after = _diagnostics(student, datasets, targets, check)
            student.eval()
            state = {key: value.detach().clone() for key, value in student.state_dict().items()}
            manifest['student_tensors_changed'] = any(not torch.equal(state[key], initial[key]) for key in state)
            if not manifest['student_tensors_changed']:
                raise ValueError('Student weights did not change')
            student_cfg = copy.deepcopy(cfg)
            student_cfg['hidden'] = HIDDEN
            checkpoint = dict(q=state, target_q={key: value.clone() for key, value in state.items()},
                              ensemble=[], ensemble_dims=[], cfg=student_cfg,
                              feature_dim=79, n_actions=6, env_steps=60000, learn_steps=0,
                              distillation_updates=manifest['updates'], distillation_epochs=epochs,
                              distillation_seed=SEED)
            _finite(checkpoint)
            (out / 'weights').mkdir()
            torch.save(checkpoint, pending)
            reload = QNet(79, 6, HIDDEN, True).eval()
            reload.load_state_dict(torch.load(pending, map_location='cpu', weights_only=True)['q'])
            probe = torch.from_numpy(datasets[0][0][:min(32, len(datasets[0][0]))])
            with torch.no_grad():
                manifest['reload_exact'] = torch.equal(reload(probe), student(probe))
            if not manifest['reload_exact']:
                raise ValueError('Checkpoint reload changed predictions')
        manifest['inputs_after'] = _hashes(inputs)
        manifest['sources_after'] = _hashes(SOURCE_FILES)
        if manifest['inputs_before'] != manifest['inputs_after'] or manifest['sources_before'] != manifest['sources_after']:
            raise ValueError('Input or source mutation detected')
        check()
        metrics = dict(buffers=[dict(**meta, before=pre, after=post) for meta, pre, post in zip(metadata, before, after)],
                       limitations=['Historical row diagnostic only; maps/episodes are not independent.',
                                    'No current action masks: argmax agreement is unmasked, not legal-action agreement.'],
                       decomposition='q_mse = mean_value_mse + centered_action_mse')
        _write(out / 'metrics.json', metrics)
        pending.replace(final)
        manifest['checkpoint_sha256'] = sha256(final)
        manifest['status'] = 'complete'
        manifest['completed_utc'] = datetime.now(timezone.utc).isoformat()
        progress('complete')
        _write(out / 'manifest.json', manifest)
        return manifest
    except BaseException as error:
        manifest['status'] = 'incomplete'
        manifest['error'] = f'{type(error).__name__}: {error}'
        for path in (pending, final):
            if path.exists():
                path.unlink()
        # Also retain hashes after deadline/errors, where inputs are still readable.
        for name, paths in (('inputs_after', inputs), ('sources_after', SOURCE_FILES)):
            try:
                manifest[name] = _hashes(paths)
            except OSError:
                pass
        progress('incomplete')
        _write(out / 'manifest.json', manifest)
        if isinstance(error, TimeoutError):
            return manifest
        raise
    finally:
        torch.use_deterministic_algorithms(prior_determinism, warn_only=prior_warn_only)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--teacher', type=Path, required=True)
    parser.add_argument('--buffers', type=Path, nargs=2, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--deadline-utc', required=True)
    parser.add_argument('--row-cap', type=int, help='Technical tests only; marks run as non-production')
    parser.add_argument('--epochs', type=int, default=EPOCHS, help='Epoch count from 1 to 100 (default: 3)')
    args = parser.parse_args(argv)
    deadline = datetime.fromisoformat(args.deadline_utc.replace('Z', '+00:00'))
    result = run_distillation(args.teacher, args.buffers, args.out, deadline, row_cap=args.row_cap, epochs=args.epochs)
    print(json.dumps(dict(status=result['status'], out=str(args.out), updates=result['updates'])))
    return 0 if result['status'] == 'complete' else 2


if __name__ == '__main__':
    raise SystemExit(main())
