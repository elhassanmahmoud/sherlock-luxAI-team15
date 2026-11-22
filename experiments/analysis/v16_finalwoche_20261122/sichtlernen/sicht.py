"""Estimate the added team visibility of one alternative using public positions and public memory."""
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
from agents.sherlock import geometry as geo
from agents.sherlock.features import FEATURE_NAMES

XY=np.indices((24,24)).reshape(2,-1).T
OPPOSITE=(23-XY[:,1])*24+(23-XY[:,0])
PAIR=np.minimum(np.arange(576),OPPOSITE)
DIAGONAL=np.arange(576)==OPPOSITE
WEIGHTS=np.where(DIAGONAL,1.,.5)
SQUARE={r:(np.abs(XY[:,None]-XY).max(2)<=r) for r in (1,2)}
POINT=[FEATURE_NAMES.index(i+"_point") for i in "curdl"]
THREAT=FEATURE_NAMES.index("enemies_in_sap")
NAMES=("extra_pairs","extra_cells","sensor","turn","energy","move_cost","was_stay","seen_fraction",
       "alt_nebula","original_nebula","alt_tile_energy","original_tile_energy","ally_count")


def new_area(now, seen):
    both=now|now[OPPOSITE]
    old=seen|seen[OPPOSITE]
    return float(WEIGHTS[both & ~old].sum()),int((now & ~seen).sum())


class Scout:
    def __init__(self,base,params=None):
        self.base=base
        self.params=params
        self.seen=np.zeros(576,dtype=bool)
        self.last=[]
        self.changed=0

    def __getattr__(self,name):
        return getattr(self.base,name)

    def act(self,step,obs):
        action=self.base.act(step,obs)
        p=self.base._imitation
        public=np.asarray(obs["sensor_mask"],dtype=bool)
        self.seen|=(geo.mirror_map(public) if p.belief.mirrored else public).ravel()
        self.last=[]
        if 10<=step<=45 and p.last_fz is not None and int(p.belief.sensor_range)<=2:
            self.last=self.options(action,p)
        if self.params is None or not self.last:
            return action
        w,b=self.params
        row=max(self.last,key=lambda q:(float(q[3] @ w+b),-q[1]))
        if float(row[3] @ w+b)<1.5:
            return action
        out=action.copy()
        out[row[1]]=[row[2],0,0]
        self.changed+=1
        return out

    def options(self,action,p):
        ctx,ids,f,masks,_,planes,pos=p.last_fz
        live=np.asarray([ctx["ally_ene"][u]>=0 for u in ids])
        if not live.any():return []
        real=action[ids,0]
        direction=np.where(real<=4,real,0)
        if p.belief.mirrored:direction=geo.MIRROR_DIR[direction]
        dest=pos+np.stack((geo.DIR_DX[direction],geo.DIR_DY[direction]),axis=1)
        keys=dest[:,0]*24+dest[:,1]
        r=int(p.belief.sensor_range)
        square=SQUARE[r]
        all_sensor=square[keys[live]].sum(0,dtype=np.int16)
        base_pairs,base_phys=new_area(all_sensor>0,self.seen)
        reserved=np.bincount(keys[live],minlength=576)
        suitable=(live & (real<=4) & (f[:,POINT].max(1)==0) & (f[:,THREAT]==0)
                  & np.asarray([ctx["ally_ene"][u]>=3*ctx["move_cost"] for u in ids]))
        candidates=[]
        for k in np.flatnonzero(suitable):
            old=int(keys[k])
            rest=all_sensor-square[old]
            best=None
            for alt in np.flatnonzero(masks[k,1:5])+1:
                if alt==direction[k]:continue
                x,y=pos[k]+(geo.DIR_DX[alt],geo.DIR_DY[alt])
                target=int(x*24+y)
                if not (0<=x<24 and 0<=y<24) or reserved[target]:continue
                alt_pairs,alt_phys=new_area((rest+square[target])>0,self.seen)
                pair_gain=alt_pairs-base_pairs
                cell_gain=alt_phys-base_phys
                ranking=pair_gain+.2*cell_gain
                if ranking<=0 or max(pair_gain,cell_gain)<1:continue
                order=(ranking,-int(alt))
                if best is not None and order<=best[0]:continue
                bx,by=divmod(old,24)
                values=np.array((pair_gain,cell_gain,r/2,ctx["match_step"]/45,
                                 min(ctx["ally_ene"][ids[k]],400)/400,ctx["move_cost"]/5,
                                 float(real[k]==0),self.seen.mean(),planes[6,x,y],planes[6,bx,by],
                                 planes[7,x,y],planes[7,bx,by],live.sum()/16),np.float32)
                world=geo.mirror_dir(alt) if p.belief.mirrored else int(alt)
                best=(order,(ranking,int(ids[k]),world,values))
            if best is not None:candidates.append(best[1])
        return sorted(candidates,key=lambda item:(-item[0],item[1],item[2]))[:2]
