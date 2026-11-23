"""Reconstruct public unchanged prefixes only for archived first attempts; deduplicate direct controls by card."""
import argparse
from collections import Counter
import gzip
import json
import os
from pathlib import Path
import random
import sys

import numpy as np
import torch

HERE=Path(__file__).resolve().parent
FIELD=HERE.parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(FIELD/"bestaetigung"))
from auswertung import check,decode,sha
from experiments.analysis.relictsuche_20261123.feldprobe.bestaetigung.spielen import CurrentMonitor,action_hash
from experiments.analysis.relictsuche_20261123.feldprobe.rueckweg.kandidat import create,reverse_veto
from experiments.analysis.relictsuche_20261123.feldprobe.kandidat import PACKAGE
from experiments.analysis.relictsuche_20261123.feldprobe.signalmodell import NAMES
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,THREADS,write_once,stamp
from scripts.common import play_game,make_opponent
from scripts.experiment import limit_threads
from scripts.r3_package import r3_package_agent
from scripts.par_eval import require_no_agent_errors

WORK=Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123")
RAW=WORK/"rueckweg"
ARCHIVES={"auswahl":FIELD/"ganze_partien.jsonl.gz","bestaetigung":FIELD/"bestaetigung/sicht1/partien.jsonl.gz"}


class EndPrefix(Exception):pass


class BeforeChoice(CurrentMonitor):
    def __init__(self,env,actor,row):
        super().__init__(env,row["team"],actor,"confirm")
        self.expected=row
        self.proof=None

    def step(self,actions):
        r=self.expected
        historic=r["event"]
        t=historic["t"]
        candidate=self.probe
        if self.turn<t:
            check(candidate.attempt is None and np.array_equal(self.original,actions[self.side]),"A new earlier attempt")
            return super().step(actions)
        check(self.turn==t and candidate.attempt is not None,"Historical first proposal not reached")
        attempt=candidate.attempt
        check(all(attempt["event"][k]==v for k,v in historic.items() if k in attempt["event"]),"Different first move")
        check(self.digest.hexdigest()==historic["prefix"] and self.profile==r["profile"][:t] and self.original is not None,"Past action or score prefix differs")
        if "current" in historic:
            check([action_hash(self.original),action_hash(actions[f"player_{1-self.team}"])]==historic["current"],"Current proposals differ")
        cmd=actions[self.side]
        diff=np.flatnonzero(np.any(cmd!=self.original,axis=1)).tolist()
        check(diff==([] if attempt["veto"] else [historic["u"]]),"Unexpected action difference")
        self.proof=dict(**attempt,seed=r["seed"],team=r["team"],opponent=r["opponent"],prefix=historic["prefix"],prior_turns=t,
                        scored=historic["scored"],arrived=historic["arrived"],candidate_original_hash=r["hash"])
        raise EndPrefix


def prefix(env,row):
    s=row["seed"];t=row["team"];side=f"player_{t}";other=f"player_{1-t}"
    random.seed(s);np.random.seed(s);torch.manual_seed(s)
    actor=create(side)
    rival=make_opponent("solution92",other) if row["opponent"]=="solution92" else r3_package_agent(other,PACKAGE)
    mon=BeforeChoice(env,actor,row)
    try:play_game(mon,actor,rival,s,side,False)
    except EndPrefix:pass
    require_no_agent_errors(actor.base,rival)
    check(mon.proof is not None,"Missing prefix")
    return mon.proof


def frozen():
    inputs=[HERE/"PLAN.md",HERE/"kandidat.py",HERE/"archiv.py",FIELD/"modell.json",FIELD/"kandidat.py",FIELD/"signalmodell.py",PACKAGE,
            FIELD/"bestaetigung/spielen.py",FIELD/"bestaetigung/auswertung.py",FIELD/"duelle.py",*ARCHIVES.values()]
    return {str(p.relative_to(ROOT)):sha(p) for p in inputs}


def key(r):return (r["seed"],r["team"],r["opponent"])


def outcome_source():
    return {stage:decode(path) for stage,path in ARCHIVES.items()}


def list_cases(raw):
    return [(stage,r) for stage,rows in raw.items() for r in rows if r["arm"]=="probe" and r["event"]]


def calculate_earlier():
    from experiments.analysis.relictsuche_20261123.feldprobe.signalmodell import NAMES
    output={}
    for split in ("train","valid"):
        records=decode(FIELD/(split+"_karten.jsonl.gz"))
        vals=[]
        for r in records:
            text=r["full"]["first"]
            if text is None:continue
            t=int(text["turn"]);uid,d,x,y,_,_=text["key"]
            s=r["seed"];team=r["team"]
            stem=f"{s}-{team}"
            original=WORK/"spaetort"/split
            receipt=json.loads((original/(stem+".json")).read_bytes())
            with np.load(original/receipt["public"]) as dat:
                check(sha(original/receipt["public"])==receipt["public_sha"],"Changed tape")
                prev=dat["position"][t-1,team]
                now=dat["position"][t,team]
                prev_alive=dat["units_mask"][t-1,team] & (dat["energy"][t-1,team].reshape(-1)>=0)
                now_alive=dat["units_mask"][t,team] & (dat["energy"][t,team].reshape(-1)>=0)
                cmds=dat["commands"][t-1,:,0]
            with np.load(WORK/"feldprobe"/split/(stem+".npz")) as choices:
                ix=np.flatnonzero((choices["step"]==t) & np.all(choices["key"]==np.asarray(text["key"]),axis=1))
                check(len(ix)==1,"Learned first choice absent")
                features=choices["x"][ix[0],0]
            v=reverse_veto(uid,d,(x,y),features,prev,prev_alive,cmds,now,now_alive)
            vals.append(dict(seed=s,team=team,opponent=r["opponent"],t=t,veto=bool(v),truth=text["actual"]))
        output[split]=dict(maps=len(records),attempts=len(vals),veto=sum(v["veto"] for v in vals),records=vals)
    write_once(HERE/"fruehe_tafeln.json",output)


def path(stage,row):
    return RAW/"prefix"/stage/("_".join(map(str,key(row)))+".json")


def direct_plan(raw,records):
    controls={}
    for stage,rows in raw.items():
        by={(r["seed"],r["team"]):r for r in rows if r["opponent"]=="v16"}
        for s in sorted({r["seed"] for r in rows}):
            needs=[t for t in (0,1) if records.get((stage,s,t,"v16"),{}).get("veto")]
            if not needs:continue
            inactive=next((by[s,t] for t in (0,1) if not by[s,t]["event"]),None)
            controls[stage,s]=(needs,inactive)
    return controls


def original_control(env,seed,team):
    side=f"player_{team}";other=f"player_{1-team}"
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    a=r3_package_agent(side,PACKAGE);b=r3_package_agent(other,PACKAGE)
    m=CurrentMonitor(env,team,None,"confirm"); outcome=play_game(m,a,b,seed,side,False)
    require_no_agent_errors(a,b)
    check(m.turn==303 and m.counts==[303,303] and len(m.matches)==3 and outcome["game_win"]==int(sum(x["win"] for x in m.matches)>=2),"Bad direct control")
    return dict(seed=seed,team=team,win=outcome["game_win"],matches=m.matches,prefix=m.prefix,current=m.current,hash=m.digest.hexdigest())


def main():
    from datetime import datetime
    from luxai_s3.wrappers import LuxAIS3GymEnv
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("prefix","control","early","score"))
    p.add_argument("--lane",type=int,default=0);p.add_argument("--stride",type=int,default=1)
    a=p.parse_args()
    check(0<=a.lane<a.stride and os.getenv("PYTHONHASHSEED")=="0" and all(os.getenv(k)=="1" for k in THREADS),"Worker setup")
    limit_threads()
    frozen_files=frozen();sid=stamp(frozen_files)
    write_once(RAW/"manifest.json",dict(inputs=frozen_files,stamp=sid))
    if a.mode=="early":
        calculate_earlier();return
    raw=outcome_source()
    jobs=list_cases(raw)
    if a.mode=="prefix":
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for stage,row in jobs[a.lane::a.stride]:
                check(datetime.now(CUTOFF.tzinfo)<CUTOFF,"Deadline")
                f=path(stage,row)
                if f.exists():
                    check(json.loads(f.read_bytes())["identity"]==sid,"Old prefix")
                    continue
                write_once(f,dict(identity=sid,**prefix(env,row)))
                print(stage,*key(row),flush=True)
        finally:env.close()
        check(frozen()==frozen_files,"Changed prefix source");return
    records={(stage,*key(r)):json.loads(path(stage,r).read_bytes()) for stage,r in jobs}
    check(len(records)==len(jobs) and all(v["identity"]==sid for v in records.values()),"Wrong prefixes")
    controls=direct_plan(raw,records)
    if a.mode=="control":
        env=None
        try:
            for (stage,s),(needed,source) in list(controls.items())[a.lane::a.stride]:
                if source is not None:continue
                file=RAW/"control"/stage/f"{s}.json"
                if file.exists():continue
                check(datetime.now(CUTOFF.tzinfo)<CUTOFF,"Deadline")
                if env is None:env=LuxAIS3GymEnv(numpy_output=True)
                write_once(file,dict(identity=sid,**original_control(env,s,needed[0])))
                print(stage,s,flush=True)
        finally:
            if env:env.close()
        return
    from archivbilanz import calculate
    calculate(raw,records,controls,RAW,HERE,sid)


if __name__=="__main__":main()
