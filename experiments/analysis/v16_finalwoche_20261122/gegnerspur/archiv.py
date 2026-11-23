"""Validate a public candidate-tile clue using synchronized archived observations."""
import argparse
from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent / "kurze_sicht"))
from sammeln import ROOT, PACKAGES, sample
from verlauf import public_obs
from scripts.experiment import limit_threads
from scripts.r3_package import r3_package_agent
from luxai_s3.wrappers import LuxAIS3GymEnv

SHIFT = np.array([[0,0],[0,-1],[1,0],[0,1],[-1,0]])


def mirror(xy):
    return 23-xy[1], 23-xy[0]


def pair(xy):
    return min(tuple(xy),mirror(xy))


def run(folder):
    limit_threads()
    tag, reference = PACKAGES["v16"]
    package = ROOT / "experiments/releases" / tag / "agent.zip"
    if sha256(package.read_bytes()).hexdigest()!=reference:
        raise ValueError("Wrong course package")
    engine=LuxAIS3GymEnv(numpy_output=True)
    events=[]
    try:
        for seat in sample():
            seed,side=seat["seed"],seat["side"]
            stock=folder/f"v16_{seed}_{side}.npz"
            meta=json.loads(stock.with_suffix(".json").read_text())
            if meta["seat"]!=seat or sha256(stock.read_bytes()).hexdigest()!=meta["sha256"]:
                raise ValueError("Source commands changed")
            with np.load(stock,allow_pickle=False) as f:
                recorded={k:f[k] for k in f.files}
            _,info=engine.reset(seed=seed)
            cfg=info["params"]
            weights=np.asarray(engine.state.relic_nodes_map_weights)
            schedule=np.asarray(engine.state.relic_spawn_schedule)
            actor=r3_package_agent(side,package)
            actor.new_game(side)
            actor.set_env_cfg(cfg)
            model=actor._imitation
            features=importlib.import_module("sherlock.imitation_agent").featurize
            geo=importlib.import_module("sherlock.geometry")
            team=int(side[-1])
            if int(cfg["unit_sensor_range"])!=seat["sensor"]:
                raise ValueError("Wrong map parameters")
            pending={}
            recorded_pairs=set()
            previous={}
            last_score=0
            for step,commands in enumerate(recorded["commands"]):
                obs=public_obs(recorded,step)
                features(model,obs)
                t=step%101
                if t==0:
                    pending={}
                    previous={}
                    last_score=0
                opp=1-team
                score=int(obs["team_points"][opp])
                gain=score-last_score
                last_score=score
                poss=obs["units"]["position"]
                energy=obs["units"]["energy"]
                live=obs["units_mask"] & (energy>=0)
                enemy={int(u):tuple(map(int,poss[opp,u])) for u in np.flatnonzero(live[opp])}
                history={u:(xy,min(3,previous[u][1]+1) if u in previous and previous[u][0]==xy and gain>0 else 1)
                         for u,xy in enemy.items()}
                previous=history
                if step<101 or not 5<=t<=97: continue
                b=model.belief
                candidates=geo.mirror_map(b.candidate) if b.mirrored else b.candidate
                points=geo.mirror_map(b.point_tiles) if b.mirrored else b.point_tiles
                active=int(np.count_nonzero((schedule>=0)&(schedule<step))//2)
                truth=(weights>0)&(weights<=active)
                if (points & ~truth).any():
                    raise ValueError(f"Oracle disagrees with already confirmed field: {seed}/{side}/{step}")
                if t<=85:
                    for u,(xy,streak) in history.items():
                        target=mirror(xy)
                        canonical=pair(xy)
                        if (streak<3 or xy==target or not candidates[xy] or not candidates[target]
                                or canonical in recorded_pairs):
                            continue
                        possible={pair(q) for q in map(tuple,np.argwhere(candidates))}
                        rate=float(np.mean([truth[q] for q in possible]))
                        r=dict(seed=seed,side=side,step=step,source=list(xy),target=list(target),
                               canonical=[int(a) for a in canonical],true=bool(truth[xy]),pool_rate=rate,available=None)
                        if bool(truth[xy])!=bool(truth[target]): raise ValueError("Map not symmetric")
                        recorded_pairs.add(canonical)
                        pending[canonical]=r
                        events.append(r)
                if not pending: continue
                own=np.flatnonzero(live[team])
                origins={tuple(poss[team,u]) for u in own}
                intended={tuple(poss[team,u]+SHIFT[int(commands[u,0]) if int(commands[u,0])<=4 else 0]) for u in own}
                for canonical,r in list(pending.items()):
                    target=tuple(r["target"])
                    if step-r["step"]>12 or not candidates[target]:
                        del pending[canonical];continue
                    if (not obs["sensor_mask"][target] or target in origins or target in intended or target in enemy.values()
                            or int(obs["map_features"]["tile_type"][target])==2):
                        continue
                    for u in own:
                        place=tuple(poss[team,u])
                        cmd=int(commands[u,0])
                        if (sum(abs(place[i]-target[i]) for i in (0,1))!=1 or cmd>4 or points[place]
                                or energy[team,u]<2*cfg["unit_move_cost"] or points[tuple(poss[team,u]+SHIFT[cmd])]):
                            continue
                        r["available"]=dict(step=step,unit=int(u))
                        del pending[canonical]
                        break
    finally:
        engine.close()
    if len(sample())!=46: raise ValueError("Missing archive controls")
    ranked=sorted(events,key=lambda x:(x["step"],x["side"]))
    unique={}
    available=set()
    for r in ranked:
        k=r["seed"],tuple(r["canonical"])
        unique.setdefault(k,r)
        if r["available"] is not None: available.add(k)
    n=len(unique)
    true=sum(r["true"] for r in unique.values())
    baseline=float(np.mean([r["pool_rate"] for r in unique.values()])) if n else 0.
    maps=len({key[0] for key in unique})
    gates=dict(support=n>=12 and maps>=8, enrichment=n>0 and true/n-baseline>=.15,
               practical=len(available)>=10 and len({k[0] for k in available})>=6)
    result=dict(seats=46, distinct_pairs=n,maps=maps,positive=true,baseline=baseline,
                executable_pairs=len(available),executable_maps=len({k[0] for k in available}),
                gates=gates,eligible=all(gates.values()), events=ranked)
    (HERE/"ergebnis.json").write_text(json.dumps(result,separators=(",",":"),allow_nan=False)+"\n")
    print({k:v for k,v in result.items() if k!="events"},flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("trajectories",type=Path)
    run(p.parse_args().trajectories)
