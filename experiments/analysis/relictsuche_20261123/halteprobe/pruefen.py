"""Replay the exact historic Feldprobe, pair a single optional stay with it, independently verify raw score windows."""
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
from kandidat import HERE,ROOT,Hold,MIRROR
sys.path.insert(0,str(HERE.parent/'vergleich'))
import spielen as course
from scripts.experiment import limit_threads
from scripts.common import make_opponent
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import match_points_after_step,point_tile_map

EINGANG=HERE.parent/'feldprobe';BIND=HERE.parent/'feldbindung';DESK=Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123');STORE=DESK/'halteprobe';check=course.require

def origin():return [json.loads(line) for line in gzip.decompress((EINGANG/'ganze_partien.jsonl.gz').read_bytes()).splitlines()]

def jobs():return sorted((r['seed'],r['team'],r['opponent']) for r in origin() if r['arm']=='probe' and r['event'])

def source():
    files=[HERE/f for f in ('PLAN.md','kandidat.py','rueckmeldung.py','lernen.py','natur.json','modell.json','pruefen.py')]+[EINGANG/f for f in ('kandidat.py','modell.json','signalmodell.py','ganze_partien.jsonl.gz')]+[BIND/f for f in ('ergebnis.json','fenster.jsonl.gz')]
    return {'study':{str(p.relative_to(ROOT)):course.sha(p) for p in files},'course':course.stamp(course.common_source())}

def play(env,key,arm,finish):
    import torch
    seed,team,op=key;side,other=f'player_{team}',f'player_{1-team}';random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    a=Hold(side,arm);rival=r3_package_agent(other,course.PACKAGE) if op=='v16' else make_opponent('solution92',other)
    for actor,label in ((a,side),(rival,other)):
        if hasattr(actor,'new_game'):actor.new_game(label)
    random.seed(seed);np.random.seed(seed);obs,inf=env.reset(seed=seed);cfg=inf['params'];check(cfg['unit_sensor_range']==1,'Expected low vision')
    for actor in (a,rival):actor.set_env_cfg(cfg)
    digest=sha256();profile=[];window=[];entry=None;prehold=None;matches=[];commands=[]
    for t in range(303):
        o=obs[side];cmd=a.act(t,o);enemy=rival.act(t,obs[other]);event=a.probe.event;all_actions={side:cmd,other:enemy};raw=a.raw
        if event is not None and t==event['t']:entry=digest.hexdigest()
        if event is not None and t==event['t']+1:
            prehold=digest.hexdigest();diff=np.flatnonzero(np.any(raw!=cmd,axis=1))
            if len(diff):
                uid=int(diff.item());target=tuple(event['xy']);s=a.base._imitation;b=s.belief
                check(a.follow['selected'] and a.follow['eligible'] and uid==event['u'] and raw[uid,0] in (1,2,3,4) and not cmd[uid].any() and a.changes==2,'Invalid single stay')
                pos=np.asarray(o['units']['position'])[team];energy=np.asarray(o['units']['energy'])[team].ravel();mask=np.asarray(o['units_mask'][team],bool)&(energy>=0)
                check(mask[uid] and tuple(pos[uid])==target and energy[uid]>=max(30,4*cfg['unit_move_cost']) and np.count_nonzero((pos[mask]==target).all(1))==1,'Missing lone, live arrival')
                check(not b.point_tiles[(23-target[1],23-target[0]) if team else target], 'A confirmed holder was changed')
                enemypos=np.asarray(o['units']['position'])[1-team,np.asarray(o['units_mask'][1-team],bool)];check(not len(enemypos) or np.min(np.abs(enemypos-pos[uid]).max(1))>cfg['unit_sap_range'],'Visible immediate danger')
                reg=s.last_fz;row=np.flatnonzero(np.asarray(reg[1])==uid).item();check(reg[3][row,0] and s._prev_actions[uid]==0 and uid not in s._sap_hits and (s.param_est._prev is None or np.array_equal(s.param_est._prev['act'],cmd)),'Forbidden stay or wrong policy memory')
                commands.append([t,uid,int(raw[uid,0]),0])
        else:check(np.array_equal(cmd,raw),'Change outside single follow-up')
        for j in (0,1):digest.update(np.asarray(all_actions[f'player_{j}']).astype('<i4',copy=False).tobytes())
        obs,_,term,trunc,info=env.step(all_actions);new=obs[side];pts=match_points_after_step(o,new,info);g=(pts-np.asarray(o['team_points']))[[team,1-team]].tolist();profile.append(g)
        if event is not None and event['t']<=t<=event['t']+4:
            p=tuple(event['xy']);state=info['final_state'];true=bool(np.asarray(point_tile_map(state))[p]);live=np.asarray(state.units_mask)[team]&(np.asarray(state.units.energy)[team,:,0]>=0);xy=np.asarray(state.units.position)[team];arrived=(xy[:,0]==p[0])&(xy[:,1]==p[1])&live
            if true and arrived.any():check(g[0]>=1,'Target credit did not reach public team score')
            window.append({'t':t,'active':true,'uid_present':bool(arrived[event['u']]),'target_credit':int(true and arrived.any()),'score':g})
        if t%101==100:
            w=np.asarray(new['team_wins'])-np.asarray(o['team_wins']);check(sorted(w.tolist())==[0,1],'Incomplete boundary');matches.append({'points':pts[[team,1-team]].tolist(),'win':int(w[team])})
        if not finish and event is not None and t==event['t']+4:break
        if t!=302:check(not bool(term[side] or trunc[side]),'Incomplete regular run')
    require_no_agent_errors(a.base,rival);check(len(commands)<=1 and a.changes==(1 if a.probe.event else 0)+len(commands),'Wrong count')
    return {'key':list(key),'arm':arm,'event':a.probe.event,'follow':a.follow,'entry_prefix':entry,'hold_prefix':prehold,'hash':digest.hexdigest(),'matches':matches,'profile':profile,'window':window,'events':commands,'errors':[0,0],'steps':len(profile)}

def collect(env,key,stamp):
    seed,team,op=key;reference=next(r for r in origin() if (r['seed'],r['team'],r['opponent'])==key and r['arm']=='probe');proof=json.loads((DESK/'feldbindung/spiele'/f'{seed}_{team}_probe_{op}.json').read_bytes());a=play(env,key,'control',True)
    e=reference['event'];check(a['hash']==proof['hash']==reference['hash'] and a['matches']==reference['matches'] and a['profile']==reference['profile'] and a['entry_prefix']==e['prefix'],'Original Feldprobe not precisely reproduced')
    check(all(a['event'][k]==e[k] for k in ('t','u','d','xy','ref','old')) and a['steps']==303 and len(a['window'])==5,'Different initial probe')
    archived=proof['readings'][str(team)];check(all(x['target_credit']==y['own_point'] and x['uid_present']==(e['u'] in y['own_units']) for x,y in zip(a['window'],archived[:5],strict=True)),'Different archived target attribution')
    b=None
    if a['follow'] and a['follow']['selected']:
        b=play(env,key,'chosen',False);check(a['entry_prefix']==b['entry_prefix'] and a['hold_prefix']==b['hold_prefix'] and a['follow']==b['follow'] and a['window'][0]==b['window'][0] and len(b['events'])==1,'Mismatched causal starting point')
    for r in (a,b):
        if r:r.pop('profile')
    return {'source':stamp,'key':list(key),'original':a,'hold':b,'archive_sha':course.sha(DESK/'feldbindung/spiele'/f'{seed}_{team}_probe_{op}.json')}

def dest(k):return STORE/'mechanik'/('_'.join(map(str,k))+'.json')

def run(worker,stamp):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    keys=jobs();check(len(keys)==56,'Wrong selected population');off=worker*27%len(keys);env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for k in keys[off:]+keys[:off]:
            p=dest(k);p.parent.mkdir(parents=True,exist_ok=True)
            if p.exists():continue
            with p.with_suffix('.lock').open('ab') as l:
                try:fcntl.flock(l,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:continue
                if p.exists():continue
                course.write_once(p,collect(env,k,stamp));print('Fall abgeschlossen',flush=True)
    finally:env.close()
    check(course.stamp(source())==stamp,'Changed study sources')

def assess(stamp):
    keys=jobs();check(set(map(dest,keys))==set((STORE/'mechanik').glob('*.json')),'Incomplete cases');packets=[];cases=[]
    for k in keys:
        pkt=json.loads(dest(k).read_bytes());check(pkt['source']==stamp and pkt['key']==list(k),'Inventory mismatch');packets.append(pkt);a=pkt['original'];b=pkt['hold'];f=a['follow'];initial=a['window'][0]
        c=dict(seed=k[0],team=k[1],opp=k[2],event=a['event']['t'],initial=bool(initial['active'] and initial['uid_present']),eligible=bool(f and f['eligible']),selected=b is not None)
        if b:
            first=np.subtract(b['window'][1]['score'],a['window'][1]['score']);four=np.subtract([x['score'] for x in b['window'][1:]],[x['score'] for x in a['window'][1:]]).sum(0)
            c.update(own1=int(first[0]),foe1=int(first[1]),own4=int(four[0]),foe4=int(four[1]),target1=b['window'][1]['target_credit']-a['window'][1]['target_credit'],target4=sum(x['target_credit'] for x in b['window'][1:])-sum(x['target_credit'] for x in a['window'][1:]))
        cases.append(c)
    def totals(v):
        s=[x for x in v if x['selected']];return {'probe_seats':len(v),'eligible':sum(x['eligible'] for x in v),'selected':len(s),'maps':len({x['seed'] for x in s}),'initial_positive':sum(x['initial'] for x in s),
            'positive1':sum(x['own1']>0 for x in s),'negative1':sum(x['own1']<0 for x in s),**{k:sum(x[k] for x in s) for k in ('own1','foe1','own4','foe4','target1','target4')}}
    s=totals(cases);group={o:totals([r for r in cases if r['opp']==o]) for o in ('solution92','v16')};natural=json.loads((HERE/'natur.json').read_bytes())
    gates={'eligible_and_maps':s['selected']>=8 and s['maps']>=5,'each_opponent_plus':all(p['positive1']>=1 for p in group.values()),'four_plus':s['positive1']>=4,'at_most_one_minus':s['negative1']<=1,'positive_sum':s['own1']>0,'nonnegative_four':s['own4']>=0,'protected':True,'natural_pass':natural['passed']}
    cards=sorted({k[0] for k in keys});bs=np.random.default_rng(16350011).integers(0,len(cards),size=(20000,len(cards)));intervals={}
    for name in ('own1','own4','target1'):
        v=np.asarray([sum(c.get(name,0) for c in cases if c['seed']==z) for z in cards]);intervals[name]={'per_affected_map':float(v.mean()),'ci95':np.quantile(v[bs].mean(1),[.025,.975]).tolist()}
    file=HERE/'mechanik_partien.jsonl.gz';raw=b''.join((json.dumps(r,separators=(',',':'),sort_keys=True)+'\n').encode() for r in packets);file.write_bytes(gzip.compress(raw,mtime=0));check(gzip.decompress(file.read_bytes())==raw,'Damaged archive')
    report={'source':stamp,'all':s,'per_opponent':group,'per_side':[totals([r for r in cases if r['team']==side]) for side in (0,1)],'gates':gates,'passed':all(gates.values()),'intervals':intervals,'cases':cases,'archive_sha':course.sha(file)};course.write_once(HERE/'mechanik.json',report);print(s,group,gates)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('op',choices=('spielen','auswerten'));cli.add_argument('--worker',type=int,default=0);args=cli.parse_args();limit_threads();check(os.getenv('PYTHONHASHSEED')=='0' and all(os.getenv(k)=='1' for k in course.THREADS),'Non-deterministic process');src=source();course.write_once(HERE/'quellen_mechanik.json',src);sig=course.stamp(src);run(args.worker,sig) if args.op=='spielen' else assess(sig)
