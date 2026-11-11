"""Bounded holder-SAP causality with fresh full-game prefixes, never snapshots.

Each alternative/repeat reconstructs both policies from episode start. Every
pre-intervention frame must equal a separately verified complete baseline.
Counters charge attempted engine calls before execution, including failed calls.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import time

import numpy as np

from scripts.early_curriculum_study import digest, hashes, require, source_identity, resource_lock
from scripts.holder_rollout import exact_digest, module_fingerprint
from scripts.holder_rollout_probe import protected_inputs, foreign_processes, write_json, V14_SHA
from scripts.match_outcome_rollout import step_frame as terminal_step_frame
from scripts.targeting_probe import _json
from scripts.ensemble_diversity_eval_supervisor import check_usage
from scripts.final_training_supervisor import read_power

ROOT = Path(__file__).resolve().parents[1]
PLANS = [ROOT/'docs/superpowers/specs/2026-11-11-holder-sap-causality-design.md',
         ROOT/'docs/superpowers/plans/2026-11-11-holder-sap-causality.md']
MAPS = (9946007, 2000000, 2000001, 2000009, 2000029, 2000035, 2000045, 2000055)
ARCHIVE = ROOT/'experiments/analysis/holder_sap_causality_20261111/reference_source.zip'
HISTORY = ROOT/'experiments/analysis/holder_oscillation_20261109/probe_v1/manifest.json'
TRACE = HISTORY.parent/'9946007_player_0.jsonl.gz'
SOURCE_CSV = ROOT/'experiments/analysis/replacement_validation_20261108/validation/V14_panel_0.csv'
SOURCE_CSV_SHA = '7f95a56e970230968d7d6f661eff814bc7a2b4b0108d8a2699978e7673359aa6'
TRACE_SHA = '2c577ce5898f7463971cefa15b5996c2331e7f5c94b0d6d68493025c86e42db2'
SOURCE_COMMIT = '021d13e1a7808d67bf8a11c78fbc4beaae3c9956'

METHOD = 'holder_sap_fullgame_prefix_v1'
FIRST = ((9946007, 'player_0'), (2000000, 'player_0'))
KEYS = FIRST + tuple((seed, side) for seed in MAPS for side in ('player_0', 'player_1')
                     if (seed, side) not in FIRST)
LIMITS = dict(reference_steps=16*303, instrumented_steps=16*303,
              diagnostic_steps=48*303, technical_extra_steps=8*303,
              total_steps=26664, started_games=32, completed_games=32,
              started_alternatives=48, completed_alternatives=48,
              started_repeats=8, completed_repeats=8,
              started_runs=88, completed_runs=88, completed_pairs=48)
ROLE_COUNTERS = dict(reference=('games', 'reference_steps'),
                     collector=('games', 'instrumented_steps'),
                     alternative=('alternatives', 'diagnostic_steps'),
                     repeat=('repeats', 'technical_extra_steps'))


class Guard:
    """Own source identity and one-worker guard; no globals of old studies change."""
    def __init__(self, state):
        self.state, self.last_check = state, 0.

    def __call__(self, force=False):
        state, now = self.state, time.time()
        require(not Path(state['stop_file']).exists(), 'STOP requested')
        if not force and now-self.last_check < 10:
            return
        usage = check_usage(state['usage_file'], now=now, max_used_percent=95)
        require(source_identity(ROOT, sys.executable, PLANS) == state['source'], 'Frozen source changed')
        require(hashes(state['inputs']) == state['inputs'] and hashes(state['protected']) == state['protected'],
                'Input/protected file changed')
        require(hashes(state['artifacts']) == state['artifacts'], 'Archived evidence changed')
        snapshot = subprocess.check_output(['ps', '-axo', 'pid=,pgid=,args='], text=True, timeout=5)
        others = foreign_processes(snapshot, owner=os.getpid())
        for line in snapshot.splitlines():
            fields = line.strip().split(None, 2)
            if len(fields) == 3 and int(fields[0]) != os.getpid():
                command = fields[2]
                if 'python' in Path(command.split()[0]).name.lower() and ('scripts.holder_sap_replay' in command or 'scripts/holder_sap_replay.py' in command):
                    others.append(int(fields[0]))
        require(not others, 'Other model/test process active')
        power = read_power()
        require(type(power['ac']) is bool and type(power['percent']) is int, 'Unknown power state')
        # Battery operation was explicitly authorized and supervised by the user.
        state.update(last_guard_at=now, last_usage=usage, last_power=power)
        self.last_check = now


def admitted_inputs():
    """Pin original package, source CSV, and the only existing exact action trace."""
    from scripts.holder_sap_probe import load_reference_class
    require(digest(SOURCE_CSV) == SOURCE_CSV_SHA, 'Original source CSV changed')
    require(digest(TRACE) == TRACE_SHA, 'Original trace changed')
    archive_manifest = ARCHIVE.with_suffix('.json')
    require(json.loads(archive_manifest.read_text())['source_commit'] == SOURCE_COMMIT,
            'Wrong original reference source')
    load_reference_class()  # Validates the zip and every member, with no model load.
    history = json.loads(HISTORY.read_text())
    require(history['status'] == 'complete' and history['games'][0]['complete'], 'Incomplete historical trace')
    require(all(history['games'][0]['passivity'].values()), 'Historical trace not passive')
    return [ARCHIVE, archive_manifest, SOURCE_CSV, HISTORY, TRACE]


def verify_historical(seed, side, result, frames, out):
    path = Path(out)/f'{seed}_{side}.historical-mismatch.json'
    if (seed, side) == FIRST[0]:
        with gzip.open(TRACE, 'rt', encoding='utf-8') as stream:
            trace = [json.loads(line) for line in stream]
        require(len(trace) == 303, 'Historical action trace incomplete')
        for step, (old, actual) in enumerate(zip(trace, frames)):
            require(old['key']['obs_step'] == step, 'Historical trace step differs')
            equal_or_evidence(old['native_actions'], actual['actions'][side], path,
                              'historical native action', step)
        historical = json.loads(HISTORY.read_text())['games'][0]['unobserved']
        expected = [historical['our_wins'], historical['opp_wins']]
        equal_or_evidence(expected, result['wins'], path, 'historical match wins')
        equal_or_evidence([historical['our_points'], historical['opp_points']], result['points'],
                          path, 'historical points')
        return dict(native_action_frames=303, match_wins=True, points=True,
                    full_state_parity_available=False)
    if seed != 9946007:
        with SOURCE_CSV.open(newline='') as stream:
            rows = [r for r in csv.DictReader(stream) if int(r['seed']) == seed and r['side'] == side]
        require(len(rows) == 1 and rows[0]['opponent'] == 'solution92', 'Historical CSV key missing/duplicated')
        row, team = rows[0], int(side[-1])
        equal_or_evidence([int(row['our_wins']), int(row['opp_wins'])],
                          [result['wins'][team], result['wins'][1-team]], path, 'historical match wins')
        equal_or_evidence([int(row['our_points']), int(row['opp_points'])],
                          [result['points'][team], result['points'][1-team]], path, 'historical points')
        return dict(match_wins=True, points=True, full_state_parity_available=False)
    return dict(historical_reference_available=False)


def step_frame(env, agent, opponent, obs, side, step, **kwargs):
    """Archive public data separately from external engine hashes/end labels."""
    public = _json(obs[side])
    def public_value(value):
        return _json(sorted(value) if isinstance(value, (set, frozenset)) else value)
    belief = {name: public_value(getattr(agent.belief, name)) for name in
              ('point_tiles', 'candidate', 'dead_tiles', 'explored') if hasattr(agent.belief, name)}
    bookkeeping = {name: public_value(getattr(agent, name)) for name in
                   ('_prev_actions', '_sap_hits', '_sap_unknown', '_pred_pending') if hasattr(agent, name)}
    estimates = {name: public_value(getattr(agent.param_est, name)) for name in
                 ('log_drop', 'log_neb', 'n_drop', 'n_neb')}
    following, frame = terminal_step_frame(env, agent, opponent, obs, side, step, **kwargs)
    frame.update(public_observation=public, own_belief=belief, own_bookkeeping=bookkeeping,
                 public_parameter_estimates=estimates)
    del frame['sha256']
    frame['sha256'] = exact_digest(frame)
    return following, frame


def phase_keys(phase):
    require(phase in ('technical', 'remaining'), 'Unknown phase')
    return list(KEYS[:2] if phase == 'technical' else KEYS[2:])


def bump(counters, prior, *names):
    """Reserve all counters atomically before entering a run/engine call."""
    require(all(counters[name] + prior[name] < LIMITS[name] for name in names),
            'Fixed execution limit exceeded')
    for name in names:
        counters[name] += 1


def append(stream, row):
    stream.write(json.dumps(row, allow_nan=False, separators=(',', ':')) + '\n')
    stream.flush()


def equal_or_evidence(expected, actual, path, kind, step=None):
    if expected == actual:
        return
    fields = ([key for key in sorted(set(expected) | set(actual))
               if expected.get(key) != actual.get(key)]
              if isinstance(expected, dict) and isinstance(actual, dict) else None)
    write_json(Path(path), dict(kind=kind, step=step, different_fields=fields,
                               expected=expected, actual=actual))
    raise ValueError(f'{kind} mismatch; actual evidence saved')


def make_runtime(seed, side, weights, instrumented):
    """Fresh policies and engine, with the original reviewed initialization."""
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.holder_sap_probe import HolderSapProbeAgent, load_reference_class
    from scripts.common import make_opponent
    from scripts.par_eval import build_cfg
    import torch

    reference_cls = load_reference_class()
    cls = HolderSapProbeAgent if instrumented else reference_cls
    cfg = build_cfg(str(weights), []) if instrumented else reference_cls._cfg_from_checkpoint(str(weights))
    require(cfg is not None and not cfg.smart_sap, 'Original non-smart-SAP config required')
    require(asdict(cfg) == json.loads(HISTORY.read_text())['games'][0]['unobserved']['config'],
            'Historical/current config differs; reconcile before admission')
    agent = cls('player_0', agent_path=str(weights), cfg=cfg,
                train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    for net in [agent.q, agent.target_q, *agent.extra_q]:
        net.eval().requires_grad_(False)
    frozen = module_fingerprint(agent)
    opponent = make_opponent('solution92', f'player_{1-int(side[-1])}')
    agent.new_game(side)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        obs, info = env.reset(seed=seed)
        require(int(info['params']['max_steps_in_match']) == 100
                and int(info['params']['match_count_per_episode']) == 3,
                'Unexpected match/game length')
        agent.set_env_cfg(info['params'])
        opponent.set_env_cfg(info['params'])
        return env, agent, opponent, obs, frozen
    except BaseException:
        env.close()
        raise


def play_run(seed, side, weights, *, role, out, name, entry, guard, on_attempt, save,
             expected=None, opportunity=None, repeat_expected=None):
    """One fresh entered run; writes the actual frame before every comparison."""
    require(role in ROLE_COUNTERS, 'Unknown execution role')
    branch = role in ('alternative', 'repeat')
    require(branch == (opportunity is not None), 'Intervention/role mismatch')
    if branch:
        require(expected is not None, 'Branch needs verified full baseline')
        require(0 <= opportunity['match'] <= 2 and 1 <= opportunity['match_step'] <= 100
                and opportunity['step'] == opportunity['match']*101+opportunity['match_step'],
                'Invalid opportunity clock')
    planned = 303
    require(entry['planned_steps'] == planned, 'Run length does not match role')
    require(role != 'repeat' or repeat_expected is not None, 'Repeat needs entire original trajectory')
    frame_path = Path(out)/(name+'.frames.jsonl.gz')
    mismatch_path = Path(out)/(name+'.mismatch.json')
    entry.update(frame_path=str(frame_path), mismatch_path=str(mismatch_path),
                 planned_full_game=planned == 303, ended_episode=False)
    frames, candidates, matches = [], [], []
    env = None
    try:
        env, agent, opponent, obs, frozen = make_runtime(seed, side, weights, role != 'reference')
        if role != 'reference':
            agent.collect = False
            agent.intervention = opportunity
            agent.intervention_hits = 0
        other = f'player_{1-int(side[-1])}'
        with gzip.open(frame_path, 'xt', encoding='utf-8') as stream:
            for step in range(planned):
                guard()
                ms = int(np.asarray(obs[side]['match_steps']))
                require(ms == step % 101, 'Unexpected match clock')
                if role != 'reference':
                    agent.collect = role == 'collector' and step//101 not in agent.used_matches
                before = exact_digest(env.state), exact_digest(obs)
                actions = {side: agent.act(step, obs[side]), other: opponent.act(step, obs[other])}
                require(not agent.caught_errors and not getattr(opponent, 'caught_errors', 0),
                        'Caught policy error')
                if role == 'collector' and agent.candidate is not None:
                    candidates.append(agent.candidate)
                on_attempt()
                entry['attempted_steps'] += 1
                def completed_step():
                    entry['steps'] += 1
                following, frame = step_frame(env, agent, opponent, obs, side, step,
                                              actions=actions, before=before,
                                              on_env_step=completed_step)
                append(stream, frame)
                frames.append(frame)
                entry['archived_frames'] += 1
                entry['ended_episode'] = bool(frame['done'])
                if entry['steps'] % 50 == 0:
                    save()
                if expected is not None and (not branch or step < opportunity['step']):
                    equal_or_evidence(expected[step], frame, mismatch_path,
                                      'prefix' if branch else 'full baseline', step)
                if repeat_expected is not None:
                    equal_or_evidence(repeat_expected[step], frame, mismatch_path, 'repeat', step)
                if frame['terminal'] is not None:
                    matches.append(frame['terminal'])
                require(bool(frame['terminal']) == (step % 101 == 100), 'Unexpected match boundary')
                require(frame['done'] == (step == 302), 'Unexpected episode ending')
                obs = following
        require(frames[-1]['terminal'] is not None and len(matches) == planned//101,
                'Incomplete current match')
        if role != 'reference':
            require(agent.intervention_hits == int(branch), 'Intervention did not execute exactly once')
        require(len(candidates) <= 3 and len({c['match'] for c in candidates}) == len(candidates),
                'Repeated match opportunity')
        equal_or_evidence(frozen, module_fingerprint(agent), mismatch_path, 'frozen modules')
        result = dict(seed=seed, side=side, role=role, steps=len(frames), resets=planned//101,
                      planned_steps=planned, full_game=planned == 303, matches=matches,
                      wins=matches[-1]['wins'],
                      points=[sum(f['points'][team] for f in frames) for team in (0, 1)],
                      trajectory_sha256=hashlib.sha256(b''.join(bytes.fromhex(f['sha256']) for f in frames)).hexdigest(),
                      candidates=candidates, artifacts=hashes([frame_path]))
        return result, frames
    finally:
        if env is not None:
            env.close()
        entry['artifacts'] = hashes([path for path in (frame_path, mismatch_path) if path.is_file()])


def branch_result(frames, side):
    team = int(side[-1])
    require(len(frames) == 303 and frames[-1]['done'], 'Incomplete full-game trajectory')
    matches = [f['terminal'] for f in frames if f['terminal'] is not None]
    require(len(matches) == 3 and sum(matches[-1]['wins']) == 3, 'Missing actual three-match results')
    wins = matches[-1]['wins']
    points = [sum(f['points'][t] for f in frames) for t in (0, 1)]
    return dict(frames=frames, matches=matches, wins=wins, points=points,
                won=int(wins[team] > wins[1-team]), match_wins=int(wins[team]),
                point_margin=int(points[team]-points[1-team]), sha256=exact_digest(frames))


def make_pair(baseline_frames, alternative_frames, opportunity, side, mismatch_path):
    baseline, alternative = (branch_result(f, side) for f in (baseline_frames, alternative_frames))
    start, match, uid = opportunity['step'], opportunity['match'], opportunity['uid']
    other = f'player_{1-int(side[-1])}'
    equal_or_evidence(baseline_frames[start]['actions'][other], alternative_frames[start]['actions'][other],
                      mismatch_path, 'opponent initial action', start)
    original, changed = baseline_frames[start]['actions'][side][uid], alternative_frames[start]['actions'][side][uid]
    require(original[0] == 5 and changed == [0, 0, 0], 'Intervention must be precisely SAP to STAY')
    # Later units may legitimately change once the cancelled shot no longer
    # reserves damage. Earlier units must retain the original emitted actions.
    equal_or_evidence(baseline_frames[start]['actions'][side][:uid],
                      alternative_frames[start]['actions'][side][:uid], mismatch_path,
                      'earlier unit actions', start)
    effective = original != changed
    if not effective:
        equal_or_evidence(baseline, alternative, mismatch_path, 'ineffective continuation', start)
    team = int(side[-1])
    return dict(candidate=opportunity, baseline=baseline, alternative=alternative, effective=effective,
                baseline_game_won=baseline['won'], alternative_game_won=alternative['won'],
                delta_game_win=alternative['won']-baseline['won'],
                delta_current_match_win=int(alternative['matches'][match]['winner'] == team)
                                        -int(baseline['matches'][match]['winner'] == team),
                delta_match_wins=alternative['match_wins']-baseline['match_wins'],
                delta_points=alternative['point_margin']-baseline['point_margin'],
                live_verified=True, prefix_verified=True, reverse_repeat=None)


def summarize(pairs, executions):
    keys = [(p['seed'], p['side'], p['candidate']['match']) for p in pairs]
    require(len(keys) == len(set(keys)) and len(pairs) <= 48, 'Duplicate/excess opportunity')
    require(all(p['delta_game_win'] == p['alternative_game_won']-p['baseline_game_won']
                and p['delta_game_win'] in (-1, 0, 1) and p['delta_current_match_win'] in (-1, 0, 1)
                and -3 <= p['delta_match_wins'] <= 3 for p in pairs), 'Invalid pair labels')
    effective = [p for p in pairs if p['effective']]
    positive = [p for p in pairs if p['delta_game_win'] > 0]
    negative = [p for p in pairs if p['delta_game_win'] < 0]
    maps, rescued_maps = len({p['seed'] for p in effective}), len({p['seed'] for p in positive})
    technical = bool(executions) and all(r['status'] == 'complete' and r['ended_episode']
        and r['steps'] == r['attempted_steps'] == r['archived_frames'] == r['planned_steps'] == 303
        for r in executions) and all(p['live_verified'] and p['prefix_verified'] for p in pairs)
    influence = len(effective) >= 12 and maps >= 4
    match_delta = sum(p['delta_match_wins'] for p in pairs)
    label = len(positive) >= 2 and rescued_maps >= 2 and len(positive) > len(negative) and match_delta >= 0
    return dict(cases=len(pairs), effective_pairs=len(effective), effective_maps=maps,
                positive_game_flips=len(positive), negative_game_flips=len(negative),
                zero_game_flips=len(pairs)-len(positive)-len(negative), rescued_maps=rescued_maps,
                delta_match_wins_sum=match_delta, delta_points_sum=sum(p['delta_points'] for p in pairs),
                positive_current_match_flips=sum(p['delta_current_match_win'] > 0 for p in pairs),
                negative_current_match_flips=sum(p['delta_current_match_win'] < 0 for p in pairs),
                technical_gate=technical, influence_gate=influence, label_gate=label,
                passed=technical and influence and label)


def all_artifacts(state):
    result = {}
    for run in state['runs']:
        result.update(run.get('artifacts', {}))
    for game in state['games']:
        result.update(game.get('pair_artifacts', {}))
        result.update(game.get('historical_artifacts', {}))
    return result


def execution_totals(runs):
    """Physical lengths, separate from the reference/collector game-role cap."""
    return dict(entered_runs=len(runs),
                completed_runs=sum(run['status'] == 'complete' for run in runs),
                failed_runs=sum(run['status'] == 'failed' for run in runs),
                entered_planned_full_length_runs=sum(run['planned_steps'] == 303 for run in runs),
                returned_full_length_runs=sum(run['steps'] == 303 for run in runs),
                observed_episode_ends=sum(bool(run.get('ended_episode')) for run in runs),
                completed_short_runs=sum(run['status'] == 'complete' and run['steps'] < 303 for run in runs),
                incomplete_runs=sum(run['status'] != 'complete' for run in runs),
                attempted_engine_steps=sum(run['attempted_steps'] for run in runs),
                returned_engine_steps=sum(run['steps'] for run in runs),
                archived_frames=sum(run['archived_frames'] for run in runs))


def verify_ledger(state, complete=True):
    derived = {key: 0 for key in LIMITS}
    for run in state['runs']:
        family, counter = ROLE_COUNTERS[run['role']]
        derived['started_'+family] += 1
        derived['started_runs'] += 1
        derived[counter] += run['attempted_steps']
        derived['total_steps'] += run['attempted_steps']
        require(0 <= run['archived_frames'] <= run['steps'] <= run['attempted_steps'] <= run['planned_steps'],
                'Invalid actual/partial execution lengths')
        if run['status'] == 'complete':
            require(run['ended_episode'] and run['steps'] == run['attempted_steps'] == run['archived_frames'] == run['planned_steps'] == 303,
                    'Completed run is partial')
            derived['completed_'+family] += 1
            derived['completed_runs'] += 1
        elif complete:
            raise ValueError('Incomplete entered run')
    derived['completed_pairs'] = sum(len(game.get('collector', {}).get('pairs', [])) for game in state['games'])
    require(derived == state['counters'], 'Execution ledger/counters differ')
    prior = state.get('prior_counters', {key: 0 for key in LIMITS})
    require(all(0 <= derived[key] + prior[key] <= LIMITS[key] for key in LIMITS), 'Execution limit exceeded')


def load_technical(previous, acceptance, source):
    previous, acceptance = Path(previous), Path(acceptance)
    prior = json.loads(previous.read_text())
    accepted = json.loads(acceptance.read_text())
    require(prior.get('method') == METHOD and prior['status'] == 'complete'
            and prior['phase'] == 'technical', 'Incomplete/wrong repaired technical phase')
    require(prior['source'] == source and prior['keys'] == [list(k) for k in FIRST],
            'Technical source/keys differ')
    require([(g['key']['seed'], g['key']['side']) for g in prior['games']] == list(FIRST),
            'Technical actual keys differ')
    require(prior['counters']['started_games'] == prior['counters']['completed_games'] == 4,
            'Four complete baseline executions required')
    require(accepted['status'] == 'accepted' and accepted['manifest_sha256'] == digest(previous),
            'Unbound actual technical acceptance')
    verify_ledger(prior)
    require(all(g['passivity'] and all(g['passivity'].values()) for g in prior['games']),
            'Technical full passivity absent')
    require(hashes(prior['inputs']) == prior['inputs'] and hashes(prior['protected']) == prior['protected'],
            'Technical input/protected file changed')
    require(all_artifacts(prior) == prior['artifacts'] and prior['artifacts'],
            'Technical artifact inventory incomplete')
    inputs = [previous, acceptance, *map(Path, prior['inputs'])]
    for filename, expected in prior['artifacts'].items():
        path = Path(filename)
        require(path.resolve().is_relative_to(previous.parent.resolve()) and path.is_file()
                and digest(path) == expected, 'Technical artifact altered or missing')
        inputs.append(path)
    return prior, inputs


def run_probe(out, *, phase, weights, usage_file, stop_file, expected_head, previous=None, acceptance=None):
    out, weights = Path(out).absolute(), Path(weights).absolute()
    require(not out.exists(), 'No resume or overwrite')
    require(not any(path.is_symlink() for path in (out, *out.parents)), 'Symlink output path')
    selected = phase_keys(phase)
    source = source_identity(ROOT, sys.executable, PLANS)
    require(source['head'] == expected_head, 'Wrong HEAD')
    require(digest(weights) == V14_SHA, 'Only frozen V14 supported')
    inputs, prior = [weights, *admitted_inputs()], None
    if phase == 'remaining':
        require(previous is not None and acceptance is not None, 'Explicit actual technical acceptance required')
        prior, prior_inputs = load_technical(previous, acceptance, source)
        inputs.extend(prior_inputs)
    prior_counts = prior['counters'] if prior else {key: 0 for key in LIMITS}
    state = dict(schema_version=2, method=METHOD, phase=phase, status='running',
                 pid=os.getpid(), started_at=time.time(), source=source,
                 inputs=hashes(inputs), protected=hashes(protected_inputs(ROOT)),
                 usage_file=str(Path(usage_file).absolute()), stop_file=str(Path(stop_file).absolute()),
                 keys=selected, limits=LIMITS, counters={key: 0 for key in LIMITS},
                 counter_semantics='Step counters include every fresh prefix and reserve each engine-call attempt before execution; runs additionally report returned steps and archived frames.',
                 prior_counters=prior_counts, runs=[], games=[], artifacts={},
                 limitations=['Terminal engine energies are recorded. Intermediate energy phases are not instrumented; no separation of SAP cost, enemy damage, nebula, and other causes is claimed.',
                              'Known diagnostic cards and multiple alternative worlds are not a policy win-rate sample.'])
    guard = Guard(state)
    guard(True)
    require(state['last_usage']['usedPercent'] < 92, 'No new phase above closure threshold')
    out.mkdir(parents=True, exist_ok=False)
    manifest = out/'manifest.json'
    def save():
        state['artifacts'] = all_artifacts(state)
        state['execution_totals'] = execution_totals(state['runs'])
        state['combined_execution_totals'] = execution_totals((prior['runs'] if prior else []) + state['runs'])
        write_json(manifest, state)
    def stop(*_):
        raise KeyboardInterrupt('Termination requested')
    previous_handler = signal.signal(signal.SIGTERM, stop)
    verified_maps = {g['key']['seed'] for g in prior['games'] if g['collector']['verified_map']} if prior else set()

    def execute(seed, side, role, *, expected=None, opportunity=None, repeat_expected=None):
        guard(True)
        family, step_counter = ROLE_COUNTERS[role]
        bump(state['counters'], prior_counts, 'started_runs', 'started_'+family)
        name = f'{seed}_{side}_{role}' + (f'_m{opportunity["match"]}' if opportunity is not None else '')
        run = dict(name=name, seed=seed, side=side, role=role, status='entered', started_at=time.time(),
                   planned_steps=303,
                   attempted_steps=0, steps=0, archived_frames=0)
        state['runs'].append(run)
        save()
        try:
            result, frames = play_run(seed, side, weights, role=role, out=out, name=name,
                entry=run, guard=guard,
                on_attempt=lambda: bump(state['counters'], prior_counts, 'total_steps', step_counter),
                save=save, expected=expected, opportunity=opportunity, repeat_expected=repeat_expected)
            bump(state['counters'], prior_counts, 'completed_runs', 'completed_'+family)
            run.update(status='complete', finished_at=time.time())
            save()
            return result, frames
        except BaseException as exc:
            run.update(status='failed', error=f'{type(exc).__name__}: {exc}', finished_at=time.time())
            save()
            raise

    save()
    try:
        from scripts.experiment import limit_threads
        limit_threads()
        with resource_lock(ROOT):
            for seed, side in selected:
                game = dict(key=dict(seed=seed, side=side))
                state['games'].append(game)
                reference, reference_frames = execute(seed, side, 'reference')
                game['reference'] = reference
                try:
                    game['historical'] = verify_historical(seed, side, reference, reference_frames, out)
                finally:
                    mismatch = out/f'{seed}_{side}.historical-mismatch.json'
                    if mismatch.is_file():
                        game['historical_artifacts'] = hashes([mismatch])
                    save()
                collector, baseline_frames = execute(seed, side, 'collector', expected=reference_frames)
                collector.update(pairs=[], verified_map=False)
                game['collector'] = collector
                game['passivity'] = dict(full_frames=True)
                pairs_path = out/f'{seed}_{side}_collector.pairs.jsonl.gz'
                try:
                    with gzip.open(pairs_path, 'xt', encoding='utf-8') as stream:
                        for index, candidate in enumerate(collector['candidates']):
                            alternative, alt_frames = execute(seed, side, 'alternative',
                                                              expected=baseline_frames, opportunity=candidate)
                            mismatch_path = out/f'{seed}_{side}_m{candidate["match"]}.pair-mismatch.json'
                            try:
                                pair = make_pair(baseline_frames, alt_frames, candidate, side, mismatch_path)
                            finally:
                                if mismatch_path.is_file():
                                    game.setdefault('pair_artifacts', {}).update(hashes([mismatch_path]))
                            pair.update(seed=seed, side=side, pair_id=index, status='live_verified',
                                        alternative_run=alternative['artifacts'])
                            if seed not in verified_maps:
                                repeat, _ = execute(seed, side, 'repeat', expected=baseline_frames,
                                                    opportunity=candidate, repeat_expected=alt_frames)
                                pair['reverse_repeat'] = dict(alternative_repeat=True, fresh_prefix_repeat=True)
                                pair['repeat_run'] = repeat['artifacts']
                                verified_maps.add(seed)
                                collector['verified_map'] = True
                            append(stream, pair)
                            brief = {key: pair[key] for key in ('seed', 'side', 'pair_id', 'candidate',
                                     'effective', 'delta_game_win', 'delta_current_match_win', 'delta_match_wins',
                                     'delta_points', 'baseline_game_won', 'alternative_game_won', 'reverse_repeat',
                                     'live_verified', 'prefix_verified')}
                            brief.update(baseline_outcome=pair['baseline']['matches'],
                                         alternative_outcome=pair['alternative']['matches'])
                            bump(state['counters'], prior_counts, 'completed_pairs')
                            collector['pairs'].append(brief)
                            save()
                finally:
                    game.setdefault('pair_artifacts', {}).update(hashes([pairs_path]) if pairs_path.is_file() else {})
                    save()
            guard(True)
            verify_ledger(state)
        all_games = (prior['games'] if prior else []) + state['games']
        state['summary'] = summarize([row for game in all_games for row in game['collector']['pairs']],
                                     (prior['runs'] if prior else []) + state['runs'])
        state.update(status='complete', finished_at=time.time())
        save()
    except BaseException as exc:
        state.update(status='failed', error=f'{type(exc).__name__}: {exc}', finished_at=time.time())
        save()
        raise
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
    return state


def run_phase(phase, output, weights, quota_receipt, previous_acceptance=None):
    """Run the fixed phase and return its manifest; acceptance binds its sibling manifest."""
    acceptance = Path(previous_acceptance).absolute() if previous_acceptance is not None else None
    previous = None
    if acceptance is not None:
        document = json.loads(acceptance.read_text())
        previous = Path(document.get('manifest', acceptance.parent/'manifest.json')).absolute()
    run_probe(output, phase=phase, weights=weights, usage_file=quota_receipt,
              stop_file=ROOT/'experiments/analysis/holder_sap_causality_20261111/STOP',
              expected_head=source_identity(ROOT, sys.executable, PLANS)['head'],
              previous=previous, acceptance=acceptance)
    return Path(output).absolute()/'manifest.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('out', 'weights', 'usage-file', 'stop-file'):
        parser.add_argument('--'+key, type=Path, required=True)
    parser.add_argument('--phase', choices=('technical', 'remaining'), required=True)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--acceptance', type=Path)
    run_probe(**vars(parser.parse_args()))


if __name__ == '__main__':
    main()
