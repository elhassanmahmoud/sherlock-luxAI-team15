"""Add exact, public parity equalities to the interval-based scoring proofs."""
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import Evidence, indices


def singletons(observations, positive, negative):
    """Reduce equalities over GF(2); keep only individual bits whose values are forced."""
    basis = {}
    for (occupied, twice), (gain, _) in observations:
        variables = occupied ^ twice
        rhs = (gain ^ (variables & positive).bit_count()) & 1
        mask = variables & ~(positive | negative)
        while mask:
            pivot = mask.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (mask, rhs)
                break
            other, parity = basis[pivot]
            mask ^= other
            rhs ^= parity
        if not mask and rhs:
            raise ValueError("Inconsistent public point parity")
    yes = no = 0
    for pivot in sorted(basis):
        mask, rhs = basis[pivot]
        mask &= ~(1 << pivot)
        # Remove all already-reduced lower pivots; unresolved, free bits remain.
        free = 0
        while mask:
            j = mask.bit_length() - 1
            if j in basis:
                other, parity = basis[j]
                mask ^= other
                rhs ^= parity
            else:
                bit = 1 << j
                free |= bit
                mask ^= bit
        bit = 1 << pivot
        basis[pivot] = (free | bit, rhs)
        if not free:
            if rhs:
                yes |= bit
            else:
                no |= bit
    return yes, no


class ParityEvidence(Evidence):
    def observe(self, row):
        fresh = super().observe(row)
        if not self.stable or not row["ms"] or row["ms"] % 4:
            return fresh
        while True:
            yes, no = singletons(self.upper.items(), self.positive, self.negative)
            if not (yes | no):
                break
            self.positive |= yes
            self.negative |= no
            fresh.extend(indices(yes))
            fresh.extend(self.propagate(row["step"]))
        return fresh
