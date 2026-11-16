"""Run the fixed field-occupancy study against original, frozen opponent policies."""
import argparse
import hashlib
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "r3_v15_blend_20261116"
sys.path.insert(0, str(PRIOR))
import spiele


def keys(stage):
    if stage == "parents":
        pairs = [(a, "solution", range(7426100, 7426140)) for a in ("r3", "blend")]
    elif stage == "candidate":
        pairs = [("field", "solution", range(7426100, 7426140))] + [
            ("field", op, spiele.DIRECT) for op in ("r3", "v15")
        ]
    else:
        cmp = json.loads((PRIOR / "restkarten.json").read_bytes())["r3_comparison"]
        return [("field", "solution", s, p) for s, p in sorted(cmp["gained"] + cmp["lost"])]
    return [(a, b, s, p) for a, b, seeds in pairs for s in seeds for p in spiele.SEATS]


def play(key):
    if key[0] == "field" and "field" not in spiele.actors:
        from feldwahl import Field
        spiele.actors["field"] = Field(key[-1])
    row = spiele.run_one(key)
    if key[0] == "field":
        row["routing"] = spiele.actors["field"].episode_stats()
    return row


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase", choices=("parents", "candidate", "cases"))
    p.add_argument("--runtime", required=True, type=Path)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    target = a.out / "games.jsonl"
    schedule = keys(a.phase)
    with target.open("x") as f, ProcessPoolExecutor(
        max_workers=a.workers,
        mp_context=multiprocessing.get_context("spawn"),
        initializer=spiele.initialize,
        initargs=(a.runtime.resolve(),),
    ) as pool:
        for k, row in zip(schedule, pool.map(play, schedule), strict=True):
            if tuple(row[n] for n in ("arm", "opponent", "seed", "seat")) != k:
                raise ValueError(k)
            f.write(json.dumps(row, sort_keys=True) + "\n")
            f.flush()
    (a.out / "complete.json").write_text(
        json.dumps(dict(n=len(schedule), sha256=hashlib.sha256(target.read_bytes()).hexdigest())) + "\n"
    )
