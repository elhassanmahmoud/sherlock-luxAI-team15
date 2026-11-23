"""Replay the complete direct contest with a same-map V16 self-play control."""
import argparse
import gzip
import json
from pathlib import Path
import random
import sys

import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
from experiments.analysis.relictsuche_20261123.vergleich.spielen import (
    CUTOFF, PACKAGE, Monitor, datetime, play_game, require, require_no_agent_errors, r3_package_agent, sha, write_once,
)
from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import create
from scripts.experiment import limit_threads
from scripts.scoring import match_points_after_step, point_tile_map


class Race:
    def __init__(self, env, actor, side):
        self.env, self.actor, self.side = env, actor, side
        self.frames = []
        self.finds = [None, None]
        self.turn = 0
        self.first_spawn = None

    def reset(self, **kwargs):
        result = self.env.reset(**kwargs)
        self.views = result[0]
        return result

    def step(self, actions):
        t = self.turn
        if t <= 100:
            state = self.env.state
            if self.first_spawn is None and np.asarray(state.relic_nodes_mask).any():
                self.first_spawn = t
            for team in (0, 1):
                obs = self.views[f"player_{team}"]
                if self.finds[team] is None and np.asarray(obs["relic_nodes_mask"]).any():
                    tiles = np.argwhere(point_tile_map(state))
                    live = np.asarray(obs["units_mask"][team],bool) & (np.asarray(obs["units"]["energy"][team]).reshape(-1)>=0)
                    positions=np.asarray(obs["units"]["position"][team])
                    picked=self.actor.ship if team==self.side and self.actor is not None else None
                    by_uid = {}
                    for uid in np.flatnonzero(live):
                        if len(tiles):
                            by_uid[int(uid)]=int(np.abs(tiles-positions[uid]).sum(1).min())
                    self.finds[team]=dict(turn=t,uid=picked,distances=by_uid,live=int(live.sum()),
                                          visible_rival=int(np.asarray(obs["units_mask"][1-team]).sum()))
        result = self.env.step(actions)
        if t <= 100:
            after = result[0]["player_0"]
            old = self.views["player_0"]
            points = match_points_after_step(old,after,result[4])
            state = result[4]["final_state"]
            truth = point_tile_map(state)
            live = np.asarray(state.units_mask) & (np.asarray(state.units.energy)[...,0]>=0)
            all_fields=[]
            for team in (0, 1):
                pos=np.asarray(state.units.position)[team,live[team]]
                fields={tuple(map(int,xy)) for xy in pos if truth[tuple(xy)]}
                all_fields.append(sorted(fields))
            require([len(v) for v in all_fields]==(points-old["team_points"]).tolist(),"Physical points differ")
            self.frames.append(dict(points=points.tolist(),fields=all_fields))
        self.turn+=1
        self.views=result[0]
        return result


def run(folder,lane,stride):
    limit_threads()
    with gzip.open(STUDY/"vergleich/discovery/partien.jsonl.gz","rt") as f:
        archive = {(r["seed"],r["team"]):r for line in f if (r:=json.loads(line))["id"]=="ziel" and r["opponent"]=="v16"}
    jobs=[(s,side) for s in sorted({k[0] for k in archive}) for side in (-1,0,1)]
    identity={p.name:sha(p) for p in (Path(__file__),HERE/"PLAN.md",PACKAGE,STUDY/"zielschaetzer/kandidat.py",STUDY/"zielschaetzer/ort.json")}
    write_once(folder/"inputs.json",identity)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed,side in jobs[lane::stride]:
            if datetime.now(CUTOFF.tzinfo)>=CUTOFF:
                break
            dest=folder/f"{seed}_{side}.json.gz"
            if dest.exists():
                with gzip.open(dest,"rt") as f:
                    require(json.load(f)["source"]==identity,"Mixed input")
                continue
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
            team=max(0,side)
            actor=create(f"player_{team}") if side>=0 else r3_package_agent(f"player_{team}",PACKAGE)
            rival=r3_package_agent(f"player_{1-team}",PACKAGE)
            race=Race(env,actor if side>=0 else None,side)
            second=Monitor(race,1-team,"discovery")
            first=Monitor(second,team,"discovery",actor if side>=0 else None)
            game=play_game(first,actor,rival,seed,f"player_{team}",False)
            require_no_agent_errors(actor.base if side>=0 else actor,rival)
            if side>=0:
                old=archive[seed,side]
                require(first.digest.hexdigest()==old["action_hash"] and first.events==old["events"]
                        and first.matches==old["matches"] and first.first_sight==old["sight"]
                        and first.first_credit==old["credit"] and game["game_win"]==old["win"],"Archive mismatch")
            require(first.digest.hexdigest()==second.digest.hexdigest() and race.first_spawn is not None, "Invalid course trace")
            views={}
            for idx,mon in ((team,first),(1-team,second)):
                require(race.frames[-1]["points"][idx]==mon.matches[0]["points"][0],"Incorrect last turn")
                require((race.finds[idx]["turn"] if race.finds[idx] else 101)==mon.first_sight,"Earliest sight differs")
                views[idx]=dict(sight=mon.first_sight,credit=mon.first_credit,matches=mon.matches)
            data=dict(seed=seed,side=side,source=identity,spawn=race.first_spawn,views=views,finds=race.finds,
                      frames=race.frames,commands=first.events,digest=first.digest.hexdigest())
            dest.parent.mkdir(parents=True,exist_ok=True)
            tmp=dest.with_suffix(".tmp")
            tmp.write_bytes(gzip.compress(json.dumps(data,separators=(",",":")).encode(),mtime=0))
            tmp.replace(dest)
            print(seed,side,flush=True)
    finally:
        env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    p.add_argument("lane",type=int)
    p.add_argument("stride",type=int)
    a=p.parse_args()
    run(a.folder,a.lane,a.stride)
