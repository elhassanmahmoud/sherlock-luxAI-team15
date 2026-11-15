"""Independent, conditionally admitted dual-midpoint confirmation with a shared V14 control."""
import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

from scripts import r8_midpoint_diagonal_games as screen

single, dual, judge = screen.single, screen.dual, screen.judge
PLAN_SHA = "2eb02f7311844b2abc6ccd1e7187835608dab6faa3b4aa5699b9b3fdf4c7492c"
SCREEN_SHA = "e3b50010563fb0e83aa923340038abc526bad8efcb9eae3dcbc5aaf3f9156add"
PLAN = screen.STUDY / "BESTAETIGUNGSPLAN.md"
EXTERNAL = range(7170300,7170360)
DIRECT = range(7170400,7170460)
ARMS = {"dual_external":(EXTERNAL,screen.OPPONENTS),"dual_direct":(DIRECT,("v14",))}


def schedule(stage):
    if stage!="confirm": raise ValueError("Only this confirmation is registered")
    return ARMS


def config(a,stage,arm):
    schedule(stage)
    single_name={"dual_external":"midpoint","dual_direct":"direct"}[arm]
    prior=screen.config(a,"screen",arm)
    original=single.expected(a.repo,"confirm",single_name)
    if any(prior[k]!=v for k,v in original.items() if k not in ("candidate","first","maps")):
        raise ValueError("Original course runtime, model or V14 differs from the admitted screen")
    return dict(prior,first=original["first"],maps=original["maps"],selection=a.selection,
                confirmation_plan=PLAN_SHA,confirmation_source=single.game.digest(Path(__file__)))


def owned(a,arm,play):
    spec=SimpleNamespace(**{**vars(a),"model":a.repo/single.MID/"midpoint.pth"})
    with ExitStack() as ctx:
        ctx.enter_context(patch.object(dual,"schedule",schedule))
        ctx.enter_context(patch.object(dual,"manifest",config))
        ctx.enter_context(patch.dict(dual.ACTORS,{"dual_midpoint":screen.POLICY}))
        return dual.play(spec,"confirm",arm) if play else dual.checked(spec,"confirm",arm)


def selection(a):
    path=a.out/"screen/assessment.json"
    if not path.is_file(): raise ValueError("No completed dual-view screen yet")
    live=screen.assessment(a)
    if live!=json.loads(path.read_bytes()): raise ValueError("Dual screen results or immutable sources changed")
    return single.game.digest(path) if live["game_gates_pass"] else None


def control(a,play,coordinated):
    path=a.singles/"confirm/v14"
    expected=single.expected(a.repo,"confirm","v14")
    if not (path/"completed.json").exists():
        if not play: raise ValueError("Shared V14 control is not sealed")
        # The regular single-view coordinator owns this arm whenever its screen passes.
        single_screen=a.singles/"screen/assessment.json"
        if not single_screen.is_file(): raise ValueError("Wait for the completed single-view selection")
        result=single.report(a.repo,a.singles,"screen")
        if result!=json.loads(single_screen.read_bytes()): raise ValueError("Single-view screen changed")
        if result["game_gates_pass"] and not coordinated:
            print("The admitted single-view confirmation owns the V14 arm. Re-run assess when it is sealed.",flush=True)
            return None
        if (path/"games.jsonl").exists() and not (path/"manifest.json").is_file():
            raise ValueError("Unbound V14 reference results")
        c=single.options(a.repo,"confirm","v14")
        # Same writable directory, original nonblocking writer lock, actor, runner and resume rules.
        subprocess.run([sys.executable,"-B","-u","-m","scripts.final_battle_compare","--candidate","v14",
            "--opponents",c.opponents,"--first",str(c.first),"--maps",str(c.maps),"--workers","1","--out",str(path)],
            cwd=screen.ROOT,check=True)
    ref=judge.load_run(path,"v14",EXTERNAL,screen.OPPONENTS)
    if ref.manifest!=expected: raise ValueError("Other V14 source, engine, weights, scoring or map range")
    return ref


def assess(a,ref):
    ext,duel=owned(a,"dual_external",False),owned(a,"dual_direct",False)
    judge.compatible(ref,ext)
    judge.compatible(ext,duel)
    result=judge.summarize(judge.Phase(ref,ext,duel,EXTERNAL,DIRECT),"confirm")
    result["changed_seats"]={}
    for opp in screen.OPPONENTS:
        keys=[(opp,s,p) for s in EXTERNAL for p in screen.SEATS]
        result["changed_seats"][opp]={label:[[k[1],k[2]] for k in keys
            if ext.games[k]["result"]-ref.games[k]["result"]==difference]
            for label,difference in (("gained",1),("lost",-1))}
    result["match_wins"]={name:{o:sum(r["wins"] for k,r in run.games.items() if k[0]==o) for o in foes}
        for name,run,foes in (("v14",ref,screen.OPPONENTS),("dual_external",ext,screen.OPPONENTS),
                              ("dual_direct",duel,("v14",)))}
    result.update(screen_sha256=a.selection,confirmation_plan=PLAN_SHA,shared_v14="r8_midpoint_20261115/games/confirm/v14",
        bootstrap=dict(draws=10000,seed=2711,unit="whole map with both start seats and external opponents"))
    single.seal(a.out/"confirm/assessment.json",result)
    print(json.dumps(result,indent=2))


def compare_views(a,ref):
    # Descriptive only; their direct games are against V14, not against each other.
    selected=single.qualified_selection(a.repo,a.singles)
    rev=single.report(a.repo,a.singles,"confirm")
    rev["selection_sha256"]=selected
    saved=a.singles/"confirm/assessment.json"
    if not saved.is_file() or rev!=json.loads(saved.read_bytes()):
        raise ValueError("The qualified single-view confirmation is not sealed")
    assess(a,ref)
    ext,duel=owned(a,"dual_external",False),owned(a,"dual_direct",False)
    old={}
    for k in ("midpoint","direct"):
        seeds,foes=single.blocks("confirm")[k]
        old[k]=judge.load_run(a.singles/"confirm"/k,"selective_movement",seeds,foes)
        if old[k].manifest!=single.expected(a.repo,"confirm",k):
            raise ValueError(f"Different single-view arm: {k}")
    by,pooled=judge.external_comparison(old["midpoint"],ext,EXTERNAL,"single_midpoint_wins")
    delta=[sum(duel.games["v14",seed,seat]["result"]-old["direct"].games["v14",seed,seat]["result"]
              for seat in screen.SEATS)/len(screen.SEATS) for seed in DIRECT]
    result=dict(external=pooled,by_opponent=by,vs_same_v14=dict(games=2*len(DIRECT),net_wins=round(2*sum(delta)),
            winrate_difference=sum(delta)/len(delta),map_ci95=judge.bounds(delta)),
            single_confirmation_sha256=single.game.digest(saved),
            dual_confirmation_sha256=single.game.digest(a.out/"confirm/assessment.json"),
            interpretation="Paired comparisons of each variant against the same opponents; descriptive, no head-to-head.")
    single.seal(a.out/"confirm/single_view_comparison.json",result)
    print(json.dumps(result,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("operation",choices=("check","run","assess","compare-views"));p.add_argument("--repo",required=True,type=Path)
    p.add_argument("--out",type=Path);p.add_argument("--singles",type=Path);p.add_argument("--fit-root",type=Path)
    p.add_argument("--arm",choices=(*ARMS,"v14"))
    p.add_argument("--coordinated-v14",action="store_true",
                   help="The coordinator has explicitly assigned the single-view V14 writer to this process")
    a=p.parse_args()
    if a.arm and a.operation!="run": p.error("--arm requires run")
    if a.coordinated_v14 and (a.operation!="run" or a.arm!="v14"):
        p.error("--coordinated-v14 requires an expressly assigned run --arm v14")
    a.repo=a.repo.resolve();a.out=(a.out or a.repo/screen.STUDY/"games").resolve()
    a.singles=(a.singles or a.repo/single.STUDY/"games").resolve()
    if a.singles==a.out: p.error("Separate the candidate from the single-view controls")
    a.archive=a.repo/screen.STUDY/"validation.json";a.archive_sha256=screen.OFFLINE_SHA
    a.fit_root=(a.fit_root or screen.ROOT/"offline").resolve();a.diagonal_control=None
    single.checked(screen.ROOT/PLAN,PLAN_SHA)
    single.checked(Path(screen.__file__),SCREEN_SHA)
    if (single.blocks("confirm")["v14"]!=(EXTERNAL,screen.OPPONENTS)
            or single.blocks("confirm")["direct"]!=(DIRECT,("v14",))
            or set(EXTERNAL)&set(DIRECT) or set(screen.MAPS)&(set(EXTERNAL)|set(DIRECT))):
        raise ValueError("Confirmation has unregistered maps or overlap with selection")
    a.receipt=screen.admission(a)
    a.selection=None
    for name in ARMS: config(a,"confirm",name)
    if a.operation=="check":
        print("Sources, weights, schedules, archives and both opponent bindings match. No games started.")
        return
    a.selection=selection(a)
    if not a.selection:
        print("Dual-view screen failed; no independent games admitted.")
        return
    if a.operation=="run":
        for name in ([a.arm] if a.arm else ARMS):
            if name=="v14":
                if control(a,True,a.coordinated_v14) is None: raise SystemExit(75)
            else: owned(a,name,True)
        if a.arm: return
    ref=control(a,a.operation=="run",False)
    if ref is None: raise SystemExit(75)
    if a.operation=="compare-views": compare_views(a,ref)
    else: assess(a,ref)


if __name__=="__main__":
    main()
