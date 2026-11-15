"""Collect randomized V14 scout actions, fit own four-step energy returns, then diagnose on new maps."""
from __future__ import annotations

import argparse
import gzip
import json
import multiprocessing
import os
import subprocess
from pathlib import Path

import numpy as np

from scripts.final_learning_agent import (DEATH_COST, FEATURES, HORIZON, MARGIN, WEIGHTS, WEIGHT_SHA,
                                          EnergyReturnAgent, choose, load_model, sha)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "experiments/analysis/final_learning_20261115"
RIDGE = 5.0
SOURCE_FILES = ("scripts/final_learning_agent.py", "scripts/final_learning_study.py",
                "scripts/kaggle3_opponent.py", "scripts/common.py", "agents/sherlock/main.py",
                "agents/sherlock/features.py", "agents/sherlock/belief.py")


def split_keys(split):
    sets = {"train": range(7162000, 7162008), "diagnose": range(7162100, 7162104)}
    return [(seed, side) for seed in sets[split] for side in range(2)]


def freeze():
    from scripts.fetch_kaggle3 import ARCHIVE_SHA256, WEIGHT_SHA256
    if sha(WEIGHTS) != WEIGHT_SHA:
        raise ValueError("V14 checkpoint changed")
    return dict(schema=1, v14=WEIGHT_SHA, kaggle3_archive=ARCHIVE_SHA256, kaggle3_weights=WEIGHT_SHA256,
                sources={p: sha(ROOT / p) for p in SOURCE_FILES},
                commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                horizon=HORIZON, margin=MARGIN, death_cost=DEATH_COST, ridge=RIDGE,
                features=list(FEATURES), train=split_keys("train"), diagnose=split_keys("diagnose"))


def save_json(path, obj):
    """Publish a complete file once without replacing any prior result."""
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with tmp.open("x") as out:
            json.dump(obj, out, allow_nan=False, indent=2)
            out.write("\n")
        os.link(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def ensure_freeze():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frozen = freeze()
    path = OUTPUT / "freeze.json"
    if not path.exists():
        try:
            save_json(path, frozen)
        except FileExistsError:
            pass
    if json.loads(path.read_text()) != json.loads(json.dumps(frozen)):
        raise ValueError("Source or protocol differs from frozen collector")
    return path


def file_for(split, seed, side):
    return OUTPUT / split / f"{seed}_p{side}.json.gz"


def collect_game(job):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.common import make_opponent, play_game
    from scripts.experiment import limit_threads
    from scripts.par_eval import require_no_agent_errors

    limit_threads()
    split, seed, side, freeze_sha = job
    out = file_for(split, seed, side)
    if out.exists():
        raise FileExistsError(out)
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        agent = EnergyReturnAgent(f"player_{side}", agent_path=str(WEIGHTS), train=False, seed=0, collect=True)
        agent.set_to_eval_mode()
        agent.set_trial_seed(seed)
        opp = make_opponent("kaggle3", f"player_{1-side}")
        summary = play_game(env, agent, opp, seed, f"player_{side}", train=False)
        require_no_agent_errors(agent, opp)
        if summary["steps"] != 303 or agent.pending is not None or len(agent.rows) != agent.probes:
            raise ValueError("Incomplete game or energy labels")
        archive = dict(seed=seed, side=side, freeze=freeze_sha, summary=summary, rows=agent.rows)
        tmp = out.with_name(f".{out.name}.{os.getpid()}.tmp")
        try:
            with gzip.open(tmp, "xt") as f:
                json.dump(archive, f, allow_nan=False, separators=(",", ":"))
            os.link(tmp, out)
        finally:
            tmp.unlink(missing_ok=True)
        return seed, side, len(agent.rows)
    finally:
        env.close()


def validate_dataset(rows, split):
    expected = set(split_keys(split))
    if {(r["seed"], r["side"]) for r in rows} != expected:
        raise ValueError(f"Incomplete/mixed {split} map and seat set")
    previous = {}
    for row in rows:
        x = np.asarray(row["x"], dtype=float)
        legal = np.asarray(row["legal"])
        a, b = row["chosen"], row["base"]
        key = row["seed"], row["side"]
        if (x.shape != (5, len(FEATURES)) or legal.shape != (5,) or legal.dtype != bool
                or legal.sum() < 2 or a not in range(5) or b not in range(5) or not legal[a] or not legal[b]
                or not np.isfinite(x).all() or not np.isfinite(row["y"])
                or row["step"] < previous.get(key, -HORIZON) + HORIZON):
            raise ValueError("Invalid randomized scout record")
        previous[key] = row["step"]


def read_dataset(split, frozen):
    rows, inputs = [], {}
    for seed, side in split_keys(split):
        path = file_for(split, seed, side)
        with gzip.open(path, "rt") as f:
            game = json.load(f)
        if (game["seed"], game["side"], game["freeze"]) != (seed, side, frozen):
            raise ValueError(f"Wrong source in {path}")
        if game["summary"]["steps"] != 303 or any((r["seed"], r["side"]) != (seed, side) for r in game["rows"]):
            raise ValueError(f"Wrong game data in {path}")
        rows.extend(game["rows"])
        inputs[str(path.relative_to(OUTPUT))] = sha(path)
    validate_dataset(rows, split)
    return rows, inputs


def fit_model(rows):
    x = np.stack([r["x"][r["chosen"]] for r in rows])
    y = np.array([r["y"] for r in rows])
    penalty = np.eye(x.shape[1]) * RIDGE
    penalty[0, 0] = 0
    return np.linalg.solve(x.T @ x + penalty, x.T @ y)


def heldout_scores(rows, weights):
    """Doubly robust policy-value difference; uniform logged propensities on all legal actions."""
    by_seed = {}
    changes = 0
    errors = []
    for r in rows:
        predictions = np.asarray(r["x"]) @ weights
        legal = np.asarray(r["legal"])
        a, base = r["chosen"], r["base"]
        chosen = choose(predictions, legal, base)
        changed = chosen != base
        changes += int(changed)
        residual = r["y"] - predictions[a]
        correction = (int(a == chosen) - int(a == base)) * int(legal.sum()) * residual
        by_seed.setdefault(r["seed"], []).append(float(predictions[chosen] - predictions[base] + correction))
        errors.append(float(residual**2))
    means = {str(seed): float(np.mean(v)) for seed, v in by_seed.items()}
    map_gain = float(np.mean(list(means.values())))
    positive = sum(v > 0 for v in means.values())
    return dict(n=len(rows), changes=changes, rmse=float(np.sqrt(np.mean(errors))),
                map_mean_gain=map_gain, map_gains=means, positive_maps=positive,
                screen_gate=changes >= 20 and map_gain > 0 and positive >= 3)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    coll = sub.add_parser("collect")
    coll.add_argument("--split", choices=["train", "diagnose"], required=True)
    coll.add_argument("--workers", type=int, choices=[1, 2], default=1)
    sub.add_parser("fit")
    sub.add_parser("diagnose")
    args = ap.parse_args()
    freeze_path = ensure_freeze()
    frozen = sha(freeze_path)
    model_path = OUTPUT / "model.json"
    if args.command == "collect":
        from scripts.fetch_kaggle3 import verify
        if not verify():
            raise ValueError("Download the pinned Kaggle3 test opponent before collection")
        (OUTPUT / args.split).mkdir(exist_ok=True)
        jobs = [(args.split, seed, side, frozen) for seed, side in split_keys(args.split)
                if not file_for(args.split, seed, side).exists()]
        if args.workers == 1:
            for result in map(collect_game, jobs):
                print(f"seed={result[0]} p{result[1]} labels={result[2]}", flush=True)
        elif jobs:
            with multiprocessing.get_context("spawn").Pool(args.workers) as pool:
                for result in pool.imap_unordered(collect_game, jobs):
                    print(f"seed={result[0]} p{result[1]} labels={result[2]}", flush=True)
        rows, _ = read_dataset(args.split, frozen)
        print(f"Complete {args.split}: {len(rows)} four-step labels", flush=True)
    elif args.command == "fit":
        rows, inputs = read_dataset("train", frozen)
        coefficients = fit_model(rows)
        model = dict(schema=1, v14=WEIGHT_SHA, freeze=frozen, horizon=HORIZON, margin=MARGIN,
                     features=list(FEATURES), ridge=RIDGE, inputs=inputs, n=len(rows),
                     deaths=sum(r["died"] for r in rows), coefficients=coefficients.tolist())
        save_json(model_path, model)
        print(f"Frozen model {sha(model_path)} from {len(rows)} decisions")
    else:
        model_obj = json.loads(model_path.read_text())
        if model_obj["freeze"] != frozen:
            raise ValueError("Model does not belong to the frozen experiment")
        _, train_inputs = read_dataset("train", frozen)
        if model_obj["inputs"] != train_inputs:
            raise ValueError("Training inputs changed")
        weights = load_model(model_path)
        rows, inputs = read_dataset("diagnose", frozen)
        report = heldout_scores(rows, weights)
        report.update(model_sha=sha(model_path), freeze=frozen, inputs=inputs)
        save_json(OUTPUT / "diagnosis.json", report)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
