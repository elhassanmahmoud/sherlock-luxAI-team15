"""Public proof-driven two-to-four-step trip; a single ship and one decision per complete game."""
from collections import deque
from functools import lru_cache
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]; PROOF=HERE.parent/'punktspeicher'
sys.path.insert(0,str(PROOF))
from beweise import Evidence, PAIR, indices, worlds

ZIP=ROOT/'experiments/releases/20261117_sherlock_v16/agent.zip'
MIRROR=(0,2,1,4,3);D=((0,0),(0,-1),(1,0),(0,1),(-1,0))
STEPS=np.full((576,5),-1,np.int16)
for q in range(576):
    x,y=divmod(q,24)
    for a,(dx,dy) in enumerate(D):
        if 0<=x+dx<24 and 0<=y+dy<24:STEPS[q,a]=24*(x+dx)+y+dy
NAMES=('distance','false_dead','original_stay','turns_left','nearby_peer','nearest_enemy','proof_age','point_holders','alternative_free','lead')

def encoded(a):return int.from_bytes(np.packbits(np.asarray(a,bool).ravel(),bitorder='little').tobytes(),'little')
def cells(obs,s):
    live=np.asarray(obs['units_mask'][s],bool)&(np.asarray(obs['units']['energy'][s]).ravel()>=0)
    p=np.asarray(obs['units']['position'][s])[live];return sorted(set((24*p[:,0]+p[:,1]).tolist()))
def distance(f,g):return abs(f//24-g//24)+abs(f%24-g%24)
def worldrow(o,team,t):
    i=t//101
    return dict(step=t,ms=t%101,occupied=cells(o,team),points=int(o['team_points'][team]),epoch_seen=bool(np.asarray(o['relic_nodes_mask'])[[i,i+3]].any()))

@lru_cache(maxsize=1)
def threat_col():
    from sherlock.features import FEATURE_NAMES
    return FEATURE_NAMES.index('enemies_in_sap')

def policyrow(o,team,base,cmd):
    p=base._imitation;b=p.belief
    def world(a):return a[::-1,::-1].T if b.mirrored else a
    tile=world(b.tile_type);safe=(tile>=0)&(tile!=2)
    energy=np.asarray(o['units']['energy'][team]).ravel();pos=np.asarray(o['units']['position'][team]);live=np.asarray(o['units_mask'][team],bool)&(energy>=0)
    dest={}
    for u in np.flatnonzero(live):
        origin=int(24*pos[u,0]+pos[u,1]);a=int(cmd[u,0]);q=int(STEPS[origin,a]) if a<5 else origin
        dest[int(u)]=q if q>=0 and tile.ravel()[q]!=2 else origin
    parked={}
    for uid in np.flatnonzero(live):
        if int(cmd[uid,0]) in (0,5):parked.setdefault(int(24*pos[uid,0]+pos[uid,1]),[]).append(int(uid))
    free=[]
    if p.last_fz is not None:
        ctx,ids,feat,mask,_,_,_=p.last_fz
        for row,uid in enumerate(ids):
            uid=int(uid);a=int(cmd[uid,0]);start=int(24*pos[uid,0]+pos[uid,1]);goal=ctx['assigned'].get(uid)
            if not live[uid] or a>4 or feat[row,threat_col()]>0 or energy[uid]<max(30,4*int(ctx['move_cost'])):continue
            if goal is not None:
                x,y=map(int,goal);goal=24*(23-y)+23-x if b.mirrored else 24*x+y
            maskbits=sum(1<<d for d in range(1,5) if mask[row,MIRROR[d] if team else d])
            if maskbits:free.append([uid,start,a,goal,maskbits])
    return dict(point=encoded(world(b.point_tiles)),dead=encoded(world(b.dead_tiles)),known_passable=encoded(safe),visible=encoded(o['sensor_mask']),
                enemy=cells(o,1-team),planned=sorted(set(dest.values())),dest=dest,free=free,parked=parked)

def bits(v):return v if isinstance(v,int) else int(v,16)
def is_set(mask,cell):return bool(mask&(1<<cell))
def stationary(policy):
    if 'parked' in policy:return policy['parked']
    parked={}
    for uid,start,cmd,_,_ in policy['free']:
        if cmd==0:parked.setdefault(start,[]).append(uid)
    return parked

def options(pub,policy,ev,team,lead=0):
    t=pub['step'];ms=t%101
    if not 1<=ms<=88:return []
    better=worlds(ev.positive);known=bits(policy['point']);positive=better|known
    occ=set(pub['occupied']);foe=set(policy['enemy']);planned=set(policy['planned']);dead=bits(policy['dead']);safe=bits(policy['known_passable'])
    targets=set(indices((better&~known)&bits(policy['visible'])&safe))-(occ|foe|planned)
    if not targets:return []
    parked=stationary(policy);transit={k for k in parked if is_set(positive,k)}
    result=[]; dirs=(2,1,4,3) if team else (1,2,3,4)
    for uid,origin,old,assigned,legal in policy['free']:
        original=int(STEPS[origin,old]);
        waiting=old==0 and pub.get('gain',0)>0 and not is_set(worlds(ev.negative),origin) and not any(i!=uid for i in parked.get(origin,[]))
        if waiting or is_set(positive,origin) or (assigned is not None and is_set(positive,assigned)) or (original>=0 and is_set(positive,original)):continue
        reserved=set(policy['dest'][j] for j in policy['dest'] if j!=uid) if 'dest' in policy else planned-{original}
        # Shortest known-passable route only. Do not turn a neighbouring target into a two-step detour.
        permitted=targets-{g for g in targets if distance(origin,g)<2}
        if not permitted:continue
        seen={origin};q=deque([(origin,())])
        while q:
            at,path=q.popleft()
            if len(path)==4:continue
            for d in dirs:
                dest=int(STEPS[at,d]);first=(not path)
                if dest<0 or dest in seen or dest in foe or not is_set(safe,dest) or (first and (not legal&(1<<d) or ((dest in reserved or dest in occ) and dest not in transit))):continue
                if is_set(positive,dest) and dest not in permitted and dest not in transit:continue
                seen.add(dest);route=(*path,dest)
                if dest in permitted and len(route)>=2:
                    if route[0]!=original:
                        near_peer=min((distance(dest,v) for v in occ if v!=origin),default=24)
                        nearest_foe=min((distance(dest,v) for v in foe),default=24)
                        feat=[len(route)/4,int(is_set(dead,dest)),int(old==0),(100-ms)/100,min(near_peer,12)/12,min(nearest_foe,12)/12,
                             min(101,t-ev.proofs[PAIR[dest]]['step'])/101,sum(is_set(positive,k) for k in occ)/16,len(policy['free'])/16,np.clip(lead,-200,200)/200]
                        result.append(dict(uid=int(uid),start=int(origin),target=int(dest),route=list(route),old=int(old),x=list(map(float,feat)),proof=ev.proofs[PAIR[dest]]['step']))
                else:q.append((dest,route))
    return result

def choose(opts,team):
    if not opts:return None
    def rank(a):
        length=len(a['route']);dest=a['target'];x,y=divmod(dest,24);canonical=24*(23-y)+23-x if team else dest
        return length,-a['x'][1],-a['x'][5],-a['x'][4],a['uid'],canonical
    return min(opts,key=rank)

def safe_step(o,team,cmd,pub,pol,ev,choice,path):
    uid=choice['uid'];target=choice['target'];nxt=path[0];known=bits(pol['point']);positive=worlds(ev.positive)|known
    free=next((r for r in pol['free'] if r[0]==uid),None)
    if not free:return None
    _,start,old,assigned,legal=free
    if start==target or is_set(known,target) or not is_set(worlds(ev.positive),target):return None
    if not is_set(bits(pol['visible']),target) or target in pub['occupied'] or target in pol['enemy']:return None
    others={v for i,v in pol['dest'].items() if i!=uid}
    orig=int(STEPS[start,old]);parked=stationary(pol)
    through_start=start!=choice['start'] and any(i!=uid for i in parked.get(start,[]))
    through_next=is_set(positive,nxt) and any(i!=uid for i in parked.get(nxt,[]))
    waiting=old==0 and pub.get('gain',0)>0 and not is_set(worlds(ev.negative),start) and not any(i!=uid for i in parked.get(start,[]))
    if (waiting or (is_set(positive,start) and not through_start) or (assigned is not None and is_set(positive,assigned)) or (orig>=0 and is_set(positive,orig) and orig!=target and not (orig==start and through_start))
            or target in others or (nxt in others and not through_next) or nxt in pol['enemy'] or (nxt!=target and is_set(positive,nxt) and not through_next) or not is_set(bits(pol['known_passable']),nxt)):return None
    ds=np.flatnonzero(STEPS[start]==nxt)
    if len(ds)!=1 or ds[0]==0 or not legal&(1<<int(ds[0])):return None
    return int(ds[0]),int(start)

class Agent:
    def __init__(self,base,arm='chosen',model=None):self.base=base;self.arm=arm;self.model=model;self.reset()
    def __getattr__(self,k):return getattr(self.base,k)
    def reset(self):
        self.team=int(self.base.player[-1]);self.ev=Evidence();self.changes=0;self.selected=None;self.active=False;self.path=[];self.expect=None;self.events=[];self.raw=None;self.pub=None;self.pol=None
    def new_game(self,player=None):self.base.new_game(player);self.reset()
    def set_env_cfg(self,cfg):return self.base.set_env_cfg(cfg)
    def act(self,step,obs):
        cmd=self.base.act(step,obs);self.raw=np.asarray(cmd).copy()
        if self.base.env_cfg['unit_sensor_range']!=1:return cmd
        p=worldrow(obs,self.team,step);p['gain']=p['points']-self.ev.previous_score if p['ms'] else 0
        self.ev.observe(p);self.pub=p
        if self.selected is not None and not self.active:return cmd
        if not 1<=p['ms']<=100 or not self.ev.positive:return cmd
        pol=policyrow(obs,self.team,self.base,cmd);self.pol=pol
        if self.selected is None:
            lead=int(obs['team_points'][self.team])-int(obs['team_points'][1-self.team]);s=choose(options(p,pol,self.ev,self.team,lead),self.team)
            if s is None:return cmd
            self.selected={'t':step,**s}; self.path=s['route'].copy()
            self.active=self.arm=='force' or (self.arm=='chosen' and allow(self.model,s['x']))
        if not self.active:return cmd
        if not self.path or step//101!=self.selected['t']//101:
            self.active=False;return cmd
        action=safe_step(obs,self.team,cmd,p,pol,self.ev,self.selected,self.path)
        if action is None or (self.expect is not None and action[1]!=self.expect):self.active=False;return cmd
        move,_=action;uid=self.selected['uid'];self.expect=self.path.pop(0)
        if int(cmd[uid,0])==move:return cmd
        out=cmd.copy();out[uid]=[move,0,0]
        m=self.base._imitation;m._prev_actions[uid]=MIRROR[move] if self.team else move;m._sap_hits.pop(uid,None);m.param_est.record_played_actions(out)
        self.changes+=1;self.events.append([step,uid,int(cmd[uid,0]),move,self.expect]);return out

def allow(model,x):
    if model is None:return False
    z=(np.asarray(x)-model['mean'])/model['scale'];b=np.array(model['coef']);return bool(b[0]+z@b[1:]>.5)

def create(side):
    if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
    from scripts.r3_package import r3_package_agent
    model=json.loads((HERE/'modell.json').read_text())
    return Agent(r3_package_agent(side,ZIP),'chosen',model)
