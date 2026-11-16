"""Measure a frozen defensive candidate and original controls on identical cards."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import json
import multiprocessing
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "unit_handoff_20261116"
POLICIES = HERE.parent / "r3_v15_blend_20261116"
sys.path.insert(0, str(POLICIES))
import spiele
from laufzeit import verify_runtime


def selected_cases():
    archive = json.loads((PREVIOUS / "archiv.json").read_bytes())
    return sorted((s, side) for s, side in archive["vs_v15"]["lost"])


def schedule(phase):
    controls = phase == "controls"
    games = []
    if not controls:
        games.extend(("defense", "solution", seed, side) for seed, side in selected_cases())
    for seed in range(7165740, 7165780):
        for seat in spiele.SEATS:
            for arm in (("r3", "v15") if controls else ("defense",)):
                games.append((arm, "solution", seed, seat))
    for seed in range(7165800, 7165816):
        for seat in spiele.SEATS:
            for arm, opp in ((("r3", "v15"),) if controls else (("defense", "r3"), ("defense", "v15"))):
                games.append((arm, opp, seed, seat))
    return games


def play(key):
    if key[0] == "defense" and "defense" not in spiele.actors:
        from verteidigung import Defense
        spiele.actors["defense"] = Defense(key[-1])
    result = spiele.run_one(key)
    if key[0] == "defense":
        result["routing"] = spiele.actors["defense"].episode_stats()
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase", choices=("controls", "candidate"))
    p.add_argument("--runtime", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--workers", type=int, default=2)
    a = p.parse_args()
    rt = a.runtime.resolve()
    verify_runtime(rt, json.loads((POLICIES / "laufzeit.json").read_bytes()))
    games = schedule(a.phase)
    if len(games) != len(set(games)):
        raise ValueError("Duplicate schedule")
    a.out.mkdir(parents=True, exist_ok=False)
    path = a.out / "games.jsonl"
    with path.open("x") as out, ProcessPoolExecutor(
        max_workers=a.workers, mp_context=multiprocessing.get_context("spawn"),
        initializer=spiele.initialize, initargs=(rt,)
    ) as pool:
        for k, row in zip(games, pool.map(play, games), strict=True):
            if tuple(row[n] for n in ("arm", "opponent", "seed", "seat")) != k:
                raise ValueError(k)
            out.write(json.dumps(row, sort_keys=True) + "\n")
            out.flush()
    (a.out / "complete.json").write_text(json.dumps({"n": len(games), "sha256": sha256(path.read_bytes()).hexdigest()}) + "\n")
