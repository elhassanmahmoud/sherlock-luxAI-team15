"""A continuously synchronized original R3 proposes one ship's approach to a previously held scoring area."""
from collections import deque
from importlib import import_module
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent; STUDY=HERE.parent; ROOT=STUDY.parents[2]
sys.path.insert(0,str(STUDY.parent/'v16_finalwoche_20261122/fruehuebergabe'))
from staffel import V16, r3_player, r3_package_agent

DXY=((0,0),(0,-1),(1,0),(0,1),(-1,0))
NEIGHBORS={}
for c in range(576):
    x,y=divmod(c,24)
    NEIGHBORS[c]=[(d,24*(x+dx)+y+dy) for d,(dx,dy) in enumerate(DXY) if d and 0<=x+dx<24 and 0<=y+dy<24]


def feedback(r3,obs,proposal,played):
    a=r3._actor
    if a.cfg.dodge_verify or a.cfg.dodge_distrust or a.cfg.dodge_shape or a.training or a._pred_pending or a._shape_pending:
        raise RuntimeError('Unexpected action-dependent R3 configuration')
    prev=a.param_est._prev
    if prev is None:raise RuntimeError('Original R3 did not remember its observation')
    if np.array_equal(proposal,played):return
    prev['act']=np.asarray(played).copy()
    native=import_module(type(a).__module__.split('.')[0]+'.orders')
    enemy=1-a.team_id
    ev=np.asarray(obs['units_mask'][enemy]) & (np.asarray(obs['units']['energy'][enemy]).reshape(-1)>=0)
    opp=np.asarray(obs['units']['position'][enemy])[ev]
    for u in a._prev_actions:
        if np.array_equal(proposal[u],played[u]):continue
        before=int(proposal[u,0]);act=int(played[u,0]);old_hits=a._sap_hits.pop(u,0)
        a._prev_actions[u]=native.canonical_action(played[u],a.belief.mirrored)[0]
        a._sap_unknown.discard(u);hits=0
        if act==5:
            xy=np.asarray(obs['units']['position'][a.team_id,u])+played[u,1:]
            hits=int(np.sum(np.all(np.abs(opp-xy)<=1,axis=1)));a._sap_hits[u]=hits
            if not obs['sensor_mask'][tuple(xy)]:a._sap_unknown.add(u)
        a.ep_stats['sap_attempts']+=int(act==5)-int(before==5)
        a.ep_stats['sap_hits_est']+=int(hits>0)-int(old_hits>0)


def world(array,mirrored):return array[::-1,::-1].T if mirrored else array


def flip(c):return (23-c%24)*24+23-c//24


def dest(c,direction):
    if direction not in (1,2,3,4):return c
    return next((p for d,p in NEIGHBORS[c] if d==direction),c)


def distances(target,safe):
    found={target:0};q=deque([target])
    while q:
        c=q.popleft()
        if found[c]==4:continue
        for _,n in NEIGHBORS[c]:
            if safe[n] and n not in found:found[n]=found[c]+1;q.append(n)
    return found


class Advice:
    def __init__(self,side,apply=True):
        self.base=r3_package_agent(side,V16);self.apply=apply;self.new_game(side)

    def __getattr__(self,name):return getattr(self.base,name)

    def new_game(self,side):
        self.side=side;self.team=int(side[-1]);self.base.new_game(side);self.teacher=None
        self.prior=None;self.first=None;self.finished=False;self.changes=0;self.events=[];self.last_base=None;self.last_r3=None

    def set_env_cfg(self,cfg):
        self.base.set_env_cfg(cfg)
        if int(cfg['unit_sensor_range'])==1:
            self.teacher=r3_player(self.side);self.teacher.new_game(self.side);self.teacher.set_env_cfg(cfg)

    def options(self,obs,base,advice):
        policy=self.base._imitation;b=policy.belief
        if policy.last_fz is None:return []
        from sherlock.features import FEATURE_NAMES
        ctx,ids,features,legal,_,_,_=policy.last_fz
        threat=FEATURE_NAMES.index('enemies_in_sap'); vis=np.asarray(obs['sensor_mask'],bool).ravel()
        points=world(b.point_tiles,b.mirrored).ravel();terrain=world(b.tile_type,b.mirrored).ravel()
        safe=(terrain>=0)&(terrain!=2); rawpos=np.asarray(obs['units']['position']);energy=np.asarray(obs['units']['energy']).reshape(2,-1)
        alive=np.asarray(obs['units_mask'],bool)&(energy>=0)
        cells=24*rawpos[:,:,0]+rawpos[:,:,1];own=cells[self.team]
        goals=self.prior & points & vis & safe
        goals[cells[alive]]=False
        safe[cells[1-self.team,alive[1-self.team]]]=False
        current_uid=None if self.first is None else self.first['uid'];current_goal=None if self.first is None else self.first['goal']
        planned=[dest(int(own[u]),int(base[u,0])) for u in range(16)]
        order=[]
        for target0 in np.flatnonzero(goals):
            target=int(target0)
            if current_goal is not None and current_goal!=target:continue
            dist=distances(target,safe)
            for i,id0 in enumerate(ids):
                uid=int(id0)
                if current_uid is not None and uid!=current_uid:continue
                old=int(base[uid,0]);direction=int(advice[uid,0]);origin=int(own[uid])
                if (not alive[self.team,uid] or energy[self.team,uid]<max(30,4*int(ctx['move_cost'])) or old>4
                        or direction not in (1,2,3,4) or old==direction or points[origin] or features[i,threat]>0):continue
                assigned=ctx['assigned'].get(uid)
                if assigned is not None:
                    a=int(assigned[0])*24+int(assigned[1]);a=flip(a) if b.mirrored else a
                    if points[a] and a!=target:continue
                if any(v!=uid and alive[self.team,v] and planned[v]==target for v in range(16)):continue
                canonical=(0,2,1,4,3)[direction] if b.mirrored else direction
                if not legal[i,canonical]:continue
                d=dist.get(origin,9);alt=dest(origin,direction)
                if d>4 or not safe[alt] or dist.get(alt,9)>=d or dist.get(planned[uid],9)<d:continue
                order.append((d,-int(energy[self.team,uid]),uid,flip(target) if b.mirrored else target,target,direction))
        return sorted(order)

    def act(self,step,obs):
        base=np.asarray(self.base.act(step,obs));self.last_base=base.copy();m,k=divmod(step,101)
        if self.teacher is None or m>=2 or (m==1 and (not obs['team_wins'][self.team] or k>57)):
            return base
        proposed=np.asarray(self.teacher.act(step,obs));self.last_r3=proposed.copy();out=base
        b=self.base._imitation.belief
        if step==100:self.prior=world(b.point_tiles,b.mirrored).ravel().copy()
        if self.first and k-self.first['turn']>=3:self.finished=True
        if m==1 and 8<=k<=57 and not self.finished and (self.first is not None or k<=55):
            choices=self.options(obs,base,proposed)
            if choices:
                distance,_,uid,_,goal,d=choices[0]
                if self.first is None:self.first=dict(step=step,turn=k,uid=uid,goal=goal,distance=distance)
                if self.apply:
                    out=base.copy();out[uid]=[d,0,0]
                    model=self.base._imitation;model._prev_actions[uid]=(0,2,1,4,3)[d] if b.mirrored else d
                    model._sap_hits.pop(uid,None);model.param_est.record_played_actions(out)
                    self.events.append([step,uid,int(base[uid,0]),d,goal]);self.changes+=1
            elif self.first is not None:self.finished=True
        feedback(self.teacher,obs,proposed,out)
        if getattr(self.teacher,'caught_errors',0):raise RuntimeError('Original R3 reported an error')
        return out


def create(side):return Advice(side)
