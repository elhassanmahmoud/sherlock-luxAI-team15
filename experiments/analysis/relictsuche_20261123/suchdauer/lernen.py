"""Learn the native scout's remaining time from public features before its proposed turn."""
import gzip
import json
from pathlib import Path

import numpy as np
from experiments.analysis.relictsuche_20261123.spielwert.politik import NAMES
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,write_once

HERE=Path(__file__).resolve().parent


def blocks(stage):
    file=HERE.parent/"spielwert"/f"{stage}_partien.jsonl.gz"
    out={}
    with gzip.open(file,"rt") as plain:
        for line in plain:
            row=json.loads(line)
            key=(row["seed"],row["team"],row["opponent"])
            assert row["steps"]==303 and row["caught_errors"]==[0,0]
            assert row["id"] not in out.setdefault(key,{})
            out[key][row["id"]]=row
    assert len(out)==len({k[0] for k in out})=={"pilot":96,"train":384}[stage]
    for arms in out.values():
        assert set(arms)=={"b0","b1","b3"} and all(r["features"]==arms["b0"]["features"] for r in arms.values())
    return out,sha(file)


def predict(features,m):
    converted=(np.asarray(features,float)-m["center"])/m["scale"]
    return float(converted@np.asarray(m["weights"])+m["bias"])


def train(refs):
    pairs=[(r["features"],r["sight"]-r["features"][0]) for r in refs if r["features"] is not None]
    x=np.array([v[0] for v in pairs]);y=np.array([v[1] for v in pairs])
    assert x.shape==(len(pairs),len(NAMES)) and np.min(y)>=0
    center=x.mean(0);scale=np.maximum(.001,x.std(0));z=(x-center)/scale
    coef=np.linalg.solve(z.T@z+48*np.eye(len(NAMES)),z.T@(y-y.mean()))
    return dict(names=NAMES,center=center.tolist(),scale=scale.tolist(),weights=coef.tolist(),
                bias=float(y.mean()),threshold=float(np.quantile(z@coef+y.mean(),.75)),opportunities=len(pairs))


def main():
    learning,inp=blocks("train")
    m=train([arms["b0"] for arms in learning.values()])
    write_once(HERE/"modell.json",{**m,"names":list(NAMES),"training_sha":inp})
    pilot,test_sha=blocks("pilot")
    assert not ({k[0] for k in learning}&{k[0] for k in pilot})
    rows=[]
    for (seed,t,opponent),arms in pilot.items():
        base=arms["b0"];x=base["features"];estimate=predict(x,m) if x is not None else None
        allowed=estimate is not None and estimate>m["threshold"]
        row=arms["b3"] if allowed else base
        if row["action_hash"]==base["action_hash"]:assert row["matches"]==base["matches"]
        rows.append(dict(seed=seed,team=t,opponent=opponent,selected=allowed,estimate=estimate,
                         remaining=base["sight"]-x[0] if x is not None else None,
                         changed=row["action_hash"]!=base["action_hash"],chosen=row["action_hash"],
                         old=base["win"],new=row["win"],sight=base["sight"]-row["sight"],credit=base["credit"]-row["credit"]))
    active=[r for r in rows if r["estimate"] is not None]
    wait={k:float(np.mean([r["remaining"] for r in active if r["selected"]==v])) for k,v in (("accepted",True),("rejected",False))}
    group={}
    for opp in ("v16","solution92"):
        g=[r for r in rows if r["opponent"]==opp]
        group[opp]=dict(cards=len(g),**{k:sum(r[k] for r in g) for k in ("old","new","changed","sight","credit")})
    gates=dict(changed=sum(r["changed"] for r in rows)>=8,earlier=sum(r["sight"] for r in rows)>0,
               winners=all(g["new"]>=g["old"] for g in group.values()),predictive=wait["accepted"]-wait["rejected"]>=8.)
    write_once(HERE/"pilot.json",dict(training_maps=len(learning),pilot_maps=len(rows),opportunities=len(active),
                 rmse=float(np.sqrt(np.mean([(r["remaining"]-r["estimate"])**2 for r in active]))),
                 reference_rmse=float(np.sqrt(np.mean([(r["remaining"]-m["bias"])**2 for r in active]))),wait=wait,group=group,
                 model=sha(HERE/"modell.json"),archive=test_sha,gates=gates,passed=bool(all(gates.values())),rows=rows))


if __name__=="__main__":main()
