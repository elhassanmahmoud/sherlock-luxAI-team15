"""Deduplicate original V16 games and isolate when an improved first match alone could rescue a full loss."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
SOURCES=("vergleich/discovery","standsuche/duelle/discovery","punktsicht","flottenblick/ganzspiel",
         "flottenblick/bestaetigung","spaetsuche/panel","feldprobe")


def main():
    seats={}
    sources={}
    for group in SOURCES:
        p=STUDY/group/("ganze_partien.jsonl.gz" if group=="feldprobe" else "partien.jsonl.gz")
        count=0
        with gzip.open(p,"rt") as f:
            for raw in map(json.loads,f):
                for r in raw.get("views",[raw]):
                    if r.get("id",r.get("arm"))!="reference" or r["opponent"]!="solution92":
                        continue
                    s,t=r["seed"],r["team"]
                    assert (s,t) not in seats and r["sensor"]==1
                    wins=tuple(m["win"] for m in r["matches"])
                    assert len(wins)==3 and int(sum(wins)>=2)==r["win"]
                    points=[m["points"] for m in r["matches"]]
                    assert all(w==(a>b) for w,(a,b) in zip(wins,points) if a!=b)
                    seats[s,t]=dict(seed=s,side=t,source=group,win=r["win"],matches=wins,points=points,sight=r["sight"],credit=r["credit"])
                    count+=1
        sources[group]=dict(seats=count,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    seeds=sorted({s for s,_ in seats})
    assert all((s,0) in seats and (s,1) in seats for s in seeds)
    rows=[seats[s,t] for s in seeds for t in (0,1)]
    def box(values):
        return dict(n=len(values),median=float(np.median(values)),quartiles=np.percentile(values,[25,75]).tolist()) if values else None
    def stats(rr):
        losses=[r for r in rr if not r["win"]]
        return dict(seats=len(rr),wins=sum(r["win"] for r in rr),losses=len(losses),loss_maps=len({r["seed"] for r in losses}),
            first_match_won_among_losses=sum(r["matches"][0] for r in losses),
            first_match_decisive_if_later_fixed=sum(not r["matches"][0] and sum(r["matches"][1:])==1 for r in losses),
            lost_all_matches=sum(sum(r["matches"])==0 for r in losses),
            first_sight_losses=box([r["sight"] for r in losses]),first_sight_wins=box([r["sight"] for r in rr if r["win"]]),
            first_credit_losses=box([r["credit"] for r in losses]),first_credit_wins=box([r["credit"] for r in rr if r["win"]]),
            patterns=dict(Counter("".join(map(str,r["matches"])) for r in rr)))
    by_card=np.array([[sum(1-seats[s,t]["win"] for t in (0,1))/2,
        sum((not seats[s,t]["win"]) and (not seats[s,t]["matches"][0]) and sum(seats[s,t]["matches"][1:])==1 for t in (0,1))/2] for s in seeds])
    draw=np.random.default_rng(231123).integers(0,len(seeds),(20000,len(seeds)))
    def rate(v):
        return dict(mean=float(v.mean()),ci95=np.percentile(v[draw].mean(1),[2.5,97.5]).tolist())
    result=dict(cards=len(seeds),sources=sources,overall=stats(rows),by_start_side={str(t):stats([r for r in rows if r["side"]==t]) for t in (0,1)},
        by_first_sight={f"{lo}-{hi}":stats([r for r in rows if lo<=r["sight"]<=hi]) for lo,hi in ((0,30),(31,50),(51,70),(71,101))},
        loss_rate=rate(by_card[:,0]),ceiling_first_match_only=rate(by_card[:,1]))
    (HERE/"ergebnis.json").write_text(json.dumps(result,indent=2)+"\n")
    data="\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n"
    (HERE/"kontrollspiele.jsonl.gz").write_bytes(gzip.compress(data.encode(),mtime=0))
    print(result["cards"],result["overall"],result["ceiling_first_match_only"])


if __name__=="__main__":
    main()
