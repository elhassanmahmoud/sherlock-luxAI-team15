"""Run the remaining registered factorial comparison on both seats of fresh boards."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path
import jax
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.kundschafter_feldwissen.spielen import HERE,ROOT,game
from experiments.analysis.relictsuche_20261123.punktwissen.spiele import decoded
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,sha,stamp,write_once,common_source
from scripts.experiment import limit_threads


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument("folder",type=Path);cli.add_argument("op",choices=("play","score"))
    cli.add_argument("lane",type=int,nargs="?",default=0);cli.add_argument("stride",type=int,nargs="?",default=1)
    a=cli.parse_args();limit_threads();assert json.loads((HERE/"faelle.json").read_bytes())["passed"]
    source=stamp(dict(base=common_source(),dep={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/"PLAN.md",HERE/"faelle.json",HERE/"spielen.py",
            ROOT/"ortundflotte/kandidat.py",ROOT/"ortundflotte/richtung.py",ROOT/"punktwissen/kandidat.py",ROOT/"flottenblick/flottengewichte.npz"]}))
    pool=np.arange(164700000,164701000,dtype=np.int32)
    seeds=list(map(int,pool[np.asarray(jax.jit(jax.vmap(sensor))(pool))==1][:32]))
    bracket=(("v16","solution92"),("joint","solution92"),("beide","solution92"),("beide","v16"),("beide","joint"))
    keys=[(s,t,arm,opp) for s in seeds for t in (0,1) for arm,opp in bracket];assert len(set(keys))==320
    def dest(k):return a.folder/("_".join(map(str,k))+".json")
    if a.op=="play":
        e=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in keys[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                if dest(k).exists():assert json.loads(dest(k).read_bytes())["source"]==source
                else:write_once(dest(k),game(e,k,source))
        finally:e.close()
        return
    rows={k:json.loads(dest(k).read_bytes()) for k in keys}
    assert all((r["seed"],r["team"],r["arm"],r["opponent"])==k and r["source"]==source and
        r["win"]==int(sum(m["win"] for m in r["matches"])>=2) for k,r in rows.items())
    data=[]
    for s in seeds:
        for t in (0,1):
            base,joint,both,dv,dj=[rows[s,t,*k] for k in bracket]
            if not both["proofs"]:
                assert joint["steps"]==both["steps"] and (joint["sight"],joint["credit"])==(both["sight"],both["credit"])
            diff=np.flatnonzero(np.any(decoded(joint)!=decoded(both),axis=(1,2,3)))
            if len(diff):assert both["proofs"] and diff[0]>=both["proofs"][0]["t"]
            else:assert both["matches"]==joint["matches"]
            data.append((base["win"],joint["win"],both["win"],dv["win"],dj["win"],both["win"]-joint["win"],
                         base["sight"]-both["sight"],base["credit"]-both["credit"],int(len(diff)>0)))
    arr=np.array(data).reshape(32,2,-1);unit=arr.mean(1);draw=np.random.default_rng(231123).integers(0,32,(20000,32))
    totals=arr.sum((0,1)).tolist();b,j,n,v,h=totals[:5]
    out=dict(original=b,joint=j,combined=n,vs_v16=v,vs_joint=h,changed_vs_joint=totals[-1],gain_vs_joint_ci=np.quantile(unit[draw,5].mean(1),[.025,.975]).tolist(),
        direct_ci=np.quantile(unit[draw,3:5].mean(1),[.025,.975],axis=0).T.tolist(),sight_gain=totals[6]/64,credit_gain=totals[7]/64,
        cards=32,games=320,source=source,passed=n>=max(b,j) and min(v,h)>=32 and (n>j or h>32))
    write_once(HERE/"duelle.json",out)
    (HERE/"duelle_partien.jsonl.gz").write_bytes(gzip.compress(b"".join(json.dumps(r,separators=(",",":")).encode()+b"\n" for r in rows.values()),mtime=0))


if __name__=="__main__":main()
