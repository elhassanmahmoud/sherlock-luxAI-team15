"""Pure-data, predeclared curriculum screening and confirmation gates.

Wire API (all reports are JSON serializable, rates are fractions, not percent):
* summarize_method({'47': {'control': CSV, 'early': CSV}, '48': ..., '49': ...})
  reads exactly six final game CSVs on maps 500720..500779. Returns per_start,
  mean, positive_pairs, passed, input_hashes and uncertainty. No intermediate
  checkpoint input is accepted. The caller binds paths to its audited study.
* compare_evaluations(candidate_csv, reference_csv, seeds, opponents=OPPONENTS)
  returns {'opponents': {label: summary}, 'input_hashes': ...} after exact-key
  validation of BOTH files. candidate_gate consumes that serialized report.
* direct_gate(rows, expected_opponent='self:/absolute/frozen/v3.pth') requires
  maps 511200..511399. The study caller must supply its exact frozen V3 label.

Each comparison summary carries delta_half_wins / result_units as the exact
rate difference; result_units = 2 * games. Floating rates are display values.
Intervals resample whole maps 5000 times with seed 0; the method mean keeps
both sides and all three fixed starts together. No model imports or jobs.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from scripts.early_curriculum_study import GAME_FIELDS, digest, read_rows, require

STARTS = ('47', '48', '49')
ARMS = ('control', 'early')
OPPONENTS = ('default', 'solution92')
SIDES = ('player_0', 'player_1')
METHOD_MAPS = tuple(range(500720, 500780))
BOOTSTRAP = {'samples': 5000, 'seed': 0, 'percentiles': [2.5, 97.5], 'unit': 'whole map'}
UNCERTAINTY = ('Explorative screening at three known starts; intervals describe map '
               'uncertainty conditional on these fixed starts, not uncertainty over new '
               'training starts or general confirmation of the training method.')


def _number(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'Invalid numeric {label}') from exc
    require(math.isfinite(number), f'Non-finite {label}')
    return number


def validate_keys(rows, seeds, opponents):
    """Require full production game schema, valid measurements and exact keys.

    Evaluation tables have no loss column/NaN exception. The narrowly scoped
    initial training-loss exception belongs to the study's training auditor.
    """
    seeds, opponents = tuple(seeds), tuple(opponents)
    require(seeds and len(set(seeds)) == len(seeds) and all(
        isinstance(s, int) and not isinstance(s, bool) and s >= 0 for s in seeds), 'Invalid expected seeds')
    require(opponents and len(set(opponents)) == len(opponents) and all(
        isinstance(o, str) and o.strip() == o and o for o in opponents), 'Invalid expected opponents')
    expected = {(seed, side, opponent) for seed in seeds for side in SIDES for opponent in opponents}
    actual = []
    for row in rows:
        require(set(row) == set(GAME_FIELDS), 'Incomplete or unexpected game schema')
        require(all(value is not None and value != '' for value in row.values()), 'Missing game value')
        numbers = {key: _number(value, key) for key, value in row.items() if key not in ('side', 'opponent')}
        require(numbers['seed'].is_integer() and numbers['seed'] >= 0, 'Invalid seed')
        require(numbers['steps'] == 303, 'Incomplete course game')
        require(numbers['point_counting_version'] == 2, 'Wrong point counting version')
        own, other = numbers['our_wins'], numbers['opp_wins']
        require(own.is_integer() and other.is_integer() and min(own, other) >= 0 and own + other <= 3,
                'Invalid match wins')
        result = 1 if own > other else 0 if own < other else .5
        require(numbers['result'] == result and numbers['game_win'] == int(own > other), 'Inconsistent game result')
        ours, theirs = numbers['our_points'], numbers['opp_points']
        require(min(ours, theirs) >= 0, 'Invalid points')
        require(numbers['point_win'] == (1 if ours > theirs else 0 if ours < theirs else .5),
                'Inconsistent point result')
        require(row['side'] in SIDES and row['opponent'] in opponents, 'Unexpected side/opponent')
        actual.append((int(numbers['seed']), row['side'], row['opponent']))
    require(len(actual) == len(expected) and set(actual) == expected, 'Incomplete or duplicated game keys')


def _load(path, seeds, opponents):
    # Hash around parsing so a concurrently replaced input is never silently bound.
    before = digest(path)
    rows = read_rows(path)
    validate_keys(rows, seeds, opponents)
    require(digest(path) == before, 'Input changed during analysis')
    return rows, before


def _map_units(rows, seeds, opponent):
    by_map = {seed: 0 for seed in seeds}
    for row in rows:
        if row['opponent'] == opponent:
            by_map[int(float(row['seed']))] += int(2 * float(row['result']))
    return np.array([by_map[seed] for seed in sorted(seeds)], dtype=np.int64)


def _interval(map_units, units_per_map):
    # Integer map totals keep paired arms/sides/starts together before division.
    draws = np.random.default_rng(0).choice(map_units, size=(5000, len(map_units)), replace=True)
    limits = np.percentile(draws.sum(axis=1), [2.5, 97.5]) / (len(map_units) * units_per_map)
    return [float(value) for value in limits]


def _comparison(candidate, reference, starts=1):
    delta = candidate - reference
    games = len(delta) * 2 * starts
    denominator = 2 * games
    low, high = _interval(delta, 4 * starts)
    candidate_total, reference_total = int(candidate.sum()), int(reference.sum())
    return dict(maps=len(delta), games=games, starts=starts,
                candidate_half_wins=candidate_total, reference_half_wins=reference_total,
                delta_half_wins=candidate_total - reference_total, result_units=denominator,
                winrate=candidate_total / denominator, ref_winrate=reference_total / denominator,
                delta=(candidate_total - reference_total) / denominator, low=low, high=high)


def summarize_method(pairs):
    """Analyze exactly the three fixed starts and six explicitly bound final CSVs."""
    require(isinstance(pairs, dict) and set(pairs) == set(STARTS), 'Expected exactly starts 47, 48, 49')
    require(all(isinstance(pairs[s], dict) and set(pairs[s]) == set(ARMS) for s in STARTS),
            'Expected exactly control/early final CSVs per start')
    paths = [Path(pairs[s][arm]).resolve(strict=True) for s in STARTS for arm in ARMS]
    require(len(set(paths)) == 6 and len({(p.stat().st_dev, p.stat().st_ino) for p in paths}) == 6,
            'Six distinct final CSV files required')
    per_start, input_hashes, units = {}, {}, {}
    for start in STARTS:
        units[start] = {}
        for arm in ARMS:
            path = Path(pairs[start][arm]).resolve()
            rows, sha = _load(path, METHOD_MAPS, OPPONENTS)
            input_hashes[str(path)] = sha
            units[start][arm] = {o: _map_units(rows, METHOD_MAPS, o) for o in OPPONENTS}
        per_start[start] = {o: _comparison(units[start]['early'][o], units[start]['control'][o]) for o in OPPONENTS}
    mean = {o: _comparison(sum(units[s]['early'][o] for s in STARTS),
                           sum(units[s]['control'][o] for s in STARTS), starts=3) for o in OPPONENTS}
    sol, default = mean['solution92'], mean['default']
    positive = sum(per_start[s]['solution92']['delta_half_wins'] > 0 for s in STARTS)
    passed = (100 * sol['delta_half_wins'] >= 3 * sol['result_units'] and positive >= 2
              and 100 * default['delta_half_wins'] >= -2 * default['result_units'])
    return dict(per_start=per_start, mean=mean, positive_pairs=positive, passed=passed,
                input_hashes=input_hashes, bootstrap=dict(BOOTSTRAP), uncertainty=UNCERTAINTY)


def compare_evaluations(candidate, reference, seeds, opponents=OPPONENTS):
    """Compare complete tables on an explicitly declared map/opponent set."""
    seeds, opponents = tuple(seeds), tuple(opponents)
    candidate, reference = Path(candidate).resolve(), Path(reference).resolve()
    c_rows, c_hash = _load(candidate, seeds, opponents)
    r_rows, r_hash = _load(reference, seeds, opponents)
    return dict(opponents={o: _comparison(_map_units(c_rows, seeds, o), _map_units(r_rows, seeds, o))
                           for o in opponents},
                input_hashes={str(candidate): c_hash, str(reference): r_hash},
                bootstrap=dict(BOOTSTRAP),
                uncertainty='Map uncertainty conditional on these fixed candidate/reference agents.')


def candidate_gate(comparison):
    """Require positive Sol difference/CI and Default loss at most two pp.

    Mandatory exact integer delta_half_wins and result_units are authoritative;
    rounded display fields cannot change a decision. Missing/invalid data raises.
    """
    require(isinstance(comparison, dict) and isinstance(comparison.get('opponents'), dict)
            and set(comparison['opponents']) == set(OPPONENTS), 'Expected exactly default/solution92 summaries')
    for summary in comparison['opponents'].values():
        require(isinstance(summary, dict), 'Invalid opponent summary')
        delta, denominator = summary.get('delta_half_wins'), summary.get('result_units')
        require(type(delta) is int and type(denominator) is int and denominator > 0
                and abs(delta) <= denominator, 'Missing/invalid exact counts')
        low, high = _number(summary.get('low'), 'lower CI'), _number(summary.get('high'), 'upper CI')
        require(-1 <= low <= high <= 1, 'Invalid confidence interval')
    sol, default = (comparison['opponents'][o] for o in ('solution92', 'default'))
    require(sol['result_units'] == default['result_units'], 'Unequal opponent denominators')
    return (sol['delta_half_wins'] > 0 and float(sol['low']) > 0
            and 100 * default['delta_half_wins'] >= -2 * default['result_units'])


def direct_gate(rows, *, expected_opponent=None):
    """Absolute candidate result on reserved direct maps; lower CI strictly > .5.

    Without expected_opponent the table must still contain exactly one absolute
    self: label; callers with a frozen study must bind its exact reference label.
    """
    rows = list(rows)
    labels = {row.get('opponent') for row in rows}
    require(len(labels) == 1, 'Expected one direct opponent')
    opponent = next(iter(labels))
    require(isinstance(opponent, str) and opponent.startswith('self:')
            and Path(opponent[5:]).is_absolute(), 'Expected absolute self opponent')
    require(expected_opponent is None or opponent == expected_opponent, 'Wrong direct opponent')
    seeds = tuple(range(511200, 511400))
    validate_keys(rows, seeds, (opponent,))
    units = _map_units(rows, seeds, opponent)
    low, high = _interval(units, 4)
    numerator, denominator = int(units.sum()), len(rows) * 2
    return dict(opponent=opponent, maps=len(seeds), games=len(rows), result_half_wins=numerator,
                result_units=denominator, winrate=numerator / denominator, low=low, high=high,
                passed=low > .5, bootstrap=dict(BOOTSTRAP),
                uncertainty='Map uncertainty conditional on these fixed candidate/reference agents.')
