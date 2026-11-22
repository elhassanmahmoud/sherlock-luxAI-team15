"""Play only a qualified late-return policy from the original V16 package on unused seeds."""
from pathlib import Path
import argparse
import hashlib
import json
import random

from messen import ROOT,HERE,PACKAGE,DIGEST,write,ReturnPolicy,limit_threads,make_opponent,r3_package_agent,require_no_agent_errors
from scripts.common import play_game
import numpy as np


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


class Candidate:
    def __init__(self,side):
        self.base=r3_package_agent(side,PACKAGE)
        self.rule=ReturnPolicy(self.base)
        self.interventions=[]

    def __getattr__(self,key):return getattr(self.base,key)

    def act(self,step,obs):
        commands=self.base.act(step,obs)
        options,_=self.rule.options(obs,commands)
        if not options:return commands
        event=options[0]
        self.interventions.append((step,event['uid'],event['old'],event['move']))
        return self.rule.apply(commands,event)


def keys(phase):
    if phase=='auswahl':
        start,maps,direct=160347100,20,20
    elif phase=='bestaetigung':
        start,maps,direct=160348000,200,50
    else:raise ValueError('Unknown phase')
    return [(s,t,o,arm) for s in range(start,start+maps) for t in (0,1)
            for o in ('solution92','kaggle3','v16') for arm in ('original','kandidat')
            if o!='v16' or (arm=='kandidat' and s<start+direct)]


def run(phase,lane,folder):
    import torch
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.fetch_kaggle3 import verify
    if sha(PACKAGE)!=DIGEST or not verify():raise ValueError('Release or opponent')
    approval=HERE/('diagnose_ergebnis.json' if phase=='auswahl' else 'auswahl_ergebnis.json')
    if not json.loads(approval.read_text())['passed']:raise ValueError('Previous stage failed')
    bindings={p.name:sha(p) for p in (HERE/'regel.py',HERE/'PLAN.md',HERE/'spielvergleich.py',approval)}
    env=LuxAIS3GymEnv(numpy_output=True)
    for index,(seed,team,opponent,arm) in enumerate(keys(phase)):
        if index%2!=lane:continue
        dest=folder/f'{seed}_{team}_{opponent}_{arm}.json'
        if dest.exists():
            old=json.loads(dest.read_text())
            if ([old['seed'],old['team'],old['opponent'],old['arm']]!=[seed,team,opponent,arm] or
                    old['steps']!=303 or old['binding']!=bindings): raise ValueError(dest)
            continue
        random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
        side,other=f'player_{team}',f'player_{1-team}'
        me=Candidate(side) if arm=='kandidat' else r3_package_agent(side,PACKAGE)
        opp=r3_package_agent(other,PACKAGE) if opponent=='v16' else make_opponent(opponent,other)
        row=play_game(env,me,opp,seed,side,train=False)
        require_no_agent_errors(me.base if arm=='kandidat' else me,opp)
        if (row['steps']!=303 or row['our_wins']+row['opp_wins']!=3 or
                row['game_win']!=int(row['our_wins']>=2) or row['point_counting_version']!=2):raise ValueError(row)
        out=dict(seed=seed,team=team,opponent=opponent,arm=arm,binding=bindings,release=DIGEST,
                 interventions=(me.interventions if arm=='kandidat' else []))
        out.update({k:row[k] for k in ('steps','our_wins','opp_wins','game_win','our_points','opp_points')})
        write(dest,out)
    env.close()


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('phase',choices=('auswahl','bestaetigung'));ap.add_argument('lane',type=int,choices=(0,1))
    ap.add_argument('folder',type=Path)
    args=ap.parse_args();limit_threads();run(args.phase,args.lane,args.folder)
