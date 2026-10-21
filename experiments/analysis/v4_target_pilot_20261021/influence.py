"""Stage 1 only: bounded legal target changes through ordinary final V3 act.

No learner, simulator fork, update/save call, or opponent call belongs here.
"""
from __future__ import annotations

from collections import deque
from contextlib import contextmanager
import copy
import hashlib
import pickle
from pathlib import Path
import random

import numpy as np
import torch

from agents.sherlock.features import FEATURE_NAMES, build_features

SHARED_FIELDS = ('q', 'target_q', 'extra_q', 'opt', 'buffer')
ASSIGNED = [FEATURE_NAMES.index('assigned_' + s) for s in ('dx', 'dy', 'dist', 'exists')]


def bounded_paths(passable, start):
    """Known raster BFS, at most six moves, UP RIGHT DOWN LEFT route ties."""
    width, height = passable.shape
    start = tuple(map(int, start))
    if not (0 <= start[0] < width and 0 <= start[1] < height):
        return {}
    paths = {start: []}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        path = paths[(x, y)]
        if len(path) == 6:
            continue
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            tile = x + dx, y + dy
            if (0 <= tile[0] < width and 0 <= tile[1] < height
                    and bool(passable[tile]) and tile not in paths):
                paths[tile] = path + [tile]
                queue.append(tile)
    return paths


def select_choices(ctx):
    """Return all eligible unit choices and the fixed farthest-baseline choice."""
    width, height = ctx['W'], ctx['H']
    valid_pos = lambda p: bool(np.isfinite(p).all() and 0 <= p[0] < width
                               and 0 <= p[1] < height)
    occupied = {tuple(map(int, ctx['ally_pos'][u])) for u in ctx['ally_ids']
                if ctx['ally_ene'][u] >= 0 and valid_pos(ctx['ally_pos'][u])}
    points = [tuple(map(int, t)) for t in np.argwhere(ctx['point_tiles'] & ctx['passable'])]
    choices = []
    for uid in sorted(map(int, ctx['ally_ids'])):
        pos = ctx['ally_pos'][uid]
        baseline = ctx['assigned'].get(uid)
        if (not valid_pos(pos) or not np.isfinite(ctx['ally_ene'][uid])
                or ctx['ally_ene'][uid] < ctx['move_cost'] or baseline is None):
            continue
        start, baseline = tuple(map(int, pos)), tuple(map(int, baseline))
        if (ctx['point_tiles'][start] or not valid_pos(np.asarray(baseline))
                or not ctx['point_tiles'][baseline]):
            continue
        assigned_elsewhere = {tuple(t) for u, t in ctx['assigned'].items() if u != uid}
        paths = bounded_paths(ctx['passable'], start)
        alternatives = sorted((len(paths[t]), t) for t in points
                              if t != baseline and t not in occupied
                              and t not in assigned_elsewhere and t in paths)[:3]
        if alternatives:
            choices.append(dict(uid=uid, position=list(start), baseline_target=list(baseline),
                                baseline_manhattan=sum(abs(a-b) for a, b in zip(start, baseline)),
                                alternatives=[dict(target=list(t), distance=d)
                                              for d, t in alternatives]))
    selected = min(choices, key=lambda c: (-c['baseline_manhattan'], c['uid'])) if choices else None
    return choices, selected


def validate_agent(agent):
    if (agent.training or agent.cfg.joint_moves or agent.cnn_policy is not None
            or not agent.cfg.use_belief or len(agent.buffer)):
        raise ValueError('probe requires eval V3, belief features, no joint/CNN, empty buffer')
    if any(module.training for module in [agent.q, agent.target_q, *agent.extra_q]):
        raise ValueError('shared networks must already be in evaluation mode')


def clone_agent(agent):
    validate_agent(agent)
    memo = {id(getattr(agent, name)): getattr(agent, name) for name in SHARED_FIELDS}
    # A single graph copy retains belief/feature/context/cache aliases and Generator state.
    return copy.deepcopy(agent, memo)


def capture_rng():
    return random.getstate(), np.random.get_state(), torch.get_rng_state().clone()


def restore_rng(state):
    random.setstate(state[0])
    np.random.set_state(state[1])
    torch.set_rng_state(state[2])


def value_digest(value):
    """Hash values, dtype/shape and object aliases; never include tensor storage IDs."""
    seen = {}
    def pack(v):
        if v is None or isinstance(v, (bool, int, float, str, bytes)):
            return v
        identity = id(v)
        if identity in seen:
            return ('ref', seen[identity])
        seen[identity] = len(seen)
        if isinstance(v, np.ndarray):
            return ('array', v.dtype.str, v.shape, v.tobytes())
        if isinstance(v, torch.Tensor):
            return ('tensor', str(v.dtype), tuple(v.shape), v.detach().cpu().numpy().tobytes())
        if isinstance(v, np.generic):
            return ('scalar', v.dtype.str, v.tobytes())
        if isinstance(v, dict):
            return ('dict', [(pack(k), pack(x)) for k, x in v.items()])
        if isinstance(v, (tuple, list)):
            return (type(v).__name__, [pack(x) for x in v])
        if isinstance(v, (set, frozenset)):
            return (type(v).__name__, sorted((pickle.dumps(x) for x in v)))
        if isinstance(v, np.random.Generator):
            return ('generator', pack(v.bit_generator.state))
        if hasattr(v, '__dict__'):
            return (type(v).__module__, type(v).__qualname__, pack(vars(v)))
        return ('pickle', pickle.dumps(v, protocol=5))
    return hashlib.sha256(pickle.dumps(pack(value), protocol=5)).hexdigest()


def dynamic_digest(agent):
    return value_digest({k: v for k, v in vars(agent).items() if k not in SHARED_FIELDS})


def rng_digest(state=None):
    return value_digest(capture_rng() if state is None else state)


def shadow_action(pre, obs, step, uid, target, initial_rng, *, live):
    """Run actual act once on a fresh pre-act clone and restore globals in finally.

    The live agent and legal input are digested even when clone preparation or
    final act raises. No environment/opponent references enter this function.
    """
    saved_rng = capture_rng()
    before_live, before_obs = dynamic_digest(live), value_digest(obs)
    try:
        restore_rng(initial_rng)
        shadow, shadow_obs = clone_agent(pre), copy.deepcopy(obs)
        if target is not None:
            shadow.belief.observe(shadow_obs)
            ctx, ids, feats, masks, saps = shadow._decide(shadow_obs)
            if uid not in ids or not bool(ctx['passable'][tuple(target)]):
                raise ValueError('invalid or blocked target intervention')
            previous = feats[uid].copy()
            ctx['assigned'][uid] = tuple(map(int, target))
            rebuilt = build_features(ctx, uid)
            unaffected = np.ones(len(previous), bool)
            unaffected[ASSIGNED] = False
            if not np.array_equal(previous[unaffected], rebuilt[unaffected]):
                raise AssertionError('target change affected unrelated features')
            feats[uid] = rebuilt  # _decide's cached dict: ordinary act sees the new features.
            shadow._cache = (int(np.asarray(shadow_obs['steps'])), ctx, ids, feats, masks, saps)
        return np.asarray(shadow.act(step=step, obs=shadow_obs)).copy()
    finally:
        restore_rng(saved_rng)
        if dynamic_digest(live) != before_live or value_digest(obs) != before_obs:
            raise AssertionError('shadow mutated live dynamic state or legal observation')


class InfluenceAgent:
    """Delegates every live action unchanged; passive shadows only at eight times."""
    def __init__(self, agent):
        validate_agent(agent)
        self.agent = agent
        self.records = []

    def __getattr__(self, name):
        return getattr(self.agent, name)

    def act(self, step, obs):
        match_idx = int(np.asarray(obs['steps'])) // 101
        match_step = int(np.asarray(obs['match_steps']))
        if match_idx not in (1, 2) or match_step not in (25, 45, 65, 85):
            return self.agent.act(step=step, obs=obs)
        pre, initial_rng = clone_agent(self.agent), capture_rng()
        baseline = self.agent.act(step=step, obs=obs)
        # Selection uses the context that really produced the live baseline action.
        ctx = self.agent._cache[1]
        choices, selected = select_choices(ctx)
        replay = shadow_action(pre, obs, step, None, None, initial_rng, live=self.agent)
        if not np.array_equal(replay, baseline):
            raise AssertionError('pre-act shadow baseline does not reproduce complete action')
        record = dict(step=step, match_idx=match_idx, match_step=match_step,
                      available_choices=choices, selected_unit=selected['uid'] if selected else None,
                      baseline_target=selected['baseline_target'] if selected else None,
                      baseline_actions=baseline.tolist(), alternatives=[], distinct_changed_arrays=0)
        distinct = set()
        if selected:
            uid = selected['uid']
            for alternative in selected['alternatives']:
                action = shadow_action(pre, obs, step, uid, tuple(alternative['target']),
                                       initial_rng, live=self.agent)
                changed = np.flatnonzero(np.any(action != baseline, axis=1)).tolist()
                if changed:
                    distinct.add(action.tobytes())
                record['alternatives'].append(dict(
                    **alternative, actions=action.tolist(), changed_units=changed,
                    other_units_changed=[u for u in changed if u != uid]))
        record['distinct_changed_arrays'] = len(distinct)
        self.records.append(record)
        return baseline


class TraceAgent:
    """Record only incoming legal observations and complete returned action arrays."""
    def __init__(self, agent):
        self.agent, self.trace = agent, []

    def __getattr__(self, name):
        return getattr(self.agent, name)

    def act(self, step, obs):
        observation = value_digest(obs)
        actions = self.agent.act(step=step, obs=obs)
        self.trace.append(dict(step=step, observation=observation,
                               action_digest=value_digest(actions), actions=actions.tolist()))
        return actions


def assert_same_game(control, shadow):
    if control['traces'] != shadow['traces']:
        raise AssertionError('complete actions or legal observation trajectory differs')
    def non_time(summary):
        # Normalize NaNs without dropping any fields other than elapsed wall time.
        return {k: ('NaN' if isinstance(v, float) and np.isnan(v) else v)
                for k, v in summary.items() if k != 'secs'}
    if non_time(control['summary']) != non_time(shadow['summary']):
        raise AssertionError('non-time game summary differs')


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


@contextmanager
def protect_files(paths):
    before = {str(Path(p).resolve()): file_hash(p) for p in paths}
    try:
        yield before
    finally:
        changed = [p for p, digest in before.items() if not Path(p).is_file() or file_hash(p) != digest]
        if changed:
            raise RuntimeError('protected weights changed: ' + ', '.join(changed))


def fresh_output(path):
    Path(path).mkdir(parents=True, exist_ok=False)


def check_data_budget(path, limit=128 * 1024 * 1024):
    if sum(p.stat().st_size for p in Path(path).rglob('*') if p.is_file()) > limit:
        raise RuntimeError('data budget exceeded')
