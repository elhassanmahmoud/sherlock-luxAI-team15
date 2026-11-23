"""Public fleet history, static projections, and legal small search routes."""
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.routenlernen.routes import (
    DIRECTIONS, DX, DY, MIRROR_DIR, STEPS, TRAIL_X, TRAIL_Y, near_enemies,
)

HERE = Path(__file__).resolve().parent
W = 24
X, Y = np.indices((W, W), dtype=np.int16)
XY = np.column_stack((X.ravel(), Y.ravel()))
GAP = np.max(np.abs(XY[:, None] - XY), axis=2).astype(np.int8)
POWER = (GAP <= 1).astype(np.int8) + 11 * (GAP == 0).astype(np.int8)
PAIR = np.minimum(np.arange(576), (23 - XY[:, 1])*24 + 23 - XY[:, 0])
CHANNELS = ("rest_now", "rest_next", "rest_t2", "rest_t5", "rest_t8", "steady", "up", "right", "down", "left",
            "low_energy", "prior_targets", "scout_here", "straight", "distance_here", "distance_next",
            "distance_straight", "walls", "nebula", "tile_energy", "seen_age", "current_sight",
            "home_distance", "spawn_soon", "turn", "rest_count")
PROJECTIONS = ("now", "next", "straight")


def flat(pos):
    return pos[..., 0] * W + pos[..., 1]


def paint(positions, weights=None):
    out = np.zeros(576, dtype=np.float32)
    if len(positions):
        np.add.at(out, flat(positions), 1 if weights is None else weights)
    return np.minimum(out, 3).reshape(W, W)/3


def distance(indices):
    return GAP[np.asarray(indices)].min(0).reshape(W, W) if len(indices) else np.full((W, W), 24)


class History:
    def __init__(self):
        self.stays = np.zeros(16, dtype=np.int16)
        self.track = np.full((9, 16, 2), -1, dtype=np.int16)
        self.last_seen = np.full((W, W), -1, dtype=np.int16)
        self.prev = np.full((16, 2), -1, dtype=np.int16)
        self.finished = False

    def observe(self, step, obs, team):
        if np.any(obs["relic_nodes_mask"]) or obs["team_points"][team] > 0:
            self.finished = True
        mask = np.asarray(obs["sensor_mask"], bool)
        self.last_seen[mask[::-1, ::-1].T if team else mask] = step

    def proposals(self, state, original, team):
        self.track[1:] = self.track[:-1]
        self.track[0].fill(-1)
        if state is None:
            self.stays.fill(0)
            self.prev.fill(-1)
            return
        ctx, ids, _, _, _, _, pos = state
        ids = np.asarray(ids, int)
        energy = np.asarray(ctx["ally_ene"])[ids]
        live = energy >= 0
        alive = ids[live]
        self.track[0, alive] = pos[live]
        same = np.all(self.prev == self.track[0], axis=1)
        stay = (original[:, 0] == 0) & (self.track[0, :, 0] >= 0)
        self.stays = np.where(stay, np.where(same, self.stays + 1, 1), 0).astype(np.int16)
        self.prev[:] = self.track[0]


def option_frame(state, original, history, team, fixed=None):
    if state is None:
        return None
    ctx, ids, _, masks, _, _, pos = state
    ids = np.asarray(ids, int)
    ene = np.asarray(ctx["ally_ene"])[ids]
    live = ene >= 0
    if live.sum() < 2:
        return None
    native = original[ids, 0]
    canon = np.where(native <= 4, native, 0)
    if team:
        canon = MIRROR_DIR[canon]
    projected = pos + np.column_stack((DX[canon], DY[canon]))
    if fixed is None:
        eligible = np.flatnonzero((native == 0) & (history.stays[ids] >= 4))
        rows = sorted(eligible, key=lambda i: (-history.stays[ids[i]], -ene[i], ids[i]))
    else:
        rows = np.flatnonzero(ids == fixed)
    for k in rows:
        uid, now = int(ids[k]), tuple(pos[k])
        own_task = ctx["assigned"].get(uid)
        if (ene[k] < max(45, 8 * ctx["move_cost"]) or native[k] > 4 or near_enemies(pos[k], ctx)
                or ctx["point_tiles"][now] or ctx["candidate"][now]
                or ctx["point_tiles"][tuple(projected[k])] or ctx["candidate"][tuple(projected[k])]
                or (own_task is not None and (ctx["point_tiles"][own_task] or ctx["candidate"][own_task]))):
            continue
        rest = live & (ids != uid)
        first = masks[k, :5].copy()
        for d in (1, 2, 3, 4):
            q = pos[k] + [DX[d], DY[d]]
            if (not first[d] or np.any(q < 0) or np.any(q >= W)
                    or np.any(np.all(projected[rest] == q, axis=1)) or not ctx["passable"][tuple(q)]
                    or near_enemies(q, ctx) or ctx["point_tiles"][tuple(q)] or ctx["candidate"][tuple(q)]):
                first[d] = False
        if np.count_nonzero(first[1:]) < (1 if fixed is not None else 2):
            continue
        return dict(uid=uid, start=pos[k], energy=ene[k], original=int(canon[k]), first=first, ctx=ctx,
                    rest=pos[rest], next=projected[rest], directions=canon[rest], rest_ids=ids[rest],
                    rest_energy=ene[rest])
    return None


def support(frame):
    x, y = frame["start"]
    tx, ty = x + TRAIL_X, y + TRAIL_Y
    inside = (tx >= 0) & (ty >= 0) & (tx < W) & (ty < W)
    tx, ty = tx.clip(0, W-1), ty.clip(0, W-1)
    ok = inside & frame["ctx"]["passable"][tx, ty]
    ok[:, 0] &= frame["first"][DIRECTIONS[:, 0]]
    lengths = np.logical_and.accumulate(ok, axis=1).sum(1)
    ids = np.flatnonzero((lengths >= 4) & (DIRECTIONS[:, 0] != 0))
    steps = np.minimum(np.arange(STEPS)[None], lengths[ids, None]-1)
    path = np.take_along_axis(tx[ids]*W + ty[ids], steps, axis=1)
    return ids, lengths[ids], path


def inputs(frame, history, step):
    c = frame["ctx"]
    peers, planned = frame["rest"], frame["next"]
    uid, way = frame["uid"], frame["directions"]
    dxy = np.column_stack((DX[way], DY[way]))
    ray = [peers.copy()]
    moving = np.ones(len(peers), dtype=bool)
    for _ in range(STEPS):
        q = ray[-1] + dxy
        moving &= np.all((q >= 0) & (q < W), axis=1)
        moving &= c["passable"][tuple(q.clip(0, W-1).T)]
        ray.append(np.where(moving[:, None], q, ray[-1]))
    footprint = np.unique(flat(np.concatenate(ray)))
    p = [paint(peers), paint(planned)]
    for back in (2, 5, 8):
        past = history.track[back]
        p.append(paint(past[(past[:, 0] >= 0) & (np.arange(16) != uid)]))
    p.extend(paint(peers[way == d]) for d in (0, 1, 2, 3, 4))
    p.append(paint(peers[frame["rest_energy"] < max(25, 5*c["move_cost"])]))
    assigned = np.asarray([c["assigned"][int(k)] for k in frame["rest_ids"] if c["assigned"].get(int(k)) is not None],
                          int).reshape(-1, 2)
    p.extend([paint(assigned), paint(frame["start"][None]), paint(XY[footprint])])
    distances = np.stack([distance(flat(peers)), distance(flat(planned)), distance(footprint)])
    p.extend((np.minimum(d, 12)/12 for d in distances))
    p.extend([~c["passable"], c["nebula"], np.clip(c["energy_map"]/20, -1, 1),
              np.where(history.last_seen < 0, 1, np.minimum(step-history.last_seen, 40)/40),
              history.last_seen == step, np.minimum(X+Y, 12)/12,
              np.full((W, W), len(peers) < 10), np.full((W, W), step/100), np.full((W, W), len(peers)/16)])
    result = np.asarray(p, np.float32)
    if result.shape != (len(CHANNELS), W, W):
        raise ValueError("Wrong number of public planes")
    return result, distances.astype(np.int8)
