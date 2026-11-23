"""Vier nachträglich ausgewählte Gegenbeispiele. Zusatzmessung bei identischem Ausgang."""
import json
from pathlib import Path

import numpy as np

from eroeffnung import HERE,Capture,MatchComplete,PKG,limit_threads,make_opponent,play_game,r3_package_agent,require_no_agent_errors


class Coverage(Capture):
    def __init__(self,env,side):
        super().__init__(env,side)
        self.union=np.zeros((24,24),dtype=bool)
        self.sample={}
        self.anchors=set()
        self.sightings=set()

    def step(self,actions):
        turn=len(self.frames)
        obs=self.previous
        self.union|=np.asarray(obs["sensor_mask"],dtype=bool)
        real=np.asarray(self.env.state.relic_nodes)[np.asarray(self.env.state.relic_nodes_mask,dtype=bool)]
        self.anchors.update(tuple(map(int,p)) for p in real)
        seen=np.asarray(obs["relic_nodes"])[np.asarray(obs["relic_nodes_mask"],dtype=bool)]
        self.sightings.update(tuple(map(int,p)) for p in seen)
        if turn in (50,70):
            alive=np.asarray(obs["units_mask"])[self.team] & (np.asarray(obs["units"]["energy"])[self.team].reshape(-1)>=0)
            units=np.asarray(obs["units"]["position"])[self.team][alive]
            self.sample[turn]=dict(coverage=int(self.union.sum()),ships=units.astype(int).tolist())
        return super().step(actions)


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    raw=[r for lane in (0,1) for r in map(json.loads,(HERE/f"teil_{lane}.jsonl").read_text().splitlines())]
    result=[]
    env=LuxAIS3GymEnv(numpy_output=True)
    for seed in (160394013,160394018):
        for arm in ("v16","kaggle3"):
            ref=next(r for r in raw if r["seed"]==seed and r["side"]=="player_1" and r["arm"]==arm)
            agent=r3_package_agent("player_1",PKG) if arm=="v16" else make_opponent(arm,"player_1")
            enemy=make_opponent("solution92","player_0")
            cap=Coverage(env,"player_1")
            try:
                play_game(cap,agent,enemy,seed,"player_1",False)
            except MatchComplete:
                pass
            require_no_agent_errors(agent,enemy)
            f=cap.frames
            comparison=dict(frames=len(f),first_relic=next((r["turn"] for r in f if r["visible"]),None),
                            first_own_score=next((r["turn"] for r in f if r["after"][0]),None),
                            after_70=f[70]["after"],match_score=f[100]["after"],match_win=cap.win)
            if any(ref[k]!=v for k,v in comparison.items()) or len(cap.anchors)!=2 or not cap.sightings<=cap.anchors:
                raise ValueError("Zusatzmessung weicht vom Match ab oder Reliktpaar uneindeutig")
            measurements={}
            for t,r in cap.sample.items():
                distances=[abs(x-p)+abs(y-q) for x,y in r["ships"] for p,q in cap.anchors]
                if not distances: raise ValueError("Keine lebenden Schiffe am Messpunkt")
                measurements[t]={**r,"nearest_relic_l1":min(distances)}
            result.append(dict(seed=seed,arm=arm,side="player_1",anchors=sorted(cap.anchors),seen=sorted(cap.sightings),
                               observations=measurements,verified=ref))
            print(seed,arm,[(t,r["coverage"],r["nearest_relic_l1"]) for t,r in measurements.items()],flush=True)
    (HERE/"suchweg.json").write_text(json.dumps(result,indent=2)+"\n")
    env.close()


if __name__=="__main__":
    main()
