"""Read frozen public V16 tapes, generate legal options, then attach referee labels."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from signalmodell import Evidence,HERE,NAMES,options

PUBLIC=("units_mask","sensor_mask","team_points","relic_nodes_mask","relic_nodes","position","energy","terrain","known_points","commands","move_mask","protected")


def read_one(source,receipt):
    team=receipt["team"]
    def load(key,fields):
        p=source/receipt[key]
        assert sha256(p.read_bytes()).hexdigest()==receipt[("public" if key=="public" else "private")+"_sha"]
        with np.load(p,allow_pickle=False) as f:
            return {n:f[n] for n in fields}
    pub=load("public",PUBLIC)
    referee=load("private",("weights","active","scoring"))
    assert pub["commands"].shape==(303,16,3)
    h=Evidence()
    moments=[]
    prev=0
    for t in range(303):
        match,turn=divmod(t,101)
        known=pub["known_points"][t]
        p=pub["position"][t,team]
        ene=pub["energy"][t,team].reshape(-1)
        alive=pub["units_mask"][t,team]&(ene>=0)
        score=int(pub["team_points"][t,team])
        h.relics(pub["relic_nodes"][t][pub["relic_nodes_mask"][t]])
        h.observe(turn,p[alive],score-prev if turn else 0,known)
        prev=score
        moves=options(h,turn,match+1,team,p,ene,alive,known,pub["terrain"][t],pub["commands"][t],
                      pub["move_mask"][t],pub["protected"][t],receipt["cfg"]["unit_move_cost"])
        if not moves:
            continue
        # The playing policy receives none of the three referee arrays.
        weights=referee["weights"]
        active=(weights>0)&(weights<=int(referee["active"][t].sum()))
        assert np.array_equal(active,active[::-1,::-1].T)
        seen=np.unpackbits(referee["scoring"][t,team],bitorder="little").reshape(24,24)
        assert not np.any(seen&~active)
        out=[]
        for uid,d,xy,base,attr,base_attr in moves:
            out.append(dict(key=[uid,d,*xy,*base],features=[attr,base_attr],truth=[active[xy],active[base]]))
        moments.append((t,out))
    return moments


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("raw",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("split",choices=("train","valid"))
    p.add_argument("lane",type=int,default=0,nargs="?")
    p.add_argument("stride",type=int,default=1,nargs="?")
    a=p.parse_args()
    if a.split=="valid" and not (HERE/"modell.json").is_file():
        raise ValueError("Field labels stay held out until the fit is frozen")
    source=a.raw/a.split
    files=sorted(source.glob("*.json"))
    assert len(files)==dict(train=160,valid=48)[a.split]
    dest=a.out/a.split
    dest.mkdir(parents=True,exist_ok=True)
    for path in files[a.lane::a.stride]:
        meta=json.loads(path.read_text())
        target=dest/(path.stem+".npz")
        if target.exists():
            continue
        groups=read_one(source,meta)
        step=[];keys=[];feat=[];truth=[]
        for t,rows in groups:
            for r in rows:
                step.append(t);keys.append(r["key"]);feat.append(r["features"]);truth.append(r["truth"])
        context=dict(seed=meta["seed"],team=meta["team"],opponent=meta["opponent"],source_public=meta["public_sha"],
                     source_private=meta["private_sha"],names=NAMES)
        temp=dest/(path.stem+".part.npz")
        np.savez_compressed(temp,step=np.array(step,np.int16),key=np.array(keys,np.int16).reshape(-1,6),
            x=np.array(feat,np.float32).reshape(-1,2,len(NAMES)),truth=np.array(truth,np.bool_).reshape(-1,2),
            meta=np.array(json.dumps(context)))
        temp.replace(target)
        print(meta["seed"],len(step),flush=True)


if __name__=="__main__":
    main()
