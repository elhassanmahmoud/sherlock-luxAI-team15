"""Replay V16's public observation preprocessing only, then audit prior and newly inferred negatives."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import PACKAGE
from scripts.r3_package import r3_package_agent

HERE=Path(__file__).resolve().parent
XY=np.indices((24,24)).transpose(1,2,0)


def load(folder,meta,key):
    file=folder/meta[key]
    assert hashlib.sha256(file.read_bytes()).hexdigest()==meta[key+"_sha"]
    with np.load(file,allow_pickle=False) as f:
        return {k:f[k] for k in f}


def replay(template,folder,meta,include_judge=True):
    team=meta["team"]
    pub=load(folder,meta,"public")
    obs_names=("units_mask","sensor_mask","team_points","relic_nodes_mask","relic_nodes")
    b=copy.deepcopy(template[team])
    b.reset_game()
    b.sensor_range=int(meta["cfg"]["unit_sensor_range"])
    old=np.zeros((24,24),bool)
    inherited=np.zeros_like(old)
    ever=np.zeros_like(old)
    zero=np.zeros((24,24),np.float32)
    judge=load(folder,meta,"private") if include_judge else None
    maps=[]
    totals=[]
    fseen=set()
    free_seen=set()
    false_points={}
    for t in range(303):
        match,turn=divmod(t,101)
        if turn==0:
            inherited=old.copy()
        obs={k:pub[k][t] for k in obs_names}
        obs.update(steps=t,match_steps=turn,units={k:pub[k][t] for k in ("position","energy")},
                   map_features=dict(energy=zero,tile_type=np.where(obs["sensor_mask"],pub["terrain"][t],-1)))
        b.observe(obs)
        def world(a):
            return a[::-1,::-1].T if b.mirrored else a
        assert np.array_equal(world(b.point_tiles),pub["known_points"][t]),(meta["seed"],team,t,"points")
        assert np.array_equal(world(b.tile_type),pub["terrain"][t]),(meta["seed"],team,t,"terrain")
        dead=world(b.dead_tiles)
        inherited &= dead
        eligible=inherited & world(b.relic_zone)
        if 4<=turn<=88 and turn%4==0:
            ene=pub["energy"][t,team].reshape(-1)
            free=pub["units_mask"][t,team] & (ene>=max(30,4*meta["cfg"]["unit_move_cost"])) & ~pub["protected"][t]
            free &= pub["move_mask"][t,:,1:].any(axis=1) & (pub["commands"][t,:,0]<=4)
            loc=pub["position"][t,team,free]
            near=np.zeros_like(dead)
            for pos in loc:
                near |= np.abs(XY-pos).sum(axis=2)<=4
            reachable=eligible & near
        else:
            reachable=np.zeros_like(dead)
        if judge is not None:
            truth=(judge["weights"]>0)&(judge["weights"]<=judge["active"][t].sum())
            bad=dead&truth
            # The public V16 mask has already matched the archived mask. Its claim can itself be wrong.
            for x,y in np.argwhere(world(b.point_tiles)&~truth):
                xy=min(24*int(x)+int(y),24*(23-int(y))+23-int(x))
                entry=false_points.setdefault(xy,dict(first=t,last=t,ticks=0))
                entry["last"]=t
                if xy==24*int(x)+int(y):
                    entry["ticks"]+=1
            for x,y in np.argwhere(bad):
                fseen.add(min(24*int(x)+int(y),24*(23-int(y))+23-int(x)))
            for x,y in np.argwhere(reachable&truth):
                free_seen.add(min(24*int(x)+int(y),24*(23-int(y))+23-int(x)))
            totals.append([int(m.sum()) for m in (bad,bad&inherited,bad&~inherited,eligible&truth,reachable,reachable&truth)])
        maps.append(np.stack([dead.copy(),inherited.copy(),reachable.copy()]))
        old=dead.copy()
        ever |= dead
    out=dict(seed=meta["seed"],team=team,opponent=meta["opponent"],false_positive_pairs=false_points,unique_wrong=len(fseen),useful=len(free_seen),
             by_match=np.array(totals).reshape(3,101,-1).sum(axis=1).tolist())
    return out,np.packbits(np.array(maps).reshape(303,3,576),axis=-1,bitorder="little")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("archives",type=Path)
    p.add_argument("folder",type=Path)
    p.add_argument("--limit",type=int)
    a=p.parse_args()
    sub=a.archives/"train"
    templates=[r3_package_agent(f"player_{i}",PACKAGE)._imitation.belief for i in (0,1)]
    files=sorted(sub.glob("*.json"))
    assert len(files)==160
    results=[]
    (a.folder/"train").mkdir(exist_ok=True,parents=True)
    for f in files[:a.limit]:
        meta=json.loads(f.read_text())
        target=a.folder/"train"/(f.stem+".npz")
        metrics,bits=replay(templates,sub,meta)
        np.savez_compressed(target,bits=bits)
        results.append(metrics)
    if a.limit:
        print(results,flush=True)
        return
    summary=dict(maps=len(results),with_false_dead=sum(r["unique_wrong"]>0 for r in results),
        with_reachable_true_inherited=sum(r["useful"]>0 for r in results),
        with_false_positive=sum(bool(r["false_positive_pairs"]) for r in results),
        by_match=np.sum([r["by_match"] for r in results],axis=0).tolist())
    summary["passed"]=summary["with_reachable_true_inherited"]>=12
    (HERE/"diagnose.json").write_text(json.dumps(summary,indent=2)+"\n")
    (HERE/"lernkarten.jsonl.gz").write_bytes(gzip.compress(("\n".join(json.dumps(r,separators=(",",":")) for r in results)+"\n").encode(),mtime=0))
    print(summary,flush=True)


if __name__=="__main__":
    main()
