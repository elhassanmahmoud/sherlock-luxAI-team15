"""Test the live frozen post-opening choice on genuine fresh bilateral games."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.folgewahl.sammeln import HERE, CUTOFF, frozen, run, sha, stamp, write_once
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from scripts.experiment import limit_threads


def main():
    import jax
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path);p.add_argument("stage",choices=("play","score"))
    p.add_argument("lane",nargs="?",default=0,type=int);p.add_argument("stride",nargs="?",default=1,type=int)
    a=p.parse_args()
    gate=json.loads((HERE/"valid.json").read_text())
    assert gate["passed"] and gate["model_sha"]==sha(HERE/"modell.json")
    token=stamp(dict(base=frozen(),model=gate["model_sha"],validation=sha(HERE/"valid.json"),runner=sha(Path(__file__))))
    pool=np.arange(163700000,163701000,dtype=np.int32)
    seeds=list(map(int,pool[np.asarray(jax.jit(jax.vmap(sensor))(pool))==1][:48]))
    jobs=[(s,t,arm,opp) for s in seeds for t in (0,1) for arm,opp in
          (("v16","solution92"),("wahl","solution92"),("wahl","v16"))]
    assert len(set(jobs))==288 and 0<=a.lane<a.stride
    def dest(k):return a.folder/"frisch"/("_".join(map(str,k))+".json")
    if a.stage=="play":
        from luxai_s3.wrappers import LuxAIS3GymEnv
        limit_threads()
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in jobs[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                if dest(k).exists():
                    assert json.loads(dest(k).read_text())["source"]==token
                    continue
                s,t,arm,opp=k
                r,_=run(env,s,t,opp,None if arm=="wahl" else False)
                write_once(dest(k),dict(key=k,source=token,row=r))
        finally:env.close()
        return
    packed=[json.loads(dest(k).read_text()) for k in jobs]
    assert all(r["source"]==token and r["key"]==list(k) for r,k in zip(packed,jobs,strict=True))
    rows={tuple(d["key"]):d["row"] for d in packed}
    pairs=[]
    for s in seeds:
        for t in (0,1):
            b,n,h=[rows[s,t,a,o] for a,o in (("v16","solution92"),("wahl","solution92"),("wahl","v16"))]
            assert b["prefix"]==n["prefix"] and b["matches"][0]==n["matches"][0]
            if not n["chosen"]:assert b["hash"]==n["hash"] and b["matches"]==n["matches"]
            pairs.append((b["win"],n["win"],h["win"],int(n["chosen"]),int(h["chosen"])))
    arr=np.array(pairs).reshape(len(seeds),2,5)
    b,n,h,w,wd=map(int,arr.sum(axis=(0,1)))
    randoms=np.random.default_rng(231123).integers(0,len(seeds),(20000,len(seeds)))
    def metric(value):
        means=value.mean(1)
        return dict(mean=float(means.mean()),ci95=np.percentile(means[randoms].mean(1),[2.5,97.5]).tolist())
    passed=(n>b and h>=48) or (n>=b and h>48)
    result=dict(cards=len(seeds),games=len(rows),source=token,solution=n,original=b,direct=h,
                solution_gain=metric(arr[:,:,1]-arr[:,:,0]),direct_fraction=metric(arr[:,:,2]),
                switched_solution=w,switched_direct=wd,passed=bool(passed))
    write_once(HERE/"duell.json",result)
    data="\n".join(json.dumps(r,separators=(",",":")) for r in packed)+"\n"
    (HERE/"duell_spiele.jsonl.gz").write_bytes(gzip.compress(data.encode(),mtime=0))
    print(result)


if __name__=="__main__":main()
