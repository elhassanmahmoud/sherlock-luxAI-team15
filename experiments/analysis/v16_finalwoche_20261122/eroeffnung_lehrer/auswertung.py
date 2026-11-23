"""Vergleicht beide Spieler paarweise auf allen 16 vorher festgelegten Startseiten."""
import argparse
import json
from pathlib import Path
from statistics import median


HERE=Path(__file__).resolve().parent


def ordered(left,right):
    return {"earlier":sum(a<b for a,b in zip(left,right,strict=True)),
            "same":sum(a==b for a,b in zip(left,right,strict=True)),
            "later":sum(a>b for a,b in zip(left,right,strict=True)),
            "median_v16":median(right),"median_teacher":median(left),
            "median_v16_minus_teacher":median(b-a for a,b in zip(left,right,strict=True))}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=HERE,help="Ordner mit Teilarchiven")
    folder=parser.parse_args().out
    records=[r for idx in (0,1) for r in map(json.loads,(folder/f"teil_{idx}.jsonl").read_text().splitlines())]
    entries={(r["seed"],r["side"],r["arm"]):r for r in records}
    seeds=sorted({r["seed"] for r in records})
    keys=[(s,p) for s in seeds for p in ("player_0","player_1")]
    if len(seeds)!=8 or len(records)!=32 or len(entries)!=32 or set(entries)!={(*key,a) for key in keys for a in ("v16","kaggle3")}:
        raise ValueError("Unvollständige Paare")
    def score(r,key):return r[key][0]-r[key][1]
    output=dict(seeds=seeds)
    for metric in ("first_relic","first_own_score"):
        data=[[entries[k+(arm,)][metric] for k in keys] for arm in ("kaggle3","v16")]
        # Beobachtung bis Zug 100 eingeschlossen. 101 ist eine vorab definierte Vergleichskonvention.
        out=ordered(*[[v if v is not None else 101 for v in column] for column in data])
        out["missed_teacher"],out["missed_v16"]=map(lambda xs:sum(x is None for x in xs),data)
        output[metric]=out
    for metric in ("after_70","match_score"):
        values={a:[score(entries[k+(a,)],metric) for k in keys] for a in ("v16","kaggle3")}
        delta=[k-v for k,v in zip(values["kaggle3"],values["v16"],strict=True)]
        output[metric]={"median_v16":median(values["v16"]),"median_teacher":median(values["kaggle3"]),
                         "median_delta":median(delta),"teacher_margin_better_equal_worse":[sum(x>0 for x in delta),delta.count(0),sum(x<0 for x in delta)]}
    output["match_wins"]={a:sum(entries[k+(a,)]["match_win"] for k in keys) for a in ("v16","kaggle3")}
    output["pair_winners"]={name:sum((entries[k+("v16",)]["match_win"],entries[k+("kaggle3",)]["match_win"])==pair for k in keys)
                            for name,pair in (("both",(1,1)),("only_v16",(1,0)),("only_teacher",(0,1)),("neither",(0,0)))}
    for r in records:
        u,v=r["match_score"]
        if r["frames"]!=101 or (u!=v and (u>v)!=bool(r["match_win"])):
            raise ValueError("Widerspruch Punkte/Matchsieg")
    (folder/"ergebnis.json").write_text(json.dumps(output,indent=2)+"\n")
    print(json.dumps(output))


if __name__=="__main__":
    main()
