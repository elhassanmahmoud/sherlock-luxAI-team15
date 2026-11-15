from collections import Counter
from itertools import product
from types import SimpleNamespace
from unittest.mock import patch

from scripts import r3_turn_advice_confirm as study


def test_four_arms_cover_exactly_480_untouched_seats():
    keys=[(a,o,n,s) for a,(maps,foes) in study.BLOCKS.items() for o,n,s in product(foes,maps,study.SEATS)]
    assert len(keys)==len(set(keys))==480
    assert Counter(a for a,_,_,_ in keys)==dict(turn_external=160,v14_external=160,r3_solution=80,direct=80)
    assert len(set(study.EXTERNAL)&set(study.DIRECT))==0
    assert min(study.EXTERNAL)==7170560 and max(study.DIRECT)==7170699


def test_exact_live_count_is_saved_even_at_zero():
    counts=Counter(movement=2,changed_unit_orders=2)
    def original(job):
        return {"study":dict(counts)}
    f=study.with_counts(original,study.screen.NAME)
    f.agent=SimpleNamespace(selective_counts=counts)
    assert f(None)["study"]["turn_extra_played"]==0
    counts["turn_extra_played"]=2
    assert f(None)["study"]["turn_extra_played"]==2


def test_attribution_retains_the_paired_map_and_requires_a_strict_lower_bound():
    keys=[("solution92",n,s) for n in study.EXTERNAL for s in study.SEATS]
    base=SimpleNamespace(games={k:dict(result=0) for k in keys},hashes={})
    cand=SimpleNamespace(games={k:dict(result=int(k[1]==study.EXTERNAL.start)) for k in keys},hashes={})
    with patch.object(study.judge,"bounds",return_value=[0.0,.07]) as ci:
        value=study.against_r3(base,cand)
        assert value["net_wins"]==2 and len(value["flips"])==2
        assert ci.call_args.args[0]==[1.0]+[0.0]*39
        assert value["demonstrated_solution_gain_over_r3"] is False
