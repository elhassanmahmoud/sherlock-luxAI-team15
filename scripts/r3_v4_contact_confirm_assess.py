"""Independent analysis of sealed contact confirmation lanes. Output files are immutable."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace

from scripts.final_battle_assess import bounds,external_comparison
from scripts.final_battle_compare import digest
from scripts.protocol import SIDES
from scripts.r3_v4_contact_confirm import EXTERNAL,DIRECT,OPPONENTS,lane_dir,panel,read_lane,stamp_for
from scripts.train_combat_advice import publish_json


def collected(out,phase,stamp):
    rows,seals={},{}
    for lane in (0,1):
        part,_=read_lane(out,phase,lane,stamp,closed=True)
        if rows.keys() & part.keys(): raise ValueError("Overlapping lane keys")
        rows.update(part)
        p=lane_dir(out,phase,lane)/"completed.json"
        seals[str(p.relative_to(out))]=digest(p)
    if set(rows)!=set(panel(phase)) or len(rows)!={"v14":600,"parents":480}[phase]:
        raise ValueError("Missing or excess study games")
    return rows,seals


def scored(rows,arm):
    return SimpleNamespace(games={(o,s,t):{"result":r["game"]["game_win"]}
                                 for (a,o,s,t),r in rows.items() if a==arm})


def summary(rows,arm):
    out={}
    for opp in (*OPPONENTS,"v14"):
        games=[r["game"] for (a,o,s,t),r in rows.items() if a==arm and o==opp]
        if games:
            wins=sum(g["game_win"] for g in games)
            out[opp]=dict(games=len(games),wins=wins,winrate=wins/len(games),
                          match_wins=sum(g["our_wins"] for g in games),wins_by_seat={
                              side:sum(r["game"]["game_win"] for (a,o,s,t),r in rows.items()
                                       if (a,o,t)==(arm,opp,side)) for side in SIDES})
    sol=scored(rows,arm).games
    maps=[sum(sol["solution92",s,t]["result"] for t in SIDES) for s in EXTERNAL]
    out["solution_target"]=dict(maps=len(maps),both_wins=maps.count(2),one_win=maps.count(1),
                                zero_wins=maps.count(0),perfect_sample=all(v==2 for v in maps))
    return out


def comparison(rows,ref):
    by,external=external_comparison(scored(rows,ref),scored(rows,"contact"),EXTERNAL,"reference_wins")
    return dict(by_opponent=by,combined=external)


def primary(rows):
    pair=comparison(rows,"v14")
    direct=scored(rows,"contact").games
    per_map=[sum(direct["v14",s,t]["result"] for t in SIDES)/2 for s in DIRECT]
    wins=int(2*sum(per_map))
    ci=bounds(per_map)
    gates=dict(external_lower_bound_positive=pair["combined"]["difference_ci95"][0]>0,
               direct_lower_bound_above_half=ci[0]>.5,solution_at_least_v14=pair["by_opponent"]["solution92"]["net_wins"]>=0)
    return dict(v14_advantage_confirmed=all(gates.values()),primary_gates=gates,paired_external=pair,
                direct_vs_v14=dict(games=120,wins=wins,winrate=wins/120,winrate_ci95=ci),
                totals={arm:summary(rows,arm) for arm in ("contact","v14")})


def parents(rows):
    compared={}
    for ref in ("r3","v4"):
        pair=comparison(rows,ref)
        supported=pair["combined"]["difference_ci95"][0]>0 and pair["by_opponent"]["solution92"]["net_wins"]>=0
        compared[ref]=dict(**pair,externally_ahead_with_solution_preserved=supported,totals=summary(rows,ref))
    return dict(comparisons=compared,beats_both_parents_externally=all(c["externally_ahead_with_solution_preserved"]
                for c in compared.values()))


def primary_report(out,stamp):
    rows,seals=collected(out,"v14",stamp)
    return dict(phase="v14",source=stamp,seals=seals,**primary(rows))


def sealed_primary(out,stamp):
    p=out/"v14_assessment.json"
    r=primary_report(out,stamp)
    if not p.is_file() or json.loads(p.read_bytes())!=r:
        raise ValueError("A sealed, reproduced primary report is required")
    if not r["v14_advantage_confirmed"]:
        raise ValueError("Primary V14 criteria failed; parent games are unnecessary")
    return digest(p)


def assess(a):
    stamp=stamp_for(a.repo,a.selection.resolve())
    out=a.out.resolve()
    if a.phase=="v14": return primary_report(out,stamp)
    primary_sha=sealed_primary(out,stamp)
    take=dict(stamp,primary_report_sha256=primary_sha)
    original,_=collected(out,"v14",stamp)
    extra,seals=collected(out,"parents",take)
    if original.keys()&extra.keys():
        raise ValueError("Duplicated reference or subject games")
    decision=json.loads((out/"v14_assessment.json").read_bytes())
    return dict(phase="parents",source=take,seals=seals,v14_advantage_confirmed=decision["v14_advantage_confirmed"],
                solution_target=decision["totals"]["contact"]["solution_target"],**parents(original|extra))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase",choices=("v14","parents"))
    p.add_argument("--repo",required=True,type=Path)
    p.add_argument("--selection",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=assess(a)
    dst=a.out.resolve()/(a.phase+"_assessment.json")
    if dst.is_file():
        if result!=json.loads(dst.read_bytes()): raise ValueError(f"Existing different report {dst}")
    else:
        publish_json(dst,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ("source","seals")},indent=2,allow_nan=False))
