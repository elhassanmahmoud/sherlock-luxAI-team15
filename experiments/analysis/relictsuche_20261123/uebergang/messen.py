"""Recover public knowledge and exact awarded points for every changed game on both seats."""
import gzip
from hashlib import sha256
import json
from pathlib import Path
import random
import sys

import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(STUDY/"vergleich"))
sys.path.insert(0,str(STUDY.parent/"v16_finalwoche_20261122"))
from spielen import Monitor, PACKAGE, RELEASE
from feldverlauf import Record
from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import create
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors


class Knowledge(Monitor):
    def __init__(self,env,team,agent,is_candidate):
        super().__init__(env,team,"discovery",agent if is_candidate else None)
        self.brain=agent.base if is_candidate else agent
        self.categories=np.zeros((3,4,2,3),int)
        self.snapshots=[]

    def step(self, actions):
        memory=self.brain._imitation.belief
        zone=np.where(memory.point_tiles,2,np.where(memory.relic_zone,1,0))
        if memory.mirrored:
            zone=zone[::-1,::-1].T
        i,t=divmod(self.turn,101)
        if t in (0, 25,50,75,100):
            self.snapshots.append(dict(match=i+1,turn=t,confirmed=int((zone==2).sum()),
                relic_locations=len(memory.relic_coords()),explored=int(memory.explored.sum())))
        result=super().step(actions)
        for j, team in enumerate((self.team,1-self.team)):
            for x,y in self.env.frames[-1][team]:
                self.categories[i,min(3,t//25),j,zone[x,y]]+=1
        return result


def main():
    from scripts.r3_package import r3_package_agent
    limit_threads()
    if sha256(PACKAGE.read_bytes()).hexdigest()!=RELEASE:
        raise ValueError("Wrong release")
    with gzip.open(STUDY/"vergleich/discovery/partien.jsonl.gz","rt") as f:
        rows=[json.loads(line) for line in f]
    archive={(r["seed"],r["team"],r["id"]):r for r in rows if r["opponent"]=="solution92"}
    affected={seed for seed,team,name in archive if name=="ziel"
              and archive[seed,team,name]["win"]!=archive[seed,team,"reference"]["win"]}
    if len(affected)!=4:
        raise ValueError("Unexpected changed maps")
    out=[]
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed in sorted(affected):
            for team in (0,1):
                for name in ("reference","ziel"):
                    source=archive[seed,team,name]
                    random.seed(seed)
                    torch.manual_seed(seed)
                    np.random.seed(seed)
                    side=f"player_{team}"
                    actor=create(side) if name=="ziel" else r3_package_agent(side,PACKAGE)
                    rival=make_opponent("solution92",f"player_{1-team}")
                    m=Knowledge(Record(env),team,actor,name=="ziel")
                    game=play_game(m,actor,rival,seed,side,False)
                    require_no_agent_errors(m.brain,rival)
                    if (m.digest.hexdigest()!=source["action_hash"] or m.events!=source["events"]
                            or m.matches!=source["matches"] or game["game_win"]!=source["win"]):
                        raise ValueError("Replay differs from whole-game benchmark")
                    if m.categories.sum(axis=(1,3)).tolist()!=[v["points"] for v in m.matches]:
                        raise ValueError("Category scores do not sum to actual points")
                    out.append(dict(seed=seed,team=team,agent=name,action_hash=source["action_hash"],
                         match_end=m.matches,knowledge=m.snapshots,points_by_quarter_team_type=m.categories.tolist()))
                    print(seed,team,name,flush=True)
    finally:
        env.close()
    content="".join(json.dumps(r,separators=(",",":"))+"\n" for r in out).encode()
    (HERE/"nachspiele.jsonl.gz").write_bytes(gzip.compress(content,mtime=0))


if __name__=="__main__":
    main()
