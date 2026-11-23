"""Run the qualified whole-game selector against both opponents with one real self-game per map."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path
import random

import numpy as np
import torch

from gruppen import HERE, STUDY, roster, source
from politik import create, utility
from spielen import (CUTOFF, Monitor, PACKAGE, THREADS, play, play_game, require, require_no_agent_errors,
                     r3_package_agent, sha, stamp, validate, write_once)
from scripts.experiment import limit_threads


def fixed_jobs():
    return [(s,t,arm,opp) for s in roster("test") for t,arm,opp in
            [(-1,"self","v16"), *((i,a,o) for i in (0,1) for a,o in
                (("reference","solution92"),("select","solution92"),("select","v16")))]]


def dual(env,seed,identity):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    a,b=(r3_package_agent(f"player_{i}",PACKAGE) for i in (0,1))
    right=Monitor(env,1,"test")
    left=Monitor(right,0,"test")
    score=play_game(left,a,b,seed,"player_0",False)
    require_no_agent_errors(a,b)
    views=[]
    for team,observer in enumerate((left,right)):
        matches=observer.matches
        wins=sum(m["win"] for m in matches)
        key=("test",seed,team,"reference","v16")
        row=dict(zip(("phase","seed","team","id","opponent"),key,strict=True),
            source=identity,sensor=observer.sensor,sight=observer.first_sight,credit=observer.first_credit,
            after_70=observer.after_70,matches=matches,events=[],steps=observer.turn,actions_checked=observer.counts,
            caught_errors=[0,0],point_counting_version=score["point_counting_version"],wins=wins,win=int(wins>=2),
            points=[sum(m["points"][i] for m in matches) for i in range(2)],action_hash=observer.digest.hexdigest())
        validate(row,key,identity)
        views.append(row)
    require(views[0]["action_hash"]==views[1]["action_hash"] and views[0]["wins"]==score["our_wins"]
            and views[1]["wins"]==score["opp_wins"],"Conflicting self-play observers")
    return dict(views=views,source=identity)


def destination(folder,key):
    seed,team,arm,opp=key
    return folder/"whole"/f"{seed}_{team}_{arm}_{opp}.json"


def summarize(rows,cards):
    draws=np.random.default_rng(231123).integers(0,len(cards),size=(20000,len(cards)))
    def metric(x):
        x=np.asarray(x,dtype=float)
        return dict(mean=float(x.mean()),ci95=np.percentile(x[draws].mean(axis=1),[2.5,97.5]).tolist())
    opponents={}
    map_vectors={}
    for opp in ("solution92","v16"):
        vectors=[]
        wins=base_wins=0
        affected=set()
        for seed in cards:
            v=[]
            for team in (0,1):
                ref=rows[seed,team,"reference",opp]
                r=rows[seed,team,"select",opp]
                if not r["events"]:
                    require(r["action_hash"]==ref["action_hash"], "Inactive route changed trajectory")
                else:
                    affected.add(seed)
                wins+=r["win"]
                base_wins+=ref["win"]
                v.append([ref["sight"]-r["sight"],ref["credit"]-r["credit"],utility(r,ref),
                          r["win"]-ref["win"],r["win"],r["matches"][0]["win"]-ref["matches"][0]["win"]])
            vectors.append(np.mean(v,axis=0))
        matrix=np.asarray(vectors)
        map_vectors[opp]=matrix
        opponents[opp]=dict(wins=wins,base_wins=base_wins,changed_cards=len(affected),
            metrics={name:metric(matrix[:,i]) for i,name in enumerate(("sight","credit","value","win_gain","win","m1"))})
    combined=(map_vectors["v16"]+map_vectors["solution92"])/2
    test=dict(solution_no_drop=opponents["solution92"]["wins"]>=opponents["solution92"]["base_wins"],
              direct=opponents["v16"]["wins"]>=len(cards),earlier=combined[:,0].mean()>0,
              value=combined[:,2].mean()>0)
    return dict(cards=len(cards),games=len(cards)*7,opponents=opponents,
                equal_opponent_sight=metric(combined[:,0]),equal_opponent_value=metric(combined[:,2]),
                gates={k:bool(v) for k,v in test.items()},passed=bool(all(test.values())))


def main():
    import os
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    p.add_argument("action",choices=("play","score"))
    p.add_argument("--lane",type=int,default=0)
    p.add_argument("--stride",type=int,default=1)
    args=p.parse_args()
    gate=json.loads((HERE/"pilot.json").read_text())
    require(gate["passed"] and gate["model_hash"]==sha(HERE/"modell.json"),"The frozen candidate did not qualify")
    require(all(os.getenv(k)=="1" for k in THREADS) and os.getenv("PYTHONHASHSEED")=="0","Unpinned worker")
    identity=stamp(dict(parent=source("test"),pilot=sha(HERE/"pilot.json"),runner=sha(Path(__file__))))
    jobs=fixed_jobs()
    require(len(jobs)==448 and len(set(jobs))==len(jobs),"Wrong independent roster")
    write_once(args.folder/"whole-sources.json",dict(source=identity))
    if args.action=="play":
        from luxai_s3.wrappers import LuxAIS3GymEnv
        limit_threads()
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for key in jobs[args.lane::args.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:
                    break
                out=destination(args.folder,key)
                if out.exists():
                    require(json.loads(out.read_text())["source"]==identity,"Mixed panel")
                    continue
                seed,team,arm,opp=key
                row=dual(env,seed,identity) if arm=="self" else play(env,("test",seed,team,arm,opp),identity,create if arm=="select" else None)
                if arm=="select":
                    require(len(row["events"])<=3 and len({e[1] for e in row["events"]})<=1,"Invalid whole-game scout")
                write_once(out,row)
        finally:
            env.close()
        return
    all_rows=[]
    archive={}
    for key in jobs:
        raw=json.loads(destination(args.folder,key).read_text())
        require(raw["source"]==identity,"Wrong game source")
        all_rows.append(raw)
        for row in raw["views"] if key[2]=="self" else [raw]:
            k=(row["seed"],row["team"],row["id"],row["opponent"])
            validate(row,("test",*k),identity)
            require(k not in archive,"Duplicate view")
            archive[k]=row
    result=summarize(archive,sorted({k[0] for k in archive}))
    write_once(HERE/"ganze_spiele.json",result)
    data="\n".join(json.dumps(r,separators=(",",":")) for r in all_rows)+"\n"
    (HERE/"ganze_spiele.jsonl.gz").write_bytes(gzip.compress(data.encode(),mtime=0))


if __name__=="__main__":
    main()
