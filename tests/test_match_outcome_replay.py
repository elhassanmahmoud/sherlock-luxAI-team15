"""Fresh-prefix contracts using toy state only, never games or checkpoints."""
import gzip
import importlib
import importlib.util
import json
from types import SimpleNamespace

import numpy as np
import pytest


def implementation():
    assert importlib.util.find_spec('scripts.match_outcome_replay') is not None
    return importlib.import_module('scripts.match_outcome_replay')


def test_fixed_repair_keys_and_all_execution_limits():
    p = implementation()
    assert p.FIRST == ((11011007, 'player_0'), (11011017, 'player_0'))
    assert len(p.KEYS) == len(set(p.KEYS)) == 16
    assert p.phase_keys('technical') + p.phase_keys('remaining') == list(p.KEYS)
    assert len(p.phase_keys('remaining')) == 14
    assert p.LIMITS['started_games'] == 32
    assert p.LIMITS['started_alternatives'] == 48
    assert p.LIMITS['started_repeats'] == 8
    assert p.LIMITS['total_steps'] == 32*303 + 16*(101+202+303) + 8*303 == 21816
    counters = {k: 0 for k in p.LIMITS}
    prior = counters.copy(); prior['total_steps'] = 21816
    with pytest.raises(ValueError, match='limit'):
        p.bump(counters, prior, 'total_steps', 'diagnostic_steps')
    assert counters['total_steps'] == counters['diagnostic_steps'] == 0


class Actor:
    def __init__(self):
        self.caught_errors = 0
        self.collect = False
        self.used_matches = set()
        self.candidate = self.intervention = None
        self.intervention_hits = 0
        self.seen = []

    def act(self, step, obs):
        self.candidate = None
        self.seen.append(step)
        if self.collect and step % 101 == 40:
            self.candidate = dict(step=step, match=step//101, match_step=40,
                                  uid=0, proposal=0, alternative=1)
            self.used_matches.add(step//101)
        action = 0
        if self.intervention is not None and step == self.intervention['step']:
            self.intervention_hits += 1
            # Emitted SAP triple stands for all downstream processing.
            action = 5
        return np.array([[action, 2 if action else 0, 3 if action else 0]])


def install_runtime(monkeypatch, p):
    actors = []
    calls = []
    def runtime(seed, side, weights, instrumented):
        actor = Actor(); actors.append(actor)
        env = SimpleNamespace(state=0, close=lambda: None)
        obs = {s: {'match_steps': 0} for s in ('player_0', 'player_1')}
        return env, actor, Actor(), obs, 'frozen'
    def step(env, actor, opponent, obs, side, number, *, actions, before, on_env_step):
        calls.append((number, actions[side].tolist()))
        env.state += 1; on_env_step()
        final = number % 101 == 100
        terminal = dict(winner=0, reason='points', points=[101, 0], energies=[1, 1],
                        wins=[number//101+1, 0]) if final else None
        frame = dict(step=number, before_state=str(number), before_obs=str(number),
                     after_state=str(number+1), after_obs=str(number+1),
                     actions={s: actions[s].tolist() for s in actions},
                     points=[1, 0], point_state=[number%101+1, 0],
                     terminal=terminal, done=number == 302)
        frame['sha256'] = p.exact_digest(frame)
        following = {s: {'match_steps': (number+1)%101} for s in obs}
        return following, frame
    monkeypatch.setattr(p, 'make_runtime', runtime)
    monkeypatch.setattr(p, 'step_frame', step)
    monkeypatch.setattr(p, 'module_fingerprint', lambda agent: 'frozen')
    return actors, calls


def run_toy(p, tmp_path, name, role, **kwargs):
    entry = dict(role=role, seed=1, side='player_0', planned_steps=303 if role in ('reference','collector') else 101,
                 attempted_steps=0, steps=0, archived_frames=0)
    result, frames = p.play_run(1, 'player_0', 'unused', role=role, out=tmp_path,
                               name=name, entry=entry, guard=lambda: None,
                               on_attempt=lambda: None, save=lambda: None, **kwargs)
    return entry, result, frames


def test_fresh_full_baseline_and_one_shot_alternative_include_final_action(monkeypatch, tmp_path):
    p = implementation(); actors, calls = install_runtime(monkeypatch, p)
    _, reference, ref_frames = run_toy(p, tmp_path, 'reference', 'reference')
    _, collector, full = run_toy(p, tmp_path, 'collector', 'collector', expected=ref_frames)
    assert full == ref_frames and len(full) == 303
    assert [c['step'] for c in collector['candidates']] == [40, 141, 242]
    candidate = collector['candidates'][0]
    entry, result, alternative = run_toy(p, tmp_path, 'alternative', 'alternative',
                                        expected=full, opportunity=candidate)
    assert [f['step'] for f in alternative] == list(range(101))
    assert alternative[:40] == full[:40]
    assert alternative[40]['actions']['player_0'] == [[5, 2, 3]]
    assert alternative[41]['actions']['player_0'] == [[0, 0, 0]]
    assert alternative[-1]['terminal'] is not None
    assert entry['steps'] == entry['attempted_steps'] == entry['archived_frames'] == 101
    assert actors[-1].intervention_hits == 1 and len(actors) == 3
    assert [n for n, _ in calls[-101:]] == list(range(101))
    pair = p.make_pair(full, alternative, candidate, 'player_0', tmp_path/'pair-mismatch.json')
    assert pair['effective'] and pair['delta_win'] == 0
    assert pair['baseline']['frames'] == full[40:101]
    assert pair['baseline']['sha256'] == p.exact_digest(full[40:101])


def test_prefix_failure_archives_actual_failed_frame_and_exact_lengths(monkeypatch, tmp_path):
    p = implementation(); install_runtime(monkeypatch, p)
    _, collector, full = run_toy(p, tmp_path, 'collector', 'collector')
    expected = json.loads(json.dumps(full)); expected[12]['after_obs'] = 'different'
    entry = dict(role='alternative', seed=1, side='player_0', planned_steps=101,
                 attempted_steps=0, steps=0, archived_frames=0)
    with pytest.raises(ValueError, match='prefix'):
        p.play_run(1, 'player_0', 'unused', role='alternative', out=tmp_path,
                   name='failed', entry=entry, expected=expected,
                   opportunity=collector['candidates'][0], guard=lambda: None,
                   on_attempt=lambda: None, save=lambda: None)
    rows = [json.loads(x) for x in gzip.open(tmp_path/'failed.frames.jsonl.gz', 'rt')]
    assert len(rows) == entry['steps'] == entry['attempted_steps'] == entry['archived_frames'] == 13
    mismatch = json.loads((tmp_path/'failed.mismatch.json').read_text())
    assert mismatch['step'] == 12 and mismatch['actual'] == rows[-1]
    assert mismatch['expected'] == expected[12] and 'after_obs' in mismatch['different_fields']


def test_repeat_checks_whole_fresh_trajectory_after_intervention(monkeypatch, tmp_path):
    p = implementation(); install_runtime(monkeypatch, p)
    _, collector, full = run_toy(p, tmp_path, 'collector', 'collector')
    candidate = collector['candidates'][0]
    _, _, alternative = run_toy(p, tmp_path, 'alternative', 'alternative', expected=full, opportunity=candidate)
    wrong = json.loads(json.dumps(alternative)); wrong[70]['after_obs'] = 'changed'
    with pytest.raises(ValueError, match='repeat'):
        run_toy(p, tmp_path, 'repeat', 'repeat', expected=full,
                opportunity=candidate, repeat_expected=wrong)
    evidence = json.loads((tmp_path/'repeat.mismatch.json').read_text())
    assert evidence['step'] == 70


def test_ineffective_first_team_action_requires_identical_continuation(tmp_path):
    p = implementation()
    candidate = dict(step=40, match=0, match_step=40)
    full = [dict(step=s, actions={'player_0': [[0,0,0]], 'player_1': [[0,0,0]]},
                 terminal={'winner':0,'points':[1,0]} if s == 100 else None,
                 point_state=[1,0]) for s in range(101)]
    alt = json.loads(json.dumps(full)); alt[99]['point_state'] = [2,0]
    path = tmp_path/'pair-mismatch.json'
    with pytest.raises(ValueError, match='ineffective'):
        p.make_pair(full, alt, candidate, 'player_0', path)
    assert path.is_file()


def test_technical_admission_rejects_changed_raw_evidence(tmp_path):
    p = implementation()
    counters = {k:0 for k in p.LIMITS}
    counters.update(started_games=4, completed_games=4, started_runs=4, completed_runs=4)
    runs=[]; games=[]; artifacts={}
    for i, (seed,side) in enumerate(p.FIRST):
        game={'key':{'seed':seed,'side':side}, 'passivity':{'full_frames':True}}
        for role in ('reference','collector'):
            path=tmp_path/f'{i}_{role}.gz';path.write_bytes(b'evidence')
            run=dict(role=role,status='complete',seed=seed,side=side,
                     planned_steps=303,attempted_steps=303,steps=303,archived_frames=303,
                     artifacts=p.hashes([path]))
            runs.append(run);artifacts.update(run['artifacts']);game[role]={'artifacts':run['artifacts']}
        path=tmp_path/f'{i}.pairs.gz';path.write_bytes(b'pairs')
        game['pair_artifacts']=p.hashes([path]);artifacts.update(game['pair_artifacts']);games.append(game)
    counters.update(reference_steps=606,instrumented_steps=606,total_steps=1212)
    prior=dict(method=p.METHOD,status='complete',phase='technical',source={'head':'fixed'},
               keys=[list(x) for x in p.FIRST],runs=runs,games=games,counters=counters,
               artifacts=artifacts)
    manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps(prior))
    accepted=tmp_path/'accepted.json';accepted.write_text(json.dumps({'status':'accepted','manifest_sha256':p.digest(manifest)}))
    loaded, inputs=p.load_technical(manifest,accepted,{'head':'fixed'})
    assert loaded == prior and len(inputs) == len(artifacts)+2
    Path = type(tmp_path)
    Path(next(iter(artifacts))).write_bytes(b'tampered')
    with pytest.raises(ValueError, match='artifact'):
        p.load_technical(manifest,accepted,{'head':'fixed'})


def test_execution_totals_count_full_third_match_alternative_and_failed_partial():
    p = implementation()
    runs = [dict(status='complete', planned_steps=303, attempted_steps=303, steps=303, archived_frames=303,
                 role='alternative', ended_episode=True),
            dict(status='complete', planned_steps=101, attempted_steps=101, steps=101, archived_frames=101,
                 role='repeat', ended_episode=False),
            dict(status='failed', planned_steps=303, attempted_steps=176, steps=176, archived_frames=176,
                 role='collector', ended_episode=False)]
    totals = p.execution_totals(runs)
    assert totals['returned_full_length_runs'] == totals['observed_episode_ends'] == 1
    assert totals['completed_short_runs'] == totals['failed_runs'] == 1
    assert totals['attempted_engine_steps'] == totals['returned_engine_steps'] == 580


def test_two_phase_controller_counts_every_fresh_prefix_and_requires_acceptance(monkeypatch, tmp_path):
    from contextlib import nullcontext
    p = implementation(); install_runtime(monkeypatch, p)
    weight=tmp_path/'weights.bin';weight.write_bytes(b'fixed')
    monkeypatch.setattr(p,'V14_SHA',p.digest(weight))
    monkeypatch.setattr(p,'source_identity',lambda *args:{'head':'fixed'})
    monkeypatch.setattr(p,'protected_inputs',lambda *args:[weight])
    monkeypatch.setattr(p,'resource_lock',lambda *args:nullcontext())
    class TestGuard:
        def __init__(self,state):self.state=state
        def __call__(self,*args):self.state['last_usage']={'usedPercent':80}
    monkeypatch.setattr(p,'Guard',TestGuard)
    kwargs=dict(weights=weight,usage_file=tmp_path/'usage',stop_file=tmp_path/'stop',expected_head='fixed')
    technical=p.run_probe(tmp_path/'technical',phase='technical',**kwargs)
    assert technical['counters']['started_runs']==12 and technical['status']=='complete'
    assert technical['execution_totals']['returned_full_length_runs']==6
    with pytest.raises(ValueError,match='acceptance'):
        p.run_probe(tmp_path/'remaining',phase='remaining',**kwargs)
    previous=tmp_path/'technical/manifest.json'
    acceptance=tmp_path/'accepted.json'
    acceptance.write_text(json.dumps({'status':'accepted','manifest_sha256':p.digest(previous)}))
    remaining=p.run_probe(tmp_path/'remaining',phase='remaining',previous=previous,acceptance=acceptance,**kwargs)
    totals=remaining['combined_execution_totals']
    assert totals['entered_runs']==totals['completed_runs']==88
    assert totals['returned_full_length_runs']==totals['observed_episode_ends']==48
    assert totals['completed_short_runs']==40 and totals['failed_runs']==0
    assert totals['attempted_engine_steps']==totals['returned_engine_steps']==20200
    assert sum(g['collector']['verified_map'] for g in technical['games']+remaining['games'])==8
    assert remaining['summary']['cases']==48
    with pytest.raises(ValueError,match='overwrite'):
        p.run_probe(tmp_path/'remaining',phase='remaining',previous=previous,acceptance=acceptance,**kwargs)
