"""Validate the fixed observation run and summarize repeated opportunities."""
import collections
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent.parent
SOURCE = HERE / "target_diagnosis_720_739.json"
REFERENCE = ROOT / "experiments/compare/autonomous_20261020/dev_reference.csv"
OUTPUT = HERE / "diagnosis_summary.json"


def main():
    data = json.loads(SOURCE.read_text())
    with REFERENCE.open(newline="") as stream:
        reference = {(int(r["seed"]), r["side"]): r for r in csv.DictReader(stream)
                     if r["opponent"] == "solution92"}
    expected = {(seed, side) for seed in range(500720, 500740)
                for side in ("player_0", "player_1")}
    games = data["games"]
    assert len(games) == 40
    assert {(g["seed"], g["side"]) for g in games} == expected
    checked = set()
    for game in games:
        ref = reference[(game["seed"], game["side"])]
        for key, value in game.items():
            if key == "secs":
                continue
            assert key in ref, key
            checked.add(key)
            try:
                equal = math.isclose(float(value), float(ref[key]), rel_tol=1e-9, abs_tol=1e-9)
            except (TypeError, ValueError):
                equal = str(value) == ref[key]
            assert equal, (game["seed"], game["side"], key, value, ref[key])
    rows = data["diagnostics"]
    assert len(rows) == 120
    assert len({(r["seed"], r["side"], r["match"]) for r in rows}) == 120
    totals = collections.Counter()
    per_game = collections.defaultdict(collections.Counter)
    for row in rows:
        for key, value in row.items():
            if key not in ("seed", "side", "match"):
                totals[key] += value
                per_game[(row["seed"], row["side"])][key] += value
    event_keys = (
        "steps_with_live_assignment_change", "uncovered_own_point_reassigned_to_live",
        "sap_geometry_strictly_better_proxy_centers",
        "pt_sap_stay_opportunities_blocked_by_negative_first_owner",
    )
    report = dict(
        reproduction_passed=40, checked_fields=sorted(checked),
        code_commit=data["code_commit"], totals=dict(totals),
        games_with_events={key: sum(row[key] > 0 for row in per_game.values()) for key in event_keys},
        source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        reference_sha256=hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
        conclusion="Both mechanisms occur repeatedly; test each separately. No causal strength claim.",
        limitations="Known development maps; repeated unit/step opportunities, not independent "
                    "events, lost points, actual damage, legal paths or counterfactual wins.",
    )
    with OUTPUT.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
