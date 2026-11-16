"""Validate every seat and summarize game wins and observed handoffs."""
from collections import Counter
import json
import sys

from duelle import HERE, POLICY_STUDY, schedule, spiele

PREVIOUS = HERE.parent / "r3_field_20261116"
sys.path.insert(0, str(PREVIOUS))
from auswertung import compare, group, rows
from versuch import keys as previous_schedule


def assess():
    all_games = rows(HERE / "spiele", schedule())
    field = rows(PREVIOUS / "candidate", previous_schedule("candidate"))
    blend = rows(POLICY_STUDY / "candidate", spiele.jobs("candidate"))
    parents = rows(POLICY_STUDY / "control", spiele.jobs("control"))
    benchmark = {k: v for k, v in all_games.items() if k[2] in range(7549200, 7549240)}
    u = group(benchmark, "unit", "solution")
    r = group(benchmark, "r3", "solution")
    report = {"solution": dict(unit=sum(u.values()), r3=sum(r.values()), n=len(u), delta=compare(u, r)),
              "direct": {}, "routing": {}, "cases": {}}
    for opp in ("r3", "v15"):
        current = group(all_games, "unit", opp)
        prev_field = group(field, "field", opp)
        prev_blend = group(blend, "blend", opp)
        report["direct"][opp] = dict(n=len(current), unit=sum(current.values()), rate=compare(current),
                                     field=sum(prev_field.values()), delta_field=compare(current, prev_field),
                                     blend=sum(prev_blend.values()), delta_blend=compare(current, prev_blend))
    orig = group(parents, "r3", "v15")
    report["direct"]["v15"].update(r3=sum(orig.values()), delta_r3=compare(group(all_games, "unit", "v15"), orig))
    for key, row in all_games.items():
        arm, opponent, seed, side = key
        if arm != "unit":
            continue
        is_case = opponent == "solution" and key not in benchmark
        if is_case:
            report["cases"][f'{seed}/P{side[-1]}'] = dict(matches=row["our_wins"],
                                                         handoffs=row["routing"].get("handoffs", 0))
        stats = Counter(row["routing"])
        if not (0 <= stats["turns_all_retained_and_gained"] <= stats["turns_all_retained"] <=
                stats["turns_with_handoff"] <= stats["handoffs"]
                and 0 <= stats["observed_own_unit"] <= stats["observed_any_ally"] <= stats["handoffs"]
                and 0 <= stats["early_handoffs"] <= stats["handoffs"]):
            raise ValueError(f"Inconsistent follow-up counters at {key}")
        block = "cases" if is_case else opponent
        total = report["routing"].setdefault(block, Counter())
        total.update(stats)
        total["games"] += 1
        total["games_with_handoff"] += int(stats["handoffs"] > 0)
    return report


if __name__ == "__main__":
    print(json.dumps(assess(), indent=2, sort_keys=True))
