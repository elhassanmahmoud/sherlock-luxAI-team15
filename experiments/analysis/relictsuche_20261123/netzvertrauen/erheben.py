"""Attach original network votes to observed route counterfactuals; play each missing V16 self-game once."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path

import numpy as np
import torch
from experiments.analysis.relictsuche_20261123.flottenblick.kandidat import create as fleet, PACKAGE
from experiments.analysis.relictsuche_20261123.netzvertrauen.stimmen import Scores
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor, CUTOFF, common_source, sha, stamp, write_once
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent

HERE=Path(__file__).resolve().parent
SOURCES=[HERE.parent/"flottenblick"/p/"partien.jsonl.gz" for p in ("ganzspiel","bestaetigung")]


def dataset():
    idx={}
    for f in SOURCES:
        for r in map(json.loads,gzip.open(f,"rt")):
            k=(r["seed"],r["team"],r["id"],r["opponent"])
            assert k not in idx
            idx[k]=r
    assert len(idx)==960
    return idx


def frozen():
    inputs=[HERE/"PLAN.md",HERE/"stimmen.py",HERE/"erheben.py",*SOURCES]
    inputs += [HERE.parent/"flottenblick"/n for n in ("kandidat.py","flotte.py","flottengewichte.npz","modell.json","vorhersage.py")]
    return stamp(dict(base=common_source(),files={str(p.relative_to(HERE.parent)):sha(p) for p in inputs}))


def view(m):
    return dict(matches=m.matches,sight=m.first_sight,credit=m.first_credit,win=int(sum(x["win"] for x in m.matches)>=2),
                action_hash=m.digest.hexdigest())


def slim(row):
    return {k:row[k] for k in ("matches","sight","credit","win","action_hash")}


class EndPrefix(Exception):
    pass


class Trigger:
    def __init__(self,actor,row,short=False):
        self.actor=actor
        self.inner=actor.base if short else actor
        self.scores=Scores(self.inner)
        self.event=row["events"][0] if row["events"] else None
        self.short=short
        self.x=None
        if short:
            raw=self.inner.act
            def base(*args,**kw):
                self.org=raw(*args,**kw)
                return self.org
            self.inner.act=base

    def __getattr__(self,k):
        return getattr(self.actor,k)

    def act(self,step,obs):
        cmd=self.actor.act(step,obs)
        if self.event:
            t,u,old,new=self.event
            if self.short and step<t:
                assert self.actor.changes==0
            if step==t:
                if self.short:
                    assert self.actor.changes==1 and self.org[u,0]==old and cmd[u,0]==new
                else:
                    assert cmd[u,0]==old
                self.x=self.scores.values(t,old,new,u,obs)
                if self.short:
                    raise EndPrefix
        return cmd


def one(env,seed,index,identity):
    historical={(s,o):index[seed,s,"flotte",o] for o in ("solution92","v16") for s in (0,1)}
    seats=[Trigger(r3_package_agent(f"player_{s}",PACKAGE),historical[s,"v16"]) for s in (0,1)]
    left=Monitor(env,0,"discovery")
    right=Monitor(left,1,"discovery")
    result=play_game(right,seats[0],seats[1],seed,"player_0",False)
    assert result["steps"]==left.turn==right.turn==303 and left.digest.hexdigest()==right.digest.hexdigest()
    require_no_agent_errors(seats[0].inner,seats[1].inner)
    comparisons=[]
    for s in (0,1):
        side=f"player_{s}"
        for opp in ("solution92","v16"):
            ref=slim(index[seed,s,"reference",opp]) if opp=="solution92" else view((left,right)[s])
            cand=historical[s,opp]
            event=cand["events"][:1]
            if not event:
                assert ref==slim(cand)
                features=None
            elif opp=="v16":
                features=seats[s].x
            else:
                probe=Trigger(fleet(side),cand,True)
                rival=make_opponent("solution92",f"player_{1-s}")
                try:
                    play_game(env,probe,rival,seed,side,False)
                except EndPrefix:
                    pass
                require_no_agent_errors(probe.inner,rival)
                features=probe.x
            assert (features is None)==(not event)
            comparisons.append(dict(seed=seed,team=s,opponent=opp,base=ref,candidate=slim(cand),event=event,features=features))
    return dict(seed=seed,source=identity,comparisons=comparisons)


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("out",type=Path);p.add_argument("lane",type=int);p.add_argument("stride",type=int)
    a=p.parse_args()
    limit_threads()
    ident=frozen()
    archive=dataset()
    seeds=sorted({k[0] for k in archive})
    assert len(seeds)==160
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed in seeds[a.lane::a.stride]:
            if datetime.now(CUTOFF.tzinfo)>=CUTOFF:
                break
            f=a.out/"karten"/f"{seed}.json"
            if f.exists():
                assert json.loads(f.read_text())["source"]==ident
            else:
                torch.manual_seed(seed)
                write_once(f,one(env,seed,archive,ident))
    finally:
        env.close()
    assert frozen()==ident


if __name__=="__main__":
    main()
