"""Auditable short-window and match-level paired results of single-command interventions."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import numpy as np
from verlauf import HERE, MODEL_SHA, SOURCE_SHA, V16, schedule, sources


def read(p):
    if p.is_dir():
        for f in sorted(p.glob("*.json")):yield json.loads(f.read_text())
    else:
        with gzip.open(p,"rt") as f:
            for ln in f:yield json.loads(ln)


def evaluate(records):
    expected=dict(schedule());stamp=sources();rows={}
    for r in records:
        k=(r["seed"],r["side"],r["group"]);orig=r["original"];alt=r["alternate"]
        if (k not in expected or k in rows or orig["scores"]!=expected[k] or r["sources"]!=stamp
                or (r["weight"],r["student_source"],r["release"])!=(MODEL_SHA,SOURCE_SHA,V16)
                or (orig["event"] is None)!=(alt is None) or orig["changes"]):
            raise ValueError("Invalid original record")
        for arm in (orig,alt):
            if arm is None:continue
            gains=np.asarray(arm["gains"])
            if (gains.shape!=(303,2) or (gains<0).any() or gains.sum(0).tolist()!=
                    [arm["scores"]["our_points"],arm["scores"]["opp_points"]] or len(arm["match_wins"])!=3 or
                    sum(arm["match_wins"])!=arm["scores"]["our_wins"] or
                    int(sum(arm["match_wins"])>=2)!=arm["scores"]["game_win"]):
                raise ValueError("Invalid scoring totals")
        event=orig["event"]
        if event and (not 26<=event["ms"]<=75 or event["step"]!=101+event["ms"] or alt["event"]!=event or
                      orig["pivot"]!=alt["pivot"] or len(orig["pivot"]["state"])!=64 or
                      orig["gains"][:event["step"]]!=alt["gains"][:event["step"]] or
                      orig["match_wins"][0]!=1 or alt["match_wins"][0]!=1 or alt["changes"]!=1 or event["value"]<.25):
            raise ValueError("Noncomparable branches")
        rows[k]=r
    if set(rows)!=set(expected):raise ValueError("Incomplete 54-seat panel")

    analyses={}
    for cohort in ("gesamt","verlust","kontrolle"):
        block=[r for r in rows.values() if cohort=="gesamt" or r["group"]==cohort]
        touched=[r for r in block if r["alternate"] is not None]
        matches=[];games=[]
        for r in block:
            o=r["original"];a=r["alternate"] or o
            matches.append(a["match_wins"][1]-o["match_wins"][1])
            games.append(a["scores"]["game_win"]-o["scores"]["game_win"])
        endpoints={}
        for name,h in (("nach1",1),("nach5",5),("nach15",15),("nach5_weiteren",6),("nach15_weiteren",16),("matchende",None)):
            diffs=[]
            for r in touched:
                o=r["original"];a=r["alternate"];i=o["event"]["step"]
                end=202 if h is None else i+h
                if end>202:raise ValueError("Window passed the end of match two")
                gain=np.asarray(a["gains"][i:end],dtype=int)-np.asarray(o["gains"][i:end],dtype=int)
                own,opp=gain.sum(0).tolist()
                diffs.append([r["seed"],r["side"],own,opp,own-opp])
            net=[v[-1] for v in diffs]
            endpoints[name]=dict(n=len(diffs),own_total=sum(v[-3] for v in diffs),opponent_total=sum(v[-2] for v in diffs),
                                 net_total=sum(net),mean_net=sum(net)/len(net) if net else None,
                                 positive=sum(x>0 for x in net),negative=sum(x<0 for x in net),neutral=net.count(0))
        analyses[cohort]=dict(seats=len(block),win_m1=sum(r["original"]["match_wins"][0] for r in block),
                behind=sum(r["original"]["behind_steps"]>0 for r in block),opportunities=sum(r["original"]["options_steps"]>0 for r in block),
                interventions=len(touched),cards=len({r["seed"] for r in touched}),original_games=sum(r["original"]["scores"]["game_win"] for r in block),
                original_m2=sum(r["original"]["match_wins"][1] for r in block),m2_gain=sum(matches),games_gain=sum(games),
                game_seat_changes=dict(Counter(games)),match_seat_changes=dict(Counter(matches)),endpoints=endpoints)
    all_=analyses["gesamt"]
    gates={"at_least_12":all_["interventions"]>=12,"at_least_8_cards":all_["cards"]>=8,
           "positive_15":all_["endpoints"]["nach15"]["net_total"]>0,
           "whole_games":all_["games_gain"]>=0,"match2_wins":all_["m2_gain"]>=0}
    return dict(groups=analyses,gates=gates,passed=all(gates.values()))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("data",type=Path);p.add_argument("--archive",type=Path)
    args=p.parse_args();rows=list(read(args.data));result=evaluate(rows)
    if args.archive:
        raw="".join(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n" for r in rows).encode()
        zipdata=gzip.compress(raw,mtime=0)
        if args.archive.exists() and args.archive.read_bytes()!=zipdata:raise ValueError("Archive already differs")
        args.archive.write_bytes(zipdata)
        if evaluate(read(args.archive))!=result:raise ValueError("Archive differs on readback")
    print(json.dumps(result,indent=2))
