"""Course games for the separate idle-ship study, using the audited first-relic monitor."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent/"vergleich"))
from auswerten import analyze, save_archive
from panel import sensor
from spielen import CUTOFF, THREADS, common_source, inputs, play, require, sha, stamp, validate, write_once
from scripts.experiment import limit_threads


def cards_for(stage):
    import jax
    first, size = {"discovery": (161520000, 40), "confirm": (161530000, 120), "general": (161540000, 160)}[stage]
    seeds = np.arange(first, first + size*8, dtype=np.int32)
    if stage != "general":
        seeds = seeds[np.asarray(jax.jit(jax.vmap(sensor))(seeds)) == 1]
    result = list(map(int, seeds[:size]))
    require(len(result)==size and len(set(result))==size, "Wrong map panel")
    return result


def identities():
    common = common_source()
    common["followup"] = {p.name:sha(p) for p in (HERE/"PLAN.md", HERE/"duell.py")}
    ref = dict(id="reference", common=stamp(common), candidate=None)
    prior = HERE.parent/"zielschaetzer"
    candidate = dict(id="stand", common=stamp(common),
                     candidate=inputs(HERE/"steuern.py", [HERE/"modell.json", prior/"kandidat.py", prior/"ort.json"]))
    return {"reference":ref, "stand":candidate}


def check_gate(stage, output):
    previous = {"confirm":"discovery", "general":"confirm"}.get(stage)
    if previous and not json.loads((output/previous/"ergebnis.json").read_text())["stand_passed"]:
        raise ValueError("The preceding independent comparison did not qualify")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("work", type=Path)
    p.add_argument("stage", choices=("discovery", "confirm", "general"))
    p.add_argument("action", choices=("play","score"))
    p.add_argument("--lane", type=int, default=0)
    p.add_argument("--stride", type=int, default=1)
    p.add_argument("--reproduce", action="store_true", help="Use a dedicated fresh output folder after the original study")
    args = p.parse_args()
    if not 0 <= args.lane < args.stride or os.getenv("PYTHONHASHSEED")!="0" or any(os.environ.get(k)!="1" for k in THREADS):
        raise ValueError("Invalid worker, randomness or thread setting")
    ids = identities()
    cards = cards_for(args.stage)
    output = HERE/"duelle"
    check_gate(args.stage, output)
    write_once(args.work/args.stage/"serien.json",dict(sources=ids, cards=cards))
    tasks = [(args.stage, seed, team, agent, opponent) for seed in cards for team in (0,1)
             for agent, opponent in (("reference","solution92"),("stand","solution92"),("stand","v16"))]
    def destination(k):
        return args.work/k[0]/k[3]/f"{k[1]}_{k[2]}_{k[4]}.json"
    if args.action == "play":
        from luxai_s3.wrappers import LuxAIS3GymEnv
        from steuern import create
        limit_threads()
        env = LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in tasks[args.lane::args.stride]:
                if not args.reproduce and datetime.now(CUTOFF.tzinfo)>=CUTOFF:
                    break
                dest = destination(k)
                if dest.exists():
                    validate(json.loads(dest.read_text()), k, stamp(ids[k[3]]))
                    continue
                r = play(env,k,stamp(ids[k[3]]),create if k[3]=="stand" else None)
                require(len(r["events"])<=3 and len({e[1] for e in r["events"]})<=1,"Invalid idle-scout changes")
                write_once(dest, r)
        finally:
            env.close()
        require(identities()==ids,"Source drift")
        return
    rows=[json.loads(destination(k).read_text()) for k in tasks]
    result=analyze(args.stage,cards,["stand"],rows,ids)
    s=result["candidates"]["stand"]
    if args.stage=="general":
        passed=s["passed"]
    else:
        q=s["paired"]
        effect=max(q["sight"]["mean"],q["credit"]["mean"])>0 and min(q["sight"]["mean"],q["credit"]["mean"])>=0
        passed=(effect and q["match1win"]["mean"]>=0 and q["whole"]["mean"]>=0 and s["direct_rate"]["mean"]>=.5)
        if args.stage=="confirm":
            passed=passed and max(q["sight"]["ci95"][0],q["credit"]["ci95"][0])>0
    result["stand_passed"]=bool(passed)
    result["nominee"]="stand" if passed else None
    # The parent helper's competing-candidate selection applies to the first three models.
    # The eligibility for this independent follow-up is recorded only in stand_passed.
    result["original_three_candidate_gates"]=s.pop("gates")
    s.pop("passed")
    dest=output/args.stage
    dest.mkdir(exist_ok=True,parents=True)
    save_archive(rows,dest/"partien.jsonl.gz")
    write_once(dest/"ergebnis.json",result)


if __name__=="__main__":
    main()
