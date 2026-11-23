"""Decompose the same-map self-play and candidate duel into relative information and actual access."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def side_view(game, team):
    f = game["frames"]
    view = game["views"][str(team)]
    sight = view["sight"]
    credit = view["credit"]
    reached = next((t for t, r in enumerate(f) if r["points"][team] >= 10), 101)
    assert credit == next((t for t,r in enumerate(f) if r["points"][team]),101)
    def rate(start):
        turns = f[start:start + 20]
        return sum(len(r["fields"][team]) for r in turns) / len(turns) if turns else None
    found=game["finds"][team]
    result=dict(sight=sight, credit=credit, ten=reached, spawn20=rate(game["spawn"]),
                sight20=rate(sight), post_sight_to_credit=max(credit-sight,0),
                after70=f[70]["points"][team], won=int(sum(m["win"] for m in view["matches"])>1))
    if found is not None:
        vals=[v for k,v in found["distances"].items() if found["uid"] is None or int(k)!=found["uid"]]
        result["nearest_other_ship"]=min(vals) if vals else None
        result["other_ships_in_two"]=sum(v<=2 for v in vals)
    else:
        result["nearest_other_ship"] = result["other_ships_in_two"] = None
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    folder=p.parse_args().folder
    raw=[json.load(gzip.open(f,"rt")) for f in sorted(folder.glob("*.json.gz"))]
    assert len(raw)==120 and len({json.dumps(r["source"],sort_keys=True) for r in raw})==1
    games={(g["seed"],g["side"]):g for g in raw}
    seeds=sorted({s for s,_ in games})
    assert len(seeds)==40 and len(games)==120
    rows=[]
    for seed in seeds:
        ref=games[seed,-1]
        assert len(ref["frames"])==101
        for team in (0,1):
            comp=games[seed,team]
            assert ref["spawn"]==comp["spawn"]
            control=[side_view(ref,i) for i in (team,1-team)]
            candidate=[side_view(comp,i) for i in (team,1-team)]
            if not comp["commands"]:
                assert ref["digest"]==comp["digest"] and candidate==control
            deltas={}
            for field in ("sight","credit","ten","spawn20","sight20","after70","won","post_sight_to_credit"):
                if any(v[field] is None for v in candidate+control):
                    continue
                # Positive numbers always favor Sherlock. For a clock, earlier is better.
                sign=-1 if field in ("sight","credit","ten","post_sight_to_credit") else 1
                deltas[field]=[sign*(a[field]-b[field]) for a,b in zip(candidate,control)]
            rows.append(dict(seed=seed,team=team,commands=len(comp["commands"]),spawn=comp["spawn"],
                             candidate=candidate,reference=control,delta=deltas))
    def describe(values):
        x=np.array(values,dtype=float)
        draws=np.random.default_rng(231123).integers(0,len(x),size=(20000,len(x)))
        return dict(cards=len(x),mean=float(x.mean()),ci95=np.percentile(x[draws].mean(1),[2.5,97.5]).tolist())
    summary={}
    for field in ("sight","credit","ten","spawn20","sight20","after70","won","post_sight_to_credit"):
        by_card={}
        for row in rows:
            if field in row["delta"]:
                by_card.setdefault(row["seed"],[]).append(row["delta"][field])
        # For each comparison keep both starting sides on the same map.
        matrix=np.array([np.mean(values,axis=0) for values in by_card.values() if len(values)==2])
        if len(matrix):
            summary[field]={k:describe(v) for k,v in (("own",matrix[:,0]),("rival",matrix[:,1]),("relative",matrix[:,0]-matrix[:,1]))}
    for label,idx in (("intervention",0),("opponent",1)):
        fast=[r for r in rows if r["delta"]["sight"][idx]>0]
        summary["earlier_"+label]=dict(seats=len(fast),cards=len({r["seed"] for r in fast}),
            also_earlier_ten=sum(r["delta"]["ten"][idx]>0 for r in fast),
            later_ten=sum(r["delta"]["ten"][idx]<0 for r in fast),same_ten=sum(r["delta"]["ten"][idx]==0 for r in fast))
    (HERE/"ergebnis.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n")
    (HERE/"sitze.jsonl.gz").write_bytes(gzip.compress(("\n".join(json.dumps(r,separators=(",",":")) for r in rows)+"\n").encode(),mtime=0))
    (HERE/"verlaeufe.jsonl.gz").write_bytes(gzip.compress(("\n".join(json.dumps(r,separators=(",",":")) for r in raw)+"\n").encode(),mtime=0))
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
