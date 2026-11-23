"""Run the frozen joint scout on V16's independently proven positive fields."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.ortundflotte.kandidat import JointScout,create as scout
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import load
from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import Knowledge,PACKAGE
from experiments.analysis.relictsuche_20261123.suche_und_wissen.spielen import Audit
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,sha,stamp,write_once
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.r3_package import r3_package_agent
from scripts.par_eval import require_no_agent_errors

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def create(side,name):
    if name=="joint":return scout(side)
    base=r3_package_agent(side,PACKAGE)
    if name=="v16":return base
    know=Knowledge(base)
    if name=="wissen":return know
    assert name=="beide"
    i=json.loads((ROOT/"ortundflotte/valid.json").read_bytes())["selected"]
    return JointScout(know,*load(),i)


def game(env,k,token):
    s,t,name,opp=k
    side=f"player_{t}";rival_side=f"player_{1-t}"
    actor=create(side,name);rival=make_opponent(opp,rival_side) if opp=="solution92" else create(rival_side,opp)
    mon=Audit(env,t,actor,{"joint":"suche"}.get(name,name))
    result=play_game(mon,actor,rival,s,side,False)
    assert mon.turn==303 and mon.sensor==1 and result["game_win"]==int(sum(m["win"] for m in mon.matches)>=2)
    require_no_agent_errors(actor,rival)
    if mon.memory:assert mon.checked==mon.memory.events
    if mon.checked:assert min(e["t"] for e in mon.checked)>=min(mon.first_sight,mon.first_credit+1)
    import base64,zlib
    cmd=np.stack(mon.commands)
    return dict(seed=s,team=t,arm=name,opponent=opp,source=token,win=result["game_win"],matches=mon.matches,
                sight=mon.first_sight,credit=mon.first_credit,hash=mon.digest.hexdigest(),steps=mon.events,proofs=mon.checked,
                tape=base64.b64encode(zlib.compress(cmd.tobytes())).decode())


def read(path):
    with gzip.open(path,"rt") as f:return list(map(json.loads,f))


def archive():
    ref={};short=read(ROOT/"schwere_starts/partien.jsonl.gz")
    for r in short:
        name={"v16":"v16","gemeinsam":"joint","wissen":"wissen"}.get(r["name"])
        if name is not None:ref[r["seed"],r["team"],name]=dict(win=r["win"],matches=r["matches"],hash=r["digest"],steps=r.get("events",[]))
    # The Fallback knowledge arms were already fully played in the corresponding original study.
    for fname in ("partien.jsonl.gz","allgemein_partien.jsonl.gz"):
        for r in read(ROOT/"punktwissen"/fname):
            k=(r["seed"],r["team"],"wissen")
            if (k[0],k[1],"v16") in ref and r["version"]=="neu" and r["opponent"]=="solution92":
                ref[k]=dict(win=r["win"],matches=r["matches"],hash=r["digest"])
    pilot=[r for r in read(ROOT/"ortundflotte/duelle_karten.jsonl.gz") if r["opponent"]=="solution92"]
    tough={r["seed"] for r in pilot if r["id"]=="reference" and not r["win"]}
    for r in pilot:
        if r["seed"] in tough:
            ref[r["seed"],r["team"],{"reference":"v16","scout":"joint"}[r["id"]]]=dict(win=r["win"],matches=r["matches"],hash=r["action_hash"],steps=r["events"])
    seats=sorted({(s,t) for s,t,_ in ref})
    assert len(seats)==20 and len(tough)==3
    return ref,seats,tough


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("folder",type=Path);p.add_argument("op",choices=("play","score"))
    p.add_argument("lane",type=int,nargs="?",default=0);p.add_argument("stride",type=int,nargs="?",default=1);a=p.parse_args();limit_threads()
    ident=stamp({str(f.relative_to(ROOT)):sha(f) for f in (Path(__file__),HERE/"PLAN.md",ROOT/"ortundflotte/duelle.json",
        ROOT/"punktwissen/allgemein.json",ROOT/"ortundflotte/kandidat.py",ROOT/"punktwissen/kandidat.py",ROOT/"schwere_starts/partien.jsonl.gz")})
    table,seats,tough=archive()
    keys=[(s,t,name,"solution92") for s,t in seats for name in ("wissen","beide") if (s,t,name) not in table]
    assert len(keys)==26
    def dest(k):return a.folder/("_".join(map(str,k))+".json")
    if a.op=="play":
        e=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in keys[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                if dest(k).exists():assert json.loads(dest(k).read_bytes())["source"]==ident
                else:write_once(dest(k),game(e,k,ident))
        finally:e.close()
        return
    out=[]
    for k in keys:
        v=json.loads(dest(k).read_bytes());assert v["source"]==ident
        table[k[:3]]=v;out.append(v)
    rows=[]
    for s,t in seats:
        b,j,w,n=[table[s,t,k] for k in ("v16","joint","wissen","beide")]
        if not n["proofs"]:assert j["hash"]==n["hash"] and j["matches"]==n["matches"]
        if not n["steps"]:assert w["hash"]==n["hash"] and w["matches"]==n["matches"]
        rows.append(dict(seed=s,team=t,original=b["win"],joint=j["win"],knowledge=w["win"],both=n["win"],early_rescue=s in tough and j["win"]>b["win"]))
    rescued=sum(r["both"]>r["joint"] for r in rows);lost=sum(r["both"]<r["joint"] for r in rows)
    pres=sum(r["both"] for r in rows if r["early_rescue"]);assert sum(r["early_rescue"] for r in rows)==2
    write_once(HERE/"faelle.json",dict(source=ident,seats=rows,retained=pres,rescued=rescued,lost=lost,passed=pres==2 and rescued>lost))
    blob="\n".join(json.dumps(r,separators=(",",":")) for r in out)+"\n"
    (HERE/"faelle_partien.jsonl.gz").write_bytes(gzip.compress(blob.encode(),mtime=0))


if __name__=="__main__":main()
