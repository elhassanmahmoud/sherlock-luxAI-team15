"""Calibrate arrival profiles on full maps and test the real first relic on separate cards."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np
from experiments.analysis.relictsuche_20261123.zeitlicher_flottenblick.zeitmodell import HORIZON,GROUPS,bins,cumulative,scores
from experiments.analysis.relictsuche_20261123.ortundflotte.richtung import score_options,take
from experiments.analysis.relictsuche_20261123.flottenblick.flotte import POWER
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import load,predict
from experiments.analysis.relictsuche_20261123.zielschaetzer.lernen import labels
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,write_once
from scripts.experiment import limit_threads

HERE=Path(__file__).resolve().parent


def samples(path,model):
    meta=json.loads(path.with_suffix(".json").read_text())
    assert sha(path)==meta["sha256"]
    with np.load(path,allow_pickle=False) as a:
        n=meta["samples"];assert n==len(a["turn"]) and int(a["seed"])==int(path.stem)
        # Copy once per game. Repeated access to a compressed array would decompress every sample.
        x,dist,turn,rest,offset,paths,last=[a[k] for k in ("x","projections","turn","remaining","offsets","paths","last")]
    for i in range(n):
        q=predict(*model,x[i],dist[i])
        yield q,dist[i],rest[i],x[i],int(turn[i]),paths[offset[i]:offset[i+1]],last[i],1/n


def train(files,model):
    hit=np.zeros((GROUPS,HORIZON))
    for path in files:
        for q,dist,remaining,_,_,_,_,w in samples(path,model):
            group=bins(q,dist).ravel()
            seen=np.maximum.accumulate(remaining.reshape(HORIZON,-1)>0,axis=0)
            for j,s in enumerate(seen):
                hit[:,j]+=w*np.bincount(group[s],minlength=GROUPS)
    avg=hit.sum(0);avg/=avg[-1]
    tables=(hit+8*avg)/(hit[:,[-1]]+8)
    assert np.all(np.diff(tables,axis=1)>=-1e-12) and np.allclose(tables[:,-1],1)
    write_once(HERE/"zeitmodell.json",dict(cards=len(files),table=tables.tolist(),global_profile=avg.tolist()))


def validate(files,model):
    import jax
    from luxai_s3.wrappers import LuxAIS3GymEnv
    table=np.array(json.loads((HERE/"zeitmodell.json").read_bytes())["table"])
    label=jax.jit(jax.vmap(labels))
    seeds=np.array([int(p.stem) for p in files],np.int32);actual={}
    for chunk in np.array_split(seeds,5):
        pos,mir,_,spawn=[np.asarray(x) for x in label(chunk)]
        for s,a,b,t in zip(chunk,pos,mir,spawn,strict=True):
            actual[int(s)]=([int(x)*24+int(y) for x,y in (a,b)],int(t))
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for s in (int(seeds[0]),int(seeds[-1])):
            env.reset(seed=s)
            assert actual[s]==([int(x)*24+int(y) for x,y in np.asarray(env.state.relic_nodes)[[0,3]]],int(env.state.relic_spawn_schedule[0]))
    finally:env.close()
    records=[]
    for path in files:
        seed=int(path.stem);aims,spawn=actual[seed];cases=[]
        for q,dist,remaining,x,t,paths,last,_ in samples(path,model):
            learned=cumulative(q,dist,table)
            fixed=np.broadcast_to(q.ravel(),(8,576))
            assert np.allclose(learned[-1],fixed[-1])
            observed=np.maximum.accumulate(remaining.reshape(8,576)>0,axis=0)
            errors=[float(np.mean((v-observed)**2)) for v in (fixed,learned)]
            fog=x[18].astype(bool);energy=x[19].astype(float)*20;origin=int(x[12].argmax())
            path_scores=score_options(q,paths,last,fog,energy,origin)[2]
            choices=[take(path_scores),*[take(scores(v,paths,last,fog,energy,origin,t)) for v in (fixed,learned)]]
            routes=np.vstack((paths,np.full((1,8),origin)))
            power=POWER[routes[:,:,None],aims]
            sight=((remaining.reshape(8,576)[:,aims]+power)>0).any(2)&(t+np.arange(1,9)>=spawn+1)
            delay=np.where(sight.any(1),sight.argmax(1)+1,9)
            cases.append(dict(t=t,picks=choices,sight=delay[choices].tolist(),brier=errors))
        records.append({"seed":seed,"cases":cases})
    m=np.asarray([np.mean([[*r["sight"],*r["brier"]] for r in z["cases"]],axis=0) if z["cases"] else np.zeros(5) for z in records])
    delta=m[:,0]-m[:,2];draw=np.random.default_rng(231123).integers(0,len(m),(20000,len(m)))
    gates=dict(calibrated=bool(m[:,4].mean()<m[:,3].mean()),earlier=bool(delta.mean()>0),maps=int(sum(delta>0))>=3)
    result=dict(cards=len(files),opportunities=sum(len(z["cases"]) for z in records),mean_sight=m[:,:3].mean(0).tolist(),
                brier=m[:,3:].mean(0).tolist(),earlier=float(delta.mean()),ci=np.quantile(delta[draw].mean(1),[.025,.975]).tolist(),
                advanced=int(sum(delta>0)),delayed=int(sum(delta<0)),gates=gates,passed=all(gates.values()),model=sha(HERE/"zeitmodell.json"))
    write_once(HERE/"valid.json",result)
    (HERE/"situationen.jsonl.gz").write_bytes(gzip.compress(b"".join(json.dumps(z,separators=(",",":")).encode()+b"\n" for z in records),mtime=0))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("folder",type=Path);p.add_argument("stage",choices=("train","valid"))
    args=p.parse_args();limit_threads();files=sorted((args.folder/args.stage).glob("*.npz"))
    assert len(files)==(480 if args.stage=="train" else 160)
    (train if args.stage=="train" else validate)(files,load())
