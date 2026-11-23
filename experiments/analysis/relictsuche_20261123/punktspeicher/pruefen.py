"""Independent enumeration of all monotone binary explanations in small worlds."""
import json
from pathlib import Path
import random

from beweise import Evidence, MIRROR, indices, subtract, weights

HERE=Path(__file__).resolve().parent


def check():
    rng=random.Random(23112302)
    pairkeys=[0,24,48,72]
    all_states=range(1<<len(pairkeys))
    frames=positive_checks=negative_checks=0
    for case in range(32):
        live=0
        possible={0}
        memory=Evidence()
        points=0
        known_stable=False
        for t in range(303):
            m,ms=divmod(t,101)
            if ms==0:
                points=0
                known_stable=False
                row=dict(step=t,ms=ms,occupied=[],points=0,epoch_seen=False)
                memory.observe(row)
                continue
            if not known_stable:
                possible={a for a in all_states if any((b&~a)==0 for b in possible)}
                if rng.random()<.035:
                    live |= 1<<rng.randrange(len(pairkeys))
            reveals=ms==25 and case%3==0
            known_stable |= reveals or ms>=50
            occ=[]
            for key in pairkeys:
                if rng.random()<.34: occ.append(key)
                if rng.random()<.19: occ.append(MIRROR[key])
            if occ and rng.random()<.25:
                occ.append(occ[0])
            def tally(a):
                return sum(bool((1<<i)&a) * sum(cell in (k,MIRROR[k]) for cell in set(occ)) for i,k in enumerate(pairkeys))
            gain=tally(live)
            points+=gain
            possible={a for a in possible if tally(a)==gain}
            assert live in possible
            memory.observe(dict(step=t,ms=ms,occupied=occ,points=points,epoch_seen=reveals))
            for i,k in enumerate(pairkeys):
                if memory.positive>>k&1:
                    assert all(a>>i&1 for a in possible)
                    positive_checks+=1
                if memory.negative>>k&1:
                    assert all(not(a>>i&1) for a in possible)
                    negative_checks+=1
            frames+=1
    for a in range(3):
        for b in range(3):
            m=subtract((int(a>=1),int(a==2)),(int(b>=1),int(b==2)))
            assert m[0]+m[1]-m[2]-m[3]==a-b
    assert weights([0,0,MIRROR[0]])==(1,1)
    assert weights([23,23])==(1<<23,0)
    return dict(sequences=32,nonreset_observations=frames,checked_positive=positive_checks,checked_negative=negative_checks,
                signed_coefficients=9,occupancy_cases=2)


if __name__=="__main__":
    result=check()
    print(json.dumps(result,indent=2))
