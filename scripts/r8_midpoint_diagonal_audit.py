"""Apply the same three final movement rules to every stored decision in both holdouts."""
import argparse
from collections import Counter
import json
from pathlib import Path

from scripts import r8_warm as warm
from scripts.r3_diagonal import R3,TwoViews,digest
from scripts.r3_trained_reflection_audit import registered_cases
from scripts.r8_midpoint_diagonal import MIDPOINT
from scripts.r8_warm_assess import measure
from scripts.selective_advice_agent import load_heads
from scripts.train_combat_advice import publish_json

SINGLE_REF="b80632ec1f7ad525bf8a469d38f38bbf8f4111acc0ed2a27455df9fe3837f1b9"
PLAN="experiments/analysis/r8_midpoint_diagonal_20261115/PLAN.md"


def gates(old,new):
    a=old["dual_correct"]-old["diagonal_correct"]
    b=new["dual_correct"]-new["diagonal_correct"]
    return dict(old_at_least_diagonal=a>=0,new_at_least_diagonal=b>=0,at_least_one_strict=max(a,b)>0,
                combined_at_least_single=old["dual_correct"]+new["dual_correct"]>=old["single_correct"]+new["single_correct"])


def sources():
    extra=(PLAN,"scripts/r3_trained_reflection_audit.py","scripts/r8_warm_assess.py","scripts/r8_midpoint_diagonal.py",
           "scripts/r8_midpoint_diagonal_audit.py","agents/sherlock/features.py")
    return {**warm.sources(),**{p:digest(warm.ROOT/p) for p in extra}}


def rename(counts):
    result={}
    for k,v in counts.items():
        k=k.replace("reconstructed_r3_differs_from_actual","diagonal_differs_from_played")
        k=k.replace("actual_r3","played_original_r3").replace("original_r3","original_parent")
        k=k.replace("control","single").replace("r3","diagonal").replace("r8","dual")
        result[k]=v
    for ref in ("diagonal","single"):
        if result["dual_gained_over_"+ref]-result["dual_lost_from_"+ref]!=result["dual_correct"]-result[ref+"_correct"]:
            raise ValueError("Inconsistent pairing")
    return result


def audit(a):
    if a.out.exists(): raise FileExistsError(a.out)
    warm.limit_threads()
    reference=warm.ROOT/"experiments/analysis/r8_midpoint_20261115/validation.json"
    if digest(a.mid)!=MIDPOINT or digest(a.r3)!=R3 or digest(reference)!=SINGLE_REF:
        raise ValueError("Unexpected source model or baseline")
    prior=json.loads(reference.read_bytes())
    if prior["model_sha256"]!=MIDPOINT or prior["passes"] is not True: raise ValueError("Unregistered original midpoint")
    singles={(r["cohort"],r["seed"],r["side"]):r for r in prior["archives"]}
    if len(singles)!=96 or len(prior["archives"])!=96: raise ValueError("Incomplete single-view baseline")
    code=sources()
    h_r3,tile_r3=load_heads(a.r3)
    h_mid,tile_mid=load_heads(a.mid)
    if not tile_r3 or not tile_mid or len(h_r3)!=1 or len(h_mid)!=1: raise ValueError("Expected two original solo models")
    nets=dict(r3=TwoViews(h_r3[0]),control=h_mid[0],r8=TwoViews(h_mid[0]))
    totals,cases,by_map={},{},{}
    for cohort,folder in (("old_validation",a.old),("new_validation",a.new)):
        known=registered_cases(cohort)
        records=warm.index(folder,cohort)
        if len(records)!=48 or {(r["seed"],r["side"]) for r in records}!=set(known):
            raise ValueError("Unexpected map/seat selection")
        maps=by_map[cohort]={}
        totals[cohort]=Counter()
        for r in records:
            key=(r["seed"],r["side"])
            old=singles[cohort,*key]
            sha,expected=known[key]
            if old["sha256"]!=sha or r["sha256"]!=sha or r["opponent"]!=old["opponent"]:
                raise ValueError("Changed archive")
            measured,diagonal=measure(nets,Path(r["path"]),cohort)
            c=rename(measured)
            if (any(diagonal[k]!=v for k,v in expected.items())
                    or c["single_correct"]!=old["counts"]["midpoint_correct"]
                    or c["single_hurt_correct_v14"]!=old["counts"]["midpoint_hurt_correct_v14"]
                    or c["rows"]!=old["counts"]["rows"] or digest(r["path"])!=sha):
                raise ValueError(f"Original archived controls differ on {key}")
            cases[cohort,*key]=dict(cohort=cohort,**warm.identities([r])[0],counts=c)
            maps.setdefault(r["seed"],Counter()).update(c)
            totals[cohort].update(c)
    checks=gates(totals["old_validation"],totals["new_validation"])
    if digest(a.mid)!=MIDPOINT or digest(a.r3)!=R3 or digest(reference)!=SINGLE_REF or sources()!=code:
        raise ValueError("Source changed during computation")
    result=dict(models=dict(diagonal_r3=R3,single_midpoint=MIDPOINT,dual_midpoint=MIDPOINT),single_reference=SINGLE_REF,
                source_sha256=code,cases=list(cases.values()),totals=totals,per_map=by_map,checks=checks,passes=all(checks.values()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    publish_json(a.out,result)
    print(json.dumps(dict(totals=totals,checks=checks,passes=result["passes"]),indent=2))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for k in ("r3","mid","old","new","out"): cli.add_argument("--"+k,type=Path,required=True)
    audit(cli.parse_args())
