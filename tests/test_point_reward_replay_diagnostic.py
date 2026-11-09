"""Synthetic arrays and temporary archives only; never read the real replays."""
import hashlib
import importlib
import json
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def diagnostic():
    name = 'scripts.point_reward_replay_diagnostic'
    assert importlib.util.find_spec(name), 'Offline diagnostic not implemented'
    return importlib.import_module(name)


def arrays(n=1):
    s = np.zeros((n, 79), dtype=np.float32)
    ns = s.copy()
    s[:, 4] = .1
    ns[:, 4] = .2
    s[:, 10] = .01
    ns[:, 10] = .02
    return dict(s=s, ns=ns, a=np.zeros(n, dtype=np.int64),
                r=np.zeros(n, dtype=np.float32), done=np.zeros(n, dtype=np.float32),
                mask=np.ones((n, 6), dtype=bool))


def test_rewards_preserve_unit_rows_and_separate_known_reference(diagnostic):
    data = arrays(5)
    data['r'][:] = [-2, 0, 5, -4, 2]
    data['ns'][3:, 76] = .05
    result = diagnostic.summarize_arrays(data)
    assert result['total_rows'] == result['eligible_rows'] == result['positive_rows'] == 5
    assert result['unknown_point_rows'] == 3
    assert result['unknown_point_fraction'] == .6
    assert result['unknown_point_rewards'] == dict(n=3, min=-2., median=0., mean=1., max=5.,
                                                  negative=1, zero=1, positive=1)
    assert result['known_point_rewards'] == dict(n=2, min=-4., median=-1., mean=-1., max=2.,
                                                negative=1, zero=0, positive=1)
    assert [example['row_index'] for example in result['examples']] == [0, 1, 2]
    assert result['examples'][0]['r'] == -2.
    assert result['examples'][0]['ns']['known_points'] == 0.


@pytest.mark.parametrize('key,index,value,eligible', [
    ('ns', 10, .01, 1), ('ns', 10, 0., 1),  # zero/negative gain
    ('s', 10, 1., 0), ('ns', 10, 1., 0), ('s', 10, -.01, 0),
    ('ns', 10, -.01, 0), ('done', None, 1., 0),
    ('ns', 5, 1/3, 0), ('ns', 12, 1/3, 0), ('ns', 13, 1/3, 0),
    ('ns', 4, 0., 0), ('ns', 4, .1, 0),
])
def test_excludes_ambiguous_transitions(diagnostic, key, index, value, eligible):
    data = arrays()
    if index is None:
        data[key][0] = value
    else:
        data[key][0, index] = value
    result = diagnostic.summarize_arrays(data)
    assert result['eligible_rows'] == eligible
    assert result['positive_rows'] == result['unknown_point_rows'] == 0
    assert result['unknown_point_fraction'] is None


def test_empty_groups_have_null_statistics_and_examples_are_bounded(diagnostic):
    empty = diagnostic.summarize_arrays(arrays(0))
    assert empty['unknown_point_rewards'] == dict(n=0, min=None, median=None, mean=None,
                                                 max=None, negative=0, zero=0, positive=0)
    assert empty['examples'] == []
    assert len(diagnostic.summarize_arrays(arrays(7))['examples']) == 5
    json.dumps(empty, allow_nan=False)


def test_zero_known_fields_cannot_contain_an_on_point_unit(diagnostic):
    data = arrays()
    data['ns'][0, 34] = 1.
    with pytest.raises(ValueError, match='inconsistent'):
        diagnostic.summarize_arrays(data)


@pytest.mark.parametrize('defect', ['shape', 'dtype', 'nan', 'inf', 'mask_dtype', 'mask_empty',
                                  'action', 'done', 'extra', 'known_negative'])
def test_malformed_arrays_are_rejected(diagnostic, defect):
    data = arrays()
    if defect == 'shape': data['ns'] = data['ns'][:, :-1]
    elif defect == 'dtype': data['s'] = data['s'].astype(np.float64)
    elif defect == 'nan': data['r'][0] = np.nan
    elif defect == 'inf': data['ns'][0, 76] = np.inf
    elif defect == 'mask_dtype': data['mask'] = data['mask'].astype(np.int8)
    elif defect == 'mask_empty': data['mask'][:] = False
    elif defect == 'action': data['a'][0] = 6
    elif defect == 'done': data['done'][0] = .5
    elif defect == 'extra': data['unknown'] = np.zeros(1)
    elif defect == 'known_negative': data['ns'][0, 76] = -.1
    with pytest.raises(ValueError):
        diagnostic.summarize_arrays(data)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def bound_fixture(tmp_path, monkeypatch, diagnostic):
    """Small real files with the actual provenance structure and independent hashes."""
    base = tmp_path / 'experiments/analysis/ensemble_behavior_20261109'
    sources = {}
    for name in diagnostic.SOURCE_FILES:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# synthetic source\n')
        sources[str(path)] = digest(path)
    source = dict(head='synthetic', files=sources)
    config = dict(use_belief=True, use_shaping=True, threat_feats=False, buffer_capacity=300000,
                  reward_fix=True, w_point=1.)
    admission = base / 'training-v1-admission.json'
    write_json(admission, dict(profile='ensemble_behavior_20261109', stage='training',
                               source=source, config=config))
    files = {}
    for role, n in [('on48', 2), ('on49', 1)]:
        directory = base / 'training_v1' / role
        directory.mkdir(parents=True)
        replay = directory / 'prefill-replay.npz'
        np.savez(replay, **arrays(n))
        files[str(replay)] = digest(replay)
        metadata = directory / 'prefill.json'
        write_json(metadata, dict(profile='ensemble_behavior_20261109', status='prefill_ready',
            role=role, start=int(role[-2:]), stage='training', games=40, learn_steps=0,
            replay_size=n, source=source, config=config, admission_sha256=digest(admission),
            replay_sha256='semantic hash is deliberately not the archive byte hash',
            files={str(replay): digest(replay)}))
        files[str(metadata)] = digest(metadata)
    closure = base / 'operations/training-completion.json'
    write_json(closure, dict(profile='ensemble_behavior_20261109',
        status='COMPLETE_TRAINING_NO_STRENGTH_CLAIM', source=source,
        admission=str(admission), admission_sha256=digest(admission), files=files))
    monkeypatch.setattr(diagnostic, 'CLOSURE_SHA256', digest(closure))
    monkeypatch.setattr(diagnostic, 'EXPECTED_ROWS', {'on48': 2, 'on49': 1})
    return tmp_path


def test_bound_run_uses_byte_hash_preserves_prep_and_refuses_overwrite(diagnostic, bound_fixture):
    root = bound_fixture
    prep = root / 'experiments/analysis/point_reward_replay_20261109/preparation/keep.txt'
    prep.parent.mkdir(parents=True)
    prep.write_text('existing preparation')
    path = diagnostic.run_diagnostic(root)
    result = json.loads(path.read_text())
    assert set(result['arms']) == {'on48', 'on49'}
    assert result['arms']['on48']['total_rows'] == 2
    assert result['arms']['on49']['unknown_point_rows'] == 1
    assert prep.read_text() == 'existing preparation'
    saved = path.read_bytes()
    with pytest.raises(FileExistsError):
        diagnostic.run_diagnostic(root)
    assert path.read_bytes() == saved


@pytest.mark.parametrize('target', ['closure', 'prefill', 'source', 'archive'])
def test_changed_provenance_rejected_without_result(diagnostic, bound_fixture, target):
    root = bound_fixture
    base = root / 'experiments/analysis/ensemble_behavior_20261109'
    path = {'closure': base / 'operations/training-completion.json',
            'prefill': base / 'training_v1/on48/prefill.json',
            'source': root / 'agents/sherlock/features.py',
            'archive': base / 'training_v1/on48/prefill-replay.npz'}[target]
    with path.open('ab') as stream:
        stream.write(b' ')
    with pytest.raises(ValueError, match='hash'):
        diagnostic.run_diagnostic(root)
    assert not (root / 'experiments/analysis/point_reward_replay_20261109/result.json').exists()
