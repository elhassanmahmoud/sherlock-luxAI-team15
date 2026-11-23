"""Sealed late-game assay. Uses normal play_game, late scout command monitor and independent 48-map score readout."""
import argparse
from datetime import datetime
from hashlib import sha256
import fcntl
import gzip
import json
import os
from pathlib import Path
import random
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4];SHARED=HERE.parents[1]/'vergleich'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(SHARED));sys.path.insert(0,str(HERE))
import spielen as common
from kandidat import create
from ort import OLD
from spielpruefer import Monitor,check
from scripts.common import make_opponent,play_game
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.experiment import limit_threads

STORE=Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/spaetort')
CARDS=json.loads((HERE/'karten.json').read_bytes());freeze_file=STORE/'eingefroren.json'

def identity():
    refs=[HERE/n for n in ('LERNPLAN.md','PRUEFPLAN.md','karten.json','daten.py','ort.py','lernen.py','mechanik.py','mechanik.json','nachpruefen.py','VERFAHREN.md','modell.json','lernpruefung.json','lernquellen.json.gz','kandidat.py','spielpruefer.py','vergleich.py')]+[OLD,HERE.parent/'signalgrenze.py']
    return {'original':common.common_source(),'study':{str(p.relative_to(ROOT)):common.sha(p) for p in refs}}

def jobs(tech):
    if tech:return [(seed,team,'candidate',('solution92','v16')[i%2]) for i,seed in enumerate(CARDS['tech']) for team in (0,1)]
    return [(seed,team,arm,op) for seed in CARDS['performance'] for team in (0,1) for arm,op in [('reference','solution92'),('candidate','solution92'),('candidate','v16')]]

def keyfile(key,tech):
    return STORE/('techniksitze' if tech else 'leistungssitze')/('_'.join(map(str,key))+'.json')

def game(env,key,signature):
    import torch
    seed,team,arm,op=key;side,other=f'player_{team}',f'player_{1-team}'
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    agent=create(side) if arm=='candidate' else r3_package_agent(side,common.PACKAGE)
    rival=r3_package_agent(other,common.PACKAGE) if op=='v16' else make_opponent('solution92',other)
    m=Monitor(env,team,agent if arm=='candidate' else None)
    res=play_game(m,agent,rival,seed,side,False);require_no_agent_errors(agent.base if arm=='candidate' else agent,rival)
    wins=sum(q['win'] for q in m.matches);points=[sum(q['points'][s] for q in m.matches) for s in (0,1)]
    check(m.t==res['steps']==303 and res['point_counting_version']==2 and len(m.matches)==3 and m.audit==[303,303],'Incomplete game')
    check([wins,int(wins>=2),*points]==[res['our_wins'],res['game_win'],res['our_points'],res['opp_points']],'Game score mismatch')
    return dict(key=list(key),source=signature,steps=m.t,counts=m.audit,caught_errors=[0,0],point_counting_version=2,
        sensor=m.cfg['unit_sensor_range'],matches=m.matches,win=int(wins>=2),points=points,anchor=m.anchor,firsts=m.firsts,
        selection=agent.selected if arm=='candidate' else None,events=m.events,m1=m.first_match_hash,digest=m.digest.hexdigest(),
        prefix=m.prefix,outside=m.outside,own_digest=m.own_digest.hexdigest())

def replay(signature):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    env=LuxAIS3GymEnv(numpy_output=True);out=[]
    try:
        for side,seed in enumerate(CARDS['train'][:2]):
            receipt=json.loads((STORE/'train'/f'{seed}-{side}.json').read_bytes());key=(seed,side,'reference','solution92')
            row=game(env,key,signature)
            with np.load(STORE/'train'/receipt['public']) as trace:
                digest=sha256(trace['commands'].astype('<i4').tobytes()).hexdigest()
            comparison=[list(reversed(p)) if side else p for p in receipt['matches']]
            check(row['own_digest']==digest and [a['points'] for a in row['matches']]==comparison and row['win']==receipt['win'],'Original replay diverged from collector')
            out.append(dict(seed=seed,team=side,own_digest=digest,turns=303,matches=comparison))
    finally:env.close()
    common.write_once(HERE/'technik_referenz.json',{'source':signature,'replay':out})

def readrows(tech,signature):
    required=jobs(tech);files=[keyfile(k,tech) for k in required]
    check(set(files)==set(files[0].parent.glob('*.json')),'Missing or unexpected games')
    rows=[]
    for k,f in zip(required,files,strict=True):
        row=json.loads(f.read_bytes());check(row['key']==list(k) and row['source']==signature,'Game identity changed')
        check(row['steps']==303 and row['counts']==[303,303] and row['point_counting_version']==2 and row['caught_errors']==[0,0] and row['sensor']==1,'Unverified game')
        check(len(row['events'])<=10 and len({r[1] for r in row['events']})<=1,'More than one scout or too long')
        rows.append(row)
    return rows

def run(tech,worker,signature):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    if not tech:
        proof=json.loads((HERE/'technik.json').read_bytes())
        check(proof['source']==signature and proof['passed'],'Technique not certified')
    env=LuxAIS3GymEnv(numpy_output=True);keys=jobs(tech);offset=worker*(11 if tech else 67)%len(keys);done=0
    try:
        for key in keys[offset:]+keys[:offset]:
            if datetime.now(common.CUTOFF.tzinfo)>=common.CUTOFF:break
            to=keyfile(key,tech);to.parent.mkdir(parents=True,exist_ok=True)
            if to.exists():continue
            with to.with_suffix('.lock').open('ab') as lock:
                try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:continue
                if to.exists():continue
                common.write_once(to,game(env,key,signature));done+=1
                if done%10==0:print(f'{done} vollständige Spiele in dieser Spur',flush=True)
    finally:env.close()
    check(common.stamp(identity())==signature,'Source changed in process');print(f'{done} Spiele abgeschlossen',flush=True)

def technical(signature):
    replayed=json.loads((HERE/'technik_referenz.json').read_bytes());check(replayed['source']==signature and len(replayed['replay'])==2,'Missing source-bound reproduction')
    rows=readrows(True,signature);events=[r for r in rows if r['events']];seeds=sorted({r['key'][0] for r in events})
    report={'source':signature,'tested':len(rows),'signal_seats':sum(r['anchor'] is not None for r in rows),'overrides':sum(len(r['events']) for r in rows),'active_seats':len(events),'maps':seeds,'sides':sorted({r['key'][1] for r in events}),
        'passed':bool(events),'cases':[{k:r[k] for k in ('key','anchor','selection','events','firsts')} for r in events]}
    check(report['passed'],'No actual technical intervention');common.write_once(HERE/'technik.json',report);print(json.dumps({k:v for k,v in report.items() if k!='cases'}))

def interval(values,draws):
    v=np.asarray(values,float);bs=v[draws].mean(1)
    return {'mean':float(v.mean()),'ci95':np.quantile(bs,[.025,.975]).tolist()}

def assess(signature):
    rows=readrows(False,signature);cards=CARDS['performance']; by={tuple(r['key']):r for r in rows}
    draw=np.random.default_rng(842317).integers(0,len(cards),size=(20000,len(cards)))
    pairs=[];prefix_checks=0
    for seed in cards:
        for team in (0,1):
            ref=by[seed,team,'reference','solution92'];cand=by[seed,team,'candidate','solution92'];direct=by[seed,team,'candidate','v16']
            check(ref['m1']==cand['m1'] and ref['matches'][0]==cand['matches'][0],'Match one diverged')
            stop=cand['events'][0][0] if cand['events'] else 303
            check(ref['prefix'][:stop+1]==cand['prefix'][:stop+1],'Trajectory differs before its first intervention')
            if stop==303:check(cand['digest']==ref['digest'] and cand['win']==ref['win'] and cand['matches']==ref['matches'],'Inactive candidate differs')
            prefix_checks+=1
            a=ref['anchor'];c=cand['anchor'];check(a==c,'First trigger diverged before any allowed intervention')
            def timing(r):
                if a is None:return 101
                cutoff=(a['t']//101+1)*101
                ticks=[r['firsts'].get(str(i),999) for i in a['ids']]
                return min((t%101 for t in ticks if a['t']<=t<cutoff),default=101)
            timing_ref,timing_cand=timing(ref),timing(cand)
            late=lambda r:sum(m['points'][0]-m['points'][1] for m in r['matches'][1:])
            pairs.append(dict(seed=seed,team=team,anchor=a,reference_win=ref['win'],candidate_win=cand['win'],direct_win=direct['win'],
                changed=bool(cand['events']),changed_direct=bool(direct['events']),time_ref=timing_ref,time_candidate=timing_cand,
                gain=timing_ref-timing_cand,margin_diff=late(cand)-late(ref),late_match_win_diff=sum(m['win'] for m in cand['matches'][1:])-sum(m['win'] for m in ref['matches'][1:]),
                selection=cand['selection'],override_count=len(cand['events'])))
    def describe(items):
        names=('reference_win','candidate_win','direct_win','gain','margin_diff','late_match_win_diff','changed','changed_direct')
        return {'n':len(items),**{k:sum(p[k] for p in items) for k in names},'alert':sum(p['anchor'] is not None for p in items),
            'earlier':sum(p['gain']>0 for p in items),'later':sum(p['gain']<0 for p in items),'added_wins':sum(p['candidate_win']>p['reference_win'] for p in items),'lost_wins':sum(p['candidate_win']<p['reference_win'] for p in items)}
    stats={q:describe([p for p in pairs if condition(p)]) for q,condition in [('all',lambda p:True),('seat0',lambda p:p['team']==0),('seat1',lambda p:p['team']==1),('changed',lambda p:p['changed']),('strict',lambda p:p['anchor'] is not None),('own_only',lambda p:p['anchor'] and p['anchor']['gain'][0]>p['anchor']['cap'][0] and p['anchor']['gain'][1]<=p['anchor']['cap'][1]),('foe',lambda p:p['anchor'] and p['anchor']['gain'][1]>p['anchor']['cap'][1])]}
    intervals={name:interval([np.mean([func(p) for p in pairs if p['seed']==s]) for s in cards],draw) for name,func in [('sight_gain',lambda p:p['gain']),('game_difference',lambda p:p['candidate_win']-p['reference_win']),('direct',lambda p:p['direct_win']),('late_point_margin_difference',lambda p:p['margin_diff'])]}
    totals=stats['all']; changed_maps=len({p['seed'] for p in pairs if p['changed']})
    gates={'wins_vs_solution':totals['candidate_win']>=totals['reference_win'],'direct':totals['direct_win']>=48,'sighting':totals['gain']/96>=.5,'more_earlier':totals['earlier']>totals['later'],'four_maps':changed_maps>=4}
    raw=b''.join((json.dumps(r,sort_keys=True,separators=(',',':'))+'\n').encode() for r in rows);archive=HERE/'partien.jsonl.gz';archive.write_bytes(gzip.compress(raw,mtime=0))
    check([json.loads(x) for x in gzip.decompress(archive.read_bytes()).splitlines()]==rows,'Archive did not roundtrip')
    result={'source':signature,'archive_sha':common.sha(archive),'maps':len(cards),'games':len(rows),'verified_prefixes':prefix_checks,'changed_maps':changed_maps,'stats':stats,'intervals':intervals,'gates':gates,'passed':all(gates.values()),'pairs':pairs}
    common.write_once(HERE/'ergebnis.json',result);print(json.dumps({k:result[k] for k in ('gates','passed','intervals','stats')},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('op',choices=('freeze','replay','tech','technikbericht','play','auswerten'));p.add_argument('--worker',type=int,default=0);args=p.parse_args()
    check(os.getenv('PYTHONHASHSEED')=='0' and all(os.getenv(k)=='1' for k in common.THREADS),'Wrong thread settings');limit_threads()
    frozen=identity();signature=common.stamp(frozen)
    if args.op=='freeze':common.write_once(freeze_file,frozen);print(signature)
    else:
        check(json.loads(freeze_file.read_bytes())==frozen,'Candidate or dependencies changed')
        if args.op=='replay':replay(signature)
        elif args.op=='tech':run(True,args.worker,signature)
        elif args.op=='technikbericht':technical(signature)
        elif args.op=='play':run(False,args.worker,signature)
        else:assess(signature)
