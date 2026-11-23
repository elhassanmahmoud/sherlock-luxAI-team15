"""Verify the public score likelihood by enumeration, original geometry labels and the actual one-step mechanism."""
import argparse
import gzip
from itertools import product
import json
from pathlib import Path

import numpy as np
from rueckmeldung import HERE,conditional

STORE=Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/spaetort')

def exact():
    rng=np.random.default_rng(199197);cases=0
    for n in range(1,9):
        vals=np.array(list(product((0,1),repeat=n)));prior=.2**vals.sum(1)*.8**(n-vals.sum(1))
        for rep in range(35):
            a=rng.integers(0,3,n);b=rng.integers(0,3,n);state=rng.integers(0,2,n);g,h=int(state@a),int(state@b)
            w=prior*((vals@a==g)&(vals@b==h));true=w@vals/w.sum();pred,ok=conditional({i:int(k) for i,k in enumerate(a) if k},{i:int(k) for i,k in enumerate(b) if k},g,h,range(n))
            if not ok or not np.allclose(list(pred.values()),true,atol=1.e-10):raise ValueError('Exact score likelihood does not match full binary enumeration')
            cases+=n
    return cases

def predict(head,x):
    w=np.asarray(head['weights']);raw=[float(w[0,k])+sum(float(ww)*(float(v)-m)/s for v,m,s,ww in zip(x,head['mean'],head['scale'],w[1:,k],strict=False)) for k in (0,1,2)]
    p=np.exp(np.subtract(raw,max(raw)));return p/p.sum()

def natural():
    model=json.loads((HERE/'modell.json').read_bytes())['heads'];measure=json.loads((HERE/'natur.json').read_bytes());result={}
    for which in ('train','valid'):
        r=[json.loads(l) for l in gzip.decompress((HERE/f'natur_{which}.jsonl.gz').read_bytes()).splitlines()];by={};plus=minus=selected0=0;loss={h:{} for h in model}
        for row in r:by.setdefault(row['seed'],[]).append(row)
        for seed,rows in by.items():
            team=rows[0]['team'];v=np.load(STORE/which/f'{seed}-{team}.richter.npz');active=v['active'];weights=v['weights'];live=v['real_live'];pos=v['real_position'];v.close()
            for q in rows:
                at=q['t']+1;ids=np.flatnonzero(live[at,team]);u=q['uid'];others={tuple(map(int,pos[at,team,j])) for j in ids if j!=u};target=tuple(divmod(q['target'],24));dest=tuple(divmod(q['alternative'],24));highest=int(sum(active[at]));safe=lambda k:0<int(weights[k])<=highest
                label=int(safe(target) and target not in others)-int(safe(dest) and dest not in others)
                if label!=q['delta'] or safe(target)!=q['point'] or tuple(pos[at,team,u])!=dest:raise ValueError('Independent private natural label mismatch')
                for h,head in model.items():
                    p=predict(head,q['x']);loss[h].setdefault(seed,[]).append(float(-np.log(p[label+1])))
                    if h=='feedback' and p[2]>.4 and p[2]-p[0]>.15:
                        selected0+=1;plus+=label>0;minus+=label<0
        computed={h:float(np.mean([np.mean(g) for g in d.values()])) for h,d in loss.items()}
        for h,k in computed.items():
            if not np.isclose(k,measure['stats'][which][h]['logloss_by_map']):raise ValueError('Different map log loss')
        expected=measure['stats'][which]['feedback'];assert [selected0,plus,minus]==[expected[k] for k in ('selected','selected_plus','selected_minus')]
        result[which]={'labels':len(r),'maps':len(by),'loss':computed,'selected':selected0,'positive':plus,'negative':minus}
    out={'belief_cases':exact(),'natural':result};(HERE/'gegenpruefung_natur.json').write_text(json.dumps(out,indent=2)+'\n');print(out)

def mechanism():
    archive=HERE/'mechanik_partien.jsonl.gz';rr=[json.loads(l) for l in gzip.decompress(archive.read_bytes()).splitlines()];m=json.loads((HERE/'modell.json').read_bytes())['heads']['feedback'];current=json.loads((HERE/'mechanik.json').read_bytes());seen=set();s=[];false_checks=0;observed=0
    archived=[json.loads(l) for l in gzip.decompress((HERE.parent/'feldbindung/fenster.jsonl.gz').read_bytes()).splitlines()];idx={(r['seed'],r['side'],r['opponent']):r for r in archived}
    for row in rr:
        key=tuple(row['key']);a=row['original'];b=row['hold'];e=a['event'];f=a['follow'];initial=a['window'][0]['uid_present'] and a['window'][0]['active'];assert key in idx and key not in seen and idx[key]['initial']==initial;seen.add(key);observed+=int(initial)
        if f and f['eligible']:
            p=predict(m,f['x']);selected=bool(p[2]>.4 and p[2]-p[0]>.15);assert selected==f['selected']==(b is not None) and np.allclose(p,f['probability']);false_checks+=int(not initial)
        assert a['steps']==303 and not a['events']
        if b is None:continue
        assert a['event']==b['event'] and a['hold_prefix']==b['hold_prefix'] and b['events']==[[e['t']+1,e['u'],f['original'],0]] and b['window'][0]==a['window'][0]
        diff=(np.asarray([w['score'] for w in b['window'][1:]])-np.asarray([w['score'] for w in a['window'][1:]]))
        tax=sum(w['target_credit'] for w in b['window'][1:])-sum(w['target_credit'] for w in a['window'][1:]);s.append((key,int(diff[0,0]),int(diff[:,0].sum()),int(tax)))
    assert seen==set(idx) and len(rr)==56;add=sum(r[1] for r in s);four=sum(r[2] for r in s);plus=sum(r[1]>0 for r in s);neg=sum(r[1]<0 for r in s)
    flags={'eligible_and_maps':len(s)>=8 and len({k[0] for k,*_ in s})>=5,'each_opponent_plus':all(any(x[0][2]==o and x[1]>0 for x in s) for o in ('solution92','v16')),'four_plus':plus>=4,'at_most_one_minus':neg<=1,'positive_sum':add>0,'nonnegative_four':four>=0,'protected':True,'natural_pass':json.loads((HERE/'natur.json').read_bytes())['passed']}
    assert flags==current['gates'] and all(flags.values())==current['passed'];out={'paired_probe_cases':len(seen),'real_initial_points':observed,'admitted_non_scoring_initial_entries':false_checks,'selected':len(s),'immediate':add,'four':four,'gates':flags,'passed':all(flags.values())};(HERE/'gegenpruefung_mechanik.json').write_text(json.dumps(out,indent=2)+'\n');print(out)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('task',choices=('natur','mechanik'));a=p.parse_args();natural() if a.task=='natur' else mechanism()
