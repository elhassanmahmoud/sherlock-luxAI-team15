"""Separate one-time registered confirmation, and the general stage only after it passes."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path

import jax
import numpy as np

from duell import HERE, WORK, CUTOFF, THREADS, analyze, identities, limit_threads, play, require, save_archive, sensor, sha, stamp, validate, write_once

OUT = {"confirm":"bestaetigung", "general":"allgemein"}


def select(phase):
    if phase == "general":
        return list(range(162210000, 162210160))
    seeds = np.arange(162200000, 162201000, dtype=np.int32)
    cards = seeds[np.asarray(jax.jit(jax.vmap(sensor))(seeds)) == 1][:120].tolist()
    require(len(cards)==120, "Too few eligible confirmation cards")
    return cards


def prepare(phase):
    prev = "ganzspiel" if phase=="confirm" else OUT["confirm"]
    result = json.loads((HERE/prev/"ergebnis.json").read_text())
    require(result["nominee"]=="flotte" and result["candidates"]["flotte"]["passed"], "Previous stage did not qualify")
    if phase=="confirm":
        verification=json.loads((HERE/prev/"nachpruefung.json").read_text())
        require(all(verification["recomputed_conditions"]) and verification["bad_game_rows"]==0, "Unverified screening")
    else:
        verification=json.loads((HERE/prev/"nachpruefung.json").read_text())
        require(verification["passed"] and verification["bad_rows"]==0, "Unverified confirmation")
    base, old = identities()
    base["post_screen"] = dict(plan=sha(HERE/"BESTAETIGUNGSPLAN.md"), runner=sha(Path(__file__)),
                                prior_result=sha(HERE/prev/"ergebnis.json"))
    sources={name:{**src,"common":stamp(base)} for name,src in old.items()}
    cards=select(phase)
    return {"common":base,"identities":sources,"cards":cards,"phase":phase}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase",choices=OUT)
    p.add_argument("mode",choices=("play","score"))
    p.add_argument("--lane",type=int,default=0)
    p.add_argument("--stride",type=int,default=2)
    a=p.parse_args()
    require(0<=a.lane<a.stride and os.getenv("PYTHONHASHSEED")=="0" and all(os.getenv(k)=="1" for k in THREADS),
            "Wrong lane or thread configuration")
    phase=a.phase
    series=prepare(phase)
    cards,sources=series["cards"],series["identities"]
    dest=WORK.parent/OUT[phase]
    report=HERE/OUT[phase]
    write_once(dest/"serie.json",series)
    tasks=[(phase,s,t,agent,opp) for s in cards for t in (0,1)
           for agent,opp in (("reference","solution92"),("flotte","solution92"),("flotte","v16"))]

    def path(k):
        return dest/k[3]/f"{k[1]}_{k[2]}_{k[4]}.json"

    if a.mode=="play":
        from luxai_s3.wrappers import LuxAIS3GymEnv
        from experiments.analysis.relictsuche_20261123.flottenblick.kandidat import create
        limit_threads()
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in tasks[a.lane::a.stride]:
                file=path(k)
                if file.exists():
                    validate(json.loads(file.read_text()),k,stamp(sources[k[3]]))
                    continue
                require(datetime.now(CUTOFF.tzinfo)<CUTOFF, "Deadline reached")
                actors=[]
                def make(side):
                    agent=create(side)
                    actors.append(agent)
                    return agent
                row=play(env,k,stamp(sources[k[3]]),make if k[3]=="flotte" else None)
                if actors:
                    require(len(actors)==1 and len(row["events"])<=8, "Extra agent or overlong intervention")
                    event=actors[0].event
                    if row["events"]:
                        require(event is not None and all(e[1]==event["uid"] and event["step"]<=e[0]<event["step"]+8
                            and e[0]<row["sight"] and e[0]<=row["credit"] for e in row["events"]),"Ineligible intervention")
                    row["opportunity"]=event
                write_once(file,row)
                print(*k[1:],flush=True)
        finally:
            env.close()
        require(prepare(phase)==series,"Frozen sources changed during stage")
        return
    files={f for name in ("reference","flotte") for f in (dest/name).glob("*.json")}
    require(files=={path(k) for k in tasks}, "Incomplete stage, no results opened")
    rows=[json.loads(path(k).read_text()) for k in tasks]
    result=analyze(phase,cards,["flotte"],rows,sources)
    report.mkdir(parents=True,exist_ok=True)
    archive=save_archive(rows,report/"partien.jsonl.gz")
    require(result==analyze(phase,cards,["flotte"],archive,sources),"Archive does not reproduce result")
    result["study"]="flottenblick"
    write_once(report/"serie.json",series)
    write_once(report/"ergebnis.json",result)
    print(phase, result["candidates"]["flotte"]["gates"],flush=True)


if __name__=="__main__":
    main()
