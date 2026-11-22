"""Collect paired early training transitions with unchanged simultaneous commands and random stream."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys

import jax
import numpy as np
import torch

from sicht import HERE,ROOT,NAMES,Scout,geo,new_area
sys.path.insert(0,str(HERE.parent/"zugnutzen"))
from berater import PACKAGE,V16
from sammeln import occupations
sys.path.insert(0,str(HERE.parent/"kartenparameter"))
from auswerten import generate
from luxai_s3.wrappers import LuxAIS3GymEnv
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent


def panel(start,count):
    seeds=np.arange(start,start+max(256,count*4),dtype=np.int32)
    sensor=np.asarray(jax.jit(jax.vmap(generate))(seeds))[:,0]
    output=seeds[sensor<=2][:count].tolist()
    if len(output)!=count:raise ValueError("Insufficient low-visibility maps")
    return output


def measure(state,team,seen):
    sensor=np.asarray(state.sensor_mask[team],bool)
    if team==1:sensor=geo.mirror_map(sensor)
    pairs,cells=new_area(sensor.ravel(),seen)
    points=occupations(state)
    return np.array([pairs,cells,points[team],points[1-team]],dtype=np.float32)


def collect(folder,part):
    if os.getenv("PYTHONHASHSEED")!="0" or sha256(PACKAGE.read_bytes()).hexdigest()!=V16 or not verify():
        raise ValueError("Reference mismatch")
    limit_threads()
    if part=="train":start,n=160368000,96
    else:start,n=160368500,32
    seeds=panel(start,n)
    binding=sha256((HERE/"PLAN.md").read_bytes()+(HERE/"sicht.py").read_bytes()+(HERE/"erheben.py").read_bytes()).hexdigest()
    folder.mkdir(parents=True,exist_ok=True)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for i,seed in enumerate(seeds):
            team=i%2
            side,other=f"player_{team}",f"player_{1-team}"
            kind=("kaggle3","solution92")[i//2%2]
            manifest=folder/f"{seed}.json"
            data=folder/f"{seed}.npz"
            if manifest.exists():
                r=json.loads(manifest.read_text())
                if r["source"]!=binding or r["sha256"]!=sha256(data.read_bytes()).hexdigest():
                    raise ValueError("Different stored collection")
                continue
            agent=Scout(r3_package_agent(side,PACKAGE))
            rival=make_opponent(kind,other)
            agent.new_game(side)
            if hasattr(rival,"new_game"):rival.new_game(other)
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
            obs,info=env.reset(seed=seed)
            if int(info["params"]["unit_sensor_range"])>2:raise ValueError("Wrong map stratum")
            for p in (agent,rival):p.set_env_cfg(info["params"])
            x,targets,turns,uids=[],[],[],[]
            checked=False
            for step in range(46):
                original=agent.act(step,obs[side])
                enemy=rival.act(step,obs[other])
                commands={side:original,other:enemy}
                alternatives=[]
                check=None
                if agent.last:
                    _,key=jax.random.split(env.rng_key)
                    def counter(actions):
                        end=env.jax_env.step(key,env.state,actions,env.env_params)[-1]["final_state"]
                        return measure(end,team,agent.seen)
                    if not checked:check=counter(commands)
                    for _,uid,direction,feature in agent.last:
                        act=original.copy()
                        act[uid]=[direction,0,0]
                        if np.count_nonzero(np.any(act!=original,axis=1))!=1:
                            raise ValueError("Expected one changed ship")
                        alternatives.append((counter({side:act,other:enemy}),uid,feature))
                nxt,_,term,trunc,info=env.step(commands)
                if bool(term[side]) or bool(trunc[side]):raise ValueError("Unexpected terminal")
                if alternatives:
                    real=measure(info["final_state"],team,agent.seen)
                    sensor=np.asarray(nxt[side]["sensor_mask"],bool)
                    if team==1:sensor=geo.mirror_map(sensor)
                    if new_area(sensor.ravel(),agent.seen)!=tuple(real[:2]):
                        raise ValueError("Counterfactual measurement differs from public observation")
                    if check is not None and not np.array_equal(check,real):raise ValueError("RNG parity")
                    if not np.array_equal(real[2:],(nxt[side]["team_points"]-obs[side]["team_points"])[[team,1-team]]):
                        raise ValueError("Point accounting")
                    checked=True
                    for alt,uid,feature in alternatives:
                        x.append(feature);targets.append(alt-real);turns.append(step);uids.append(uid)
                obs=nxt
            require_no_agent_errors(agent.base,rival)
            tmp=data.with_suffix(".pending.npz")
            np.savez_compressed(tmp,x=np.asarray(x,np.float32).reshape(-1,len(NAMES)),
                                delta=np.asarray(targets,np.float32).reshape(-1,4),
                                step=np.asarray(turns,np.int16),uid=np.asarray(uids,np.int8))
            tmp.replace(data)
            row=dict(seed=seed,side=side,opponent=kind,split=part,ticks=46,rows=len(x),calibration=checked,
                     source=binding,sha256=sha256(data.read_bytes()).hexdigest())
            tmp=manifest.with_suffix(".pending")
            tmp.write_text(json.dumps(row)+"\n")
            tmp.replace(manifest)
            print(seed,len(x),flush=True)
    finally:env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    p.add_argument("part",choices=("train","valid"))
    a=p.parse_args()
    collect(a.folder,a.part)
