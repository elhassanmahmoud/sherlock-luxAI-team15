"""Synthetic complete CSVs test the bounded study without models or games."""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import pytest

from scripts import early_curriculum_study as early
from scripts import network_breadth_study as study

ROOT = Path(__file__).resolve().parents[1]


def weights():
    return {role: f'{role}.pth' for role in ('baseline', 'SOLO28', 'FO42')}


def test_fixed_jobs_cover_exact_asymmetric_counts_and_separate_direct_seeds(tmp_path):
    screen = study.build_jobs(ROOT, tmp_path, weights(), 'selection')
    confirm = study.build_jobs(ROOT, tmp_path, weights(), 'confirmation', candidate='SOLO28')
    assert len(screen) == len(confirm) == 5
    assert sum(j['games'] for j in screen) == 920
    assert sum(j['games'] for j in confirm) == 4800
    assert {(j['first_seed'], j['n_maps']) for j in screen} == {(861000, 20)}
    assert sorted((j['first_seed'], j['n_maps'], j['games']) for j in confirm) == [
        (862000, 120, 1680), (862000, 120, 1680),
        (862120, 280, 560), (862120, 280, 560), (863000, 160, 320)]
    assert all(j['workers'] == 2 and j['overrides'] == [] for j in screen + confirm)
    with pytest.raises(ValueError): study.build_jobs(ROOT, tmp_path, weights(), 'confirmation', candidate='FT18')
    with pytest.raises(ValueError): study.candidate_roles({**weights(), 'OTHER': 'x'})


def test_rates_are_wall_time_and_only_rise_with_pilot_and_completed_jobs():
    games = dict(combined_panel=5320, direct=400)
    observed = dict(combined_panel=[], direct=[])
    assert study.project_seconds(games, observed) == pytest.approx(18278.4)
    assert study.admit(games, observed, now=study.GAME_END - 19479) == pytest.approx(18278.4)
    with pytest.raises(ValueError): study.admit(games, observed, now=study.GAME_END - 19478)
    assert study.project_seconds(games, dict(combined_panel=[5.2], direct=[])) == pytest.approx(36556.8)
    assert study.project_seconds(games, dict(combined_panel=[.1], direct=[.1])) == pytest.approx(18278.4)
    assert study.GAME_END == datetime(2026, 11, 4, 13, 30, tzinfo=timezone.utc).timestamp()


def test_quota_receipt_must_be_known_fresh_and_below_65(tmp_path):
    path = tmp_path / 'usage.json'
    now = datetime(2026, 11, 4, 8, tzinfo=timezone.utc).timestamp()
    good = dict(at='2026-11-04T07:55:00Z', ordinary_usage_allowed=True,
                max_used_percent=53, windows=[dict(used_percent=53)])
    with pytest.raises(ValueError): study.check_usage(path, now=now)
    path.write_text(json.dumps(good))
    assert study.check_usage(path, now=now)['max_used_percent'] == 53
    for change in [dict(at='2026-11-04T07:44:59Z'), dict(at='2026-11-04T08:00:01Z'),
                   dict(max_used_percent=65, windows=[dict(used_percent=65)]),
                   dict(windows=[]), dict(ordinary_usage_allowed=False),
                   dict(max_used_percent=53, windows=[dict(used_percent=70)])]:
        path.write_text(json.dumps({**good, **change}))
        with pytest.raises(ValueError): study.check_usage(path, now=now)


def test_all_seven_confirmation_gates_and_fixed_nomination():
    p, s, d, direct = dict(delta=.01, low=.001), dict(delta=0, low=-.009), dict(winrate=.99, delta=-.01), dict(winrate=.5, low=.501)
    assert len(study.gates('confirmation', p, s, d, direct)) == 7
    assert all(study.gates('confirmation', p, s, d, direct).values())
    assert not study.gates('confirmation', dict(p, low=0), s, d, direct)['panel_lower']
    assert not study.gates('confirmation', p, dict(s, low=-.01), d, direct)['solution_lower']
    assert not study.gates('confirmation', p, s, d, dict(direct, low=.5))['direct_lower']
    counts = {opponent: dict(candidate=dict(wins=1, draws=0), baseline=dict(wins=0, draws=0))
              for opponent in study.PANEL}
    result = dict(panel=dict(delta=.02), opponents=dict(solution92=dict(delta=.01)), counts=counts, passed=True)
    assert study.nominee(dict(FO42=result, SOLO28=result)) == 'SOLO28'
    assert study.nominee(dict(FO42=dict(result, passed=False))) is None


def write_games(path, job, value):
    rows = []
    for seed in range(job['first_seed'], job['first_seed'] + job['n_maps']):
        for side in ('player_0', 'player_1'):
            for opponent in job['opponents']:
                score = 1 if opponent == 'default' else value
                row = {key: 0 for key in early.GAME_FIELDS}
                row.update(seed=seed, side=side, opponent=opponent, result=score,
                           game_win=int(score == 1), point_win=score,
                           our_wins=int(score == 1), opp_wins=int(score == 0),
                           our_points=int(score == 1), opp_points=int(score == 0),
                           point_counting_version=2, steps=303, secs=.01)
                rows.append(row)
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=early.GAME_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def complete_state(plan, plan_path, identity, values):
    done = []
    for job in plan['jobs']:
        write_games(Path(job['out']), job, values(job))
        done.append(dict(name=job['name'], timing_class=job['timing_class'], status='complete',
                         exit_code=0, actual_games=job['games'], out=job['out'],
                         output_sha256=study.digest(job['out']), wall_seconds=job['games'] * .01))
    state = dict(status='complete', phase=plan['phase'], plan_path=str(plan_path),
                 plan_sha256=study.digest(plan_path), study_freeze_sha256=plan['study_freeze_sha256'],
                 source_before=identity, source_after=identity, jobs=done,
                 completed_games=sum(j['games'] for j in plan['jobs']))
    path = plan_path.parent / 'state.json'
    path.write_text(json.dumps(state))
    return path


@pytest.fixture
def screen(tmp_path, monkeypatch):
    # The identity reads repository/interpreter/model state, not synthetic CSV semantics.
    identity = dict(source=dict(head='a' * 40), weights={}, driver={})
    frozen = dict(root=str(ROOT), python=sys.executable, weights=weights(), identity=identity,
                  pilot_observed_seconds_per_game=dict(combined_panel=[], direct=[]))
    freeze = tmp_path / 'freeze.json'
    freeze.write_text(json.dumps(frozen))
    monkeypatch.setattr(study, 'check_freeze', lambda path, **kw: json.loads(Path(path).read_text()))
    monkeypatch.setattr(study, 'analysis_output', lambda root, path: study.new_path(path))
    plan = study.prepare_phase(freeze, tmp_path / 'selection', 'selection')
    plan_path = tmp_path / 'selection/plan.json'
    state = complete_state(plan, plan_path, identity, lambda job: 0 if job['role'] == 'baseline' else 1)
    summary = tmp_path / 'selection-summary.json'
    assert study.summarize(plan_path, state, summary)['nominee'] == 'SOLO28'
    return freeze, plan_path, state, summary, identity


def test_extra_solution_changes_solution_only_and_all_complete_maps_are_used(screen, tmp_path):
    freeze, _, state, summary, identity = screen
    plan = study.prepare_phase(freeze, tmp_path / 'confirmation', 'confirmation', candidate='SOLO28',
                               selection_state=state, selection_summary=summary)
    plan_path = tmp_path / 'confirmation/plan.json'
    # Candidate wins every panel game but loses the extra 280 Solution maps.
    # Reference loses panel games but wins all extra Solution maps.
    state = complete_state(plan, plan_path, identity,
        lambda job: int((job['role'] != 'baseline') != (job['kind'] == 'solution_extra')))
    result = study.summarize(plan_path, state, tmp_path / 'confirmation-summary.json')
    r = result['candidates']['SOLO28']
    assert result['completed_games'] == 4800
    assert r['panel']['maps'] == 120 and r['panel']['delta'] == 1
    assert r['direct']['maps'] == 160 and r['direct']['games'] == 320
    assert r['opponents']['solution92']['maps'] == 400
    assert r['opponents']['solution92']['winrate'] == .3
    assert r['opponents']['solution92']['ref_winrate'] == .7
    assert r['opponents']['solution92']['delta'] == pytest.approx(-.4)
    assert r['counts']['solution92']['candidate']['games'] == 800
    assert r['counts']['default']['candidate']['games'] == 240
    assert not result['promotion_qualified']
    with pytest.raises(FileExistsError):
        study.prepare_phase(freeze, tmp_path / 'again', 'confirmation', candidate='SOLO28',
                            selection_state=screen[2], selection_summary=summary)


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'extra', 'steps', 'version'])
def test_corrupt_or_partial_job_never_yields_summary(screen, tmp_path, mutation):
    _, plan_path, state_path, _, _ = screen
    state = json.loads(state_path.read_text())
    target = Path(state['jobs'][0]['out'])
    with target.open(newline='') as handle: rows = list(csv.DictReader(handle))
    if mutation == 'missing': rows.pop()
    if mutation == 'duplicate': rows[-1] = dict(rows[0])
    if mutation == 'extra': rows[-1]['seed'] = 999999
    if mutation == 'steps': rows[0]['steps'] = 302
    if mutation == 'version': rows[0]['point_counting_version'] = 1
    with target.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=early.GAME_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    state['jobs'][0]['output_sha256'] = study.digest(target)
    state_path.write_text(json.dumps(state))
    with pytest.raises(ValueError): study.summarize(plan_path, state_path, tmp_path / 'bad-summary.json')
    assert not (tmp_path / 'bad-summary.json').exists()


def test_immutable_nomination_and_single_screen(screen, tmp_path):
    freeze, plan, state, summary, _ = screen
    with pytest.raises(FileExistsError): study.prepare_phase(freeze, tmp_path / 'second', 'selection')
    with pytest.raises(ValueError):
        study.prepare_phase(freeze, tmp_path / 'wrong', 'confirmation', candidate='FO42',
                            selection_state=state, selection_summary=summary)
    data = json.loads(summary.read_text())
    data['nominee'] = 'FO42'
    summary.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        study.prepare_phase(freeze, tmp_path / 'forged', 'confirmation', candidate='FO42',
                            selection_state=state, selection_summary=summary)


def test_equal_panel_totals_use_network_tiebreak_despite_float_map_placement(screen):
    _, plan_path, state_path, _, identity = screen
    plan = json.loads(plan_path.read_text())
    complete_state(plan, plan_path, identity, lambda job: int(job['kind'] == 'direct'))
    state = json.loads(state_path.read_text())
    for job, done in zip(plan['jobs'], state['jobs']):
        if job['kind'] != 'panel' or job['role'] == 'baseline':
            continue
        target = Path(job['out'])
        with target.open(newline='') as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            # Both have five wins outside Solution. SOLO spreads them over five
            # maps; FO puts all five non-Solution opponent wins on one map.
            wins = (row['side'] == 'player_0' and (
                row['opponent'] == 'sol92_sq' and int(row['seed']) < 861005
                if job['role'] == 'SOLO28' else
                int(row['seed']) == 861000 and row['opponent'] in study.PANEL[1:]))
            if wins:
                row.update(result=1, game_win=1, point_win=1, our_wins=1,
                           opp_wins=0, our_points=1, opp_points=0)
        with target.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=early.GAME_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        done['output_sha256'] = study.digest(target)
    state_path.write_text(json.dumps(state))
    summary = study.summary_data(plan_path, state_path)
    solo, fo = (summary['candidates'][role] for role in ('SOLO28', 'FO42'))
    assert solo['panel']['delta'] == .020833333333333332
    assert fo['panel']['delta'] == .020833333333333336
    for result in (solo, fo):
        assert sum(result['counts'][opponent]['candidate']['wins'] for opponent in study.PANEL) == 5
        assert sum(result['counts'][opponent]['candidate']['draws'] for opponent in study.PANEL) == 0
        assert result['counts']['solution92']['candidate']['wins'] == 0
        assert result['passed']
    assert summary['nominee'] == 'SOLO28'


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'extra'])
def test_solution_merge_rejects_bad_extra_block_even_with_complete_panel(tmp_path, mutation):
    import pandas as pd
    jobs = study.build_jobs(ROOT, tmp_path, weights(), 'confirmation', candidate='SOLO28')
    frames = {}
    for job in jobs[:2]:
        write_games(Path(job['out']), job, 1)
        frames[job['kind']] = pd.read_csv(job['out'])
    assert len(study.combined_solution(frames, 'confirmation')) == 800
    extra = frames['solution_extra']
    if mutation == 'missing': frames['solution_extra'] = extra.iloc[:-2]
    if mutation == 'duplicate': frames['solution_extra'] = pd.concat([extra, extra.iloc[:2]])
    if mutation == 'extra': frames['solution_extra'] = extra.assign(seed=extra.seed + 1)
    with pytest.raises(ValueError): study.combined_solution(frames, 'confirmation')


def test_plan_changes_to_deadline_work_or_rates_cannot_be_adopted(screen):
    _, plan_path, _, _, _ = screen
    original = json.loads(plan_path.read_text())
    for change in [dict(game_end_utc='2026-11-04T15:00:00+00:00'),
                   dict(initial_seconds_per_game=dict(combined_panel=1.3, direct=1.75)),
                   dict(future_confirmation_games=dict(combined_panel=0, direct=0)),
                   dict(prior_observed_seconds_per_game=dict(combined_panel=[.1], direct=[]))]:
        plan_path.write_text(json.dumps({**original, **change}))
        with pytest.raises(ValueError): study.check_plan(plan_path)


def test_pilot_counts_and_slower_observations_are_required():
    pilot = dict(status='complete', jobs=[dict(status='complete', timing_class=kind,
                 actual_games=count, wall_seconds=count * rate)
                 for kind, count, rate in [('combined_panel', 12, 3), ('combined_panel', 12, 1),
                                          ('combined_panel', 12, 2), ('direct', 4, 4), ('direct', 4, 1)]])
    rates = study.pilot_rates(pilot)
    assert study.project_seconds(dict(combined_panel=1, direct=0), rates) == pytest.approx(3.6)
    pilot['jobs'].pop()
    with pytest.raises(ValueError): study.pilot_rates(pilot)


def test_stop_cleans_only_real_owned_process_group(tmp_path, monkeypatch):
    from types import SimpleNamespace
    stop = tmp_path / 'STOP'
    monkeypatch.setattr(study, 'STOP_FILE', stop)
    monkeypatch.setattr(study, 'current_power', lambda: (True, 90))
    monkeypatch.setattr(study, 'check_freeze', lambda *args, **kwargs: {})
    monkeypatch.setattr(study, 'job_command', lambda *args: [sys.executable, '-B', '-c', 'import time; time.sleep(60)'])
    plan_path = tmp_path / 'plan.json'
    plan_path.write_text('{}')
    job = study.build_jobs(ROOT, tmp_path, weights(), 'selection')[0]
    frozen = dict(root=str(ROOT), python=sys.executable, frozen_weights={})
    plan = dict(study_freeze_path='unused', study_freeze_sha256='unused')
    tools = SimpleNamespace(early=early, jobs=SimpleNamespace(validate_inputs=lambda *args: None))
    record = dict(plan_sha256=study.digest(plan_path))
    def save():
        if record.get('pid'): stop.write_text('stop')
    with pytest.raises(ValueError, match='STOP'):
        study.run_job(job, plan_path, plan, frozen, tools, record=record, save=save)
    assert record['status'] == 'incomplete' and record['exit_code'] is not None
    assert not early.group_exists(record['pgid'])
    assert early.CURRENT is None


def test_foreign_breadth_supervisor_and_battery_deadline_blocks(tmp_path, monkeypatch):
    assert study.model_supervisor_command('/Library/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python -B -m scripts.network_breadth_study run --plan p --start')
    assert study.model_supervisor_command('/venv/bin/python -B -m scripts.network_breadth_study run --plan p --start')
    assert study.model_supervisor_command('/venv/bin/python scripts/network_breadth_study.py run --plan p --start')
    assert not study.model_supervisor_command('/venv/bin/python -m scripts.network_breadth_study prepare --out x')
    assert not study.model_supervisor_command('/bin/zsh -c "python -m scripts.network_breadth_study run"')
    monkeypatch.setattr(study, 'STOP_FILE', tmp_path / 'STOP')
    monkeypatch.setattr(study.time, 'time', lambda: study.GAME_END - 1)
    monkeypatch.setattr(study, 'current_power', lambda: (False, 34))
    with pytest.raises(ValueError, match='Battery'): study.check_runtime(start=True)
    monkeypatch.setattr(study, 'current_power', lambda: (False, 25))
    with pytest.raises(ValueError, match='Battery'): study.check_runtime(start=False)
    monkeypatch.setattr(study.time, 'time', lambda: study.GAME_END)
    with pytest.raises(ValueError, match='deadline'): study.check_runtime(start=False)


def test_new_freeze_name_cannot_restart_same_study(tmp_path):
    base = tmp_path / 'experiments/analysis/network_breadth_20261104'
    base.mkdir(parents=True)
    first, second = base / 'first.json', base / 'second.json'
    study.reserve_study(tmp_path, first)
    with pytest.raises(FileExistsError): study.reserve_study(tmp_path, second)
    assert json.loads(study.study_reservation(tmp_path).read_text()) == dict(freeze_path=str(first))


def test_freeze_checks_pilot_rates_and_live_identity(tmp_path, monkeypatch):
    base = tmp_path / 'experiments/analysis/network_breadth_20261104'
    base.mkdir(parents=True)
    pilot = dict(status='complete', jobs=[dict(status='complete', timing_class=kind,
                 actual_games=count, wall_seconds=count * rate)
                 for kind, count, rate in [('combined_panel', 12, 3), ('combined_panel', 12, 1),
                                          ('combined_panel', 12, 2), ('direct', 4, 4), ('direct', 4, 1)]])
    pilot_path = base / 'pilot.json'
    pilot_path.write_text(json.dumps(pilot))
    frozen = dict(schema_version=1, root=str(tmp_path), weights=weights(), expected_head='a' * 40,
                  driver=dict(path=str(Path(study.__file__).resolve())), identity=dict(source=dict(head='a' * 40)),
                  pilot_receipt_path=str(pilot_path), pilot_observed_seconds_per_game=dict(combined_panel=[3, 1, 2], direct=[4, 1]))
    path = base / 'freeze.json'
    path.write_text(json.dumps(frozen))
    study.reserve_study(tmp_path, path)
    monkeypatch.setattr(study, 'identity', lambda value, tools: value['identity'])
    assert study.check_freeze(path, tools=object()) == frozen
    frozen['pilot_observed_seconds_per_game']['combined_panel'] = [1]
    path.write_text(json.dumps(frozen))
    with pytest.raises(ValueError, match='Pilot'): study.check_freeze(path, tools=object())
    frozen['pilot_observed_seconds_per_game']['combined_panel'] = [3, 1, 2]
    path.write_text(json.dumps(frozen))
    monkeypatch.setattr(study, 'identity', lambda value, tools: dict(changed=True))
    with pytest.raises(ValueError, match='freeze changed'): study.check_freeze(path, tools=object())
