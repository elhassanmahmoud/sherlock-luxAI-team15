"""Test the first publicly chosen probe, both scores at its exact turn and the full game."""
import argparse
from datetime import datetime
import gzip
import hashlib
import json
from pathlib import Path
import random

import numpy as np
import torch
from experiments.analysis.relictsuche_20261123.feldprobe.kandidat import create, PACKAGE
from experiments.analysis.relictsuche_20261123.feldprobe.signalmodell import DELTA,HERE
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import (
    CUTOFF,Monitor,common_source,require,sha,stamp,write_once,
)
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import match_points_after_step,point_tile_map


def source():
    report=json.loads((HERE/"valid.json").read_text())
    tech=json.loads((HERE/"technik.json").read_text())
    require(report["passed"] and report["model_hash"]==sha(HERE/"modell.json")
            and len(tech)==13 and sum(r["choice"] is not None for r in tech)==report["changed"],"Incomplete qualification")
    files=[HERE/name for name in ("PLAN.md","kandidat.py","signalmodell.py","modell.json","duelle.py","valid.json","technik.json")]
    return stamp(dict(common=common_source(),files={p.name:sha(p) for p in files}))


def roster():
    import jax
    x=np.arange(162400000,162401000,dtype=np.int32)
    result=list(map(int,x[np.asarray(jax.jit(jax.vmap(sensor))(x))==1][:48]))
    assert len(result)==48
    return result


class ProbeMonitor(Monitor):
    def __init__(self,env,team,actor):
        super().__init__(env,team,"field")
        self.probe=actor
        self.profile=[]
        self.prefix={}
        self.original=None
        self.detail=None
        if actor:
            base_act=actor.base.act
            def capture(*args,**kw):
                assert self.original is None
                command=base_act(*args,**kw)
                self.original=command.copy()
                return command
            actor.base.act=capture

    def step(self,cmd):
        t=self.turn
        mi,turn=divmod(t,101)
        if turn%4==0 and 8<=turn<=84:
            self.prefix[t]=self.digest.hexdigest()
        before=self.old
        e=None
        if self.probe is not None:
            current=cmd[self.side]
            diff=np.flatnonzero(np.any(current!=self.original,axis=1))
            if len(diff):
                assert len(diff)==1 and self.detail is None and t in self.prefix
                e=self.probe.event
                uid=int(diff[0])
                assert uid==e["u"] and e["t"]==t and tuple(current[uid])==(e["d"],0,0)
                pos=np.asarray(before["units"]["position"][self.team,uid])
                assert list(pos+DELTA[e["d"]])==e["xy"] and self.original[uid,0]==e["old"]
                assert self.old["units_mask"][self.team,uid] and self.old["units"]["energy"][self.team,uid].item()>=30
                assert self.sensor==1 and self.probe.changes==1
                truth=point_tile_map(self.env.state)
                self.detail=dict(**e,prefix=self.prefix[t],
                                 prior_truth=[int(truth[tuple(e[k])]) for k in ("xy","ref")])
            self.original=None
        out=super().step(cmd)
        new=out[0][self.side]
        after=match_points_after_step(before,new,out[4])
        gains=after-before["team_points"]
        self.profile.append([int(gains[self.team]),int(gains[1-self.team])])
        if e:
            st=out[4]["final_state"]
            p=np.asarray(st.units.position)[self.team,e["u"]]
            live=bool(np.asarray(st.units_mask)[self.team,e["u"]] and np.asarray(st.units.energy)[self.team,e["u"],0]>=0)
            self.detail["arrived"]=live and list(p)==e["xy"]
            self.detail["scored"]=self.detail["arrived"] and bool(point_tile_map(st)[tuple(p)])
        return out


def play_one(env,seed,team,arm,opp,identity):
    random.seed(seed)
    torch.manual_seed(seed)
    np.random.seed(seed)
    side=f"player_{team}"
    other=f"player_{1-team}"
    a=create(side) if arm=="probe" else r3_package_agent(side,PACKAGE)
    z=make_opponent("solution92",other) if opp=="solution92" else r3_package_agent(other,PACKAGE)
    m=ProbeMonitor(env,team,a if arm=="probe" else None)
    result=play_game(m,a,z,seed,side,False)
    require_no_agent_errors(a.base if arm=="probe" else a,z)
    assert len(m.profile)==m.turn==303 and m.sensor==1 and len(m.matches)==3
    if arm=="probe":
        assert a.changes==int(m.detail is not None)
    assert sum(x["win"] for x in m.matches)==result["our_wins"] and result["game_win"]==int(result["our_wins"]>=2)
    assert all(np.sum(m.profile[j*101:(j+1)*101],axis=0).tolist()==match["points"] for j,match in enumerate(m.matches))
    return dict(seed=seed,team=team,arm=arm,opponent=opp,source=identity,sensor=m.sensor,turns=m.turn,
                win=result["game_win"],matches=m.matches,sight=m.first_sight,credit=m.first_credit,profile=m.profile,
                prefix=m.prefix if arm=="reference" else None, event=m.detail,hash=m.digest.hexdigest())


def evaluate(rows):
    idx={(r["seed"],r["team"],r["arm"],r["opponent"]):r for r in rows}
    cards=roster()
    assert len(idx)==len(rows)==288
    groups={}
    draws=np.random.default_rng(231123).integers(0,48,(20000,48))
    def metric(vals):
        v=np.asarray(vals)
        return dict(mean=float(v.mean()),ci95=np.percentile(v[draws].mean(1),[2.5,97.5]).tolist())
    for a,o in (("reference","solution92"),("probe","solution92"),("probe","v16")):
        rr=[idx[s,t,a,o] for s in cards for t in (0,1)]
        groups[a+"_"+o]=dict(wins=sum(r["win"] for r in rr),
            matches=np.sum([[m["win"] for m in r["matches"]] for r in rr],axis=0).tolist(),
            changed=sum(r["event"] is not None for r in rr),
            scoring_arrivals=sum(bool(r["event"] and r["event"]["scored"]) for r in rr))
    dv=[]
    im=[]
    active=[]
    for s in cards:
        values=[];gains=[]
        for t in (0,1):
            ref=idx[s,t,"reference","solution92"]
            r=idx[s,t,"probe","solution92"]
            values.append(r["win"]-ref["win"])
            if r["event"]:
                e=r["event"]
                tick=e["t"]
                assert ref["prefix"][str(tick)]==e["prefix"] and ref["profile"][:tick]==r["profile"][:tick]
                change=np.subtract(r["profile"][tick],ref["profile"][tick]).tolist()
                active.append(dict(seed=s,team=t,tick=tick,actual=e["scored"],change=change,dead=e["known_empty"]))
                gains.append(change[0])
            else:
                assert ref["hash"]==r["hash"] and ref["matches"]==r["matches"]
                gains.append(0)
        dv.append(np.mean(values));im.append(np.mean(gains))
    direct=[(idx[s,0,"probe","v16"]["win"]+idx[s,1,"probe","v16"]["win"])/2 for s in cards]
    gates=dict(solution=sum(dv)>=0,direct=np.mean(direct)>=.5,own_immediate=sum(im)>0)
    return dict(groups=groups,games=288,cards=48,solution_difference=metric(dv),direct_rate=metric(direct),
        immediate_own_gain=metric(im),changed_solution=active,gates={k:bool(v) for k,v in gates.items()},passed=bool(all(gates.values())))


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    p.add_argument("mode",choices=("play","score"))
    p.add_argument("lane",type=int,default=0,nargs="?")
    p.add_argument("stride",type=int,default=1,nargs="?")
    a=p.parse_args()
    limit_threads()
    ident=source()
    cards=roster()
    jobs=[(s,t,n,o) for s in cards for t in (0,1) for n,o in (("reference","solution92"),("probe","solution92"),("probe","v16"))]
    def dest(k):
        return a.folder/"spiele"/("_".join(map(str,k))+".json")
    write_once(a.folder/"manifest.json",dict(source=ident,cards=cards))
    if a.mode=="play":
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in jobs[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:
                    break
                f=dest(k)
                if f.exists():
                    assert json.loads(f.read_text())["source"]==ident
                    continue
                write_once(f,play_one(env,*k,ident))
        finally:
            env.close()
        assert source()==ident
    else:
        rows=[json.loads(dest(k).read_text()) for k in jobs]
        assert all(r["source"]==ident for r in rows)
        obj=evaluate(rows)
        raw="\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n"
        (HERE/"ganze_partien.jsonl.gz").write_bytes(gzip.compress(raw.encode(),mtime=0))
        write_once(HERE/"duell.json",obj)
        print(json.dumps(obj,indent=2))


if __name__=="__main__":
    main()
