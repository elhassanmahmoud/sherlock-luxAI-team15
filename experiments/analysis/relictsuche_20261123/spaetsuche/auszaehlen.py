"""Describe fixed late policies on the same held-out public opportunities."""
import gzip
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent


def summarize():
    result=json.loads((HERE/"test/ergebnis.json").read_text())
    with gzip.open(HERE/"test/eroeffnungen.jsonl.gz","rt") as f:
        rows=[json.loads(line) for line in f]
    games={(r["seed"],r["team"],r["opponent"],r["arm"]):r for r in rows if r["eligible"]}
    chosen={(r["seed"],r["team"],r["opponent"]):r["chosen"] for r in result["rows"]}
    report={}
    for o in ("solution92","v16","both"):
        keys=[k for k in chosen if o=="both" or k[-1]==o]
        report[o]={}
        for arm in ("reference","route","ziel","learned"):
            active=0; win=0; no_sight=0; no_credit=0; changed_turns=0
            earlier=later=0
            effects=[]
            for k in keys:
                b=games[(*k,"reference")]
                a=games[(*k,chosen[k] if arm=="learned" else arm)]
                active+=bool(a["events"]);changed_turns+=len(a["events"])
                win+=a["match"]["win"]
                no_sight+=a["sight"]==101;no_credit+=a["credit"]==101
                diff=b["sight"]-a["sight"]
                earlier+=diff>0;later+=diff<0
                effects.append([diff,b["credit"]-a["credit"],
                    (a["after70"][0]-a["after70"][1])-(b["after70"][0]-b["after70"][1]), a["match"]["win"]-b["match"]["win"]])
            array=np.asarray(effects,dtype=float)
            rng=np.random.default_rng(231123)
            # Each held-out map carries one seat. Keep equal prespecified opponent weights in the combined interval.
            strata=sorted({k[-1] for k in keys})
            samples=[]
            for opponent in strata:
                sub=array[[k[-1]==opponent for k in keys]]
                draws=rng.integers(0,len(sub),size=(20000,len(sub)))
                samples.append(sub[draws].mean(axis=1))
            bounds=np.quantile(np.mean(samples,axis=0),[.025,.975],axis=0)
            report[o][arm]=dict(maps=len(keys),changed_maps=active,changed_turns=changed_turns,match1_wins=win,
                                no_sight=no_sight,no_credit=no_credit,sight_earlier=earlier,sight_later=later,
                                mean_effect=array.mean(axis=0).tolist(),ci95=bounds.T.tolist())
    return report


if __name__=="__main__":
    print(json.dumps(summarize(),indent=2))
