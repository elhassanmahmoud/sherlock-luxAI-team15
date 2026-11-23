"""Train and verify whole-map calibrated visibility against the actual first active relic and fleet power."""
import argparse
import gzip
import json
from pathlib import Path
import jax
import numpy as np
from experiments.analysis.relictsuche_20261123.sensorpaare.modell import HERE,REP,MIRROR,groups,scores,estimate,learned
from experiments.analysis.relictsuche_20261123.zeitlicher_flottenblick.lernen import samples
from experiments.analysis.relictsuche_20261123.ortundflotte.richtung import take,score_options
from experiments.analysis.relictsuche_20261123.flottenblick.flotte import POWER
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import load
from experiments.analysis.relictsuche_20261123.zielschaetzer.lernen import labels
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,write_once
from scripts.experiment import limit_threads


def fit(files,net):
    union_n=np.zeros(256);union_delta=np.zeros(256)
    count=np.zeros(96);out=np.zeros(96);weight=np.zeros(96)
    for f in files:
        for q,dist,rest,x,t,paths,last,w in samples(f,net):
            gi,base,near,old=groups(q,last,x[18].astype(bool))
            rest=rest.reshape(8,576);single=(rest>0).any(0);seen=single|single[MIRROR]
            union_n+=w*np.bincount(gi[REP],minlength=256)
            union_delta+=w*np.bincount(gi[REP],weights=seen[REP]-base[REP],minlength=256)
            use=rest<=0
            count+=w*np.bincount(near[use],minlength=96)
            out+=w*np.bincount(near[use],weights=(rest[use]==0),minlength=96)
    i=np.arange(96);default=np.where((i//4)%3==2,.25,1.)
    np.savez_compressed(HERE/'tabellen.npz',union=union_delta/(64+union_n),near=(out+64*default)/(64+count))


def analyze(files,net,stage):
    items=[];table=learned();seeds=np.array([int(p.stem) for p in files],dtype=np.int32)
    lookup=jax.jit(jax.vmap(labels));views={}
    for chunk in np.array_split(seeds,len(seeds)//32):
        a,b,_,spawn=map(np.asarray,lookup(chunk))
        for s,p,other,birth in zip(chunk,a,b,spawn,strict=True):
            views[int(s)]=(np.array([24*p[0]+p[1],24*other[0]+other[1]],int),int(birth))
    for f in files:
        seen,spawn=views[int(f.stem)];records=[]
        for q,dist,rem,x,t,paths,last,w in samples(f,net):
            rest=rem.reshape(8,576);fog=x[18].astype(bool);energy=x[19].astype(float)*20;start=int(x[12].argmax())
            alternatives=scores(q,paths,last,fog,energy,start,table)
            reference=score_options(q,paths,last,fog,energy,start)[2]
            assert np.allclose(reference,alternatives[0],rtol=1.e-5,atol=1.e-5) and take(alternatives[0])==take(reference)
            choice=[take(row) for row in alternatives];path=np.vstack((paths,np.full((1,8),start)))[choice]
            sight=((rest[:,seen]+POWER[path[:,:,None],seen])>0).any(2)&(t+np.arange(1,9)>=spawn+1)
            found=np.where(sight.any(1),sight.argmax(1)+1,9)
            pair,adj=estimate(q,last,fog,table)
            alone=(rest>0).any(0);truth=alone|alone[MIRROR];mask=rest<=0
            errs=[float(np.mean((prob[REP]-truth[REP])**2)) for prob in pair]
            errs += [float(np.mean((prob[mask]-(rest[mask]==0))**2)) for prob in adj]
            records.append(dict(t=t,choices=choice,sight=found.tolist(),brier=errs))
        items.append(dict(seed=int(f.stem),cases=records))
    m=np.array([np.mean([v['sight']+v['brier'] for v in r['cases']],axis=0) if r['cases'] else np.zeros(8) for r in items])
    gain=m[:,[0]]-m[:,:4];chosen=int(np.argmax(gain.mean(0))) if stage=='train' else json.loads((HERE/'train.json').read_bytes())['chosen']
    delta=gain[:,chosen];draw=np.random.default_rng(231123).integers(0,len(m),(20000,len(m)))
    brier=m[:,4:].mean(0);has_cal=(chosen in (1,3) and brier[1]<brier[0]) or (chosen in (2,3) and brier[3]<brier[2])
    win=int((delta>0).sum())
    write_once(HERE/(stage+'.json'),dict(cards=len(m),situations=sum(len(z['cases']) for z in items),
        chosen=chosen,gain=gain.mean(0).tolist(),ci=np.quantile(delta[draw].mean(1),[.025,.975]).tolist(),
        ahead=win,behind=int((delta<0).sum()),brier=brier.tolist(),passed=bool(chosen and delta.mean()>0 and (stage=='train' or (has_cal and win>=3))),model=sha(HERE/'tabellen.npz')))
    (HERE/(stage+'_karten.jsonl.gz')).write_bytes(gzip.compress(b''.join(json.dumps(r,separators=(',',':')).encode()+b'\n' for r in items),mtime=0))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('stage',choices=('fit','train','valid'));a=p.parse_args()
    limit_threads();stage='train' if a.stage=='fit' else a.stage
    if a.stage=='valid' and not json.loads((HERE/'train.json').read_bytes())['passed']:return
    files=sorted((a.folder/stage).glob('*.npz'));assert len(files)==(480 if stage=='train' else 160)
    net=load()
    if a.stage=='fit':fit(files,net)
    else:analyze(files,net,stage)


if __name__=='__main__':main()
