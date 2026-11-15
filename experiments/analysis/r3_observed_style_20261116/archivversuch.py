"""Measure one pre-registered M1 trigger on immutable DAgger recordings. No game/agent imports."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import tempfile

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
                 "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[variable] = "1"

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE.parent
PLAN = "e1c79a474ff21eabfc350becde3b6487088df3451d0eff0e9707b2fc5e921846"
MANIFESTS = {
    "r1": ("movement_dagger_20261115/corpus.json", "fed298f9dd84100c119423e2a8d9c5607291a54a028b3ca560b9d454e64d405f"),
    "r3_train": ("r3_context_selector_20261115/fit/table.json", "5dde3b73432758af1fd4b1e07f9722bbe1816341ccc8b00a6a94761680bf2090"),
    "r3_val": ("r3_context_selector_20261115/fit/validation.json", "2a10ebcd77c6922281521d00c97f9c76bd8eebb38ca6a64d390a15cac57f4e9f"),
}
DATA = {
    "r1": ("final_20261115_movement_dagger", "50bf0bb810f7b913acce8940937d335ebf180bc796457dcf880ffa6743ec2724",
           "5327d0ff4e2cc4b09bdcb43ae51fbd7dcc9f6d8487f79f4a7cfd1ad176813575"),
    "r3": ("final_20261115_r3_context", "3476e80f57ff23f76fb4d8aa00269e647116ca9c468c0d2d0f6278af85567a03",
           "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"),
}
OPPONENTS = ("kaggle3", "solution92", "v14")
SIDES = ("player_0","player_1")
ROSTER = {
    "fit":range(7272000,7272120), "calibration":range(7272200,7272224),
    "r3_train":range(7287000,7287048), "r3_val":range(7287100,7287124),
}
NAMES = [f"m1_{start}_{f}" for start in ("1_50","51_100") for f in (
    "covered_fraction","enemy_contact","occupied_per_covered","stacked_share","units_per_tile",
    "on_points","in_own_half","clipped_energy_per_unit","occupancy_jaccard")]
MODEL = "regel.json"
RESULT = "pruefung.json"


def insist(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def register(which):
    name, expected = MANIFESTS[which]
    p=ANALYSIS/name
    insist(sha(p)==expected, f"Source index changed: {p}")
    return json.loads(p.read_bytes())


def key(seed,side):
    opp = OPPONENTS[(seed-7271000)%3]
    return f"g{seed}_{side}_{opp}.npz"


def archives(base, policy):
    directory, digest, student = DATA[policy]
    folder = base/directory
    p=folder/"protocol.json"
    insist(sha(p)==digest, "Different collection protocol")
    protocol=json.loads(p.read_bytes())
    insist(protocol["student_sha256"]==student and protocol["rotation"]==list(OPPONENTS) and
           protocol["rotation_origin"]==7271000 and protocol["steps"]==303, "Unexpected episode/actor")
    if policy=="r1":
        entries=register("r1")["games"]
        records={key(r["seed"],r["side"]):r["sha256"] for r in entries}
        insist(len(records)==len(entries),"Duplicate old source IDs")
        labels=("fit","calibration")
    else:
        a=register("r3_train")["sources"]
        b=register("r3_val")["valid_sources"]
        insist(a.keys().isdisjoint(b),"R3 source blocks overlap")
        records={**a,**b}
        labels=("r3_train","r3_val")
    expected={key(s,side) for label in labels for s in ROSTER[label] for side in SIDES}
    insist(set(records)==expected=={p.name for p in folder.glob("g*.npz")},"Missing or additional game keys")
    return folder, records


def read_first_match(path, expected_sha):
    insist(sha(path)==expected_sha, f"Archive changed: {path.name}")
    with np.load(path,allow_pickle=False) as z:
        frames=z["global_step"]
        insist(frames.ndim==1 and frames.dtype==np.int16 and np.all(np.diff(frames)>0) and
               np.all((frames>=1)&(frames<=302)&(frames%101!=0)), "Invalid public timeline")
        n=int(np.searchsorted(frames,101))
        with z.zip.open("planes.npy") as stream:
            insist(np.lib.format.read_magic(stream)==(1,0),"Unexpected NPY version")
            size,fortran,dtype=np.lib.format.read_array_header_1_0(stream)
            insist(size==(len(frames),16,24,24) and not fortran and dtype==np.int8,"Unexpected plane encoding")
            # Read just the prefix of this member: no Match 2 or Match 3 data enter feature extraction.
            raw=stream.read(n*16*24*24)
    first=np.frombuffer(raw,np.int8).reshape(n,16,24,24)
    return frames[:n], first[:,[0,10,11,12,14]]


def window_features(steps, board):
    """Accept only the five public planes and the retained times of one M1 window."""
    points,counts,energy,coverage,own_half=board.transpose(1,0,2,3)
    tiles=counts>0
    units=np.rint(counts.astype(float)*(4/127)).astype(np.int16)
    visible=coverage>0  # Historical last_seen plane includes the symmetry reflection.
    num_tiles=int(tiles.sum())
    num_units=int(units.sum())
    total_views=len(steps)
    ncovered=int(visible.sum())
    joint=visible[:-1]&visible[1:]&(np.diff(steps)==1)[:,None,None]
    union=(tiles[:-1]|tiles[1:])&joint
    intersection=(tiles[:-1]&tiles[1:])&joint

    def frac(n,d):
        return float(n/d) if d else 0.0

    return [frac(ncovered,total_views*24*24),frac(tiles.any(axis=(1,2)).sum(),total_views),
            frac(num_tiles,ncovered),frac((units>=2).sum(),num_tiles),frac(num_units,num_tiles),
            frac((tiles & (points>0)).sum(),num_tiles),frac((tiles & (own_half>0)).sum(),num_tiles),
            frac(energy.sum()/127,num_units),frac(intersection.sum(),union.sum())]


def observations(base, policy, groups):
    folder, records=archives(base, policy)
    rows=[]
    for group in groups:
        for seed in ROSTER[group]:
            opponent=OPPONENTS[(seed-7271000)%3]
            for side in SIDES:
                name=key(seed,side)
                steps,board=read_first_match(folder/name,records[name])
                first=steps<=50
                x=window_features(steps[first],board[first])+window_features(steps[~first],board[~first])
                rows.append(dict(group=group,seed=seed,side=side,opponent=opponent,archive_sha256=records[name],
                                 m1_boards=len(steps),features=x))
    return rows


def matrix(rows):
    return np.asarray([r["features"] for r in rows],dtype=float)


def learn(rows):
    x=matrix(rows)
    mean=x.mean(axis=0)
    sd=x.std(axis=0)
    sd=np.where(np.ptp(x,axis=0)==0,1.0,sd)
    z=(x-mean)/sd
    y=np.array([r["opponent"]=="v14" for r in rows],dtype=float)
    balance=np.where(y==1,0.5/y.mean(),0.5/(1-y.mean()))

    def objective(w):
        logits=z @ w[:-1]+w[-1]
        loss=np.sum(balance*(np.logaddexp(0,logits)-y*logits))+.5*np.dot(w[:-1],w[:-1])
        delta=balance*(expit(logits)-y)
        grad=np.r_[z.T @ delta+w[:-1],delta.sum()]
        return loss,grad

    fitted=minimize(objective,np.zeros(z.shape[1]+1),jac=True,method="L-BFGS-B",
                    options=dict(maxiter=1000,ftol=1e-15,gtol=1e-8))
    insist(fitted.success and np.max(abs(fitted.jac))<1e-4,"Fit did not converge")
    return dict(names=NAMES,mean=mean.tolist(),scale=sd.tolist(),coef=fitted.x[:-1].tolist(),
                intercept=float(fitted.x[-1]))


def scores(rows, fit):
    return expit((matrix(rows)-fit["mean"])/fit["scale"] @ np.array(fit["coef"])+fit["intercept"])


def scored(rows,fit,threshold):
    return [{k:v for k,v in r.items() if k!="features"} |
            dict(score=float(p),triggers=bool(p>threshold)) for r,p in zip(rows,scores(rows,fit),strict=True)]


def summary(rows):
    rng=np.random.default_rng(2711)
    result={}
    for opp in OPPONENTS:
        group=[r for r in rows if r["opponent"]==opp]
        seeds=sorted({r["seed"] for r in group})
        pairs={s:{r["side"]:int(r["triggers"]) for r in group if r["seed"]==s} for s in seeds}
        insist(all(set(p)==set(SIDES) for p in pairs.values()),"Unpaired game seats")
        draws=np.array([sum(pairs[s].values())/2 for s in seeds])
        ci=np.percentile(draws[rng.integers(len(draws),size=(10000,len(draws)))].mean(1),[2.5,97.5])
        result[opp]=dict(seats=len(group),triggers=sum(r["triggers"] for r in group),
                         maps=len(pairs),triggered_maps=int(sum(draws>0)),ci95=ci.tolist(),
                         by_seat={s:sum(r["triggers"] for r in group if r["side"]==s) for s in SIDES})
    return result


def publish(path, value):
    payload=(json.dumps(value,indent=1,sort_keys=True,allow_nan=False)+"\n").encode()
    if path.exists():
        insist(path.read_bytes()==payload,"An earlier frozen result differs")
        return
    with tempfile.NamedTemporaryFile(dir=path.parent) as f:
        f.write(payload)
        f.flush()
        os.link(f.name,path)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("fit","assess"))
    p.add_argument("--data",required=True,type=Path,help="Original experiments/imitation directory")
    p.add_argument("--out",required=True,type=Path,help="Directory for regel.json and pruefung.json")
    a=p.parse_args()
    insist(sha(HERE/"PLAN.md")==PLAN,"Plan differs from registration")
    a.out.mkdir(exist_ok=True)
    source=sha(Path(__file__))
    rule_path=a.out/MODEL
    if a.mode=="fit":
        old=observations(a.data,"r1",("fit","calibration"))
        train=[r for r in old if r["group"]=="fit"]
        held=[r for r in old if r["group"]=="calibration"]
        fit=learn(train)
        held_scores=scores(held,fit)
        threshold=float(max(.5,max(p for p,r in zip(held_scores,held,strict=True) if r["opponent"]!="v14")))
        train=scored(train,fit,threshold)
        held=scored(held,fit,threshold)
        rule=dict(plan_sha256=PLAN,source_sha256=source,fit=fit,threshold_strictly_above=threshold,
                  archive_protocol=DATA["r1"][1],source_register=MANIFESTS["r1"][1],
                  counts={k:summary(v) for k,v in (("fit",train),("calibration",held))},cases=train+held)
        publish(rule_path,rule)
        print("Fixed threshold",threshold,rule_path)
    else:
        rule=json.loads(rule_path.read_bytes())
        insist((rule["source_sha256"],rule["plan_sha256"],rule["archive_protocol"],rule["source_register"])==
               (source,PLAN,DATA["r1"][1],MANIFESTS["r1"][1]),"Different frozen fit")
        rows=scored(observations(a.data,"r3",("r3_train","r3_val")),rule["fit"],rule["threshold_strictly_above"])
        counts=summary(rows)
        passed=counts["v14"]["triggers"]>=16 and all(counts[o]["triggers"]<=1 for o in ("solution92","kaggle3"))
        details={g:summary([r for r in rows if r["group"]==g]) for g in ("r3_train","r3_val")}
        publish(a.out/RESULT,dict(passes=passed,rule_sha256=sha(rule_path),plan_sha256=PLAN,
                                  source_sha256=source,archive_protocol=DATA["r3"][1],
                                  source_registers={k:MANIFESTS[k][1] for k in details},counts=counts,by_block=details,cases=rows))
        print("Gate",passed,"R3 triggers", {o: v["triggers"] for o,v in counts.items()})


if __name__=="__main__":
    main()
