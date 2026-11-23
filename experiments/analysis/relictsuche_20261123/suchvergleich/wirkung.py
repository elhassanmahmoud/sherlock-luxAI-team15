"""Pair complete games and distinguish earlier discoveries from flips in the game winner."""
import gzip
import json
from pathlib import Path
import numpy as np

from experiments.analysis.relictsuche_20261123.suchvergleich.abbildung import ROOT,PANELS


def analyse(path,arm):
    with gzip.open(path,"rt") as f:
        packed=list(map(json.loads,f))
    table={}
    for item in packed:
        for row in item.get("views",[item]):
            key=row["seed"],row["team"],row["id"],row["opponent"]
            assert key not in table and row["steps"]==303 and row["sensor"]==1
            assert row["caught_errors"]==[0,0] and len(row["matches"])==3
            assert row["win"]==int(sum(m["win"] for m in row["matches"])>=2)
            table[key]=row
    keys=sorted({(s,t) for s,t,_,_ in table})
    assert set(keys)=={(s,t) for s,_ in keys for t in (0,1)}
    effects=[];duels=[]
    for s,t in keys:
        b=table[s,t,"reference","solution92"];n=table[s,t,arm,"solution92"];h=table[s,t,arm,"v16"]
        if n["action_hash"]==b["action_hash"]:assert n["matches"]==b["matches"] and n["sight"]==b["sight"]
        effects.append([b["sight"]-n["sight"],b["credit"]-n["credit"],n["win"]-b["win"],
                        n["win"],b["win"],*(nm["win"]-bm["win"] for nm,bm in zip(n["matches"],b["matches"],strict=True))])
        duels.append(h["win"])
    v=np.array(effects)
    groups={}
    for name,mask in (("earlier",v[:,0]>0),("same",v[:,0]==0),("later",v[:,0]<0),("all",np.ones(len(v),bool))):
        z=v[mask];groups[name]=dict(seats=len(z),solution=int(z[:,3].sum()),original=int(z[:,4].sum()),
                won=int((z[:,2]>0).sum()),lost=int((z[:,2]<0).sum()),match_gain=z[:,5:].sum(0).tolist())
    return dict(cards=len(keys)//2,actual_games=len(packed),total_direct=sum(duels),direct_by_side=[sum(duels[t::2]) for t in (0,1)],groups=groups)


if __name__=="__main__":
    panels={name:analyse(ROOT/file,arm) for name,file,arm in PANELS if (ROOT/file).is_file()}
    (Path(__file__).parent/"wirkungen.json").write_text(json.dumps(panels,indent=2,ensure_ascii=False)+"\n")
