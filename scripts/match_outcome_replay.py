"""Bounded match-outcome repair using fresh original prefixes, never snapshots.

Each alternative/repeat reconstructs both policies from episode start. Every
pre-intervention frame must equal a separately verified complete baseline.
Counters charge attempted engine calls before execution, including failed calls.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import sys
import time

import numpy as np

from scripts.early_curriculum_study import digest, hashes, require, source_identity, resource_lock
from scripts.holder_rollout import exact_digest, module_fingerprint
from scripts.holder_rollout_probe import protected_inputs, write_json, V14_SHA
from scripts.match_outcome_probe import Guard, MAPS, PLANS, ROOT, summarize_pairs
from scripts.match_outcome_rollout import MatchOutcomeAgent, step_frame

METHOD = 'fresh_prefix_v1'
FIRST = ((11011007, 'player_0'), (11011017, 'player_0'))
KEYS = FIRST + tuple((seed, side) for seed in MAPS for side in ('player_0', 'player_1')
                     if (seed, side) not in FIRST)
LIMITS = dict(reference_steps=16*303, instrumented_steps=16*303,
              diagnostic_steps=16*(101+202+303), technical_extra_steps=8*303,
              total_steps=21816, started_games=32, completed_games=32,
              started_alternatives=48, completed_alternatives=48,
              started_repeats=8, completed_repeats=8,
              started_runs=88, completed_runs=88, completed_pairs=48)
ROLE_COUNTERS = dict(reference=('games', 'reference_steps'),
                     collector=('games', 'instrumented_steps'),
                     alternative=('alternatives', 'diagnostic_steps'),
                     repeat=('repeats', 'technical_extra_steps'))


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
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent
    from scripts.par_eval import build_cfg
    import torch

    cls = MatchOutcomeAgent if instrumented else Agent_x
    agent = cls('player_0', agent_path=str(weights), cfg=build_cfg(str(weights), []),
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
        require(0 <= opportunity['match'] <= 2 and 40 <= opportunity['match_step'] <= 70
                and opportunity['step'] == opportunity['match']*101+opportunity['match_step'],
                'Invalid opportunity clock')
    planned = (opportunity['match']+1)*101 if branch else 303
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
                    agent.collect = (role == 'collector' and 40 <= ms <= 70
                                     and step//101 not in agent.used_matches)
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
    require(len(frames) >= 12 and frames[-1]['terminal'] is not None,
            'Missing terminal branch')
    outcome = frames[-1]['terminal']
    return dict(frames=frames, outcome=outcome, h12_points=frames[11]['point_state'],
                won=int(outcome['winner'] == team),
                point_margin=int(outcome['points'][team]-outcome['points'][1-team]),
                sha256=exact_digest(frames))


def make_pair(baseline_frames, alternative_frames, opportunity, side, mismatch_path):
    start, end = opportunity['step'], (opportunity['match']+1)*101
    require(len(alternative_frames) == end and len(baseline_frames) >= end, 'Incomplete pair trajectories')
    baseline = branch_result(baseline_frames[start:end], side)
    alternative = branch_result(alternative_frames[start:end], side)
    other = f'player_{1-int(side[-1])}'
    equal_or_evidence(baseline['frames'][0]['actions'][other],
                      alternative['frames'][0]['actions'][other], mismatch_path,
                      'opponent initial action', start)
    effective = baseline['frames'][0]['actions'] != alternative['frames'][0]['actions']
    if not effective:
        equal_or_evidence(baseline, alternative, mismatch_path, 'ineffective continuation', start)
    team, other = int(side[-1]), 1-int(side[-1])
    return dict(candidate=opportunity, baseline=baseline, alternative=alternative,
                effective=effective, delta_win=alternative['won']-baseline['won'],
                delta_points=alternative['point_margin']-baseline['point_margin'],
                delta_h12=(alternative['h12_points'][team]-alternative['h12_points'][other]
                           -baseline['h12_points'][team]+baseline['h12_points'][other]),
                live_verified=True, prefix_verified=True, reverse_repeat=None)


def all_artifacts(state):
    result = {}
    for run in state['runs']:
        result.update(run.get('artifacts', {}))
    for game in state['games']:
        result.update(game.get('pair_artifacts', {}))
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
            require(run['steps'] == run['attempted_steps'] == run['archived_frames'] == run['planned_steps'],
                    'Completed run is partial')
            derived['completed_'+family] += 1
            derived['completed_runs'] += 1
        elif complete:
            raise ValueError('Incomplete entered run')
    derived['completed_pairs'] = sum(len(game.get('collector', {}).get('pairs', [])) for game in state['games'])
    require(derived == state['counters'], 'Execution ledger/counters differ')


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
    require(all_artifacts(prior) == prior['artifacts'] and prior['artifacts'],
            'Technical artifact inventory incomplete')
    inputs = [previous, acceptance]
    for filename, expected in prior['artifacts'].items():
        path = Path(filename)
        require(path.resolve().is_relative_to(previous.parent.resolve()) and path.is_file()
                and digest(path) == expected, 'Technical artifact altered or missing')
        inputs.append(path)
    return prior, inputs


def run_probe(out, *, phase, weights, usage_file, stop_file, expected_head, previous=None, acceptance=None):
    out, weights = Path(out).absolute(), Path(weights).absolute()
    require(not out.exists(), 'No resume or overwrite')
    selected = phase_keys(phase)
    source = source_identity(ROOT, sys.executable, PLANS)
    require(source['head'] == expected_head, 'Wrong HEAD')
    require(digest(weights) == V14_SHA, 'Only frozen V14 supported')
    inputs, prior = [weights], None
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
                 prior_counters=prior_counts, runs=[], games=[], artifacts={})
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
                   planned_steps=(opportunity['match']+1)*101 if opportunity else 303,
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
                                     'effective', 'delta_win', 'delta_points', 'delta_h12', 'reverse_repeat',
                                     'live_verified', 'prefix_verified')}
                            brief.update(baseline_outcome=pair['baseline']['outcome'],
                                         alternative_outcome=pair['alternative']['outcome'])
                            bump(state['counters'], prior_counts, 'completed_pairs')
                            collector['pairs'].append(brief)
                            save()
                finally:
                    game.setdefault('pair_artifacts', {}).update(hashes([pairs_path]) if pairs_path.is_file() else {})
                    save()
            guard(True)
            verify_ledger(state)
        all_games = (prior['games'] if prior else []) + state['games']
        state['summary'] = summarize_pairs([row for game in all_games for row in game['collector']['pairs']])
        state.update(status='complete', finished_at=time.time())
        save()
    except BaseException as exc:
        state.update(status='failed', error=f'{type(exc).__name__}: {exc}', finished_at=time.time())
        save()
        raise
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
    return state


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
