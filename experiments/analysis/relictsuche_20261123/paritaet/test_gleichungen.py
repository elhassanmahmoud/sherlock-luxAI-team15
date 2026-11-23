"""Compare the GF(2) eliminator to all assignments, including coincident mirrored cells."""
import itertools
import random
from experiments.analysis.relictsuche_20261123.paritaet.gleichungen import singletons


def test_two_aggregate_scores_force_a_positive_without_a_single_cell_visit():
    # x+y+z=1 and x+y=0 in parity determine z, leaving x and y individually unconstrained.
    assert singletons([((7,0),(1,0)),((3,0),(0,1))],0,0)==(4,0)


def test_repeated_world_endpoints_cancel_in_parity():
    assert singletons([((3,1),(3,9))],0,0)==(2,0)


def test_all_assignments_satisfying_random_public_equations():
    rng=random.Random(231123)
    for _ in range(600):
        n=rng.randint(2,8)
        actual=rng.randrange(1<<n)
        fixed=rng.randrange(1<<n)
        yes,no=fixed&actual,fixed&~actual
        rows=[]
        for turn in range(rng.randint(1,10)):
            seen=rng.randrange(1<<n)
            twice=rng.randrange(1<<n)&seen
            gain=(actual&seen).bit_count()+(actual&twice).bit_count()
            rows.append(((seen,twice),(gain,turn)))
        candidates=[m for m in range(1<<n) if m&fixed==yes and all(
            (m&(seen^twice)).bit_count()%2==gain%2 for (seen,twice),(gain,_) in rows)]
        assert candidates
        positive=negative=0
        for i in range(n):
            bit=1<<i
            if bit&fixed:continue
            if all(m&bit for m in candidates):positive|=bit
            if all(not(m&bit) for m in candidates):negative|=bit
        assert singletons(rows,yes,no)==(positive,negative)


def test_positive_and_transient_negative_claims_across_hidden_spawns():
    from pathlib import Path
    from unittest.mock import patch
    import sys
    before=Path(__file__).resolve().parents[1]/"punktspeicher"
    if str(before) not in sys.path:
        sys.path.insert(0,str(before))
    import pruefen
    from experiments.analysis.relictsuche_20261123.paritaet.gleichungen import ParityEvidence
    with patch.object(pruefen,"Evidence",ParityEvidence):
        result=pruefen.check()
    assert result["nonreset_observations"]==9600 and result["checked_positive"]>0 and result["checked_negative"]>0
