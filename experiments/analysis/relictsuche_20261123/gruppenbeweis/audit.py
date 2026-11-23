"""Independent time-indexed public feasibility and route checks."""
from collections import Counter, defaultdict
from itertools import chain
import warnings

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


def mirror(cell):
    x, y = divmod(cell, 24)
    return (23-y)*24 + 23-x


def canonical(cell):
    return min(cell, mirror(cell))


def neighbors(cell):
    x, y = divmod(cell, 24)
    return [(d, a*24+b) for d, (a, b) in enumerate(((x,y), (x,y-1), (x+1,y), (x,y+1), (x-1,y)))
            if d and 0 <= a < 24 and 0 <= b < 24]


def cells(hex_mask):
    n = int(hex_mask, 16)
    return {i for i in range(n.bit_length()) if (n >> i) & 1}


class PublicModel:
    def __init__(self, public, t, query_cells):
        slots = {}
        history = defaultdict(list)
        ri, ci, value, lower, upper = [], [], [], [], []
        phase = 0
        stable = False
        def var(key):
            pair = (key, phase)
            if pair not in slots:
                number = len(slots)
                history[key].append(number)
                slots[pair] = number
            return slots[pair]
        for row in public[:t+1]:
            if row["ms"] == 0:
                stable = False
                prev = row["points"]
                phase += 1
                continue
            if not stable:
                phase += 1
                stable = row["epoch_seen"] or row["ms"] >= 50
            gain = row["points"] - prev
            prev = row["points"]
            counts = Counter(canonical(c) for c in set(row["occupied"]))
            for key, n in counts.items():
                ci.append(var(key)); ri.append(len(lower)); value.append(n)
            lower.append(gain); upper.append(gain)
        self.query = {cell: var(cell) for cell in query_cells}
        for variables in history.values():
            for earlier, later in zip(variables, variables[1:]):
                ri.extend([len(lower)]*2); ci.extend((earlier, later)); value.extend((-1, 1))
                lower.append(0); upper.append(np.inf)
        self.n = len(slots)
        self.constraints = LinearConstraint(coo_matrix((value,(ri,ci)),shape=(len(lower),self.n)).tocsr(), lower, upper)

    def zero_possible(self, keys):
        high = np.ones(self.n)
        for key in keys:
            high[self.query[key]] = 0
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Unrecognized options detected.*threads.*")
            sol = milp(np.zeros(self.n), integrality=np.ones(self.n), bounds=Bounds(np.zeros(self.n), high),
                       constraints=self.constraints, options={"presolve": True, "threads": 1, "time_limit": 20.})
        if sol.status not in (0, 2):
            raise ValueError(f"Unresolved public feasibility query, status {sol.status}")
        return sol.status == 0


def independent_routes(public, policy, groups, positives):
    if not groups or not public["ms"]:
        return set()
    own_claims = {canonical(p) for p in chain(public["occupied"], policy["planned"])}
    v16 = cells(policy["point"])
    invisible_or_assigned = own_claims | {canonical(c) for c in v16} | positives
    safe = cells(policy["known_passable"]) - set(policy["enemy"])
    visible_safe = cells(policy["visible"]) & safe
    planned_points = v16 | positives | {mirror(k) for k in positives}
    available = [row for row in policy["free"] if row[1] not in planned_points and row[3] not in planned_points]
    found = set()
    for idx, members in groups:
        members = set(members)
        if invisible_or_assigned & members:
            continue
        targets = {k: {k, mirror(k)} & visible_safe for k in members}
        if not all(targets.values()):
            continue
        for uid, origin, orig, _, legal in available:
            x, y = divmod(origin, 24)
            if any(min(abs(x-c//24)+abs(y-c%24) for c in ends) > 4 for ends in targets.values()):
                continue
            def reached(c):
                k = canonical(c)
                return frozenset([k]) if k in targets and c in targets[k] else frozenset()
            level = {(c, reached(c)) for d, c in neighbors(origin) if d != orig and legal & (1<<d) and c in safe}
            visited = {(origin, frozenset())}
            for distance in range(1, 5):
                if any(hit == members for _,hit in level):
                    found.add((idx, uid))
                    break
                visited.update(level)
                if distance < 4:
                    level = {(n, hit | reached(n)) for c,hit in level for _,n in neighbors(c) if n in safe} - visited
    return found
