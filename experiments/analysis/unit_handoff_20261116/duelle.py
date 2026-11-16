"""Play one fixed schedule using the original native evaluation environment."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import json
import multiprocessing
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
POLICY_STUDY = HERE.parent / "r3_v15_blend_20261116"
sys.path.insert(0, str(POLICY_STUDY))
import spiele
from laufzeit import verify_runtime


def schedule():
    cases = json.loads((POLICY_STUDY / "restkarten.json").read_bytes())["r3_comparison"]
    games = [("unit", "solution", s, p) for s, p in sorted(cases["lost"] + cases["gained"])]
    for seed in range(7549200, 7549240):
        for seat in spiele.SEATS:
            for policy in ("r3", "unit"):
                games.append((policy, "solution", seed, seat))
    for seed in spiele.DIRECT:
        for opp in ("r3", "v15"):
            for seat in spiele.SEATS:
                games.append(("unit", opp, seed, seat))
    return games


def archive_schedule():
    return [("unit", "solution", seed, seat) for seed in range(7158000, 7158040) for seat in spiele.SEATS]


def play(key):
    if key[0] == "unit" and "unit" not in spiele.actors:
        from agent_unit import UnitHandoff
        spiele.actors["unit"] = UnitHandoff(key[-1])
    result = spiele.run_one(key)
    if key[0] == "unit":
        agent = spiele.actors["unit"]
        if agent.pending:
            raise ValueError("Missing follow-up observation")
        result["routing"] = agent.episode_stats()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--archiv", action="store_true", help="Play the complete supplementary historical block")
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    verify_runtime(runtime, json.loads((POLICY_STUDY / "laufzeit.json").read_bytes()))
    args.out.mkdir(parents=True, exist_ok=False)
    path = args.out / "games.jsonl"
    games = archive_schedule() if args.archiv else schedule()
    with path.open("x") as out, ProcessPoolExecutor(
        max_workers=args.workers, mp_context=multiprocessing.get_context("spawn"),
        initializer=spiele.initialize, initargs=(runtime,)
    ) as pool:
        for key, row in zip(games, pool.map(play, games), strict=True):
            if tuple(row[k] for k in ("arm", "opponent", "seed", "seat")) != key:
                raise ValueError(f"Unexpected game {key}")
            out.write(json.dumps(row, sort_keys=True) + "\n")
            out.flush()
    (args.out / "complete.json").write_text(
        json.dumps({"n": len(games), "sha256": sha256(path.read_bytes()).hexdigest()}) + "\n")
