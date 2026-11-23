"""Trace both saved games and transfer only verified individual point entries at the next match."""
import gzip
import json
from pathlib import Path
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.ortundflotte.kandidat import create
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor,PACKAGE,sha,write_once
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import point_tile_map

HERE=Path(__file__).resolve().parent


class Boundary(Monitor):
    def __init__(self,env,t,scout,base,extra):
        super().__init__(env,t,"discovery",scout)
        self.locations=[];self.known=None;self.applied=[];self.extra=extra
        act=base.act
        def bridge(step,obs):
            if step==101:
                belief=base._imitation.belief
                belief.observe(obs)
                truth=point_tile_map(env.state)
                if belief.mirrored:truth=truth[::-1,::-1].T
                self.known=dict(points=sorted(int(c) for c in belief._point),true_points=np.flatnonzero(truth).tolist(),
                     dead=len(belief._dead),visible_tiles=int(np.sum(belief.tile_type>=0)))
                self.applied=sorted(set(extra)-belief._point)
                assert set(self.applied)<=set(self.known["true_points"])
                if any(c in belief._dead for c in self.applied):belief.records.clear()
                for c in self.applied:belief._mark_point(c)
                if self.applied:belief._refresh_candidates()
            return act(step,obs)
        base.act=bridge

    def step(self,commands):
        if self.turn<101:
            old=self.old
            pos=np.asarray(old["units"]["position"])[self.team,0]
            self.locations.append(dict(t=self.turn,pos=pos.astype(int).tolist(),cmd=np.asarray(commands[self.side])[0].astype(int).tolist(),
                                       score=int(old["team_points"][self.team]),seen=int(old["sensor_mask"].sum())))
        return super().step(commands)


def play(env,s,t,route,extra=()):
    side=f"player_{t}";rival=make_opponent("solution92",f"player_{1-t}")
    who=create(side) if route else r3_package_agent(side,PACKAGE)
    base=who.base if route else who
    mon=Boundary(env,t,who if route else None,base,extra)
    r=play_game(mon,who,rival,s,side,False);require_no_agent_errors(base,rival)
    assert mon.turn==303 and r["game_win"]==int(sum(m["win"] for m in mon.matches)>=2)
    return dict(hash=mon.digest.hexdigest(),matches=mon.matches,win=r["game_win"],known=mon.known,added=mon.applied,
                sight=mon.first_sight,credit=mon.first_credit,route=mon.events,opening=mon.locations)


def main():
    limit_threads();archive=HERE.parent/"duelle_karten.jsonl.gz"
    with gzip.open(archive,"rt") as f:bank={(r["seed"],r["team"],r["id"]):r for r in map(json.loads,f) if r["opponent"]=="solution92"}
    saved=[(s,t) for s,t,a in bank if a=="scout" and bank[s,t,a]["win"]>bank[s,t,"reference"]["win"]]
    env=LuxAIS3GymEnv(numpy_output=True);cases=[]
    try:
        for s,t in saved:
            controls=[play(env,s,t,flag) for flag in (False,True)]
            for r,k in zip(controls,("reference","scout"),strict=True):
                old=bank[s,t,k];assert r["hash"]==old["action_hash"] and r["matches"]==old["matches"]
            mixed=[]
            for idx in (0,1):
                base,other=controls[idx],controls[1-idx]
                extras=(set(other["known"]["points"])-set(base["known"]["points"]))&set(base["known"]["true_points"])
                if extras:
                    r=play(env,s,t,bool(idx),extras)
                    assert r["opening"]==base["opening"] and r["known"]==base["known"] and r["matches"][0]==base["matches"][0] and set(r["added"])==extras
                else:r=base
                mixed.append(dict(added=sorted(extras),matches=r["matches"],hash=r["hash"],win=r["win"],replayed=bool(extras)))
            cases.append(dict(seed=s,team=t,controls=controls,transfer=mixed))
    finally:env.close()
    assert len(cases)==2
    write_once(HERE/"ergebnis.json",dict(archive=sha(archive),cases=cases))


if __name__=="__main__":main()
