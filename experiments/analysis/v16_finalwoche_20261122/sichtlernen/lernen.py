"""Fit the prespecified ridge estimator and audit causal one-step effects on untouched maps."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from sicht import HERE, NAMES


def read(folder,part,count):
    records=[]
    for p in sorted(folder.glob("*.json")):
        row=json.loads(p.read_text())
        if row["split"]!=part:continue
        raw=p.with_suffix(".npz")
        if (sha256(raw.read_bytes()).hexdigest()!=row["sha256"] or row["ticks"]!=46
                or row["calibration"]!=bool(row["rows"])):
            raise ValueError("Different measured opening")
        with np.load(raw,allow_pickle=False) as d:
            a={k:d[k] for k in d.files}
        if a["x"].shape!=(row["rows"],len(NAMES)) or a["delta"].shape!=(row["rows"],4):
            raise ValueError("Number of training cases differs")
        records.append((row,a))
    if len(records)!=count or len({r["seed"] for r,_ in records})!=count:
        raise ValueError("Incomplete fixed set")
    return records


def run(folder,out):
    train=read(folder,"train",96)
    x=np.concatenate([a["x"] for _,a in train]).astype(np.float64)
    changes=np.concatenate([a["delta"] for _,a in train])
    stay=NAMES.index("was_stay")
    target=changes[:,0]+.2*changes[:,1]+5*(changes[:,2]-changes[:,3])-.25*x[:,stay]
    mean=x.mean(0)
    center=x-mean
    w=np.linalg.solve(center.T@center+5*np.eye(len(NAMES)),center.T@(target-target.mean()))
    b=float(target.mean()-mean@w)
    valid=read(folder,"valid",32)
    if len({r["source"] for r,_ in train+valid})!=1:raise ValueError("Input collections differ")
    selections=[]
    for row,a in valid:
        est=a["x"]@w+b
        for step in np.unique(a["step"]):
            ids=np.flatnonzero(a["step"]==step)
            k=max(ids,key=lambda j:(float(est[j]),-int(a["uid"][j])))
            if est[k]<1.5:continue
            pairs,cells,own,enemy=map(float,a["delta"][k])
            selections.append(dict(seed=row["seed"],side=row["side"],opponent=row["opponent"],step=int(step),
                                   uid=int(a["uid"][k]),pairs=pairs,cells=cells,own=own,enemy=enemy,estimate=float(est[k])))
    maps=len({q["seed"] for q in selections})
    effect={k:float(sum(r[k] for r in selections)) for k in ("pairs","cells","own","enemy")}
    n=len(selections)
    gates=dict(support=n>=100 and maps>=12, pairs=effect["pairs"]>=n if n else False, points=effect["own"]>=effect["enemy"])
    r=dict(eligible=all(gates.values()),gates=gates,estimate=dict(w=w.tolist(),bias=b,names=NAMES),
           train_maps=96,train_rows=len(x),valid_maps=32,valid_rows=sum(len(a["x"]) for _,a in valid),
           chosen=n,affected_maps=maps,mean_pairs=effect["pairs"]/max(1,n),mean_cells=effect["cells"]/max(1,n),
           total=effect,selections=selections,manifests=[r for r,_ in train+valid],
           plan=sha256((HERE/"PLAN.md").read_bytes()).hexdigest(),
           policy=sha256((HERE/"sicht.py").read_bytes()).hexdigest())
    (out/"offline.json").write_text(json.dumps(r,separators=(",",":"),allow_nan=False)+"\n")
    print({k:r[k] for k in ("eligible","gates","train_rows","chosen","affected_maps","mean_pairs","mean_cells","total")},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    run(a.folder,a.out)
