"""Complete new, outcome-independent panel of both original course packages."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys

import jax
import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

HERE=Path(__file__).resolve().parent; STUDY=HERE.parent
sys.path.insert(0,str(STUDY/'vergleich'))
from panel import sensor
from spielen import Monitor, PACKAGE, make_opponent, play_game, r3_package_agent, require_no_agent_errors
from scripts.experiment import limit_threads

ROOT=STUDY.parents[2];SCRATCH=Path.home()/'Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/r3_folge'
R3=ROOT/'experiments/releases/20261116_r3_finale/agent.zip'
HASHES={'r3':'8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d','v16':'0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099'}


def digest(p):return sha256(p.read_bytes()).hexdigest()


def seeds():
    vals=np.arange(163400000,163401000,dtype=np.int32)
    sight=np.asarray(jax.jit(jax.vmap(sensor))(vals)); selected=vals[sight==1][:24].tolist()
    assert len(set(selected))==24
    return selected


def run(policy):
    assert os.environ.get('PYTHONHASHSEED')=='0';limit_threads()
    package={'r3':R3,'v16':PACKAGE}[policy];assert digest(package)==HASHES[policy]
    binding={p.name:digest(p) for p in (package,HERE/'PLAN.md',Path(__file__),STUDY/'vergleich/spielen.py')}
    out=SCRATCH/'originale'/policy;out.mkdir(parents=True,exist_ok=True)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed in seeds():
            for team in (0,1):
                dest=out/f'{seed}-{team}.json'
                if dest.exists():assert json.loads(dest.read_text())['source']==binding;continue
                side=f'player_{team}';random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
                actor=r3_package_agent(side,package);rival=make_opponent('solution92',f'player_{1-team}')
                mon=Monitor(env,team,'discovery');game=play_game(mon,actor,rival,seed,side,False)
                assert mon.turn==game['steps']==303 and len(mon.matches)==3 and mon.sensor==1
                require_no_agent_errors(actor,rival)
                assert sum(m['win'] for m in mon.matches)==game['our_wins']
                row=dict(seed=seed,team=team,id=policy,sensor=1,matches=mon.matches,win=int(game['game_win']),
                         sight=mon.first_sight,credit=mon.first_credit,action_hash=mon.digest.hexdigest(),agent_errors=[0,0],source=binding)
                tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(row,sort_keys=True)+'\n');tmp.replace(dest)
    finally:env.close()
    print(policy,'48 complete games',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('policy',choices=('r3','v16'));run(p.parse_args().policy)
