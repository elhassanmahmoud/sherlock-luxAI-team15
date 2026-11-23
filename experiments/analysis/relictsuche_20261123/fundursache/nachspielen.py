"""Isolate the scout's physical sensor on the precise turn the first relic became visible."""
import gzip
import json
import os
from pathlib import Path
import sys

import jax
import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
sys.path.insert(0,str(STUDY/"vergleich"))
from spielen import Monitor
from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import create
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors


class FirstMatch(Exception):
    pass


class Capture(Monitor):
    def __init__(self,env,team,actor,physical):
        super().__init__(env,team,"discovery",actor)
        self.physical=physical
        self.terrain=None
        self.cause=None

    def step(self,commands):
        obs=self.old
        st=self.env.state
        if self.cause is None and np.any(obs["relic_nodes_mask"]):
            seen=np.asarray(obs["relic_nodes_mask"],bool)
            assert self.terrain is not None
            grid=np.asarray(self.physical(st,self.env.env_params,self.terrain,self.team,st.units_mask[self.team]))
            assert np.array_equal(grid,np.asarray(obs["sensor_mask"],bool))
            live=np.asarray(st.relic_nodes_mask,bool)
            places=np.asarray(st.relic_nodes,int)
            assert np.array_equal(live & grid[tuple(places.T)],seen)
            uid=self.events[0][1] if self.events else None
            detail=None
            if uid is not None:
                selected=st.units_mask[self.team]
                without=np.asarray(self.physical(st,self.env.env_params,self.terrain,self.team,selected.at[uid].set(False)))
                only=np.asarray(self.physical(st,self.env.env_params,self.terrain,self.team,(selected*False).at[uid].set(selected[uid])))
                if (without & ~grid).any() or (only & ~grid).any():
                    raise ValueError("Removing ships enlarged real sensor coverage")
                detail=dict(uid=uid,others_see=bool((live & without[tuple(places.T)]).any()),
                            scout_alone_sees=bool((live & only[tuple(places.T)]).any()))
            self.cause=dict(turn=self.turn,prior_changes=len(self.events),sensor=detail)
        self.terrain=st.map_features.tile_type
        result=super().step(commands)
        if self.turn==101:
            raise FirstMatch
        return result


def main():
    if os.environ.get("PYTHONHASHSEED")!="0":
        raise ValueError("Invalid random setup")
    limit_threads()
    with gzip.open(STUDY/"vergleich/discovery/partien.jsonl.gz","rt") as f: rows=[json.loads(line) for line in f]
    refs={(r["seed"],r["team"]):r for r in rows if r["id"]=="reference" and r["opponent"]=="solution92"}
    target=[r for r in rows if r["id"]=="ziel" and r["opponent"]=="solution92"]
    if len(refs)!=80 or len(target)!=80:
        raise ValueError("Missing paired cases")
    env=LuxAIS3GymEnv(numpy_output=True)
    @jax.jit
    def physical(state,params,terrain,team,mask):
        state=state.replace(units_mask=state.units_mask.at[team].set(mask),
                            map_features=state.map_features.replace(tile_type=terrain))
        return env.jax_env.compute_sensor_masks(state,params).sensor_mask[team]
    records=[]
    try:
        for r in sorted(target,key=lambda x:(x["seed"],x["team"])):
            seed,team=r["seed"],r["team"]
            side=f"player_{team}"
            torch.manual_seed(seed)
            actor=create(side)
            rival=make_opponent("solution92",f"player_{1-team}")
            cap=Capture(env,team,actor,physical)
            try:
                play_game(cap,actor,rival,seed,side,False)
            except FirstMatch:
                pass
            require_no_agent_errors(actor.base,rival)
            if (cap.events!=r["events"] or cap.first_sight!=r["sight"] or cap.first_credit!=r["credit"]
                    or cap.after_70!=r["after_70"] or cap.matches!=r["matches"][:1]):
                raise ValueError(f"Opening replay differs on {seed}/{team}")
            records.append(dict(seed=seed,team=team,cause=cap.cause,first=r["sight"],
                          baseline=refs[seed,team]["sight"],credit=r["credit"]))
            print(seed,team,flush=True)
    finally: env.close()
    (HERE/"ursachen.json").write_text(json.dumps(records,indent=2)+"\n")


if __name__=="__main__":
    main()
