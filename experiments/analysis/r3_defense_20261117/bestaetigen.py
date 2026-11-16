"""Independent fixed Solution comparison for the unchanged defensive candidate."""
from argparse import ArgumentParser
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import json
import multiprocessing
from pathlib import Path

from spielreihe import HERE, POLICIES, play, spiele, verify_runtime


def games():
    return [(a, "solution", s, p) for s in range(7165860, 7165920)
            for p in spiele.SEATS for a in ("r3", "defense")]


def report(directory):
    from auswerten import compare, group, rows, totals
    table = rows(directory, games())
    return {a: totals(table, a, "solution") for a in ("r3", "defense")} | {
        "vs_r3": compare(group(table, "defense", "solution"), group(table, "r3", "solution"))}


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.runtime:
        runtime = args.runtime.resolve()
        verify_runtime(runtime, json.loads((POLICIES / "laufzeit.json").read_bytes()))
        args.out.mkdir(parents=True, exist_ok=False)
        path = args.out / "games.jsonl"
        with ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context("spawn"),
                                 initializer=spiele.initialize, initargs=(runtime,)) as pool, path.open("x") as out:
            for key, row in zip(games(), pool.map(play, games()), strict=True):
                if tuple(row[n] for n in ("arm", "opponent", "seed", "seat")) != key:
                    raise ValueError(key)
                out.write(json.dumps(row, sort_keys=True) + "\n")
                out.flush()
        (args.out / "complete.json").write_text(json.dumps({"n": len(games()), "sha256": sha256(path.read_bytes()).hexdigest()}) + "\n")
    print(json.dumps(report(args.out), indent=2))
