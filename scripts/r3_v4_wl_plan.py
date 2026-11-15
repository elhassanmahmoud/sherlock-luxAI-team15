"""Read the frozen offline evidence, check source bytes and assess the paired mechanism test."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

STUDY = Path("experiments/analysis/r3_v4_wl_20261115")
ROOT = Path(__file__).resolve().parents[1]
GAME = ("result", "wins", "losses", "points", "opp_points", "steps")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def registry():
    return json.loads((ROOT / STUDY / "registered.json").read_bytes())


def provenance(project):
    manifest = registry()
    for name, expect in manifest["inputs_sha256"].items():
        if digest(project / name) != expect:
            raise ValueError(f"Changed study input {name}")
    return dict(registration=digest(ROOT / STUDY / "registered.json"),
                plan=digest(ROOT / STUDY / "PLAN.md"), files=manifest["inputs_sha256"])


def cases(project):
    rows = registry()["cases"]
    output = {(r["seed"], r["side"], r["opponent"]):
              {k: r[k] for k in ("expected", "sequence", "group")} for r in rows}
    if len(output) != 10 or len(rows) != 10:
        raise ValueError("Changed or repeated registered case")
    return output


def evaluate(pairs):
    cases_by_group = {}
    for key, rows in pairs.items():
        a, b = rows["control"], rows["switch"]
        item = dict(seed=key[0], side=key[1], opponent=key[2], original=a["game"]["result"],
                    candidate=b["game"]["result"], original_matches=a["sequence"],
                    candidate_matches=b["sequence"], different_active=b["actor_stats"]["different_active"])
        cases_by_group.setdefault(a["group"], []).append(item)
    def group(name, outcomes, n):
        data = cases_by_group[name]
        if len(data) != n or any(s["original"] not in outcomes for s in data):
            raise ValueError(f"Unexpected historical controls for {name}")
        return data
    primary = group("dev_a_target", {0}, 2)
    risk = group("solution_risk", {1}, 1) + group("direct_risk", {1}, 2)
    secondary = group("hard_map_target", {0}, 1)
    saved = sum(s["candidate"] and s["different_active"] > 0 for s in primary)
    checks = dict(at_least_one_primary_rescue=saved >= 1,
                  all_three_reachable_wins_preserved=all(s["candidate"] == 1 for s in risk))
    return dict(paired_games=len(pairs), checks=checks, passes=all(checks.values()),
                hard_map_rescued=bool(secondary[0]["candidate"]), cases=cases_by_group)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    from scripts.r3_v4_wl_games import verified_pairs
    print(json.dumps(evaluate(verified_pairs(args.project)), indent=2, sort_keys=True))
