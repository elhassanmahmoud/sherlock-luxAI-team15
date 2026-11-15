"""Assess finished final_battle_compare runs, without loading agents or starting games.

python -m scripts.final_battle_assess screen --reference V14_EXT --candidate NEW_ALL
python -m scripts.final_battle_assess confirm --reference CONF_V14 --candidate CONF_EXT --direct CONF_DIRECT \
    --screen-reference V14_EXT --screen-candidate NEW_ALL

Use --protocol dagger or --protocol stack_reserve for the registered follow-ups. Fractions and confidence bounds are on the 0–1 scale.
completed.json binds the JSONL rows. Manifest hashes in the report identify the configurations
actually compared; the runner does not issue a signed manifest or separately log runtime parameters.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re

from scripts.fetch_kaggle3 import WEIGHT_SHA256
from scripts.final_battle_compare import POLICIES
from scripts.final_battle_select import OPPONENTS, SEATS, checked_run_files


V14_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
FIRST_MOVEMENT_MODEL = "5327d0ff4e2cc4b09bdcb43ae51fbd7dcc9f6d8487f79f4a7cfd1ad176813575"
STACK_RESERVE_SHA = "ed19e3df648821ad54b1fa3c2dbf0148f30f496dceeb4a921ba095f712af24c6"
KAGGLE = "experiments/opponents/kaggle3_lux3_048fn/"
CORE = {"agents/sherlock/main.py", "agents/sherlock/config.py", "agents/sherlock/features.py",
        "agents/Solution_92_Kaggle/agent.py", "scripts/common.py", "scripts/scoring.py",
        "scripts/final_battle_compare.py", "scripts/par_eval.py", "scripts/metrics.py",
        "scripts/experiment.py", "scripts/kaggle3_opponent.py"}


@dataclass
class Run:
    manifest: dict
    games: dict
    hashes: dict


def load_run(directory, name, seeds, opponents):
    directory = Path(directory)
    games, m, provenance = checked_run_files(directory, name, seeds, opponents)
    name = m["candidate"]
    if name not in POLICIES or type(m["first"]) is not int or type(m["maps"]) is not int:
        raise ValueError(f"Invalid run configuration in {directory}")
    if m["weights"] != V14_SHA or set(m["engine"]) != {"env.py", "params.py", "wrappers.py"}:
        raise ValueError(f"Invalid V14 / engine manifest in {directory}")
    sources = m["sources"]
    policy_file = POLICIES[name].split(":")[0].replace(".", "/") + ".py"
    required = CORE | {policy_file}
    if name.startswith("selective_"):
        required |= {"scripts/combat_teacher_counterfactual.py", "scripts/collect_combat_advice.py", "scripts/imitate.py"}
    if name == "stack_reserve":
        required.add("scripts/combat_teacher_counterfactual.py")
        if sources.get(policy_file) != STACK_RESERVE_SHA:
            raise ValueError(f"Unregistered stack_reserve policy SHA in {directory}")
    if "kaggle3" in opponents:
        required |= {KAGGLE + "agent/base.py", KAGGLE + "agent/agent.py"}
        if any(sources.get(KAGGLE + key) != h for key, h in WEIGHT_SHA256.items()):
            raise ValueError(f"Kaggle opponent weights differ in {directory}")
    if not required.issubset(sources):
        raise ValueError(f"Missing source bindings in {directory}: {sorted(required - sources.keys())}")
    hashes = [*sources.values(), *m["engine"].values()]
    model = m["model"]
    if model is not None:
        hashes.append(model)
    if any(not isinstance(h, str) or not re.fullmatch(r"[0-9a-f]{64}", h) for h in hashes):
        raise ValueError(f"Malformed SHA-256 in {directory}")
    if (name in ("v14", "stack_reserve") and model is not None) or (name.startswith("selective_") and model is None):
        raise ValueError(f"Unexpected checkpoint binding for {name}")
    return Run(m, games, provenance)


def compatible(left, right):
    a, b = left.manifest, right.manifest
    if a["weights"] != b["weights"] or a["engine"] != b["engine"]:
        raise ValueError("Incompatible V14/engine bindings")
    # A direct-only run legitimately omits the external Kaggle implementation. Its fixed
    # adapter, all V14/Solution code, and the evaluation runner must still match.
    both_kaggle = "kaggle3" in a["opponents"] and "kaggle3" in b["opponents"]
    def relevant(m):
        return {k:v for k,v in m["sources"].items() if both_kaggle or not k.startswith(KAGGLE)}
    sa, sb = relevant(a), relevant(b)
    if a["candidate"] == b["candidate"]:
        if a["model"] != b["model"] or sa != sb:
            raise ValueError("Candidate checkpoint or implementation changed across runs")
    else:
        # Called with the V14 reference first. A candidate may bind additional implementation files.
        if a["candidate"] != "v14" or any(sb.get(k) != v for k, v in sa.items()):
            raise ValueError("Reference, opponent or evaluation sources differ")


@dataclass
class Phase:
    reference: Run
    candidate: Run
    direct: Run
    external_seeds: range
    direct_seeds: range


def load_phase(reference, candidate, direct, external_seeds, direct_seeds, name="selective_movement"):
    if not external_seeds or not direct_seeds:
        raise ValueError("Each map block must be nonempty")
    ref = load_run(reference, "v14", external_seeds, OPPONENTS)
    if direct is None and external_seeds != direct_seeds:
        raise ValueError("The registered direct seeds require a separate --direct directory")
    opponents = OPPONENTS if direct is not None else (*OPPONENTS, "v14")
    cand = load_run(candidate, name, external_seeds, opponents)
    duel = load_run(direct, cand.manifest["candidate"], direct_seeds, ("v14",)) if direct is not None else cand
    compatible(ref, cand)
    compatible(cand, duel)
    return Phase(ref, cand, duel, external_seeds, direct_seeds)


def bounds(map_values):
    from scripts.residual_ensemble_compare import interval
    return interval(map_values, seed=2711, draws=10000)


def summarize(phase, stage):
    n_games = len(phase.external_seeds) * len(SEATS)
    by_opp, deltas = {}, {}
    for opponent in OPPONENTS:
        gains = losses = before = after = 0
        per_map = []
        for seed in phase.external_seeds:
            difference = 0
            for side in SEATS:
                key = (opponent, seed, side)
                a = int(phase.reference.games[key]["result"])
                b = int(phase.candidate.games[key]["result"])
                before += a
                after += b
                gains += b > a
                losses += b < a
                difference += b - a
            per_map.append(difference / len(SEATS))
        deltas[opponent] = per_map
        by_opp[opponent] = dict(games=n_games, v14_wins=before, candidate_wins=after,
                                gained=gains, lost=losses, net_wins=after-before,
                                winrate_difference=(after-before)/n_games, difference_ci95=bounds(per_map))
    # One draw picks the entire map, retaining BOTH seats and BOTH external opponents.
    panel = [sum(row) / len(OPPONENTS) for row in zip(*(deltas[o] for o in OPPONENTS))]
    total_gain = sum(v["net_wins"] for v in by_opp.values())
    external = dict(games=n_games*len(OPPONENTS), net_wins=total_gain,
                    winrate_difference=sum(panel)/len(panel), difference_ci95=bounds(panel))
    duel = phase.direct.games
    direct_by_map = [sum(duel["v14",seed,s]["result"] for s in SEATS)/len(SEATS) for seed in phase.direct_seeds]
    direct_wins = int(sum(direct_by_map)*len(SEATS))
    direct_games = len(direct_by_map)*len(SEATS)
    direct = dict(games=direct_games, wins=direct_wins, losses=direct_games-direct_wins,
                  winrate=direct_wins/direct_games, winrate_ci95=bounds(direct_by_map))
    gates = {"solution_at_least_reference":by_opp["solution92"]["net_wins"] >= 0,
             "direct_majority":direct["winrate"] > .5}
    if stage == "screen":
        gates["two_additional_external_wins"] = total_gain >= 2
    elif stage == "confirm":
        gates["external_lower_bound_positive"] = external["difference_ci95"][0] > 0
        gates["direct_lower_bound_above_half"] = direct["winrate_ci95"][0] > .5
    else:
        raise ValueError(stage)
    report = dict(stage=stage, candidate=phase.candidate.manifest["candidate"], model=phase.candidate.manifest["model"],
                reference_files=phase.reference.hashes, candidate_files=phase.candidate.hashes, direct_files=phase.direct.hashes,
                external_first=phase.external_seeds.start, direct_first=phase.direct_seeds.start,
                by_opponent=by_opp, external=external, direct=direct, gates=gates, game_gates_pass=all(gates.values()))
    if report["candidate"] == "stack_reserve":
        report["policy_sha256"] = phase.candidate.manifest["sources"]["scripts/stack_reserve.py"]
    return report


def assess(args):
    name = "stack_reserve" if getattr(args, "protocol", "selective") == "stack_reserve" else "selective_movement"
    if name == "stack_reserve" and args.model_sha256 is not None:
        raise ValueError("stack_reserve uses the registered policy source without an extra checkpoint")
    first = args.screen_first
    screen_direct = first if args.screen_direct_first is None else args.screen_direct_first
    screen_maps = range(first, first + args.screen_maps)
    direct_maps = range(screen_direct, screen_direct + args.screen_maps)
    if args.stage == "screen":
        phase = load_phase(args.reference, args.candidate, args.direct, screen_maps, direct_maps, name)
        if args.model_sha256 is not None and phase.candidate.manifest["model"] != args.model_sha256:
            raise ValueError("Model differs from the registered checkpoint")
        return summarize(phase, "screen")
    if not args.screen_reference or not args.screen_candidate:
        raise ValueError("Confirmation requires the actual completed selection runs")
    screen = load_phase(args.screen_reference, args.screen_candidate, args.screen_direct, screen_maps, direct_maps, name)
    if args.model_sha256 is not None and screen.candidate.manifest["model"] != args.model_sha256:
        raise ValueError("Model differs from the registered checkpoint")
    report = summarize(screen, "screen")
    if not report["game_gates_pass"]:
        raise ValueError("This candidate failed registered selection")
    external = range(args.confirm_first, args.confirm_first + args.confirm_maps)
    direct = range(args.confirm_direct_first, args.confirm_direct_first + args.confirm_maps)
    selected = set(screen_maps) | set(direct_maps)
    if selected.intersection(external) or selected.intersection(direct) or set(external).intersection(direct):
        raise ValueError("Confirmation blocks overlap selection or each other")
    confirmation = load_phase(args.reference, args.candidate, args.direct, external, direct, name)
    if screen.candidate.manifest["candidate"] != confirmation.candidate.manifest["candidate"]:
        raise ValueError("Confirmation is for a different candidate")
    compatible(screen.candidate, confirmation.candidate)
    result = summarize(confirmation, "confirm")
    result["selection"] = report
    result["scope"] = "Whole-game gates only. Default, course and submission-package checks remain separate."
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("screen", "confirm"))
    parser.add_argument("--protocol", choices=("selective", "dagger", "stack_reserve"), default="selective")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--direct", type=Path, help="Separate direct-only run; otherwise read V14 duels from --candidate")
    parser.add_argument("--model-sha256", help="Also pin the candidate to the registered training output")
    for flag in ("screen-reference", "screen-candidate", "screen-direct"):
        parser.add_argument("--"+flag, type=Path)
    parser.add_argument("--screen-direct-first", type=int, help="First separately registered direct screen map; defaults to the external screen block")
    args = parser.parse_args()
    if args.protocol == "selective":
        if args.model_sha256 not in (None, FIRST_MOVEMENT_MODEL):
            parser.error("The selective protocol uses the frozen first movement checkpoint")
        args.model_sha256 = FIRST_MOVEMENT_MODEL
    args.screen_maps, args.confirm_maps = 16, 60
    args.screen_first, args.confirm_first, args.confirm_direct_first = (
        (7271400, 7271500, 7271600) if args.protocol == "selective" else (7272300, 7272400, 7272500))
    try:
        result = assess(args)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"Invalid study input: {error}\n")
    result["protocol"] = args.protocol
    result["bootstrap"] = {"unit":"whole map, both seats; external opponents sampled together",
                           "draws":10000, "seed":2711, "generator":"PCG64", "interval":"95% percentile"}
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
