"""Synthetic contracts for the final fixed-roster study; no models or games."""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import pytest

from scripts import early_curriculum_study as early
from scripts import final_battle_study as study


ROOT = Path(__file__).resolve().parents[1]


def weights(full=False):
    roles = ('baseline', 'PAIR18', 'PAIR24', 'FT18', 'Z36')
    if full:
        roles += ('C36', 'R36')
    return {role: f'{role}.pth' for role in roles}


@pytest.mark.parametrize('full,total,roles', [(False, 6240, 5), (True, 8800, 7)])
def test_fixed_selection_and_confirmation_schedules(tmp_path, full, total, roles):
    jobs = study.build_jobs(ROOT, tmp_path, weights(full), 'selection')
    assert len(jobs) == 2 * roles - 1
    assert sum(j['games'] for j in jobs) == total
    assert {j['first_seed'] for j in jobs} == {851000}
    assert {j['n_maps'] for j in jobs} == {80}
    assert all(j['workers'] == 2 and j['overrides'] == [] for j in jobs)
    confirms = study.build_jobs(ROOT, tmp_path, weights(full), 'confirmation', candidate='PAIR18')
    assert sum(j['games'] for j in confirms) == 12000
    assert {j['first_seed'] for j in confirms if j['timing_class'] == 'combined_panel'} == {852000}
    assert {j['first_seed'] for j in confirms if j['timing_class'] == 'direct'} == {853000}
    assert {j['n_maps'] for j in confirms} == {400}


@pytest.mark.parametrize('bad', [dict(baseline='a', P='b'),
    {k: v for k, v in weights(True).items() if k != 'C36'},
    {k: v for k, v in weights(True).items() if k != 'R36'},
    {**weights(), 'EXTRA': 'extra.pth'}])
def test_wrong_or_unpaired_roles_rejected(bad):
    with pytest.raises(ValueError):
        study.candidate_roles(bad)


def test_c36_never_confirmation_nominee(tmp_path):
    with pytest.raises(ValueError):
        study.build_jobs(ROOT, tmp_path, weights(True), 'confirmation', candidate='C36')


def test_gates_exact_boundaries_and_r36_control():
    panel = dict(delta=.01, low=.001)
    solution = dict(delta=0, low=-.009)
    default = dict(winrate=.99, delta=-.01)
    direct = dict(winrate=.5, low=.501)
    assert all(study.gates('confirmation', panel, solution, default, direct).values())
    assert not study.gates('confirmation', panel, dict(solution, low=-.01), default, direct)['solution_lower']
    assert not study.gates('confirmation', dict(panel, low=0), solution, default, direct)['panel_lower']
    assert not study.gates('confirmation', panel, solution, default, dict(direct, low=.5))['direct_lower']
    assert all(study.gates('selection', dict(panel, delta=.005), solution, default, direct).values())
    rchecks = study.gates('selection', panel, solution, default, direct,
                         control_panel=dict(delta=.02), control_solution=dict(delta=.001))
    assert not rchecks['control_panel'] and not rchecks['control_solution']


def result(delta=.02, solution=.01, passed=True):
    return dict(panel=dict(delta=delta), opponents=dict(solution92=dict(delta=solution)), passed=passed)


def test_nomination_tiebreaks_panel_solution_net_count_then_name():
    assert study.nominee({'C36': result(.99), 'Z36': result(), 'FT18': result(), 'PAIR18': result()}) == 'FT18'
    assert study.nominee({'PAIR18': result(), 'PAIR24': result(solution=.02)}) == 'PAIR24'
    assert study.nominee({'PAIR18': result(.03), 'PAIR24': result(solution=.02)}) == 'PAIR18'
    assert study.nominee({'C36': result(.99), 'PAIR18': result(passed=False)}) is None


def test_wall_rate_projection_never_divides_by_workers_and_reserves_transition():
    observed = dict(combined_panel=[], direct=[])
    games = dict(combined_panel=11200, direct=800)
    expected = 1.2 * (11200 * 2.22 + 800 * 3)
    assert study.project_seconds(games, observed) == pytest.approx(expected)
    assert study.GAME_END == datetime(2026, 11, 4, 12, 30, tzinfo=timezone.utc).timestamp()
    assert study.admit(games, observed, now=study.GAME_END - study.RESERVE - expected - 1) == pytest.approx(expected)
    with pytest.raises(ValueError, match='Insufficient time'):
        study.admit(games, observed, now=study.GAME_END - study.RESERVE - expected + 1)
    slower = dict(combined_panel=[4.44], direct=[])
    assert study.project_seconds(games, slower) == pytest.approx(2 * expected)


def write_games(path, job, value=1):
    rows = []
    for seed in range(job['first_seed'], job['first_seed'] + job['n_maps']):
        for side in study.SIDES:
            for opponent in job['opponents']:
                row = {key: 0 for key in early.GAME_FIELDS}
                score = value if opponent != 'default' else 1
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


def test_output_requires_every_expected_key_steps_and_v2(tmp_path):
    job = study.build_jobs(ROOT, tmp_path, weights(), 'selection')[0]
    target = Path(job['out'])
    write_games(target, job)
    assert study.validate_output(target, job) == 1120
    text = target.read_text()
    target.write_text('\n'.join(text.splitlines()[:-1]) + '\n')
    with pytest.raises(ValueError, match='Incomplete'):
        study.validate_output(target, job)
    target.write_text(text.replace(',303,', ',302,'))
    with pytest.raises(ValueError):
        study.validate_output(target, job)
    target.write_text(text)
    with target.open(newline='') as handle:
        rows = list(csv.DictReader(handle))
    rows[0]['point_counting_version'] = '1'
    with target.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=early.GAME_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match='point counting version'):
        study.validate_output(target, job)


def test_stop_file_and_battery_block_without_launch(tmp_path, monkeypatch):
    stop = tmp_path / 'STOP'
    monkeypatch.setattr(study, 'STOP_FILE', stop)
    monkeypatch.setattr(study, 'current_power', lambda: (True, 90))
    monkeypatch.setattr(study.time, 'time', lambda: study.GAME_END - 100)
    stop.write_text('quota threshold')
    with pytest.raises(ValueError, match='STOP'):
        study.check_runtime(start=True)
    stop.unlink()
    monkeypatch.setattr(study, 'current_power', lambda: (False, 25))
    with pytest.raises(ValueError, match='Battery'):
        study.check_runtime(start=False)
    monkeypatch.setattr(study.time, 'time', lambda: study.GAME_END)
    with pytest.raises(ValueError, match='deadline'):
        study.check_runtime(start=False)


def fixture_study(tmp_path, monkeypatch, full=False):
    """Use real schedules, CSV validation/stats and files; replace only identity/power."""
    freeze = tmp_path / 'freeze.json'
    identity = {'source': {'head': 'a' * 40}, 'weights': {}, 'driver': {}}
    frozen = dict(root=str(ROOT), python=sys.executable, weights=weights(full), identity=identity)
    freeze.write_text(json.dumps(frozen))
    monkeypatch.setattr(study, 'check_freeze', lambda path, **kw: json.loads(Path(path).read_text()))
    plan = study.prepare_phase(freeze, tmp_path / 'selection', 'selection')
    plan_path = tmp_path / 'selection/plan.json'
    done = []
    for job in plan['jobs']:
        target = Path(job['out'])
        value = 0 if job['role'] == 'baseline' else 1
        write_games(target, job, value)
        done.append(dict(name=job['name'], timing_class=job['timing_class'], status='complete',
                         exit_code=0, actual_games=job['games'], out=job['out'],
                         output_sha256=study.digest(target), wall_seconds=job['games'] * .01))
    state = dict(status='complete', phase='selection', plan_path=str(plan_path), plan_sha256=study.digest(plan_path),
                 study_freeze_sha256=study.digest(freeze), source_before=identity, source_after=identity,
                 jobs=done, completed_games=sum(j['games'] for j in plan['jobs']))
    state_path = tmp_path / 'selection/state.json'
    state_path.write_text(json.dumps(state))
    return freeze, plan_path, state_path


def test_real_summary_and_confirmation_bind_and_recompute_selection(tmp_path, monkeypatch):
    freeze, plan_path, state_path = fixture_study(tmp_path, monkeypatch)
    summary_path = tmp_path / 'summary.json'
    summary = study.summarize(plan_path, state_path, summary_path)
    assert summary['completed_games'] == 6240 and summary['nominee'] == 'FT18'
    assert summary['promotion_qualified'] is False
    confirmation = study.prepare_phase(freeze, tmp_path / 'confirmation', 'confirmation', candidate='FT18',
                                      selection_state=state_path, selection_summary=summary_path)
    assert sum(j['games'] for j in confirmation['jobs']) == 12000
    study.check_plan(tmp_path / 'confirmation/plan.json')
    summary['candidates']['FT18']['panel']['delta'] = .123
    summary_path.write_text(json.dumps(summary))
    with pytest.raises(ValueError):
        study.prepare_phase(freeze, tmp_path / 'forged', 'confirmation', candidate='FT18',
                            selection_state=state_path, selection_summary=summary_path)
    assert not (tmp_path / 'forged').exists()


def test_incomplete_or_csv_tampered_state_cannot_be_summarized(tmp_path, monkeypatch):
    freeze, plan_path, state_path = fixture_study(tmp_path, monkeypatch)
    state = json.loads(state_path.read_text())
    state['status'] = 'incomplete'
    state_path.write_text(json.dumps(state))
    with pytest.raises(ValueError):
        study.summarize(plan_path, state_path, tmp_path / 'no-summary.json')
    state['status'] = 'complete'
    state_path.write_text(json.dumps(state))
    Path(state['jobs'][0]['out']).write_text('bad csv')
    with pytest.raises(ValueError):
        study.summarize(plan_path, state_path, tmp_path / 'no-summary.json')
    assert not (tmp_path / 'no-summary.json').exists()


def test_phase_reservation_rejects_second_output_directory(tmp_path, monkeypatch):
    freeze, plan_path, state_path = fixture_study(tmp_path, monkeypatch)
    with pytest.raises(FileExistsError):
        study.prepare_phase(freeze, tmp_path / 'second-selection', 'selection')
    with pytest.raises(FileExistsError):
        study.run_phase(plan_path, start=True)
    assert not (tmp_path / 'second-selection').exists()


def test_freeze_verifies_head_and_live_source_identity(tmp_path, monkeypatch):
    tools = study.load_tools(ROOT)
    frozen = dict(schema_version=1, root=str(ROOT), weights=weights(), expected_head='a' * 40,
                  driver=dict(path=str(Path(study.__file__).resolve())), identity=dict(source=dict(head='a' * 40)))
    path = tmp_path / 'freeze.json'
    path.write_text(json.dumps(frozen))
    monkeypatch.setattr(study, 'identity', lambda f, t: f['identity'])
    assert study.check_freeze(path, tools=tools) == frozen
    with pytest.raises(ValueError, match='SHA'):
        study.check_freeze(path, expected_sha='0' * 64, tools=tools)
    frozen['expected_head'] = 'b' * 40
    path.write_text(json.dumps(frozen))
    with pytest.raises(ValueError, match='HEAD'):
        study.check_freeze(path, tools=tools)
    frozen['expected_head'] = 'a' * 40
    path.write_text(json.dumps(frozen))
    monkeypatch.setattr(study, 'identity', lambda f, t: dict(source=dict(head='a' * 40), changed=True))
    with pytest.raises(ValueError, match='freeze changed'):
        study.check_freeze(path, tools=tools)


def test_stop_cleans_real_owned_stdlib_child_group(tmp_path, monkeypatch):
    from types import SimpleNamespace
    stop = tmp_path / 'STOP'
    monkeypatch.setattr(study, 'STOP_FILE', stop)
    monkeypatch.setattr(study, 'current_power', lambda: (True, 90))
    monkeypatch.setattr(study, 'check_freeze', lambda *a, **k: {})
    monkeypatch.setattr(study, 'job_command', lambda *a: [sys.executable, '-B', '-c', 'import time; time.sleep(60)'])
    plan_path = tmp_path / 'plan.json'
    plan_path.write_text('{}')
    job = study.build_jobs(ROOT, tmp_path, weights(), 'selection')[0]
    frozen = dict(root=str(ROOT), python=sys.executable, frozen_weights={})
    plan = dict(study_freeze_path='unused', study_freeze_sha256='unused')
    tools = SimpleNamespace(early=early, jobs=SimpleNamespace(validate_inputs=lambda *a: None))
    record = dict(plan_sha256=study.digest(plan_path))

    def save():
        if record.get('pid'):
            stop.write_text('stop test')

    with pytest.raises(ValueError, match='STOP'):
        study.run_job(job, plan_path, plan, frozen, tools, record=record, save=save)
    assert record['status'] == 'incomplete'
    assert record['exit_code'] is not None
    assert not early.group_exists(record['pgid'])
    assert early.CURRENT is None


def test_foreign_process_parser_ignores_shell_text_but_catches_training():
    assert study.model_supervisor_command('/venv/bin/python -B -m scripts.final_rescue_train runarm --arm R')
    assert study.model_supervisor_command('/venv/bin/python /tmp/sherlock-final-20261103/train_supervisor.py')
    assert study.model_supervisor_command('/venv/bin/python -B -m scripts.final_battle_study run --plan p --start')
    assert not study.model_supervisor_command('/venv/bin/python -B -m scripts.final_battle_study prepare --out x')
    assert not study.model_supervisor_command("/bin/zsh -lc 'python -m scripts.final_rescue_train runarm'")
    assert not study.model_supervisor_command('/venv/bin/python -c "scripts.final_rescue_train runarm"')


def test_reduced_freeze_requires_technical_omission_reason(tmp_path):
    with pytest.raises(ValueError, match='omission reason'):
        study.create_freeze(ROOT, tmp_path / 'freeze.json', weights(),
                            python=sys.executable, expected_head='a' * 40)
    assert not (tmp_path / 'freeze.json').exists()


def test_full_roster_r36_cannot_outvote_better_control(tmp_path, monkeypatch):
    freeze, plan_path, state_path = fixture_study(tmp_path, monkeypatch, full=True)
    plan, state = json.loads(plan_path.read_text()), json.loads(state_path.read_text())
    for job, done in zip(plan['jobs'], state['jobs']):
        if job['role'] == 'R36':
            write_games(Path(job['out']), job, .5)
            done['output_sha256'] = study.digest(job['out'])
    state_path.write_text(json.dumps(state))
    result = study.summarize(plan_path, state_path, tmp_path / 'summary.json')
    assert result['completed_games'] == 8800
    assert result['candidates']['C36']['passed']
    assert result['nominee'] == 'FT18'
    assert not result['candidates']['R36']['gates']['control_panel']
    assert not result['candidates']['R36']['gates']['control_solution']
    assert not result['candidates']['R36']['passed']


def test_confirmation_summary_uses_all_12000_complete_games(tmp_path, monkeypatch):
    freeze, selection_plan, selection_state = fixture_study(tmp_path, monkeypatch)
    selection_summary = tmp_path / 'selection-summary.json'
    study.summarize(selection_plan, selection_state, selection_summary)
    plan = study.prepare_phase(freeze, tmp_path / 'confirmation', 'confirmation', candidate='FT18',
                               selection_state=selection_state, selection_summary=selection_summary)
    plan_path = tmp_path / 'confirmation/plan.json'
    state = json.loads(selection_state.read_text())
    done = []
    for job in plan['jobs']:
        target = Path(job['out'])
        write_games(target, job, 0 if job['role'] == 'baseline' else 1)
        done.append(dict(name=job['name'], timing_class=job['timing_class'], status='complete', exit_code=0,
                         actual_games=job['games'], out=job['out'], output_sha256=study.digest(target),
                         wall_seconds=job['games'] * .01))
    state.update(phase='confirmation', plan_path=str(plan_path), plan_sha256=study.digest(plan_path),
                 jobs=done, completed_games=12000)
    state_path = tmp_path / 'confirmation/state.json'
    state_path.write_text(json.dumps(state))
    summary = study.summarize(plan_path, state_path, tmp_path / 'confirmation-summary.json')
    assert summary['completed_games'] == 12000
    assert summary['promotion_qualified'] is True
    assert len(summary['candidates']['FT18']['gates']) == 7
    assert all(summary['candidates']['FT18']['gates'].values())
    with pytest.raises(FileExistsError):
        study.prepare_phase(freeze, tmp_path / 'second-confirmation', 'confirmation', candidate='FT18',
                            selection_state=selection_state, selection_summary=selection_summary)
    assert not (tmp_path / 'second-confirmation').exists()


def test_plan_tampering_cannot_change_rates_or_roles(tmp_path, monkeypatch):
    freeze, plan_path, state_path = fixture_study(tmp_path, monkeypatch)
    original = json.loads(plan_path.read_text())
    for field, changed in [('initial_seconds_per_game', dict(combined_panel=1.11, direct=1.5)),
                           ('future_confirmation_games', dict(combined_panel=0, direct=0)),
                           ('game_end_utc', '2026-11-04T16:00:00+00:00')]:
        plan = dict(original, **{field: changed})
        plan_path.write_text(json.dumps(plan))
        with pytest.raises(ValueError):
            study.check_plan(plan_path)
    plan = json.loads(json.dumps(original))
    plan['jobs'][0]['role'] = 'FT18'
    plan_path.write_text(json.dumps(plan))
    with pytest.raises(ValueError):
        study.check_plan(plan_path)
