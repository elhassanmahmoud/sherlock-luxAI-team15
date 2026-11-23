"""Find whether the agent previously scored on, or could physically test, the unknown mirrored tile."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import random

import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.vergleich.spielen import PACKAGE, Monitor, require
from experiments.analysis.v16_finalwoche_20261122.feldverlauf import Record
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.r3_package import r3_package_agent
from scripts.par_eval import require_no_agent_errors

HERE=Path(__file__).resolve().parent
DELTAS=((0,-1),(1,0),(0,1),(-1,0))


def mirror(p):
    return 23-p[1],23-p[0]


def canonical_pair(p):
    return min(p,mirror(p))


class MirrorAccess(Monitor):
    def __init__(self,env,team,brain):
        super().__init__(env,team,"discovery")
        self.brain=brain
        self.scored=set()
        self.enterable={}
        self.events=[]
        self.ready_rows=[]

    def step(self,commands):
        match,turn=divmod(self.turn,101)
        if turn==0:
            self.enterable.clear()
        p=self.brain._imitation
        b=p.belief
        def world(board):
            return board[::-1,::-1].T if b.mirrored else board
        zone,point,dead=map(world,(b.relic_zone,b.point_tiles,b.dead_tiles))
        current_candidates=set()
        options=[]
        if p.last_fz is not None:
            ctx,ids,_,masks,_,_,pos=p.last_fz
            team=self.team
            for idx,uid in enumerate(ids):
                uid=int(uid)
                loc=tuple(map(int,pos[idx]))
                if not (ctx["ally_ene"][uid]>=max(30,4*ctx["move_cost"])
                        and commands[self.side][uid,0]<=4 and not ctx["point_tiles"][loc]
                        and not (ctx["assigned"].get(uid) is not None and ctx["point_tiles"][ctx["assigned"][uid]])):
                    continue
                for dir_id,(dx,dy) in enumerate(DELTAS,1):
                    x,y=loc[0]+dx,loc[1]+dy
                    if not(0<=x<24 and 0<=y<24 and masks[idx,dir_id] and ctx["candidate"][x,y]):
                        continue
                    tile=mirror((x,y)) if team else (x,y)
                    pair=canonical_pair(tile)
                    current_candidates.add(pair)
                    options.append((uid,dir_id,pair))
        for pair in current_candidates:
            self.enterable[pair]=turn
        result=super().step(commands)
        own,enemy=[self.env.frames[-1][i] for i in (self.team,1-self.team)]
        touched={canonical_pair(xy) for xy in own}
        for xy in sorted(enemy):
            if zone[xy] and not point[xy]:
                pair=canonical_pair(xy)
                self.events.append(dict(match=match+1,t=turn,x=xy[0],y=xy[1],
                    pair=pair,was_known_empty=bool(dead[xy]),previously_scored=pair in self.scored,
                    currently_enterable=pair in current_candidates,
                    entered_in_last_20=pair in self.enterable and turn-self.enterable[pair]<=20,
                    ever_enterable_this_match=pair in self.enterable))
        if current_candidates:
            self.ready_rows.append(dict(match=match+1,t=turn,candidate_pairs=[list(x) for x in sorted(current_candidates)],
                correct_pairs_after_move=[list(x) for x in sorted(touched & current_candidates)]))
        self.scored.update(touched)
        return result


def main():
    limit_threads()
    with gzip.open(HERE/"verlaeufe.jsonl.gz","rt") as f:
        originals={(r["seed"],r["team"]):r for r in map(json.loads,f)}
    env=LuxAIS3GymEnv(numpy_output=True)
    studies=[]
    try:
        for (seed,team),old in sorted(originals.items()):
            random.seed(seed)
            torch.manual_seed(seed)
            np.random.seed(seed)
            side=f"player_{team}"
            a=r3_package_agent(side,PACKAGE)
            foe=make_opponent("solution92",f"player_{1-team}")
            m=MirrorAccess(Record(env),team,a)
            play_game(m,a,foe,seed,side,False)
            require_no_agent_errors(a,foe)
            require(m.matches==old["matches"] and len(m.events)==sum(r["points"][1][1] for r in old["rows"]),
                    "Mirrored opportunities do not match independently classified points")
            gathered=[]
            for idx in (1,2,3):
                events=[e for e in m.events if e["match"]==idx]
                stats={col:sum(bool(e[col]) for e in events) for col in
                         ("was_known_empty","previously_scored","currently_enterable","entered_in_last_20","ever_enterable_this_match")}
                gathered.append(dict(match=idx,events=len(events),distinct_pairs=len({tuple(r["pair"]) for r in events}),**stats))
            studies.append(dict(seed=seed,team=team,matches=gathered,events=m.events,ready=m.ready_rows))
    finally:
        env.close()
    raw="\n".join(json.dumps(r,separators=(",",":"),default=int) for r in studies)+"\n"
    (HERE/"spiegelereignisse.jsonl.gz").write_bytes(gzip.compress(raw.encode(),mtime=0))
    print(json.dumps([{k:r[k] for k in ("seed","team","matches")} for r in studies],indent=2))


if __name__=="__main__":
    main()
