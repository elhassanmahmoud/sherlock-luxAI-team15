"""Play the V16 opening twice and verify true, opponent-paired whole-game continuations."""
import argparse
from datetime import datetime
import hashlib
import inspect
import json
from pathlib import Path
import random

import numpy as np
import torch

from experiments.analysis.relictsuche_20261123.folgewahl.politik import HERE,Switch,feedback
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,Monitor,PACKAGE,common_source,sha,stamp,write_once
from scripts.common import make_opponent,play_game
from scripts.r3_package import r3_package_agent
from scripts.par_eval import require_no_agent_errors
from scripts.experiment import limit_threads

ROOT=HERE.parents[3]
OLD=ROOT/"experiments/releases/20261116_r3_finale/agent.zip"


def frozen():
    files=[HERE/n for n in ("PLAN.md","politik.py","sammeln.py")]
    files.append(HERE.parents[1]/"v16_finalwoche_20261122/fruehuebergabe/staffel.py")
    return stamp(dict(official=common_source(),r3=sha(OLD),sync=hashlib.sha256(inspect.getsource(feedback).encode()).hexdigest(),
                      files={str(f.relative_to(ROOT)):sha(f) for f in files}))


class Observe(Monitor):
    def __init__(self,env,team):
        super().__init__(env,team,"discovery")
        self.actual=[]
        self.prefix=None
    def step(self,cmd):
        self.actual.append(np.array(cmd[self.side],copy=True))
        result=super().step(cmd)
        if self.turn==101:self.prefix=self.digest.hexdigest()
        return result


def run(env,seed,team,opp,forced):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    side=f"player_{team}";other=f"player_{1-team}"
    a=Switch(side,forced)
    b=r3_package_agent(other,PACKAGE) if opp=="v16" else make_opponent(opp,other)
    obs=Observe(env,team)
    result=play_game(obs,a,b,seed,side,False)
    require_no_agent_errors(a.base,b)
    if a.r3 is not None:require_no_agent_errors(a.r3,b)
    assert obs.turn==303 and result["game_win"]==int(sum(m["win"] for m in obs.matches)>=2)
    return dict(matches=obs.matches,win=result["game_win"],prefix=obs.prefix,hash=obs.digest.hexdigest(),
                features=a.features,chosen=a.chosen,sight=obs.first_sight,credit=obs.first_credit),np.stack(obs.actual)


def one(env,receipt,ident):
    meta=json.loads(receipt.read_text())
    s,t,opp=meta["seed"],meta["team"],meta["opponent"]
    base,cmd=run(env,s,t,opp,False)
    pub=receipt.parent/meta["public"]
    assert sha(pub)==meta["public_sha"]
    with np.load(pub) as inputs:
        assert np.array_equal(cmd,inputs["commands"])
    adjusted=[pair if t==0 else pair[::-1] for pair in meta["matches"]]
    assert base["win"]==meta["win"] and [m["points"] for m in base["matches"]]==adjusted
    eligible=bool(base["matches"][0]["win"])
    if eligible:
        after,commands=run(env,s,t,opp,True)
        assert after["chosen"] and after["features"]==base["features"] and after["prefix"]==base["prefix"]
        assert np.array_equal(cmd[:101],commands[:101]) and after["matches"][0]==base["matches"][0]
    else:
        after=base
    return dict(source=ident,seed=s,team=t,opponent=opp,eligible=eligible,experiments=1+int(eligible),base=base,switch=after)


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive",type=Path);p.add_argument("folder",type=Path);p.add_argument("stage",choices=("train","valid"))
    p.add_argument("lane",type=int);p.add_argument("stride",type=int)
    a=p.parse_args()
    if a.stage=="valid":assert json.loads((HERE/"train.json").read_text())["passed"]
    limit_threads()
    ident=frozen()
    receipts=sorted((a.archive/a.stage).glob("*.json"))
    assert len(receipts)==(160 if a.stage=="train" else 48) and 0<=a.lane<a.stride
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for receipt in receipts[a.lane::a.stride]:
            if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
            dest=a.folder/a.stage/receipt.name
            if dest.exists():
                assert json.loads(dest.read_text())["source"]==ident
                continue
            write_once(dest,one(env,receipt,ident))
    finally:env.close()
    assert frozen()==ident


if __name__=="__main__":main()
