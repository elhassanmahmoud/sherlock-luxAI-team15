"""Train a three-class next-score comparison on independent natural moves from original V16 traces."""
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

from rueckmeldung import D,NEIGH,STATIC,FEEDBACK,HERE,History,eligible,frame_now

ORIG=HERE.parent/'spaetgebiet/ortsmodell';STORE=Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/spaetort')

def source(p):return sha256(p.read_bytes()).hexdigest()

def observation(p,t):return {**{k:p[k][t] for k in ('team_points','units_mask','relic_nodes_mask','relic_nodes')},'units':{k:p[k][t] for k in ('position','energy')}}

def collect(which,manifest):
    rows=[];cnt=0;rejected_motion=0
    for meta in manifest:
        if meta['split']!=which:continue
        cnt+=1;team=meta['team'];pf=STORE/which/meta['public'];rf=STORE/which/meta['private']
        if source(pf)!=meta['public_sha'] or source(rf)!=meta['private_sha']:raise ValueError('Natural trajectory changed')
        with np.load(pf) as q:p={k:q[k] for k in q.files}
        with np.load(rf) as q:v={k:q[k] for k in ('real_live','real_position','active','weights')}
        h=History(team);seen=set()
        for t in range(303):
            o=observation(p,t);known=p['known_points'][t];h.update(t,o,known);ms=t%101
            if ms<9 or ms>85 or (ms-1)%4 or not h.centres:continue
            f=frame_now(o,team,known,p['terrain'][t],p['commands'][t],p['move_mask'][t],meta['cfg']);old=h.old
            true=(v['weights']>0)&(v['weights']<=sum(v['active'][t+1]));late=v['real_position'][t+1,team];live=v['real_live'][t+1,team];nextpos=24*late[:,0]+late[:,1];positions=h.now['pos']
            for uid in old['ids']:
                target=int(24*positions[uid,0]+positions[uid,1]);prior=int(24*old['pos'][uid,0]+old['pos'][uid,1]);oldcmd=int(p['commands'][t-1,uid,0]);spec=(t//101,int(uid),target)
                if target<0 or prior<0 or not 1<=oldcmd<=4 or old['en'][uid]<max(30,4*meta['cfg']['unit_move_cost']) or p['protected'][t-1,uid] or NEIGH[prior,oldcmd]!=target:continue
                if target in old['own'] or p['known_points'][t-1].ravel()[target] or not h.zone[target] or spec in seen:continue
                available=eligible(f,int(uid),target)
                if available is None:continue
                alt,covered=available
                if not live[uid] or nextpos[uid]!=alt:rejected_motion+=1;continue
                seen.add(spec);other=nextpos[live&(np.arange(16)!=uid)]
                y=int(true.ravel()[target] and target not in other)-int(true.ravel()[alt] and alt not in other)
                x=h.features(target,alt,int(f['en'][uid]),f['terrain'],covered)
                rows.append({'seed':meta['seed'],'team':team,'opponent':meta['opponent'],'t':t,'uid':int(uid),'target':target,'alternative':alt,'x':x.tolist(),'delta':y,'point':bool(true.ravel()[target])})
    return rows,{'maps':cnt,'examples':len(rows),'with_examples':len({r['seed'] for r in rows}),'excluded_unexecuted_or_death':rejected_motion}

def fit(rows,n):
    x=np.asarray([r['x'][:n] for r in rows],float);labels=np.asarray([r['delta']+1 for r in rows]);ids=np.array([r['seed'] for r in rows]);_,index,counts=np.unique(ids,return_inverse=True,return_counts=True);weights=1/counts[index];weights/=weights.sum()
    center=np.average(x,axis=0,weights=weights);scale=np.maximum(.08,np.sqrt(np.average((x-center)**2,axis=0,weights=weights)));z=np.column_stack((np.ones(len(x)),(x-center)/scale));one=np.eye(3)[labels]
    def objective(b):
        w=b.reshape(-1,3);logits=z@w;lse=logsumexp(logits,axis=1);p=np.exp(logits-lse[:,None]);loss=((lse-(one*logits).sum(1))*weights).sum()+.01*(w[1:]**2).sum();grad=z.T@((p-one)*weights[:,None]);grad[1:]+=.02*w[1:];return loss,grad.ravel()
    res=minimize(objective,np.zeros(z.shape[1]*3),jac=True,method='L-BFGS-B',options={'ftol':1.e-11,'maxiter':150});
    if not res.success:raise ValueError(res.message)
    return {'mean':center.tolist(),'scale':scale.tolist(),'weights':res.x.reshape(-1,3).tolist(),'features':list((STATIC+FEEDBACK)[:n])}

def probabilities(m,x):
    mean=np.asarray(m['mean']);z=(np.asarray(x)[...,:len(mean)]-mean)/m['scale'];w=np.asarray(m['weights']);v=z@w[1:]+w[0];v=np.exp(v-v.max(axis=-1,keepdims=True));return v/v.sum(axis=-1,keepdims=True)

def selected(p):return (p[...,2]>.4)&((p[...,2]-p[...,0])>.15)

def describe(rows,models):
    x=np.asarray([r['x'] for r in rows]);y=np.array([r['delta'] for r in rows]);seeds=np.array([r['seed'] for r in rows]);out={}
    for name,model in models.items():
        prob=probabilities(model,x);allow=selected(prob);nll=-np.log(np.maximum(1.e-12,prob[np.arange(len(y)),y+1]));maps=np.unique(seeds);per=[float(nll[seeds==s].mean()) for s in maps]
        out[name]={'logloss_by_map':float(np.mean(per)),'logloss':float(nll.mean()),'maps':len(maps),'n':len(y),'selected':int(allow.sum()),'selected_plus':int((allow&(y>0)).sum()),'selected_minus':int((allow&(y<0)).sum()),'selected_true':int(sum(bool(r['point']) for i,r in enumerate(rows) if allow[i])),'delta_selected':int(y[allow].sum()),'per_map_loss':per,'map_ids':maps.tolist()}
    return out

def run():
    mfile=ORIG/'lernquellen.json.gz';original=json.loads(gzip.decompress(mfile.read_bytes()));groups={};counts={};stats={}
    for k in ('train','valid'):
        groups[k],counts[k]=collect(k,original);print(k,counts[k],flush=True)
        data=b''.join((json.dumps(r,sort_keys=True,separators=(',',':'))+'\n').encode() for r in groups[k]);(HERE/f'natur_{k}.jsonl.gz').write_bytes(gzip.compress(data,mtime=0))
    if counts['train']['examples']<40 or counts['valid']['examples']<15:raise ValueError('Too few eligible natural arrivals')
    if set(r['seed'] for r in groups['train'])&set(r['seed'] for r in groups['valid']):raise ValueError('Natural splits overlap')
    models={'prior':fit(groups['train'],len(STATIC)),'feedback':fit(groups['train'],len(STATIC)+len(FEEDBACK))}
    for k in ('train','valid'):stats[k]=describe(groups[k],models)
    rv=stats['valid'];gate={'better_map_logloss':rv['feedback']['logloss_by_map']<rv['prior']['logloss_by_map'],'positive_natural_gain':rv['feedback']['selected_plus']>rv['feedback']['selected_minus']}
    diff=np.asarray(rv['prior']['per_map_loss'])-rv['feedback']['per_map_loss'];draw=np.random.default_rng(163500).integers(0,len(diff),size=(20000,len(diff)));interval=np.quantile(diff[draw].mean(1),[.025,.975]).tolist()
    ident={p.name:source(p) for p in (mfile,HERE/'lernen.py',HERE/'rueckmeldung.py',HERE/'PLAN.md',HERE/'natur_train.jsonl.gz',HERE/'natur_valid.jsonl.gz')}
    (HERE/'modell.json').write_text(json.dumps({'heads':models,'source':ident},indent=2)+'\n');result={'counts':counts,'stats':stats,'gates':gate,'passed':all(gate.values()),'loss_improvement_ci95':interval,'source':ident,'model_sha':source(HERE/'modell.json')};(HERE/'natur.json').write_text(json.dumps(result,indent=2)+'\n');print(gate,{k:{z:v0 for z,v0 in v.items() if z not in ('per_map_loss','map_ids')} for k,v in rv.items()},flush=True)

if __name__=='__main__':run()
