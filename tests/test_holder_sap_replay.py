"""Bounded holder-SAP runner contracts with toy states, no model or game loads."""
import gzip
import importlib
import importlib.util
import json
from contextlib import nullcontext
from types import SimpleNamespace

import numpy as np
import pytest


def implementation():
    assert importlib.util.find_spec('scripts.holder_sap_replay') is not None, 'holder replay implementation missing'
    return importlib.import_module('scripts.holder_sap_replay')


def test_fixed_keys_and_atomic_full_game_budget():
    p = implementation()
    assert p.MAPS == (9946007, 2000000, 2000001, 2000009, 2000029, 2000035, 2000045, 2000055)
    assert p.FIRST == ((9946007, 'player_0'), (2000000, 'player_0'))
    assert len(p.KEYS) == len(set(p.KEYS)) == 16
    assert p.phase_keys('technical') + p.phase_keys('remaining') == list(p.KEYS)
    assert p.LIMITS['started_runs'] == 88
    assert p.LIMITS['started_games'] == 32
    assert p.LIMITS['started_alternatives'] == 48
    assert p.LIMITS['started_repeats'] == 8
    assert p.LIMITS['total_steps'] == 26664 == 88*303
    assert p.LIMITS['diagnostic_steps'] == 48*303
    counts = {k: 0 for k in p.LIMITS}; prior = counts.copy()
    prior['total_steps'] = 26664
    with pytest.raises(ValueError, match='limit'):
        p.bump(counts, prior, 'total_steps', 'diagnostic_steps')
    assert not any(counts.values())


class Actor:
    opportunities = True
    def __init__(self):
        self.caught_errors = self.intervention_hits = 0
        self.collect = False
        self.used_matches = set()
        self.candidate = self.intervention = None
        self.seen = []

    def act(self, step, obs):
        self.candidate = None; self.seen.append(step)
        if self.opportunities and self.collect and step % 101 in (2, 3):
            self.candidate = dict(step=step, match=step//101, match_step=step%101,
                uid=0, network_action=0, action=5, sap=[2., 3.], energy=50., position=[1, 1])
            self.used_matches.add(step//101)
        action = [5, 2, 3]
        if self.intervention is not None and step == self.intervention['step']:
            self.intervention_hits += 1
            action = [0, 0, 0]
        return np.array([action])


def install_runtime(monkeypatch, p, *, opportunities=True):
    actors, calls = [], []
    def runtime(seed, side, weights, instrumented):
        actor = Actor(); actor.opportunities = opportunities; actors.append(actor)
        env = SimpleNamespace(state=0, close=lambda: None)
        obs = {s: {'match_steps': 0} for s in ('player_0', 'player_1')}
        return env, actor, Actor(), obs, 'frozen'
    def frame(env, actor, opponent, obs, side, number, *, actions, before, on_env_step):
        calls.append(number); env.state += 1; on_env_step()
        terminal = (dict(winner=0, reason='points', points=[101, 0], energies=[1, 1],
                        wins=[number//101+1, 0]) if number%101 == 100 else None)
        row = dict(step=number, before_state=str(number), before_obs=str(number),
            after_state=str(number+1), after_obs=str(number+1),
            actions={s: actions[s].tolist() for s in actions}, points=[1, 0],
            point_state=[number%101+1, 0], terminal=terminal, done=number==302)
        row['sha256'] = p.exact_digest(row)
        return {s: {'match_steps': (number+1)%101} for s in obs}, row
    monkeypatch.setattr(p, 'make_runtime', runtime)
    monkeypatch.setattr(p, 'step_frame', frame)
    monkeypatch.setattr(p, 'module_fingerprint', lambda _: 'frozen')
    return actors, calls


def run_toy(p, tmp_path, name, role, **kwargs):
    entry = dict(role=role, planned_steps=303, attempted_steps=0, steps=0, archived_frames=0)
    result, frames = p.play_run(1, 'player_0', 'unused', role=role, out=tmp_path,
        name=name, entry=entry, guard=lambda: None, on_attempt=lambda: None,
        save=lambda: None, **kwargs)
    return entry, result, frames


def test_first_event_each_match_one_intervention_and_full_game(monkeypatch, tmp_path):
    p = implementation(); actors, calls = install_runtime(monkeypatch, p)
    _, _, reference = run_toy(p, tmp_path, 'reference', 'reference')
    _, collector, baseline = run_toy(p, tmp_path, 'collector', 'collector', expected=reference)
    assert baseline == reference
    assert [c['step'] for c in collector['candidates']] == [2, 103, 204]
    candidate = collector['candidates'][0]
    entry, result, alternative = run_toy(p, tmp_path, 'alternative', 'alternative',
        expected=baseline, opportunity=candidate)
    assert alternative[:2] == baseline[:2]
    assert alternative[2]['actions']['player_0'] == [[0, 0, 0]]
    assert alternative[3]['actions']['player_0'] == [[5, 2, 3]]
    assert entry['steps'] == entry['attempted_steps'] == entry['archived_frames'] == 303
    assert result['full_game'] and len(result['matches']) == 3
    assert actors[-1].intervention_hits == 1 and len(actors) == 3
    assert calls[-303:] == list(range(303))
    pair = p.make_pair(baseline, alternative, candidate, 'player_0', tmp_path/'pair.json')
    assert pair['effective'] and pair['delta_game_win'] == pair['delta_current_match_win'] == 0
    assert pair['baseline']['frames'] == baseline
    assert len(pair['alternative']['matches']) == 3


def test_prefix_failure_archives_actual_frame_and_partial_attempts(monkeypatch, tmp_path):
    p = implementation(); install_runtime(monkeypatch, p)
    _, collector, full = run_toy(p, tmp_path, 'collector', 'collector')
    wrong = json.loads(json.dumps(full)); wrong[1]['after_obs'] = 'wrong'
    entry = dict(planned_steps=303, attempted_steps=0, steps=0, archived_frames=0)
    with pytest.raises(ValueError, match='prefix'):
        p.play_run(1, 'player_0', 'unused', role='alternative', out=tmp_path,
            name='failed', entry=entry, guard=lambda: None, on_attempt=lambda: None,
            save=lambda: None, expected=wrong, opportunity=collector['candidates'][0])
    rows = [json.loads(r) for r in gzip.open(tmp_path/'failed.frames.jsonl.gz', 'rt')]
    assert len(rows) == entry['steps'] == entry['attempted_steps'] == 2
    evidence = json.loads((tmp_path/'failed.mismatch.json').read_text())
    assert evidence['actual'] == rows[-1] and evidence['step'] == 1


def test_repeat_compares_late_third_match(monkeypatch, tmp_path):
    p = implementation(); install_runtime(monkeypatch, p)
    _, collector, full = run_toy(p, tmp_path, 'collector', 'collector')
    event = collector['candidates'][0]
    _, _, alternative = run_toy(p, tmp_path, 'alternative', 'alternative', expected=full, opportunity=event)
    wrong = json.loads(json.dumps(alternative)); wrong[290]['after_obs'] = 'wrong'
    with pytest.raises(ValueError, match='repeat'):
        run_toy(p, tmp_path, 'repeat', 'repeat', expected=full, opportunity=event, repeat_expected=wrong)
    assert json.loads((tmp_path/'repeat.mismatch.json').read_text())['step'] == 290


def set_outcomes(frames, winners):
    wins = [0, 0]
    for match, winner in enumerate(winners):
        wins[winner] += 1
        frame = frames[match*101+100]
        frame['terminal'] = dict(winner=winner, reason='random', energies=[0, 0], points=[0, 0], wins=wins.copy())


def test_full_game_and_current_match_labels_are_distinct(monkeypatch, tmp_path):
    p = implementation(); install_runtime(monkeypatch, p)
    _, collector, base = run_toy(p, tmp_path, 'collector', 'collector')
    event = collector['candidates'][0]
    _, _, alt = run_toy(p, tmp_path, 'alternative', 'alternative', expected=base, opportunity=event)
    set_outcomes(base, [1, 1, 0]); set_outcomes(alt, [1, 0, 0])
    pair = p.make_pair(base, alt, event, 'player_0', tmp_path/'pair.json')
    assert pair['delta_game_win'] == 1 and pair['delta_current_match_win'] == 0
    set_outcomes(base, [0, 0, 1]); set_outcomes(alt, [1, 0, 0])
    pair = p.make_pair(base, alt, event, 'player_0', tmp_path/'pair2.json')
    assert pair['delta_game_win'] == 0 and pair['delta_current_match_win'] == -1


def setup_controller(monkeypatch, tmp_path, p, *, opportunities=True):
    actors, calls = install_runtime(monkeypatch, p, opportunities=opportunities)
    weight = tmp_path/'weight'; weight.write_bytes(b'fixed')
    monkeypatch.setattr(p, 'V14_SHA', p.digest(weight))
    monkeypatch.setattr(p, 'source_identity', lambda *args: {'head': 'fixed'})
    monkeypatch.setattr(p, 'protected_inputs', lambda *args: [weight])
    monkeypatch.setattr(p, 'admitted_inputs', lambda: [weight])
    monkeypatch.setattr(p, 'verify_historical', lambda *args: {'synthetic': True})
    monkeypatch.setattr(p, 'resource_lock', lambda *args: nullcontext())
    class Guard:
        def __init__(self, state): self.state = state
        def __call__(self, *args): self.state['last_usage'] = {'usedPercent': 80}
    monkeypatch.setattr(p, 'Guard', Guard)
    return dict(weights=weight, usage_file=tmp_path/'usage', stop_file=tmp_path/'stop', expected_head='fixed'), actors, calls


def test_two_phases_all_88_full_games_require_actual_bound_acceptance(monkeypatch, tmp_path):
    p = implementation(); kwargs, actors, _ = setup_controller(monkeypatch, tmp_path, p)
    tech = p.run_probe(tmp_path/'technical', phase='technical', **kwargs)
    assert tech['counters']['started_runs'] == 12
    assert tech['execution_totals']['returned_full_length_runs'] == 12
    with pytest.raises(ValueError, match='acceptance'):
        p.run_probe(tmp_path/'remaining', phase='remaining', **kwargs)
    previous = tmp_path/'technical/manifest.json'; acceptance = tmp_path/'accepted.json'
    acceptance.write_text(json.dumps({'status': 'accepted', 'manifest_sha256': p.digest(previous)}))
    remaining = p.run_probe(tmp_path/'remaining', phase='remaining', previous=previous, acceptance=acceptance, **kwargs)
    totals = remaining['combined_execution_totals']
    assert totals['entered_runs'] == totals['completed_runs'] == totals['returned_full_length_runs'] == 88
    assert totals['attempted_engine_steps'] == totals['returned_engine_steps'] == 26664
    assert remaining['summary']['cases'] == 48
    assert len(actors) == 88
    with pytest.raises(ValueError, match='overwrite'):
        p.run_probe(tmp_path/'remaining', phase='remaining', previous=previous, acceptance=acceptance, **kwargs)
    artifact = next(iter(tech['artifacts']))
    with open(artifact, 'ab') as f: f.write(b'tamper')
    with pytest.raises(ValueError, match='artifact'):
        p.load_technical(previous, acceptance, {'head': 'fixed'})


def test_no_opportunities_are_valid_null_cases(monkeypatch, tmp_path):
    p = implementation(); kwargs, _, _ = setup_controller(monkeypatch, tmp_path, p, opportunities=False)
    state = p.run_probe(tmp_path/'technical', phase='technical', **kwargs)
    assert state['counters']['started_runs'] == 4
    assert all(g['collector']['candidates'] == [] for g in state['games'])
    assert state['summary']['cases'] == 0 and not state['summary']['passed']


def test_failed_engine_call_is_charged_before_entry(monkeypatch, tmp_path):
    p = implementation(); kwargs, _, _ = setup_controller(monkeypatch, tmp_path, p)
    def broken(*args, **kwargs): raise RuntimeError('engine failed')
    monkeypatch.setattr(p, 'step_frame', broken)
    with pytest.raises(RuntimeError, match='engine failed'):
        p.run_probe(tmp_path/'technical', phase='technical', **kwargs)
    state = json.loads((tmp_path/'technical/manifest.json').read_text())
    assert state['status'] == 'failed'
    assert state['counters']['started_runs'] == state['counters']['total_steps'] == 1
    assert state['runs'][0]['attempted_steps'] == 1 and state['runs'][0]['steps'] == 0
    p.verify_ledger(state, complete=False)


def test_summary_gate_requires_distinct_whole_game_rescues_and_nonnegative_matches():
    p = implementation()
    rows = [dict(seed=100+i//3, side='player_0', candidate={'match': i%3}, effective=True,
        live_verified=True, prefix_verified=True, delta_game_win=int(i in (0, 3)),
        delta_current_match_win=0, delta_match_wins=int(i in (0, 3)), delta_points=0,
        baseline_game_won=0, alternative_game_won=int(i in (0, 3))) for i in range(12)]
    executions = [dict(status='complete', steps=303, planned_steps=303, attempted_steps=303,
        archived_frames=303, ended_episode=True)]
    summary = p.summarize(rows, executions)
    assert summary['technical_gate'] and summary['influence_gate'] and summary['label_gate'] and summary['passed']
    rows[3].update(delta_game_win=0, alternative_game_won=0)
    assert not p.summarize(rows, executions)['label_gate']
    rows[3].update(delta_game_win=1, alternative_game_won=1)
    rows[1]['delta_match_wins'] = -3
    assert not p.summarize(rows, executions)['label_gate']
    executions[0]['status'] = 'failed'
    assert not p.summarize(rows, executions)['technical_gate']


def test_public_frame_archives_set_bookkeeping_without_engine_attribution(monkeypatch):
    p = implementation()
    agent = SimpleNamespace(belief=SimpleNamespace(point_tiles=np.array([[True]]), dead_tiles={(1, 2)}),
        param_est=SimpleNamespace(log_drop=np.array([0., -1., -2.]), log_neb=np.array([0., -1.]), n_drop=2, n_neb=1),
        _prev_actions={0: 0}, _sap_hits={1: 2}, _sap_unknown={3, 2}, _pred_pending=[(1, 2, 3, 50., False)])
    original = dict(terminal=None, sha256='old')
    monkeypatch.setattr(p, 'terminal_step_frame', lambda *a, **k: ({'next': True}, original.copy()))
    following, frame = p.step_frame(None, agent, None, {'player_0': {'energy': np.array([50])}}, 'player_0', 1)
    assert following == {'next': True}
    assert frame['public_observation']['energy'] == [50]
    assert frame['own_belief']['dead_tiles'] == [[1, 2]]
    assert frame['own_bookkeeping']['_sap_unknown'] == [2, 3]
    assert frame['own_bookkeeping']['_prev_actions'] == {'0': 0}
    assert frame['public_parameter_estimates']['n_drop'] == 2
    assert frame['public_parameter_estimates']['log_drop'] == [0., -1., -2.]
    assert 'energy_causes' not in frame


def test_guard_uses_this_plan_and_refuses_parallel_replay(monkeypatch, tmp_path):
    p = implementation(); source = {'head': 'fixed'}; checked = []
    state = dict(stop_file=str(tmp_path/'stop'), usage_file='receipt', source=source,
                 inputs={}, protected={}, artifacts={})
    def identity(root, python, plans): checked.append(plans); return source
    monkeypatch.setattr(p, 'source_identity', identity)
    monkeypatch.setattr(p, 'check_usage', lambda *a, **k: {'usedPercent': 84})
    monkeypatch.setattr(p, 'read_power', lambda: {'ac': False, 'percent': 80})
    monkeypatch.setattr(p.subprocess, 'check_output', lambda *a, **k: '99999 99999 python -m scripts.holder_sap_replay --phase technical')
    monkeypatch.setattr(p, 'foreign_processes', lambda *a, **k: [])
    with pytest.raises(ValueError, match='process'):
        p.Guard(state)(True)
    assert checked == [p.PLANS] and all('2026-11-11-holder-sap' in str(x) for x in p.PLANS)
    monkeypatch.setattr(p.subprocess, 'check_output', lambda *a, **k: '')
    p.Guard(state)(True)
    assert state['last_usage']['usedPercent'] == 84
    (tmp_path/'stop').write_text('stop')
    with pytest.raises(ValueError, match='STOP'):
        p.Guard(state)()


def test_history_compares_all_native_actions_and_side_relative_csv(monkeypatch, tmp_path):
    p = implementation()
    trace = tmp_path/'trace.gz'; history = tmp_path/'history.json'; source = tmp_path/'source.csv'
    frames = [dict(actions={'player_0': [[0, 0, 0]]}) for _ in range(303)]
    with gzip.open(trace, 'wt') as f:
        for step in range(303): f.write(json.dumps(dict(key={'obs_step': step}, native_actions=[[0, 0, 0]]))+'\n')
    history.write_text(json.dumps({'games': [{'unobserved': {'our_wins': 1, 'opp_wins': 2, 'our_points': 7, 'opp_points': 5}}]}))
    source.write_text('seed,side,opponent,our_wins,opp_wins,our_points,opp_points\n2000000,player_1,solution92,3,0,10,4\n')
    monkeypatch.setattr(p, 'TRACE', trace); monkeypatch.setattr(p, 'HISTORY', history); monkeypatch.setattr(p, 'SOURCE_CSV', source)
    verified = p.verify_historical(9946007, 'player_0', {'wins': [1, 2], 'points': [7, 5]}, frames, tmp_path)
    assert verified['native_action_frames'] == 303 and not verified['full_state_parity_available']
    p.verify_historical(2000000, 'player_1', {'wins': [0, 3], 'points': [4, 10]}, frames, tmp_path)
    frames[302]['actions']['player_0'] = [[5, 1, 0]]
    with pytest.raises(ValueError, match='historical native'):
        p.verify_historical(9946007, 'player_0', {'wins': [1, 2], 'points': [7, 5]}, frames, tmp_path)
    assert json.loads((tmp_path/'9946007_player_0.historical-mismatch.json').read_text())['step'] == 302


def test_runtime_creation_failure_is_entered_before_loading(monkeypatch, tmp_path):
    p = implementation(); kwargs, _, _ = setup_controller(monkeypatch, tmp_path, p)
    def failed(*args): raise KeyboardInterrupt('stop before engine')
    monkeypatch.setattr(p, 'make_runtime', failed)
    with pytest.raises(KeyboardInterrupt):
        p.run_probe(tmp_path/'technical', phase='technical', **kwargs)
    state = json.loads((tmp_path/'technical/manifest.json').read_text())
    assert state['status'] == 'failed' and state['counters']['started_runs'] == 1
    assert state['counters']['total_steps'] == 0 and state['runs'][0]['status'] == 'failed'
    p.verify_ledger(state, complete=False)


def test_historical_config_only_allows_documented_inactive_added_flag():
    p=implementation()
    assert hasattr(p,'verify_historical_config')
    original={'smart_sap':False,'ram':False}
    p.verify_historical_config({**original,'cand_stall_rescue':False},original)
    assert original=={'smart_sap':False,'ram':False}
    for changed in ({**original,'cand_stall_rescue':True},
                    {**original,'cand_stall_rescue':False,'ram':True},
                    {**original,'cand_stall_rescue':False,'another_flag':False}):
        with pytest.raises(ValueError): p.verify_historical_config(changed,original)
