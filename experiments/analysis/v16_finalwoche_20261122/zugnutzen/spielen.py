"""Play the offline-qualified one-ply reward student against the three frozen opponents."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

import numpy as np
import torch

from berater import HERE, PACKAGE, Policy, V16, ValueNet
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from luxai_s3.wrappers import LuxAIS3GymEnv


def check_qualification(replicated):
    original_path = HERE / "offline.json"
    first = json.loads(original_path.read_text())
    weight = HERE / "wertberater.npz"
    checkpoint = sha256(weight.read_bytes()).hexdigest()
    if first["checkpoint"] != checkpoint or first["plan"] != sha256((HERE / "PLAN.md").read_bytes()).hexdigest():
        raise ValueError("Training plan or frozen weights changed")
    result = first
    if replicated:
        result = json.loads((HERE / "replikation.json").read_text())
        if (result["original"] != sha256(original_path.read_bytes()).hexdigest()
                or result["plan"] != sha256((HERE / "REPLIKATION.md").read_bytes()).hexdigest()
                or result["checkpoint"] != checkpoint or first["eligible"]):
            raise ValueError("Replication does not match the frozen initial study")
        stats = result["overall"]
        gates = {
            "support": stats["n"] >= 60 and stats["maps"] >= 12,
            "gain": stats["mean"] >= 0.15,
            "positive": stats["positive"] > stats["negative"],
            "card_interval": result["ci95"][0] > 0,
        }
        seeds = {entry["seed"] for entry in result["manifests"]}
        if gates != result["gates"] or len(result["manifests"]) != 64 or seeds != set(range(160373000, 160373064)):
            raise ValueError("Incomplete replication or inconsistent gates")
    if not result["eligible"] or not result["gates"] or not all(result["gates"].values()):
        raise ValueError("Offline study unqualified")
    return weight


def run(out, offset, stride, replicated=False):
    if os.getenv("PYTHONHASHSEED")!="0" or sha256(PACKAGE.read_bytes()).hexdigest()!=V16 or not verify():
        raise ValueError("Reference identity mismatch")
    limit_threads()
    weight = check_qualification(replicated)
    net=ValueNet().eval()
    with np.load(weight,allow_pickle=False) as z:
        net.load_state_dict({k:torch.from_numpy(z[k]) for k in z.files})
    version=sha256(weight.read_bytes()+(HERE/"berater.py").read_bytes()+(HERE/"spielen.py").read_bytes()).hexdigest()
    out.mkdir(parents=True,exist_ok=True)
    cases=[(seed,side,rival,arm) for seed in range(160364400,160364440) for side in ("player_0","player_1")
           for rival in ("solution92","kaggle3","v16")
           for arm in (("adviser",) if rival=="v16" else ("adviser","original"))]
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed,side,rival,arm in cases[offset::stride]:
            path=out/f"{seed}_{side}_{rival}_{arm}.json"
            if path.exists():
                old=json.loads(path.read_text())
                if old["model"]!=version or old["steps"]!=303:
                    raise ValueError(f"Changed seat {path.name}")
                continue
            agent=r3_package_agent(side,PACKAGE)
            if arm=="adviser":
                agent=Policy(agent,net)
            other="player_0" if side=="player_1" else "player_1"
            enemy=r3_package_agent(other,PACKAGE) if rival=="v16" else make_opponent(rival,other)
            g=play_game(env,agent,enemy,seed,side,train=False)
            require_no_agent_errors(agent.base if arm=="adviser" else agent,enemy)
            if g["steps"]!=303 or g["our_wins"]+g["opp_wins"]!=3 or g["point_counting_version"]!=2:
                raise ValueError("Incomplete game")
            row={k:g[k] for k in ("seed","side","steps","point_counting_version","our_wins","opp_wins","our_points","opp_points","game_win")}
            row.update(arm=arm, opponent=rival, model=version, changes=getattr(agent,"changed",0))
            temp=path.with_suffix(".pending")
            temp.write_text(json.dumps(row)+"\n")
            temp.replace(path)
            print(path.name,flush=True)
    finally:
        env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("out",type=Path)
    p.add_argument("--offset",type=int,default=0)
    p.add_argument("--stride",type=int,default=1)
    p.add_argument("--replication", action="store_true", help="Require the independent 64-map qualification")
    a=p.parse_args()
    if not 0<=a.offset<a.stride:
        p.error("Invalid lane")
    run(a.out,a.offset,a.stride,a.replication)
