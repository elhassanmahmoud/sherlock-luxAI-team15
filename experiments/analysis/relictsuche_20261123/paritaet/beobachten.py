"""Compare two public memories on the exact archived trajectory; inspect referee truth only after inference."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.paritaet.gleichungen import ParityEvidence
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import Evidence, MIRROR, indices
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha, stamp, write_once

HERE=Path(__file__).resolve().parent
SOURCES=(HERE/"PLAN.md",HERE/"gleichungen.py",HERE/"beobachten.py",HERE.parent/"punktspeicher/beweise.py")


def one(receipt):
    meta=json.loads(receipt.read_text())
    pub, judge=[receipt.parent/meta[k] for k in ("public","private")]
    assert all(sha(path)==meta[key+"_sha"] for path,key in ((pub,"public"),(judge,"private")))
    with np.load(pub) as data:
        names=("position","units_mask","energy","protected","team_points","relic_nodes_mask","known_points","move_mask","commands")
        game={n:data[n] for n in names}
    with np.load(judge) as world:
        active=world["active"]
        weights=world["weights"].ravel()
    team=meta["team"]
    basic, extended=Evidence(),ParityEvidence()
    earliest={}
    durations={}
    windows=[]
    independent=[]
    first_sight=next((t for t,q in enumerate(game["relic_nodes_mask"][:101]) if q.any()),101)
    for t in range(303):
        ms=t%101
        sidepos=game["position"][t,team]
        alive=game["units_mask"][t,team] & (game["energy"][t,team]>=0)
        pos=sidepos[alive]
        occupied={int(x)*24+int(y) for x,y in pos}
        row=dict(step=t,ms=ms,occupied=occupied,points=int(game["team_points"][t,team]),
                 epoch_seen=bool(game["relic_nodes_mask"][t,[t//101,t//101+3]].any()))
        basic.observe(row)
        extended.observe(row)
        assert (basic.positive & ~extended.positive)==0
        delta=extended.positive & ~basic.positive
        hidden=set(indices(delta))
        assert all(0 < weights[f] <= active[t].sum() and 0 < weights[MIRROR[f]] <= active[t].sum() for f in hidden)
        known=game["known_points"][t].ravel()
        unknown={f for f in hidden if not known[f] and not known[MIRROR[f]]}
        free=alive & ~game["protected"][t] & (game["commands"][t,:,0]<5) & (game["energy"][t,team]>=30)
        free &= game["move_mask"][t,:,1:5].any(1)
        new=set()
        for f in sorted(unknown):
            key=t//101,f
            new.add(key)
            if key not in durations:
                ends=[e for e in {f,MIRROR[f]} if e not in occupied]
                distance=min((int(np.abs(sidepos[free]-divmod(e,24)).sum(1).min()) for e in ends),default=99) if free.any() else 99
                durations[key]=dict(t=t,f=f,until=t,distance=distance)
                earliest.setdefault(f,t)
            durations[key]["until"]=t
        for key in list(durations):
            if key not in new:
                windows.append(durations.pop(key))
        if delta:
            independent.append([t,len(hidden),len(unknown)])
    windows.extend(durations.values())
    valid=[r for r in windows if r["until"]-r["t"]>=3]
    return dict(seed=meta["seed"],side=team,opponent=meta["opponent"],sight=first_sight,
                extra_fields=len({f for _,f in [(r["t"],r["f"]) for r in windows]}),
                unknown_ticks=sum(r["until"]-r["t"]+1 for r in windows),
                early=len(valid),near=sum(r["distance"]<=4 for r in valid),
                before_first=sum(r["t"]<first_sight for r in valid),
                windows=windows, extra_proof_ticks=sum(row[1] for row in independent))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive",type=Path)
    p.add_argument("stage",choices=("train","valid"))
    a=p.parse_args()
    if a.stage=="valid":
        assert json.loads((HERE/"train.json").read_text())["passed"]
    src=stamp({f.name:sha(f) for f in SOURCES})
    receipts=sorted((a.archive/a.stage).glob("*.json"))
    assert len(receipts)==(160 if a.stage=="train" else 48)
    rows=[one(f) for f in receipts]
    assert len({r["seed"] for r in rows})==len(rows)
    early=sum(bool(r["early"]) for r in rows)
    near=sum(bool(r["near"]) for r in rows)
    limits=(6,3) if a.stage=="train" else (2,1)
    gates=dict(earlier=early>=limits[0],near=near>=limits[1])
    out=dict(cards=len(rows),source=src,early_cards=early,near_cards=near,
             positive_cards=sum(bool(r["extra_proof_ticks"]) for r in rows),
             before_first_cards=sum(bool(r["before_first"]) for r in rows),
             new_unknown_fields=sum(r["extra_fields"] for r in rows),unknown_ticks=sum(r["unknown_ticks"] for r in rows),
             true_additional_proof_ticks=sum(r["extra_proof_ticks"] for r in rows), gates=gates,passed=all(gates.values()))
    write_once(HERE/f"{a.stage}.json",out)
    data="\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n"
    (HERE/f"{a.stage}_karten.jsonl.gz").write_bytes(gzip.compress(data.encode(),mtime=0))
    print(out)


if __name__=="__main__":
    main()
