"""Identify a distinct second high-confidence target in another match, before attaching actual scoring labels."""
from pathlib import Path
import argparse
import gzip
import json
import numpy as np
from experiments.analysis.relictsuche_20261123.feldprobe.signalmodell import parameters,proba

HERE=Path(__file__).resolve().parent


def analyze(folder):
    rows=[]
    for f in sorted(folder.glob("*.npz")):
        with np.load(f,allow_pickle=False) as z:
            seed=json.loads(str(z["meta"]))["seed"];step=z["step"];key=z["key"];x=z["x"];y=z["truth"]
        model=parameters()
        scores=proba(model,x) if len(x) else np.zeros((0,2))
        matches=set();used=set();events=[]
        for t in np.unique(step):
            if t//101 in matches:continue
            options=[]
            for j in np.flatnonzero(step==t):
                a,b=scores[j]
                uid,d,px,py,*_=map(int,key[j])
                pair=min(24*px+py,24*(23-py)+23-px)
                if pair in used or a<.55 or a-b<.25:continue
                options.append((a-b,a,-uid,-d,int(j),pair))
            if options:
                *_,j,pair=max(options)
                used.add(pair)
                matches.add(t//101)
                events.append(dict(t=int(t),key=key[j].tolist(),target=bool(y[j,0]),original=bool(y[j,1])))
                if len(events)==2:break
        rows.append(dict(seed=seed,events=events))
    second=[r["events"][1] for r in rows if len(r["events"])>1]
    positive=sum(v["target"] and not v["original"] for v in second)
    negative=sum(v["original"] and not v["target"] for v in second)
    return rows,dict(cards=len(rows),first=sum(bool(r["events"]) for r in rows),second=len(second),
        positive=positive,negative=negative,passed=bool(positive>negative and len(second)>=(10 if len(rows)==160 else 4)))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    a=p.parse_args()
    all_results={}
    for phase,n in (("train",160),("valid",48)):
        if phase=="valid" and not all_results["train"]["passed"]:break
        rows,result=analyze(a.folder/phase)
        assert result["cards"]==n
        all_results[phase]=result
        (HERE/(phase+"_karten.jsonl.gz")).write_bytes(gzip.compress(("\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n").encode(),mtime=0))
    (HERE/"ergebnis.json").write_text(json.dumps(all_results,indent=2)+"\n")
    print(all_results)
