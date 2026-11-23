"""After the one actual Feldprobe move, offer a single feedback-dependent stay to exactly the same ship."""
from functools import lru_cache
import json
import sys

import numpy as np

from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE))
from rueckmeldung import History,eligible,flat,frame_now,world
from experiments.analysis.relictsuche_20261123.feldprobe.kandidat import create as original_probe

MIRROR=np.array([0,2,1,4,3]);
@lru_cache(maxsize=1)
def model():return json.loads((HERE/'modell.json').read_bytes())['heads']['feedback']

def infer(x):
    head=model();z=(np.asarray(x)-head['mean'])/head['scale'];w=np.asarray(head['weights']);v=z@w[1:]+w[0];exp=np.exp(v-v.max());p=exp/exp.sum();return p.tolist(),bool(p[2]>.4 and p[2]-p[0]>.15)

class Hold:
    def __init__(self,side,arm='chosen'):
        self.probe=original_probe(side);self.base=self.probe.base;self.arm=arm;self.reset()
    def __getattr__(self,k):return getattr(self.probe,k)
    def reset(self):
        self.team=int(self.base.player[-1]);self.h=History(self.team);self.follow=None;self.changes=0;self.changed=False;self.raw=None
    def new_game(self,player=None):self.probe.new_game(player);self.reset()
    def set_env_cfg(self,cfg):return self.probe.set_env_cfg(cfg)
    def act(self,step,obs):
        original=self.probe.act(step,obs);self.raw=np.asarray(original).copy();self.changes=self.probe.changes+int(self.changed)
        e=self.probe.event
        if int(self.base.env_cfg['unit_sensor_range'])!=1 or (e and step>e['t']+1):return original
        m=self.base._imitation;b=m.belief;known=world(b.point_tiles,self.team);self.h.update(step,obs,known)
        if e is None or step!=e['t']+1:return original
        u=e['u'];target=24*e['xy'][0]+e['xy'][1]
        if m.last_fz is None:return original
        ctx,ids,_,masks,*_=m.last_fz;ids=np.asarray(ids,int);allowed=np.zeros((16,5),bool);allowed[ids]=masks[:,:5][:,MIRROR] if self.team else masks[:,:5]
        assigned={}
        for uid,xy in ctx['assigned'].items():
            if xy is not None:
                x,y=map(int,xy);assigned[int(uid)]=24*(23-y)+23-x if self.team else 24*x+y
        terrain=world(b.tile_type,self.team);frame=frame_now(obs,self.team,known,terrain,original,allowed,self.base.env_cfg,assigned)
        guard=eligible(frame,u,target)
        self.follow={'t':step,'uid':u,'target':int(target),'eligible':guard is not None,'selected':False,'original':int(original[u,0]),'signal_gain':self.h.now['gain']}
        if guard is None:return original
        reference,covered=guard;x=self.h.features(target,reference,int(frame['en'][u]),terrain,covered);p,yes=infer(x)
        self.follow.update(reference=reference,x=x.tolist(),probability=p,selected=yes)
        if not yes or self.arm=='control':return original
        out=original.copy();out[u]=[0,0,0];m._prev_actions[u]=0;m._sap_hits.pop(u,None);m.param_est.record_played_actions(out)
        self.changed=True;self.changes=self.probe.changes+1;return out

def create(side):return Hold(side)
