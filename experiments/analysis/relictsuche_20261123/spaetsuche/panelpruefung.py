"""Verify optional whole-game panel directly from the raw compressed archive."""
import gzip
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent


def check():
    out=HERE/"panel"
    stated=json.loads((out/"ergebnis.json").read_text())
    cards=json.loads((HERE/"karten.json").read_text())["panel"]
    with gzip.open(out/"partien.jsonl.gz","rt") as f:
        rows=[json.loads(line) for line in f]
    assert len(rows)==420 and len(cards)==60
    games={};controls=0
    for r in rows:
        entries=r.get("views",[r])
        if "views" in r:
            controls+=1
            assert len(entries)==2 and entries[0]["action_hash"]==entries[1]["action_hash"] and entries[0]["win"]+entries[1]["win"]==1
        for x in entries:
            k=x["seed"],x["team"],x["id"],x["opponent"]
            assert k not in games
            games[k]=x
            assert x["caught_errors"]==[0,0] and x["steps"]==303 and x["sensor"]==1
            assert x["wins"]==sum(m["win"] for m in x["matches"]) and int(x["wins"]>1)==x["win"]
            assert len({e[1] for e in x["events"]})<=1 and all(55<=e[0]<x["sight"] and e[0]<=x["credit"] for e in x["events"])
    assert controls==60 and len(games)==480
    draws=np.random.Generator(np.random.PCG64(231123)).choice(60,(20000,60),replace=True)
    changes={};all_values=[];direct=[];inactive=0
    def vector(r):
        return [-r["sight"],-r["credit"],r["after_70"][0]-r["after_70"][1],r["matches"][0]["win"],r["win"]]
    def check_stats(values,stats):
        bounds=np.percentile(np.take(values,draws).mean(axis=1),[2.5,97.5])
        assert np.allclose([np.mean(values),*bounds],[stats["mean"],*stats["ci95"]],atol=1e-12,rtol=0)
    for o,n in (("solution92","reference"),("v16","control")):
        maps=[];active=set()
        for s in cards:
            seat=[]
            for t in (0,1):
                a,b=games[s,t,"late",o],games[s,t,n,o]
                if a["events"]:
                    active.add(s)
                else:
                    assert a["action_hash"]==b["action_hash"] and vector(a)==vector(b)
                    inactive+=1
                seat.append(np.subtract(vector(a),vector(b)))
            maps.append(np.mean(seat,axis=0))
            if o=="v16":
                direct.append(sum(games[s,t,"late",o]["win"] for t in (0,1))/2)
        m=np.asarray(maps)
        for i,f in enumerate(("sight","credit","margin70","m1","whole")):
            check_stats(m[:,i],stated["groups"][o]["paired"][f])
        assert sorted(active)==stated["groups"][o]["active_maps"]
        changes[o]=active
        all_values.append(m)
    pooled=np.mean(all_values,axis=0)
    for i,f in enumerate(("sight","credit","margin70","m1","whole")):
        check_stats(pooled[:,i],stated["pooled"][f])
    check_stats(direct,stated["direct_actual"])
    assert inactive==stated["inactive_exact"]
    lo=np.percentile(np.take(pooled[:,0],draws).mean(1),2.5)
    passed=(len(changes["solution92"]|changes["v16"])>=8 and min(map(len,changes.values()))>=4 and
            lo>0 and pooled[:,1].mean()>=0 and pooled[:,3].mean()>=0)
    assert bool(passed)==stated["passed"]
    by_seat={}
    for o,n in (("solution92","reference"),("v16","control")):
        sides={}
        for t in (0,1):
            references=[games[s,t,n,o] for s in cards]
            actors=[games[s,t,"late",o] for s in cards]
            sides[str(t)]={
                "baseline_whole_wins":sum(r["win"] for r in references),
                "late_whole_wins":sum(r["win"] for r in actors),
                "baseline_match_wins":[sum(r["matches"][i]["win"] for r in references) for i in range(3)],
                "late_match_wins":[sum(r["matches"][i]["win"] for r in actors) for i in range(3)],
                "changed_seats":sum(bool(r["events"]) for r in actors),
                "whole_gains":sum(a["win"]>b["win"] for a,b in zip(actors,references)),
                "whole_losses":sum(a["win"]<b["win"] for a,b in zip(actors,references)),
            }
        by_seat[o]=sides
    return {"real_games":420,"by_seat":by_seat,"independent_maps":60,"actual_selfplay_games":controls,"complete_perspectives":len(games),
            "inactive_full_traces_identical":inactive,"intervals_recalculated":16,"gate_reproduced":bool(passed)}


if __name__=="__main__":
    print(json.dumps(check(),indent=2))
