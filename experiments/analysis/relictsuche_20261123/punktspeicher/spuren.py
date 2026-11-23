"""Unchanged V16 games. Keep public equations, policy readouts and referee checks separate."""
import argparse
import fcntl
import gzip
import json
import os
from pathlib import Path
import random
import sys

import numpy as np
import torch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"vergleich"))
from spielen import (CUTOFF,PACKAGE,SCRATCH as BENCH,Monitor,common_source,datetime,make_opponent,
                     play_game,r3_package_agent,require,require_no_agent_errors,sha,stamp,write_once)
from scripts.experiment import limit_threads
from scripts.scoring import point_tile_map

WORK=BENCH.parent/"punktspeicher"
MIRROR_DIR=(0,2,1,4,3)
DX=(0,0,1,0,-1)
DY=(0,-1,0,1,0)


def encode(array):
    return format(int.from_bytes(np.packbits(np.asarray(array,bool).ravel(),bitorder="little").tobytes(),"little"),"x")


def cells(obs,t):
    alive=np.asarray(obs["units_mask"][t],bool) & (np.asarray(obs["units"]["energy"][t]).ravel()>=0)
    pos=np.asarray(obs["units"]["position"][t])[alive]
    return sorted(set((pos[:,0]*24+pos[:,1]).astype(int).tolist()))


def manifest():
    hist=HERE.parent/"flottenblick/ganzspiel/partien.jsonl.gz"
    return {"shared":common_source(),"observer":sha(Path(__file__)),"plan":sha(HERE/"PLAN.md"),"maps":sha(HERE/"karten.json"),
            "archived_games_sha":sha(hist)}


def jobs(group):
    return [(seed,team) for seed in json.loads((HERE/"karten.json").read_text())[group] for team in (0,1)]


class Recorder(Monitor):
    def __init__(self, env, team, actor):
        super().__init__(env,team,"discovery")
        self.brain=actor
        self.public=[]
        self.policy=[]
        self.referee=[]

    def step(self,actions):
        s=self.turn
        m,ms=divmod(s,101)
        obs=self.old
        p=self.brain._imitation
        b=p.belief
        def world(x):
            return x[::-1,::-1].T if b.mirrored else x
        cmd=np.asarray(actions[self.side])
        own=cells(obs,self.team)
        theirs=cells(obs,1-self.team)
        score=int(obs["team_points"][self.team])
        public=dict(step=s,ms=ms,occupied=own,points=score,
                    epoch_seen=bool(np.asarray(obs["relic_nodes_mask"])[[m,m+3]].any()))
        truth=np.asarray(point_tile_map(self.env.state))
        require(np.array_equal(truth,truth[::-1,::-1].T),"Asymmetric real scoring map")
        if self.referee:
            previous=int(self.referee[-1],16)
            encoded=int(encode(truth),16)
            require((previous&~encoded)==0,"Real point map decreased")
            if ms:
                require(sum(bool(truth[divmod(f,24)]) for f in own)==score-self.public[-1]["points"],"Public occupancy disagrees with scored gain")
        options=[]
        planned=set()
        live=np.asarray(obs["units_mask"][self.team]) & (np.asarray(obs["units"]["energy"][self.team]).ravel()>=0)
        ownpos=np.asarray(obs["units"]["position"][self.team])
        for uid in np.flatnonzero(live):
            x,y=map(int,ownpos[uid])
            d=int(cmd[uid,0])
            if d>4: d=0
            nx,ny=x+DX[d],y+DY[d]
            if 0<=nx<24 and 0<=ny<24:
                planned.add(24*nx+ny)
        if ms and p.last_fz is not None:
            from sherlock.features import FEATURE_NAMES
            ctx,ids,features,masks,_,_,xy=p.last_fz
            threat=FEATURE_NAMES.index("enemies_in_sap")
            for i,raw_uid in enumerate(ids):
                uid=int(raw_uid)
                x,y=map(int,ownpos[uid])
                if not live[uid] or int(cmd[uid,0])>4 or features[i,threat]>0:
                    continue
                energy=int(np.asarray(obs["units"]["energy"][self.team]).ravel()[uid])
                if energy<max(30,4*int(ctx["move_cost"])):
                    continue
                target=ctx["assigned"].get(uid)
                if target is not None:
                    tx,ty=map(int,target)
                    if b.mirrored:
                        tx,ty=23-ty,23-tx
                    target=24*tx+ty
                canon_dirs=[MIRROR_DIR[d] if b.mirrored else d for d in range(1,5)]
                legal=sum(1<<d for d,canonical in enumerate(canon_dirs,1) if masks[i,canonical])
                if legal:
                    options.append([uid,24*x+y,int(cmd[uid,0]),target,legal])
        types=world(np.asarray(b.tile_type))
        self.public.append(public)
        self.referee.append(encode(truth))
        self.policy.append(dict(point=encode(world(b.point_tiles)),dead=encode(world(b.dead_tiles)),
                                known_passable=encode((types>=0)&(types!=2)),visible=encode(obs["sensor_mask"]),
                                enemy=theirs,planned=sorted(planned),free=options))
        return super().step(actions)


def run(group,worker):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    require(os.environ.get("PYTHONHASHSEED")=="0","Uncontrolled hash iteration")
    source=manifest()
    write_once(WORK/"herkunft.json",source)
    binding=stamp(source)
    history={}
    with gzip.open(HERE.parent/"flottenblick/ganzspiel/partien.jsonl.gz","rt") as f:
        for line in f:
            row=json.loads(line)
            if row["id"]=="reference" and row["opponent"]=="solution92":
                history[row["seed"],row["team"]]=row
    path=WORK/group
    locks=path/".leases";locks.mkdir(parents=True,exist_ok=True)
    order=jobs(group)
    offset=worker*19%len(order)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed,team in order[offset:]+order[:offset]:
            require(datetime.now(CUTOFF.tzinfo)<CUTOFF,"Deadline")
            f=path/f"{seed}_{team}.json"
            if f.exists():
                continue
            with (locks/(f.stem+".lock")).open("a+") as lease:
                try:
                    fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:
                    continue
                if f.exists():continue
                random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
                side=f"player_{team}"
                actor=r3_package_agent(side,PACKAGE);rival=make_opponent("solution92",f"player_{1-team}")
                rec=Recorder(env,team,actor)
                raw=play_game(rec,actor,rival,seed,side,False)
                require_no_agent_errors(actor,rival)
                require(raw["steps"]==len(rec.public)==len(rec.policy)==len(rec.referee)==303,"Incomplete trajectory")
                if group=="archiv":
                    h=history[seed,team]
                    require(rec.matches==h["matches"] and rec.digest.hexdigest()==h["action_hash"],"Historical action or score divergence")
                write_once(f,dict(seed=seed,team=team,source=binding,group=group,sensor=rec.sensor,
                                  action_hash=rec.digest.hexdigest(),matches=rec.matches,win=raw["game_win"],
                                  agent_errors=[0,0],public=rec.public,policy=rec.policy,referee=rec.referee))
    finally:
        env.close()
    require(manifest()==source,"Frozen collection sources changed")
    print(group,worker,"finished",flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("group",choices=("archiv","frisch"))
    p.add_argument("worker",type=int)
    a=p.parse_args()
    run(a.group,a.worker)
