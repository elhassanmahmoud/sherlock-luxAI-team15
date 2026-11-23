"""Visible bounded group tours by one available ship, in world coordinates."""
from gruppen import indices
from beweise import MIRROR, PAIR, folded, worlds


NEIGHBORS = {}
for loc in range(576):
    x, y = divmod(loc, 24)
    NEIGHBORS[loc] = [(d, 24 * xx + yy) for d, (xx, yy) in
                      enumerate(((x, y), (x, y-1), (x+1, y), (x, y+1), (x-1, y)))
                      if d and 0 <= xx < 24 and 0 <= yy < 24]


def useful_tour(path, group, visible_targets):
    seen = set()
    visited = 0
    for cell in path:
        state = (cell, visited)
        if state in seen:
            return False
        seen.add(state)
        if cell in visible_targets and group in visible_targets[cell]:
            visited |= 1 << PAIR[cell]
    return visited == group


def routes(public, policy, groups, singles):
    """Return every eligible (group, UID) with a complete tour and groups with partial access."""
    if not groups or not public["ms"]:
        return {}, set()
    positions = set(public["occupied"]) | set(policy["planned"])
    blocked = sum(1 << k for k in {PAIR[p] for p in positions}) | folded(int(policy["point"], 16)) | singles
    open_groups = {mask for mask in groups if not mask & blocked}
    safe = int(policy["known_passable"], 16)
    visible = int(policy["visible"], 16)
    enemies = set(policy["enemy"])
    enemy_mask = sum(1 << c for c in enemies)
    passable = safe & ~enemy_mask
    seen_free = visible & passable
    if not open_groups or not seen_free:
        return {}, set()
    target_groups = {}
    for group in open_groups:
        for key in indices(group):
            for cell in {key, MIRROR[key]}:
                if (seen_free >> cell) & 1:
                    target_groups.setdefault(cell, set()).add(group)
    occupied_task = worlds(singles) | int(policy["point"], 16)
    complete = {}
    partial = set()
    for uid, origin, original, assigned, legality in policy["free"]:
        if (occupied_task >> origin) & 1 or (assigned is not None and (occupied_task >> assigned) & 1):
            continue
        xx, yy = divmod(origin, 24)
        nearby = {loc: gs for loc, gs in target_groups.items()
                  if abs(xx-loc//24) + abs(yy-loc%24) <= 4}
        if not nearby:
            continue
        frontier = [([origin, n], 0, frozenset()) for d, n in NEIGHBORS[origin]
                    if (legality >> d) & 1 and d != original and (passable >> n) & 1]
        for length in range(1, 5):
            following = []
            for path, hits, earlier in frontier:
                cur = path[-1]
                if cur in nearby:
                    key = 1 << PAIR[cur]
                    hits |= key
                    candidate_groups = nearby[cur]
                    partial.update(candidate_groups)
                    for group in candidate_groups:
                        if not group & ~hits and useful_tour(path, group, nearby):
                            complete.setdefault((group, uid), path)
                if length == 4:
                    continue
                # Revisiting a cell before reaching a new candidate would only manufacture an alternative first step.
                state = (cur, hits)
                visited = earlier | {state, (origin, 0)}
                for _, nxt in NEIGHBORS[cur]:
                    if not (passable >> nxt) & 1 or (nxt, hits) in visited:
                        continue
                    following.append(([*path, nxt], hits, visited))
            frontier = following
    return complete, partial
