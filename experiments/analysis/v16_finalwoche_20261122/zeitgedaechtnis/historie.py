"""Build a causal history per surviving ship using the same encoder offline and in play."""
from collections import deque
from pathlib import Path
import sys

import numpy as np
import torch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
from agents.sherlock.features import FEATURE_NAMES

NAMES=("self_x","self_y","self_energy","match_step_frac","match_idx_frac","on_point","on_cand","point_dx",
       "point_dy","assigned_dx","assigned_dy","enemy_dx","enemy_dy","enemy_dist","enemy_energy_rel",
       "enemies_in_sap","enemies_visible","own_points","point_diff","known_points","explored_frac")
COLS=[FEATURE_NAMES.index(name) for name in NAMES]
WIDTH=len(COLS)+4*(len(COLS)+1)


class History:
    def __init__(self):
        self.ships={}

    def record(self, tick, ids, pos, feats, live):
        current=feats[:,COLS].astype(np.float32)
        x=np.zeros((len(ids),WIDTH),np.float32)
        x[:,:len(COLS)]=current
        prev=self.ships
        self.ships={}
        for k in np.flatnonzero(live):
            uid=int(ids[k])
            turns=prev.get(uid,deque(maxlen=8))
            if turns and (turns[-1][0]!=tick-1 or np.abs(pos[k]-turns[-1][1]).sum()>1):
                turns=deque(maxlen=8)
            offset=len(COLS)
            for lag in (1,2,4,8):
                if len(turns)>=lag:
                    x[k,offset:offset+len(COLS)]=turns[-lag][2]-current[k]
                    x[k,offset+len(COLS)]=1
                offset+=len(COLS)+1
            turns.append((int(tick),pos[k].copy(),current[k].copy()))
            self.ships[uid]=turns
        return x


class Residual(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.body=torch.nn.Linear(WIDTH,48)
        self.head=torch.nn.Linear(48,6)
        torch.nn.init.zeros_(self.head.weight)
        torch.nn.init.zeros_(self.head.bias)

    def forward(self,x,current_only=False):
        if current_only:
            x=torch.cat((x[:,:len(COLS)],torch.zeros_like(x[:,len(COLS):])),dim=1)
        return 1.5*torch.tanh(self.head(torch.relu(self.body(x))))


def archived_inputs(step,mstep,ids,pos,feats):
    h=History()
    splits=np.r_[0,np.flatnonzero(np.diff(step))+1,len(step)]
    x=np.empty((len(step),WIDTH),np.float16)
    for a,b in zip(splits[:-1],splits[1:],strict=True):
        if b<=a: continue
        if not np.all(mstep[a:b]==mstep[a]):
            raise ValueError("Inconsistent match clock")
        x[a:b]=h.record(int(mstep[a]),ids[a:b],pos[a:b].astype(int),feats[a:b],np.ones(b-a,bool))
    return x
