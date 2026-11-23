"""Fit on 48 entire archived maps; evaluate once on the next 24 maps."""
import gzip
import json
from hashlib import sha256
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
WORK=Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/gegnerhaelfte')
NAMES=['Weglänge','Originalschritt folgt Route','Zug','Energie des Schiffs','Sichtweite','Bewegungskosten','bestätigte Ziele','sichtbare Gegner','Gegnerabstand zum Ziel','Punktedifferenz','Feldenergie am Ziel','Nebel am Ziel','Felder jenseits der Mittellinie']


def pack(rows):
    x=[];y=[];w=[];groups=[]
    for r in rows:
        for o in r['offers']:
            x.append(o['x']);y.append(o['y']);w.append(1/len(r['offers']));groups.append(r['seed'])
    return np.asarray(x,float).reshape(-1,len(NAMES)),np.asarray(y,float),np.asarray(w,float),np.asarray(groups,int)


def fit(x,y,w,cols):
    x=x[:,cols];mu=np.average(x,weights=w,axis=0);sd=np.sqrt(np.average((x-mu)**2,weights=w,axis=0));sd[sd<1e-6]=1
    z=(x-mu)/sd;offset=np.average(y,weights=w);coef=np.linalg.solve(z.T@(z*w[:,None])+np.eye(len(cols)),z.T@((y-offset)*w)) if len(cols) else np.zeros(0)
    return dict(columns=cols,mean=mu.tolist(),scale=sd.tolist(),coefficient=coef.tolist(),intercept=float(offset),lambda_ridge=1)


def predict(model,x):
    c=model['columns'];return np.clip(((x[:,c]-model['mean'])/model['scale'])@model['coefficient']+model['intercept'],0,12)


def brief(rows):
    x,y,w,g=pack(rows);natural=[r['first_away'] for r in rows if r['first_away'] is not None];eligible=[r for r in rows if r['offers']]
    return dict(cards=len(rows),sensor_maps={str(z):sum(r['sensor']==z for r in rows) for z in (2,3,4)},
                cards_with_sight=sum(r['first_view'] is not None for r in rows),cards_with_away_contact=len(natural),
                cards_contact_after_sight=sum(r['first_view'] is not None and r['first_away'] is not None and r['first_away']>=r['first_view'] for r in rows),
                median_first_away=float(np.median(natural)) if natural else None,cards_with_offer=len(eligible),rows=len(y),
                cards_with_target_value=len(np.unique(g[y>0])),positive_rows=int(sum(y>0)),score_labels=int(sum(y)),
                original_would_take_first_step=int(sum(x[:,1])) if len(x) else 0,
                cards_contact_within12_of_offer=sum(any(o['natural_first_within12'] for o in r['offers']) for r in rows),
                unverifiable_prior_contact_rows=sum(o['already_unrecognized'] for r in rows for o in r['offers']),
                whole_match_wins=sum(r['matches']['win'] for r in rows),
                eligible_original_wins=sum(r['matches']['win'] for r in eligible))


def main():
    rows=[json.loads((WORK/f'{i:02d}.json').read_bytes()) for i in range(72)]
    train,test=rows[:48],rows[48:]
    assert len(set(r['seed'] for r in rows))==72 and not set(r['seed'] for r in train).intersection(r['seed'] for r in test) and all(162860000<=r['seed']<=162860159 for r in rows)
    assert len({r['source'] for r in rows})==1
    x,y,w,g=pack(train);xv,yv,wv,gv=pack(test)
    fit_info={};metrics={};loss={};maps=np.unique(gv)
    if len(x) and len(xv):
        for name,cols in [('constant',[]),('geometry',[0,1]),('model',list(range(len(NAMES))))]:
            m=fit(x,y,w,cols);p=predict(m,xv);e=(p-yv)**2;fit_info[name]=m
            mse=np.array([e[gv==s].mean() for s in maps]);loss[name]=mse
            metrics[name]=dict(map_mse=float(mse.mean()),map_mae=float(np.average(abs(p-yv),weights=wv)),
                               mean_prediction=float(np.average(p,weights=wv)),mean_observed=float(np.average(yv,weights=wv)))
        baseline=min(('constant','geometry'),key=lambda n:metrics[n]['map_mse']);diff=loss[baseline]-loss['model']
        boot=np.random.default_rng(231123).integers(0,len(maps),(20000,len(maps)))
        ci=np.quantile(diff[boot].mean(1),[.025,.975]).tolist()
    else:baseline=None;ci=None
    tr=brief(train);te=brief(test)
    gate=tr['cards_with_target_value']>=4 and te['cards_with_target_value']>=4 and baseline is not None and ci[0]>0 and metrics['model']['map_mse']<min(metrics['constant']['map_mse'],metrics['geometry']['map_mse'])
    obj=dict(train=tr,test=te,models=fit_info,names=NAMES,holdout=metrics,best_reference=baseline,positive_mse_gain_ci95=ci,qualified_causal_trial=bool(gate),
             train_seeds=[r['seed'] for r in train],test_seeds=[r['seed'] for r in test],source=rows[0]['source'])
    (HERE/'modell.json').write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
    blob=''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows).encode();(HERE/'entscheide.jsonl.gz').write_bytes(gzip.compress(blob,mtime=0))
    print(json.dumps({k:obj[k] for k in ('train','test','holdout','positive_mse_gain_ci95','qualified_causal_trial')},indent=2))


if __name__=='__main__':main()
