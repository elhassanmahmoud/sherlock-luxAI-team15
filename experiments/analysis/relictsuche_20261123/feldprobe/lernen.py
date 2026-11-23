"""Calibrate a scoring-field ranker and check actual first proposals on held-out maps."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

from signalmodell import HERE,NAMES,STATIC,pick,proba


def boards(path,n):
    result=[]
    for f in sorted(path.glob("*.npz")):
        if f.name.endswith(".part.npz"):
            continue
        with np.load(f,allow_pickle=False) as a:
            result.append((json.loads(str(a["meta"])),*[a[k] for k in ("step","key","x","truth")]))
    assert len(result)==n and len({m["seed"] for m,*_ in result})==n
    for m,step,key,x,y in result:
        assert tuple(m["names"])==NAMES and x.shape==(len(step),2,len(NAMES)) and np.isfinite(x).all()
        assert key.shape==(len(step),6) and y.shape==(len(step),2)
    return result


def train(data,size):
    arr=[x[:,:,:size].reshape(-1,size) for _,_,_,x,_ in data if len(x)]
    labels=[y.reshape(-1) for _,_,_,x,y in data if len(x)]
    x=np.concatenate(arr).astype(float)
    y=np.concatenate(labels).astype(float)
    w=np.concatenate([np.full(len(r),len(x)/len(arr)/len(r)) for r in arr])
    center=np.average(x,axis=0,weights=w)
    scale=np.maximum(.001,np.sqrt(np.average((x-center)**2,axis=0,weights=w)))
    x=(x-center)/scale
    def objective(b):
        z=x@b[:-1]+b[-1]
        loss=w@(np.logaddexp(0,z)-y*z)+4*(b[:-1]@b[:-1])
        error=w*(expit(z)-y)
        return loss,np.r_[x.T@error+8*b[:-1],error.sum()]
    result=minimize(objective,np.zeros(size+1),jac=True,method="L-BFGS-B",
                    options={"maxiter":400,"ftol":1e-12,"gtol":1e-7})
    assert result.success
    return dict(mean=center.tolist(),scale=scale.tolist(),beta=result.x[:-1].tolist(),
                intercept=float(result.x[-1]),features=list(NAMES[:size]),rows=len(x),maps=len(arr),objective=float(result.fun))


def chosen(model,key,x,step):
    for t in np.unique(step):
        indices=np.flatnonzero(step==t)
        rows=[(int(key[j,0]),int(key[j,1]),tuple(key[j,2:4]),tuple(key[j,4:6]),x[j,0],x[j,1]) for j in indices]
        picked=pick(rows,model)
        if picked is not None:
            return int(indices[picked])
    return None


def summarize(data,models):
    rows=[]
    for m,step,key,x,y in data:
        line=dict(seed=m["seed"],team=m["team"],opponent=m["opponent"],options=len(step))
        for name,model in models.items():
            if len(step):
                score=proba(model,x[:,0])
                brier=float(np.mean((score-y[:,0])**2))
                arg=chosen(model,key,x,step)
            else:
                brier=None
                arg=None
            line[name]=dict(brier=brier,first=None if arg is None else dict(turn=int(step[arg]),key=key[arg].tolist(),
                actual=list(map(int,y[arg])),probabilities=proba(model,x[arg]).tolist()))
        rows.append(line)
    nonempty=[r for r in rows if r["options"]]
    diffs=np.array([r["geometry"]["brier"]-r["full"]["brier"] for r in nonempty])
    picks=[r["full"]["first"] for r in rows if r["full"]["first"] is not None]
    delta=[p["actual"][0]-p["actual"][1] for p in picks]
    draw=np.random.default_rng(231123).integers(0,len(diffs),size=(20000,len(diffs)))
    stat=dict(maps=len(rows),eligible=len(nonempty),options=sum(r["options"] for r in rows),
        mean_brier={n:float(np.mean([r[n]["brier"] for r in nonempty])) for n in models},
        brier_gain=float(diffs.mean()),ci95_brier_gain=np.percentile(diffs[draw].mean(1),[2.5,97.5]).tolist(),
        changed=len(picks),added=delta.count(1),gave_up=delta.count(-1),unchanged=delta.count(0),
        target_true=sum(p["actual"][0] for p in picks),original_true=sum(p["actual"][1] for p in picks))
    stat["passed"]=stat["brier_gain"]>0 and stat["changed"]>=6 and stat["added"]>stat["gave_up"]
    return stat,rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("raw",type=Path)
    p.add_argument("stage",choices=("train","valid"))
    a=p.parse_args()
    data=boards(a.raw/a.stage,160 if a.stage=="train" else 48)
    path=HERE/"modell.json"
    if a.stage=="train":
        models=dict(full=train(data,len(NAMES)),geometry=train(data,len(STATIC)))
        raw=(json.dumps(models,indent=2,allow_nan=False)+"\n").encode()
        if path.exists() and path.read_bytes()!=raw:
            raise ValueError("Previously frozen weights differ")
        path.write_bytes(raw)
    models=json.loads(path.read_text())
    stats,rows=summarize(data,models)
    if a.stage=="train":
        stats.pop("passed")
    stats["model_hash"]=sha256(path.read_bytes()).hexdigest()
    (HERE/f"{a.stage}.json").write_text(json.dumps(stats,indent=2,allow_nan=False)+"\n")
    raw="\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n"
    (HERE/f"{a.stage}_karten.jsonl.gz").write_bytes(gzip.compress(raw.encode(),mtime=0))
    print(json.dumps(stats,indent=2))


if __name__=="__main__":
    main()
