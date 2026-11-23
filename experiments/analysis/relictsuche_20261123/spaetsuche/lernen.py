"""Fit on training openings, evaluate once on independently selected real continuations."""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np

from kandidat import FEATURES, predict
from sammeln import ALT, HERE, OPP, QUOTA, WORK, binding, game_path, panel
from auswerten import save_archive
from spielen import require, sha, stamp, write_once


def read(which):
    contract = binding()
    require(json.loads((WORK/"herkunft.json").read_text()) == contract, "Material source mismatch")
    signature = stamp(contract)
    selection = json.loads((WORK/which/"auswahl.json").read_text())
    require(selection["source"] == signature, "Selection source changed")
    streams = panel(which)
    groups = {}
    extra = []
    for opp in OPP:
        count = selection["screened_through_quota"][opp]
        expected = []
        limit = streams[opp][:count]
        for key in limit:
            r = json.loads(game_path(which,"reference",key).read_text())
            require(r["source"] == signature and r["events"] == [] and r["arm"] == "reference", "Baseline is not V16")
            if r["eligible"]:
                expected.append(key)
            else:
                require(r["turns"] == 55 and r["features"] is None and r["choice"] is None,"Bad rejected prefix")
            extra.append(r)
        require(expected == [tuple(x) for x in selection["selected"][opp]] and len(expected) == QUOTA[which]
                and expected[-1] == limit[-1], "Not first eligible fixed quota")
        for key in expected:
            variants = {a:json.loads(game_path(which,a,key).read_text()) for a in ("reference", *ALT)}
            b = variants["reference"]
            for a,r in variants.items():
                require(r["arm"] == a and r["choice"] == a and r["eligible"] and r["source"] == signature and
                        r["caught_errors"] == [0, 0] and r["turns"] == 101 and r["sensor"] == 1, "Bad full branch")
                require(all(r[k] == b[k] for k in ("prefix_commands","prefix_observations","seed","team","opponent","features")), "Unequal original prefix")
                require(len(b["features"]) == len(FEATURES) and np.all(np.isfinite(b["features"])), "Bad features")
                require(len({e[1] for e in r["events"]}) <= 1 and all(55 <= e[0] < r["sight"] and e[0] <= r["credit"] for e in r["events"]), "Bad search scope")
                if not r["events"]:
                    require(all(r[f] == b[f] for f in ("action_hash","sight","credit","after70","match")), "Inactive arm diverged")
            groups[key] = variants
    require(len(groups) == 2*QUOTA[which] and len({k[0] for k in groups}) == len(groups), "Duplicate map")
    rows = extra + [r for g in groups.values() for a,r in g.items() if a != "reference"]
    target = HERE/which
    target.mkdir(exist_ok=True)
    archive = target/"eroeffnungen.jsonl.gz"
    require(save_archive(rows,archive) == rows, "Archive readback differs")
    # Record honest overshoot from concurrent screening separately, never include it in the learner.
    planned = {f"{r['seed']}_{r['team']}_{r['opponent']}.json" for r in extra}
    extra_refs = [p for p in (WORK/which/"reference").glob("*.json") if p.name not in planned]
    spills = [json.loads(p.read_text()) for p in sorted(extra_refs)]
    if spills:
        save_archive(spills,target/"zusaetzliche_technikpraefixe.jsonl.gz")
    write_once(target/"material.json", dict(selection=selection, recorded_prefixes=len(extra), eligible=len(groups),
               full_openings=3*len(groups), truncated_prefixes=len(extra)-len(groups), overshoot=len(spills),
               overshoot_full=sum(r["turns"]==101 for r in spills), archive_sha256=sha(archive), contract=contract))
    return groups


def differences(b, a):
    return np.array([b["sight"] - a["sight"], b["credit"] - a["credit"],
                     (a["after70"][0]-a["after70"][1])-(b["after70"][0]-b["after70"][1]), a["match"]["win"]-b["match"]["win"]])


def utility(v):
    return float(.45*np.clip(v[0],-40,40)+.25*np.clip(v[1],-40,40)+.10*np.clip(v[2],-60,60)+6*v[3])


def fit():
    groups = read("train")
    x,y = [],[]
    for g in groups.values():
        b = g["reference"]
        x.append(b["features"])
        y.append([utility(differences(b,g[a])) for a in ALT])
    x,y = np.asarray(x),np.asarray(y)
    mean,scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-9] = 1
    z = (x-mean)/scale
    intercept = y.mean(axis=0)
    coef = np.linalg.solve(z.T@z + 30*np.eye(z.shape[1]),z.T@(y-intercept))
    model = dict(features=list(FEATURES), mean=mean.tolist(),scale=scale.tolist(),
                 coef=coef.tolist(),intercept=intercept.tolist(),threshold=1.0,penalty=30,
                 train_rows=len(groups), archive_sha256=sha(HERE/"train/eroeffnungen.jsonl.gz"))
    write_once(HERE/"modell.json",model)
    print("Locked model fitted to",len(groups),"qualifying training maps")


def evaluate():
    model = json.loads((HERE/"modell.json").read_text())
    groups = read("test")
    rows = []
    for (s,t,o),g in groups.items():
        b = g["reference"]
        arm = predict(model,b["features"])
        a = g[arm]
        delta=differences(b,a)
        rows.append(dict(seed=s,team=t,opponent=o,chosen=arm,changes=len(a["events"]),delta=delta.tolist(),
                         utility=utility(delta),baseline_m1=b["match"]["win"],selected_m1=a["match"]["win"]))
    def stats(sub):
        ds=np.asarray([r["delta"] for r in sub],float)
        return dict(n=len(sub),active_maps=sum(r["changes"]>0 for r in sub),choices=dict(Counter(r["chosen"] for r in sub)),
                    changes=sum(r["changes"] for r in sub),mean_delta=ds.mean(axis=0).tolist(),
                    utility=float(np.mean([r["utility"] for r in sub])),m1_reference=sum(r["baseline_m1"] for r in sub),
                    m1_selected=sum(r["selected_m1"] for r in sub),gained_m1=int(sum(ds[:,3]>0)),lost_m1=int(sum(ds[:,3]<0)))
    by = {o:stats([r for r in rows if r["opponent"]==o]) for o in OPP}
    all_rows=stats(rows)
    gates = {"eight_active_maps":all_rows["active_maps"]>=8, "two_active_each":all(by[o]["active_maps"]>=2 for o in OPP),
             "positive_value":all_rows["utility"]>0, "sight_positive":all_rows["mean_delta"][0]>0,
             "credit_nonnegative":all_rows["mean_delta"][1]>=0, "m1_nonnegative":all_rows["m1_selected"]>=all_rows["m1_reference"]}
    result=dict(model_sha256=sha(HERE/"modell.json"),by_opponent=by,combined=all_rows,gates=gates,
                passed=all(gates.values()),rows=rows)
    write_once(HERE/"test/ergebnis.json",result)
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},indent=2))


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("stage",choices=("fit","test"))
    args=p.parse_args()
    fit() if args.stage=="fit" else evaluate()
