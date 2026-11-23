"""One registered 48-map panel, conditional on the retrospective archive decision."""
import argparse
from datetime import datetime
import gzip
import json
import os
from pathlib import Path
import random

import jax
import numpy as np
import torch

from archiv import HERE, FIELD, ROOT, RAW, CUTOFF, THREADS, CurrentMonitor, check, create, decode, frozen, limit_threads, make_opponent, PACKAGE, play_game, require_no_agent_errors, r3_package_agent, sha, stamp, write_once
from auswertung import ARMS,csv_out,run
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import common_source

DEST=HERE/"sicht1"


def series():
    prior=json.loads((HERE/"archivbilanz.json").read_bytes())
    check(prior["passed"] and all(prior["gates"].values()) and prior["identity"]==stamp(frozen()),"Retrospective gate failed")
    audit=json.loads((HERE/"archiv_nachpruefung.json").read_bytes())
    check(audit["passed"] and audit["archival_result_sha256"]==sha(HERE/"archivbilanz.json"),"Missing independent archive check")
    inputs={**frozen(),str((HERE/"archivbilanz.json").relative_to(ROOT)):sha(HERE/"archivbilanz.json"),
            str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str((HERE/"archivbilanz.py").relative_to(ROOT)):sha(HERE/"archivbilanz.py")}
    seeds=np.arange(164080000,164081000,dtype=np.int32)
    public=np.asarray(jax.jit(jax.vmap(sensor))(seeds))
    cards=seeds[public==1][:48].tolist()
    check(len(cards)==48,"Incomplete fresh selection")
    return dict(inputs=inputs,common=common_source(),cards=cards,selection="first 48 sensor-1 cards from 164080000")


def play(env,key,sig):
    seed,t,arm,op=key
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    side=f"player_{t}";other=f"player_{1-t}"
    actor=create(side) if arm=="probe" else r3_package_agent(side,PACKAGE)
    enemy=make_opponent("solution92",other) if op=="solution92" else r3_package_agent(other,PACKAGE)
    m=CurrentMonitor(env,t,actor if arm=="probe" else None,"confirm")
    won=play_game(m,actor,enemy,seed,side,False)
    require_no_agent_errors(actor.base if arm=="probe" else actor,enemy)
    check(m.sensor==1 and m.turn==303 and m.counts==[303,303] and len(m.matches)==3 and
          int(sum(z["win"] for z in m.matches)>=2)==won["game_win"],"Incomplete game")
    attempt=actor.attempt if arm=="probe" else None
    if arm=="probe":
        check(actor.changes==int(m.detail is not None) and m.command_count==4848 and
              bool(attempt and not attempt["veto"])==bool(m.detail),"Guard or change count")
        if attempt and attempt["veto"]:
            check(actor.changes==0 and attempt["bounds"]==[0.,0.] and attempt["prior_position"]==attempt["event"]["xy"],"Wrong veto")
    return dict(seed=seed,team=t,arm=arm,opponent=op,source=sig,sensor=m.sensor,turns=m.turn,win=won["game_win"],
        matches=m.matches,sight=m.first_sight,credit=m.first_credit,profile=m.profile,prefix=m.prefix if arm=="reference" else None,
        current=m.current if arm=="reference" else None,event=m.detail,attempt=attempt,hash=m.digest.hexdigest(),caught_errors=[0,0],
        actions_checked=m.counts,commands_vs_original=m.command_count)


def score(raw,cards,sig):
    res,seats,events=run(raw,cards,"confirm",sig)
    veto=[r for r in raw if r["attempt"] and r["attempt"]["veto"]]
    affected={r["seed"] for r in veto}
    res["veto_count"]=len(veto);res["veto_maps"]=len(affected)
    res["veto_rows"]=[dict(seed=r["seed"],team=r["team"],opponent=r["opponent"],**r["attempt"]) for r in veto]
    res["gates"]["two_fresh_veto_cards"]=len(affected)>=2
    res["passed"]=all(res["gates"].values())
    return res,seats,events


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("mode",choices=("play","score"))
    p.add_argument("--lane",type=int,default=0);p.add_argument("--stride",type=int,default=4)
    a=p.parse_args()
    check(0<=a.lane<a.stride and os.getenv("PYTHONHASHSEED")=="0" and all(os.getenv(k)=="1" for k in THREADS),"Worker environment")
    limit_threads()
    reg=series();cards=reg["cards"];sig=stamp(reg)
    fs=RAW/"frisch"
    write_once(fs/"manifest.json",reg)
    jobs=[(s,t,k,o) for s in cards for t in (0,1) for k,o in ARMS]
    def target(k):return fs/"spiele"/("_".join(map(str,k))+".json")
    if a.mode=="play":
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in jobs[a.lane::a.stride]:
                f=target(k)
                if f.exists():
                    check(json.loads(f.read_bytes())["source"]==sig,"Old inputs")
                    continue
                check(datetime.now(CUTOFF.tzinfo)<CUTOFF,"Deadline")
                write_once(f,play(env,k,sig))
                print(*k,flush=True)
        finally:env.close()
        check(series()==reg,"Inputs changed")
        return
    check(set((fs/"spiele").glob("*.json"))=={target(k) for k in jobs},"Incomplete stage")
    rows=[json.loads(target(k).read_bytes()) for k in jobs]
    result,pairs,events=score(rows,cards,sig)
    DEST.mkdir(parents=True,exist_ok=True)
    archive=DEST/"partien.jsonl.gz"
    blob=b"".join(json.dumps(r,sort_keys=True,separators=(",",":")).encode()+b"\n" for r in rows)
    if not archive.exists():archive.write_bytes(gzip.compress(blob,mtime=0))
    check(gzip.decompress(archive.read_bytes())==blob and score(decode(archive),cards,sig)==(result,pairs,events),"Archive mismatch")
    write_once(DEST/"manifest.json",reg);write_once(DEST/"ergebnis.json",result)
    csv_out(DEST/"sitze.csv",pairs)
    if events:
        csv_out(DEST/"eingriffe.csv",events)
    else:
        (DEST/"eingriffe.csv").write_text("seed,side,opponent,tick,match,region,arrived,scored,own_credit,opp_credit\n")
    print(result["passed"],result["gates"],flush=True)


if __name__=="__main__":main()
