"""Measure M3 CPU vs GPU on the same V14 evaluation, including returning the scores to the CPU."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from statistics import median
import sys
from time import perf_counter

import numpy as np
import torch

from benchmark import ParallelDueling, V14


def prepare(project, pilot):
    from scripts.common import make_opponent
    weights = project/'agents/sherlock/weights/agent_p0.pth'
    if sha256(weights.read_bytes()).hexdigest() != V14:
        raise ValueError('Expected the published V14')
    actor=make_opponent('self','player_0',self_play_path=str(weights))
    actor.set_to_eval_mode()
    native=actor._network_values
    cpu=ParallelDueling([actor.q,*actor.extra_q])
    gpu=ParallelDueling([actor.q,*actor.extra_q])
    gpu.layers={k:(bias.to('mps'),weights.to('mps')) for k,(bias,weights) in gpu.layers.items()}
    calls={'cpu':cpu,'mps':lambda x:gpu(x.to('mps')).to('cpu')}
    frames=[]
    for filename,pin in sorted(pilot['inputs'].items()):
        path=project/'experiments/imitation/final_20261115_r3_context'/filename
        if sha256(path.read_bytes()).hexdigest()!=pin:
            raise ValueError('Changed sample '+filename)
        with np.load(path,allow_pickle=False) as z:
            feats=z['feats'].astype(np.float32); masks=z['mask'];steps=z['step']
            for i in np.unique(steps):
                select=steps==i
                frames.append((torch.from_numpy(feats[select]),torch.from_numpy(masks[select])))
    return native,calls,frames


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--project',type=Path,required=True)
    cli.add_argument('--pilot',type=Path,required=True)
    cli.add_argument('--out',type=Path,required=True)
    a=cli.parse_args()
    sys.path.insert(0,str(a.project.resolve()))
    if not torch.backends.mps.is_available():
        raise SystemExit('Metal accelerator unavailable')
    native,calls,frames=prepare(a.project,json.loads(a.pilot.read_bytes()))
    max_error=0
    changes=0
    for x,mask in frames:
        ref=native(x)
        g=calls['mps'](x)
        if not torch.isfinite(g).all():
            raise ValueError('Nonfinite MPS output')
        max_error=max(max_error,float((g-ref).abs().max()))
        changes+=int((g.masked_fill(~mask,-torch.inf).argmax(1)!=ref.masked_fill(~mask,-torch.inf).argmax(1)).sum())
    results={}
    # Timing includes copying from actual CPU features and returning all six scores per unit.
    # Frames in a block need not be consecutive in the game; the feedforward nets have no hidden state.
    selected=frames[::4]
    for block in (1,16,64):
        batches=[torch.cat([x for x,_ in selected[i:i+block]]) for i in range(0,len(selected),block)]
        timing={'cpu':[],'mps':[]}
        for fn in calls.values():
            for x in batches: fn(x)
        for order in (('cpu','mps'),('mps','cpu'))*2:
            for device in order:
                t=perf_counter()
                for x in batches: calls[device](x)
                timing[device].append(perf_counter()-t)
        results[str(block)]={'batches':len(batches),'unit_rows':sum(len(x) for x in batches),'seconds':timing,'cpu_over_mps':median(timing['cpu'])/median(timing['mps'])}
    proof={'study_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'pilot_sha256':sha256(a.pilot.read_bytes()).hexdigest(),'weight_sha256':V14,
           'torch':torch.__version__,'frames':len(frames),'decisions':sum(len(x) for x,_ in frames),'gpu_different_legal_argmax':changes,
           'gpu_max_abs_q_error':max_error,'cpu_threads':torch.get_num_threads(),'results':results}
    with a.out.open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
    print({k:round(v['cpu_over_mps'],3) for k,v in results.items()},'changed',changes,flush=True)

if __name__=='__main__':
    torch.set_num_threads(1)
    with torch.inference_mode():
        main()
