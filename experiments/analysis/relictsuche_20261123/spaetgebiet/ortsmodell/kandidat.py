"""After a late geometric score proof, steer one freely moving original V16 ship to a learned sighting station."""
from collections import deque
from functools import lru_cache
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE))
from ort import ORB, MID, OTHER, COORD, DIST, XY, PublicHistory, predict

ZIP=ROOT/'experiments/releases/20261117_sherlock_v16/agent.zip'
MIRROR=np.array([0,2,1,4,3])
DELTA=np.array([[0,0],[0,-1],[1,0],[0,1],[-1,0]],np.int16)
ADJ=np.full((576,5),-1,np.int16)
for move,d in enumerate(DELTA):
    target=XY+d;ok=(target>=0).all(1)&(target<24).all(1)
    ADJ[ok,move]=24*target[ok,0]+target[ok,1]
DLEFT=np.abs(XY[:,None,:]-COORD).max(2)
DRIGHT=np.abs(XY[:,None,:]-(23-COORD[:,::-1])).max(2)

@lru_cache(maxsize=1)
def model():
    return {k:np.asarray(v,float) for k,v in json.loads((HERE/'modell.json').read_bytes()).items()}

@lru_cache(maxsize=1)
def indices():
    from sherlock.features import FEATURE_NAMES
    return [FEATURE_NAMES.index(s+'_point') for s in 'curdl'],FEATURE_NAMES.index('enemies_in_sap')

def frame(o,agent,cmd):
    team=agent.team
    student=agent.base._imitation
    zone=student.belief
    def board(a):return np.asarray(a[::-1,::-1].T if team else a).ravel()
    mask=np.zeros((16,5),bool);protect=np.ones(16,bool)
    if student.last_fz is not None:
        _,ids,f,m,_,_,_=student.last_fz
        ids=np.asarray(ids,int);cols,risk=indices()
        mask[ids]=m[:,:5][:,MIRROR] if team else m[:,:5]
        protect[ids]=(f[:,cols].max(1)>0)|(f[:,risk]>0)
    return {'terrain':board(zone.tile_type),'points':board(zone.point_tiles),'protect':protect,'mask':mask,
        'energy':np.asarray(o['units']['energy']).reshape(2,16)[team], 'live':np.asarray(o['units_mask'],bool)[team],
        'xy':np.asarray(o['units']['position'])[team],'cmd':np.asarray(cmd)[:,0]}

def movable(f,h,cost):
    ids=np.flatnonzero(f['live']&(f['energy']>=0));p=f['xy'][ids];cells=24*p[:,0]+p[:,1]
    cmd=f['cmd'][ids];dest=ADJ[cells,np.minimum(cmd,4)]
    dest=np.where((cmd==5)|(dest<0)|(f['terrain'][np.maximum(dest,0)]==2),cells,dest)
    # An originally stationary possible contributor has priority over a diverted movement.
    free=(cmd<=4)&(~f['protect'][ids])&(f['energy'][ids]>=max(12,3*cost))&(~f['points'][cells])&(~f['points'][dest])
    free &= ~((cmd==0)&(h.gain[0]>0)&(np.bincount(dest,minlength=576)[cells]<=1))
    return ids,cells,dest,free

def route(f,h,cost):
    center,points=predict(h,model())
    if not center.any():return None
    ids,cells,dest,free=movable(f,h,cost)
    if not free.any():return None
    board=f['terrain'];blocked=(board==2)|f['points']|h.foeseen
    # Unit sight one: the center station sees itself. Neighboring nebula centers attenuate vision.
    rate=np.where(board==1,.1,np.where(board<0,.72,1.))
    view=np.maximum(np.where(DLEFT==0,1.,np.where(DLEFT==1,rate[MID],0.)),
                    np.where(DRIGHT==0,1.,np.where(DRIGHT==1,rate[OTHER],0.))).astype(np.float32)
    best=None
    moves=(2,1,4,3) if h.team else (1,2,3,4)
    for i in np.flatnonzero(free):
        uid=int(ids[i]);start=int(cells[i]);orig=int(f['cmd'][uid]); original_pos=int(dest[i])
        other=ids!=uid
        peer=view[dest[other]].max(0,initial=0.)
        mass=(center*(1-.92*peer)).astype(np.float32)
        # Score target is a real formerly unseen opponent scoring field, folded by map symmetry.
        sight=view@mass
        points_station=points[ORB]
        base_sight=float(sight[original_pos]);baseline=float(base_sight+.22*points_station[original_pos]);
        reserved=set(dest[other].tolist()); forbidden=np.copy(blocked)
        forbidden[list(reserved)]=True
        parents={start:(-1,0,0)};q=deque([start]); value={start:(0.,0.)}
        while q:
            at=q.popleft(); _,first,depth=parents[at]
            if depth>=10:continue
            for move in moves:
                nxt=int(ADJ[at,move]);n=depth+1
                if nxt<0 or nxt in parents or forbidden[nxt] or (not depth and not f['mask'][uid,move]):continue
                parents[nxt]=(at,move if not depth else first,n);q.append(nxt)
                v0,v1=value[at];evidence=max(v0,float(sight[nxt])*.96**(n-1));contact=max(v1,float(points_station[nxt])*.96**(n-1));value[nxt]=(evidence,contact)
                firstmove=parents[nxt][1]
                if firstmove==orig:continue
                # Prefer short routes with an endpoint near one of the unobserved relic positions.
                added=(evidence+.22*contact-baseline)/(1+.065*(n-1))
                if added<.045 or evidence<.06:continue
                x,y=XY[nxt];canonical_cell=int((23-y)*24+23-x) if h.team else nxt
                rank=(added,evidence,contact,-n,-uid,-canonical_cell)
                if best is None or rank>best[0]:
                    path=[];p=nxt
                    while p!=start:path.append(p);p=parents[p][0]
                    best=(rank,uid,path[::-1],{'gain':float(added),'sight':float(evidence),'field':float(contact)})
    return best

class Agent:
    def __init__(self,base):self.base=base;self.reset()
    def __getattr__(self,name):return getattr(self.base,name)
    def reset(self):
        self.team=int(self.base.player[-1]);self.history=PublicHistory(self.team)
        self.ship=None;self.path=[];self.expected=None;self.changes=0;self.selected=None;self.alarm=None;self.done=False;self.last=None
    def new_game(self,player=None):self.base.new_game(player);self.reset()
    def set_env_cfg(self,cfg):return self.base.set_env_cfg(cfg)
    def act(self,step,obs):
        o=obs
        cmd=self.base.act(step,o);self.last=None
        if self.done or int(self.base.env_cfg['unit_sensor_range'])!=1:return cmd
        h=self.history;h.update(step,o)
        if self.alarm is None:
            if not h.alarm:return cmd
            self.alarm={'step':step,'known':dict(h.known),'gain':h.gain.tolist(),'limits':list(h.limits)}
        first=self.alarm['step']
        if (step//101!=first//101 or step-first>=16 or h.known!=self.alarm['known'] or
              (self.ship is None and step-first>=6) or (self.ship is not None and not self.path)):
            self.done=True;return cmd
        cost=int(self.base.env_cfg['unit_move_cost']);f=frame(o,self,cmd)
        if self.ship is None:
            choice=route(f,h,cost)
            if choice is None:return cmd
            _,self.ship,self.path,measure=choice
            self.selected={'step':step,'uid':self.ship,'path':self.path.copy(),**measure}
        ids,cells,dest,free=movable(f,h,cost)
        k=np.flatnonzero(ids==self.ship)
        if len(k)!=1 or not free[k[0]]:
            self.done=True;return cmd
        current=int(cells[k[0]]);nxt=self.path[0]
        dirs=np.flatnonzero(ADJ[current]==nxt)
        if (self.expected is not None and current!=self.expected) or len(dirs)!=1 or dirs[0]==0 or not f['mask'][self.ship,dirs[0]] or f['terrain'][nxt]==2 or f['points'][nxt] or h.foeseen[nxt] or nxt in dest[ids!=self.ship]:
            self.done=True;return cmd
        move=int(dirs[0]);self.expected=self.path.pop(0)
        if int(cmd[self.ship,0])==move:return cmd
        out=cmd.copy();out[self.ship]=[move,0,0]
        student=self.base._imitation;student._prev_actions[self.ship]=int(MIRROR[move]) if self.team else move
        student._sap_hits.pop(self.ship,None);student.param_est.record_played_actions(out)
        self.changes+=1;self.last={'step':step,'uid':self.ship,'tile':nxt}
        return out

def create(side):
    if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
    from scripts.r3_package import r3_package_agent
    return Agent(r3_package_agent(side,ZIP))
