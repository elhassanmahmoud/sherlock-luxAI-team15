"""Verify the replay totals and identify which sorts of scoring cells account for M3 differences."""
import gzip
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent


def main():
    with gzip.open(HERE/"nachspiele.jsonl.gz","rt") as inp:
        rows=[json.loads(line) for line in inp]
    keyed={(r["seed"],r["team"],r["agent"]):r for r in rows}
    if len(rows)!=16 or len(keyed)!=len(rows):
        raise ValueError("Incomplete or duplicated seat and policy")
    out=[]
    for seed,team,name in sorted(keyed):
        if name!="reference":
            continue
        pair=[keyed[seed,team,n] for n in ("reference","ziel")]
        types=[]
        for r in pair:
            a=np.array(r["points_by_quarter_team_type"])
            points=np.array([p["points"] for p in r["match_end"]])
            if not np.array_equal(a.sum((1,3)),points):
                raise ValueError("Per-type totals contradict match scores")
            bytype=a[2].sum(0)
            types.append(bytype[0]-bytype[1])
        wins=[[m["win"] for m in r["match_end"]] for r in pair]
        counts=[r["knowledge"] for r in pair]
        summaries=[]
        for match,turn in ((1,100),(2,100),(3,0),(3,75)):
            old,new=[next(x for x in arm if x["match"]==match and x["turn"]==turn) for arm in counts]
            summaries.append(dict(match=match,turn=turn,
                confirmed=[old["confirmed"],new["confirmed"]],explored=[old["explored"],new["explored"]],
                relics=[old["relic_locations"],new["relic_locations"]]))
        out.append(dict(seed=seed,team=team,full_win=[int(sum(w)>=2) for w in wins],matches=wins,
                    m3_score=[r["match_end"][2]["points"] for r in pair],
                    m3_net_by_kind=[x.tolist() for x in types],m3_delta_by_kind=(types[1]-types[0]).tolist(),
                    knowledge=summaries))
    (HERE/"vergleich.json").write_text(json.dumps(out,indent=2)+"\n")
    for r in out:
        if len(set(r["full_win"]))>1:
            print(r["seed"],r["team"],r["full_win"],r["m3_score"],r["m3_delta_by_kind"],
                  r["knowledge"][0]["confirmed"],r["knowledge"][2]["confirmed"])


if __name__=="__main__":
    main()
