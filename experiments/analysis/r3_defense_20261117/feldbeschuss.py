"""Select V15's differing SAP on a publicly known, apparently unoccupied scoring tile."""
from collections import Counter


def switches(own, visible_enemy, points, r3_destinations, base, advice, sap_cost, sap_range):
    ally_tiles = {pos for _, pos, _ in own}
    available = points - ally_tiles - visible_enemy
    if not available:
        return []
    coverage = Counter(r3_destinations.values())
    accepted = []
    for uid, pos, energy in sorted(own):
        cmd = tuple(map(int, advice[uid]))
        if cmd[0] != 5 or tuple(base[uid]) == cmd or energy < sap_cost:
            continue
        dx, dy = cmd[1:]
        target = (pos[0] + dx, pos[1] + dy)
        if target not in available or max(abs(dx), abs(dy)) > sap_range:
            continue
        planned = r3_destinations[uid]
        if planned != pos and planned in points and coverage[planned] == 1:
            continue
        coverage[planned] -= 1
        coverage[pos] += 1
        accepted.append((uid, target))
    return accepted
