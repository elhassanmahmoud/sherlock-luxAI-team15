"""Unchanged V16 match traces. Public arrays and private scoring/centre labels use separate files."""
import argparse
import fcntl
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys

import jax
import jax.numpy as jnp
import numpy as np
import torch
from luxai_s3.params import env_params_ranges
from luxai_s3.wrappers import LuxAIS3GymEnv

HERE=Path(__file__).resolve().parent
STUDY=HERE.parents[1]
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import match_points_after_step
ZIP=ROOT/"experiments/releases/20261117_sherlock_v16/agent.zip"
V16="0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
STORE=Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/spaetort")
SPLITS={"train":(162000000,160),"valid":(162015000,48),"tech":(162025000,16),"performance":(162030000,48)}
MIRROR=np.array([0,2,1,4,3])


def sensor(seed):
    key,_=jax.random.split(jax.random.key(seed))
    for name,vals in env_params_ranges.items():
        key,sub=jax.random.split(key)
        if name=="unit_sensor_range":
            return jax.random.choice(sub,jnp.asarray(vals))
    raise RuntimeError("No public sensor")


def prepare():
    out={}
    for name,(start,n) in SPLITS.items():
        seeds=np.arange(start,start+1200,dtype=np.int32)
        out[name]=seeds[np.asarray(jax.jit(jax.vmap(sensor))(seeds))==1][:n].tolist()
        if len(out[name])!=n:raise ValueError("Insufficient sensor-1 maps")
    if len(set.union(*(set(v) for v in out.values())))!=sum(map(len,out.values())):raise ValueError("Overlap")
    path=HERE/"karten.json"
    if path.exists() and json.loads(path.read_bytes())!=out:raise ValueError("Map panel changed")
    path.write_text(json.dumps(out,indent=2)+"\n")


def source():
    files=(ZIP,Path(__file__),HERE/"LERNPLAN.md",HERE/"karten.json")
    return {p.name:sha256(p.read_bytes()).hexdigest() for p in files}


def save(path,entries):
    tmp=path.with_suffix(".pending.npz")
    np.savez_compressed(tmp,**entries)
    tmp.replace(path)
    return sha256(path.read_bytes()).hexdigest()


def collect(env,seed,team,opp,folder):
    side,other=f"player_{team}",f"player_{1-team}"
    random.seed(seed); np.random.seed(seed);torch.manual_seed(seed)
    actor=r3_package_agent(side,ZIP)
    rival=r3_package_agent(other,ZIP) if opp=="v16" else make_opponent("solution92",other)
    for p,s in ((actor,side),(rival,other)):
        if hasattr(p,"new_game"):p.new_game(s)
    random.seed(seed);np.random.seed(seed)
    obs,info=env.reset(seed=seed)
    cfg=info["params"]
    if cfg["unit_sensor_range"]!=1:raise ValueError("Wrong sight")
    for p in (actor,rival):p.set_env_cfg(cfg)
    from sherlock.features import FEATURE_NAMES
    fs=[FEATURE_NAMES.index(x+"_point") for x in "curdl"]
    enemycol=FEATURE_NAMES.index("enemies_in_sap")
    pub={}; label={}
    push=lambda store,k,v:store.setdefault(k,[]).append(np.asarray(v).copy())
    centres=np.asarray(env.state.relic_nodes)[:3].copy()
    weights=np.asarray(env.state.relic_nodes_map_weights).copy()
    lastscore=np.zeros(2,int)
    matches=[]
    for step in range(303):
        o=obs[side]
        if int(o["steps"])!=step:raise ValueError("Wrong observation order")
        action=actor.act(step,o)
        m=actor._imitation
        mask=np.zeros((16,5),bool); protected=np.ones(16,bool)
        if m.last_fz is not None:
            _,ids,feature,masks,_,_,_=m.last_fz
            ids=np.asarray(ids,int)
            mask[ids]=masks[:,:5][:,MIRROR] if team else masks[:,:5]
            protected[ids]=(feature[:,fs].max(1)>0)|(feature[:,enemycol]>0)
        for k in ("units_mask","sensor_mask","team_points","relic_nodes_mask","relic_nodes"):
            push(pub,k,o[k])
        for k in ("position","energy"):push(pub,k,o["units"][k])
        for k,board in (("terrain",m.belief.tile_type),("known_points",m.belief.point_tiles)):
            push(pub,k,board[::-1,::-1].T if team else board)
        for k,val in (("commands",action),("move_mask",mask),("protected",protected)):
            push(pub,k,val)
        state=env.state
        visible=np.asarray(state.relic_nodes_mask,bool)[:3]
        push(label,"active",visible)
        score_tiles=(weights>0)&(weights<=visible.sum())
        scoring=np.zeros((2,24,24),bool)
        actual_live=np.asarray(state.units_mask,bool)&(np.asarray(state.units.energy)[...,0]>=0)
        realpos=np.asarray(state.units.position)
        for s in (0,1):
            p=realpos[s,actual_live[s]]
            scoring[s,p[:,0],p[:,1]]=score_tiles[p[:,0],p[:,1]]
        if step%101 and not np.array_equal(scoring.sum((1,2)),np.asarray(o["team_points"])-lastscore):
            raise ValueError("Private scored cells and public score differ")
        push(label,"scoring",np.packbits(scoring.reshape(2,576),axis=1,bitorder="little"))
        push(label,"real_position",realpos)
        push(label,"real_live",actual_live)
        lastscore=np.asarray(o["team_points"]).copy()
        enemy=rival.act(step,obs[other])
        obs,_,term,trunc,info=env.step({side:action,other:enemy})
        if step%101==100:matches.append(match_points_after_step(o,obs[side],info).tolist())
        if bool(term[side] or trunc[side])!=(step==302):raise ValueError("Premature termination")
    require_no_agent_errors(actor,rival)
    label.update(centres=centres,weights=weights)
    prefix=f"{seed}-{team}"
    f=folder/(prefix+".npz"); g=folder/(prefix+".richter.npz")
    return dict(seed=seed,team=team,opponent=opp,steps=303,cfg=cfg,matches=matches,win=int(obs[side]["team_wins"][team]>=2),
        public=f.name,private=g.name,public_sha=save(f,{k:np.asarray(v) for k,v in pub.items()}),
        private_sha=save(g,{k:np.asarray(v) for k,v in label.items()}))


def run(worker):
    limit_threads()
    maps=json.loads((HERE/"karten.json").read_bytes())
    identity=source()
    if identity["agent.zip"]!=V16 or os.getenv("PYTHONHASHSEED")!="0":raise ValueError("Unexpected reference")
    jobs=[(part,i,seed) for part in ("train","valid") for i,seed in enumerate(maps[part])]
    offset=(worker*71)%len(jobs)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for part,i,seed in jobs[offset:]+jobs[:offset]:
            team=i%2; opp=("solution92","v16")[i//2%2]
            folder=STORE/part;folder.mkdir(parents=True,exist_ok=True)
            receipt=folder/f"{seed}-{team}.json"
            if receipt.exists():continue
            with receipt.with_suffix(".lock").open("ab") as lock:
                try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:continue
                if receipt.exists():continue
                row=collect(env,seed,team,opp,folder)
                row.update(source=identity,split=part)
                temp=receipt.with_suffix(".tmp");temp.write_text(json.dumps(row,sort_keys=True)+"\n");temp.replace(receipt)
                print(f"Fertig {part} {seed}",flush=True)
    finally:env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("task",choices=("prepare","run"));p.add_argument("--worker",type=int,default=0)
    args=p.parse_args();prepare() if args.task=="prepare" else run(args.worker)
