"""Recompute arrivals, actual point credits, and independent map-level uncertainty from sealed branch archives."""
import argparse
import gzip
from hashlib import sha256
import json

import numpy as np

from anfahrt import HERE,STEPS

def verify(split,n):
    file=HERE/f'{split}_{n}.jsonl.gz';items=[json.loads(r) for r in gzip.decompress(file.read_bytes()).splitlines()]
    if len(items)!=n or len({r['base']['seed'] for r in items})!=n:raise ValueError('Unexpected map inventory')
    agg=[];cases=[];point_delta=[];arrival=[];gains=[];firsts=[]
    for i,r in enumerate(items):
        ref=r['base'];other=r['force'];s=ref['selection']
        if r['id']!=i or ref['agent_errors']!=[0,0] or ref['sensor']!=1:raise ValueError('Invalid reference')
        if other is None:
            if s is not None or ref['steps_checked']!=303 or ref['after'] or ref['events']:raise ValueError('Incomplete inactive map')
            agg.append([0,0,0,0]);continue
        if s!=other['selection'] or other['agent_errors']!=[0,0] or ref['prefix']!=other['prefix'] or len(ref['prefix'])!=64:raise ValueError('Unequal decision state')
        if not 2<=len(s['route'])<=4 or s['route'][-1]!=s['target'] or not 0<=s['proof']<=s['t']:raise ValueError('Bad planned trip')
        last=s['start']
        for cell in s['route']:
            if cell not in STEPS[last,1:]:raise ValueError('Noncardinal route');
            last=cell
        if not 1<=len(other['events'])<=4 or {e[1] for e in other['events']}!={s['uid']} or ref['events']:raise ValueError('Invalid change count or identity')
        for t,uid,old,action,cell in other['events']:
            j=t-s['t'];origin=s['start'] if j==0 else s['route'][j-1]
            if not 0<=old<=4 or not 1<=action<=4 or old==action or s['route'][j]!=cell or STEPS[origin,action]!=cell:raise ValueError('Submitted move disagrees with route')
        def metrics(row):
            seq=row['after'];previous=[0,0];credits=[];arr=[]
            if len(seq)!=12 or row['steps_checked']!=s['t']+12:raise ValueError('Incorrect horizon')
            for j,d in enumerate(seq,1):
                diff=np.subtract(d['score'],previous);previous=d['score']
                if d['at']!=s['t']+j or np.any((diff<0)|(diff>16)) or (d['credit'] and diff[0]<1) or (d['arrival'] and not d['credit']):raise ValueError('Invalid credit or score packet')
                if d['credit']:credits.append(j)
                if d['arrival']:arr.append(j)
            return credits,arr,previous
        a,ra,p=metrics(ref);b,rb,q=metrics(other);delta=len(b)-len(a);dh=q[0]-p[0];earliest=min(a,default=13)-min(rb,default=13)
        c={'seed':ref['seed'],'team':ref['team'],'opponent':ref['opponent'],'step':s['t'],'uid':s['uid'],'target':s['target'],'route':s['route'],
            'base_target_gains':a,'new_target_gains':b,'new_ship_arrivals':rb,'first_new_credit_ahead':earliest,'extra_target':delta,'extra_own':dh,'extra_foe':q[1]-p[1],'changes':len(other['events'])}
        cases.append(c);agg.append([1,delta,dh,int(bool(rb))]);point_delta.append(delta);arrival.append(bool(rb));gains.append(dh);firsts.append(earliest>0)
    v=np.asarray(agg,float);draw=np.random.default_rng(36833).integers(0,len(v),size=(20000,len(v)))
    bounds=np.quantile(v[draw].mean(1),[.025,.975],axis=0)
    result={'maps':n,'cases':len(cases),'arrivals':sum(arrival),'earlier':sum(firsts),'more':sum(x>0 for x in point_delta),'fewer':sum(x<0 for x in point_delta),'extra_target':sum(point_delta),'extra_own':sum(gains),'extra_foe':sum(c['extra_foe'] for c in cases),
        'per_screened_map':{k:{'mean':float(v[:,j].mean()),'ci95':bounds[:,j].tolist()} for j,k in enumerate(('eligible','extra_target','extra_own','arrived'))},'archive_sha':sha256(file.read_bytes()).hexdigest(),'examples':cases}
    old=json.loads((HERE/f'{split}_{n}.json').read_bytes())['stats']
    if [result[x] for x in ('maps','cases','arrivals','more','earlier')]!=[old[x] for x in ('maps','opportunities','actual_arrivals','more_target_credits','first_earlier')]:raise ValueError('Independent recomputation disagrees')
    (HERE/f'gegenpruefung_{split}_{n}.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('split');cli.add_argument('n',type=int);args=cli.parse_args();report=verify(args.split,args.n);print({k:v for k,v in report.items() if k not in ('examples','per_screened_map')})
