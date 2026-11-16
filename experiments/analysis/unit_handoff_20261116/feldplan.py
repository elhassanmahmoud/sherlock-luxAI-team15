"""Select individual V15 moves with strictly additive known scoring coverage."""
from collections import Counter

DIRECTIONS = ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0), (0, 0))


def endpoint(position, action, energy, cost, blocked, shape):
    x, y = position
    dx, dy = DIRECTIONS[action]
    nx, ny = x + dx, y + dy
    if energy < cost or not (0 <= nx < shape[0] and 0 <= ny < shape[1]) or (nx, ny) in blocked:
        return position
    return nx, ny


def select(own, visible_enemy_positions, points, blocked, cost, shape, r3, v15):
    """All inputs are from the same pre-action state and use world coordinates."""
    if not points:
        return []
    occupied = {pos for _, pos, _ in own}
    planned = {uid: endpoint(pos, int(r3[uid][0]), energy, cost, blocked, shape)
               for uid, pos, energy in own}
    counts = Counter(planned.values())
    if any(not counts[p] for p in points & occupied):
        return []
    free = points - occupied - visible_enemy_positions
    selected = []
    for uid, pos, energy in sorted(own):
        action = int(v15[uid][0])
        if action not in (1, 2, 3, 4):
            continue
        new = endpoint(pos, action, energy, cost, blocked, shape)
        previous = planned[uid]
        if new not in free or counts[new]:
            continue
        if previous in points and counts[previous] == 1:
            continue
        counts[previous] -= 1
        counts[new] += 1
        selected.append((uid, new))
    return selected
