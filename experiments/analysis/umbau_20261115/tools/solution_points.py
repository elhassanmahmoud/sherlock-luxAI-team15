"""Paired Solution outcome switches and scoring, from already published complete games."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


DEV = "kaggle3_20261115"
STUDY = "umbau_20261115"
PANELS = {
    "Dev A": (7150000, 100, DEV+"/v14_ref_devA.csv", DEV+"/student_hyb_v4_mixed.csv"),
    "Dev B": (7151000, 100, DEV+"/devB_v14.csv", DEV+"/devB_hyb_v4_mixed.csv"),
    "Bestätigung": (7158000, 400, STUDY+"/confirm/v14_ref.csv", STUDY+"/confirm/v15_candidate.csv"),
}
SEATS = ("player_0", "player_1")
METRICS = ("our_points", "opp_points", "unit_steps")


def read(file, keys):
    rows = {}
    with file.open() as stream:
        for row in csv.DictReader(stream):
            if row["opponent"] != "solution92":
                continue
            key = (int(row["seed"]), row["side"])
            if key in rows:
                raise ValueError(f"Duplicate seed and seat in {file}: {key}")
            row = {k:int(row[k]) for k in (*METRICS,"game_win","our_wins","opp_wins","steps","point_counting_version")}
            if (row["steps"] != 303 or row["point_counting_version"] != 2 or
                    row["our_wins"] + row["opp_wins"] != 3 or row["game_win"] != int(row["our_wins"] > row["opp_wins"])):
                raise ValueError(f"Invalid complete match or score in {file}: {key}")
            rows[key] = row
    if set(rows) != set(keys):
        raise ValueError(f"Missing or unexpected Solution seeds in {file}")
    return rows


def effects(keys, ref, candidate):
    groups = {"won_by_both": [], "gained": [], "lost": [], "lost_by_both": []}
    for key in keys:
        a, b = ref[key]["game_win"], candidate[key]["game_win"]
        groups[("won_by_both" if a else "lost_by_both") if a == b else ("gained" if b else "lost")].append(key)
    summaries = {}
    for group, subset in {**groups,"all":keys}.items():
        delta = {m:np.array([candidate[k][m]-ref[k][m] for k in subset]) for m in METRICS}
        summaries[group] = dict(seats=len(subset),maps=len({s for s,_ in subset}),
            side_counts={p:sum(side==p for _,side in subset) for p in SEATS},
            own_points_lower=int((delta["our_points"] < 0).sum()),
            opponents_points_lower=int((delta["opp_points"] < 0).sum()),
            more_unit_steps=int((delta["unit_steps"] > 0).sum()),
            median_delta={m:float(np.median(d)) if len(d) else None for m,d in delta.items()})
    means = {}
    picks = np.random.default_rng(2711).integers(0,len(keys)//2,size=(10000,len(keys)//2))
    for metric in METRICS:
        paired = np.array([candidate[k][metric]-ref[k][metric] for k in keys]).reshape(-1,2).mean(axis=1)
        means[metric] = dict(mean=float(paired.mean()),ci95=np.quantile(paired[picks].mean(axis=1),[.025,.975]).tolist())
    return dict(groups=summaries,unconditional_map_paired_means=means), groups


def report(root):
    out, hashes = {}, {}
    for name,(first,n,f1,f2) in PANELS.items():
        keys = [(seed,p) for seed in range(first,first+n) for p in SEATS]
        ref, mixed = (read(root/path,keys) for path in (f1,f2))
        for path in (f1,f2):
            hashes[path] = hashlib.sha256((root/path).read_bytes()).hexdigest()
        out[name], groups = effects(keys, ref, mixed)
        if name=="Dev A":
            path = DEV+"/student_hyb_v4_points.csv"
            points = read(root/path,keys)
            hashes[path] = hashlib.sha256((root/path).read_bytes()).hexdigest()
            out[name]["points_wins_per_mixed_v14_group"] = {
                group:sum(points[k]["game_win"] for k in subset) for group,subset in groups.items()}
            out[name]["7150068_match_wins_of_three"] = {
                p:{arm:r[7150068,p]["our_wins"] for arm,r in (("v14",ref),("points",points),("mixed",mixed))}
                for p in SEATS}
    return dict(input_sha256=hashes, panels=out)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path,help="Directory containing kaggle3_20261115 and umbau_20261115")
    print(json.dumps(report(p.parse_args().root),indent=2,sort_keys=True))
