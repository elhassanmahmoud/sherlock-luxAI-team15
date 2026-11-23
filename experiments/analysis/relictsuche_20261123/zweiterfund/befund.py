"""Evaluate old original V16 games, with public route construction separated from referee scoring."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from wege import DIST, MID, ORB, OTHER, ROOT, STUDY, ZONE, alternatives, free_units, previous_centres, public_orders
from experiments.analysis.relictsuche_20261123.nullwissen.gedaechtnis import PACKAGE, load
from scripts.experiment import limit_threads
from scripts.r3_package import r3_package_agent

HERE=Path(__file__).resolve().parent
WORK=Path.home()/'Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123'
DATA=WORK/'spaetort/train'; DEAD=WORK/'nullwissen/train'
ZERO=np.zeros((24,24),np.float32)


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def orbits(mask):
    return sorted(int(i) for i in np.unique(ORB[np.flatnonzero(mask)]))


def observation(pub,t):
    o={k:pub[k][t] for k in ('units_mask','sensor_mask','team_points','relic_nodes_mask','relic_nodes')}
    o.update(steps=t,match_steps=t%101,units={k:pub[k][t] for k in ('position','energy')},
             map_features=dict(energy=ZERO,tile_type=np.where(o['sensor_mask'],pub['terrain'][t],-1)))
    return o


def run_match(pub,j,history,meta,m,orders):
    team=meta['team']; cost=meta['cfg']['unit_move_cost']; start=101*m
    active=np.flatnonzero(j['active'][start:start+101,m]); orig=np.flatnonzero(pub['relic_nodes_mask'][start:start+101,[m,m+3]].any(axis=1))
    sight=start+(int(orig[0]) if len(orig) else 101)
    out=dict(match=m,spawn=None,first=sight,relation=None,public_orders=orders,modes={},broad=False)
    if not len(active):return out
    spawn=start+int(active[0]);out['spawn']=spawn
    x,y=map(int,j['centres'][m]); target=int(ORB[24*x+y]); endpoints={int(MID[target]),int(OTHER[target])}
    prior_columns=[i for number in range(m) for i in (number,number+3)]
    old_observations=np.flatnonzero(pub['relic_nodes_mask'][:,prior_columns].any(axis=1))
    if not len(old_observations):return out
    context=max(start,spawn,int(old_observations[0]))
    if context>start+57:return out
    old=previous_centres(pub,context,m)
    sep=min(int(DIST[int(MID[target]),k]) for k in old.values())
    out.update(relation='inner' if sep<=2 else ('overlap' if sep<=4 else 'outside'),distance=sep,centre=target)
    if target in old.values():
        out['already_registered']=True
        return out
    scores=j['weights'].reshape(-1);counts=j['active'].sum(axis=1)
    threshold_pre=int(counts[spawn-1]); zone=ZONE[target]
    until=min(sight-3,start+57,start+100)
    if until<spawn:return out
    effects={}
    for t in range(context,until+1):
        # The inherited wrong fields must be active at the proposed sight, not simply close to a new centre.
        true=(scores>0)&(scores<=counts[t]); bad=zone&history[t,1].reshape(-1)&true
        if bad.any(): effects[t]=dict(pairs=orbits(bad),new_pairs=orbits(bad&(scores>threshold_pre)))
    out['raw_pair_turns']=sum(len(x['pairs']) for x in effects.values())
    if not effects:return out
    def proposal(t,depart=None,uid=None,path=None):
        return dict(at=t,depart=depart,uid=uid,path=path,**effects[t])
    initial=min(effects);out['modes']['ideal']=proposal(initial)
    for t in range(start+1,min(start+49,until-1)+1):
        known=previous_centres(pub,t,m)
        if not known or target in known.values():continue
        usable=[a for a in range(t+1,min(t+8,until)+1) if a in effects]
        if not usable:continue
        free=free_units(pub,t,team,cost)
        if not len(free):continue
        # Optimistic floor for reaching either centre's Chebyshev-one sensor square, through any terrain.
        positions=pub['position'][t,team,free]
        floor=min(max(0,abs(int(px)-c//24)-1)+max(0,abs(int(py)-c%24)-1) for px,py in positions for c in endpoints)
        if floor>max(usable)-t:continue
        out['broad']=True
        reach=alternatives(pub,t,team,cost,only=endpoints)
        for uid,path in reach.values():
            for a in usable:
                if a<t+len(path)-1:continue
                key=(a,len(path),t,uid,path)
                oldroute=out['modes'].get('route')
                if oldroute is None or key<(oldroute['at'],len(oldroute['path']),oldroute['depart'],oldroute['uid'],oldroute['path']):
                    out['modes']['route']=proposal(a,t,uid,path)
                break
    for name,order in orders.items():
        t=order['depart']; path=order['path']
        # The precommitted route visits its known squares and may wait at its chosen centre until step eight.
        sequence=path[1:] + [path[-1]]*(9-len(path))
        for dt,cell in enumerate(sequence,1):
            if cell in endpoints and t+dt in effects:
                out['modes'][name]=proposal(t+dt,t,order['uid'],path);break
    return out


def shadows(pub,j,hist,meta,matches,template):
    main=copy.deepcopy(template)
    main.reset_game();main.sensor_range=int(meta['cfg']['unit_sensor_range'])
    def world(agent,data):return data[::-1,::-1].T if agent.mirrored else data
    shadows={};pairs={};checks=0
    scores=j['weights'].reshape(-1); counts=j['active'].sum(axis=1)
    for t in range(303):
        m,k=divmod(t,101)
        if k==0:
            shadows={};pairs={}
        mo=matches[m-1]['modes'] if m else {}
        o=observation(pub,t)
        starts=[name for name,event in mo.items() if event['at']==t]
        for name in starts:
            shadows[name]=copy.deepcopy(main);pairs[name]=set(mo[name]['pairs'])
            mo[name].update(opened=[],earlier=[],other_true=[],false_positive=[],first_classified={},
                            classification_pair_ticks=0,eligible_pair_ticks=0)
        main.observe(o)
        baseline=world(main,main.point_tiles).reshape(-1); main_dead=world(main,main.dead_tiles).reshape(-1)
        assert np.array_equal(baseline,pub['known_points'][t].reshape(-1)) and np.array_equal(main_dead,hist[t,0].reshape(-1))
        checks+=1
        for name,agent in shadows.items():
            event=mo[name]
            if name in starts:
                # Isolate V16's reaction to a genuine new marker; all other public inputs stay identical to the recorded trajectory.
                assert j['active'][t,m] and not pub['relic_nodes_mask'][101*m:t+1,[m,m+3]].any()
                o2={**o,'relic_nodes':o['relic_nodes'].copy(),'relic_nodes_mask':o['relic_nodes_mask'].copy()}
                o2['relic_nodes'][m]=j['centres'][m];o2['relic_nodes_mask'][m]=True
                agent.observe(o2)
            else:agent.observe(o)
            points=world(agent,agent.point_tiles).reshape(-1); deads=world(agent,agent.dead_tiles).reshape(-1)
            true=(scores>0)&(scores<=counts[t]); gained=set(orbits(points&~baseline&true))
            opened=set(orbits(main_dead&~deads&true)) & pairs[name]
            if name in starts:event['opened']=sorted(opened)
            selected=gained & pairs[name]
            for key in selected:event['first_classified'].setdefault(str(key),t)
            event['earlier']=sorted(set(event['earlier'])|selected)
            event['other_true']=sorted(set(event['other_true'])|(gained-selected))
            event['false_positive']=sorted(set(event['false_positive'])|set(orbits(points&~baseline&~true)))
            event['classification_pair_ticks']+=len(selected);event['eligible_pair_ticks']+=len(opened)
    return checks


def run(lane):
    limit_threads()
    templates=[r3_package_agent(f'player_{i}',PACKAGE)._imitation.belief for i in (0,1)]
    binds={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name:digest(p) for p in
           (HERE/'PLAN.md',Path(__file__),HERE/'wege.py',STUDY/'nullwissen/gedaechtnis.py',
            STUDY/'spaetgebiet/ortsmodell/ort.py',STUDY.parent/'v16_finalwoche_20261122/reliktorte/paarhaeufigkeiten.npz',PACKAGE)}
    files=sorted(DATA.glob('*.json'));assert len(files)==160
    out=WORK/'zweiterfund';out.mkdir(exist_ok=True)
    for f in files[lane::2]:
        dest=out/(f.stem+'.json')
        meta=json.loads(f.read_text()); dpath=DEAD/(f.stem+'.npz')
        src={**binds,'public':meta['public_sha'],'referee':meta['private_sha'],'negative':digest(dpath)}
        if dest.exists():
            assert json.loads(dest.read_text())['source']==src
            continue
        pub=load(DATA,meta,'public')
        with np.load(dpath,allow_pickle=False) as z:
            hist=np.unpackbits(z['bits'],axis=-1,bitorder='little').reshape(303,3,24,24).astype(bool)
        # Route commitments for both matches are made entirely before the separate referee file is read.
        orders=[public_orders(pub,hist[:,1],meta,m) for m in (1,2)]
        j=load(DATA,meta,'private')
        truth=(j['weights'][None]>0)&(j['weights'][None]<=j['active'].sum(1)[:,None,None])
        wrong=hist[:,0]&truth
        assert not (wrong&~hist[:,1]).any()
        matches=[run_match(pub,j,hist,meta,m,orders[m-1]) for m in (1,2)]
        checks=shadows(pub,j,hist,meta,matches,templates[meta['team']])
        record=dict(seed=meta['seed'],team=meta['team'],opponent=meta['opponent'],checks=checks,
                    false_dead_world_ticks=int(wrong.sum()),matches=matches,source=src)
        tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(record,sort_keys=True,separators=(',',':'))+'\n');tmp.replace(dest)
    print(lane,'complete',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('lane',type=int,choices=(0,1));run(p.parse_args().lane)
