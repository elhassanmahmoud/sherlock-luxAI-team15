"""Check sealed data and model using independent least squares and reported gameplay outcomes."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent


def read(which):
    root=HERE/which
    meta=json.loads((root/"material.json").read_text())
    archive=root/"eroeffnungen.jsonl.gz"
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==meta["archive_sha256"]
    with gzip.open(archive,"rt") as f:
        rows=[json.loads(line) for line in f]
    keys={(r["seed"],r["team"],r["opponent"],r["arm"]):r for r in rows}
    assert len(keys)==len(rows)
    selected=meta["selection"]["selected"]
    expected={tuple(k) for os in selected.values() for k in os}
    eligible={k[:3] for k,r in keys.items() if r["eligible"] and k[-1]=="reference"}
    assert eligible==expected and len(eligible)==meta["eligible"]
    out=[]
    for o in ("solution92","v16"):
        stream=sorted(r["seed"] for r in rows if r["arm"]=="reference" and r["opponent"]==o)
        assert sorted(k[0] for k in eligible if k[2]==o)[-1]==stream[-1]
        for k in sorted(u for u in eligible if u[2]==o):
            b=keys[(*k,"reference")]
            alternatives=[]
            for name in ("route","ziel"):
                a=keys[(*k,name)]
                assert b["turns"]==a["turns"]==101 and b["sensor"]==a["sensor"]==1
                assert all(a[f]==b[f] for f in ("prefix_commands","prefix_observations","features"))
                assert not b["events"] and len({e[1] for e in a["events"]})<=1
                if not a["events"]:
                    assert b["action_hash"]==a["action_hash"]
                diffs=[b["sight"]-a["sight"],b["credit"]-a["credit"],
                       a["after70"][0]-a["after70"][1]-b["after70"][0]+b["after70"][1],
                       a["match"]["win"]-b["match"]["win"]]
                capped=np.clip(diffs,[-40,-40,-60,-1],[40,40,60,1])
                utility=float(capped @ [.45,.25,.10,6.])
                alternatives.append((diffs,utility,bool(a["events"])))
            out.append((k,b["features"],alternatives))
    return out


def check():
    model=json.loads((HERE/"modell.json").read_text())
    train=read("train")
    x=np.asarray([v[1] for v in train])
    y=np.asarray([[a[1] for a in r[2]] for r in train])
    scale=np.std(x,axis=0)
    scale[scale<1e-9]=1.
    z=(x-x.mean(axis=0))/scale
    A=np.vstack((z,np.sqrt(30)*np.eye(z.shape[1])))
    B=np.vstack((y-y.mean(axis=0),np.zeros((z.shape[1],2))))
    w=np.linalg.lstsq(A,B,rcond=None)[0]
    assert np.allclose(model["mean"],x.mean(axis=0),atol=1e-10)
    assert np.allclose(model["scale"],scale,atol=1e-10)
    assert np.allclose(model["intercept"],y.mean(axis=0),atol=1e-10)
    assert np.allclose(model["coef"],w,atol=1e-10)
    test=read("test")
    report=json.loads((HERE/"test/ergebnis.json").read_text())
    actual={(r["seed"],r["team"],r["opponent"]):r for r in report["rows"]}
    activated=Counter(); values=[]; ds=[]
    for k,features,alts in test:
        scores=(np.array(features)-x.mean(axis=0))/scale @ w + y.mean(axis=0)
        name="reference"
        delta=[0,0,0,0];u=0;changed=False
        if scores.max()>=1:
            j=int(scores[1]>scores[0])
            name=("route","ziel")[j]
            delta,u,changed=alts[j]
        assert actual[k]["chosen"]==name and actual[k]["delta"]==delta
        assert abs(actual[k]["utility"]-u)<1e-10 and (actual[k]["changes"]>0)==changed
        activated[k[2]]+=changed
        values.append(u);ds.append(delta)
    v=np.array(ds)
    passed=(sum(activated.values())>=8 and min(activated.values())>=2 and np.mean(values)>0 and
            v[:,0].mean()>0 and v[:,1].mean()>=0 and v[:,3].sum()>=0)
    assert bool(passed)==report["passed"]
    return dict(training_maps=len(train),test_maps=len(test),same_weights=True,
                maximum_weight_error=float(np.max(abs(w-np.asarray(model["coef"])))),
                actual_test_outcomes_verified=len(test),passed=bool(passed),active_maps=dict(activated))


if __name__=="__main__":
    result=check()
    print(json.dumps(result,indent=2))
