"""Evaluate the three frozen movement advisers on exactly the same stored inputs."""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np
import torch

from scripts import imitate
from scripts.collect_combat_advice import file_sha
from scripts.experiment import limit_threads
from scripts.r3_diagonal import REFERENCE, decision_counts, played_action
from scripts.r8_warm import ARMS, BLOCKS, R3, ROOT, SEED, UPDATES, identities, index, sources
from scripts.selective_advice_agent import load_heads
from scripts.train_combat_advice import publish_json


def check_fits(paths,old,new):
    replay = identities(index(old,"replay"))
    controls = {}
    for name,path in paths.items():
        checkpoint = torch.load(path,map_location="cpu",weights_only=True)
        m = checkpoint["warm_training"]
        expected = dict(kind="r8_dagger_warm_v1",arm=name,parent_sha256=R3,seed=SEED,steps=UPDATES,lr=.0001,
                        optimizer="AdamW",weight_decay=.0001,clip=1.,sap_target_weight=.5,movement_kl_weight=.5,
                        movement_temperature=2.,sources=sources())
        if (any(m[k]!=value for k,value in expected.items()) or m["inputs"]["replay"] != replay
                or m["inputs"]["support"]!=identities(index(old if name=="control" else new,name))
                or m["counts"]["updates"]!=UPDATES or m["counts"]["policy_adam_steps"]!=UPDATES
                or m["counts"]["rows"]!=256*UPDATES):
            raise ValueError("Wrong training inputs, settings or optimizer updates: "+name)
        for half in ("replay","support"):
            counts=m[half]
            if (counts["sampled_rows"]!=128*UPDATES or len(counts["sampled_rows_by_archive"])!=96
                    or sum(counts["sampled_rows_by_archive"])!=128*UPDATES
                    or any(x<=0 for x in counts["sampled_rows_by_archive"])):
                raise ValueError("Unexpected archive coverage: "+name)
        controls[name] = {k:m[k] for k in ("device","torch","numpy","python","replay")}
    if controls["r8"]!=controls["control"]:
        raise ValueError("Warm starts differ in environment or actual common replay draw")
    return controls["r8"]


@torch.inference_mode()
def measure(nets,path,cohort):
    with np.load(path,allow_pickle=False) as z:
        boards=torch.from_numpy(z["planes"])
        rows={k:torch.from_numpy(z[k]) for k in ("step","mask","pos","feats","act","base_act","sdx","sdy")}
        played=torch.from_numpy(z["played_act"])
    imitate.prepare_labels(rows,24,24)
    steps=rows["step"].numpy()
    result=Counter()
    parent=Counter()
    for first in range(0,len(boards),24):
        stop=min(len(boards),first+24)
        span=slice(*np.searchsorted(steps,(first,stop)))
        board=boards[first:stop].float()/imitate.PLANE_SCALE
        inv=rows["step"][span].long()-first
        pos,feats=rows["pos"][span],rows["feats"][span].float()
        base,mask,teacher=rows["base_act"][span],rows["mask"][span],rows["act"][span]
        actual=played[span]
        commands={}
        for name,net in nets.items():
            logits=net.forward_all(board,inv,pos,feats)[0]
            issued=played_action(logits,mask,base)
            commands[name]=issued
            correct=issued==teacher
            result[name+"_correct"]+=int(correct.sum())
            result[name+"_hurt_correct_v14"]+=int(((base==teacher) & ~correct).sum())
            if name=="r3":
                parent.update(decision_counts(issued,base,teacher,actual))
        result["rows"]+=len(teacher)
        result["v14_correct"]+=int((base==teacher).sum())
        for name in ("r3","control"):
            a,b=commands[name]==teacher,commands["r8"]==teacher
            result["r8_gained_over_"+name]+=int((~a & b).sum())
            result["r8_lost_from_"+name]+=int((a & ~b).sum())
        if cohort=="new_validation":
            result["actual_r3_correct"]+=int((actual==teacher).sum())
            result["reconstructed_r3_differs_from_actual"]+=int((commands["r3"]!=actual).sum())
            a,b=actual==teacher,commands["r8"]==teacher
            result["r8_gained_over_actual_r3"]+=int((~a & b).sum())
            result["r8_lost_from_actual_r3"]+=int((a & ~b).sum())
    return result,parent


def gates(old,new):
    return dict(new_beats_r3=new["r8_correct"]>new["r3_correct"],
                new_beats_warm_control=new["r8_correct"]>new["control_correct"],
                old_at_least_r3=old["r8_correct"]>=old["r3_correct"])


def audit(a):
    limit_threads()
    if a.out.exists():
        raise FileExistsError(a.out)
    ref=ROOT/"experiments/analysis/movement_dagger_20261115/r3_validation.json"
    paths={"r3":a.parent, **{arm:a.models/(arm+".pth") for arm in ARMS}}
    digests={k:file_sha(p) for k,p in paths.items()}
    if digests["r3"]!=R3 or file_sha(ref)!=REFERENCE or len(set(digests.values()))!=len(paths):
        raise ValueError("Changed parent, historical counts or identical inputs")
    common=check_fits({k:paths[k] for k in ARMS},a.old,a.new)
    known={(r["seed"],r["side"]):r["counts"] for r in json.loads(ref.read_bytes())["games"] if r["cohort"]=="mixed"}
    nets={}
    for k,p in paths.items():
        heads, own_tile=load_heads(p)
        if len(heads)!=1 or not own_tile:
            raise ValueError("Expected one registered R3-compatible movement model")
        nets[k]=heads[0]
    by_map,totals,sits={},{},[]
    for cohort,d in (("old_validation",a.old),("new_validation",a.new)):
        by_map[cohort]={seed:Counter() for seed in BLOCKS[cohort]}
        for r in index(d,cohort):
            counts,parent=measure(nets,Path(r["path"]),cohort)
            if (cohort=="old_validation" and dict(parent)!=known[r["seed"],r["side"]]) or file_sha(r["path"])!=r["sha256"]:
                raise ValueError("Historic R3 reproduction or archive identity failed")
            by_map[cohort][r["seed"]].update(counts)
            sits.append(dict(cohort=cohort,**identities([r])[0],counts=dict(counts)))
        total=Counter()
        for c in by_map[cohort].values():
            total.update(c)
        totals[cohort]=total
    checks=gates(totals["old_validation"],totals["new_validation"])
    if any(file_sha(p)!=digests[k] for k,p in paths.items()):
        raise ValueError("Model changed during offline comparison")
    output=dict(models=digests,old_reference=REFERENCE,common_replay_and_runtime=common,per_map=by_map,
                totals=totals,archives=sits,checks=checks,passes_offline_gate=all(checks.values()),
                source_sha256={**sources(),"scripts/r8_warm_assess.py":file_sha(Path(__file__))})
    a.out.parent.mkdir(parents=True,exist_ok=True)
    publish_json(a.out,output)
    print(json.dumps({"totals":totals,"checks":checks,"passes":all(checks.values())},indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ("parent","models","old","new","out"):
        p.add_argument("--"+flag,type=Path,required=True)
    audit(p.parse_args())
