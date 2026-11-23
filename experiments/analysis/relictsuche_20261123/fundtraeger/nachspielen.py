"""Replay recorded actions only. At the first official sight, isolate the redirected ship's sensor."""
import argparse, base64, gzip, hashlib, json, zlib
from collections import Counter
from pathlib import Path

import jax
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/"sicht1_wiederholung/partien.jsonl.gz"


def tape(r):
    a=np.frombuffer(zlib.decompress(base64.b64decode(r["tape"])),np.int8).reshape(303,2,16,3)
    assert hashlib.sha256(a.astype("<i4").tobytes()).hexdigest()==r["digest"]
    return a


def work(lane,parts):
    rows=[json.loads(l) for l in gzip.decompress(SOURCE.read_bytes()).splitlines()]
    idx={tuple(r["key"]):r for r in rows}
    sample=sorted((s,t) for s,t,arm,op in idx if (arm,op)==("ortundflotte","solution92"))
    assert len(sample)==192
    env=LuxAIS3GymEnv(numpy_output=True)
    @jax.jit
    def visible(state,params,terrain,team,mask):
        limited=state.replace(units_mask=state.units_mask.at[team].set(mask),
                              map_features=state.map_features.replace(tile_type=terrain))
        return env.jax_env.compute_sensor_masks(limited,params).sensor_mask[team]
    out=[]
    try:
        for seed,team in sample[lane::parts]:
            base=idx[seed,team,"v16","solution92"];new=idx[seed,team,"ortundflotte","solution92"]
            a,b=tape(base),tape(new);ts=np.flatnonzero((a!=b).any(axis=(1,2,3)))
            first=int(ts[0]) if len(ts) else None
            uid=None
            if first is not None:
                assert np.array_equal(a[first,1-team],b[first,1-team])
                uid=int(np.flatnonzero((a[first,team]!=b[first,team]).any(1)).item())
            obs,info=env.reset(seed=seed);side=f"player_{team}";assert info["params"]["unit_sensor_range"]==1
            terrain=None;kind=None;sc=others=None;witness=[]
            for t in range(min(new["sight"],100)+1):
                o=obs[side];seen=np.asarray(o["relic_nodes_mask"],bool)
                assert int(o["steps"])==t and bool(seen.any())==(t==new["sight"])
                if seen.any():
                    state=env.state;mask=state.units_mask[team];coords=np.asarray(state.relic_nodes,int);active=np.asarray(state.relic_nodes_mask,bool)
                    def check(m):
                        view=np.asarray(visible(state,env.env_params,terrain,team,m))
                        return view,active&view[tuple(coords.T)]
                    grid,covered=check(mask)
                    assert np.array_equal(grid,o["sensor_mask"]) and np.array_equal(covered,seen)
                    if uid is None or first>=t:
                        kind="vor_eingriff"
                    else:
                        _,single=check((mask*False).at[uid].set(mask[uid]));_,rest=check(mask.at[uid].set(False))
                        # Independent reconstruction via physical Chebyshev power and the real pre-drift nebula.
                        mob=np.asarray(state.units.position)[team];dist=np.abs(mob[:,None,:]-coords[None,:,:]).max(-1)
                        power=(dist<=1).astype(int)+11*(dist==0);power*=np.asarray(mask,bool)[:,None]
                        penalty=(np.asarray(terrain)[tuple(coords.T)]==1)*int(env.env_params.nebula_tile_vision_reduction)
                        assert np.array_equal(single,active&(power[uid]-penalty>0))
                        assert np.array_equal(rest,active&(power.sum(0)-power[uid]-penalty>0))
                        sc,others=bool(single.any()),bool(rest.any())
                        kind={(True,False):"nur_schiff",(False,True):"nur_rest",(True,True):"beide_allein",(False,False):"nur_gemeinsam"}[sc,others]
                        witness=[{"node":int(k),"xy":coords[k].tolist(),"ship":bool(single[k]),"rest":bool(rest[k]),
                                  "individual_uids":np.flatnonzero((power[:,k]-penalty[k])>0).tolist()}
                                 for k in np.flatnonzero(seen)]
                    break
                if t<min(new["sight"],100):
                    terrain=env.state.map_features.tile_type
                    obs,*_=env.step({"player_0":b[t,0],"player_1":b[t,1]})
            if kind is None:
                assert new["sight"]==101
                kind="kein_fund"
            out.append(dict(seed=seed,side=team,first_raw_change=first,uid=uid,sight=new["sight"],original=base["sight"],
                            ship_alone=sc,rest_alone=others,kind=kind,visible_nodes=witness,digest=new["digest"]))
            if len(out)%20==0:print(lane,len(out),flush=True)
    finally:env.close()
    (HERE/f".spur_{lane}.json").write_text(json.dumps(out))


def combine(parts):
    rows=sorted([r for k in range(parts) for r in json.loads((HERE/f".spur_{k}.json").read_bytes())],key=lambda r:(r["seed"],r["side"]))
    assert len(rows)==len({(r['seed'],r['side']) for r in rows})==192
    count={}
    for label,sign in (("frueher",1),("gleich",0),("spaeter",-1)):
        matched=[r for r in rows if np.sign(r["original"]-r["sight"])==sign]
        count[label]={"seats":len(matched),**dict(Counter(r["kind"] for r in matched))}
    assert count["frueher"]["seats"]==57
    payload=b"".join((json.dumps(r,separators=(",",":"))+"\n").encode() for r in rows)
    dump=HERE/"sitze.jsonl.gz";dump.write_bytes(gzip.compress(payload,mtime=0))
    result={"maps":96,"seats":192,"source_sha":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "archive_sha":hashlib.sha256(dump.read_bytes()).hexdigest(),"groups":count}
    (HERE/"ergebnis.json").write_text(json.dumps(result,indent=2)+"\n");print(result)
    for k in range(parts):(HERE/f".spur_{k}.json").unlink()


if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("lane",type=int);ap.add_argument("--parts",default=2,type=int);a=ap.parse_args()
    combine(a.parts) if a.lane<0 else work(a.lane,a.parts)
