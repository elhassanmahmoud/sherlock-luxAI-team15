"""Independent, read-only audit of the COMPLETE preregistered 3100-game selection.

No repository imports, pandas, Torch, Lux environments, models or evaluation subprocesses.
Run only after the coordinator reports that every selection job has finished::

    python selection-independent-audit.py --out /tmp/sherlock-night-20261101/selection-independent-audit.json

Optionally compare the official full summary with --compare-summary PATH.
Incomplete phases are rejected before reading any outcome CSV or printing scores.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np

ROOT = Path('/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics')
D = ROOT / 'experiments/analysis/night_20261101'
PHASE_SHA = '54c8f8593396fc5ef035c48cd1e2f2899f660a969c2d6bd33f60c453a3b5212c'
FREEZE_SHA = '96385f7398bcc531d6983ab7d127df200b74fb4ca54599a8b4ad6e64e51d61ab'
HEAD = 'aa0660183cace1e21285fde30ae61e3812136f05'
PANEL = (
    'solution92', 'sol92_sq',
    'self:experiments/releases/20261022_all18_v3/agent_p0.pth',
    'self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth',
    'self:experiments/releases/20261022_v10_baseline/agent_p0.pth',
    'self:experiments/releases/20261101_v13_neb/agent_p0.pth',
)
REFERENCE = 'self:experiments/releases/20261101_v14_baseline/agent_p0.pth'
CANDIDATES = ('overlap', 'control', 'discovery')
SIDES = ('player_0', 'player_1')
SEEDS = tuple(range(831000, 831050))
EPS = 1e-9
FIELDS = ['seed', 'side', 'opponent', 'result', 'game_win', 'point_win',
          'our_wins', 'opp_wins', 'our_points', 'opp_points', 'point_counting_version',
          'wait_frac', 'invalid_frac', 'greedy_masked_frac', 'sap_attempts', 'sap_hits',
          'stack_frac', 'relics_found', 'relics_seen', 'known_point_tiles',
          'belief_contradictions', 'unit_steps', 'steps', 'secs']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def expected_args(name):
    candidate = name.removesuffix('_direct')
    weight = ('experiments/releases/20261101_v14_baseline/agent_p0.pth'
              if name == 'baseline' else f'experiments/ensembles/night_20261101_{candidate}.pth')
    opponents = REFERENCE if name.endswith('_direct') else ','.join((*PANEL, 'default'))
    return ['--weights', weight, '--first', '331000', '--n', '50', '--workers', '2',
            '--opponents', opponents, '--out', str(D / f'selection_{name}.csv')]


def load_complete_csv(path, opponents):
    required = {(s, side, opp) for s in SEEDS for side in SIDES for opp in opponents}
    rows = {}
    with path.open(newline='') as handle:
        reader = csv.DictReader(handle)
        require(reader.fieldnames == FIELDS, f'{path.name}: exact CSV schema')
        for row in reader:
            values = {k: float(row[k]) for k in FIELDS if k not in ('side', 'opponent')}
            require(all(math.isfinite(v) for v in values.values()), f'{path.name}: nonfinite value')
            require(values['seed'].is_integer(), f'{path.name}: nonintegral seed')
            key = (int(values['seed']), row['side'], row['opponent'])
            require(key in required and key not in rows, f'{path.name}: unexpected/duplicate key {key}')
            require(values['steps'] == 303 and values['point_counting_version'] == 2, f'{key}: incomplete/old game')
            a, b = values['our_wins'], values['opp_wins']
            require(a.is_integer() and b.is_integer() and min(a, b) >= 0 and a + b <= 3, f'{key}: match wins')
            result = 1.0 if a > b else 0.0 if a < b else .5
            require(values['result'] == result and values['game_win'] == int(result == 1), f'{key}: result incoherent')
            a, b = values['our_points'], values['opp_points']
            require(a.is_integer() and b.is_integer() and min(a, b) >= 0, f'{key}: invalid points')
            point_result = 1.0 if a > b else 0.0 if a < b else .5
            require(values['point_win'] == point_result, f'{key}: point result incoherent')
            require(values['secs'] >= 0, f'{key}: negative time')
            require(all(0 <= values[k] <= 1 for k in ('wait_frac', 'invalid_frac', 'greedy_masked_frac', 'stack_frac')), f'{key}: fraction')
            require(all(values[k].is_integer() and values[k] >= 0 for k in ('sap_attempts', 'sap_hits', 'relics_found', 'relics_seen', 'known_point_tiles', 'belief_contradictions', 'unit_steps')), f'{key}: invalid count')
            rows[key] = result
    require(set(rows) == required, f'{path.name}: incomplete expected key set')
    return rows


def bootstrap(values):
    # Draw card indices once per comparison. Both sides and all panel opponents
    # have already been averaged WITHIN each card; never resample game rows.
    values = np.asarray(values, dtype=float)
    indexes = np.random.default_rng(0).integers(0, len(values), size=(5000, len(values)))
    means = values[indexes].mean(axis=1)
    low, high = np.percentile(means, [2.5, 97.5])
    return float(low), float(high)


def matrix(rows, opponents):
    return np.array([[[rows[(s, side, opp)] for side in SIDES] for opp in opponents] for s in SEEDS])


def comparison(candidate, baseline):
    low, high = bootstrap(candidate - baseline)
    return dict(maps=50, games=100, winrate=float(candidate.mean()), ref_winrate=float(baseline.mean()),
                delta=float((candidate - baseline).mean()), low=low, high=high)


def raw_counts(rows, opponent):
    values = [value for (seed, side, opp), value in rows.items() if opp == opponent]
    return dict(games=len(values), wins=values.count(1.0), draws=values.count(.5), losses=values.count(0.0))


def same_number(a, b):
    return math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-12)


def compare_official(ours, path):
    official = read_json(path)
    require(official['phase'] == 'selection' and tuple(official['panel']) == PANEL, 'Official panel/phase')
    require(official['nominee'] == ours['nominee'], 'Official nominee differs')
    require(official['promotion_qualified'] is False and official['completed_games'] == 3100, 'Official phase totals')
    require(official['csv_sha256'] == ours['csv_sha256'], 'Official CSV hashes differ')
    require(set(official['candidates']) == set(CANDIDATES), 'Official candidate set')
    for name in CANDIDATES:
        left, right = ours['candidates'][name], official['candidates'][name]
        require(left['gates'] == right['gates'] and left['passed'] == right['passed'], f'{name}: official gate mismatch')
        require(left['counts'] == right['counts'], f'{name}: official win/draw/loss counts differ')
        for group in ('panel', 'direct'):
            for key, value in left[group].items():
                require(same_number(value, right[group][key]), f'{name}: official {group}.{key} differs')
        for opponent in (*PANEL, 'default'):
            for key, value in left['opponents'][opponent].items():
                require(same_number(value, right['opponents'][opponent][key]), f'{name}: official opponent metric {key} differs')
            require(right['opponents'][opponent]['excluded_candidate'] == 0 and right['opponents'][opponent]['excluded_reference'] == 0, f'{name}: official excluded cards')
    return dict(path=str(path), sha256=sha(path), matched=True)


def audit():
    # Completion guard precedes all CSV reads, metric calculations and output.
    journal = read_json(D / 'selection_state.json')
    require(journal.get('status') == 'complete', 'Selection incomplete; no results may be read or selected')
    names = ['baseline', 'overlap', 'overlap_direct', 'control', 'control_direct', 'discovery', 'discovery_direct']
    require([job['name'] for job in journal['jobs']] == names, 'Incomplete/unexpected executed job list')
    require(all(job.get('exit_code') == 0 and job.get('output_sha256') for job in journal['jobs']), 'Unfinished/failed output job')
    phase_path, freeze_path = D / 'selection_jobs.json', D / 'selection_freeze.json'
    require(sha(phase_path) == PHASE_SHA == journal['phase_sha256'], 'Phase changed since independent preflight')
    require(sha(freeze_path) == FREEZE_SHA, 'Freeze changed since independent preflight')
    phase, freeze = read_json(phase_path), read_json(freeze_path)
    require(journal['phase'] == phase, 'Embedded phase does not match original')
    require(phase['manifest_path'] == str(phase_path) and phase['name'] == 'selection', 'Original phase binding')
    require(tuple(phase['panel']) == PANEL and phase['direct_opponent'] == REFERENCE, 'Exact six-opponent panel/reference')
    require(tuple(phase['candidates']) == CANDIDATES and [job['name'] for job in phase['jobs']] == names, 'Fixed A/B/C order')
    require(freeze['source']['head'] == HEAD, 'Expected frozen source revision')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    require(head == HEAD, 'Current source HEAD changed')
    for path, expected in freeze['source']['files'].items():
        require(sha(path) == expected, 'Frozen executable source changed: ' + path)
    require(sha(freeze['source']['executable']) == freeze['source']['executable_sha256'], 'Python executable changed')
    for path, expected in freeze['weights'].items():
        require(sha(path) == expected, 'Frozen actual weight input changed: ' + path)
    for path, expected in phase['weight_sha256_before_selection'].items():
        require(freeze['weights'][path] == expected and sha(path) == expected, 'Preselection weight hash binding: ' + path)
    for name, expected in phase['admission_proof_sha256'].items():
        require(sha(D / name) == expected, 'Admission evidence changed: ' + name)
    admitted = datetime.fromisoformat(phase['admitted_at'])
    require(datetime.fromisoformat(journal['started_at']) >= admitted, 'Selection started before admission')
    require(datetime.fromisoformat(journal['finished_at']) <= datetime.fromisoformat(phase['deadline_utc']), 'Selection missed phase deadline')

    # Bind every real command to both the original phase AND an independent
    # literal recipe, before reading any of the seven completed CSVs.
    for planned, actual, name in zip(phase['jobs'], journal['jobs'], names):
        require(planned['args'] == expected_args(name), name + ': preregistered job recipe differs')
        expected_command = [freeze['source']['python'], '-B', '-m', 'scripts.par_eval', *expected_args(name)]
        require(actual['command'] == expected_command, name + ': executed command differs')
        path = D / f'selection_{name}.csv'
        require(sha(path) == actual['output_sha256'], name + ': output hash changed')

    tables, csv_hashes = {}, {}
    for name in names:
        path = D / f'selection_{name}.csv'
        tables[name] = load_complete_csv(path, (REFERENCE,) if name.endswith('_direct') else (*PANEL, 'default'))
        csv_hashes[path.name] = sha(path)
    require(sum(len(rows) for rows in tables.values()) == 3100, 'Exactly 3100 completed games required')
    baseline = matrix(tables['baseline'], (*PANEL, 'default'))
    entries, nominee = {}, None
    for name in CANDIDATES:
        candidate = matrix(tables[name], (*PANEL, 'default'))
        panel = comparison(candidate[:, :6, :].mean(axis=(1, 2)), baseline[:, :6, :].mean(axis=(1, 2)))
        panel.pop('games')  # The historical panel schema counts complete cards.
        opponents = {opp: comparison(candidate[:, i, :].mean(axis=1), baseline[:, i, :].mean(axis=1))
                     for i, opp in enumerate((*PANEL, 'default'))}
        direct_values = matrix(tables[name + '_direct'], (REFERENCE,)).mean(axis=(1, 2))
        low, high = bootstrap(direct_values)
        direct = dict(maps=50, games=100, winrate=float(direct_values.mean()), low=low, high=high)
        gates = dict(panel_delta=panel['delta'] >= .005 - EPS, solution=opponents['solution92']['delta'] >= -EPS,
                     default=opponents['default']['winrate'] >= .99 - EPS, direct=direct['winrate'] >= .5 - EPS)
        counts = {opp: dict(baseline=raw_counts(tables['baseline'], opp), candidate=raw_counts(tables[name], opp))
                  for opp in (*PANEL, 'default')}
        entries[name] = dict(panel=panel, direct=direct, opponents=opponents, gates=gates,
                             counts=counts, passed=all(gates.values()))
        if entries[name]['passed'] and (nominee is None or panel['delta'] > entries[nominee]['panel']['delta'] + EPS):
            nominee = name
    return dict(phase='selection', independent=True, accepted_data=True, panel=PANEL,
                source_head=HEAD, phase_sha256=PHASE_SHA, freeze_sha256=FREEZE_SHA,
                completed_games=3100, csv_sha256=csv_hashes, candidates=entries, nominee=nominee,
                promotion_qualified=False, bootstrap=dict(unit='whole card: both sides and six panel opponents',
                draws=5000, rng_seed=0, percentiles=[2.5, 97.5]),
                limitation='Selection only; the single nominee still needs the separately preregistered fresh confirmation.')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--compare-summary', type=Path)
    args = parser.parse_args()
    require(not args.out.exists(), 'Independent output already exists')
    require(not args.out.resolve().is_relative_to(ROOT), 'Independent report must remain outside the frozen worktree')
    report = audit()
    if args.compare_summary:
        report['official_comparison'] = compare_official(report, args.compare_summary)
    report['reviewed_at_utc'] = datetime.now(timezone.utc).isoformat()
    with args.out.open('x') as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(dict(accepted_data=True, completed_games=3100, nominee=report['nominee'],
                         promotion_qualified=False, output=str(args.out)), indent=2))


if __name__ == '__main__':
    main()
