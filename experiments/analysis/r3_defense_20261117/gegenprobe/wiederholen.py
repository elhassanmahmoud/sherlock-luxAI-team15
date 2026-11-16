"""Replay only the four selected candidate games with one-step action forks and score parity."""
from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import json
import multiprocessing
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
sys.path.insert(0, str(STUDY))
from spielreihe import POLICIES, play, selected_cases, spiele, verify_runtime


def repeat(key):
    from einzelschritt import StepFork
    from verteidigung import Defense
    if "defense" not in spiele.actors:
        spiele.actors["defense"] = Defense(key[-1])
    native = spiele.env
    probe = StepFork(native, spiele.actors["defense"], key[-1])
    spiele.env = probe
    try:
        row = play(key)
    finally:
        spiele.env = native
    row["forks"] = probe.events
    return row


def references(keys):
    ref = {}
    with (STUDY / "candidate/games.jsonl").open() as f:
        for line in f:
            r = json.loads(line)
            k = tuple(r[n] for n in ("arm", "opponent", "seed", "seat"))
            if k in keys:
                if k in ref:
                    raise ValueError("Duplicate primary case")
                ref[k] = r
            if len(ref) == len(keys):
                break
    if set(ref) != set(keys):
        raise ValueError("Missing primary cases")
    return ref


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--workers", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    if not any((STUDY / phase / "complete.json").exists() for phase in ("controls", "candidate")):
        raise SystemExit("Both primary worker pools are still active")
    keys = [("defense", "solution", s, p) for s, p in selected_cases()]
    refs = references(keys)
    runtime = args.runtime.resolve()
    verify_runtime(runtime, json.loads((POLICIES / "laufzeit.json").read_bytes()))
    args.out.mkdir(parents=True, exist_ok=False)
    path = args.out / "games.jsonl"
    with path.open("x") as f, ProcessPoolExecutor(max_workers=args.workers,
            mp_context=multiprocessing.get_context("spawn"), initializer=spiele.initialize,
            initargs=(runtime,)) as pool:
        for key, row in zip(keys, pool.map(repeat, keys), strict=True):
            if {k: v for k, v in row.items() if k != "forks"} != refs[key]:
                raise ValueError(f"Interference with primary game on {key}")
            f.write(json.dumps(row, sort_keys=True) + "\n")
            f.flush()
    (args.out / "complete.json").write_text(json.dumps(
        {"n":len(keys),"sha256":sha256(path.read_bytes()).hexdigest()}) + "\n")
