"""Public free-ship routes and two previously fixed spatial priors. No referee access."""
from collections import deque
from pathlib import Path
import sys

import numpy as np

STUDY=Path(__file__).resolve().parent.parent
ROOT=STUDY.parents[2]
sys.path.insert(0,str(ROOT))
from experiments.analysis.relictsuche_20261123.spaetgebiet.ortsmodell.ort import COORD, DIST, MID, ORB, OTHER, ZONE, priors

ALL=np.arange(576)
NEIGHBORS={}
for cell in ALL:
    x,y=divmod(int(cell),24)
    NEIGHBORS[int(cell)]=[(d,a*24+b) for d,(a,b) in enumerate(((x,y),(x,y-1),(x+1,y),(x,y+1),(x-1,y)))
                          if d and 0<=a<24 and 0<=b<24]


def previous_centres(pub, t, m):
    found={}
    for j in range(m):
        for idx in (j,j+3):
            seen=np.flatnonzero(pub['relic_nodes_mask'][:t+1,idx])
            if len(seen):
                x,y=pub['relic_nodes'][seen[-1],idx]
                found[j]=int(ORB[int(x)*24+int(y)])
    return found


def free_units(pub,t,team,move_cost):
    energy=pub['energy'][t,team].reshape(-1)
    allowed=(pub['units_mask'][t,team] & (energy>=max(30,8*move_cost)) & ~pub['protected'][t]
             & (pub['commands'][t,:,0]<=4) & pub['move_mask'][t,:,1:].any(axis=1))
    return np.flatnonzero(allowed)


def alternatives(pub,t,team,move_cost,only=None):
    terrain=pub['terrain'][t].reshape(-1)
    safe=(terrain>=0)&(terrain!=2)
    enemies=pub['position'][t,1-team][pub['units_mask'][t,1-team]]
    for x,y in enemies:safe[int(x)*24+int(y)]=False
    paths={}
    for uid0 in free_units(pub,t,team,move_cost):
        uid=int(uid0)
        x,y=pub['position'][t,team,uid]; origin=int(x)*24+int(y)
        if only is not None and min(abs(int(x)-c//24)+abs(int(y)-c%24) for c in only)>8:continue
        original=int(pub['commands'][t,uid,0]); mask=pub['move_mask'][t,uid]
        seen={origin};queue=deque()
        for d,n in NEIGHBORS[origin]:
            if d!=original and mask[d] and safe[n]:
                queue.append((n,[origin,n]));seen.add(n)
        while queue:
            cell,path=queue.popleft()
            if only is None or cell in only:
                best=paths.get(cell)
                if best is None or (len(path),uid)<(len(best[1]),best[0]): paths[cell]=(uid,path)
            if len(path)==9:continue
            for _,n in NEIGHBORS[cell]:
                if n not in seen and safe[n]:
                    seen.add(n);queue.append((n,[*path,n]))
    return paths


def public_orders(pub,inherited,meta,match):
    team=meta['team'];start=101*match;cost=meta['cfg']['unit_move_cost']
    marginal,conditional=priors()
    commands={}
    for k in (8,16,24,32,40,48):
        t=start+k
        if pub['relic_nodes_mask'][start:t+1,[match,match+3]].any():break
        known=previous_centres(pub,t,match)
        if not known or not inherited[t].any():continue
        route=alternatives(pub,t,team,cost)
        if not route:continue
        # Latest visible absence at either endpoint discounts spawn times already excluded by the public view.
        vis=pub['sensor_mask'][start:t+1].reshape(k+1,576)
        seen=vis[:,MID]|vis[:,OTHER]
        last=np.max(seen*np.arange(k+1)[:,None],axis=0)
        survival=(50-last)/50
        dead=inherited[t].ravel()
        reopening=ZONE@dead.astype(np.int16)
        # Previously observed positions do not produce a new spatial registration in V16.
        for old in known.values():reopening[old]=0
        for name,prior in (('conditional',conditional[known[max(known)]]),('marginal',marginal)):
            if name in commands:continue
            value=prior*survival*reopening
            options=[(-float(value[ORB[c]]),len(p),uid,c,p) for c,(uid,p) in route.items() if value[ORB[c]]>0]
            if not options:continue
            score,_,uid,c,p=min(options)
            commands[name]=dict(depart=t,uid=uid,path=p,score=-score,target=c)
        if len(commands)==2:break
    return commands
