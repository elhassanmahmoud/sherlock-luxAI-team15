"""Compare temporal public integer feasibility against all eight states of monotone toy worlds."""
from itertools import combinations
import json
import random

from audit import PublicModel
from pruefen import check


def solver_check():
    rng = random.Random(231126)
    calls = 0
    keys = (1, 2, 3)
    for run in range(4):
        possible = set(range(8))
        observed = []
        actual = rng.randrange(3)
        stable = False
        score = 0
        for t in range(119):
            ms = t % 101
            if not ms:
                stable = False
                score = 0
                observed.append(dict(ms=0, points=0, occupied=[], epoch_seen=False))
                continue
            if not stable:
                possible = {now for old in possible for now in range(8) if now & old == old}
                if rng.random() < .05:
                    actual |= 1 << rng.randrange(3)
            seen = ms == 14 and run % 2 == 1
            stable |= seen or ms >= 50
            occupied = {k for k in keys if rng.random() < .5}
            gain = sum(bool(actual & (1 << (k-1))) for k in occupied)
            score += gain
            possible = {s for s in possible if sum(bool(s & (1 << (k-1))) for k in occupied) == gain}
            observed.append(dict(ms=ms, points=score, occupied=sorted(occupied), epoch_seen=seen))
            if t not in (1, 5, 14, 25, 50, 99, 102, 116):
                continue
            model = PublicModel(observed, t, keys)
            for size in (1, 2, 3):
                for subset in combinations(keys, size):
                    expected = any(all(not (s & (1 << (k-1))) for k in subset) for s in possible)
                    assert model.zero_possible(subset) == expected
                    calls += 1
    return calls


if __name__ == "__main__":
    print(json.dumps({**check(), "time_indexed_solver_comparisons": solver_check()}, indent=2))
