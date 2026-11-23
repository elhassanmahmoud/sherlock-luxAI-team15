"""Run a public disproof as a live V16 input correction and retain paired action tapes."""
import argparse
import base64
from datetime import datetime
import gzip
import json
from pathlib import Path
import zlib

import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

from experiments.analysis.relictsuche_20261123.fehlmarkierung.korrektur import PACKAGE, create
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import MIRROR,PAIR
from experiments.analysis.relictsuche_20261123.punktwissen.spiele import decoded
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,Monitor,common_source,sha,stamp,write_once
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import point_tile_map

HERE=Path(__file__).resolve().parent


class Audit(Monitor):
    def __init__(self,env,team,actor,sites):
        super().__init__(env,team,"general")
        self.repair=actor
        self.sites=sites
        self.commands=[]
        self.verified=[]
        self.camping=0

    def step(self,actions):
        truth=point_tile_map(self.env.state)
        if self.repair:
            for e in self.repair.events[len(self.verified):]:
                f=e["pair"]
                assert e["t"]==self.turn and all(not truth[divmod(q,24)] for q in (f,MIRROR[f]))
                b=self.repair.base._imitation.belief
                assert not b.point_tiles[divmod(f,24)] and not b.point_tiles[divmod(MIRROR[f],24)]
                self.verified.append(e)
        if self.sites:
            st=self.env.state
            pos=np.asarray(st.units.position[self.team])
            active=np.asarray(st.units_mask[self.team],bool)&(np.asarray(st.units.energy[self.team]).reshape(-1)>=0)
            for x,y in pos[active]:
                if PAIR[int(x)*24+int(y)] in self.sites and not truth[int(x),int(y)]:
                    self.camping+=1
        self.commands.append(np.stack([actions["player_0"],actions["player_1"]]).astype(np.int8))
        return super().step(actions)


def game(env,s,t,arm,opp,ident,sites=()):
    side,other=f"player_{t}",f"player_{1-t}"
    a=create(side) if arm=="fix" else r3_package_agent(side,PACKAGE)
    b=make_opponent("solution92",other) if opp=="solution92" else r3_package_agent(other,PACKAGE)
    rec=Audit(env,t,a if arm=="fix" else None,sites)
    result=play_game(rec,a,b,s,side,False)
    require_no_agent_errors(a.base if arm=="fix" else a,b)
    assert rec.turn==result["steps"]==303 and result["game_win"]==int(sum(m["win"] for m in rec.matches)>=2)
    if arm=="fix":assert rec.verified==a.events
    return dict(seed=s,team=t,version=arm,opponent=opp,source=ident,matches=rec.matches,win=result["game_win"],
                digest=rec.digest.hexdigest(),events=rec.verified,camping=rec.camping,sensor=rec.sensor,
                tape=base64.b64encode(zlib.compress(np.stack(rec.commands).tobytes())).decode())


def compare(ref,new,reverse=False):
    baseline=decoded(ref)
    actual=decoded(new)
    difference=np.flatnonzero(np.any(baseline!=actual,axis=(1,2,3)))
    if len(difference):
        assert new["events"] and difference[0]>=new["events"][0]["t"]
        return int(difference[0])
    assert new["win"]==(1-ref["win"] if reverse else ref["win"])
    for original,candidate in zip(ref["matches"],new["matches"],strict=True):
        assert candidate["points"]==(original["points"][::-1] if reverse else original["points"])
        assert candidate["win"]==(1-original["win"] if reverse else original["win"])
    return None


def tech(env,ident):
    original=json.loads((HERE/"ursachen.json").read_text())["cases"]
    roster=[(c["seed"],c["team"],c["opp"],{e["canonical_pair"] for e in c["errors"]},c["hash"]) for c in original]
    with gzip.open(HERE.parent/"punktwissen/partien.jsonl.gz","rt") as f:
        control=next(r for r in map(json.loads,f) if r["version"]=="neu" and r["opponent"]=="solution92"
                     and not r["false_positive_ticks"] and not r["events"])
    roster.append((control["seed"],control["team"],"solution92",set(),control["digest"]))
    rows=[]
    for s,t,opp,sites,digest in roster:
        ref,new=[game(env,s,t,arm,opp,ident,sites) for arm in ("v16","fix")]
        assert ref["digest"]==digest
        diff=compare(ref,new)
        assert bool(sites)==bool(new["events"])
        rows.append(dict(seed=s,team=t,opponent=opp,sites=sorted(sites),first_difference=diff,
                         original_camping=ref["camping"],new_camping=new["camping"],
                         original=ref["matches"],new=new["matches"],original_win=ref["win"],win=new["win"],
                         events=new["events"],control_hash=ref["digest"],candidate_hash=new["digest"]))
    passed=(sum(r["first_difference"] is not None for r in rows)>=2 and
            sum(r["new_camping"] for r in rows)<sum(r["original_camping"] for r in rows))
    write_once(HERE/"technik.json",dict(source=ident,passed=passed,cases=rows))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path);p.add_argument("stage",choices=("tech","play","score"))
    p.add_argument("lane",nargs="?",type=int,default=0);p.add_argument("stride",nargs="?",type=int,default=1)
    a=p.parse_args();limit_threads()
    paths=[HERE/n for n in ("KORREKTURPLAN.md","korrektur.py","korrekturspiele.py","widerspruch.json")]
    paths += [HERE.parent/"punktgrenzen/grenzen.py",HERE.parent/"punktspeicher/beweise.py"]
    ident=stamp(dict(common=common_source(),files={str(p.relative_to(HERE.parent)):sha(p) for p in paths}))
    if a.stage=="tech":
        env=LuxAIS3GymEnv(numpy_output=True)
        try:tech(env,ident)
        finally:env.close()
        return
    result=json.loads((HERE/"technik.json").read_text())
    assert result["source"]==ident and result["passed"]
    import jax
    pool=np.arange(164020000,164021000,dtype=np.int32)
    seeds=list(map(int,pool[np.asarray(jax.jit(jax.vmap(sensor))(pool))==1][:64]))
    assert len(seeds)==64
    keys=[(s,t,arm,opp) for s in seeds for t,arm,opp in [(0,"v16","v16")]+[
        (t,arm,opp) for t in (0,1) for arm,opp in (("v16","solution92"),("fix","solution92"),("fix","v16"))]]
    def path(k):return a.folder/"spiele"/("_".join(map(str,k))+".json")
    if a.stage=="play":
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in keys[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                f=path(k)
                if f.exists():
                    assert json.loads(f.read_text())["source"]==ident
                else:write_once(f,game(env,*k,ident))
        finally:env.close()
        return
    runs={k:json.loads(path(k).read_text()) for k in keys}
    assert len(runs)==448 and all(r["source"]==ident and r["sensor"]==1 for r in runs.values())
    rows=[]
    for s in seeds:
        for t in (0,1):
            v,n,d=[runs[s,t,arm,opp] for arm,opp in (("v16","solution92"),("fix","solution92"),("fix","v16"))]
            rows.append(dict(seed=s,team=t,base=v["win"],candidate=n["win"],direct=d["win"],
                             changed=compare(v,n),changed_direct=compare(runs[s,0,"v16","v16"],d,bool(t)),
                             events=len(n["events"]),events_direct=len(d["events"])))
    base,cand,direct=(sum(r[k] for r in rows) for k in ("base","candidate","direct"))
    ix=np.random.default_rng(231123).integers(0,64,(20000,64))
    gain=np.array([r["candidate"]-r["base"] for r in rows]).reshape(64,2).mean(1)
    h2h=np.array([r["direct"] for r in rows]).reshape(64,2).mean(1)
    passed=(cand>base and direct>=64) or (cand>=base and direct>=65)
    write_once(HERE/"duelle.json",dict(source=ident,cards=64,base=base,candidate=cand,direct=direct,passed=passed,
        solution_gain_ci95=np.quantile(gain[ix].mean(1),[.025,.975]).tolist(),direct_ci95=np.quantile(h2h[ix].mean(1),[.025,.975]).tolist(),rows=rows))
    data="\n".join(json.dumps(r,separators=(",",":")) for r in runs.values())+"\n"
    (HERE/"partien.jsonl.gz").write_bytes(gzip.compress(data.encode(),mtime=0))


if __name__=="__main__":main()
