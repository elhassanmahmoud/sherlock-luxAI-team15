"""Replay 14 archived originals and run three fixed search policies on the identical seeds and seats."""
import argparse
import base64
from datetime import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import zlib

import numpy as np
import torch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
from experiments.analysis.relictsuche_20261123.ortundflotte.kandidat import create as joint
from experiments.analysis.relictsuche_20261123.spaetsuche.kandidat import create as late
from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import create as prior
from experiments.analysis.relictsuche_20261123.punktwissen.spiele import decoded
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,THREADS,PACKAGE,Monitor,common_source,require,sha,stamp,write_once
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import point_tile_map

D=HERE.parent
WORK=Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/schwere_starts")
FACTORIES={"v16":None,"ort":prior,"gemeinsam":joint,"spaet":late}
ARCH=[D/"punktwissen/partien.jsonl.gz",D/"punktwissen/allgemein_partien.jsonl.gz"]
DEPS={
    "punktwissen":["kandidat.py","spiele.py","allgemein.py"],
    "punktspeicher":["beweise.py"],"zielschaetzer":["kandidat.py","ort.json"],
    "routenlernen":["kandidat.py","routes.py","routengewichte.json"],
    "flottenblick":["kandidat.py","flotte.py","vorhersage.py","flottengewichte.npz","modell.json"],
    "ortundflotte":["kandidat.py","richtung.py","valid.json"],"spaetsuche":["kandidat.py","modell.json"]
}


def original_rows():
    idx={}
    for f in ARCH:
        with gzip.open(f,"rt") as stream:
            for r in map(json.loads,stream):
                if r["opponent"]!="solution92" or r["sensor"]!=1:continue
                k=(r["seed"],r["team"],r["version"])
                require(k not in idx,"Duplicate source seat")
                idx[k]=r
    losses=sorted((s,t) for (s,t,k),r in idx.items() if k=="v16" and not r["win"])
    cards=sorted({s for s,t in losses})
    require(len(losses)==8 and len(cards)==7,"Unexpected source selection")
    selected={(s,t,v):idx[s,t,v] for s in cards for t in (0,1) for v in ("v16","neu")}
    for (s,t,v),r in selected.items():
        a=decoded(r)
        require(a.shape==(303,2,16,3) and hashlib.sha256(a.astype("<i4").tobytes()).hexdigest()==r["digest"]
                and int(sum(m["win"] for m in r["matches"])>=2)==r["win"],"Broken original tape")
        if v=="neu" and not r["events"]:
            baseline=selected[s,t,"v16"]
            require(r["digest"]==baseline["digest"] and r["matches"]==baseline["matches"],"Inactive knowledge not original")
    return losses,cards,selected


def sources():
    files=[D/s/f for s,ns in DEPS.items() for f in ns]+[HERE/"PLAN.md",Path(__file__),*ARCH]
    return dict(common=common_source(),files={str(f.relative_to(ROOT)):sha(f) for f in files})


class Trace(Monitor):
    def __init__(self,env,team,actor,base):
        super().__init__(env,team,"discovery",actor)
        self.base_for_review=base
        self.tape=[]
        self.profile=[]

    def step(self,acts):
        self.tape.append(np.stack([acts[f"player_{i}"] for i in (0,1)]).astype(np.int8))
        brain=self.base_for_review._imitation.belief
        point=brain.point_tiles
        zone=brain.relic_zone
        if self.team:
            point=point[::-1,::-1].T
            zone=zone[::-1,::-1].T
        old=self.old
        seen_relic=bool(np.any(old["relic_nodes_mask"]))
        out=super().step(acts)
        st=out[4]["final_state"]
        grid=point_tile_map(st)
        pos=np.asarray(st.units.position)
        alive=np.asarray(st.units_mask,bool)&(np.asarray(st.units.energy)[...,0]>=0)
        entry=[]
        for team in (self.team,1-self.team):
            xy=np.unique(pos[team][alive[team]],axis=0)
            tiles=sorted(int(x)*24+int(y) for x,y in xy if grid[x,y])
            known=sum(bool(point[divmod(k,24)]) for k in tiles)
            possible=sum(bool(zone[divmod(k,24)]) for k in tiles)
            entry.append(dict(actual=tiles,known=known,in_zone=possible,live=int(alive[team].sum())))
        self.profile.append(dict(scores=entry,visible_relic=seen_relic,visible_cells=int(np.asarray(old["sensor_mask"]).sum())))
        return out


def play_one(env,key,source,original):
    seed,team,name=key
    side=f"player_{team}";other=f"player_{1-team}"
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    acting=FACTORIES[name](side) if FACTORIES[name] else r3_package_agent(side,PACKAGE)
    base=acting.base if name!="v16" else acting
    enemy=make_opponent("solution92",other)
    m=Trace(env,team,acting if name!="v16" else None,base)
    outcome=play_game(m,acting,enemy,seed,side,False)
    require_no_agent_errors(base,enemy)
    arr=np.stack(m.tape)
    require(m.sensor==1 and m.turn==303 and m.counts==[303,303] and len(m.matches)==3 and
            sum(v["win"] for v in m.matches)==outcome["our_wins"] and int(outcome["our_wins"]>=2)==outcome["game_win"],"Incomplete game")
    for j,mt in enumerate(m.matches):
        expected=[sum(len(r["scores"][i]["actual"]) for r in m.profile[j*101:(j+1)*101]) for i in (0,1)]
        require(expected==mt["points"],"Occupation does not explain match score")
    require(hashlib.sha256(arr.astype("<i4").tobytes()).hexdigest()==m.digest.hexdigest(),"Command packing")
    if name=="v16" or not m.events:
        require(np.array_equal(arr,decoded(original)) and original["digest"]==m.digest.hexdigest()
                and m.matches==original["matches"] and original["sight"]==m.first_sight and original["credit"]==m.first_credit,
                "Original repeat or inactive policy differs from archive")
    else:
        early=m.events[0][0];raw=decoded(original)
        require(np.array_equal(arr[:early],raw[:early]) and np.array_equal(arr[early,1-team],raw[early,1-team]),
                "Actions changed prior to the first intervention")
    return dict(seed=seed,team=team,name=name,source=source,env_sensor=m.sensor,sight=m.first_sight,credit=m.first_credit,
        wins=outcome["our_wins"],win=outcome["game_win"],matches=m.matches,events=m.events,
        choice=getattr(acting,"choice",None) if name=="spaet" else None,profile=m.profile,
        digest=m.digest.hexdigest(),tape=base64.b64encode(zlib.compress(arr.tobytes())).decode(),
        steps=m.turn,actions_checked=m.counts,caught_errors=[0,0])


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("mode",choices=("play","collect"))
    p.add_argument("--lane",type=int,default=0);p.add_argument("--stride",type=int,default=2)
    a=p.parse_args()
    require(0<=a.lane<a.stride and os.getenv("PYTHONHASHSEED")=="0" and all(os.getenv(k)=="1" for k in THREADS),"Process settings")
    limit_threads()
    lost,cards,arch=original_rows();src=sources();sig=stamp(src)
    case=dict(losses=[list(x) for x in lost],cards=cards,source=src,identity=sig)
    write_once(WORK/"manifest.json",case)
    jobs=[(s,t,k) for s in cards for t in (0,1) for k in FACTORIES]
    fn=lambda k:WORK/"spiele"/("_".join(map(str,k))+".json")
    if a.mode=="play":
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in jobs[a.lane::a.stride]:
                f=fn(k)
                if f.exists():
                    require(json.loads(f.read_bytes())["source"]==sig,"Different input");continue
                require(datetime.now(CUTOFF.tzinfo)<CUTOFF,"Deadline")
                row=play_one(env,k,sig,arch[k[0],k[1],"v16"])
                write_once(f,row);print(*k,flush=True)
        finally:env.close()
        require(sources()==src,"Sources changed");return
    require(set((WORK/"spiele").glob("*.json"))=={fn(k) for k in jobs},"Incomplete selected panel")
    rows=[json.loads(fn(k).read_bytes()) for k in jobs]
    require(all(r["source"]==sig for r in rows),"Source identity mismatch")
    blob=b"".join(json.dumps(r,sort_keys=True,separators=(",",":")).encode()+b"\n" for r in rows)
    dest=HERE/"partien.jsonl.gz"
    if not dest.exists():dest.write_bytes(gzip.compress(blob,mtime=0))
    require(gzip.decompress(dest.read_bytes())==blob,"Bad game archive")
    write_once(HERE/"manifest.json",case)
    print(len(rows),sha(dest),flush=True)


if __name__=="__main__":main()
