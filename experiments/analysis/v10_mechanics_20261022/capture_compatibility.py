"""Capture full action-sequence hashes and non-time metrics for a fixed V10 check.

Run this file with --root ORIGINAL_OR_PATCHED_CHECKOUT --out NEW.json.
Each invocation imports exactly one checkout; no training or checkpoint writes.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    if args.out.exists():
        raise SystemExit('Refusing to overwrite an existing receipt')
    sys.path.insert(0, str(root))
    from scripts.experiment import limit_threads
    limit_threads()
    import numpy as np
    from luxai_s3.params import EnvParams
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent, play_game

    assert EnvParams().match_count_per_episode == 3
    weights = root / 'agents/sherlock/weights/agent_p0.pth'
    expected = '03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67'
    assert hashlib.sha256(weights.read_bytes()).hexdigest() == expected
    agent = Agent_x('player_0', agent_path=str(weights), train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    for flag in ('sap_overkill_recovery', 'nebula_infer_drift_safe'):
        assert not getattr(agent.cfg, flag, False)
    original_act = agent.act
    env = LuxAIS3GymEnv(numpy_output=True)
    games = []
    try:
        for seed in (610000, 610001):
            for side in ('player_0', 'player_1'):
                opponent = make_opponent('solution92', 'player_1' if side == 'player_0' else 'player_0')
                traces = {'agent': [], 'opponent': []}

                def capture(call, name):
                    def act(*a, **kw):
                        actions = call(*a, **kw)
                        traces[name].append(np.asarray(actions, dtype=np.int64).tolist())
                        return actions
                    return act

                agent.act = capture(original_act, 'agent')
                opponent.act = capture(opponent.act, 'opponent')
                row = play_game(env, agent, opponent, seed, side, train=False)
                row.pop('secs')
                row['action_trace_sha256'] = {
                    name: hashlib.sha256(json.dumps(trace, separators=(',', ':')).encode()).hexdigest()
                    for name, trace in traces.items()
                }
                row['action_count'] = {name: len(trace) for name, trace in traces.items()}
                assert all(count == row['steps'] for count in row['action_count'].values())
                games.append(row)
    finally:
        env.close()
    assert hashlib.sha256(weights.read_bytes()).hexdigest() == expected
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as f:
        json.dump({'root': str(root), 'weights_sha256': expected, 'games': games}, f, indent=2, allow_nan=False)
        f.write('\n')
    print(f'Captured {len(games)} games with all action-sequence hashes: {args.out}')


if __name__ == '__main__':
    main()
