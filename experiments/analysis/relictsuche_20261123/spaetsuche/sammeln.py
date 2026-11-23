"""Collect the first fixed number of eligible late openings per opponent, with per-job leases."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

from match import HERE, play
from spielen import CUTOFF, ROOT, SCRATCH as BENCH, common_source, datetime, require, sha, stamp, write_once
from scripts.experiment import limit_threads

WORK = BENCH.parent / "spaetsuche"
QUOTA = {"train": 80, "test": 32}
OPP = ("solution92", "v16")
ALT = ("route", "ziel")


def binding():
    files = [HERE/n for n in ("PLAN.md","kandidat.py","match.py","sammeln.py","karten.py","karten.json")]
    files += [HERE.parent / sub / f for sub, fs in (("routenlernen",("kandidat.py","routes.py","routengewichte.json")),
             ("zielschaetzer",("kandidat.py","ort.json"))) for f in fs]
    frozen = json.loads((HERE.parent/"vergleich/discovery/herkunft.json").read_text())
    for ident in ("route", "ziel"):
        for rel, expected in frozen["sources"][ident]["candidate"]["files"].items():
            require(sha(ROOT/rel) == expected, "Earlier released provider changed")
    return {"course_and_common": stamp(common_source()), "sources": {str(p.relative_to(ROOT)):sha(p) for p in files}}


def panel(which):
    cards = json.loads((HERE/"karten.json").read_text())[which]
    return {opp: [(s, (i//2) % 2, opp) for i,s in enumerate(cards) if i%2 == j] for j,opp in enumerate(OPP)}


def game_path(which, arm, key):
    seed, team, opponent = key
    return WORK/which/arm/f"{seed}_{team}_{opponent}.json"


def claim(path, generate):
    if path.exists():
        return False
    locks = path.parent/".leases"
    locks.mkdir(exist_ok=True, parents=True)
    with (locks/(path.stem+".lock")).open("a+") as f:
        try:
            fcntl.flock(f,fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        if path.exists():
            return False
        write_once(path, generate())
        return True


def run(which, worker):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    require(os.getenv("PYTHONHASHSEED") == "0", "Use the study environment")
    contract = binding()
    write_once(WORK/"herkunft.json", contract)
    identity = stamp(contract)
    series = panel(which)
    selected = {opp:[] for opp in OPP}
    consumed = {opp:0 for opp in OPP}
    quota = QUOTA[which]
    env = LuxAIS3GymEnv(numpy_output=True)
    additions = 0

    def screen(key):
        s,t,o = key
        result = play(env,s,t,o,"reference")
        result["source"] = identity
        return result

    def alternative(key, arm):
        base = json.loads(game_path(which,"reference",key).read_text())
        r = play(env,*key,arm)
        require(r["eligible"] and r["turns"] == 101 and r["features"] == base["features"], "Changed late decision state")
        for field in ("prefix_commands","prefix_observations","seed","team","opponent","sensor"):
            require(r[field] == base[field], f"Original replay diverged at {field}")
        if not r["events"]:
            for f in ("action_hash","match","after70","sight","credit"):
                require(r[f] == base[f], f"Inactive trajectory differed at {f}")
        r["source"] = identity
        return r

    try:
        while any(len(k)<quota for k in selected.values()):
            require(datetime.now(CUTOFF.tzinfo) < CUTOFF,"Study deadline")
            jobs = []
            for opp in OPP:
                seq = series[opp]
                while len(selected[opp])<quota and consumed[opp]<len(seq):
                    key = seq[consumed[opp]]
                    p = game_path(which,"reference",key)
                    if not p.exists():
                        break
                    val = json.loads(p.read_text())
                    require(val["source"] == identity and (val["seed"],val["team"],val["opponent"]) == key, "Foreign screening data")
                    if val["eligible"]:
                        selected[opp].append(key)
                    consumed[opp] += 1
                if len(selected[opp])<quota:
                    require(consumed[opp]<len(seq),"Reserved map screening exhausted")
                    jobs.extend(seq[consumed[opp]:consumed[opp]+4])
            if not jobs:
                break
            shift = (worker*3) % len(jobs)
            for key in jobs[shift:]+jobs[:shift]:
                if claim(game_path(which,"reference",key), lambda:screen(key)):
                    additions += 1
                    break
            else:
                time.sleep(.2)
            if additions and additions % 100 == 0:
                print(which, worker, "screened_here", additions, flush=True)
        desc = {"source": identity, "screened_through_quota": consumed, "selected": {o:[list(k) for k in v] for o,v in selected.items()}}
        write_once(WORK/which/"auswahl.json",desc)
        jobs = [(key,arm) for o in OPP for key in selected[o] for arm in ALT]
        offset = worker*41 % len(jobs)
        for key,arm in jobs[offset:]+jobs[:offset]:
            require(datetime.now(CUTOFF.tzinfo) < CUTOFF,"Study deadline")
            claim(game_path(which,arm,key),lambda:alternative(key,arm))
    finally:
        env.close()
    require(binding() == contract,"Source drift detected during collection")
    print(which,worker,"finished",flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("set",choices=("train","test"))
    p.add_argument("worker",type=int)
    a = p.parse_args()
    run(a.set,a.worker)
