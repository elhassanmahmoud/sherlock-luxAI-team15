"""Observe the first real opening disagreement, then reproduce the archived original V16 result."""
import argparse
import csv
import gzip
from hashlib import sha256
import json
from pathlib import Path
import sys
import random
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from staffel import ROOT, R3, R3_SHA, V16, V16_SHA, r3_package_agent, r3_player
from spielen import save
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import require_no_agent_errors

MOVES=((0,0),(0,-1),(1,0),(0,1),(-1,0))
SCORES=("game_win","our_wins","opp_wins","our_points","opp_points")
ARCHIVE_SHA="6379d063531bea987518b256fe5f1e8815b04c266b32f5ac1be57d4e9ea7c1a0"
CHECK_SHA="e9d6946d7894ebd4e3d0abb41341a66b95df68d0c897c486139dca00a2ee6cef"


def observations():
    original=HERE.parent/"auswahl_partien.jsonl.gz"
    if sha256(original.read_bytes()).hexdigest()!=ARCHIVE_SHA:
        raise ValueError("Screen archive identity changed")
    with gzip.open(original,"rt") as f:
        target={(r["seed"],r["team"],r["opponent"]):r for line in f if (r:=json.loads(line))["arm"]=="original"}
    cases=[(s,1,"solution92","solution_gerettet") for s in (160362065,160362073)]
    cases +=[(s,t,"kaggle3","kaggle_verloren") for s in (160362049,160362057,160362066) for t in (0,1)]
    cases +=[(160362030,t,"kaggle3","kaggle_gerettet") for t in (0,1)]
    out=[((s,t,o,g),target[s,t,o]) for s,t,o,g in cases]
    public=json.loads((HERE.parents[1]/"kartenparameter/ergebnis.json").read_text())["maps"]
    path=ROOT/"experiments/analysis/devf_20261117/bestaetigung3_kandidat.csv"
    if sha256(path.read_bytes()).hexdigest()!=CHECK_SHA:
        raise ValueError("Original V16 confirmation archive changed")
    with path.open(newline="") as f:
        ref={(int(r["seed"]),int(r["side"][-1]),r["opponent"]):r for r in csv.DictReader(f)}
    conditions=(("solution92",0),("kaggle3",0),("solution92",1),("kaggle3",1))
    for sight in (1,2):
        seeds=sorted(r["seed"] for r in public if 7261000<=r["seed"]<7261400 and r["unit_sensor_range"]==sight)[:16]
        if len(seeds)!=16:
            raise ValueError("Missing independent original maps")
        for i,s in enumerate(seeds):
            opponent,team=conditions[i%4]
            out.append(((s,team,opponent,"kontrolle"),ref[s,team,opponent]))
    if len(out)!=42 or len({k for k,r in out})!=42:
        raise ValueError("Duplicated cases")
    return out


def features(obs, model, cfg, team, observed, original, r3):
    pos=np.asarray(obs["units"]["position"])[team]
    energy=np.asarray(obs["units"]["energy"])[team]
    live=np.flatnonzero(np.asarray(obs["units_mask"])[team] & (energy>=0))
    if not len(live):
        raise ValueError("No living own units at disagreement")
    belief=model.belief
    terrain=belief.tile_type
    if belief.mirrored:
        terrain=terrain[::-1,::-1].T
    W,H=observed.shape
    radius=int(cfg["unit_sensor_range"]);cost=int(cfg["unit_move_cost"])
    def destination(commands,uid):
        x,y=map(int,pos[uid]);a=int(commands[uid,0])
        if 1<=a<=4 and energy[uid]>=cost:
            dx,dy=MOVES[a]
            x1,y1=x+dx,y+dy
            if 0<=x1<W and 0<=y1<H and terrain[x1,y1]!=2:
                return x1,y1
        return x,y
    def footprint(commands):
        visible=np.zeros_like(observed)
        for uid in live:
            x,y=destination(commands,uid)
            visible[max(0,x-radius):x+radius+1,max(0,y-radius):y+radius+1]=True
        return int((visible&~observed).sum())
    changed=[int(uid) for uid in live if not np.array_equal(original[uid],r3[uid])]
    if not changed:
        raise ValueError("Only an inactive unit changed")
    foe=int(np.asarray(obs["units_mask"])[1-team].sum())
    relics=len(belief.relic_positions);points=int(belief.point_tiles.sum())
    shoot=any(5 in (int(original[u,0]),int(r3[u,0])) for u in changed)
    base_new=footprint(original);alt_new=footprint(r3)
    return dict(geometric_frontier_v16=base_new,geometric_frontier_r3=alt_new,unseen_difference=alt_new-base_new,
                own_visible_cumulative=int(observed.sum()),own_units=len(live),movable_units=int((energy[live]>=cost).sum()),
                enemies_visible=foe,known_relics=relics,known_points=points,changed_sap=shoot,
                changed_ids=changed,changes=[dict(uid=u,xy=pos[u].tolist(),v16=original[u].tolist(),
                                                  r3=r3[u].tolist()) for u in changed],
                trigger=bool(not (foe or relics or points or shoot) and alt_new>base_new))


class Shadow:
    def __init__(self, side):
        self.team=int(side[-1])
        self.base=r3_package_agent(side,V16)
        self.r3=r3_player(side)
        self.seen=np.zeros((24,24),dtype=bool)
        self.first=None

    def __getattr__(self,name):return getattr(self.base,name)

    def new_game(self, side):
        self.base.new_game(side);self.r3.new_game(side)

    def set_env_cfg(self,cfg):
        self.base.set_env_cfg(cfg);self.r3.set_env_cfg(cfg)

    def act(self,step,obs):
        command=self.base.act(step,obs)
        if self.first is not None or step>40:
            return command
        self.seen |= np.asarray(obs["sensor_mask"],dtype=bool)
        other=self.r3.act(step,obs)
        if np.any(other!=command):
            if not 1<=step<=40:
                raise ValueError("Difference at setup")
            self.first=features(obs,self.base._imitation,self.base.env_cfg,self.team,self.seen,command,other)
            self.first["step"]=step
        return command


def run(lane):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    if sha256(R3.read_bytes()).hexdigest()!=R3_SHA or sha256(V16.read_bytes()).hexdigest()!=V16_SHA or not verify():
        raise ValueError("Policy source changed")
    folder=HERE/"partien"
    folder.mkdir(exist_ok=True)
    stamp={x:sha256((HERE/x).read_bytes()).hexdigest() for x in ("messen.py","PLAN.md")}
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for key,expected in observations()[lane::2]:
            seed,team,opponent,group=key
            target=folder/(f"{seed}_{team}_{opponent}.json")
            if target.exists():
                old=json.loads(target.read_text())
                if old["source"]!=stamp or old["scores"]!={f:int(expected[f]) for f in SCORES}:
                    raise ValueError("Stale measured case")
                continue
            random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
            side=f"player_{team}"
            shadow=Shadow(side);rival=make_opponent(opponent,f"player_{1-team}")
            game=play_game(env,shadow,rival,seed,side,False)
            require_no_agent_errors(shadow.base,rival);require_no_agent_errors(shadow.r3,rival)
            scores={f:game[f] for f in SCORES}
            if any(scores[f]!=int(expected[f]) for f in SCORES) or game["steps"]!=303 or game["point_counting_version"]!=2:
                raise ValueError(f"Original V16 archive mismatch {key}")
            save(target,dict(seed=seed,team=team,opponent=opponent,group=group,scores=scores,source=stamp,
                             sensor=int(shadow.base.env_cfg["unit_sensor_range"]),steps=303,first=shadow.first))
    finally:
        env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("lane",type=int,choices=(0,1))
    args=p.parse_args();run(args.lane)
