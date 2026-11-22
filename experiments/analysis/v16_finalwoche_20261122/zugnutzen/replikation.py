"""Independent fixed replication of the exact frozen one-turn reward predictor."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import torch

import sammeln as data
from berater import HERE,ValueNet
from lernen import read
import lernen


def new_games(split):
    if split!="replication":raise ValueError("This runner is only for the independent replication")
    for i in range(64):
        yield 160373000+i,f"player_{i%2}",("solution92","kaggle3")[i//2%2]


def run(folder,stage,offset,stride):
    first=json.loads((HERE/"offline.json").read_text())
    weight=HERE/"wertberater.npz"
    if (first["eligible"] or first["overall"]["turns"]!=58 or first["overall"]["own"]!=37 or
            first["checkpoint"]!=sha256(weight.read_bytes()).hexdigest()):
        raise ValueError("Original study or model does not match the frozen replication")
    if stage=="collect":
        data.games=new_games
        data.run(folder,"replication",offset,stride)
        return
    lernen.games=new_games
    validation=read(folder,"replication")
    if not all(row["source"]==first["manifests"][0]["source"] for row,_ in validation):
        raise ValueError("The generation method changed")
    net=ValueNet().eval()
    with np.load(weight,allow_pickle=False) as z:
        net.load_state_dict({k:torch.from_numpy(z[k]) for k in z.files})
    decisions=[]
    scores_by_map=[]
    with torch.inference_mode():
        for receipt,a in validation:
            estimates=net(torch.from_numpy(a["x"])).flatten().numpy()
            part=[]
            for step in np.unique(a["step"]):
                if step%101<91:continue
                options=np.flatnonzero(a["step"]==step)
                i=max(options,key=lambda k:(float(estimates[k]),-int(a["uid"][k])))
                if estimates[i]<.25:continue
                own,opp=map(int,a["delta"][i])
                row={k:receipt[k] for k in ("seed","side","opponent")}
                part.append(dict(**row,step=int(step),uid=int(a["uid"][i]),own=own,enemy=opp,adv=own-opp))
            decisions.extend(part)
            scores_by_map.append([len(part),sum(q["adv"] for q in part)])
    card=np.array(scores_by_map)
    rng=np.random.default_rng(231141)
    reps=card[rng.integers(64,size=(10000,64))].sum(1)
    if (reps[:,0]==0).any():raise ValueError("Insufficient cases for the fixed bootstrap")
    ci=np.percentile(reps[:,1]/reps[:,0],[2.5,97.5]).tolist()
    def stats(items):
        n=len(items); adv=sum(q["adv"] for q in items)
        return dict(n=n,maps=len({q["seed"] for q in items}),positive=sum(q["adv"]>0 for q in items),
                    negative=sum(q["adv"]<0 for q in items),neutral=sum(q["adv"]==0 for q in items),
                    own=sum(q["own"] for q in items),opponent=sum(q["enemy"] for q in items),mean=adv/max(1,n))
    all_stats=stats(decisions)
    gate=dict(support=all_stats["n"]>=60 and all_stats["maps"]>=12, gain=all_stats["mean"]>=.15,
              positive=all_stats["positive"]>all_stats["negative"],card_interval=ci[0]>0)
    output=dict(eligible=all(gate.values()),gates=gate,original=sha256((HERE/"offline.json").read_bytes()).hexdigest(),
                checkpoint=first["checkpoint"],plan=sha256((HERE/"REPLIKATION.md").read_bytes()).hexdigest(),
                overall=all_stats,ci95=ci,by_opponent={k:stats([r for r in decisions if r["opponent"]==k]) for k in ("kaggle3","solution92")},
                by_side={k:stats([r for r in decisions if r["side"]==k]) for k in ("player_0","player_1")},
                selected=decisions,manifests=[r for r,_ in validation])
    (HERE/"replikation.json").write_text(json.dumps(output,separators=(",",":"),allow_nan=False)+"\n")
    print(all_stats,ci,gate,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    p.add_argument("stage",choices=("collect","check"))
    p.add_argument("--offset",type=int,default=0)
    p.add_argument("--stride",type=int,default=1)
    a=p.parse_args()
    if not 0<=a.offset<a.stride:p.error("Invalid partition")
    run(a.folder,a.stage,a.offset,a.stride)
