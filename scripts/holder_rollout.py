"""Diagnostic-only, isolated twelve-action HOLD counterfactuals.

The installed Lux wrapper mutates only state and rng_key in step; the JAX
engine is pure. Snapshot rejects an unreviewed wrapper attribute inventory.
No reset, configuration setter, training, or production monkeypatch is used.
"""
from __future__ import annotations

import copy
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import random
import struct
import sys

import numpy as np
import torch

from agents.sherlock.main import Agent_x
from agents.sherlock import geometry as geo
from scripts.scoring import match_points_after_step
from scripts.targeting_probe import PUBLIC_FIELDS, _json, action_bytes

HORIZON = 12
WRAPPER_FIELDS = {'numpy_output', 'rng_key', 'jax_env', 'env_params', 'action_space', 'state'}


def exact_digest(value):
    """Hash typed arrays and nested states without rounding or float JSON loss."""
    digest = hashlib.sha256()
    def emit(data):
        digest.update(struct.pack('!Q', len(data))); digest.update(data)
    def visit(obj):
        if isinstance(obj, dict):
            emit(b'dict')
            for key in sorted(obj, key=lambda k: (type(k).__name__, str(k))):
                visit(key); visit(obj[key])
        elif isinstance(obj, (tuple, list)):
            emit(type(obj).__name__.encode())
            emit(str(len(obj)).encode())
            for v in obj: visit(v)
        elif isinstance(obj, torch.Tensor):
            visit(obj.detach().cpu().numpy())
        elif isinstance(obj, np.ndarray) or hasattr(obj, '__jax_array__') or type(obj).__module__.startswith(('jax', 'jaxlib')):
            import jax
            if hasattr(obj, 'dtype') and jax.dtypes.issubdtype(obj.dtype, jax.dtypes.prng_key):
                emit(b'jax-key'); visit(jax.random.key_data(obj)); return
            arr = np.asarray(obj)
            emit(b'array'); emit(arr.dtype.str.encode()); emit(str(arr.shape).encode()); emit(arr.tobytes())
        elif isinstance(obj, np.generic):
            visit(np.asarray(obj))
        elif obj is None or isinstance(obj, (str, bool, int, float)):
            emit(type(obj).__name__.encode()); emit(repr(obj).encode())
        else:
            from flax.serialization import to_state_dict
            converted = to_state_dict(obj)
            if converted is obj:
                raise TypeError(f'Unsupported exact hash type {type(obj)}')
            emit(type(obj).__qualname__.encode()); visit(converted)
    visit(value)
    return digest.hexdigest()


def rng_state():
    return random.getstate(), np.random.get_state(), torch.get_rng_state().clone()


def restore_rng(state):
    random.setstate(state[0]); np.random.set_state(state[1]); torch.set_rng_state(state[2])


def global_attributes(cls):
    return {k: v for k, v in vars(cls).items() if not k.startswith('__')}


def install_globals(cls, attributes):
    for name in set(global_attributes(cls)) - set(attributes): delattr(cls, name)
    for name, value in attributes.items(): setattr(cls, name, value)


def module_fingerprint(agent):
    return exact_digest([dict(state=net.state_dict(),
                              modules=[dict(type=type(m).__qualname__, training=m.training,
                                            forward_hooks=list(m._forward_hooks),
                                            pre_hooks=list(m._forward_pre_hooks),
                                            backward_hooks=list(m._backward_hooks)) for m in net.modules()],
                              requires_grad=[p.requires_grad for p in net.parameters()])
                         for net in [agent.q, agent.target_q, *agent.extra_q]])


def frozen_memo(agent):
    if agent.training or agent.cnn_policy is not None:
        raise ValueError('Only evaluation DQN agents without CNN are supported')
    memo = {}
    from agents.sherlock.model import QNet
    for net in [agent.q, agent.target_q, *agent.extra_q]:
        if any(type(m) not in (QNet, torch.nn.Sequential, torch.nn.Linear, torch.nn.ReLU) for m in net.modules()):
            raise ValueError('Only inspected stateless QNet layers may be shared')
        if any(m.training or m._forward_hooks or m._forward_pre_hooks for m in net.modules()):
            raise ValueError('Shared Q modules must be stateless evaluation modules without hooks')
        if list(net.buffers()) or any(p.requires_grad for p in net.parameters()):
            raise ValueError('Shared Q modules must have frozen parameters and no mutable buffers')
        memo[id(net)] = net
        # Optimizer references, if present, must point to the same frozen params.
        for parameter in net.parameters(): memo[id(parameter)] = parameter
    return memo


@dataclass
class Snapshot:
    env: object
    agent: object
    opponent: object
    globals: dict
    obs: dict
    rng: tuple
    global_class: type

    @classmethod
    def capture(cls, env, agent, opponent, obs, global_class):
        if set(vars(env)) != WRAPPER_FIELDS:
            raise ValueError('Lux wrapper attribute inventory changed; inspect step before continuing')
        cloned_env = copy.copy(env)
        a, o, g, observation = copy.deepcopy(
            (agent, opponent, global_attributes(global_class), obs), frozen_memo(agent))
        return cls(cloned_env, a, o, g, observation, rng_state(), global_class)

    def fork(self):
        a, o, g, observation = copy.deepcopy(
            (self.agent, self.opponent, self.globals, self.obs), frozen_memo(self.agent))
        return Snapshot(copy.copy(self.env), a, o, g, observation, copy.deepcopy(self.rng), self.global_class)

    @contextmanager
    def activate(self):
        # Restore live identities, not deepcopies, including additions/deletions.
        live_globals, live_rng = global_attributes(self.global_class), rng_state()
        try:
            install_globals(self.global_class, self.globals)
            restore_rng(self.rng)
            yield self
        finally:
            install_globals(self.global_class, live_globals)
            restore_rng(live_rng)


def eligible(ctx, uid, mask, proposal):
    ms, maximum = int(ctx['match_step']), int(ctx['max_match_steps'])
    if not 1 <= ms <= maximum or maximum - ms + 1 < HORIZON:
        return False
    if proposal not in (1, 2, 3, 4) or not mask[geo.STAY] or not mask[proposal]: return False
    ids = list(map(int, ctx['ally_ids']))
    if uid not in ids or ctx['ally_ene'][uid] < 0: return False
    p = tuple(map(int, ctx['ally_pos'][uid])); w, height = ctx['point_tiles'].shape
    if not (0 <= p[0] < w and 0 <= p[1] < height): return False
    target = ctx['assigned'].get(uid)
    if target is None or tuple(target) != p or not ctx['point_tiles'][p]: return False
    holders = [u for u in ids if ctx['ally_ene'][u] >= 0 and tuple(ctx['ally_pos'][u]) == p]
    if holders != [uid]: return False
    dest = p[0] + int(geo.DIR_DX[proposal]), p[1] + int(geo.DIR_DY[proposal])
    return bool(0 <= dest[0] < w and 0 <= dest[1] < height and not ctx['point_tiles'][dest])


@dataclass(frozen=True)
class Intervention:
    step: int
    uid: int
    proposal: int


class DiagnosticAgent(Agent_x):
    """A copied agent carries only data, never a closure pointing at live state."""
    def __init__(self, *args, head=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.training: raise ValueError('Diagnostic agent cannot train')
        if head is not None:
            from scripts.holder_learning import validate_head
            head = validate_head(head)
        self.head = head
        self.head_opportunities = 0
        self.last_opportunity_step = -HORIZON
        # Neither object is read by evaluation act. No mutable state is shared.
        self.buffer = None
        self.opt = None
        self.collect = False
        self.candidate = None
        self.intervention = None
        self.intervention_hits = 0
        for net in [self.q, self.target_q, *self.extra_q]: net.eval().requires_grad_(False)

    def update(self, *args, **kwargs):
        raise RuntimeError('Diagnostic agent cannot update')

    def new_game(self, player=None):
        super().new_game(player)
        self.head_opportunities = 0
        self.last_opportunity_step = -HORIZON

    def act(self, step, obs):
        self.candidate = None
        return super().act(step, obs)

    def _rule_override(self, ctx, uid, mask, a):
        head = getattr(self, 'head', None)
        if head is not None and self.intervention is not None:
            raise ValueError('Learned head and forced intervention cannot coexist')
        score = (head is not None and self.head_opportunities < 8
                 and int(ctx['step']) - self.last_opportunity_step >= HORIZON)
        valid = eligible(ctx, uid, mask, a) if self.collect or self.intervention or score else False
        if valid and ((self.collect and self.candidate is None) or score):
            # Keep this in the direct Agent_x._act caller: wrapping this hook
            # would hide its audited masked Q row and invalidate the check.
            caller = sys._getframe(1)
            try:
                if caller.f_code is not Agent_x._act.__code__ or caller.f_locals.get('self') is not self:
                    raise RuntimeError('Unrecognized action-stage caller')
                row = caller.f_locals['k']
                q = caller.f_locals['q'][row].copy()
            finally:
                del caller
            public = {k: _json(v) for k, v in ctx.items() if k in PUBLIC_FIELDS}
            public.update(assigned=_json(ctx['assigned']))
            candidate = dict(step=int(ctx['step']), uid=int(uid), proposal=int(a),
                             match_step=int(ctx['match_step']), q=[float(v) if np.isfinite(v) else None for v in q],
                             mask=_json(mask), features=_json(self._cache[3][uid]), public=public)
            if self.collect and self.candidate is None: self.candidate = candidate
            if score:
                # An attempted decision consumes the opportunity even on reject.
                self.head_opportunities += 1
                self.last_opportunity_step = int(ctx['step'])
                from scripts.holder_learning import predict_gain
                if predict_gain(head, candidate) > head['threshold']: a = geo.STAY
        order = self.intervention
        if order is not None and int(ctx['step']) == order.step and uid == order.uid:
            if not valid or a != order.proposal: raise RuntimeError('Intervention precondition mismatch')
            self.intervention_hits += 1
            a = geo.STAY
        return super()._rule_override(ctx, uid, mask, a)


def step_frame(env, agent, opponent, obs, side, step, *, actions=None, before=None, on_env_step=lambda: None):
    other = f'player_{1-int(side[-1])}'
    before_state, before_obs = before or (exact_digest(env.state), exact_digest(obs))
    if actions is None:
        actions = {side: agent.act(step, obs[side]), other: opponent.act(step, obs[other])}
    # The engine modifies the supplied action dictionary while tracing; archive
    # before env.step and give it an independent dictionary/array graph.
    saved_actions = {k: np.asarray(v).copy() for k, v in actions.items()}
    next_obs, _, terminated, truncated, info = env.step(copy.deepcopy(actions))
    on_env_step()
    points = match_points_after_step(obs[side], next_obs[side], info)
    delta = points - np.asarray(obs[side]['team_points'], dtype=np.int64)
    frame = dict(step=step, before_state=before_state, before_obs=before_obs,
                 actions=_json(saved_actions), action_sha256=hashlib.sha256(action_bytes(saved_actions)).hexdigest(),
                 after_state=exact_digest(env.state), after_obs=exact_digest(next_obs), points=_json(delta),
                 point_state=_json(points), done=bool(np.asarray(terminated[side])) or bool(np.asarray(truncated[side])))
    frame['sha256'] = exact_digest(frame)
    return next_obs, frame


def rollout(snapshot, side, step, intervention=None, *, guard=lambda: None, on_step=lambda: None):
    branch = snapshot.fork()
    branch.agent.collect = False
    branch.agent.intervention = intervention
    branch.agent.intervention_hits = 0
    frames, total = [], np.zeros(2, np.int64)
    with branch.activate():
        obs = branch.obs
        for offset in range(HORIZON):
            guard()
            if int(np.asarray(obs[side]['match_steps'])) == 0: raise RuntimeError('Rollout crossed a reset')
            obs, frame = step_frame(branch.env, branch.agent, branch.opponent, obs, side, step + offset, on_env_step=on_step)
            if branch.agent.caught_errors: raise RuntimeError('Caught agent error in rollout')
            total += frame['points']; frames.append(frame)
            if frame['done'] and offset != HORIZON - 1: raise RuntimeError('Premature terminal rollout')
        if branch.agent.intervention_hits != int(intervention is not None):
            raise RuntimeError('Intervention did not execute exactly once')
    team = int(side[-1])
    return dict(frames=frames, points=_json(total), point_differential=int(total[team] - total[1-team]),
                sha256=exact_digest(frames))


def paired_rollout(snapshot, side, step, candidate, *, verify=False, guard=lambda: None, on_step=lambda: None, on_technical_step=lambda: None):
    order = Intervention(step, candidate['uid'], candidate['proposal'])
    baseline = rollout(snapshot, side, step, guard=guard, on_step=on_step)
    hold = rollout(snapshot, side, step, order, guard=guard, on_step=on_step)
    checks = None
    if verify:
        # Reverse order, then repeat baseline: independent forks of pre-act graph.
        hold_again = rollout(snapshot, side, step, order, guard=guard, on_step=on_technical_step)
        baseline_again = rollout(snapshot, side, step, guard=guard, on_step=on_technical_step)
        checks = dict(hold_repeat=hold == hold_again, baseline_reverse_repeat=baseline == baseline_again)
        if not all(checks.values()): raise RuntimeError('Branch reverse/repeat failed')
    effective = baseline['frames'][0]['actions'][side] != hold['frames'][0]['actions'][side]
    if not effective and baseline != hold:
        raise RuntimeError('Identical first team actions produced divergent internal continuation')
    return dict(candidate=candidate, baseline=baseline, hold=hold,
                effective=effective,
                label=hold['point_differential'] - baseline['point_differential'], reverse_repeat=checks)
