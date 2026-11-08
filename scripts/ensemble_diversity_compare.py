"""Bounded result validation and analysis for fixed November ensemble profiles.

No model loads or games. Scores count draws as half a win; strict win rates
are reported separately. The CLI requires a complete block and bound receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from scripts.early_curriculum_study import read_rows

ROOT = Path(__file__).resolve().parents[1]
SIDES = ('player_0', 'player_1')
LOCAL_SIX = (
    'solution92', 'sol92_sq',
    'self:experiments/releases/20261022_all18_v3/agent_p0.pth',
    'self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth',
    'self:experiments/releases/20261022_v10_baseline/agent_p0.pth',
    'self:experiments/releases/20261101_v13_neb/agent_p0.pth',
)
V14_PATH = 'experiments/releases/20261101_v14_baseline/agent_p0.pth'
V14_LABEL = 'self:' + V14_PATH
OPPONENTS = LOCAL_SIX + ('default',)
NET_COUNTS = {'A39': 39, 'B39': 39, 'ALL42': 42, 'REPLACE36': 36}
NOMINABLE = ('A39', 'B39', 'ALL42')
ROLE_PATHS = {'V14': V14_PATH, **{
    name: f'experiments/candidates/ensemble_diversity_20261107/{name}.pth'
    for name in NET_COUNTS}}


def require(condition, message):
    if not condition:
        raise ValueError(message)


DEFAULT_PROFILE = 'full20261107'


@dataclass(frozen=True)
class ComparisonProfile:
    name: str
    analysis: Path
    protocol: str
    selection: tuple[int, int, int, int]
    confirmation: tuple[int, int, int, int]
    totals: tuple[int, int]

    def cohort(self, phase):
        require(phase in ('selection', 'confirmation'), 'Invalid comparison phase')
        return self.selection if phase == 'selection' else self.confirmation

    def total(self, phase):
        self.cohort(phase)
        return self.totals[0 if phase == 'selection' else 1]


PROFILES = MappingProxyType({
    DEFAULT_PROFILE: ComparisonProfile(DEFAULT_PROFILE,
        Path('experiments/analysis/ensemble_diversity_20261107'),
        'docs/superpowers/plans/2026-11-07-ensemble-comparison.md',
        (1400000, 100, 1401000, 100), (1500000, 800, 1600000, 400), (7800, 23200)),
    'compact20261108': ComparisonProfile('compact20261108',
        Path('experiments/analysis/ensemble_diversity_20261108_compact'),
        'docs/superpowers/plans/2026-11-08-ensemble-compact.md',
        (1700000, 20, 1701000, 20), (1800000, 100, 1900000, 200), (1560, 3200)),
})


def comparison_profile(name=DEFAULT_PROFILE):
    require(isinstance(name, str) and name in PROFILES, 'Unknown comparison profile')
    return PROFILES[name]


def plan_profile(plan, expected=None):
    require(isinstance(plan, dict), 'Invalid comparison plan')
    profile = comparison_profile(plan.get('profile', DEFAULT_PROFILE))
    require(expected is None or profile.name == comparison_profile(expected).name,
            'Plan/controller profile differs')
    return profile


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _seeds(seeds):
    require(isinstance(seeds, list) and bool(seeds)
            and all(type(seed) is int and seed >= 0 for seed in seeds)
            and len(set(seeds)) == len(seeds), 'Invalid expected seed list')
    return seeds


def validate_job_csv(csv_path, job, seeds) -> list[dict]:
    """Require every expected (opponent, absolute seed, side), exactly once.

    This checks game data, not execution provenance; analyze additionally binds
    the CSV to the controller receipt, fixed plan and frozen inputs.
    """
    seeds = _seeds(seeds)
    require(type(job.get('expected_games')) is int
            and job['expected_games'] == 2 * len(seeds), 'Unexpected job game count')
    require(isinstance(job.get('opponent'), str) and job['opponent'] in (*OPPONENTS, V14_LABEL),
            'Unexpected job opponent')
    expected = {(job['opponent'], seed, side) for seed in seeds for side in SIDES}
    seen, normalized = set(), []
    for row in read_rows(csv_path):
        numbers = {key: float(value) for key, value in row.items() if key not in ('opponent', 'side')}
        require(all(math.isfinite(value) for value in numbers.values()), 'Nonfinite game value')
        require(numbers['seed'].is_integer(), 'Noninteger seed')
        key = (row['opponent'], int(numbers['seed']), row['side'])
        require(key in expected and key not in seen, f'Unexpected/duplicate game key: {key}')
        seen.add(key)
        require(numbers['steps'] == 303 and numbers['point_counting_version'] == 2
                and numbers['secs'] >= 0, 'Wrong runtime/course steps/point version')
        for name in ('sap_attempts', 'sap_hits', 'relics_found', 'relics_seen',
                     'known_point_tiles', 'belief_contradictions', 'unit_steps', 'our_points', 'opp_points'):
            require(numbers[name].is_integer() and numbers[name] >= 0, f'Invalid {name}')
        for name in ('wait_frac', 'invalid_frac', 'greedy_masked_frac', 'stack_frac'):
            require(0 <= numbers[name] <= 1, f'Invalid {name}')
        normalized.append({**row, **numbers, 'seed': key[1]})
    require(seen == expected and len(normalized) == job['expected_games'], 'Incomplete CSV game keys')
    return normalized


def _checked_frame(frame, opponents, first, maps):
    from scripts.compare_report import KEY, validated_results
    clean = validated_results(frame, 'Study data')
    expected = {(opponent, seed, side) for opponent in opponents
                for seed in range(first, first + maps) for side in SIDES}
    require(set(clean[KEY].itertuples(index=False, name=None)) == expected, 'Incomplete/unexpected game keys')
    require('game_win' in frame and frame['game_win'].isin((0, 1)).all()
            and frame['game_win'].eq(frame['result'].eq(1).astype(int)).all(), 'Inconsistent strict wins')
    return clean


def _counts(frame):
    wins = int(frame['result'].eq(1).sum())
    draws = int(frame['result'].eq(.5).sum())
    games = len(frame)
    return dict(games=games, wins=wins, draws=draws, losses=games - wins - draws,
                half_wins=2 * wins + draws, score=(wins + .5 * draws) / games,
                strict_winrate=wins / games)


def _score_stats(stats, candidate, reference=None):
    # The reused library calls mean(result) 'winrate'; never propagate that
    # ambiguous label into this study's report.
    renamed = {'winrate': 'score', 'ref_winrate': 'ref_score'}
    result = {renamed.get(key, key): value for key, value in stats.items()}
    result['candidate'] = _counts(candidate)
    if reference is not None:
        result['reference'] = _counts(reference)
    return result


def _complete_frames(reference, candidate, direct, *, phase, profile=DEFAULT_PROFILE):
    first, maps, direct_first, direct_maps = comparison_profile(profile).cohort(phase)
    return (_checked_frame(reference, OPPONENTS, first, maps),
            _checked_frame(candidate, OPPONENTS, first, maps),
            _checked_frame(direct, (V14_LABEL,), direct_first, direct_maps))


def _report_stats(reference, candidate, direct, stats):
    def subset(df, opponents):
        return df[df['opponent'].isin(opponents)]
    result = {'panel': _score_stats(stats['panel'], subset(candidate, LOCAL_SIX), subset(reference, LOCAL_SIX)),
              'direct': _score_stats(stats['direct'], direct)}
    for opponent in ('solution92', 'default'):
        result[opponent] = _score_stats(stats[opponent], subset(candidate, (opponent,)),
                                       subset(reference, (opponent,)))
    result['opponent_outcomes'] = {
        opponent: {'candidate': _counts(subset(candidate, (opponent,))),
                   'reference': _counts(subset(reference, (opponent,)))} for opponent in OPPONENTS}
    result['panel_half_win_gain'] = (result['panel']['candidate']['half_wins']
                                     - result['panel']['reference']['half_wins'])
    result['solution_half_win_gain'] = (result['solution92']['candidate']['half_wins']
                                        - result['solution92']['reference']['half_wins'])
    return result


def _additional_checks(result):
    sol, dfl = result['solution92'], result['default']['candidate']
    return {'solution92_score_nonnegative': result['solution_half_win_gain'] >= 0,
            'solution92_strict_winrate_nonnegative': sol['candidate']['wins'] >= sol['reference']['wins'],
            'default_strict_winrate_ge_0.99': dfl['wins'] * 100 >= 99 * dfl['games']}


def selection_checks(reference, candidate, direct, *, name, profile=DEFAULT_PROFILE):
    """Exploratory gates on one complete fixed selection cohort, preserving W/D/L."""
    from scripts.compare_report import compare_results
    from scripts.league_gates import direct_result, panel_delta
    require(name in NET_COUNTS, 'Unknown candidate')
    reference, candidate, direct = _complete_frames(reference, candidate, direct, phase='selection', profile=profile)
    by_opponent = {row['opponent']: row for row in compare_results(candidate, reference)}
    stats = dict(panel=panel_delta(candidate, reference, panel=LOCAL_SIX),
                 direct=direct_result(direct, opponent=V14_LABEL), **by_opponent)
    result = _report_stats(reference, candidate, direct, stats)
    panel, dfl, duel = (result[key]['candidate'] for key in ('panel', 'default', 'direct'))
    checks = {'panel_score_gain_ge_0.005': result['panel_half_win_gain'] * 100 >= panel['games'],
              'default_score_ge_0.99': dfl['half_wins'] * 100 >= 198 * dfl['games'],
              'direct_score_ge_0.50': duel['half_wins'] >= duel['games'],
              **_additional_checks(result)}
    return dict(**result, checks=checks, passed=all(checks.values()), nominable=name in NOMINABLE)


def choose_nominee(results):
    """Integer half-win ranking; the diagnostic role can never be nominated."""
    require(set(results) == set(NET_COUNTS), 'All four candidate results required before nomination')
    eligible = [name for name in NOMINABLE if results[name]['passed']]
    return min(eligible, key=lambda name: (-results[name]['panel_half_win_gain'],
        -results[name]['solution_half_win_gain'], NET_COUNTS[name], name)) if eligible else None


def confirmation_checks(reference, candidate, direct, *, name, profile=DEFAULT_PROFILE):
    """Established seven score gates plus three predeclared safeguards."""
    from scripts.league_gates import confirm_checks
    require(name in NOMINABLE, 'Invalid confirmation nominee')
    reference, candidate, direct = _complete_frames(reference, candidate, direct, phase='confirmation', profile=profile)
    stats = confirm_checks(reference, candidate, direct, direct_opponent=V14_LABEL,
                           panel=LOCAL_SIX, min_delta=.01, label='Local six score')
    result = _report_stats(reference, candidate, direct, stats)
    checks = {**stats['checks'], **_additional_checks(result)}
    return dict(**result, checks=checks, passed=all(checks.values()), nominable=True)


PROTOCOL = 'docs/superpowers/plans/2026-11-07-ensemble-comparison.md'
OPPONENT_SHA256 = {
    'experiments/releases/20261022_all18_v3/agent_p0.pth': 'aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935',
    'experiments/releases/20261022_v7_Bsnpd/agent_p0.pth': 'c394acba84f7a298f8f1e6107328d8e6ce151b367a28997b059aa82fc8a895e6',
    'experiments/releases/20261022_v10_baseline/agent_p0.pth': '03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67',
    'experiments/releases/20261101_v13_neb/agent_p0.pth': '6d00b6c52366a613eed3b7b5b6f9c3c088802716a85c30fe192c46c57bdd8e62',
    V14_PATH: '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8',
}


def _load_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def validate_plan(plan, root, *, phase='selection', nominee=None, profile=None) -> list[dict]:
    """Validate the immutable schedule; return copies augmented with seed lists.

    Model admission is separate: candidate files need not exist to validate the
    prepared plan. Opponent bytes and the exact fixed seed blocks must exist.
    """
    root = Path(root).resolve()
    require(phase in ('selection', 'confirmation'), 'Invalid comparison phase')
    require(nominee is None if phase == 'selection' else nominee in NOMINABLE, 'Invalid phase nominee')
    spec = plan_profile(plan, profile)
    require(plan.get('protocol') == spec.protocol, 'Wrong comparison protocol')
    require(plan.get('phase', phase) == phase and plan.get('nominee', nominee) == nominee,
            'Wrong plan phase/nominee')
    roles = tuple(ROLE_PATHS) if phase == 'selection' else ('V14', nominee)
    require(plan.get('roles') == {name: ROLE_PATHS[name] for name in roles}, 'Wrong fixed role paths')
    require(type(plan.get('max_simultaneous_model_processes')) is int
            and plan['max_simultaneous_model_processes'] == 2, 'Wrong process limit')
    require(plan.get('opponent_sha256') == OPPONENT_SHA256, 'Wrong pinned opponent hashes')
    for path, sha in OPPONENT_SHA256.items():
        require(digest(root / path) == sha, f'Opponent hash changed: {path}')
    expected = {}
    for role in roles:
        for index, opponent in enumerate(OPPONENTS):
            expected[f'{role}_panel_{index}'] = (role, 'panel', opponent)
        if role != 'V14':
            expected[f'{role}_direct'] = (role, 'direct', V14_LABEL)
    raw_jobs = plan.get('jobs')
    require(isinstance(raw_jobs, list) and len(raw_jobs) == len(expected), 'Missing/extra jobs')
    jobs, seen, seed_cache = [], set(), {}
    fields = {'name', 'role', 'kind', 'weights', 'opponent', 'seed_list', 'expected_games', 'workers'}
    for job in raw_jobs:
        require(isinstance(job, dict) and set(job) == fields, 'Unexpected job schema')
        name = job['name']
        require(isinstance(name, str) and name in expected and name not in seen, 'Unexpected/duplicate job')
        seen.add(name)
        role, kind, opponent = expected[name]
        require((job['role'], job['kind'], job['opponent']) == (role, kind, opponent)
                and job['weights'] == ROLE_PATHS[role], 'Job differs from fixed schedule')
        require(type(job['workers']) is int and job['workers'] == 1, 'Each job must use one worker')
        panel_first, panel_maps, direct_first, direct_maps = spec.cohort(phase)
        first, maps = (direct_first, direct_maps) if kind == 'direct' else (panel_first, panel_maps)
        require(type(job['expected_games']) is int and job['expected_games'] == 2 * maps, 'Wrong job game count')
        value = job['seed_list']
        require(isinstance(value, str), 'Invalid seed path')
        path = Path(value)
        require(not path.is_absolute() and '..' not in path.parts
                and path.is_relative_to(spec.analysis)
                and (root / path).resolve().is_relative_to(root / spec.analysis), 'Invalid seed path')
        if value not in seed_cache:
            seed_cache[value] = _seeds(_load_json(root / path))
        seeds = seed_cache[value]
        require(seeds == list(range(first, first + maps)), 'Wrong fixed seed block')
        jobs.append({**job, 'seeds': seeds.copy()})
    total = spec.total(phase)
    require(type(plan.get('total_games')) is int and plan['total_games'] == total
            and sum(job['expected_games'] for job in jobs) == total, 'Wrong total game count')
    return jobs


def _hex(value, length=64):
    return isinstance(value, str) and len(value) == length and all(c in '0123456789abcdef' for c in value)


def _provenance(value, plan, root):
    require(value is not None, 'Frozen provenance is required')
    frozen = value if isinstance(value, dict) else _load_json(value)
    require(isinstance(frozen, dict), 'Invalid frozen provenance')
    require(frozen.get('profile', DEFAULT_PROFILE) == plan_profile(plan).name,
            'Frozen provenance profile differs')
    models, source = frozen.get('model_sha256'), frozen.get('source_identity')
    require(isinstance(models, dict) and set(models) == set(plan['roles'])
            and all(_hex(sha) for sha in models.values()), 'Invalid frozen model hashes')
    for role, path in plan['roles'].items():
        require(digest(root / path) == models[role], f'Model hash changed: {role}')
    require(isinstance(source, dict) and _hex(source.get('head'), 40)
            and isinstance(source.get('files'), dict) and bool(source['files']), 'Invalid frozen source identity')
    for path, sha in source['files'].items():
        require(isinstance(path, str) and _hex(sha) and digest(root / path) == sha,
                f'Source hash changed: {path}')
    if 'executable' in source or 'executable_sha256' in source:
        require(isinstance(source.get('executable'), str) and _hex(source.get('executable_sha256'))
                and digest(source['executable']) == source['executable_sha256'], 'Executable hash changed')
    sha = (hashlib.sha256(json.dumps(frozen, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
           if isinstance(value, dict) else digest(value))
    return frozen, sha


def _receipt(receipt, job, csv_path, root, phase, plan, provenance):
    require(isinstance(receipt, dict) and receipt.get('profile', DEFAULT_PROFILE) == plan_profile(plan).name,
            'Execution receipt profile differs')
    expected = dict(status='complete', returncode=0, job_name=job['name'], phase=phase,
                    role=job['role'], opponent=job['opponent'], weights=job['weights'],
                    model_sha256=provenance['model_sha256'][job['role']],
                    seed_list_sha256=digest(root / job['seed_list']), csv_sha256=digest(csv_path),
                    rows=job['expected_games'], source_identity=provenance['source_identity'],
                    opponent_sha256=plan['opponent_sha256'])
    require(isinstance(receipt, dict) and all(receipt.get(key) == value for key, value in expected.items())
            and type(receipt.get('returncode')) is int and type(receipt.get('rows')) is int,
            f'Invalid/unbound execution receipt: {job["name"]}')
    command = receipt.get('command')
    args = ['-B', '-m', 'scripts.par_eval', '--weights', str((root / job['weights']).resolve()),
            '--seed-list', str((root / job['seed_list']).resolve()), '--workers', '1',
            '--opponents', job['opponent'], '--out', str(csv_path.resolve())]
    require(isinstance(command, list) and len(command) == len(args) + 1
            and isinstance(command[0], str) and bool(command[0]) and command[1:] == args,
            f'Unexpected execution command: {job["name"]}')
    source = provenance['source_identity']
    if 'executable_sha256' in source:
        import shutil
        executable = shutil.which(command[0]) if not Path(command[0]).is_absolute() else command[0]
        require(executable is not None and digest(executable) == source['executable_sha256'],
                'Command interpreter differs from frozen executable')
    return expected['csv_sha256']


def analyze(jobs_json, result_dir, *, root=ROOT, phase='selection', nominee=None, provenance=None):
    """Validate every job and receipt before computing any aggregate or choice.

    Receipts live in results/receipts/{job_name}.json; CSVs are
    results/{job_name}.csv. Frozen provenance contains model_sha256 by role and
    source_identity (HEAD, file hashes, optionally executable and its hash).
    """
    import pandas as pd
    root, result_dir = Path(root).resolve(), Path(result_dir).resolve()
    plan = _load_json(jobs_json)
    spec = plan_profile(plan)
    jobs = validate_plan(plan, root, phase=phase, nominee=nominee)
    frozen, frozen_sha = _provenance(provenance, plan, root)
    names = {job['name'] for job in jobs}
    require({path.stem for path in result_dir.glob('*.csv')} == names, 'Missing/extra result CSV jobs')
    receipt_dir = result_dir / 'receipts'
    require({path.stem for path in receipt_dir.glob('*.json')} == names, 'Missing/extra execution receipts')
    rows, csv_hashes, receipt_hashes = {}, {}, {}
    for job in jobs:
        name = job['name']
        csv_path, receipt_path = result_dir / f'{name}.csv', receipt_dir / f'{name}.json'
        csv_hashes[name] = _receipt(_load_json(receipt_path), job, csv_path, root, phase, plan, frozen)
        rows[name] = validate_job_csv(csv_path, job, job['seeds'])
        receipt_hashes[name] = digest(receipt_path)
    # No stats above this line: even the diagnostic role must be complete.
    panels = {role: pd.DataFrame([row for job in jobs if job['role'] == role and job['kind'] == 'panel'
                                 for row in rows[job['name']]]) for role in plan['roles']}
    results = {}
    for role in plan['roles']:
        if role == 'V14':
            continue
        direct = pd.DataFrame(rows[f'{role}_direct'])
        check = selection_checks if phase == 'selection' else confirmation_checks
        results[role] = check(panels['V14'], panels[role], direct, name=role, profile=spec.name)
    report = dict(schema_version=1, status='complete', phase=phase, jobs=len(jobs),
                  games=sum(len(value) for value in rows.values()), results=results,
                  nominee=choose_nominee(results) if phase == 'selection' else nominee,
                  score_definition='Spielscore = (Siege + 0.5 * Remis) / Spiele; strict_winrate counts only wins.',
                  interpretation=('Selection is exploratory, not confirmation of strength.' if phase == 'selection'
                                  else 'Fixed-agent paired map bootstrap; passing gates does not authorize promotion.'),
                  input_sha256=dict(plan=digest(jobs_json), provenance=frozen_sha,
                                    csv=csv_hashes, receipts=receipt_hashes))
    if spec.name != DEFAULT_PROFILE:
        report['profile'] = spec.name
    if phase == 'confirmation':
        report['passed'] = results[nominee]['passed']
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('analyze',))
    parser.add_argument('--jobs', required=True, help='Fixed jobs JSON')
    parser.add_argument('--results', required=True, help='Complete CSV/receipts directory')
    parser.add_argument('--provenance', required=True, help='Frozen role hashes and source identity JSON')
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--phase', choices=('selection', 'confirmation'), default='selection')
    parser.add_argument('--nominee', choices=NOMINABLE)
    parser.add_argument('--out', help='New summary JSON; otherwise print JSON')
    args = parser.parse_args(argv)
    try:
        report = analyze(args.jobs, args.results, root=args.root, phase=args.phase,
                         nominee=args.nominee, provenance=args.provenance)
        content = json.dumps(report, indent=2, allow_nan=False) + '\n'
        if args.out:
            with Path(args.out).open('x') as stream:
                stream.write(content)
        else:
            print(content, end='')
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
