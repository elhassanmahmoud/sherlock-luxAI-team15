"""Reconcile the original 200-map Dev H panel at game-seat grain."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
DEV=HERE.parents[1]/"devh_20261117"


def load(name):
    path=DEV/f"{name}_devH.csv"
    with path.open() as f: items=list(csv.DictReader(f))
    data={}
    for r in items:
        k=(int(r["seed"]),r["side"],r["opponent"])
        if k in data or int(r["steps"])!=303 or int(r["point_counting_version"])!=2 or int(r["our_wins"])+int(r["opp_wins"])!=3:
            raise ValueError(f"Invalid archival row {k}")
        data[k]=r
    if set(data)!={(s,p,o) for s in range(7266000,7266200) for p in ("player_0","player_1") for o in ("solution92","kaggle3")}:
        raise ValueError("Incomplete Dev H panel")
    return data,hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    v,vs=load("k"); w,ws=load("wechsel")
    groups={}
    flips={}
    for o in ("solution92","kaggle3"):
        rows=[k for k in sorted(v) if k[2]==o]; c=Counter(); changed=[]
        for k in rows:
            a,b=int(v[k]["game_win"]),int(w[k]["game_win"])
            c[{(0,0):"both_lost",(1,1):"both_won",(1,0):"v16_only",(0,1):"wechsel_only"}[a,b]]+=1
            c["v16_match_wins"]+=int(v[k]["our_wins"]); c["wechsel_match_wins"]+=int(w[k]["our_wins"])
            if (v[k]["our_points"],v[k]["opp_points"])!=(w[k]["our_points"],w[k]["opp_points"]):
                c["different_point_totals"]+=1
            if a!=b: changed.append({"seed":k[0],"side":k[1],"winner":"wechsel" if b else "v16"})
        groups[o]=dict(c); flips[o]=changed
    return dict(source_sha256={"K":vs,"WECHSEL":ws},paired=groups,discordant=flips)


if __name__=="__main__":print(json.dumps(run(),indent=2))
