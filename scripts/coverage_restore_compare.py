"""Evaluate the opt-in R2 coverage restoration on the original final_battle_compare game loop."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from copy import copy
import fcntl
import json
import multiprocessing
from pathlib import Path

from scripts import final_battle_compare as compare


NAME = "coverage_restore"
SIDES = ("player_0", "player_1")


def contract(args):
    # Start with exactly the bindings of the unmodified R2 movement run, including
    # its real runner bytes. The additional runner and policy are bound separately.
    movement = copy(args)
    movement.candidate = "selective_movement"
    manifest = compare.contract(movement)
    manifest["candidate"] = NAME
    for name in ("coverage_restore.py", "coverage_restore_compare.py"):
        manifest["sources"]["scripts/" + name] = compare.digest(compare.ROOT / "scripts" / name)
    return manifest


def init_worker(model):
    # The historical initializer supplies the movement constructor arguments, seeds
    # and environment. Select the derived class only during this worker's setup.
    previous = compare.POLICIES["selective_movement"]
    compare.POLICIES["selective_movement"] = "scripts.coverage_restore:CoverageRestoreAgent"
    try:
        compare.init_worker("selective_movement", model)
    finally:
        compare.POLICIES["selective_movement"] = previous


def evaluate(job):
    row = compare.evaluate(job)
    agent = compare.evaluate.agent
    row["coverage_counts"] = dict(agent.coverage_counts)
    row["selective_counts"] = dict(agent.selective_counts)
    return row


def game_key(row):
    return row["opponent"], row["seed"], row["side"]


def run(args):
    opponents = args.opponents.split(",")
    if (not args.model or args.maps <= 0 or len(opponents) != len(set(opponents))
            or any(not o for o in opponents)):
        raise ValueError("Expected R2 weights, a positive map count and distinct study opponents")
    keys = [(o, seed, side) for seed in range(args.first, args.first + args.maps)
            for o in opponents for side in SIDES]
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / ".run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        bound = contract(args)
        manifest = args.out / "manifest.json"
        log = args.out / "games.jsonl"
        if manifest.exists():
            if json.loads(manifest.read_text()) != bound:
                raise ValueError("Source or configuration changed on resume")
        else:
            if log.exists() or (args.out / "completed.json").exists():
                raise ValueError("Missing manifest for existing results")
            with manifest.open("x") as f:
                f.write(json.dumps(bound, indent=2) + "\n")
        pending = set(keys)
        rows = []
        if log.exists():
            for line in log.read_text().splitlines():
                row = json.loads(line)
                key = game_key(row)
                if (key not in pending or row["candidate"] != NAME or row["steps"] != 303
                        or row["wins"] + row["losses"] != 3 or row["result"] != int(row["wins"] > row["losses"])
                        or not all(isinstance(row[c], dict) for c in ("coverage_counts", "selective_counts"))):
                    raise ValueError(f"Unexpected saved game {key}")
                pending.remove(key)
                rows.append(row)
        if pending:
            jobs = [(NAME, *key, args.model) for key in keys if key in pending]
            with ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context("spawn"),
                                     initializer=init_worker, initargs=(args.model,)) as pool, log.open("a") as f:
                for row in pool.map(evaluate, jobs, chunksize=1):
                    pending.remove(game_key(row))
                    f.write(json.dumps(row, allow_nan=False) + "\n")
                    f.flush()
                    rows.append(row)
                    print(*game_key(row), row["result"], flush=True)
        if pending or contract(args) != bound:
            raise RuntimeError("Incomplete run or changed inputs")
        summary = {o: dict(played=0, wins=0, matches=0) for o in opponents}
        for r in rows:
            counts = summary[r["opponent"]]
            counts["played"] += 1
            counts["wins"] += r["result"]
            counts["matches"] += r["wins"]
        result = dict(summary=summary, rows_sha256=compare.digest(log))
        (args.out / "completed.json").write_text(json.dumps(result, indent=2) + "\n")
        print(summary)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate", default=NAME, choices=(NAME,))
    p.add_argument("--model", required=True)
    p.add_argument("--opponents", default="kaggle3,solution92")
    p.add_argument("--first", required=True, type=int)
    p.add_argument("--maps", required=True, type=int)
    p.add_argument("--workers", type=int, choices=(1, 2), default=2)
    p.add_argument("--out", required=True, type=Path)
    run(p.parse_args())
