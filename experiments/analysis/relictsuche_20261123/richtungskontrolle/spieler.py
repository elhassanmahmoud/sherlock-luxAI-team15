"""First publicly eligible direction pair, then exactly one action or unmodified V16."""
import numpy as np

from experiments.analysis.relictsuche_20261123.flottenblick.flotte import (
    DIRECTIONS, DX, DY, GAP, MIRROR_DIR, flat, option_frame, support,
)
from experiments.analysis.relictsuche_20261123.ortundflotte.kandidat import create
from experiments.analysis.relictsuche_20261123.vergleich.spielen import PACKAGE, require
from scripts.r3_package import r3_package_agent


def one_view(origin, fog):
    cell=int(flat(origin))
    weight=np.where(fog.ravel(),.25,1.)*(GAP[cell]<=1)
    weight[cell]=1.
    return weight


def pair(frame,history,learned):
    ids,_,_=support(frame)
    options=sorted(set(int(d) for d in DIRECTIONS[ids,0]))
    require(learned in options,'First learned movement lacks its public route support')
    ctx=frame['ctx'];fog=ctx['nebula'];energy=ctx['energy_map'];new=history.last_seen.ravel()<0
    rest=np.zeros(576)
    for q in frame['next']:
        # Off-board projections for other ships remain physically at the boundary.
        rest=np.maximum(rest,one_view(np.clip(q,0,23),fog))
    measured={}
    for direction in options:
        require(frame['first'][direction], 'Illegal supported first move')
        xy=frame['start']+np.array([DX[direction],DY[direction]])
        gain=np.maximum(0,one_view(xy,fog)-rest)[new].sum()
        measured[direction]=dict(gain=float(gain),fog=bool(fog[tuple(xy)]),energy=float(energy[tuple(xy)]),dest=xy.tolist())
    ref=measured[learned]
    pairs=[]
    for direction,other in measured.items():
        dv=abs(other['gain']-ref['gain']);de=abs(other['energy']-ref['energy'])
        if direction not in (learned,frame['original']) and ref['fog']==other['fog'] and dv<=1. and de<=2.:
            pairs.append((dv,de,direction))
    return measured,min(pairs)[2] if pairs else None


class OneMove:
    def __init__(self, side, mode):
        self.mode=mode
        self.base=r3_package_agent(side,PACKAGE)
        self.scout=create(side)
        self.new_game(side)
        raw=self.scout.base.act
        def shadow_action(*args,**kwargs):
            a=raw(*args,**kwargs)
            require(np.array_equal(a,self.original), 'Separate policy copies diverged before the first intervention')
            return a
        self.scout.base.act=shadow_action

    def __getattr__(self,name):
        return getattr(self.base,name)

    def new_game(self,side):
        self.base.new_game(side)
        self.scout.new_game(side)
        self.finished=False;self.changes=0;self.decision=None;self.original=None

    def set_env_cfg(self,cfg):
        self.base.set_env_cfg(cfg);self.scout.set_env_cfg(cfg)

    def act(self,step,obs):
        a=self.base.act(step,obs)
        if self.finished:return a
        self.original=a.copy()
        provisional=self.scout.act(step,obs)
        delta=np.flatnonzero(np.any(a!=provisional,axis=1))
        if not len(delta):
            self.finished=self.scout.done
            return a
        require(len(delta)==1 and self.scout.uid==int(delta[0]), 'Ambiguous earliest learned movement')
        uid=int(delta[0]);team=self.base.team_id
        to_world=lambda d:int(MIRROR_DIR[d]) if team else int(d)
        learned=to_world(int(provisional[uid,0]))
        p=self.base._imitation
        frame=option_frame(p.last_fz,a,self.scout.history,team,uid)
        require(frame is not None, 'First learned action failed the original public safety frame')
        measured,other=pair(frame,self.scout.history,learned)
        self.decision=dict(step=int(step),uid=uid,origin=frame['start'].tolist(),energy=int(frame['energy']),
                           original=int(a[uid,0]),learned=to_world(learned),alternative=to_world(other) if other is not None else None,
                           views={str(to_world(d)):v for d,v in measured.items()})
        self.finished=True
        if other is None or self.mode=='original':return a
        chosen=learned if self.mode=='gelernt' else other
        out=a.copy();out[uid]=[to_world(chosen),0,0]
        p._prev_actions[uid]=int(chosen)
        p._sap_hits.pop(uid,None)
        p.param_est.record_played_actions(out)
        self.changes=1
        return out
