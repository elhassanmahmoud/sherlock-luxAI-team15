"""Check all public calls against the actual points on each archived game before admitting live play."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.punktgrenzen.grenzen import PublicBounds,public_row
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import Evidence,MIRROR,indices
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,stamp,write_once

HERE=Path(__file__).resolve().parent
SOURCES=[HERE/n for n in ("PLAN.md","grenzen.py","archiv.py")]+[HERE.parent/"punktspeicher/beweise.py"]


def bits(x):
    return int.from_bytes(np.packbits(np.asarray(x).ravel(),bitorder="little").tobytes(),"little")


def read(meta,folder,key,fields):
    file=folder/meta[key]
    assert sha(file)==meta[key+"_sha"]
    with np.load(file) as data:
        return {n:data[n] for n in fields}


def check(file,token):
    meta=json.loads(file.read_text())
    team=meta["team"]
    p=read(meta,file.parent,"public",("position","energy","units_mask","team_points","relic_nodes_mask","relic_nodes",
                                        "known_points","move_mask","commands","protected"))
    ref=read(meta,file.parent,"private",("weights","active"))
    truths={n:bits((ref["weights"]>0)&(ref["weights"]<=n)) for n in range(4)}
    baseline=Evidence()
    models={k:PublicBounds(e,g) for k,e,g in (("enemy",True,False),("zones",False,True),("both",True,True))}
    pending={k:{} for k in models}
    opportunities={k:[] for k in models}
    totals={k:[0,0] for k in models}
    for t in range(303):
        row=public_row(t,team,p["position"][t],p["energy"][t],p["units_mask"][t],p["team_points"][t],
                       p["relic_nodes_mask"][t],p["relic_nodes"][t])
        baseline.observe(row)
        truth=truths[int(ref["active"][t].sum())]
        public_known=bits(p["known_points"][t])
        own=set(row["occupied"])
        free=p["units_mask"][t,team] & ~p["protected"][t] & (p["energy"][t,team]>=30)
        free &= p["move_mask"][t,:,1:5].any(1)&(p["commands"][t,:,0]<5)
        loc=p["position"][t,team,free]
        for name,m in models.items():
            m.observe(row)
            assert not (m.positive&~truth or m.negative&truth) and baseline.positive&~m.positive==0
            delta=m.positive&~baseline.positive
            raw=[f for f in indices(delta) if not((public_known>>f)&1 or (public_known>>MIRROR[f])&1)]
            totals[name][0]+=delta.bit_count()
            totals[name][1]+=len(raw)
            history=pending[name]
            for f in list(history):
                if f not in raw or not t%101:
                    opportunities[name].append(history.pop(f))
            for f in raw:
                if f not in history:
                    ends={f,MIRROR[f]}-own
                    distance=min((int(np.abs(loc-divmod(e,24)).sum(1).min()) for e in ends),default=99) if len(loc) else 99
                    history[f]=dict(first=t,last=t,cell=f,distance=distance)
                history[f]["last"]=t
    summaries={}
    for name,hist in pending.items():
        all_runs=opportunities[name]+list(hist.values())
        valid=[q for q in all_runs if q["last"]-q["first"]>=3]
        summaries[name]=dict(proof_ticks=totals[name][0],new_ticks=totals[name][1],usable=bool(valid),near=any(q["distance"]<=4 for q in valid),windows=valid)
    return dict(source=token,seed=meta["seed"],team=team,opponent=meta["opponent"],groups=summaries)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive",type=Path);p.add_argument("folder",type=Path);p.add_argument("stage",choices=("train","valid"))
    p.add_argument("action",choices=("play","score"));p.add_argument("lane",type=int,nargs="?",default=0);p.add_argument("stride",type=int,nargs="?",default=1)
    a=p.parse_args()
    if a.stage=="valid":assert json.loads((HERE/"train.json").read_text())["passed"]
    token=stamp({str(f.relative_to(HERE.parent)):sha(f) for f in SOURCES})
    src=sorted((a.archive/a.stage).glob("*.json"))
    assert len(src)==(160 if a.stage=="train" else 48)
    def dest(s):return a.folder/a.stage/s.name
    if a.action=="play":
        for f in src[a.lane::a.stride]:
            path=dest(f)
            if path.exists():
                assert json.loads(path.read_text())["source"]==token
                continue
            write_once(path,check(f,token))
        return
    rows=[json.loads(dest(f).read_text()) for f in src]
    assert len({r["seed"] for r in rows})==len(rows) and all(r["source"]==token for r in rows)
    summary={}
    for name in ("enemy","zones","both"):
        groups=[r["groups"][name] for r in rows]
        summary[name]={c:sum(g[c] for g in groups) for c in ("proof_ticks","new_ticks","usable","near")}
    limits=(8,4) if a.stage=="train" else (2,1)
    gates=dict(knowledge=summary["both"]["usable"]>=limits[0],distance=summary["both"]["near"]>=limits[1])
    out=dict(cards=len(rows),source=token,groups=summary,gates=gates,passed=all(gates.values()))
    write_once(HERE/f"{a.stage}.json",out)
    text="\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n"
    (HERE/f"{a.stage}_karten.jsonl.gz").write_bytes(gzip.compress(text.encode(),mtime=0))
    print(out)


if __name__=="__main__":main()
