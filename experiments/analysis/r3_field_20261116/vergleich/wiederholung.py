"""Record V15 and Field on the five fixed seats; compare both with the original raw replays."""
import argparse
import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
sys.path.insert(0, str(STUDY))
from versuch import PRIOR, keys, play, spiele

sys.path.insert(0, str(PRIOR / "diagnose"))
from replay import Observer, require
from laufzeit import verify_runtime


def read_trace(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def match_summary(frames):
    # Step zero can still contain observations from the preceding match.
    active = list(enumerate(frames[1:], 1))
    def first(test):
        return next((turn for turn, frame in active if test(frame)), None)
    confirmed = first(lambda f: bool(f["confirmed"]))
    def occupied_fields(f):
        return set(map(tuple, f["confirmed"])) & {(x, y) for _, x, y, _ in f["own"]}
    occupied = first(occupied_fields)
    return dict(confirmed=confirmed, occupied=occupied,
                covered_turns25=sum(len(occupied_fields(f)) for _, f in active[:25]),
                first_score=first(lambda f: f["after"][0] > 0),
                score25=frames[25]["after"], score100=frames[100]["after"])


def study(runtime, originals, out):
    require((STUDY / "parents/complete.json").exists(), "Parent run still active")
    verify_runtime(runtime, json.loads((PRIOR / "laufzeit.json").read_bytes()))
    cfg = json.loads((PRIOR / "restkarten.json").read_bytes())
    v15_csv = spiele.ROOT / "experiments/analysis/kaggle3_20261115/devB_hyb_v4_mixed.csv"
    require(hashlib.sha256(v15_csv.read_bytes()).hexdigest() == cfg["v15_csv_sha256"], "V15 archive")
    with v15_csv.open() as f:
        refs = {(int(r["seed"]), r["side"]): r for r in csv.DictReader(f)
                if r["opponent"] == "solution92" and r["point_counting_version"] == "2"}
    cases = (STUDY / "cases/games.jsonl").read_bytes()
    seal = json.loads((STUDY / "cases/complete.json").read_bytes())
    require(seal == {"n": 5, "sha256": hashlib.sha256(cases).hexdigest()}, "Candidate archive")
    field_refs = {(r["seed"], r["seat"]): r for r in map(json.loads, cases.splitlines())}
    out.mkdir(parents=True, exist_ok=False)
    spiele.initialize(runtime)
    from feldwahl import Field
    engine = spiele.env
    for arm in ("v15", "field"):
        for _, opp, seed, seat in keys("cases"):
            if arm == "field" and arm not in spiele.actors:
                spiele.actors[arm] = Field(seat)
            actor = spiele.actor(arm, seat)
            observer = Observer(engine, actor.v14 if arm == "v15" else actor.r3, "r3", seat)
            spiele.env = observer
            try:
                got = play((arm, opp, seed, seat))
            finally:
                spiele.env = engine
            ref = (refs if arm == "v15" else field_refs)[seed, seat]
            require(all(got[k] == int(ref[k]) for k in spiele.GAME), "Different original end score")
            require(len(observer.frames) == 303 and (arm == "v15" or got == ref), "Incomplete replay")
            data = dict(arm=arm, seed=seed, seat=seat, game=got, frames=observer.frames)
            blob = gzip.compress(json.dumps(data, separators=(",", ":")).encode(), mtime=0)
            (out / f"{arm}-{seed}-{seat}.json.gz").write_bytes(blob)
    engine.close()
    results = {}
    for _, _, seed, seat in keys("cases"):
        logs = {}
        for arm in ("r3", "blend", "v15", "field"):
            src = originals if arm in ("r3", "blend") else out
            logs[arm] = read_trace(src / f"{arm}-{seed}-{seat}.json.gz")["frames"]
        item = {arm: [match_summary(frames[i:i+101]) for i in (0, 101, 202)]
                for arm, frames in logs.items()}
        first, ref = logs["field"][:101], logs["r3"][:101]
        item["identical_m1"] = {
            key: sum(a[key] == b[key] for a, b in zip(first, ref, strict=True))
            for key in ("own_orders", "opp_orders", "confirmed", "own", "after")}
        results[f"{seed}/{seat}"] = item
    (out / "vergleich.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("runtime", "originals", "out"):
        parser.add_argument("--" + arg, type=lambda path: Path(path).resolve(), required=True)
    args = parser.parse_args()
    study(args.runtime, args.originals, args.out)
