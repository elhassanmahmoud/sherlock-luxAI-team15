"""A partial or inconsistent CSV must never count as a completed night phase."""
import csv
import importlib.util
from pathlib import Path

import pytest

from scripts.experiment import GAME_FIELDS


def validator():
    path = Path(__file__).parents[1] / 'experiments/analysis/night_20261101/run_jobs.py'
    spec = importlib.util.spec_from_file_location('night_eval_journal', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_output


def input_validator():
    path = Path(__file__).parents[1] / 'experiments/analysis/night_20261101/run_jobs.py'
    spec = importlib.util.spec_from_file_location('night_eval_inputs', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_inputs


def rows():
    result = []
    for side in ('player_0', 'player_1'):
        r = dict.fromkeys(GAME_FIELDS, 0)
        r.update(seed=832000, side=side, opponent='solution92', result=1,
                 game_win=1, point_win=1, our_wins=2, opp_wins=1,
                 our_points=20, opp_points=10, steps=303, point_counting_version=2)
        result.append(r)
    return result


def write(path, data):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=GAME_FIELDS)
        writer.writeheader()
        writer.writerows(data)


ARGS = ['--first', '332000', '--n', '1', '--opponents', 'solution92']


def test_complete_both_side_game_pair_is_valid(tmp_path):
    path = tmp_path / 'ok.csv'
    write(path, rows())
    validator()(path, ARGS)


@pytest.mark.parametrize('defect', ['missing', 'duplicate', 'wrong_seed', 'wrong_opponent',
                                  'unfinished', 'old_points', 'result', 'points', 'nonfinite',
                                  'negative_time', 'negative_count', 'invalid_fraction'])
def test_incomplete_or_incoherent_measurement_is_rejected(tmp_path, defect):
    data = rows()
    if defect == 'missing':
        data.pop()
    elif defect == 'duplicate':
        data[1] = dict(data[0])
    else:
        key, value = {
            'wrong_seed': ('seed', 832001), 'wrong_opponent': ('opponent', 'default'),
            'unfinished': ('steps', 302), 'old_points': ('point_counting_version', 1),
            'result': ('result', 0), 'points': ('point_win', 0),
            'nonfinite': ('secs', float('nan')),
            'negative_time': ('secs', -1), 'negative_count': ('unit_steps', -1),
            'invalid_fraction': ('wait_frac', 2),
        }[defect]
        data[0][key] = value
    path = tmp_path / 'invalid.csv'
    write(path, data)
    with pytest.raises(AssertionError):
        validator()(path, ARGS)


def test_all_actual_weight_inputs_must_exist_and_be_frozen(tmp_path):
    own, opponent, cnn = [tmp_path / n for n in ('own.pth', 'opponent.pth', 'cnn.pth')]
    for p in (own, opponent, cnn):
        p.write_bytes(b'checkpoint')
    args = ['--weights', str(own), '--opponents', f'solution92,self:{opponent}',
            '--set', f'cnn={cnn}']
    check = input_validator()
    check(args, [own, opponent, cnn])
    with pytest.raises(ValueError, match='frozen'):
        check(args, [own, cnn])
    opponent.unlink()
    with pytest.raises(ValueError, match='Missing'):
        check(args, [own, opponent, cnn])
