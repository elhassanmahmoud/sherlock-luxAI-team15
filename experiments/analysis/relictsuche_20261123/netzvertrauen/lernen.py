"""Learn whether to allow the trained scout's entire route using actual paired full-game outcomes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.netzvertrauen.erheben import HERE, frozen
from experiments.analysis.relictsuche_20261123.netzvertrauen.stimmen import BASE,NAMES


def utility(c,b):
    def share(r):
        return np.mean([(p["points"][0]+1)/(sum(p["points"])+2) for p in r["matches"]])
    return float(8*(c["win"]-b["win"])+2*sum(m["win"]-n["win"] for m,n in zip(c["matches"],b["matches"],strict=True))+
                 .08*np.clip(b["sight"]-c["sight"],-30,30)+.04*np.clip(b["credit"]-c["credit"],-30,30)+share(c)-share(b))


def fit(rows,columns):
    active=[r for r in rows if r["features"] is not None]
    X=np.array([r["features"][:columns] for r in active])
    y=np.array([utility(r["candidate"],r["base"]) for r in active])
    center=X.mean(0)
    scale=np.maximum(.05,X.std(0))
    x=(X-center)/scale
    bias=y.mean()
    beta=np.linalg.solve(x.T@x+160*np.eye(columns),x.T@(y-bias))
    return dict(center=center.tolist(),scale=scale.tolist(),bias=float(bias),beta=beta.tolist(),active=len(y))


def predict(values,model):
    cols=len(model["beta"])
    return float(((np.asarray(values[:cols])-model["center"])/model["scale"])@model["beta"]+model["bias"])


def summarize(rows,gate):
    seeds=sorted({r["seed"] for r in rows})
    ri={(r["seed"],r["team"],r["opponent"]):r for r in rows}
    rng=np.random.default_rng(231123)
    ix=rng.integers(0,len(seeds),(20000,len(seeds)))
    def estimate(x):
        x=np.asarray(x,float)
        return dict(mean=float(x.mean()),ci95=np.percentile(x[ix].mean(1),[2.5,97.5]).tolist())
    groups={}
    combined=[]
    altered=set()
    for opp in ("solution92","v16"):
        values=[];used=0
        for seed in seeds:
            pairs=[]
            for team in (0,1):
                r=ri[seed,team,opp]
                b=r["base"]
                active=r["features"] is not None and gate(r)
                c=r["candidate"] if active else b
                if active:
                    used+=1
                    altered.add(seed)
                pairs.append([utility(c,b),b["sight"]-c["sight"],b["credit"]-c["credit"],c["win"],b["win"]])
            values.append(np.mean(pairs,axis=0))
        values=np.array(values)
        combined.append(values)
        groups[opp]=dict(allowed=used,wins=int(2*values[:,3].sum()),base_wins=int(2*values[:,4].sum()),
                         sight=estimate(values[:,1]),utility=estimate(values[:,0]),credit=estimate(values[:,2]),
                         direct_or_external=estimate(values[:,3]),win_change=estimate(values[:,3]-values[:,4]))
    both=np.mean(combined,axis=0)
    return dict(groups=groups,cards=len(seeds),altered=len(altered),sight=estimate(both[:,1]),utility=estimate(both[:,0]))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    a=p.parse_args()
    records=[json.loads(f.read_text()) for f in sorted((a.folder/"karten").glob("*.json"))]
    ident=frozen()
    assert len(records)==len({d["seed"] for d in records})==160 and all(d["source"]==ident for d in records)
    rows=[r for d in records for r in d["comparisons"]]
    assert len(rows)==640
    seeds=sorted(d["seed"] for d in records)
    folds={s:i%4 for i,s in enumerate(seeds)}
    oof={}
    all_stats={}
    for name,columns in (("public",len(BASE)),("network",len(NAMES))):
        predictions={}
        for k in range(4):
            head=fit([r for r in rows if folds[r["seed"]]!=k],columns)
            for r in rows:
                if folds[r["seed"]]==k and r["features"] is not None:
                    predictions[r["seed"],r["team"],r["opponent"]]=predict(r["features"],head)
        all_stats[name]=summarize(rows,lambda r: predictions[r["seed"],r["team"],r["opponent"]]>=.20)
        oof[name]=predictions
    all_stats["always"]=summarize(rows,lambda r:True)
    full=all_stats["network"]
    gates=dict(benefit=full["utility"]["mean"]>max(all_stats["always"]["utility"]["mean"],all_stats["public"]["utility"]["mean"]),
               changed=full["altered"]>=24,sight=full["sight"]["mean"]>0,
               wins=all(g["wins"]>=g["base_wins"] for g in full["groups"].values()))
    model=dict(features=NAMES,source=ident,threshold=.20,ridge=160,model=fit(rows,len(NAMES)))
    (HERE/"modell.json").write_text(json.dumps(model,indent=2)+"\n")
    output=dict(results=all_stats,gates={k:bool(v) for k,v in gates.items()},passed=bool(all(gates.values())),
                model_sha=hashlib.sha256((HERE/"modell.json").read_bytes()).hexdigest())
    (HERE/"ergebnis.json").write_text(json.dumps(output,indent=2)+"\n")
    for r in rows:
        key=r["seed"],r["team"],r["opponent"]
        r["oof"]={n:vs.get(key) for n,vs in oof.items()}
    data="\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n"
    (HERE/"lernspiele.jsonl.gz").write_bytes(gzip.compress(data.encode(),mtime=0))
    print(json.dumps(output,indent=2))


if __name__=="__main__":
    main()
