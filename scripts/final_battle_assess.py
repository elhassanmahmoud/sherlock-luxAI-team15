"""Assess finished final_battle_compare runs, without loading agents or starting games.

python -m scripts.final_battle_assess screen --reference V14_EXT --candidate NEW_ALL
python -m scripts.final_battle_assess confirm --reference CONF_V14 --candidate CONF_EXT --direct CONF_DIRECT \
    --screen-reference V14_EXT --screen-candidate NEW_ALL

For distill, previous_enemy and own_command, pass --selection-control R2_SCREEN in both stages.
Only own_command also requires --confirmation-control R2_FRESH in the confirm stage. For
previous_enemy also pass --model-sha256 with the SHA-256 of the temporal training output.
Fractions and confidence bounds are on the 0–1 scale.
completed.json binds the JSONL rows. Manifest hashes in the report identify the configurations
actually compared. The own_command snapshot additionally records its runtime environment.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re

from scripts.fetch_kaggle3 import WEIGHT_SHA256
from scripts.final_battle_compare import POLICIES
from scripts.final_battle_select import OPPONENTS, SEATS, checked_run_files


V14_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
FIRST_MOVEMENT_MODEL = "5327d0ff4e2cc4b09bdcb43ae51fbd7dcc9f6d8487f79f4a7cfd1ad176813575"
STACK_RESERVE_SHA = "ed19e3df648821ad54b1fa3c2dbf0148f30f496dceeb4a921ba095f712af24c6"
R2_MODEL = "23fa6208d76e81940916388b9ee56c1d290693e8febfa53622442b64b0d33f96"
DISTILL_MODEL = "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"
OWN_COMMAND_MODEL = "a41e95000017aa853f277f8bf99d71ce4fdb8c45950751f942e6fde19570b153"
# Computed before the first game from the separate R5 runner snapshot. Native Kaggle
# sources and weights are included for external arms and omitted in direct-only duels.
OWN_SOURCE_DIGESTS = {
    ("v14", True): "44d2542e1c683aed6c5ce661ed56b25327242e53175c7a923b66215961019430",
    ("selective_movement", True): "9329ea12255fe151340415990df333376f60780dded38ef6802a40d82fde62d8",
    ("selective_movement", False): "558b20783f564e6f4b9f52eb7ce082705ca4f89d6376eaf245d72bf084f5fba1",
}
OWN_ENGINE_FILES = {"__init__.py", "env.py", "globals.py", "params.py", "profiler.py", "pygame_render.py",
                    "spaces.py", "state.py", "utils.py", "wrappers.py"}
SEED_BLOCKS = {
    "selective": (7271400, 7271500, 7271600),
    "dagger": (7272300, 7272400, 7272500),
    "stack_reserve": (7272300, 7272400, 7272500),
    "distill": (7273000, 7273100, 7273200),
    "previous_enemy": (7275000, 7275100, 7275200),
    "own_command": (7277000, 7277100, 7277200),
}
# In these snapshots the registered runner maps selective_movement to mode="movement".
# Temporal and ordinary agents share a manifest name. Pin the actual implementation.
_COMMON_MOVEMENT = {
    "scripts/final_battle_compare.py": "de6931510d847b0baa4dc7065ab01ef2a37613baed361ca85df1fe3b27e5d764",
    "scripts/combat_teacher_counterfactual.py": "9cfb62c6488b5ffae122487642e4ac72e2e054e728e5aa4d24635efa609d385d",
    "scripts/collect_combat_advice.py": "6d54e866cbb2e451216eea10679d71a04b164d403a9f624faab8895fe61ac24c",
}
MOVEMENT_SOURCES = {
    "own_command": {**_COMMON_MOVEMENT,
                    "scripts/final_battle_compare.py": "94a3730379641129f0d6de49ee492e9f76d226d3782b47d637fe2c86962f7365",
                    "scripts/selective_advice_agent.py": "89c8cda564e84e9ec0424aece1117702012179b498253210d2fda5f5354d502e",
                    "scripts/imitate.py": "48a1b5c133799dfd0a6ca83b61215d1243a873634b9bed24ae01e6077c35b10e"},

    "distill": {**_COMMON_MOVEMENT,
                "scripts/selective_advice_agent.py": "fc7540ce2e299ff4601bfa5c25e390b477ae65cc91a796b56432b9cb0a6759f1",
                "scripts/imitate.py": "fa80f17712f52e4236e2ff771e62c1a8a8cac616c76d02ce493a0b8635af2ccb"},
    "previous_enemy": {**_COMMON_MOVEMENT,
                       "scripts/selective_advice_agent.py": "21e333187eb6eec47ede4bb7461ecd1a17ca2f5bd248d0dffa775f1b859e0254",
                       "scripts/imitate.py": "710abbad1152f0e48e0fd8c0270bcb2cd067bcfce34cf9ecea7fe35dbf9de58e"},
}
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


def compatible(left, right, *, compare_checkpoint=True):
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
        if (compare_checkpoint and a["model"] != b["model"]) or sa != sb:
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


def external_comparison(reference, candidate, seeds, reference_label):
    n_games = len(seeds) * len(SEATS)
    by_opp, deltas = {}, {}
    for opponent in OPPONENTS:
        gains = losses = before = after = 0
        per_map = []
        for seed in seeds:
            difference = 0
            for side in SEATS:
                key = (opponent, seed, side)
                a = int(reference.games[key]["result"])
                b = int(candidate.games[key]["result"])
                before += a
                after += b
                gains += b > a
                losses += b < a
                difference += b - a
            per_map.append(difference / len(SEATS))
        deltas[opponent] = per_map
        by_opp[opponent] = dict(games=n_games, candidate_wins=after,
                                gained=gains, lost=losses, net_wins=after-before,
                                winrate_difference=(after-before)/n_games, difference_ci95=bounds(per_map))
        by_opp[opponent][reference_label] = before
    # One draw picks the entire map, retaining BOTH seats and BOTH external opponents.
    panel = [sum(row) / len(OPPONENTS) for row in zip(*(deltas[o] for o in OPPONENTS))]
    total_gain = sum(v["net_wins"] for v in by_opp.values())
    external = dict(games=n_games*len(OPPONENTS), net_wins=total_gain,
                    winrate_difference=sum(panel)/len(panel), difference_ci95=bounds(panel))
    return by_opp, external


def summarize(phase, stage):
    by_opp, external = external_comparison(phase.reference, phase.candidate, phase.external_seeds, "v14_wins")
    duel = phase.direct.games
    direct_by_map = [sum(duel["v14",seed,s]["result"] for s in SEATS)/len(SEATS) for seed in phase.direct_seeds]
    direct_wins = int(sum(direct_by_map)*len(SEATS))
    direct_games = len(direct_by_map)*len(SEATS)
    direct = dict(games=direct_games, wins=direct_wins, losses=direct_games-direct_wins,
                  winrate=direct_wins/direct_games, winrate_ci95=bounds(direct_by_map))
    gates = {"solution_at_least_reference":by_opp["solution92"]["net_wins"] >= 0,
             "direct_majority":direct["winrate"] > .5}
    if stage == "screen":
        gates["two_additional_external_wins"] = external["net_wins"] >= 2
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


def own_command_runtime(phase, control):
    reference = phase.reference.manifest.get("environment")
    for run in (phase.reference, phase.candidate, phase.direct, control):
        m = run.manifest
        native = "kaggle3" in m["opponents"]
        encoded = json.dumps(m["sources"], sort_keys=True, separators=(",", ":")).encode()
        if sha256(encoded).hexdigest() != OWN_SOURCE_DIGESTS.get((m["candidate"], native)):
            raise ValueError("Unregistered own-command game snapshot")
        env = m.get("environment", {})
        if (env != reference or not env.get("python") or not env.get("machine") or not env.get("platform")
                or not isinstance(env.get("flags"), dict) or set(env.get("engine", {})) != OWN_ENGINE_FILES
                or any(env["engine"].get(k) != v for k, v in m["engine"].items())
                or set(env.get("versions", {})) != {"numpy", "scipy", "torch", "jax", "jaxlib", "luxai-s3"}):
            raise ValueError("Different or incomplete own-command environment")


def selection_control(phase, directory, protocol):
    control = load_run(directory, "selective_movement", phase.external_seeds, OPPONENTS)
    if control.manifest["model"] != R2_MODEL:
        raise ValueError("Selection control must use the registered R2 checkpoint")
    compatible(phase.reference, control)
    compatible(control, phase.candidate, compare_checkpoint=False)
    # The registered runner adds only the bound movement sources to the V14 manifest.
    expected = {**phase.reference.manifest["sources"], **MOVEMENT_SOURCES[protocol]}
    if control.manifest["sources"] != expected:
        raise ValueError(f"Movement or reference implementation differs from the registered {protocol} snapshot")
    if protocol == "own_command":
        own_command_runtime(phase, control)
    by_opp, paired = external_comparison(control, phase.candidate, phase.external_seeds, "r2_wins")
    return {**paired, "by_opponent": by_opp, "model": R2_MODEL, "files": control.hashes,
            "r2_wins": sum(v["r2_wins"] for v in by_opp.values()),
            "candidate_wins": sum(v["candidate_wins"] for v in by_opp.values())}


def assess(args):
    protocol = getattr(args, "protocol", "selective")
    name = "stack_reserve" if protocol == "stack_reserve" else "selective_movement"
    model = args.model_sha256
    control_dir = getattr(args, "selection_control", None)
    fresh_control = getattr(args, "confirmation_control", None)
    needs_fresh_control = protocol == "own_command" and args.stage == "confirm"
    if bool(fresh_control) != needs_fresh_control:
        raise ValueError("--confirmation-control on the 60 fresh external maps is required only for own_command confirmation")
    if protocol in MOVEMENT_SOURCES:
        if not control_dir:
            raise ValueError(f"{protocol} requires --selection-control from the original 16 selection maps")
        if (args.screen_first, args.confirm_first, args.confirm_direct_first) != SEED_BLOCKS[protocol] or (
                args.screen_maps, args.confirm_maps) != (16, 60) or args.screen_direct_first not in (None, args.screen_first):
            raise ValueError(f"Map blocks differ from the registered {protocol} protocol")
        if protocol in ("distill", "own_command"):
            fixed = DISTILL_MODEL if protocol == "distill" else OWN_COMMAND_MODEL
            if model not in (None, fixed):
                raise ValueError(f"{protocol} requires the registered training checkpoint")
            model = fixed
        elif (not model or not re.fullmatch(r"[0-9a-f]{64}", model)
              or model in (FIRST_MOVEMENT_MODEL, R2_MODEL, DISTILL_MODEL, V14_SHA)):
            raise ValueError("previous_enemy requires --model-sha256 of the temporal training output")
    elif control_dir:
        raise ValueError("--selection-control applies only to movement protocols with an R2 control")
    if name == "stack_reserve" and model is not None:
        raise ValueError("stack_reserve uses the registered policy source without an extra checkpoint")
    first = args.screen_first
    screen_direct = first if args.screen_direct_first is None else args.screen_direct_first
    screen_maps = range(first, first + args.screen_maps)
    direct_maps = range(screen_direct, screen_direct + args.screen_maps)
    if args.stage == "screen":
        paths = args.reference, args.candidate, args.direct
    else:
        if not args.screen_reference or not args.screen_candidate:
            raise ValueError("Confirmation requires the actual completed selection runs")
        paths = args.screen_reference, args.screen_candidate, args.screen_direct
    screen = load_phase(*paths, screen_maps, direct_maps, name)
    if model is not None and screen.candidate.manifest["model"] != model:
        raise ValueError("Model differs from the registered checkpoint")
    report = summarize(screen, "screen")
    if control_dir:
        control = selection_control(screen, control_dir, protocol)
        report["selection_control"] = control
        report["gates"]["external_at_least_r2"] = control["net_wins"] >= 0
        report["game_gates_pass"] = all(report["gates"].values())
    if args.stage == "screen":
        return report
    if not report["game_gates_pass"]:
        if control_dir:
            raise ValueError(f"This candidate failed registered selection: {report['gates']}; "
                             f"external wins candidate {control['candidate_wins']}, R2 {control['r2_wins']}")
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
    if control_dir:
        compatible(screen.reference, confirmation.reference)
    result = summarize(confirmation, "confirm")
    if fresh_control:
        if screen.reference.manifest["environment"] != confirmation.reference.manifest.get("environment"):
            raise ValueError("Different own-command environment across study phases")
        paired = selection_control(confirmation, fresh_control, protocol)
        result["confirmation_control"] = paired
        result["gates"]["external_at_least_r2"] = paired["net_wins"] >= 0
        result["game_gates_pass"] = all(result["gates"].values())
    result["selection"] = report
    result["scope"] = "Whole-game gates only. Default, course and submission-package checks remain separate."
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("screen", "confirm"))
    parser.add_argument("--protocol", choices=tuple(SEED_BLOCKS), default="selective")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--direct", type=Path, help="Separate direct-only run; otherwise read V14 duels from --candidate")
    parser.add_argument("--selection-control", type=Path, help="External R2 run on the original 16 selection maps")
    parser.add_argument("--confirmation-control", type=Path, help="Fresh R2 external comparison for own_command confirmation")
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
    args.screen_first, args.confirm_first, args.confirm_direct_first = SEED_BLOCKS[args.protocol]
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
