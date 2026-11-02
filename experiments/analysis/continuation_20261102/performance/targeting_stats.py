"""Summarize complete, frozen P/PT phases. Does not play, train or promote."""
from pathlib import Path
import argparse, hashlib, json, sys

EPS = 1e-9
PANEL = ('solution92', 'sol92_sq',
         'self:experiments/releases/20261022_all18_v3/agent_p0.pth',
         'self:experiments/releases/20261022_v7_Bsnpd/agent_p0.pth',
         'self:experiments/releases/20261022_v10_baseline/agent_p0.pth',
         'self:experiments/releases/20261101_v13_neb/agent_p0.pth')
DIRECT = 'self:experiments/releases/20261101_v14_baseline/agent_p0.pth'


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
    chosen = None
    for name in ('P', 'PT'):
        if name in results and results[name]['passed']:
            if chosen is None or results[name]['panel']['delta'] > results[chosen]['panel']['delta'] + EPS:
                chosen = name
    return chosen


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
    assert state['status'] == 'complete', 'Phase incomplete'
    assert state['plan_sha256'] == sha(plan_path)
    assert state['study_freeze_sha256'] == plan['study_freeze_sha256']
    freeze = Path(plan['study_freeze_path'])
    assert sha(freeze) == plan['study_freeze_sha256']
    frozen = json.loads(freeze.read_text())
    root = Path(frozen['root'])
    sys.path.insert(0, str(root))
    from scripts.compare_report import compare_results
    from scripts.league_gates import panel_delta, direct_result
    from scripts.early_curriculum_study import GAME_FIELDS
    # Import the independently tested driver by its recorded committed path.
    import importlib.util
    driver_path = Path(frozen['driver']['path'])
    assert sha(driver_path) == frozen['driver']['sha256']
    spec = importlib.util.spec_from_file_location('targeting_eval_driver', driver_path)
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    checked_plan, checked_frozen = driver.check_plan(plan_path)
    assert checked_plan == plan and checked_frozen == frozen
    assert state['phase'] == plan['phase']
    phase = plan['phase']
    assert phase in ('selection', 'confirmation')
    assert state['source_before'] == state['source_after'] == frozen['identity']
    planned = plan['jobs']
    actual = state['jobs']
    assert len(planned) == len(actual)
    assert [r['name'] for r in planned] == [r['name'] for r in actual]
    by_role = {}
    csv_hashes = {}
    total = 0
    for job, done in zip(planned, actual):
        assert done['status'] == 'complete' and done['exit_code'] == 0
        target = Path(job['out'])
        assert Path(done['out']) == target and sha(target) == done['output_sha256']
        assert done['actual_games'] == job['games']
        driver.validate_output(target, job)
        frame = pd.read_csv(target)
        assert list(frame.columns) == list(GAME_FIELDS)
        assert len(frame) == job['games']
        assert job['role'] in ('baseline', 'P', 'PT')
        by_role.setdefault(job['role'], []).append((job, frame))
        csv_hashes[str(target)] = done['output_sha256']
        total += len(frame)
    roles = [name for name in ('P', 'PT') if name in frozen['weights']] if phase == 'selection' else [plan['candidate']]
    assert roles in (['P', 'PT'], ['P'], ['PT'])
    assert set(by_role) == {'baseline', *roles}
    expected_first = 841000 if phase == 'selection' else 842000
    expected_n = 100 if phase == 'selection' else 300
    frames, directs = {}, {}
    for role, entries in by_role.items():
        panel_frames, defaults, direct_frames = [], [], []
        for job, frame in entries:
            assert job['n_maps'] == expected_n
            opp = tuple(job['opponents'])
            if opp == PANEL:
                assert job['first_seed'] == expected_first
                panel_frames.append(frame)
            elif opp == (*PANEL, 'default'):
                assert job['first_seed'] == expected_first
                panel_frames.append(frame.loc[frame.opponent.isin(PANEL)])
                defaults.append(frame.loc[frame.opponent == 'default'])
            elif opp == ('default',):
                assert job['first_seed'] == expected_first
                defaults.append(frame)
            elif opp == (DIRECT,):
                assert role != 'baseline'
                assert job['first_seed'] == (841000 if phase == 'selection' else 843000)
                direct_frames.append(frame)
            else:
                raise ValueError(f'Unexpected opponent panel: {opp}')
        assert len(panel_frames) == len(defaults) == 1
        assert len(direct_frames) == (0 if role == 'baseline' else 1)
        frames[role] = pd.concat([*panel_frames, *defaults], ignore_index=True)
        if direct_frames:
            directs[role] = direct_frames[0]
    if phase == 'confirmation':
        selection_path = Path(plan['selection_summary_path'])
        assert sha(selection_path) == plan['selection_summary_sha256']
        selection = json.loads(selection_path.read_text())
        assert selection['phase'] == 'selection' and selection['nominee'] == plan['candidate']
        assert selection['study_freeze_sha256'] == plan['study_freeze_sha256']
        for path, digest in selection['csv_sha256'].items():
            assert sha(path) == digest
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
        assert panel['maps'] == expected_n and direct['maps'] == expected_n
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
    expected_total = (1400 + 1600*len(roles) if phase == 'selection' else 9000)
    assert total == expected_total
    result = dict(phase=phase, status='complete', study_freeze_sha256=plan['study_freeze_sha256'],
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
