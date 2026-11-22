"""Create the public map panel and run one of two disjoint fixed game lanes."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys

import numpy as np
from staffel import HERE, ROOT, R3, R3_SHA, V16, V16_SHA, Relay, r3_package_agent
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import require_no_agent_errors


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def save(path, value):
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    with tmp.open("w") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(path)


def panel():
    import jax
    sys.path.insert(0, str(HERE.parent / "kartenparameter"))
    from auswerten import generate
    seeds = np.arange(160362000, 160362500, dtype=np.int32)
    sensor = np.asarray(jax.jit(jax.vmap(generate))(seeds))[:,0]
    maps = [(int(s),int(v)) for s,v in zip(seeds,sensor) if v in (1,2)][:40]
    if len(maps) != 40:
        raise ValueError("Too few eligible seeds")
    result = dict(low=maps, confirmation=list(range(160363000,160363120)), plan=digest(HERE/"PLAN.md"))
    path = HERE/"karten.json"
    if path.exists():
        if json.loads(path.read_text()) != json.loads(json.dumps(result)):
            raise ValueError("Map list changed")
    else:
        save(path,result)


def validated_maps(phase):
    data=json.loads((HERE/"karten.json").read_text())
    if data["plan"] != digest(HERE/"PLAN.md"):
        raise ValueError("Plan changed")
    if phase == "auswahl":
        seeds=[s for s,v in data["low"]]
        if len(seeds)!=40 or sorted(set(seeds))!=seeds or not all(
                160362000<=s<160362500 and v in (1,2) for s,v in data["low"]):
            raise ValueError("Low visibility panel")
        return seeds
    if phase!="bestaetigung" or data["confirmation"] != list(range(160363000,160363120)):
        raise ValueError("Confirmation panel")
    return data["confirmation"]


def jobs(phase):
    seeds=validated_maps(phase)
    return [(s,t,o,a) for i,s in enumerate(seeds) for t in (0,1)
            for o in ("solution92","kaggle3","v16") for a in ("original","staffel")
            if o!="v16" or (a=="staffel" and i<40)]


def binding(phase):
    names = ["PLAN.md","staffel.py","technik.py","technik_0.json","technik_1.json","karten.json","spielen.py"]
    if phase == "bestaetigung":
        prior = HERE/"auswahl_ergebnis.json"
        if not json.loads(prior.read_text())["passed"]:
            raise ValueError("First stage failed")
        names += [prior.name]
    return {n:digest(HERE/n) for n in names}


def valid(row,key,source):
    if (tuple(row[k] for k in ("seed","team","opponent","arm"))!=key or row["source"]!=source
            or row["steps"]!=303 or row["point_counting_version"]!=2
            or row["our_wins"]+row["opp_wins"]!=3 or row["game_win"]!=int(row["our_wins"]>=2)
            or min(row["our_points"],row["opp_points"])<0
            or row["r3_steps"]!=(41 if row["sensor"]<=2 and row["arm"]=="staffel" else 0)):
        raise ValueError(f"Invalid course-game record {key}")


def run(phase, lane, output):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    import torch
    limit_threads()
    if digest(V16)!=V16_SHA or digest(R3)!=R3_SHA or not verify() or os.environ.get("PYTHONHASHSEED")!="0":
        raise ValueError("Package, opponent or hash seed differs")
    contract=binding(phase)
    source=sha256(json.dumps(contract,sort_keys=True).encode()).hexdigest()
    sensors=dict(json.loads((HERE/"karten.json").read_text())["low"])
    output.mkdir(parents=True,exist_ok=True)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for key in jobs(phase)[lane::2]:
            seed,team,opponent,arm=key
            target=output/("_".join(map(str,key))+".json")
            if target.exists():
                valid(json.loads(target.read_text()),key,source)
                continue
            random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
            side, other=f"player_{team}",f"player_{1-team}"
            actor=Relay(side) if arm=="staffel" else r3_package_agent(side,V16)
            rival=r3_package_agent(other,V16) if opponent=="v16" else make_opponent(opponent,other)
            result=play_game(env,actor,rival,seed,side,False)
            base=actor.base if arm=="staffel" else actor
            require_no_agent_errors(base,rival)
            if arm=="staffel" and actor.r3 is not None:
                require_no_agent_errors(actor.r3,rival)
            sensor=int(base.env_cfg["unit_sensor_range"])
            if phase=="auswahl" and sensor!=sensors[seed]:
                raise ValueError("Actual public parameter differs from registered maps")
            row=dict(zip(("seed","team","opponent","arm"),key))
            row.update({k:result[k] for k in ("steps","game_win","our_wins","opp_wins","our_points","opp_points",
                                              "point_counting_version","secs")})
            row.update(source=source,sensor=sensor,r3_steps=actor.early if arm=="staffel" else 0,
                       divergent_steps=actor.changed_steps if arm=="staffel" else 0,
                       divergent_units=actor.changed_units if arm=="staffel" else 0)
            valid(row,key,source)
            save(target,row)
    finally:
        env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("phase",choices=("karten","auswahl","bestaetigung"))
    p.add_argument("lane",type=int,choices=(0,1),nargs="?")
    p.add_argument("output",type=Path,nargs="?")
    args=p.parse_args()
    if args.phase=="karten":
        panel()
    else:
        run(args.phase,args.lane,args.output)
