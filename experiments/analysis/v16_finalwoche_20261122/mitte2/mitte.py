"""Frozen one-step value student in a public middle-match situation."""
import ast
import inspect
from hashlib import sha256
from pathlib import Path
import sys
import textwrap

import numpy as np
import torch

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/"zugnutzen"
sys.path.insert(0,str(SOURCE))
from berater import PACKAGE, V16, Policy, ValueNet, g
import optionen
from scripts.r3_package import r3_package_agent

MODEL_SHA="67d6f11e7c87b20f068f0b800fc352362b962d2577903a2182658d50f56c06fb"
SOURCE_SHA="315cce8f84389355ee0bd1482e3e92bb24ff3b74da5d30a1e268a01d27fc6b8c"


def sha(file):return sha256(file.read_bytes()).hexdigest()


def model():
    weights=SOURCE/"wertberater.npz"
    if sha(weights)!=MODEL_SHA or sha(SOURCE/"berater.py")!=SOURCE_SHA or sha(PACKAGE)!=V16:
        raise ValueError("Frozen model identity differs")
    source=ast.parse(textwrap.dedent(inspect.getsource(Policy.options)))
    local=ast.parse(inspect.getsource(optionen.options))
    f=source.body[0]
    gate=ast.parse('if int(ctx["match_step"]) < 81:\n    return []').body[0]
    matches=[i for i,node in enumerate(f.body) if ast.dump(node)==ast.dump(gate)]
    if len(matches)!=1:
        raise ValueError("Cannot identify the original time filter")
    f.body.pop(matches[0])
    if ast.dump(source)!=ast.dump(local):
        raise ValueError("Public option calculations differ beyond the sole time guard")
    network=ValueNet().eval()
    with np.load(weights,allow_pickle=False) as z:
        network.load_state_dict({k:torch.from_numpy(z[k]) for k in z.files})
    return network


def choose(net, options):
    if not options:return None
    with torch.inference_mode():
        scores=net(torch.from_numpy(np.stack([r[3] for r in options]))).flatten().numpy()
    i=max(range(len(scores)),key=lambda j:(float(scores[j]),-options[j][1]))
    if scores[i]<.25:return None
    gap,uid,world,features=options[i]
    return dict(uid=int(uid),world=int(world),value=float(scores[i]),gap=float(gap),
                public_features=sha256(np.ascontiguousarray(features).tobytes()).hexdigest())


class Middle(Policy):
    def __init__(self,side,net,apply=False):
        super().__init__(r3_package_agent(side,PACKAGE),net)
        self.team=int(side[-1]);self.apply=apply
        self.event=None;self.original=None
        self.behind_steps=0;self.options_steps=0

    def act(self,step,obs):
        command=self.base.act(step,obs)
        self.original=command
        t=int(obs["match_steps"])
        wins=np.asarray(obs["team_wins"])
        points=np.asarray(obs["team_points"])
        if (self.event is not None or not 26<=t<=75 or wins[self.team]!=1 or wins[1-self.team]!=0
                or not 101<=step<202 or points[self.team]>=points[1-self.team]):
            return command
        self.behind_steps+=1
        options=optionen.options(self,command)
        self.options_steps+=int(bool(options))
        picked=choose(self.net,options)
        if picked is None:return command
        uid=picked["uid"];world=picked["world"]
        if not 0<=world<=4 or not 0<=command[uid,0]<=4 or int(command[uid,0])==world:
            raise ValueError("Not a distinct feasible movement")
        side=self.base._imitation
        canon=g.mirror_dir(world) if side.belief.mirrored else world
        ids=np.asarray(side.last_fz[1]);k=np.flatnonzero(ids==uid)
        if len(k)!=1 or not side.last_fz[3][int(k[0]),canon]:
            raise ValueError("Incorrect side transformation or illegal movement")
        self.event=dict(**picked,step=step,ms=t,original=int(command[uid,0]),
                        team_points=[int(x) for x in points],world_position=obs["units"]["position"][self.team,uid].tolist())
        if not self.apply:return command
        out=command.copy();out[uid]=[world,0,0]
        if np.count_nonzero(np.any(out!=command,axis=1))!=1:
            raise ValueError("Changed more than one ship")
        side._prev_actions[uid]=canon
        side._sap_hits.pop(uid,None)
        side.param_est.record_played_actions(out)
        self.changed+=1
        return out
