"""Screen every map, then replay both real continuations of its first eligible decision for twelve steps."""
import argparse
from collections import Counter
import fcntl
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys

import numpy as np

from anfahrt import Agent,HERE,ROOT,PROOF,ZIP,bits,encoded,is_set,worlds,STEPS,stationary
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE.parent/'vergleich'))
import spielen as common
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import point_tile_map,match_points_after_step

STORE=Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/beweisfahrt')
AUTH='9db1687b2435743ea4cb0d081781ccdac7c16f26980e0fca265f6718b915dd06'
check=common.require

def make_cards():
    import jax
    from panel import sensor
    out={}
    for part,start,n in [('train',162500000,240),('mechanik',162515000,80),('leistung',162530000,48)]:
        pool=np.arange(start,start+n*10,dtype=np.int32)
        found=pool[np.asarray(jax.jit(jax.vmap(sensor))(pool))==1][:n].tolist()
        check(len(found)==n,'Too few fixed sight-1 maps');out[part]=found
    common.write_once(HERE/'karten.json',out)

def binding():
    files=[HERE/f for f in ('PLAN.md','karten.json','anfahrt.py','gegenfahrten.py')]+[PROOF/'beweise.py',ZIP]
    src={str(p.relative_to(ROOT)):common.sha(p) for p in files};check(common.sha(PROOF/'beweise.py')==AUTH and common.sha(ZIP)==common.RELEASE,'Wrong proof or original V16')
    return {'files':src,'runner':common.stamp(common.common_source())}

def arrays_digest(d,view,original,opponent):
    for a in (original,opponent,view['units']['position'],view['units']['energy'],view['units_mask'],view['team_points'],view['sensor_mask'],view['relic_nodes_mask']):d.update(np.asarray(a).tobytes())

def start(env,seed,team,opponent,arm):
    import torch
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);side=f'player_{team}';other=f'player_{1-team}'
    actor=Agent(r3_package_agent(side,ZIP),arm);rival=r3_package_agent(other,ZIP) if opponent=='v16' else make_opponent('solution92',other)
    for a,s in ((actor,side),(rival,other)):
        if hasattr(a,'new_game'):a.new_game(s)
    random.seed(seed);np.random.seed(seed);obs,info=env.reset(seed=seed);cfg=info['params'];check(int(cfg['unit_sensor_range'])==1,'Unexpected sight')
    for a in (actor,rival):a.set_env_cfg(cfg)
    return side,other,actor,rival,obs

def play(env,seed,team,opponent,arm):
    side,other,actor,rival,obs=start(env,seed,team,opponent,arm);prefix=sha256();prefix0=None;after=[];anchor_score=None;checked=0;seen_positives=set();first_extra=None;first_dead=None
    for t in range(303):
        o=obs[side];a=actor.act(step=t,obs=o);b=rival.act(t,obs[other]);raw=actor.raw;selection=actor.selected
        truth=np.asarray(point_tile_map(env.state),bool);present=encoded(truth)
        check(not worlds(actor.ev.positive)&~present and not worlds(actor.ev.negative)&present,'Incorrect public evidence')
        checked+=1
        if actor.pol is not None and (selection is None or t==selection['t']):
            extra=worlds(actor.ev.positive)&~bits(actor.pol['point'])
            if extra and first_extra is None:first_extra=t
            if extra&bits(actor.pol['dead']) and first_dead is None:first_dead=t
        edited=np.flatnonzero(np.any(raw!=a,axis=1));check(len(edited)<=1,'More than one changed UID')
        if len(edited):
            uid=edited.item();r=selection;target=r['target'];move=int(a[uid,0]);check(uid==r['uid'] and t-r['t']<4 and 1<=move<=4 and not a[uid,1:].any() and int(raw[uid,0])!=move and raw[uid,0]<=4,'Invalid changed movement')
            check(is_set(worlds(actor.ev.positive),target) and truth.ravel()[target] and not is_set(bits(actor.pol['point']),target),'Target no longer newly proven')
            check(target not in actor.pub['occupied'] and target not in actor.pol['enemy'] and target not in {v for u,v in actor.pol['dest'].items() if u!=uid},'Target occupied or assigned')
            p=actor.base._imitation;canonical=(0,2,1,4,3)[move] if team else move
            check(p._prev_actions[uid]==canonical and uid not in p._sap_hits and (p.param_est._prev is None or np.array_equal(p.param_est._prev['act'],a)),'Action memory diverged')
            guard={k:g for k,g in stationary(actor.pol).items() if len(g)>0}
            pos=np.asarray(o['units']['position'])[team,uid];startcell=int(24*pos[0]+pos[1]);orig=int(raw[uid,0])
            if orig==0 and truth.ravel()[startcell]:check(any(i!=uid for i in guard.get(startcell,[])),'Removed sole actual scoring holder')
            check(np.array_equal(a[np.arange(16)!=uid],raw[np.arange(16)!=uid]),'Changed another agent')
        if prefix0 is None:
            arrays_digest(prefix,o,raw,b)
            if selection is not None:
                prefix0=prefix.hexdigest();anchor_score=np.asarray(o['team_points'],int)[[team,1-team]].copy()
        obs,_,done,trunc,info=env.step({side:a,other:b});new=obs[side]
        if selection is not None:
            target=selection['target'];uid=selection['uid'];p=np.asarray(env.state.units.position)[team];live=np.asarray(env.state.units_mask)[team]&(np.asarray(env.state.units.energy)[team,:,0]>=0)
            xy=divmod(target,24);entered=(p[:,0]==xy[0])&(p[:,1]==xy[1])&live;true=np.asarray(point_tile_map(env.state),bool)
            check(true[xy], 'Proven target disappeared')
            clock=np.asarray(match_points_after_step(o,new,info),int)[[team,1-team]];g=clock-anchor_score
            if entered.any():check(clock[0]>int(np.asarray(o['team_points'])[team]),'Occupied target failed to credit')
            after.append(dict(at=t+1,arrival=bool(entered[uid]),credit=bool(entered.any()),score=g.tolist()))
            if len(after)==12:break
        if t<302:check(not bool(done[side] or trunc[side]),'Incomplete game')
    require_no_agent_errors(actor.base,rival)
    if selection is not None:check(len(after)==12 and len(actor.events)<=4 and len({e[1] for e in actor.events})<=1,'Invalid paired horizon')
    return dict(seed=seed,team=team,opponent=opponent,arm=arm,selection=selection,prefix=prefix0,after=after,events=actor.events,
                steps_checked=checked,first_extra=first_extra,first_dead=first_dead,agent_errors=[0,0],sensor=1)

def key(which,i):
    cards=json.loads((HERE/'karten.json').read_bytes())[which]
    return cards[i],i%2,('solution92','v16')[i//2%2]

def path(which,i):
    s,team,o=key(which,i);return STORE/which/f'{i:03d}_{s}_{team}_{o}.json'

def observe(env,which,i,stamp):
    k=key(which,i);r=play(env,*k,'base');c=None
    if r['selection'] is not None:
        c=play(env,*k,'force');check(r['selection']==c['selection'] and r['prefix']==c['prefix'],'Diverged before chosen branch')
        check(c['events'] and c['events'][0][0]==r['selection']['t'],'Proposed alternative never took a different action')
    return {'source':stamp,'id':i,'base':r,'force':c}

def run(which,start,stop,worker):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    identity=binding();sig=common.stamp(identity);common.write_once(STORE/'quellen.json',identity)
    if which=='mechanik':check((HERE/'modell.json').exists(),'Unfitted candidate')
    jobs=list(range(start,stop));offset=worker*max(1,len(jobs)//2)%len(jobs);env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for i in jobs[offset:]+jobs[:offset]:
            dest=path(which,i);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():continue
            with dest.with_suffix('.lock').open('ab') as f:
                try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:continue
                if dest.exists():continue
                common.write_once(dest,observe(env,which,i,sig));print(f'{which} {i} abgeschlossen',flush=True)
    finally:env.close()
    check(identity==binding(),'Changed provider');print('Spur beendet',flush=True)

def stats(rows):
    opportunities=[r for r in rows if r['force']];added=actual=earlier=0
    for e in opportunities:
        a,b=e['base']['after'],e['force']['after'];added+=sum(x['credit'] for x in b)>sum(x['credit'] for x in a)
        actual+=any(x['arrival'] for x in b);bt=min((i for i,x in enumerate(b) if x['arrival'] and x['credit']),default=13);at=min((i for i,x in enumerate(a) if x['credit']),default=13);earlier+=bt<at
    return {'maps':len(rows),'opportunities':len(opportunities),'actual_arrivals':actual,'more_target_credits':added,'first_earlier':earlier,'unrecognized_ever':sum(r['base']['first_extra'] is not None for r in rows),'dead_ever':sum(r['base']['first_dead'] is not None for r in rows)}

def audit(which,n):
    sig=common.stamp(binding());rows=[json.loads(path(which,i).read_bytes()) for i in range(n)]
    check(all(r['source']==sig and r['id']==i for i,r in enumerate(rows)),'Unexpected sources');result=stats(rows)
    report={'sources':sig,'stats':result,'per_side':[stats([r for r in rows if r['base']['team']==t]) for t in (0,1)],'per_opponent':{q:stats([r for r in rows if r['base']['opponent']==q]) for q in ('solution92','v16')}}
    common.write_once(HERE/f'{which}_{n}.json',report);print(json.dumps(report),flush=True)
    raw=b''.join((json.dumps(r,separators=(',',':'),sort_keys=True)+'\n').encode() for r in rows)
    arc=HERE/f'{which}_{n}.jsonl.gz';blob=gzip.compress(raw,mtime=0)
    if arc.exists():check(arc.read_bytes()==blob,'Archive changed')
    else:arc.write_bytes(blob)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('op',choices=('karten','sammeln','bilanz'));p.add_argument('--split',default='train',choices=('train','mechanik'));p.add_argument('--start',type=int,default=0);p.add_argument('--end',type=int,default=40);p.add_argument('--worker',type=int,default=0);args=p.parse_args()
    check(os.environ.get('PYTHONHASHSEED')=='0' and all(os.environ.get(k)=='1' for k in common.THREADS),'Unpinned process');limit_threads()
    if args.op=='karten':make_cards()
    elif args.op=='sammeln':run(args.split,args.start,args.end,args.worker)
    else:audit(args.split,args.end)
