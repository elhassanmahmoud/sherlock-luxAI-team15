"""Evaluate the fixed 40-map paired movement screens with one vote per complete game."""
import argparse
from collections import defaultdict
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np


def run(folder, out, start, selected=None):
    cards = np.arange(start, start + 40) if selected is None else np.asarray(selected, dtype=np.int64)
    if len(cards) != 40 or len(np.unique(cards)) != 40:
        raise ValueError("Expected exactly 40 unique fixed maps")
    pairs = defaultdict(dict)
    direct = []
    raw = []
    names = ("solution92","kaggle3")
    for seed_np in cards:
        seed = int(seed_np)
        for side in ("player_0", "player_1"):
            for rival in (*names,"v16"):
                for arm in (("adviser",) if rival=="v16" else ("original","adviser")):
                    p = folder / f"{seed}_{side}_{rival}_{arm}.json"
                    row = json.loads(p.read_text())
                    if ((row["seed"],row["side"],row["opponent"],row["arm"]) != (seed,side,rival,arm) or
                            row["steps"] != 303 or row["point_counting_version"] != 2 or
                            row["our_wins"]+row["opp_wins"] != 3 or row["game_win"] != int(row["our_wins"]>=2)):
                        raise ValueError(f"Invalid seat {p.name}")
                    raw.append(row)
                    if rival == "v16":
                        direct.append(row)
                    else:
                        pairs[rival,seed,side][arm] = row
    if len(raw)!=400 or len({r["model"] for r in raw})!=1:
        raise ValueError("Incomplete screen or mixed candidates")
    counts = {}
    rng = np.random.default_rng(231121)
    draws = rng.integers(0,40,(10000,40))
    for rival in names:
        by_card = []
        gains=losses=changes=0
        sums=defaultdict(lambda: defaultdict(int))
        for s in cards:
            delta=[]
            for side in ("player_0","player_1"):
                v,c = (pairs[rival,int(s),side][k] for k in ("original","adviser"))
                if c["changes"]==0 and any(v[k]!=c[k] for k in ("our_wins","our_points","opp_points")):
                    raise ValueError("Inactive candidate diverged")
                changes+=int(c["changes"]>0)
                diff=c["game_win"]-v["game_win"]
                gains+=int(diff>0)
                losses+=int(diff<0)
                delta.append(diff)
                for key, r in (("original",v),("adviser",c)):
                    for col in ("game_win","our_wins","our_points","opp_points","changes"):
                        sums[key][col]+=int(r[col])
            by_card.append(np.mean(delta))
        ci=(100*np.percentile(np.array(by_card)[draws].mean(axis=1),[2.5,97.5])).tolist()
        counts[rival]=dict(games_per_arm=80, by_arm=sums, seats_changed=changes, new_wins=gains,
                           lost_wins=losses, delta_pp=(gains-losses)*1.25, paired_ci95_pp=ci)
    n=sum(r["game_win"] for r in direct)
    counts["direct"]=dict(wins=int(n),games=80,active=sum(r["changes"]>0 for r in direct),
                          own_match_wins=sum(r["our_wins"] for r in direct),
                          by_side={s:sum(r["game_win"] for r in direct if r["side"]==s) for s in ("player_0","player_1")})
    deltas=[counts[r]["new_wins"]-counts[r]["lost_wins"] for r in names]
    gates=dict(solution=deltas[0]>=0,kaggle=deltas[1]>=0,additional_wins=sum(deltas)>0,direct=n>=40)
    data=gzip.compress(("\n".join(json.dumps(r,sort_keys=True) for r in raw)+"\n").encode(),mtime=0)
    (out/"auswahl_partien.jsonl.gz").write_bytes(data)
    result=dict(start=start, seeds=cards.tolist(), maps=40, actual_games=len(raw), model=raw[0]["model"], raw_sha256=sha256(data).hexdigest(),
                opponents=counts, gates=gates, qualifies=all(gates.values()))
    (out/"auswahl_ergebnis.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("folder",type=Path)
    cli.add_argument("out",type=Path)
    cli.add_argument("start",type=int)
    args=cli.parse_args()
    run(args.folder,args.out,args.start)
