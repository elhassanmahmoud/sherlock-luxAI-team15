"""Passively replay public score evidence. Two deterministic lanes, no simulation."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from gruppen import GroupEvidence, indices
from beweise import folded
from wege import routes

HERE = Path(__file__).resolve().parent
SINGLE = HERE.parent / "punktspeicher"
SCRATCH = (Path.home() / "Desktop/KI/sherlock-luxAI-team15/experiments/imitation/"
           "relictsuche_20261123/gruppenbeweis")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source(group):
    return {str(p.relative_to(HERE.parent)): digest(p) for p in
            [HERE / n for n in ("PLAN.md", "gruppen.py", "wege.py", "studie.py")]
            + [SINGLE / "beweise.py", SINGLE / "karten.json",
               SINGLE / group / "beobachtungen.jsonl.gz", SINGLE / group / "beweise.jsonl.gz"]}


def read_zip(path):
    with gzip.open(path, "rt") as stream:
        return [json.loads(line) for line in stream]


def calculate(raw, original):
    evidence = GroupEvidence()
    index = {}
    frames = []
    checks = Counter()
    for public, policy, judge, saved in zip(raw["public"], raw["policy"], raw["referee"], original["frames"], strict=True):
        # The inference step sees public inputs only. The referee is read afterwards.
        groups = evidence.observe(public)
        single = evidence.single
        assert single.positive == int(saved["p"], 16) and single.negative == int(saved["n"], 16)
        truth = int(judge, 16)
        assert not evidence.extra_positive & ~truth
        for mask in sorted(groups):
            assert mask & truth and mask.bit_count() in (2, 3)
            index.setdefault(mask, len(index))
            checks[f"validated_group_{mask.bit_count()}_ticks"] += 1
        singletons = single.positive | evidence.extra_positive
        v16 = folded(int(policy["point"], 16))
        open_groups = {m for m in groups if not m & v16}
        complete, partial = routes(public, policy, open_groups, singletons)
        def bits(items):
            return format(sum(1 << index[m] for m in items), "x")
        f = dict(t=public["step"], groups=bits(groups), open=bits(open_groups), partial=bits(partial),
                 singleton_route=bool(int(saved.get("strict_four", "0"), 16)),
                 complete=sorted([index[g], uid, path] for (g, uid), path in complete.items()))
        if evidence.extra_positive:
            f["extra_single"] = format(evidence.extra_positive, "x")
        frames.append(f)
        checks["observations"] += 1
    return dict(seed=raw["seed"], team=raw["team"], action_hash=raw["action_hash"],
                groups=[list(indices(m)) for m in index], frames=frames, checks=checks)


def run(group, lane):
    binding = source(group)
    games = read_zip(SINGLE / group / "beobachtungen.jsonl.gz")
    baseline = {(r["seed"], r["team"]): r for r in read_zip(SINGLE / group / "beweise.jsonl.gz")}
    folder = SCRATCH / group
    folder.mkdir(parents=True, exist_ok=True)
    for raw in games[lane::2]:
        key = (raw["seed"], raw["team"])
        path = folder / f"{key[0]}_{key[1]}.json.gz"
        if path.exists():
            assert json.loads(gzip.decompress(path.read_bytes()))["source"] == binding
            continue
        base = baseline[key]
        assert raw["action_hash"] == base["action_hash"]
        result = calculate(raw, base)
        result["source"] = binding
        encoded = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(gzip.compress(encoded, mtime=0))
        tmp.replace(path)
    assert binding == source(group)
    print(group, "lane", lane, "complete", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("group", choices=("archiv", "frisch"))
    parser.add_argument("lane", choices=(0, 1), type=int)
    args = parser.parse_args()
    run(args.group, args.lane)
