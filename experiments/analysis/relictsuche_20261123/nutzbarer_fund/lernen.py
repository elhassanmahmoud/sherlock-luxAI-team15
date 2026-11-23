"""Fit on actual near-term field receipts and validate on different original boards."""
import argparse
import json
from pathlib import Path
import numpy as np
from experiments.analysis.relictsuche_20261123.nutzbarer_fund.ertrag import HERE,COORD,ZONE,features,forecast
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,write_once

LOOKUP={tuple(x):i for i,x in enumerate(COORD)}


def read(path):
    meta=json.loads(path.read_text());team=meta["team"]
    vals=[]
    for k in ("public","private"):
        f=path.parent/meta[k];assert sha(f)==meta[k+"_sha"]
        vals.append(np.load(f,allow_pickle=False))
    public,ref=vals
    with public,ref:
        masks=public["relic_nodes_mask"].any(axis=1);points=public["team_points"][:,team]
        center=ref["centres"][0];center=min(tuple(center),tuple(23-center[::-1]));idx=LOOKUP[center]
        # The sum of private occupied scoring tiles equals the public score increment.
        occupied=np.unpackbits(ref["scoring"][:,team],axis=-1,bitorder="little").astype(bool)
        assert np.array_equal(occupied[1:101].sum(1),np.diff(points[:101]))
        y=occupied[:,ZONE[idx]].sum(1)
        # Symmetry makes the pair itself invariant under mapping the player's perspective.
        pos=public["position"][:,team];alive=public["units_mask"][:,team]&(public["energy"][:,team]>=0);walls=public["terrain"]==2
        rows=[]
        for t in range(12,61,8):
            if np.any(masks[:t+1]) or points[t] or not np.any(alive[t]):continue
            ships=pos[t,alive[t]]
            terrain=walls[t]
            if team:ships=23-ships[:,::-1];terrain=terrain[::-1,::-1].T
            x=features(ships,terrain,[idx])[0]
            rows.append(dict(seed=meta["seed"],team=team,t=t,x=x.tolist(),target=float(y[t+1:t+25].mean())))
    return rows


def load(folder,n):
    files=sorted(folder.glob("*.json"));assert len(files)==n
    rows=[]
    for f in files:
        group=read(f)
        for r in group:r["w"]=1/len(group)
        rows+=group
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("folder",type=Path);p.add_argument("stage",choices=("train","valid"))
    a=p.parse_args();rows=load(a.folder/a.stage,160 if a.stage=="train" else 48)
    x=np.array([r["x"] for r in rows]);y=np.array([r["target"] for r in rows]);w=np.array([r["w"] for r in rows])
    if a.stage=="train":
        mu=np.average(x,axis=0,weights=w);sd=np.maximum(.001,np.sqrt(np.average((x-mu)**2,axis=0,weights=w)))
        z=(x-mu)/sd;ly=np.log1p(y);bias=np.average(ly,weights=w)
        coef=np.linalg.solve((z.T*w)@z+24*np.eye(z.shape[1]),(z.T*w)@(ly-bias))
        m=dict(center=mu.tolist(),scale=sd.tolist(),bias=float(bias),weights=coef.tolist(),mean_points=float(np.average(y,weights=w)),
               cards=len({r["seed"] for r in rows}),situations=len(rows))
        write_once(HERE/"modell.json",m)
        return
    m=json.loads((HERE/"modell.json").read_bytes());pred=forecast(x,m)
    mid=np.median(pred);high=pred>mid
    actual=[float(np.average(y[k],weights=w[k])) for k in (~high,high)]
    errors=[float(np.average((v-y)**2,weights=w)) for v in (m["mean_points"],pred)]
    gates=dict(error=errors[1]<errors[0],separation=actual[1]-actual[0]>=.2)
    write_once(HERE/"valid.json",dict(total_cards=48,eligible_cards=len({r["seed"] for r in rows}),situations=len(rows),
               mean_points=actual,mse=errors,gates=gates,passed=all(gates.values()),model=sha(HERE/"modell.json"),rows=rows))


if __name__=="__main__":main()
