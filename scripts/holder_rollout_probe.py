"""Bounded HOLD influence diagnostic on twelve preselected historical games.

No training, promotion, resume, overwrite, or fresh performance evaluation.
Run as python -m scripts.holder_rollout_probe; --technical-smoke selects two
fixed known games, with one pair each, in a separate exclusive output folder.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import time

import numpy as np

from scripts.early_curriculum_study import digest, hashes, require, source_identity, resource_lock
from scripts.ensemble_diversity_eval_supervisor import check_usage
from scripts.final_training_supervisor import read_power

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / 'experiments/analysis/continuation_20261102/targeting/manifest.json'
SMOKE_KEYS = ((831006, 'player_1'), (831043, 'player_0'))
PLANS = [ROOT / 'docs/superpowers/specs/2026-11-08-decision-learning.md',
         ROOT / 'docs/superpowers/plans/2026-11-08-holder-rollout-probe.md']
V14_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
ZIP_SHA = '88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6'


def protected_inputs(root):
    root = Path(root)
    weights = [root / 'agents/sherlock/weights/agent_p0.pth',
               root / 'agents/sherlock/weights/agent_p1.pth']
    archive = root / 'Gruppe15.zip'
    require(all(p.is_file() for p in [*weights, archive]), 'Protected V14/ZIP missing')
    require(all(digest(p) == V14_SHA for p in weights) and digest(archive) == ZIP_SHA,
            'Protected V14/ZIP differs from the released submission')
    return [*weights, archive]


def validate_keys(path):
    document = json.loads(Path(path).read_text())
    source = ROOT / document['source']
    require(source.resolve() == HISTORICAL.resolve() and digest(source) == document['source_sha256'],
            'Keys must bind the original targeting manifest')
    historic = json.loads(source.read_text())
    keys = document['keys']
    project = lambda rows: [(k['seed'], k['side'], k['group']) for k in rows]
    require(len(keys) == 12 and project(keys) == project(historic['keys']),
            'Exactly the twelve historical keys in original order are required')
    require(len(set((k['seed'], k['side']) for k in keys)) == 12 and all(
        type(k['seed']) is int and k['side'] in ('player_0', 'player_1') and
        k.get('opponent', 'solution92') == 'solution92' for k in keys), 'Invalid historical keys')
    return keys, source


def foreign_processes(snapshot, *, owner):
    from scripts.final_training_supervisor import foreign_jobs
    jobs = set(foreign_jobs(snapshot, owner_pid=owner, owned_pgids=set()))
    for line in snapshot.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) != 3: continue
        pid, _, command = fields
        if int(pid) == owner: continue
        executable = Path(command.split()[0]).name.lower()
        module = re.search(r'(?:-m\s+scripts\.|scripts/)([A-Za-z0-9_]+)', command)
        if 'python' in executable and module and any(word in module[1] for word in (
                'train', 'eval', 'study', 'supervisor', 'probe', 'distill', 'experiment')):
            jobs.add(int(pid))
    return sorted(jobs)


class Guard:
    def __init__(self, state):
        self.state, self.last_check = state, 0.

    def __call__(self, *, force=False):
        s = self.state
        require(not Path(s['stop_file']).exists(), 'External STOP requested')
        now = time.time()
        if not force and now - self.last_check < 10: return
        usage = check_usage(s['usage_file'], now=now, max_used_percent=100)
        power = read_power()
        require(power['ac'] is True, 'AC power required for the diagnostic')
        require(source_identity(ROOT, sys.executable, s.get('source_plans', PLANS)) == s['source'], 'Frozen sources/HEAD changed')
        require(hashes(s['inputs']) == s['inputs'] and hashes(s['protected']) == s['protected'],
                'Pinned inputs/weights/ZIP changed')
        processes = subprocess.check_output(['ps', '-axo', 'pid=,pgid=,args='], text=True, timeout=5)
        require(not foreign_processes(processes, owner=os.getpid()), 'Foreign model/test process is active')
        s.update(last_guard_at=now, last_power=power, last_usage=usage)
        self.last_check = now


def write_json(path, document):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(document, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def play(seed, side, weights, *, instrumented, frame_path, pair_path, guard, progress, max_pairs, head=None):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock.main import Agent_x
    from agents.Solution_92_Kaggle.base import Global
    from scripts.common import make_opponent
    from scripts.par_eval import build_cfg
    from scripts.holder_rollout import (DiagnosticAgent, Snapshot, HORIZON, paired_rollout,
                                       exact_digest, step_frame, module_fingerprint)
    from scripts.scoring import POINT_COUNTING_VERSION
    import torch

    cls = DiagnosticAgent if instrumented else Agent_x
    options = {'head': head} if instrumented and head is not None else {}
    agent = cls('player_0', agent_path=str(weights), cfg=build_cfg(str(weights), []), train=False, seed=0, **options)
    agent.set_to_eval_mode(); agent.autosave_on_terminate = False
    # Freeze stateless inference modules without altering values or policy.
    for net in [agent.q, agent.target_q, *agent.extra_q]: net.eval().requires_grad_(False)
    other = f'player_{1-int(side[-1])}'
    frozen_modules = module_fingerprint(agent)
    opponent = make_opponent('solution92', other)
    agent.new_game(side)
    random.seed(seed); np.random.seed(seed % 2**32)
    # Neither policy needs Torch randomness in eval; seeding also makes the
    # process-global RNG proof reproducible between the two full executions.
    torch.manual_seed(seed)
    env = LuxAIS3GymEnv(numpy_output=True)
    totals = np.zeros(2, np.int64)
    game_digest = hashlib.sha256()
    steps, resets, pairs, pending, last_pair = 0, 0, [], None, -HORIZON
    matches = []
    def append(stream, value):
        stream.write(json.dumps(value, allow_nan=False, separators=(',', ':')) + '\n'); stream.flush()
    try:
        obs, info = env.reset(seed=seed)
        agent.set_env_cfg(info['params']); opponent.set_env_cfg(info['params'])
        with gzip.open(frame_path, 'xt', encoding='utf-8') as frames, pair_path.open('x') as evidence:
            while True:
                guard()
                before = exact_digest(env.state), exact_digest(obs)
                ms = int(np.asarray(obs[side]['match_steps']))
                can_select = (instrumented and len(pairs) < max_pairs and pending is None
                              and steps-last_pair >= HORIZON and 1 <= ms <= 89)
                if instrumented: agent.collect = can_select
                # Snapshot must precede BOTH live policies. A passive scan chooses
                # the first eligible UID only after the unchanged live act.
                snapshot = Snapshot.capture(env, agent, opponent, obs, Global) if can_select else None
                actions = {side: agent.act(steps, obs[side]), other: opponent.act(steps, obs[other])}
                if agent.caught_errors: raise RuntimeError('Caught agent error in live policy')
                if can_select and agent.candidate is not None:
                    def additional_step(): progress('diagnostic_steps')
                    def technical_step(): progress('technical_extra_steps')
                    pair = paired_rollout(snapshot, side, steps, agent.candidate,
                                          verify=not pairs, guard=guard, on_step=additional_step,
                                          on_technical_step=technical_step)
                    pair.update(pair_id=len(pairs), seed=seed, side=side, status='pending_live_verification')
                    append(evidence, pair)
                    pairs.append(dict(pair_id=len(pairs), step=steps, uid=pair['candidate']['uid'],
                                      effective=pair['effective'], label=pair['label'], reverse_repeat=pair['reverse_repeat']))
                    pending = pair
                    last_pair = steps
                    progress('completed_pairs')
                # Branch activation restored post-act Global references/RNG.
                # Live agent/env/observations and already chosen actions survive.
                next_obs, frame = step_frame(env, agent, opponent, obs, side, steps, actions=actions, before=before,
                                             on_env_step=lambda: progress('instrumented_steps' if instrumented else 'reference_steps'))
                if pending is not None:
                    offset = steps - pending['candidate']['step']
                    require(frame == pending['baseline']['frames'][offset], 'Baseline branch differs from live future')
                    if offset == HORIZON-1:
                        append(evidence, dict(pair_id=pending['pair_id'], status='live_verified',
                                              baseline_sha256=pending['baseline']['sha256']))
                        pairs[-1]['live_verified'] = True
                        pending = None
                append(frames, frame); game_digest.update(bytes.fromhex(frame['sha256']))
                totals += frame['points']; resets += int(ms == 0)
                if int(np.asarray(next_obs[side]['match_steps'])) == 0 or frame['done']:
                    matches.append(dict(points=frame['point_state'], wins=np.asarray(next_obs[side]['team_wins']).tolist()))
                obs = next_obs; steps += 1
                if frame['done']: break
        wins = np.asarray(obs[side]['team_wins']).astype(int).tolist()
        require(pending is None and steps == 303 and resets == 3 and len(matches) == 3 and not agent.caught_errors,
                'Incomplete game or unverified baseline future')
        require(module_fingerprint(agent) == frozen_modules, 'In-memory frozen Q modules changed')
        result = dict(seed=seed, side=side, steps=steps, resets=resets, wins=wins, points=totals.tolist(),
                    matches=matches, point_counting_version=POINT_COUNTING_VERSION,
                    trajectory_sha256=game_digest.hexdigest(), caught_errors=agent.caught_errors, pairs=pairs)
        if instrumented and head is not None:
            result.update(head_opportunities=agent.head_opportunities,
                          last_opportunity_step=agent.last_opportunity_step)
        return result
    finally:
        env.close()


def run_probe(weights, keys_path, out, *, expected_head, usage_file, stop_file, technical_smoke=False):
    weights, keys_path, out = Path(weights).resolve(), Path(keys_path).resolve(), Path(out).absolute()
    require(not out.exists(), 'Output directory already exists; no resume/overwrite')
    keys, historical = validate_keys(keys_path)
    selected = [k for identity in SMOKE_KEYS for k in keys if (k['seed'], k['side']) == identity] if technical_smoke else keys
    return run_collection(weights, out, selected=selected, all_keys=keys,
                          frozen_inputs=[weights, keys_path, historical], source_plans=PLANS,
                          expected_head=expected_head, usage_file=usage_file, stop_file=stop_file,
                          kind='technical_smoke' if technical_smoke else 'historical_diagnostic',
                          max_pairs=1 if technical_smoke else 8, historical_feasibility=True)


def run_collection(weights, out, *, selected, all_keys, frozen_inputs, source_plans,
                   expected_head, usage_file, stop_file, kind, max_pairs=8,
                   historical_feasibility=False, metadata=None, head=None):
    """Shared audited engine loop; callers validate their fixed key protocols first."""
    weights, out = Path(weights).resolve(), Path(out).absolute()
    require(not out.exists(), 'Output directory already exists; no resume/overwrite')
    require(digest(weights) == V14_SHA, 'Only the original V14 weights are allowed')
    protected = protected_inputs(ROOT)
    source = source_identity(ROOT, sys.executable, source_plans)
    require(source['head'] == expected_head, 'Expected HEAD mismatch')
    state = dict(schema_version=1, kind=kind,
                 status='running', pid=os.getpid(), started_at=time.time(), expected_head=expected_head,
                 source=source, inputs=hashes(frozen_inputs), protected=hashes(protected),
                 usage_file=str(Path(usage_file).absolute()), stop_file=str(Path(stop_file).absolute()),
                 keys=selected, all_keys=all_keys, planned_games=2*len(selected), max_pairs_per_game=max_pairs,
                 horizon=12, completed_games=0, completed_pairs=0, additional_steps=0, diagnostic_steps=0, technical_extra_steps=0,
                 reference_steps=0, instrumented_steps=0, games=[],
                 limitations=['historically selected loss/control keys; no performance-strength claim',
                              'whole-team intervention consequences, not single-unit isolated causality'])
    if source_plans != PLANS: state['source_plans'] = list(map(str, source_plans))
    if metadata is not None:
        require(not set(metadata).intersection(state), 'Study metadata shadows collector state')
        state.update(metadata)
        state['limitations'] = ['counterfactual opportunities on baseline trajectories; no policy-strength claim',
                                'whole-team intervention consequences, not single-unit isolated causality']
    guard = Guard(state)
    guard(force=True)
    out.mkdir(parents=True, exist_ok=False)
    manifest = out / 'manifest.json'
    def save(): write_json(manifest, state)
    def progress(counter):
        state[counter] += 1
        if counter in ('diagnostic_steps', 'technical_extra_steps'): state['additional_steps'] += 1
        save()
    save()
    try:
        from scripts.experiment import limit_threads
        limit_threads()
        with resource_lock(ROOT):
            for key in selected:
                seed, side = key['seed'], key['side']
                record = dict(key=key); state['games'].append(record); save()
                for instrumented in (False, True):
                    guard(force=True)
                    name = f'{seed}_{side}_' + ('collector' if instrumented else 'reference')
                    options = {'head': head} if head is not None else {}
                    result = play(seed, side, weights, instrumented=instrumented,
                                  frame_path=out / (name + '.frames.jsonl.gz'), pair_path=out / (name + '.pairs.jsonl'),
                                  guard=guard, progress=progress, max_pairs=state['max_pairs_per_game'], **options)
                    record['collector' if instrumented else 'reference'] = result
                    state['completed_games'] += 1
                    record[name.split('_')[-1] + '_artifacts'] = hashes([
                        out / (name + '.frames.jsonl.gz'), out / (name + '.pairs.jsonl')])
                    save()
                ref, col = record['reference'], record['collector']
                record['passivity'] = {k: ref[k] == col[k] for k in ref if k != 'pairs'}
                save()
                require(all(record['passivity'].values()), 'Reference/collector passivity failure')
                if head is not None:
                    require(1 <= col['head_opportunities'] <= 8,
                            'Neutral head scored no opportunities or exceeded its budget')
            guard(force=True)
        if historical_feasibility:
            cases = [p for g in state['games'] for p in g['collector']['pairs']]
            effective = [p for p in cases if p['effective']]
            positive_games = {(g['key']['seed'], g['key']['side']) for g in state['games']
                              if any(p['effective'] and p['label'] > 0 for p in g['collector']['pairs'])}
            positive = sum(p['label'] > 0 for p in effective)
            state['feasibility'] = dict(cases=len(cases), effective=len(effective), positive=positive,
                                        positive_games=len(positive_games),
                                        passed=(len(effective) >= 24 and positive >= 6 and len(positive_games) >= 3))
        state.update(status='complete', finished_at=time.time()); save()
    except BaseException as exc:
        state.update(status='failed', error=f'{type(exc).__name__}: {exc}', finished_at=time.time()); save()
        raise
    return state


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('weights', 'keys', 'out', 'usage-file', 'stop-file'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--technical-smoke', action='store_true')
    args = parser.parse_args(argv)
    run_probe(args.weights, args.keys, args.out, expected_head=args.expected_head,
              usage_file=args.usage_file, stop_file=args.stop_file, technical_smoke=args.technical_smoke)


if __name__ == '__main__': main()
