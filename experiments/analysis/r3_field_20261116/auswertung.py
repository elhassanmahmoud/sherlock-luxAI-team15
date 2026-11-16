"""Verify games and report paired differences, with both seats clustered by map."""
from collections import Counter
from hashlib import sha256
import json

import numpy as np

from versuch import HERE, PRIOR, keys
import spiele


def rows(folder, schedule):
    data = (folder / "games.jsonl").read_bytes()
    seal = json.loads((folder / "complete.json").read_bytes())
    if seal["sha256"] != sha256(data).hexdigest() or seal["n"] != len(schedule):
        raise ValueError(f"Incorrect result seal in {folder}")
    result = {}
    for line in data.splitlines():
        row = json.loads(line)
        key = tuple(row[t] for t in ("arm", "opponent", "seed", "seat"))
        if (key in result or row["steps"] != 303 or row["our_wins"] + row["opp_wins"] != 3
                or row["game_win"] != int(row["our_wins"] >= 2)):
            raise ValueError(f"Invalid or duplicate game {key}")
        result[key] = row
    if set(schedule) != result.keys():
        raise ValueError(f"Missing or unexpected seats in {folder}")
    return result


def group(data, agent, opponent):
    return {(s, p): v["game_win"] for (arm, op, s, p), v in data.items()
            if (arm, op) == (agent, opponent)}


def compare(a, b=None):
    ordered = sorted(a)
    if len(ordered) % 2 or (b is not None and a.keys() != b.keys()):
        raise ValueError("Different map sets")
    for left, right in zip(ordered[::2], ordered[1::2], strict=True):
        if left[0] != right[0] or (left[1], right[1]) != spiele.SEATS:
            raise ValueError("Unpaired map")
    values = np.array([a[k] - (b[k] if b is not None else 0) for k in ordered])
    by_map = values.reshape(-1, 2).mean(axis=1)
    samples = np.random.default_rng(2711).choice(by_map, (10000, len(by_map))).mean(axis=1)
    out = dict(value=float(by_map.mean()), ci95=np.quantile(samples, [.025, .975]).tolist())
    if b is not None:
        out.update(gained=[k for k in ordered if a[k] > b[k]], lost=[k for k in ordered if a[k] < b[k]])
    return out


def assess():
    data = rows(HERE / "candidate", keys("candidate"))
    data.update(rows(HERE / "parents", keys("parents")))
    old = rows(PRIOR / "candidate", spiele.jobs("candidate"))
    oldparents = rows(PRIOR / "control", spiele.jobs("control"))
    cases = rows(HERE / "cases", keys("cases"))
    report = {"cases": {f"{k[2]}/{k[3]}": v["our_wins"] for k, v in cases.items()},
              "solution": {}, "direct": {}, "routing": {}}
    for who in ("field", "blend", "r3"):
        g = group(data, who, "solution")
        report["solution"][who] = [sum(g.values()), len(g)]
    for ref in ("blend", "r3"):
        report["solution"]["vs_" + ref] = compare(group(data, "field", "solution"), group(data, ref, "solution"))
    for opp in ("r3", "v15"):
        a = group(data, "field", opp)
        b = group(old, "blend", opp)
        report["direct"][opp] = dict(field=sum(a.values()), baseline_blend=sum(b.values()), games=len(a),
                                     rate=compare(a), delta=compare(a, b))
    original = group(oldparents, "r3", "v15")
    report["direct"]["r3_against_v15"] = sum(original.values())
    report["direct"]["vs_v15_relative_to_original_r3"] = compare(group(data, "field", "v15"), original)
    for opp in ("r3", "v15", "solution"):
        counts = Counter()
        for (arm, opponent, _, _), row in data.items():
            if (arm, opponent) == ("field", opp):
                counts.update(row["routing"])
        report["routing"][opp] = dict(counts)
    return report


if __name__ == "__main__":
    print(json.dumps(assess(), indent=2))
