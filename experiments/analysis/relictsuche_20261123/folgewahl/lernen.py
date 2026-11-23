"""Fit the public match-two choice and score its held-out trajectories against both always-fixed alternatives."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.folgewahl.politik import HERE, NAMES
from experiments.analysis.relictsuche_20261123.folgewahl.sammeln import frozen
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,write_once


def utility(a,b):
    def share(r):
        return np.mean([(m["points"][0]+1)/(sum(m["points"])+2) for m in r["matches"][1:]])
    return float(8*(a["win"]-b["win"])+2*sum(m["win"]-n["win"] for m,n in zip(a["matches"][1:],b["matches"][1:],strict=True))
                 +share(a)-share(b))


def fit(rows):
    usable=[r for r in rows if r["eligible"]]
    x=np.array([r["base"]["features"] for r in usable])
    y=np.array([utility(r["switch"],r["base"]) for r in usable])
    center=x.mean(0);scale=np.maximum(x.std(0),.05)
    z=(x-center)/scale
    bias=y.mean()
    beta=np.linalg.solve(z.T@z+80*np.eye(x.shape[1]),z.T@(y-bias))
    return dict(names=NAMES,center=center.tolist(),scale=scale.tolist(),beta=beta.tolist(),bias=float(bias),
                threshold=.35,ridge=80,source=frozen())


def prediction(row,spec):
    z=(np.array(row["base"]["features"])-spec["center"])/spec["scale"]
    return float(z@spec["beta"]+spec["bias"])


def summary(rows,allowed):
    groups={}
    for label in ("solution92","v16","both"):
        selected=[r for r in rows if label=="both" or r["opponent"]==label]
        picked=[r["switch"] if r["eligible"] and allowed(r) else r["base"] for r in selected]
        data=[utility(c,r["base"]) for c,r in zip(picked,selected,strict=True)]
        draw=np.random.default_rng(231123).integers(0,len(data),(20000,len(data)))
        groups[label]=dict(cards=len(data),chosen=sum(r["eligible"] and bool(allowed(r)) for r in selected),
            wins=sum(r["win"] for r in picked),baseline=sum(r["base"]["win"] for r in selected),
            utility=float(np.mean(data)),ci95=np.percentile(np.array(data)[draw].mean(1),[2.5,97.5]).tolist(),
            matches=np.sum([[m["win"] for m in c["matches"]] for c in picked],axis=0).tolist(),
            base_matches=np.sum([[m["win"] for m in r["base"]["matches"]] for r in selected],axis=0).tolist())
    return groups


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path);p.add_argument("stage",choices=("train","valid"))
    a=p.parse_args()
    rows=[json.loads(f.read_text()) for f in sorted((a.folder/a.stage).glob("*.json"))]
    ident=frozen()
    assert len(rows)==len({r["seed"] for r in rows})==(160 if a.stage=="train" else 48)
    assert all(r["source"]==ident for r in rows)
    if a.stage=="train":
        folds={}
        rng=np.random.default_rng(231123)
        for opp in ("solution92","v16"):
            for team in (0,1):
                keys=sorted(r["seed"] for r in rows if r["opponent"]==opp and r["team"]==team)
                assert len(keys)==40
                for i,s in enumerate(rng.permutation(keys)):folds[int(s)]=i%4
        scores={}
        for i in range(4):
            head=fit([r for r in rows if folds[r["seed"]]!=i])
            for r in rows:
                if folds[r["seed"]]==i:scores[r["seed"]]=prediction(r,head)
        write_once(HERE/"modell.json",fit(rows))
    else:
        gate=json.loads((HERE/"train.json").read_text())
        assert gate["passed"] and gate["model_sha"]==sha(HERE/"modell.json")
        model=json.loads((HERE/"modell.json").read_text())
        scores={r["seed"]:prediction(r,model) for r in rows}
    selected=summary(rows,lambda r:scores[r["seed"]]>=.35)
    forced=summary(rows,lambda r:True)
    improvement=selected["both"]["utility"]>max(0,forced["both"]["utility"]) if a.stage=="train" else selected["both"]["utility"]>0
    gates=dict(utility=bool(improvement),chosen=selected["both"]["chosen"]>=(12 if a.stage=="train" else 5),
               wins=all(selected[o]["wins"]>=selected[o]["baseline"] for o in ("solution92","v16")))
    out=dict(selected=selected,always_r3=forced,source=ident,model_sha=sha(HERE/"modell.json"),
             games=sum(r["experiments"] for r in rows),gates=gates,passed=all(gates.values()))
    write_once(HERE/f"{a.stage}.json",out)
    for r in rows:r["held_out_value"]=scores[r["seed"]]
    d="\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n"
    (HERE/f"{a.stage}_spiele.jsonl.gz").write_bytes(gzip.compress(d.encode(),mtime=0))
    print(out)


if __name__=="__main__":main()
