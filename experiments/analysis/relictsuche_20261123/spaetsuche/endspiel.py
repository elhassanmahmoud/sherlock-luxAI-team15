"""Optional 60-map mixed-opponent panel, including a real dual-perspective self-play control."""
import argparse
from collections import Counter
import json
from pathlib import Path
import random

import numpy as np
import torch

from kandidat import create
from sammeln import HERE, WORK, claim, binding
from auswerten import describe, save_archive
from spielen import CUTOFF, PACKAGE, Monitor, datetime, play as complete, play_game, require, require_no_agent_errors, r3_package_agent, sha, stamp, validate, write_once
from scripts.experiment import limit_threads

PHASE = "spaetpanel"


def keys():
    cards = json.loads((HERE/"karten.json").read_text())["panel"]
    jobs=[]
    for seed in cards:
        jobs.append((seed,0,"control","v16"))
        for team in (0,1):
            jobs.append((seed,team,"reference","solution92"))
            jobs.append((seed,team,"late","solution92"))
            jobs.append((seed,team,"late","v16"))
    return jobs


def contract():
    gate = json.loads((HERE/"test/ergebnis.json").read_text())
    require(gate["passed"] and gate["model_sha256"] == sha(HERE/"modell.json"),"No eligible offline candidate")
    checks = json.loads((HERE/"technik.json").read_text())
    require(checks["passed"] and checks["model_sha256"] == sha(HERE/"modell.json"), "Incomplete actual course controls")
    return {"collection":binding(), "model":sha(HERE/"modell.json"),"gate":sha(HERE/"test/ergebnis.json"),
            "checks":sha(HERE/"technik.json"),"endspiel":sha(Path(__file__))}


def self_game(env, seed, source):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    a,b = (r3_package_agent(f"player_{i}",PACKAGE) for i in (0,1))
    second = Monitor(env,1,PHASE)
    first = Monitor(second,0,PHASE)
    raw = play_game(first,a,b,seed,"player_0",False)
    require_no_agent_errors(a,b)
    views=[]
    for t,m in enumerate((first,second)):
        key=(PHASE,seed,t,"control","v16")
        win=sum(v["win"] for v in m.matches)
        r=dict(zip(("phase","seed","team","id","opponent"),key),source=source,sensor=m.sensor,sight=m.first_sight,credit=m.first_credit,
               after_70=m.after_70,matches=m.matches,events=[],steps=m.turn,actions_checked=m.counts,caught_errors=[0,0],
               point_counting_version=raw["point_counting_version"],wins=win,win=int(win>1),
               points=[raw["our_points"],raw["opp_points"]][::1 if t==0 else -1],action_hash=m.digest.hexdigest())
        validate(r,key,source)
        views.append(r)
    require(views[0]["action_hash"]==views[1]["action_hash"] and views[0]["wins"]==raw["our_wins"] and
            views[1]["wins"]==raw["opp_wins"],"Self-play observers disagree")
    return {"seed":seed,"views":views,"games":1,"source":source}


def dest(key):
    return WORK/"panel"/("_".join(map(str,key))+".json")


def run(worker):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    manifest=contract()
    source=stamp(manifest)
    write_once(WORK/"panel_herkunft.json",manifest)
    jobs=keys()
    offset=worker*53%len(jobs)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for k in jobs[offset:]+jobs[:offset]:
            require(datetime.now(CUTOFF.tzinfo)<CUTOFF,"Deadline reached")
            s,t,n,o=k
            def produce():
                if n=="control":
                    return self_game(env,s,source)
                r=complete(env,(PHASE,s,t,n,o),source,create if n=="late" else None)
                require(len({e[1] for e in r["events"]})<=1 and all(55<=e[0]<r["sight"] and e[0]<=r["credit"] for e in r["events"]), "Wrong late activation")
                return r
            claim(dest(k),produce)
    finally:
        env.close()
    require(contract()==manifest,"Source drift during whole games")


def evaluate():
    jobs=keys()
    require(len(jobs)==420 and len(set(jobs))==420 and all(dest(k).is_file() for k in jobs),"Full 420-game panel is required")
    manifest=contract()
    source=stamp(manifest)
    require(json.loads((WORK/"panel_herkunft.json").read_text())==manifest,"Wrong sources")
    by={};rows=[]
    for k in jobs:
        r=json.loads(dest(k).read_text())
        rows.append(r)
        if k[2]=="control":
            require(r["games"]==1 and r["seed"]==k[0] and r["source"]==source,"Bad real self-play control")
            for t,x in enumerate(r["views"]):
                validate(x,(PHASE,k[0],t,"control","v16"),source)
                by[k[0],t,"control","v16"]=x
        else:
            validate(r,(PHASE,*k),source)
            by[k]=r
    cards=json.loads((HERE/"karten.json").read_text())["panel"]
    draws=np.random.default_rng(231123).integers(0,len(cards),size=(20000,len(cards)))
    deltas={}; direct=[]; active={}
    per={}; inactive=0
    for opp,baseline in (("solution92","reference"),("v16","control")):
        matrix=[];changed=set();totals=Counter();changed_trace=set()
        for s in cards:
            pairs=[]
            for t in (0,1):
                b,r=by[s,t,baseline,opp],by[s,t,"late",opp]
                if not r["events"]:
                    require(r["action_hash"]==b["action_hash"],"Inactive real opponent trajectory diverged")
                    inactive+=1
                else:
                    changed.add(s)
                if b["action_hash"]!=r["action_hash"]:
                    changed_trace.add(s)
                v=[b["sight"]-r["sight"],b["credit"]-r["credit"],(r["after_70"][0]-r["after_70"][1])-(b["after_70"][0]-b["after_70"][1]),
                   r["matches"][0]["win"]-b["matches"][0]["win"],r["win"]-b["win"]]
                pairs.append(v)
                for arm,x in (("baseline",b),("late",r)):
                    totals[f"{arm}_whole"]+=x["win"]
                    totals[f"{arm}_match1"]+=x["matches"][0]["win"]
                    totals[f"{arm}_no_sight"]+=int(x["sight"]==101)
                    totals[f"{arm}_no_credit"]+=int(x["credit"]==101)
                totals["changed_seats"]+=int(bool(r["events"]))
                totals["changed_moves"]+=len(r["events"])
            matrix.append(np.mean(pairs,axis=0))
            if opp=="v16":
                direct.append(np.mean([by[s,t,"late",opp]["win"] for t in (0,1)]))
        deltas[opp]=np.array(matrix)
        active[opp]=changed
        per[opp]=dict(totals=dict(totals),active_maps=sorted(changed),different_full_trajectory_maps=sorted(changed_trace),
                      paired={f:describe(deltas[opp][:,j],draws) for j,f in enumerate(("sight","credit","margin70","m1","whole"))})
    combined=(deltas["solution92"]+deltas["v16"])/2
    pooled={f:describe(combined[:,j],draws) for j,f in enumerate(("sight","credit","margin70","m1","whole"))}
    gates={"eight_active":len(active["v16"]|active["solution92"])>=8,"four_each":min(map(len,active.values()))>=4,
           "positive_sight_lower":pooled["sight"]["ci95"][0]>0,"credit_not_later":pooled["credit"]["mean"]>=0,
           "m1_not_worse":pooled["m1"]["mean"]>=0}
    result=dict(games=420,cards=60,groups=per,pooled=pooled,direct_actual=describe(direct,draws),gates=gates,passed=all(gates.values()),inactive_exact=inactive)
    out=HERE/"panel"
    out.mkdir(exist_ok=True)
    require(save_archive(rows,out/"partien.jsonl.gz")==rows,"Archive readback differs")
    write_once(out/"herkunft.json",manifest)
    write_once(out/"ergebnis.json",result)
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("play","analyze"))
    p.add_argument("--worker",type=int,default=0)
    a=p.parse_args()
    run(a.worker) if a.mode=="play" else evaluate()
