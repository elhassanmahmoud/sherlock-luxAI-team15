"""Score paired whole games; bootstrap entire maps with both seats together."""
import argparse
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path
from statistics import median

import numpy as np
from spielen import binding, jobs, valid


def read(path):
    if path.is_dir():
        for f in sorted(path.glob("*.json")):
            yield json.loads(f.read_text())
    else:
        with gzip.open(path,"rt") as stream:
            for line in stream:
                yield json.loads(line)


def evaluate(phase, raw):
    keys=set(jobs(phase))
    source=sha256(json.dumps(binding(phase),sort_keys=True).encode()).hexdigest()
    data={}
    for r in read(raw):
        k=tuple(r[x] for x in ("seed","team","opponent","arm"))
        valid(r,k,source)
        if k in data or k not in keys:
            raise ValueError(f"Repeated or unexpected seat {k}")
        data[k]=r
    if set(data)!=keys:
        raise ValueError("Incomplete game panel")
    seeds=sorted({k[0] for k in keys})
    draws=np.random.default_rng(231123).integers(0,len(seeds),size=(20000,len(seeds)))
    result={}
    comparisons={}
    protected=0
    for opp in ("solution92","kaggle3","v16"):
        result[opp]={}
        for arm in (("staffel",) if opp=="v16" else ("original","staffel")):
            rows=[r for k,r in data.items() if k[2:]==(opp,arm)]
            result[opp][arm]=dict(games=len(rows),wins=sum(r["game_win"] for r in rows),
                    matches=sum(r["our_wins"] for r in rows),p0_wins=sum(r["game_win"] for r in rows if r["team"]==0),
                    p1_wins=sum(r["game_win"] for r in rows if r["team"]==1),
                    changed_games=sum(r["divergent_steps"]>0 for r in rows),
                    diff_unit_commands=sum(r["divergent_units"] for r in rows),median_secs=median(r["secs"] for r in rows))
        if opp=="v16":
            continue
        flips=Counter()
        wins=[]; matches=[]; shares=[]
        def share(r):
            total=r["our_points"]+r["opp_points"]
            return r["our_points"]/total if total else 0.5
        for s in seeds:
            w=[];m=[];p=[]
            for t in (0,1):
                candidate,original=(data[s,t,opp,a] for a in ("staffel","original"))
                if candidate["sensor"]!=original["sensor"]:
                    raise ValueError("Paired sensor mismatch")
                if candidate["sensor"]>2 or candidate["divergent_steps"]==0:
                    for field in ("our_points","opp_points","our_wins","opp_wins","game_win"):
                        if candidate[field]!=original[field]:
                            raise ValueError(f"Inactive candidate differed at {s} {t} {opp}")
                    protected+=1
                flips[f'{candidate["game_win"]}:{original["game_win"]}']+=1
                w.append(candidate["game_win"]-original["game_win"])
                m.append(candidate["our_wins"]-original["our_wins"])
                p.append(share(candidate)-share(original))
            wins.append(sum(w)/2);matches.append(sum(m)/2);shares.append(sum(p)/2)
        def describe(xs):
            x=np.asarray(xs)
            return {"difference":float(x.mean()), "ci95":np.quantile(x[draws].mean(axis=1),[.025,.975],method="linear").tolist()}
        comparisons[opp]=dict(whole_game_seats=dict(flips),wins=describe(wins),matches=describe(matches),point_share=describe(shares))
    g={opp:result[opp]["staffel"]["wins"]-result[opp]["original"]["wins"] for opp in ("solution92","kaggle3")}
    gates={"more_solution_wins":g["solution92"]>0,"at_least_as_many_kaggle_wins":g["kaggle3"]>=0,
           "direct_at_least_40":result["v16"]["staffel"]["wins"]>=40}
    if phase=="bestaetigung":
        gates["positive_solution_lower"]=comparisons["solution92"]["wins"]["ci95"][0]>0
    return dict(phase=phase,games=len(data),map_count=len(seeds),results=result,paired=comparisons,
                identical_inactive_external_pairs=protected,gates=gates,passed=all(gates.values()))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("phase",choices=("auswahl","bestaetigung"));p.add_argument("raw",type=Path)
    p.add_argument("--archive",type=Path)
    args=p.parse_args()
    result=evaluate(args.phase,args.raw)
    if args.archive:
        payload="".join(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n" for r in read(args.raw))
        compressed=gzip.compress(payload.encode(),mtime=0)
        if args.archive.exists() and args.archive.read_bytes()!=compressed:
            raise ValueError("Existing archive differs")
        args.archive.write_bytes(compressed)
        if evaluate(args.phase,args.archive)!=result:
            raise ValueError("Archive readback differs")
    print(json.dumps(result,indent=2))
