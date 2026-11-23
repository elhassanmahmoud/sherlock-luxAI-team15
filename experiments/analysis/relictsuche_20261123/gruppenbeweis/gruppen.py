"""Small, certifiably positive disjunctions from public score bounds."""
from itertools import chain, combinations
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "punktspeicher"))
from beweise import Evidence, indices


def candidates(coefficients, rhs, positive, negative):
    plus, double_plus, minus, double_minus = coefficients
    maximum = ((plus & ~negative).bit_count() + (double_plus & ~negative).bit_count()
               - (minus & positive).bit_count() - (double_minus & positive).bit_count())
    slack = maximum - rhs
    if not 1 <= slack <= 5:
        return
    free = plus & ~(positive | negative)
    if free.bit_count() < 2:
        return
    twice = free & double_plus
    once = free & ~double_plus
    for size in (2, 3):
        for doubles in range(size + 1):
            singles = size - doubles
            total = singles + 2 * doubles
            smallest = 1 if singles else 2
            if total <= slack or total - smallest > slack:
                continue
            if singles > once.bit_count() or doubles > twice.bit_count():
                continue
            for left in combinations(indices(once), singles):
                for right in combinations(indices(twice), doubles):
                    yield sum(1 << i for i in left + right)


class GroupEvidence:
    def __init__(self):
        self.single = Evidence()
        self.groups = set()
        self.extra_positive = 0

    def observe(self, public):
        self.single.observe(public)
        single = self.single
        groups = self.groups.copy()
        if public["ms"]:
            for coeff, (rhs, _, _) in chain(single.lower_bounds.items(), single.bounds.items()):
                groups.update(candidates(coeff, rhs, single.positive, single.negative))
        possible = set()
        for mask in groups:
            if mask & (single.positive | self.extra_positive):
                continue
            remaining = mask & ~single.negative
            if not remaining:
                raise ValueError("A previously certified positive group has no possible member")
            if remaining.bit_count() == 1:
                self.extra_positive |= remaining
            else:
                possible.add(remaining)
        possible = {mask for mask in possible if not mask & self.extra_positive}
        pairs = {mask for mask in possible if mask.bit_count() == 2}
        triples = {mask for mask in possible if mask.bit_count() == 3
                   and not any(mask ^ (1 << i) in pairs for i in indices(mask))}
        self.groups = pairs | triples
        return self.groups
