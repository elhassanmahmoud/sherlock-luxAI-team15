"""Replay identical archived commands and count physical points on the first newly certified pair(s)."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path

import numpy as np

from spiele import HERE, board_seeds, decoded, keys, paired, path, frozen, write_once, MIRROR
from scripts.scoring import match_points_after_step, point_tile_map


def targets(row):
    t=row["events"][0]["t"]
    fields={f for e in row["events"] if e["t"]==t for f in (e["world"],MIRROR[e["world"]])}
    return t,fields


def replay(env,row,team,since,fields):
    game,_=env.reset(seed=row["seed"])
    counts=[]
    totals=[]
    actual=decoded(row)
    side=f"player_{team}"
    for tick,commands in enumerate(actual):
        obs=game[side]
        game,_,done,trunc,info=env.step({"player_0":commands[0].astype(int),"player_1":commands[1].astype(int)})
        end=game[side]
        if tick%101==100:
            score=match_points_after_step(obs,end,info)
            totals.append([int(score[team]),int(score[1-team])])
        assert bool(done[side]) or bool(trunc[side]) or tick<302
        if tick<since:
            continue
        s=info["final_state"]
        positive=point_tile_map(s)
        assert all(positive[divmod(f,24)] for f in fields)
        result=[]
        for who in (team,1-team):
            pos=np.asarray(s.units.position)[who]
            live=np.asarray(s.units_mask)[who] & (np.asarray(s.units.energy)[who,:,0]>=0)
            controlled={int(x)*24+int(y) for x,y in pos[live]}
            result.append(len(controlled&fields))
        counts.append(result)
    expect=[m["points"] if row["team"]==team else m["points"][::-1] for m in row["matches"]]
    assert totals==expect
    return np.array(counts)


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.experiment import limit_threads
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    a=p.parse_args()
    assert (HERE/"ergebnis.json").exists() and json.loads((HERE/"ergebnis.json").read_text())["source"]==frozen()
    limit_threads()
    env=LuxAIS3GymEnv(numpy_output=True)
    rows=[]
    try:
        for k in keys():
            s,t,variant,opp=k
            if variant!="neu":
                continue
            c=json.loads(path(a.folder,k).read_text())
            if not c["events"]:
                continue
            r=json.loads(path(a.folder,(s,0 if opp=="v16" else t,"v16",opp)).read_text())
            tick,fields=targets(c)
            first=paired(r,c,selfplay=opp=="v16")
            if first is None:
                rows.append(dict(seed=s,team=t,opponent=opp,t=tick,fields=sorted(fields),first=None,delta4=[0,0],delta12=[0,0],delta_all=[0,0]))
                continue
            x=replay(env,c,t,tick,fields)
            y=replay(env,r,t,tick,fields)
            diff=x-y
            rows.append(dict(seed=s,team=t,opponent=opp,t=tick,fields=sorted(fields),first=first,
                delta4=diff[:4].sum(axis=0).tolist(),delta12=diff[:12].sum(axis=0).tolist(),delta_all=diff.sum(axis=0).tolist(),
                original=y.sum(axis=0).tolist(),candidate=x.sum(axis=0).tolist()))
    finally:
        env.close()
    rng=np.random.default_rng(231123)
    seeds=board_seeds()
    take=rng.integers(0,len(seeds),(20000,len(seeds)))
    groups={}
    for opp in ("solution92","v16"):
        subset=[r for r in rows if r["opponent"]==opp]
        amounts={}
        for field in ("delta4","delta12","delta_all"):
            permap=np.zeros((len(seeds),2),float)
            for r in subset:
                permap[seeds.index(r["seed"])]+=np.asarray(r[field])/2
            net=permap[:,0]-permap[:,1]
            amounts[field]=dict(sum=(2*permap.sum(axis=0)).astype(int).tolist(),mean_net=float(net.mean()),
                                ci95=np.percentile(net[take].mean(axis=1),[2.5,97.5]).tolist())
        groups[opp]=dict(evidence_seats=len(subset),changed=sum(r["first"] is not None for r in subset),windows=amounts)
    write_once(HERE/"feldwirkung.json",groups)
    payload="\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n"
    (HERE/"feldwirkung_karten.jsonl.gz").write_bytes(gzip.compress(payload.encode(),mtime=0))
    print(groups,flush=True)


if __name__=="__main__":
    main()
