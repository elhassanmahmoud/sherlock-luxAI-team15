"""Certify positive point pairs from two public score gains under monotone relic activation."""
from collections import Counter, defaultdict, deque
from itertools import product

import numpy as np

WIDTH=24
STRIDE=32


def pair_key(x,y):
    return min(24*int(x)+int(y),24*(23-int(y))+23-int(x))


def occupancy(obs,team):
    xy=np.asarray(obs["units"]["position"][team])
    energy=np.asarray(obs["units"]["energy"][team]).reshape(-1)
    allowed=np.asarray(obs["units_mask"][team],bool)&(energy>=0)&(xy[:,0]>=0)&(xy[:,1]>=0)
    distinct={tuple(v) for v in xy[allowed]}
    return Counter(pair_key(x,y) for x,y in distinct)


def positive(old,new,previous_gain,current_gain,known,previous_tick,current_tick):
    # One bit for each achievable (previous_score,current_score).
    # Current score never exceeds 16, keeping the rows of 32 bits completely separate.
    groups=defaultdict(list)
    fixed=0
    for key in old.keys()|new.keys():
        a,b=old[key],new[key]
        seen=known.get(key,current_tick+1)
        if seen<=previous_tick:
            fixed+=a*STRIDE+b
        else:
            groups[a,b,seen<=current_tick].append(key)
    desired=int(previous_gain)*STRIDE+int(current_gain)
    def attainable(omit=None):
        values=1<<fixed
        for token,keys in groups.items():
            a,b,already=token
            for _ in range(len(keys)-(token==omit)):
                after=values<<b
                before=values<<(a*STRIDE+b)
                values=(after|before) if already else (values|after|before)
        return bool((values>>desired)&1)
    if not attainable():
        return set(),False
    forced=set()
    for token,keys in groups.items():
        if not token[2] and not attainable(token):
            forced.update(keys)
    return forced,True


class Evidence:
    def __init__(self,team):
        self.team=team
        self.known={}
        self.earlier=deque(maxlen=12)
        self.score=0
        self.last_step=-1
        self.conflicts=0

    def observe(self,obs):
        step=int(obs["steps"])
        if self.last_step==step:return []
        self.last_step=step
        match_step=int(obs["match_steps"])
        total=int(obs["team_points"][self.team])
        if match_step==0:
            self.score=total
            self.earlier.clear()
            return []
        gain=total-self.score
        self.score=total
        if match_step>50:
            return []
        now=occupancy(obs,self.team)
        if not 0<=gain<=sum(now.values()):
            self.conflicts+=1
            return []
        # The empty observation also includes deductions from today's single equation.
        found=set()
        for then,old,prev in [(-1,Counter(),0),*self.earlier]:
            positives,ok=positive(old,now,prev,gain,self.known,then,step)
            if not ok:
                self.conflicts+=1
                continue
            found.update(positives)
        fresh=sorted(found-self.known.keys())
        self.known.update({key:step for key in fresh})
        self.earlier.append((step,now,gain))
        return fresh


def crosscheck():
    rng=np.random.default_rng(23112391)
    count=0
    for n in range(1,6):
        for _ in range(120):
            aa=rng.integers(0,3,size=n).tolist()
            bb=rng.integers(0,3,size=n).tolist()
            real=rng.integers(0,3,size=n).tolist()
            ga=sum(a*(v==2) for a,v in zip(aa,real));gb=sum(b*(v>=1) for b,v in zip(bb,real))
            known={i: (3 if v==2 else 7) for i,v in enumerate(real) if v and rng.random()<.25}
            possibles=[]
            for spec in product(range(3),repeat=n):
                if any((spec[i]!=2 if t==3 else spec[i]==0) for i,t in known.items()):continue
                if sum(a*(v==2) for a,v in zip(aa,spec))==ga and sum(b*(v>=1) for b,v in zip(bb,spec))==gb:
                    possibles.append(spec)
            old=Counter({i:a for i,a in enumerate(aa) if a})
            new=Counter({i:b for i,b in enumerate(bb) if b})
            forced,ok=positive(old,new,ga,gb,known,4,8)
            target={i for i in old.keys()|new.keys() if i not in known and all(row[i]>0 for row in possibles)}
            if not ok or forced!=target:raise ValueError((old,new,known,target,forced))
            count+=1
    return count


if __name__=="__main__":print(crosscheck(),"independent exhaustive checks")
