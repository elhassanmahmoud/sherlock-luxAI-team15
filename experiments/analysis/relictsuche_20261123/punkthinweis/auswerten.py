"""Assess first positive score, nonproducing available ships, exact site/target inference, and original follow-up."""
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path
import time

import numpy as np

from belegung import COORD, HERE, MID, OTHER, ScoreEvidence, occupied
from gelegenheit import candidate_paths, choose, grade

TIMINGS = []
FOLDER = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/punkthinweis")


def first(mask):
    v=np.flatnonzero(mask)
    return int(v[0]) if len(v) else 101


def rank(w, idx):
    p=float(w[idx])
    if p<=0:
        raise ValueError("Public score equations excluded the actual pair")
    return dict(prob=p,logloss=float(-np.log(p)),rank=float((w>p).sum()+((w==p).sum()+1)/2),
                possible=int((w>0).sum()))


def seat(row):
    prefix=FOLDER/row["name"]
    data=prefix.with_suffix(".npz")
    labels=prefix.with_suffix(".richter.npz")
    if sha256(data.read_bytes()).hexdigest()!=row["public_sha"] or sha256(labels.read_bytes()).hexdigest()!=row["label_sha"]:
        raise ValueError("Changed original match")
    with np.load(data,allow_pickle=False) as f:
        d={k:f[k] for k in f}
    with np.load(labels,allow_pickle=False) as f:
        truth={k:f[k] for k in f}
    team=row["team"]
    score=d["team_points"][:,team]
    gain=d["after"][:,team]
    sight=first(d["relic_nodes_mask"].any(1))
    credit=first(gain>0)
    t0=first(score>0)
    if not np.array_equal(score[1:],gain[:-1]) or d["after"][-1].tolist()!=row["points"]:
        raise ValueError("Invalid score chronology")
    true_cell=truth["first_pair"][0]
    if true_cell.sum()>=24:
        true_cell=23-true_cell[::-1]
    true_id=int(np.flatnonzero((COORD==true_cell).all(1)).item())
    end=min(92,sight)
    r={"seed":row["seed"],"team":team,"first_sight":sight,"first_credit_action":credit,"first_public_credit":t0,
       "match_won":row["match_won"],"points":row["points"][team],"opponent_points":row["points"][1-team],"snapshots":[]}
    # Cross-check all 101 actual credits, including the last before the reset.
    static=truth["points"].ravel()
    for t in range(1,102):
        if t<=100:
            occ=occupied(d,team,t)
        else:
            pos=truth["end_position"][truth["end_live"] & (truth["end_energy"]>=0)]
            occ=np.unique(pos[:,0]*24+pos[:,1])
        inc=int(static[occ].sum()) if t>=int(truth["spawn"]) else 0
        if gain[t-1]-(gain[t-2] if t>1 else 0)!=inc:
            raise ValueError("Grading board and public scoring disagree")
    if not t0<sight:
        return r
    r["after_clue_10"]=int(gain[min(t0+9,100)]-score[t0])
    r["after_clue_10_20"]=int(gain[min(t0+19,100)]-gain[min(t0+9,100)])
    if t0>=end:
        return r
    evidence=ScoreEvidence(d,team,t0)
    for t in range(t0,end):
        t_start = time.process_time()
        evidence.extend(t)
        loc,prob,flat,base_prob=evidence.estimate()
        t_posterior = time.process_time()
        units,protected,options=candidate_paths(d,team,t,t0,prob,row["cfg"]["unit_move_cost"])
        choice=choose(options,prob)
        baseline=choose(options,base_prob)
        TIMINGS.append(((t_posterior-t_start)*1000,(time.process_time()-t_posterior)*1000))
        details=dict(t=t,gain=int(score[t]-score[t-1]),all_points=int(score[t]),free=int(len(units)),
                     free_ids=units.tolist(),possibly_scored_ids=protected.tolist(),legal_targets=len({x[1] for x in options}),
                     full=rank(loc,true_id),reference=rank(flat,true_id),
                     chosen=grade(choice,d,truth,team,t,prob),baseline=grade(baseline,d,truth,team,t,base_prob))
        # Compare mean grade of all feasible distinct targets (one equal vote per cell).
        target_ids=sorted({x[1] for x in options})
        details["possible_target_hit_fraction"]=float(static[target_ids].mean()) if target_ids else None
        r["snapshots"].append(details)
    return r


def describe(rows):
    def fraction(vals):
        return float(np.mean(vals)) if vals else None
    result={}
    pre=[r for r in rows if r["first_public_credit"]<r["first_sight"]]
    nested={"pre_sight":pre, "at_least_ten_turns":[r for r in pre if r["snapshots"]],
        "has_free_other":[r for r in pre if any(s["free"] for s in r["snapshots"])],
        "has_different_route":[r for r in pre if any(s["chosen"] for s in r["snapshots"])]}
    for label,rr in nested.items():
        result[label]={"seats":len(rr),"maps":len({r["seed"] for r in rr}),"side_0":sum(r["team"]==0 for r in rr)}
    result["same_time"]=sum(r["first_public_credit"]==r["first_sight"] and r["first_sight"]<101 for r in rows)
    result["first_sight_earlier"]=sum(r["first_sight"]<r["first_public_credit"] for r in rows)
    result["both_missing"]=sum(r["first_sight"]==r["first_public_credit"]==101 for r in rows)
    result["pre_sight_window"]={"median":float(np.median([r["first_sight"]-r["first_public_credit"] for r in pre])),
                                 "at_least_five":sum(r["first_sight"]-r["first_public_credit"]>=5 for r in pre)}
    samples=[r["snapshots"][0] for r in pre if r["snapshots"]]
    chosen=[next(s for s in r["snapshots"] if s["chosen"]) for r in nested["has_different_route"]]
    for name,batch in (("first_signal",samples),("first_actionable",chosen)):
        quality={}
        for model in ("full","reference"):
            quality[model]={k:fraction([s[model][k] for s in batch]) for k in ("logloss","rank","possible")}
        result[name]=quality
    result["targets"]={}
    for k in ("chosen","baseline"):
        records=[s[k] for s in chosen if s[k]]
        result["targets"][k]={"n":len(records),"true_hits":sum(o["real_score"] for o in records),
            "avg_predictions":fraction([o["prob"] for o in records]),"true_not_used_by_own5":sum(o["real_score"] and o["baseline_used_target5"]==0 for o in records),
            "all_route_visible":sum(o["known_steps"]==o["steps"] for o in records),
            "mean_steps":fraction([o["steps"] for o in records]),
            "hypothetical_uncovered_point_slots":sum(o["available_scoring_slots5"] for o in records),
            "historical_ship_unique_points_same_window":sum(o["baseline_ship_unique_points5"] for o in records),
            "safe_historically_nonproducing":sum(o["baseline_ship_unique_points5"]==0 for o in records),
            "later_observed_turns":sum(o["later_observed_turns"] for o in records),
            "later_hypothetical_slots":sum(o["later_available_slots"] for o in records),
            "later_original_unique":sum(o["later_original_unique"] for o in records)}
    result["equal_feasible_target_hit_rate"]=fraction([s["possible_target_hit_fraction"] for s in chosen])
    result["original_only"]={"total_pre_sight_wins":sum(r["match_won"] for r in pre),
        "mean_points_first_10_after_clue":fraction([r["after_clue_10"] for r in pre]),
        "mean_points_next_10_after_clue":fraction([r["after_clue_10_20"] for r in pre]),
        "seats_with_20_full_future_turns":sum(r["first_public_credit"]<=81 for r in pre),
        "full_window_first_10":fraction([r["after_clue_10"] for r in pre if r["first_public_credit"]<=81]),
        "full_window_next_10":fraction([r["after_clue_10_20"] for r in pre if r["first_public_credit"]<=81])}
    return result


def main():
    ledger=json.loads(gzip.decompress((HERE/"quellen.json.gz").read_bytes()))
    if len(ledger["rows"])!=160 or len(set(ledger["seeds"]))!=80:
        raise ValueError("Incomplete source")
    rows=[]
    for i,r in enumerate(ledger["rows"]):
        rows.append(seat(r))
        if i%16==15:
            print(f"{i+1}/160 geprüft",flush=True)
    (HERE/"diagnose.json.gz").write_bytes(gzip.compress((json.dumps(rows,sort_keys=True,allow_nan=False)+"\n").encode(),mtime=0))
    result=describe(rows)
    result["sha256"]={p.name:sha256(p.read_bytes()).hexdigest() for p in (HERE/"quellen.json.gz",HERE/"diagnose.json.gz",
        HERE.parent/"zielschaetzer/ort.json",HERE/"PLAN.md",HERE/"belegung.py",HERE/"gelegenheit.py",Path(__file__))}
    (HERE/"ergebnis.json").write_text(json.dumps(result,indent=2)+"\n")
    timing=np.asarray(TIMINGS)
    if len(timing):
        speed={n:{"median_ms":float(np.median(timing[:,i])),"p95_ms":float(np.quantile(timing[:,i],.95)),
                  "max_ms":float(timing[:,i].max())} for i,n in enumerate(("posterior","both_route_selections"))}
        speed["snapshots"]=len(timing)
        (HERE/"laufzeit.json").write_text(json.dumps(speed,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
