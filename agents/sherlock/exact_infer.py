"""Small exact observation components; no engine, network or timing dependencies."""
from collections import Counter
from fractions import Fraction

MAX_RECORDS = 400
MAX_RAW_TILES = 16
MAX_VARIABLES = 24
MAX_ROWS = 40
MAX_CELL_OPS = 4096
MAX_BITS = 256


class _Abort(Exception):
    """A contradiction or deterministic work limit invalidates the whole result."""


def _reduce(rows, variables):
    matrix = [[Fraction(coeff.get(v, 0)) for v in variables] + [Fraction(rest)]
              for coeff, rest in rows]
    operations = 0

    def check(value):
        if (value.numerator.bit_length() > MAX_BITS
                or value.denominator.bit_length() > MAX_BITS):
            raise _Abort
        return value

    for row in matrix:
        for value in row:
            check(value)
    rank, width = 0, len(variables)
    for col in range(width):
        pivot = next((r for r in range(rank, len(matrix)) if matrix[r][col]), None)
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        divisor = matrix[rank][col]
        for j in range(col, width + 1):
            if operations >= MAX_CELL_OPS:
                raise _Abort
            operations += 1
            matrix[rank][j] = check(matrix[rank][j] / divisor)
        for r, row in enumerate(matrix):
            if r == rank or not row[col]:
                continue
            factor = row[col]
            for j in range(col, width + 1):
                if operations >= MAX_CELL_OPS:
                    raise _Abort
                operations += 1
                row[j] = check(row[j] - factor * matrix[rank][j])
        rank += 1
        if rank == len(matrix):
            break
    facts = {}
    for row in matrix:
        nonzero = [i for i in range(width) if row[i]]
        if not nonzero:
            if row[-1]:
                raise _Abort
        elif len(nonzero) == 1:
            # RREF pivot is exactly one: no rounding and no free-variable guess.
            value = row[-1]
            if value not in (0, 1):
                raise _Abort
            facts[variables[nonzero[0]]] = int(value)
    return facts


def exact_facts(records, touched, *, point=(), dead=(), mirror=None):
    """Facts in one complete bounded component, or {} on any rejected result.

    A symmetry orbit receives one coefficient per unique physical occupied tile;
    two simultaneously occupied mirror tiles therefore have coefficient two.
    Input objects are never changed. Larger components are skipped, not truncated.
    """
    def representative(tile):
        return min(tile, mirror(tile)) if mirror is not None else tile

    points = {representative(t) for t in point}
    nulls = {representative(t) for t in dead}
    if points & nulls:
        return {}
    equations = {}
    for tiles, original_rest in records[:MAX_RECORDS]:
        if len(tiles) > MAX_RAW_TILES:
            continue
        physical = set(tiles)
        coeff = Counter(representative(t) for t in physical)
        rest = original_rest - sum(k for v, k in coeff.items() if v in points)
        coeff = {v: k for v, k in coeff.items() if v not in points and v not in nulls}
        if not 0 <= rest <= sum(coeff.values()):
            return {}
        key = tuple(sorted(coeff.items()))
        if key in equations and equations[key] != rest:
            return {}
        if key:
            equations[key] = rest
    # Sort before graph construction: component choice and pivots are deterministic.
    rows = [(dict(key), rest) for key, rest in sorted(equations.items())]
    incidence = {}
    for i, (coeff, _) in enumerate(rows):
        for variable in coeff:
            incidence.setdefault(variable, []).append(i)
    starts = sorted({representative(t) for t in touched} & incidence.keys())
    if not starts:
        return {}
    variables, selected, pending = {starts[0]}, set(), [starts[0]]
    while pending:
        variable = pending.pop()
        for i in incidence[variable]:
            if i in selected:
                continue
            selected.add(i)
            if len(selected) > MAX_ROWS:
                return {}
            for other in rows[i][0]:
                if other not in variables:
                    variables.add(other)
                    if len(variables) > MAX_VARIABLES:
                        return {}
                    pending.append(other)
    try:
        return _reduce([rows[i] for i in sorted(selected)], sorted(variables))
    except _Abort:
        return {}
