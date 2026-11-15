"""Read complete parent, diagnostic and fresh game panels and report paired map results."""
import argparse
from collections import Counter
import json
from pathlib import Path
from types import SimpleNamespace

from scripts.final_battle_assess import bounds, external_comparison
from scripts.final_battle_compare import digest
from scripts.protocol import SIDES
from scripts.r3_v4_contact_study import R3_LOSS, V4_LOSS, accept, binding, diagnosis, prerequisites, target


def check(condition,message):
    if not condition: raise ValueError(message)


def rawcheck(rows):
    """Independent content invariants in addition to the runner's roster and source checks."""
    for key,r in rows.items():
        g=r["game"]
        check(type(g["game_win"]) is int and g["game_win"] in (0,1), "Invalid whole game flag")
        check(all(type(g[k]) is int and g[k]>=0 for k in ("our_points","opp_points","our_wins","opp_wins")),
              "Invalid match/point totals")
        check(g["our_wins"] in range(4) and g["opp_wins"] in range(4) and
              g["game_win"] == int(g["our_wins"]>g["opp_wins"]), "Invalid winner")
        if key[0]=="contact":
            count=r["routing"]
            check(set(count)=={"near_unit_turns","far_unit_turns","different_near","different_far"} and
                  all(type(x) is int and x>=0 for x in count.values()) and
                  count["near_unit_turns"]>=count["different_near"] and count["far_unit_turns"]>=count["different_far"] and
                  0 < count["near_unit_turns"]+count["far_unit_turns"] <= 16*300, "Invalid public routing counters")
        else:
            check(r["routing"]=={},"Unexpected intervention in an unmodified parent")


def diagnostic_report(rows,old):
    cases=[]
    for group,roster in (("r3",R3_LOSS),("v4",V4_LOSS)):
        for seed,seat in roster:
            k=("solution92",seed,SIDES[seat])
            r=rows["contact",*k]
            a,b=old["r3",*k],old["v4",*k]
            check(a["game_win"]+b["game_win"]==1,"Counterexample groups overlap")
            check((a if group=="r3" else b)["game_win"]==0,"Erroneous counterexample group")
            cases.append(dict(seed=seed,side=SIDES[seat],losing_parent=group,r3=a,v4=b,contact=r["game"],routing=r["routing"]))
    hits={p:sum(c["contact"]["game_win"] for c in cases if c["losing_parent"]==p) for p in ("r3","v4")}
    total=sum(hits.values())
    gate=(min(hits.values())>=1 and total>=7)
    check(diagnosis(rows)==dict(group_wins=hits,total_wins=total,passes=gate),"Differing diagnostic gate")
    return dict(games=len(cases),cases=cases,wins_in_each_group=hits,total_wins=total,
                historic_totals={p:sum(c[p]["game_win"] for c in cases) for p in ("r3","v4")},passes=gate)


def fresh_report(rows):
    seeds=range(7170260,7170276)
    runs={arm:SimpleNamespace(games={(o,s,t):{"result":r["game"]["game_win"]}
                                    for (a,o,s,t),r in rows.items() if a==arm})
          for arm in ("r3","v4","v14","contact")}
    totals={}
    for arm in runs:
        totals[arm]={}
        for opp in ("kaggle3","solution92","v14"):
            scores=[r["game"] for (a,o,s,t),r in rows.items() if a==arm and o==opp]
            if not scores: continue
            totals[arm][opp]=dict(games=len(scores),game_wins=sum(s["game_win"] for s in scores),
                                  match_wins=sum(s["our_wins"] for s in scores))
    paired={}
    for ref in ("r3","v4","v14"):
        by,combined=external_comparison(runs[ref],runs["contact"],seeds,"reference_wins")
        paired[ref]=dict(by_opponent=by,combined=combined)
    direct={}
    for arm in ("contact","r3","v4"):
        scores=runs[arm].games
        panel=[sum(scores["v14",s,t]["result"] for t in SIDES)/2 for s in seeds]
        wins=int(2*sum(panel))
        direct[arm]=dict(wins=wins,games=32,winrate=wins/32,winrate_ci95=bounds(panel))
    gates=dict(beats_both_external=all(paired[a]["combined"]["net_wins"]>0 for a in ("r3","v4")),
               solution_at_least_both=all(paired[a]["by_opponent"]["solution92"]["net_wins"]>=0 for a in ("r3","v4")),
               two_extra_external_vs_v14=paired["v14"]["combined"]["net_wins"]>=2,
               direct_majority=direct["contact"]["wins"]>16)
    return dict(games=len(rows),totals=totals,paired=paired,direct=direct,gates=gates,
                passes=all(gates.values()),decision_scope="independent confirmation required for release")


def report(stage,out,repo):
    stamp,old=binding(repo)
    prerequisites(stage,out,stamp,old)
    rows=accept(stage,out,stamp,old)
    rawcheck(rows)
    if stage=="sentinel":
        result=dict(passes=all(r["game"]==old[k] for k,r in rows.items()),games=len(rows),
                    parent_results=[{field:r[field] for field in ("arm","seed","side","game")} for r in rows.values()])
    elif stage=="diagnosis":
        result=diagnostic_report(rows,old)
    else:
        result=fresh_report(rows)
    return dict(stage=stage,source=stamp,assessor_sha256=digest(Path(__file__)),**result,
                raw_sha256={str(target(out,stage,k).relative_to(out)):digest(target(out,stage,k)) for k in rows})


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage",choices=("sentinel","diagnosis","screen"))
    p.add_argument("--repo",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(report(a.stage,a.out.resolve(),a.repo),indent=2,allow_nan=False))
