"""Run a qualified public point memory on a preregistered, unfiltered general population."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path
import numpy as np

from spiele import HERE, CUTOFF, frozen, run, paired, sha, stamp, write_once


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.experiment import limit_threads
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path);p.add_argument("stage",choices=("play","score"))
    p.add_argument("lane",type=int,nargs="?",default=0);p.add_argument("stride",type=int,nargs="?",default=1)
    a=p.parse_args()
    limit_threads()
    qualifying=json.loads((HERE/"ergebnis.json").read_text())
    assert qualifying["passed"] and qualifying["source"]==frozen()
    ident=stamp(dict(phase=frozen(),qualifier=sha(HERE/"ergebnis.json"),prereg=sha(HERE/"ALLGEMEIN.md"),runner=sha(Path(__file__))))
    seeds=range(162860000,162860160)
    keys=[(s,t,mode,opp) for s in seeds for t in (0,1) for mode,opp in
          (("v16","solution92"),("neu","solution92"),("neu","v16"))]
    def output(k):
        return a.folder/"alle"/("_".join(map(str,k))+".json")
    if a.stage=="play":
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in keys[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                dest=output(k)
                if dest.exists():
                    assert json.loads(dest.read_text())["source"]==ident
                    continue
                write_once(dest,run(env,*k,ident))
        finally:
            env.close()
        assert qualifying["source"]==frozen()
        return
    rows={k:json.loads(output(k).read_text()) for k in keys}
    assert len(rows)==960 and all(r["source"]==ident for r in rows.values())
    results=[]
    for s in seeds:
        a0,a1=[rows[s,t,"neu","v16"] for t in (0,1)]
        ranges={r["sensor"] for k,r in rows.items() if k[0]==s}
        assert len(ranges)==1
        if a0["sensor"]!=1:
            assert a0["digest"]==a1["digest"] and a0["win"]+a1["win"]==1
        for t in (0,1):
            ref,new,direct=[rows[s,t,arm,opp] for arm,opp in (("v16","solution92"),("neu","solution92"),("neu","v16"))]
            d=paired(ref,new)
            if new["sensor"]!=1:
                assert not new["events"] and not direct["events"] and d is None
            results.append(dict(seed=s,team=t,win=new["win"],baseline=ref["win"],direct=direct["win"],sensor=new["sensor"],first_action=d))
    draw=np.random.default_rng(231123).integers(0,160,(20000,160))
    def metric(vals):
        v=np.array(vals,float).reshape((160,2)).mean(1)
        return dict(mean=float(v.mean()),ci95=np.percentile(v[draw].mean(1),[2.5,97.5]).tolist())
    gain=metric([r["win"]-r["baseline"] for r in results])
    direct=metric([r["direct"] for r in results])
    way_a=gain["ci95"][0]>0 and direct["mean"]>=.5 and direct["ci95"][0]>=.45
    way_b=direct["ci95"][0]>.5 and gain["ci95"][0]>=-.01
    res=dict(cards=160,games=len(rows),source=ident,solution=sum(r["win"] for r in results),
        baseline=sum(r["baseline"] for r in results),direct_wins=sum(r["direct"] for r in results),solution_gain=gain,direct=direct,
        changed=sum(r["first_action"] is not None for r in results),sight1=sum(r["sensor"]==1 for r in results),
        way_a=way_a,way_b=way_b,qualified=bool(way_a or way_b))
    write_once(HERE/"allgemein.json",res)
    payload="\n".join(json.dumps(r,separators=(",",":")) for r in rows.values())+"\n"
    (HERE/"allgemein_partien.jsonl.gz").write_bytes(gzip.compress(payload.encode(),mtime=0))
    print(res,flush=True)


if __name__=="__main__":
    main()
