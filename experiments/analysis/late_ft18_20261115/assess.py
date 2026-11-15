"""Summarize the preregistered paired Solution development panel from finished games."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def read_pairs(directory):
    complete = json.loads((directory / "completed.json").read_text())
    for name in ("manifest", "pairs", "games"):
        file = directory / (name + (".json" if name == "manifest" else ".jsonl"))
        if hashlib.sha256(file.read_bytes()).hexdigest() != complete[name + "_sha256"]:
            raise ValueError(f"Checksum differs for {file}")
    manifest = json.loads((directory / "manifest.json").read_text())
    seeds = set(manifest["seeds"])
    expected = {(seed, side) for seed in seeds for side in ("player_0", "player_1")}
    if len(seeds) != 14 or complete["pairs"] != 28 or complete["games"] != 56:
        raise ValueError("Incomplete development panel")
    games = collections.defaultdict(dict)
    for line in (directory / "games.jsonl").read_text().splitlines():
        row = json.loads(line)
        key = row["seed"], row["side"]
        if (row["arm"] in games[key] or row["opponent"] != "solution92" or row["steps"] != 303
                or row["our_wins"] + row["opp_wins"] != 3 or row["game_win"] != (row["our_wins"] >= 2)):
            raise ValueError(f"Invalid game {key}")
        games[key][row["arm"]] = row
    if set(games) != expected:
        raise ValueError("Game keys differ from the manifest")
    seen = set()
    for line in (directory / "pairs.jsonl").read_text().splitlines():
        pair = json.loads(line)
        key = pair["seed"], pair["side"]
        if key in seen or set(games[key]) != {"v14", "ft18_movement"}:
            raise ValueError(f"Duplicate or incomplete pair {key}")
        seen.add(key)
        base, variant = games[key]["v14"], games[key]["ft18_movement"]
        if (not pair["same_first_match"] or base["first_match"] != variant["first_match"]
                or base["first_match"]["steps"] != 101 or base["historical_v14_differences"]
                or any(base[field] != int(val) for field, val in pair["historical_v14"].items())
                or variant["interventions"] != pair["interventions"]
                or variant["movement_by_match"][0]["before_rules_changed"] != 0):
            raise ValueError(f"Invalid first-match parity, historical control or votes on {key}")
    if seen != expected:
        raise ValueError("Missing pairs")
    return games


def summarize(directory):
    games = read_pairs(directory)
    rescued, lost = [], []
    totals = {arm: collections.Counter() for arm in ("v14", "ft18_movement")}
    for (seed, side), arms in games.items():
        for arm, game in arms.items():
            totals[arm].update(wins=game["game_win"], matches=game["our_wins"], interventions=game["interventions"])
        base, variant = arms["v14"]["game_win"], arms["ft18_movement"]["game_win"]
        if base != variant:
            (rescued if variant else lost).append(dict(seed=seed, side=side))
    if totals["v14"]["wins"] != 16:
        raise ValueError("Historical 16 wins and 12 losses were not reproduced")
    gates = dict(three_rescues=len(rescued) >= 3, two_maps=len({row["seed"] for row in rescued}) >= 2,
                 at_most_one_new_loss=len(lost) <= 1,
                 match_total=totals["ft18_movement"]["matches"] >= totals["v14"]["matches"])
    return dict(totals=totals, rescued=rescued, lost=lost, gates=gates, advance=all(gates.values()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(summarize(parser.parse_args().directory), indent=2))
