"""Fixed 1,040-game prospective study. Exclusive OS leases prevent duplicate games."""
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

HERE=Path(__file__).resolve().parent
MIDDLE=HERE.parent/"mitte2"
sys.path.insert(0,str(MIDDLE))
from mitte import MODEL_SHA, PACKAGE, SOURCE, SOURCE_SHA, V16, Middle, model, sha, r3_package_agent
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import require_no_agent_errors

FROZEN={"mitte.py":"22f80ab0852f22adc07202da37cd6a20263570a46aa669427be08e6af5bd9620",
        "optionen.py":"c03586fe09e697b5a8ba39dba0c93ae9ffe970b1822730ec9c59a021bca7748e",
        "archiv_partien.jsonl.gz":"5bc24ce8c5d1f2bbbd543b0df46259eaea79b1c782c62965324cf40678b80c28",
        "archiv_ergebnis.json":"e8bf62d6b4798f07641f3caad3e79bce15fc5bb619d4eaf0c76399b515aa5101"}


def contract():
    if (sha(PACKAGE)!=V16 or sha(SOURCE/"wertberater.npz")!=MODEL_SHA or sha(SOURCE/"berater.py")!=SOURCE_SHA or
            any(sha(MIDDLE/k)!=v for k,v in FROZEN.items())):
        raise ValueError("Frozen course package, policy, model or prior evidence changed")
    old=json.loads((MIDDLE/"archiv_ergebnis.json").read_text())
    if old["passed"] or old["gates"]["positive_15"] is not False or old["groups"]["gesamt"]["games_gain"]!=7:
        raise ValueError("Wrong prior study or unrecorded prior failure")
    root=HERE.parents[3]
    support=("scripts/r3_package.py","scripts/common.py","scripts/scoring.py","scripts/kaggle3_opponent.py",
             "scripts/fetch_kaggle3.py","scripts/par_eval.py","scripts/xversion_replay.py")
    eng=Path(importlib.util.find_spec("luxai_s3").origin).parent
    return dict(plan=sha(HERE/"PLAN.md"),runner=sha(HERE/"spielen.py"),policy=FROZEN["mitte.py"],
                options=FROZEN["optionen.py"],student=MODEL_SHA,student_source=SOURCE_SHA,release=V16,
                support={n:sha(root/n) for n in support},
                engine={str(p.relative_to(eng)):sha(p) for p in sorted(eng.rglob("*.py"))})


def signature(m):return sha256(json.dumps(m,sort_keys=True).encode()).hexdigest()


def jobs():
    return [(s,t,o,a) for s in range(160384000,160384120) for t in (0,1)
            for o in ("solution92","kaggle3","v16") for a in ("original","mitte2")
            if o!="v16" or (a=="mitte2" and s<160384040)]


def validate(r,k,source):
    if (tuple(r[f] for f in ("seed","team","opponent","arm"))!=k or r["source"]!=source or
            r["steps"]!=303 or r["point_counting_version"]!=2 or r["our_wins"]+r["opp_wins"]!=3 or
            int(r["our_wins"]>=2)!=r["game_win"] or min(r["our_points"],r["opp_points"])<0 or
            r["changes"] not in (0,1) or (r["changes"]>0)!=(r["event"] is not None)):
        raise ValueError(f"Failed game validation {k}")
    if r["event"]:
        e=r["event"];t=k[1]
        if (k[3]!="mitte2" or not 26<=e["ms"]<=75 or e["step"]!=101+e["ms"] or
                e["value"]<.25 or e["team_points"][t]>=e["team_points"][1-t]):
            raise ValueError(f"Invalid modified command {k}")


def save(path,value):
    tmp=path.with_suffix(f".{os.getpid()}.tmp")
    with tmp.open("w") as f:
        json.dump(value,f,sort_keys=True,separators=(",",":"));f.write("\n");f.flush();os.fsync(f.fileno())
    tmp.replace(path)


def play(env,k,net,source):
    seed,team,opp,arm=k
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    side,other=f"player_{team}",f"player_{1-team}"
    # The network is loaded once per worker; no learning or model state is updated.
    actor=Middle(side,net,True) if arm=="mitte2" else r3_package_agent(side,PACKAGE)
    rival=r3_package_agent(other,PACKAGE) if opp=="v16" else make_opponent(opp,other)
    raw=play_game(env,actor,rival,seed,side,False)
    require_no_agent_errors(actor.base if arm=="mitte2" else actor,rival)
    r=dict(zip(("seed","team","opponent","arm"),k))
    r.update({f:raw[f] for f in ("steps","game_win","our_wins","opp_wins","our_points","opp_points","point_counting_version")})
    r.update(source=source,changes=actor.changed if arm=="mitte2" else 0,event=actor.event if arm=="mitte2" else None)
    validate(r,k,source)
    return r


def run(worker):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    if os.environ.get("PYTHONHASHSEED")!="0" or not verify():
        raise ValueError("Kaggle policy or hash-seed mismatch")
    record=contract();stamp=signature(record);net=model()
    target=HERE/"partien";target.mkdir(exist_ok=True)
    claims=target/".leases";claims.mkdir(exist_ok=True)
    if not (HERE/"herkunft.json").exists():save(HERE/"herkunft.json",record)
    if json.loads((HERE/"herkunft.json").read_text())!=record:raise ValueError("Recorded run contract differs")
    panel=jobs()
    # Assign distinct initial regions without depending on how many future workers join.
    start=(worker*137)%len(panel);panel=panel[start:]+panel[:start]
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for k in panel:
            stem="_".join(map(str,k));dest=target/(stem+".json")
            if dest.exists():
                validate(json.loads(dest.read_text()),k,stamp)
                continue
            with (claims/(stem+".lock")).open("a+") as lease:
                try:fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:continue
                if dest.exists():validate(json.loads(dest.read_text()),k,stamp)
                else:save(dest,play(env,k,net,stamp))
    finally:
        env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("worker",type=int)
    run(p.parse_args().worker)
