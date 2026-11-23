"""Replay exactly the three changed Solution seats from the frozen scout confirmation."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path
import random
import sys
import numpy as np
import torch

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent
sys.path.insert(0,str(SOURCE))
from sicht import Scout
from erheben import V16, PACKAGE
from scripts.r3_package import r3_package_agent
from scripts.common import play_game,make_opponent
from scripts.par_eval import require_no_agent_errors
from scripts.experiment import limit_threads
from scripts.scoring import match_points_after_step
from luxai_s3.wrappers import LuxAIS3GymEnv


class Observe:
    def __init__(self,actor,base):
        self.actor=actor;self.base=base
        self.relic=None;self.point=None;self.count=0

    def __getattr__(self,k):return getattr(self.actor,k)

    def act(self,step,obs):
        actions=self.actor.act(step,obs);self.count+=1
        when=[step//101+1,int(obs["match_steps"])]
        if self.relic is None and np.asarray(obs["relic_nodes_mask"]).any():self.relic=when
        if self.point is None and self.base._imitation.belief.point_tiles.any():self.point=when
        return actions


class MatchScore:
    def __init__(self,env,t):
        self.env=env;self.t=t;self.side=f"player_{t}"
        self.score=[];self.winners=[];self.first_point=None

    def reset(self,**kwargs):
        obs,info=self.env.reset(**kwargs);self.last=obs[self.side]
        return obs,info

    def step(self,cmd):
        result=self.env.step(cmd);obs=result[0][self.side]
        gain=np.asarray(match_points_after_step(self.last,obs,result[-1]))-self.last["team_points"]
        self.score.append([int(gain[self.t]),int(gain[1-self.t])])
        s=len(self.score)-1
        if self.first_point is None and gain[self.t]>0:self.first_point=[s//101+1,s%101]
        if (s+1)%101==0:
            d=np.asarray(obs["team_wins"])-self.last["team_wins"]
            if sorted(d.tolist())!=[0,1]:raise ValueError("Invalid match winner")
            self.winners.append(int(d[self.t]))
        self.last=obs;return result


def run(lane):
    limit_threads();config=json.loads((SOURCE/"bestaetigung_ergebnis.json").read_text())
    archive=SOURCE/"bestaetigung_partien.jsonl.gz"
    if (sha256(archive.read_bytes()).hexdigest()!=config["evidence_sha256"] or
            sha256(PACKAGE.read_bytes()).hexdigest()!=V16
            or any(sha256((SOURCE/n).read_bytes()).hexdigest()!=config["source"][n] for n in ("offline.json","sicht.py"))):
        raise ValueError("Source identity")
    with gzip.open(archive,"rt") as f:
        rows={(r["seed"],r["team"],r["arm"]):r for s in f if (r:=json.loads(s))["opponent"]=="solution92"}
    swaps=config["external"]["solution92"]["swings"]
    if len(swaps)!=3:raise ValueError("Unexpected seat selection")
    estimate=json.loads((SOURCE/"offline.json").read_text())["estimate"]
    weights=(np.asarray(estimate["w"],dtype=float),float(estimate["bias"]))
    env=LuxAIS3GymEnv(numpy_output=True);report=[]
    try:
        for swing in swaps:
            seed=swing["seed"];team=swing["team"];arm=("original","adviser")[lane]
            side=f"player_{team}"
            random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
            base=r3_package_agent(side,PACKAGE)
            actor=Scout(base,weights) if lane else base
            tracker=Observe(actor,base);monitor=MatchScore(env,team)
            rival=make_opponent("solution92",f"player_{1-team}")
            result=play_game(monitor,tracker,rival,seed,side,False)
            require_no_agent_errors(base,rival)
            old=rows[seed,team,arm]
            key=("our_wins","opp_wins","our_points","opp_points","game_win","steps","point_counting_version")
            scores=np.array(monitor.score,dtype=int).reshape(3,101,2).sum(1)
            if (tracker.count!=303 or int(getattr(actor,"changed",0))!=old["changes"]
                    or any(result[k]!=old[k] for k in key) or sum(monitor.winners)!=result["our_wins"]
                    or scores.sum(0).tolist()!=[result["our_points"],result["opp_points"]]):
                raise ValueError(f"Historical course record differs: {seed} {arm}")
            report.append(dict(seed=seed,side=side,arm=arm,score=scores.tolist(),match_wins=monitor.winners,
                               relic_visible=tracker.relic,known_point=tracker.point,first_scored=monitor.first_point,
                               changes=old["changes"],original_archive_sha=config["evidence_sha256"]))
    finally:
        env.close()
    (HERE/f"verlauf_{lane}.json").write_text(json.dumps(report,indent=2)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("lane",type=int,choices=(0,1));run(p.parse_args().lane)
