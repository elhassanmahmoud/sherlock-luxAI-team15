"""Assess the actual post-victory selector and the two prespecified map groups."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0,str(HERE.parents[4]))
from scripts.ft18_after_win import reference_panel, REFERENCE_SHA


def outcome(games, seeds):
    differences = []
    rescued, lost = [], []
    v14_wins = chosen_wins = v14_matches = chosen_matches = switches = 0
    for seed in seeds:
        deltas = []
        for side in ("player_0","player_1"):
            base, candidate = (games[seed,side][k] for k in ("v14","ft18_after_win"))
            won = bool(base["first_match"]["wins_world"][int(side[-1])])
            if won != candidate["switch_after_first_win"]:
                raise ValueError("Wrong first-match observation for seat")
            if not won and any(base[k] != candidate[k] for k in (
                    "our_wins", "opp_wins", "our_points", "opp_points","unit_steps","sap_attempts","sap_hits")):
                raise ValueError("Outcomes differed on a seat where V14 played throughout")
            switches += won
            before, after = base["game_win"], candidate["game_win"]
            v14_wins += before
            chosen_wins += after
            v14_matches += base["our_wins"]
            chosen_matches += candidate["our_wins"]
            if before != after:
                (rescued if after else lost).append([seed,side])
            deltas.append(after-before)
        differences.append(sum(deltas)/2)
    rng=np.random.default_rng(2711)
    draws=rng.choice(differences, size=(10000,len(seeds)), replace=True).mean(axis=1)
    return dict(maps=len(seeds), games=2*len(seeds), switches=switches, v14_wins=v14_wins, chosen_wins=chosen_wins,
                v14_matches=v14_matches, chosen_matches=chosen_matches, rescued=rescued, lost=lost,
                win_difference_ci95=np.quantile(draws,[.025,.975]).tolist())


def assess(directory):
    # Reuse the same file hashes, matched command-prefix and per-game outcome checks as the preceding study.
    spec=importlib.util.spec_from_file_location("ft18_pair_check", HERE.parents[1]/"assess.py")
    checker=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    history=reference_panel()
    games=checker.read_pairs(directory, "ft18_after_win", 24)
    manifest=json.loads((directory/"manifest.json").read_text())
    if set(games)!=set(history) or manifest.get("historical_csv_sha256")!=REFERENCE_SHA:
        raise ValueError("Unexpected map panel or historical results")
    for key,record in history.items():
        base=games[key]["v14"]
        if any(base[k]!=int(record[k]) for k in ("our_wins","opp_wins","game_win","our_points","opp_points")):
            raise ValueError("Historical baseline did not reproduce")
    seeds=sorted({s for s,_ in history})
    loss=[s for s in seeds if any(history[s,p]["game_win"]=="0" for p in ("player_0","player_1"))]
    all_rows=outcome(games,seeds)
    gates=dict(three_rescued=len(all_rows["rescued"])>=3, two_maps=len({s for s,_ in all_rows["rescued"]})>=2,
               at_most_one_lost=len(all_rows["lost"])<=1, match_sum=all_rows["chosen_matches"]>=all_rows["v14_matches"])
    return dict(whole_panel=all_rows, prior_loss_maps=outcome(games,loss),
                prior_two_win_maps=outcome(games,sorted(set(seeds)-set(loss))), gates=gates, advance=all(gates.values()))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    print(json.dumps(assess(parser.parse_args().directory),indent=2))
