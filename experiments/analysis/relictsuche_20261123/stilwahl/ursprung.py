"""Reproduce the first eligible historical opening per side and opponent; require exact public tensors and two-team command hashes."""
import gzip
import json
from pathlib import Path
import random
import sys

import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

from daten import ARCH,GAMES,HERE,save
sys.path.insert(0,str(HERE.parents[3]))
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor,PACKAGE,require_no_agent_errors
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.r3_package import r3_package_agent


def main():
    limit_threads();rows=[json.loads(l) for l in gzip.decompress(GAMES.read_bytes()).splitlines()]
    checks=[];env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for opp in ('solution92','v16'):
            for team in (0,1):
                row=min((r for r in rows if r['eligible'] and r['team']==team and r['opponent']==opp),key=lambda r:r['seed'])
                s=row['seed'];side=f'player_{team}';other=f'player_{1-team}'
                random.seed(s);np.random.seed(s);torch.manual_seed(s)
                own=r3_package_agent(side,PACKAGE);rival=r3_package_agent(other,PACKAGE) if opp=='v16' else make_opponent(opp,other)
                for a,name in ((own,side),(rival,other)):
                    if hasattr(a,'new_game'):a.new_game(name)
                random.seed(s);np.random.seed(s);mon=Monitor(env,team,'discovery');obs,info=mon.reset(seed=s)
                for a in (own,rival):
                    if hasattr(a,'set_env_cfg'):a.set_env_cfg(info['params'])
                with np.load(ARCH/f'{s}-{team}.npz',allow_pickle=False) as z:
                    archive={k:z[k][:101] for k in ('units_mask','position','energy','sensor_mask','commands')}
                for t in range(101):
                    view=obs[side]
                    assert np.array_equal(view['units_mask'],archive['units_mask'][t]) and np.array_equal(view['sensor_mask'],archive['sensor_mask'][t])
                    for k in ('position','energy'):assert np.array_equal(view['units'][k],archive[k][t])
                    a=own.act(t,view);assert np.array_equal(a,archive['commands'][t])
                    obs,_,_,_,_=mon.step({side:a,other:rival.act(t,obs[other])})
                assert mon.matches==row['base']['matches'][:1] and mon.digest.hexdigest()==row['base']['prefix']==row['switch']['prefix']
                require_no_agent_errors(own,rival)
                checks.append(dict(seed=s,team=team,opponent=opp,opening_steps=101,exact_both_teams_hash=mon.digest.hexdigest()))
    finally:env.close()
    save(HERE/'ursprung.json',dict(anchors=checks,replayed_public_frames=404))
    print('All four original M1 observation archives and both-team action traces reproduced')


if __name__=='__main__':main()
