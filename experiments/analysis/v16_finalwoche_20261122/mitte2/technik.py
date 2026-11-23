import argparse
from collections import Counter
from hashlib import sha256
import csv
import json
from pathlib import Path
import random

import numpy as np
import torch
from mitte import HERE, SOURCE, PACKAGE, Policy, Middle, choose, model, optionen, r3_package_agent
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors


class Compare:
    def __init__(self,side,net):
        self.middle=Middle(side,net)
        self.reference=Policy(r3_package_agent(side,PACKAGE),net)
        original=self.reference.base.act
        def original_action(step,obs):
            self.plain=original(step,obs)
            return self.plain
        self.reference.base.act=original_action
        self.count=Counter()

    def new_game(self,side):
        self.middle.new_game(side);self.reference.new_game(side)

    def set_env_cfg(self,cfg):
        self.middle.set_env_cfg(cfg);self.reference.set_env_cfg(cfg)

    def act(self,step,obs):
        neutral=self.middle.act(step,obs)
        original_advice=self.reference.act(step,obs)
        if not np.array_equal(neutral,self.plain):
            raise ValueError("Passive middle changed the real original command")
        self.count["all_actions"]+=1
        if int(obs["match_steps"])>=91:
            ours=optionen.options(self.middle,neutral)
            their=self.reference.last
            if len(ours)!=len(their) or any(a[:3]!=b[:3] or not np.array_equal(a[3],b[3]) for a,b in zip(ours,their)):
                raise ValueError("Option identity failed")
            self.count["identical_options"]+=len(ours)
            proposed=choose(self.middle.net,ours)
            action=neutral.copy()
            if proposed:
                action[proposed["uid"]]=[proposed["world"],0,0]
                self.count["identical_changes"]+=1
            if not np.array_equal(action,original_advice):
                raise ValueError("Score selection, identity or release threshold failed")
        return neutral


def run(lane):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads();net=model()
    starts=(7261000,7267000);side=f"player_{lane}"
    paths=("devf_20261117/bestaetigung3_kandidat.csv","devh_20261117/bestaetigung5_k.csv")
    with (HERE.parents[1]/paths[lane]).open() as src:
        original={(int(r["seed"]),r["side"]):r for r in csv.DictReader(src) if r["opponent"]=="solution92"}
    env=LuxAIS3GymEnv(numpy_output=True);rows=[]
    try:
        for seed in range(starts[lane],starts[lane]+8):
            random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
            audit=Compare(side,net);opp=make_opponent("solution92",f"player_{1-lane}")
            g=play_game(env,audit,opp,seed,side,False)
            if (audit.count["all_actions"]!=303 or any(g[k]!=int(original[seed,side][k]) for k in
                    ("game_win","our_wins","opp_wins","our_points","opp_points"))):
                raise ValueError("Passive actual game differs from archived original")
            require_no_agent_errors(audit.middle.base,opp);require_no_agent_errors(audit.reference.base,opp)
            rows.append(dict(seed=seed,side=side,**dict(audit.count)))
            if audit.count["identical_changes"]>0:
                break
        if not any(r.get("identical_changes",0)>0 for r in rows):
            raise ValueError("No active late action in the technical panel")
        (HERE/f"technik_{lane}.json").write_text(json.dumps(rows,indent=2)+"\n")
    finally:
        env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("lane",type=int,choices=(0,1));run(p.parse_args().lane)
