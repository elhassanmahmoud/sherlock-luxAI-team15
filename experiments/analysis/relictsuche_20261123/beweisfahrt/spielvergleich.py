"""Conditional complete games for the frozen learned trip; refuses to run when the held-out mechanism failed."""
import argparse
import fcntl
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys

import numpy as np

from anfahrt import HERE,ROOT,ZIP,Agent,allow,bits,cells,encoded,is_set,worlds,stationary,MIRROR,threat_col,STEPS
from gegenfahrten import STORE,binding,common,check
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import match_points_after_step,point_tile_map

def identity():
    mechanics=json.loads((HERE/'mechanik.json').read_bytes());check(mechanics['passed'] and mechanics['model_sha']==common.sha(HERE/'modell.json'),'Independent mechanism did not clear its gates')
    return {'collection':binding(),'evaluation':{p.name:common.sha(p) for p in [HERE/n for n in ('LERNREGEL.md','entscheidung.py','modell.json','mechanik.json','spielvergleich.py','gegenpruefer.py')]}}

class Audit:
    def __init__(self,env,team,actor):
        self.env=env;self.team=team;self.side=f'player_{team}';self.actor=actor;self.proposal=None;self.digest=sha256();self.turn=0;self.prefix=[];self.matches=[];self.events=[];self.after=[];self.anchor_score=None
        raw=actor.base.act
        def capture(*args,**kwargs):
            check(self.proposal is None,'Called original twice');v=raw(*args,**kwargs);self.proposal=np.asarray(v).copy();return v
        actor.base.act=capture
    def reset(self,**kwargs):
        v=self.env.reset(**kwargs);self.o=v[0][self.side];check(int(v[1]['params']['unit_sensor_range'])==1,'Wrong sensor');return v
    def step(self,actions):
        t=self.turn;ms=t%101;o=self.o;team=self.team;a=self.actor;s=a.selected;raw=self.proposal
        check(raw is not None and int(o['steps'])==t and int(o['match_steps'])==ms,'Skipped or discontinuous original')
        out=np.asarray(actions[self.side]);changed=np.flatnonzero(np.any(out!=raw,axis=1));self.prefix.append(self.digest.hexdigest()[:24])
        for j in (0,1):
            ar=np.asarray(actions[f'player_{j}']);check(ar.shape==(16,3) and np.issubdtype(ar.dtype,np.integer) and np.all((ar[:,0]>=0)&(ar[:,0]<=5)),'Malformed command');self.digest.update(ar.astype('<i4',copy=False).tobytes())
        truth=np.asarray(point_tile_map(self.env.state),bool);check(not worlds(a.ev.positive)&~encoded(truth) and not worlds(a.ev.negative)&encoded(truth),'Invalid public certificate')
        if s and t==s['t']:
            self.anchor_score=np.asarray(o['team_points'],int)[[team,1-team]];check(t%101<=88 and 2<=len(s['route'])<=4 and s['route'][-1]==s['target'],'Bad future credit horizon')
        if len(changed):
            check(len(changed)==1 and a.arm=='chosen' and s is not None,'Unexpected intervention');uid=changed.item();b=a.base._imitation;xy=tuple(map(int,o['units']['position'][team,uid]));origin=24*xy[0]+xy[1];new=int(out[uid,0]);old=int(raw[uid,0]);target=s['target'];dst=int(STEPS[origin,new]);j=t-s['t']
            check(uid==s['uid'] and 0<=j<len(s['route']) and s['route'][j]==dst and 0<=old<=4 and 1<=new<=4 and new!=old and not out[uid,1:].any(),'Bound scout or movement mismatch')
            check(t//101==s['t']//101 and np.asarray(o['units_mask'])[team,uid] and o['units']['energy'][team,uid].item()>=max(30,4*int(a.base.env_cfg['unit_move_cost'])),'Energy or time violation')
            p=a.pol;active_true=set(cells(o,team))|set(cells(o,1-team));check(bool(np.asarray(o['sensor_mask']).ravel()[target]) and target not in active_true and target not in {v for u,v in p['dest'].items() if u!=uid},'Goal occupied, unseen or reserved')
            check(truth.ravel()[target] and not is_set(bits(p['point']),target) and is_set(worlds(a.ev.positive),target),'Goal not a genuinely new proven scoring tile')
            ctx,ids,feature,masks,*_=b.last_fz;row=np.flatnonzero(np.asarray(ids)==uid).item();canonical=MIRROR[new] if team else new
            check(masks[row,canonical] and not feature[row,threat_col()]>0,'Masked movement or immediate threat')
            known=worlds(a.ev.positive)|bits(p['point']);goal=ctx['assigned'].get(uid)
            if goal is not None:
                x,y=map(int,goal);field=24*(23-y)+23-x if team else 24*x+y;check(not is_set(known,field),'Overwrote known alternative assignment')
            if is_set(known,origin) or (old==0 and truth.ravel()[origin]):check(any(u!=uid for u in stationary(p).get(origin,[])),'Abandoned holder')
            check(b._prev_actions[uid]==canonical and uid not in b._sap_hits and (b.param_est._prev is None or np.array_equal(b.param_est._prev['act'],out)),'Memory records wrong move')
            chk=a.events[-1];check(chk==[t,uid,old,new,dst],'Event disagrees');self.events.append(chk)
        check(a.changes==len(self.events) and len(self.events)<=4,'Incorrect change count');self.proposal=None
        v=self.env.step(actions);newobs=v[0][self.side]
        if s is not None and 0<=t-s['t']<12:
            state=self.env.state;target=s['target'];x,y=divmod(target,24);live=np.asarray(state.units_mask)[team]&(np.asarray(state.units.energy)[team,:,0]>=0);pos=np.asarray(state.units.position)[team];on=live&(pos[:,0]==x)&(pos[:,1]==y)
            check(np.asarray(point_tile_map(state))[x,y],'Proven point disappeared')
            pts=match_points_after_step(o,newobs,v[4])[[team,1-team]];check(not on.any() or pts[0]>int(o['team_points'][team]),'Occupied point failed to credit')
            self.after.append(dict(at=t+1,arrival=bool(on[s['uid']]),credit=bool(on.any()),score=(pts-self.anchor_score).tolist()))
        if ms==100:
            pts=match_points_after_step(o,newobs,v[4]);win=np.asarray(newobs['team_wins'])-np.asarray(o['team_wins']);check(sorted(win.tolist())==[0,1],'Invalid match result')
            self.matches.append({'points':pts[[team,1-team]].tolist(),'win':int(win[team])})
        self.turn+=1;self.o=newobs;return v

def game(env,key,sig):
    import torch
    seed,team,arm,op=key;side,other=f'player_{team}',f'player_{1-team}';random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    model=json.loads((HERE/'modell.json').read_bytes());a=Agent(r3_package_agent(side,ZIP),'chosen' if arm=='candidate' else 'base',model)
    b=r3_package_agent(other,ZIP) if op=='v16' else make_opponent('solution92',other);m=Audit(env,team,a)
    result=play_game(m,a,b,seed,side,False);require_no_agent_errors(a.base,b)
    check(result['steps']==m.turn==303 and len(m.matches)==3 and result['point_counting_version']==2 and sum(s['win'] for s in m.matches)==result['our_wins'],'Incomplete normal runner')
    check([sum(s['points'][j] for s in m.matches) for j in (0,1)]==[result['our_points'],result['opp_points']],'Totals diverge')
    check(len(m.after)==(12 if a.selected else 0),'Incorrect target-credit horizon')
    return {'key':list(key),'source':sig,'steps':303,'errors':[0,0],'matches':m.matches,'win':result['game_win'],'prefix':m.prefix,'hash':m.digest.hexdigest(),
         'selection':a.selected,'events':m.events,'after':m.after,'chosen':bool(a.selected and arm=='candidate' and allow(model,a.selected['x']))}

def jobs():
    return [(s,t,arm,op) for s in json.loads((HERE/'karten.json').read_bytes())['leistung'] for t in (0,1) for arm,op in [('reference','solution92'),('candidate','solution92'),('candidate','v16')]]

def dest(k):return STORE/'leistung'/('_'.join(map(str,k))+'.json')

def run(worker,sig):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    keys=jobs();off=worker*137%len(keys);env=LuxAIS3GymEnv(numpy_output=True);count=0
    try:
        for k in keys[off:]+keys[:off]:
            p=dest(k);p.parent.mkdir(parents=True,exist_ok=True)
            if p.exists():continue
            with p.with_suffix('.lock').open('ab') as f:
                try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:continue
                if p.exists():continue
                common.write_once(p,game(env,k,sig));count+=1
                if count%10==0:print(count,'fertig',flush=True)
    finally:env.close()
    check(common.stamp(identity())==sig,'Changed frozen performance sources')

def assess(sig):
    keys=jobs();check(set(map(dest,keys))==set((STORE/'leistung').glob('*.json')),'Missing or extra games');groups={}
    for k in keys:
        r=json.loads(dest(k).read_bytes());check(r['source']==sig and r['key']==list(k) and r['errors']==[0,0] and r['steps']==303,'Bad sources or incomplete game');groups[k]=r
    cards=json.loads((HERE/'karten.json').read_bytes())['leistung'];pairs=[]
    for s in cards:
        for t in (0,1):
            ref=groups[s,t,'reference','solution92'];cand=groups[s,t,'candidate','solution92'];direct=groups[s,t,'candidate','v16']
            stop=cand['events'][0][0] if cand['events'] else 303;check(ref['prefix'][:stop+1]==cand['prefix'][:stop+1] and ref['selection']==cand['selection'],'Pre-intervention state diverges')
            if not cand['events']:check(ref['hash']==cand['hash'] and cand['matches']==ref['matches'] and cand['after']==ref['after'],'Inactive candidate diverged')
            a,b=ref['after'],cand['after'];old=min((i for i,x in enumerate(a) if x['credit']),default=13);new=min((i for i,x in enumerate(b) if x['arrival'] and x['credit']),default=13)
            pairs.append({'seed':s,'team':t,'ref':ref['win'],'candidate':cand['win'],'direct':direct['win'],'changed':bool(cand['events']),
                'arrived':any(x['arrival'] for x in b) and bool(cand['events']),'earlier':bool(cand['events']) and new<old,
                'extra':sum(x['credit'] for x in b)-sum(x['credit'] for x in a),'own':b[-1]['score'][0]-a[-1]['score'][0] if b else 0})
    totals={k:sum(r[k] for r in pairs) for k in ('ref','candidate','direct','changed','arrived','earlier','extra','own')};early_maps=len({p['seed'] for p in pairs if p['earlier']})
    gates={'whole':totals['candidate']>=totals['ref'],'direct':totals['direct']>=48,'earlier_maps':early_maps>=3,'extra_points':totals['extra']>0,'protected':True}
    bs=np.random.default_rng(745357).integers(0,48,size=(20000,48));bounds={}
    for name,func in [('whole_diff',lambda p:p['candidate']-p['ref']),('direct',lambda p:p['direct']),('target',lambda p:p['extra'])]:
        values=np.array([np.mean([func(r) for r in pairs if r['seed']==s]) for s in cards]);bounds[name]={'mean':float(values.mean()),'ci95':np.quantile(values[bs].mean(1),[.025,.975]).tolist()}
    raw=b''.join((json.dumps(groups[k],sort_keys=True,separators=(',',':'))+'\n').encode() for k in keys);file=HERE/'leistung_partien.jsonl.gz';file.write_bytes(gzip.compress(raw,mtime=0));check(gzip.decompress(file.read_bytes())==raw,'Raw archive changed')
    rep={'games':len(keys),'maps':len(cards),'source':sig,'totals':totals,'earlier_maps':early_maps,'gates':gates,'passed':all(gates.values()),'intervals':bounds,'pairs':pairs,'archive_sha':common.sha(file)}
    common.write_once(HERE/'leistung.json',rep);print(totals,gates)

if __name__=='__main__':
    c=argparse.ArgumentParser(description=__doc__);c.add_argument('op',choices=('einfrieren','spielen','auswerten'));c.add_argument('--worker',type=int,default=0);args=c.parse_args();limit_threads()
    check(os.getenv('PYTHONHASHSEED')=='0' and all(os.getenv(k)=='1' for k in common.THREADS),'Unexpected thread configuration');src=identity();sig=common.stamp(src);p=HERE/'quellen_leistung.json'
    if args.op=='einfrieren':common.write_once(p,src);print(sig)
    else:
        check(json.loads(p.read_bytes())==src,'Sources changed');run(args.worker,sig) if args.op=='spielen' else assess(sig)
