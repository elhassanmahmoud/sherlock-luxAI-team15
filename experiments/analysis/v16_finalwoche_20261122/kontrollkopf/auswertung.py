"""Inspect 200 completed games, pairing seats first and resampling whole maps."""
import json
from pathlib import Path
import sys
from collections import Counter

import numpy as np

HERE = Path(__file__).resolve().parent
SEEDS = range(19377000,19377020)
SIDES = ("player_0","player_1")


def metrics(v):
    return {f:sum(r[key] for r in v) for f,key in (("games_won","game_win"),("matches_won","our_wins"),
                                                      ("points_for","our_points"),("points_against","opp_points"))}


def bootstrap(per_map, draws):
    v = np.asarray(per_map, dtype=float)
    bounds = np.percentile(v[draws].mean(axis=1), [2.5,97.5])
    return {"estimate":float(v.mean()), "map_bootstrap_95":bounds.tolist()}


def summarize(file):
    rows = [json.loads(line) for line in file.read_text().splitlines()]
    keys = [(r["seed"],r["side"],r["opponent"],r["arm"]) for r in rows]
    expected = {(s,side,o,a) for s in SEEDS for side in SIDES for o in ("kaggle3","solution92","v16")
                for a in (("kontrolle",) if o=="v16" else ("kontrolle","original"))}
    if set(keys)!=expected or len(keys)!=len(expected):
        raise ValueError("Missing or duplicate seats")
    for r in rows:
        if (r["steps"]!=303 or r["point_counting_version"]!=2 or r["our_wins"]+r["opp_wins"]!=3
                or r["game_win"]!=int(r["our_wins"]>=2)):
            raise ValueError("Corrupt game")
    lookup = dict(zip(keys,rows))
    counts, comparisons = {}, {}
    rng = np.random.default_rng(221122)
    draws = rng.integers(0,len(SEEDS),(20000,len(SEEDS)))
    for o in ("solution92","kaggle3","v16"):
        counts[o] = {}
        for arm in (("kontrolle",) if o=="v16" else ("original","kontrolle")):
            v = [r for r in rows if r["arm"]==arm and r["opponent"]==o]
            counts[o][arm] = {"n":len(v),**metrics(v),
                               "sides":{side:metrics([r for r in v if r["side"]==side]) for side in SIDES}}
        if o=="v16":
            direct = [np.mean([lookup[s,side,o,"kontrolle"]["game_win"] for side in SIDES]) for s in SEEDS]
            comparisons[o] = {"win_rate":bootstrap(direct,draws)}
            continue
        discordance = Counter()
        by_map = []
        for seed in SEEDS:
            diffs = []
            for side in SIDES:
                orig = lookup[seed,side,o,"original"]
                ctrl = lookup[seed,side,o,"kontrolle"]
                outcome = (orig["game_win"],ctrl["game_win"])
                discordance[{(0,0):"both_lost",(1,0):"original_only",(0,1):"control_only",(1,1):"both_won"}[outcome]] += 1
                diffs.append([ctrl[k]-orig[k] for k in ("game_win","our_wins")])
            by_map.append(np.mean(diffs,axis=0))
        per_map = np.stack(by_map)
        comparisons[o] = {"seats": dict(discordance), "win_rate_difference":bootstrap(per_map[:,0],draws),
                          "matches_per_game_difference":bootstrap(per_map[:,1],draws)}
    sol, kag, duel = counts["solution92"], counts["kaggle3"], counts["v16"]
    gates = {"solution_games":sol["kontrolle"]["games_won"]>=sol["original"]["games_won"],
             "kaggle_games":kag["kontrolle"]["games_won"]>=kag["original"]["games_won"],
             "kaggle_matches":kag["kontrolle"]["matches_won"]>kag["original"]["matches_won"],
             "direct":duel["kontrolle"]["games_won"]>20}
    return dict(n=len(rows),counts=counts,contrasts=comparisons,gates=gates,passed=all(gates.values()))


if __name__=="__main__":
    result = summarize(Path(sys.argv[1]))
    print(json.dumps(result,indent=2))
