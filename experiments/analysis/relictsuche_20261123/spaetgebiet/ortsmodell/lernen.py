"""Supervised center and enemy scoring-field distributions, map-disjoint training and validation."""
import argparse
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

from ort import HERE, MID, ORB, OLD, Z, PublicHistory, orbit, priors

STORE=Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/spaetort')

def digest(p):return sha256(p.read_bytes()).hexdigest()

def observation(d,t):
    return {**{k:d[k][t] for k in ('sensor_mask','units_mask','team_points','relic_nodes','relic_nodes_mask')},
        'units':{k:d[k][t] for k in ('position','energy')}}

def extract(receipt):
    meta=json.loads(receipt.read_bytes()); team=meta['team'];rival=1-team
    pub=receipt.parent/meta['public']; truth=receipt.parent/meta['private']
    if digest(pub)!=meta['public_sha'] or digest(truth)!=meta['private_sha']:raise ValueError('Changed game')
    with np.load(pub) as p: data={k:p[k] for k in ('sensor_mask','units_mask','team_points','relic_nodes','relic_nodes_mask','position','energy')}
    with np.load(truth) as p: judge={k:p[k] for k in p.files}
    scores=np.unpackbits(judge['scoring'],axis=-1,bitorder='little').astype(bool)
    weights=judge['weights'].ravel(); centres=judge['centres'];centerids=ORB[24*centres[:,0]+centres[:,1]]
    history=PublicHistory(team); output=[]; coverage=0; snapshots=Counter()
    for t in range(303):
        mi,ms=divmod(t,101)
        history.update(t,observation(data,t))
        live=judge['real_live'][t,rival]; p=judge['real_position'][t,rival,live]
        if ms and len(p):
            if not history.reach[np.flatnonzero(live),p[:,0],p[:,1]].all():raise ValueError(f'True enemy excluded on {receipt.name} frame {t}')
            coverage+=len(p)
        if mi==0 or not 10<=ms<=80 or not history.known:continue
        unseen=[i for i,a in enumerate(judge['active'][t]) if a and i not in history.known]
        if history.alarm and not unseen:raise ValueError('Geometric signal without true missing pair')
        if not unseen:continue
        c,support,q,off=history.features()
        if not support[centerids[unseen]].all():raise ValueError(f'True center excluded: {receipt.name} {t} {unseen} {history.first_proof}')
        snapshots['complete_support_checked']+=1
        anchor=history.first_proof==t
        if not anchor and ms%5:continue
        extra=(~history.zone)&np.isin(weights,np.array(unseen)+1)
        target=np.zeros(300,np.float32);labels=np.zeros(300,np.float32)
        future=scores[t:min(t+5,(mi+1)*101),rival].sum(0)*extra
        np.add.at(labels,ORB,future)
        field_cells=labels.sum()
        if field_cells:labels/=field_cells
        for i in unseen:target[centerids[i]]+=1+min(3,int(future[weights==i+1].sum()))
        target/=target.sum()
        if np.any(labels[~off]):raise ValueError('Scored-field target overlaps known area')
        output.append((c,support,target,q,off,labels,meta['seed'],team,int(meta['opponent']=='v16'),t,int(anchor),int(history.first_proof is not None),int(field_cells),sum(s.sum() for s in scores[t,:,~history.zone])))
    if not output:return None,coverage,snapshots
    return [np.stack(x) for x in zip(*output,strict=True)],coverage,snapshots

NAMES=('center','allowed','yc','field','off','yf','seed','team','op','t','anchor','proof','fields','outside')

def extract_split(which,partial):
    maps=json.loads((HERE/'karten.json').read_bytes())[which]
    files=sorted((STORE/which).glob('*.json'))
    if not partial and len(files)!=len(maps):raise ValueError(f'{which}: only {len(files)}/{len(maps)} games')
    rows=[];reach=0;stats=Counter(); meta=[]
    for f in files:
        a,checked,count=extract(f);reach+=checked;stats.update(count)
        if a is not None:rows.append(a)
        row=json.loads(f.read_bytes());i=maps.index(row['seed'])
        if row['split']!=which or row['team']!=i%2 or row['opponent']!=('solution92','v16')[i//2%2] or row['steps']!=303:
            raise ValueError('Unexpected sampling assignment')
        for name,sha in row['source'].items():
            target=HERE/name if name!='agent.zip' else HERE.parents[4]/'experiments/releases/20261117_sherlock_v16/agent.zip'
            if digest(target)!=sha:raise ValueError('Collection dependencies changed')
        meta.append(row)
    if len({r['seed'] for r in meta})!=len(files):raise ValueError('Duplicate map')
    d={k:np.concatenate(v) for k,v in zip(NAMES,zip(*rows,strict=True),strict=True)}
    stats.update(games=len(files),reach_checks=reach,examples=len(d['t']),seeds_with_labels=len(np.unique(d['seed'])),anchors=int(d['anchor'].sum()),external_foe_targets=int((d['fields']>0).sum()))
    return d,dict(stats),meta

def train(x,y,mask,weight,initial,penalty):
    x=x.astype(float); y=y.astype(float);weight=weight/weight.sum()
    def value(w):
        logits=x@w;logits=np.where(mask,logits,-1.e8)
        lse=logsumexp(logits,axis=1)
        p=np.exp(logits-lse[:,None]); diff=(p-y)*weight[:,None]
        loss=np.sum(weight*(lse-np.sum(y*logits,axis=1)))
        return loss+.5*penalty*((w-initial)**2).sum(),np.einsum('ij,ijk->k',diff,x)+penalty*(w-initial)
    result=minimize(value,initial,jac=True,method='L-BFGS-B',options={'maxiter':120,'ftol':1.e-10})
    if not result.success:raise ValueError(result.message)
    return result.x

def prob(x,w,mask):
    logits=np.where(mask,x@w,-1.e8);return np.exp(logits-logsumexp(logits,axis=1)[:,None])

def field_features(d,center):
    coverage=(center@Z[:,MID]).clip(1.e-7,1.)
    return np.concatenate((d['field'],np.log(coverage)[:,:,None]),axis=2),d['off']&((d['allowed'].astype(np.float32)@Z[:,MID])>0)

def metrics(probs,y,groups):
    rows={}
    for name,mask in groups.items():
        s=mask&(y.sum(1)>0)
        if not s.any():continue
        local={}
        for method,arr in probs.items():
            p=arr[s]; target=y[s]
            k=min(10,p.shape[1]); cut=np.sort(p,axis=1)[:,-k,None]
            high=p>cut; ties=p==cut
            cred=high+ties*(k-high.sum(1))[:,None]/np.maximum(1,ties.sum(1))[:,None]
            local[method]={'logloss':float((-np.log(np.maximum(1.e-12,p))*target).sum(1).mean()),'top10cells':float((cred*target).sum(1).mean())}
        rows[name]={'n':int(s.sum()),'models':local}
    return rows

def run(partial):
    datasets={}; source={}; manifest=[]
    for part in ('train','valid'):
        d,measure,rows=extract_split(part,partial);datasets[part]=d;source[part]=measure;manifest.extend(rows);print(part,measure,flush=True)
    a=datasets['train']; b=datasets['valid']
    if set(a['seed'])&set(b['seed']):raise ValueError('Leakage')
    groups=np.unique(a['seed'],return_inverse=True,return_counts=True)
    weights=(1+3*a['anchor']+a['proof'])/np.sqrt(groups[2][groups[1]])
    start=np.zeros(a['center'].shape[-1]);start[0]=1
    wc=train(a['center'],a['yc'],a['allowed'],weights,start,.015)
    ca=prob(a['center'],wc,a['allowed']); fa,ma=field_features(a,ca);take=a['fields']>0
    if np.any(a['yf'][~ma]>0):raise ValueError('Impossible true scoring tile given real active centers')
    sf=np.zeros(fa.shape[-1]);sf[-1]=1
    wf=train(fa[take],a['yf'][take],ma[take],weights[take],sf,.02)
    c=prob(b['center'],wc,b['allowed']);bl=prob(b['center'],start,b['allowed']);fb,mb=field_features(b,c)
    q=prob(fb,wf,mb);ql=prob(fb,sf,mb)
    select={'all':np.ones(len(c),bool),'strict_first':b['anchor']>0,'after_strict':b['proof']>0,'foe_scores':b['fields']>0,'side0':b['team']==0,'side1':b['team']==1,'solution':b['op']==0,'v16':b['op']==1}
    result={'sampling':source,'center':metrics({'old_restricted':bl,'trained':c},b['yc'],select),'foe_field':metrics({'center_coverage':ql,'trained':q},b['yf'],select),'source':{p.name:digest(p) for p in (HERE/'lernen.py',HERE/'ort.py',HERE/'daten.py',HERE/'LERNPLAN.md',HERE/'karten.json',OLD)},'training_maps':len(np.unique(a['seed']))}
    model={'center':wc.tolist(),'points':wf.tolist()}
    if not partial:
        for file,obj in (('modell.json',model),('lernpruefung.json',result)):(HERE/file).write_text(json.dumps(obj,indent=2)+'\n')
        (HERE/'lernquellen.json.gz').write_bytes(gzip.compress(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    print(json.dumps({'center':result['center'].get('strict_first'),'foe_field':result['foe_field'].get('strict_first'),'model':model}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--partial',action='store_true');run(p.parse_args().partial)
