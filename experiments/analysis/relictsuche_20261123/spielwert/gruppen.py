"""Play complete, side- and opponent-balanced games with forced and learned route budgets."""
import argparse
from datetime import datetime
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
sys.path.insert(0, str(STUDY / "vergleich"))
from panel import sensor
from spielen import CUTOFF, THREADS, common_source, play, require, sha, stamp, write_once
from politik import create


def roster(stage):
    import jax
    start, n = {"train": (162100000, 384), "pilot": (162110000, 96), "test": (162120000, 64)}[stage]
    pool = np.arange(start, start+n*9, dtype=np.int32)
    cards = list(map(int, pool[np.asarray(jax.jit(jax.vmap(sensor))(pool)) == 1][:n]))
    require(len(set(cards)) == n, "Invalid roster")
    return cards


def schedule(stage):
    cards = roster(stage)
    if stage == "test":
        return [(seed, t, opp, a) for seed in cards for t in (0, 1) for opp in ("solution92", "v16") for a in ("reference", "select")]
    return [(seed, (i//2)%2, ("solution92", "v16")[i%2], arm)
            for i, seed in enumerate(cards) for arm in ("b0", "b1", "b3")]


def source(stage):
    files = [HERE / n for n in ("PLAN.md", "gruppen.py", "politik.py")]
    files += [STUDY / "zielschaetzer" / n for n in ("kandidat.py", "ort.json")]
    if stage == "test":
        files.append(HERE / "modell.json")
    return stamp(dict(base=common_source(), files={str(p.relative_to(STUDY)): sha(p) for p in files}))


def path(folder, stage, key):
    seed, team, opp, arm = key
    return folder / stage / f"{seed}-{team}-{opp}-{arm}.json"


def main():
    import json
    import os
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.experiment import limit_threads
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", type=Path)
    p.add_argument("stage", choices=("train", "pilot", "test"))
    p.add_argument("lane", type=int)
    p.add_argument("stride", type=int)
    p.add_argument("--sample", type=int)
    args = p.parse_args()
    if args.stage == "test" and not json.loads((HERE / "pilot.json").read_text())["passed"]:
        raise ValueError("Independent check did not qualify")
    require(0 <= args.lane < args.stride and os.getenv("PYTHONHASHSEED") == "0"
            and all(os.getenv(k) == "1" for k in THREADS), "Invalid worker settings")
    limit_threads()
    jobs = schedule(args.stage)
    if args.sample:
        jobs = jobs[:args.sample]
    identity = source(args.stage)
    write_once(args.folder / f"{args.stage}-sources.json", {"source": identity, "stage": args.stage})
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for key in jobs[args.lane::args.stride]:
            if datetime.now(CUTOFF.tzinfo) >= CUTOFF:
                break
            seed, team, opp, arm = key
            dest = path(args.folder, args.stage, key)
            if dest.exists():
                require(json.loads(dest.read_text())["source"] == identity, "Changed inputs on resume")
                continue
            player = []
            def factory(side):
                obj = create(side, None if arm == "select" else int(arm[1]))
                player.append(obj)
                return obj
            row = play(env, (args.stage, seed, team, arm, opp), identity, factory if arm != "reference" else None)
            row["features"] = player[0].features if player else None
            row["budget"] = player[0].budget if player else None
            require(len(row["events"]) <= (row["budget"] or 0)
                    and len({e[1] for e in row["events"]}) <= 1, "Scout limit breached")
            write_once(dest, row)
            print(seed, team, opp, arm, flush=True)
    finally:
        env.close()
    require(source(args.stage) == identity, "Source drift")


if __name__ == "__main__":
    main()
