"""Passive Sherlock targeting trace (six-action evaluation DQN only).

Run the predeclared keys sequentially, twice each, into a NEW directory::

    python -m scripts.targeting_probe --weights PATH --keys JSON --out DIR

The keys document has ``keys: [{seed, side, group}]`` and ``source`` naming the
original selection_baseline.csv. Only solution92 is supported. Each key produces
a streamed gzip JSONL trace, native action-byte SHA256s, v2 point totals and a
passivity record in manifest.json. Incomplete/mismatched runs fail closed. No
policy, weights or existing output is changed. Importing this module runs no games.

``classify_frame`` consumes canonical public context, masks by unit ID, float32
Q rows in ally_ids order and canonical final actions. Its ``posthoc`` object is
the only consumer of optional truth. BFS and a legal first step say nothing about
whole-route energy or safe arrival. Inline action provenance remains unresolved.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import inspect
import json
import math
import random
import struct
import subprocess
import sys
from collections import deque
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import torch

from agents.sherlock import geometry as geo

ROOT = Path(__file__).resolve().parent.parent
RULE_METHODS = ("_rule_override", "_path_fix", "_obey_target", "_soft_nebula",
                "_no_strand", "_fog_sap", "_artillery_ok", "_overkill")
PUBLIC_FIELDS = (
    "W", "H", "ally_ids", "ally_pos", "ally_ene", "enemy_coords",
    "enemy_energies", "enemy_vis_ids", "ally_count", "point_tiles", "candidate",
    "passable", "nebula", "energy_map", "explored", "point_coords", "cand_coords",
    "relic_coords", "unexp_coords", "move_cost", "sap_cost", "sap_range",
    "sensor_range", "step", "match_step", "match_idx", "own_points", "opp_points",
    "own_wins", "opp_wins", "max_match_steps", "config", "sensor_mask",
    "energy_observation_age", "nebula_estimate", "active_switches")


def _json(value):
    """Copy selected data into strict JSON values; never traverse agent objects."""
    if isinstance(value, np.ndarray):
        return _json(value.tolist())
    if isinstance(value, np.generic):
        return _json(value.item())
    if isinstance(value, dict):
        return {str(k): _json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json(v) for v in value]
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        return value if math.isfinite(value) else None
    if value is None or isinstance(value, (str, bool)):
        return value
    raise TypeError(f"Unsupported trace value: {type(value).__name__}")


def _distance_map(passable, target):
    """4-neighbour distance to a passable target; -1 means unreachable."""
    w, h = passable.shape
    distances = np.full((w, h), -1, np.int32)
    x, y = target
    if not (0 <= x < w and 0 <= y < h and passable[x, y]):
        return distances
    distances[x, y] = 0
    queue = deque([(x, y)])
    while queue:
        x, y = queue.popleft()
        for d in range(1, 5):
            nx, ny = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
            if 0 <= nx < w and 0 <= ny < h and passable[nx, ny] and distances[nx, ny] < 0:
                distances[nx, ny] = distances[x, y] + 1
                queue.append((nx, ny))
    return distances


def _path_info(distances, position, mask):
    x, y = position
    w, h = distances.shape
    if not (0 <= x < w and 0 <= y < h):
        return None, []
    dist = int(distances[x, y])
    # A current tile can have drifted into an asteroid. The agent may leave it;
    # shortest paths constrain entered tiles, not the unit's starting tile.
    if dist < 0:
        neighbours = [int(distances[nx, ny]) + 1 for d in range(1, 5)
                      for nx, ny in [(x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d]))]
                      if 0 <= nx < w and 0 <= ny < h and distances[nx, ny] >= 0]
        if neighbours:
            dist = min(neighbours)
    if dist < 0:
        return None, []
    progress = []
    for d in range(1, 5):
        nx, ny = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
        if (mask[d] and 0 <= nx < w and 0 <= ny < h
                and distances[nx, ny] >= 0 and distances[nx, ny] == dist - 1):
            progress.append(d)
    return dist, progress


def _mask_reasons(ctx, uid, mask):
    x, y = map(int, ctx["ally_pos"][uid])
    energy = float(ctx["ally_ene"][uid])
    w, h = int(ctx["W"]), int(ctx["H"])
    cfg = ctx.get("config", {})
    result = {}
    for d in np.flatnonzero(~mask):
        reasons = []
        if 1 <= d <= 4:
            nx, ny = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
            if energy < ctx["move_cost"]:
                reasons.append("below_move_cost")
            if not (0 <= nx < w and 0 <= ny < h):
                reasons.append("map_edge")
            elif not ctx["passable"][nx, ny]:
                reasons.append("memory_impassable")
            elif cfg.get("safe_moves", False):
                enemy = np.asarray(ctx["enemy_coords"]).reshape(-1, 2)
                here = np.all(enemy == (nx, ny), axis=1)
                if here.any() and np.asarray(ctx["enemy_energies"])[here].sum() >= energy - ctx["move_cost"]:
                    reasons.append("visible_enemy_energy")
        elif d == geo.SAP and energy < ctx["sap_cost"]:
            reasons.append("below_sap_cost")
        result[str(int(d))] = reasons or ["later_guard_unresolved"]
    return result


def _posthoc(truth, free_tiles, visible_enemies):
    if truth is None:
        return None
    positions = np.asarray(truth["enemy_positions"]).reshape(-1, 2)
    energies = np.asarray(truth["enemy_energy"]).reshape(-1)
    enemies = {tuple(map(int, p)) for p in positions}
    visible = {tuple(map(int, p)) for p in visible_enemies}
    tiles = np.asarray(truth["point_tiles"], bool)
    return dict(point_tiles=_json(tiles),
                enemies=[dict(position=_json(p), energy=float(e)) for p, e in zip(positions, energies)],
                free_own_tiles=[dict(position=t["position"], true_point=bool(tiles[tuple(t["position"])]),
                                     enemy_occupied=tuple(t["position"]) in enemies,
                                     hidden_enemy_occupied=(tuple(t["position"]) in enemies
                                                            and tuple(t["position"]) not in visible))
                                for t in free_tiles])


def classify_frame(ctx, masks, q_values, final_actions, truth=None) -> dict:
    """Pure canonical-space classifier; truth affects only the posthoc object."""
    ids = [int(u) for u in ctx["ally_ids"]]
    q = np.asarray(q_values, dtype=np.float32)
    if q.shape != (len(ids), 6):
        raise ValueError("Q matrix must have shape (len(ally_ids), 6)")
    actions = np.asarray(final_actions)
    passable = np.asarray(ctx["passable"], bool)
    points = np.asarray(ctx["point_tiles"], bool)
    w, h = points.shape
    assigned = {int(u): tuple(map(int, p)) for u, p in ctx["assigned"].items() if p is not None}
    positions = {u: tuple(map(int, ctx["ally_pos"][u])) for u in ids}
    energy = {u: float(ctx["ally_ene"][u]) for u in ids}
    occupancy = {}
    for u, p in positions.items():
        occupancy.setdefault(p, []).append(u)
    living_first = {p: min((u for u in us if energy[u] >= 0), default=None)
                    for p, us in occupancy.items()}
    maps = {}

    def path(u, target):
        if target not in maps:
            maps[target] = _distance_map(passable, target)
        return _path_info(maps[target], positions[u], np.asarray(masks[u], bool))

    units = []
    for row, u in enumerate(ids):
        p = positions[u]
        on_point = 0 <= p[0] < w and 0 <= p[1] < h and bool(points[p])
        holder = on_point and energy[u] >= 0 and living_first[p] == u
        living_stack_size = sum(energy[v] >= 0 for v in occupancy[p])
        sole = holder and living_stack_size == 1
        stacker = energy[u] >= 0 and living_stack_size > 1 and not holder
        mask = np.asarray(masks[u], bool)
        if mask.shape != (6,):
            raise ValueError("Each mask must contain six actions")
        target = assigned.get(u)
        dist, progress = path(u, target) if target is not None else (None, [])
        target_class = None
        if target is not None:
            tx, ty = target
            if 0 <= tx < w and 0 <= ty < h:
                target_class = ("known_point" if points[target] else
                                "candidate" if ctx["candidate"][target] else "exploration")
        ec = ("negative" if energy[u] < 0 else "below_move_cost" if energy[u] < ctx["move_cost"]
              else "below_sap_cost" if energy[u] < ctx["sap_cost"] else "sap_ready")
        units.append(dict(uid=u, position=list(p), energy=energy[u], energy_class=ec,
                          holder=bool(holder), sole_holder=bool(sole), stacker=bool(stacker),
                          stack_size=len(occupancy[p]), living_stack_size=living_stack_size,
                          legacy_first_on_tile=ctx.get("first_on_tile", {}).get(p) == u,
                          mobile_nonholder=bool(energy[u] >= ctx["move_cost"] and not holder),
                          assigned_target=_json(target), target_class=target_class,
                          target_half=None if target is None else ("own" if sum(target) <= w - 1 else "enemy"),
                          target_bfs_distance=dist, allowed_target_progress=progress,
                          q_values=_json(q[row]), mask=_json(mask), raw_argmax=int(q[row].argmax()),
                          masked_argmax=int(np.where(mask, q[row], -np.inf).argmax()),
                          final_action=_json(actions[u]), mask_reasons=_mask_reasons(ctx, u, mask),
                          provenance="inline_transitions_unresolved"))
    living = [u for u in ids if energy[u] >= 0]
    mobile = [unit["uid"] for unit in units if unit["mobile_nonholder"]]
    free_tiles = []
    visible = {tuple(map(int, p)) for p in ctx["enemy_coords"]}
    for tx, ty in np.argwhere(points):
        tile = (int(tx), int(ty))
        if sum(tile) > w - 1 or tile in occupancy:
            continue
        paths = {u: path(u, tile) for u in living}
        def minimum(group):
            distances = [paths[u][0] for u in group if paths[u][0] is not None]
            return min(distances) if distances else None
        free_tiles.append(dict(position=list(tile), visible_enemy=tile in visible,
                               assigned_units=[u for u in ids if assigned.get(u) == tile],
                               memory_passable=bool(passable[tile]), min_bfs_living=minimum(living),
                               min_bfs_mobile_nonholders=minimum(mobile),
                               allowed_first_progress_units=[u for u in mobile if paths[u][1]],
                               competing_targets=[dict(uid=u, target=_json(assigned.get(u)),
                                                       bfs_distance=units[k]["target_bfs_distance"])
                                                  for k, u in enumerate(ids) if assigned.get(u) != tile]))
    cfg = ctx.get("config")
    required_costs = ("home_first", "home_penalty", "energy_pref", "sticky")
    admitted = (cfg is not None and cfg.get("reach_assign") is True
                and all(k in cfg and not cfg[k] for k in required_costs))
    swap = dict(admitted=admitted, reason=("same_target_set_bfs_only" if admitted
                                           else "missing_or_incompatible_cost_config"),
                pairs_checked=0, improvements=[])
    if admitted:
        eligible = [u for u in mobile if u in assigned and sum(assigned[u]) <= w - 1
                    and 0 <= assigned[u][0] < w and 0 <= assigned[u][1] < h and points[assigned[u]]]
        for i, u in enumerate(eligible):
            for v in eligible[i + 1:]:
                if swap["pairs_checked"] >= 120:
                    break
                swap["pairs_checked"] += 1
                tu, tv = assigned[u], assigned[v]
                if tu == tv:
                    continue
                alternatives = [path(u, tu), path(v, tv), path(u, tv), path(v, tu)]
                if any(d is None or not progress for d, progress in alternatives):
                    continue
                old = alternatives[0][0] + alternatives[1][0]
                new = alternatives[2][0] + alternatives[3][0]
                if new < old:
                    swap["improvements"].append(dict(units=[u, v], old_targets=[list(tu), list(tv)],
                                                       new_targets=[list(tv), list(tu)], old_bfs_sum=old,
                                                       new_bfs_sum=new, saved_bfs=old - new))
    public = {k: _json(ctx[k]) for k in PUBLIC_FIELDS if k in ctx}
    public["assigned"] = _json(assigned)
    public["first_on_tile"] = [dict(position=list(p), uid=int(u))
                                for p, u in ctx.get("first_on_tile", {}).items()]
    return dict(status="decision", public=public, units=units, free_own_tiles=free_tiles,
                two_owner_swap=swap, posthoc=_posthoc(truth, free_tiles, ctx["enemy_coords"]))


def canonical_actions(actions, mirrored):
    """Copy native actions; antidiagonal reflection is its own inverse."""
    out = np.asarray(actions).copy()
    if mirrored:
        for row in out:
            if row[0] == geo.SAP:
                row[1], row[2] = geo.mirror_delta(row[1], row[2])
            else:
                row[0] = geo.mirror_dir(row[0])
    return out


class DecisionObserver:
    """Temporarily wrap an existing act call; do not call any decision method."""

    def __init__(self, agent):
        self.agent = agent
        self.last_frame = None
        self.events = []
        self._handles = []
        self._originals = {}
        self._outputs = []
        self._free_since = {}
        self._energy_seen = None
        self._last_match = None

    def _install(self, name, function):
        self._originals[name] = (name in self.agent.__dict__, self.agent.__dict__.get(name))
        setattr(self.agent, name, function)

    def __enter__(self):
        a = self.agent
        if a.training or a.n_actions != 6 or a.cnn_policy is not None:
            raise ValueError("Observer requires evaluation DQN, six actions and no CNN policy")
        if self._originals or self._handles:
            raise RuntimeError("Observer already installed")
        try:
            for index, net in enumerate([a.q] + list(a.extra_q)):
                def capture(module, inputs, output, _index=index):
                    self._outputs.append((_index, output.detach().clone()))
                self._handles.append(net.register_forward_hook(capture))
            for name in RULE_METHODS:
                original = getattr(a, name)
                signature = inspect.signature(original)
                def wrapper(*args, _original=original, _signature=signature, _name=name, **kwargs):
                    bound = _signature.bind(*args, **kwargs).arguments
                    ctx, uid = bound["ctx"], int(bound["uid"])
                    caller_action = None
                    caller = sys._getframe(1)
                    try:
                        # Read the actual inline action only from this agent's
                        # exact _act frame. Never infer it from network argmax.
                        code = getattr(getattr(a._act, "__func__", None), "__code__", None)
                        local = caller.f_locals
                        if (caller.f_code is code and local.get("self") is a
                                and local.get("uid") == uid and "a" in local):
                            caller_action = int(local["a"])
                    finally:
                        del caller
                        del local
                    event = dict(order=len(self.events), method=_name, uid=uid,
                                 caller_action=caller_action,
                                 caller_action_status="observed" if caller_action is not None else "unresolved",
                                 arguments={k: _json(v) for k, v in bound.items() if k not in ("ctx", "uid")},
                                 unit_context=dict(position=_json(ctx["ally_pos"][uid]),
                                                   energy=float(ctx["ally_ene"][uid]),
                                                   target=_json(ctx["assigned"].get(uid))),
                                 return_status="pending")
                    self.events.append(event)
                    try:
                        result = _original(*args, **kwargs)
                    except BaseException as exc:
                        event.update(return_status="error", error=type(exc).__name__)
                        raise
                    event.update(return_status="returned", **{"return": _json(result)})
                    event["arguments_after"] = {k: _json(v) for k, v in bound.items() if k not in ("ctx", "uid")}
                    return result
                self._install(name, wrapper)
            original_act = a.act
            def act(*args, **kwargs):
                bound = inspect.signature(original_act).bind(*args, **kwargs).arguments
                obs = bound["obs"]
                self.events = []
                self._outputs = []
                self.last_frame = None
                actions = original_act(*args, **kwargs)
                self.last_frame = self._frame(obs, actions)
                return actions
            self._install("act", act)
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, exc_type, exc, tb):
        for handle in self._handles:
            handle.remove()
        self._handles.clear()
        for name, (existed, value) in reversed(list(self._originals.items())):
            if existed:
                setattr(self.agent, name, value)
            else:
                delattr(self.agent, name)
        self._originals.clear()
        self._outputs = []
        return False

    def _frame(self, obs, actions):
        a = self.agent
        sid = int(np.asarray(obs["steps"]))
        ms = int(np.asarray(obs["match_steps"]))
        mi = int(a.belief.match_idx)
        key = dict(obs_step=sid, match_step=ms, match_idx=mi)
        native = _json(actions)
        if ms == 0:
            self._free_since.clear()
            self._last_match = mi
            return dict(status="reset", key=key, units=[], events=self.events,
                        native_actions=native, posthoc=None)
        cache = getattr(a, "_cache", None)
        if cache is None:
            return dict(status="missing_cache", key=key, units=[], events=self.events,
                        native_actions=native, posthoc=None)
        cache_sid, ctx, ids, feats, masks, saps = cache
        if (cache_sid != sid or ctx["step"] != sid or ctx["match_step"] != ms
                or ctx["match_idx"] != mi or list(ids) != list(ctx["ally_ids"])):
            return dict(status="cache_mismatch", key=key, units=[], events=self.events,
                        native_actions=native, posthoc=None)
        if not ids:
            q = np.empty((0, 6), np.float32)
        elif ([index for index, _ in self._outputs] != list(range(1 + len(a.extra_q)))
              or any(output.shape != (len(ids), 6) or output.dtype != torch.float32
                     for _, output in self._outputs)):
            return dict(status="q_capture_mismatch", key=key, units=[], events=self.events,
                        native_actions=native, posthoc=None)
        else:
            tensors = [output for _, output in self._outputs]
            q = (torch.stack(tensors).mean(dim=0) if a.extra_q else tensors[0]).cpu().numpy()
        # Shallow dictionary plus selective copied arrays; never copy belief/agent.
        copied = {k: v.copy() if isinstance(v, np.ndarray) else v for k, v in ctx.items() if k in PUBLIC_FIELDS}
        copied["assigned"] = dict(ctx["assigned"])
        copied["first_on_tile"] = dict(ctx["first_on_tile"])
        copied["config"] = {k: v for k, v in vars(a.cfg).items() if isinstance(v, (str, int, float, bool)) or v is None}
        copied["active_switches"] = {k: v for k, v in copied["config"].items() if isinstance(v, bool) and v}
        # Derive a descriptive posterior from copied public observation history;
        # no extra call into the agent/estimator or mutation of its counters.
        from agents.sherlock.param_est import NEBULA_REDUCTIONS
        logp = a.param_est.log_neb.copy()
        posterior = np.exp(logp - logp.max())
        posterior /= posterior.sum()
        best = int(posterior.argmax())
        samples = int(a.param_est.n_neb)
        copied["nebula_estimate"] = dict(value=NEBULA_REDUCTIONS[best] if samples and posterior[best] >= .9 else None,
                                          confidence=float(posterior[best]), samples=samples,
                                          log_likelihood=_json(logp))
        sensor = np.asarray(obs["sensor_mask"], bool).copy()
        if a.belief.mirrored:
            sensor = geo.mirror_map(sensor)
        if self._energy_seen is None or self._energy_seen.shape != sensor.shape:
            self._energy_seen = np.full(sensor.shape, -1, np.int64)
        self._energy_seen[sensor] = sid
        ages = np.empty(sensor.shape, object)
        ages[:] = None
        seen = self._energy_seen >= 0
        ages[seen] = sid - self._energy_seen[seen]
        copied.update(sensor_mask=sensor, energy_observation_age=ages)
        canonical = canonical_actions(actions, a.belief.mirrored)
        frame = classify_frame(copied, masks, q, canonical)
        frame.update(key=key, native_actions=native, events=self.events,
                     provenance="wrapped_methods_observed_inline_transitions_unresolved")
        for unit in frame["units"]:
            u = unit["uid"]
            unit.update(features=_json(feats[u]), native_action=_json(actions[u]), sap_target=_json(saps.get(u)))
        if self._last_match != mi:
            self._free_since.clear()
        self._last_match = mi
        current = {tuple(t["position"]) for t in frame["free_own_tiles"]}
        self._free_since = {p: start for p, start in self._free_since.items() if p in current}
        for tile in frame["free_own_tiles"]:
            start = self._free_since.setdefault(tuple(tile["position"]), ms)
            tile["free_duration"] = ms - start + 1
        return frame


def action_bytes(actions):
    """Unmodified native array bytes, with unambiguous player/shape/dtype header."""
    chunks = []
    for side in sorted(actions):
        arr = np.asarray(actions[side])
        header = json.dumps(dict(side=side, shape=list(arr.shape), dtype=arr.dtype.str), sort_keys=True).encode()
        data = arr.tobytes(order="C")
        chunks.extend((struct.pack("!Q", len(header)), header, struct.pack("!Q", len(data)), data))
    return b"".join(chunks)


def _truth(state, team, mirrored):
    from scripts.scoring import point_tile_map
    pos = np.asarray(state.units.position).copy()
    energy = np.asarray(state.units.energy)[..., 0].copy()
    mask = np.asarray(state.units_mask, bool).copy()
    valid = mask[1 - team] & (pos[1 - team, :, 0] >= 0) & (pos[1 - team, :, 1] >= 0)
    enemy_positions = pos[1 - team, valid]
    points = point_tile_map(state)
    asteroid = np.asarray(state.map_features.tile_type) == 2
    if mirrored:
        enemy_positions = geo.mirror_positions(enemy_positions, *points.shape)
        pos = geo.mirror_positions(pos, *points.shape)
        points, asteroid = geo.mirror_map(points), geo.mirror_map(asteroid)
    return dict(point_tiles=points, enemy_positions=enemy_positions, enemy_energy=energy[1 - team, valid],
                positions=pos, energy=energy, unit_mask=mask, asteroid=asteroid,
                match_step=int(np.asarray(state.match_steps)))


def _play(seed, side, weights, trace_path=None):
    """One full real game; own and opposing action streams are both hashed."""
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent
    from scripts.par_eval import build_cfg
    from scripts.scoring import POINT_COUNTING_VERSION, match_points_after_step

    agent = Agent_x("player_0", agent_path=str(weights), cfg=build_cfg(str(weights), []), train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    team = int(side[-1])
    other = f"player_{1 - team}"
    opponent = make_opponent("solution92", other)
    agent.new_game(side)
    random.seed(seed)
    np.random.seed(seed % 2**32)
    env = LuxAIS3GymEnv(numpy_output=True)
    digest = hashlib.sha256()
    steps, resets = 0, 0
    totals = np.zeros(2, np.int64)
    matches, statuses = [], {}
    try:
        obs, info = env.reset(seed=seed)
        agent.set_env_cfg(info["params"])
        opponent.set_env_cfg(info["params"])
        cfg = _json(vars(agent.cfg))
        manager = DecisionObserver(agent) if trace_path is not None else nullcontext()
        stream = gzip.open(trace_path, "xt", encoding="utf-8") if trace_path is not None else nullcontext()
        with manager as observer, stream as output:
            while True:
                actions = {side: agent.act(steps, obs[side]), other: opponent.act(steps, obs[other])}
                digest.update(action_bytes(actions))
                # Truth is read only after both policies chose their actions.
                before = _truth(env.state, team, agent.belief.mirrored) if observer else None
                next_obs, _, terminated, truncated, info = env.step(actions)
                points = match_points_after_step(obs[side], next_obs[side], info)
                totals += points - np.asarray(obs[side]["team_points"])
                done = bool(np.asarray(terminated[side])) or bool(np.asarray(truncated[side]))
                is_reset = int(np.asarray(obs[side]["match_steps"])) == 0
                resets += int(is_reset)
                if int(np.asarray(next_obs[side]["match_steps"])) == 0 or done:
                    matches.append(dict(match_idx=len(matches), points=_json(points),
                                        cumulative_wins=_json(next_obs[side]["team_wins"])))
                if observer:
                    frame = observer.last_frame
                    frame["key"].update(seed=seed, side=side)
                    after = _truth(env.state, team, agent.belief.mirrored)
                    posthoc = _posthoc(before, frame.get("free_own_tiles", []),
                                       frame.get("public", {}).get("enemy_coords", []))
                    posthoc.update(before=_json(before), after=_json(after),
                                   transition_status=("reset" if is_reset or after["match_step"] == 0
                                                      else "unit_identity_continuity_unresolved"),
                                   energy_phase_reconstruction=None)
                    frame["posthoc"] = posthoc
                    output.write(json.dumps(frame, allow_nan=False, separators=(",", ":")) + "\n")
                    statuses[frame["status"]] = statuses.get(frame["status"], 0) + 1
                steps += 1
                obs = next_obs
                if done:
                    break
        wins = np.asarray(obs[side]["team_wins"]).astype(int)
        return dict(seed=seed, side=side, opponent="solution92", steps=steps, reset_steps=resets,
                    decision_steps=steps-resets, our_wins=int(wins[team]), opp_wins=int(wins[1-team]),
                    result=1.0 if wins[team] > wins[1-team] else 0.0 if wins[team] < wins[1-team] else 0.5,
                    our_points=int(totals[team]), opp_points=int(totals[1-team]),
                    point_counting_version=POINT_COUNTING_VERSION, matches=matches,
                    action_sha256=digest.hexdigest(), statuses=statuses, config=cfg,
                    caught_errors=int(agent.caught_errors))
    finally:
        env.close()


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _baseline(keys_document):
    source = Path(keys_document["source"])
    source = source if source.is_absolute() else ROOT / source
    with source.open(newline="") as f:
        rows = {(int(r["seed"]), r["side"]): r for r in csv.DictReader(f) if r["opponent"] == "solution92"}
    return source, rows


def run_probe(weights, keys_path, out):
    """Validate all inputs before creating output or starting the first game."""
    weights, keys_path, out = Path(weights), Path(keys_path), Path(out)
    if out.exists():
        raise FileExistsError(out)
    if not weights.is_file():
        raise FileNotFoundError(weights)
    document = json.loads(keys_path.read_text())
    keys = document["keys"]
    if not keys or len({(k["seed"], k["side"]) for k in keys}) != len(keys):
        raise ValueError("Keys must be nonempty and unique")
    source, baseline = _baseline(document)
    for key in keys:
        if (key["side"] not in ("player_0", "player_1") or not isinstance(key["seed"], int)
                or not key.get("group") or key.get("opponent", "solution92") != "solution92"):
            raise ValueError("Expected seed/side/group keys for solution92 only")
        if (key["seed"], key["side"]) not in baseline:
            raise ValueError("Key absent from the original solution92 baseline")
    from scripts.experiment import limit_threads
    limit_threads()
    files = [ROOT / p for p in ("scripts/targeting_probe.py", "scripts/common.py", "scripts/scoring.py")]
    files += sorted((ROOT / "agents/sherlock").glob("*.py"))
    files += sorted((ROOT / "agents/Solution_92_Kaggle").glob("*.py"))
    import luxai_s3.env
    files.append(Path(luxai_s3.env.__file__))
    manifest = dict(schema_version=1, status="running", keys=keys,
                    weights=dict(path=str(weights.resolve()), sha256=_sha(weights)),
                    keys_sha256=_sha(keys_path), baseline=dict(path=str(source), sha256=_sha(source)),
                    sources={str(p): _sha(p) for p in files},
                    git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                    planned_games=2*len(keys), completed_games=0, games=[],
                    limitations=["inline action transitions unresolved", "no full route energy guarantee",
                                 "no reconstructed energy phases", "unit identity continuity unresolved",
                                 "selected qualitative keys are not prevalence estimates"])
    out.mkdir(parents=True, exist_ok=False)
    def save():
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    save()
    try:
        for key in keys:
            seed, side = key["seed"], key["side"]
            trace_path = out / f"{seed}_{side}.jsonl.gz"
            unobserved = _play(seed, side, weights)
            manifest["completed_games"] += 1
            manifest["games"].append(dict(key=key, unobserved=unobserved))
            save()
            observed = _play(seed, side, weights, trace_path)
            manifest["completed_games"] += 1
            record = manifest["games"][-1]
            record.update(observed=observed, trace=dict(path=trace_path.name, sha256=_sha(trace_path)))
            compared = ("action_sha256", "steps", "reset_steps", "decision_steps", "our_wins", "opp_wins",
                        "result", "our_points", "opp_points", "point_counting_version", "matches", "config", "caught_errors")
            record["passivity"] = {k: unobserved[k] == observed[k] for k in compared}
            original = baseline[seed, side]
            fields = ("result", "our_wins", "opp_wins", "our_points", "opp_points", "point_counting_version", "steps")
            record["baseline_reproduction"] = {k: observed[k] == float(original[k]) for k in fields}
            record["complete"] = (observed["steps"] == 303 and observed["reset_steps"] == 3
                                  and len(observed["matches"]) == 3 and observed["caught_errors"] == 0
                                  and set(observed["statuses"]) <= {"decision", "reset"})
            save()
            if (not all(record["passivity"].values()) or not all(record["baseline_reproduction"].values())
                    or not record["complete"]):
                raise RuntimeError(f"Passivity/completeness/baseline gate failed for {seed}/{side}")
        if _sha(weights) != manifest["weights"]["sha256"] or any(_sha(p) != digest for p, digest in manifest["sources"].items()):
            raise RuntimeError("Source or weights changed during the run")
        manifest["status"] = "complete"
        save()
    except BaseException as exc:
        manifest.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        save()
        raise
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--keys", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    run_probe(args.weights, args.keys, args.out)


if __name__ == "__main__":
    main()
