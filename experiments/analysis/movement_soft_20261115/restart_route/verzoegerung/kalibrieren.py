"""First publicly positive match-step and the true match winner from frozen V14 archives."""
import argparse
import csv
import hashlib
import json
from math import inf, isfinite
from pathlib import Path
from statistics import median

import numpy as np


PLAN = "1cca2e8f5b645e00dd0d01f18f514d1ad7fc4820d672e7e0fa52bba3db406065"
PROTOCOL = "8eb465d5a603ac87d6453f2ce9d6fad5258fe1d8cd2539cdf7a39497cd4a7e8d"
AUDIT = "f5efa80451d5c1bea61b387c96960b6e4f695fff92451f050798462aaec14268"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(check, message):
    if not check:
        raise ValueError(message)


def score_bounds(clock, points):
    require(len(clock) and np.all((points >= 0) & (points <= 1)), "Invalid own score")
    require(np.all(np.diff(points) >= 0), "Decreasing in-match score")
    first = np.flatnonzero(points > 0)
    if len(first):
        i = first[0]
        return (int(clock[i-1]) + 1 if i else 1), int(clock[i])
    return int(clock[-1]) + 1 if clock[-1] < 100 else inf, inf


def read_matches(path, meta):
    with np.load(path, allow_pickle=False) as data:
        require(json.loads(data["meta"].item()) == meta, "Audited metadata differs")
        clock, board = data["global_step"].astype(int), data["step"].astype(int)
        require(np.all((0 < clock) & (clock < 303) & (clock % 101 != 0) & (np.diff(clock, prepend=-1) > 0)), "Clock")
        require(np.all(np.diff(board) >= 0) and np.array_equal(np.unique(board), np.arange(len(clock))), "Board rows")
        require(np.array_equal(clock[board] % 101, data["mstep"]), "Match clock")
        score = data["feats"][:, [10, 12, 13]].astype(float)
    public = score[np.searchsorted(board, np.arange(len(clock)))]
    require(np.array_equal(public[board], score), "Unit-dependent scoreboard")
    standings = []
    for match in range(3):
        scores = public[clock // 101 == match, 1:3] * 3
        require(len(scores) and np.max(np.abs(scores - scores.round())) < .002, "Nonintegral match score")
        rounded = scores.round().astype(int)
        require(np.all(rounded == rounded[0]) and np.all(rounded >= 0) and rounded[0].sum() == match, "Wins")
        standings.append(rounded[0])
    standings.append(np.asarray([meta["our_wins"], meta["opp_wins"]]))
    advances = np.diff(standings, axis=0)
    require(np.all((advances == 0) | (advances == 1)) and np.all(advances.sum(axis=1) == 1), "Winner")
    for j in (1, 2):
        ix = clock // 101 == j
        ms = clock[ix] % 101
        lo, hi = score_bounds(ms, public[ix, 0])
        yield dict(seed=meta["seed"], side=meta["side"], match=j+1, won=int(advances[j, 0]),
                   first_lower=lo, first_upper=hi, recorded_boards=len(ms), sha256=sha(path))


def summarize(rows):
    won = [r for r in rows if r["won"]]
    if not won:
        return dict(matches=len(rows), wins=0, first_median=None)
    low, high = (median(r[k] for r in won) for k in ("first_lower", "first_upper"))
    return dict(matches=len(rows), wins=len(won), exact_won_times=sum(r["first_lower"] == r["first_upper"] for r in won),
                won_with_no_public_point=sum(r["first_lower"] == inf for r in won),
                median_bounds=[low if isfinite(low) else None, high if isfinite(high) else None],
                first_median=low if low == high and isfinite(low) else None)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True, help="Checkout containing raw original NPZ and the published audit")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    require(sha(Path(__file__).with_name("KALIBRIERPLAN.md")) == PLAN, "Pre-registration changed")
    data_dir = a.repo / "experiments/imitation/final_20261115_v14_advice"
    prior = a.repo / "experiments/analysis/combat_advice_20261115"
    require(sha(data_dir / "protocol.json") == sha(prior / "data_protocol.json") == PROTOCOL, "Protocol")
    require(sha(prior / "v14_advice_audit.json") == AUDIT, "Published archive index")
    audit = json.loads((prior / "v14_advice_audit.json").read_bytes())
    rows = []
    seen = set()
    for item in audit["map_sides"]:
        meta = item["metadata"]
        if meta["opponent"] != "solution92":
            continue
        seed, side = meta["seed"], meta["side"]
        key = seed, side
        path = data_dir / f"g{seed}_{side}_solution92.npz"
        require(sha(path) == item["input_sha256"] and key not in seen, f"Archive mismatch: {key}")
        require(meta["policy"] == "v14" and meta["protocol_sha256"] == PROTOCOL and meta["steps"] == 303, f"Source: {key}")
        seen.add(key)
        rows.extend(read_matches(path, meta))
    seeds = range(7271001, 7271040, 3)
    require(seen == {(s, p) for s in seeds for p in ("player_0", "player_1")}, "Different calibration maps")
    rows.sort(key=lambda r: (r["seed"], r["side"], r["match"]))
    report = dict(protocol_sha256=PROTOCOL, audit_sha256=AUDIT, plan_sha256=PLAN,
                  maps=len(seeds), games=len(seen), overall=summarize(rows))
    for k in ("match", "side", "seed"):
        report["by_" + k] = {v: summarize([r for r in rows if r[k] == v]) for v in sorted({r[k] for r in rows})}
    a.out.mkdir(parents=True, exist_ok=False)
    with (a.out / "matches.csv").open("x") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    report["match_rows_sha256"] = sha(a.out / "matches.csv")
    with (a.out / "ergebnis.json").open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
