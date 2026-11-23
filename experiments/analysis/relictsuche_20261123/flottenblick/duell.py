"""Complete the registered 40-map comparison using the original course game and audited monitor."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys

import jax
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0,str(ROOT))
shared = HERE.parent / "vergleich"
sys.path.insert(0,str(shared))
from auswerten import analyze, save_archive
from panel import sensor
from spielen import CUTOFF, THREADS, common_source, inputs, play, require, sha, stamp, validate, write_once
from scripts.experiment import limit_threads

WORK = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/flottenblick/ganzspiel")
REPORT = HERE / "ganzspiel"


def roster():
    seeds = np.arange(161620000,161621000,dtype=np.int32)
    selected = seeds[np.asarray(jax.jit(jax.vmap(sensor))(seeds)) == 1][:40].tolist()
    require(len(selected)==40 and len(set(selected))==40, "Incomplete sensor-1 roster")
    return selected


def identities():
    approval = json.loads((HERE/"freigabe_spielpruefung.json").read_text())
    require(approval["qualifies_for_game_screen"] and approval["real_exclusive_gain"]["mean"] > 0 and
            approval["brier_gain"]["ci95"][0] > 0, "Eligibility not established")
    main = HERE/"kandidat.py"
    files = [ROOT/p for p in approval["frozen"] if ROOT/p != main]
    signed = inputs(main,files)
    require(signed["files"] == approval["frozen"], "Frozen fleet weights or runtime source differ")
    base = common_source()
    base["fleet_study"] = {p.name:sha(p) for p in (HERE/"VERGLEICHSPLAN.md",HERE/"duell.py",
        HERE/"freigabe_spielpruefung.json", shared/"auswerten.py")}
    sources = {name:dict(id=name,common=stamp(base),candidate=(signed if name=="flotte" else None))
               for name in ("reference","flotte")}
    return base,sources


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("play","score"))
    p.add_argument("--lane", type=int,default=0)
    p.add_argument("--stride",type=int,default=2)
    p.add_argument("--work",type=Path,default=WORK)
    a=p.parse_args()
    require(0 <= a.lane < a.stride and os.getenv("PYTHONHASHSEED")=="0" and all(os.environ.get(k)=="1" for k in THREADS),
            "Invalid lane or randomness")
    cards = roster()
    base, uid = identities()
    series = {"common":base,"identities":uid,"cards":cards}
    write_once(a.work/"serie.json",series)
    tasks = [("discovery",seed,t,agent,opp) for seed in cards for t in (0,1)
             for agent,opp in (("reference","solution92"),("flotte","solution92"),("flotte","v16"))]
    def place(k):
        return a.work/k[3]/f"{k[1]}_{k[2]}_{k[4]}.json"
    if a.action=="play":
        from luxai_s3.wrappers import LuxAIS3GymEnv
        from experiments.analysis.relictsuche_20261123.flottenblick.kandidat import create
        limit_threads()
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in tasks[a.lane::a.stride]:
                dest=place(k)
                if dest.exists():
                    validate(json.loads(dest.read_text()),k,stamp(uid[k[3]]))
                    continue
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:
                    raise RuntimeError("Project deadline reached")
                actors=[]
                def factory(side):
                    agent=create(side)
                    actors.append(agent)
                    return agent
                row=play(env,k,stamp(uid[k[3]]),factory if k[3]=="flotte" else None)
                if actors:
                    require(len(actors)==1 and len(row["events"])<=8, "Multiple fleet agents or long route")
                    event=actors[0].event
                    if row["events"]:
                        require(event is not None and all(
                            e[1]==event["uid"] and event["step"]<=e[0]<event["step"]+8 and
                            e[0]<row["sight"] and e[0]<=row["credit"] for e in row["events"]),
                            "Scout changed outside its public eligible period")
                    row["opportunity"]=event
                write_once(dest,row)
                print(k[1],k[2],k[3],k[4],flush=True)
        finally:
            env.close()
        require(identities()==(base,uid),"Frozen sources changed")
        return
    rows=[]
    for k in tasks:
        path=place(k)
        require(path.is_file(),f"Incomplete registered panel: {path.name}")
        rows.append(json.loads(path.read_text()))
    result=analyze("discovery",cards,["flotte"],rows,uid)
    result["study"]="flottenblick"
    REPORT.mkdir(exist_ok=True)
    save_archive(rows, REPORT/"partien.jsonl.gz")
    write_once(REPORT/"serie.json",series)
    write_once(REPORT/"ergebnis.json",result)
    print(result["candidates"]["flotte"]["gates"],flush=True)


if __name__=="__main__":
    main()
