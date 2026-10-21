"""Evaluation-only pair decoding over V3's canonical movement proposals.

The objective is nominal distinct known point occupancy. It does not predict
field energy, enemy actions, hidden enemies, Sap, void or collision outcomes.
"""
from __future__ import annotations

from itertools import combinations, product

import numpy as np

from . import geometry as geo


def coordinate_moves(ctx, ids, q, masks, base_actions) -> dict[int, int]:
    """Return only changed movement classes, without mutating caller inputs.

    Each sorted nearby pair gets baseline plus at most two learned alternatives
    per unit. Accepted pairs reserve both units; all other units' destinations
    remain part of the occupancy objective throughout the bounded search.
    """
    if len(ids) == 0 or not np.any(ctx['point_tiles']):
        return {}
    move_cost = float(ctx['move_cost'])
    if not np.isfinite(move_cost) or move_cost < 0:
        return {}
    width, height = ctx['W'], ctx['H']
    points = ctx['point_tiles']
    positions, energies, destinations = {}, {}, {}
    options, spans, rows = {}, {}, {}
    plan = dict(base_actions)

    def valid_position(pos):
        return (np.all(np.isfinite(pos)) and np.all(pos == np.floor(pos))
                and 0 <= pos[0] < width and 0 <= pos[1] < height)

    enemies = []
    for pos, energy in zip(ctx['enemy_coords'], ctx['enemy_energies']):
        # Malformed visible threats cannot justify creating a new movement.
        if not np.isfinite(energy) or not valid_position(pos):
            return {}
        if energy >= 0:
            enemies.append(pos)

    def away_from_enemies(pos):
        return all(max(abs(pos[0] - enemy[0]), abs(pos[1] - enemy[1])) > 1
                   for enemy in enemies)

    def destination(uid, action):
        if uid not in positions or not np.isfinite(energies[uid]) or energies[uid] < 0:
            return None
        x, y = positions[uid]
        if action == geo.SAP:
            return (x, y)
        if action not in range(5):
            return None
        if action != geo.STAY and energies[uid] < move_cost:
            return None
        tile = (x + int(geo.DIR_DX[action]), y + int(geo.DIR_DY[action]))
        return tile if 0 <= tile[0] < width and 0 <= tile[1] < height else None

    for row, uid in enumerate(ids):
        pos = np.asarray(ctx['ally_pos'][uid])
        energies[uid] = float(ctx['ally_ene'][uid])
        if valid_position(pos):
            positions[uid] = tuple(int(v) for v in pos)
        base = base_actions[uid]
        destinations[uid] = destination(uid, base)
        rows[uid] = row
        if (uid not in positions or not np.isfinite(energies[uid]) or energies[uid] < 0
                or base not in range(5) or not masks[row, base]
                or not np.isfinite(q[row, base])):
            continue
        legal = [a for a in range(q.shape[1]) if masks[row, a] and np.isfinite(q[row, a])]
        values = [float(q[row, a]) for a in legal]
        span = max(max(values) - min(values), 1e-6)
        if not np.isfinite(span):
            continue
        spans[uid] = span
        top = sorted((a for a in legal if a < 5), key=lambda a: (-float(q[row, a]), a))[:2]
        choices = [base]
        for action in top:
            tile = destination(uid, action)
            if (action != base and tile is not None
                    and float(q[row, base]) - float(q[row, action]) <= 0.15 * span
                    and away_from_enemies(positions[uid]) and away_from_enemies(tile)):
                choices.append(action)
        options[uid] = choices

    def occupied(tiles):
        return {tile for tile in tiles if tile is not None and points[tile]}

    used = set()
    for left, right in combinations(sorted(options), 2):
        if left in used or right in used:
            continue
        if sum(abs(a - b) for a, b in zip(positions[left], positions[right])) > 2:
            continue
        left_tiles = occupied(destination(left, a) for a in options[left])
        right_tiles = occupied(destination(right, a) for a in options[right])
        if not left_tiles.intersection(right_tiles):
            continue
        outside = occupied(tile for uid, tile in destinations.items() if uid not in (left, right))
        current = len(outside | occupied([destinations[left], destinations[right]]))
        best_score, best_actions = None, None
        for actions in product(options[left], options[right]):
            tiles = [destination(uid, a) for uid, a in zip((left, right), actions)]
            count = len(outside | occupied(tiles))
            regret = sum(max(0.0, float(q[rows[uid], base_actions[uid]])
                             - float(q[rows[uid], a])) / spans[uid]
                         for uid, a in zip((left, right), actions))
            changes = sum(a != base_actions[uid] for uid, a in zip((left, right), actions))
            score = (-count, regret, changes, actions)
            if best_score is None or score < best_score:
                best_score, best_actions = score, actions
        if -best_score[0] > current:
            for uid, action in zip((left, right), best_actions):
                plan[uid] = action
                destinations[uid] = destination(uid, action)
            used.update((left, right))
    return {uid: action for uid, action in plan.items() if action != base_actions[uid]}
