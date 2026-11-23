"""Nach vollständigen Stufen prüfen. Drei Quellen historischer Siege werden getrennt gezählt."""
import argparse
import json
from collections import Counter
import numpy as np

from technik import HERE,selection,manifest,raw,verify_reference


def technical():
    folder=HERE/"technik"; cases=selection()
    for i in (0,1):
        if json.loads((folder/f"quellen_{i}.json").read_text())!=manifest():raise ValueError("Andere Technikquelle")
    records=raw(folder)
    rows={(r["seed"],r["side"],r["arm"]):r for r in records}
    if len(records)!=44 or set(rows)!={(s,t,a) for s,t in cases for a in ("aus","signal","mitte","beide")}:
        raise ValueError("Nur alle vollständigen 44 Spiele sind auswertbar")
    totals=Counter(); effects=Counter(); details=[]
    for (seed,side),case in sorted(cases.items()):
        for arm in ("aus","mitte","signal"):
            if arm in case:verify_reference(rows[seed,side,arm],case[arm])
        key=case["labels"][0]
        k=rows[seed,side,"beide"]
        if k["decisions"]!=303 or len({e["step"] for e in k["events"]})!=len(k["events"]):
            raise ValueError("Überlappende Aktionen oder fehlerhafte Beobachtung")
        kinds=[e["module"] for e in k["events"]]
        totals[key]+=k["game_win"]
        effects.update(kinds)
        details.append(dict(seed=seed,side=side,source=key,
            old=rows[seed,side,"aus"]["our_wins"],signal=rows[seed,side,"signal"]["our_wins"],
            middle=rows[seed,side,"mitte"]["our_wins"],combined=k["our_wins"],
            single_scout_turns=[e['step']-101 for e in rows[seed,side,"signal"]["events"]],
            single_middle_turns=[e['step']-101 for e in rows[seed,side,"mitte"]["events"]],
            scout_turns=[e['step']-101 for e in k["events"] if e["module"]=="signal"],
            middle_turns=[e['step']-101 for e in k["events"] if e["module"]=="mitte"]))
    gate=totals["signal_pruef"]>=2 and totals["mitte_archiv"]>=4 and effects["mitte"]>0 and effects["signal"]>0
    return dict(n=44,kept={a:totals[a] for a in ("signal_pruef","mitte_archiv","signal_entwicklung")},
                real_commands=dict(effects),gate=gate,details=details)


def summarize_fresh():
    from frisch import contract,panel
    folder=HERE/"frisch"; hashes=contract()
    for s in (0,1):
        if json.loads((folder/f"quellen_{s}.json").read_bytes())!=hashes:raise ValueError("Andere Quelle")
    records=raw(folder)
    indexed={(r["seed"],r["side"],r["opponent"],r["arm"]):r for r in records}
    if len(records)!=720 or set(indexed)!=set(panel()):raise ValueError("Nur 720 eindeutige abgeschlossene Spiele für das feste Panel auswerten")
    for r in records:
        t=int(r["side"][-1])
        if r["steps"]!=303 or r["decisions"]!=303 or len(r["match_winners"])!=3 or r["our_wins"]!=r["match_winners"].count(t):
            raise ValueError("Spiel nicht vollständig")
    output={}
    for opponent in ("solution92","kaggle3"):
        groups={p:[] for p in ("player_0","player_1")}
        for (seed,p,o,a),r in sorted(indexed.items()):
            if a!="beide" or o!=opponent:continue
            old=indexed[seed,p,o,"aus"]
            if not r["events"] and any(r[k]!=old[k] for k in ("match_winners","our_points","opp_points","game_win")):
                raise ValueError("Unterschied trotz identischer Aktion")
            kinds=sorted({v["module"] for v in r["events"]})
            groups[p].append(dict(seed=seed,side=p,base=old["game_win"],comb=r["game_win"],
                old_matches=old["our_wins"],matches=r["our_wins"],reference_points=old["our_points"]-old["opp_points"],
                candidate_points=r["our_points"]-r["opp_points"],
                delta=r["game_win"]-old["game_win"],modules=kinds,changes=len(r["events"])))
        def stats(sub):
            mixed=lambda r:"+".join(r["modules"]) if r["modules"] else "kein"
            return dict(sides=len(sub),maps=len({r["seed"] for r in sub}),base=sum(r["base"] for r in sub),
                combined=sum(r["comb"] for r in sub),added=sum(r["delta"]==1 for r in sub),lost=sum(r["delta"]==-1 for r in sub),
                reference_matches=sum(r["old_matches"] for r in sub),combined_matches=sum(r["matches"] for r in sub),
                point_diff=sum(r["candidate_points"]-r["reference_points"] for r in sub),
                affected=sum(bool(r["modules"]) for r in sub),modules=dict(Counter(mixed(r) for r in sub)),
                changed_actions=sum(r["changes"] for r in sub))
        sub=groups["player_0"]+groups["player_1"]
        d=np.array([(l["delta"]+r["delta"])/2 for l,r in zip(groups["player_0"],groups["player_1"],strict=True)])
        if [r["seed"] for r in groups["player_0"]]!=[r["seed"] for r in groups["player_1"]]:raise ValueError("Karten unsortiert")
        rng=np.random.default_rng(231786)
        intervals=np.quantile(d[rng.integers(0,len(d),size=(20000,len(d)))].mean(axis=1),[.025,.975],method="linear")
        output[opponent]=dict(total=stats(sub),by_side={p:stats(v) for p,v in groups.items()},
            diff=float(d.mean()),ci95=intervals.tolist(),flips=[r for r in sub if r["delta"]])
    direct=[r for r in records if r["opponent"]=="v16"]
    def duel(sub):
        return dict(n=len(sub),wins=sum(r["game_win"] for r in sub),matchwins=sum(r["our_wins"] for r in sub),
                    affected=sum(bool(r["events"]) for r in sub),affected_wins=sum(r["game_win"] for r in sub if r["events"]),
                    quiet_wins=sum(r["game_win"] for r in sub if not r["events"]),
                    both_modules=sum({e["module"] for e in r["events"]}=={"mitte","signal"} for r in sub))
    mixed=[];quiet=both=0
    for s in sorted({r["seed"] for r in direct}):
        pair=[r for r in direct if r["seed"]==s]
        off=[r for r in pair if not r["events"]]
        if len(off)==2:
            quiet+=1
            if off[0]["match_winners"]!=off[1]["match_winners"]:raise ValueError("Unveränderte Direktsitze weichen ab")
        elif len(off)==1:
            alt=next(r for r in pair if r["events"])
            b=off[0]["match_winners"].count(int(alt["side"][-1]))
            mixed.append(dict(seed=s,side=alt["side"],baseline_matches=b,candidate_matches=alt["our_wins"]))
        else:both+=1
    output["v16"]=dict(total=duel(direct),by_side={p:duel([r for r in direct if r["side"]==p]) for p in ("player_0","player_1")},
                       unchanged_maps=quiet,both_active=both,inferred_control=mixed)
    gate=output["solution92"]["ci95"][0]>0 and output["kaggle3"]["total"]["combined"]>=output["kaggle3"]["total"]["base"] and output["v16"]["total"]["wins"]>=40
    return dict(n=len(records),gate=gate,results=output)


if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("phase",choices=("technik","frisch"));phase=ap.parse_args().phase
    result=technical() if phase=="technik" else summarize_fresh()
    (HERE/phase/"ergebnis.json").write_text(json.dumps(result,indent=2)+"\n")
    if phase=="technik":
        print(result["kept"],result["real_commands"],result["gate"])
    else:
        print(json.dumps({k:(v["total"],v.get("ci95")) for k,v in result["results"].items()},indent=2))
        print("Freigabeprüfung eröffnet",result["gate"])
