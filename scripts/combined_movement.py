"""Fit and audit R7, a single R5-history network with R3's soft movement targets."""
import argparse
from collections import Counter
import inspect
import json
from pathlib import Path

from scripts import collect_combat_advice as collect
from scripts import own_command_study, selective_agreement, selective_dagger as dagger

CONTROL_FILES = {"r2": "r2.pth", "r3": "r3_soft.pth", "r5": "r5_own_command.pth"}
CONTROL_SHA = {"r2": own_command_study.R2_SHA,
               "r3": "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9",
               "r5": "a41e95000017aa853f277f8bf99d71ce4fdb8c45950751f942e6fde19570b153"}
CONTROL_REPORTS = {
    "r3": ("movement_dagger_20261115/r3_validation.json",
           "6d2cefcc03703596b44b87d0c611e44f015db2ba0fe6fcb708d9e1a1ec2ba523"),
    "r5": ("own_command_20261115/paired_validation.json",
           "aa7859ba3255de1faf1b4b5081df789d2842a7d79d6c90df94d6eb32f85b961c")}
SOURCE_FILES = (*own_command_study.SOURCES, "scripts/combined_movement.py", "scripts/train_combat_advice.py",
                "scripts/collect_combat_advice.py", "agents/sherlock/ppo_agent.py", "agents/sherlock/features.py",
                "agents/sherlock/imitation_agent.py", "scripts/experiment.py")
ROOT = Path(__file__).resolve().parents[1]


def check_output(path):
    # Restrict this study to scratch space, including when running from a second checkout.
    path = path.resolve()
    if not any(p.name == "imitation" and p.parent.name == "experiments" for p in path.parents):
        raise ValueError("R7 weights must go in an experiments/imitation directory")


def source_hashes():
    result = {key: collect.file_sha(ROOT/key) for key in SOURCE_FILES}
    # Bind the function that does the optimizer steps, even if the import path is redirected.
    actual_trainer = Path(inspect.getsourcefile(dagger.imitate.train_student)).resolve()
    if actual_trainer != (ROOT/"scripts/imitate.py").resolve():
        raise ValueError("Trainer was imported from a different source tree")
    return result


def check_digest(path, expected):
    if collect.file_sha(path) != expected:
        raise ValueError(f"Changed control file: {path}")


def bind_controls(directory, parent, inputs):
    import torch
    for name, filename in CONTROL_FILES.items():
        path = directory/filename
        check_digest(path, CONTROL_SHA[name])
        ck = torch.load(path, map_location="cpu", weights_only=True, mmap=True)
        settings = ck["selective_training"]
        if settings["inputs"] != inputs or settings["parent_sha256"] != parent:
            raise ValueError(f"{name} differs in data or collection policy")
    return {"control_sha256": dict(CONTROL_SHA), "source_sha256": source_hashes()}


def verify_targets(info):
    if (info["temperature"] != 2.0 or info["weight"] != 0.5
            or info["eligible_train_rows"] != 656134 or info["rows_with_multiple_legal_moves"] != 631325):
        raise ValueError("Soft-target coverage differs from the fixed R3 control")


def verify_fit(extra, settings):
    info = settings["movement_distillation"]
    verify_targets(info)
    if info["used_train_rows_per_epoch"] != [656134] * 5:
        raise ValueError("R7 did not consume the registered soft labels in all five epochs")
    if (extra["kind"] != own_command_study.KIND or extra["feature_dim"] != 85
            or len(extra["own_command"]["initial_parity"]["max_abs_by_head"]) != 3
            or extra["combined_movement"]["source_sha256"] != source_hashes()):
        raise ValueError("R7 initialization or executed source binding changed")


def offline_gate(mixed):
    candidate, r3, r5 = mixed["r7"], mixed["r3"], mixed["r5"]
    return {"net_at_least_r5": candidate["net"] >= r5["net"],
            "hurt_at_most_r3": candidate["hurt"] <= r3["hurt"],
            "one_strict": candidate["net"] > r5["net"] or candidate["hurt"] < r3["hurt"]}


def historical_rows(reports):
    rows = {}
    for name, (rel, expected) in CONTROL_REPORTS.items():
        path = reports/rel
        check_digest(path, expected)
        report = json.loads(path.read_text())
        if name == "r3":
            if report["model_sha256"] != CONTROL_SHA["r3"]:
                raise ValueError("R3 historical model mismatch")
        elif (report["candidate_sha256"], report["r2_sha256"]) != (CONTROL_SHA["r5"], CONTROL_SHA["r2"]):
            raise ValueError("R5 historical model mismatch")
        keyed = {(g["cohort"], g["seed"], g["side"]): g for g in report["games"]}
        if len(keyed) != len(report["games"]) or len(keyed) != 64:
            raise ValueError("Incomplete historical game keys")
        rows[name] = keyed
    return rows


def audit(a):
    import torch
    from scripts.experiment import limit_threads
    from scripts.selective_advice_agent import load_heads
    from scripts.train_combat_advice import publish_json
    limit_threads()
    if a.out.exists():
        raise FileExistsError(a.out)
    initial_digest = collect.file_sha(a.candidate)
    ck = torch.load(a.candidate, map_location="cpu", weights_only=True, mmap=True)
    inputs = ck["selective_training"]["inputs"]
    binding = bind_controls(a.controls, ck["selective_training"]["parent_sha256"], inputs)
    if ck["combined_movement"] != binding or ck["arch"]["feat_dim"] != 85 or ck.get("imitation_ensemble"):
        raise ValueError("R7 model identity, architecture or controls do not match")
    verify_fit(ck, ck["selective_training"])
    historical = historical_rows(a.reports)
    models = {"r3": load_heads(a.controls/CONTROL_FILES["r3"])[0], "r7": load_heads(a.candidate)[0]}
    totals, games = {}, []
    with torch.inference_mode():
        for cohort, split in inputs.items():
            counts = {name: Counter() for name in ("r2", "r3", "r5", "r7")}
            for row in split["val"]:
                key = cohort, row["seed"], row["side"]
                reference = historical["r5"][key]
                if any(reference[k] != row[k] for k in ("sha256","protocol")):
                    raise ValueError("Historical archive binding differs")
                candidates = [path/collect.filename(*key[1:]) for path in a.data]
                found = [path for path in candidates if path.is_file()]
                if len(found) != 1:
                    raise ValueError(f"Missing or duplicate archive {key}")
                check_digest(found[0], row["sha256"])
                measured = {name: dict(selective_agreement.measure(heads, found[0], with_history_scope=True))
                            for name, heads in models.items()}
                if any(measured["r3"][k] != v for k,v in historical["r3"][key]["counts"].items()):
                    raise ValueError(f"Live R3 evaluation no longer reproduces {key}")
                measured.update(r2=reference["r2"], r5=reference["own_command"])
                populations = ("rows","base_matches","history_rows","history_base_matches")
                if len({tuple(m[k] for k in populations) for m in measured.values()}) != 1:
                    raise ValueError(f"Unpaired decisions on {key}")
                for name, m in measured.items():
                    counts[name].update(m)
                games.append(dict(cohort=cohort, **row, counts=measured))
            totals[cohort] = {name: dict(c, net=c["helped"] - c["hurt"],
                                         history_net=c["history_helped"] - c["history_hurt"])
                              for name, c in counts.items()}
    mixed = totals["mixed"]
    if ((mixed["r5"]["net"], mixed["r3"]["hurt"], mixed["r7"]["rows"], mixed["r7"]["history_rows"])
            != (17481, 2343, 156243, 147228) or totals["original"]["r7"]["rows"] != 51048):
        raise ValueError("Validation populations or frozen control totals differ")
    checks = offline_gate(mixed)
    check_digest(a.candidate, initial_digest)
    result = dict(candidate_sha256=initial_digest, **binding, validation=totals, games=games,
                  control_reports_sha256={k:v[1] for k,v in CONTROL_REPORTS.items()},
                  offline_checks=checks, passes_offline_gate=all(checks.values()))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    publish_json(a.out, result)
    print(json.dumps({"validation": totals, "offline_checks": checks,
                      "passes_offline_gate": result["passes_offline_gate"]}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    train = sub.add_parser("train")
    train.add_argument("--parent", type=Path, required=True)
    train.add_argument("--original-data", type=Path, nargs="+", required=True)
    train.add_argument("--mixed-data", type=Path, nargs="+", required=True)
    train.add_argument("--device", choices=("auto","cpu","mps"), default="auto")
    assess = sub.add_parser("audit")
    assess.add_argument("--data", type=Path, nargs="+", required=True)
    assess.add_argument("--candidate", type=Path, required=True)
    assess.add_argument("--reports", type=Path, required=True)
    for cmd in (train, assess):
        cmd.add_argument("--controls", type=Path, required=True)
        cmd.add_argument("--out", type=Path, required=True)
    a = parser.parse_args()
    if a.command == "audit":
        audit(a)
        return
    check_output(a.out)
    a.combined_controls = a.controls
    a.own_command_r2 = a.controls/CONTROL_FILES["r2"]
    a.distill_movement = True
    a.train_first, a.train_count, a.val_first, a.val_count = 7272000,120,7272200,24
    dagger.train_mixed(a)


if __name__ == "__main__":
    main()
