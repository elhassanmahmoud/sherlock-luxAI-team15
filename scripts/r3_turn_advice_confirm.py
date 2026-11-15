"""Independent 480-game validation after replaying the original 96-game selection audit."""
import argparse
from collections import Counter
from contextlib import ExitStack,redirect_stdout
import io
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import final_battle_assess as judge, final_battle_compare as game
from scripts import r3_diagonal_games as dual, r3_turn_advice_games as screen, r8_midpoint_games as single
from scripts.final_battle_select import OPPONENTS,SEATS

EXTERNAL=range(7170560,7170600)
DIRECT=range(7170660,7170700)
BLOCKS={"turn_external":(EXTERNAL,OPPONENTS),"v14_external":(EXTERNAL,OPPONENTS),
        "r3_solution":(EXTERNAL,("solution92",)),"direct":(DIRECT,("v14",))}
ACTORS={"turn_external":screen.NAME,"direct":screen.NAME,"r3_solution":"r3","v14_external":"v14"}
SELECTION="bff2a30023edfae57aa85bad1410a9696469dc641c506648764a04c930f08afe"
SCREEN_RUNNER="918a6c725e5e01325564bc5453d66f5b0996c97efe20efcea34bf21509ce8565"
NATIVE_RUNNER="e1dd43bb4c8926e394d686b0f61bfd9b14c5a41611e3faea68856fc8a6a34cc9"
PLAN=screen.STUDY/"BESTAETIGUNGSPLAN.md"


def selection(a):
    official=a.repo/screen.STUDY/"games/screen/assessment.json"
    single.checked(official,SELECTION)
    single.checked(game.ROOT/"scripts/r3_turn_advice_games.py",SCREEN_RUNNER)
    single.checked(game.ROOT/"scripts/r3_diagonal_games.py",NATIVE_RUNNER)
    data=json.loads(official.read_bytes())
    if data["game_gates_pass"] is not True or not all(data["gates"].values()):
        raise ValueError("The fixed screen did not qualify")
    def verify_only(path,obj):
        if path!=official or obj!=data:raise ValueError("96-game selection did not reproduce exactly")
    with patch.object(single,"seal",verify_only) as observed, redirect_stdout(io.StringIO()):
        screen.assess(SimpleNamespace(repo=a.repo,out=official.parent.parent))
    return dict(selection=SELECTION,screen_source=SCREEN_RUNNER,game_loop=NATIVE_RUNNER,
                screen_receipt=data["receipt"],runner=game.digest(Path(__file__)),plan=game.digest(game.ROOT/PLAN))


def schedule(stage):
    if stage!="confirm":raise ValueError("Only the independent confirmation is registered")
    return BLOCKS


def config(a,stage,arm):
    seeds,opps=schedule(stage)[arm]
    actor=ACTORS[arm]
    original="v14" if actor=="v14" else ("r3" if "kaggle3" in opps else "direct")
    historical=game.ROOT/"experiments/analysis/movement_soft_20261115/confirmation"/original/"manifest.json"
    single.checked(historical,single.HIST[original])
    orig=json.loads(historical.read_bytes())
    run=SimpleNamespace(candidate=orig["candidate"],model=None if actor=="v14" else a.model,
                        opponents=",".join(opps),first=seeds.start,maps=len(seeds))
    expected=dict(orig,first=seeds.start,maps=len(seeds),opponents=list(opps))
    if game.contract(run)!=expected or (actor!="v14" and expected["model"]!=judge.DISTILL_MODEL):
        raise ValueError("Original source, opponent, environment or weights differ")
    source=single.environment()
    if source!=a.receipt["screen_receipt"]["environment"]:raise ValueError("Different software since screen")
    return dict(expected,candidate=actor,arm=arm,actor_import=screen.ACTOR if actor==screen.NAME else dual.ACTORS[actor],
                receipt=a.receipt,environment=source)


def with_counts(original,actor):
    def evaluate(job):
        row=original(job)
        if actor==screen.NAME:
            live=evaluate.agent.selective_counts
            if not isinstance(live,Counter) or row["study"]!=dict(live):raise ValueError("Missing true candidate counters")
            row["study"]["turn_extra_played"]=live["turn_extra_played"]
            screen.turn_count(row)
        return row
    return evaluate


def run_arm(a,arm,play):
    with ExitStack() as ctx:
        ctx.enter_context(patch.object(dual,"schedule",schedule))
        ctx.enter_context(patch.object(dual,"manifest",config))
        ctx.enter_context(patch.dict(dual.ACTORS,{screen.NAME:screen.ACTOR}))
        if play:
            # The original initializer stores the live agent/env on the installed callable.
            ctx.enter_context(patch.object(game,"evaluate",with_counts(game.evaluate,ACTORS[arm])))
            run=dual.play(a,"confirm",arm)
        else:
            run=dual.checked(a,"confirm",arm)
    if ACTORS[arm]==screen.NAME:
        for row in run.games.values():screen.turn_count(row)
    return run


def against_r3(reference,candidate):
    values=[];flips=[];old=new=0
    for n in EXTERNAL:
        total=0
        for s in SEATS:
            k=("solution92",n,s);a=int(reference.games[k]["result"]);b=int(candidate.games[k]["result"])
            old+=a;new+=b;total+=b-a
            if a!=b: flips.append(dict(seed=n,side=s,r3=a,turn=b))
        values.append(total/len(SEATS))
    ci=judge.bounds(values)
    return dict(games=2*len(EXTERNAL),candidate_wins=new,r3_wins=old,net_wins=new-old,winrate_difference=sum(values)/len(values),
                difference_ci95=ci,gained=sum(z["turn"] for z in flips),lost=sum(z["r3"] for z in flips),flips=flips,
                demonstrated_solution_gain_over_r3=ci[0]>0,reference_files=reference.hashes)


def assess(a):
    runs={arm:run_arm(a,arm,False) for arm in BLOCKS}
    report=judge.summarize(judge.Phase(runs["v14_external"],runs["turn_external"],runs["direct"],EXTERNAL,DIRECT),"confirm")
    attr=against_r3(runs["r3_solution"],runs["turn_external"])
    counts={s:Counter() for s in SEATS}
    for arm in ("turn_external","direct"):
        for (o,n,s),row in runs[arm].games.items():counts[s][o]+=screen.turn_count(row)
    # summarize also reports direct_majority, logically implied by the strictly positive direct lower margin.
    checks={k:report["gates"][k] for k in ("solution_at_least_reference","external_lower_bound_positive","direct_lower_bound_above_half")}
    checks.update({s+"_additional_directions":sum(counts[s].values())>0 for s in SEATS})
    report.update(gates=checks,game_gates_pass=all(checks.values()),against_r3_solution=attr,
                  additional_directions_by_side_and_opponent=counts,receipt=a.receipt,
                  bootstrap=dict(draws=10000,seed=2711,unit="whole map with both seats and external opponents"))
    report["match_wins"]={k:{o:sum(v["wins"] for (foe,_,_),v in r.games.items() if foe==o)
                            for o in BLOCKS[k][1]} for k,r in runs.items()}
    report["external_flips_vs_v14"]=[dict(opponent=o,seed=n,side=s,v14=runs["v14_external"].games[o,n,s]["result"],turn=row["result"])
                                     for (o,n,s),row in runs["turn_external"].games.items()
                                     if row["result"]!=runs["v14_external"].games[o,n,s]["result"]]
    single.seal(a.out/"confirm/assessment.json",report)
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation",choices=("check","play","assess"))
    p.add_argument("--repo",required=True,type=Path);p.add_argument("--arm",choices=tuple(BLOCKS))
    a=p.parse_args();a.repo=a.repo.resolve();a.out=a.repo/screen.STUDY/"games";a.model=a.repo/single.R3
    if a.arm and a.operation!="play":p.error("--arm only applies to playing")
    a.receipt=selection(a)
    if a.operation=="play":
        for arm in ((a.arm,) if a.arm else BLOCKS):run_arm(a,arm,True)
    elif a.operation=="assess":assess(a)
    else:
        for arm in BLOCKS:config(a,"confirm",arm)
        print(json.dumps(a.receipt,indent=2))
