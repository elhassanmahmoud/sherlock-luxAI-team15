"""Play a prespecified R8 panel using the frozen R3 runtime after its fitted checkpoint passes diagnosis."""
import argparse
from collections import Counter
from functools import partial
from hashlib import sha256
from importlib import metadata, util
import json
import os
from pathlib import Path
import platform
from types import SimpleNamespace

from scripts import final_battle_assess as judge, final_battle_compare as game
from scripts.collect_combat_advice import opponent_for
from scripts.final_battle_select import OPPONENTS, SEATS
from scripts.train_combat_advice import publish_json

R3 = judge.DISTILL_MODEL
OLD_REPORT = "6d2cefcc03703596b44b87d0c611e44f015db2ba0fe6fcb708d9e1a1ec2ba523"
PROTOCOLS = {"old_validation":"50bf0bb810f7b913acce8940937d335ebf180bc796457dcf880ffa6743ec2724",
             "new_validation":"3476e80f57ff23f76fb4d8aa00269e647116ca9c468c0d2d0f6278af85567a03"}
DIAGNOSIS = {"old_validation":range(7272200,7272224),"new_validation":range(7287100,7287124)}
RUNTIME = {("v14",True):"42975cd50a804f807ba25f066f7faeadc52243789b362960526fddb1041e1f8c",
           ("selective_movement",True):"af7f904d3925fe573c85aa9e4405ca426231f0dcbbc3be7e99209ffa475911b9",
           ("selective_movement",False):"1914c045574d83cffae00de8562943ef5d3abb841a0577925c30752cd3d25e4a"}
EXTRA = "3b7cfffb85785fbc3b67625beed2f5f176c2bdebe0e721d576d94c1d8359f6ff"
ENGINE = "551a263ede77ef6d64c0cac6faa02b5990eba3134942118783bb28cbdfb92b80"


def blocks(stage):
    if stage=="screen":
        maps=range(7288000,7288016)
        return {"r8":(maps,(*OPPONENTS,"v14")),**{k:(maps,OPPONENTS) for k in ("v14","r3","control")}}
    if stage=="confirm":
        maps=range(7288100,7288160)
        return {"v14":(maps,OPPONENTS),"r8":(maps,OPPONENTS),"direct":(range(7288200,7288260),("v14",))}
    raise ValueError(stage)


def combined_sha(mapping):
    return sha256(json.dumps(mapping,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def verified_offline(report):
    if len(report["archives"])!=96 or set(report["per_map"])!=set(DIAGNOSIS) or set(report["totals"])!=set(DIAGNOSIS):
        raise ValueError("Expected two complete diagnosis panels")
    for label,seeds in DIAGNOSIS.items():
        arrived=set()
        totals={s:Counter() for s in seeds}
        for r in (e for e in report["archives"] if e["cohort"]==label):
            key=(r["seed"],r["side"])
            c=r["counts"]
            if (key in arrived or key[0] not in seeds or key[1] not in SEATS or
                    r["opponent"]!=opponent_for(key[0]) or r["protocol"]!=PROTOCOLS[label] or
                    len(r["sha256"])!=64 or not c["rows"] or any(type(x) is not int or x<0 for x in c.values())):
                raise ValueError("Invalid offline seat or measurement")
            if any(c[k+"_correct"]>c["rows"] for k in ("v14","r3","control","r8")):
                raise ValueError("Invalid teacher counts")
            for arm in ("r3","control"):
                if c["r8_gained_over_"+arm]-c["r8_lost_from_"+arm]!=c["r8_correct"]-c[arm+"_correct"]:
                    raise ValueError("Offline paired counts disagree")
            arrived.add(key)
            totals[key[0]].update(c)
        if arrived!={(s,side) for s in seeds for side in SEATS}:
            raise ValueError("Missing or duplicate diagnostic seat")
        accumulated=Counter()
        for c in totals.values():
            accumulated.update(c)
        if ({str(s):dict(c) for s,c in totals.items()}!=report["per_map"][label]
                or dict(accumulated)!=report["totals"][label]):
            raise ValueError("Offline totals differ from the actual measured seats")
    old,new=(report["totals"][k] for k in DIAGNOSIS)
    checks=dict(new_beats_r3=new["r8_correct"]>new["r3_correct"],
                new_beats_warm_control=new["r8_correct"]>new["control_correct"],
                old_at_least_r3=old["r8_correct"]>=old["r3_correct"])
    if ((old["rows"],old["r3_correct"],old["v14_correct"],old["r3_hurt_correct_v14"])!=(156243,98938,82581,2343)
            or report["old_reference"]!=OLD_REPORT or
            report["checks"]!=checks or not all(checks.values()) or report["passes_offline_gate"] is not True):
        raise ValueError("R8 did not qualify on both frozen panels")


def admission(a):
    data=a.audit.read_bytes()
    if sha256(data).hexdigest()!=a.audit_sha256:
        raise ValueError("Different reviewed R8 fit/diagnosis receipt")
    report=json.loads(data)
    verified_offline(report)
    paths={"r3":a.r3,**{k:a.models/(k+".pth") for k in ("control","r8")}}
    models={k:game.digest(p) for k,p in paths.items()}
    if models!=report["models"] or models["r3"]!=R3 or len(set(models.values()))!=3:
        raise ValueError("Swapped, modified or duplicate R8, warm control or R3 checkpoint")
    observed=report["source_sha256"]
    if not {"scripts/r8_warm.py","scripts/r8_warm_assess.py","scripts/imitate.py"}.issubset(observed):
        raise ValueError("Incomplete fit/audit source binding")
    for f,digest in observed.items():
        path=(a.fit_root/f).resolve()
        if not path.is_relative_to(a.fit_root.resolve()) or game.digest(path)!=digest:
            raise ValueError("Changed fit or audit source: "+f)
    return dict(models=models,audit_sha256=a.audit_sha256,fit_sources_sha256=combined_sha(observed),
                study_sha256=game.digest(Path(__file__)))


def runtime():
    paths=set((game.ROOT/"agents").rglob("*.py"))|set((game.ROOT/"lux").glob("*.py"))
    paths.update(game.ROOT/"scripts"/p for p in ("__init__.py","protocol.py","variants.py","fetch_kaggle3.py",
                 "train_combat_advice.py","final_battle_assess.py","final_battle_select.py","residual_ensemble_compare.py"))
    extra=combined_sha({str(p.relative_to(game.ROOT)):game.digest(p) for p in paths})
    env=Path(util.find_spec("luxai_s3").origin).parent
    eng=combined_sha({p.name:game.digest(p) for p in env.glob("*.py")})
    if extra!=EXTRA or eng!=ENGINE:
        raise ValueError("Different supporting sources, paired statistics or game engine")
    return dict(support=extra,engine=eng,python=platform.python_version(),machine=platform.machine(),
                platform=platform.system(),versions={k:metadata.version(k) for k in ("numpy","scipy","jax","jaxlib","torch","luxai-s3")},
                flags={k:os.getenv(k) for k in ("JAX_PLATFORMS","XLA_FLAGS","CUDA_VISIBLE_DEVICES","PYTHONHASHSEED")})


def prepared(a,stage,arm):
    seeds,foes=blocks(stage)[arm]
    model={"v14":None,"r3":a.r3,"control":a.models/"control.pth","r8":a.models/"r8.pth","direct":a.models/"r8.pth"}[arm]
    return SimpleNamespace(candidate="v14" if model is None else "selective_movement",model=str(model) if model else None,
                           first=seeds.start,maps=len(seeds),opponents=",".join(foes),out=a.out/stage/arm,workers=1)


def contract(c, *, a,arm):
    pins=admission(a)
    m=game.contract(c)
    model=None if arm=="v14" else pins["models"]["r8" if arm=="direct" else arm]
    if (m["weights"]!=judge.V14_SHA or m["model"]!=model or
            combined_sha(m["sources"])!=RUNTIME[m["candidate"],"kaggle3" in m["opponents"]]):
        raise ValueError("Changed reviewed game source, opponent, V14 or arm weights")
    return dict(m,arm=arm,admission=pins,environment=runtime())


def load(a,stage,arm):
    c=prepared(a,stage,arm)
    current=contract(c,a=a,arm=arm)
    run=judge.load_run(c.out,c.candidate,*blocks(stage)[arm])
    if run.manifest!=current or any(r["study"].get("movement",0)!=r["study"].get("changed_unit_orders",0)
                                     for r in run.games.values()):
        raise ValueError("Invalid completed arm or unexpected SAP change")
    return run


def control_gates(r3,control):
    return dict(external_beats_r3=r3["external"]["net_wins"]>0,
                external_beats_warm_control=control["external"]["net_wins"]>0,
                solution_at_least_r3=r3["by_opponent"]["solution92"]["net_wins"]>=0)


def report(a,stage):
    runs={arm:load(a,stage,arm) for arm in blocks(stage)}
    cand,ref=runs["r8"],runs["v14"]
    direct=runs.get("direct",cand)
    maps=blocks(stage)["r8"][0]
    judge.compatible(ref,cand)
    judge.compatible(cand,direct)
    phase=judge.Phase(ref,cand,direct,maps,blocks(stage).get("direct",(maps,))[0])
    result=judge.summarize(phase,stage)
    if stage=="screen":
        controls={}
        for arm in ("r3","control"):
            judge.compatible(runs[arm],cand,compare_checkpoint=False)
            by,external=judge.external_comparison(runs[arm],cand,maps,arm+"_wins")
            controls[arm]=dict(by_opponent=by,external=external,files=runs[arm].hashes)
        result["selection_controls"]=controls
        result["gates"].update(control_gates(controls["r3"],controls["control"]))
        result["game_gates_pass"]=all(result["gates"].values())
    result.update(candidate="r8",admission=cand.manifest["admission"],environment=cand.manifest["environment"],
                  bootstrap={"unit":"whole map, both seats and external opponents","seed":2711,"draws":10000})
    return result


def verified_selection(a):
    fresh=report(a,"screen")
    path=a.out/"screen/assessment.json"
    if not fresh["game_gates_pass"] or not path.is_file() or json.loads(path.read_bytes())!=fresh:
        raise ValueError("Independent games require the actual nominated and archived screen")
    return game.digest(path)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation",choices=("play","assess"))
    p.add_argument("stage",choices=("screen","confirm"))
    p.add_argument("--arm",choices=("r8","control","v14","r3","direct"))
    p.add_argument("--audit-sha256",required=True)
    for flag in ("audit","r3","models","fit-root","out"):
        p.add_argument("--"+flag,type=Path,required=True)
    a=p.parse_args()
    for key in ("audit","r3","models","fit_root","out"):
        setattr(a,key,getattr(a,key).resolve())
    admission(a)
    selection=verified_selection(a) if a.stage=="confirm" else None
    if a.operation=="assess":
        if a.arm:
            p.error("Assess the whole stage")
        result=report(a,a.stage)
        if selection:
            result["screen_sha256"]=selection
        path=a.out/a.stage/"assessment.json"
        if path.exists():
            if json.loads(path.read_bytes())!=result:
                raise ValueError("Changed result file")
        else:
            publish_json(path,result)
        print(json.dumps(result,indent=2))
        return
    if a.arm and a.arm not in blocks(a.stage):
        p.error("Unknown arm for stage")
    for arm in ([a.arm] if a.arm else blocks(a.stage)):
        c=prepared(a,a.stage,arm)
        c.out.mkdir(parents=True,exist_ok=True)
        if not (c.out/"completed.json").exists():
            if (c.out/"games.jsonl").exists() and not (c.out/"manifest.json").exists():
                raise ValueError("Game evidence lacks its original source binding")
            game.run(c,get_contract=partial(contract,a=a,arm=arm))
        load(a,a.stage,arm)


if __name__=="__main__":
    main()
