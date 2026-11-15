"""Read sealed restart-route panels. Stage development is retrospective, stage solution uses fresh maps."""
import argparse
import json
from pathlib import Path

from scripts import final_battle_assess as audit
from scripts import r3_route_games as study
from scripts.final_battle_select import SEATS
from scripts.train_combat_advice import publish_json


def check_origins(rows, archived):
    if (not archived.keys() <= rows.keys() or any(row != rows[key] for key, row in archived.items())
            or any(r["origin"] != ("archived" if key in archived else "fresh") for key, r in rows.items())):
        raise ValueError("Wrong, missing or re-executed archived seat")


def paired(reference, route, seeds):
    gains, losses, map_values = [], [], []
    wins = dict(reference=0, route=0)
    matches = dict(reference=0, route=0)
    for seed in seeds:
        step = 0
        for seat in SEATS:
            key = "solution92", seed, seat
            a, b = reference[key], route[key]
            delta = int(b["result"]) - int(a["result"])
            step += delta
            if delta > 0:
                gains.append((seed, seat))
            elif delta < 0:
                losses.append((seed, seat))
            for name, row in (("reference", a), ("route", b)):
                wins[name] += int(row["result"])
                matches[name] += row["wins"]
        map_values.append(step / len(SEATS))
    return dict(games=len(seeds) * len(SEATS), wins=wins, matches=matches, gained=gains, lost=losses,
                difference=sum(map_values) / len(seeds), difference_ci95=audit.bounds(map_values))


def assess(a):
    original, stamp = study.binding(a)
    def run(stage, arm, imported=None):
        rows, m, hashes = study.read(a, stage, arm, stamp)
        check_origins(rows, imported or {})
        return audit.Run(m, rows, hashes)

    meta = dict(bootstrap=dict(unit="whole map, retaining both seats", draws=10000, seed=2711, interval="95% percentile"),
                assessment_sources={p:study.battle.digest(study.battle.ROOT / p) for p in (
                    "scripts/r3_route_assess.py", "scripts/final_battle_assess.py", "scripts/residual_ensemble_compare.py")})
    if a.stage == "development":
        imported = study.archived(a, original)
        route = run("development", "route", imported)
        seeds = study.PANELS[a.stage][0]
        return dict(stage=a.stage, reused=len(imported), new=len(route.games) - len(imported), route_files=route.hashes,
                    v14_files=stamp["original"]["v14"], r3_files=stamp["original"]["r3"],
                    vs_v14=paired(original["v14"], route.games, seeds), vs_r3=paired(original["r3"], route.games, seeds),
                    scope="Development only; includes twelve outcome-selected historical positions", **meta)
    solutions = {arm:run("solution", arm) for arm in study.PANELS["solution"][2]}
    wins, passed = study.solution_gate({k:v.games for k,v in solutions.items()})
    seeds = study.PANELS["solution"][0]
    report = dict(stage="solution", wins=wins, solution_gate_passes=passed, files={k:v.hashes for k,v in solutions.items()},
                  vs_r3=paired(solutions["r3"].games, solutions["route"].games, seeds),
                  vs_v14=paired(solutions["v14"].games, solutions["route"].games, seeds), **meta)
    if a.stage == "solution":
        return report
    if not passed:
        raise ValueError("The independent Solution comparison did not pass")
    def external(arm):
        native = run("kaggle", arm)
        sol = solutions[arm]
        return audit.Run(native.manifest, {**sol.games, **native.games}, {"solution": sol.hashes, "kaggle": native.hashes})
    phase = audit.Phase(external("v14"), external("route"), run("direct", "route"), seeds, study.PANELS["direct"][0])
    result = audit.summarize(phase, "confirm")
    result.update(solution_pass=report, scope="External panel conditional on passing its Solution component. "
                  "Default, course, package and submission approval are separate.", **meta)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    study.arguments(parser)
    parser.add_argument("stage", choices=("development", "solution", "confirm"))
    args = parser.parse_args()
    result = assess(args)
    dest = args.out / args.stage / "assessment.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    publish_json(dest, result)
    print(json.dumps(result, indent=2, allow_nan=False))
