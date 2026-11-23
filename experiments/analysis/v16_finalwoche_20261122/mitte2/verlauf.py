"""Replay 54 complete archived V16 games and matched, single-command alternatives."""
import argparse
import csv
from hashlib import sha256
import json
import os
from pathlib import Path
import random

import jax
import numpy as np
import torch
from mitte import HERE, PACKAGE, V16, MODEL_SHA, SOURCE_SHA, Middle, model, sha
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.scoring import match_points_after_step

DATA=HERE.parents[1]
ARCHIVES=(("devf_20261117/bestaetigung3_kandidat.csv","e9d6946d7894ebd4e3d0abb41341a66b95df68d0c897c486139dca00a2ee6cef"),
          ("devh_20261117/bestaetigung5_k.csv","94e7f359be85323561dbfefc4a43668a2b82bee06a8315e82ca33367ee8a9e04"))
SCORES=("game_win","our_wins","opp_wins","our_points","opp_points")


def schedule():
    rows={}
    for filename,digest in ARCHIVES:
        file=DATA/filename
        if sha(file)!=digest:raise ValueError("Wrong archive")
        with file.open() as src:
            for r in csv.DictReader(src):
                if r["opponent"]=="solution92":
                    key=(int(r["seed"]),r["side"])
                    if key in rows:raise ValueError("Duplicate archival key")
                    rows[key]={k:int(r[k]) for k in SCORES}
    lost=json.loads((HERE.parent/"spielabstand/spielabstand.json").read_text())
    holdout={r["seed"] for r in lost["games"]}
    selected=[(r["seed"],r["side"],"verlust") for r in lost["games"] if r["matches"][0]["win"]==1]
    order=sorted([(seed,side) for (seed,side),r in rows.items() if r["game_win"] and seed not in holdout],
                 key=lambda k:sha256(f"mitte2-vorpruefung-{k[0]}-{k[1]}".encode()).hexdigest())
    used=set()
    for i in range(27):
        seed,side=next(k for k in order if k[0] not in used and k[1]==f"player_{i%2}")
        used.add(seed);selected.append((seed,side,"kontrolle"))
    if len(selected)!=54 or len(used)!=27 or len({s[:2] for s in selected})!=54:
        raise ValueError("Archive sample is not 27+27")
    return [(r,rows[r[:2]]) for r in selected]


def sources():
    return {n:sha(HERE/n) for n in ("PLAN.md","mitte.py","optionen.py","technik.py","technik_0.json",
                                     "technik_1.json","verlauf.py")}


def save(path,row):
    tmp=path.with_suffix(f".{os.getpid()}.tmp")
    with tmp.open("w") as f:
        json.dump(row,f,sort_keys=True,separators=(",",":"));f.write("\n");f.flush();os.fsync(f.fileno())
    tmp.replace(path)


def state_digest(state):
    digest=sha256()
    for leaf in jax.tree_util.tree_leaves(state):
        value=np.asarray(leaf)
        digest.update(str((value.dtype,value.shape)).encode())
        digest.update(value.tobytes())
    return digest.hexdigest()


class Track:
    def __init__(self, env, actor,team):
        self.env=env; self.actor=actor;self.team=team
        self.side=f"player_{team}";self.other=f"player_{1-team}"
        self.gains=[];self.match_wins=[]
        self.pivot=None;self.prior=sha256()

    def reset(self, **kw):
        observation,info=self.env.reset(**kw)
        self.previous=observation[self.side]
        return observation,info

    def step(self, actions):
        i=len(self.gains)
        seq=np.stack((actions["player_0"],actions["player_1"])).astype("<i2")
        event=self.actor.event
        if event and event["step"]==i:
            if self.pivot is not None:raise ValueError("Second pivot")
            native=seq.copy()
            native[self.team]=self.actor.original
            current=self.env
            self.pivot=dict(before=self.prior.hexdigest(),state=state_digest(current.state),
                            rng=np.asarray(jax.random.key_data(current.rng_key)).tolist(),
                            simultaneous_native=sha256(native.tobytes()).hexdigest())
            count=np.count_nonzero(np.any(native!=seq,axis=2))
            if count!=int(self.actor.apply):
                raise ValueError("Original or the number of replaced commands disagrees")
            if self.actor.apply:
                u=event["uid"]
                if not np.array_equal(seq[self.team,u],[event["world"],0,0]):
                    raise ValueError("Incorrect world action")
        next_obs,reward,term,trunc,info=self.env.step(actions)
        before=self.previous;after=next_obs[self.side]
        delta=np.asarray(match_points_after_step(before,after,info))-np.asarray(before["team_points"])
        if delta.shape!=(2,) or min(delta)<0:raise ValueError("Negative or malformed per-step points")
        self.gains.append([int(delta[self.team]),int(delta[1-self.team])])
        self.prior.update(seq.tobytes())
        self.prior.update(delta.astype("<i2").tobytes())
        if (i+1)%101==0:
            change=np.asarray(after["team_wins"])-np.asarray(before["team_wins"])
            if sorted(change.tolist())!=[0,1]:raise ValueError("Invalid match decision")
            self.match_wins.append(int(change[self.team]))
        self.previous=after
        return next_obs,reward,term,trunc,info


def replay(env,seed,side,net,apply):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    team=int(side[-1]);actor=Middle(side,net,apply)
    rival=make_opponent("solution92",f"player_{1-team}")
    tracer=Track(env,actor,team)
    result=play_game(tracer,actor,rival,seed,side,False)
    require_no_agent_errors(actor.base,rival)
    scores={k:result[k] for k in SCORES}
    if (result["steps"]!=303 or len(tracer.gains)!=303 or len(tracer.match_wins)!=3
            or sum(tracer.match_wins)!=result["our_wins"] or result["point_counting_version"]!=2
            or np.sum(tracer.gains,axis=0).tolist()!=[scores["our_points"],scores["opp_points"]]):
        raise ValueError("Incomplete or inconsistent match record")
    return dict(scores=scores,match_wins=tracer.match_wins,event=actor.event,pivot=tracer.pivot,gains=tracer.gains,
                behind_steps=actor.behind_steps,options_steps=actor.options_steps,changes=actor.changed)


def run(lane):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads();net=model();stamp=sources()
    folder=HERE/"archivspiele";folder.mkdir(exist_ok=True)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for (seed,side,group),expected in schedule()[lane::2]:
            target=folder/f"{seed}_{side}.json"
            if target.exists():
                old=json.loads(target.read_text())
                if old["original"]["scores"]!=expected or old["sources"]!=stamp:
                    raise ValueError("A previous record differs")
                continue
            original=replay(env,seed,side,net,False)
            if original["scores"]!=expected or (group=="verlust" and original["match_wins"]!=[1,0,0]):
                raise ValueError(f"Archived result differs at {seed}, {side}")
            alt=None
            if original["event"]:
                pos=original["event"]["step"]
                alt=replay(env,seed,side,net,True)
                if (alt["event"]!=original["event"] or alt["pivot"]!=original["pivot"] or alt["changes"]!=1
                        or alt["gains"][:pos]!=original["gains"][:pos]):
                    raise ValueError("Histories or pivot state do not match")
            save(target,dict(seed=seed,side=side,group=group,sources=stamp,weight=MODEL_SHA,
                             release=V16,student_source=SOURCE_SHA,original=original,alternate=alt))
    finally:
        env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("lane",type=int,choices=(0,1));run(p.parse_args().lane)
