"""Run the fixed confirmation from an isolated tree, sealing each complete game once."""
import argparse
import fcntl
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import random
import sys

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import TARGET, verify
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import _module_for, r3_package_agent

RELEASE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
ORIGINAL = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
CONTROL = "5b200d5a7fadfffb86ccb6c3e74324e49fe4c1e27510581ae810e6a452b2a67b"
SCOUT = HERE.parent / "kundschafter/kandidat.py"


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def study_keys(arm):
    return [(s,side,o,arm) for s in range(160337000,160337200) for side in ("player_0","player_1")
            for o in ("solution92","kaggle3","v16") if o!="v16" or (s<160337050 and arm=="kandidat")]


def verify_sources(out):
    if sha(RELEASE)!=ORIGINAL or not verify() or os.environ.get("PYTHONHASHSEED")!="0":
        raise ValueError("Invalid release, teacher, or interpreter seed")
    paths = sorted([p for d in ("scripts","agents","lux") for p in (ROOT/d).rglob("*.py")] +
                   [p for p in TARGET.rglob("*") if p.suffix in (".py",".pth")] +
                   [RELEASE,HERE/"PLAN.md",HERE/"festlauf.py",SCOUT])
    engine = Path(importlib.util.find_spec("luxai_s3").origin).parent
    data = dict(project={str(p.relative_to(ROOT)):sha(p) for p in paths},
                engine={str(p.relative_to(engine)):sha(p) for p in sorted(engine.rglob("*.py"))},
                torch=torch.__version__,numpy=np.__version__,python=sys.version,
                seed0=160337000,maps=200,direct=50,release_sha256=ORIGINAL)
    text=json.dumps(data,sort_keys=True,indent=1)+"\n"
    outfile=out/"quellen.json"
    if not outfile.exists():
        with outfile.open("x") as stream:
            stream.write(text)
    if outfile.read_text()!=text:
        raise ValueError("Bound source or runtime changed")
    return sha(outfile)


def read_choice(out,weight):
    path=out/"auswahl.json"
    d=json.loads(path.read_text())
    if not d["control_passed"] or d["name"]!=("scout" if d["scout_passed"] else "kontrolle"):
        raise ValueError("Wrong nomination")
    candidate_sha=sha(SCOUT if d["name"]=="scout" else weight)
    if candidate_sha!=d["candidate_sha256"] or (d["name"]=="kontrolle" and candidate_sha!=CONTROL):
        raise ValueError("Candidate hash")
    return d["name"],sha(path)


def validate(row,k,source,choice):
    if (tuple(row[x] for x in ("seed","side","opponent","arm"))!=k or row["source"]!=source or row["choice"]!=choice
            or row["steps"]!=303 or row["point_counting_version"]!=2 or row["our_wins"]+row["opp_wins"]!=3
            or row["game_win"]!=int(row["our_wins"]>=2) or min(row["our_points"],row["opp_points"])<0):
        raise ValueError(f"Invalid saved game {k}")


def run(arm,out,weight):
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    out.mkdir(exist_ok=True,parents=True)
    source=verify_sources(out)
    name,choice=read_choice(out,weight) if arm=="kandidat" else ("original",None)
    _,module=_module_for(RELEASE.resolve())
    if name=="scout":
        spec=importlib.util.spec_from_file_location("confirmation_scout",SCOUT)
        scout=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scout)
    env=LuxAIS3GymEnv(numpy_output=True)
    rows=out/"partien"; locks=out/"sperren"
    rows.mkdir(exist_ok=True); locks.mkdir(exist_ok=True)
    completed=0
    for key in study_keys(arm):
        s,side,opponent,_=key
        stem=f"{arm}_{s}_{side}_{opponent}"
        result=rows/f"{stem}.json"
        if result.exists():
            validate(json.loads(result.read_text()),key,source,choice)
            continue
        with (locks/stem).open("a") as lock:
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:
                continue
            if result.exists():
                validate(json.loads(result.read_text()),key,source,choice)
                continue
            other="player_1" if side=="player_0" else "player_0"
            random.seed(s); np.random.seed(s); torch.manual_seed(s)
            if name=="original":
                player=r3_package_agent(side,RELEASE)
            elif name=="scout":
                player=scout.Scout(side,True)
            else:
                player=module.Agent_x(side,agent_path=str(weight))
                player.set_to_eval_mode()
            rival=r3_package_agent(other,RELEASE) if opponent=="v16" else make_opponent(opponent,other)
            game=play_game(env,player,rival,s,side,train=False)
            require_no_agent_errors(player.base if name=="scout" else player,rival)
            row={k:game[k] for k in ("seed","side","steps","point_counting_version","our_points","opp_points",
                                     "our_wins","opp_wins","game_win")}
            row.update(arm=arm,opponent=opponent,source=source,choice=choice)
            validate(row,key,source,choice)
            tmp=result.with_suffix(".partial")
            with tmp.open("w") as f:
                json.dump(row,f); f.write("\n"); f.flush(); os.fsync(f.fileno())
            tmp.replace(result); completed+=1
            if completed%20==0: print("Fertige zusätzliche Partien",arm,completed,flush=True)
    env.close()
    if source!=verify_sources(out) or (arm=="kandidat" and read_choice(out,weight)!=(name,choice)):
        raise ValueError("Bound input changed during play")
    print("Worker regulär beendet",arm,completed,flush=True)


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("arm",choices=("referenz","kandidat"))
    ap.add_argument("out",type=Path)
    ap.add_argument("--weight",type=Path)
    a=ap.parse_args()
    run(a.arm,a.out,a.weight)
