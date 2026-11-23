"""Exhaustive four-cell inequalities, streak transitions and bounded-route controls."""
from itertools import combinations, product
import json

from gruppen import GroupEvidence, candidates
from beweise import MIRROR
from wege import routes


def check():
    comparisons = 0
    for weights in product(range(-2, 3), repeat=4):
        coeff = tuple(sum(1 << i for i, w in enumerate(weights) if predicate(w)) for predicate in
                      (lambda w: w >= 1, lambda w: w == 2, lambda w: w <= -1, lambda w: w == -2))
        for rhs in range(-2, 5):
            for positive, negative in ((0, 0), (1, 0), (0, 1), (2, 4)):
                states = [s for s in range(16) if s & positive == positive and not s & negative and
                          sum(w for i, w in enumerate(weights) if s >> i & 1) >= rhs]
                if not states:
                    continue
                # Mirror the frozen singleton solver: factor out all individually forced values first.
                ones = sum(1 << i for i in range(4) if all(s >> i & 1 for s in states))
                zeros = sum(1 << i for i in range(4) if all(not (s >> i & 1) for s in states))
                free = [i for i in range(4) if not (ones | zeros) >> i & 1]
                expected = set()
                for size in (2, 3):
                    for choice in combinations(free, size):
                        m = sum(1 << i for i in choice)
                        if all(m & s for s in states) and not any(n & m == n for n in expected):
                            expected.add(m)
                assert set(candidates(coeff, rhs, ones, zeros)) == expected
                comparisons += 1
    memory = GroupEvidence()
    a, b, c = 100, 101, 102
    pair = (1 << a) | (1 << b)
    fields = {t: [a, b] if t == 1 else [] for t in range(102)}
    for t in range(102):
        row = dict(step=t, ms=t%101, occupied=fields[t], points=int(1 <= t <= 100), epoch_seen=False)
        known = memory.observe(row)
        if t:
            assert pair in known
    free = [9, a-1, 0, None, 30]
    world_mask = format((1 << 576)-1, "x")
    policy = dict(free=[free], planned=[a-1], point="0", known_passable=world_mask, visible=world_mask, enemy=[])
    row = dict(ms=1, occupied=[a-1])
    triple = pair | (1 << c)
    found, partial = routes(row, policy, {pair, triple}, 0)
    assert found[pair, 9] == [a-1, a, b] and found[triple, 9] == [a-1, a, b, c]
    assert partial == {pair, triple}
    for changed, expected in ((dict(planned=[MIRROR[b]]), set()), (dict(enemy=[b]), {pair, triple}),
                              (dict(free=[[9, a-1, 3, None, 1 << 3]]), set())):
        f, p = routes(row, {**policy, **changed}, {pair, triple}, 0)
        assert not f and p == expected
    assert routes(row, policy, {pair}, 1 << a) == ({}, set())
    return dict(exhaustive_inequality_states=comparisons, persistent_steps=101, route_controls=7)


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
