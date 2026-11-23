"""Original R3 tape parity and independent forced-return feedback on original V16 tapes."""
import json
from pathlib import Path

import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

from archiv import TAPES, save
from berater import Advice, feedback, r3_player
from originale import HERE, digest, limit_threads


def frame(z,t):
    return {**{k:z[k][t] for k in ('units_mask','sensor_mask','relic_nodes','relic_nodes_mask','team_points','team_wins','steps','match_steps')},
            'units':{k:z['units/'+k][t] for k in ('position','energy')},
            'map_features':{k:z['map_features/'+k][t] for k in ('energy','tile_type')}}


def test():
    limit_threads();env=LuxAIS3GymEnv(numpy_output=True);results=[]
    try:
        for team in (0,1):
            side=f'player_{team}'
            for mode in ('r3','v16'):
                meta=next(iter(sorted(TAPES.glob(f'{mode}_*_{side}.json'))));receipt=json.loads(meta.read_text());seed=receipt['seat']['seed']
                npz=TAPES/receipt['filename'];assert digest(npz)==receipt['sha256']
                with np.load(npz,allow_pickle=False) as data:z={k:data[k] for k in data.files}
                _,info=env.reset(seed=seed);cfg=info['params'];main=r3_player(side);main.new_game(side);main.set_env_cfg(cfg)
                seen=changed=memories=0
                if mode=='v16':
                    ref=r3_player(side);ref.new_game(side);ref.set_env_cfg(cfg);under=ref._actor;native=under._act;reference_proposals=[]
                    def force(step,obs):
                        proposal=np.asarray(native(step,obs));reference_proposals.append(proposal.copy());truth=z['commands'][step]
                        for uid in under._prev_actions:
                            if np.array_equal(proposal[uid],truth[uid]):continue
                            d,dx,dy=map(int,truth[uid]);under._prev_actions[uid]=(0,2,1,4,3,5)[d] if team else d
                            under._sap_unknown.discard(uid);under._sap_hits.pop(uid,None)
                            if d==5:
                                x,y=map(int,obs['units']['position'][team,uid]);gx,gy=x+dx,y+dy
                                foe=1-team;v=obs['units_mask'][foe]&(obs['units']['energy'][foe].reshape(-1)>=0)
                                under._sap_hits[uid]=sum(max(abs(int(a)-gx),abs(int(b)-gy))<=1 for a,b in obs['units']['position'][foe,v])
                                if not obs['sensor_mask'][gx,gy]:under._sap_unknown.add(uid)
                        return truth.copy()
                    under._act=force
                for t in range(160):
                    o=frame(z,t);actual=z['commands'][t];proposed=main.act(t,o)
                    if mode=='r3':assert np.array_equal(proposed,actual),(seed,team,t,'native')
                    else:
                        forced=ref.act(t,o);assert np.array_equal(forced,actual) and np.array_equal(reference_proposals[-1],proposed),(seed,team,t,'advice')
                    feedback(main,o,proposed,actual)
                    changed+=int(np.any(proposed!=actual));seen+=1
                    orig=main._actor
                    assert np.array_equal(orig.param_est._prev['act'],actual)
                    for u,a in orig._prev_actions.items():
                        d=int(actual[u,0]);assert a==((0,2,1,4,3,5)[d] if team else d);memories+=1
                    if mode=='v16':
                        assert under._prev_actions==orig._prev_actions and under._sap_hits==orig._sap_hits and under._sap_unknown==orig._sap_unknown
                        assert np.array_equal(under.param_est._prev['act'],orig.param_est._prev['act'])
                        assert np.array_equal(under.belief.point_tiles,orig.belief.point_tiles)
                    assert not main.caught_errors and (mode!='v16' or not ref.caught_errors)
                results.append(dict(seed=seed,team=team,original=mode,public_steps=seen,changed_reference_commands=changed,
                                    canonical_unit_actions=memories,tape_sha=receipt['sha256']))
    finally:env.close()
    save(HERE/'technik.json',dict(checks=results,source=digest(HERE/'berater.py')))
    print('Both seats, frozen package and independent input-forcing replay verified',flush=True)


if __name__=='__main__':test()
