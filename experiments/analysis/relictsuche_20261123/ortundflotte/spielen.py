"""Paired whole games for the relic/fleet route, with an original no-prior identity check."""
import argparse
from datetime import datetime
from pathlib import Path
import gzip
import json

import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

from experiments.analysis.relictsuche_20261123.ortundflotte.kandidat import HERE,create
from experiments.analysis.relictsuche_20261123.flottenblick.kandidat import create as fleet
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,common_source,play,sha,stamp,validate,write_once
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from scripts.experiment import limit_threads


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path);p.add_argument("stage",choices=("tech","play","score"))
    p.add_argument("lane",type=int,nargs="?",default=0);p.add_argument("stride",type=int,nargs="?",default=1)
    a=p.parse_args();limit_threads()
    results=json.loads((HERE/"valid.json").read_text())
    assert results["passed"] and results["selected"]==json.loads((HERE/"train.json").read_text())["selected"]
    files=[HERE/f for f in ("PLAN.md","richtung.py","kandidat.py","spielen.py","train.json","valid.json")]
    files+= [HERE.parent/"flottenblick"/n for n in ("flotte.py","kandidat.py","vorhersage.py","flottengewichte.npz","modell.json")]
    ident=stamp(dict(common=common_source(),files={str(f.relative_to(HERE.parent)):sha(f) for f in files}))
    if a.stage=="tech":
        env=LuxAIS3GymEnv(numpy_output=True);cases=[]
        try:
            with gzip.open(HERE.parent/"flottenblick/ganzspiel/partien.jsonl.gz","rt") as f:
                archival=[r for r in map(json.loads,f) if r["id"]=="flotte" and len(r["events"])>=3]
            for t,opp in ((0,"solution92"),(1,"v16")):
                ref=next(r for r in archival if r["team"]==t and r["opponent"]==opp)
                seed=ref["seed"]
                k=("test",seed,t,"scout",opp)
                orig=play(env,k,ident,fleet)
                equal=play(env,k,ident,lambda side:create(side,0))
                assert equal==orig and orig["action_hash"]==ref["action_hash"] and orig["matches"]==ref["matches"]
                new=play(env,k,ident,create)
                cases.append(dict(seed=seed,team=t,opponent=opp,original=orig,new=new))
        finally:env.close()
        assert any(r["original"]["events"] for r in cases)
        write_once(HERE/"technik.json",dict(source=ident,cases=cases))
        return
    assert json.loads((HERE/"technik.json").read_text())["source"]==ident
    import jax
    pool=np.arange(164050000,164051000,dtype=np.int32)
    seeds=[int(s) for s in pool[np.asarray(jax.jit(jax.vmap(sensor))(pool))==1][:48]]
    keys=[("test",s,t,arm,opp) for s in seeds for t in (0,1) for arm,opp in
          (("reference","solution92"),("scout","solution92"),("scout","v16"))]
    def path(k):return a.folder/"spiele"/("_".join(map(str,k))+".json")
    if a.stage=="play":
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in keys[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                if path(k).exists():
                    assert json.loads(path(k).read_text())["source"]==ident
                else:write_once(path(k),play(env,k,ident,create if k[3]=="scout" else None))
        finally:env.close()
        return
    cards=[];packed=[]
    for seed in seeds:
        for t in (0,1):
            rows=[]
            for arm,opp in (("reference","solution92"),("scout","solution92"),("scout","v16")):
                k=("test",seed,t,arm,opp);r=json.loads(path(k).read_text());validate(r,k,ident);rows.append(r);packed.append(r)
            base,new,direct=rows
            if not new["events"]:assert new["action_hash"]==base["action_hash"] and new["matches"]==base["matches"]
            cards.append([base["win"],new["win"],direct["win"],base["sight"]-new["sight"],base["credit"]-new["credit"]])
    mat=np.array(cards).reshape(48,2,5)
    sums=mat.sum((0,1));by_map=mat.mean(1)
    draws=np.random.default_rng(231123).integers(0,48,(20000,48))
    ci=np.quantile(by_map[draws].mean(1),[.025,.975],axis=0)
    passed=sums[3]>0 and sums[1]>=sums[0] and sums[2]>=48 and (sums[1]>sums[0] or sums[2]>48)
    write_once(HERE/"duelle.json",dict(games=len(packed),cards=48,source=ident,columns=["base","candidate","direct","sight","credit"],
                                      sums=sums.tolist(),means=by_map.mean(0).tolist(),ci95=ci.T.tolist(),passed=bool(passed)))
    data="\n".join(json.dumps(r,separators=(",",":")) for r in packed)+"\n"
    (HERE/"duelle_karten.jsonl.gz").write_bytes(gzip.compress(data.encode(),mtime=0))


if __name__=="__main__":main()
