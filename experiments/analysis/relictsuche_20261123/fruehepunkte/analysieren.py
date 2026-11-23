"""Explain each real awarded point on the two early-credit loss maps and the paired control."""
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
from scripts.r3_package import r3_package_agent
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors

HERE=Path(__file__).resolve().parent
DELTA=np.asarray([(0,0),(0,-1),(1,0),(0,1),(-1,0)])
MIRROR=np.asarray([0,2,1,4,3])


class Detail(Monitor):
    def __init__(self,env,team,actor):
        super().__init__(env,team,"discovery")
        self.brain=actor
        self.rows=[]
        self.source=None

    def step(self,commands):
        t=self.turn
        match,turn=divmod(t,101)
        pol=self.brain._imitation
        b=pol.belief
        labels=np.where(b.point_tiles,2,np.where(b.relic_zone,1,0))
        if b.mirrored:
            labels=labels[::-1,::-1].T
        obs=self.old
        own=np.asarray(obs["units_mask"][self.team],bool) & (np.asarray(obs["units"]["energy"][self.team]).reshape(-1)>=0)
        pos=np.asarray(obs["units"]["position"][self.team])
        rival=np.asarray(obs["units_mask"][1-self.team],bool) & (np.asarray(obs["units"]["energy"][1-self.team]).reshape(-1)>=0)
        foe_pos=np.asarray(obs["units"]["position"][1-self.team])[rival]
        seen_foe={tuple(xy) for xy in foe_pos}
        available={}
        if pol.last_fz is not None:
            _,ids,_,mask,_,_,_=pol.last_fz
            for uid,m in zip(ids,mask,strict=True):
                uid=int(uid)
                if not own[uid]:
                    continue
                for native in range(1,5):
                    canon=int(MIRROR[native]) if self.team else native
                    if m[canon]:
                        xy=tuple(pos[uid]+DELTA[native])
                        available.setdefault(xy,[]).append(uid)
        result=super().step(commands)
        totals=np.zeros((2,3),int)
        chances=Counter()
        for side,team in enumerate((self.team,1-self.team)):
            for xy in self.env.frames[-1][team]:
                c=int(labels[xy])
                totals[side,c]+=1
                if side==1 and c==2:
                    near=int(np.abs(pos[own]-xy).sum(1).min()) if own.any() else 50
                    chances["distance_0" if near==0 else "distance_1" if near==1 else "distance_2_3" if near<=3 else "distance_4_plus"]+=1
                    chances["visible_enemy_before"]+=int(xy in seen_foe)
                    movers=available.get(xy,[])
                    if movers:
                        chances["entry_physically_allowed"]+=1
                        attempted=any(1<=int(commands[self.side][u,0])<=4
                            and tuple(pos[u]+DELTA[int(commands[self.side][u,0])])==xy for u in movers)
                        chances["entry_attempted"]+=int(attempted)
        self.rows.append(dict(match=match+1,turn=turn,points=totals.tolist(),rival_known=chances,
                              known_fields=int(np.sum(labels==2)),known_relics=len(b.relic_coords())))
        return result


def main():
    limit_threads()
    with gzip.open(HERE.parent/"flottenblick/ganzspiel/partien.jsonl.gz","rt") as f:
        idx={(r["seed"],r["team"],r["id"]):r for line in f if (r:=json.loads(line))["opponent"]=="solution92"}
    losses={(s,t) for (s,t,n),r in idx.items() if n=="flotte" and r["win"]==0}
    assert losses=={(161620068,0),(161620068,1),(161620111,1)}
    env=LuxAIS3GymEnv(numpy_output=True)
    output=[]
    try:
        for seed in sorted({s for s,_ in losses}):
            for team in (0,1):
                source=idx[seed,team,"reference"]
                random.seed(seed)
                torch.manual_seed(seed)
                np.random.seed(seed)
                side=f"player_{team}"
                a=r3_package_agent(side,PACKAGE)
                z=make_opponent("solution92",f"player_{1-team}")
                m=Detail(Record(env),team,a)
                played=play_game(m,a,z,seed,side,False)
                require_no_agent_errors(a,z)
                require(m.digest.hexdigest()==source["action_hash"] and m.matches==source["matches"]
                        and m.first_sight==source["sight"] and m.first_credit==source["credit"]
                        and len(m.rows)==303,"Archived game differs")
                for j,match in enumerate(m.matches):
                    sums=np.asarray([r["points"] for r in m.rows if r["match"]==j+1]).sum(axis=(0,2))
                    require(sums.tolist()==match["points"],"Classified scores differ")
                output.append(dict(seed=seed,team=team,win=played["game_win"],matches=m.matches,rows=m.rows))
    finally:
        env.close()
    content="\n".join(json.dumps(x,separators=(",",":")) for x in output)+"\n"
    (HERE/"verlaeufe.jsonl.gz").write_bytes(gzip.compress(content.encode(),mtime=0))


if __name__=="__main__":
    main()
