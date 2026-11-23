"""Monotone public positive bounds on hidden, symmetric scoring tiles. No reference-policy labels."""
from itertools import chain

WIDTH=24
MIRROR=tuple((23-(i%24))*24+(23-(i//24)) for i in range(576))
PAIR=tuple(min(i,MIRROR[i]) for i in range(576))
CANONICAL=sum(1<<i for i in range(576) if PAIR[i]==i)


def indices(mask):
    while mask:
        bit=mask & -mask
        yield bit.bit_length()-1
        mask ^= bit


def worlds(pairs):
    result=pairs
    for k in indices(pairs):
        result |= 1<<MIRROR[k]
    return result


def folded(world):
    return sum(1<<f for f in {PAIR[k] for k in indices(world)})


def weights(occupied):
    """One contribution per unique physical world tile, including distinct occupied symmetric endpoints."""
    one=two=0
    for cell in set(occupied):
        bit=1<<PAIR[cell]
        if one & bit:
            two |= bit
        one |= bit
    return one,two


def subtract(x,y):
    a,b=x
    c,d=y
    return (a&~c)|(b&~d), b&~c, (c&~a)|(d&~b), d&~a


class Evidence:
    def __init__(self,forget_at_match=False):
        self.forget_at_match=forget_at_match
        self.step=-1
        self.match=-1
        self.previous_score=0
        self.positive=0
        self.lower={}
        self.lower_bounds={}
        self.proofs={}
        self.clear_epoch(None)

    def clear_epoch(self,key):
        self.epoch=key
        self.negative=0
        self.upper={}
        self.bounds={}

    def add_bound(self,coef,limit,lo,hi):
        a,b,c,d=coef
        if limit<=-c.bit_count()-d.bit_count():
            return
        if limit>a.bit_count()+b.bit_count():
            raise ValueError("Impossible public score inequality")
        if coef not in self.bounds or self.bounds[coef][0]<limit:
            self.bounds[coef]=(limit,lo,hi)

    def propagate(self,step):
        fresh=[]
        while True:
            previous=(self.positive,self.negative)
            for (plus,plus2,minus,minus2),(limit,lo,hi) in chain(self.lower_bounds.items(),self.bounds.items()):
                max_now=((plus & ~self.negative).bit_count()+(plus2 & ~self.negative).bit_count()
                         -(minus & self.positive).bit_count()-(minus2 & self.positive).bit_count())
                slack=max_now-limit
                if slack<0:
                    raise ValueError("Contradictory public constraints")
                if slack>=2:continue
                unknown=~(self.positive|self.negative)
                new_pos=(plus if slack==0 else plus2) & unknown
                new_neg=(minus if slack==0 else minus2) & unknown
                if new_pos:
                    witness=dict(step=step,lo=lo,hi=hi,rhs=limit,slack=slack,
                                 coefficients=[format(x,"x") for x in (plus,plus2,minus,minus2)],
                                 positive_before=format(self.positive,"x"),negative_before=format(self.negative,"x"))
                    for key in indices(new_pos):
                        self.proofs[key]=witness
                        fresh.append(key)
                self.positive |= new_pos
                self.negative |= new_neg
            if previous==(self.positive,self.negative):
                return fresh

    def observe(self, row):
        t=row["step"]; ms=row["ms"]; match=t//101
        if t != self.step+1 or ms != t%101:
            raise ValueError("Public chronology is not continuous")
        self.step=t
        if ms==0:
            if self.forget_at_match:
                self.positive=0
                self.lower.clear();self.lower_bounds.clear();self.proofs.clear()
            self.clear_epoch(None)
            self.stable=False
            self.match=match
            self.previous_score=row["points"]
            return []
        gain=row["points"]-self.previous_score
        self.previous_score=row["points"]
        if not 0<=gain<=len(set(row["occupied"])):
            raise ValueError("Invalid public gain")
        self.stable |= row["epoch_seen"] or ms>=50
        epoch=(match,-1 if self.stable else ms)
        if epoch != self.epoch:
            self.clear_epoch(epoch)
        current=weights(row["occupied"])
        a,b=current
        older=self.lower.get(current)
        if gain>0 and (older is None or gain>older[0]):
            self.lower[current]=(gain,t)
            self.lower_bounds[(a,b,0,0)]=(gain,t,None)
            for prior,(cap,hi) in self.upper.items():
                if a & prior[0]:
                    self.add_bound(subtract(current,prior),gain-cap,t,hi)
        upper=self.upper.get(current)
        if upper is None:
            self.upper[current]=(gain,t)
            self.add_bound((0,0,a,b),-gain,None,t)
            for old,(floor,lo) in self.lower.items():
                if a & old[0]:
                    self.add_bound(subtract(old,current),floor-gain,lo,t)
        elif upper[0]!=gain:
            raise ValueError("Different gain for identical occupancy inside a fixed epoch")
        return self.propagate(t)
