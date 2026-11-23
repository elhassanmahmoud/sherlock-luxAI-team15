"""Counterfactual route geometry on frozen original validation trajectories, separately from whole-game effects."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from kandidat import DLEFT,DRIGHT,MIRROR,route
from lernen import STORE,observation
from ort import HERE, ORB, PublicHistory


def reflected(o):
    def xy(a):
        return np.where((a>=0).all(-1,keepdims=True),23-a[...,::-1],-1)
    return {'sensor_mask':o['sensor_mask'][::-1,::-1].T,'units_mask':o['units_mask'][::-1],
       'team_points':o['team_points'][::-1], 'relic_nodes':xy(o['relic_nodes']), 'relic_nodes_mask':o['relic_nodes_mask'],
       'units':{'position':xy(o['units']['position'][::-1]),'energy':o['units']['energy'][::-1]}}

def reflected_frame(f):
    out={**f}
    for k in ('terrain','points'):out[k]=f[k].reshape(24,24)[::-1,::-1].T.ravel()
    out['mask']=f['mask'][:,MIRROR];out['cmd']=np.array([0,2,1,4,3,5])[f['cmd']]
    out['xy']=np.where((f['xy']>=0).all(-1,keepdims=True),23-f['xy'][:,::-1],-1)
    return out

def assess():
    records=[];true_unknown=0;parity_frames=0;parity_routes=0
    for receipt in sorted((STORE/'valid').glob('*.json')):
        meta=json.loads(receipt.read_bytes());team=meta['team'];h=PublicHistory(team);m=PublicHistory(1-team)
        with np.load(receipt.parent/meta['public']) as p:d={k:p[k] for k in p.files}
        with np.load(receipt.parent/meta['private']) as p:lab={k:p[k] for k in ('centres','active','weights','scoring')}
        anchor=None;entry=None
        for t in range(303):
            o=observation(d,t);h.update(t,o);m.update(t,reflected(o))
            if h.alarm!=m.alarm or h.known!=m.known:raise ValueError('Reflected public trigger differs')
            parity_frames+=1
            if anchor is None:
                if not h.alarm:continue
                anchor=t;known=dict(h.known);wrong=[i for i,v in enumerate(lab['active'][t]) if v and i not in known]
                if not wrong:raise ValueError('No actual missing pair')
                true_unknown+=1;entry=dict(seed=meta['seed'],team=team,op=meta['opponent'],t=t,alert=h.gain.tolist(),cap=list(h.limits),options=False)
            if t-anchor>=6 or t//101!=anchor//101 or h.known!=known:break
            f=dict(terrain=d['terrain'][t].ravel(),points=d['known_points'][t].ravel().astype(bool),protect=d['protected'][t],mask=d['move_mask'][t],energy=d['energy'][t,team].reshape(-1),live=d['units_mask'][t,team],xy=d['position'][t,team],cmd=d['commands'][t,:,0])
            option=route(f,h,meta['cfg']['unit_move_cost'])
            symmetric=route(reflected_frame(f),m,meta['cfg']['unit_move_cost'])
            if (option is None)!=(symmetric is None):raise ValueError('One starting side abstains differently')
            if option is None:continue
            planned=np.asarray(option[2]);equiv=(23-planned%24)*24+23-planned//24
            if option[1]!=symmetric[1] or not np.array_equal(equiv,symmetric[2]):raise ValueError('Reflected scout or route differs')
            parity_routes+=1
            _,uid,path,measure=option;cent=lab['centres'][wrong];cent=ORB[24*cent[:,0]+cent[:,1]]
            pt=d['position'][t+1:t+len(path)+1,team,uid];live=d['units_mask'][t+1:t+len(path)+1,team,uid];orig=(pt[:,0]*24+pt[:,1])[live]
            judge=np.unpackbits(lab['scoring'],axis=-1,bitorder='little').astype(bool)
            outside=(~h.zone)&np.isin(lab['weights'].ravel(),np.array(wrong)+1)
            external=judge[t:min(t+len(path)+5,(t//101+1)*101),1-team].any(0)&outside
            target=np.zeros(300,bool);target[ORB[external]]=True
            def metrics(a):
                if not len(a):return dict(sight=False,exact=False,field=False,min_distance=99)
                distance=np.minimum(DLEFT[a,:][:,cent],DRIGHT[a,:][:,cent]);return dict(sight=bool((distance<=1).any()),exact=bool((distance==0).any()),field=bool(target[ORB[a]].any()),min_distance=int(distance.min()))
            entry.update(options=True,uid=uid,start=t,steps=len(path),forecast=measure,foe_field_present=bool(external.any()),planned=metrics(path),original=metrics(orig))
            break
        if entry:records.append(entry)
    def summarize(rows):
        with_route=[r for r in rows if r['options']]
        return dict(alarms=len(rows),routes=len(with_route),planned={key:sum(r['planned'][key] for r in with_route) for key in ('sight','exact','field')},
            baseline={key:sum(r['original'][key] for r in with_route) for key in ('sight','exact','field')},opp_scores= sum(r['foe_field_present'] for r in with_route))
    out={'equivariant_frames':parity_frames,'equivariant_routes':parity_routes,'tested':len(list((STORE/'valid').glob('*.json'))),'all':summarize(records),'per_side':[summarize([r for r in records if r['team']==i]) for i in (0,1)],'records':records,
        'sha':{s:sha256((HERE/s).read_bytes()).hexdigest() for s in ('mechanik.py','kandidat.py','ort.py','modell.json','lernquellen.json.gz')}}
    (HERE/'mechanik.json').write_text(json.dumps(out,indent=2)+'\n');print(out['all'])

if __name__=='__main__':assess()
