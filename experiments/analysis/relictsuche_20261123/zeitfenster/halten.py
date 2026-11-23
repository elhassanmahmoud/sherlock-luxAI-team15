"""One public hold decision from the current fleet, its proposal and the archived, frozen first-centre prior."""
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
sys.path.insert(0,str(STUDY.parents[2]))
from experiments.analysis.relictsuche_20261123.spaetgebiet.ortsmodell.ort import COORD, MID, ORB, OTHER, OLD

DXY=((0,0),(0,-1),(1,0),(0,1),(-1,0))
FOOT={}
for c in range(576):
    x,y=divmod(c,24)
    FOOT[c]={24*a+b for a in range(max(0,x-1),min(24,x+2)) for b in range(max(0,y-1),min(24,y+2))}


def free(pub,team,t,move):
    d=pub['commands'][t,:,0]
    return np.flatnonzero(pub['units_mask'][t,team] & (pub['energy'][t,team].reshape(-1)>=max(30,3*move))
                          & ~pub['protected'][t] & (d>=1) & (d<=4))


def forecast(pub,t,team,uid):
    x,y=map(int,pub['position'][t,team,uid]);direction=int(pub['commands'][t,uid,0])
    if not 1<=direction<=4:return 24*x+y
    dx,dy=DXY[direction];a,b=x+dx,y+dy
    if not 0<=a<24 or not 0<=b<24 or pub['terrain'][t,a,b]==2:return 24*x+y
    return 24*a+b


def choose(pub,meta):
    team=meta['team'];move=meta['cfg']['unit_move_cost']
    with np.load(OLD,allow_pickle=False) as z:
        assert np.array_equal(z['coords'],COORD)
        count=z['counts'].sum(axis=1)+.5
    prior=count/count.sum()
    seen=np.zeros(300,int)
    for t in range(49):
        if pub['relic_nodes_mask'][t].any() or pub['team_points'][t,team]>0:return None
        sensor=pub['sensor_mask'][t].ravel(); now=set(np.flatnonzero(sensor))
        seen[sensor[MID]|sensor[OTHER]]=t
        if t<20:continue
        weight=prior*(50-seen)/50
        nex={int(u):forecast(pub,t,team,u) for u in np.flatnonzero(pub['units_mask'][t,team])}
        options=[]
        for u in free(pub,team,t,move):
            uid=int(u);x,y=map(int,pub['position'][t,team,uid]);location=x*24+y
            destination=nex[uid]
            if destination==location:continue
            rest=set().union(*(FOOT[c] for k,c in nex.items() if k!=uid))
            lost={int(ORB[c]) for c in (FOOT[location]-FOOT[destination]-rest)&now}
            fresh={int(ORB[c]) for c in (FOOT[destination]-FOOT[location]-rest)-now}
            both=lost&fresh;lost-=both;fresh-=both
            if len(lost)<2:continue
            a=sum(float(weight[k]) for k in sorted(lost));b=sum(float(weight[k]) for k in sorted(fresh))
            if a>=b:options.append((-(a-b),uid,location,destination,sorted(lost),sorted(fresh)))
        if options:
            score,uid,origin,planned,lost,fresh=min(options)
            return dict(t=t,uid=uid,origin=origin,planned=planned,advantage=-score,lost=lost,fresh=fresh)
    return None
