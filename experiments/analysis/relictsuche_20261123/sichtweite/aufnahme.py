"""Measure available additional public point knowledge while the untouched original V16 controls every command."""
import argparse
from datetime import datetime
import json
from pathlib import Path

import numpy as np
import torch

from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import Evidence, MIRROR, indices
from experiments.analysis.relictsuche_20261123.punktwissen.spiele import PACKAGE
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF, Monitor, common_source, sha, stamp, write_once
from scripts.r3_package import r3_package_agent
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.scoring import point_tile_map

HERE=Path(__file__).resolve().parent


def roster(start):
    import jax
    pool=np.arange(start,start+1000,dtype=np.int32)
    levels=np.asarray(jax.jit(jax.vmap(sensor))(pool))
    candidates=[(int(s),int(level),i) for level in (2,3,4) for i,s in enumerate(pool[levels==level][:24])]
    assert len(candidates)==len({s for s,_,_ in candidates})==72
    return sorted(candidates)


class Passive(Monitor):
    def __init__(self,env,team,brain):
        super().__init__(env,team,"general")
        self.brain=brain
        self.proof=Evidence()
        self.opportunities={}
        self.longest={}
        self.total_missing=0
        self.records=[]

    def step(self,acts):
        t=self.turn
        team=self.team
        obs=self.old
        loc=np.asarray(obs["units"]["position"][team])
        energy=np.asarray(obs["units"]["energy"][team]).reshape(-1)
        alive=np.asarray(obs["units_mask"][team],bool)&(energy>=0)
        occupied={int(x)*24+int(y) for x,y in loc[alive]}
        self.proof.observe(dict(step=t,ms=t%101,occupied=occupied,points=int(obs["team_points"][team]),
                    epoch_seen=bool(np.asarray(obs["relic_nodes_mask"])[[t//101,t//101+3]].any())))
        b=self.brain._imitation
        points=(b.belief.point_tiles[::-1,::-1].T if team else b.belief.point_tiles).ravel()
        truth=point_tile_map(self.env.state).ravel()
        fs=list(indices(self.proof.positive))
        assert all(truth[f] and truth[MIRROR[f]] for f in fs)
        missing=[f for f in fs if not points[f] and not points[MIRROR[f]]]
        self.total_missing+=len(missing)
        protected=np.ones(16,bool)
        if b.last_fz is not None:
            from sherlock.features import FEATURE_NAMES
            _,ids,feats,masks,_,_,_=b.last_fz
            point_cols=[FEATURE_NAMES.index(k+"_point") for k in "curdl"]
            protected[np.asarray(ids,int)]=(feats[:,point_cols].max(1)>0)|(feats[:,FEATURE_NAMES.index("enemies_in_sap")]>0)|~masks[:,1:5].any(1)
        free=alive & ~protected & (energy>=30) & (np.asarray(acts[self.side])[:,0]<5)
        near=set()
        if free.any():
            for f in missing:
                for end in {f,MIRROR[f]}-occupied:
                    if np.abs(loc[free]-divmod(end,24)).sum(1).min()<=4:
                        near.add(f)
        for f in list(self.opportunities):
            if f not in near or t%101==0:
                self.opportunities.pop(f)
        for f in near:
            first=self.opportunities.setdefault(f,t)
            self.longest[f]=max(self.longest.get(f,0),t-first+1)
            if t-first==3:
                self.records.append(dict(first=first,field=f,match=t//101+1))
        return super().step(acts)


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path);p.add_argument("stage",choices=("play","score"))
    p.add_argument("lane",type=int,nargs="?",default=0);p.add_argument("stride",type=int,nargs="?",default=1)
    a=p.parse_args()
    token=stamp(dict(base=common_source(),files={str(f.relative_to(HERE.parent)):sha(f) for f in
                (HERE/"aufnahme.py",HERE/"PLAN.md",HERE.parent/"punktspeicher/beweise.py")}))
    choices=roster(163300000)
    def path(s):
        return a.folder/"roh"/f"{s}.json"
    if a.stage=="play":
        limit_threads()
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for seed,level,i in choices[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                out=path(seed)
                if out.exists():
                    assert json.loads(out.read_text())["source"]==token
                    continue
                team=(i//2)%2
                side=f"player_{team}";other=f"player_{1-team}"
                opp=("solution92","v16")[i%2]
                torch.manual_seed(seed)
                actor=r3_package_agent(side,PACKAGE)
                rival=make_opponent(opp,other) if opp=="solution92" else r3_package_agent(other,PACKAGE)
                watch=Passive(env,team,actor)
                result=play_game(watch,actor,rival,seed,side,False)
                require_no_agent_errors(actor,rival)
                assert watch.turn==303 and watch.sensor==level and result["our_wins"]==sum(q["win"] for q in watch.matches)
                write_once(out,dict(source=token,seed=seed,team=team,level=level,opponent=opp,hash=watch.digest.hexdigest(),
                           matches=watch.matches,total_missing=watch.total_missing,accessible=watch.records))
        finally:
            env.close()
        return
    rows=[json.loads(path(s).read_text()) for s,_,_ in choices]
    assert all(r["source"]==token for r in rows)
    levels={n:dict(cards=sum(r["level"]==n and bool(r["accessible"]) for r in rows),
                   extra_cards=sum(r["level"]==n and r["total_missing"]>0 for r in rows)) for n in (2,3,4)}
    n=sum(x["cards"] for x in levels.values())
    good=n>=6 and sum(x["cards"]>0 for x in levels.values())>=2
    write_once(HERE/"reichweite.json",dict(source=token,cards=len(rows),levels=levels,usable=n,passed=bool(good),rows=rows))
    print(levels,good)


if __name__=="__main__":
    main()
