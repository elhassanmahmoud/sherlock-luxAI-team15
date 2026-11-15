"""Assess the 16-map coverage-restoration development screen, using completed games only."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from scripts.final_battle_assess import Run, bounds, compatible, load_run
from scripts.final_battle_select import OPPONENTS, SEATS, checked_run_files

NAME = "coverage_restore"
R2_SHA = "23fa6208d76e81940916388b9ee56c1d290693e8febfa53622442b64b0d33f96"
SEEDS = range(7272300, 7272316)
ROLES = (*OPPONENTS, "v14")
EXTRAS = {
    "scripts/coverage_restore.py": "b9cace02d583802d88d25f87a4c04a8203e85255394e150ad46cb642c11399b8",
    "scripts/coverage_restore_compare.py": "4c3a018ad52df3c4fcf0a6e3c0992d37d0e0a4c1f42c9e9692a1c0a1d61874f9",
}
# Canonical JSON digests of the actual reused manifests' source and engine entries.
SOURCE_SHA = {
    "v14": "b838dc94ca403992d92d1b38a086b957ddaa9f09d53f7c9621599cbd80fd0a62",
    "selective_movement": "adab51bd97b625718c0a9eb387afa61b45f3f66d409421dca08a7b3d148812ba",
}
ENGINE_SHA = "e268dee1dfffb818ddf92ae3e6d5f716a4aab10f25b6d1dec74265f1ea42d1b3"


def digest_dict(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify_candidate(r2, candidate):
    a, b = r2.manifest, candidate.manifest
    if a["candidate"] != "selective_movement" or b["candidate"] != NAME:
        raise ValueError("Unexpected movement or coverage candidate identity")
    if a["model"] != R2_SHA or b["model"] != R2_SHA:
        raise ValueError("Weights differ from the trained five-epoch R2 checkpoint")
    if (type(b["first"]) is not int or type(b["maps"]) is not int
            or b["first"] != a["first"] or b["maps"] != a["maps"]
            or sorted(b["opponents"]) != sorted(a["opponents"])):
        raise ValueError("Coverage and R2 map/opponent blocks differ")
    if a["weights"] != b["weights"] or a["engine"] != b["engine"]:
        raise ValueError("Base weights or engine differ")
    if set(EXTRAS) & a["sources"].keys() or b["sources"] != {**a["sources"], **EXTRAS}:
        raise ValueError("R2 and coverage must share the full original runner and sources plus the two registered files")


def contrast(left_games, right_games, opponents, seeds):
    """Paired differences on identical keys. Each bootstrap draw resamples entire cards."""
    wins = reference_wins = matches = reference_matches = 0
    rescued, lost, map_delta = [], [], []
    for seed in seeds:
        difference = 0
        for opponent in opponents:
            for side in SEATS:
                key = opponent, seed, side
                left, right = left_games[key], right_games[key]
                a, b = int(left["result"]), int(right["result"])
                wins += a
                reference_wins += b
                matches += left["wins"]
                reference_matches += right["wins"]
                difference += a-b
                if a != b:
                    (rescued if a>b else lost).append(dict(opponent=opponent, seed=seed, side=side))
        map_delta.append(difference/(len(opponents)*len(SEATS)))
    n = len(seeds)*len(opponents)*len(SEATS)
    return dict(games=n, wins=wins, game_losses=n-wins, reference_wins=reference_wins,
                reference_game_losses=n-reference_wins, match_wins=matches, reference_match_wins=reference_matches,
                rescued=len(rescued), lost=len(lost), rescued_keys=rescued, lost_keys=lost, net_wins=wins-reference_wins,
                delta_rate=(wins-reference_wins)/n, paired_95=bounds(map_delta))


def gates(net_external_r2, solution_net_r2, direct_net_r2, net_external_v14):
    return dict(external_gain_over_r2_at_least_two=net_external_r2>=2,
                solution_at_least_r2=solution_net_r2>=0, direct_at_least_r2=direct_net_r2>=0,
                external_at_least_v14=net_external_v14>=0)


def technical(games):
    rows = {opponent: Counter() for opponent in ROLES}
    maps = {opponent: set() for opponent in ROLES}
    for (opponent, seed, _side), row in games.items():
        coverage, initial = row["coverage_counts"], row["selective_counts"]
        if not isinstance(coverage,dict) or not isinstance(initial,dict) or row["study"] != initial:
            raise ValueError("Coverage and pre-restoration R2 counters must be logged separately")
        if any(type(v) is not int or v<0 for counts in (coverage,initial) for v in counts.values()):
            raise ValueError("Malformed technical counters")
        n = coverage.get("restored_fields",0)
        steps = coverage.get("changed_steps",0)
        threatened = coverage.get("fields_with_visible_enemy_in_range",0)
        last_cover = coverage.get("fields_with_only_last_cover",0)
        original_changes = initial.get("changed_unit_orders",0)
        if (n != coverage.get("changed_unit_orders",0) or n != coverage.get("movement",0)
                or coverage.get("rejected_orders",0) or n>original_changes or steps>min(n,300)
                or bool(steps)!=bool(n) or n+threatened+last_cover!=coverage.get("uncovered_candidate_fields",0)):
            raise ValueError("Inconsistent coverage intervention counters")
        rows[opponent].update(games=1, games_with_restore=int(n>0), restored_fields=n, affected_steps=steps,
                              original_r2_changes=original_changes, final_changes_vs_base=original_changes-n,
                              skipped_visible_enemy=threatened, skipped_last_cover=last_cover)
        if n:
            maps[opponent].add(seed)
    return {o:dict(c, maps_with_restore=len(maps[o])) for o,c in rows.items()}


def assess(v14_dir, r2_dir, candidate_dir):
    ref = load_run(v14_dir, "v14", SEEDS, OPPONENTS)
    r2 = load_run(r2_dir, "selective_movement", SEEDS, ROLES)
    compatible(ref,r2)
    for run in (ref,r2):
        m = run.manifest
        if digest_dict(m["sources"]) != SOURCE_SHA[m["candidate"]] or digest_dict(m["engine"]) != ENGINE_SHA:
            raise ValueError("Source or engine bindings differ from the registered reused runs")
    rows, manifest, hashes = checked_run_files(Path(candidate_dir), NAME, SEEDS, ROLES)
    candidate = Run(manifest, rows, hashes)
    verify_candidate(r2,candidate)

    comparisons = {}
    for name, comparator, roles in (("r2",r2,ROLES),("v14",ref,OPPONENTS)):
        comparisons[name] = {o:contrast(rows,comparator.games,(o,),SEEDS) for o in roles}
        comparisons[name]["external"] = contrast(rows,comparator.games,OPPONENTS,SEEDS)
    r = comparisons["r2"]
    criteria = gates(r["external"]["net_wins"],r["solution92"]["net_wins"],r["v14"]["net_wins"],
                     comparisons["v14"]["external"]["net_wins"])
    return dict(stage="development_screen", first=SEEDS.start, maps=len(SEEDS), model_sha256=R2_SHA,
                input_hashes=dict(v14=ref.hashes,r2=r2.hashes,coverage_restore=candidate.hashes),
                source_set_sha256=SOURCE_SHA, engine_set_sha256=ENGINE_SHA, coverage_sources=EXTRAS,
                candidate_minus=comparisons, technical=technical(rows), gates=criteria, game_gates_pass=all(criteria.values()),
                interval="Paired game-win-rate difference. 95% percentile, 10000 PCG64 draws, seed 2711. Each draw keeps both seats and all included opponents together.",
                scope="Development screen only. Qualification permits the separate fresh-map confirmation in PLAN.md.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ("v14","r2","candidate"):
        p.add_argument("--"+flag,type=Path,required=True)
    args = p.parse_args()
    print(json.dumps(assess(args.v14,args.r2,args.candidate),indent=2,allow_nan=False))
