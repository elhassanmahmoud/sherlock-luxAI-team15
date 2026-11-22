"""Train identically initialized temporal and current-only residuals. Score once on genuinely new cards."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import torch

from historie import HERE, NAMES, Residual


def dataset(folder,seeds):
    groups={k:[] for k in ("x","scores","disagree","y","mask","seed")}
    sources=[]
    for seed in seeds:
        path=folder/f"{seed}.npz"
        with np.load(path,allow_pickle=False) as z:
            n=len(z["y"])
            if not n or not z["mask"][np.arange(n),z["y"]].all():
                raise ValueError("Invalid label rows")
            for k in groups:
                groups[k].append(np.full(n,seed,dtype=np.int32) if k=="seed" else z[k])
            sources.append(dict(seed=seed, source_sha=str(z["source"]), projected=sha256(path.read_bytes()).hexdigest(), rows=n))
    return {k:torch.from_numpy(np.concatenate(vals)) for k,vals in groups.items()},sources


def train(folder,cache,device):
    torch.set_num_threads(1)
    old, old_sources=dataset(folder,range(7172000,7172120))
    new, new_sources=dataset(folder,[*range(19376200,19376208),*range(160345000,160345032)])
    rng=np.random.default_rng(231140)
    torch.manual_seed(231140)
    one=Residual().to(device)
    two=Residual().to(device)
    two.load_state_dict(one.state_dict())
    opts=[torch.optim.Adam(n.parameters(),lr=.0015) for n in (one,two)]
    for iteration in range(1000):
        indices=[rng.integers(len(src["y"]),size=256) for src in (old,new)]
        def assemble(k):
            return torch.cat([src[k][i] for src,i in zip((old,new),indices,strict=True)]).to(device)
        x=assemble("x").float()
        scores=assemble("scores")
        mask=assemble("mask")
        y=assemble("y").long()
        for n, current, opt in ((one,True,opts[0]),(two,False,opts[1])):
            residual=n(x,current_only=current)
            logits=(scores+residual).masked_fill(~mask,-torch.inf)
            loss=torch.nn.functional.cross_entropy(logits,y)+.01*residual.square().mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
    for name,net in (("aktuell",one),("zeitlich",two)):
        path=cache/f"{name}.npz"
        np.savez_compressed(path,**{k:v.detach().cpu().numpy() for k,v in net.state_dict().items()})
    report={"plan":sha256((HERE/"PLAN.md").read_bytes()).hexdigest(),"source":sha256((HERE/"historie.py").read_bytes()).hexdigest(),
            "train_rows":len(old["y"])+len(new["y"]),"inputs":old_sources+new_sources,
            "checkpoints":{k:sha256((cache/f"{k}.npz").read_bytes()).hexdigest() for k in ("aktuell","zeitlich")}}
    (cache/"trainiert.json").write_text(json.dumps(report,indent=2)+"\n")
    print("Trained",report["train_rows"],"rows",flush=True)


def load_model(p):
    net=Residual().eval()
    with np.load(p,allow_pickle=False) as z:
        net.load_state_dict({k:torch.from_numpy(z[k]) for k in z.files},strict=True)
    return net


def evaluate(folder,cache):
    torch.set_num_threads(1)
    report=json.loads((cache/"trainiert.json").read_text())
    if report["plan"]!=sha256((HERE/"PLAN.md").read_bytes()).hexdigest():
        raise ValueError("Changed plan")
    data,sources=dataset(folder,range(160366000,160366024))
    val={}
    per_map={}
    mask,base,y,conflict=data["mask"],data["scores"],data["y"].long(),data["disagree"]
    with torch.inference_mode():
        for which in ("original","aktuell","zeitlich"):
            if which=="original":
                total=base
            else:
                p=cache/f"{which}.npz"
                if sha256(p.read_bytes()).hexdigest()!=report["checkpoints"][which]:raise ValueError("Changed model")
                net=load_model(p)
                effects=torch.cat([net(a.float(),current_only=(which=="aktuell")) for a in data["x"].split(2048)])
                total=base+effects
            logits=total.masked_fill(~mask,-torch.inf)
            action=logits.argmax(1)
            correct=action==y
            val[which]=dict(hits=int(correct.sum()), conflict_hits=int(correct[conflict].sum()),
                            logloss=float(torch.nn.functional.cross_entropy(logits,y)))
            per_map[which]=[dict(seed=int(seed),hits=int(correct[data["seed"]==seed].sum()),
                                 conflict_hits=int(correct[(data["seed"]==seed)&conflict].sum()))
                            for seed in range(160366000,160366024)]
    o,c,t=(val[k] for k in ("original","aktuell","zeitlich"))
    n=len(y)
    nc=int(conflict.sum())
    maps=int(data["seed"][conflict].unique().numel())
    gate=dict(support=nc>=500 and maps>=12, all_gain=(t["hits"]-o["hits"])/n>=.005,
              conflict_gain=(t["conflict_hits"]-o["conflict_hits"])/max(1,nc)>=.01,
              beats_control_accuracy=t["hits"]>c["hits"],beats_control_loss=t["logloss"]<c["logloss"])
    result=dict(eligible=all(gate.values()),gates=gate, rows=n,disagreements=nc,cards_with_disagreement=maps,
                metrics=val,per_map=per_map, inputs=sources, train=sha256((cache/"trainiert.json").read_bytes()).hexdigest(),
                plan=report["plan"], checkpoint=report["checkpoints"]["zeitlich"])
    (cache/"offline.json").write_text(json.dumps(result,indent=2)+"\n")
    print(n,nc,val,gate,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("action",choices=("train","check"))
    p.add_argument("--device",choices=("mps","cpu"),default="mps")
    a=p.parse_args()
    if a.action=="train":train(a.folder,a.out,a.device)
    else:evaluate(a.folder,a.out)
