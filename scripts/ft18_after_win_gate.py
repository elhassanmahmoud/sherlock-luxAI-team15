"""Fresh preregistered FT18-after-win screen and confirmation.

In the frozen diagnostic tree use the reusable final_battle_compare scheduler from
d566705, the published after_win/{PLAN.md,assessment.json,dev/manifest.json} and
the verified Kaggle opponent. All actor and opponent imports are local to this copy.

    python -m scripts.ft18_after_win_gate play screen candidate --root RESULTS
    python -m scripts.ft18_after_win_gate play screen v14 --root RESULTS
    python -m scripts.ft18_after_win_gate assess screen --root RESULTS

After nomination use play confirm for candidate, v14 and direct, and assess confirm.
Each play command defaults to one worker. Disk contents bind resumptions and reports.
"""
import argparse
import hashlib
from importlib import metadata, util
import json
import os
from pathlib import Path
import platform
import re
from types import SimpleNamespace

from scripts import final_battle_assess as audit
from scripts import final_battle_compare as base
from scripts.final_battle_select import OPPONENTS

ARM = "ft18_after_win"
ACTOR = "scripts.ft18_after_win:FT18AfterWinAgent"
STUDY = "scripts/ft18_after_win_gate.py"
PRIOR = "experiments/analysis/late_ft18_20261115/after_win/"
PRIOR_HASHES = {
    PRIOR + "dev/manifest.json": "da464277c77c64ce03bc43759d3ae52ffab0e630f564c551470edd14241e3f7f",
    PRIOR + "PLAN.md": "788b0fb9829bf51202c56589d9218cd566c69f692b6b33ba38ef3216de4888af",
    PRIOR + "assessment.json": "18fd2a3e134edc4522b0a56a0b89dd5565273b36c11b1ed22e118d53951f6b08",
}
# Evaluation-only dependencies, including the generic resumable scheduler from d566705.
HELPERS = ("scripts/final_battle_compare.py", "scripts/final_battle_assess.py", "scripts/final_battle_select.py",
           "scripts/residual_ensemble_compare.py", "scripts/variants.py", "scripts/fetch_kaggle3.py",
           "scripts/kaggle3_opponent.py", "agents/__init__.py", "lux/__init__.py", "lux/utils.py", "lux/kit.py")
HELPERS_SHA = "60477571d6540e0b7ae3d43ab4e9b2e3570ccd70be3a6282c63f66287b59acf5"
NATIVE_SHA = "b6f210571a404f741da1477a05473e421808bdb01b85868fa57948b6d2829371"


def spec(stage, arm):
    if stage not in ("screen", "confirm") or arm not in ("v14", "candidate", "direct"):
        raise ValueError("Unknown study arm")
    if stage == "screen" and arm == "direct":
        raise ValueError("The screen candidate includes all direct games")
    first = 7279000 if stage == "screen" else (7279200 if arm == "direct" else 7279100)
    opponents = OPPONENTS
    if arm == "direct":
        opponents = ("v14",)
    elif stage == "screen" and arm == "candidate":
        opponents = (*OPPONENTS, "v14")
    return SimpleNamespace(candidate="v14" if arm == "v14" else ARM, model=None,
                           opponents=",".join(opponents), first=first, maps=16 if stage == "screen" else 60)


def combined_sha(bindings):
    return hashlib.sha256(json.dumps(bindings, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def prior():
    path = PRIOR + "dev/manifest.json"
    if base.digest(base.ROOT / path) != PRIOR_HASHES[path]:
        raise ValueError("The registered diagnostic manifest changed")
    return json.loads((base.ROOT / path).read_text())


def register():
    # Spawned workers import a fresh policy registry.
    base.POLICIES[ARM] = ACTOR


def validate_sources(m):
    history = prior()
    sources = m["sources"]
    expected = {**history["source_sha256"], **PRIOR_HASHES, STUDY: base.digest(base.ROOT / STUDY)}
    native = {k: v for k, v in sources.items() if k.startswith(audit.KAGGLE)}
    if (any(sources.get(k) != h for k, h in expected.items())
            or set(sources) != set(expected) | set(HELPERS) | set(native)
            or combined_sha({k: sources[k] for k in HELPERS}) != HELPERS_SHA
            or (combined_sha(native) != NATIVE_SHA if "kaggle3" in m["opponents"] else bool(native))):
        raise ValueError("Sources differ from the registered diagnostic snapshot or native opponent")
    if (m["model"] is not None or m["weights"] != history["v14_sha256"]
            or m["engine"]["env.py"] != history["engine_sha256"]
            or m["engine"]["wrappers.py"] != history["wrapper_sha256"]):
        raise ValueError("Different V14 checkpoint or course engine")
    env = m["environment"]
    if (set(env["versions"]) != {"torch", "jax", "jaxlib", "luxai-s3", "numpy", "scipy"}
            or not all(env.get(k) for k in ("python", "platform", "machine"))
            or env["flags"]["PYTHONHASHSEED"] != "0"
            or any(env["lux_modules"].get(k) != h for k, h in m["engine"].items())):
        raise ValueError("Incomplete runtime binding")


def contract(a):
    register()
    m = base.contract(a)
    for name in {*prior()["source_sha256"], *PRIOR_HASHES, *HELPERS, STUDY}:
        m["sources"][name] = base.digest(base.ROOT / name)
    pkg = Path(util.find_spec("luxai_s3").origin).parent
    m["environment"] = {
        "python": platform.python_version(), "platform": platform.system(), "machine": platform.machine(),
        "versions": {k: metadata.version(k) for k in ("torch", "jax", "jaxlib", "luxai-s3", "numpy", "scipy")},
        "flags": {k: os.environ.get(k) for k in ("PYTHONHASHSEED", "JAX_PLATFORMS", "XLA_FLAGS", "CUDA_VISIBLE_DEVICES")},
        "lux_modules": {p.name: base.digest(p) for p in pkg.glob("*.py")},
    }
    validate_sources(m)
    return m


def init_worker(arm, model):
    register()
    base.init_worker(arm, model)
    from scripts.final_battle_candidates import tensor_sha256
    from scripts.ft18_movement_study import PrefixObserver
    agent = base.evaluate.agent
    loaded = [tensor_sha256(member.state_dict()) for member in [agent.q, *agent.extra_q]]
    if agent.cnn_policy is not None or loaded != prior()["tensor_sha256"]:
        raise ValueError("The loaded members differ from the ordered diagnostic V14 ensemble")
    base.evaluate.env = PrefixObserver(base.evaluate.env)


def play(job):
    from scripts.common import make_opponent, play_game
    from scripts.par_eval import require_no_agent_errors
    arm, opponent, seed, side, _ = job
    agent, env = base.evaluate.agent, base.evaluate.env
    other = "player_1" if side == "player_0" else "player_0"
    rival = make_opponent("self" if opponent == "v14" else opponent, other, self_play_path=str(base.WEIGHTS))
    row = play_game(env, agent, rival, seed, side, train=False)
    require_no_agent_errors(agent, rival)
    if row["steps"] != 303 or row["our_wins"] + row["opp_wins"] != 3:
        raise ValueError("Incomplete course game")
    output = dict(candidate=arm, opponent=opponent, seed=seed, side=side, steps=row["steps"], result=row["result"],
                  wins=row["our_wins"], losses=row["opp_wins"], points=row["our_points"], opp_points=row["opp_points"],
                  secs=row["secs"], first_match=env.first_match())
    if arm == ARM:
        counts = [r["before_rules_changed"] for r in agent.movement_statistics()]
        won = bool(output["first_match"]["wins_world"][int(side[-1])])
        if agent.first_won is not won or counts[0] or (not won and any(counts)):
            raise ValueError("Actual policy routing differs from the first public win")
        output.update(first_won=won, movement_changes_by_match=counts)
    return output


def gates(stage, r):
    sol, kaggle = r["by_opponent"]["solution92"], r["by_opponent"]["kaggle3"]
    if stage == "screen":
        return {"external_plus_two": r["external"]["net_wins"] >= 2,
                "solution_plus_one": sol["net_wins"] >= 1, "kaggle_at_least_minus_one": kaggle["net_wins"] >= -1,
                "direct_majority": r["direct"]["winrate"] > .5}
    if stage == "confirm":
        return {"external_lower_positive": r["external"]["difference_ci95"][0] > 0,
                "solution_lower_positive": sol["difference_ci95"][0] > 0,
                "direct_lower_above_half": r["direct"]["winrate_ci95"][0] > .5}
    raise ValueError(stage)


def check_first_match(row):
    prefix = row["first_match"]
    wins = prefix["wins_world"]
    if (prefix["steps"] != 101 or wins not in ([1, 0], [0, 1])
            or not re.fullmatch("[0-9a-f]{64}", prefix["actions_sha256"])
            or len(prefix["points_world"]) != 2 or any(type(v) is not int or v < 0 for v in prefix["points_world"])):
        raise ValueError("Incomplete first-match record")
    if row["candidate"] == ARM:
        changed = row["movement_changes_by_match"]
        won = bool(wins[int(row["side"][-1])])
        if (row["first_won"] is not won or len(changed) != 3 or any(type(v) is not int or v < 0 for v in changed)
                or changed[0] or (not won and any(changed))):
            raise ValueError("Impossible FT18 movement routing")


def compare_prefixes(reference, candidate):
    for key, row in reference.games.items():
        new = candidate.games[key]
        if row["first_match"] != new["first_match"]:
            raise ValueError(f"Different submitted first-match actions or endpoint: {key}")
        if not new["first_won"] and any(row[k] != new[k] for k in ("result", "wins", "losses", "points", "opp_points")):
            raise ValueError(f"Different unchanged V14 result after first-match loss: {key}")


def phase_report(root, stage):
    register()
    ext = spec(stage, "candidate")
    duel = ext if stage == "screen" else spec(stage, "direct")
    directory = root / stage
    phase = audit.load_phase(directory / "v14", directory / "candidate",
                             None if stage == "screen" else directory / "direct",
                             range(ext.first, ext.first + ext.maps), range(duel.first, duel.first + duel.maps), ARM)
    for run in (phase.reference, phase.candidate, phase.direct):
        validate_sources(run.manifest)
        if run.manifest["environment"] != phase.reference.manifest["environment"]:
            raise ValueError("Different runtimes within paired phase")
    for run in (phase.reference, phase.candidate) if phase.direct is phase.candidate else (phase.reference, phase.candidate, phase.direct):
        for row in run.games.values():
            check_first_match(row)
    compare_prefixes(phase.reference, phase.candidate)
    report = audit.summarize(phase, stage)
    report["gates"] = gates(stage, report)
    report["game_gates_pass"] = all(report["gates"].values())
    report["first_match_prefix_pairs"] = len(phase.reference.games)
    report["first_match_wins"] = {}
    for opponent in (*OPPONENTS, "v14"):
        games = phase.direct.games if opponent == "v14" else phase.candidate.games
        report["first_match_wins"][opponent] = sum(r["first_won"] for k, r in games.items() if k[0] == opponent)
    report["protocol_sha256"] = PRIOR_HASHES[PRIOR + "PLAN.md"]
    report["bootstrap"] = {"unit": "whole map, both seats; external opponents paired", "draws": 10000,
                           "seed": 2711, "interval": "95% percentile"}
    return report, phase


def nomination(root):
    report, phase = phase_report(root, "screen")
    if not report["game_gates_pass"]:
        raise ValueError(f"Selection did not nominate FT18 after win: {report['gates']}")
    return report, phase


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for kind in ("play", "assess"):
        p = sub.add_parser(kind)
        p.add_argument("stage", choices=("screen", "confirm"))
        p.add_argument("--root", required=True, type=Path)
        if kind == "play":
            p.add_argument("arm", choices=("candidate", "v14", "direct"))
            p.add_argument("--workers", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    selected = nomination(args.root) if args.stage == "confirm" else None
    if args.cmd == "assess":
        report, phase = phase_report(args.root, args.stage)
        if selected:
            audit.compatible(selected[1].candidate, phase.candidate)
            if selected[1].candidate.manifest["environment"] != phase.candidate.manifest["environment"]:
                raise ValueError("Different runtimes across selection and confirmation")
            report["selection"] = selected[0]
        print(json.dumps(report, indent=2, allow_nan=False))
        return
    a = spec(args.stage, args.arm)
    # Spawned workers must agree on Python's randomized string/set order regardless of job order.
    os.environ["PYTHONHASHSEED"] = "0"
    if selected and contract(a)["environment"] != selected[1].candidate.manifest["environment"]:
        raise ValueError("The selected runtime differs before confirmation play")
    a.out, a.workers = args.root / args.stage / args.arm, args.workers
    a.out.mkdir(parents=True, exist_ok=True)
    base.run(a, get_contract=contract, initializer=init_worker, play=play)


if __name__ == "__main__":
    main()
