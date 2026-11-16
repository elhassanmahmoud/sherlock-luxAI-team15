"""Verify the fixed paired panels and compare game wins, matches and points."""
from collections import Counter
import json
import sys

from spielreihe import HERE, POLICIES, schedule, selected_cases, spiele

sys.path.insert(0, str(HERE.parent / "r3_field_20261116"))
from auswertung import compare, group, rows
sys.path.insert(0, str(POLICIES / "diagnose"))
from replay import originals


def totals(data, arm, opponent):
    games = [v for (a, b, _, _), v in data.items() if (a, b) == (arm, opponent)]
    return {k: sum(r[k] for r in games) for k in ("game_win", "our_wins", "our_points", "opp_points")} | {"n": len(games)}


def assess():
    data = rows(HERE / "controls", schedule("controls"))
    data.update(rows(HERE / "candidate", schedule("candidate")))
    fresh = {k:v for k,v in data.items() if 7165740 <= k[2] < 7165780}
    report = {"solution": {}, "direct": {}, "cases": {}, "routing": {}}
    for arm in ("defense", "r3", "v15"):
        report["solution"][arm] = totals(fresh, arm, "solution")
    candidate = group(fresh, "defense", "solution")
    for arm in ("r3", "v15"):
        report["solution"]["vs_" + arm] = compare(candidate, group(fresh, arm, "solution"))
    original = group(data, "r3", "v15")
    report["direct"]["r3_vs_v15"] = totals(data, "r3", "v15")
    for opponent in ("r3", "v15"):
        direct = group(data, "defense", opponent)
        report["direct"][opponent] = dict(**totals(data, "defense", opponent), rate=compare(direct))
    report["direct"]["vs_v15_relative_to_r3"] = compare(group(data, "defense", "v15"), original)
    _, references = originals(spiele.ROOT)
    prev_path = HERE.parent / "unit_handoff_20261116/archiv"
    unit = rows(prev_path, [("unit", "solution", s, p) for s in range(7158000, 7158040) for p in spiele.SEATS])
    for s, p in selected_cases():
        v = data["defense", "solution", s, p]
        report["cases"][f"{s}/P{p[-1]}"] = {
            "defense": v["our_wins"], "r3": references["r3"][s, p][1],
            "v15": references["v15"][s, p][1], "unit": unit["unit", "solution", s, p]["our_wins"],
            "defense_points": [v["our_points"], v["opp_points"]],
        }
    for (arm, opponent, seed, side), row in data.items():
        if arm != "defense":
            continue
        label = "cases" if (seed, side) in selected_cases() else opponent
        counts = Counter(row["routing"])
        if not (0 <= counts["changed_turns"] <= counts["changed_unit_actions"]
                and all(0 <= v <= counts["changed_unit_actions"] for v in counts.values())):
            raise ValueError("Inconsistent routing counts")
        agg = report["routing"].setdefault(label, Counter())
        agg.update(counts)
        agg["games_with_changes"] += int(counts["changed_turns"] > 0)
        agg["n"] += 1
    return report


if __name__ == "__main__":
    print(json.dumps(assess(), indent=2, sort_keys=True))
