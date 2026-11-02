"""A bounded improvement of the owners of already selected own point targets."""
from __future__ import annotations

from itertools import combinations, islice

import numpy as np

from . import features, rules


def improve_point_assignment(ctx: dict, masks: dict, cfg) -> tuple[dict, int]:
    """Copy the assignment and make at most one strictly shorter legal BFS pair swap.

    The gain is local path potential, not a guarantee of route energy or points.
    Productive holders are derived from live units, not legacy first_on_tile.
    """
    assigned = dict(ctx["assigned"])
    if (not cfg.point_pair_swap or not cfg.use_belief or not cfg.reach_assign
            or cfg.home_first or cfg.home_penalty or cfg.energy_pref or cfg.sticky):
        return assigned, 0

    W, H = ctx["W"], ctx["H"]
    points, passable = ctx["point_tiles"], ctx["passable"]
    pos, energy = ctx["ally_pos"], ctx["ally_ene"]
    ids = sorted(int(u) for u in ctx["ally_ids"])
    holders = {}
    for uid in ids:
        x, y = map(int, pos[uid])
        if energy[uid] >= 0 and 0 <= x < W and 0 <= y < H and points[x, y]:
            holders.setdefault((x, y), uid)

    belief = ctx["belief"]
    own_origin = belief.canonical or belief.team_id == 0
    eligible = []
    for uid in ids:
        x, y = map(int, pos[uid])
        target = assigned.get(uid)
        if (energy[uid] < ctx["move_cost"] or not (0 <= x < W and 0 <= y < H)
                or holders.get((x, y)) == uid or not passable[x, y] or target is None):
            continue
        tx, ty = target
        if not (0 <= tx < W and 0 <= ty < H and points[tx, ty] and passable[tx, ty]):
            continue
        enemy = tx + ty > W - 1 if own_origin else tx + ty < W - 1
        if not enemy:
            eligible.append(uid)
    if len(eligible) < 2:
        return assigned, 0

    goals = sorted({assigned[u] for u in eligible})
    distances = features.bfs_maps(passable, np.asarray(goals))
    by_goal = dict(zip(goals, distances))
    best_pair, best_gain = None, 0
    # The game has at most 16 units; keep the bound explicit for synthetic contexts.
    for u, v in islice(combinations(eligible, 2), 120):
        gu, gv = assigned[u], assigned[v]
        if gu == gv:
            continue
        routes = ((u, gu), (v, gv), (u, gv), (v, gu))
        lengths = [int(by_goal[g][tuple(pos[uid])]) for uid, g in routes]
        if any(d < 0 for d in lengths):
            continue
        gain = lengths[0] + lengths[1] - lengths[2] - lengths[3]
        if gain <= best_gain:
            continue
        if any(rules.first_step(by_goal[g], pos[uid], masks[uid]) is None for uid, g in routes):
            continue
        best_pair, best_gain = (u, v), gain
    if best_pair is not None:
        u, v = best_pair
        assigned[u], assigned[v] = assigned[v], assigned[u]
    return assigned, best_gain
