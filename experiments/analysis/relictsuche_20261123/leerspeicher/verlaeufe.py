"""Measure both V16 belief modes under identical original actions and verify each archived public snapshot."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

from experiments.analysis.relictsuche_20261123.leerspeicher.kandidat import switch,PACKAGE
from experiments.analysis.relictsuche_20261123.nullwissen.gedaechtnis import load,XY
from scripts.r3_package import r3_package_agent

HERE=Path(__file__).resolve().parent


def one(template,folder,meta):
    team=meta["team"]
    pub=load(folder,meta,"public")
    judge=load(folder,meta,"private")
    two=[copy.deepcopy(template[team]) for _ in range(2)]
    for b in two:
        b.reset_game()
        b.sensor_range=1
        assert b.keep_dead_fast and not b.keep_dead
    zero=np.zeros((24,24),np.float32)
    table=[]
    samples=[]
    m1hash=hashlib.sha256()
    def world(arr):
        return arr[::-1,::-1].T if team else arr
    for t in range(303):
        match,ms=divmod(t,101)
        if t==101:
            switch(two[1])
        obs={k:pub[k][t] for k in ("units_mask","sensor_mask","team_points","relic_nodes_mask","relic_nodes")}
        obs.update(steps=t,match_steps=ms,units={k:pub[k][t] for k in ("position","energy")},
                   map_features=dict(energy=zero,tile_type=np.where(obs["sensor_mask"],pub["terrain"][t],-1)))
        for b in two:
            b.observe(obs)
        assert np.array_equal(world(two[0].point_tiles),pub["known_points"][t])
        assert all(np.array_equal(world(b.tile_type),pub["terrain"][t]) for b in two)
        point=[world(b.point_tiles) for b in two]
        dead=[world(b.dead_tiles) for b in two]
        if not match:
            assert np.array_equal(point[0],point[1]) and np.array_equal(dead[0],dead[1])
            m1hash.update(np.packbits(point[0]).tobytes()+np.packbits(dead[0]).tobytes())
        actual=(judge["weights"]>0)&(judge["weights"]<=judge["active"][t].sum())
        def counts(p,d):
            return [int(x.sum()) for x in (p&actual,p&~actual,d&actual,d&~actual)]
        extra=(point[1]&~point[0]&actual)
        lost=(point[0]&~point[1]&actual)
        close=np.zeros_like(extra)
        if (extra|lost).any():
            ene=pub["energy"][t,team].reshape(-1)
            free=obs["units_mask"][team]&(ene>=max(30,4*meta["cfg"]["unit_move_cost"]))&~pub["protected"][t]
            free &= pub["move_mask"][t,:,1:].any(1)&(pub["commands"][t,:,0]<=4)
            for xy in pub["position"][t,team,free]:
                close |= np.abs(XY-xy).sum(2)<=4
        added=int((extra&close).sum())
        removed=int((lost&close).sum())
        if added or removed:
            samples.append([t,added,removed])
        table.append(counts(point[0],dead[0])+counts(point[1],dead[1])+[added,removed])
    return dict(seed=meta["seed"],team=team,opponent=meta["opponent"],m1=m1hash.hexdigest(),
                phases=np.array(table).reshape((3,101,10)).sum(axis=1).tolist(),near=samples)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("stage",choices=("train","valid"))
    a=p.parse_args()
    if a.stage=="valid":
        assert json.loads((HERE/"train.json").read_text())["passed"]
    folder=a.source/a.stage
    files=sorted(folder.glob("*.json"))
    assert len(files)==dict(train=160,valid=48)[a.stage]
    base=[r3_package_agent(f"player_{q}",PACKAGE)._imitation.belief for q in (0,1)]
    rows=[one(base,folder,json.loads(f.read_text())) for f in files]
    assert len({r["seed"] for r in rows})==len(rows)
    a3=np.array([r["phases"] for r in rows])
    total=a3.sum(axis=(0,1))
    near=(a3[:,:,8].sum(1)>0)
    net=(a3[:,:,8]-a3[:,:,9]).sum(1)
    draw=np.random.default_rng(231123).integers(0,len(rows),(20000,len(rows)))
    checks=dict(fewer_false_zero=total[6]<=.2*total[2],correct_positive=total[5]<=total[1],
        enough_new_reachable=near.sum()>=(12 if a.stage=="train" else 4),levels=total[4]>=.99*total[0])
    sumry=dict(cards=len(rows),summary=total.tolist(),phases=a3.sum(axis=0).tolist(),near_maps=int(near.sum()),
        mean_net_near=float(net.mean()),ci95=np.percentile(net[draw].mean(1),[2.5,97.5]).tolist(),
        gates={k:bool(v) for k,v in checks.items()},passed=bool(all(checks.values())))
    (HERE/(a.stage+".json")).write_text(json.dumps(sumry,indent=2)+"\n")
    (HERE/(a.stage+"_karten.jsonl.gz")).write_bytes(gzip.compress(("\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n").encode(),mtime=0))
    print(sumry,flush=True)


if __name__=="__main__":
    main()
