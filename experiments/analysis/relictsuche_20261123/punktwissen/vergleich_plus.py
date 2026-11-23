"""Paired full games for a qualified extension, with both players' public proofs checked against the live referee."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path
import random

import numpy as np
import torch

from experiments.analysis.relictsuche_20261123.punktgrenzen.politik import AreaKnowledge
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import MIRROR
from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import Knowledge,PACKAGE
from experiments.analysis.relictsuche_20261123.sichtweite.aufnahme import roster
from experiments.analysis.relictsuche_20261123.sichtweite.politik import AllSight
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor,CUTOFF,common_source,sha,stamp,write_once
from scripts.common import make_opponent,play_game
from scripts.r3_package import r3_package_agent
from scripts.par_eval import require_no_agent_errors
from scripts.experiment import limit_threads
from scripts.scoring import point_tile_map

STUDY=Path(__file__).resolve().parents[1]


def make(kind,side):
    if kind=="solution92":
        return make_opponent(kind,side)
    base=r3_package_agent(side,PACKAGE)
    cls={"v16":None,"wissen":Knowledge,"sichtweite":AllSight,"punktgrenzen":AreaKnowledge}[kind]
    return base if cls is None else cls(base)


class BothPlayers(Monitor):
    def __init__(self,env,team,players):
        super().__init__(env,team,"general")
        self.checked=[[],[]]
        self.players=players
        self.action_hashes=[]

    def step(self,cmd):
        import hashlib
        actions=np.stack([cmd[f"player_{s}"] for s in (0,1)]).astype("<i4")
        self.action_hashes.append(hashlib.blake2b(actions.tobytes(),digest_size=12).hexdigest())
        for team,actor in self.players.items():
            additions=actor.events[len(self.checked[team]):]
            if additions:
                truth=point_tile_map(self.env.state)
                for e in additions:
                    assert e["t"]==self.turn and truth[divmod(e["world"],24)] and truth[divmod(MIRROR[e["world"]],24)]
                self.checked[team].extend(additions)
        return super().step(cmd)


def game(env,key,identity):
    seed,team,arm,opp=key
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    side=f"player_{team}"
    actor,rival=make(arm,side),make(opp,f"player_{1-team}")
    pair={team:actor,1-team:rival}
    checker=BothPlayers(env,team,{k:v for k,v in pair.items() if isinstance(v,Knowledge)})
    result=play_game(checker,actor,rival,seed,side,False)
    require_no_agent_errors(*(v.base if isinstance(v,Knowledge) else v for v in (actor,rival)))
    assert checker.turn==303 and sum(q["win"] for q in checker.matches)==result["our_wins"]
    assert result["game_win"]==int(result["our_wins"]>=2)
    for k,v in checker.players.items():
        assert checker.checked[k]==v.events
    return dict(key=key,source=identity,hash=checker.digest.hexdigest(),per_turn=checker.action_hashes,
                matches=checker.matches,win=result["game_win"],sensor=checker.sensor,events=checker.checked,
                sight=checker.first_sight,credit=checker.first_credit)


def selection(arm):
    if arm=="sichtweite":
        requirement=STUDY/arm/"reichweite.json"
        assert json.loads(requirement.read_text())["passed"]
        pairs=[("v16","solution92"),(arm,"solution92"),(arm,"v16")]
        return [(s,t,a,o) for s,_,_ in roster(163315000) for t in (0,1) for a,o in pairs],requirement
    requirement=STUDY/arm/"valid.json"
    assert json.loads(requirement.read_text())["passed"]
    import jax
    pool=np.arange(163600000,163601000,dtype=np.int32)
    candidates=pool[np.asarray(jax.jit(jax.vmap(sensor))(pool))==1][:48]
    pairs=[("v16","solution92"),("wissen","solution92"),(arm,"solution92"),(arm,"v16"),(arm,"wissen")]
    return [(int(s),t,a,o) for s in candidates for t in (0,1) for a,o in pairs],requirement


def technical(env,arm,identity):
    with gzip.open(STUDY/"punktwissen/partien.jsonl.gz","rt") as f:
        recorded=[r for r in map(json.loads,f) if r["opponent"]=="solution92" and r["version"]=="neu" and r["events"]]
    outcome=[]
    for t in (0,1):
        anchor=next(r for r in sorted(recorded,key=lambda r:r["seed"]) if r["team"]==t)
        k=(anchor["seed"],t,arm,"solution92")
        row=game(env,k,identity)
        if arm=="sichtweite":
            assert row["hash"]==anchor["digest"] and row["matches"]==anchor["matches"] and row["events"][t]==anchor["events"]
        else:
            ref=game(env,(k[0],t,"v16","solution92"),identity)
            first=next((i for i in range(303) if row["per_turn"][i]!=ref["per_turn"][i]),303)
            assert first>=min((e["t"] for e in row["events"][t]),default=303)
        outcome.append(dict(seed=k[0],team=t,hash=row["hash"],events=row["events"][t]))
    return outcome


def evaluate(rows,arm):
    seeds=sorted({k[0] for k in rows})
    randoms=np.random.default_rng(231123).integers(0,len(seeds),(20000,len(seeds)))
    def estimate(values):
        v=np.asarray(values,float).reshape(len(seeds),2).mean(1)
        return dict(mean=float(v.mean()),ci95=np.percentile(v[randoms].mean(1),[2.5,97.5]).tolist())
    names=["v16",arm] if arm=="sichtweite" else ["v16","wissen",arm]
    def seats(a,o):
        return [rows[s,t,a,o]["win"] for s in seeds for t in (0,1)]
    external={n:sum(seats(n,"solution92")) for n in names}
    direct={n:sum(seats(arm,n)) for n in names[:-1]}
    relative={n:estimate(np.subtract(seats(arm,"solution92"),seats(n,"solution92"))) for n in names[:-1]}
    active=0
    for s in seeds:
        for t in (0,1):
            orig=rows[s,t,"v16","solution92"]
            for n in names[1:]:
                c=rows[s,t,n,"solution92"]
                unshared=next((i for i in range(303) if c["per_turn"][i]!=orig["per_turn"][i]),303)
                assert unshared>=min((e["t"] for e in c["events"][t]),default=303)
                if n==arm:active+=unshared<303
                if unshared==303:
                    assert orig["matches"]==c["matches"] and orig["hash"]==c["hash"]
    strict=names[-2]
    gates=dict(solution=external[arm]>=max(external.values()),
               direct=min(direct.values())>=len(seeds),
               improvement=external[arm]>external[strict] or direct[strict]>len(seeds))
    return dict(cards=len(seeds),games=len(rows),external=external,direct=direct,external_difference=relative,
                direct_fraction={n:estimate(seats(arm,n)) for n in names[:-1]},changed_solution=active,
                gates=gates,passed=all(gates.values()))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path);p.add_argument("arm",choices=("sichtweite","punktgrenzen"))
    p.add_argument("stage",choices=("tech","play","score"));p.add_argument("lane",type=int,nargs="?",default=0);p.add_argument("stride",type=int,nargs="?",default=1)
    a=p.parse_args()
    assert 0<=a.lane<a.stride
    keys,gate=selection(a.arm)
    sources=[STUDY/n for n in ("punktwissen/vergleich_plus.py","punktwissen/kandidat.py","punktspeicher/beweise.py","punktgrenzen/grenzen.py",
                               "punktgrenzen/politik.py","sichtweite/aufnahme.py","sichtweite/politik.py")]
    identity=stamp(dict(base=common_source(),admission=sha(gate),rules=sha(STUDY/a.arm/"PLAN.md"),
                        files={str(f.relative_to(STUDY)):sha(f) for f in sources}))
    assert len(set(keys))==len(keys)==(432 if a.arm=="sichtweite" else 480)
    def dest(k):return a.folder/"spiele"/("_".join(map(str,k))+".json")
    record=STUDY/a.arm/"technik_aktiv.json"
    if a.stage in ("play","score"):
        assert json.loads(record.read_text())["source"]==identity
    if a.stage in ("tech","play"):
        from luxai_s3.wrappers import LuxAIS3GymEnv
        limit_threads()
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            if a.stage=="tech":
                write_once(record,dict(source=identity,cases=technical(env,a.arm,identity)))
                return
            for k in keys[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                f=dest(k)
                if f.exists():
                    assert json.loads(f.read_text())["source"]==identity
                    continue
                row=game(env,k,identity)
                assert (row["sensor"]>1) if a.arm=="sichtweite" else (row["sensor"]==1)
                write_once(f,row)
        finally: env.close()
        return
    rows={k:json.loads(dest(k).read_text()) for k in keys}
    assert all(tuple(r["key"])==k and r["source"]==identity for k,r in rows.items())
    output=evaluate(rows,a.arm)
    write_once(STUDY/a.arm/"duell.json",dict(source=identity,**output))
    data="\n".join(json.dumps(r,separators=(",",":")) for r in rows.values())+"\n"
    (STUDY/a.arm/"duell_karten.jsonl.gz").write_bytes(gzip.compress(data.encode(),mtime=0))
    print(output)


if __name__=="__main__":
    main()
