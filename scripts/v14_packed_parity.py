"""Two 12-game par_eval._worker groups, recording the original env.step inputs for both seats."""
import argparse
import csv
import hashlib
import importlib.metadata as metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (7158000, 7158001, 7158002)
SIDES = ("player_0", "player_1")
OPPONENTS = ("solution92", "kaggle3")
ROSTER = [(o, s, p) for o in OPPONENTS for s in SEEDS for p in SIDES]
WEIGHTS = ROOT / "agents/sherlock/weights/agent_p0.pth"
V14_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
REF_SHA = "957ac8668e10b6a118b40cb81338a86b3ec356556d68a116535b16d4130bfa05"
SCORE = ("result", "our_wins", "opp_wins", "our_points", "opp_points", "steps", "point_counting_version")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, doc):
    with path.open("x") as f:
        json.dump(doc, f, sort_keys=True, indent=1, allow_nan=False)
        f.write("\n")


def name(key):
    return "_".join(str(x) for x in key)


def scores(row):
    return {key: float(row[key]) if key == "result" else int(row[key]) for key in SCORE}


def reference(path):
    require(sha(path) == REF_SHA, "different published V14 CSV")
    result = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            key = (row["opponent"], int(row["seed"]), row["side"])
            if key in ROSTER:
                require(key not in result, "duplicate published key")
                result[key] = scores(row)
    require(set(result) == set(ROSTER), "incomplete published roster")
    return result


def binding():
    from scripts.fetch_kaggle3 import TARGET, WEIGHT_SHA256
    engine = Path(importlib.util.find_spec("luxai_s3").origin).parent
    trees = {name: {str(p.relative_to(base)): sha(p) for p in sorted(base.rglob("*.py"))}
             for name, base in (("agents", ROOT/"agents"), ("lux", ROOT/"lux"), ("scripts", ROOT/"scripts"),
                                ("kaggle", TARGET), ("luxai_s3", engine))}
    require(all(trees.values()) and "agent/agent.py" in trees["kaggle"] and "env.py" in trees["luxai_s3"],
            "missing source tree")
    k3 = {k: sha(TARGET/k) for k in WEIGHT_SHA256}
    require(sha(WEIGHTS) == V14_SHA and k3 == WEIGHT_SHA256, "different V14 or Kaggle weights")
    return dict(trees=trees, v14_sha256=V14_SHA, kaggle_weights=k3, published_csv_sha256=REF_SHA,
                python=sys.version, platform=platform.platform(), pythonhashseed=os.getenv("PYTHONHASHSEED"),
                version={p: metadata.version(p) for p in ("numpy", "scipy", "torch", "jax", "jaxlib", "luxai-s3")})


def world_orders(actions):
    require(set(actions) == set(SIDES), "missing seat in env.step")
    out = []
    for side in SIDES:
        m = np.asarray(actions[side])
        require(m.shape == (16, 3) and m.dtype.kind in "iu" and m.min() >= -32768 and m.max() <= 32767,
                f"nonrepresentable world action for {side}")
        out.append(m.astype("<i2"))
    return np.stack(out)


def checked_stream(arr):
    require(arr.dtype == np.dtype("<i2") and arr.shape == (303, 2, 16, 3), "incomplete world actions")
    return arr


class Recorder:
    """Delegate reset and step unchanged. Copy the submitted orders before each successful step."""
    def __init__(self, env):
        self.env = env
        self.orders = []
        self.matches = []

    def reset(self, *args, **kwargs):
        result = self.env.reset(*args, **kwargs)
        self.last = result[0][SIDES[0]]
        return result

    def step(self, actions):
        from scripts.scoring import match_points_after_step
        i = len(self.orders)
        require(int(self.last["steps"]) == i and int(self.last["match_steps"]) == i % 101, "invalid engine clock")
        copied = world_orders(actions)
        result = self.env.step(actions)
        new, _, terminated, truncated, info = result
        nxt = new[SIDES[0]]
        require((bool(terminated[SIDES[0]]) or bool(truncated[SIDES[0]])) == (i == 302), "early/late terminal")
        if i % 101 == 100:
            self.matches.append({"points_p0_p1": match_points_after_step(self.last, nxt, info).tolist(),
                                 "wins_p0_p1": np.asarray(nxt["team_wins"]).tolist()})
        self.last = nxt
        self.orders.append(copied)
        return result


def run_arm(mode, folder):
    from agents.sherlock.main import Agent_x
    from scripts import common, par_eval
    from scripts.packed_v14 import PackedV14Values
    k3_class = ("scripts.kaggle3_opponent", "Kaggle3Opponent")
    sol_class = ("agents.Solution_92_Kaggle.agent", "Agent")
    native_play = common.play_game
    seen = []

    def observe(env, agent, opp, seed, side, train):
        opponent, expected_seed, expected_side = ROSTER[len(seen)]
        rival = (type(opp).__module__, type(opp).__name__)
        require(not train and (seed, side) == (expected_seed, expected_side) and
                rival == (k3_class if opponent == "kaggle3" else sol_class), "wrong worker game or rival")
        require(type(agent) is Agent_x and not agent.training and len(agent.extra_q) == 35, "wrong candidate")
        packed = isinstance(agent._network_values, PackedV14Values)
        require(packed == (mode == "packed") and (packed or agent._network_values.__func__ is Agent_x._network_values),
                "packing was not applied exactly to the requested arm")
        rec = Recorder(env)
        row = native_play(rec, agent, opp, seed, side, train=train)
        stream = checked_stream(np.stack(rec.orders))
        require(len(rec.matches) == 3 and row["steps"] == 303, "incomplete episode")
        team = int(side[-1])
        pts = np.sum([r["points_p0_p1"] for r in rec.matches], axis=0)
        wins = rec.matches[-1]["wins_p0_p1"]
        require([wins[team], wins[1-team], int(pts[team]), int(pts[1-team])] ==
                [row[k] for k in ("our_wins", "opp_wins", "our_points", "opp_points")], "false final score")
        case = name((opponent, seed, side))
        path = folder / (case + ".npz")
        with path.open("xb") as f:
            np.savez_compressed(f, orders=stream)
        seen.append({"case": case, "score": scores(row), "matches": rec.matches, "stream_sha256": sha(path)})
        print(f"{mode} {case} {len(seen)}/12", flush=True)
        return row

    before = binding()
    write(folder/"binding.json", before)
    job = (str(WEIGHTS), [], list(SEEDS), list(OPPONENTS))
    start = time.monotonic()
    with patch.object(common, "play_game", observe):
        rows = par_eval._worker(job + (True,) if mode == "packed" else job)
    secs = time.monotonic() - start
    require([(r["opponent"], r["seed"], r["side"]) for r in rows] == ROSTER and len(seen) == len(ROSTER)
            and [scores(r) for r in rows] == [entry["score"] for entry in seen], "worker row mismatch")
    require(binding() == before, "sources changed during worker execution")
    write(folder/"group.json", {"binding_sha256": sha(folder/"binding.json"), "mode": mode,
                                "group_seconds_with_recorder": secs, "games": seen})


def compare_case(native, packed, n, p):
    different = (checked_stream(native) != checked_stream(packed)).any(axis=3)
    which = np.argwhere(different)
    first = None
    if len(which):
        t, seat, uid = map(int, which[0])
        first = dict(step=t, side=SIDES[seat], uid=uid, native=native[t,seat,uid].tolist(), packed=packed[t,seat,uid].tolist())
    same_end = n["score"] == p["score"] and n["matches"] == p["matches"]
    return {"pass": not len(which) and same_end, "diff_steps": int(different.any(axis=(1,2)).sum()),
            "different_unit_orders": dict(zip(SIDES, different.sum(axis=(0,2)).tolist())),
            "first": first, "same_match_and_game_scores": same_end}


def compare(out, csv_path):
    hist = reference(csv_path)
    arms, groups = {}, {}
    for arm in ("native", "packed"):
        folder = out / arm
        group = json.loads((folder/"group.json").read_text())
        require(group["mode"] == arm and sha(folder/"binding.json") == group["binding_sha256"], "mixed group")
        require([row["case"] for row in group["games"]] == list(map(name, ROSTER)), "wrong recorded roster")
        groups[arm] = group
        arms[arm] = {row["case"]: row for row in group["games"]}
    require(groups["native"]["binding_sha256"] == groups["packed"]["binding_sha256"], "different source/environment")
    results = {}
    for key in ROSTER:
        case = name(key)
        streams = {}
        for arm in arms:
            path = out / arm / (case + ".npz")
            require(sha(path) == arms[arm][case]["stream_sha256"], "altered trace")
            with np.load(path, allow_pickle=False) as f:
                streams[arm] = f["orders"]
        n, p = arms["native"][case], arms["packed"][case]
        r = compare_case(streams["native"], streams["packed"], n, p)
        r.update(native=n["score"], packed=p["score"], native_matches=n["matches"], packed_matches=p["matches"],
                 published_v14=hist[key], native_reproduces_published=n["score"] == hist[key])
        results[case] = r
    return {"parity_pass": all(r["pass"] for r in results.values()), "games_each": len(ROSTER),
            "reference_agreement": sum(r["native_reproduces_published"] for r in results.values()),
            "binding_sha256": groups["native"]["binding_sha256"],
            "group_sha256": {arm: sha(out/arm/"group.json") for arm in arms}, "cases": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify", "_arm"))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--reference", type=Path, help="original confirm/v14_ref.csv")
    parser.add_argument("--arm", choices=("native", "packed"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    out = args.out.resolve()
    if args.mode == "_arm":
        run_arm(args.arm, out)
        return
    require(args.reference, "--reference is required")
    reference(args.reference)
    if args.mode == "run":
        out.mkdir(parents=True, exist_ok=False)
        for arm in ("native", "packed"):
            folder = out / arm
            folder.mkdir()
            subprocess.run([sys.executable, "-B", "-m", "scripts.v14_packed_parity", "_arm", "--arm", arm,
                            "--out", str(folder)], check=True, cwd=ROOT, env=dict(os.environ, PYTHONHASHSEED="0"))
    report = compare(out, args.reference)
    if args.mode == "run":
        write(out/"result.json", report)
    else:
        require(json.loads((out/"result.json").read_text()) == report, "summary mismatch")
    print(f"Parity {report['parity_pass']}, native/published {report['reference_agreement']}/12")
    raise SystemExit(0 if report["parity_pass"] else 1)


if __name__ == "__main__":
    main()
