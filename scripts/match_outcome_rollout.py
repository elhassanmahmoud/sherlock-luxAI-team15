"""Experimental one-shot runner-up proposals with real match-end labels.

No production patch, learning, lookahead in the actor, or hidden actor features.
The simulator-only observer uses the same installed wrapper state as final_state.
"""
from __future__ import annotations

import numpy as np
from agents.sherlock.main import Agent_x
from scripts import holder_rollout as h


def choose_opportunity(ctx, ids, masks, q, used_match):
    ms = int(ctx['match_step'])
    match = int(ctx['step']) // (int(ctx['max_match_steps']) + 1)
    if not 40 <= ms <= 70 or match in used_match:
        return None
    if np.shape(q) != np.shape(masks) or np.shape(q) != (len(ids), 6):
        raise ValueError('Q/mask/unit shape mismatch')
    choices = []
    for i, uid in enumerate(ids):
        legal = np.flatnonzero(masks[i])
        if not np.isfinite(q[i, legal]).all():
            raise ValueError('Legal Q values must be finite')
        if len(legal) < 2:
            continue
        order = sorted(map(int, legal), key=lambda a: (-float(q[i, a]), a))
        first, second = order[:2]
        choices.append(dict(step=int(ctx['step']), match=match, match_step=ms,
                            uid=int(uid), row=i, proposal=first, alternative=second,
                            gap=float(q[i, first])-float(q[i, second])))
    return min(choices, key=lambda x: (x['gap'], x['uid'])) if choices else None


class MatchOutcomeAgent(Agent_x):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.training or self.cnn_policy is not None:
            raise ValueError('Only frozen evaluation DQN is supported')
        self.buffer = self.opt = None
        self.collect = False
        self.used_matches = set()
        self.candidate = self.intervention = None
        self.intervention_hits = 0
        for net in [self.q, self.target_q, *self.extra_q]:
            net.eval().requires_grad_(False)

    def new_game(self, player=None):
        super().new_game(player)
        self.used_matches = set()

    def update(self, *args, **kwargs):
        raise RuntimeError('Match outcome actor cannot train')

    def act(self, step, obs):
        self.candidate = None
        return super().act(step, obs)

    def _network_values(self, features):
        result = super()._network_values(features)
        # Copies precede main.py's in-place NumPy masking; no second _decide.
        self.probe_q = result.detach().cpu().numpy().copy()
        self.probe_features = features.detach().cpu().numpy().copy()
        return result

    def _policy_greedy(self, ctx, ids, masks, greedy):
        if self.collect:
            candidate = choose_opportunity(ctx, ids, masks, self.probe_q, self.used_matches)
            if candidate is not None:
                k = candidate['row']
                candidate.update(features=self.probe_features[k].tolist(),
                                 q=self.probe_q[k].tolist(), mask=masks[k].tolist())
                self.candidate = candidate
                self.used_matches.add(candidate['match'])
        order = self.intervention
        if order is not None and int(ctx['step']) == order['step']:
            if self.intervention_hits or order['uid'] not in ids:
                raise ValueError('Repeated or missing-unit intervention')
            k = list(ids).index(order['uid'])
            if int(greedy[k]) != order['proposal'] or not masks[k, order['alternative']]:
                raise ValueError('Intervention precondition mismatch')
            result = greedy.copy()
            result[k] = order['alternative']
            self.intervention_hits += 1
            return result
        return greedy


def terminal_outcome(previous, following, points, info):
    if int(np.asarray(following['match_steps'])) != 0:
        raise ValueError('Not a match boundary')
    delta = np.asarray(following['team_wins'], dtype=np.int64) - np.asarray(previous['team_wins'], dtype=np.int64)
    if delta.shape != (2,) or delta.sum() != 1 or not np.isin(delta, [0, 1]).all():
        raise ValueError('Expected exactly one actual match winner')
    winner = int(delta.argmax())
    state = info['final_state']
    energies = (np.asarray(state.units.energy)[..., 0] * np.asarray(state.units_mask)).sum(axis=1)
    points = np.asarray(points)
    if points.shape != (2,) or energies.shape != (2,) or not np.isfinite(energies).all():
        raise ValueError('Malformed terminal values')
    reason = 'points' if points[0] != points[1] else 'energy' if energies[0] != energies[1] else 'random'
    expected = int(points.argmax()) if reason == 'points' else int(energies.argmax())
    if reason != 'random' and winner != expected:
        raise ValueError('Winner inconsistent with engine priority')
    return dict(winner=winner, reason=reason, points=points.tolist(), energies=energies.tolist(),
                wins=np.asarray(following['team_wins']).tolist())


def step_frame(env, agent, opponent, obs, side, step, **kwargs):
    following, frame = h.step_frame(env, agent, opponent, obs, side, step, **kwargs)
    frame['terminal'] = None
    if int(np.asarray(following[side]['match_steps'])) == 0:
        # The reviewed Lux wrapper assigns exactly info['final_state'] to state.
        frame['terminal'] = terminal_outcome(obs[side], following[side], frame['point_state'],
                                             {'final_state': env.state})
    del frame['sha256']
    frame['sha256'] = h.exact_digest(frame)
    return following, frame


def rollout_to_match_end(snapshot, side, opportunity, alternative=False, *, guard=lambda: None, on_step=lambda: None):
    branch = snapshot.fork()
    branch.agent.collect = False
    branch.agent.intervention = opportunity if alternative else None
    branch.agent.intervention_hits = 0
    frames = []
    with branch.activate():
        obs = branch.obs
        ms = int(np.asarray(obs[side]['match_steps']))
        if not 40 <= ms <= 70 or ms != opportunity['match_step']:
            raise ValueError('Invalid snapshot start')
        for offset in range(101-ms):
            guard()
            if int(np.asarray(obs[side]['match_steps'])) != ms+offset:
                raise ValueError('Unexpected match clock')
            obs, frame = step_frame(branch.env, branch.agent, branch.opponent, obs, side,
                                    opportunity['step']+offset, on_env_step=on_step)
            if branch.agent.caught_errors:
                raise ValueError('Caught agent error in branch')
            frames.append(frame)
            if frame['terminal'] is not None:
                if offset != 100-ms:
                    raise ValueError('Unexpected early match boundary')
                break
            if frame['done']:
                raise ValueError('Episode terminated before match boundary')
        if not frames[-1]['terminal'] or branch.agent.intervention_hits != int(alternative):
            raise ValueError('Missing terminal or intervention')
    team = int(side[-1]); other = 1-team
    return dict(frames=frames, outcome=frames[-1]['terminal'],
                h12_points=frames[11]['point_state'],
                won=int(frames[-1]['terminal']['winner'] == team),
                point_margin=int(frames[-1]['point_state'][team]-frames[-1]['point_state'][other]),
                sha256=h.exact_digest(frames))


def paired_match_outcome(snapshot, side, opportunity, *, verify=False, guard=lambda: None,
                         on_step=lambda: None, on_technical_step=lambda: None):
    baseline = rollout_to_match_end(snapshot, side, opportunity, guard=guard, on_step=on_step)
    alternative = rollout_to_match_end(snapshot, side, opportunity, True, guard=guard, on_step=on_step)
    checks = None
    if verify:
        again_alt = rollout_to_match_end(snapshot, side, opportunity, True, guard=guard, on_step=on_technical_step)
        again_base = rollout_to_match_end(snapshot, side, opportunity, guard=guard, on_step=on_technical_step)
        checks = dict(alternative_repeat=alternative == again_alt, baseline_reverse_repeat=baseline == again_base)
        if not all(checks.values()):
            raise ValueError('Branch isolation/repeat failure')
    effective = baseline['frames'][0]['actions'] != alternative['frames'][0]['actions']
    if not effective and baseline != alternative:
        raise ValueError('Identical emitted actions have different continuation')
    t = int(side[-1]); o = 1-t
    return dict(candidate=opportunity, baseline=baseline, alternative=alternative,
                effective=effective, delta_win=alternative['won']-baseline['won'],
                delta_points=alternative['point_margin']-baseline['point_margin'],
                delta_h12=(alternative['h12_points'][t]-alternative['h12_points'][o]
                           -baseline['h12_points'][t]+baseline['h12_points'][o]),
                reverse_repeat=checks)
