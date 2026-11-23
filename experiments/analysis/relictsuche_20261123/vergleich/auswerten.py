"""Validate complete fixed stages, score by map, and preserve inspectable raw games."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path

import numpy as np

from spielen import HERE, ROOT, SCRATCH, common_source, require, sha, stamp, validate, write_once

OUTCOME_FIELDS = ("sensor", "sight", "credit", "after_70", "matches", "steps", "wins", "win", "points", "action_hash")
BOOTSTRAP_SEED = 231123
DRAWS = 20000


def measurements(row):
    match = row["matches"][0]
    our, their = row["after_70"]
    mp, ep = match["points"]
    return {"sight": row["sight"], "credit": row["credit"], "own70": our, "opp70": their,
            "margin70": our - their, "match1points": mp, "match1opp": ep, "match1margin": mp - ep,
            "match1win": match["win"], "whole": row["win"], "all_match_wins": row["wins"]}


def summary(rows):
    return {"games": len(rows), "wins": sum(r["win"] for r in rows), "match1wins": sum(r["matches"][0]["win"] for r in rows),
            "no_sight": sum(r["sight"] == 101 for r in rows), "no_credit": sum(r["credit"] == 101 for r in rows),
            "changes": sum(len(r["events"]) for r in rows), "changed_games": sum(bool(r["events"]) for r in rows),
            "changed_maps": len({r["seed"] for r in rows if r["events"]}),
            "means": {k: float(np.mean([measurements(r)[k] for r in rows])) for k in measurements(rows[0])}}


def describe(values, draws):
    v = np.asarray(values, dtype=float)
    require(v.shape == (draws.shape[1],) and np.isfinite(v).all(), "Invalid map series")
    means = v[draws].mean(axis=1)
    return {"mean": float(v.mean()), "ci95": np.quantile(means, [0.025, 0.975], method="linear").tolist()}


def verify_sources(source):
    require(source["common"] == stamp(common_source()), "Common benchmark inputs changed")
    if source["candidate"]:
        for loc, digest in source["candidate"]["files"].items():
            p = Path(loc)
            require(sha(p if p.is_absolute() else ROOT / p) == digest, f"Changed candidate input: {loc}")


def expected(phase, cards, ids):
    return [(phase, s, t, name, opp) for name in ["reference", *ids] for s in cards for t in (0, 1)
            for opp in (["solution92"] if name == "reference" else ["solution92", "v16"])]


def score(name, cards, groups, draws):
    base = groups["reference", "solution92"]
    cand = groups[name, "solution92"]
    direct = groups[name, "v16"]
    for k, b in base.items():
        r = cand[k]
        require(r["sensor"] == b["sensor"] == direct[k]["sensor"], "Reset parameters disagree")
        if not r["events"]:
            require(all(r[f] == b[f] for f in OUTCOME_FIELDS), f"Inactive policy changed the trajectory: {k}")

    def panel(g):
        rows = list(g.values())
        return {"all": summary(rows), "by_seat": {str(t): summary([r for r in rows if r["team"] == t]) for t in (0, 1)}}

    result = {"solution": panel(cand), "direct": panel(direct), "paired": {}, "transitions": {}}
    for field in measurements(next(iter(base.values()))):
        sign = -1 if field in ("sight", "credit") else 1
        diffs, seats = [], [[], []]
        for s in cards:
            pair = []
            for t in (0, 1):
                d = sign * (measurements(cand[s, t])[field] - measurements(base[s, t])[field])
                pair.append(d)
                seats[t].append(d)
            diffs.append(sum(pair) / 2)
        result["paired"][field] = {**describe(diffs, draws), "by_seat": [float(np.mean(v)) for v in seats],
                                   "positive_seats": sum(x > 0 for v in seats for x in v),
                                   "equal_seats": sum(x == 0 for v in seats for x in v),
                                   "negative_seats": sum(x < 0 for v in seats for x in v)}
    for field in ("match1win", "whole"):
        changes = []
        for s in cards:
            for t in (0, 1):
                before, after = measurements(base[s, t])[field], measurements(cand[s, t])[field]
                if before != after:
                    changes.append({"seed": s, "team": t, "reference": before, "candidate": after})
        result["transitions"][field] = changes
    result["direct_rate"] = describe([np.mean([direct[s, t]["win"] for t in (0, 1)]) for s in cards], draws)
    return result


def gates(phase, d):
    paired = d["paired"]
    direct = d["direct_rate"]
    if phase == "general":
        v = paired["whole"]["ci95"][0]
        conditions = {"route_a_external_lower_above_0": v > 0, "route_a_direct_mean_at_least_half": direct["mean"] >= .5,
                      "route_a_direct_lower_at_least_45pct": direct["ci95"][0] >= .45,
                      "route_b_direct_lower_above_half": direct["ci95"][0] > .5,
                      "route_b_external_lower_at_least_minus_1pp": v >= -.01}
        return conditions, all(v for k, v in conditions.items() if k.startswith("route_a")) or all(v for k, v in conditions.items() if k.startswith("route_b"))
    conditions = {"sight_earlier_at_least_one": paired["sight"]["mean"] >= 1,
                  "credit_no_later": paired["credit"]["mean"] >= 0, "margin70_no_worse": paired["margin70"]["mean"] >= 0,
                  "match1wins_no_fewer": paired["match1win"]["mean"] >= 0, "whole_wins_no_fewer": paired["whole"]["mean"] >= 0}
    if phase == "discovery":
        conditions.update(direct_at_least_half=direct["mean"] >= .5, at_least_8_affected_maps=d["solution"]["all"]["changed_maps"] >= 8)
    elif phase == "confirm":
        conditions.update(sight_lower_positive=paired["sight"]["ci95"][0] > 0)
    return conditions, all(conditions.values())


def eligibility(phase, ids, out):
    prior = {"confirm": "discovery", "general": "confirm"}.get(phase)
    if prior:
        previous = json.loads((out / prior / "ergebnis.json").read_text())
        require(len(ids) == 1 and ids[0] == previous["nominee"], "No eligible nominee from preceding stage")


def analyze(phase, cards, ids, rows, sources):
    require(phase in ("discovery", "confirm", "general"), "Unknown phase")
    exp = set(expected(phase, cards, ids))
    groups = {}
    seen = set()
    for r in rows:
        k = tuple(r[f] for f in ("phase", "seed", "team", "id", "opponent"))
        require(k in exp and k not in seen, f"Unexpected or duplicate case {k}")
        seen.add(k)
        validate(r, k, stamp(sources[r["id"]]))
        require(len({e[1] for e in r["events"]}) <= 1, f"Several scout identities in one game: {k}")
        groups.setdefault((r["id"], r["opponent"]), {})[r["seed"], r["team"]] = r
    require(seen == exp, f"Incomplete panel ({len(seen)}/{len(exp)})")
    draws = np.random.default_rng(BOOTSTRAP_SEED).integers(0, len(cards), size=(DRAWS, len(cards)))
    b = list(groups["reference", "solution92"].values())
    result = {"phase": phase, "maps": len(cards), "games": len(rows), "identities": {k: stamp(v) for k, v in sources.items()},
              "sampling": {"seed": BOOTSTRAP_SEED, "replicates": DRAWS, "unit": "map, both seats"},
              "reference": {"all": summary(b), "by_seat": {str(t): summary([r for r in b if r["team"] == t]) for t in (0, 1)}},
              "sensor_maps": dict(sorted(Counter(str(groups["reference", "solution92"][s, 0]["sensor"]) for s in cards).items())),
              "candidates": {}}
    for name in ids:
        d = score(name, cards, groups, draws)
        d["gates"], d["passed"] = gates(phase, d)
        result["candidates"][name] = d
    def ordering(k):
        d = result["candidates"][k]
        return (-d["paired"]["sight"]["mean"], -d["paired"]["match1margin"]["mean"], -d["solution"]["all"]["wins"], k)
    passed = sorted((i for i in ids if result["candidates"][i]["passed"]), key=ordering)
    result["nominee"] = passed[0] if passed else None
    return result


def check_complete(work, phase, cards, ids):
    all_games = {}
    for k in expected(phase, cards, ids):
        _, seed, team, name, opponent = k
        all_games[k] = work / phase / name / f"{seed}_{team}_{opponent}.json"
    existing = {p for n in ["reference", *ids] for p in (work / phase / n).glob("*.json")}
    require(existing == set(all_games.values()), f"Panel incomplete or extra games ({len(existing)}/{len(all_games)}), no scores opened")
    return [json.loads(all_games[k].read_text()) for k in sorted(all_games)]


def save_archive(rows, path):
    raw = "".join(json.dumps(r, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n" for r in rows).encode()
    blob = gzip.compress(raw, mtime=0)
    if path.exists():
        require(gzip.decompress(path.read_bytes()) == raw, "Raw archive content changed")
    else:
        with path.open("xb") as f:
            f.write(blob)
    with gzip.open(path, "rt") as f:
        return [json.loads(line) for line in f]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase", choices=("discovery", "confirm", "general"))
    p.add_argument("--ids", nargs="+", required=True)
    p.add_argument("--work", type=Path, default=SCRATCH)
    p.add_argument("--out", type=Path, default=HERE)
    a = p.parse_args()
    ids = sorted(a.ids)
    require(len(ids) == len(set(ids)) and "reference" not in ids, "Invalid candidate list")
    eligibility(a.phase, ids, a.out)
    cards = json.loads((HERE / "karten.json").read_text())[a.phase]
    lineup = json.loads((a.out / "kandidaten.json").read_text())
    require(ids == sorted(lineup) if a.phase == "discovery" else set(ids) <= set(lineup), "Candidate selection differs from registration")
    sources = {n: json.loads((a.work / "sources" / (n + ".json")).read_text()) for n in ["reference", *ids]}
    common = common_source()
    require(common == json.loads((a.work / "common.json").read_text()), "Benchmark source differs")
    for n, source in sources.items():
        verify_sources(source)
        if n != "reference":
            require(stamp(source) == lineup[n], "Frozen candidate differs from prior registration")
    data = check_complete(a.work, a.phase, cards, ids)
    result = analyze(a.phase, cards, ids, data, sources)
    target = a.out / a.phase
    target.mkdir(parents=True, exist_ok=True)
    reread = save_archive(data, target / "partien.jsonl.gz")
    require(analyze(a.phase, cards, ids, reread, sources) == result, "Archive did not reproduce conclusions")
    write_once(target / "herkunft.json", {"common": common, "sources": sources, "analysis_sha256": sha(Path(__file__)),
                                         "plan_sha256": sha(HERE / "PLAN.md"), "archive_sha256": sha(target / "partien.jsonl.gz")})
    write_once(target / "ergebnis.json", result)
    print(f"{a.phase}: {result['maps']} cards; {len(data)} verified complete games; nominee={result['nominee']}")


if __name__ == "__main__":
    main()
