"""Paired exact-prefix twelve-step counterfactuals with two fixed worker lanes."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import random

import jax
import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

from berater import Advice, world
from originale import HASHES, HERE, PACKAGE, R3, SCRATCH, STUDY, digest, limit_threads, make_opponent, r3_package_agent, sensor
from scripts.par_eval import require_no_agent_errors
from scripts.scoring import point_tile_map
from spielen import common_source, stamp, write_once


def cards(start=163410000,n=64):
    values=np.arange(start,start+1000,dtype=np.int32)
    visible=np.asarray(jax.jit(jax.vmap(sensor))(values))
    out=values[visible==1][:n].tolist();assert len(out)==n
    return out


def update_hash(h,value):
    leaves,tree=jax.tree_util.tree_flatten(value);h.update(str(tree).encode())
    for leaf in leaves:
        array=np.asarray(leaf)
        h.update(str(array.dtype).encode());h.update(str(array.shape).encode());h.update(array.tobytes(order='C'))


def hash_value(*args):
    h=sha256()
    for v in args:update_hash(h,v)
    return h.hexdigest()


def credited(state):
    mask=point_tile_map(state);p=np.asarray(state.units.position);e=np.asarray(state.units.energy).reshape(2,-1)
    alive=np.asarray(state.units_mask,dtype=bool)&(e>=0);scores=[]
    for i in (0,1):
        cells={24*int(x)+int(y) for x,y in p[i,alive[i]] if mask[int(x),int(y)]}
        scores.append(cells)
    return scores


def checked_command(command):
    a=np.asarray(command);assert a.shape==(16,3) and np.issubdtype(a.dtype,np.integer) and ((a[:,0]>=0)&(a[:,0]<=5)).all()
    return a


def game(env,seed,team,rival,apply):
    own,other=f'player_{team}',f'player_{1-team}'
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    our=Advice(own,apply);opp=r3_package_agent(other,PACKAGE) if rival=='v16' else make_opponent('solution92',other)
    our.new_game(own)
    if hasattr(opp,'new_game'):opp.new_game(other)
    random.seed(seed);np.random.seed(seed)
    obs,params=env.reset(seed=seed);cfg=params['params'];assert cfg['unit_sensor_range']==1
    for a in (our,opp):
        if hasattr(a,'set_env_cfg'):a.set_env_cfg(cfg)
    stream=sha256();record=None;track=[];m1=None;count=0
    for t in range(169):
        o=obs[own];assert int(o['steps'])==t and int(o['match_steps'])==t%101
        update_hash(stream,obs)
        act=checked_command(our.act(t,o));enemy=checked_command(opp.act(t,obs[other]))
        commands={own:act,other:enemy}
        changed=np.flatnonzero(np.any(act!=our.last_base,axis=1))
        if len(changed):
            first=our.first;assert apply and len(changed)==1 and first and t<first['step']+3 and t>=first['step'] and 101<=t<202
            u=int(changed[0]);assert u==first['uid'] and m1==1 and bool(o['units_mask'][team,u])
            d=int(act[u,0]);assert 1<=d<=4 and not act[u,1:].any() and d!=int(our.last_base[u,0]) and our.last_base[u,0]!=5
            assert np.array_equal(act[u],our.last_r3[u])
            model=our.base._imitation;e=our.teacher._actor
            # The pure imitation release does not use the optional estimator.
            # R3 uses it on every live decision. Any existing record must match.
            v16_record=model.param_est._prev
            assert v16_record is None or np.array_equal(v16_record['act'],act)
            assert np.array_equal(e.param_est._prev['act'],act)
            assert model._prev_actions[u]==((0,2,1,4,3)[d] if team else d)
        if our.first and t==our.first['step']:
            first=our.first;g=divmod(first['goal'],24)
            assert 8<=first['turn']<=55 and o['sensor_mask'][g] and our.prior[first['goal']]
            assert world(our.base._imitation.belief.point_tiles,bool(team))[g]
            record=dict(first=first.copy(),public_history=stream.hexdigest(),current_opponent=hash_value(enemy),
                current_native=hash_value(our.last_base),current_advice=hash_value(our.last_r3),
                engine=hash_value(env.state),rng=hash_value(jax.random.key_data(env.rng_key)),
                prior_points=np.asarray(o['team_points'],int).tolist(),prior_match_wins=np.asarray(o['team_wins'],int).tolist())
            assert len(changed)==int(apply)
        update_hash(stream,commands)
        obs,_,terminated,truncated,_=env.step(commands);after=obs[own];count+=1
        assert not terminated[own] and not truncated[own]
        if t==100:m1=int(after['team_wins'][team])
        if record:
            credit=credited(env.state);g=record['first']['goal'];p0=np.asarray(o['team_points']);p1=np.asarray(after['team_points'])
            assert [len(c) for c in credit]==(p1-p0).tolist()
            track.append(dict(team_points=p1.tolist(),target_credited=g in credit[team],
                target_true=bool(point_tile_map(env.state).ravel()[g]),
                own_position=np.asarray(env.state.units.position)[team,record['first']['uid']].astype(int).tolist(),
                own_alive=bool(np.asarray(env.state.units_mask)[team,record['first']['uid']]),
                own_energy=int(np.asarray(env.state.units.energy)[team,record['first']['uid'],0])))
            if len(track)==12:break
        elif t==156 or (m1==0 and t==100):break
    require_no_agent_errors(our.base,opp)
    if our.teacher is not None:assert not our.teacher.caught_errors
    assert len(track)==(12 if record else 0) and our.changes==len(our.events)
    assert not our.events or (len({e[1] for e in our.events})==len({e[4] for e in our.events})==1 and len(our.events)<=3)
    return dict(m1=m1,decision=record,track=track,events=our.events,action_steps=count,final_history=stream.hexdigest())


def identity():
    assert digest(PACKAGE)==HASHES['v16'] and digest(R3)==HASHES['r3']
    assert json.loads((HERE/'originalpruefung/ergebnis.json').read_text())['fresh_gate']
    assert all(json.loads((HERE/'archiv/ergebnis.json').read_text())['historical_gates'].values())
    assert json.loads((HERE/'technik.json').read_text())['source']==digest(HERE/'berater.py')
    guard=json.loads((HERE/'schutzpruefung.json').read_text())
    assert guard['count']==34 and guard['source']==digest(HERE/'berater.py')
    shadow=json.loads((HERE/'schatten.json').read_text())
    assert sum(r['equal_unit_actions'] for r in shadow['rows'])==5120 and shadow['source']==digest(HERE/'berater.py')
    files=[HERE/n for n in ('PLAN.md','GEGENPLAN.md','berater.py','originale.py','gegenrunde.py','technik.json','schutzpruefung.json','schatten.json')]
    files.append(STUDY.parent/'v16_finalwoche_20261122/fruehuebergabe/staffel.py')
    return dict(common=stamp(common_source()),r3=HASHES['r3'],files={f.name:digest(f) for f in files})


def run(lane):
    assert os.environ.get('PYTHONHASHSEED')=='0'
    limit_threads();source=identity();root=SCRATCH/'gegenrunde';root.mkdir(parents=True,exist_ok=True)
    write_once(root/'quelle.json',source);version=stamp(source);env=LuxAIS3GymEnv(numpy_output=True)
    try:
        from fcntl import flock,LOCK_EX,LOCK_NB
        with (root/f'lane{lane}.lock').open('a+') as lock:
            flock(lock,LOCK_EX|LOCK_NB)
            for i,seed in enumerate(cards()):
                for j,rival in enumerate(('solution92','v16')):
                    if (i+j)%2!=lane:continue
                    team=i%2;path=root/f'{seed}-{team}-{rival}.json'
                    if path.exists():
                        assert json.loads(path.read_text())['source']==version
                        continue
                    control=game(env,seed,team,rival,False)
                    treatment=game(env,seed,team,rival,True) if control['decision'] else None
                    if treatment:
                        assert treatment['decision']==control['decision'] and treatment['m1']==control['m1']==1
                        assert treatment['events'] and not control['events']
                    row=dict(seed=seed,team=team,rival=rival,control=control,treatment=treatment,source=version)
                    write_once(path,row)
    finally:env.close()
    assert identity()==source
    print('Completed counterfactual lane',lane,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('lane',type=int,choices=(0,1));run(p.parse_args().lane)
