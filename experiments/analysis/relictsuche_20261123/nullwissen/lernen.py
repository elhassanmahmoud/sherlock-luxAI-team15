"""Fit an old-empty-field probability and choose the operating point using strictly out-of-map predictions."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

from experiments.analysis.relictsuche_20261123.nullwissen.gedaechtnis import load,replay
from experiments.analysis.relictsuche_20261123.nullwissen.risiko import GEOMETRY,HERE,NAMES,Public,probabilities
from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import PACKAGE
from scripts.r3_package import r3_package_agent

THRESHOLDS=(.005,.01,.02,.04,.07,.12,.20)


def features(root,out,stage):
    src=root/stage
    exist=out/"train"
    folders=out/("merkmale_"+stage)
    folders.mkdir(exist_ok=True)
    templates=None
    if stage=="valid":
        assert (HERE/"modell.json").exists() and json.loads((HERE/"modell.json").read_text())["qualified"]
        templates=[r3_package_agent(f"player_{i}",PACKAGE)._imitation.belief for i in (0,1)]
    for receipt in sorted(src.glob("*.json")):
        meta=json.loads(receipt.read_text())
        file=folders/(receipt.stem+".npz")
        if file.exists():
            continue
        pub=load(src,meta,"public")
        if stage=="valid":
            _,bits=replay(templates,src,meta,include_judge=False)
        else:
            with np.load(exist/(receipt.stem+".npz")) as tmp:
                bits=tmp["bits"]
        masks=np.unpackbits(bits,axis=-1,bitorder="little").reshape(303,3,24,24).astype(bool)
        brain=Public()
        team=meta["team"]
        zone=np.zeros((24,24),bool)
        moments=[]
        for t in range(303):
            obs={k:pub[k][t] for k in ("units_mask","sensor_mask","team_points","relic_nodes_mask","relic_nodes")}
            obs["units"]={k:pub[k][t] for k in ("position","energy")}
            for x,y in obs["relic_nodes"][obs["relic_nodes_mask"]]:
                for i,j in ((int(x),int(y)),(23-int(y),23-int(x))):
                    zone[max(0,i-2):i+3,max(0,j-2):j+3]=True
            rows=brain.frame(t,obs,masks[t,0],pub["known_points"][t],zone,pub["terrain"][t],pub["commands"][t],
                             pub["move_mask"][t],pub["protected"][t],team,meta["cfg"]["unit_move_cost"])
            assert np.array_equal(brain.inherited,masks[t,1])
            for q,cell,dist,x in rows:
                assert masks[t,2].ravel()[cell]
                moments.append((t,q,cell,x))
        # Attach truth only once the public choices and their attributes are fixed.
        judge=load(src,meta,"private")
        turns=np.array([r[0] for r in moments],int)
        cells=np.array([r[2] for r in moments],int)
        w=judge["weights"].ravel()[cells]
        labels=(w>0)&(w<=judge["active"][turns].sum(axis=1))
        np.savez_compressed(file,seed=meta["seed"],team=team,opponent=meta["opponent"],turn=turns,cell=cells,
            pair=np.array([r[1] for r in moments],int),x=np.array([r[3] for r in moments],float).reshape(-1,len(NAMES)),y=labels)
    data=[]
    for f in sorted(folders.glob("*.npz")):
        with np.load(f) as z:
            data.append({k:z[k] for k in z})
    assert len(data)==dict(train=160,valid=48)[stage] and len({int(d["seed"]) for d in data})==len(data)
    return data


def fit(data,ncol):
    active=[r for r in data if len(r["y"])]
    x=np.concatenate([r["x"][:,:ncol] for r in active])
    y=np.concatenate([r["y"] for r in active])
    row_weights=np.concatenate([np.full(len(r["y"]),len(y)/(len(active)*len(r["y"]))) for r in active])
    average=np.average(x,axis=0,weights=row_weights)
    scale=np.maximum(.02,np.sqrt(np.average((x-average)**2,axis=0,weights=row_weights)))
    X=(x-average)/scale
    def objective(v):
        z=X@v[:-1]+v[-1]
        diff=row_weights*(expit(z)-y)
        loss=(row_weights*(np.logaddexp(0,z)-y*z)).sum()+.5*(v[:-1]@v[:-1])
        return loss,np.r_[X.T@diff+v[:-1],diff.sum()]
    start=np.zeros(ncol+1)
    start[-1]=np.log(np.average(y,weights=row_weights)/(1-np.average(y,weights=row_weights)))
    sol=minimize(objective,start,jac=True,method="L-BFGS-B",options=dict(maxiter=600,ftol=1e-12))
    assert sol.success
    return dict(center=average.tolist(),scale=scale.tolist(),bias=float(sol.x[-1]),beta=sol.x[:-1].tolist())


def first(r,prob,tau):
    ok=np.flatnonzero(prob>=tau)
    if not len(ok):
        return None
    t=r["turn"][ok[0]]
    choices=np.flatnonzero(r["turn"]==t)
    i=int(choices[np.argmax(prob[choices])])
    return dict(t=int(t),cell=int(r["cell"][i]),pair=int(r["pair"][i]),p=float(prob[i]),actual=bool(r["y"][i]))


def metrics(data,predictions,threshold):
    choices=[first(r,p,threshold) for r,p in zip(data,predictions,strict=True)]
    used=[c for c in choices if c is not None]
    hit=sum(c["actual"] for c in used)
    return dict(picked=len(used),hit=hit,wrong=len(used)-hit,value=6*hit-len(used)),choices


def summarize(data,model):
    full=[probabilities(r["x"],model["full"]) for r in data]
    small=[probabilities(r["x"][:,:GEOMETRY],model["geom"]) for r in data]
    stat,choices=metrics(data,full,model["threshold"])
    valid=[i for i,r in enumerate(data) if len(r["y"])]
    diffs=np.array([((small[i]-data[i]["y"])**2).mean()-((full[i]-data[i]["y"])**2).mean() for i in valid])
    draw=np.random.default_rng(231123).integers(0,len(valid),(20000,len(valid)))
    base=float(np.mean(np.concatenate([r["y"] for r in data])))
    stat.update(rows=sum(len(r["y"]) for r in data),cards=len(data),cards_with_options=len(valid),
        base_prevalence=base,brier_gain_map=float(diffs.mean()),brier_ci95=np.percentile(diffs[draw].mean(1),[2.5,97.5]).tolist())
    rate=stat["hit"]/max(1,stat["picked"])
    conditions=dict(used=stat["picked"]>=6,targets=stat["hit"]>=3,precision=rate>=max(.10,2*base),brier=diffs.mean()>=0)
    stat.update(gates={k:bool(v) for k,v in conditions.items()},passed=bool(all(conditions.values())))
    case_rows=[dict(seed=int(r["seed"]),team=int(r["team"]),opponent=str(r["opponent"]),first=c,
                    options=len(r["y"]),real=int(r["y"].sum())) for r,c in zip(data,choices,strict=True)]
    return stat,case_rows


def immutable(path,raw):
    if path.exists():
        assert path.read_bytes()==raw
    else:
        path.write_bytes(raw)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("split",choices=("train","valid"))
    a=p.parse_args()
    data=features(a.archive,a.out,a.split)
    if a.split=="train":
        folds=[i%4 for i in range(len(data))]
        preds=[None]*len(data)
        for f in range(4):
            head=fit([r for i,r in enumerate(data) if folds[i]!=f],len(NAMES))
            for i,r in enumerate(data):
                if folds[i]==f:
                    preds[i]=probabilities(r["x"],head)
        scores={str(t):metrics(data,preds,t)[0] for t in THRESHOLDS}
        ranked=sorted(((r["value"],float(t)) for t,r in scores.items() if r["picked"]>=12),reverse=True)
        value,tau=ranked[0] if ranked else (-1,1.)
        model=dict(full=fit(data,len(NAMES)),geom=fit(data,GEOMETRY),threshold=tau,qualified=value>0,
                   names=NAMES,train_cards=len(data),by_threshold=scores)
        immutable(HERE/"modell.json",(json.dumps(model,indent=2)+"\n").encode())
    model=json.loads((HERE/"modell.json").read_text())
    stat,rows=summarize(data,model)
    immutable(HERE/(a.split+".json"),(json.dumps(stat,indent=2)+"\n").encode())
    immutable(HERE/(a.split+"_wahl.jsonl.gz"),gzip.compress(("\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n").encode(),mtime=0))
    print(stat,flush=True)


if __name__=="__main__":
    main()
