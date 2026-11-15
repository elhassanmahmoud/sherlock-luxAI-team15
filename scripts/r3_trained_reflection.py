"""One fixed x/y-augmented training arm paired to the real archived R8 MPS run."""
import argparse
from collections import Counter
import fcntl
from pathlib import Path
import platform
import tempfile

import numpy as np
import torch

from scripts import r8_warm as warm
from scripts.r3_diagonal import ACTIONS, FEATURES, R3
from scripts.selective_advice_agent import load_heads
from scripts.train_combat_advice import publish

CONTROL = "93046242f41e16a5e355bc75836b1630816d174890abb804b49969b49893c532"
PLAN = "experiments/analysis/r3_trained_reflection_20261115/PLAN.md"


def provenance():
    extra = ("scripts/r3_trained_reflection.py","agents/sherlock/features.py",PLAN)
    return {**warm.sources(), **{f:warm.file_sha(warm.ROOT/f) for f in extra}}


def control_metadata(parent, control):
    if warm.file_sha(parent)!=R3 or warm.file_sha(control)!=CONTROL:
        raise ValueError("Original R3 and completed unaugmented R8 required")
    baseline=torch.load(control,map_location="cpu",weights_only=True)["warm_training"]
    env=(baseline["device"],baseline["torch"],baseline["numpy"],baseline["python"])
    if (env!=("mps",str(torch.__version__),np.__version__,platform.python_version())
            or baseline["arm"]!="r8" or baseline["parent_sha256"]!=R3 or baseline["sources"]!=warm.sources()):
        raise ValueError("Reference training source or numerical environment differs")
    return baseline


def reflected_step(step):
    # Eight per round, alternating which positions reflect between successive sampler rounds.
    return (step//16+step%16)%2==1


def transposed_minibatch(boards, rows, chosen):
    ids=torch.from_numpy(chosen)
    frames,local=torch.unique(rows["step"][ids],sorted=True,return_inverse=True)
    take=lambda key: rows[key][ids]
    perm=torch.tensor(ACTIONS)
    pos=take("pos")[:,[1,0]]
    dx,dy=take("sdy").long(),take("sdx").long()
    if boards.shape[2:]!=(24,24):
        raise ValueError("Expected the archived 24 by 24 board")
    batch=dict(step=local,pos=pos,feats=take("feats")[:,FEATURES],mask=take("mask")[:,ACTIONS],
               act=perm[take("act").long()],base_act=perm[take("base_act").long()],sdx=dx,sdy=dy,
               tgt=(pos[:,0]+dx)*24+pos[:,1]+dy,rng=take("rng"),sap_label=take("sap_label"),
               distill_ok=take("distill_ok"),movement_scores=take("movement_scores")[:,ACTIONS[:5]])
    return boards[frames].transpose(-1,-2).contiguous(),batch,np.arange(len(ids),dtype=np.int64)


def fit(a):
    warm.limit_threads()
    torch.manual_seed(warm.SEED)
    reference=control_metadata(a.parent,a.control)
    out=warm.imitate._check_out(a.out)/"augmented.pth"
    if any(part in ("weights","releases") for part in out.parts) or not torch.backends.mps.is_available():
        raise ValueError("Fresh study location and matching MPS device required")
    out.parent.mkdir(parents=True,exist_ok=True)
    with (out.parent/"augmented.lock").open("a") as lock, tempfile.TemporaryDirectory(dir=out.parent) as tmp:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if out.exists(): raise FileExistsError(out)
        source=provenance()
        replay,support=warm.index(a.old,"replay"),warm.index(a.new,"r8")
        identity=dict(replay=warm.identities(replay),support=warm.identities(support))
        if identity!=reference["inputs"]: raise ValueError("Training data differ from the control")
        board, raw, sizes=warm.mapped_part(replay+support,Path(tmp)/"frames",distill_movement=True)
        boards=torch.from_numpy(board)
        rows={k:torch.from_numpy(v) for k,v in raw.items()}
        warm.imitate.prepare_labels(rows,24,24)
        edges=np.cumsum([0,*sizes])
        allowed=rows["admitted"].numpy()
        pools=[lo+np.flatnonzero(allowed[lo:hi]) for lo,hi in zip(edges,edges[1:])]
        left=warm.HalfBatch(replay,pools[:len(replay)],warm.SEED)
        right=warm.HalfBatch(support,pools[len(replay):],warm.SEED+1)
        nets,own_tile=load_heads(a.parent)
        if len(nets)!=1 or not own_tile: raise ValueError("Expected original solo R3")
        net=nets[0].to("mps").train()
        opt=torch.optim.AdamW(net.parameters(),lr=.0001,weight_decay=.0001)
        counts=Counter()
        flipped_updates=0
        for step in range(warm.UPDATES):
            old,new=left.draw(step),right.draw(step)
            chosen=np.concatenate((old,new))
            if len(np.unique(chosen))!=256 or not allowed[chosen].all():
                raise ValueError("Invalid training draw")
            if reflected_step(step):
                b,r,ids=transposed_minibatch(boards,rows,chosen)
                flipped_updates+=1
            else:
                b,r,ids=boards,rows,chosen
            opt.zero_grad(set_to_none=True)
            loss,frames,soft,shots=warm.loss_for(net,b,r,ids,"mps")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(),1.,error_if_nonfinite=True)
            opt.step()
            counts.update(updates=1,rows=len(chosen),unique_frames_per_update_summed=frames,soft_rows=soft,
                          sap_target_rows=shots,soft_replay_rows=int(raw["distill_ok"][old].sum()),
                          soft_support_rows=int(raw["distill_ok"][new].sum()))
            if (step+1)%128==0: print(f"reflected {step+1}/1024, loss {loss.item():.5f}",flush=True)
        counts["policy_adam_steps"]=int(opt.state[net.pi.weight]["step"].item())
        trace=dict(replay=left.summary(),support=right.summary())
        if (counts!=reference["counts"] or any(v!=reference[k] for k,v in trace.items()) or flipped_updates!=512
                or counts["rows"]!=262144 or min(counts["updates"],counts["policy_adam_steps"])!=1024
                or source!=provenance() or warm.file_sha(a.parent)!=R3 or warm.file_sha(a.control)!=CONTROL):
            raise ValueError("Actual draw, gradient steps, sources or parent differ")
        if any(warm.file_sha(r["path"])!=r["sha256"] for r in replay+support):
            raise ValueError("Training archives changed during fitting")
        base=torch.load(a.parent,map_location="cpu",weights_only=True)
        checkpoint={k:base[k] for k in ("kind","arch","cfg","feature_dim","sap_own_tile")}
        metadata=dict(parent=R3,control=CONTROL,source=source,counts=dict(counts),flipped_updates=flipped_updates,
                      inputs=identity,**trace)
        checkpoint.update(policy=net.cpu().eval().state_dict(),reflection_training=metadata)
        publish(out,lambda p:torch.save(checkpoint,p))
        print(out,warm.file_sha(out),flush=True)


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("parent","control","old","new","out"): cli.add_argument("--"+key,type=Path,required=True)
    fit(cli.parse_args())
