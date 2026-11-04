"""Observation-only development traces, paired with an ordinary identical game.

Run as ``python -m scripts.student_failure_trace``. Both games use common.play_game.
Only post-step measurement reads terminal scoring information; it never reaches act.
A final action differing from the masked network preference is an observed override,
not proof of a particular rule's causal contribution.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x
from scripts.common import make_opponent, play_game
from scripts.scoring import match_points_after_step
from scripts.student_collect import (_env, _learning_digest, _pins, reserve_output)
from scripts.student_distill import _hashes, _write, sha256


def json_copy(value):
    """Detach observed values into JSON without references to live agent arrays."""
    if isinstance(value, dict):
        return {str(k): json_copy(v) for k, v in value.items()}
    if isinstance(value, np.ndarray):
        return json_copy(value.tolist())
    if isinstance(value, (list, tuple, set)):
        return [json_copy(v) for v in value]
    if isinstance(value, np.generic):
        return json_copy(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f'Cannot retain non-data observer value: {type(value).__name__}')


def canonical_actions(world, mirrored):
    result = np.asarray(world).copy()
    if mirrored:
        moving = result[:, 0] < geo.SAP
        result[moving, 0] = geo.MIRROR_DIR[result[moving, 0]]
        sapping = result[:, 0] == geo.SAP
        result[sapping, 1:3] = -result[sapping, 1:3][:, ::-1]
    return result


def action_digest(actions):
    """Both players, all unit rows and all three action components."""
    digest = hashlib.sha256()
    for side in ('player_0', 'player_1'):
        array = np.asarray(actions[side])
        if array.ndim != 2 or array.shape[1] != 3 or not np.issubdtype(array.dtype, np.integer):
            raise ValueError('Actions must be integer [units,3] arrays')
        digest.update(side.encode())
        digest.update(str(array.shape).encode())
        digest.update(np.asarray(array, dtype='<i8').tobytes())
    return digest.hexdigest()


class FailureTrace:
    """Instance-local hooks observe original forwards and the original act once."""
    def __init__(self, agent, emit, check=lambda: None):
        self.agent, self.emit, self.check = agent, emit, check
        self._active = False
        self._handles = []
        self._match = None
        self.act_steps = 0
        self._seen_relics, self._seen_points = set(), set()
        self.first_seen = dict(relics={}, points={})

    def __enter__(self):
        self._had_act = 'act' in vars(self.agent)
        self._own_act = vars(self.agent).get('act')
        self._original = self.agent.act
        try:
            for index, net in enumerate([self.agent.q, *self.agent.extra_q]):
                self._handles.append(net.register_forward_hook(
                    lambda module, inputs, output, index=index: self._hook(index, inputs, output)))
            self.agent.act = self._act
        except BaseException:
            self.__exit__()
            raise
        return self

    def __exit__(self, *exc):
        for handle in self._handles:
            handle.remove()
        self._handles.clear()
        if self._had_act:
            self.agent.act = self._own_act
        elif 'act' in vars(self.agent):
            del self.agent.act

    def _hook(self, index, inputs, output):
        if not self._active:
            raise ValueError('Observed network forward outside original act')
        if index in self._calls:
            raise ValueError('Network forwarded twice in one decision')
        # Agent_x masks its CPU numpy view in place. Clone before returning!
        self._calls[index] = (inputs[0].detach().cpu().clone(), output.detach().cpu().clone())
        if index == 0:
            ctx = self.agent._prev_ctx
            if ctx is None:
                raise ValueError('Current network call has no current context')
            self._context = json_copy({k: v for k, v in ctx.items() if k != 'belief'})

    def _act(self, step, obs):
        self.check()
        if self.agent.training or self.agent.cfg.frozen or self.agent.autosave_on_terminate:
            raise ValueError('Trace requires fail-fast eval with autosave disabled')
        if self.agent.cnn_policy is not None:
            raise ValueError('Trace supports raw Q policies without CNN mixing')
        self._calls, self._context = {}, None
        visible = json_copy(obs)
        self._active = True
        try:
            actions = self._original(step=step, obs=obs)
        finally:
            self._active = False
        belief = self.agent.belief
        match = int(belief.match_idx)
        if match != self._match:
            self._match = match
            self._counts = dict(act_steps=0, network_steps=0, unit_rows=0, overrides=0)
        self._counts['act_steps'] += 1
        self.act_steps += 1
        relics = set(map(tuple, belief.relic_positions))
        points = set(map(tuple, np.argwhere(belief.point_tiles)))
        new_relics, new_points = relics - self._seen_relics, points - self._seen_points
        for name, coordinates in (('relics', new_relics), ('points', new_points)):
            for xy in sorted(coordinates):
                self.first_seen[name].setdefault(str(xy), dict(env_step=int(step), match_index=match,
                                                              match_step=int(np.asarray(obs['match_steps']))))
        self._seen_relics |= relics
        self._seen_points |= points
        row = dict(type='decision', env_step=int(step), match_step=int(np.asarray(obs['match_steps'])),
                   match_index=match, player=self.agent.player if hasattr(self.agent, 'player') else None,
                   canonical_mirrored=bool(belief.mirrored),
                   coordinate_convention='observation/final_world_action: world; context/features/knowledge/network/final_canonical_action: canonical',
                   observation=visible, context=self._context, units=[],
                   known_relics=sorted(relics), known_point_tiles=sorted(points),
                   discoveries=dict(new_relics=sorted(new_relics), new_point_tiles=sorted(new_points)),
                   final_world_actions=np.asarray(actions).copy())
        feats, masks = self.agent._prev_feats, self.agent._prev_masks
        if not self._calls:
            if feats or masks:
                raise ValueError('Ghost features without a current network call')
            row['kind'] = 'reset' if row['match_step'] == 0 else 'no_units'
            row['context'] = None
        else:
            if row['match_step'] == 0 or set(self._calls) != set(range(1 + len(self.agent.extra_q))):
                raise ValueError('Reset network rows or incomplete ensemble')
            ids = list(feats)
            if not ids or set(ids) != set(masks):
                raise ValueError('Invalid current feature/mask unit alignment')
            x = self._calls[0][0].numpy()
            if x.shape != (len(ids), 79) or not np.array_equal(x, np.stack([feats[u] for u in ids])):
                raise ValueError('Captured features differ from current decision')
            predictions = []
            for index in range(len(self._calls)):
                inputs, output = self._calls[index]
                if (not torch.equal(inputs, torch.from_numpy(x[:, :inputs.shape[1]]))
                        or output.shape != (len(ids), 6) or not torch.isfinite(output).all()):
                    raise ValueError('Invalid ensemble input/output alignment')
                predictions.append(output)
            # Same float32 reduction/order as Agent_x, not numpy's different sum.
            raw_q = (torch.stack(predictions).mean(0) if len(predictions) > 1 else predictions[0]).numpy()
            mask = np.stack([masks[u] for u in ids]).copy()
            if mask.dtype != np.bool_ or mask.shape != raw_q.shape or not mask.any(axis=1).all():
                raise ValueError('Invalid current action mask')
            if not np.isfinite(x).all():
                raise ValueError('Nonfinite network input')
            world = np.asarray(actions)
            if (world.shape != (16, 3) or not np.issubdtype(world.dtype, np.integer)
                    or any(not 0 <= u < 16 for u in ids) or ((world[:, 0] < 0) | (world[:, 0] > 5)).any()):
                raise ValueError('Invalid final world actions or unit IDs')
            final = canonical_actions(world, belief.mirrored)
            preferences = np.where(mask, raw_q, -np.inf).argmax(1)
            for index, uid in enumerate(ids):
                action = int(final[uid, 0])
                changed = action != int(preferences[index])
                row['units'].append(dict(uid=int(uid), features=x[index], mask=mask[index],
                    raw_q=raw_q[index], network_action=int(preferences[index]),
                    final_world_action=world[uid].copy(), final_canonical_action=final[uid].copy(),
                    final_outside_network_mask=not bool(mask[index, action]), override_observed=changed))
                self._counts['overrides'] += int(changed)
            self._counts['network_steps'] += 1
            self._counts['unit_rows'] += len(ids)
            row['kind'] = 'network'
            row['ensemble_members'] = len(predictions)
        row['match_counts'] = dict(self._counts)
        self.emit(json_copy(row))
        return actions


class ObservedEnv:
    """Read-only step recorder; delegates simulation to the unmodified env."""
    def __init__(self, env, side, emit=lambda row: None, check=lambda: None):
        self.env, self.side, self.emit, self.check = env, side, emit, check

    def __getattr__(self, name):
        return getattr(self.env, name)

    def reset(self, *args, **kwargs):
        result = self.env.reset(*args, **kwargs)
        self._previous = result[0][self.side]
        self.step_digests, self.matches, self.action_history = [], [], []
        self._match = 0
        self._first_point_step = [None, None]
        return result

    def step(self, actions):
        self.check()
        digest = action_digest(actions)
        saved_actions = json_copy(actions)
        result = self.env.step(actions)
        observations, _, _, _, info = result
        next_obs = observations[self.side]
        points = match_points_after_step(self._previous, next_obs, info)
        index = len(self.step_digests)
        for team in (0, 1):
            if points[team] > 0 and self._first_point_step[team] is None:
                self._first_point_step[team] = index
        ended = int(np.asarray(next_obs['match_steps'])) == 0
        row = dict(type='transition', env_step=index, match_index=self._match,
                   actions_world=saved_actions, action_digest=digest,
                   next_visible_team_points=json_copy(next_obs['team_points']),
                   next_visible_team_wins=json_copy(next_obs['team_wins']),
                   next_match_step=int(np.asarray(next_obs['match_steps'])))
        if ended:
            metrics = dict(match_index=self._match, end_env_step=index, points=json_copy(points),
                           team_wins=json_copy(next_obs['team_wins']),
                           first_positive_points_env_step=list(self._first_point_step))
            self.matches.append(metrics)
            row['terminal_points_external_only'] = json_copy(points)
            self._match += 1
            self._first_point_step = [None, None]
        self.step_digests.append(digest)
        self.action_history.append(saved_actions)
        self.emit(row)
        self._previous = next_obs
        return result

    @property
    def digest(self):
        return hashlib.sha256(''.join(self.step_digests).encode()).hexdigest()


def _agent(path, side, seed):
    checkpoint = torch.load(path, map_location='cpu', weights_only=True)
    if checkpoint.get('feature_dim') != 79 or checkpoint.get('n_actions') != 6:
        raise ValueError('Trace requires 79-feature/6-action checkpoints')
    cfg = AgentConfig(**dict(checkpoint['cfg'], frozen=False))
    agent = Agent_x(side, str(path), cfg=cfg, train=False, seed=seed)
    agent.autosave_on_terminate = agent.learn_enabled = False
    agent.set_to_eval_mode()
    if agent.device.type != 'cpu':
        raise ValueError('Trace requires one CPU thread')
    for net in [agent.q, agent.target_q, *agent.extra_q]:
        net.eval()
    return agent


def trace_pair(model: Path, opponent: str, seed: int, side: str, out: Path,
               deadline: datetime, opponent_path: Path | None = None):
    if deadline.tzinfo is None:
        raise ValueError('Deadline must include a UTC offset')
    if opponent not in ('solution92', 'self') or side not in ('player_0', 'player_1'):
        raise ValueError('Unsupported opponent or side')
    if opponent == 'self' and opponent_path is None:
        raise ValueError('Self opponent requires --opponent-path')
    if type(seed) is not int or seed < 0:
        raise ValueError('Seed must be a nonnegative integer')
    def check():
        if datetime.now(timezone.utc) >= deadline:
            raise TimeoutError('Trace deadline reached')
    check()
    model = Path(model).expanduser().resolve(strict=True)
    opponent_path = Path(opponent_path).expanduser().resolve(strict=True) if opponent_path else None
    inputs = [model] + ([opponent_path] if opponent_path else [])
    out = reserve_output(out, inputs)
    summary = dict(schema_version=1, status='running', model=str(model), opponent=opponent,
                   opponent_path=str(opponent_path) if opponent_path else None, seed=seed, side=side,
                   cpu_threads=1, deadline_utc=deadline.isoformat(), games_completed=0,
                   observation_limitations='Agent-visible state only in decision rows. Terminal scoring is external measurement. Overrides have no attributed rule identity.')
    _write(out / 'summary.json', summary)
    try:
        torch.set_num_threads(1)
        summary['inputs_before'] = _hashes(inputs)
        summary['pins_before'] = _pins()
        summary['source_sha256'] = sha256(Path(__file__).resolve())
        runs, histories = [], []
        for instrumented in (False, True):
            check()
            label = 'observed' if instrumented else 'plain'
            # Historical par_eval uses this local agent RNG seed; env uses seed.
            agent = _agent(model, side, 0)
            opp = make_opponent(opponent, 'player_1' if side == 'player_0' else 'player_0',
                                self_play_path=str(opponent_path) if opponent_path else None)
            if hasattr(opp, 'cfg'):
                opp.cfg.frozen = False
            if hasattr(opp, 'autosave_on_terminate'):
                opp.autosave_on_terminate = False
            initial = _learning_digest(agent)
            with (out / f'{label}.jsonl').open('x') as log:
                def emit(row):
                    log.write(json.dumps(json_copy(row), allow_nan=False, separators=(',', ':')) + '\n')
                env = ObservedEnv(_env(), side, emit, check)
                observer = FailureTrace(agent, emit, check) if instrumented else nullcontext()
                try:
                    with observer:
                        metrics = play_game(env, agent, opp, seed, side, train=False)
                    if metrics['steps'] != 303 or len(env.matches) != 3:
                        raise ValueError('Expected a complete three-match/303-step course game')
                    if instrumented and observer.act_steps != 303:
                        raise ValueError('Expected exactly 303 observed original act calls')
                    if _learning_digest(agent) != initial or agent.caught_errors or getattr(opp, 'caught_errors', 0):
                        raise ValueError('Learning-state mutation or caught agent failure')
                    run = dict(label=label, result=json_copy({k: v for k, v in metrics.items() if k != 'secs'}),
                               secs=metrics['secs'], full_action_digest=env.digest,
                               step_digests=env.step_digests, matches=env.matches,
                               learning_state_unchanged=True)
                    if instrumented:
                        run['first_seen'] = observer.first_seen
                        run['observed_act_steps'] = observer.act_steps
                    runs.append(run)
                    histories.append(env.action_history)
                    summary['games_completed'] += 1
                finally:
                    env.close()
            _write(out / f'{label}_summary.json', run)
        plain, observed = runs
        summary.update(actions_equal=histories[0] == histories[1],
                       step_digests_equal=plain['step_digests'] == observed['step_digests'],
                       full_action_digest_equal=plain['full_action_digest'] == observed['full_action_digest'],
                       results_equal=plain['result'] == observed['result'],
                       match_metrics_equal=plain['matches'] == observed['matches'], runs=runs)
        summary['inputs_after'], summary['pins_after'] = _hashes(inputs), _pins()
        if not all(summary[k] for k in ('actions_equal', 'step_digests_equal', 'full_action_digest_equal', 'results_equal', 'match_metrics_equal')):
            raise ValueError('Plain/instrumented actions or results differ')
        if (summary['inputs_before'] != summary['inputs_after'] or summary['pins_before'] != summary['pins_after']
                or summary['source_sha256'] != sha256(Path(__file__).resolve())):
            raise ValueError('Input/source/protected-file mutation during trace')
        check()
        summary.update(status='done', files_sha256={name: sha256(out / name) for name in
                       ('plain.jsonl', 'observed.jsonl', 'plain_summary.json', 'observed_summary.json')})
        _write(out / 'summary.json', summary)
        return summary
    except BaseException as error:
        summary.update(status='failed', error=f'{type(error).__name__}: {error}')
        _write(out / 'summary.json', summary)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--opponent', choices=('solution92', 'self'), required=True)
    parser.add_argument('--opponent-path', type=Path)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--side', choices=('player_0', 'player_1'), required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--deadline-utc', required=True)
    args = parser.parse_args()
    result = trace_pair(args.model, args.opponent, args.seed, args.side, args.out,
                        datetime.fromisoformat(args.deadline_utc.replace('Z', '+00:00')), args.opponent_path)
    print(json.dumps(dict(status=result['status'], out=str(args.out), actions_equal=result['actions_equal'])))


if __name__ == '__main__':
    main()
