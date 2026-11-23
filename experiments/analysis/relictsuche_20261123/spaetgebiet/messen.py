"""Measure public scoring bounds against actual scoring cells in two late matches."""
import argparse
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys

import jax
import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
sys.path.insert(0,str(STUDY.parent/"v16_finalwoche_20261122"))
from feldverlauf import Record
from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import create
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from scripts.experiment import limit_threads
from scripts.common import make_opponent, play_game
from scripts.par_eval import require_no_agent_errors
from signalgrenze import bounds


def points(mask,mirror):
    return mask[::-1,::-1].T if mirror else mask


class Observe(Record):
    def __init__(self, env, actor, team):
        super().__init__(env)
        self.actor,self.team=actor,team
        self.rows=[]
        self.lastscore=None

    def reset(self,**kw):
        x=super().reset(**kw)
        self.view=x[0][f"player_{self.team}"]
        if x[1]["params"]["unit_sensor_range"]!=1:
            raise ValueError("Invalid course range")
        return x

    def step(self,actions):
        t=len(self.frames)
        mi,turn=divmod(t,101)
        if int(self.view["match_steps"])!=turn:
            raise ValueError("Discontinuous course trace")
        score=np.asarray(self.view["team_points"],int)
        b=self.actor.base._imitation.belief
        if mi>=1:
            zone=points(b.relic_zone,b.mirrored)
            candidate=points(b.point_tiles|b.candidate,b.mirrored)&zone
            known=np.asarray(b.relic_coords(),int).reshape(-1,2)
            if b.mirrored and len(known):
                known=23-known[:,::-1]
            known={tuple(map(int,p)) for p in known}
            state=self.env.state
            active={tuple(map(int,p)) for p in np.asarray(state.relic_nodes)[np.asarray(state.relic_nodes_mask,bool)]}
            missing=active-known
            if turn:
                prev=self.frames[-1]
                gains=score-self.lastscore
                if list(gains)!=[len(f) for f in prev]:
                    raise ValueError("Public score change differs from actual unique tiles")
                g=[int(gains[self.team]),int(gains[1-self.team])]
                outside=[sum(not zone[tile] for tile in prev[s]) for s in (self.team,1-self.team)]
                limits={n:list(bounds(self.view,self.team,m)) for n,m in (("region",zone),("possible",candidate))}
                joint=int(candidate.sum()+candidate[0,0]+candidate[-1,-1])
                alarms={n:bool(any(v>c for v,c in zip(g,cap,strict=True))) for n,cap in limits.items()}
                alarms["old_joint"]=bool(mi==1 and turn>=50 and len(known)==2 and b.candidate.sum()==0 and sum(g)>joint)
                self.rows.append(dict(match=mi+1,turn=turn,known=[list(p) for p in sorted(known)],
                                    missing=[list(p) for p in sorted(missing)],gains=g,outside=outside,
                                    limits=limits,alarms=alarms))
        self.lastscore=score.copy()
        x=super().step(actions)
        self.view=x[0][f"player_{self.team}"]
        return x


def run():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    p.add_argument("lane",type=int)
    p.add_argument("stride",type=int)
    a=p.parse_args()
    limit_threads()
    s=np.arange(161800000,161801000,dtype=np.int32)
    chosen=s[np.asarray(jax.jit(jax.vmap(sensor))(s))==1][:40].tolist()
    historic=[161200052,161200057,161200063,161200078]
    jobs=[(s,i,group) for group,seeds in (("new",chosen),("archive",historic)) for s in seeds for i in range(2)]
    if len(jobs)!=88 or os.getenv("PYTHONHASHSEED")!="0":
        raise ValueError("Incorrect map or randomness setup")
    with gzip.open(STUDY/"vergleich/discovery/partien.jsonl.gz","rt") as f:
        archived={(q["seed"],q["team"]):q for line in f if (q:=json.loads(line))["id"]=="ziel" and q["opponent"]=="solution92"}
    a.folder.mkdir(parents=True,exist_ok=True)
    files={p.name:sha256(p.read_bytes()).hexdigest() for p in (HERE/"signalgrenze.py",HERE/"messen.py",HERE/"PLAN.md",STUDY/"zielschaetzer/kandidat.py",STUDY/"zielschaetzer/ort.json")}
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed,team,group in jobs[a.lane::a.stride]:
            target=a.folder/f"{seed}-{team}.json.gz"
            if target.exists():
                with gzip.open(target,"rt") as f: assert json.load(f)["sources"]==files
                continue
            side=f"player_{team}"
            torch.manual_seed(seed)
            np.random.seed(seed)
            random.seed(seed)
            actor=create(side)
            rival=make_opponent("solution92",f"player_{1-team}")
            view=Observe(env,actor,team)
            result=play_game(view,actor,rival,seed,side,False)
            require_no_agent_errors(actor.base,rival)
            if len(view.rows)!=200 or len(view.frames)!=303:
                raise ValueError("Incorrect game length")
            wins=[]
            for start in (0,101,202):
                fs=view.frames[start:start+101]
                wins.append([sum(len(z[t]) for z in fs) for t in (team,1-team)])
            if group=="archive" and wins!=[m["points"] for m in archived[seed,team]["matches"]]:
                raise ValueError("Archive match not reproduced")
            v=dict(seed=seed,team=team,group=group,sources=files,matches=wins,game_win=result["game_win"],frames=view.rows)
            tmp=target.with_suffix(".tmp")
            tmp.write_bytes(gzip.compress(json.dumps(v,separators=(",",":")).encode(),mtime=0))
            tmp.replace(target)
            print(seed,team,flush=True)
    finally:
        env.close()


if __name__=="__main__":
    run()
