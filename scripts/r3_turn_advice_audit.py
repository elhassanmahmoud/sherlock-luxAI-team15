"""Measure one registered moderate-confidence movement arbitration on two fixed holdouts."""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np
import torch

from scripts.experiment import limit_threads
from scripts.imitate import PLANE_SCALE, prepare_labels
from scripts.r3_diagonal import R3,REFERENCE,decision_counts,digest,played_action
from scripts.r3_turn_advice import extra
from scripts.selective_advice_agent import load_heads
from scripts.train_combat_advice import publish_json

ROOT=Path(__file__).resolve().parents[1]
REF="3f05bde9320d9c718e404d2280590f76ab5de823c9fdea594f564433bbcc54de"
PLAN="experiments/analysis/r3_turn_advice_20261115/PLAN.md"
BLOCKS={"old_validation":range(7272200,7272224),"new_validation":range(7287100,7287124)}
OPPONENTS=("kaggle3","solution92","v14")


def summary(cards):
    records=list(cards)
    good=np.asarray([c["gained"]-c["lost"] for c in records],dtype=np.int64)
    rows=np.asarray([c["rows"] for c in records],dtype=np.int64)
    if (rows<=0).any() or not len(rows): raise ValueError("Empty map cluster")
    draws=np.random.Generator(np.random.PCG64(2711)).integers(0,len(rows),(10000,len(rows)))
    values=100*good[draws].sum(1)/rows[draws].sum(1)
    c=sum((Counter(r) for r in records),Counter())
    if c["changed"]!=c["gained"]+c["lost"]+c["neutral"] or c["candidate_correct"]-c["r3_correct"]!=good.sum():
        raise ValueError("Unpaired final counts")
    return dict(maps=len(rows),counts=dict(c),net=int(good.sum()),difference_pp=100*int(good.sum())/int(rows.sum()),
                paired_ci95_pp=np.quantile(values,[.025,.975]).tolist())


def gates(summaries):
    old,new=(summaries[k] for k in BLOCKS)
    return dict(old_lower_positive=old["overall"]["paired_ci95_pp"][0]>0,
                new_lower_positive=new["overall"]["paired_ci95_pp"][0]>0,
                **{opp+"_new_nonnegative":new["opponents"][opp]["net"]>=0 for opp in OPPONENTS})


def verify_movement_mask(board,rows):
    x,y=rows["pos"].long().T
    step=rows["step"].long()
    n=0
    for d,(dx,dy) in enumerate(((0,-1),(1,0),(0,1),(-1,0)),1):
        tx,ty=x+dx,y+dy
        ok=(tx>=0)&(tx<24)&(ty>=0)&(ty<24)&(rows["feats"][:,3]==0)
        ok=ok & (board[step,5,tx.clamp(0,23),ty.clamp(0,23)]==0)
        allowed=rows["mask"][:,d]
        if (allowed & ~ok).any(): raise ValueError("Archived original mask admitted an unexecutable direction")
        n+=int(allowed.sum())
    return n


@torch.inference_mode()
def score_case(net,path):
    with np.load(path,allow_pickle=False) as z:
        board=torch.from_numpy(z["planes"]); actual=torch.from_numpy(z["played_act"])
        data={k:torch.from_numpy(z[k]) for k in ("step","pos","mask","act","base_act","feats","sdx","sdy")}
        if np.any(z["mstep"]<=0):raise ValueError("Unexpected reset frame")
    prepare_labels(data,24,24)
    result=Counter(legal_direction_options=verify_movement_mask(board,data))
    parent=Counter()
    diffs=0
    previous=data["step"].numpy()
    for first in range(0,len(board),24):
        stop=min(len(board),first+24);lo,hi=np.searchsorted(previous,(first,stop));s=slice(lo,hi)
        logits=net.forward_all(board[first:stop].float()/PLANE_SCALE,data["step"][s].long()-first,
                               data["pos"][s],data["feats"][s].float())[0]
        mask,base,teacher=data["mask"][s],data["base_act"][s],data["act"][s]
        old=played_action(logits,mask,base)
        prob,choice=logits.masked_fill(~mask,-torch.inf).softmax(1).max(1)
        eligible=extra(prob,choice,base)
        new=torch.where(eligible,choice,old)
        change=old!=new
        if not torch.equal(change,eligible) or (change & (old!=base)).any():
            raise ValueError("Additional changes must be direction replacements below the old threshold")
        gain=change & (new==teacher); lost=change & (old==teacher)
        parent.update(decision_counts(old,base,teacher,actual[s]))
        diffs+=int((old!=actual[s]).sum())
        result.update(rows=len(old),changed=int(change.sum()),gained=int(gain.sum()),lost=int(lost.sum()),
                      neutral=int((change & ~gain & ~lost).sum()),r3_correct=int((old==teacher).sum()),
                      candidate_correct=int((new==teacher).sum()),candidate_hurt_correct_v14=int(((new!=teacher)&(base==teacher)).sum()))
    return result,parent,diffs


def run(a):
    limit_threads()
    if a.out.exists():raise FileExistsError(a.out)
    ref=ROOT/"experiments/analysis/r8_warm_20261115/validation.json"
    oldref=ROOT/"experiments/analysis/movement_dagger_20261115/r3_validation.json"
    if (digest(ref),digest(oldref),digest(a.model))!=(REF,REFERENCE,R3):raise ValueError("Changed original inputs")
    reference=json.loads(ref.read_bytes())
    oldrows={(r["seed"],r["side"]):r["counts"] for r in json.loads(oldref.read_bytes())["games"] if r["cohort"]=="mixed"}
    if reference["models"]["r3"]!=R3:raise ValueError("Unexpected archived model")
    paths=(PLAN,"scripts/r3_turn_advice.py","scripts/r3_turn_advice_audit.py","scripts/r3_diagonal.py",
           "scripts/selective_advice_agent.py","scripts/imitate.py","scripts/combat_teacher_counterfactual.py",
           "agents/sherlock/imitation_net.py","agents/sherlock/cnn_model.py","agents/sherlock/imitation_agent.py",
           "agents/sherlock/geometry.py","agents/sherlock/main.py","agents/sherlock/features.py")
    source={p:digest(ROOT/p) for p in paths}
    nets,own=load_heads(a.model)
    if len(nets)!=1 or not own:raise ValueError("One original R3 required")
    result={};all_cases=[];sensitivity=Counter()
    for cohort,maps in BLOCKS.items():
        folder=a.old if cohort=="old_validation" else a.new
        records=[r for r in reference["archives"] if r["cohort"]==cohort]
        if (len(records)!=48 or {(r["seed"],r["side"]) for r in records}!=
                {(seed,side) for seed in maps for side in ("player_0","player_1")}):
            raise ValueError("Incomplete reference cohort")
        by_map={k:Counter() for k in maps};foes={}
        for r in records:
            n,side,opp=r["seed"],r["side"],r["opponent"]
            if foes.setdefault(n,opp)!=opp or opp not in OPPONENTS:raise ValueError("Changed opponent rotation")
            path=folder/f"g{n}_{side}_{opp}.npz"
            if digest(folder/"protocol.json")!=r["protocol"] or digest(path)!=r["sha256"]:raise ValueError("Changed archive")
            c,parent,diffs=score_case(nets[0],path)
            known=r["counts"]
            if (c["rows"]!=known["rows"] or parent["advised_matches"]!=known["r3_correct"] or
                    parent["base_matches"]!=known["v14_correct"] or parent["hurt"]!=known["r3_hurt_correct_v14"]):
                raise ValueError(f"Original R3 decisions differ on {n}/{side}")
            if cohort=="old_validation" and parent!=oldrows[n,side]:raise ValueError("Incomplete old reproduction")
            if cohort=="new_validation":
                if diffs!=known["reconstructed_r3_differs_from_actual"] or parent["parent_played_matches"]!=known["actual_r3_correct"]:
                    raise ValueError("Actual R3 sensitivity differs")
                sensitivity.update(reconstructed_differs_from_actual=diffs,actual_r3_correct=parent["parent_played_matches"])
            if digest(path)!=r["sha256"]:raise ValueError("Archive changed during measurement")
            by_map[n].update(c)
            all_cases.append(dict(cohort=cohort,seed=n,side=side,opponent=opp,sha256=r["sha256"],counts=c,
                                  old_reproduction=parent,baseline_differs_from_recorded=diffs))
        if Counter(foes.values())!=Counter({opp:8 for opp in OPPONENTS}):raise ValueError("Unbalanced map groups")
        result[cohort]=dict(overall=summary(by_map.values()),per_map=by_map,
                            opponents={o:summary(by_map[n] for n in maps if foes[n]==o) for o in OPPONENTS})
    if (sensitivity!=dict(reconstructed_differs_from_actual=164,actual_r3_correct=109591)
            or digest(a.model)!=R3 or any(digest(ROOT/p)!=h for p,h in source.items())):
        raise ValueError("Wrong reconstructed reference or study changed")
    checks=gates(result)
    out=dict(reference=REF,old_reference=REFERENCE,model=R3,source=source,cases=all_cases,cohorts=result,
             recorded_r3=sensitivity,checks=checks,passes=all(checks.values()))
    a.out.parent.mkdir(parents=True,exist_ok=True);publish_json(a.out,out)
    print(json.dumps({k:v["overall"] for k,v in result.items()},indent=2));print(checks,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("model","old","new","out"):p.add_argument("--"+name,type=Path,required=True)
    run(p.parse_args())
