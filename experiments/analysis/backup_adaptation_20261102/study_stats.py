"""Summarize complete, frozen conditional PT2 phases. Does not play, train or promote."""
from pathlib import Path
import argparse, hashlib, json, sys

EPS = 1e-9
PANEL = ('solution92', 'sol92_sq',
         'self:experiments/releases/20261022_all18_v3/agent_p0.pth',
         'self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth',
         'self:experiments/releases/20261022_v10_baseline/agent_p0.pth',
         'self:experiments/releases/20261101_v13_neb/agent_p0.pth')
DIRECT = 'self:experiments/releases/20261101_v14_baseline/agent_p0.pth'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def gates(phase, panel, solution, default, direct):
    if phase == 'selection':
        return dict(panel_delta=panel['delta'] >= .005-EPS,
                    solution_delta=solution['delta'] >= -EPS,
                    default=default['winrate'] >= .99-EPS,
                    direct=direct['winrate'] >= .5-EPS)
    if phase != 'confirmation':
        raise ValueError(phase)
    return dict(panel_delta=panel['delta'] >= .01-EPS, panel_lower=panel['low'] > EPS,
                solution_delta=solution['delta'] >= -EPS, solution_lower=solution['low'] >= -.01-EPS,
                default=default['winrate'] >= .99-EPS, default_delta=default['delta'] >= -.01-EPS,
                direct_lower=direct['low'] > .5+EPS)


def nominee(results):
    if set(results) != {'PT2'}:
        raise ValueError('Only the predeclared PT2 candidate is eligible')
    return 'PT2' if results['PT2']['passed'] else None


def load_driver(path):
    import importlib.util
    spec = importlib.util.spec_from_file_location('conditional_backup_driver', path)
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    return driver


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def summarize(plan_path, state_path, out):
    import pandas as pd
    plan_path, state_path, out = map(Path, (plan_path, state_path, out))
    if out.exists():
        raise FileExistsError(out)
    plan = json.loads(plan_path.read_text())
    state = json.loads(state_path.read_text())
    require(state['status'] == 'complete', 'Phase incomplete')
    require(state['plan_sha256'] == sha(plan_path), 'Invalid complete frozen phase evidence')
    require(state['study_freeze_sha256'] == plan['study_freeze_sha256'], 'Invalid complete frozen phase evidence')
    freeze = Path(plan['study_freeze_path'])
    require(sha(freeze) == plan['study_freeze_sha256'], 'Invalid complete frozen phase evidence')
    frozen = json.loads(freeze.read_text())
    root = Path(frozen['root'])
    sys.path.insert(0, str(root))
    from scripts.compare_report import compare_results
    from scripts.league_gates import panel_delta, direct_result
    from scripts.early_curriculum_study import GAME_FIELDS
    # Import the independently tested driver by its recorded committed path.
    driver_path = Path(frozen['driver']['path'])
    require(sha(driver_path) == frozen['driver']['sha256'], 'Invalid complete frozen phase evidence')
    driver = load_driver(driver_path)
    checked_plan, checked_frozen = driver.check_plan(plan_path)
    require(checked_plan == plan and checked_frozen == frozen, 'Invalid complete frozen phase evidence')
    require(state_path.resolve(strict=True) == plan_path.resolve(strict=True).parent / 'state.json', 'Noncanonical state path')
    require(state['phase'] == plan['phase'], 'Invalid complete frozen phase evidence')
    phase = plan['phase']
    require(phase in ('selection', 'confirmation'), 'Invalid complete frozen phase evidence')
    require(state['source_before'] == state['source_after'] == frozen['identity'], 'Invalid complete frozen phase evidence')
    planned = plan['jobs']
    actual = state['jobs']
    require(len(planned) == len(actual), 'Invalid complete frozen phase evidence')
    require([r['name'] for r in planned] == [r['name'] for r in actual], 'Invalid complete frozen phase evidence')
    by_role = {}
    csv_hashes = {}
    total = 0
    for job, done in zip(planned, actual):
        require(done['status'] == 'complete' and done['exit_code'] == 0, 'Invalid complete frozen phase evidence')
        target = Path(job['out'])
        require(Path(done['out']) == target and sha(target) == done['output_sha256'], 'Invalid complete frozen phase evidence')
        require(done['actual_games'] == job['games'], 'Invalid complete frozen phase evidence')
        driver.validate_output(target, job)
        frame = pd.read_csv(target)
        require(list(frame.columns) == list(GAME_FIELDS), 'Invalid complete frozen phase evidence')
        require(len(frame) == job['games'], 'Invalid complete frozen phase evidence')
        require(done['name'] == job['name'] and done['timing_class'] == job['timing_class'], 'Invalid complete frozen phase evidence')
        require(job['role'] in ('baseline', 'PT2'), 'Invalid complete frozen phase evidence')
        by_role.setdefault(job['role'], []).append((job, frame))
        csv_hashes[str(target)] = done['output_sha256']
        total += len(frame)
    roles = ['PT2']
    require(set(frozen['weights']) == {'baseline', 'PT2'}, 'Invalid complete frozen phase evidence')
    require(phase == 'selection' or plan['candidate'] == 'PT2', 'Invalid complete frozen phase evidence')
    require(set(by_role) == {'baseline', *roles}, 'Invalid complete frozen phase evidence')
    expected_first = 844000 if phase == 'selection' else 842000
    expected_n = 50 if phase == 'selection' else 300
    frames, directs = {}, {}
    for role, entries in by_role.items():
        panel_frames, defaults, direct_frames = [], [], []
        for job, frame in entries:
            require(job['n_maps'] == expected_n, 'Invalid complete frozen phase evidence')
            opp = tuple(job['opponents'])
            if opp == PANEL:
                require(job['first_seed'] == expected_first, 'Invalid complete frozen phase evidence')
                panel_frames.append(frame)
            elif opp == (*PANEL, 'default'):
                require(job['first_seed'] == expected_first, 'Invalid complete frozen phase evidence')
                panel_frames.append(frame.loc[frame.opponent.isin(PANEL)])
                defaults.append(frame.loc[frame.opponent == 'default'])
            elif opp == ('default',):
                require(job['first_seed'] == expected_first, 'Invalid complete frozen phase evidence')
                defaults.append(frame)
            elif opp == (DIRECT,):
                require(role != 'baseline', 'Invalid complete frozen phase evidence')
                require(job['first_seed'] == (844000 if phase == 'selection' else 843000), 'Invalid complete frozen phase evidence')
                direct_frames.append(frame)
            else:
                raise ValueError(f'Unexpected opponent panel: {opp}')
        require(len(panel_frames) == len(defaults) == 1, 'Invalid complete frozen phase evidence')
        require(len(direct_frames) == (0 if role == 'baseline' else 1), 'Invalid complete frozen phase evidence')
        frames[role] = pd.concat([*panel_frames, *defaults], ignore_index=True)
        if direct_frames:
            directs[role] = direct_frames[0]
    if phase == 'confirmation':
        selection_path = Path(plan['selection_summary_path'])
        require(sha(selection_path) == plan['selection_summary_sha256'], 'Invalid complete frozen phase evidence')
        selection = json.loads(selection_path.read_text())
        require(selection['phase'] == 'selection' and selection['nominee'] == plan['candidate'], 'Invalid complete frozen phase evidence')
        require(selection['study_freeze_sha256'] == plan['study_freeze_sha256'], 'Invalid complete frozen phase evidence')
        for path, digest in selection['csv_sha256'].items():
            require(sha(path) == digest, 'Invalid complete frozen phase evidence')
    results = {}
    baseline = frames['baseline']
    for role in roles:
        frame = frames[role]
        rows = {r['opponent']: r for r in compare_results(frame, baseline)}
        panel = panel_delta(frame, baseline, panel=PANEL)
        direct = direct_result(directs[role], DIRECT)
        direct_values = directs[role]['result']
        direct.update(wins=int((direct_values == 1).sum()), draws=int((direct_values == .5).sum()),
                      losses=int((direct_values == 0).sum()))
        require(panel['maps'] == expected_n and direct['maps'] == expected_n, 'Invalid complete frozen phase evidence')
        checks = gates(phase, panel, rows['solution92'], rows['default'], direct)
        counts = {}
        for opponent in (*PANEL, 'default'):
            counts[opponent] = {}
            for name, data in [('baseline', baseline), ('candidate', frame)]:
                values = data.loc[data.opponent == opponent, 'result']
                counts[opponent][name] = dict(games=len(values), wins=int((values == 1).sum()),
                                             draws=int((values == .5).sum()), losses=int((values == 0).sum()))
        results[role] = dict(panel=panel, direct=direct, opponents=rows, counts=counts,
                             gates={k: bool(v) for k, v in checks.items()}, passed=all(checks.values()))
    expected_total = 1500 if phase == 'selection' else 9000
    require(total == expected_total == state['completed_games'], 'Invalid complete frozen phase evidence')
    result = dict(study_name=driver.STUDY_NAME, phase=phase, status='complete', study_freeze_sha256=plan['study_freeze_sha256'],
                  plan_path=str(plan_path), plan_sha256=sha(plan_path), state_sha256=sha(state_path),
                  csv_sha256=csv_hashes, candidates=results,
                  nominee=nominee(results) if phase == 'selection' else plan['candidate'],
                  promotion_qualified=(results[plan['candidate']]['passed'] if phase == 'confirmation' else False),
                  completed_games=total, bootstrap_samples=5000, bootstrap_rng_seed=0,
                  bootstrap_cluster='whole map, paired sides and all panel opponents')
    with out.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(result, indent=2, allow_nan=False))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan')
    parser.add_argument('state')
    parser.add_argument('out')
    args = parser.parse_args()
    summarize(args.plan, args.state, args.out)
