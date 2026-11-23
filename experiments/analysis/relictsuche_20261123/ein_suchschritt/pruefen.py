"""Test a single scout override against the full scout and the unchanged release on common cards."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path

import jax
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.abschlusspruefung.vergleich import play_if_available
from experiments.analysis.relictsuche_20261123.ortundflotte.kandidat import create
from experiments.analysis.relictsuche_20261123.sieben_eroeffnungen.nachspiel import LimitedScout
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF, play, sha, stamp, validate, write_once
from scripts.experiment import limit_threads


HERE = Path(__file__).resolve().parent
ARMS = (("v16","solution92"),("eins","solution92"),("voll","solution92"),("eins","v16"),("voll","v16"))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    p.add_argument("stage",choices=("freeze","play","score"))
    p.add_argument("lane",type=int,nargs="?",default=0)
    p.add_argument("workers",type=int,nargs="?",default=8)
    a=p.parse_args()
    limit_threads()
    file=HERE/"karten.json"
    files=[HERE/"PLAN.md",Path(__file__),HERE.parent/"sieben_eroeffnungen/nachspiel.py",HERE.parent/"abschlusspruefung/nominierung.json"]
    sources={str(f.relative_to(HERE.parent)):sha(f) for f in files}
    if a.stage=="freeze":
        seeds=np.arange(166200000,166201000,dtype=np.int32)
        cards=list(map(int,seeds[np.asarray(jax.jit(jax.vmap(sensor))(seeds))==1][:32]))
        assert len(cards)==32
        write_once(file,dict(cards=cards,sources=sources))
        return
    spec=json.loads(file.read_bytes())
    assert spec["sources"]==sources
    token=stamp(spec)
    keys=[("test",s,t,arm,opp) for s in spec["cards"] for t in (0,1) for arm,opp in ARMS]
    def target(k):
        return a.folder/("_".join(map(str,k))+".json")
    if a.stage=="play":
        env=LuxAIS3GymEnv(numpy_output=True)
        factories={"v16":None,"eins":lambda side: LimitedScout(side,1),"voll":create}
        try:
            for offset in range(a.workers):
                for k in keys[(a.lane+offset)%a.workers::a.workers]:
                    if datetime.now(CUTOFF.tzinfo)>=CUTOFF:
                        return
                    play_if_available(target(k),token,lambda:play(env,k,token,factories[k[3]]))
        finally:
            env.close()
        return
    games=[]
    for k in keys:
        r=json.loads(target(k).read_bytes())
        validate(r,k,token)
        if k[3]=="eins":
            assert len(r["events"])<=1
        games.append(r)
    assert len(games)==320
    values=[]
    for i in range(0,len(games),5):
        base,one,full,d1,df=games[i:i+5]
        if len(full["events"])<=1:
            assert one["action_hash"]==full["action_hash"]
        if len(df["events"])<=1:
            assert d1["action_hash"]==df["action_hash"]
        values.append([r["win"] for r in (base,one,full,d1,df)]+[r["sight"] for r in (base,one,full)]+
                      [r["credit"] for r in (base,one,full)]+[one["action_hash"]!=full["action_hash"]])
    a0=np.asarray(values).reshape(32,2,-1)
    w=a0.sum((0,1))[:5].tolist()
    times=a0.mean((0,1))[5:11].tolist()
    by_map=np.stack((a0[:,:,1]-a0[:,:,0],a0[:,:,1]-a0[:,:,2],a0[:,:,7]-a0[:,:,6],a0[:,:,3]),axis=-1).mean(1)
    samples=np.random.default_rng(231123).integers(0,32,(20000,32))
    ci=np.quantile(by_map[samples].mean(1),[.025,.975],axis=0).T.tolist()
    passed=w[1]>=max(w[0],w[2]) and w[3]>=32 and times[1]<times[2]
    out=dict(source=token,arms=ARMS,wins=w,times=times,changed=int(a0[:,:,11].sum()),ci=ci,passed=bool(passed))
    write_once(HERE/"ergebnis.json",out)
    (HERE/"partien.jsonl.gz").write_bytes(gzip.compress(b"".join((json.dumps(r)+"\n").encode() for r in games),mtime=0))


if __name__=="__main__":
    main()
