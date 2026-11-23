"""Public evidence and one affordable local probe. The referee map is never an input."""
from pathlib import Path
import json
import numpy as np

SIZE=24
XY=np.indices((SIZE,SIZE)).transpose(1,2,0)
X,Y=np.indices((SIZE,SIZE))
PAIR=np.minimum(X*SIZE+Y,(23-Y)*SIZE+23-X)
DELTA=np.array(((0,0),(0,-1),(1,0),(0,1),(-1,0)),int)
STATIC=("known_zone","overlap","center_distance","axis_distance","home_distance","fog","rock","turn","match","energy","base_stay","occupied_now")
HISTORY=("observed","recent_seen","recent_max","recent_mean","recent_lower","recent_zero","ever_max","ever_lower","last_visit","first_moment")
NAMES=STATIC+HISTORY
HERE=Path(__file__).resolve().parent


class Evidence:
    def __init__(self):
        self.lifetime_n=np.zeros(576,int)
        self.lifetime_max=np.zeros(576)
        self.lifetime_lower=np.zeros(576)
        self.first=np.full(576,-1,int)
        self.landmarks=set()
        self.zones=np.zeros((SIZE,SIZE),int)
        self.dist=np.full((SIZE,SIZE),24,int)
        self.start_round()

    def start_round(self):
        self.seen_keys=set()
        self.last=np.full(576,-1,int)
        self.recent_n=np.zeros(576,int)
        self.recent_sum=np.zeros(576)
        self.recent_max=np.zeros(576)
        self.recent_low=np.zeros(576)
        self.recent_zero=np.zeros(576,int)

    def observe(self,turn,positions,gain,known):
        if turn==0:
            self.start_round()
            return
        if not len(positions):
            if gain:
                raise ValueError("Points without an occupied tile")
            return
        coords=np.unique(positions,axis=0)
        ids=PAIR[tuple(coords.T)]
        known_count=int(known[tuple(coords.T)].sum())
        unknown=tuple(sorted(ids[~known[tuple(coords.T)]].tolist()))
        residual=gain-known_count
        if residual<0 or residual>len(unknown):
            # Current public inference can occasionally include a new field in a changed
            # game. An inconsistent observation carries no usable soft attribution.
            return
        if not unknown:
            return
        idx,weight=np.unique(unknown,return_counts=True)
        self.last[idx]=turn
        identity=(unknown,residual)
        if identity in self.seen_keys:
            return
        self.seen_keys.add(identity)
        fraction=residual/len(unknown)
        # The same unknown scoring bit can represent both opposite world ends.
        lower=np.maximum(0,(residual-(len(unknown)-weight))/weight)
        self.lifetime_n[idx]+=1
        self.lifetime_max[idx]=np.maximum(self.lifetime_max[idx],fraction)
        self.lifetime_lower[idx]=np.maximum(self.lifetime_lower[idx],lower)
        self.first[idx]=np.where(self.first[idx]<0,turn,self.first[idx])
        self.recent_n[idx]+=1
        self.recent_sum[idx]+=fraction
        self.recent_max[idx]=np.maximum(self.recent_max[idx],fraction)
        self.recent_low[idx]=np.maximum(self.recent_low[idx],lower)
        self.recent_zero[idx]+=int(residual==0)

    def relics(self,coords):
        for x,y in coords:
            for cell in ((int(x),int(y)),(23-int(y),23-int(x))):
                if cell in self.landmarks:
                    continue
                self.landmarks.add(cell)
                d=np.abs(XY-np.asarray(cell)).max(2)
                self.zones+=d<=2
                self.dist=np.minimum(self.dist,d)

    def features(self,xy,turn,match,cfg):
        loc=tuple(xy)
        k=PAIR[loc]
        team=cfg["team"]
        x,y=loc
        terrain=cfg["terrain"][loc]
        n=self.recent_n[k]
        return [self.zones[loc]>0,self.zones[loc],min(6,self.dist[loc]),abs(x+y-23)/23,
            (x+y if team==0 else 46-x-y)/46,terrain==1,terrain==2,turn/100,match/3,
            cfg["energy"]/200,cfg["base_stay"],loc in cfg["occupied"],np.log1p(self.lifetime_n[k]),np.log1p(n),
            self.recent_max[k],self.recent_sum[k]/max(1,n),self.recent_low[k],self.recent_zero[k]/max(1,n),
            self.lifetime_max[k],self.lifetime_lower[k],1./(1+turn-self.last[k]) if self.last[k]>=0 else 0,
            self.first[k]/100 if self.first[k]>=0 else -1]


def options(history,turn,match,team,position,energies,alive,known,terrain,commands,mask,protected,move_cost):
    if not (8<=turn<=84 and turn%4==0 and history.landmarks):
        return []
    alive=np.asarray(alive,bool)&(np.asarray(energies).reshape(-1)>=0)
    ids=np.flatnonzero(alive)
    if not len(ids):
        return []
    codes=commands[ids,0].astype(int)
    dest=np.clip(position[ids]+DELTA[np.where(codes<=4,codes,0)],0,23)
    occupied={tuple(v) for v in position[ids]}
    planned={tuple(v) for v in dest}
    rows=[]
    for j,u in enumerate(ids):
        if protected[u] or codes[j]>4 or energies[u]<max(30,4*move_cost) or known[tuple(dest[j])]:
            continue
        moves=[]
        for d in range(1,5):
            if not mask[u,d] or d==codes[j]:
                continue
            point=position[u]+DELTA[d]
            if (point<0).any() or (point>=SIZE).any():
                continue
            loc=tuple(point)
            if loc in occupied or loc in planned or not history.zones[loc] or known[loc] or terrain[loc]==2:
                continue
            moves.append((d,loc))
        if not moves:
            continue
        cfg=dict(team=team,terrain=terrain,energy=float(energies[u]),base_stay=codes[j]==0,occupied=occupied)
        ref=tuple(map(int,dest[j]))
        xref=history.features(ref,turn,match,cfg)
        for d,loc in moves:
            rows.append((int(u),int(d),tuple(map(int,loc)),ref,history.features(loc,turn,match,cfg),xref))
    return rows


def proba(model,features):
    n=len(model["mean"])
    x=(np.asarray(features,dtype=float)[...,:n]-model["mean"])/model["scale"]
    z=x@np.asarray(model["beta"])+model["intercept"]
    return 1/(1+np.exp(-np.clip(z,-40,40)))


def pick(rows,model):
    if not rows:
        return None
    new=proba(model,[r[4] for r in rows])
    old=proba(model,[r[5] for r in rows])
    best=None
    for i,(a,b) in enumerate(zip(new,old,strict=True)):
        if a>=.55 and a-b>=.25:
            key=(float(a-b),float(a),-rows[i][0],-rows[i][1])
            if best is None or key>best[0]:
                best=(key,i)
    return None if best is None else int(best[1])


def parameters():
    return json.loads((HERE/"modell.json").read_text())["full"]
