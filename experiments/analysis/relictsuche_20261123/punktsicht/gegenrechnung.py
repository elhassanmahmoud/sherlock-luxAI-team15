"""Independently recount the single post-credit sighting panel from archived whole games."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent


def main():
    with gzip.open(HERE/"partien.jsonl.gz","rt") as file:
        rows=[json.loads(line) for line in file]
    result=json.loads((HERE/"ergebnis.json").read_bytes())
    cards=json.loads((HERE/"karten.json").read_bytes())["discovery"]
    u={(r["seed"],r["team"],r["id"],r["opponent"]):r for r in rows}
    assert len(u)==len(rows)==240 and len(cards)==40
    swaps={name:[] for name in ("sight","score70","match","game","direct","active")}
    per_seat=Counter()
    later_early=Counter()
    no_delta=0
    changed_sites={}
    for seed in cards:
        kv={k:[] for k in swaps}
        for team in (0,1):
            ref=u[seed,team,"reference","solution92"]
            cand=u[seed,team,"punktsicht","solution92"]
            duel=u[seed,team,"punktsicht","v16"]
            for row in (ref,cand,duel):
                assert row["steps"]==303 and len(row["matches"])==3 and sum(m["win"] for m in row["matches"])==row["wins"]
                assert bool(row["win"])==(row["wins"]>=2) and row["actions_checked"]==[303,303]
                assert row["caught_errors"]==[0,0]
                events=row["events"]
                assert len({e[1] for e in events})<=1 and len(events)<=5
                assert len(row["protected_at_changes"])==len(events)
                if events:
                    uid=events[0][1]
                    sep=row["selection"]
                    assert uid==sep["uid"] and sep["raw"]>=.15 and sep["added"]>=.08
                    assert sep["t"]-row["first_public_credit"]<12 and sep["t"]<=91
                    assert all(row["credit"]<e[0]<row["sight"] and 0<=e[0]-sep["t"]<5 for e in events)
                assert row["action_hash"] and len(row["action_hash"])==64
            assert ref["credit"]==cand["credit"]
            if not cand["events"]:
                assert ref["action_hash"]==cand["action_hash"]
                assert ref["matches"]==cand["matches"]
                no_delta+=1
            delta=ref["sight"]-cand["sight"]
            if delta>0:per_seat["earlier"]+=1
            if delta<0:per_seat["later"]+=1
            if cand["events"]:
                changed_sites.setdefault(seed,[]).append(team)
            kv["sight"].append(delta)
            kv["score70"].append((cand["after_70"][0]-cand["after_70"][1])-(ref["after_70"][0]-ref["after_70"][1]))
            kv["match"].append(cand["matches"][0]["win"]-ref["matches"][0]["win"])
            kv["game"].append(cand["win"]-ref["win"])
            kv["direct"].append(duel["win"])
            kv["active"].append(bool(cand["events"]))
            later_early["before50"]+=cand["after49"]-ref["after49"]
            later_early["turn50_89"]+=(cand["after89"]-cand["after49"])-(ref["after89"]-ref["after49"])
            later_early["last11"]+=(cand["matches"][0]["points"][0]-cand["after89"])-(ref["matches"][0]["points"][0]-ref["after89"])
        for k,val in kv.items():swaps[k].append(sum(val)/2)
    means={k:float(np.mean(v)) for k,v in swaps.items()}
    refdirect=result["candidate"]["direct_rate"]
    assert means["sight"]==result["candidate"]["paired"]["sight"]["mean"]
    assert means["direct"]==refdirect["mean"]
    gates={"earlier_sight_half":means["sight"]>=.5,"more_earlier_than_later":per_seat["earlier"]>per_seat["later"],
          "four_changed_maps":len(changed_sites)>=4,"credit_equal_each_seat":True,"margin70_nondecreasing":means["score70"]>=0,
          "match1wins_nondecreasing":means["match"]>=0,"wins_nondecreasing":means["game"]>=0,"direct_at_least_half":means["direct"]>=.5}
    assert gates==result["gates"] and all(gates.values())==result["passed"]
    rng=np.random.default_rng(231123)
    sample=rng.integers(0,len(cards),size=(20000,len(cards)))
    ci=np.percentile(np.asarray(swaps["sight"])[sample].mean(1),[2.5,97.5])
    np.testing.assert_allclose(ci,result["candidate"]["paired"]["sight"]["ci95"],atol=1e-12)
    archive=HERE/"partien.jsonl.gz"
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==result["sha256"]
    out={"games":len(rows),"maps":len(cards),"inactive_solution_seats_with_identical_full_action_history":no_delta,
         "earlier_later":dict(per_seat),"solution_changed_maps":len(changed_sites),"means":means,
         "sight_map_ci95":ci.tolist(),"own_point_deltas":dict(later_early),"passed":all(gates.values()),
         "verified_sha256":result["sha256"]}
    (HERE/"gegenrechnung.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))


if __name__=="__main__":
    main()
