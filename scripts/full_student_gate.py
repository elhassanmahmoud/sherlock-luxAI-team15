"""Evaluate the paired whole-policy students on the November 15 registered panels."""
import argparse
import json
import math
from pathlib import Path
from types import SimpleNamespace

from scripts import final_battle_assess as audit
from scripts import final_battle_compare as base
from scripts import full_student_study as fit
from scripts import points_hybrid_screen as points
from scripts.final_battle_select import OPPONENTS, checked_run_files
from scripts.train_combat_advice import publish_json


STUDENTS = ("historical", "plus_teacher")
ARCH = dict(feat_dim=79, n_actions=6, in_ch=16, ch=32, blocks=3, hidden=128, detach_value=True, sap_head=True)
# Digest of the six relative path -> SHA-256 entries in the frozen fit's metadata.
TRAINING_SOURCES = "4b4501d3b62b6a53ddad4772f5bb447665745c6435fb0ef9fd7d79b98074687f"
PANELS = {"screen": range(7281000, 7281016), "confirm": range(7281100, 7281160),
          "direct": range(7281200, 7281260)}
EVAL_SOURCES = ("scripts/full_student_gate.py", "scripts/points_hybrid_screen.py", "agents/__init__.py",
                "scripts/fetch_kaggle3.py", "scripts/protocol.py", "scripts/variants.py")


def correct_count(fraction, rows):
    """The trainer stores its Python integer quotient, before log formatting."""
    if type(rows) is not int or rows <= 0 or not isinstance(fraction, (int, float)) or not math.isfinite(fraction):
        raise ValueError("Invalid complete-command fraction or row count")
    n = round(fraction * rows)
    if not 0 <= n <= rows or n / rows != fraction:
        raise ValueError("Complete-command fraction does not identify an exact tally")
    return n


def offline_checks(control, candidate):
    return dict(mixed_at_least_control=candidate["mixed"] >= control["mixed"],
                expert_above_control=candidate["expert"] > control["expert"])


def load_checkpoint(path):
    import torch
    return torch.load(path, weights_only=True, map_location="cpu")


def offline(corpus, models):
    data = json.loads(corpus.read_bytes())
    expected = fit.roster()
    actual = {(r["cohort"], r["seed"], r["side"]): (r["split"], r["opponent"]) for r in data["files"]}
    if (actual != expected or len(actual) != len(data["files"]) or data["model"] != fit.MODEL
            or data["collector_sha256"] != fit.COLLECTOR_DIGEST or data["teacher"] != fit.TEACHER):
        raise ValueError("Manifest differs from the fixed data roster or training definition")
    _, _, groups = fit.arm_inputs(data["files"], "historical")
    counts, tallies, identities = {}, {}, {}
    runtime = None
    corpus_hash = base.digest(corpus)
    for arm in STUDENTS:
        path = models / (arm + ".pth")
        checkpoint = load_checkpoint(path)
        info = checkpoint["full_policy_study"]
        if (checkpoint["kind"] != "imitation" or checkpoint["arch"] != ARCH or checkpoint["feature_dim"] != 79
                or checkpoint["teacher"] != fit.TEACHER or checkpoint["sap_own_tile"] is not True
                or info["study"] != "whole_policy_20261115" or info["arm"] != arm or info["settings"] != fit.MODEL
                or info["manifest_sha256"] != corpus_hash or set(info["validation"]) != set(fit.COHORTS)
                or fit.digest_json(info["training_sources_sha256"]) != TRAINING_SOURCES):
            raise ValueError(f"Unexpected {arm} checkpoint, corpus or trainer")
        current = {k: info[k] for k in ("training_device", "torch_version", "numpy_version")}
        if runtime is not None and runtime != current:
            raise ValueError("Arms used different training environments")
        runtime = current
        identities[arm] = base.digest(path)
        counts[arm] = {}
        for cohort, start, stop in groups:
            v = info["validation"][cohort]
            rows = stop - start
            sap = v["legal_teacher_saps"]
            if v["rows"] != rows or type(sap) is not int or not 0 <= sap <= rows:
                raise ValueError(f"Unpaired {arm} validation rows or labels for {cohort}")
            shared = tallies.setdefault(cohort, dict(rows=rows, legal_teacher_saps=sap))
            if shared["legal_teacher_saps"] != sap:
                raise ValueError(f"Arms evaluated different legal SAP labels for {cohort}")
            shared[arm] = counts[arm][cohort] = correct_count(v["full_order"], rows)
    checks = offline_checks(counts["historical"], counts["plus_teacher"])
    return dict(manifest_sha256=corpus_hash, training_source_digest=TRAINING_SOURCES, runtime=runtime,
                models=identities, complete_orders=tallies, checks=checks, passes=all(checks.values()))


def panel(stage, arm):
    if (stage not in PANELS or arm not in ("v14", *STUDENTS)
            or (stage == "direct" and arm != "plus_teacher") or (stage == "confirm" and arm == "historical")):
        raise ValueError(f"No registered {stage} panel for {arm}")
    if stage == "direct":
        return PANELS[stage], ("v14",)
    return PANELS[stage], (*OPPONENTS, "v14") if (stage, arm) == ("screen", "plus_teacher") else OPPONENTS


def identity(stage, arm, receipt):
    seeds, opponents = panel(stage, arm)
    return dict(candidate=arm, first=seeds.start, maps=len(seeds), opponents=list(opponents),
                weights=audit.V14_SHA, model=receipt["models"].get(arm),
                offline_sha256=fit.digest_json(receipt),
                hybrid=None if arm == "v14" else {"mode": "points", "student_overrides": points.OVERRIDES})


def contract(options):
    stamp = identity(options.stage, options.candidate, options.receipt)
    # The ordinary contract binds both players, runtime agent code, engine and foreign opponent weights.
    m = base.contract(SimpleNamespace(**{**vars(options), "candidate": "v14"}))
    if (m["model"], m["weights"]) != (stamp["model"], stamp["weights"]):
        raise ValueError("Game model bytes differ from the inspected checkpoints")
    m.update(stamp)
    m["sources"].update({path: base.digest(base.ROOT / path) for path in EVAL_SOURCES})
    m["environment"] = points.environment()
    return m


def play(job):
    row = base.evaluate(job)
    if job[0] != "v14":
        agent = base.evaluate.agent
        if agent.v14.caught_errors or agent.student.caught_errors:
            raise RuntimeError("A branch of the points hybrid caught a policy error")
        row["study"] = dict(agent.stats)
    return row


def read_run(stage, arm, directory, receipt):
    seeds, opponents = panel(stage, arm)
    rows, m, hashes = checked_run_files(directory, arm, seeds, opponents)
    if any(m.get(key) != v for key, v in identity(stage, arm, receipt).items()):
        raise ValueError(f"Wrong {stage} model, offline selection or configuration for {arm}")
    if (not set(EVAL_SOURCES) <= m["sources"].keys() or not audit.CORE <= m["sources"].keys()
            or not m["environment"]["lux_modules"]):
        raise ValueError("Missing policy or runtime provenance")
    if "kaggle3" in opponents and any(m["sources"].get(audit.KAGGLE + name) != h
                                      for name, h in audit.WEIGHT_SHA256.items()):
        raise ValueError("Native Kaggle opponent weights differ")
    return audit.Run(m, rows, hashes)


def compatible(a, b):
    audit.compatible(a, b)
    both_native = all("kaggle3" in r.manifest["opponents"] for r in (a, b))
    def sources(r):
        return {k: v for k, v in r.manifest["sources"].items() if both_native or not k.startswith(audit.KAGGLE)}
    if a.manifest["environment"] != b.manifest["environment"] or sources(a) != sources(b):
        raise ValueError("Different runner, policy source or engine environment")


def selection(directory, receipt):
    v14, historical, candidate = [read_run("screen", arm, directory / arm, receipt)
                                  for arm in ("v14", *STUDENTS)]
    compatible(v14, historical)
    compatible(v14, candidate)
    block = PANELS["screen"]
    result = audit.summarize(audit.Phase(v14, candidate, candidate, block, block), "screen")
    opponents, external = audit.external_comparison(historical, candidate, block, "historical_wins")
    result["historical"] = dict(model=historical.manifest["model"], files=historical.hashes,
                                by_opponent=opponents, external=external)
    result["gates"]["external_at_least_historical"] = external["net_wins"] >= 0
    result["game_gates_pass"] = all(result["gates"].values())
    return result


def confirmation(directory, receipt, selected):
    reference, candidate = [read_run("confirm", arm, directory / arm, receipt) for arm in ("v14", "plus_teacher")]
    direct = read_run("direct", "plus_teacher", directory / "direct", receipt)
    screen_candidate = read_run("screen", "plus_teacher", directory.parent / "screen" / "plus_teacher", receipt)
    compatible(reference, candidate)
    compatible(candidate, direct)
    compatible(screen_candidate, candidate)
    result = audit.summarize(audit.Phase(reference, candidate, direct, PANELS["confirm"], PANELS["direct"]), "confirm")
    result["selection"] = selected
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", type=Path, required=True, help="Frozen full_student_study manifest")
    p.add_argument("--models", type=Path, required=True, help="Directory containing both final .pth files")
    p.add_argument("--out", type=Path, required=True, help="One study result directory, shared by all commands")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("offline")
    run = sub.add_parser("play")
    run.add_argument("stage", choices=tuple(PANELS))
    run.add_argument("arm", choices=("v14", *STUDENTS))
    run.add_argument("--workers", type=int, default=1, choices=(1, 2))
    summarize = sub.add_parser("assess")
    summarize.add_argument("stage", choices=("screen", "confirm"))
    a = p.parse_args()
    receipt = offline(a.corpus, a.models)
    a.out.mkdir(parents=True, exist_ok=True)
    gate_file = a.out / "offline.json"
    if a.command == "offline":
        publish_json(gate_file, receipt)
        print(json.dumps(receipt, indent=2))
        return
    if not receipt["passes"] or json.loads(gate_file.read_text()) != receipt:
        raise ValueError("The two final checkpoints did not earn this offline admission")
    selected = None
    if a.stage != "screen" or a.command == "assess":
        selected = selection(a.out / "screen", receipt)
        if a.stage != "screen" and not selected["game_gates_pass"]:
            raise ValueError("Registered screen did not nominate the student")
    if a.command == "assess":
        result = selected if a.stage == "screen" else confirmation(a.out / "confirm", receipt, selected)
        publish_json(a.out / a.stage / "assessment.json", result)
        print(json.dumps(result, indent=2, allow_nan=False))
        return
    seeds, foes = panel(a.stage, a.arm)
    folder = a.out / ("screen" if a.stage == "screen" else "confirm") / ("direct" if a.stage == "direct" else a.arm)
    model = None if a.arm == "v14" else str((a.models / (a.arm + ".pth")).resolve())
    args = SimpleNamespace(stage=a.stage, receipt=receipt, candidate=a.arm, first=seeds.start, maps=len(seeds),
                           opponents=",".join(foes), model=model, workers=a.workers, out=folder)
    folder.mkdir(parents=True, exist_ok=True)
    base.run(args, get_contract=contract, initializer=points.init_worker, play=play)


if __name__ == "__main__":
    main()
