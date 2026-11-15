"""Admission, single-worker games and paired assessment for the registered R7 study."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from scripts import final_battle_assess as assess
from scripts import final_battle_compare as runner
from scripts.final_battle_select import OPPONENTS, SEATS
from scripts.train_combat_advice import publish_json

R3, R5 = assess.DISTILL_MODEL, assess.OWN_COMMAND_MODEL
ENGINE_DIGEST = "551a263ede77ef6d64c0cac6faa02b5990eba3134942118783bb28cbdfb92b80"
ASSESS_FILES = {"final_battle_assess.py": "b5a535a3aa665203edc5d0987ce6c4965998e0cfc34c1060b768a2fc383fa4ff",
                "final_battle_select.py": "8fbb96e068fdf5c581766202272b061987efe5bed6b6b337dc31f042a1e831f4",
                "residual_ensemble_compare.py": "525c58d23f3245e523d2416cfc7dc452d393d83d416a4509e6fb332fe5ce463a"}
MODEL_FILES = {"r3": "r3_soft.pth", "r5": "r5_own_command.pth"}
FROZEN_TRAINER = {"scripts/combined_movement.py": "7c5f2c5fb0300f0bcd5148ed511d2d65660fdad1ecf1b00ae64049b3399d5ecc",
                  "scripts/imitate.py": "c7f14b68d429ec66999bea35193980b5a8b0b8468b61eac7cfa965f3edcd2199"}
CONTROL_REPORTS = {"r3": "6d2cefcc03703596b44b87d0c611e44f015db2ba0fe6fcb708d9e1a1ec2ba523",
                   "r5": "aa7859ba3255de1faf1b4b5081df789d2842a7d79d6c90df94d6eb32f85b961c"}


def blocks(stage):
    if stage == "screen":
        maps = range(7284000, 7284016)
        return {"r7": (maps, (*OPPONENTS, "v14")), "v14": (maps, OPPONENTS),
                "r3": (maps, OPPONENTS), "r5": (maps, OPPONENTS)}
    if stage == "confirm":
        maps = range(7284100,7284160)
        return {"v14": (maps, OPPONENTS), "r7": (maps, OPPONENTS),
                "direct": (range(7284200,7284260), ("v14",))}
    raise ValueError(f"Unknown stage {stage}")


def verify_gate(mixed, recorded, passed):
    r3, r5, r7 = (mixed[k] for k in ("r3","r5","r7"))
    checks = {"net_at_least_r5": r7["net"] >= r5["net"], "hurt_at_most_r3": r7["hurt"] <= r3["hurt"],
              "one_strict": r7["net"] > r5["net"] or r7["hurt"] < r3["hurt"]}
    if (r5["net"],r3["hurt"]) != (17481,2343) or checks != recorded or not all(checks.values()) or passed is not True:
        raise ValueError("Actual registered R7 offline selection did not pass")


def admission(a):
    raw = a.audit.read_bytes()
    digest = sha256(raw).hexdigest()
    if digest != a.audit_sha256:
        raise ValueError("Different offline audit receipt")
    report = json.loads(raw)
    h = runner.digest(a.model)
    if (h != report["candidate_sha256"] or h in {R3, R5, assess.R2_MODEL, assess.V14_SHA}
            or report["control_sha256"] != {"r2": assess.R2_MODEL, "r3": R3, "r5": R5}
            or report["control_reports_sha256"] != CONTROL_REPORTS
            or any(report["source_sha256"].get(f) != v for f,v in FROZEN_TRAINER.items())):
        raise ValueError("Different model, fit sources, controls or control receipts")
    for name, model_hash in (("r3",R3),("r5",R5)):
        if runner.digest(a.controls/MODEL_FILES[name]) != model_hash:
            raise ValueError(f"{name} control weights changed")
    for cohort, seeds, rows in (("original",range(7271032,7271040),51048), ("mixed",range(7272200,7272224),156243)):
        data = [r for r in report["games"] if r["cohort"] == cohort]
        roster = {(seed,s) for seed in seeds for s in SEATS}
        if {(r["seed"],r["side"]) for r in data} != roster or len(data) != len(roster):
            raise ValueError("Unpaired or duplicate archived maps")
        for arm in ("r2","r3","r5","r7"):
            c = report["validation"][cohort][arm]
            for name in ("rows","helped","hurt","history_rows","history_helped","history_hurt"):
                if sum(r["counts"][arm][name] for r in data) != c[name]:
                    raise ValueError("Offline summary differs from individual archive measurements")
            if (c["rows"] != rows or c["net"] != c["helped"]-c["hurt"]
                    or c["history_net"] != c["history_helped"]-c["history_hurt"]
                    or (cohort == "mixed" and c["history_rows"] != 147228)):
                raise ValueError("Unexpected decision populations or teacher gains")
    if len(report["games"]) != 64:
        raise ValueError("Unexpected extra archive cohort")
    verify_gate(report["validation"]["mixed"], report["offline_checks"], report["passes_offline_gate"])
    for name,expected in ASSESS_FILES.items():
        if runner.digest(Path(__file__).with_name(name)) != expected:
            raise ValueError(f"Different result verifier: {name}")
    return {"offline_sha256": digest, "r7_sha256": h, "study_sources":
            {**ASSESS_FILES, "combined_movement_games.py": runner.digest(Path(__file__))}}


def config(a, stage, arm):
    seeds, opponents = blocks(stage)[arm]
    model = None if arm == "v14" else (a.controls/MODEL_FILES[arm] if arm in MODEL_FILES else a.model)
    return SimpleNamespace(candidate="v14" if arm == "v14" else "selective_movement", model=model,
                           opponents=",".join(opponents), first=seeds.start, maps=len(seeds))


def check_live_manifest(m, pin):
    environment = m.get("environment", {})
    def canonical_hash(data):
        return sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    source_hash = canonical_hash(m["sources"])
    expected = assess.OWN_SOURCE_DIGESTS.get((m["candidate"], "kaggle3" in m["opponents"]))
    if (m["weights"] != assess.V14_SHA or m["model"] != pin or source_hash != expected
            or canonical_hash(environment.get("engine", {})) != ENGINE_DIGEST):
        raise ValueError("Wrong frozen runtime, policy, V14 or student")


def registered_run(a,stage,arm,pins):
    c = config(a,stage,arm)
    seeds, opponents = blocks(stage)[arm]
    result = assess.load_run(a.out/stage/arm,c.candidate,seeds,opponents)
    model_hash = {"v14":None,"r3":R3,"r5":R5}.get(arm,pins["r7_sha256"])
    check_live_manifest(result.manifest,model_hash)
    for row in result.games.values():
        counts = row.get("study",{})
        if counts.get("changed_unit_orders",0) != counts.get("movement",0):
            raise ValueError("A non-movement substitution occurred")
    return result


def paired(a,stage,pins):
    runs = {k: registered_run(a,stage,k,pins) for k in blocks(stage)}
    ref, candidate = runs["v14"], runs["r7"]
    direct = runs.get("direct",candidate)
    maps = blocks(stage)["r7"][0]
    phase = assess.Phase(ref,candidate,direct,maps,blocks(stage).get("direct",(maps,))[0])
    assess.compatible(ref,candidate)
    assess.compatible(candidate,direct)
    assess.own_command_runtime(phase,ref)
    result = assess.summarize(phase,stage)
    if stage == "screen":
        result["selection_controls"] = {}
        for name in ("r3","r5"):
            ctrl = runs[name]
            assess.compatible(ref,ctrl)
            assess.compatible(ctrl,candidate,compare_checkpoint=False)
            assess.own_command_runtime(phase,ctrl)
            by_opponent, external = assess.external_comparison(ctrl,candidate,maps,f"{name}_wins")
            result["selection_controls"][name] = {**external,"by_opponent":by_opponent,
                                                   "files":ctrl.hashes,"model":ctrl.manifest["model"]}
            result["gates"][f"external_at_least_{name}"] = external["net_wins"] >= 0
        result["game_gates_pass"] = all(result["gates"].values())
    result.update(pins,environment=ref.manifest["environment"],bootstrap={"seed":2711,"draws":10000,
                  "unit":"map with both seats and, externally, both opponents","interval":"95% percentile"})
    return result


def checked_selection(a,pins):
    fresh = paired(a,"screen",pins)
    receipt = a.out/"screen/assessment.json"
    if not fresh["game_gates_pass"] or not receipt.is_file() or json.loads(receipt.read_text()) != fresh:
        raise ValueError("Independent confirmation requires a complete, accepted and verified selection")
    return fresh


def execute(a):
    pins = admission(a)
    selected = checked_selection(a,pins) if a.stage == "confirm" else None
    if a.operation == "assess":
        if a.arm:
            raise ValueError("Assess the complete stage")
        result = paired(a,a.stage,pins)
        if selected is not None:
            if selected["environment"] != result["environment"]:
                raise ValueError("Runtime changed after selection")
            result["screen_assessment_sha256"] = runner.digest(a.out/"screen/assessment.json")
        dest = a.out/a.stage/"assessment.json"
        if dest.exists():
            if json.loads(dest.read_text()) != result:
                raise ValueError("Published assessment differs")
        else:
            publish_json(dest,result)
        print(json.dumps(result,indent=2))
        return
    arms = blocks(a.stage)
    if a.arm and a.arm not in arms:
        raise ValueError(f"Unregistered arm {a.arm} for {a.stage}")
    for name in ([a.arm] if a.arm else arms):
        c = config(a,a.stage,name)
        output = a.out/a.stage/name
        expected = {"v14":None,"r3":R3,"r5":R5}.get(name,pins["r7_sha256"])
        manifest = runner.contract(c)
        check_live_manifest(manifest,expected)
        if selected and selected["environment"] != manifest["environment"]:
            raise ValueError("Runtime changed after selection")
        if not (output/"completed.json").exists():
            args = ["--candidate",c.candidate,"--opponents",c.opponents,"--first",str(c.first),
                    "--maps",str(c.maps),"--workers","1","--out",str(output)]
            if c.model:
                args += ["--model",str(c.model)]
            subprocess.run([sys.executable,"-B","-u","-m","scripts.final_battle_compare",*args],
                           cwd=runner.ROOT,check=True)
        finished = registered_run(a,a.stage,name,pins)
        if finished.manifest != manifest:
            raise ValueError("Finished run differs from frozen start")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation",choices=("play","assess"))
    parser.add_argument("stage",choices=("screen","confirm"))
    parser.add_argument("--arm",choices=("r7","v14","r3","r5","direct"))
    for key in ("out","model","controls","audit"):
        parser.add_argument("--"+key,type=Path,required=True)
    parser.add_argument("--audit-sha256",required=True)
    args = parser.parse_args()
    for key in ("out","model","controls","audit"):
        setattr(args,key,getattr(args,key).resolve())
    execute(args)
