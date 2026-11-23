"""Real independent game panel; the inherited low-vision match monitor checks every changed free-ship command."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.kontextsuche.kandidat import HERE,create
from experiments.analysis.relictsuche_20261123.netzvertrauen.pruefen import dual,evaluate
from experiments.analysis.relictsuche_20261123.netzvertrauen.erheben import frozen
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,play,sha,stamp,validate,write_once
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from scripts.experiment import limit_threads


def schedule():
    import jax
    pool=np.arange(163810000,163811000,dtype=np.int32)
    seeds=pool[np.asarray(jax.jit(jax.vmap(sensor))(pool))==1][:64]
    return [(int(s),t,arm,opp) for s in seeds for t,arm,opp in
            [(-1,"self","v16"),*((t,a,o) for t in (0,1) for a,o in
              (("reference","solution92"),("select","solution92"),("select","v16")))]]


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path);p.add_argument("stage",choices=("play","score"))
    p.add_argument("lane",nargs="?",default=0,type=int);p.add_argument("stride",nargs="?",default=1,type=int)
    a=p.parse_args()
    checked=json.loads((HERE/"technik.json").read_text())
    assert checked["model_sha"]==sha(HERE/"modell.json") and all(r["steps"]==303 for r in checked["cases"]) and len(checked["cases"])==4
    deps=[HERE/n for n in ("PLAN.md","modell.json","technik.json","spielen.py","kandidat.py")]
    deps.extend(HERE.parent/n for n in ("netzvertrauen/lernen.py","netzvertrauen/pruefen.py","netzvertrauen/kandidat.py","spielwert/pruefspiele.py"))
    token=stamp(dict(base=frozen(),files={str(f.relative_to(HERE.parent)):sha(f) for f in deps}))
    jobs=schedule()
    assert len(set(jobs))==len(jobs)==448 and 0<=a.lane<a.stride
    def dest(k):return a.folder/"spiele"/("_".join(map(str,k))+".json")
    if a.stage=="play":
        limit_threads()
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in jobs[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                if dest(k).exists():
                    assert json.loads(dest(k).read_text())["source"]==token
                    continue
                s,t,arm,opp=k
                if arm=="self":
                    r=dual(env,s,token)
                else:
                    chosen=[]
                    def factory(side):
                        actor=create(side)
                        chosen.append(actor)
                        return actor
                    r=play(env,("test",*k),token,factory if arm=="select" else None)
                    if chosen:r.update(decision=chosen[0].decision,first_proposal=chosen[0].at)
                write_once(dest(k),r)
        finally:env.close()
        return
    packed=[json.loads(dest(k).read_text()) for k in jobs]
    assert all(q["source"]==token for q in packed)
    rows={}
    for q in packed:
        for r in q.get("views",[q]):
            k=r["seed"],r["team"],r["id"],r["opponent"]
            validate(r,("test",*k),token)
            assert k not in rows
            rows[k]=r
    assert len(rows)==512
    result=evaluate(rows)
    sol,head=(result["groups"][o] for o in ("solution92","v16"))
    result["gates"]["solution_earlier"]=sol["sight"]["mean"]>0
    result["gates"]["strict_improvement"]=sol["wins"]>sol["base_wins"] or head["wins"]>64
    result["passed"]=all(result["gates"].values())
    write_once(HERE/"duelle.json",dict(source=token,**result))
    payload="\n".join(json.dumps(r,separators=(",",":")) for r in packed)+"\n"
    (HERE/"duelle.jsonl.gz").write_bytes(gzip.compress(payload.encode(),mtime=0))
    print(result)


if __name__=="__main__":main()
