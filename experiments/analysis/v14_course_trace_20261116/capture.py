"""Extract a masked V14 movement from the trusted 4242 course trajectory."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path
import pickle
import sys

import numpy as np
import torch

WEIGHT = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
REPLAY = 'd6a2b14937e3687051f5fd5ac0dca7edfad2469e7a6bd7877e0170184f6b53eb'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    repo=args.project.resolve()
    sys.path.insert(0,str(repo))
    from scripts.common import make_opponent
    from scripts.xversion_replay import arrays,require_clean_policy
    from agents.sherlock import geometry as geo
    weight=repo/'agents/sherlock/weights/agent_p0.pth'
    assert sha256(weight.read_bytes()).hexdigest()==WEIGHT
    packed=repo/'experiments/analysis/continuation_20261102/existing_v14_preflight/v14_4242.pkl.gz'
    raw=gzip.decompress(packed.read_bytes())
    assert sha256(raw).hexdigest()==REPLAY
    d=pickle.loads(raw)
    side='player_0'
    a=make_opponent('self',side,self_play_path=str(weight))
    a.new_game(side)
    a.set_env_cfg(d['cfg'])
    assert a.cnn_policy is None and len(a.extra_q)==35 and not a.training and not a.belief.mirrored
    native=a._network_values
    last=[]
    def capture(features):
        values=native(features)
        last.append(values.detach().cpu().numpy().copy())
        return values
    a._network_values=capture
    matches=0
    candidates=[]
    for turn in d['rec']:
        last.clear()
        obs=arrays(turn['obs'][side])
        command=a.act(turn['step'],obs)
        require_clean_policy(a,side)
        assert np.array_equal(command,turn['acts'][side])
        matches+=1
        if not last:
            continue
        step,ctx,uids,_,masks,targets=a._cache
        assert step==turn['step'] and len(last)==1
        for row,uid in enumerate(uids):
            pos=np.array(ctx['ally_pos'][uid],dtype=int); values=last[0][row]
            mask=masks[uid]
            top=int(np.argmax(values)); best=int(np.argmax(np.where(mask,values,-np.inf)))
            if top==best or best!=int(command[uid,0]) or top==0 or np.sum(mask)<2:
                continue
            # Opponent-facing explanations limited to unambiguous geometry or absent shot target.
            if top==geo.SAP:
                if targets[uid] is not None or ctx['ally_ene'][uid]<ctx['sap_cost']:
                    continue
                reason='Kein gültiges Schussziel'
            else:
                tx=int(pos[0]+geo.DIR_DX[top]);ty=int(pos[1]+geo.DIR_DY[top])
                if not (0<=tx<ctx['W'] and 0<=ty<ctx['H']):
                    reason='Zielfeld außerhalb der Karte'
                elif not ctx['passable'][tx,ty] and int(a.belief.tile_type[tx,ty])==2:
                    reason='Asteroid auf dem Zielfeld'
                else:
                    continue
            ranked=np.sort(values[mask])
            gap=min(values[top]-values[best],ranked[-1]-ranked[-2])
            candidates.append(dict(step=step,match=step//101+1,match_step=int(obs['match_steps']),uid=uid,
                position=pos.tolist(),q=list(map(float,values)),mask=mask.tolist(),raw_max=top,allowed_max=best,
                executed=command[uid].tolist(),reason=reason,energy=int(ctx['ally_ene'][uid]),
                sap_cost=int(ctx['sap_cost']),visible_enemies=len(ctx['enemy_coords']),margin=float(gap)))
    assert matches==303 and candidates
    # Pick a representative, clearly separated example, preferably an asteroid and actual move.
    c=sorted(candidates,key=lambda r:(r['reason']!='Asteroid auf dem Zielfeld',r['allowed_max'] not in (1,2,3,4),
                                     r['margin']<.12,r['step'],r['uid']))[0]
    result=dict(map_seed=4242,side=side,weight=WEIGHT,replay=REPLAY,source_sha256=sha256((repo/'agents/sherlock/main.py').read_bytes()).hexdigest(),
      script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),q_order=['stay','up','right','down','left','sap'],
      matrices_reproduced=matches,examples_meeting_filters=len(candidates),example=c)
    with args.out.open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False);f.write('\n')
    print(c)
if __name__=='__main__':
    torch.set_num_threads(1)
    main()
