"""Repeat every R3/Blend outcome reversal, recording both parents on the actual Blend position."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

BASE="experiments/analysis/r3_v15_blend_20261116"
PINS={"restkarten.json":"d7b1a8ec7501f147d3f4be49ac19d6c511dfd9c659f557fbed8a9b1f75a6df87",
      "rest_r3/games.jsonl":"8895081974aeac1d73247866da042e890d280c7becfd3d2f82a582c6622cf4fe",
      "rest_blend/games.jsonl":"294143115bfcb527d3cddccde8bb2b9882ae163adda67901b36beb14123c2bb5",
      "diagnose/replay.py":"7557844790e86cc358f6cfc2d6a45064082d1aaa20ffdc36c839a98197cfc333",
      "spiele.py":"155fa15c4b0da30dfb5fe1b9d5a4239c9da4836ed3d171fb4b3e4f84a200c863",
      "kombination.py":"46b8c35d8acbfd0126fa4d37c2bff9485121fb8fca8aa982535e2b78cb774468"}


def main(a):
    base=a.repo/BASE
    for f,h in PINS.items():
        if hashlib.sha256((base/f).read_bytes()).hexdigest()!=h:
            raise ValueError(f"Source changed: {f}")
    sys.path[:0]=[str(base),str(base/"diagnose")]
    import spiele
    from replay import Observer,require
    from laufzeit import verify_runtime
    verify_runtime(a.runtime,json.loads((base/"laufzeit.json").read_bytes()))
    spiele.initialize(a.runtime)
    from scripts.r3_v4_contact_agent import routing
    from agents.sherlock.belief import TILE_ASTEROID
    refs={(r["seed"],r["seat"]):r for r in map(json.loads,(base/("rest_"+a.arm)/"games.jsonl").read_bytes().splitlines())}
    cmp=json.loads((base/"restkarten.json").read_bytes())["r3_comparison"]
    keys=sorted(tuple(x) for tag in ("gained","lost") for x in cmp[tag])
    a.out.mkdir(parents=True,exist_ok=True)
    cached={}
    env=spiele.env
    for seed,side in keys:
        agent=spiele.actor(a.arm,side)
        parent=agent.r3 if a.arm=="blend" else agent
        if a.arm=="blend" and not cached:
            # Store copies of the commands actually returned on this observation; do not call a parent twice.
            for name,obj in (("r3",parent),("v15",agent.v4)):
                act=obj.act
                def tap(step,obs,act=act,name=name):
                    world=act(step,obs)
                    cached[name]=(int(step),np.array(world,copy=True))
                    return world
                obj.act=tap
            cached["installed"]=True
        class Fields(Observer):
            def reset(self,**kw):
                obs,info=super().reset(**kw)
                self.move_cost=int(info["params"]["unit_move_cost"])
                return obs,info
            def step(self,orders):
                before=self.obs[side]
                n=len(self.frames)
                live,near=routing(before,self.team)
                asteroid=np.argwhere(parent.belief.tile_type==TILE_ASTEROID)
                if parent.belief.mirrored:
                    asteroid=23-asteroid[:,::-1]
                result=super().step(orders)
                frame=self.frames[-1]
                after=result[0][side]
                energy=np.asarray(after["units"]["energy"])[self.team].reshape(16)
                pos=np.asarray(after["units"]["position"])[self.team]
                mask=np.asarray(after["units_mask"])[self.team] & (energy>=0)
                frame["next_own"]=[[int(u),int(pos[u,0]),int(pos[u,1])] for u in np.flatnonzero(mask)]
                frame["known_asteroids"]=asteroid.tolist()
                if a.arm=="blend":
                    require(all(cached[k][0]==n for k in ("r3","v15")),"Stale parent command")
                    frame["r3_orders"]=cached["r3"][1].tolist()
                    frame["v15_orders"]=cached["v15"][1].tolist()
                    early=1<=n%101<=25 and n>=101
                    use=near | (live & ~near & early)
                    require(np.array_equal(np.where(use[:,None],cached["v15"][1],cached["r3"][1]),orders[side]),"Routing mismatch")
                    frame["contact_uids"]=np.flatnonzero(near).tolist()
                return result
        obs=Fields(env,parent,"r3",side)
        spiele.env=obs
        try: row=spiele.run_one((a.arm,"solution",seed,side))
        finally: spiele.env=env
        ref=refs[seed,side]
        require(row==ref and len(obs.frames)==303,"Mismatching original or incomplete game")
        obj=dict(arm=a.arm,seed=seed,seat=side,expected=ref,actual=row,move_cost=obs.move_cost,sap_range=obs.radius,
                 command_sha256={k:v.hexdigest() for k,v in obs.commands.items()},frames=obs.frames)
        with (a.out/f"{a.arm}-{seed}-{side}.json.gz").open("xb") as f:
            f.write(gzip.compress(json.dumps(obj,separators=(",",":")).encode(),mtime=0))
        print(a.arm,seed,side,row["game_win"],row["our_points"],row["opp_points"],flush=True)
    env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("arm",choices=("r3","blend"))
    for n in ("repo","runtime","out"):
        p.add_argument("--"+n,required=True,type=lambda x:Path(x).resolve())
    main(p.parse_args())
