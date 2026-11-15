"""Play or assess the preregistered R8 midpoint panel using the original R3 game runner.

python -B -m scripts.r8_midpoint_games check screen --repo PROJECT --out RESULTS
python -B -u -m scripts.r8_midpoint_games run screen --repo PROJECT --out RESULTS
python -B -u -m scripts.r8_midpoint_games run confirm --repo PROJECT --out RESULTS
"""
import argparse
from collections import Counter
import fcntl
from hashlib import sha256
from importlib import metadata, util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from types import SimpleNamespace

from scripts import final_battle_assess as judge, final_battle_compare as game
from scripts.final_battle_select import OPPONENTS, SEATS

ROOT = game.ROOT
STUDY = Path("experiments/analysis/r8_midpoint_20261115")
IM = Path("experiments/imitation")
R3 = Path("experiments/candidates/movement_dagger_20261115/r3_soft.pth")
WARM = IM / "final_20261115_r8_warm"
MID = IM / "final_20261115_r8_midpoint"
ARCHIVES = {"old_validation": (7272200, IM/"final_20261115_movement_dagger"),
            "new_validation": (7287100, IM/"final_20261115_r3_context")}
MODELS = {"r3": judge.DISTILL_MODEL, "control": "a5755fb1d4a006a95769cb7f19bd38401ffcb42d0058b5cb4f88a9fc7ef5ea32",
          "r8": "93046242f41e16a5e355bc75836b1630816d174890abb804b49969b49893c532",
          "midpoint": "51a52f0453d5ac8e9a4ea70b3792572356761054cb2890520005160f77097cf2"}
FIT_SHA = "3214bec51aa4784472bfb724b923e0ffd7bedc9a3d2da6c9185f34750b875308"
AUDIT_SHA = "b80632ec1f7ad525bf8a469d38f38bbf8f4111acc0ed2a27455df9fe3837f1b9"
PARENT_SHA = "3f05bde9320d9c718e404d2280590f76ab5de823c9fdea594f564433bbcc54de"
PLAN_SHA = "7296f009f0eea131191de4c7a7631cce74f358d39de5d6a793b18decb71d3d63"
HIST = {"v14":"807963c7ebe4b278c7f85e72f8e71978c3438070311ef92e1e60871817e6d42c",
        "r3":"cb904ef4d18ddbb6f05afc7092ba2dd5c86d63724c0b6193eb244c78173c49fd",
        "direct":"db650772a8858bb0cfc2828b7445d8c961bef8f5e3c1516055aec068b5f657b8"}
ENGINE = "551a263ede77ef6d64c0cac6faa02b5990eba3134942118783bb28cbdfb92b80"
SUPPORT = "fb1e9c1e55c2707a362a6ee08b6807fe528629d8bce8d2b77dbc77d0fb90691e"


def checked(path, expected):
    if game.digest(path) != expected:
        raise ValueError(f"Changed artifact: {path}")
    return expected


def hash_mapping(mapping):
    return sha256(json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def seat_totals(parent, audit, repo):
    def indexed(rows):
        return {(r["cohort"], r["seed"], r["side"]): r for r in rows}
    old = indexed(parent["archives"])
    new = indexed(audit["archives"])
    keys = {(c, s, side) for c,(first, _) in ARCHIVES.items() for s in range(first, first+24) for side in SEATS}
    if len(parent["archives"]) != 96 or len(audit["archives"]) != 96 or set(old) != keys or set(new) != keys:
        raise ValueError("Expected both seats on every registered diagnostic map")
    out = {}
    for cohort, (_, directory) in ARCHIVES.items():
        protocol = game.digest(repo/directory/"protocol.json")
        totals, parent_totals = Counter(), Counter()
        for key in sorted(k for k in keys if k[0] == cohort):
            p, r = old[key], new[key]
            if any(p[k] != r[k] for k in ("opponent","protocol","sha256")) or protocol != r["protocol"]:
                raise ValueError(f"Different archive or protocol on {key}")
            checked(repo/directory/f"g{key[1]}_{key[2]}_{r['opponent']}.npz",r["sha256"])
            a, b = p["counts"], r["counts"]
            if any(a[k] != b[k] for k in a.keys() & b.keys()):
                raise ValueError(f"Parent reconstruction differs on {key}")
            for model in ("r3","control"):
                if b["midpoint_correct"] - b[model+"_correct"] != b["midpoint_gained_over_"+model] - b["midpoint_lost_from_"+model]:
                    raise ValueError(f"Inconsistent paired teacher counts on {key}")
            totals.update(b)
            parent_totals.update(a)
        if dict(totals) != audit["totals"][cohort] or dict(parent_totals) != parent["totals"][cohort]:
            raise ValueError(f"Seat totals disagree on {cohort}")
        if totals["midpoint_correct"] <= totals["r3_correct"] or audit["checks"][cohort] is not True:
            raise ValueError(f"Midpoint did not qualify on {cohort}")
        out[cohort] = {k:totals[k] for k in ("rows","r3_correct","midpoint_correct")}
    return out


def admission(repo):
    checked(ROOT/STUDY/"PLAN.md",PLAN_SHA)
    checked(repo/MID/"validation.json",AUDIT_SHA)
    checked(repo/WARM/"validation.json",PARENT_SHA)
    parent = json.loads((repo/WARM/"validation.json").read_bytes())
    audit = json.loads((repo/MID/"validation.json").read_bytes())
    models = {k:checked(repo/path, MODELS[k]) for k,path in (
        ("control",WARM/"control.pth"),("r8",WARM/"r8.pth"),("r3",R3),("midpoint",MID/"midpoint.pth"))}
    parents = {k:models[k] for k in ("control","r8","r3")}
    if (audit["parents"] != parents or parent["models"] != parents or audit["model_sha256"] != models["midpoint"]
            or audit["parent_audit"] != PARENT_SHA or audit["source_sha256"] != FIT_SHA or audit["passes"] is not True):
        raise ValueError("Archived fit, model and parent identity disagree")
    for name, digest in {**parent["source_sha256"], "scripts/r8_midpoint.py":FIT_SHA}.items():
        checked(ROOT/"fit_sources"/name,digest)
    return dict(admitted=seat_totals(parent,audit,repo),models=models,audit=AUDIT_SHA,parent=PARENT_SHA,
                fit_sources=hash_mapping(parent["source_sha256"]),midpoint_source=FIT_SHA,plan=PLAN_SHA)


def blocks(stage):
    if stage == "screen":
        ext = direct = range(7170230,7170246)
        return {"midpoint":(ext,OPPONENTS),"v14":(ext,OPPONENTS),"r3":(ext,OPPONENTS),"direct":(direct,("v14",))}
    if stage == "confirm":
        ext = range(7170300,7170360)
        return {"midpoint":(ext,OPPONENTS),"v14":(ext,OPPONENTS),"direct":(range(7170400,7170460),("v14",))}
    raise ValueError(stage)


def environment():
    names = ("__init__.py","protocol.py","variants.py","fetch_kaggle3.py","final_battle_assess.py",
             "final_battle_select.py","residual_ensemble_compare.py")
    extra = list((ROOT/"agents").rglob("*.py")) + list((ROOT/"lux").glob("*.py")) + [ROOT/"scripts"/n for n in names]
    engine_dir = Path(util.find_spec("luxai_s3").origin).parent
    if (hash_mapping({str(p.relative_to(ROOT)):game.digest(p) for p in extra}) != SUPPORT or
            hash_mapping({p.name:game.digest(p) for p in engine_dir.glob("*.py")}) != ENGINE):
        raise ValueError("Changed game support, assessment or engine")
    return dict(support=SUPPORT,engine=ENGINE,machine=platform.machine(),platform=platform.system(),python=platform.python_version(),
                versions={k:metadata.version(k) for k in ("numpy","scipy","jax","jaxlib","torch","luxai-s3")},
                flags={k:os.getenv(k) for k in ("PYTHONHASHSEED","XLA_FLAGS","JAX_PLATFORMS","CUDA_VISIBLE_DEVICES")})


def options(repo, stage, arm):
    seeds, foes = blocks(stage)[arm]
    model = {"v14":None,"r3":repo/R3,"midpoint":repo/MID/"midpoint.pth","direct":repo/MID/"midpoint.pth"}[arm]
    return SimpleNamespace(candidate="selective_movement" if model else "v14",model=str(model) if model else None,
                           opponents=",".join(foes),first=seeds.start,maps=len(seeds))


def expected(repo, stage, arm):
    c = options(repo,stage,arm)
    origin = "r3" if arm=="midpoint" else arm
    path = ROOT/"experiments/analysis/movement_soft_20261115/confirmation"/origin/"manifest.json"
    checked(path,HIST[origin])
    historical = json.loads(path.read_bytes())
    historical.update(first=c.first,maps=c.maps,model=None if arm=="v14" else MODELS["r3" if arm=="r3" else "midpoint"])
    if game.contract(c) != historical:
        raise ValueError(f"Game runtime differs from the original R3/V14 source or weights in {arm}")
    return historical


def seal(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with (path.parent/("."+path.name+".lock")).open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if path.exists():
            if json.loads(path.read_bytes()) != value:
                raise ValueError(f"Changed registered file: {path}")
        else:
            temp = path.with_suffix(".tmp")
            temp.write_text(json.dumps(value, sort_keys=True, indent=2)+"\n")
            temp.replace(path)


def add_screen_gates(result, old, new, seeds):
    by, pooled = judge.external_comparison(old,new,seeds,"r3_wins")
    result["against_r3"] = dict(by_opponent=by,external=pooled,files=old.hashes)
    result["gates"].update(external_more_than_r3=pooled["net_wins"]>0,
                           solution_at_least_r3=by["solution92"]["net_wins"]>=0)
    result["game_gates_pass"] = all(result["gates"].values())


def report(repo, out, stage):
    layout = blocks(stage)
    runs = {}
    for arm,(seeds,foes) in layout.items():
        manifest = expected(repo,stage,arm)
        run = judge.load_run(out/stage/arm,manifest["candidate"],seeds,foes)
        if run.manifest != manifest:
            raise ValueError("Different stored manifest: "+arm)
        if arm!="v14" and any(row["study"].get("movement",0)!=row["study"].get("changed_unit_orders",0) for row in run.games.values()):
            raise ValueError("Unexpected non-movement intervention: "+arm)
        runs[arm] = run
    new, ref, duel = (runs[k] for k in ("midpoint","v14","direct"))
    judge.compatible(ref,new)
    judge.compatible(new,duel)
    seeds = layout["midpoint"][0]
    result = judge.summarize(judge.Phase(ref,new,duel,seeds,layout["direct"][0]),stage)
    if stage=="screen":
        judge.compatible(runs["r3"],new,compare_checkpoint=False)
        add_screen_gates(result,runs["r3"],new,seeds)
    result.update(candidate="midpoint",protocol_sha256=game.digest(out/"protocol.json"),
                  bootstrap=dict(unit="whole map",seed=2711,draws=10000),
                  matches={k:{o:sum(r["wins"] for r in arm.games.values() if r["opponent"]==o)
                              for o in layout[k][1]} for k,arm in runs.items()})
    return result


def qualified_selection(repo, out):
    original = out/"screen/assessment.json"
    recomputed = report(repo,out,"screen")
    if not recomputed["game_gates_pass"] or not original.is_file() or json.loads(original.read_bytes()) != recomputed:
        raise ValueError("Confirmation requires the qualified, sealed 224-game selection")
    return game.digest(original)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation",choices=("check","run","assess"))
    p.add_argument("stage",choices=("screen","confirm"))
    p.add_argument("--repo",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--arm",choices=("midpoint","v14","r3","direct"),help="Only run this arm, without judging the stage")
    args = p.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    layout = blocks(args.stage)
    if args.arm and (args.arm not in layout or args.operation!="run"):
        p.error("The selected arm must belong to the requested run stage")
    receipt = dict(archive=admission(repo),runtime=environment(),source=game.digest(Path(__file__)),original=HIST)
    for arm in layout:
        expected(repo,args.stage,arm)
    if args.operation=="check":
        print(json.dumps(receipt,indent=2))
        return
    seal(out/"protocol.json",receipt)
    selection = qualified_selection(repo,out) if args.stage=="confirm" else None
    if args.operation=="run":
        for arm in ([args.arm] if args.arm else layout):
            c = options(repo,args.stage,arm)
            path = out/args.stage/arm
            if (path/"games.jsonl").exists() and not (path/"manifest.json").is_file():
                raise ValueError("Missing original manifest for existing games")
            if (path/"completed.json").exists():
                saved = judge.load_run(path,c.candidate,*layout[arm])
                if saved.manifest != expected(repo,args.stage,arm):
                    raise ValueError("Completed arm differs from its registered source")
                continue
            cmd = [sys.executable,"-B","-u","-m","scripts.final_battle_compare","--candidate",c.candidate,"--opponents",
                   c.opponents,"--first",str(c.first),"--maps",str(c.maps),"--out",str(path),"--workers","1"]
            if c.model:
                cmd += ["--model",c.model]
            subprocess.run(cmd,cwd=ROOT,check=True)
        if args.arm:
            return
    result = report(repo,out,args.stage)
    if selection:
        result["selection_sha256"] = selection
    seal(out/args.stage/"assessment.json",result)
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
