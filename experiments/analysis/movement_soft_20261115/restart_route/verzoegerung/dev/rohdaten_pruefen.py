"""Read the completed 14-seat diagnostic independently of game and actor code."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def require(check, condition):
    if not check:
        raise ValueError(condition)


def stream_hash(array):
    return sha(np.ascontiguousarray(array, dtype="<i2").tobytes())


def entry(path, c, side):
    team = int(side[-1])
    actual = c["delayed_record"]
    with np.load(path.with_suffix(".npz"), allow_pickle=False) as archive:
        require(archive.files == ["delayed"], "Extra stream")
        orders = archive["delayed"]
    require(orders.shape == (303, 2, 16, 3) and orders.dtype == np.int16, "Shape/type")
    require(np.all((orders[..., 0] >= 0) & (orders[..., 0] <= 5)), "Malformed native command")
    require(sha(path.with_suffix(".npz").read_bytes()) == c["orders_file_sha256"], "Wrong NPZ")
    require(stream_hash(orders) == c["comparison"]["actions_sha256"], "Wrong submitted worlds")
    ekeys = set()
    for event in actual["opportunities"]:
        t, uid = event["step"], event["uid"]
        require(0 <= uid < 16 and 101 <= t < 303 and (t, uid) not in ekeys, "Unit clock")
        ekeys.add((t, uid))
        require(t // 101 + 1 == event["match"] and t % 101 == event["match_step"], "Match clock")
        require(event["applied"] is (event["match_step"] > 12.5), "Wrong delay")
        old, new = event["r3_world"], event["v14_world"]
        require(old != new and old[0] in range(5) and new[0] in range(1, 5), "Substitution")
        require(orders[t, team, uid].tolist() == (new if event["applied"] else old), "Wrong UID world action")
        x, v14, r3 = event["distances"]
        require(0 <= v14 < x <= r3, "Wrong target distances")
    events = actual["opportunities"]
    require(c["comparison"]["applied"] == sum(e["applied"] for e in events)
            and c["comparison"]["withheld"] == sum(not e["applied"] for e in events), "Changed counts")
    return orders


def independently_first(a, b, side, changes):
    diverge = np.flatnonzero(np.any(a != b, axis=(1, 2, 3)))
    first = int(diverge[0]) if len(diverge) else None
    earliest = min((e["step"] for e in changes), default=None)
    require(first == earliest, "First difference vs intervention mismatch")
    if first is not None:
        team = int(side[-1])
        require(np.array_equal(a[first,1-team], b[first,1-team]), "Simultaneous opponent change")
        different = np.flatnonzero(np.any(a[first,team] != b[first,team], axis=1)).tolist()
        require(set(different) == {e["uid"] for e in changes if e["step"] == first}, "First diverging UID set")
    return first


def check(args):
    out = args.out
    summary = load(out / "summary.json")
    mf = out / "manifest.json"
    require(sha(mf.read_bytes()) == summary["manifest_sha256"], "Manifest")
    require(summary["new_games"] == 14 and summary["reused_games"] == 28, "Game count")
    keys = [(s, f"player_{p}") for s in (7273105, 7273116, 7273131, 7273141, 7273148, 7273149, 7273152) for p in (0,1)]
    require(set(summary["cases"]) == {f"{s}_{p}.json" for s,p in keys}, "Panel")
    obs, checks, totals = [], [], {}
    for s, side in keys:
        p = out / f"{s}_{side}.json"; c = load(p)
        require((c["seed"], c["side"]) == (s,side) and sha(p.read_bytes()) == summary["cases"][p.name], "Case")
        orders = entry(p, c, side)
        events = c["delayed_record"]["opportunities"]
        applied = [e for e in events if e["applied"]]
        skipped = [e for e in events if not e["applied"]]
        if s == 7273105:
            ref = load(args.route / "tradeoff_replay" / (side + ".json"))
            history = ref["same_prefix"]
            end = history["equal_steps_before_first_change"]
            require(stream_hash(orders[:101]) == history["match1_sha256"] and
                    stream_hash(orders[:end]) == history["equal_prefix_sha256"], "Historic digest prefix")
            diffs = {}
            for arm, filtered, actual in (("original", [e for e in ref["original"]["opportunities"] if e["match_step"]>=13], applied),
                                          ("restart", [e for e in ref["restart"]["opportunities"] if e["match_step"]<=12], skipped)):
                diffs[arm] = min((e["step"] for e in filtered), default=None)
                require(diffs[arm] == min((e["step"] for e in actual), default=None), "Historic intervention time")
                if diffs[arm] is None:
                    salt = "r3" if arm == "original" else "restart"
                    require(stream_hash(orders) == history[salt+"_actions_sha256"], "Expected whole-game equality")
                else:
                    for e in filtered:
                        if e["step"] == diffs[arm]:
                            require(orders[e["step"], int(side[-1]), e["uid"]].tolist() != e["r3_world" if arm == "original" else "v14_world"],
                                    "Expected recorded UID to diverge")
        else:
            rpath = args.route / "dev" / p.name
            ref = load(rpath)
            require(sha(rpath.with_suffix(".npz").read_bytes()) == ref["orders_sha256"], "History NPZ")
            with np.load(rpath.with_suffix(".npz"), allow_pickle=False) as archive:
                diffs = {arm: independently_first(archive[arm], orders, side, applied if arm == "original" else skipped)
                         for arm in ("original", "restart")}
        require(diffs == c["comparison"]["first_difference_global_step"], "Reported divergence")
        for arm in ("original","restart","delayed"):
            source = c["delayed_record"] if arm == "delayed" else ref[arm]
            game, matches = source["game"], source["matches"]
            require(len(matches)==3 and len(c[arm]["matches"]) == 3 and game["steps"] == 303, "Complete matches")
            require(game["wins"] == sum(m["won"] for m in matches) == c[arm]["matches_won"], "Match score")
            require(int(game["wins"] >= 2) == c[arm]["won"] == game["result"], "Game result")
            require(game["points"] == sum(m["points_ours"] for m in matches) == c[arm]["points"] and
                    game["opp_points"] == sum(m["points_rival"] for m in matches) == c[arm]["rival_points"], "Points")
            for j,(m, final) in enumerate(zip(matches,c[arm]["matches"]),1):
                public = None if m["first_own_point"] in (100,None) else m["first_own_point"]+1
                require(final == {**m, "first_public_positive":public}, "Match clock conversion")
                obs.append(dict(seed=s,side=side,arm=arm,match=j,won=m["won"],points=m["points_ours"],
                                rival_points=m["points_rival"],first_public_positive=public))
            bucket = totals.setdefault(arm, [0,0]); bucket[0] += c[arm]["won"]; bucket[1] += c[arm]["matches_won"]
        checks.append(dict(seed=s,side=side,r3=c["original"]["won"],immediate=c["restart"]["won"],delayed=c["delayed"]["won"],
                           deltas=diffs,applied=len(applied),withheld=len(skipped)))
    for arm,(wins,matches) in totals.items():
        require(summary["outcomes"][arm]["wins"] == wins and summary["outcomes"][arm]["matches"] == matches, "Total")
    for arm,f in (("original","r3"), ("restart","immediate")):
        for name in ("gained","lost"):
            seats=[[r["seed"],r["side"]] for r in checks if ((r["delayed"] > r[f]) if name=="gained" else (r["delayed"] < r[f]))]
            require(seats==summary["outcomes"][arm][name],"Paired flips")
    proof = dict(verified_games=len(checks), full_historical_pairs=12, historical_prefix_and_event_pairs=2,
                 matches_verified=len(obs), n_world_order_rows=303*2*16*len(checks), outcomes=summary["outcomes"],
                 checks=checks, summary_sha256=sha((out/"summary.json").read_bytes()))
    with (out/"raw_audit.json").open("x") as f:
        json.dump(proof, f, indent=2)
    with (out/"matches.csv").open("x", newline="") as f:
        w=csv.DictWriter(f, fieldnames=obs[0]);w.writeheader();w.writerows(obs)
    print(json.dumps(proof["outcomes"]))

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("route","out"):parser.add_argument("--"+name,type=Path,required=True)
    check(parser.parse_args())
