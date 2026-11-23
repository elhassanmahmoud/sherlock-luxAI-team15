"""Replay specific external game changes, then unlock fresh cards only if the targeted handoff works."""
import argparse
import base64
from datetime import datetime
import gzip
import hashlib
import json
from pathlib import Path
import zlib

import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import MIRROR
from experiments.analysis.relictsuche_20261123.punktwissen.spiele import decoded
from experiments.analysis.relictsuche_20261123.suche_und_wissen.spieler import make_player
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,Monitor,common_source,sha,stamp,write_once
from scripts.common import play_game,make_opponent
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.scoring import point_tile_map

HERE=Path(__file__).resolve().parent


class Audit(Monitor):
    def __init__(self,env,t,player,kind):
        route=player if kind in ("suche","beide") else None
        super().__init__(env,t,"discovery",route)
        self.memory=player.base if kind=="beide" else player if kind=="wissen" else None
        self.checked=[]
        self.commands=[]

    def step(self,actions):
        self.commands.append(np.stack([actions["player_0"],actions["player_1"]]).astype(np.int8))
        if self.memory:
            news=self.memory.events[len(self.checked):]
            if news:
                truth=point_tile_map(self.env.state)
                for e in news:
                    assert self.turn==e["t"] and all(truth[divmod(k,24)] for k in (e["world"],MIRROR[e["world"]]))
                self.checked.extend(news)
        return super().step(actions)


def play(env,k,src):
    s,t,arm,opp=k
    side=f"player_{t}"
    actor=make_player(side,arm)
    rival=make_player(f"player_{1-t}","v16") if opp=="v16" else make_opponent("solution92",f"player_{1-t}")
    mon=Audit(env,t,actor,arm)
    res=play_game(mon,actor,rival,s,side,False)
    require_no_agent_errors(actor,rival)
    if mon.memory:assert mon.checked==mon.memory.events
    assert res["game_win"]==int(sum(m["win"] for m in mon.matches)>=2) and mon.turn==303 and mon.sensor==1
    cmds=np.stack(mon.commands)
    assert hashlib.sha256(cmds.astype("<i4").tobytes()).hexdigest()==mon.digest.hexdigest()
    return dict(seed=s,team=t,arm=arm,opponent=opp,source=src,win=res["game_win"],matches=mon.matches,
                sight=mon.first_sight,credit=mon.first_credit,hash=mon.digest.hexdigest(),steps=mon.events,
                additions=mon.checked,tape=base64.b64encode(zlib.compress(cmds.tobytes())).decode())


def first(a,b):
    ids=np.flatnonzero(np.any(decoded(a)!=decoded(b),axis=(1,2,3)))
    return int(ids[0]) if len(ids) else 303


def effects(arms):
    base,scout,know,joined=[arms[k] for k in ("v16","suche","wissen","beide")]
    switch=first(scout,joined)
    # A credit is reported on completing the indexed action; first sight is the observation before action.
    assert switch>=min(scout["sight"],scout["credit"]+1) and switch>=min((e["t"] for e in joined["additions"]),default=303)
    assert first(base,know)>=min((e["t"] for e in know["additions"]),default=303)
    return switch


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path);p.add_argument("stage",choices=("tech","play","score"));p.add_argument("lane",nargs="?",type=int,default=0);p.add_argument("stride",nargs="?",type=int,default=1)
    a=p.parse_args();limit_threads()
    srcs=[HERE/"PLAN.md",HERE/"spieler.py",Path(__file__)]+[HERE.parent/f for f in ("zielschaetzer/kandidat.py","zielschaetzer/ort.json","punktgrenzen/politik.py","punktgrenzen/grenzen.py","punktwissen/kandidat.py","punktspeicher/beweise.py")]
    token=stamp(dict(common=common_source(),inputs={str(p.relative_to(HERE.parent)):sha(p) for p in srcs}))
    tech=a.stage=="tech"
    arms=("v16","suche","wissen","beide")
    if tech:
        with gzip.open(HERE.parent/"vergleich/discovery/partien.jsonl.gz","rt") as f:
            hist={(r["seed"],r["team"],r["id"]):r for r in map(json.loads,f) if r["opponent"]=="solution92"}
        cases=sorted((s,t) for s,t,arm in hist if arm=="ziel" and hist[s,t,"ziel"]["win"]!=hist[s,t,"reference"]["win"])
        assert len(cases)==5
        keys=[(s,t,n,"solution92") for s,t in cases for n in arms]
    else:
        gate=json.loads((HERE/"technik.json").read_text())
        assert gate["passed"] and gate["source"]==token
        import jax
        pool=np.arange(164110000,164111000,dtype=np.int32)
        seeds=[int(s) for s in pool[np.asarray(jax.jit(jax.vmap(sensor))(pool))==1][:48]]
        cases=[(s,t) for s in seeds for t in (0,1)]
        keys=[(s,t,n,o) for s,t in cases for n,o in [(n,"solution92") for n in arms]+[("beide","v16")]]
    def dst(k):return a.folder/("technik" if tech else "spiele")/("_".join(map(str,k))+".json")
    if a.stage!="score":
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in keys[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                if dst(k).exists():assert json.loads(dst(k).read_text())["source"]==token
                else:write_once(dst(k),play(env,k,token))
        finally:env.close()
        if not tech:return
    rows={k:json.loads(dst(k).read_text()) for k in keys}
    data=[]
    for s,t in cases:
        g={n:rows[s,t,n,"solution92"] for n in arms}
        at=effects(g)
        if tech:
            for n,old in (("v16","reference"),("suche","ziel")):
                ref=hist[s,t,old]
                assert ref["action_hash"]==g[n]["hash"] and ref["matches"]==g[n]["matches"]
        data.append(dict(seed=s,team=t,first=at if at<303 else None,wins={n:r["win"] for n,r in g.items()},
                         matches={n:r["matches"] for n,r in g.items()},sight={n:r["sight"] for n,r in g.items()},
                         credit={n:r["credit"] for n,r in g.items()},events=len(g["beide"]["additions"])))
    if tech:
        rescued=sum(r["wins"]["v16"] and r["wins"]["beide"] for r in data)
        kept=sum(not r["wins"]["v16"] and r["wins"]["beide"] for r in data)
        different=sum(r["first"] is not None and r["events"]>0 for r in data)
        write_once(HERE/"technik.json",dict(source=token,passed=bool(rescued>=2 and kept==1 and different>=2),
                   recovered=rescued,kept=kept,changed=different,rows=data))
    else:
        wins={n:sum(r["wins"][n] for r in data) for n in arms}
        direct=sum(rows[s,t,"beide","v16"]["win"] for s,t in cases)
        gains={k:float(np.mean([r[k]["v16"]-r[k]["beide"] for r in data])) for k in ("sight","credit")}
        passed=max(gains.values())>0 and wins["beide"]==max(wins.values()) and direct>=48 and (wins["beide"]>wins["v16"] or direct>48)
        write_once(HERE/"duelle.json",dict(source=token,cards=48,games=len(rows),wins=wins,direct=direct,gains=gains,passed=passed,rows=data))
    payload="\n".join(json.dumps(r,separators=(",",":")) for r in rows.values())+"\n"
    (HERE/("technik_partien.jsonl.gz" if tech else "duelle_partien.jsonl.gz")).write_bytes(gzip.compress(payload.encode(),mtime=0))


if __name__=="__main__":main()
