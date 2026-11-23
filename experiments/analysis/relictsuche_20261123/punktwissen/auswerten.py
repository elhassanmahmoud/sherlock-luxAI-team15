"""Independently compare actual complete action sequences, match outcomes, and on-map paired differences."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from spiele import HERE, board_seeds, decoded, frozen, keys, paired, path, write_once


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", type=Path)
    args=p.parse_args()
    identity=frozen()
    games={}
    for k in keys():
        r=json.loads(path(args.folder,k).read_text())
        assert r["source"]==identity and tuple(r[s] for s in ("seed","team","version","opponent"))==k
        assert r["sensor"]==1 and len(r["matches"])==3 and r["win"]==int(sum(m["win"] for m in r["matches"])>=2)
        assert hashlib.sha256(decoded(r).astype("<i4").tobytes()).hexdigest()==r["digest"]
        games[k]=r
    assert len(games)==448
    cards=board_seeds()
    changed=set()
    results={}
    draws=np.random.default_rng(231123).integers(0,len(cards),(20000,len(cards)))
    def report(x):
        x=np.asarray(x,dtype=float)
        return dict(mean=float(x.mean()),ci95=np.percentile(x[draws].mean(1),[2.5,97.5]).tolist())
    for o in ("solution92","v16"):
        arr=[]
        for s in cards:
            for t in (0,1):
                r=games[s,t,"neu",o]
                ref=games[s,0 if o=="v16" else t,"v16",o]
                diff=paired(ref,r,selfplay=o=="v16")
                base=int(not ref["win"]) if o=="v16" and t else ref["win"]
                vs=[(1-m["win"] if o=="v16" and t else m["win"]) for m in ref["matches"]]
                totals=[m["points"][::-1] if o=="v16" and t else m["points"] for m in ref["matches"]]
                if diff is None:
                    assert r["matches"]==[dict(win=v,points=p) for v,p in zip(vs,totals,strict=True)]
                else:
                    changed.add(s)
                own=sum(m["points"][0] for m in r["matches"]); old=sum(x[0] for x in totals)
                opp=sum(m["points"][1] for m in r["matches"]); before=sum(x[1] for x in totals)
                arr.append(dict(seed=s,team=t,win=r["win"],base=base,own=own-old,opp=opp-before,
                    turns_with_bad_belief=r["false_positive_ticks"],first_change=diff,added=len(r["events"]),
                    prior_dead=sum(e["was_dead"] for e in r["events"]),matches=[m["win"] for m in r["matches"]],reference_matches=vs))
        def metric(values):
            return report(np.asarray(values,dtype=float).reshape((-1,2)).mean(axis=1))
        win=np.array([r["win"] for r in arr])
        base=np.array([r["base"] for r in arr])
        results[o]=dict(wins=int(win.sum()),ref_wins=int(base.sum()),new_wins=int((win>base).sum()),
            lost_wins=int((win<base).sum()),win_rate=metric(win),difference=metric(win-base),
            own_points=metric([r["own"] for r in arr]),opponent_points=metric([r["opp"] for r in arr]),
            matches=np.sum([r["matches"] for r in arr],axis=0).tolist(),
            reference_matches=np.sum([r["reference_matches"] for r in arr],axis=0).tolist(),
            first_event_seats=sum(bool(r["added"]) for r in arr),events=sum(r["added"] for r in arr),
            prior_dead=sum(r["prior_dead"] for r in arr),changed_seats=sum(r["first_change"] is not None for r in arr),
            false_positive_ticks=sum(r["turns_with_bad_belief"] for r in arr))
    good=results["solution92"]["wins"]-results["solution92"]["ref_wins"]
    direct=results["v16"]["wins"]
    gates=dict(changed_maps=len(changed)>=8,positive_wins=(good>=1 and direct>=64) or (good>=0 and direct>64))
    summary=dict(cards=len(cards),games=len(games),source=identity,results=results,changed_cards=len(changed),
                 gates=gates,passed=all(gates.values()))
    write_once(HERE/"ergebnis.json",summary)
    data="\n".join(json.dumps(r,separators=(",",":")) for r in games.values())+"\n"
    (HERE/"partien.jsonl.gz").write_bytes(gzip.compress(data.encode(),mtime=0))
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
