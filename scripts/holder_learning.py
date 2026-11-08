"""Fixed public HOLD features, one weighted ridge fit, and offline screening.

This module has no agent, environment, Torch, file, or historical-data access.
Callers verify complete pairs and bind source/data hashes before passing rows.
"""
from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping

import numpy as np

FEATURE_NAMES = (
    'proposal_q_advantage', 'own_energy', 'move_cost', 'sap_cost',
    'remaining_match_fraction', 'point_lead', 'current_energy_field',
    'destination_energy_field', 'current_nebula', 'destination_nebula',
    'current_armed_enemy_count', 'destination_armed_enemy_count',
    'current_adjacent_enemy_energy', 'destination_adjacent_enemy_energy',
    'current_stacked_enemy_energy', 'destination_stacked_enemy_energy',
)
SCHEMA_VERSION = 1
FEATURE_VERSION = 'holder_public_v1'
ELIGIBILITY_VERSION = 'holder_eligibility_v1'
CADENCE = dict(version='scored_opportunities_v1', max_opportunities=8,
               min_step_gap=12, reset='new_game')
HORIZON = 12
RIDGE_ALPHA = 0.1
THRESHOLD = 1.0
BASELINE_SHA256 = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
_HEAD_KEYS = {'schema_version', 'feature_version', 'feature_names', 'eligibility_version',
              'cadence', 'horizon', 'mean', 'scale', 'coefficients', 'intercept',
              'ridge_alpha', 'threshold', 'baseline_sha256', 'provenance'}
_DIRECTIONS = ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0))


class InsufficientTrainingData(ValueError):
    """The predeclared minimum amount of training information was not reached."""


def _number(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.number)):
        raise ValueError(f'{name} must be numeric')
    result = float(value)
    if not np.isfinite(result):
        raise ValueError(f'{name} must be finite')
    return result


def _integer(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f'{name} must be an integer')
    return int(value)


def _array(value, name, shape=None):
    try:
        arr = np.asarray(value, dtype=np.float64)
    except (ValueError, TypeError) as exc:
        raise ValueError(f'{name} must be a numeric array') from exc
    if not np.all(np.isfinite(arr)) or (shape is not None and arr.shape != shape):
        raise ValueError(f'{name} has invalid shape or nonfinite values')
    return arr


def feature_vector(candidate):
    """Return the sixteen fixed features using only candidate public fields.

    Coordinates and directions already occupy the agent's canonical space, for
    both player sides. Unused candidate data is deliberately never traversed.
    """
    try:
        public = candidate['public']
        uid = _integer(candidate['uid'], 'uid')
        proposal = _integer(candidate['proposal'], 'proposal')
        q, mask = candidate['q'], candidate['mask']
        if proposal not in (1, 2, 3, 4) or len(q) not in (5, 6) or len(mask) != len(q):
            raise ValueError('Expected a legal move and five or six q/mask entries')
        if not all(isinstance(v, (bool, np.bool_)) for v in mask):
            raise ValueError('mask entries must be boolean')
        if not mask[0] or not mask[proposal]:
            raise ValueError('STAY and proposal must be legal')
        legal_q = []
        for index, allowed in enumerate(mask):
            if allowed:
                legal_q.append(_number(q[index], 'legal q'))
            elif q[index] is not None:
                raise ValueError('Illegal q entries must be None')
        positions = _array(public['ally_pos'], 'ally_pos')
        energies = _array(public['ally_ene'], 'ally_ene')
        if positions.ndim != 2 or positions.shape[1] != 2 or energies.shape != (len(positions),):
            raise ValueError('Own position and energy arrays must align')
        if not 0 <= uid < len(positions) or energies[uid] < 0:
            raise ValueError('Candidate must identify a live own unit')
        if not np.all(positions[uid] == np.floor(positions[uid])):
            raise ValueError('Position must be integral')
        p = positions[uid].astype(np.int64)
        d = p + _DIRECTIONS[proposal]
        energy_map = _array(public['energy_map'], 'energy_map')
        nebula = _array(public['nebula'], 'nebula', energy_map.shape)
        if energy_map.ndim != 2 or not np.all(np.isin(nebula, [0., 1.])):
            raise ValueError('Expected two dimensional maps and boolean nebula values')
        if any(np.any(pos < 0) or np.any(pos >= energy_map.shape) for pos in (p, d)):
            raise ValueError('Position and destination must be within public map')
        enemy_energy = _array(public['enemy_energies'], 'enemy_energies')
        enemy_pos = _array(public['enemy_coords'], 'enemy_coords')
        # Recorded empty coordinates are JSON [], not an array of shape (0,2).
        if enemy_pos.size == 0:
            enemy_pos = enemy_pos.reshape(0, 2)
        if enemy_pos.ndim != 2 or enemy_pos.shape[1] != 2 or enemy_energy.shape != (len(enemy_pos),):
            raise ValueError('Enemy position and energy arrays must align')
        visible = enemy_energy >= 0
        enemy_pos, enemy_energy = enemy_pos[visible], enemy_energy[visible]
        cost = _number(public['sap_cost'], 'sap_cost')
        radius = _number(public['sap_range'], 'sap_range')
        move_cost = _number(public['move_cost'], 'move_cost')
        ms = _number(public['match_step'], 'match_step')
        maximum = _number(public['max_match_steps'], 'max_match_steps')
        if maximum <= 0 or not 1 <= ms <= maximum or cost < 0 or radius < 0 or move_cost < 0:
            raise ValueError('Invalid public costs, range, or match step')
        armed = enemy_energy >= cost
        distance_p, distance_d = np.abs(enemy_pos - p), np.abs(enemy_pos - d)
        at_p, at_d = distance_p.sum(axis=1), distance_d.sum(axis=1)
        span = max(legal_q) - min(legal_q)
        x = np.array([
            np.clip((float(q[proposal]) - float(q[0])) / max(span, 1e-6), -1, 1),
            np.clip(energies[uid] / 400, 0, 1), move_cost / 5, cost / 50,
            (maximum - ms + 1) / maximum,
            np.tanh((_number(public['own_points'], 'own_points') -
                     _number(public['opp_points'], 'opp_points')) / 20),
            np.clip(energy_map[tuple(p)] / 20, -1, 1),
            np.clip(energy_map[tuple(d)] / 20, -1, 1),
            nebula[tuple(p)], nebula[tuple(d)],
            np.count_nonzero(armed & (distance_p.max(axis=1) <= radius)) / 16,
            np.count_nonzero(armed & (distance_d.max(axis=1) <= radius)) / 16,
            enemy_energy[at_p == 1].sum() / 6400, enemy_energy[at_d == 1].sum() / 6400,
            enemy_energy[at_p == 0].sum() / 6400, enemy_energy[at_d == 0].sum() / 6400,
        ], dtype=np.float64)
        if not np.all(np.isfinite(x)):
            raise ValueError('Nonfinite derived feature')
        return x
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError('Malformed public candidate') from exc


def _json_copy(value, name):
    def check(obj):
        if isinstance(obj, dict):
            if not all(isinstance(key, str) for key in obj):
                raise ValueError(f'{name} JSON keys must be strings')
            for item in obj.values(): check(item)
        elif isinstance(obj, list):
            for item in obj: check(item)
        elif obj is not None and type(obj) not in (str, bool, int, float):
            raise ValueError(f'{name} must contain exact JSON types')
    check(value)
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f'{name} must be finite JSON data') from exc


def _provenance(value):
    if not isinstance(value, dict) or value.get('baseline_sha256') != BASELINE_SHA256:
        raise ValueError('provenance must identify the fixed V14 baseline SHA-256')
    return _json_copy(value, 'provenance')


def validate_head(head):
    """Strictly validate schema and fixed policy constants; return a detached copy."""
    if not isinstance(head, dict) or set(head) != _HEAD_KEYS:
        raise ValueError('Head keys do not match schema v1')
    fixed = dict(schema_version=SCHEMA_VERSION, feature_version=FEATURE_VERSION,
                 feature_names=list(FEATURE_NAMES), eligibility_version=ELIGIBILITY_VERSION,
                 cadence=CADENCE, horizon=HORIZON, ridge_alpha=RIDGE_ALPHA,
                 threshold=THRESHOLD, baseline_sha256=BASELINE_SHA256)
    for name, wanted in fixed.items():
        if head[name] != wanted:
            raise ValueError(f'Unexpected head {name}')
    _integer(head['schema_version'], 'schema_version')
    _integer(head['horizon'], 'horizon')
    for name in ('max_opportunities', 'min_step_gap'):
        _integer(head['cadence'][name], f'cadence {name}')
    _number(head['ridge_alpha'], 'ridge_alpha')
    _number(head['threshold'], 'threshold')
    for name in ('mean', 'scale', 'coefficients'):
        if not isinstance(head[name], list):
            raise ValueError(f'{name} must be a JSON list')
        for v in head[name]: _number(v, name)
        arr = _array(head[name], name, (16,))
        if name == 'scale' and np.any(arr <= 0):
            raise ValueError('Scales must be positive')
    _number(head['intercept'], 'intercept')
    _provenance(head['provenance'])
    return _json_copy(head, 'head')


def _rows(rows):
    seeds, features, labels = [], [], []
    for row in rows:
        if not isinstance(row, Mapping) or not {'seed', 'side', 'candidate', 'label'} <= row.keys():
            raise ValueError('Each row must be a complete seed/side/candidate/label pair')
        seed = _integer(row['seed'], 'seed')
        if seed < 0 or row['side'] not in ('player_0', 'player_1'):
            raise ValueError('Invalid seed or side')
        seeds.append(seed)
        features.append(feature_vector(row['candidate']))
        labels.append(_number(row['label'], 'label'))
    return np.array(seeds, dtype=np.int64), np.array(features, dtype=np.float64).reshape(-1, 16), np.array(labels, dtype=np.float64)


def _weights(seeds):
    counts = Counter(map(int, seeds))
    return np.array([1 / (len(counts) * counts[int(seed)]) for seed in seeds], dtype=np.float64)


def _transform(head, x):
    return np.clip((x - np.asarray(head['mean'])) / np.asarray(head['scale']), -5, 5)


def fit_head(rows, *, provenance):
    """Fit exactly one float64 map-balanced ridge head, using training rows only."""
    provenance = _provenance(provenance)
    seeds, x, y = _rows(rows)
    positive_maps = len(set(map(int, seeds[y > 0])))
    gates = dict(minimum_pairs=len(y) >= 96, minimum_maps=len(set(seeds)) >= 12,
                 minimum_positive_labels=int(np.count_nonzero(y > 0)) >= 12,
                 minimum_positive_maps=positive_maps >= 6)
    report = dict(pairs=len(y), represented_maps=len(set(seeds)),
                  positive_labels=int(np.count_nonzero(y > 0)), positive_maps=positive_maps,
                  gates=gates, passed=all(gates.values()))
    if not report['passed']:
        raise InsufficientTrainingData(f'Fixed training minima not reached: {report}')
    w = _weights(seeds)
    mean = np.sum(w[:, None] * x, axis=0)
    std = np.sqrt(np.sum(w[:, None] * (x - mean) ** 2, axis=0))
    scale = np.where(std < 1e-6, 1., std)
    z = np.clip((x - mean) / scale, -5, 5)
    design = np.column_stack((np.ones(len(y)), z))
    penalty = np.diag([0.] + [RIDGE_ALPHA] * 16)
    solution = np.linalg.solve(design.T @ (w[:, None] * design) + penalty,
                               design.T @ (w * y))
    head = dict(schema_version=SCHEMA_VERSION, feature_version=FEATURE_VERSION,
                feature_names=list(FEATURE_NAMES), eligibility_version=ELIGIBILITY_VERSION,
                cadence=CADENCE.copy(), horizon=HORIZON, mean=mean.tolist(), scale=scale.tolist(),
                coefficients=solution[1:].tolist(), intercept=float(solution[0]),
                ridge_alpha=RIDGE_ALPHA, threshold=THRESHOLD,
                baseline_sha256=BASELINE_SHA256, provenance=provenance)
    return validate_head(head), report


def predict_gain(head, candidate):
    """Predict points gained; deployment accepts HOLD only when this is >1.0."""
    head = validate_head(head)
    prediction = float(head['intercept'] + np.asarray(head['coefficients']) @
                       _transform(head, feature_vector(candidate)))
    if not np.isfinite(prediction):
        raise ValueError('Nonfinite prediction')
    return prediction


def validation_report(head, rows, validation_seeds):
    """Screen a frozen head on all eight maps; never fit or modify the head.

    Map gains are counterfactual opportunity proxies, not repeated-policy wins.
    Weighted MSE balances the represented maps; zero-pair maps enter the gain
    proxy as zero without fabricating MSE observations.
    """
    head = validate_head(head)
    validation_seeds = [_integer(seed, 'validation seed') for seed in validation_seeds]
    if len(validation_seeds) != 8 or len(set(validation_seeds)) != 8 or min(validation_seeds) < 0:
        raise ValueError('Exactly eight distinct validation maps are required')
    seeds, x, y = _rows(rows)
    if not set(map(int, seeds)) <= set(validation_seeds):
        raise ValueError('Rows include maps outside the fixed validation split')
    predictions = head['intercept'] + _transform(head, x) @ np.asarray(head['coefficients'])
    if not np.all(np.isfinite(predictions)):
        raise ValueError('Nonfinite predictions')
    chosen = predictions > THRESHOLD
    selected_y = y[chosen]
    gains = np.array([.5 * y[chosen & (seeds == seed)].sum() for seed in validation_seeds])
    bootstrap = np.random.default_rng(0).choice(gains, size=(5000, 8), replace=True).mean(axis=1)
    lower = float(np.percentile(bootstrap, 2.5))
    selected_maps = len(set(map(int, seeds[chosen])))
    mean_gain = float(gains.mean())
    gates = dict(minimum_pairs=len(y) >= 32, minimum_maps=len(set(seeds)) >= 4,
                 minimum_selected=int(chosen.sum()) >= 8, minimum_selected_maps=selected_maps >= 4,
                 positive_mean_map_gain=mean_gain > 0, positive_bootstrap_lower=lower > 0)
    errors = (predictions - y) ** 2
    return dict(pairs=len(y), represented_maps=len(set(seeds)), selected=int(chosen.sum()),
                selected_maps=selected_maps, selected_positive=int(np.count_nonzero(selected_y > 0)),
                selected_zero=int(np.count_nonzero(selected_y == 0)),
                selected_negative=int(np.count_nonzero(selected_y < 0)),
                total_selected_gain=float(selected_y.sum()),
                selected_mean_gain=float(selected_y.mean()) if len(selected_y) else None,
                map_gains=[dict(seed=seed, gain=float(gain)) for seed, gain in zip(validation_seeds, gains)],
                mean_map_gain=mean_gain, bootstrap_lower_025=lower,
                weighted_mse=float(_weights(seeds) @ errors) if len(y) else None,
                unweighted_mse=float(errors.mean()) if len(y) else None,
                gates=gates, passed=all(gates.values()))
