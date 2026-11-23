"""Learn opponent scoring displacements from its last public velocity; private arrays are labels only."""
import argparse
import gzip
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "spaetgebiet/ortsmodell"
sys.path.insert(0, str(OLD))
from kandidat import model as original_model
from lernen import STORE, digest, observation
from ort import ORB, MID, OTHER, PublicHistory, predict

MIX = np.array([0.,.15,.35,.60])
GRID = np.indices((24,24)).reshape(2,-1).T
OFF = 23
DIR = {(-1,0):0,(1,0):1,(0,-1):2,(0,1):3,(0,0):4}
HORIZON = 6


def frames(receipt):
    meta=json.loads(receipt.read_bytes())
    public=receipt.parent/meta['public']
    labels=receipt.parent/meta['private']
    assert digest(public)==meta['public_sha'] and digest(labels)==meta['private_sha']
    with np.load(public) as f:
        data={k:f[k] for k in ('sensor_mask','units_mask','team_points','relic_nodes','relic_nodes_mask','position','energy','known_points')}
    with np.load(labels) as f:
        judge={k:f[k] for k in ('real_position','real_live','scoring')}
    judge['scoring']=np.unpackbits(judge['scoring'],axis=-1,bitorder='little').reshape(-1,2,24,24).astype(bool)
    return meta,data,judge


class Tracks:
    def __init__(self,foe):
        self.foe=foe
        self.clock=np.full(16,-1000,int)
        self.position=np.zeros((16,2),int)
        self.dir=np.full(16,5,int)
        self.known=np.zeros(16,int)

    def coord(self,xy):
        return 23-xy[...,::-1] if self.foe else xy

    def update(self,t,obs,known):
        if t%101==0:
            self.clock.fill(-1000)
        live=np.asarray(obs['units_mask'][self.foe],bool) & (np.asarray(obs['units']['energy'][self.foe]).reshape(-1)>=0)
        for i in np.flatnonzero(live):
            pos=obs['units']['position'][self.foe,i]
            q=self.coord(pos)
            self.dir[i]=DIR.get(tuple(q-self.position[i]),5) if t-self.clock[i]==1 else 5
            self.known[i]=int(known[tuple(pos)])
            self.position[i]=q
            self.clock[i]=t

    def active(self,t):
        age=t-self.clock
        return [(i,int(np.searchsorted([0,2,5,9,18],age[i])),self.dir[i],self.known[i]) for i in np.flatnonzero(age<=18)]


def train(receipts):
    counts=np.zeros((5,6,2,47,47),float)
    for path in receipts:
        meta,pub,truth=frames(path);foe=1-meta['team'];h=Tracks(foe)
        for t in range(303):
            h.update(t,observation(pub,t),pub['known_points'][t])
            m,turn=divmod(t,101)
            if m==0 or turn%5 or not 5<=turn<=90:continue
            for i,age,d,k in h.active(t):
                for u in range(t+1,t+HORIZON+1):
                    if not truth['real_live'][u,foe,i]:continue
                    at=truth['real_position'][u,foe,i]
                    if truth['scoring'][u,foe,at[0],at[1]]:
                        delta=h.coord(at)-h.position[i]
                        counts[age,d,k,delta[0]+OFF,delta[1]+OFF]+=1
    # Counts per tracked slot retain the relative probability that different public histories score.
    # Smoothing leaves even rare movement types backed by the broader age-specific shape.
    broad=counts.sum((1,2))
    broad/=np.maximum(1,broad.sum((1,2),keepdims=True))
    smoothed=counts+64*broad[:,None,None]
    return smoothed/np.maximum(1,smoothed.sum((3,4),keepdims=True)), int(counts.sum())


def forecast(h,t,kernels):
    heat=np.zeros(576)
    for i,a,d,k in h.active(t):
        delta=GRID-h.position[i]
        heat+=kernels[a,d,k,delta[:,0]+OFF,delta[:,1]+OFF]
    if h.foe:heat=heat.reshape(24,24)[::-1,::-1].T.ravel()
    return heat


def measure(receipt,kernels):
    meta,pub,truth=frames(receipt);foe=1-meta['team']
    tracks=Tracks(foe);hist=PublicHistory(meta['team'])
    values=[]
    for t in range(303):
        obs=observation(pub,t);hist.update(t,obs);tracks.update(t,obs,pub['known_points'][t])
        m,step=divmod(t,101)
        if m==0 or step%5 or not 5<=step<=90:continue
        # The eligible physical cells are defined only by public information at time t.
        mask=(~hist.zone)&(~pub['sensor_mask'][t].ravel())
        future=truth['scoring'][t+1:t+HORIZON+1,foe].sum(0).ravel()*mask
        if not future.any():continue
        actual=np.bincount(ORB,weights=future,minlength=300)
        actual/=actual.sum()
        _,base=predict(hist,original_model())
        visible=mask[MID]|mask[OTHER]
        base=(base+1.e-7)*visible;base/=base.sum()
        heat=forecast(tracks,t,kernels)*mask
        route=np.bincount(ORB,weights=heat,minlength=300)
        if route.sum():route/=route.sum()
        else:route=base
        probabilities=(1-MIX[:,None])*base+MIX[:,None]*route
        logloss=-(np.log(probabilities.clip(1.e-12))@actual)
        top=actual[np.argsort(-probabilities,axis=1,kind='stable')[:,:10]].sum(1)
        values.append(dict(t=t,loss=logloss.tolist(),top=top.tolist(),observed=int(future.sum()),tracks=len(tracks.active(t))))
    return dict(seed=meta['seed'],opponent=meta['opponent'],data=values)


def compact(rows,index):
    result={}
    for who in ('all','solution92','v16'):
        chosen=[r for r in rows if r['data'] and (who=='all' or r['opponent']==who)]
        outcome=np.array([[np.mean([s[k] for s in r['data']],axis=0) for k in ('loss','top')] for r in chosen])
        if not len(outcome):
            result[who]={'cards':0};continue
        diff=outcome[:,:,index]-outcome[:,:,0];diff[:,0]*=-1
        idx=np.random.default_rng(231123).integers(0,len(diff),(20000,len(diff)))
        result[who]=dict(cards=len(chosen),frames=sum(len(r['data']) for r in chosen),gain=diff.mean(0).tolist(),
                       improvement_cards=int((diff[:,0]>1.e-8).sum()),ci=np.quantile(diff[idx].mean(1),[.025,.975],axis=0).T.tolist(),
                       loss=outcome[:,0].mean(0).tolist(),top=outcome[:,1].mean(0).tolist())
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('op',choices=('fit','measure','score'));p.add_argument('stage',choices=('train','valid'))
    p.add_argument('store',type=Path);p.add_argument('lane',type=int,nargs='?',default=0);p.add_argument('stride',type=int,nargs='?',default=1)
    a=p.parse_args()
    receipt=sorted((STORE/a.stage).glob('*.json'));assert len(receipt)==(160 if a.stage=='train' else 48)
    a.store.mkdir(exist_ok=True,parents=True)
    if a.op=='fit':
        assert a.stage=='train';kernels,n=train(receipt)
        np.savez_compressed(HERE/'gelernte_spuren.npz',kernel=kernels.astype(np.float32),observations=n);return
    path=HERE/'gelernte_spuren.npz'
    with np.load(path) as q:kernels=q['kernel']
    decision=HERE/'train.json'
    if a.stage=='valid':assert json.loads(decision.read_bytes())['selected']>0
    folder=a.store/a.stage;folder.mkdir(exist_ok=True)
    if a.op=='measure':
        for f in receipt[a.lane::a.stride]:
            v=measure(f,kernels)
            (folder/(f.stem+'.json')).write_text(json.dumps(v,separators=(',',':')))
        return
    rows=[json.loads((folder/(f.stem+'.json')).read_bytes()) for f in receipt]
    assert len({r['seed'] for r in rows})==len(receipt)
    means=compact(rows,0)['all']['loss']
    best=int(np.argmin(means)) if a.stage=='train' else json.loads(decision.read_bytes())['selected']
    metrics=compact(rows,best);r=metrics['all']
    status=dict(selected=best,weight=float(MIX[best]),source=digest(path),cards=len(rows),metrics=metrics,
                passed=best>0 and r['gain'][0]>0 and r['gain'][1]>=0 and r['improvement_cards']>=3)
    (HERE/(a.stage+'.json')).write_text(json.dumps(status,separators=(',',':'))+'\n')
    with (HERE/(a.stage+'_karten.jsonl.gz')).open('wb') as f:
        f.write(gzip.compress(b''.join(json.dumps(r,separators=(',',':')).encode()+b'\n' for r in rows),mtime=0))


if __name__=='__main__':main()
