"""Frozen 120-map whole-game study of the original Dev H holder swap option."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
from archiv import load
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import build_cfg, require_no_agent_errors
from scripts.r3_package import r3_package_agent

REF=ROOT/"experiments/releases/20261117_sherlock_v16/agent.zip"
WEIGHT=ROOT/"v16.pth"
SET=["imit_stay_bias=1.0","imit_unstack=true","imit_hold_points=true","imit_tactics=wechsel"]


def h(p):
    return sha256(p.read_bytes()).hexdigest()


def fsync_json(path,row):
    tmp=path.with_suffix(f".{os.getpid()}.pending")
    with tmp.open("w") as f:
        json.dump(row,f); f.write("\n"); f.flush(); os.fsync(f.fileno())
    tmp.replace(path)


def keys(phase):
    seeds=[7266000] if phase=="technik" else range(160358000,160358120)
    return [(s,p,o,a) for s in seeds for p in ("player_0","player_1")
            for o in (("solution92","kaggle3") if phase=="technik" else ("solution92","kaggle3","v16"))
            for a in (("wechsel",) if o=="v16" else ("original","wechsel"))]


def signature():
    import importlib.util
    eng=Path(importlib.util.find_spec("luxai_s3").origin).parent
    paths=[p for d in ("agents","scripts","lux","experiments/opponents") for p in (ROOT/d).rglob("*")
           if p.suffix in (".py",".pth")]
    paths+=[HERE/"PLAN.md",HERE/"spielen.py",HERE/"archiv.py",WEIGHT,REF]
    files={str(p.relative_to(ROOT)):h(p) for p in sorted(paths)}
    if h(REF)!="0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099" or not verify():
        raise ValueError("Wrong reference")
    return dict(project=files,engine={str(p.relative_to(eng)):h(p) for p in sorted(eng.rglob("*.py"))},
                historical_source="0cd2ce37bf5c9dec21ac976c549c9c7f616ac614",switches=SET,hashseed=os.environ["PYTHONHASHSEED"])


def valid(row,k,hash_):
    if (tuple(row[x] for x in ("seed","side","opponent","arm"))!=k or row["source"]!=hash_
            or row["steps"]!=303 or row["point_counting_version"]!=2 or row["our_wins"]+row["opp_wins"]!=3
            or row["game_win"]!=int(row["our_wins"]>=2)):
        raise ValueError(f"Invalid game {k}")


def total_check(folder,phase,hash_):
    outcomes=[]
    for k in keys(phase):
        stem="_".join(map(str,k))
        row=json.loads((folder/phase/f"{stem}.json").read_text())
        valid(row,k,hash_)
        outcomes.append(row)
    return outcomes


def tech_check(folder,hash_):
    result=total_check(folder,"technik",hash_)
    arch={a:load(name)[0] for a,name in (("original","k"),("wechsel","wechsel"))}
    for row in result:
        k=tuple(row[x] for x in ("seed","side","opponent"))
        ref=arch[row["arm"]][k]
        if any(row[x]!=int(ref[x]) for x in ("our_wins","opp_wins","our_points","opp_points","game_win","steps")):
            raise ValueError(f"Archived course game differs for {row['arm']} {k}")
    if not any(r["swaps"]>0 for r in result): raise ValueError("No technical swap")
    return result


def run(folder,phase,lane,workers):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock.imitation_agent import ImitationAgent
    limit_threads()
    folder.mkdir(parents=True,exist_ok=True); (folder/phase).mkdir(exist_ok=True)
    contract=signature()
    path=folder/"auftrag.json"
    if not path.exists():fsync_json(path,contract)
    if json.loads(path.read_text())!=contract:raise ValueError("Source changed")
    source=h(path)
    if phase=="frisch":tech_check(folder,source)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for k in keys(phase)[lane::workers]:
            s,side,o,arm=k; dest=folder/phase/("_".join(map(str,k))+".json")
            if dest.exists():
                valid(json.loads(dest.read_text()),k,source);continue
            if arm=="wechsel":
                player=ImitationAgent(side,agent_path=str(WEIGHT),train=False,cfg=build_cfg(str(WEIGHT),SET))
                player.set_to_eval_mode()
            else:player=r3_package_agent(side,REF)
            other="player_1" if side=="player_0" else "player_0"
            rival=r3_package_agent(other,REF) if o=="v16" else make_opponent(o,other)
            game=play_game(env,player,rival,s,side,train=False)
            require_no_agent_errors(player,rival)
            row={x:game[x] for x in ("seed","side","steps","point_counting_version","game_win","our_wins","opp_wins","our_points","opp_points")}
            swaps=int(player._tactics.counts["wechsel"]) if arm=="wechsel" and player._tactics is not None else 0
            changes=int(player.ep_stats.get("tactics_units",0)) if arm=="wechsel" else 0
            row.update(arm=arm,opponent=o,source=source,swaps=swaps,changed_units=changes)
            valid(row,k,source);fsync_json(dest,row)
    finally:env.close()
    if json.loads(path.read_text())!=signature():raise ValueError("Source changed at end")
    print("Lauf abgeschlossen",phase,lane,flush=True)


if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("folder",type=Path);a.add_argument("phase",choices=("technik","frisch","check"))
    a.add_argument("lane",type=int,default=0,nargs="?");a.add_argument("workers",type=int,default=1,nargs="?")
    v=a.parse_args()
    if v.phase=="check":print(json.dumps(tech_check(v.folder,h(v.folder/"auftrag.json")),indent=2))
    else:run(v.folder,v.phase,v.lane,v.workers)
