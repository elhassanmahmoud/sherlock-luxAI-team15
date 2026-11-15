"""Paired card-level result on all 368 registered Solution seats."""
import argparse
from collections import Counter
import json
from pathlib import Path

from scripts.residual_ensemble_compare import interval
from scripts.r3_v4_wl_solution import complete, STUDY
from scripts.r3_v4_wl_solution_registry import registered


def summarize(cases, pairs):
    cards={}; by_seat={}; flips=[]; totals=Counter(); classes=Counter()
    for key,c in sorted(cases.items()):
        seed,side,_=key; g=c["expected"]; b=g
        if key in pairs:
            p=pairs[key]; a=p["control"]; b=p["switch"]
            if a["game"]!=g: raise ValueError("Reference mismatch")
            if b:
                if a["sequence"][:2]!="WL": raise ValueError("Unregistered intervention")
                classes["observed_switch"]+=1
                if b["game"]["result"]!=g["result"]:
                    flips.append(dict(seed=seed,side=side,panel=c["panel"],r3=a["sequence"],switch=b["sequence"],
                                      old_m3=a["matches"][2],new_m3=b["matches"][2],changed_active=b["actor_stats"]["different_active"]))
                b=b["game"]
            else:
                if a["sequence"][:2]=="WL": raise ValueError("Missing intervention")
                classes["reproduced_no_wl"]+=1;b=g
        else:
            if g["wins"] not in (0,3): raise ValueError("Missing mixed game")
            classes["archive_no_wl"]+=1
        row=dict(r3_games=g["result"],switch_games=b["result"],r3_matches=g["wins"],switch_matches=b["wins"])
        totals.update(row);cards.setdefault(seed,Counter()).update(row);by_seat.setdefault(side,Counter()).update(row)
    ci=lambda x:interval(x, seed=2711,draws=10000)
    stats={}
    for kind,denom in (("games",2),("matches",6)):
        x=[r["r3_"+kind]/denom for r in cards.values()];y=[r["switch_"+kind]/denom for r in cards.values()]
        stats[kind]=dict(r3_share=sum(x)/len(x),switch_share=sum(y)/len(y),difference=(sum(y)-sum(x))/len(x),
                         r3_ci95=ci(x),switch_ci95=ci(y),paired_difference_ci95=ci([b-a for a,b in zip(x,y)]))
    return dict(map_count=len(cards),games_per_agent=len(cases),matches_per_agent=3*len(cases),
                counts=totals,totals_by_seat=by_seat,provenance_counts=classes,switch_outcomes=flips,
                gained=sum(f["switch"]=="WLW" for f in flips),lost=sum(f["switch"]=="WLL" for f in flips),
                estimates=stats,bootstrap=dict(unit="whole map with both seats",draws=10000,seed=2711),
                per_map=[dict(seed=k,**dict(v)) for k,v in cards.items()])


if __name__=="__main__":
    from scripts.train_combat_advice import publish_json
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project",type=Path,required=True)
    a=p.parse_args(); project=a.project.resolve();cases,source=registered(project)
    pairs=complete(project); result=summarize(cases,pairs)
    from scripts.r3_v4_wl_solution_registry import digest
    folder=project/STUDY
    result.update(roster_sha256=source["roster_sha256"],receipt_sha256=digest(folder/"completed.json"),
                  assessment_source_sha256=digest(Path(__file__)))
    dest=folder/"assessment.json"
    if dest.exists():
        if json.loads(dest.read_bytes())!=result: raise ValueError("Prior assessment differs")
    else: publish_json(dest,result)
    print(json.dumps({k:v for k,v in result.items() if k!="per_map"},indent=2,sort_keys=True))
