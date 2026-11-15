"""Registered game panels for the trained R3 context selector; no teacher at inference."""
import argparse
from functools import partial
import json
from pathlib import Path
from types import SimpleNamespace

from scripts import final_battle_assess as audit
from scripts import final_battle_compare as base
from scripts import r3_context_study as study
from scripts.final_battle_select import OPPONENTS, checked_run_files
from scripts.r3_context_table import PROTOCOL_SHA, R3_SHA
from scripts.train_combat_advice import publish_json

SEEDS = {"screen":range(7287200,7287216), "confirm":range(7287300,7287360), "direct":range(7287400,7287460)}
FILES = ("r3_context_table.py","r3_context_study.py","r3_context_agent.py","r3_context_games.py")


def admitted(directory, model):
    table = directory / "table.json"
    report = directory / "validation.json"
    proposal = json.loads(table.read_bytes())
    valid = json.loads(report.read_bytes())
    if (base.digest(model) != R3_SHA or proposal["r3_sha256"] != R3_SHA or
            proposal["protocol_sha256"] != PROTOCOL_SHA or proposal["training_seeds"] != [7287000,7287047] or
            valid["table_sha256"] != base.digest(table) or valid["source_sha256"] != study.source_hashes() or
            proposal["source_sha256"] != valid["source_sha256"] or not valid["passes"] or
            valid["counts"]["all"]["mean_net_per_map_ci95"][0] <= 0 or valid["counts"]["solution92"]["net"] < 0):
        raise ValueError("Context training, offline nomination or original R3 is not bound")
    return {"table_sha256":valid["table_sha256"],"offline_sha256":base.digest(report)}


def opponents(stage, arm):
    if arm not in ("context","v14","r3") or stage not in SEEDS or (
            arm=="r3" and stage!="screen") or (stage=="direct" and arm!="context"):
        raise ValueError(f"Unregistered panel {stage}/{arm}")
    if stage=="direct":
        return ("v14",)
    return (*OPPONENTS, "v14") if (stage,arm)==("screen","context") else OPPONENTS


def init_worker(arm, model, *, table):
    if arm != "context":
        base.init_worker("selective_movement" if arm=="r3" else "v14", model)
        return
    from scripts.experiment import limit_threads
    limit_threads()
    import torch
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.par_eval import build_cfg
    from scripts.r3_context_agent import ContextMovementAgent

    torch.manual_seed(0)
    actor = ContextMovementAgent("player_0",agent_path=str(base.WEIGHTS),cfg=build_cfg(str(base.WEIGHTS),[]),
                                 train=False,seed=0,mode="movement",advice_path=model,table=table)
    actor.set_to_eval_mode()
    actor.autosave_on_terminate = False
    base.evaluate.agent, base.evaluate.env = actor, LuxAIS3GymEnv(numpy_output=True)


def contract(a):
    m = base.contract(SimpleNamespace(**{**vars(a), "candidate":"selective_movement"}))
    if m["weights"] != audit.V14_SHA or m["model"] != (None if a.candidate=="v14" else R3_SHA):
        raise ValueError("Runtime weights differ from the reviewed versions")
    m.update(candidate=a.candidate, admission=admitted(a.study,a.r3))
    m["sources"].update({"scripts/"+n:base.digest(Path(__file__).with_name(n)) for n in FILES})
    return m


def load(directory, stage, arm, receipt):
    path = directory / ("confirm" if stage=="direct" else stage) / ("direct" if stage=="direct" else arm)
    seeds, foes = SEEDS[stage], opponents(stage,arm)
    rows, native, hashes = checked_run_files(path,arm,seeds,foes)
    if (native["weights"] != audit.V14_SHA or native["model"] != (None if arm=="v14" else R3_SHA)
            or native["admission"] != receipt
            or not all(native["sources"].get("scripts/"+n)==base.digest(Path(__file__).with_name(n)) for n in FILES)):
        raise ValueError("Run identity differs from the registered context comparison")
    if "kaggle3" in foes and any(native["sources"].get(audit.KAGGLE+k)!=v for k,v in audit.WEIGHT_SHA256.items()):
        raise ValueError("Different native opponent weights")
    return audit.Run(native,rows,hashes)


def screen(directory, receipt):
    v14, old, candidate = [load(directory,"screen",arm,receipt) for arm in ("v14","r3","context")]
    audit.compatible(v14,candidate)
    audit.compatible(v14,old)
    maps = SEEDS["screen"]
    judged = audit.summarize(audit.Phase(v14,candidate,candidate,maps,maps),"screen")
    enemy, ext = audit.external_comparison(old,candidate,maps,"r3_wins")
    judged["against_r3"] = dict(files=old.hashes,by_opponent=enemy,external=ext)
    judged["gates"].update(external_more_than_r3=ext["net_wins"]>0,solution_at_least_r3=enemy["solution92"]["net_wins"]>=0)
    judged["game_gates_pass"] = all(judged["gates"].values())
    return judged


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--study",type=Path,required=True,help="Directory holding the sealed table and validation")
    p.add_argument("--r3",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    sub = p.add_subparsers(dest="command",required=True)
    play = sub.add_parser("play")
    play.add_argument("stage",choices=SEEDS)
    play.add_argument("arm",choices=("context","r3","v14"))
    play.add_argument("--workers",type=int,choices=(1,2),default=1)
    judge = sub.add_parser("assess")
    judge.add_argument("stage",choices=("screen","confirm"))
    a = p.parse_args()
    receipt = admitted(a.study,a.r3)
    selected = None
    if a.stage!="screen" or a.command=="assess":
        selected = screen(a.out,receipt)
        if a.stage!="screen" and not selected["game_gates_pass"]:
            raise ValueError("Selection did not pass")
    if a.command=="assess":
        result = selected
        if a.stage=="confirm":
            ref, new, duel = [load(a.out,stage,arm,receipt) for stage,arm in
                              (("confirm","v14"),("confirm","context"),("direct","context"))]
            audit.compatible(ref,new)
            audit.compatible(new,duel)
            audit.compatible(load(a.out,"screen","context",receipt),new)
            result = audit.summarize(audit.Phase(ref,new,duel,SEEDS["confirm"],SEEDS["direct"]),"confirm")
            result["selection"] = selected
        publish_json(a.out / a.stage / "assessment.json",result)
        print(json.dumps(result["gates"]))
        return
    foes = opponents(a.stage,a.arm)
    seeds = SEEDS[a.stage]
    model = None if a.arm=="v14" else str(a.r3.resolve())
    dest = a.out / ("confirm" if a.stage=="direct" else a.stage) / ("direct" if a.stage=="direct" else a.arm)
    dest.mkdir(parents=True,exist_ok=True)
    opts = SimpleNamespace(candidate=a.arm,model=model,opponents=",".join(foes),first=seeds.start,
                           maps=len(seeds),workers=a.workers,out=dest,study=a.study,r3=a.r3)
    base.run(opts,get_contract=contract,initializer=partial(init_worker,table=str((a.study/"table.json").resolve())))


if __name__=="__main__":
    main()
