"""Run the registered field-probe confirmation and the conditional unfiltered stage."""
import argparse
from datetime import datetime
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys

import jax
import numpy as np
import torch

from auswertung import ARMS, HERE, FIELD, ROOT, check, csv_out, decode, run, sha
sys.path.insert(0,str(ROOT))
from experiments.analysis.relictsuche_20261123.feldprobe.duelle import ProbeMonitor
from experiments.analysis.relictsuche_20261123.feldprobe.kandidat import create, PACKAGE
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,THREADS,common_source,stamp,write_once
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent

WORK=Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/feldprobe")
OUT={"confirm":"sicht1","general":"allgemein"}


def registration(stage):
    prior=FIELD/"duell.json" if stage=="confirm" else HERE/"sicht1/ergebnis.json"
    check(json.loads(prior.read_bytes())["passed"],"Prior stage did not qualify")
    if stage=="general":
        check(json.loads((HERE/"sicht1/nachpruefung.json").read_bytes())["passed"],"Confirmation audit missing")
    approval=json.loads((HERE/"freigabe.json").read_bytes())
    check(all(sha(ROOT/f)==v for f,v in approval["files"].items()) and sha(HERE/"PLAN.md")==approval["plan"] and
          sha(FIELD/"duell.json")==approval["selection"],"Frozen model or plan changed")
    if stage=="confirm":
        all_seeds=np.arange(162800000,162801000,dtype=np.int32)
        cards=list(map(int,all_seeds[np.asarray(jax.jit(jax.vmap(sensor))(all_seeds))==1][:120]))
        check(len(cards)==120,"Incomplete selection")
    else:
        cards=list(range(162810000,162810160))
    sources=dict(common=common_source(),registered=approval,runner=sha(Path(__file__)),analysis=sha(HERE/"auswertung.py"),
                 preceding=sha(prior))
    return dict(stage=stage,cards=cards,sources=sources,identity=stamp(sources))


def action_hash(commands):
    return sha256(np.asarray(commands,dtype="<i4").tobytes()).hexdigest()


class CurrentMonitor(ProbeMonitor):
    def __init__(self,env,team,actor,stage):
        super().__init__(env,team,actor)
        self.phase=stage
        self.current={}
        self.command_count=0

    def step(self,actual):
        t=self.turn
        turn=t%101
        anchor=None
        sid=self.side
        if self.probe is not None:
            check(self.original is not None and self.original.shape==(16,3),"Missing current V16 proposal")
            self.command_count+=len(self.original)
            if self.sensor!=1:
                check(np.array_equal(self.original,actual[sid]) and self.probe.changes==0 and self.probe.event is None,
                      "A normal-vision command differs from V16")
        if 8<=turn<=84 and turn%4==0:
            proposed=self.original if self.probe is not None else actual[sid]
            anchor=[action_hash(proposed),action_hash(actual[f"player_{1-self.team}"])]
            if self.probe is None:
                self.current[t]=anchor
        out=super().step(actual)
        if self.detail is not None and self.detail["t"]==t:
            check(anchor is not None,"Changed a non-probe turn")
            self.detail["current"]=anchor
        return out


def play(env,key,identity,stage):
    seed,team,arm,opponent=key
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    side=f"player_{team}"
    other=f"player_{1-team}"
    candidate=create(side) if arm=="probe" else r3_package_agent(side,PACKAGE)
    bot=make_opponent("solution92",other) if opponent=="solution92" else r3_package_agent(other,PACKAGE)
    w=CurrentMonitor(env,team,candidate if arm=="probe" else None,stage)
    report=play_game(w,candidate,bot,seed,side,False)
    require_no_agent_errors(candidate.base if arm=="probe" else candidate,bot)
    check(w.turn==len(w.profile)==303 and w.counts==[303,303] and len(w.matches)==3 and
          (stage=="general" or w.sensor==1) and not (w.sensor!=1 and w.detail is not None),"Bad runtime")
    if arm=="probe":
        check(candidate.changes==int(w.detail is not None) and w.command_count==303*16,"Unrecorded changes")
    check(sum(m["win"] for m in w.matches)==report["our_wins"] and report["game_win"]==int(report["our_wins"]>=2)
          and all(np.sum(w.profile[j*101:(j+1)*101],axis=0).tolist()==m["points"] for j,m in enumerate(w.matches)),"Scores")
    return dict(seed=seed,team=team,arm=arm,opponent=opponent,source=identity,sensor=w.sensor,turns=303,win=report["game_win"],
                matches=w.matches,sight=w.first_sight,credit=w.first_credit,profile=w.profile,prefix=w.prefix if arm=="reference" else None,
                current=w.current if arm=="reference" else None,event=w.detail,hash=w.digest.hexdigest(),
                caught_errors=[0,0],actions_checked=w.counts,commands_vs_original=w.command_count)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage",choices=OUT)
    p.add_argument("mode",choices=("play","score"))
    p.add_argument("--lane",type=int,default=0);p.add_argument("--stride",type=int,default=4)
    a=p.parse_args();stage=a.stage
    check(0<=a.lane<a.stride and os.getenv("PYTHONHASHSEED")=="0" and all(os.getenv(k)=="1" for k in THREADS),"Worker settings")
    limit_threads()
    series=registration(stage)
    cards=series["cards"]; identity=series["identity"]
    data=WORK/OUT[stage]
    dest=HERE/OUT[stage]
    write_once(data/"manifest.json",series)
    jobs=[(s,t,n,o) for s in cards for t in (0,1) for n,o in ARMS]
    def path(k):
        return data/"spiele"/("_".join(map(str,k))+".json")
    if a.mode=="play":
        from luxai_s3.wrappers import LuxAIS3GymEnv
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in jobs[a.lane::a.stride]:
                f=path(k)
                if f.exists():
                    old=json.loads(f.read_bytes())
                    check(old["source"]==identity and old["turns"]==303,"Stale old game")
                else:
                    check(datetime.now(CUTOFF.tzinfo)<CUTOFF,"Deadline")
                    write_once(f,play(env,k,identity,stage))
                    print(*k,flush=True)
        finally:
            env.close()
        check(series==registration(stage),"Evaluated sources changed")
        return
    check({path(k) for k in jobs}==set((data/"spiele").glob("*.json")),"Incomplete grid")
    rows=[json.loads(path(k).read_bytes()) for k in jobs]
    result,pairs,events=run(rows,cards,stage,identity)
    dest.mkdir(parents=True,exist_ok=True)
    archive=dest/"partien.jsonl.gz"
    blob=b"".join(json.dumps(r,sort_keys=True,separators=(",",":")).encode()+b"\n" for r in rows)
    if not archive.exists():
        archive.write_bytes(gzip.compress(blob,mtime=0))
    check(run(decode(archive),cards,stage,identity)==(result,pairs,events) and gzip.decompress(archive.read_bytes())==blob,"Archive mismatch")
    csv_out(dest/"sitze.csv",pairs);csv_out(dest/"eingriffe.csv",events)
    write_once(dest/"manifest.json",series)
    write_once(dest/"ergebnis.json",result)
    write_once(dest/"nachpruefung.json",dict(passed=result["passed"],game_rows=len(rows),paired_seats=len(pairs),
               archive_sha256=sha(archive),paired_sha256=sha(dest/"sitze.csv"),events_sha256=sha(dest/"eingriffe.csv"),
               inputs=identity,original_proposals_checked=sum(r["commands_vs_original"] for r in rows),
               normal_sight_proposals_checked=sum(r["commands_vs_original"] for r in rows if r["sensor"]!=1)))
    print(stage,result["passed"],result["gates"],flush=True)


if __name__=="__main__":
    main()
