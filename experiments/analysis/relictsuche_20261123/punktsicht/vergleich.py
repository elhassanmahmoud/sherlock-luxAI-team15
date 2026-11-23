"""Fixed and independent 40-map whole-game panel for the post-credit sighting policy."""
import argparse
from datetime import datetime
import fcntl
import gzip
import json
import os
from pathlib import Path
import random
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SHARED=HERE.parent/"vergleich"
sys.path.insert(0,str(SHARED))
sys.path.insert(0,str(ROOT))
import spielen as benchmark
from auswerten import BOOTSTRAP_SEED, DRAWS, save_archive, score, summary
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from kandidat import MIRROR, create
from panel import sensor

STORE=Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/punktsicht")
TECH=[161420038,161420046,161420047,161420064]
require=benchmark.require
write=benchmark.write_once


def identity():
    common=benchmark.common_source()
    files=[HERE/"PLAN.md",HERE/"karten.json",HERE/"kandidat.py",HERE/"vergleich.py",HERE.parent/"punkthinweis/belegung.py",
           HERE.parent/"punkthinweis/gelegenheit.py",HERE.parent/"zielschaetzer/ort.json",SHARED/"auswerten.py"]
    source={str(p.relative_to(ROOT)):benchmark.sha(p) for p in files}
    return {"common":common,"source":source}


def prepare():
    import jax
    seeds=np.arange(161450000,161451000,dtype=np.int32)
    selected=seeds[np.asarray(jax.jit(jax.vmap(sensor))(seeds))==1][:40].tolist()
    require(len(selected)==40 and len(set(selected))==40 and not set(selected).intersection(TECH),"Wrong card panel")
    write(HERE/"karten.json",{"technical":TECH,"discovery":selected})
    write(STORE/"freeze.json",identity())


class Monitor(benchmark.Monitor):
    def __init__(self,env,team,phase,actor=None):
        super().__init__(env,team,phase,actor)
        self.first_signal=None
        self.earlier_producers=set()
        self.protection=[]
        self.match1_after=[]

    def step(self,actions):
        t=self.turn
        if t<=100:
            o=self.old
            state=self.env.state
            if self.first_signal is None and int(o["team_points"][self.team])>0:
                self.first_signal=t
            if self.first_signal is not None:
                live=np.asarray(o["units_mask"][self.team],bool)&(np.asarray(o["units"]["energy"][self.team]).reshape(-1)>=0)
                p=np.asarray(o["units"]["position"][self.team])
                if np.asarray(state.relic_nodes_mask).any():
                    actual=np.asarray(state.relic_nodes_map_weights)==1
                    self.earlier_producers.update(uid for uid in map(int,np.flatnonzero(live)) if actual[tuple(p[uid])])
            if self.actor is not None:
                output=np.asarray(actions[self.side])
                delta=np.flatnonzero(np.any(output!=self.proposal,axis=1))
                if len(delta):
                    uid=delta.item()
                    move=int(output[uid,0])
                    actor=self.actor
                    require(self.first_signal is not None and self.first_sight==101 and not o["relic_nodes_mask"].any() and
                        uid==actor.ship and uid not in self.earlier_producers and self.sensor==1,
                        "Override outside the post-credit window or on a historical point contributor")
                    require(actor.selected["t"]-self.first_signal<12 and t-actor.selected["t"]<5 and actor.selected["t"]<=91,
                        "Search window exceeded")
                    mem=actor.base._imitation
                    require(mem._prev_actions[uid]==(MIRROR[move] if self.team else move) and uid not in mem._sap_hits and
                        (mem.param_est._prev is None or np.array_equal(mem.param_est._prev["act"],output)),
                        "Agent memory disagrees with issued override")
                    require(uid not in actor.last["contributors"] and set(self.earlier_producers).issubset(actor.last["contributors"]),
                        "Public scorer protection failed to cover actual prior contributors")
                    self.protection.append([t,uid,len(self.earlier_producers),len(actor.last["contributors"])])
        result=super().step(actions)
        if t<=100:
            pts=self.matches[0]["points"][0] if t==100 else int(result[0][self.side]["team_points"][self.team])
            self.match1_after.append(pts)
        return result


def game(env,key,src,technical=False):
    import torch
    phase,seed,team,arm,op=key
    side,other=f"player_{team}",f"player_{1-team}"
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    agent=create(side) if arm=="punktsicht" else r3_package_agent(side,benchmark.PACKAGE)
    rival=r3_package_agent(other,benchmark.PACKAGE) if op=="v16" else make_opponent("solution92",other)
    m=Monitor(env,team,phase,agent if arm=="punktsicht" else None)
    class Finished(Exception):
        pass
    class Opening:
        def reset(self,**kwargs):
            return m.reset(**kwargs)
        def step(self,actions):
            result=m.step(actions)
            if m.turn==101: raise Finished
            return result
    if technical:
        try:
            play_game(Opening(),agent,rival,seed,side,False)
        except Finished:
            pass
        require(m.turn==101 and len(m.matches)==1,"Invalid technical prefix")
    else:
        raw=play_game(m,agent,rival,seed,side,False)
        require(raw["steps"]==303 and m.turn==303 and raw["point_counting_version"]==2,"Incomplete full game")
    require_no_agent_errors(agent.base if arm=="punktsicht" else agent,rival)
    row=dict(zip(("phase","seed","team","id","opponent"),key,strict=True),source=src,sensor=m.sensor,sight=m.first_sight,
        credit=m.first_credit,after_70=m.after_70,matches=m.matches,events=m.events,steps=m.turn,actions_checked=m.counts,
        caught_errors=[0,0],point_counting_version=2,wins=sum(a["win"] for a in m.matches),
        points=[sum(a["points"][i] for a in m.matches) for i in (0,1)],action_hash=m.digest.hexdigest(),
        first_public_credit=m.first_signal,protected_at_changes=m.protection,
        selection=agent.selected if arm=="punktsicht" else None, after49=m.match1_after[49],after89=m.match1_after[89])
    row["win"]=int(row["wins"]>=2)
    require(len({e[1] for e in row["events"]})<=1 and len(row["protected_at_changes"])==len(row["events"]) and
        len(row["events"])<=5,"Invalid scout identity, memory or number of overrides")
    if not technical:
        require([row["wins"],row["win"],*row["points"]]==[raw["our_wins"],raw["game_win"],raw["our_points"],raw["opp_points"]],
                "Monitor diverged from normal runner")
        benchmark.validate(row,key,src)
    return row


def technical(frozen):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    receipt=json.loads(gzip.decompress((HERE.parent/"punkthinweis/quellen.json.gz").read_bytes()))
    baseline={(r["seed"],r["team"]):r for r in receipt["rows"]}
    env=LuxAIS3GymEnv(numpy_output=True)
    rows=[]
    try:
        for seed in TECH:
            for team in (0,1):
                key=("tech_credit",seed,team,"punktsicht","solution92")
                row=game(env,key,benchmark.stamp(frozen),True)
                old=baseline[seed,team]
                if not row["events"]:
                    expected=[old["points"][team],old["points"][1-team]]
                    require(row["matches"][0]["points"]==expected and row["matches"][0]["win"]==old["match_won"],
                        "Inactive technical candidate differs from archived baseline")
                rows.append(row)
                print(f"{len(rows)}/8 Technikpräfixe",flush=True)
    finally:
        env.close()
    require(any(r["events"] and r["team"]==0 for r in rows) and any(r["events"] and r["team"]==1 for r in rows),
            "No real intervention on both start positions")
    write(HERE/"technik.json",dict(source=benchmark.stamp(frozen),rows=rows))


def jobs(cards):
    return [("discovery",seed,team,arm,op) for seed in cards for team in (0,1)
            for arm,op in (("reference","solution92"),("punktsicht","solution92"),("punktsicht","v16"))]


def dest(k):
    _,seed,team,arm,op=k
    return STORE/"partien"/f"{seed}_{team}_{arm}_{op}.json"


def run(frozen,worker):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    tech=json.loads((HERE/"technik.json").read_bytes())
    require(tech["source"]==benchmark.stamp(frozen),"Technique/source binding mismatch")
    cards=json.loads((HERE/"karten.json").read_bytes())["discovery"]
    all_jobs=jobs(cards)
    offset=worker*53%len(all_jobs)
    (STORE/"leases").mkdir(parents=True,exist_ok=True)
    env=LuxAIS3GymEnv(numpy_output=True)
    completed=0
    try:
        for key in all_jobs[offset:]+all_jobs[:offset]:
            if datetime.now(benchmark.CUTOFF.tzinfo)>=benchmark.CUTOFF: break
            to=dest(key)
            if to.exists():continue
            with (STORE/"leases"/(to.stem+".lock")).open("ab") as lock:
                try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:continue
                if to.exists():continue
                src=benchmark.stamp({"freeze":benchmark.stamp(frozen),"id":key[3]})
                write(to,game(env,key,src))
                completed+=1
                if completed%10==0:print(f"Worker {worker}: {completed} neue vollständige Spiele",flush=True)
    finally:env.close()
    require(identity()==frozen,"Sources changed during the run")
    print(f"Worker {worker}: {completed} zusätzliche Spiele, beendet",flush=True)


def assess(frozen):
    cards=json.loads((HERE/"karten.json").read_bytes())["discovery"]
    expected=jobs(cards)
    require({dest(k) for k in expected}==set((STORE/"partien").glob("*.json")),"All 240 games must be complete")
    rows=[];groups={}
    for key in expected:
        row=json.loads(dest(key).read_bytes())
        benchmark.validate(row,key,benchmark.stamp({"freeze":benchmark.stamp(frozen),"id":key[3]}))
        require(len({e[1] for e in row["events"]})<=1,"Multiple scouts")
        groups.setdefault((key[3],key[4]),{})[key[1],key[2]]=row
        rows.append(row)
    output=save_archive(rows,HERE/"partien.jsonl.gz")
    require(rows==output,"Compressed games disagree")
    draws=np.random.default_rng(BOOTSTRAP_SEED).integers(0,len(cards),size=(DRAWS,len(cards)))
    d=score("punktsicht",cards,groups,draws)
    b=groups["reference","solution92"]; a=groups["punktsicht","solution92"]
    credit_parity=all(a[k]["credit"]==b[k]["credit"] for k in b)
    p=d["paired"]
    gates=dict(earlier_sight_half=p["sight"]["mean"]>=.5,more_earlier_than_later=p["sight"]["positive_seats"]>p["sight"]["negative_seats"],
        four_changed_maps=d["solution"]["all"]["changed_maps"]>=4,credit_equal_each_seat=credit_parity,
        margin70_nondecreasing=p["margin70"]["mean"]>=0,match1wins_nondecreasing=p["match1win"]["mean"]>=0,
        wins_nondecreasing=p["whole"]["mean"]>=0,direct_at_least_half=d["direct_rate"]["mean"]>=.5)
    changed=[k for k in b if a[k]["events"]]
    impact={str(k):{"n":sum(1 for key in changed if key[0]==k),
        "sight_gain":sum(b[key]["sight"]-a[key]["sight"] for key in changed if key[0]==k)} for k in sorted({i[0] for i in changed})}
    late={}
    for name,func in (("actions50_to89",lambda r:r["after89"]-r["after49"]),
                      ("actions90_to100",lambda r:r["matches"][0]["points"][0]-r["after89"])):
        vals={n:sum(func(g[k]) for k in b) for n,g in (("reference",b),("candidate",a))}
        late[name]=vals
    out={"maps":len(cards),"games":len(rows),"reference":summary(list(b.values())),"candidate":d,"gates":gates,
         "passed":all(gates.values()),"changed_solution_maps":impact,"later_own_points":late,
         "source":frozen,"sha256":benchmark.sha(HERE/"partien.jsonl.gz")}
    write(HERE/"ergebnis.json",out)
    print(json.dumps({k:out[k] for k in ("gates","passed","later_own_points")},indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("prepare","technical","run","assess"))
    p.add_argument("--worker",type=int,default=0)
    args=p.parse_args()
    require(os.getenv("PYTHONHASHSEED")=="0" and all(os.getenv(k)=="1" for k in benchmark.THREADS),"Unexpected thread settings")
    limit_threads()
    if args.mode=="prepare":prepare()
    else:
        frozen=json.loads((STORE/"freeze.json").read_bytes())
        require(identity()==frozen,"Frozen files differ")
        if args.mode=="technical":technical(frozen)
        elif args.mode=="run":run(frozen,args.worker)
        else:assess(frozen)
