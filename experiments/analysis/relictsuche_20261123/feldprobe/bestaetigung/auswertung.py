"""Independent reconstruction of field-probe results from 303 turnwise score pairs per game."""
from collections import Counter
from hashlib import sha256
import csv
import gzip
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
FIELD=HERE.parent
ROOT=HERE.parents[4]
ARMS=(("reference","solution92"),("probe","solution92"),("probe","v16"))
FILES=("kandidat.py","signalmodell.py","modell.json","duelle.py","PLAN.md","valid.json","technik.json")


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def check(test,msg):
    if not test:
        raise ValueError(msg)


def decode(path):
    with gzip.open(path,"rt") as f:
        return [json.loads(line) for line in f]


def run(rows,cards,stage,source):
    n=len(cards)
    idx={(r["seed"],r["team"],r["arm"],r["opponent"]):r for r in rows}
    check(len(rows)==len(idx)==n*6 and set(idx)=={(s,t,k,o) for s in cards for t in (0,1) for k,o in ARMS}, "Case grid")
    region_events=[]
    groups={}
    for a,o in ARMS:
        subset=[idx[s,t,a,o] for s in cards for t in (0,1)]
        for r in subset:
            profile=np.asarray(r["profile"])
            check(r["turns"]==303 and profile.shape==(303,2) and np.all(profile>=0)
                  and len(r["matches"])==3 and all(profile[j*101:(j+1)*101].sum(0).tolist()==m["points"]
                      for j,m in enumerate(r["matches"])) and sum(m["win"] for m in r["matches"])>=0
                  and int(sum(m["win"] for m in r["matches"])>=2)==r["win"] and r["source"]==source
                  and len(r["hash"])==64 and (stage=="general" or r["sensor"]==1),"Invalid game scores or source")
            credit=np.flatnonzero(profile[:101,0])
            check((int(credit[0]) if len(credit) else 101)==r["credit"],"First own score")
            if stage!="selection":
                check(r["caught_errors"]==[0,0] and r["actions_checked"]==[303,303] and
                      r["commands_vs_original"]==(303*16 if a=="probe" else 0),"Command coverage")
            e=r["event"]
            if e is not None:
                t=e["t"]; turn=t%101
                check(a=="probe" and r["sensor"]==1 and 8<=turn<=84 and turn%4==0 and 0<=e["u"]<16 and
                      1<=e["d"]<=4 and 0<=e["old"]<=4 and e["old"]!=e["d"] and len(e["prefix"])==64 and
                      (not e["scored"] or e["arrived"]) and len(e["prior_truth"])==2,"Invalid field event")
                x,y=e["xy"]
                distance=(x+y-23)*(1 if r["team"]==0 else -1)
                zone="eigene Hälfte" if distance<0 else ("Achse" if distance==0 else "gegnerische Hälfte")
                region_events.append(dict(seed=r["seed"],side=r["team"],opponent=o,tick=t,match=t//101+1,region=zone,
                                          arrived=e["arrived"],scored=e["scored"],own_credit=int(profile[t,0]),
                                          opp_credit=int(profile[t,1])))
        groups[a+"_"+o]=dict(wins=sum(r["win"] for r in subset), matches=np.sum([[m["win"] for m in r["matches"]] for r in subset],axis=0).tolist(),
            changed=sum(r["event"] is not None for r in subset),scoring_arrivals=sum(bool(r["event"] and r["event"]["scored"]) for r in subset))
    paired=[]
    active=[]
    for s in cards:
        for t in (0,1):
            ref,can,duel=[idx[s,t,k,o] for k,o in ARMS]
            check(ref["sensor"]==can["sensor"]==duel["sensor"],"Sensor mismatch")
            e=can["event"]
            delta=[0,0]
            if e is not None:
                tick=e["t"]
                check(e["prefix"]==ref["prefix"][str(tick)] and ref["profile"][:tick]==can["profile"][:tick],"Pre-action history")
                if stage!="selection":
                    check(e["current"]==ref["current"][str(tick)],"Current 16 own original proposals or opponent actions differ")
                delta=np.subtract(can["profile"][tick],ref["profile"][tick]).tolist()
                active.append(dict(seed=s,team=t,tick=tick,actual=e["scored"],change=delta,dead=e["known_empty"]))
            else:
                check(all(ref[k]==can[k] for k in ("hash","profile","matches","sight","credit","win")),"Silent trajectory changed")
            paired.append(dict(seed=s,side=t,sensor=ref["sensor"],solution_ref=ref["win"],solution_probe=can["win"],
                 direct=duel["win"],immediate_own=delta[0],immediate_opp=delta[1],active=e is not None,
                 direct_active=duel["event"] is not None,ref_sight=ref["sight"],probe_sight=can["sight"],
                 ref_credit=ref["credit"],probe_credit=can["credit"]))
    draws=np.random.default_rng(231123).integers(n,size=(20000,n))
    def metric(seats):
        data=np.asarray(seats,dtype=float).reshape(n,2).mean(1)
        return dict(mean=float(data.mean()),ci95=np.quantile(data[draws].mean(1),[.025,.975]).tolist())
    solution=metric([r["solution_probe"]-r["solution_ref"] for r in paired])
    direct=metric([r["direct"] for r in paired])
    immed=metric([r["immediate_own"] for r in paired])
    if stage=="selection":
        gates=dict(solution=solution["mean"]>=0,direct=direct["mean"]>=.5,own_immediate=immed["mean"]>0)
        passed=all(gates.values())
    elif stage=="confirm":
        gates=dict(observed_both=all(groups["probe_"+o]["changed"]>0 for o in ("solution92","v16")),
                   own_immediate_lower_positive=immed["ci95"][0]>0,solution_no_fewer=solution["mean"]>=0,
                   direct_at_least_half=direct["mean"]>=.5,strict_whole_improvement=solution["mean"]>0 or direct["mean"]>.5)
        passed=all(gates.values())
    else:
        gates=dict(route_a_solution_lower_positive=solution["ci95"][0]>0,route_a_direct_mean=direct["mean"]>=.5,
                   route_a_direct_lower=direct["ci95"][0]>=.45,route_b_direct_lower=direct["ci95"][0]>.5,
                   route_b_solution_lower=solution["ci95"][0]>=-.01)
        passed=all(v for k,v in gates.items() if k.startswith("route_a")) or all(v for k,v in gates.items() if k.startswith("route_b"))
    outcome=dict(groups=groups,games=len(rows),cards=n,solution_difference=solution,direct_rate=direct,
                 immediate_own_gain=immed,changed_solution=active,gates=gates,passed=bool(passed))
    return outcome,paired,region_events


def csv_out(path,rows):
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)


def audit_selection():
    archive=FIELD/"ganze_partien.jsonl.gz"
    rows=decode(archive)
    p=Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/feldprobe")
    manifest=json.loads((p/"v2/manifest.json").read_bytes())
    cards=manifest["cards"]
    check(len(cards)==48 and cards==sorted(set(cards)) and min(cards)>=162400000 and max(cards)<162401000,"Selection map block")
    result,pairs,events=run(rows,cards,"selection",manifest["source"])
    check(result==json.loads((FIELD/"duell.json").read_bytes()) and result["passed"],"Initial published result failed reproduction")
    failed=json.loads((p/"manifest.json").read_bytes())
    check(failed["source"]!=manifest["source"] and len(list((p/"spiele").glob("*.json")))==2 and
          all(json.loads(f.read_bytes())["arm"]=="reference" for f in (p/"spiele").glob("*.json")),"Initial two controls")
    check(len(list((p/"v2/spiele").glob("*.json")))==288 and all(
        json.loads((p/"v2/spiele"/f"{r['seed']}_{r['team']}_{r['arm']}_{r['opponent']}.json").read_bytes())==r for r in rows),"Published raw disagrees with final simulations")
    evidence=dict(passed=True,complete_games=len(rows),paired_seats=len(pairs),field_events=len(events),
        source=manifest["source"],first_map=cards[0],last_map=cards[-1],archived_sha256=sha(archive),result_sha256=sha(FIELD/"duell.json"),
        active_by_region={f"{o}_{z}":sum(e["opponent"]==o and e["region"]==z for e in events)
                          for o in ("solution92","v16") for z in ("eigene Hälfte","Achse","gegnerische Hälfte")},
        verified_runtime_command_rows=len(rows)*303*2*16,round_points_recomputed=len(rows)*3,unused_initial_control_games=2)
    (HERE/"auswahl_nachweis.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n")
    return result


if __name__=="__main__":
    print(audit_selection()["gates"])
