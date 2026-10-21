"""Eight-game passive influence probe; fixed seeds/times, no learning or rollouts.

Run as a module from the repository root after independent code review:
  python -m experiments.analysis.v4_target_pilot_20261021.run_influence \
    --weights agents/sherlock/weights/agent_p0.pth --out /fresh/output/directory
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

import numpy as np
import torch

from .influence import (InfluenceAgent, TraceAgent, assert_same_game, check_data_budget,
                        clone_agent, file_hash, fresh_output, protect_files, validate_agent)

ROOT = Path(__file__).resolve().parents[3]
GAMES = ((524000, 'player_0'), (524000, 'player_1'),
         (524001, 'player_0'), (524001, 'player_1'))
V3_SHA256 = 'aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935'
OLD_SHA256 = '3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158'
DATA_LIMIT = 128 * 1024 * 1024
SECONDS_LIMIT = 30 * 60


@contextmanager
def hard_deadline(seconds=SECONDS_LIMIT):
    """Real wall-time signal, including a blocked game; never grant extra time."""
    if seconds <= 0 or seconds > SECONDS_LIMIT:
        raise ValueError('deadline must be positive and at most 30 minutes')
    if signal.getitimer(signal.ITIMER_REAL)[0]:
        raise RuntimeError('refuse to replace an existing wall-time alarm')
    previous = signal.getsignal(signal.SIGALRM)
    def expired(signum, frame):
        raise TimeoutError('30-minute influence collection deadline reached')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def validate_v3(path):
    if file_hash(path) != V3_SHA256:
        raise ValueError('input weights must be the unchanged protected V3 checkpoint')


def protected_paths(weights):
    """Protect this checkout, the primary checkout and both old-release backups."""
    common = subprocess.check_output(['git', 'rev-parse', '--git-common-dir'], cwd=ROOT,
                                     text=True).strip()
    primary = (ROOT / common).resolve().parent
    paths = {Path(weights).resolve()}
    for checkout in {ROOT, primary}:
        for side in (0, 1):
            current = checkout / 'agents/sherlock/weights' / f'agent_p{side}.pth'
            old = checkout / 'experiments/releases/20261020_old3_sym3' / f'agent_p{side}.pth'
            validate_v3(current)
            if file_hash(old) != OLD_SHA256:
                raise ValueError(f'old release backup does not match expected hash: {old}')
            paths.update((current.resolve(), old.resolve()))
    return sorted(paths)


def write_json(path, payload, limit=DATA_LIMIT):
    path = Path(path)
    def scalar(value):
        if isinstance(value, np.generic): return value.item()
        if isinstance(value, np.ndarray): return value.tolist()
        raise TypeError(f'unsupported JSON value {type(value)}')
    data = (json.dumps(payload, indent=2, sort_keys=True, default=scalar,
                       allow_nan=False) + '\n').encode()
    used = sum(p.stat().st_size for p in path.parent.rglob('*') if p.is_file())
    if used + len(data) > limit:
        raise RuntimeError('data budget exceeded before write')
    with path.open('xb') as stream:
        stream.write(data)


def influence_gate(record_sets):
    expected = {(m, s) for m in (1, 2) for s in (25, 45, 65, 85)}
    if len(record_sets) != 4:
        raise AssertionError('influence requires exactly four shadow games')
    for records in record_sets:
        if len(records) != 8 or {(r['match_idx'], r['match_step']) for r in records} != expected:
            raise AssertionError('missing or duplicate scheduled influence state')
    changed = sum(r['distinct_changed_arrays'] > 0 for rows in record_sets for r in rows)
    return dict(scheduled_states=32, action_changing_states=changed,
                threshold=8, passed=bool(changed >= 8))


def run_one(env, base_agent, seed, side, shadow):
    from scripts.common import make_opponent, play_game
    agent = clone_agent(base_agent)
    influenced = InfluenceAgent(agent) if shadow else None
    own = TraceAgent(influenced if shadow else agent)
    opponent = TraceAgent(make_opponent('solution92', 'player_1' if side == 'player_0' else 'player_0'))
    torch.manual_seed(seed)
    summary = play_game(env, own, opponent, seed=seed, our_side=side, train=False)
    return dict(summary=summary, traces=dict(ours=own.trace, opponent=opponent.trace),
                scheduled_states=influenced.records if shadow else [])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--weights', required=True)
    parser.add_argument('--out', required=True, help='new, nonexistent result directory')
    args = parser.parse_args(argv)
    out, weights = Path(args.out).resolve(), Path(args.weights).resolve()
    validate_v3(weights)
    paths = protected_paths(weights)
    fresh_output(out)
    start = time.monotonic()
    records = []
    status = 'failed'
    try:
        with hard_deadline(), protect_files(paths) as before:
            write_json(out / 'manifest.json', dict(
                stage='influence_only', games=[list(g) for g in GAMES], total_games=8,
                weights=str(weights), protected_before=before,
                seconds_limit=SECONDS_LIMIT, data_bytes_limit=DATA_LIMIT,
                scheduled_states=32, action_change_gate=8,
                point_counting_version=2, python=sys.version,
                numpy=np.__version__, torch=torch.__version__,
                git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()))
            from luxai_s3.wrappers import LuxAIS3GymEnv
            from agents.sherlock.main import Agent_x
            torch.set_num_threads(1)
            base = Agent_x('player_0', agent_path=str(weights), train=False, seed=0)
            # Prepare once, before sharing anything. Shadows never switch module mode.
            for module in [base.q, base.target_q, *base.extra_q]:
                module.eval()
            validate_agent(base)
            env = LuxAIS3GymEnv(numpy_output=True)
            try:
                for seed, side in GAMES:
                    control = run_one(env, base, seed, side, shadow=False)
                    write_json(out / f'{seed}_{side}_control.json', control)
                    shadow = run_one(env, base, seed, side, shadow=True)
                    write_json(out / f'{seed}_{side}_shadow.json', shadow)
                    assert_same_game(control, shadow)
                    records.append(shadow['scheduled_states'])
                    check_data_budget(out)
                    print(f'{seed} {side}: complete control trajectory reproduced; '
                          f'{sum(r["distinct_changed_arrays"] > 0 for r in records[-1])}/8 action-changing states',
                          flush=True)
            finally:
                env.close()
            gate = influence_gate(records)
            status = 'complete'
        # protect_files has verified all protected files, including exception paths.
        write_json(out / 'result.json', dict(
            status=status, elapsed_seconds=time.monotonic() - start, gate=gate,
            trajectories_identical=True, games_completed=8,
            protected_after={str(p): file_hash(p) for p in paths},
            next_step='eligible_for_separate_isolation_stage' if gate['passed'] else 'stop_pilot'))
        print(json.dumps(gate, sort_keys=True), flush=True)
    except BaseException as error:
        write_json(out / 'failure.json', dict(
            status='failed', error=repr(error), elapsed_seconds=time.monotonic() - start,
            completed_pairs=len(records),
            protected_after={str(p): file_hash(p) if p.is_file() else None for p in paths}))
        raise


if __name__ == '__main__':
    main()
