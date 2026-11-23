"""Describe visibility subgroups and archived first sightings; used only for interpretation."""
import argparse
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path
import numpy as np


def sightings(directory):
    rows=[]
    for seed,team in ((7261004,0),(7261005,1)):
        for name in ("r3","v16"):
            receipt=json.loads((directory/f"{name}_{seed}_player_{team}.json").read_text())
            archive=directory/receipt["filename"]
            if sha256(archive.read_bytes()).hexdigest()!=receipt["sha256"]:
                raise ValueError("Historical observation identity differs")
            with np.load(archive,allow_pickle=False) as raw:
                mask=np.asarray(raw["relic_nodes_mask"],dtype=bool)
                matchsteps=raw["match_steps"]
                if not np.array_equal(matchsteps[:101],np.arange(101)):
                    raise ValueError("Cannot identify first match")
                found=np.flatnonzero(mask[:101].any(axis=1))
                first=int(found[0]) if found.size else None
                coords=raw["relic_nodes"][first][mask[first]].tolist() if first is not None else []
            rows.append(dict(seed=seed,team=team,package=name,archive=receipt["sha256"],
                             first_seen_in_original_match=first,world_positions=coords,
                             seen_in_first_40_playable_steps=(first is not None and first<=40)))
    return rows


def subgroups(archive):
    with gzip.open(archive,"rt") as stream:
        raw=[json.loads(line) for line in stream]
    lookup={(r["seed"],r["team"],r["opponent"],r["arm"]):r for r in raw}
    if len(raw)!=400 or len(lookup)!=400:
        raise ValueError("Selection must be complete before descriptive analysis")
    result={}
    for sensor in (1,2):
        maps={r["seed"] for r in raw if r["sensor"]==sensor}
        result[sensor]={"maps":len(maps)}
        for opp in ("solution92","kaggle3","v16"):
            c=[lookup[s,t,opp,"staffel"] for s in sorted(maps) for t in (0,1)]
            row={"games":len(c),"candidate_wins":sum(r["game_win"] for r in c),"candidate_matches":sum(r["our_wins"] for r in c)}
            if opp!="v16":
                original=[lookup[r["seed"],r["team"],opp,"original"] for r in c]
                row["original_wins"]=sum(r["game_win"] for r in original)
                row["original_matches"]=sum(r["our_wins"] for r in original)
                row["paired_seats"]=dict(Counter(f'{a["game_win"]}:{b["game_win"]}' for a,b in zip(c,original)))
            result[sensor][opp]=row
    return result


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("type",choices=("sichtung","gruppen"))
    ap.add_argument("input",type=Path)
    a=ap.parse_args()
    print(json.dumps(sightings(a.input) if a.type=="sichtung" else subgroups(a.input),indent=2))
