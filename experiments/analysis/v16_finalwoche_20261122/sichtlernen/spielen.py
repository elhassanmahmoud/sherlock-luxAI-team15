"""Evaluate the public visibility estimator in complete course games on fresh low-sight maps."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import numpy as np

from sicht import HERE,NAMES,Scout
from erheben import PACKAGE,V16,panel
sys.path.insert(0,str(HERE.parent))
from bewegungsvergleich import run as compare
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from luxai_s3.wrappers import LuxAIS3GymEnv


def run(folder,offset,stride,report_only):
    if os.getenv("PYTHONHASHSEED")!="0" or sha256(PACKAGE.read_bytes()).hexdigest()!=V16 or not verify():
        raise ValueError("Invalid policy identity")
    limit_threads()
    out=HERE/"offline.json"
    metrics=json.loads(out.read_text())
    if (not metrics["eligible"] or not all(metrics["gates"].values()) or list(NAMES)!=metrics["estimate"]["names"]
            or metrics["policy"]!=sha256((HERE/"sicht.py").read_bytes()).hexdigest()
            or metrics["plan"]!=sha256((HERE/"PLAN.md").read_bytes()).hexdigest()):
        raise ValueError("The offline evidence is missing")
    weights=np.array(metrics["estimate"]["w"],dtype=float),float(metrics["estimate"]["bias"])
    seeds=panel(160369000,40)
    if report_only:
        compare(folder,HERE,160369000,selected=seeds)
        result=HERE/"auswahl_ergebnis.json"
        r=json.loads(result.read_text())
        s=r["opponents"]["solution92"]
        r["gates"]["additional_solution"]=s["new_wins"]>s["lost_wins"]
        r["qualifies"]=all(r["gates"].values())
        result.write_text(json.dumps(r,indent=2)+"\n")
        return
    signature=sha256(out.read_bytes()+(HERE/"spielen.py").read_bytes()+(HERE/"sicht.py").read_bytes()).hexdigest()
    cases=[(s,side,o,a) for s in seeds for side in ("player_0","player_1") for o in ("solution92","kaggle3","v16")
           for a in (("adviser",) if o=="v16" else ("original","adviser"))]
    folder.mkdir(parents=True,exist_ok=True)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed,side,rival,arm in cases[offset::stride]:
            path=folder/f"{seed}_{side}_{rival}_{arm}.json"
            if path.exists():
                row=json.loads(path.read_text())
                if ((row["seed"],row["side"],row["opponent"],row["arm"])!=(seed,side,rival,arm)
                       or row["model"]!=signature or row["steps"]!=303):
                    raise ValueError(f"Inconsistent previous seat {path.name}")
                continue
            agent=r3_package_agent(side,PACKAGE)
            if arm=="adviser":agent=Scout(agent,weights)
            other="player_0" if side=="player_1" else "player_1"
            opponent=r3_package_agent(other,PACKAGE) if rival=="v16" else make_opponent(rival,other)
            r=play_game(env,agent,opponent,seed,side,train=False)
            require_no_agent_errors(agent.base if arm=="adviser" else agent,opponent)
            if (r["steps"]!=303 or r["point_counting_version"]!=2 or r["our_wins"]+r["opp_wins"]!=3
                    or r["game_win"]!=int(r["our_wins"]>=2) or int(agent.env_cfg["unit_sensor_range"])>2):
                raise ValueError("Invalid completed low-vision game")
            row={k:r[k] for k in ("seed","side","steps","point_counting_version","our_wins","opp_wins","our_points","opp_points","game_win")}
            row.update(opponent=rival,arm=arm,model=signature,changes=getattr(agent,"changed",0))
            tmp=path.with_suffix(".pending")
            tmp.write_text(json.dumps(row)+"\n")
            tmp.replace(path)
            print(path.name,flush=True)
    finally:
        env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    p.add_argument("--offset",type=int,default=0)
    p.add_argument("--stride",type=int,default=1)
    p.add_argument("--report",action="store_true")
    a=p.parse_args()
    if not 0<=a.offset<a.stride:p.error("Invalid partition")
    run(a.folder,a.offset,a.stride,a.report)
