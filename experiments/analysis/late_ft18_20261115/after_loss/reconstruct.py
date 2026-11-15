"""Combine two recorded continuations on the public, identical first-match result."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def reconstruct(input_file):
    data = input_file.read_bytes()
    pairs = {}
    for line in data.splitlines():
        row = json.loads(line)
        key = row["seed"], row["side"]
        if row["arm"] in pairs.setdefault(key, {}) or row["steps"] != 303:
            raise ValueError(f"Duplicate arm or incomplete game for {key}")
        pairs[key][row["arm"]] = row
    if len(pairs) != 28 or len({k[0] for k in pairs}) != 14 or any(
        {side for s, side in pairs if s == seed} != {"player_0", "player_1"} for seed, _ in pairs
    ):
        raise ValueError("Expected both seats on 14 development maps")
    totals = Counter()
    rescued_maps = set()
    keys = []
    for (seed, side), arms in sorted(pairs.items()):
        if len(arms) != 2 or "v14" not in arms:
            raise ValueError(f"Missing arm for {seed}, {side}")
        base = arms["v14"]
        changed = next(r for name, r in arms.items() if name != "v14")
        first = base["first_match"]
        if first != changed["first_match"] or first["steps"] != 101 or len(first["actions_sha256"]) != 64:
            raise ValueError("Mismatched initial trajectories")
        wins = first["wins_world"]
        if sorted(wins) != [0, 1]:
            raise ValueError("Ambiguous first match")
        switch = wins[int(side[-1])] == 0
        played = changed if switch else base
        delta = int(played["game_win"]) - int(base["game_win"])
        totals.update(games=1, switch=switch, v14_wins=int(base["game_win"]),
                      chosen_wins=int(played["game_win"]), v14_match_wins=base["our_wins"],
                      chosen_match_wins=played["our_wins"], rescued=delta>0, lost=delta<0)
        if delta>0:
            rescued_maps.add(seed)
        keys.append(dict(seed=seed, side=side, switch=switch, initial_wins_world=wins,
                         v14_match_wins=base["our_wins"], chosen_match_wins=played["our_wins"], win_delta=delta))
    gates = dict(three_rescued=totals["rescued"]>=3, two_cards=len(rescued_maps)>=2,
                 at_most_one_lost=totals["lost"]<=1, match_count_holds=totals["chosen_match_wins"]>=totals["v14_match_wins"])
    return dict(source_sha256=hashlib.sha256(data).hexdigest(), counts=totals, rescued_maps=sorted(rescued_maps),
                gates=gates, passes=all(gates.values()), games=keys)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("games", type=Path)
    args = parser.parse_args()
    print(json.dumps(reconstruct(args.games), indent=2))
