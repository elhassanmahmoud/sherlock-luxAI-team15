"""Reproduce each held-out first choice and both team prefixes in real untouched course processes."""
import argparse
import gzip
import json
from pathlib import Path
import random

import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.feldprobe.kandidat import create,PACKAGE
from experiments.analysis.relictsuche_20261123.feldprobe.signalmodell import HERE
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.r3_package import r3_package_agent
from scripts.par_eval import require_no_agent_errors
from scripts.scoring import point_tile_map


class Checked(Exception):
    pass


class Tape:
    def __init__(self,env,record,actor,side,target):
        self.env,self.record,self.actor,self.side,self.target=env,record,actor,side,target
        self.step_count=0
        self.proof=None

    def reset(self,**kw):
        return self.env.reset(**kw)

    def step(self,commands):
        t=self.step_count
        output=commands[self.side]
        ref=self.record[t]
        if self.actor.event:
            e=self.actor.event
            uid=e["u"]
            truth=point_tile_map(self.env.state)
            assert self.target is not None and self.target["turn"]==t
            assert self.target["key"]==[uid,e["d"],*e["xy"],*e["ref"]]
            assert self.target["actual"]==[int(truth[tuple(e[k])]) for k in ("xy","ref")]
            diff=np.flatnonzero(np.any(output!=ref,1))
            assert diff.tolist()==[uid]
            self.proof=e
            raise Checked
        assert np.array_equal(ref,output)
        self.step_count+=1
        return self.env.step(commands)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive",type=Path)
    a=p.parse_args()
    limit_threads()
    with gzip.open(HERE/"valid_karten.jsonl.gz","rt") as f:
        cards=list(map(json.loads,f))
    picked=[r for r in cards if r["full"]["first"] is not None]
    for team in (0,1):
        for opp in ("solution92","v16"):
            picked.append(next(r for r in cards if r["full"]["first"] is None and r["team"]==team and r["opponent"]==opp))
    assert len(picked)==13
    env=LuxAIS3GymEnv(numpy_output=True)
    checked=[]
    try:
        for r in picked:
            seed,team,opp=r["seed"],r["team"],r["opponent"]
            side=f"player_{team}"
            other=f"player_{1-team}"
            random.seed(seed)
            torch.manual_seed(seed)
            np.random.seed(seed)
            actor=create(side)
            rival=r3_package_agent(other,PACKAGE) if opp=="v16" else make_opponent("solution92",other)
            with np.load(a.archive/"valid"/f"{seed}-{team}.npz",allow_pickle=False) as af:
                ref=af["commands"]
            check=Tape(env,ref,actor,side,r["full"]["first"])
            try:
                play_game(check,actor,rival,seed,side,False)
            except Checked:
                pass
            require_no_agent_errors(actor.base,rival)
            assert (r["full"]["first"] is None and check.step_count==303) or check.proof is not None
            checked.append(dict(seed=seed,team=team,opponent=opp,same_turns=check.step_count,choice=check.proof))
    finally:
        env.close()
    (HERE/"technik.json").write_text(json.dumps(checked,indent=2)+"\n")


if __name__=="__main__":
    main()
