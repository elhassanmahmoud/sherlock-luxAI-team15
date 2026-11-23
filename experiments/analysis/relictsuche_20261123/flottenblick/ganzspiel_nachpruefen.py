"""Independently check all full-game rows, compute paired metrics, and list all 80 paired seats."""
import csv
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPORT = HERE / "ganzspiel"


def check(ok, message):
    if not ok:
        raise ValueError(message)


def read(row):
    wins = row["matches"]
    return dict(sight=row["sight"], credit=row["credit"], margin70=row["after_70"][0]-row["after_70"][1],
                match1margin=wins[0]["points"][0]-wins[0]["points"][1], match1win=wins[0]["win"], whole=row["win"])


def main():
    series = json.loads((REPORT/"serie.json").read_text())
    public = json.loads((REPORT/"ergebnis.json").read_text())
    frozen = json.loads((HERE/"freigabe_spielpruefung.json").read_text())["frozen"]
    check(all(sha256((HERE.parents[3]/f).read_bytes()).hexdigest()==v for f,v in frozen.items()),"Changed evaluated model")
    cards = series["cards"]
    check(len(cards)==40 and cards==sorted(set(cards)) and min(cards)>=161620000 and max(cards)<161621000,"Bad cards")
    previous = set()
    for r in ("fit","pruefung"):
        previous.update(map(int,json.loads((HERE/f"{r}.json").read_text())["maps_sha256"]))
    short = [json.loads(line) for line in gzip.decompress((HERE/"spielzuege.jsonl.gz").read_bytes()).splitlines()]
    previous.update(r["seed"] for r in short)
    check(not previous.intersection(cards),"Overlapping previous and complete-game cards")
    raw= gzip.decompress((REPORT/"partien.jsonl.gz").read_bytes())
    rows = [json.loads(line) for line in raw.splitlines()]
    keyed = {(r["seed"],r["team"],r["id"],r["opponent"]):r for r in rows}
    check(len(keyed)==len(rows)==240,"Duplicated or missing games")
    for r in rows:
        matches=r["matches"]
        check(r["steps"]==303 and r["sensor"]==1 and r["caught_errors"]==[0,0]
              and r["point_counting_version"]==2 and r["actions_checked"]==[303,303]
              and len(matches)==3 and sum(z["win"] for z in matches)==r["wins"]
              and r["win"]==int(r["wins"]>=2)
              and r["points"]==[sum(z["points"][t] for z in matches) for t in (0,1)], "Bad completion or outcomes")
        events=r["events"]
        check(len(events)<=8 and len({e[1] for e in events})<=1 and (r["id"]!="reference" or not events),"Bad unit interventions")
        if events:
            o=r["opportunity"]
            check(all(16<=e[0]<=83 and o["step"]<=e[0]<o["step"]+8 and e[0]<r["sight"] and
                      e[0]<=r["credit"] and e[1]==o["uid"] and e[2]!=e[3] for e in events),"Bad scout window")
    result = public["candidates"]["flotte"]
    detailed, differences, direct = [],{},[]
    for s in cards:
        per_card={};direct_wins=[]
        for t in (0,1):
            original = keyed[s,t,"reference","solution92"]
            candidate = keyed[s,t,"flotte","solution92"]
            ref, cnn = read(original), read(candidate)
            duel = keyed[s,t,"flotte","v16"]
            record = {"seed":s,"side":t,**{"v16_"+k:v for k,v in ref.items()},**{"cnn_"+k:v for k,v in cnn.items()},
                      "cnn_direct_win":duel["win"],"cnn_changed_solution":len(candidate["events"]),
                      "cnn_changed_direct":len(duel["events"])}
            detailed.append(record)
            for k in ref:
                d=cnn[k]-ref[k]
                per_card.setdefault(k,[]).append(-d if k in ("sight","credit") else d)
            direct_wins.append(duel["win"])
        for k,value in per_card.items():
            differences.setdefault(k,[]).append(np.mean(value))
        direct.append(np.mean(direct_wins))
    bootstrap = public["sampling"]
    idx = np.random.default_rng(bootstrap["seed"]).integers(40,size=(bootstrap["replicates"],40))
    for k,values in {**differences,"direct":direct}.items():
        a=np.array(values)
        ref = result["direct_rate"] if k=="direct" else result["paired"][k]
        check(abs(a.mean()-ref["mean"])<1e-12 and np.allclose(np.percentile(a[idx].mean(1),[2.5,97.5]),
                ref["ci95"],atol=1e-10,rtol=0),f"Mismatch in independent {k} metric")
    with (REPORT/"gepaarte_sitze.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=detailed[0])
        w.writeheader()
        w.writerows(detailed)
    conditions=[np.mean(differences["sight"])>=1, np.mean(differences["credit"])>=0,
                np.mean(differences["margin70"])>=0, np.mean(differences["match1win"])>=0,
                np.mean(differences["whole"])>=0, np.mean(direct)>=.5,
                len({r["seed"] for r in detailed if r["cnn_changed_solution"]})>=8]
    names=("sight_earlier_at_least_one","credit_no_later","margin70_no_worse","match1wins_no_fewer",
           "whole_wins_no_fewer","direct_at_least_half","at_least_8_affected_maps")
    check(dict(zip(names,conditions,strict=True))==result["gates"] and all(conditions)==result["passed"],
          "Different criterion decision")
    audit=dict(game_rows=len(rows),paired_seats=len(detailed),maps=len(cards),independent_metrics=len(differences)+1,
               frozen_files=len(frozen),recomputed_conditions=[bool(x) for x in conditions],bad_game_rows=0,
               raw_archive_sha256=sha256((REPORT/"partien.jsonl.gz").read_bytes()).hexdigest(),
               paired_seats_sha256=sha256((REPORT/"gepaarte_sitze.csv").read_bytes()).hexdigest())
    (REPORT/"nachpruefung.json").write_text(json.dumps(audit,indent=2)+"\n")
    print(json.dumps(audit),flush=True)


if __name__=="__main__":
    main()
