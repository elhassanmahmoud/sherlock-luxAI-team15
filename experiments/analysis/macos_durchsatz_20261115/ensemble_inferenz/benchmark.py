"""Compare native and packed evaluation of the same 36 fixed V14 networks."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import pickle
from statistics import median
import sys
from time import perf_counter

import numpy as np
import torch

V14 = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
RECORD = 'd6a2b14937e3687051f5fd5ac0dca7edfad2469e7a6bd7877e0170184f6b53eb'
SIDES = ('player_0', 'player_1')


class ParallelDueling:
    def __init__(self, members):
        if len(members) != 36 or any(not x.dueling or x.feat_dim != 79 for x in members):
            raise ValueError('Expected the homogeneous V14 ensemble')
        self.layers = {}
        for group, indices in (('body', (0, 2)), ('adv', (0, 2)), ('value', (0, 2))):
            for index in indices:
                layers = [getattr(m, group)[index] for m in members]
                self.layers[group,index] = (torch.stack([n.bias.detach() for n in layers])[:,None,:],
                    torch.stack([n.weight.detach().T for n in layers]).contiguous())

    def layer(self, group, index, h):
        bias, weights = self.layers[group,index]
        return torch.baddbmm(bias, h, weights)

    def __call__(self, features):
        inputs = features.unsqueeze(0).expand(36,-1,-1)
        h = self.layer('body', 0, inputs).relu()
        h = self.layer('body', 2, h).relu()
        a = self.layer('adv', 2, self.layer('adv', 0, h).relu())
        v = self.layer('value', 2, self.layer('value', 0, h).relu())
        return (v + a - a.mean(-1, keepdim=True)).mean(0)


def replay(weights, record, fast):
    from scripts.common import make_opponent
    from scripts.xversion_replay import arrays, require_clean_policy
    actors = {}
    for side in SIDES:
        actor = make_opponent('self',side,self_play_path=str(weights))
        actor.new_game(side)
        actor.set_env_cfg(record['cfg'])
        if fast:
            actor._network_values = ParallelDueling([actor.q, *actor.extra_q])
        actors[side] = actor
    t = perf_counter()
    differences = 0
    for turn in record['rec']:
        for side,actor in actors.items():
            obs = arrays(turn['obs'][side])
            predicted = actor.act(turn['step'], obs)
            require_clean_policy(actor,side)
            differences += int(not np.array_equal(predicted, turn['acts'][side]))
    return {'seconds': perf_counter()-t, 'different_commands': differences}


def run(args):
    repo = args.project.resolve()
    sys.path.insert(0,str(repo))
    from scripts.common import make_opponent
    weights = repo / 'agents/sherlock/weights/agent_p0.pth'
    assert hashlib.sha256(weights.read_bytes()).hexdigest() == V14
    record_path = repo / 'experiments/analysis/continuation_20261102/existing_v14_preflight/v14_4242.pkl.gz'
    recorded = gzip.decompress(record_path.read_bytes())
    assert hashlib.sha256(recorded).hexdigest() == RECORD
    record = pickle.loads(recorded)
    assert len(record['rec']) == 303
    actor = make_opponent('self', SIDES[0], self_play_path=str(weights))
    packed = ParallelDueling([actor.q,*actor.extra_q])
    funcs = {'native':actor._network_values, 'packed':packed}
    data = repo / 'experiments/imitation/final_20261115_r3_context'
    batches = []
    inputs = {}
    for seed,opp in ((7287000,'solution92'),(7287001,'v14'),(7287002,'kaggle3')):
        for side in SIDES:
            p = data / f'g{seed}_{side}_{opp}.npz'
            inputs[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
            with np.load(p,allow_pickle=False) as archive:
                feats = archive['feats'].astype(np.float32)
                masks = archive['mask']
                steps = archive['step']
                for step in np.unique(steps):
                    select = steps == step
                    batches.append((torch.from_numpy(feats[select]),torch.from_numpy(masks[select])))
    max_error=0
    different=0
    exact=0
    for features,mask in batches:
        n=funcs['native'](features)
        f=packed(features)
        assert torch.isfinite(n).all() and torch.isfinite(f).all()
        max_error=max(max_error,float((n-f).abs().max()))
        exact+=int(torch.equal(n,f))
        different+=int((n.masked_fill(~mask,-torch.inf).argmax(1)!=f.masked_fill(~mask,-torch.inf).argmax(1)).sum())
    timing={'native':[],'packed':[]}
    for order in [('native','packed'),('packed','native')]*2:
        for name in order:
            fn=funcs[name]
            t=perf_counter()
            for features,_ in batches[::4]:
                fn(features)
            timing[name].append(perf_counter()-t)
    games={'native':[],'packed':[]}
    for order in [('native','packed'),('packed','native')]:
        for name in order:
            games[name].append(replay(weights,record,name=='packed'))
    result=dict(source={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in
                ['agents/sherlock/model.py','agents/sherlock/main.py','scripts/common.py']},
                tool=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),v14=V14,fixture=RECORD,
                inputs=inputs,timed_batches=len(batches[::4]),batches=len(batches),units=sum(len(f) for f,_ in batches),
                torch=torch.__version__,threads=torch.get_num_threads(),exact_batches=exact,max_abs_q_error=max_error,
                different_masked_argmax=different,timing=timing,network_speed_ratio=median(timing['native'])/median(timing['packed']),
                replay=games,action_runtime_ratio=median(r['seconds'] for r in games['native'])/median(r['seconds'] for r in games['packed']))
    with args.out.open('x') as f:
        json.dump(result,f,indent=2)
        f.write('\n')
    print(json.dumps({k:result[k] for k in ('different_masked_argmax','max_abs_q_error','network_speed_ratio','replay','action_runtime_ratio')}))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    torch.manual_seed(0)
    torch.set_num_threads(1)
    with torch.inference_mode():
        run(parser.parse_args())
