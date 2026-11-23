"""Supplementary map-level uncertainty and label concentration on the frozen, previously measured splits."""
import json
from pathlib import Path

import numpy as np

from lernen import extract_split,field_features,prob
from ort import HERE

def evaluate():
    model=json.loads((HERE/'modell.json').read_bytes());wc=np.asarray(model['center']);wf=np.asarray(model['points']);out={}
    for split in ('train','valid'):
        d,_,_=extract_split(split,False)
        c=prob(d['center'],wc,d['allowed']);w0=np.zeros_like(wc);w0[0]=1
        old=prob(d['center'],w0,d['allowed']);f,support=field_features(d,c);wq=np.zeros_like(wf);wq[-1]=1
        q=prob(f,wf,support);baseline=prob(f,wq,support)
        groups={}
        for name,mask,a,b,y in [('center',np.ones(len(c),bool),old,c,d['yc']),('strict_center',d['anchor']>0,old,c,d['yc']),('enemy_fields',d['fields']>0,baseline,q,d['yf'])]:
            seed=d['seed'][mask];ids=np.unique(seed)
            improvement=(np.log(b[mask].clip(1.e-12,1))-np.log(a[mask].clip(1.e-12,1)))*y[mask]
            values=[float(improvement[seed==i].sum(1).mean()) for i in ids]
            counts=[int(np.sum(seed==i)) for i in ids]
            bs=np.random.default_rng(32715).choice(values,size=(20000,len(values))).mean(1) if len(ids)>=4 else None
            groups[name]={'frames':int(mask.sum()),'maps':len(ids),'max_frames_per_map':max(counts,default=0),'maps_with_better_mean_logloss':sum(v>0 for v in values),
                'mean_logloss_reduction_per_map':float(np.mean(values)) if values else None,'ci95_map_bootstrap':np.quantile(bs,[.025,.975]).tolist() if bs is not None else None}
        out[split]=groups
    (HERE/'lernaudit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

if __name__=='__main__':evaluate()
