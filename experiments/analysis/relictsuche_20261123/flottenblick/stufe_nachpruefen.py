"""Reconstruct all paired endpoints and intervals from the complete held-out archive."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FOLDER = {"confirm": "bestaetigung", "general": "allgemein"}
ARMS = (("reference", "solution92"), ("flotte", "solution92"), ("flotte", "v16"))
ORIGINAL = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"


def check(ok, label):
    if not ok:
        raise ValueError(label)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fields(row):
    match = row["matches"][0]
    a, b = row["after_70"]
    c, d = match["points"]
    return dict(sight=row["sight"], credit=row["credit"], own70=a, opp70=b, margin70=a-b,
                match1points=c, match1opp=d, match1margin=c-d, match1win=match["win"],
                whole=row["win"], all_match_wins=sum(m["win"] for m in row["matches"]))


def prior_maps(phase):
    raw = [json.loads(l) for l in gzip.decompress((HERE/"spielzuege.jsonl.gz").read_bytes()).splitlines()]
    used = {r["seed"] for r in raw}
    for name in ("fit","pruefung"):
        used.update(map(int,json.loads((HERE/f"{name}.json").read_text())["maps_sha256"]))
    for name in (["ganzspiel"] if phase == "confirm" else ["ganzspiel","bestaetigung"]):
        used.update(json.loads((HERE/name/"serie.json").read_bytes())["cards"])
    return used


def audit(phase):
    out = HERE / FOLDER[phase]
    series = json.loads((out/"serie.json").read_bytes())
    result = json.loads((out/"ergebnis.json").read_bytes())
    candidate = result["candidates"]["flotte"]
    sources = series["common"]
    cards = series["cards"]
    check(result["phase"]==series["phase"]==phase and
          sources["release"]==ORIGINAL and sources["post_screen"]["plan"]==digest(HERE/"BESTAETIGUNGSPLAN.md") and
          sources["post_screen"]["runner"]==digest(HERE/"weiterpruefen.py"),"Stage or signed source mismatch")
    frozen = json.loads((HERE/"freigabe_spielpruefung.json").read_text())["frozen"]
    check(series["identities"]["flotte"]["candidate"]["files"]==frozen and
          all(digest(ROOT/f)==v for f,v in frozen.items()), "Evaluated model changed")
    expected_maps = 120 if phase=="confirm" else 160
    check(len(cards)==expected_maps and cards==sorted(set(cards)) and not prior_maps(phase).intersection(cards),"Card selection")
    if phase=="confirm":
        check(all(162200000<=s<162201000 for s in cards),"Confirmation seed range")
    else:
        check(cards==list(range(162210000,162210160)),"General seed range")
    with gzip.open(out/"partien.jsonl.gz","rt") as f:
        raw = [json.loads(l) for l in f]
    rows = {(r["seed"],r["team"],r["id"],r["opponent"]):r for r in raw}
    check(set(rows)=={(s,t,k,o) for s in cards for t in (0,1) for k,o in ARMS} and
          len(raw)==len(rows)==expected_maps*6,"Game grid or duplicate")
    for r in raw:
        m=r["matches"]
        check(r["phase"]==phase and r["point_counting_version"]==2 and r["steps"]==303 and
              r["actions_checked"]==[303,303] and r["caught_errors"]==[0,0] and len(m)==3 and
              all(x["win"] in (0,1) for x in m) and r["wins"]==sum(x["win"] for x in m) and
              r["win"]==int(r["wins"]>=2) and r["points"]==[sum(x["points"][t] for x in m) for t in (0,1)] and
              (phase=="general" or r["sensor"]==1), "Incomplete game")
        e = r["events"]
        if e:
            event=r["opportunity"]
            check(r["id"]=="flotte" and r["sensor"]==1 and len(e)<=8 and
                  all(16<=z[0]<=83 and event["step"]<=z[0]<event["step"]+8 and z[0]<r["sight"] and z[0]<=r["credit"]
                      and z[1]==event["uid"] and z[2]!=z[3] for z in e),"Illegal scout")
    detailed = []
    metrics = {}
    for seed in cards:
        per_card = {}
        for team in (0,1):
            ref, cnn, direct = [rows[seed,team,k,o] for k,o in ARMS]
            check(ref["sensor"]==cnn["sensor"]==direct["sensor"],"Wrong reset")
            if not cnn["events"]:
                check(all(ref[f]==cnn[f] for f in ("action_hash","matches","points","sight","credit","after_70","win")),"No-intervention parity")
            v,c=fields(ref),fields(cnn)
            detail={"seed":seed,"side":team,"sensor":ref["sensor"],**{"v16_"+k:x for k,x in v.items()},
                    **{"cnn_"+k:x for k,x in c.items()},"cnn_direct_win":direct["win"],
                    "cnn_changed_solution":len(cnn["events"]),"cnn_changed_direct":len(direct["events"])}
            detailed.append(detail)
            for k in v:
                per_card.setdefault(k,[]).append((v[k]-c[k]) if k in ("sight","credit") else (c[k]-v[k]))
            per_card.setdefault("direct",[]).append(direct["win"])
        for k,pair in per_card.items():
            metrics.setdefault(k,[]).append(pair)
    check(result["sampling"]=={"seed":231123,"replicates":20000,"unit":"map, both seats"},"Sampling method")
    draws=np.random.default_rng(231123).integers(len(cards),size=(20000,len(cards)))
    verified={}
    for field,pairs in metrics.items():
        v=np.asarray(pairs)
        means=v.mean(1)
        point=float(means.mean())
        ci=np.quantile(means[draws].mean(1),[.025,.975])
        official=candidate["direct_rate"] if field=="direct" else candidate["paired"][field]
        check(abs(official["mean"]-point)<1e-12 and np.allclose(official["ci95"],ci,rtol=0,atol=1e-10),f"Paired statistic {field}")
        if field!="direct":
            check(official["positive_seats"]==int((v>0).sum()) and official["negative_seats"]==int((v<0).sum())
                  and official["equal_seats"]==int((v==0).sum()) and np.allclose(official["by_seat"],v.mean(0),rtol=0,atol=1e-10),
                  f"Seat statistics {field}")
        verified[field] = (point,float(ci[0]),float(ci[1]))
    p = {k:x[0] for k,x in verified.items()}
    lo = {k:x[1] for k,x in verified.items()}
    if phase=="confirm":
        gates={"sight_earlier_at_least_one":p["sight"]>=1.0,"credit_no_later":p["credit"]>=0,
               "margin70_no_worse":p["margin70"]>=0,"match1wins_no_fewer":p["match1win"]>=0,
               "whole_wins_no_fewer":p["whole"]>=0,"sight_lower_positive":lo["sight"]>0}
        passed=all(gates.values())
    else:
        gates={"route_a_external_lower_above_0":lo["whole"]>0,"route_a_direct_mean_at_least_half":p["direct"]>=.5,
               "route_a_direct_lower_at_least_45pct":lo["direct"]>=.45,"route_b_direct_lower_above_half":lo["direct"]>.5,
               "route_b_external_lower_at_least_minus_1pp":lo["whole"]>=-.01}
        passed=all(v for k,v in gates.items() if k.startswith("route_a")) or all(v for k,v in gates.items() if k.startswith("route_b"))
    check(gates==candidate["gates"] and passed==candidate["passed"] and result["nominee"]==("flotte" if passed else None),"Stage decision")
    for key,(agent,opponent) in zip(("reference","solution","direct"),ARMS,strict=True):
        rset=[r for r in raw if r["id"]==agent and r["opponent"]==opponent]
        section=result["reference"] if key=="reference" else candidate[key]
        for subset,summary in [(rset,section["all"])]+[([r for r in rset if r["team"]==t],section["by_seat"][str(t)]) for t in (0,1)]:
            m=[fields(r) for r in subset]
            check(summary["wins"]==sum(x["whole"] for x in m) and summary["match1wins"]==sum(x["match1win"] for x in m)
                  and summary["changes"]==sum(len(r["events"]) for r in subset) and summary["changed_maps"]==len({r["seed"] for r in subset if r["events"]})
                  and summary["changed_games"]==sum(bool(r["events"]) for r in subset)
                  and all(abs(summary["means"][f]-np.mean([x[f] for x in m]))<1e-12 for f in m[0]),"Raw summaries")
    with (out/"gepaarte_sitze.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=detailed[0])
        writer.writeheader()
        writer.writerows(detailed)
    evidence=dict(passed=passed,bad_rows=0,phase=phase,maps=len(cards),paired_seats=len(detailed),complete_games=len(raw),
                  checked_unit_command_rows=len(raw)*303*2*16,recomputed_metrics=len(verified),frozen_files=len(frozen),
                  conditions=gates,raw_sha256=digest(out/"partien.jsonl.gz"),paired_csv_sha256=digest(out/"gepaarte_sitze.csv"),
                  outcome_sha256=digest(out/"ergebnis.json"),auditor_sha256=digest(Path(__file__)))
    (out/"nachpruefung.json").write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(evidence),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase",choices=FOLDER)
    audit(p.parse_args().phase)
