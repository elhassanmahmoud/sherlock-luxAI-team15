"""Observe the original point-mark routine without intercepting or changing any of its decisions."""
import argparse
import gzip
import hashlib
import inspect
import json
from pathlib import Path

import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor,PACKAGE,sha,write_once
from scripts.r3_package import r3_package_agent
from scripts.common import make_opponent,play_game
from scripts.scoring import point_tile_map
from scripts.par_eval import require_no_agent_errors
from scripts.experiment import limit_threads

HERE=Path(__file__).resolve().parent


class Observed:
    def __init__(self,brain,env):
        self.brain=brain
        self.env=env
        self.false_calls=[]
        self.seen=set()
        self.total=0
        self.occupied_ticks=0
        self.own=[]
        self.wrong_occupied=[]
        self.tick=-1

    def __getattr__(self,k):return getattr(self.brain,k)

    def new_game(self,side=None):
        self.brain.new_game(side)
        b=self.brain._imitation.belief
        original=b._mark_point
        def mark(f):
            q=int(f)
            world=b._mirror_idx(q) if b.mirrored else q
            key=min(world,b._mirror_idx(world))
            if not self.truth[divmod(world,24)] and key not in self.seen:
                self.seen.add(key)
                call=inspect.currentframe().f_back
                trace=[]
                while call is not None and len(trace)<9:
                    name=call.f_code.co_name
                    info={}
                    for n in ("rest","gain","known","match_step","k","required","target"):
                        v=call.f_locals.get(n)
                        if isinstance(v,(int,np.integer)):info[n]=int(v)
                    for n in ("unknown","occupied","tiles","fields","remaining","record","rec","cells"):
                        v=call.f_locals.get(n)
                        if isinstance(v,(set,list,tuple)) and len(v)<=32 and all(isinstance(i,(int,np.integer)) for i in v):
                            info[n]=list(map(int,v))
                    trace.append(dict(routine=name,locals=info))
                    if name=="act":break
                    call=call.f_back
                actual=self.obs
                team=self.brain.team_id
                rows=[]
                for xy in sorted({tuple(map(int,p)) for p in np.asarray(actual["units"]["position"][team])[np.asarray(actual["units_mask"][team],bool)&(np.asarray(actual["units"]["energy"][team]).reshape(-1)>=0)]}):
                    fxy=xy[0]*24+xy[1]
                    cell=b._mirror_idx(fxy) if b.mirrored else fxy
                    rows.append(dict(world=fxy,native=cell,point=bool(self.truth[xy]),was_dead=bool(cell in b._dead),was_known=bool(cell in b._point)))
                self.false_calls.append(dict(t=self.tick,world=world,native=q,canonical_pair=key,trace=trace,
                    observed=rows,public_points=np.asarray(actual["team_points"]).tolist(),records=[(list(flds),int(cnt)) for flds,cnt in b.records],
                    stable=bool(b._stable(self.tick%101)),known_pairs=int(b.known_pairs()),active_pairs=int(np.asarray(self.env.state.relic_nodes_mask).sum()//2)))
            return original(f)
        b._mark_point=mark

    def act(self,step,obs):
        t=step
        self.tick=t;self.obs=obs
        self.truth=point_tile_map(self.env.state)
        cmd=self.brain.act(t,obs)
        self.own.append(cmd.copy())
        b=self.brain._imitation.belief
        point=b.point_tiles[::-1,::-1].T if b.mirrored else b.point_tiles
        wrong=point & ~self.truth
        self.total+=int(wrong.any())
        team=self.brain.team_id
        live=np.asarray(obs["units_mask"][team],bool)&(np.asarray(obs["units"]["energy"][team]).reshape(-1)>=0)
        for uid in np.flatnonzero(live):
            pos=tuple(np.asarray(obs["units"]["position"][team,uid]).tolist())
            if wrong[pos]:
                self.occupied_ticks+=1
                self.wrong_occupied.append((t,int(uid),pos,int(cmd[uid,0])))
        return cmd


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive",type=Path)
    a=p.parse_args()
    with gzip.open(HERE.parent/"punktwissen/partien.jsonl.gz","rt") as f:
        known=next(r for r in map(json.loads,f) if r["seed"]==162640027 and r["team"]==1 and r["version"]=="v16" and r["opponent"]=="solution92")
    env=LuxAIS3GymEnv(numpy_output=True)
    limit_threads()
    output=[]
    try:
        for s,t in ((162000169,1),(162000431,0),(162640027,1)):
            anchor=known if s==known["seed"] else json.loads((a.archive/"train"/f"{s}-{t}.json").read_text())
            opp=anchor["opponent"]
            torch.manual_seed(s);side=f"player_{t}";other=f"player_{1-t}"
            actor=Observed(r3_package_agent(side,PACKAGE),env)
            rival=make_opponent(opp,other) if opp=="solution92" else r3_package_agent(other,PACKAGE)
            mon=Monitor(env,t,"discovery")
            result=play_game(mon,actor,rival,s,side,False)
            require_no_agent_errors(actor.brain,rival)
            assert result["game_win"]==anchor["win"] and actor.false_calls
            if s==known["seed"]:
                assert mon.digest.hexdigest()==known["digest"] and mon.matches==known["matches"] and actor.total==37
            else:
                data=a.archive/"train"/anchor["public"]
                assert sha(data)==anchor["public_sha"]
                with np.load(data) as r:assert np.array_equal(np.stack(actor.own),r["commands"])
                assert [m["points"] if t==0 else m["points"][::-1] for m in mon.matches]==anchor["matches"]
            output.append(dict(seed=s,team=t,opp=opp,win=result["game_win"],hash=mon.digest.hexdigest(),matches=mon.matches,
                               ticks=actor.total,occupied=actor.occupied_ticks,occupancies=actor.wrong_occupied,errors=actor.false_calls))
    finally:env.close()
    write_once(HERE/"ursachen.json",dict(original=sha(PACKAGE),cases=output))


if __name__=="__main__":main()
