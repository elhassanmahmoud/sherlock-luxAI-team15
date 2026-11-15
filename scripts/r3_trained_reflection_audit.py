"""Measure the three dual-view advisers on the two pre-registered untouched holdouts."""
import argparse
from collections import Counter
import json
from pathlib import Path
import torch

from scripts import r8_warm as warm
from scripts.r8_warm_assess import measure
from scripts.r3_diagonal import TwoViews
from scripts.r3_trained_reflection import CONTROL,R3,control_metadata,provenance
from scripts.selective_advice_agent import load_heads
from scripts.train_combat_advice import publish_json

REFERENCES={
    "old_validation":("experiments/analysis/movement_reflection_20261115/paired_validation.json",
                      "8f927db8b83927899d7dba2eeaf0fad23facba5901e05fe430f59632814857b1"),
    "new_validation":("experiments/analysis/r3_view_consensus_20261115/audit.json",
                      "ebdd5b28421e9d2f1dc8bf963a10c8f80d0d0ae7bd5c2e2533e657019050c6f9")}


def registered_cases(cohort):
    path,expected=REFERENCES[cohort]
    if warm.file_sha(warm.ROOT/path)!=expected: raise ValueError("Different diagonal reference")
    ref=json.loads((warm.ROOT/path).read_bytes())
    if cohort=="old_validation":
        cases=[r for r in ref["games"] if r["cohort"]=="mixed"]
    else:
        cases=ref["cases"]
    table={}
    for r in cases:
        if cohort=="old_validation":
            d=r["reflected"]
            counts={k:d[k] for k in ("advised_matches","helped","hurt","changed","rows")}
        else:
            d=r["measured"]
            counts=dict(advised_matches=d["diagonal_correct"],helped=d["diagonal_helped_v14"],
                        hurt=d["diagonal_hurt_v14"],changed=d["diagonal_changed"],rows=d["rows"])
        table[(r["seed"],r["side"])]=(r["sha256"],counts)
    if len(cases)!=48 or len(table)!=48: raise ValueError("Incomplete historic reference")
    return table


def gates(old,new):
    return {f"{cohort}_against_{opponent}": (c["augmented_correct"]>c[opponent+"_correct"] if cohort=="new"
                                             else c["augmented_correct"]>=c[opponent+"_correct"])
            for cohort,c in (("new",new),("old",old)) for opponent in ("diagonal","control")}


def named_counts(counts):
    # The shared paired assay uses positional model roles internally.
    out={}
    for k,v in counts.items():
        k=k.replace("reconstructed_r3_differs_from_actual","diagonal_differs_from_played")
        k=k.replace("actual_r3","played_single").replace("r3","diagonal").replace("r8","augmented")
        out[k]=v
    for other in ("diagonal","control"):
        if out["augmented_gained_over_"+other]-out["augmented_lost_from_"+other]!=out["augmented_correct"]-out[other+"_correct"]:
            raise ValueError("Paired counts do not add up")
    return out


def audit(a):
    warm.limit_threads()
    if a.out.exists(): raise FileExistsError(a.out)
    reference=control_metadata(a.parent,a.control)
    weights={"r3":a.parent,"control":a.control,"r8":a.model}
    hashes={k:warm.file_sha(v) for k,v in weights.items()}
    if len(set(hashes.values()))!=3: raise ValueError("Models must be distinct")
    train=torch.load(a.model,map_location="cpu",weights_only=True)["reflection_training"]
    expected=dict(parent=R3,control=CONTROL,flipped_updates=512,source=provenance(),
                  **{k:reference[k] for k in ("inputs","counts","replay","support")})
    inputs=dict(replay=warm.identities(warm.index(a.old,"replay")),support=warm.identities(warm.index(a.new,"r8")))
    if expected!=train or train["inputs"]!=inputs: raise ValueError("Augmented fit differs from actually executed control")
    learn_seeds={r["seed"] for block in inputs.values() for r in block}
    nets={}
    for k,path in weights.items():
        head,own=load_heads(path)
        if len(head)!=1 or not own: raise ValueError("One original architecture required")
        nets[k]=TwoViews(head[0])
    cases=[]
    totals={}
    both_maps={}
    src={**provenance(),**{f:warm.file_sha(warm.ROOT/f) for f in ("scripts/r8_warm_assess.py","scripts/r3_trained_reflection_audit.py")}}
    for cohort,folder in (("old_validation",a.old),("new_validation",a.new)):
        records=warm.index(folder,cohort)
        known=registered_cases(cohort)
        if {(r["seed"],r["side"]) for r in records}!=set(known) or len(records)!=48:
            raise ValueError("Unexpected validation cohort")
        totals[cohort]=Counter()
        by_map=both_maps[cohort]={}
        for r in records:
            rawhash,expected=known[(r["seed"],r["side"])]
            if r["seed"] in learn_seeds or r["sha256"]!=rawhash: raise ValueError("Holdout provenance or overlap")
            counts,diag=measure(nets,Path(r["path"]),cohort)
            if (any(diag[k]!=v for k,v in expected.items()) or warm.file_sha(r["path"])!=rawhash):
                raise ValueError(f"Original dual-view result or archive changed: {r['seed']} {r['side']}")
            row=named_counts(counts)
            cases.append(dict(cohort=cohort,**warm.identities([r])[0],counts=row))
            totals[cohort].update(row)
            by_map.setdefault(r["seed"],Counter()).update(row)
    if (totals["old_validation"]["diagonal_correct"],totals["new_validation"]["diagonal_correct"])!=(99182,109672):
        raise ValueError("Original dual-view totals differ")
    if any(warm.file_sha(v)!=hashes[k] for k,v in weights.items()) or any(warm.file_sha(warm.ROOT/k)!=v for k,v in src.items()):
        raise ValueError("Study changed during inference")
    checks=gates(totals["old_validation"],totals["new_validation"])
    result=dict(models=dict(original_diagonal=R3,unaugmented=CONTROL,augmented=hashes["r8"]),training=train,
                references=REFERENCES,totals=totals,per_map=both_maps,cases=cases,checks=checks,passes=all(checks.values()),
                source_sha256=src)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    publish_json(a.out,result)
    print(json.dumps(dict(totals=totals,checks=checks,passes=result["passes"]),indent=2))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("parent","control","old","new","model","out"): cli.add_argument("--"+key,type=Path,required=True)
    audit(cli.parse_args())
