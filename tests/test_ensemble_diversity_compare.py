"""Fixed study boundaries: complete keys, draw semantics, and one nominee."""
from __future__ import annotations

import csv

import pytest

from scripts import ensemble_diversity_compare as C
from scripts.early_curriculum_study import GAME_FIELDS


def game(seed=1400000, side='player_0', opponent='solution92', result=1):
    row = dict.fromkeys(GAME_FIELDS, 0)
    row.update(seed=seed, side=side, opponent=opponent, result=result,
               game_win=int(result == 1), point_win=result,
               our_wins=int(result == 1), opp_wins=int(result == 0),
               our_points=int(result == 1), opp_points=int(result == 0),
               point_counting_version=2, steps=303, secs=.1)
    return row


def job(opponent='solution92', games=4):
    return dict(name='A39_panel_0', role='A39', kind='panel',
                weights='experiments/candidates/ensemble_diversity_20261107/A39.pth',
                opponent=opponent, seed_list='seeds.json', expected_games=games, workers=1)


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, GAME_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_csv_accepts_complete_shuffled_keys_and_keeps_draws(tmp_path):
    rows = [game(seed, side, result=.5 if seed == 1400000 else 1)
            for seed in (1400000, 1400001) for side in ('player_0', 'player_1')]
    path = write_csv(tmp_path / 'games.csv', rows[::-1])
    actual = C.validate_job_csv(path, job(), [1400000, 1400001])
    assert len(actual) == 4
    assert sum(r['result'] for r in actual) == 3
    assert sum(r['game_win'] for r in actual) == 2


@pytest.mark.parametrize('damage', ['missing_map', 'missing_side', 'extra_map', 'duplicate',
                                    'wrong_opponent', 'fractional_seed', 'wrong_side'])
def test_csv_rejects_incomplete_or_wrong_exact_keys(tmp_path, damage):
    rows = [game(seed, side) for seed in (1400000, 1400001)
            for side in ('player_0', 'player_1')]
    if damage == 'missing_map':
        rows = rows[:2]
    elif damage == 'missing_side':
        rows = rows[:-1]
    elif damage == 'extra_map':
        rows += [game(1400002, side) for side in ('player_0', 'player_1')]
    elif damage == 'duplicate':
        rows[-1] = rows[0]
    else:
        column, value = {'wrong_opponent': ('opponent', 'default'),
                         'fractional_seed': ('seed', 1400000.5),
                         'wrong_side': ('side', 'player_2')}[damage]
        rows[0][column] = value
    with pytest.raises(ValueError):
        C.validate_job_csv(write_csv(tmp_path / 'bad.csv', rows), job(), [1400000, 1400001])


@pytest.mark.parametrize(('column', 'value'), [
    ('steps', 303.5), ('steps', 302), ('point_counting_version', 1),
    ('secs', float('inf')), ('secs', -1), ('result', .5), ('game_win', 0),
    ('point_win', 0), ('our_wins', 1.5), ('opp_wins', 3),
    ('our_points', -1), ('sap_hits', .5), ('invalid_frac', 1.1),
    ('wait_frac', float('nan')),
])
def test_csv_rejects_malformed_numeric_or_inconsistent_outcomes(tmp_path, column, value):
    rows = [game(1400000, side) for side in ('player_0', 'player_1')]
    rows[0][column] = value
    with pytest.raises(ValueError):
        C.validate_job_csv(write_csv(tmp_path / 'bad.csv', rows), job(games=2), [1400000])


@pytest.mark.parametrize('seeds', [[1400000, 1400000], [1400000.0], [True], [], [-1]])
def test_csv_rejects_invalid_expected_seed_list(tmp_path, seeds):
    path = write_csv(tmp_path / 'games.csv', [game()])
    with pytest.raises(ValueError):
        C.validate_job_csv(path, job(games=2 * len(seeds)), seeds)


def frame(opponents=C.OPPONENTS, *, first=1400000, maps=100, value=.5):
    import pandas as pd
    return pd.DataFrame([dict(opponent=opponent, seed=seed, side=side,
                              result=1. if opponent == 'default' else value,
                              game_win=int(opponent == 'default' or value == 1))
                         for opponent in opponents for seed in range(first, first + maps)
                         for side in ('player_0', 'player_1')])


def outcomes(df, opponent, values):
    mask = df['opponent'] == opponent
    assert mask.sum() == len(values)
    df.loc[mask, 'result'] = values
    df.loc[mask, 'game_win'] = [int(value == 1) for value in values]
    return df


def selected_frames():
    ref = frame()
    candidate = outcomes(frame(), 'sol92_sq', [1] * 12 + [.5] * 188)
    direct = frame((C.V14_LABEL,), first=1401000)
    return ref, candidate, direct


def test_selection_exact_boundary_and_draw_score_are_distinct_from_wins():
    result = C.selection_checks(*selected_frames(), name='A39')
    assert result['passed']
    assert result['panel_half_win_gain'] == 12
    assert result['panel']['delta'] == pytest.approx(.005)
    assert result['direct']['score'] == .5
    assert result['direct']['candidate'] == dict(games=200, wins=0, draws=200, losses=0,
                                                 half_wins=200, score=.5, strict_winrate=0.)
    assert result['nominable']


def test_selection_rejects_one_half_win_below_panel_boundary():
    ref, candidate, direct = selected_frames()
    outcomes(candidate, 'sol92_sq', [1] * 11 + [.5] * 189)
    result = C.selection_checks(ref, candidate, direct, name='A39')
    assert not result['checks']['panel_score_gain_ge_0.005']
    assert not result['passed']


def test_draws_cannot_mask_strict_default_winrate_failure():
    ref, candidate, direct = selected_frames()
    outcomes(candidate, 'default', [1] * 197 + [.5] * 2 + [0])
    result = C.selection_checks(ref, candidate, direct, name='A39')
    assert result['checks']['default_score_ge_0.99']
    assert not result['checks']['default_strict_winrate_ge_0.99']
    assert result['default']['candidate']['wins'] == 197
    assert result['default']['candidate']['draws'] == 2
    assert result['default']['candidate']['losses'] == 1
    assert not result['passed']


def test_draws_cannot_mask_strict_solution_regression():
    ref, candidate, direct = selected_frames()
    outcomes(ref, 'solution92', [1] * 100 + [0] * 100)
    outcomes(candidate, 'solution92', [1] * 99 + [.5] * 2 + [0] * 99)
    result = C.selection_checks(ref, candidate, direct, name='B39')
    assert result['checks']['solution92_score_nonnegative']
    assert not result['checks']['solution92_strict_winrate_nonnegative']
    assert not result['passed']


@pytest.mark.parametrize('target', ['reference', 'candidate', 'direct'])
def test_selection_helpers_refuse_common_incomplete_maps(target):
    ref, candidate, direct = selected_frames()
    inputs = dict(reference=ref, candidate=candidate, direct=direct)
    inputs[target] = inputs[target].iloc[2:]
    with pytest.raises(ValueError, match='keys'):
        C.selection_checks(**inputs, name='A39')


def ranked(panel=12, solution=0, passed=True):
    return dict(panel_half_win_gain=panel, solution_half_win_gain=solution, passed=passed)


def test_ranking_ignores_diagnostic_and_uses_integer_gains_then_netcount_then_name():
    results = {name: ranked() for name in C.NET_COUNTS}
    results['REPLACE36'] = ranked(panel=1000)
    assert C.choose_nominee(results) == 'A39'  # smaller than ALL42, alphabetical before B39
    results['B39'] = ranked(solution=1)
    assert C.choose_nominee(results) == 'B39'
    results['ALL42'] = ranked(panel=13)
    assert C.choose_nominee(results) == 'ALL42'
    results['ALL42']['passed'] = False
    assert C.choose_nominee(results) == 'B39'
    for row in results.values():
        row['passed'] = False
    assert C.choose_nominee(results) is None


def test_ranking_requires_all_four_candidates_even_if_one_already_passes():
    with pytest.raises(ValueError):
        C.choose_nominee({'A39': ranked()})


def confirmation_frames():
    ref = frame(first=1500000, maps=800)
    candidate = frame(first=1500000, maps=800)
    for opponent in C.LOCAL_SIX:
        outcomes(candidate, opponent, [1] * 32 + [.5] * 1568)
    direct = frame((C.V14_LABEL,), first=1600000, maps=400, value=1)
    return ref, candidate, direct


def test_confirmation_reuses_seven_gates_with_local_six_and_one_percent_delta():
    result = C.confirmation_checks(*confirmation_frames(), name='ALL42')
    assert result['passed']
    assert len(result['checks']) == 10
    assert result['panel']['delta'] == pytest.approx(.01)
    assert result['panel']['candidate']['games'] == 9600
    assert result['direct']['candidate']['games'] == 800


def test_confirmation_adds_nonnegative_solution_score_to_legacy_tolerance():
    ref, candidate, direct = confirmation_frames()
    outcomes(candidate, 'solution92', [0] * 8 + [.5] * 1592)
    result = C.confirmation_checks(ref, candidate, direct, name='A39')
    assert result['solution92']['delta'] == pytest.approx(-.0025)
    assert not result['checks']['solution92_score_nonnegative']
    assert not result['passed']


def test_confirmation_never_accepts_diagnostic_candidate():
    with pytest.raises(ValueError, match='nominee'):
        C.confirmation_checks(*confirmation_frames(), name='REPLACE36')


@pytest.fixture
def planned(tmp_path, monkeypatch):
    import hashlib
    import json
    plan = json.loads((C.ROOT / 'experiments/analysis/ensemble_diversity_20261107/selection_plan/jobs.json').read_text())
    root = tmp_path / 'root'
    root.mkdir()
    for role, path in plan['roles'].items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(role.encode())
    pinned = {}
    for path in plan['opponent_sha256']:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.encode())
        pinned[path] = hashlib.sha256(target.read_bytes()).hexdigest()
    monkeypatch.setattr(C, 'OPPONENT_SHA256', pinned)
    plan['opponent_sha256'] = pinned.copy()
    for item in plan['jobs']:
        path = root / item['seed_list']
        path.parent.mkdir(parents=True, exist_ok=True)
        first = 1401000 if item['kind'] == 'direct' else 1400000
        path.write_text(json.dumps(list(range(first, first + 100))))
    return root, plan


def test_plan_requires_the_frozen_39_job_inventory(planned):
    root, plan = planned
    jobs = C.validate_plan(plan, root)
    assert len(jobs) == 39
    assert sum(item['expected_games'] for item in jobs) == 7800
    assert jobs[0]['seeds'] == list(range(1400000, 1400100))
    assert 'seeds' not in plan['jobs'][0]  # validation does not mutate the frozen plan


@pytest.mark.parametrize('damage', ['missing', 'extra', 'duplicate', 'role', 'weights', 'opponent',
                                    'workers', 'games', 'total', 'hash', 'seed_path', 'seeds'])
def test_plan_rejects_changed_schedule_or_provenance(planned, damage):
    import copy
    import json
    root, plan = planned
    if damage == 'missing':
        plan['jobs'].pop()
    elif damage in ('extra', 'duplicate'):
        item = copy.deepcopy(plan['jobs'][0])
        if damage == 'extra':
            item['name'] = 'surprise'
        plan['jobs'].append(item)
    elif damage == 'total':
        plan['total_games'] = 7600
    elif damage == 'hash':
        plan['opponent_sha256'][C.V14_PATH] = '0' * 64
    elif damage == 'seeds':
        (root / plan['jobs'][0]['seed_list']).write_text(json.dumps(list(range(1400001, 1400101))))
    else:
        column, value = {'role': ('role', 'SURPRISE'), 'weights': ('weights', C.ROLE_PATHS['A39']),
                         'opponent': ('opponent', 'sol92_weak'), 'workers': ('workers', 2),
                         'games': ('expected_games', 198), 'seed_path': ('seed_list', '../escape.json')}[damage]
        plan['jobs'][0][column] = value
    with pytest.raises(ValueError):
        C.validate_plan(plan, root)


def test_plan_rejects_changed_opponent_file(planned):
    root, plan = planned
    (root / C.V14_PATH).write_bytes(b'changed')
    with pytest.raises(ValueError, match='hash'):
        C.validate_plan(plan, root)


def confirmation_plan(root, plan, nominee='A39'):
    import json
    plan['roles'] = {name: path for name, path in plan['roles'].items() if name in ('V14', nominee)}
    plan['jobs'] = [item for item in plan['jobs'] if item['role'] in plan['roles']]
    plan['total_games'] = 23200
    plan['nominee'] = nominee
    for item in plan['jobs']:
        direct = item['kind'] == 'direct'
        first, maps = (1600000, 400) if direct else (1500000, 800)
        item['expected_games'] = 2 * maps
        item['seed_list'] = item['seed_list'].replace('selection_plan', 'confirmation_plan')
        seed_file = root / item['seed_list']
        seed_file.parent.mkdir(parents=True, exist_ok=True)
        seed_file.write_text(json.dumps(list(range(first, first + maps))))
    return plan


def test_confirmation_plan_is_exactly_named_nominee_and_fresh_block(planned):
    root, plan = planned
    plan = confirmation_plan(root, plan)
    jobs = C.validate_plan(plan, root, phase='confirmation', nominee='A39')
    assert len(jobs) == 15
    assert sum(item['expected_games'] for item in jobs) == 23200
    with pytest.raises(ValueError, match='nominee|roles'):
        C.validate_plan(plan, root, phase='confirmation', nominee='B39')
    with pytest.raises(ValueError, match='nominee'):
        C.validate_plan(plan, root, phase='confirmation')


def completed_block(planned, *, phase='selection'):
    import hashlib
    import json
    import sys
    root, plan = planned
    if phase == 'confirmation':
        plan = confirmation_plan(root, plan)
    output = root / 'results'
    (output / 'receipts').mkdir(parents=True)
    source = root / 'source.py'
    source.write_text('# frozen synthetic source\n')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    provenance = {'model_sha256': {name: sha(root / path) for name, path in plan['roles'].items()},
                  'source_identity': {'head': 'a' * 40, 'files': {str(source): sha(source)}}}
    provenance_path = output / 'provenance.json'
    provenance_path.write_text(json.dumps(provenance))
    plan_path = root / 'jobs.json'
    plan_path.write_text(json.dumps(plan))
    for item in plan['jobs']:
        seeds = json.loads((root / item['seed_list']).read_text())
        rows = []
        for seed in seeds:
            for side in ('player_0', 'player_1'):
                index = 2 * (seed - seeds[0]) + int(side[-1])
                value = 1 if item['opponent'] == 'default' else .5
                if item['role'] != 'V14' and item['opponent'] == 'sol92_sq' and index < 12:
                    value = 1
                if phase == 'confirmation' and item['role'] != 'V14':
                    if item['kind'] == 'direct' or (item['opponent'] in C.LOCAL_SIX and index < 32):
                        value = 1
                if item['role'] == 'REPLACE36':
                    value = 1
                rows.append(game(seed, side, item['opponent'], value))
        csv_path = write_csv(output / f"{item['name']}.csv", rows)
        receipt = dict(status='complete', returncode=0, job_name=item['name'], phase=phase,
                       role=item['role'], opponent=item['opponent'], weights=item['weights'],
                       model_sha256=provenance['model_sha256'][item['role']],
                       seed_list_sha256=sha(root / item['seed_list']), csv_sha256=sha(csv_path),
                       rows=item['expected_games'], source_identity=provenance['source_identity'],
                       opponent_sha256=plan['opponent_sha256'],
                       command=[sys.executable, '-B', '-m', 'scripts.par_eval', '--weights', str(root / item['weights']),
                                '--seed-list', str(root / item['seed_list']), '--workers', '1',
                                '--opponents', item['opponent'], '--out', str(csv_path)])
        (output / 'receipts' / f"{item['name']}.json").write_text(json.dumps(receipt))
    return dict(jobs_json=plan_path, result_dir=output, root=root, provenance=provenance_path,
                phase=phase, nominee='A39' if phase == 'confirmation' else None)


@pytest.fixture
def completed(planned):
    return completed_block(planned)


def test_analyze_complete_selection_nominates_once_and_reports_all_games(completed):
    report = C.analyze(**completed)
    assert report['status'] == 'complete'
    assert (report['jobs'], report['games'], report['nominee']) == (39, 7800, 'A39')
    assert set(report['results']) == {'A39', 'B39', 'ALL42', 'REPLACE36'}
    assert report['results']['REPLACE36']['passed']
    assert not report['results']['REPLACE36']['nominable']
    assert len(report['input_sha256']['csv']) == 39


@pytest.mark.parametrize('damage', ['missing_csv', 'extra_csv', 'missing_receipt', 'extra_receipt',
                                    'csv_hash', 'model_hash', 'source_hash', 'seed_hash',
                                    'returncode', 'partial', 'command', 'receipt_role', 'receipt_source'])
def test_analyze_rejects_unbound_or_incomplete_inputs_before_statistics(completed, monkeypatch, damage):
    import json
    output = completed['result_dir']
    csv_path = output / 'A39_panel_0.csv'
    receipt_path = output / 'receipts/A39_panel_0.json'
    if damage == 'missing_csv':
        csv_path.unlink()
    elif damage == 'extra_csv':
        (output / 'extra.csv').write_text(csv_path.read_text())
    elif damage == 'missing_receipt':
        receipt_path.unlink()
    elif damage == 'extra_receipt':
        (output / 'receipts/extra.json').write_text(receipt_path.read_text())
    elif damage == 'csv_hash':
        csv_path.write_text(csv_path.read_text() + '\n')
    elif damage == 'model_hash':
        (completed['root'] / C.ROLE_PATHS['A39']).write_bytes(b'changed')
    elif damage == 'source_hash':
        (completed['root'] / 'source.py').write_text('# changed\n')
    else:
        receipt = json.loads(receipt_path.read_text())
        if damage == 'command':
            receipt['command'] += ['--set', 'cand_rescue=false']
        else:
            key, value = {'seed_hash': ('seed_list_sha256', '0' * 64), 'returncode': ('returncode', 1),
                          'partial': ('status', 'running'), 'receipt_role': ('role', 'B39'),
                          'receipt_source': ('source_identity', {})}[damage]
            receipt[key] = value
        receipt_path.write_text(json.dumps(receipt))
    def forbidden(*args, **kwargs):
        pytest.fail('Statistics must not run before all inputs are validated')
    monkeypatch.setattr(C, 'selection_checks', forbidden)
    with pytest.raises(ValueError):
        C.analyze(**completed)


def test_cli_emits_no_partial_report_on_incomplete_block(completed, capsys):
    (completed['result_dir'] / 'REPLACE36_direct.csv').unlink()
    with pytest.raises(SystemExit) as error:
        C.main(['analyze', '--jobs', str(completed['jobs_json']), '--results', str(completed['result_dir']),
                '--root', str(completed['root']), '--provenance', str(completed['provenance'])])
    assert error.value.code == 2
    assert capsys.readouterr().out == ''


def test_confirmation_keeps_additional_strict_default_gate():
    ref, candidate, direct = confirmation_frames()
    outcomes(candidate, 'default', [1] * 1583 + [.5] * 2 + [0] * 15)
    result = C.confirmation_checks(ref, candidate, direct, name='A39')
    assert result['checks']['default >= 99%']
    assert not result['checks']['default_strict_winrate_ge_0.99']
    assert not result['passed']


def test_confirmation_keeps_additional_strict_solution_gate():
    ref, candidate, direct = confirmation_frames()
    outcomes(ref, 'solution92', [1] * 800 + [0] * 800)
    outcomes(candidate, 'solution92', [1] * 799 + [.5] * 2 + [0] * 799)
    result = C.confirmation_checks(ref, candidate, direct, name='B39')
    assert result['checks']['solution92_score_nonnegative']
    assert not result['checks']['solution92_strict_winrate_nonnegative']
    assert not result['passed']


def test_last_diagnostic_job_malformed_still_prevents_all_statistics(completed, monkeypatch):
    import hashlib
    import json
    path = completed['result_dir'] / 'REPLACE36_direct.csv'
    lines = path.read_text().splitlines()
    path.write_text('\n'.join(lines[:-2]) + '\n')
    receipt_path = completed['result_dir'] / 'receipts/REPLACE36_direct.json'
    receipt = json.loads(receipt_path.read_text())
    receipt['csv_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(receipt))
    def forbidden(*args, **kwargs):
        pytest.fail('Incomplete final diagnostic job must prevent every statistic')
    monkeypatch.setattr(C, 'selection_checks', forbidden)
    with pytest.raises(ValueError, match='keys'):
        C.analyze(**completed)


def test_analyze_complete_confirmation_keeps_only_the_named_nominee(planned):
    report = C.analyze(**completed_block(planned, phase='confirmation'))
    assert (report['phase'], report['jobs'], report['games'], report['nominee']) == (
        'confirmation', 15, 23200, 'A39')
    assert set(report['results']) == {'A39'}
    assert report['passed']
    assert len(report['input_sha256']['receipts']) == 15


def test_actual_prepared_plan_matches_the_pinned_schedule():
    import json
    path = C.ROOT / 'experiments/analysis/ensemble_diversity_20261107/selection_plan/jobs.json'
    assert len(C.validate_plan(json.loads(path.read_text()), C.ROOT)) == 39
