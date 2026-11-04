"""Read-only QNet retention diagnostics on excluded collector rows.

This measures agreement with recorded V14 Q values in known development data.
Recorded final actions belong to the collecting policy, not the evaluated model.
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

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet
from scripts.student_action_distill import (ROOT, _validate_q, action_metrics,
                                           load_datasets, reserve_output)
from scripts.student_distill import _finite, _write, sha256

SOURCE_FILES = [Path(__file__).resolve(), *(ROOT / name for name in (
    'scripts/student_action_distill.py', 'scripts/student_distill.py',
    'scripts/output_paths.py', 'agents/sherlock/model.py', 'agents/sherlock/config.py'))]
DATA_FILES = ('manifest.json', 'status.json', 'dataset.npz', 'games.jsonl')


def parse_models(entries):
    """Parse repeated NAME=PATH arguments without silently replacing a role."""
    models = {}
    for entry in entries:
        name, separator, path = entry.partition('=')
        if not separator or not name.strip() or name != name.strip() or not path.strip() or name in models:
            raise ValueError('Require distinct nonempty model NAME=PATH arguments')
        models[name] = path
    if not models:
        raise ValueError('Require at least one model NAME=PATH')
    return models


def load_model(path):
    """Load only a single checkpoint q, inferring and checking its QNet shape."""
    checkpoint = torch.load(path, map_location='cpu', weights_only=True)
    if (not isinstance(checkpoint, dict) or not isinstance(checkpoint.get('q'), dict)
            or not isinstance(checkpoint.get('cfg', {}), dict)
            or checkpoint.get('feature_dim', 79) != 79 or checkpoint.get('n_actions', 6) != 6
            or checkpoint.get('ensemble') or checkpoint.get('ensemble_dims')):
        raise ValueError('Require a single 79-input six-action QNet checkpoint q/config')
    state = checkpoint['q']
    weight = state.get('body.0.weight')
    if (not isinstance(weight, torch.Tensor) or weight.ndim != 2
            or weight.shape[1] != 79 or weight.shape[0] < 1
            or not all(isinstance(value, torch.Tensor) and value.is_floating_point()
                       for value in state.values())):
        raise ValueError('Invalid QNet state/input dimensions')
    _finite(state)
    hidden = int(weight.shape[0])
    dueling = 'value.0.weight' in state or 'adv.0.weight' in state
    cfg = checkpoint.get('cfg', {})
    if (('hidden' in cfg and (type(cfg['hidden']) is not int or cfg['hidden'] != hidden))
            or ('dueling' in cfg and (type(cfg['dueling']) is not bool or cfg['dueling'] != dueling))):
        raise ValueError('Checkpoint config hidden/dueling differs from q architecture')
    try:
        config = AgentConfig(**dict(cfg, hidden=hidden, dueling=dueling)).to_dict()
        # Construction must not consume the caller's RNG, even between model roles.
        with torch.random.fork_rng(devices=[]):
            net = QNet(79, 6, hidden=hidden, dueling=dueling)
            net.load_state_dict(state, strict=True)
    except (RuntimeError, TypeError, ValueError) as error:
        raise ValueError(f'Invalid QNet state/config: {error}') from error
    return net.eval(), dict(hidden=hidden, dueling=dueling, feature_dim=79,
                            n_actions=6, config=config)


def q_summary(q, mask):
    """Population moments of legal entries; top-two gaps omit singleton masks."""
    q = torch.as_tensor(q, dtype=torch.float64)
    mask = torch.as_tensor(mask)
    _validate_q(q, q, mask)
    values = q[mask]
    count = mask.sum(1)
    means = q.masked_fill(~mask, 0).sum(1) / count
    centered = (q - means[:, None]).masked_fill(~mask, 0)
    row_stds = (centered.square().sum(1) / count).sqrt()
    multiple = count >= 2
    top = q[multiple].masked_fill(~mask[multiple], -torch.inf).topk(2, dim=1).values
    gaps = top[:, 0] - top[:, 1]
    return dict(legal_q_entries=int(mask.sum()), legal_q_mean=float(values.mean()),
                legal_q_std=float(values.std(correction=0)),
                mean_row_legal_q_std=float(row_stds.mean()),
                top_two_gap_rows=len(gaps),
                top_two_gap_mean=float(gaps.mean()) if len(gaps) else None,
                top_two_gap_std=float(gaps.std(correction=0)) if len(gaps) else None,
                top_two_gap_zero_rate=float((gaps == 0).double().mean()) if len(gaps) else None)


@torch.no_grad()
def _predict(net, rows, batch_size):
    prediction = np.empty((len(rows), 6), np.float32)
    for start in range(0, len(rows), batch_size):
        value = net(torch.from_numpy(rows[start:start + batch_size]))
        if value.shape != (min(batch_size, len(rows) - start), 6):
            raise ValueError('QNet prediction must have six actions per row')
        _finite(value)
        prediction[start:start + batch_size] = value.cpu().numpy()
    return prediction


def _hashes(paths):
    return {str(Path(path).resolve()): sha256(path) for path in paths}


def run_retention(datasets, models, out, *, batch_size=1024):
    """Write one complete JSON report; no train row reaches model inference."""
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError('batch_size must be a positive integer')
    if not isinstance(models, dict) or not models:
        raise ValueError('Require at least one named model')
    if any(not isinstance(name, str) or not name.strip() or name != name.strip() for name in models):
        raise ValueError('Require nonempty model names')
    paths = [Path(path).expanduser().resolve() for path in datasets]
    if not paths or len(set(paths)) != len(paths):
        raise ValueError('Require distinct completed dataset directories')
    models = {name: Path(path).expanduser().resolve() for name, path in models.items()}
    inputs = [*models.values(), *(directory / name for directory in paths for name in DATA_FILES)]
    resolved_out = Path(out).expanduser().resolve()
    if any(resolved_out.is_relative_to(directory) for directory in paths):
        raise ValueError('Output must not be inside an input dataset archive')
    out = reserve_output(out, inputs)
    started = time.monotonic()
    report = dict(schema_version=1, status='running', started_utc=datetime.now(timezone.utc).isoformat(),
                  batch_size=batch_size, inputs_before=_hashes(inputs), sources_before=_hashes(SOURCE_FILES))
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True,
                          capture_output=True, check=False)
    report['source_head'] = head.stdout.strip() if head.returncode == 0 else None
    report['runtime'] = dict(python_executable=sys.executable, python_version=platform.python_version(),
                             numpy_version=np.__version__, torch_version=str(torch.__version__),
                             torch_threads=torch.get_num_threads(), device='cpu')
    arrays, metadata = load_datasets(paths)
    selected = ~arrays['is_train']
    diagnostic = {name: value[selected] for name, value in arrays.items()}
    report['split'] = dict(name='diagnostic', diagnostic_rows=int(selected.sum()),
                           excluded_training_rows=int((~selected).sum()),
                           diagnostic_seeds=sorted(set(diagnostic['env_seed'].tolist())))
    report['datasets'] = []
    offset = 0
    for item in metadata:
        rows = item['rows']
        count = int(selected[offset:offset + rows].sum())
        report['datasets'].append(dict(item, diagnostic_rows=count))
        offset += rows
    report['metric_definitions'] = dict(
        aggregation='action_metrics averages rows equally; legal_q_mean/std pool legal entries; std is population std',
        top_two_gap='largest minus second-largest legal Q; only rows with at least two legal actions',
        row_spread='mean_row_legal_q_std averages each row population standard deviation over its legal actions',
        recorded_collector='override/outside-mask metrics describe the collecting policy only')
    report['limitations'] = [
        'Known development rows excluded from supervised learning; no new-map or game-win measurement.',
        'Teacher Q values and collector final actions are recorded data; no teacher or game replay occurs.',
        'Retention differences are observations and do not establish a causal explanation of game losses.']
    report['teacher_metrics'] = q_summary(diagnostic['teacher_q'], diagnostic['mask'])
    report['models'] = {}
    for name, path in models.items():
        net, architecture = load_model(path)
        prediction = _predict(net, diagnostic['s'], batch_size)
        metrics = action_metrics(prediction, diagnostic['teacher_q'], diagnostic['mask'],
                                 diagnostic['final_action'], diagnostic['student_q'])
        metrics.update(q_summary(prediction, diagnostic['mask']))
        report['models'][name] = dict(path=str(path), sha256=report['inputs_before'][str(path)],
                                      architecture=architecture, metrics=metrics)
    report['inputs_after'] = _hashes(inputs)
    report['sources_after'] = _hashes(SOURCE_FILES)
    if (report['inputs_before'] != report['inputs_after']
            or report['sources_before'] != report['sources_after']):
        raise ValueError('Diagnostic inputs or sources changed during evaluation')
    report.update(status='complete', completed_utc=datetime.now(timezone.utc).isoformat(),
                  wall_seconds=time.monotonic() - started)
    _write(out / 'report.json', report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--datasets', nargs='+', required=True, type=Path)
    parser.add_argument('--model', action='append', required=True, metavar='NAME=PATH')
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--batch-size', type=int, default=1024)
    args = parser.parse_args(argv)
    try:
        models = parse_models(args.model)
        torch.set_num_threads(1)
        report = run_retention(args.datasets, models, args.out, batch_size=args.batch_size)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(dict(status=report['status'], diagnostic_rows=report['split']['diagnostic_rows'],
                          models=list(report['models']), report=str(args.out.resolve() / 'report.json'))))


if __name__ == '__main__':
    main()
