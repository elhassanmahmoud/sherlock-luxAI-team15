"""Detect structurally incompatible simultaneous teacher targets; cache public ranking inputs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import torch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(HERE.parent/"netzwahl"))
from vorhersagen import input_files, networks
from scripts.imitate import prepare_labels

CHANNELS=(0,6,5,7,8,10,11,12)
WIDTH=12


def legal_shots(z):
    rows={k:torch.from_numpy(z[k]) for k in ("pos","feats","mask","act","sdx","sdy")}
    prepare_labels(rows,*z["planes"].shape[-2:])
    idx=rows["sap_label"].nonzero().flatten().numpy()
    return idx,rows["rng"].numpy()[idx],rows["tgt"].numpy()[idx]


def conflict_data(step,position,radius,targets):
    active=np.zeros(len(step),dtype=bool)
    frames=set(); count=np.zeros(4,dtype=np.int64)
    for f in np.unique(step):
        rows=np.flatnonzero(step==f)
        if len(rows)<2: continue
        first,second=np.triu_indices(len(rows),k=1)
        a,b=rows[first],rows[second]
        overlap=(np.abs(position[a]-position[b]).max(1)<=radius[a]+radius[b])
        mutual=((np.abs(position[a]-targets[b]).max(1)<=radius[a]) &
                (np.abs(position[b]-targets[a]).max(1)<=radius[b]))
        different=(targets[a]!=targets[b]).any(1)
        bad=mutual & different
        count+=np.array([len(a),overlap.sum(),mutual.sum(),bad.sum()])
        if bad.any():
            frames.add(int(f)); active[a[bad]]=True; active[b[bad]]=True
    return active, dict(zip(("pairs","overlap","mutual","conflict_pairs"),map(int,count))),len(frames)


def candidates(board_map,pos,radius):
    width,height=board_map.shape
    x,y=map(int,pos)
    xs=np.arange(max(0,x-radius),min(width,x+radius+1))
    ys=np.arange(max(0,y-radius),min(height,y+radius+1))
    ids=(xs[:,None]*height+ys).reshape(-1)
    scores=board_map.flat[ids]
    top=np.argsort(-scores,kind="stable")[:WIDTH]
    return ids[top],scores[top]


def features(public,xy,pos,radius,energy):
    own_x,own_y=map(int,pos)
    dx=(xy[:,0]-own_x)/max(1,radius)
    dy=(xy[:,1]-own_y)/max(1,radius)
    field=public[np.asarray(CHANNELS)[:,None],xy[None,:,0],xy[None,:,1]].T
    condition=np.stack((dx,dy,abs(dx),abs(dy),np.maximum(abs(dx),abs(dy)),
                        np.full_like(dx,energy),np.full_like(dx,public[0,own_x,own_y])),axis=1)
    return np.concatenate((field,condition),axis=1).astype(np.float32)


def load(e,p):
    if sha256(p.read_bytes()).hexdigest()!=e["sha256"]:
        raise ValueError(f"Checksum failed at {p}")
    with np.load(p,allow_pickle=False) as archive:
        z={k:archive[k] for k in ("planes","pos","feats","mask","act","sdx","sdy","step")}
        m=json.loads(str(archive["meta"]))
    if m["teacher_history"]!="played_student_actions" or m["steps"]!=303 or any(m[k]!=e[k] for k in ("seed","side","opponent")):
        raise ValueError("Not a certified teacher decision")
    return z


def preprocess(entry,path,split,models,out):
    z=load(entry,path); board=z["planes"]; height=board.shape[-1]
    idx,radius,y=legal_shots(z)
    pos=z["pos"][idx].astype(int)
    frame=z["step"][idx]
    xy=np.stack(np.divmod(y,height),axis=1)
    conflict,c,nfrm=conflict_data(frame,pos,radius,xy)
    stat=dict(seed=entry["seed"],source=entry["sha256"],split=split,side=entry["side"],opponent=entry["opponent"],
              legal_shots=len(idx),conflicting_rows=int(conflict.sum()),conflict_frames=nfrm,**c)
    if models is None: return stat
    n=len(idx)
    x=np.zeros((n,WIDTH,15),dtype=np.float16)
    scores=np.full((n,WIDTH),-np.inf,dtype=np.float32)
    label=np.full(n,-1,dtype=np.int16)
    selected=np.unique(frame)
    for at in range(0,len(selected),16):
        frames=selected[at:at+16]
        boards=board[frames].astype(np.float32)/127
        with torch.no_grad():
            inp=torch.from_numpy(boards).to(next(models[0].parameters()).device)
            # The released ImitationNet target head depends on this board encoder only.
            maps=[torch.log_softmax(net.sap(net.blocks(net.stem(inp))).flatten(1),dim=1) for net in models]
            raw=(maps[0]+maps[1]).cpu().numpy().reshape(len(frames),*board.shape[-2:])
        for k,f in enumerate(frames):
            for r in np.flatnonzero(frame==f):
                ids,values=candidates(raw[k],pos[r],int(radius[r]))
                cols=np.stack(np.divmod(ids,height),axis=1)
                x[r,:len(ids)]=features(boards[k],cols,pos[r],radius[r],float(z["feats"][idx[r],2]))
                scores[r,:len(ids)]=values-values[0]
                hits=np.flatnonzero(ids==y[r])
                if len(hits): label[r]=hits[0]
    np.savez_compressed(out/f"{split}_{entry['seed']}.npz",x=x,scores=scores,y=label,conflict=conflict,source=entry["sha256"])
    stat["shortlist_hits"]=int((label>=0).sum())
    return stat


def totals(rows):
    return {key:sum(r[key] for r in rows) for key in ("legal_shots","pairs","overlap","mutual","conflict_pairs","conflicting_rows","conflict_frames")}


def run(phase,base,out):
    torch.set_num_threads(1)
    out.mkdir(exist_ok=True,parents=True)
    items=input_files(base,False,include_validation=phase=="valid")
    if phase=="structure":
        stats=[preprocess(e,p,split,None,out) for e,p,split in items]
        s=totals(stats); s["maps_with_conflicts"]=sum(r["conflict_pairs"]>0 for r in stats)
        s["gate"]=s["conflict_pairs"]>=150 and s["maps_with_conflicts"]>=12 and s["conflict_pairs"]>=.02*s["mutual"]
        result=dict(totals=s,maps=stats)
        (out/"struktur.json").write_text(json.dumps(result,indent=2)+"\n"); print(s); return
    if not json.loads((out/"struktur.json").read_text())["totals"]["gate"]:
        raise ValueError("Insufficient structural signal")
    models=networks("mps")
    items=[row for row in items if (row[2]=="valid")==(phase=="valid")]
    stats=[]
    for e,p,split in items:
        row=preprocess(e,p,split,models,out)
        stats.append(row)
        print(split,e["seed"],flush=True)
    (out/f"{phase}.json").write_text(json.dumps(stats,indent=2)+"\n")


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("phase",choices=("structure","train","valid"))
    cli.add_argument("base",type=Path);cli.add_argument("out",type=Path)
    a=cli.parse_args();run(a.phase,a.base,a.out)
