"""Choose the first-relic prior strength using separate, card-balanced course trajectories."""
import argparse
import gzip
import json
from pathlib import Path

import jax
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

from experiments.analysis.relictsuche_20261123.ortundflotte.richtung import EXPONENTS,score_options,take
from experiments.analysis.relictsuche_20261123.flottenblick.flotte import POWER
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import choose,load,predict
from experiments.analysis.relictsuche_20261123.zielschaetzer.lernen import labels
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,stamp,write_once
from scripts.experiment import limit_threads

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def measure(path,targets,spawn,model):
    meta=json.loads(path.with_suffix(".json").read_text())
    assert sha(path)==meta["sha256"]
    with np.load(path,allow_pickle=False) as src:
        seed=int(src["seed"])
        assert seed==meta["seed"] and len(src["turn"])==meta["samples"]
        aims=np.asarray([int(x)*24+int(y) for x,y in targets])
        # Mirroring the map exchanges the two ends of the zone; testing both is side invariant.
        assert set(aims)=={(23-int(x)%24)*24+23-int(x)//24 for x in aims}
        summary=[]
        for k,t in enumerate(src["turn"]):
            t=int(t)
            a,b=src["offsets"][k:k+2]
            paths=src["paths"][a:b]
            x=src["x"][k].astype(np.float32)
            dist=src["projections"][k]
            last=src["last"][k]
            q=predict(*model,x,dist)
            fog=x[18].astype(bool)
            energy=x[19]*20
            origin=int(np.argmax(x[12]))
            scores=score_options(q,paths,last,fog,energy,origin)
            selected=[take(row) for row in scores]
            baseline=choose(q,paths,last,fog,energy,origin)
            assert selected[0]==(len(paths) if baseline is None else baseline)
            all_paths=np.concatenate((paths,np.full((1,8),origin,np.int16)))
            allowed=np.arange(1,9)+t>=int(spawn)+1
            remaining=src["remaining"][k].reshape(8,576)[:,aims]
            unit_power=POWER.reshape(576,576)[all_paths[:,:,None],aims]
            visible=((remaining+unit_power)>0).any(2) & allowed
            seen=np.where(visible.any(1),visible.argmax(1)+1,9)
            summary.append(dict(t=t,picks=selected,sight=seen[selected].tolist(),oracle=int(seen.min())))
    return dict(seed=seed,team=int(meta["index"])%2,opponent=("solution92","v16")[(meta["index"]//2)%2],situations=summary)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path);p.add_argument("stage",choices=("train","valid"))
    args=p.parse_args();limit_threads()
    n=480 if args.stage=="train" else 160
    files=sorted((args.folder/args.stage).glob("*.npz"))
    assert len(files)==n
    train=None if args.stage=="train" else json.loads((HERE/"train.json").read_text())
    if train is not None and not train["passed"]:return
    keys=np.array([int(f.stem) for f in files],np.int32)
    label=jax.jit(jax.vmap(labels))
    chunks=[]
    # Small batches keep this passive calculation inexpensive on an 8 GB laptop.
    for start in range(0,n,32):
        current=np.asarray(keys[start:start+32])
        chunks.append([np.asarray(v) for v in label(current)])
    pos,mir,_,spawn=[np.concatenate(group) for group in zip(*chunks,strict=True)]
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for i in (0,n-1):
            env.reset(seed=int(keys[i]))
            assert np.array_equal(np.array([pos[i],mir[i]]),np.asarray(env.state.relic_nodes)[[0,3]])
            assert int(env.state.relic_spawn_schedule[0])==int(spawn[i])
    finally:env.close()
    net=load()
    rows=[measure(path,(pos[i],mir[i]),spawn[i],net) for i,path in enumerate(files)]
    contrast=[]
    for r in rows:
        vals=np.array([j["sight"]+[j["oracle"]] for j in r["situations"]],float).reshape(-1,4)
        contrast.append((vals[:,[0]]-vals).mean(0) if len(vals) else np.zeros(4))
    panel=np.array(contrast)
    ii=int(np.argmax(panel[:,:3].mean(0))) if train is None else int(train["selected"])
    sampled=np.random.default_rng(231123).integers(0,n,(20000,n))
    summary=dict(cards=n,situations=sum(len(r["situations"]) for r in rows),selected=ii,exponent=EXPONENTS[ii],
        averages=panel.mean(0).tolist(),ahead=int(np.sum(panel[:,ii]>0)),behind=int(np.sum(panel[:,ii]<0)),
        any_change=sum(any(j["picks"][0]!=j["picks"][ii] for j in r["situations"]) for r in rows),
        ci95=np.quantile(panel[sampled,ii].mean(1),[.025,.975]).tolist())
    summary["passed"]=ii>0 and summary["averages"][ii]>0 and (train is None or summary["ahead"]>=2)
    files=[HERE/"PLAN.md",HERE/"archiv.py",HERE/"richtung.py",ROOT/"flottenblick/flottengewichte.npz",ROOT/"flottenblick/modell.json",ROOT/"zielschaetzer/ort.json"]
    summary["source"]=stamp({str(f.relative_to(ROOT)):sha(f) for f in files})
    if train is not None:assert summary["source"]==train["source"]
    write_once(HERE/f"{args.stage}.json",summary)
    data="\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n"
    (HERE/f"{args.stage}_karten.jsonl.gz").write_bytes(gzip.compress(data.encode(),mtime=0))


if __name__=="__main__":main()
