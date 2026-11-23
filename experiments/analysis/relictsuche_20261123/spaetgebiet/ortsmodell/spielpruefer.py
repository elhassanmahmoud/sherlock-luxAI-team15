"""Full game monitor with independent late-window, role, coverage and V16 action audits."""
from hashlib import sha256
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE.parent))
from signalgrenze import bounds
from scripts.scoring import match_points_after_step
from scripts.r3_package import _module_for

PACKAGE=ROOT/'experiments/releases/20261117_sherlock_v16/agent.zip'
MIRROR=[0,2,1,4,3]
MOVES=np.array([(0,0),(0,-1),(1,0),(0,1),(-1,0)])
XY=np.indices((24,24)).transpose(1,2,0)

def check(condition,message):
    if not condition:raise ValueError(message)

class Monitor:
    def __init__(self,env,team,agent):
        self.env=env;self.team=team;self.side=f'player_{team}';self.actor=agent
        self.t=0;self.known={};self.firsts={};self.anchor=None;self.proposal=None;self.events=[];self.matches=[];self.scores=np.zeros(2,int)
        self.prefix=[];self.digest=sha256();self.own_digest=sha256();self.audit=[0,0];self.outside=[0,0];self.first_match_hash=None
        if agent is not None:
            _,course=_module_for(PACKAGE.resolve());check(type(agent.base) is course.Agent_x,'Wrong actual base')
            original=agent.base.act
            def capture(*args,**kwargs):
                check(self.proposal is None,'Called V16 twice');v=original(*args,**kwargs);self.proposal=np.asarray(v).copy();return v
            agent.base.act=capture

    def reset(self,**kwargs):
        v=self.env.reset(**kwargs);self.o=v[0][self.side];self.cfg=v[1]['params'];check(self.cfg['unit_sensor_range']==1,'Wrong sight');return v

    def step(self,actions):
        t=self.t;mi,ms=divmod(t,101);o=self.o;team=self.team
        check(int(o['steps'])==t and int(o['match_steps'])==ms,'Noncontiguous play')
        active_ids=np.flatnonzero(o['relic_nodes_mask'])
        for i in active_ids:
            x,y=map(int,o['relic_nodes'][i]);slot=int(i%3)
            self.known[slot]=min((x,y),(23-y,23-x));self.firsts.setdefault(slot,t)
        region=np.zeros((24,24),bool)
        for x,y in self.known.values():
            region|=(np.max(np.abs(XY-[x,y]),axis=2)<=2)|(np.max(np.abs(XY-[23-y,23-x]),axis=2)<=2)
        score=np.asarray(o['team_points'],int);g=(score-self.scores)[[team,1-team]] if ms else np.zeros(2,int);self.scores=score.copy()
        cap=bounds(o,team,region)
        live_true=np.asarray(self.env.state.units_mask,bool)&(np.asarray(self.env.state.units.energy).reshape(2,16)>=0)
        true_pos=np.asarray(self.env.state.units.position)
        active=np.asarray(self.env.state.relic_nodes_mask,bool)[:3];weight=np.asarray(self.env.state.relic_nodes_map_weights)
        scoring=(weight>0)&(weight<=sum(active));outside=[]
        if ms:
            for s in (team,1-team):
                p=true_pos[s,live_true[s]];occ=np.zeros((24,24),bool);occ[p[:,0],p[:,1]]=True
                check(int((occ&scoring).sum())==g[0 if s==team else 1],'Actual credited cells disagree with public points')
                outside.append(int((occ&scoring&~region).sum()))
            if mi:self.outside=[a+b for a,b in zip(self.outside,outside,strict=True)]
        triggered=mi in (1,2) and 10<=ms<=80 and bool(self.known) and np.any(g>cap)
        if triggered and self.anchor is None:
            missing=[int(i) for i in np.flatnonzero(active) if i not in self.known]
            check(missing and any(outside),'Geometric warning has no true external score')
            self.anchor=dict(t=t,known=sorted(self.known),ids=missing,gain=g.tolist(),cap=list(cap),outside=outside)
        self.prefix.append(self.digest.hexdigest()[:24])
        for s in (0,1):
            a=np.asarray(actions[f'player_{s}']);check(a.shape==(16,3) and np.issubdtype(a.dtype,np.integer) and np.all((a[:,0]>=0)&(a[:,0]<=5)),'Malformed actions')
            packet=a.astype('<i4',copy=False).tobytes();self.digest.update(packet);self.audit[s]+=1
            if s==team:self.own_digest.update(packet)
        if self.actor is not None:
            check(self.proposal is not None,'Skipped base');played=np.asarray(actions[self.side]);changed=np.flatnonzero(np.any(played!=self.proposal,axis=1))
            check(len(changed)<=1,'Modified multiple ships')
            if len(changed):
                uid=changed.item();before=self.proposal[uid];after=played[uid];move=int(after[0]);a=self.actor
                check(self.anchor is not None and a.alarm['step']==self.anchor['t'] and self.anchor['known']==sorted(self.known),'Outside first public geometric alert')
                check(mi in (1,2) and mi==self.anchor['t']//101 and 0<=t-self.anchor['t']<16 and 0<=a.selected['step']-self.anchor['t']<6 and 0<=t-a.selected['step']<10,'Outside allowed late window')
                check(all(e[1]==uid for e in self.events) and uid==a.ship==a.selected['uid'],'Switched scout identity')
                check(0<=before[0]<=4 and 1<=move<=4 and before[0]!=move and not after[1:].any(),'Overwrote SAP or emitted invalid action')
                check(bool(o['units_mask'][team,uid]) and o['units']['energy'][team,uid].item()>=max(12,3*int(self.cfg['unit_move_cost'])),'No free energy reserve')
                student=a.base._imitation; _,ids,f,m,_,_,_=student.last_fz; i=np.flatnonzero(np.asarray(ids)==uid).item()
                from sherlock.features import FEATURE_NAMES
                cols=[FEATURE_NAMES.index(s+'_point') for s in 'curdl'];threat=FEATURE_NAMES.index('enemies_in_sap');canonical=MIRROR[move] if team else move
                check(m[i,canonical] and not np.any(f[i,cols]>0) and f[i,threat]<=0,'Protected field, threatened ship or masked move')
                b=student.belief; confirmed=np.asarray(b.point_tiles[::-1,::-1].T if team else b.point_tiles,bool);terrain=np.asarray(b.tile_type[::-1,::-1].T if team else b.tile_type)
                p=np.asarray(o['units']['position'][team,uid]); nxt=p+MOVES[move]
                check((nxt>=0).all() and (nxt<24).all() and not confirmed[tuple(p)] and not confirmed[tuple(nxt)] and terrain[tuple(nxt)]!=2,'Prohibited current or next tile')
                ids_live=np.flatnonzero(np.asarray(o['units_mask'][team],bool)&(np.asarray(o['units']['energy'][team]).reshape(-1)>=0))
                cur=np.asarray(o['units']['position'][team])[ids_live];cmd=self.proposal[ids_live,0];dest=cur+MOVES[np.where(cmd<5,cmd,0)]
                bad=np.any((dest<0)|(dest>23),axis=1);dest[bad]=cur[bad];bad=terrain[dest[:,0],dest[:,1]]==2;dest[bad]=cur[bad]
                check(not np.any(np.all(dest[ids_live!=uid]==nxt,axis=1)) and not confirmed[tuple(dest[np.flatnonzero(ids_live==uid).item()])],'Reserved ship destination')
                holds=int((scoring&~region)[tuple(p)] and before[0]==0)
                if before[0]==0 and scoring[tuple(p)]:
                    check(np.any(np.all(dest[ids_live!=uid]==p,axis=1)),'Removed a sole actual scoring holder')
                check(student._prev_actions[uid]==canonical and uid not in student._sap_hits and (student.param_est._prev is None or np.array_equal(student.param_est._prev['act'],played)),'Incorrect post-command memory')
                self.events.append([t,int(uid),int(before[0]),move,int(p[0]*24+p[1]),int(nxt[0]*24+nxt[1]),holds])
            check(self.actor.changes==len(self.events),'Wrong intervention count')
            self.proposal=None
        v=self.env.step(actions);new=v[0][self.side]
        if ms==100:
            pts=match_points_after_step(o,new,v[4]);wins=np.asarray(new['team_wins'])-np.asarray(o['team_wins'])
            check(sorted(wins.tolist())==[0,1] and int(new['match_steps'])==0,'Boundary missing')
            self.matches.append(dict(points=pts[[team,1-team]].tolist(),win=int(wins[team])))
            if mi==0:self.first_match_hash=self.digest.hexdigest()
        self.o=new;self.t+=1;return v
