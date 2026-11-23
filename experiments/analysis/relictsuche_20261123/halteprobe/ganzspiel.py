"""Conditional fresh 48-map panel including field probe itself as an external and head-to-head control."""
import argparse
import fcntl
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import random

import numpy as np
from kandidat import HERE,Hold,original_probe
from pruefen import STORE,check,course,source
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import match_points_after_step,point_tile_map

def identity():
    m=json.loads((HERE/'mechanik.json').read_bytes());v=json.loads((HERE/'gegenpruefung_mechanik.json').read_bytes());check(m['passed'] and v['passed'],'Public post-probe mechanism did not pass')
    return {'mechanism':source(),'current':{p.name:course.sha(p) for p in (HERE/'mechanik.json',HERE/'gegenpruefung_mechanik.json',HERE/'gegenpruefung_natur.json',HERE/'karten_leistung.json',Path(__file__))}}

def cards():
    import jax
    from panel import sensor
    a=np.arange(163500000,163501200,dtype=np.int32);s=a[np.asarray(jax.jit(jax.vmap(sensor))(a))==1][:48].tolist();check(len(s)==48,'Insufficient fresh low-vision cards');return s

class Watch:
    def __init__(self,env,team,actor,arm):
        self.env=env;self.team=team;self.name=f'player_{team}';self.actor=actor;self.arm=arm;self.t=0;self.proposal=None;self.digest=sha256();self.prefix=[];self.events=[];self.matches=[];self.profile=[];self.target_window=[]
        src=actor if arm=='reference' else actor.base;old=src.act
        def capture(*args,**kwargs):
            check(self.proposal is None,'Called original twice');cmd=old(*args,**kwargs);self.proposal=np.asarray(cmd).copy();return cmd
        src.act=capture
    def reset(self,**kwargs):
        v=self.env.reset(**kwargs);self.obs=v[0][self.name];self.cfg=v[1]['params'];check(self.cfg['unit_sensor_range']==1,'Unexpected sensor');return v
    def step(self,actions):
        t=self.t;a=self.actor;team=self.team;o=self.obs;raw=self.proposal;check(raw is not None and int(o['steps'])==t and int(o['match_steps'])==t%101,'Original missed a turn')
        own=np.asarray(actions[self.name]);diff=np.flatnonzero(np.any(raw!=own,axis=1));e=None if self.arm=='reference' else (a.event if self.arm=='probe' else a.probe.event);self.prefix.append(self.digest.hexdigest()[:24])
        for s in (0,1):
            z=np.asarray(actions[f'player_{s}']);check(z.shape==(16,3) and np.issubdtype(z.dtype,np.integer) and np.all((z[:,0]>=0)&(z[:,0]<=5)),'Invalid command');self.digest.update(z.astype('<i4',copy=False).tobytes())
        if len(diff):
            uid=diff.item();old=int(raw[uid,0]);move=int(own[uid,0]);check(e is not None and uid==e['u'] and old<=4 and not own[uid,1:].any(),'Changed unrelated role or unit')
            if t==e['t']:
                check(len(self.events)==0 and move==e['d'] and old==e['old'] and 1<=move<=4,'Unexpected first probe')
            else:
                check(self.arm=='hold' and t==e['t']+1 and len(self.events)==1 and a.follow['eligible'] and a.follow['selected'] and move==0 and 1<=old<=4,'Unexpected second command')
                target=tuple(e['xy']);p=np.asarray(o['units']['position'])[team];ene=np.asarray(o['units']['energy'])[team].ravel();live=np.asarray(o['units_mask'][team],bool)&(ene>=0);enemy=np.asarray(o['units']['position'])[1-team,np.asarray(o['units_mask'][1-team],bool)]
                check(live[uid] and tuple(p[uid])==target and ene[uid]>=max(30,4*self.cfg['unit_move_cost']) and (p[live]==target).all(1).sum()==1,'Invalid sole arrival or energy')
                check(not len(enemy) or np.abs(enemy-p[uid]).max(1).min()>self.cfg['unit_sap_range'],'Immediate enemy danger')
                m=a.base._imitation;ids=np.asarray(m.last_fz[1]);row=np.flatnonzero(ids==uid).item();check(m.last_fz[3][row,0] and m._prev_actions[uid]==0 and uid not in m._sap_hits and (m.param_est._prev is None or np.array_equal(m.param_est._prev['act'],own)),'Hold mask or memory disagrees')
                xy=(23-target[1],23-target[0]) if team else target;check(not m.belief.point_tiles[xy],'Changed a confirmed holder')
            self.events.append([t,uid,old,move])
        check(self.arm=='reference' or self.actor.changes==len(self.events),'Policy count mismatch');self.proposal=None
        v=self.env.step(actions);new=v[0][self.name];pts=match_points_after_step(o,new,v[4]);g=(pts-np.asarray(o['team_points']))[[team,1-team]].tolist();self.profile.append(g)
        if e is not None and e['t']<=t<=e['t']+4:
            state=v[4]['final_state'];target=tuple(e['xy']);tm=point_tile_map(state);live=np.asarray(state.units_mask)[team]&(np.asarray(state.units.energy)[team,:,0]>=0);pos=np.asarray(state.units.position)[team];on=live&(pos==target).all(1)
            self.target_window.append({'t':t,'uid':bool(on[e['u']]),'team':bool(on.any()),'scoring':bool(tm[target]),'gain':g})
        if t%101==100:
            won=np.asarray(new['team_wins'])-np.asarray(o['team_wins']);check(sorted(won.tolist())==[0,1],'Invalid match');self.matches.append({'points':pts[[team,1-team]].tolist(),'win':int(won[team])})
        self.t+=1;self.obs=new;return v

def game(env,k,signature):
    import torch
    seed,team,arm,op=k;side,other=f'player_{team}',f'player_{1-team}';random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    actor=r3_package_agent(side,course.PACKAGE) if arm=='reference' else (original_probe(side) if arm=='probe' else Hold(side));rival=make_opponent('solution92',other) if op=='solution92' else (r3_package_agent(other,course.PACKAGE) if op=='v16' else original_probe(other));w=Watch(env,team,actor,arm)
    result=play_game(w,actor,rival,seed,side,False);require_no_agent_errors(actor if arm=='reference' else actor.base,rival.base if op=='probe' else rival)
    check(w.t==result['steps']==303 and result['point_counting_version']==2 and sum(x['win'] for x in w.matches)==result['our_wins'],'Incomplete full game')
    for i in range(3):check(np.asarray(w.profile[i*101:(i+1)*101]).sum(0).tolist()==w.matches[i]['points'],'Invalid score total')
    return {'key':list(k),'source':signature,'win':result['game_win'],'matches':w.matches,'profile':w.profile,'prefix':w.prefix,'hash':w.digest.hexdigest(),'events':w.events,'window':w.target_window,'follow':actor.follow if arm=='hold' else None,'steps':w.t,'errors':[0,0]}

def jobs(panel):return [(s,t,arm,op) for s in panel for t in (0,1) for arm,op in [('reference','solution92'),('probe','solution92'),('hold','solution92'),('hold','v16'),('hold','probe')]]
def dest(k):return STORE/'leistung'/('_'.join(map(str,k))+'.json')

def run(panel,worker,sig):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    keys=jobs(panel);off=worker*211%len(keys);env=LuxAIS3GymEnv(numpy_output=True);n=0
    try:
        for k in keys[off:]+keys[:off]:
            p=dest(k);p.parent.mkdir(parents=True,exist_ok=True)
            if p.exists():continue
            with p.with_suffix('.lock').open('ab') as f:
                try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:continue
                if p.exists():continue
                course.write_once(p,game(env,k,sig));n+=1
                if n%10==0:print(n,'weitere vollständige Spiele',flush=True)
    finally:env.close()
    check(course.stamp(identity())==sig,'Sources changed')

def assess(panel,sig):
    keys=jobs(panel);check(set(map(dest,keys))==set((STORE/'leistung').glob('*.json')),'Incomplete performance dataset');d={k:json.loads(dest(k).read_bytes()) for k in keys}
    for k,r in d.items():check(r['source']==sig and r['key']==list(k) and r['errors']==[0,0] and r['steps']==303,'Game fingerprint mismatch')
    pairs=[]
    for s in panel:
        for t in (0,1):
            r=d[s,t,'reference','solution92'];p=d[s,t,'probe','solution92'];c=d[s,t,'hold','solution92'];stop=c['events'][1][0] if len(c['events'])>1 else 303
            check(c['prefix'][:stop+1]==p['prefix'][:stop+1] and c['events'][:1]==p['events'][:1],'Earlier trajectory changed between hold and field probe')
            if stop==303:check(c['hash']==p['hash'] and c['matches']==p['matches'],'Inactive added hold diverged')
            if p['events']:
                start=p['events'][0][0];check(p['prefix'][:start+1]==r['prefix'][:start+1],'Base diverged before probe')
            else:check(p['hash']==r['hash'],'No-probe original diverged')
            pairs.append(dict(seed=s,team=t,base=r['win'],probe=p['win'],hold=c['win'],vs_v16=d[s,t,'hold','v16']['win'],vs_probe=d[s,t,'hold','probe']['win'],actual_hold=stop<303,
                own1=c['profile'][stop][0]-p['profile'][stop][0] if stop<303 else 0,own4=sum(x[0] for x in c['profile'][stop:stop+4])-sum(x[0] for x in p['profile'][stop:stop+4]) if stop<303 else 0))
    totals={k:sum(r[k] for r in pairs) for k in ('base','probe','hold','vs_v16','vs_probe','actual_hold','own1','own4')};gates={'solution_vs_base':totals['hold']>=totals['base'],'solution_vs_probe':totals['hold']>=totals['probe'],'direct_v16':totals['vs_v16']>=48,'direct_probe':totals['vs_probe']>=48,'immediate':totals['own1']>0,'protected':True}
    bs=np.random.default_rng(16350071).integers(0,len(panel),size=(20000,len(panel)));intervals={}
    for k,fn in [('solution_base',lambda r:r['hold']-r['base']),('solution_probe',lambda r:r['hold']-r['probe']),('direct_v16',lambda r:r['vs_v16']),('direct_probe',lambda r:r['vs_probe']),('immediate',lambda r:r['own1'])]:
        v=np.asarray([np.mean([fn(r) for r in pairs if r['seed']==s]) for s in panel]);intervals[k]={'mean':float(v.mean()),'ci95':np.quantile(v[bs].mean(1),[.025,.975]).tolist()}
    archive=HERE/'leistung_partien.jsonl.gz';raw=b''.join((json.dumps(d[k],sort_keys=True,separators=(',',':'))+'\n').encode() for k in keys);archive.write_bytes(gzip.compress(raw,mtime=0));check(gzip.decompress(archive.read_bytes())==raw,'Archive differs')
    rep={'maps':len(panel),'games':len(keys),'source':sig,'totals':totals,'gates':gates,'passed':all(gates.values()),'intervals':intervals,'pairs':pairs,'archive_sha':course.sha(archive)};course.write_once(HERE/'leistung.json',rep);print(totals,gates)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('op',choices=('einfrieren','spielen','auswerten'));p.add_argument('--worker',default=0,type=int);a=p.parse_args();limit_threads();check(os.getenv('PYTHONHASHSEED')=='0' and all(os.getenv(k)=='1' for k in course.THREADS),'Unexpected process settings')
    if a.op=='einfrieren':
        gate=json.loads((HERE/'gegenpruefung_mechanik.json').read_bytes());check(gate['passed'],'Independent mechanism did not pass');course.write_once(HERE/'karten_leistung.json',cards())
    src=identity();sig=course.stamp(src);f=HERE/'quellen_leistung.json'
    if a.op=='einfrieren':course.write_once(f,src);print(sig)
    else:
        check(json.loads(f.read_bytes())==src,'Sources changed');panel=json.loads((HERE/'karten_leistung.json').read_bytes());run(panel,a.worker,sig) if a.op=='spielen' else assess(panel,sig)
