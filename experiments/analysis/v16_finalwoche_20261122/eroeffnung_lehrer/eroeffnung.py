"""Die ersten 101 Originalentscheidungen der beiden Spieler gegen Solution auf acht neuen Karten."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
import jax

HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
ROOT=STUDY.parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(STUDY/"kartenparameter"))
from auswerten import generate
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import match_points_after_step

PKG=ROOT/"experiments/releases/20261117_sherlock_v16/agent.zip"
SHA="0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"


class MatchComplete(Exception):
    pass


class Capture:
    """Unterbricht den gemeinsamen Spielrunner nach exakt einem vollständigen Originalmatch."""
    def __init__(self,env,side):
        self.env=env
        self.side=side
        self.team=int(side[-1])
        self.frames=[]

    def reset(self,**kw):
        result=self.env.reset(**kw)
        self.previous=result[0][self.side]
        if int(result[1]["params"]["unit_sensor_range"])!=1:
            raise ValueError("Falsche Reichweite im Originalspiel")
        return result

    def step(self,actions):
        t=len(self.frames)
        old=self.previous
        if t!=int(old["match_steps"]):
            raise ValueError("Unterbrochene Zugfolge")
        output=self.env.step(actions)
        new=output[0][self.side]
        points=match_points_after_step(old,new,output[4])
        scores=[int(points[self.team]),int(points[1-self.team])]
        self.frames.append(dict(turn=t,visible=bool(np.asarray(old["relic_nodes_mask"]).any()),after=scores))
        self.previous=new
        if t==100:
            wins=list(map(int,new["team_wins"]))
            if sum(wins)!=1 or int(new["match_steps"])!=0:
                raise ValueError("Kein gültiger Matchabschluss")
            self.win=wins[self.team]
            raise MatchComplete
        return output


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("lane",type=int,choices=(0,1))
    parser.add_argument("--out",type=Path,default=HERE,help="Leerer Zielordner für die eigene Reproduktion")
    args=parser.parse_args()
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    if hashlib.sha256(PKG.read_bytes()).hexdigest()!=SHA or not verify():
        raise ValueError("Falsche Originaldateien")
    candidates=np.arange(160394000,160394100,dtype=np.int32)
    params=np.asarray(jax.jit(jax.vmap(generate))(candidates))
    seeds=[int(s) for s,p in zip(candidates,params,strict=True) if p[0]==1][:8]
    if len(seeds)!=8:
        raise ValueError("Unvollständige Auswahl")
    args.out.mkdir(parents=True,exist_ok=True)
    path=args.out/f"teil_{args.lane}.jsonl"
    path.touch(exist_ok=False)
    env=LuxAIS3GymEnv(numpy_output=True)
    for seed in seeds[args.lane::2]:
        for side in ("player_0","player_1"):
            for arm in ("v16","kaggle3"):
                agent=r3_package_agent(side,PKG) if arm=="v16" else make_opponent(arm,side)
                enemy=make_opponent("solution92",f"player_{1-int(side[-1])}")
                capture=Capture(env,side)
                try:
                    play_game(capture,agent,enemy,seed,side,False)
                except MatchComplete:
                    pass
                if len(capture.frames)!=101:
                    raise ValueError("Falsche Matchlänge")
                require_no_agent_errors(agent,enemy)
                f=capture.frames
                record=dict(seed=seed,side=side,arm=arm,first_relic=next((r["turn"] for r in f if r["visible"]),None),
                            first_own_score=next((r["turn"] for r in f if r["after"][0]),None),
                            after_70=f[70]["after"],match_score=f[100]["after"],match_win=capture.win,
                            frames=101)
                with path.open("a") as out:
                    out.write(json.dumps(record)+"\n")
                    out.flush()
                    os.fsync(out.fileno())
                print(seed,side,arm,flush=True)
    env.close()


if __name__=="__main__":
    main()
