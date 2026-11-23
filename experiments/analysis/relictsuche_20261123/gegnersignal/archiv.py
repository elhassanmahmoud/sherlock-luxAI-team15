"""Test the public first opponent point as a bound on the first relic's activation."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import COORD, Evidence

HERE=Path(__file__).resolve().parent


def first(v):
    where=np.flatnonzero(v)
    return int(where[0]) if len(where) else 101


def normalized(w):
    if not np.isfinite(w).all() or w.sum()<=0:
        raise ValueError("No feasible relic pair")
    return w/w.sum()


def features(credit):
    depth=COORD.sum(1).astype(float)/23
    flank=np.abs(COORD[:,0]-COORD[:,1])/23
    t=np.clip((credit-35)/20,-2,2)
    x=np.stack([depth,depth**2,flank,t*depth,t*flank],axis=1)
    return x-x.mean(0)


def observations(folder):
    eligible=[]
    count=foe_first=0
    for meta in sorted(folder.glob("*.json")):
        d=json.loads(meta.read_text())
        if "public_sha" not in d:
            continue
        paths=(meta.with_suffix(".npz"),meta.with_suffix(".richter.npz"))
        for p,key in zip(paths,("public_sha","label_sha"),strict=True):
            if hashlib.sha256(p.read_bytes()).hexdigest()!=d[key]:
                raise ValueError(f"Original archive mismatch: {p.name}")
        with np.load(paths[0]) as data, np.load(paths[1]) as judge:
            count+=1
            team=d["team"]
            credit=first(data["team_points"][:,1-team]>0)
            end=min(first(data["team_points"][:,team]>0),first(data["relic_nodes_mask"].any(1)))
            if credit>=end:
                continue
            foe_first+=1
            t=credit+6
            if t>=end or t>90:
                continue
            ev=Evidence()
            for i in range(t+1):
                ev.observe(i,dict(sensor_mask=data["sensor_mask"][i],units_mask=data["units_mask"][i],
                                units=dict(position=data["position"][i],energy=data["energy"][i])),team)
            w0=normalized(ev.location_weights(t))
            w1=normalized(ev.location_weights(credit))
            true=np.asarray(judge["first_pair"])[0]
            if sum(true)>=24:
                true=23-true[::-1]
            i_true,=np.flatnonzero(np.all(COORD==true,axis=1))
            if int(judge["spawn"])>credit:
                raise ValueError("Opponent scored before first-pair activation")
            if w1[i_true]<=0:
                raise ValueError("The true pair does not satisfy the public evidence")
            eligible.append((d["seed"],team,credit,int(i_true),w0,w1))
    if count!=160 or len({r[0] for r in eligible})<5:
        raise ValueError("Insufficient or incomplete source data")
    return eligible,count,foe_first


def fit(rows):
    def objective(beta):
        loss=.5*(beta@beta)*8.
        grad=8.*beta.copy()
        for _,_,t,y,_,w in rows:
            idx=w>0
            x=features(t)
            scores=np.log(w[idx])+x[idx]@beta
            logz=logsumexp(scores)
            loss+=logz-np.log(w[y])-x[y]@beta
            grad+=np.exp(scores-logz)@x[idx] - x[y]
        return loss,grad
    result=minimize(objective,np.zeros(5),jac=True,method="BFGS")
    if np.max(np.abs(result.jac))>.0005:
        raise ValueError("Unfitted score model")
    return result.x


def metrics(w,y):
    v=w[y]
    rank=1+(w>v).sum()+((w==v).sum()-1)/2
    return [-float(np.log(v)),float(rank),float(v),int((w>0).sum())]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    args=p.parse_args()
    rows,total,foe=observations(args.source)
    keys=sorted({r[0] for r in rows})
    shuffled=list(np.random.default_rng(231123).permutation(keys))
    fold={int(k):i%5 for i,k in enumerate(shuffled)}
    records=[]
    for i in range(5):
        beta=fit([r for r in rows if fold[r[0]]!=i])
        for seed,team,t,y,w0,w1 in rows:
            if fold[seed]!=i: continue
            w2=normalized(w1*np.exp(features(t)@beta))
            records.append(dict(seed=seed,team=team,foe_credit=t,fold=i,
                          old=metrics(w0,y),bounded=metrics(w1,y),learned=metrics(w2,y),
                          tv=float(np.abs(w0-w1).sum()/2)))
    by_map=defaultdict(list)
    for r in records:
        by_map[r["seed"]].append(r)
    draws=np.random.default_rng(231123).integers(len(keys),size=(5000,len(keys)))
    summary={}
    for lab in ("old","bounded","learned"):
        v=np.array([np.mean([r[lab] for r in by_map[k]],axis=0) for k in keys])
        other=np.array([np.mean([r["old"] for r in by_map[k]],axis=0) for k in keys])
        delta=other-v
        summary[lab]=dict(avg=v.mean(0).tolist(),logloss_gain=float(delta[:,0].mean()),
                          logloss_gain_ci95=np.quantile(delta[draws,0].mean(1),[.025,.975]).tolist())
    result=dict(total=total,foe_first=foe,timed_seats=len(records),maps=len(keys),summary=summary,
                altered=sum(r["tv"]>1e-7 for r in records),records=records)
    (HERE/"ergebnis.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="records"},indent=2))


if __name__=="__main__":
    main()
