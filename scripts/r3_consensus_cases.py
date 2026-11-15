"""After a positive offline study, replay five counterexamples and only then try the fixed ten-seat intervention."""
import argparse
from collections import Counter
import fcntl
import json
from pathlib import Path
from types import SimpleNamespace

from scripts import final_battle_compare as runner
from scripts.r3_diagonal_games import manifest,json_sha
from scripts.r3_consensus_offline import REFERENCE,checks
from scripts.r3_diagonal import R3,digest
from scripts.train_combat_advice import publish_json

LOST=(("kaggle3",7286135,"player_0"),("kaggle3",7286135,"player_1"),("kaggle3",7286141,"player_0"),
      ("kaggle3",7286141,"player_1"),("solution92",7286137,"player_1"))
WON=tuple(("solution92",n,"player_"+s) for n,s in ((7286102,"1"),(7286115,"0"),(7286124,"0"),
                                                          (7286142,"1"),(7286144,"0")))
ROSTER={"trace":LOST,"candidate":LOST+WON}
ASSESSMENT="0e19f04f02db6e56b595c70b5e4ced682f5860a4efc08f0809b508fdd53bc030"
FIELDS=("wins","losses","result","points","opp_points","steps","study")


def registration(a):
    off=json.loads(a.offline.read_bytes())
    ref=json.loads(a.reference.read_bytes())
    if digest(a.reference)!=REFERENCE or off["reference"]!=REFERENCE or off["model"]!=R3 or digest(a.model)!=R3:
        raise ValueError("Different offline provenance")
    required={"scripts/r3_diagonal.py","scripts/r3_view_consensus.py","scripts/r3_consensus_offline.py",
              "scripts/selective_advice_agent.py","scripts/combat_teacher_counterfactual.py","scripts/imitate.py",
              "agents/sherlock/imitation_net.py","agents/sherlock/cnn_model.py","agents/sherlock/features.py",
              "experiments/analysis/r3_view_consensus_20261115/PLAN.md"}
    if set(off["source"])!=required or any(digest(runner.ROOT/f)!=sha for f,sha in off["source"].items()):
        raise ValueError("Changed policy since offline selection")
    records=[r for r in ref["archives"] if r["cohort"]=="new_validation"]
    expected={(r["seed"],r["side"]):r for r in records}
    done={(r["seed"],r["side"]):r for r in off["cases"]}
    if len(off["cases"])!=48 or set(done)!=set(expected):
        raise ValueError("Incomplete archive comparison")
    counts=("rows","r3_correct","v14_correct","actual_r3_correct","reconstructed_r3_differs_from_actual","r3_hurt_correct_v14")
    total=Counter()
    for key, r in done.items():
        if r["sha256"]!=expected[key]["sha256"] or r["original"]!={k:expected[key]["counts"][k] for k in counts}:
            raise ValueError("Original control case differs")
        checks(r["measured"])
        total.update(r["measured"])
    if total!=Counter(off["total"]) or not all(checks(total).values()) or off["passes"] is not True:
        raise ValueError("Offline gate failed")
    frozen=manifest(SimpleNamespace(model=a.model,archive=a.archive),"confirm","diagonal")
    hist_report=a.historical/"assessment.json"
    if digest(hist_report)!=ASSESSMENT: raise ValueError("Different independent confirmation")
    hist=json.loads(hist_report.read_bytes())
    paths={arm:a.historical/arm for arm in ("v14","diagonal")}
    data={}
    for arm,p in paths.items():
        f=hist["reference_files" if arm=="v14" else "candidate_files"]
        if digest(p/"games.jsonl")!=f["games_sha256"] or digest(p/"manifest.json")!=f["manifest_sha256"]:
            raise ValueError("Changed historical outcomes")
        if arm=="diagonal" and json.loads((p/"manifest.json").read_bytes())!=frozen:
            raise ValueError("Original playing sources or execution environment differ")
        raw=list(map(json.loads,(p/"games.jsonl").read_text().splitlines()))
        data[arm]={(r["opponent"],r["seed"],r["side"]):r for r in raw}
        if len(data[arm])!=len(raw) or len(raw)!=240: raise ValueError("Incomplete original results")
    loss={k for k,r in data["diagonal"].items() if r["result"]<data["v14"][k]["result"]}
    gains=sorted(k for k,r in data["diagonal"].items() if r["result"]>data["v14"][k]["result"])
    controls={}
    for k in gains:
        controls.setdefault(k[1],k)
    if loss!=set(LOST) or tuple(list(controls.values())[:5])!=WON: raise ValueError("Changed counterexample groups")
    return dict(confirmation_sha256=ASSESSMENT,offline_sha256=digest(a.offline),basis=json_sha(frozen),
                runner_sha256=digest(Path(__file__))),data["diagonal"]


def report(stage,folder,stamp,old):
    keys=ROSTER[stage]
    fname=lambda k:folder/("_".join(map(str,k))+".json")
    if {p.name for p in folder.glob("*.json") if p.name!="assessment.json"} != {fname(k).name for k in keys}:
        raise ValueError("Missing or additional paired game")
    rows={}
    for k in keys:
        r=json.loads(fname(k).read_bytes())
        if (r["source"]!=stamp or tuple(r["game"][t] for t in ("opponent","seed","side"))!=k or r["stage"]!=stage
                or r["game"]["steps"]!=303 or r["game"]["wins"]+r["game"]["losses"]!=3
                or r["game"]["result"]!=int(r["game"]["wins"]>=2)):
            raise ValueError("Wrong original state or incomplete game")
        if stage=="trace" and any(r["game"][f]!=old[k][f] for f in FIELDS):
            raise ValueError(f"Passive game does not reproduce original {k}")
        n=r["routing"].get("would_veto_executable",0)
        if bool(n)!=(r["first"] is not None) or n>r["routing"].get("would_veto_proposed",0):
            raise ValueError("Invalid trace data")
        rows[k]=r
    hashes={fname(k).name:digest(fname(k)) for k in keys}
    results=[dict(opponent=k[0],seed=k[1],side=k[2],old=old[k]["result"],now=v["game"]["result"],
                  original_match_wins=old[k]["wins"],now_match_wins=v["game"]["wins"],
                  executable_vetoes=v["routing"].get("would_veto_executable",0),first=v["first"]) for k,v in rows.items()]
    if stage=="trace":
        return dict(rows=results,files=hashes,passes=any(v["executable_vetoes"]>0 for v in results))
    rescue=sum(rows[k]["game"]["result"] for k in LOST)
    harm=sum(1-rows[k]["game"]["result"] for k in WON)
    return dict(rows=results,files=hashes,rescued=int(rescue),former_wins_lost=int(harm),passes=rescue>0 and rescue>harm)


def stage(a):
    stamp,old=registration(a)
    out=a.out.resolve()
    if a.stage=="candidate":
        verified=report("trace",out/"trace",stamp,old)
        if (not verified["passes"] or json.loads((out/"trace/assessment.json").read_bytes())!=verified):
            raise ValueError("Original replay did not demonstrate any executable disagreement")
        stamp=dict(stamp,traces=digest(out/"trace/assessment.json"))
    folder=out/a.stage
    folder.mkdir(parents=True,exist_ok=True)
    klass="ObservedDiagonalAgent" if a.stage=="trace" else "ViewConsensusAgent"
    with (folder/".lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        started=False
        try:
            for k in ROSTER[a.stage]:
                f=folder/("_".join(map(str,k))+".json")
                if f.exists(): continue
                if not started:
                    key="selective_movement"
                    stock=runner.POLICIES[key]
                    try:
                        runner.POLICIES[key]="scripts.r3_view_consensus:"+klass
                        runner.init_worker(key,str(a.model))
                    finally:
                        runner.POLICIES[key]=stock
                    started=True
                g=runner.evaluate(("selective_movement",*k,str(a.model)))
                player=runner.evaluate.agent
                if type(player).__name__!=klass: raise ValueError("Wrong actually evaluated agent")
                if a.stage=="trace" and any(g[f]!=old[k][f] for f in FIELDS):
                    raise ValueError(f"Original result, score, or change counters differ on {k}")
                r=dict(stage=a.stage,source=stamp,game=g,routing=dict(player.consensus_counts),first=player.first_disagreement)
                publish_json(f,r)
                print(k,g["result"],r["routing"],flush=True)
        finally:
            if started: runner.evaluate.env.close()
        fresh,_=registration(a)
        if any(stamp[k]!=v for k,v in fresh.items()): raise ValueError("Source changed during play")
        result=report(a.stage,folder,stamp,old)
        destination=folder/"assessment.json"
        if destination.exists():
            if json.loads(destination.read_bytes())!=result: raise ValueError("Previous report differs")
        else: publish_json(destination,result)
        print(json.dumps({k:v for k,v in result.items() if k not in ("rows","files")},indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage",choices=tuple(ROSTER))
    for name in ("offline","historical","archive","model","reference","out"):
        p.add_argument("--"+name,type=Path,required=True)
    stage(p.parse_args())
