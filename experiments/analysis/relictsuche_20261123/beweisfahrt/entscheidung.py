"""Learning from matched real branches and evaluation on the prospectively reserved mechanism panel."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from anfahrt import HERE,NAMES,allow
from gegenfahrten import common,check,stats

def load(split,n):
    f=HERE/f'{split}_{n}.jsonl.gz';rows=[json.loads(line) for line in gzip.decompress(f.read_bytes()).splitlines()];check(len(rows)==n and [r['id'] for r in rows]==list(range(n)),'Incomplete previous sample');return rows

def values(row):
    a,b=row['base']['after'],row['force']['after']
    gain=b[-1]['score'][0]-a[-1]['score'][0];enemy=b[-1]['score'][1]-a[-1]['score'][1]
    target=sum(x['credit'] for x in b)-sum(x['credit'] for x in a)
    earliest=lambda arr,ship:min((i+1 for i,x in enumerate(arr) if x['credit'] and (not ship or x['arrival'])),default=13)
    return dict(seed=row['base']['seed'],team=row['base']['team'],opponent=row['base']['opponent'],t=row['base']['selection']['t'],
        x=row['base']['selection']['x'],gain=gain,enemy=enemy,target=target,earlier=earliest(a,False)-earliest(b,True),arrived=any(x['arrival'] for x in b),net=.65*np.clip(gain,-12,12)+.35*np.clip(target,-12,12))

def summary(v):
    return dict(cases=len(v),maps=len({x['seed'] for x in v}),arrived=sum(x['arrived'] for x in v),earlier=sum(x['earlier']>0 for x in v),
        better=sum(x['target']>0 for x in v),worse=sum(x['target']<0 for x in v),added_credits=sum(x['target'] for x in v),own_gain=sum(x['gain'] for x in v),enemy_gain=sum(x['enemy'] for x in v))

def fit(rows):
    v=[values(r) for r in rows if r['force']];s=summary(v)
    source={'procedure':common.sha(HERE/'LERNREGEL.md'),'fitting':common.sha(Path(__file__)),'archive':common.sha(HERE/f'train_{len(rows)}.jsonl.gz'),'collection':rows[0]['source']}
    if s['maps']<16 or s['better']<4:
        common.write_once(HERE/'lernbilanz.json',{'eligible_to_fit':False,'training':s,'source':source});print(s);return
    x=np.asarray([a['x'] for a in v]);y=np.asarray([a['net'] for a in v]);mean=x.mean(0);scale=np.maximum(x.std(0),.1)
    z=(x-mean)/scale;matrix=np.column_stack([np.ones(len(v)),z]);penalty=np.diag([0]+[12]*len(NAMES))
    coeff=np.linalg.solve(matrix.T@matrix+penalty,matrix.T@y)
    model=dict(features=NAMES,mean=mean.tolist(),scale=scale.tolist(),coef=coeff.tolist(),threshold=.5,regularizer=12,source=source)
    common.write_once(HERE/'modell.json',model);selected=[a for a in v if allow(model,a['x'])]
    common.write_once(HERE/'lernbilanz.json',{'eligible_to_fit':True,'training':s,'fit_selection':summary(selected),'source':source});print(s,summary(selected))

def mechanism(rows):
    model=json.loads((HERE/'modell.json').read_bytes());v=[values(r) for r in rows if r['force']];selected=[a for a in v if allow(model,a['x'])];s=summary(selected)
    gates=dict(five_maps=s['maps']>=5,three_early=s['earlier']>=3,more_better=s['better']>s['worse'],own_points=s['own_gain']>=0)
    rep=dict(maps=len(rows),all=summary(v),selected=s,selected_per_team=[summary([a for a in selected if a['team']==i]) for i in (0,1)],
          selected_per_opponent={op:summary([a for a in selected if a['opponent']==op]) for op in ('solution92','v16')},
          gates=gates,passed=all(gates.values()),cases=[{k:value for k,value in a.items() if k not in ('net','x')}|{'chosen':allow(model,a['x'])} for a in v],
          model_sha=common.sha(HERE/'modell.json'),source=rows[0]['source'])
    common.write_once(HERE/'mechanik.json',rep);print(json.dumps(rep,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('fit','mechanik'));p.add_argument('count',type=int);a=p.parse_args()
    data=load('train' if a.mode=='fit' else 'mechanik',a.count);fit(data) if a.mode=='fit' else mechanism(data)
