"""Prespecified external and direct screen of the two-view midpoint. Single-view controls are read-only."""
import argparse
from collections import Counter,defaultdict
from contextlib import ExitStack
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import r3_diagonal_games as dual, r8_midpoint_games as single
from scripts import final_battle_assess as judge
from scripts.final_battle_select import OPPONENTS, SEATS, checked_run_files

ROOT=single.ROOT
STUDY=Path("experiments/analysis/r8_midpoint_diagonal_20261115")
MAPS=range(7170230,7170246)
ARMS=("diagonal","dual_external","dual_direct")
SINGLES=("v14","r3","midpoint")
POLICY="scripts.r8_midpoint_diagonal:MidpointDiagonalAgent"
PLAN=STUDY/"PLAN.md"
AUDITOR="scripts/r8_midpoint_diagonal_audit.py"
PINS={"scripts/r8_midpoint_diagonal.py":"d5d8eaea95977e8c02ed25f2be0d05490303349cd6c6eb4f23632eb06560353b",
      "scripts/r3_diagonal.py":"13758f9a8566e587322ea3f8ab12920feb34a8bd1864ee50cb35b478ce564194",
      "scripts/r3_diagonal_games.py":"e1dd43bb4c8926e394d686b0f61bfd9b14c5a41611e3faea68856fc8a6a34cc9",
      "scripts/r8_midpoint_games.py":"de95c522ee4dddaf725d85821fb0803c277f7c88e85e9fecb427fa44f8c113c1"}
HIST_SHA="e06715ca12db558f7055284bff5ff51ae8416b237722f80421d24f46eaaf8894"
PLAN_SHA="dd54ac9688f411a66d1b29a2f962c0959770123490e11fbfa6f5917a46f51e6b"
OFFLINE_SHA="65ad72a84559634ab1284ac33a65886bd3ae6c4b775f3ba7cb98c20424877998"
AUDITOR_SHA="0837c875c59c838b59adc090bf9632dfe2726bc88dc9c4ccabf55eb76f2a99ab"


def schedule(stage):
    if stage!="screen": raise ValueError("Only selection is registered")
    return {arm:(MAPS,("v14",) if arm=="dual_direct" else OPPONENTS) for arm in ARMS}


def gates(a,b):
    return dict(old_at_least_diagonal=a["dual_correct"]>=a["diagonal_correct"],
                new_at_least_diagonal=b["dual_correct"]>=b["diagonal_correct"],
                at_least_one_strict=any(c["dual_correct"]>c["diagonal_correct"] for c in (a,b)),
                combined_at_least_single=sum(c["dual_correct"]-c["single_correct"] for c in (a,b))>=0)


def admission(a):
    if a.archive_sha256!=OFFLINE_SHA: raise ValueError("Different reviewed dual-view audit")
    single.checked(a.archive,OFFLINE_SHA)
    proof=json.loads(a.archive.read_bytes())
    for path,sha in PINS.items(): single.checked(ROOT/path,sha)
    single.checked(a.fit_root/PLAN,PLAN_SHA);single.checked(a.fit_root/AUDITOR,AUDITOR_SHA)
    code=proof["source_sha256"]
    if (code.get(str(PLAN))!=PLAN_SHA or code.get(AUDITOR)!=AUDITOR_SHA or
            code.get("scripts/r8_midpoint_diagonal.py")!=PINS["scripts/r8_midpoint_diagonal.py"]):
        raise ValueError("Offline audit or plan not bound to fit source")
    for name,sha in code.items():
        p=(a.fit_root/name).resolve()
        if not p.is_relative_to(a.fit_root): raise ValueError("Invalid fit source path")
        single.checked(p,sha)
    models={"diagonal_r3":dual.R3,"single_midpoint":single.MODELS["midpoint"],"dual_midpoint":single.MODELS["midpoint"]}
    if proof["models"]!=models or proof["single_reference"]!=single.AUDIT_SHA: raise ValueError("Changed controls")
    baseline=single.admission(a.repo)
    source=json.loads((a.repo/single.MID/"validation.json").read_bytes())
    def index(rows): return {(r["cohort"],r["seed"],r["side"]):r for r in rows}
    prior,now=index(source["archives"]),index(proof["cases"])
    if set(prior)!=set(now) or len(proof["cases"])!=96: raise ValueError("Changed seat roster")
    maps={k:defaultdict(Counter) for k in single.ARCHIVES}
    totals={k:Counter() for k in single.ARCHIVES}
    for key,r in now.items():
        prev=prior[key]; c=r["counts"]
        if (any(prev[k]!=r[k] for k in ("sha256","opponent","protocol"))
                or c["rows"]!=prev["counts"]["rows"] or c["single_correct"]!=prev["counts"]["midpoint_correct"]
                or any(type(v) is not int or v<0 for v in c.values())
                or any(c["dual_correct"]-c[ref+"_correct"]!=c["dual_gained_over_"+ref]-c["dual_lost_from_"+ref]
                       for ref in ("single","diagonal"))):
            raise ValueError(f"Changed archive or counts on {key}")
        totals[key[0]].update(c); maps[key[0]][str(key[1])].update(c)
    expected=gates(totals["old_validation"],totals["new_validation"])
    if (totals!=proof["totals"] or maps!=proof["per_map"] or proof["checks"]!=expected
            or not all(expected.values()) or proof["passes"] is not True):
        raise ValueError("Midpoint dual-view offline nomination not established")
    return dict(archive=a.archive_sha256,plan=PLAN_SHA,fit=single.hash_mapping(code),single=baseline,
                model=models,checks=expected)


def historical(a):
    path=a.repo/"experiments/analysis/movement_reflection_20261115/confirm/diagonal/manifest.json"
    single.checked(path,HIST_SHA)
    hist=json.loads(path.read_bytes())
    for name in ("scripts/r3_diagonal.py","scripts/r3_diagonal_games.py"):
        if hist["study_sources"][name]!=PINS[name]: raise ValueError("Different original diagonal actor/runner")
    return hist


def config(a,stage,arm):
    if arm not in schedule(stage): raise ValueError(arm)
    reference={"diagonal":"r3","dual_external":"midpoint","dual_direct":"direct"}[arm]
    m=single.expected(a.repo,"screen",reference)
    historic=historical(a)
    runtime=single.environment()
    if (any(runtime.get(k)!=v for k,v in historic["environment"].items() if k!="engine")
            or single.hash_mapping(historic["environment"]["engine"])!=runtime["engine"]):
        raise ValueError("Original diagonal and single-view runtime environments differ")
    registered={k:v for k,v in historic["sources"].items() if arm!="dual_direct" or not k.startswith(judge.KAGGLE)}
    if (m["weights"]!=historic["weights"] or m["engine"]!=historic["engine"] or m["sources"]!=registered):
        raise ValueError("Different original runtime or opponents")
    return dict(m,candidate="diagonal" if arm=="diagonal" else "dual_midpoint",
                actor_import=dual.ACTORS["diagonal"] if arm=="diagonal" else POLICY,arm=arm,admission=a.receipt,
                environment=runtime,code={**PINS,"scripts/r8_midpoint_diagonal_games.py":single.game.digest(Path(__file__))})


def pending(path):
    if (path/"completed.json").is_file(): return "complete"
    if (path/"games.jsonl").is_file():
        return f"partial ({len((path/'games.jsonl').read_bytes().splitlines())} rows)"
    return "started" if (path/"manifest.json").is_file() else "missing"


def control_paths(a):
    """Find the matching external actor even if an earlier runner also included direct games."""
    own=(a.out/"screen/diagonal").resolve()
    candidates=set()
    if a.diagonal_control: candidates.add(a.diagonal_control.resolve())
    for m in (a.repo/"experiments/analysis").rglob("manifest.json"):
        try: h=json.loads(m.read_bytes())
        except (ValueError,OSError): continue
        if (isinstance(h,dict) and h.get("first")==MAPS.start and h.get("maps")==len(MAPS)
                and h.get("candidate")=="diagonal" and set(OPPONENTS)<=set(h.get("opponents",[]))):
            candidates.add(m.parent.resolve())
    candidates.discard(own)
    return own,sorted(candidates)


def foreign(a,path):
    h=json.loads((path/"manifest.json").read_bytes()); original=historical(a)
    foes=tuple(h["opponents"])
    if set(foes) not in (set(OPPONENTS),set(OPPONENTS)|{"v14"}): raise ValueError("Unregistered opponents")
    if "admission" in h:
        if h!=config(a,"screen","diagonal"): raise ValueError("Other study has different game provenance")
    else:
        expected={**original,"first":MAPS.start,"maps":len(MAPS),"opponents":list(foes)}
        if h!=expected: raise ValueError("Unrecognized diagonal-control manifest")
    rows,_,hashes=checked_run_files(path,"diagonal",MAPS,foes)
    if any(r["study"].get("movement",0)!=r["study"].get("changed_unit_orders",0) for r in rows.values()):
        raise ValueError("Unexpected intervention in existing diagonal control")
    return judge.Run(h,{k:v for k,v in rows.items() if k[0] in OPPONENTS},hashes)


def diagonal(a,play):
    own,elsewhere=control_paths(a)
    if elsewhere:
        if len(elsewhere)!=1 or pending(own)!="missing":
            raise ValueError(f"Multiple control directories; resolve original provenance before use: {elsewhere}, {own}")
        path=elsewhere[0]
        if pending(path)!="complete": raise ValueError(f"Existing source has incomplete control; resume its original run: {path}")
        return foreign(a,path)
    return owned(a,"diagonal",play)


def owned(a,arm,play):
    model=a.repo/(single.R3 if arm=="diagonal" else single.MID/"midpoint.pth")
    spec=SimpleNamespace(**{**vars(a),"model":model})
    # The native two-view runner owns initialization, locking, resume, per-game validation and sealing.
    with ExitStack() as ctx:
        ctx.enter_context(patch.object(dual,"schedule",schedule))
        ctx.enter_context(patch.object(dual,"manifest",config))
        ctx.enter_context(patch.dict(dual.ACTORS,{"dual_midpoint":POLICY}))
        return dual.play(spec,"screen",arm) if play else dual.checked(spec,"screen",arm)


def screen_gates(result,comparisons):
    result["gates"].update({f"external_beats_{k}":comparisons[k]["external"]["net_wins"]>0
                            for k in ("midpoint","diagonal")})
    result["gates"].update({f"solution_at_least_{k}":comparisons[k]["by_opponent"]["solution92"]["net_wins"]>=0
                            for k in ("midpoint","diagonal")})
    result["game_gates_pass"]=all(result["gates"].values())


def assessment(a):
    singles={}
    receipt=dict(archive=a.receipt["single"],runtime=single.environment(),source=PINS["scripts/r8_midpoint_games.py"],original=single.HIST)
    if not (a.singles/"protocol.json").is_file() or json.loads((a.singles/"protocol.json").read_bytes())!=receipt:
        raise ValueError(f"Missing or changed original single-view study receipt: {a.singles}")
    for name in SINGLES:
        expected=single.expected(a.repo,"screen",name)
        path=a.singles/"screen"/name
        if pending(path)!="complete": raise ValueError(f"{name} single-arm {pending(path)} in original runner: {path}")
        r=judge.load_run(path,expected["candidate"],MAPS,OPPONENTS)
        if r.manifest!=expected or any(row["study"].get("movement",0)!=row["study"].get("changed_unit_orders",0)
                                       for row in r.games.values()): raise ValueError(f"Changed original single arm {name}")
        singles[name]=r
    d=diagonal(a,False); cand=owned(a,"dual_external",False); duel=owned(a,"dual_direct",False)
    result=judge.summarize(judge.Phase(singles["v14"],cand,duel,MAPS,MAPS),"screen")
    comp={}
    for name,ref in (("midpoint",singles["midpoint"]),("diagonal",d),("r3",singles["r3"])):
        by,ext=judge.external_comparison(ref,cand,MAPS,name+"_wins")
        comp[name]=dict(files=ref.hashes,external=ext,by_opponent=by)
    screen_gates(result,comp)
    result.update(controls=comp,archive_sha256=a.receipt["archive"],plan_sha256=PLAN_SHA,
                  bootstrap=dict(seed=2711,draws=10000,unit="whole map, retaining all seats and both external opponents"),
                  match_wins={name:{opp:sum(v["wins"] for k,v in r.games.items() if k[0]==opp)
                                    for opp in sorted({k[0] for k in r.games})}
                              for name,r in {**singles,"diagonal":d,"dual_external":cand,"dual_direct":duel}.items()})
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation",choices=("status","check","play","assess"))
    for name in ("repo","out","singles","diagonal-control","archive","fit-root"): p.add_argument("--"+name,type=Path,required=name in ("repo","out"))
    p.add_argument("--archive-sha256",default=OFFLINE_SHA);p.add_argument("--arm",choices=ARMS)
    a=p.parse_args()
    a.repo=a.repo.resolve(); a.out=a.out.resolve()
    a.singles=(a.singles or a.repo/single.STUDY/"games").resolve()
    a.archive=(a.archive or a.repo/STUDY/"validation.json").resolve()
    a.fit_root=(a.fit_root or ROOT/"offline").resolve()
    if a.out==a.singles: p.error("Use the separate dual-view output")
    if a.arm and a.operation!="play": p.error("--arm is for play")
    own,external=control_paths(a)
    states={k:pending(a.singles/"screen"/k) for k in SINGLES}
    states.update(diagonal=pending(own),external_diagonal_controls={str(p):pending(p) for p in external},
                  dual_external=pending(a.out/"screen/dual_external"),dual_direct=pending(a.out/"screen/dual_direct"))
    print(json.dumps(states,indent=2),flush=True)
    if a.operation=="status": return
    if not a.archive_sha256: p.error("Supply the reviewed --archive-sha256")
    a.receipt=admission(a)
    for arm in ARMS: config(a,"screen",arm)
    if a.operation=="check": return
    if a.operation=="play":
        for arm in ([a.arm] if a.arm else ARMS):
            if arm=="diagonal": diagonal(a,True)
            else: owned(a,arm,True)
        return
    result=assessment(a)
    single.seal(a.out/"screen/assessment.json",result)
    print(json.dumps(result,indent=2))


if __name__=="__main__": main()
