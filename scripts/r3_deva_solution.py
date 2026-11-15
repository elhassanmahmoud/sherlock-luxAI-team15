"""Check the V14 replay and compare R3 with the published Dev A solutions on identical seats."""
import argparse
import csv
import json
from pathlib import Path

from scripts.final_battle_assess import KAGGLE, bounds
from scripts.final_battle_compare import digest
from scripts.final_battle_select import SEATS, checked_run_files

MAPS = range(7150000, 7150100)
SEEDS_SHA = "18f39c9d86a6809a4ac6008bf43143ea29bb86fd17709d35984ac6b9615acb8d"
TABLES = {
    "v14": ("v14_ref_devA.csv", "589ebf326adbb2535bd0079b603d914a47b7b2987b2bdf8dd83ba9c2bcefb25f"),
    "v3_points": ("student_hyb_v3_points.csv", "0ef267b05fddf6816485d696e0794ba6b28cd13e056585db3d6e39dde5444e64"),
    "v4_mixed": ("student_hyb_v4_mixed.csv", "dab8ad9200433eb46b311992ef940e8110aeaf520ef4b1995b81b7403b80381c"),
}


def reference_tables(base):
    seed_file = base / "seeds_devA.json"
    if digest(seed_file) != SEEDS_SHA or json.loads(seed_file.read_bytes()) != list(MAPS):
        raise ValueError("Unexpected Dev A maps")
    tables = {}
    for tag, (name, checksum) in TABLES.items():
        path = base / name
        if digest(path) != checksum:
            raise ValueError(f"Unexpected published table: {path}")
        with path.open(newline="") as stream:
            table = [row for row in csv.DictReader(stream) if row["opponent"] == "solution92"]
        rows = {}
        for row in table:
            score = tuple(int(row[k]) for k in ("game_win", "our_wins", "opp_wins", "our_points", "opp_points", "steps"))
            won, own, rival, _, _, steps = score
            if steps != 303 or own not in range(4) or own + rival != 3 or won != int(own > rival):
                raise ValueError(f"Invalid course outcome in {name}")
            rows[int(row["seed"]), row["side"]] = score
        if len(table) != len(rows) or rows.keys() != {(s, side) for s in MAPS for side in SEATS}:
            raise ValueError(f"Invalid seat pairing in {name}")
        tables[tag] = rows
    return tables


def read_games(study, arm):
    reproduction = arm == "v14"
    policy, seats, directory = ("v14", MAPS[:4], "reproduction") if reproduction else ("selective_movement", MAPS, "r3")
    root = study / "dev_a_solution" / directory
    games, actual, files = checked_run_files(root, policy, seats, ("solution92",))
    original = json.loads((study / "confirmation" / arm / "manifest.json").read_bytes())
    if (any(actual[k] != original[k] for k in ("model", "weights", "engine", "candidate"))
            or actual["sources"] != {k: v for k, v in original["sources"].items() if not k.startswith(KAGGLE)}):
        raise ValueError(f"{directory} differs from the original, independent R3 comparison")
    scores = {(seed, side): tuple(int(row[k]) for k in ("result", "wins", "losses", "points", "opp_points", "steps"))
              for (_, seed, side), row in games.items()}
    return scores, files


def assess(study, published, replay_only=False):
    refs = reference_tables(published)
    replay, replay_files = read_games(study, "v14")
    if any(refs["v14"][key] != score for key, score in replay.items()):
        raise ValueError("V14 replay did not exactly reproduce all scores")
    result = dict(reproduced=len(replay), replay_files=replay_files)
    if replay_only:
        return result
    candidate, files = read_games(study, "r3")
    result.update(scope="Shared development cards, no promotion decision", paired_solution_seats=len(candidate),
                  candidate_wins=sum(v[0] for v in candidate.values()), candidate_matches=sum(v[1] for v in candidate.values()),
                  candidate_files=files, references={})
    for tag, rows in refs.items():
        delta = {key: value[0] - rows[key][0] for key, value in candidate.items()}
        per_map = [sum(delta[s, side] for side in SEATS) / len(SEATS) for s in MAPS]
        result["references"][tag] = dict(table_sha256=TABLES[tag][1], wins=sum(v[0] for v in rows.values()),
            matches=sum(v[1] for v in rows.values()), gained=sorted(k for k,v in delta.items() if v > 0),
            lost=sorted(k for k,v in delta.items() if v < 0), difference=sum(per_map) / len(MAPS), ci95=bounds(per_map))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--study", type=Path, required=True)
    p.add_argument("--tables", type=Path, required=True)
    p.add_argument("--replay-only", action="store_true")
    args = p.parse_args()
    print(json.dumps(assess(args.study, args.tables, args.replay_only), indent=2, allow_nan=False))
