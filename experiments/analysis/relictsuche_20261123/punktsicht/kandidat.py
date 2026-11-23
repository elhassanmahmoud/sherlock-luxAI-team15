"""One permanently assigned nonproducer tries a short posterior-weighted sighting route after a first score."""
from functools import lru_cache
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0,str(HERE.parent/"punkthinweis"))
from belegung import COORD, MID, OTHER, ScoreEvidence
from gelegenheit import DELTA, STEP, XY, candidate_paths, mobile

MIRROR=np.array([0,2,1,4,3],int)
PACKAGE=ROOT/"experiments/releases/20261117_sherlock_v16/agent.zip"
DIST=np.abs(XY[:,None,:]-XY[None,:,:]).max(2).astype(np.int8)


def history():
    return {"sensor_mask":np.zeros((101,24,24),bool),"relic_nodes_mask":np.zeros((101,6),bool),
        "team_points":np.zeros((101,2),np.int32),"units_mask":np.zeros((101,2,16),bool),
        "energy":np.zeros((101,2,16),np.int16),"position":np.zeros((101,2,16,2),np.int16),
        "terrain":np.full((101,24,24),-1,np.int8),"known_points":np.zeros((101,24,24),bool),
        "protected":np.ones((101,16),bool),"move_mask":np.zeros((101,16,5),bool),
        "commands":np.zeros((101,16,3),np.int16)}


@lru_cache(maxsize=1)
def features():
    from sherlock.features import FEATURE_NAMES
    return [FEATURE_NAMES.index(d+"_point") for d in "curdl"],FEATURE_NAMES.index("enemies_in_sap")


def sense_table(board):
    # A single station can reveal either endpoint. Checking the centre itself ignores nebula attenuation.
    terrain=board.ravel()
    rate=np.where(terrain==1,.08,np.where(terrain<0,.75,1.)).astype(np.float32)
    def endpoint(idx):
        d=DIST[:,idx]
        return np.where(d==0,1.,np.where(d==1,rate[idx],0.)).astype(np.float32)
    return np.maximum(endpoint(MID),endpoint(OTHER))


def best_route(d,team,t,proposals,loc):
    if not proposals:
        return None
    see=sense_table(d["terrain"][t])
    live=d["units_mask"][t,team] & (d["energy"][t,team]>=0)
    ids=np.flatnonzero(live)
    commands=d["commands"][t,ids,0]
    move=np.where(commands<=4,commands,0)
    pos=d["position"][t,team,ids]
    p1=np.clip(pos+DELTA[move],0,23)
    p2=np.clip(p1+DELTA[move],0,23)
    board=d["terrain"][t]
    p1=np.where((board[p1[:,0],p1[:,1]]==2)[:,None],pos,p1)
    p2=np.where((board[p2[:,0],p2[:,1]]==2)[:,None],p1,p2)
    expected=np.maximum(see[p1[:,0]*24+p1[:,1]],.8*see[p2[:,0]*24+p2[:,1]])
    # The other ships' near-future coverage, including the mirror endpoint, is discounted.
    plans={}
    for uid in set(q[0] for q in proposals):
        k=np.flatnonzero(ids==uid).item()
        peer=np.max(expected[ids!=uid],axis=0,initial=0.)
        mass=loc*(1-peer)
        plans[uid]=(mass,float(mass@expected[k]))
    best=None
    for uid,goal,direction,path in proposals:
        if len(path)>5:
            continue
        view=see[path[0]].copy()
        for i,tile in enumerate(path[1:],1):
            np.maximum(view,(.94**i)*see[tile],out=view)
        mass,original=plans[uid]
        raw=float(loc@view)
        added=float(mass@view)-original
        if raw<.15 or added<.08:
            continue
        rank=(added/(1+.10*(len(path)-1)),added,raw,-len(path),-uid,-goal)
        if best is None or rank>best[0]:
            best=(rank,int(uid),list(path),raw,added)
    return best


class Agent:
    def __init__(self,base):
        self.base=base
        self.reset()

    def __getattr__(self,name):
        return getattr(self.base,name)

    def reset(self):
        self.team=int(self.base.player[-1])
        self.data=history()
        self.evidence=None
        self.first=None
        self.ship=None
        self.path=[]
        self.changes=0
        self.done=False
        self.expected=None
        self.selected=None
        self.last=None

    def new_game(self,player=None):
        self.base.new_game(player)
        self.reset()

    def set_env_cfg(self,cfg):
        return self.base.set_env_cfg(cfg)

    def observe(self,step,o,cmd):
        d=self.data
        for name in ("sensor_mask","relic_nodes_mask","team_points","units_mask"):
            d[name][step]=o[name]
        for name in ("position","energy"):
            d[name][step]=np.asarray(o["units"][name]).reshape(d[name][step].shape)
        d["commands"][step]=cmd
        p=self.base._imitation
        if p.last_fz is None:
            return
        _,ids,f,m,_,_,_=p.last_fz
        ids=np.asarray(ids,int)
        columns,threat=features()
        d["move_mask"][step,ids]=m[:,:5][:,MIRROR] if self.team else m[:,:5]
        d["protected"][step,ids]=(f[:,columns].max(1)>0)|(f[:,threat]>0)
        for k,grid in (("terrain",p.belief.tile_type),("known_points",p.belief.point_tiles)):
            d[k][step]=grid[::-1,::-1].T if self.team else grid

    def act(self,step,obs):
        cmd=self.base.act(step,obs)
        self.last=None
        if self.done or step>=101 or int(self.base.env_cfg["unit_sensor_range"])!=1:
            return cmd
        if np.any(obs["relic_nodes_mask"]):
            self.done=True
            return cmd
        self.observe(step,obs,cmd)
        if self.first is None:
            if int(obs["team_points"][self.team])==0:
                return cmd
            self.first=step
            self.evidence=ScoreEvidence(self.data,self.team,step)
        if (self.ship is None and (step-self.first>=12 or step>91)) or (self.ship is not None and not self.path):
            self.done=True
            return cmd
        self.evidence.extend(step)
        loc,prob,_,_=self.evidence.estimate()
        cost=int(self.base.env_cfg["unit_move_cost"])
        d=self.data
        if self.ship is None:
            _,_,options=candidate_paths(d,self.team,step,self.first,prob,cost)
            selected=best_route(d,self.team,step,options,loc)
            if selected is None:
                return cmd
            _,self.ship,self.path,raw,added=selected
            self.selected={"t":step,"uid":self.ship,"path":self.path.copy(),"raw":raw,"added":added}
        free,contributors,_,ids,dest=mobile(d,self.team,step,self.first,prob,cost)
        if self.ship not in free:
            self.done=True
            return cmd
        current=d["position"][step,self.team,self.ship]
        start=int(current[0]*24+current[1])
        nxt=self.path[0]
        directions=np.flatnonzero(STEP[start]==nxt)
        if ((self.expected is not None and start!=self.expected) or len(directions)!=1 or directions[0]==0
                or not d["move_mask"][step,self.ship,directions[0]] or d["terrain"][step].ravel()[nxt]==2
                or nxt in dest[ids!=self.ship]):
            self.done=True
            return cmd
        move=int(directions[0])
        self.path.pop(0)
        self.expected=int(nxt)
        if int(cmd[self.ship,0])==move:
            return cmd
        out=cmd.copy()
        out[self.ship]=[move,0,0]
        student=self.base._imitation
        student._prev_actions[self.ship]=int(MIRROR[move]) if self.team else move
        student._sap_hits.pop(self.ship,None)
        student.param_est.record_played_actions(out)
        self.changes+=1
        self.last={"step":step,"ship":self.ship,"contributors":contributors.tolist()}
        return out


def create(side):
    if str(ROOT) not in sys.path:
        sys.path.insert(0,str(ROOT))
    from scripts.r3_package import r3_package_agent
    return Agent(r3_package_agent(side,PACKAGE))
