"""Public estimates of whether a persistent zero can have expired since an earlier match."""
from functools import lru_cache
import json
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.spaetgebiet.ortsmodell.ort import COORD, MID, OTHER, ORB, ZONE, priors

HERE=Path(__file__).resolve().parent
XY=np.indices((24,24)).transpose(1,2,0)
PAIR=ORB.reshape(24,24)
NAMES=("match","turn","distance","energy","free_ships","old_pair_0","old_pair_1","current_known","last_seen",
       "previous_zero_age","pair_layer","prior_mass","visible_mass","prior_known_area","distance_old","distance_fresh",
       "ally_score","enemy_score","overlap_old","terrain","centre_distance","near_own","epoch_seen",
       "positions","residual_rate","recent_max","required_in_group","zero_fraction","observation_age","occupied_now")
GEOMETRY=23


class Public:
    def __init__(self):
        self.centers={}
        self.dead=np.zeros((24,24),bool)
        self.inherited=self.dead.copy()
        self.since=np.full(300,-1,int)
        self.seen=np.full(576,-1,int)
        self.last_points=0
        self.score=np.zeros((300,6),np.float64)
        self.last_visit=np.full(300,-1,int)

    def frame(self,t,ob,dead,known,zone,terrain,command,legal,protected,team,move_cost):
        """All arrays are in world coordinates and are available before returning the original action."""
        m,k=divmod(t,101)
        if k==0:
            self.inherited=self.dead.copy()
            self.seen.fill(-1)
            self.score.fill(0)
            self.last_visit.fill(-1)
            self.last_points=0
        self.inherited &= dead
        oldfold=self.dead.reshape(-1)[MID]
        current=dead.reshape(-1)[MID]
        self.since[current&~oldfold]=t
        self.since[~current]=-1
        self.dead=dead.copy()
        seen=np.asarray(ob["sensor_mask"],bool).ravel()
        self.seen[seen]=k
        for idx in np.flatnonzero(ob["relic_nodes_mask"]):
            xy=tuple(np.asarray(ob["relic_nodes"])[idx])
            self.centers[int(idx)%3]=int(PAIR[xy])
        loc=np.asarray(ob["units"]["position"][team])
        ene=np.asarray(ob["units"]["energy"][team]).reshape(-1)
        live=np.asarray(ob["units_mask"][team],bool)&(ene>=0)
        occ=np.unique(loc[live],axis=0)
        score=int(ob["team_points"][team])
        if k and len(occ):
            inc=score-self.last_points
            occupied=tuple(occ.T)
            known_occ=known[occupied]
            unsettled=occ[~known_occ]
            if len(unsettled):
                ix=np.unique(PAIR[tuple(unsettled.T)])
                need=max(0,inc-int(known_occ.sum()))
                fraction=need/len(unsettled)
                required=max(0,need-int((~dead[tuple(unsettled.T)]).sum()))
                self.score[ix,0]+=1
                self.score[ix,1]+=fraction
                self.score[ix,2]=np.maximum(self.score[ix,2],fraction)
                self.score[ix,3]=np.maximum(self.score[ix,3],required/max(1,int(dead[tuple(unsettled.T)].sum())))
                self.score[ix,4]+=int(need==0)
                self.last_visit[ix]=t
        self.last_points=score
        if not m or not 4<=k<=88 or k%4 or not np.any(self.inherited&zone):
            return []
        free=live &(ene>=max(30,4*move_cost)) & ~protected & np.asarray(legal)[:,1:5].any(1) & (command[:,0]<=4)
        units=loc[free]
        if not len(units):
            return []
        distance=np.min(np.abs(XY[:,:,None]-units).sum(axis=-1),axis=2)
        cells=np.argwhere(self.inherited&zone&(distance<=4))
        if not len(cells):
            return []
        marginal,conditional=priors()
        previous=[v for i,v in self.centers.items() if i<m]
        prior=np.mean(conditional[previous],axis=0) if previous else marginal
        last=np.maximum(self.seen[MID],self.seen[OTHER])
        # Publicly seen empty centres require a later activation if the current pair is still hidden.
        mass=prior*np.maximum(0,min(50,k)-np.maximum(0,np.minimum(last,50)))/50
        rows={}
        for x,y in cells:
            here=x*24+y
            j=int(ORB[here])
            dist=int(distance[x,y])
            earlier=rows.get(j)
            if earlier and (dist,here)>=(earlier[2],earlier[1]):
                continue
            near=ZONE[:,here]
            old_dist=min((np.abs(COORD[h]-[x,y]).max() for h in previous),default=24)
            old_dist=min(old_dist,min((np.abs((23-COORD[h][::-1])-[x,y]).max() for h in previous),default=24))
            new=self.centers.get(m)
            new_dist=min(np.abs(COORD[new]-[x,y]).max(),np.abs((23-COORD[new][::-1])-[x,y]).max()) if new is not None else 24
            old_zone=sum(near[h] for h in previous)
            n,tot,largest,required,zero,_=self.score[j]
            nearunit=int(np.argmin(np.abs(units-[x,y]).sum(1)))
            home=x+y if not team else 46-x-y
            attr=[m/2,k/100,dist/4,ene[free][nearunit]/200,len(units)/16,0 in self.centers,1 in self.centers,
                  new is not None,last[j]/100,(t-self.since[j])/303,int(self.since[j])//101,
                  prior[near].sum(),mass[near].sum(),sum(prior[h] for h in previous),
                  min(old_dist,8)/8,min(new_dist,8)/8,score/200,int(ob["team_points"][1-team])/200,old_zone,
                  terrain[x,y],abs(x+y-23)/23,home/46,last[j]>=50,np.log1p(n),tot/max(n,1),
                  largest,required,zero/max(n,1),min(101,t-self.last_visit[j])/101 if n else 1,
                  bool(n and self.last_visit[j]==t)]
            assert len(attr)==len(NAMES)
            rows[j]=(j,int(here),dist,attr)
        return sorted(rows.values())


@lru_cache(maxsize=1)
def fitted():
    return json.loads((HERE/"modell.json").read_text())


def probabilities(x,w):
    z=((np.asarray(x,float)-w["center"])/w["scale"])@np.asarray(w["beta"])+w["bias"]
    return 1/(1+np.exp(-np.clip(z,-40,40)))


def choose(rows,model):
    if not rows:
        return None
    prob=probabilities([r[3] for r in rows],model["full"])
    i=int(np.argmax(prob))
    return (rows[i],float(prob[i])) if prob[i]>=model["threshold"] else None
