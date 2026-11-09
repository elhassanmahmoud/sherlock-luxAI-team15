"""Offline diagnostic of two accepted initial-policy replay archives."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CLOSURE_SHA256 = 'fca3a077e57f079605db362f9dc68facadf787b0a3e819d1aca85050a84b23ce'
EXPECTED_ROWS = {'on48': 141704, 'on49': 141514}
SOURCE_FILES = ('agents/sherlock/features.py', 'agents/sherlock/reward.py',
                'agents/sherlock/main.py', 'agents/sherlock/replay_buffer.py')
# Zero-based FEATURE_NAMES in the hash-bound original features.py. No agent import.
FEATURE_INDICES = dict(match_step_frac=4, match_idx_frac=5, own_points=10,
                       own_wins=12, opp_wins=13, on_point=34, known_points=76)
INPUT_PROFILE = Path('experiments/analysis/ensemble_behavior_20261109')
OUTPUT_PROFILE = Path('experiments/analysis/point_reward_replay_20261109')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reward_stats(values):
    """Describe stored total rewards, without attributing reward components."""
    values = values.astype(np.float64)
    return dict(n=len(values), min=float(values.min()) if len(values) else None,
                median=float(np.median(values)) if len(values) else None,
                mean=float(values.mean()) if len(values) else None,
                max=float(values.max()) if len(values) else None,
                negative=int((values < 0).sum()), zero=int((values == 0).sum()),
                positive=int((values > 0).sum()))


def summarize_arrays(data):
    """Count unit transitions, never games, point events or individual scorers."""
    require(set(data) == {'s', 'a', 'r', 'ns', 'done', 'mask'}, 'Replay keys differ')
    require(all(isinstance(value, np.ndarray) for value in data.values()), 'Arrays required')
    s, ns = data['s'], data['ns']
    require(s.ndim == 2, 'Invalid feature shape')
    n = len(s)
    require(s.shape == ns.shape == (n, 79) and data['mask'].shape == (n, 6)
            and all(data[key].shape == (n,) for key in ('a', 'r', 'done')), 'Invalid replay shape')
    require(all(data[key].dtype == np.float32 for key in ('s', 'ns', 'r', 'done'))
            and data['a'].dtype == np.int64 and data['mask'].dtype == bool, 'Invalid replay dtype')
    require(all(np.isfinite(value).all() for value in data.values()), 'Nonfinite replay values')
    require(np.isin(data['a'], range(6)).all() and np.isin(data['done'], [0., 1.]).all()
            and data['mask'].any(axis=1).all(), 'Invalid action, done or next mask')
    require(((ns[:, 76] >= 0) & (ns[:, 76] <= 1)).all()
            and np.isin(ns[:, 34], [0., 1.]).all(), 'Invalid known-point features')
    eligible = ((data['done'] == 0) & (s[:, 10] >= 0) & (s[:, 10] < 1)
                & (ns[:, 10] >= 0) & (ns[:, 10] < 1) & (ns[:, 4] > s[:, 4])
                & (ns[:, 5] == s[:, 5]) & (ns[:, 12] == s[:, 12])
                & (ns[:, 13] == s[:, 13]))
    positive = eligible & (ns[:, 10] > s[:, 10])
    unknown = positive & (ns[:, 76] == 0)
    known = positive & (ns[:, 76] > 0)
    require((ns[unknown, 34] == 0).all(), 'Zero known points and on_point are inconsistent')
    positive_count, unknown_count = int(positive.sum()), int(unknown.sum())
    examples = [dict(row_index=int(i), r=float(data['r'][i]),
                     s={name: float(s[i, index]) for name, index in FEATURE_INDICES.items()},
                     ns={name: float(ns[i, index]) for name, index in FEATURE_INDICES.items()})
                for i in np.flatnonzero(unknown)[:5]]
    return dict(total_rows=n, eligible_rows=int(eligible.sum()), positive_rows=positive_count,
                unknown_point_rows=unknown_count,
                unknown_point_fraction=unknown_count / positive_count if positive_count else None,
                unknown_point_rewards=reward_stats(data['r'][unknown]),
                known_point_rewards=reward_stats(data['r'][known]), examples=examples)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def bound_json(path, expected_hash):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected_hash, f'JSON hash mismatch: {path}')
    return json.loads(raw)


def bound_inputs(root):
    """Follow only the accepted closure, admission, metadata and relevant sources."""
    base = root / INPUT_PROFILE
    closure_path = base / 'operations/training-completion.json'
    closure = bound_json(closure_path, CLOSURE_SHA256)
    require(closure['profile'] == 'ensemble_behavior_20261109'
            and closure['status'] == 'COMPLETE_TRAINING_NO_STRENGTH_CLAIM', 'Invalid training closure')
    admission_path = base / 'training-v1-admission.json'
    require(closure['admission'] == str(admission_path), 'Admission path differs')
    admission = bound_json(admission_path, closure['admission_sha256'])
    require(admission['source'] == closure['source']
            and admission['profile'] == 'ensemble_behavior_20261109'
            and admission['stage'] == 'training', 'Training source/admission differs')
    source_hashes = {}
    for name in SOURCE_FILES:
        path = root / name
        expected = closure['source']['files'][str(path)]
        require(digest(path) == expected, f'Source hash mismatch: {path}')
        source_hashes[name] = expected
    config = admission['config']
    require(config['use_belief'] is True and config['use_shaping'] is True
            and config['threat_feats'] is False, 'Unexpected feature/reward configuration')
    inputs = {}
    for role, n in EXPECTED_ROWS.items():
        directory = base / 'training_v1' / role
        metadata_path, archive = directory / 'prefill.json', directory / 'prefill-replay.npz'
        metadata_hash = closure['files'][str(metadata_path)]
        metadata = bound_json(metadata_path, metadata_hash)
        require(metadata['profile'] == 'ensemble_behavior_20261109'
                and metadata['status'] == 'prefill_ready' and metadata['role'] == role
                and metadata['start'] == int(role[-2:]) and metadata['stage'] == 'training'
                and metadata['games'] == 40 and metadata['learn_steps'] == 0
                and metadata['replay_size'] == n and n <= config['buffer_capacity']
                and metadata['source'] == closure['source'] and metadata['config'] == config
                and metadata['admission_sha256'] == closure['admission_sha256'],
                f'Accepted prefill metadata differs: {role}')
        # replay_sha256 is a semantic tensor hash, NOT an archive file hash.
        archive_hash = metadata['files'][str(archive)]
        require(archive_hash == closure['files'][str(archive)]
                and digest(archive) == archive_hash, f'Archive hash mismatch: {archive}')
        inputs[role] = dict(archive=str(archive), archive_sha256=archive_hash,
                            metadata=str(metadata_path), metadata_sha256=metadata_hash, expected_rows=n)
    return dict(training_closure=str(closure_path), training_closure_sha256=CLOSURE_SHA256,
                admission_sha256=closure['admission_sha256'], source_hashes=source_hashes,
                feature_indices=FEATURE_INDICES, inputs=inputs)


def run_diagnostic(root=ROOT):
    root = Path(root).resolve()
    output = root / OUTPUT_PROFILE / 'result.json'
    if output.exists():
        raise FileExistsError(output)
    provenance = bound_inputs(root)
    arms = {}
    for role, binding in provenance['inputs'].items():
        with np.load(binding['archive'], allow_pickle=False) as archive:
            data = {key: archive[key] for key in archive.files}
        arms[role] = summarize_arrays(data)
        require(arms[role]['total_rows'] == binding['expected_rows'], f'Replay row count differs: {role}')
    result = dict(profile='point_reward_replay_20261109', unit='unit_transition',
                  phase='initial_policy_prefill_no_gradient_updates', provenance=provenance, arms=arms,
                  limitations=['Team point gains repeat across units; rows are not point events.',
                               'Capped, terminal and match-changing transitions are excluded.',
                               'Known-point rewards are descriptive, not a fair causal comparison.',
                               'No individual attribution, strength or reward-change benefit is established.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    return output


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(run_diagnostic())
