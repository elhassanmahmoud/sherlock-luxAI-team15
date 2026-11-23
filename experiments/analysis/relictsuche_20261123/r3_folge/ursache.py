"""Reproduce both actual courses of all discordant complete-game seats; diagnose public and referee endpoints."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import gzip
import json
from pathlib import Path
import random

import jax
import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

from archiv import compressed, save
from berater import Advice, world
from gegenrunde import credited, hash_value, update_hash
from originale import HERE, PACKAGE, SCRATCH, limit_threads, make_opponent, r3_package_agent
from pilot import FullMonitor
from spielen import play_game, require_no_agent_errors, write_once
from scripts.scoring import match_points_after_step


def seats():
    rows=[json.loads(line) for line in gzip.decompress((HERE/'pilotpruefung/spiele.jsonl.gz').read_bytes()).splitlines()]
    by=defaultdict(dict)
    for r in rows:by[(r['seed'],r['team'])][r['arm']]=r
    result=[];counts=Counter()
    for (seed,team),all_arms in sorted(by.items()):
        active=all_arms['solution'];native=all_arms['reference']
        if active['win']!=native['win']:result.append((seed,team,'solution',active,native))
        active=all_arms['direct']
        if active['matches'][0]['win']==0:
            assert not active['events']
            continue
        other=by[seed,1-team]['direct']
        assert other['matches'][0]['win']==0 and not other['events']
        native={**other,'team':team,'win':1-other['win'],'matches':[dict(win=1-m['win'],points=list(reversed(m['points']))) for m in other['matches']]}
        assert native['matches'][0]==active['matches'][0]
        if not active['events']:assert native['matches']==active['matches'] and native['trace']==active['trace'];counts['both_inert']+=1
        counts['maps']+=1;counts['m2_'+str(active['matches'][1]['win']-native['matches'][1]['win'])]+=1
        counts['m3_'+str(active['matches'][2]['win']-native['matches'][2]['win'])]+=1
        counts['whole_'+str(active['win']-native['win'])]+=1
        if active['win']!=native['win']:result.append((seed,team,'direct',active,native))
    assert counts['maps']==32 and len(result)==8 and sum(x[2]=='solution' for x in result)==1
    return result,dict(counts)


class Diagnostic(FullMonitor):
    def __init__(self,env,team,actor,apply,at,target):
        super().__init__(env,team,actor if apply else None)
        self.observed=actor;self.at=at;self.target=target;self.prefix=None;self.states={};self.credits=defaultdict(Counter)
        self.knew={};self.trace_prefix=sha256();self.post_states=0

    def step(self,actions):
        t=self.turn;o=self.old;team=self.team
        if t<=self.at:update_hash(self.trace_prefix,o)
        if t==self.at:
            self.prefix=dict(public=self.trace_prefix.hexdigest(),engine=hash_value(self.env.state),rng=hash_value(jax.random.key_data(self.env.rng_key)),
                             opponent=hash_value(actions[f'player_{1-team}']),points=np.asarray(o['team_points'],int).tolist())
        if t<self.at:update_hash(self.trace_prefix,actions)
        model=self.observed.base._imitation if isinstance(self.observed,Advice) else self.observed._imitation
        if t in (self.at,201,202,203,302):
            b=model.belief;self.knew[str(t)]=np.flatnonzero(world(b.point_tiles,b.mirrored).ravel()).tolist()
        out=super().step(actions);after=out[0][self.side];ms=t%101
        if t>=self.at:
            state=out[4]['final_state'] if ms==100 else self.env.state
            score=match_points_after_step(o,after,out[4]);prior=np.asarray(o['team_points']);cells=credited(state)
            assert (score-prior).tolist()==list(map(len,cells))
            self.post_states+=1
            for i in (0,1):self.credits[(t//101,i)].update(cells[i])
            if t in (self.at+5,self.at+11,201,302):self.states[str(t)]=score.astype(int).tolist()
        return out


def collect(env,seed,team,rival,active,reference,apply):
    side=f'player_{team}';other=f'player_{1-team}';random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    actor=Advice(side,True) if apply else r3_package_agent(side,PACKAGE)
    enemy=r3_package_agent(other,PACKAGE) if rival=='direct' else make_opponent('solution92',other)
    at,_,_,_,target=active['events'][0];mon=Diagnostic(env,team,actor,apply,at,target)
    game=play_game(mon,actor,enemy,seed,side,False);require_no_agent_errors(actor,enemy)
    row=active if apply else reference
    assert game['game_win']==row['win'] and mon.matches==row['matches'] and mon.digest.hexdigest()==row['trace']
    assert mon.events==(active['events'] if apply else []) and mon.post_states==303-at
    return dict(matches=mon.matches,action_trace=mon.digest.hexdigest(),prefix=mon.prefix,states=mon.states,
                known=mon.knew,checked=mon.post_states,credits={f'{m}-{i}':dict(sorted(c.items())) for (m,i),c in mon.credits.items()})


def run(lane):
    limit_threads();cases,_=seats();folder=SCRATCH/'ursache';folder.mkdir(exist_ok=True)
    version=sha256(Path(__file__).read_bytes()).hexdigest();env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for ix,(seed,team,rival,active,reference) in enumerate(cases):
            if ix%2!=lane:continue
            dst=folder/f'{seed}-{team}-{rival}.json'
            if dst.exists():assert json.loads(dst.read_text())['source']==version;continue
            old=collect(env,seed,team,rival,active,reference,False)
            new=collect(env,seed,team,rival,active,reference,True)
            assert old['prefix']==new['prefix']
            write_once(dst,dict(seed=seed,team=team,rival=rival,events=active['events'],control=old,active=new,source=version))
    finally:env.close()
    print('Technical causal reproduction lane complete',lane)


def summarize():
    cases,geometry=seats();raw=[]
    for s,team,opp,_,_ in cases:
        path=SCRATCH/'ursache'/f'{s}-{team}-{opp}.json';row=json.loads(path.read_text());assert row['source']==sha256(Path(__file__).read_bytes()).hexdigest()
        raw.append(row)
    out=HERE/'ursachen';out.mkdir(exist_ok=True);compressed(out/'wertungen.jsonl.gz',raw);small=[]
    for r in raw:
        u=r['team'];v=1-u;at,uid,before,after,target=r['events'][0]
        a=r['active'];b=r['control'];ds={}
        for t in (at+5,at+11,201,302):
            p=a['states'][str(t)];q=b['states'][str(t)];ds[str(t)]=[p[u]-q[u],p[v]-q[v],(p[u]-q[u])-(p[v]-q[v])]
        def delta_cells(m,j):
            k=f'{m}-{j}';ca=a['credits'][k];cb=b['credits'][k]
            return sorted([[int(c),ca.get(c,0)-cb.get(c,0)] for c in ca.keys()|cb.keys() if ca.get(c,0)!=cb.get(c,0)],key=lambda x:(-abs(x[1]),x[0]))
        delta={f'm{m+1}_{n}':delta_cells(m,j) for m in (1,2) for n,j in (('own',u),('opponent',v))}
        s3='203';ka=set(a['known'][s3]);kb=set(b['known'][s3])
        for m,t in ((1,'201'),(2,'302')):
            for who,j,k in (('own',u,0),('opponent',v,1)):
                assert sum(v for _,v in delta[f'm{m+1}_{who}'])==ds[t][k]
        small.append(dict(seed=r['seed'],team=u,rival=r['rival'],uid=uid,turn=at-101,target=divmod(target,24),
                 whole_change=int(sum(m['win'] for m in a['matches'])>=2)-int(sum(m['win'] for m in b['matches'])>=2),
                 net_after_12=ds[str(at+11)][2],m2=ds['201'],m3=ds['302'],m3_known_only_active=sorted(ka-kb),m3_known_only_native=sorted(kb-ka),
                 target_m3_delta={n:dict(delta['m3_'+n]).get(target,0) for n in ('own','opponent')},cell_differences=delta))
    save(out/'ergebnis.json',dict(direct_controls=geometry,cases=small,full_replayed_games=2*len(raw),checked_post_states=sum(x[n]['checked'] for x in raw for n in ('active','control'))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('0','1','auswerten'));mode=p.parse_args().mode
    summarize() if mode=='auswerten' else run(int(mode))
