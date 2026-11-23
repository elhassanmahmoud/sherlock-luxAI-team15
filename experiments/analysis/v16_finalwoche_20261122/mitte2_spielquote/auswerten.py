"""Evaluate only a complete, source-identified 1,040-game panel."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path

import numpy as np
from spielen import HERE, contract, jobs, signature, validate


def read(path):
    if path.is_dir():
        for p in sorted(path.glob("*.json")):
            yield json.loads(p.read_text())
    else:
        with gzip.open(path,"rt") as f:
            for line in f:yield json.loads(line)


def evaluate(rows):
    expected=set(jobs())
    supplied=json.loads((HERE/"herkunft.json").read_text())
    if supplied!=contract():
        raise ValueError("Recorded and actual run sources differ")
    binding=signature(supplied);data={}
    for r in rows:
        k=tuple(r[f] for f in ("seed","team","opponent","arm"))
        if k in data or k not in expected:raise ValueError(f"Duplicate or unexpected case {k}")
        validate(r,k,binding);data[k]=r
    if len(expected)!=1040 or set(data)!=expected:
        raise ValueError("The fixed panel is incomplete")
    cards=list(range(160384000,160384120));draws=np.random.default_rng(231145).integers(0,120,size=(20000,120))
    totals={};paired={};identical=0
    def stats(x):
        x=np.array(x,float)
        if x.shape!=(120,):raise ValueError("Invalid card vector")
        return dict(mean=float(x.mean()),ci95=np.quantile(x[draws].mean(1),[.025,.975],method="linear").tolist())
    def share(r):
        s=r["our_points"]+r["opp_points"]
        return r["our_points"]/s if s else .5
    for opp in ("solution92","kaggle3","v16"):
        totals[opp]={}
        for arm in (("mitte2",) if opp=="v16" else ("original","mitte2")):
            panel=[r for k,r in data.items() if k[2:]==(opp,arm)]
            totals[opp][arm]=dict(n=len(panel),wins=sum(r["game_win"] for r in panel),
                    matches=sum(r["our_wins"] for r in panel),
                    p0_wins=sum(r["game_win"] for r in panel if r["team"]==0),
                    p1_wins=sum(r["game_win"] for r in panel if r["team"]==1),
                    changed=sum(r["changes"] for r in panel),
                    active_maps=len({r["seed"] for r in panel if r["changes"]}))
        if opp=="v16":continue
        wins=[];matches=[];point_share=[];discordant=[];contingency=Counter();cl=Counter()
        for s in cards:
            w=[];m=[];p=[]
            for t in (0,1):
                c,b=(data[s,t,opp,a] for a in ("mitte2","original"))
                if not c["changes"]:
                    if any(c[k]!=b[k] for k in ("game_win","our_wins","opp_wins","our_points","opp_points")):
                        raise ValueError(f"Inactive policy differed from V16 on {s,t,opp}")
                    identical+=1
                delta=c["game_win"]-b["game_win"]
                if delta:discordant.append(dict(seed=s,team=t,delta=delta,turn=c["event"]["ms"]))
                contingency[f'{c["game_win"]}:{b["game_win"]}']+=1
                w.append(delta)
                m.append(c["our_wins"]-b["our_wins"]);p.append(share(c)-share(b))
            cl[str(sum(w))]+=1
            wins.append(np.mean(w));matches.append(np.mean(m));point_share.append(np.mean(p))
        paired[opp]=dict(wins=stats(wins),matches=stats(matches),point_share=stats(point_share),whole_seats=dict(contingency),
                         map_wins_delta=dict(cl),changed_game_outcomes=discordant)
    gates={"solution_positive_lower":paired["solution92"]["wins"]["ci95"][0]>0,
           "kaggle_at_least_as_many":totals["kaggle3"]["mitte2"]["wins"]>=totals["kaggle3"]["original"]["wins"],
           "direct_at_least_40":totals["v16"]["mitte2"]["wins"]>=40}
    return dict(games=len(data),independent_maps=len(cards),groups=totals,paired=paired,
                identical_inactive_external_pairs=identical,gates=gates,passed=all(gates.values()))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("data",type=Path);p.add_argument("--archive",type=Path)
    args=p.parse_args();rows=list(read(args.data));result=evaluate(rows)
    if args.archive:
        raw="".join(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n" for r in rows).encode()
        zipdata=gzip.compress(raw,mtime=0)
        if args.archive.exists() and args.archive.read_bytes()!=zipdata:
            raise ValueError("Another archive already exists")
        args.archive.write_bytes(zipdata)
        if evaluate(read(args.archive))!=result:raise ValueError("Archive readback differs")
    print(json.dumps(result,indent=2))
