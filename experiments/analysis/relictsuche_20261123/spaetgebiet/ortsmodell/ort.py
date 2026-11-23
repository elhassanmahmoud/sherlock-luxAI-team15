"""Public-only location features. Index physical cells x*24+y and mirror orbits once."""
from functools import lru_cache
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from signalgrenze import bounds

COORD=np.array([(x,y) for x in range(24) for y in range(24) if x+y<24],np.int16)
XY=np.indices((24,24),dtype=np.int16).reshape(2,-1).T
MID=24*COORD[:,0]+COORD[:,1]
MIR=23-COORD[:,::-1]
OTHER=24*MIR[:,0]+MIR[:,1]
ORB=np.empty(576,np.int16); ORB[MID]=ORB[OTHER]=np.arange(300)
DIST=np.minimum(np.abs(XY[:,None,:]-COORD).max(2),np.abs(XY[:,None,:]-MIR).max(2))
ZONE=(DIST.T<=2); Z=ZONE.astype(np.float32)
OLD=HERE.parents[2]/'v16_finalwoche_20261122/reliktorte/paarhaeufigkeiten.npz'

def orbit(a):
    a=np.asarray(a).reshape(-1)
    return np.maximum(a[MID],a[OTHER])

@lru_cache(maxsize=1)
def priors():
    with np.load(OLD) as data:
        if not np.array_equal(data['coords'],COORD):raise ValueError('Old prior uses different coordinates')
        counts=data['counts'].astype(float)
    marginal=counts.sum(0)+.5; marginal/=marginal.sum()
    cond=counts+32*marginal; cond/=cond.sum(1,keepdims=True)
    return marginal,cond

def bitmask(a):
    return int.from_bytes(np.packbits(a,bitorder='little').tobytes(),'little')

ZONE_BITS=tuple(bitmask(z) for z in ZONE)

def enough(options,need):
    """Decide whether enough distinct physical cells can be assigned to different ships."""
    if need<=0:return True
    ships=sorted((x for x in options if x),key=int.bit_count)
    if len(ships)<need:return False
    assigned={}
    def find(unit,visited):
        candidates=ships[unit]
        while candidates:
            cell=candidates&-candidates
            candidates-=cell
            if cell in visited:continue
            visited.add(cell)
            other=assigned.get(cell)
            if other is None or find(other,visited):
                assigned[cell]=unit
                return True
        return False
    hits=0
    for i in range(len(ships)):
        hits+=find(i,set())
        if hits>=need:return True
    return False

class PublicHistory:
    def __init__(self,team):
        self.team=team
        self.known={}
        self.last_seen=np.full(300,-1000,np.int16)
        self.score=np.zeros(2,int)
        self.reach=np.zeros((16,24,24),bool)
        self.heat=np.zeros((2,576),np.float32)
        self.allowed=np.ones(300,bool)
        self.first_proof=None
        self.last_signature=None
        self.last_observed=np.full(16,-1000,np.int16)
        self.last_enemy=np.zeros((16,2),np.int16)
        self.prior=None

    def update(self,t,o):
        self.t=t
        mi,ms=divmod(t,101)
        sensor=np.asarray(o['sensor_mask'],bool)
        visible_orbit=orbit(sensor)
        self.last_seen[visible_orbit]=t
        if not ms:
            self.reach[:]=False;self.heat[:]=0;self.last_observed[:]=-1000
            self.score=np.asarray(o['team_points'],int).copy()
            self.last_signature=None
        rm=np.asarray(o['relic_nodes_mask'],bool)
        for i in np.flatnonzero(rm):
            p=np.asarray(o['relic_nodes'][i],int)
            self.known[int(i%3)]=int(ORB[24*p[0]+p[1]])
        sig=tuple(sorted(self.known.items()))
        if self.last_signature!=sig:
            self.first_proof=None;self.allowed[:]=True
            self.zone=ZONE[list(self.known.values())].any(0) if self.known else np.zeros(576,bool)
            self.zone_bits=bitmask(self.zone)
            prior,cond=priors()
            self.prior=(.7*prior+.3*cond[list(self.known.values())].mean(0)) if self.known else prior
            self.last_signature=sig
        scores=np.asarray(o['team_points'],int)
        gains=scores-self.score
        self.gain=gains[[self.team,1-self.team]]
        self.score=scores.copy()
        self.limits=bounds(o,self.team,self.zone.reshape(24,24))
        self.alarm=bool(mi in (1,2) and 10<=ms<=80 and self.known and np.any(self.gain>self.limits))
        if self.alarm and self.first_proof is None:self.first_proof=t
        self.certain=mi+1-len(self.known)==1
        q=self.reach
        nxt=q.copy();nxt[:,1:]|=q[:,:-1];nxt[:,:-1]|=q[:,1:];nxt[:,:,1:]|=q[:,:,:-1];nxt[:,:,:-1]|=q[:,:,1:]
        corner=23 if self.team==0 else 0
        nxt[:,corner,corner]=True
        nxt[:,sensor]=False
        pos=np.asarray(o['units']['position'],int)
        masks=np.asarray(o['units_mask'],bool)
        energies=np.asarray(o['units']['energy']).reshape(2,16)
        foe=1-self.team
        for i in np.flatnonzero(masks[foe]):
            nxt[i]=False
            p=pos[foe,i]; nxt[i,p[0],p[1]]=True
            self.last_observed[i]=t;self.last_enemy[i]=p
        self.reach=nxt
        own=np.zeros(576,bool);foeseen=np.zeros(576,bool)
        for team,board in ((self.team,own),(foe,foeseen)):
            p=pos[team,masks[team]&(energies[team]>=0)]
            board[p[:,0]*24+p[:,1]]=True
        self.own=own;self.foeseen=foeseen
        evidence=nxt.reshape(16,-1).copy()
        evidence[masks[foe]&(energies[foe]<0)]=False
        self.enemy_evidence=evidence
        # Uniform reachable positions mixed with recent, locally concentrated occupancy.
        # The hard capacity always retains the full reachable sets, including respawns.
        base=evidence.astype(np.float32)
        base/=np.maximum(1,base.sum(1))[:,None]
        recent=np.flatnonzero(t-self.last_observed<=12)
        if len(recent):
            radius=np.abs(XY[None,:,:]-self.last_enemy[recent,None,:]).sum(2)
            narrow=evidence[recent]*np.exp(-radius/(1+(t-self.last_observed[recent,None])*.45))
            narrow/=np.maximum(1.e-8,narrow.sum(1))[:,None]
            base[recent]=.8*narrow+.2*base[recent]
        self.enemy_prob=base.sum(0)
        self.heat*=.8
        for i,occ in enumerate((own,self.enemy_prob)):
            extra=occ*(~self.zone)
            if self.gain[i]>0:self.heat[i]+=(min(3,self.gain[i])/3)*extra/max(1.,extra.sum())
        if self.certain and self.first_proof is not None:
            self.allowed &= ~visible_orbit
            own_extra=int(self.gain[0])-self.limits[0]
            if own_extra>0:self.allowed &= (Z@(own&~self.zone).astype(np.float32))>=own_extra
            if self.gain[1]>self.limits[1]:
                bits=[bitmask(x) for x in evidence]
                for c in np.flatnonzero(self.allowed):
                    union=self.zone_bits|ZONE_BITS[c]
                    if not enough([r&union for r in bits],int(self.gain[1])):self.allowed[c]=False

    def features(self):
        mi,ms=divmod(self.t,101)
        since=mi*101+50 if ms>=50 else self.t
        if self.certain and self.first_proof is not None:since=min(since,self.first_proof)
        allowed=(self.last_seen<since)&self.allowed
        off=(~self.zone).astype(np.float32)
        marginal,_=priors()
        kd=DIST[MID][:,list(self.known.values())].min(1) if self.known else np.full(300,24)
        signals=np.stack((off,off*self.own,off*self.foeseen,off*self.enemy_prob,off*self.heat[0],off*self.heat[1]),axis=1)
        offcount,own,rival,mass,ownheat,foeheat=(Z@signals).T
        age=np.clip(self.t-self.last_seen,0,50)/50.
        c=np.stack((np.log(self.prior*300),np.log(marginal*300),np.minimum(kd,10)/5.,offcount/50,
            np.log1p(own),np.log1p(rival),np.log1p(mass),np.log1p(5*ownheat),np.log1p(5*foeheat),
            np.log1p(own)*min(2,max(0,self.gain[0]-self.limits[0])),
            np.log1p(mass)*min(2,max(0,self.gain[1]-self.limits[1])),age),axis=1).astype(np.float32)
        field=np.stack((orbit(self.foeseen),np.log1p(orbit(self.enemy_prob)),np.log1p(12*orbit(self.heat[1])),
            orbit(self.own),np.log1p(12*orbit(self.heat[0])),kd.clip(0,8)/4.,age),axis=1).astype(np.float32)
        return c,allowed,field,~orbit(self.zone)


def softmax(logits,mask):
    if not np.any(mask):return np.zeros(len(mask))
    v=np.zeros(len(mask));v[mask]=np.exp(logits[mask]-np.max(logits[mask]));return v/v.sum()

def predict(history,model):
    c,support,q,off=history.features()
    center=softmax(c@model['center'],support)
    coverage=(Z[:,MID].T@center).clip(1.e-7,1.)
    score=softmax(q@model['points'][:-1]+model['points'][-1]*np.log(coverage),off&((Z[:,MID].T@support.astype(np.float32))>0))
    return center,score
