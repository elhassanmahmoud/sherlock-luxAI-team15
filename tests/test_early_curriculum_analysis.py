"""Pure-data contracts for the predeclared curriculum gates."""
import csv
import importlib
import hashlib
from pathlib import Path
import json
import subprocess
import sys

import numpy as np
import pytest

from scripts.early_curriculum_study import GAME_FIELDS


@pytest.fixture
def analysis():
    assert importlib.util.find_spec('scripts.early_curriculum_analysis'), 'Analysis module is missing'
    return importlib.import_module('scripts.early_curriculum_analysis')


def rows(seeds=range(500720, 500780), opponents=('default', 'solution92'), result=0.5):
    out = []
    for opponent in opponents:
        for seed in seeds:
            for side in ('player_0', 'player_1'):
                row = dict.fromkeys(GAME_FIELDS, 0)
                row.update(seed=seed, side=side, opponent=opponent, steps=303,
                           point_counting_version=2, point_win=.5)
                set_result(row, result)
                out.append(row)
    return out


def set_result(row, value):
    row.update(result=value, game_win=int(value == 1), our_wins=int(value == 1),
               opp_wins=int(value == 0))


def save(path, data):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=GAME_FIELDS)
        writer.writeheader()
        writer.writerows(data)
    return str(path)


def pairs(tmp_path, deltas=(8, 8, 6), default_deltas=(0, 0, 0)):
    """Integer half-win gains over 120 draws per opponent per start."""
    out = {}
    for seed, gain, default_gain in zip((47, 48, 49), deltas, default_deltas):
        control, early = rows(), rows()
        for opponent, difference in [('solution92', gain), ('default', default_gain)]:
            group = [r for r in early if r['opponent'] == opponent]
            for row in group[:abs(difference)]:
                set_result(row, 1 if difference > 0 else 0)
        out[str(seed)] = {arm: save(tmp_path / f's{seed}_{arm}.csv', data)
                          for arm, data in [('control', control), ('early', early)]}
    return out


def test_light_import(analysis):
    completed = subprocess.run([sys.executable, '-c',
        "import sys; import scripts.early_curriculum_analysis; assert 'torch' not in sys.modules; assert 'scripts.experiment' not in sys.modules"], capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'foreign_seed', 'foreign_opponent',
    'fractional_seed', 'bad_side', 'nan', 'infinity', 'result', 'wins', 'game_win', 'points',
    'point_win', 'version', 'steps', 'fractional_steps', 'schema', 'extra', 'missing_value'])
def test_rejects_invalid_full_game_tables(analysis, change):
    data = rows(range(2))
    changes = {'foreign_seed': ('seed', 99), 'foreign_opponent': ('opponent', 'other'),
        'fractional_seed': ('seed', .1), 'bad_side': ('side', 'player_2'),
        'nan': ('wait_frac', float('nan')), 'infinity': ('secs', float('inf')),
        'result': ('result', .25), 'wins': ('our_wins', 4), 'game_win': ('game_win', 1),
        'points': ('our_points', -1), 'point_win': ('point_win', 0),
        'version': ('point_counting_version', 1), 'steps': ('steps', 302),
        'fractional_steps': ('steps', 303.5), 'extra': ('mean_loss', float('nan')),
        'missing_value': ('secs', '')}
    if change == 'missing':
        data.pop()
    elif change == 'duplicate':
        data[-1] = data[0].copy()
    elif change == 'schema':
        del data[0]['secs']
    else:
        key, value = changes[change]
        data[0][key] = value
    with pytest.raises(ValueError):
        analysis.validate_keys(data, range(2), ('default', 'solution92'))


def test_complete_tables_accept_numeric_csv_strings(analysis):
    data = [{k: str(v) for k, v in r.items()} for r in rows(range(2))]
    analysis.validate_keys(data, range(2), ('default', 'solution92'))


@pytest.mark.parametrize('deltas,default_deltas,passed', [
    ((8, 8, 6), (0, 0, 0), True),       # 22/720 exceeds 3 pp
    ((7, 7, 7), (0, 0, 0), False),      # 21/720 falls short
    ((22, 0, 0), (0, 0, 0), False),     # only one positive start
    ((8, 8, 6), (-5, -5, -4), True),    # -14/720 within 2 pp
    ((8, 8, 6), (-5, -5, -5), False),
])
def test_method_uses_exact_counts_and_two_positive_starts(analysis, tmp_path, deltas, default_deltas, passed):
    report = analysis.summarize_method(pairs(tmp_path, deltas, default_deltas))
    assert report['passed'] is passed
    assert report['mean']['solution92']['delta_half_wins'] == sum(deltas)
    assert report['mean']['solution92']['result_units'] == 720
    assert report['mean']['solution92']['delta'] == sum(deltas) / 720
    assert len(report['input_hashes']) == 6
    assert report['positive_pairs'] == sum(d > 0 for d in deltas)
    assert json.loads(json.dumps(report, allow_nan=False)) == report
    assert 'known starts' in report['uncertainty']


@pytest.mark.parametrize('change', ['missing_start', 'extra_start', 'missing_arm', 'extra_arm', 'alias', 'missing_row', 'wrong_map', 'header'])
def test_method_rejects_incomplete_or_unbound_six_files(analysis, tmp_path, change):
    inputs = pairs(tmp_path)
    if change == 'missing_start': del inputs['49']
    elif change == 'extra_start': inputs['50'] = inputs['49']
    elif change == 'missing_arm': del inputs['49']['early']
    elif change == 'extra_arm': inputs['49']['intermediate'] = inputs['49']['early']
    elif change == 'alias': inputs['49']['early'] = inputs['48']['early']
    else:
        path = tmp_path / 's49_early.csv'
        data = rows()
        if change == 'missing_row': data.pop()
        elif change == 'wrong_map': data[0]['seed'] = 500719
        save(path, data)
        if change == 'header': path.write_text(path.read_text().replace('secs', 'mean_loss', 1))
    with pytest.raises(ValueError): analysis.summarize_method(inputs)


def test_method_bootstrap_preserves_shared_maps_across_sides_and_starts(analysis, tmp_path):
    inputs = pairs(tmp_path, (0, 0, 0))
    # Start 47 improves first half of maps, 48 the second half; 49 stays equal.
    # The three-start mean is exactly 1/6 on EVERY map: shared-map CI is degenerate.
    for start, first_half in [('47', True), ('48', False)]:
        data = rows()
        for row in data:
            if row['opponent'] == 'solution92' and (row['seed'] < 500750) == first_half:
                set_result(row, 1)
        save(tmp_path / f's{start}_early.csv', data)
    report = analysis.summarize_method(inputs)
    assert report['mean']['solution92']['delta'] == 1 / 6
    assert report['mean']['solution92']['low'] == 1 / 6
    assert report['mean']['solution92']['high'] == 1 / 6
    assert report['per_start']['49']['solution92']['delta'] == 0
    assert report['passed'] is True
    # Byte hashes change with order, statistics must not.
    for paths in inputs.values():
        for path in paths.values():
            with open(path, newline='') as stream: data = list(csv.DictReader(stream))
            save(Path(path), list(reversed(data)))
    reordered = analysis.summarize_method(inputs)
    assert reordered['mean'] == report['mean']
    assert reordered['per_start'] == report['per_start']


def test_comparison_bootstrap_clusters_both_sides_and_matches_fixed_draws(analysis, tmp_path):
    control, candidate = rows(range(4)), rows(range(4))
    for row in candidate:
        if row['opponent'] == 'solution92': set_result(row, int(row['seed'] < 2))
        else: set_result(row, int(row['side'] == 'player_0'))
    report = analysis.compare_evaluations(save(tmp_path / 'c.csv', candidate), save(tmp_path / 'r.csv', control), range(4))
    assert report['opponents']['default']['low'] == report['opponents']['default']['high'] == 0
    expected = np.percentile(np.random.default_rng(0).choice([.5, .5, -.5, -.5], (5000, 4)).mean(axis=1), [2.5, 97.5])
    assert [report['opponents']['solution92'][k] for k in ('low', 'high')] == list(expected)
    candidate.pop()
    save(tmp_path / 'c.csv', candidate)
    with pytest.raises(ValueError): analysis.compare_evaluations(tmp_path / 'c.csv', tmp_path / 'r.csv', range(4))


@pytest.mark.parametrize('sol,low,default,passed', [(1, .001, -16, True), (0, .001, 0, False),
    (1, 0, 0, False), (1, -.001, 0, False), (1, .001, -17, False)])
def test_candidate_exact_default_boundary_and_strict_sol_interval(analysis, sol, low, default, passed):
    comparison = {'opponents': {opp: {'delta_half_wins': d, 'result_units': 800,
        'low': lo, 'high': .1, 'delta': 999} for opp, d, lo in
        [('solution92', sol, low), ('default', default, -.1)]}}
    assert analysis.candidate_gate(comparison) is passed


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), None])
def test_candidate_rejects_invalid_interval(analysis, bad):
    report = {'opponents': {o: {'delta_half_wins': 1, 'result_units': 800, 'low': bad, 'high': .2}
                           for o in ('default', 'solution92')}}
    with pytest.raises(ValueError): analysis.candidate_gate(report)


def test_direct_gate_is_absolute_strict_and_has_fixed_keys(analysis):
    data = rows(range(511200, 511400), ('self:/frozen/v3.pth',))
    assert analysis.direct_gate(data, expected_opponent='self:/frozen/v3.pth')['passed'] is False
    for row in data: set_result(row, int(row['side'] == 'player_0'))
    report = analysis.direct_gate(data)
    assert report['low'] == report['high'] == .5
    assert report['passed'] is False
    for row in data: set_result(row, 1)
    report = analysis.direct_gate(data)
    assert report['low'] == report['high'] == 1
    assert report['passed'] is True
    assert report['result_half_wins'] == report['result_units'] == 800
    with pytest.raises(ValueError): analysis.direct_gate(data[:-1])
    with pytest.raises(ValueError): analysis.direct_gate(data, expected_opponent='self:/other.pth')
    with pytest.raises(ValueError): analysis.direct_gate(rows(range(511200, 511400), ('solution92',)))


def test_method_does_not_add_a_confidence_interval_gate(analysis, tmp_path):
    inputs = pairs(tmp_path, (0, 0, 0))
    for start in ('47', '48', '49'):
        data = rows()
        for row in data:
            if row['opponent'] == 'solution92':
                set_result(row, int(row['seed'] < 500752))
        save(tmp_path / f's{start}_early.csv', data)
    report = analysis.summarize_method(inputs)
    assert report['mean']['solution92']['delta'] == 1 / 30
    assert report['mean']['solution92']['low'] < 0
    assert report['positive_pairs'] == 3
    assert report['passed'] is True
    for path, sha in report['input_hashes'].items():
        assert sha == hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.mark.parametrize('change', ['missing_counts', 'float_counts', 'wrong_opponent', 'missing_opponent',
                                   'wrong_denominator', 'zero_denominator', 'negative_denominator', 'impossible_counts'])
def test_candidate_gate_fails_closed_on_incomplete_exact_summaries(analysis, change):
    report = {'opponents': {o: {'delta_half_wins': 1, 'result_units': 800, 'low': .001, 'high': .1}
                           for o in ('default', 'solution92')}}
    sol = report['opponents']['solution92']
    if change == 'missing_counts': del sol['delta_half_wins']
    elif change == 'float_counts': sol['delta_half_wins'] = 1.0
    elif change == 'wrong_opponent': report['opponents']['intermediate'] = sol
    elif change == 'missing_opponent': del report['opponents']['default']
    elif change == 'wrong_denominator': sol['result_units'] = 240
    elif change == 'zero_denominator': sol['result_units'] = 0
    elif change == 'negative_denominator': sol['result_units'] = -800
    elif change == 'impossible_counts': sol['delta_half_wins'] = 801
    with pytest.raises(ValueError): analysis.candidate_gate(report)
