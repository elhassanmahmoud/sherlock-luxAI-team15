#!/usr/bin/env python3
"""Independent, read-only recomputation of the closed artillery exposure study.

Only stdlib and NumPy are imported. No project code is imported/executed; no
agent, model, environment or training process is instantiated. The sole writes
are this audit's JSON/Markdown reports beside this file. Git is read-only.
"""
from __future__ import annotations

import ast
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RUN = HERE.parent / "run_v1"
TRACES = ROOT / "experiments/analysis/continuation_20261102/targeting"
HISTORICAL_RUN_HEAD = "76d01cf08177f85bf0b1fff7c2b007734ca21d3a"
HISTORICAL_TRACE_HEAD = "0c0dda642e9876141a705c2b8ed807a4f26ed870"
V14 = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
ZIP = "88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6"
KEYS = ((831006, "player_1"), (831043, "player_0"))
CHECKS = Counter()


def check(condition, category, detail):
    CHECKS[category] += 1
    if not condition:
        raise AssertionError(f"{category}: {detail}")


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def load_json(path):
    return json.loads(Path(path).read_text())


def typed_hash(value):
    """Independent implementation of the archived typed serialization contract.

    Each token is length-prefixed with an unsigned network-order uint64;
    dictionaries sort by key type/name; NumPy arrays include dtype and shape.
    Only actual archived types are accepted. No tensor/JAX imports are needed.
    """
    result = hashlib.sha256()

    def token(data):
        result.update(struct.pack(">Q", len(data)))
        result.update(data)

    def walk(item):
        kind = type(item)
        if kind is dict:
            token(b"dict")
            for key in sorted(item, key=lambda k: (type(k).__name__, str(k))):
                walk(key)
                walk(item[key])
        elif kind in (list, tuple):
            token(kind.__name__.encode())
            token(str(len(item)).encode())
            for child in item:
                walk(child)
        elif isinstance(item, np.ndarray):
            token(b"array")
            token(item.dtype.str.encode())
            token(str(item.shape).encode())
            token(item.tobytes(order="C"))
        elif kind in (type(None), str, bool, int, float):
            token(kind.__name__.encode())
            token(repr(item).encode())
        else:
            raise TypeError(f"Unsupported archived value: {kind}")

    walk(value)
    return result.hexdigest()


def helper_ast(blob):
    found = [node for node in ast.walk(ast.parse(blob))
             if isinstance(node, ast.FunctionDef) and node.name == "_artillery_ok"]
    check(len(found) == 1, "source_helper", "unique helper AST")
    return ast.dump(found[0], include_attributes=False)


def config_defaults(blob):
    classes = [n for n in ast.parse(blob).body
               if isinstance(n, ast.ClassDef) and n.name == "AgentConfig"]
    check(len(classes) == 1, "configuration", "unique AgentConfig definition")
    # literal_eval evaluates data only, never the module or a method.
    return {n.target.id: ast.literal_eval(n.value) for n in classes[0].body
            if isinstance(n, ast.AnnAssign)}


def normalized_config(raw, defaults):
    return {key: raw.get(key, value) for key, value in defaults.items()}


def training_formula(public, event, config):
    """Scalar conjunction derived independently from training=True semantics.

    Training never queries the estimator or uses art_splash thresholds. The
    configuration switches that determine whether the caller invokes the
    helper are outside this helper-only counterfactual.
    """
    uid = event["uid"]
    x, y = public["ally_pos"][uid]
    target = public["assigned"].get(str(uid))
    first = {tuple(v["position"]): v["uid"] for v in public["first_on_tile"]}
    held_point = bool(public["point_tiles"][x][y]) and first.get((x, y)) == uid
    reserved_target = bool(config["art_surplus"] and target is not None
                           and public["point_tiles"][target[0]][target[1]]
                           and sum(target) <= public["W"] - 1)
    hits_enough = int(event["arguments"]["sap"][2]) >= config["art_min_hits"]
    reserve = public["sap_cost"] * (1 + config["sap_reserve_k"]) + config["art_reserve"]
    energy_enough = float(public["ally_ene"][uid]) >= reserve
    threatened = False
    for (ex, ey), energy in zip(public["enemy_coords"], public["enemy_energies"]):
        distance = max(abs(ex - x), abs(ey - y)) if config["art_safe_cheb"] else abs(ex - x) + abs(ey - y)
        threatened |= energy >= public["sap_cost"] and distance <= public["sap_range"]
    safe_enough = not config["art_safe"] or not threatened
    gates = {
        "not_primary_point_holder": not held_point,
        "not_reserved_for_own_point": not reserved_target,
        "hits_enough": hits_enough,
        "energy_enough": energy_enough,
        "safe_enough": safe_enough,
    }
    rejected_at = next((k for k, value in gates.items() if not value), None)
    return all(gates.values()), gates, rejected_at


def reconstruct_hashes(public, event, config):
    ctx = {k: public[k] for k in ("W", "H", "sap_cost", "sap_range")}
    ctx["ally_pos"] = np.array(public["ally_pos"], dtype=np.int64)
    ctx["ally_ene"] = np.array(public["ally_ene"], dtype=np.float64)
    ctx["enemy_coords"] = np.array(public["enemy_coords"], dtype=np.int64).reshape(-1, 2)
    ctx["enemy_energies"] = np.array(public["enemy_energies"], dtype=np.float64)
    ctx["assigned"] = {int(k): tuple(v) for k, v in public["assigned"].items()}
    ctx["first_on_tile"] = {tuple(v["position"]): int(v["uid"]) for v in public["first_on_tile"]}
    belief = {"point_tiles": np.array(public["point_tiles"], dtype=bool)}
    return {
        "cfg": typed_hash(config),
        "param_est": typed_hash({"posterior": "not serialized; never queried"}),
        "belief": typed_hash(belief),
        "ctx": typed_hash(ctx),
        "sap": typed_hash(tuple(event["arguments"]["sap"])),
    }


def historical_sources(mapping, head, original_prefix):
    details = []
    for path, expected in mapping.items():
        if path.startswith(original_prefix + "/"):
            relative = path[len(original_prefix) + 1:]
            actual = sha_bytes(git("show", f"{head}:{relative}"))
            mode = "historical_git_blob"
        else:
            relative = path
            actual = file_sha(path)
            mode = "external_runtime_file_current_bytes"
        check(actual == expected, "historical_source_hash", path)
        details.append({"path": relative, "sha256": actual, "method": mode})
    return details


def audit():
    manifest_path = RUN / "manifest.json"
    original_manifest_path = TRACES / "manifest.json"
    acceptance_path = HERE / "root-acceptance.json"
    manifest = load_json(manifest_path)
    original = load_json(original_manifest_path)
    acceptance = load_json(acceptance_path)
    current_head = git("rev-parse", "HEAD").decode().strip()
    check(manifest["source"]["head"] == HISTORICAL_RUN_HEAD, "provenance", "run HEAD")
    check(original["git_head"] == HISTORICAL_TRACE_HEAD, "provenance", "trace HEAD")
    check(manifest["status"] == original["status"] == "complete", "provenance", "closed runs")
    check(manifest["games"] == manifest["training_updates"] == manifest["model_forwards"] == 0,
          "scope", "archived zero-work counters")
    check(original["weights"]["sha256"] == V14, "protected_hash", "original trace V14")
    expected_protected = {
        str(ROOT / "Gruppe15.zip"): ZIP,
        str(ROOT / "agents/sherlock/weights/agent_p0.pth"): V14,
        str(ROOT / "agents/sherlock/weights/agent_p1.pth"): V14,
    }
    check(manifest["protected"] == expected_protected, "protected_hash", "exact protected inventory")
    outputs = {p: h for r in manifest["trace_reports"] for p, h in r["artifacts"].items()}
    bound = {**manifest["inputs"], **manifest["protected"], **outputs}
    for path, expected in bound.items():
        check(file_sha(path) == expected, "bound_file_hash", path)
    check(acceptance["status"] == "PASS" and acceptance["source_head"] == HISTORICAL_RUN_HEAD,
          "root_acceptance", "historical acceptance identity")
    check(acceptance["manifest_sha256"] == file_sha(manifest_path), "root_acceptance", "manifest hash")
    check(acceptance["inputs"] == manifest["inputs"] and acceptance["protected"] == manifest["protected"],
          "root_acceptance", "bound input and protected inventory")

    # Historical Git bindings are intentionally NOT compared with current HEAD.
    sources = historical_sources(manifest["source"]["files"], HISTORICAL_RUN_HEAD, str(ROOT))
    old_prefix = next(p.rsplit("/agents/sherlock/main.py", 1)[0]
                      for p in original["sources"] if p.endswith("/agents/sherlock/main.py"))
    original_sources = historical_sources(original["sources"], HISTORICAL_TRACE_HEAD, old_prefix)
    check(file_sha(manifest["source"]["executable"]) == manifest["source"]["executable_sha256"],
          "runtime", "recorded executable bytes")
    check(Path(manifest["source"]["python"]).resolve() == Path(manifest["source"]["executable"]),
          "runtime", "recorded interpreter resolution")

    observed_paths = set(bound) | set(manifest["source"]["files"])
    observed_paths |= {str(manifest_path), str(acceptance_path), str(Path(__file__).resolve())}
    before = {path: file_sha(path) for path in sorted(observed_paths)}
    current_source_differences = [path for path, value in manifest["source"]["files"].items()
                                  if before[path] != value]
    old_main = git("show", f"{HISTORICAL_TRACE_HEAD}:agents/sherlock/main.py")
    run_main = git("show", f"{HISTORICAL_RUN_HEAD}:agents/sherlock/main.py")
    old_ast = helper_ast(old_main)
    run_ast = helper_ast(run_main)
    current_ast = helper_ast((ROOT / "agents/sherlock/main.py").read_bytes())
    check(old_ast == run_ast == current_ast, "source_helper", "trace/run/current helper identity")
    expected_history = {
        "historical_head": HISTORICAL_TRACE_HEAD,
        "historical_main_sha256": sha_bytes(old_main),
        "current_main_sha256": sha_bytes(run_main),
        "helper_ast_sha256": sha_bytes(run_ast.encode()),
        "helper_code_identical": True,
        "full_agent_source_identical": old_main == run_main,
        "config_rule": "normalized full trace config equals normalized historical game config",
    }
    check(manifest["history"] == expected_history, "provenance", "complete history record")
    defaults = config_defaults(git("show", f"{HISTORICAL_RUN_HEAD}:agents/sherlock/config.py"))
    check([(v["key"]["seed"], v["key"]["side"]) for v in manifest["trace_reports"]] == list(KEYS),
          "trace_inventory", "exact preselected trace order")
    expected_inputs = {str(original_manifest_path),
                       str(ROOT / "docs/superpowers/plans/2026-11-08-artillery-training-exposure.md")}
    expected_inputs.update(str(TRACES / f"{seed}_{side}.jsonl.gz") for seed, side in KEYS)
    check(set(manifest["inputs"]) == expected_inputs, "trace_inventory", "exact input inventory")
    results, event_evidence = [], []
    total = Counter({f"{e}_{t}": 0 for e in ("false", "true") for t in ("false", "true")})
    for seed, side in KEYS:
        original_games = [g for g in original["games"] if (g["key"]["seed"], g["key"]["side"]) == (seed, side)]
        check(len(original_games) == 1, "trace_inventory", f"unique original game {seed}/{side}")
        game = original_games[0]
        report = next(r for r in manifest["trace_reports"] if r["key"] == {"seed": seed, "side": side})
        path = TRACES / f"{seed}_{side}.jsonl.gz"
        output = RUN / f"{seed}_{side}.helper_calls.jsonl"
        check(game["trace"]["path"] == path.name and game["trace"]["sha256"] == file_sha(path),
              "trace_hash", f"original trace {seed}/{side}")
        check(game["complete"] and all(game["passivity"].values()) and all(game["baseline_reproduction"].values()),
              "original_manifest", f"historical declared passivity/completion {seed}/{side}")
        for field, status in game["passivity"].items():
            check(status is True and game["observed"][field] == game["unobserved"][field],
                  "original_manifest", f"actual manifest passivity field {field}")
        with gzip.open(path, "rt") as stream:
            records = [json.loads(line) for line in stream]
        saved = [json.loads(line) for line in output.read_text().splitlines()]
        check(set(report["artifacts"]) == {str(output)}, "trace_inventory", "one exact output per trace")
        observed_config = normalized_config(game["observed"]["config"], defaults)
        statuses = Counter()
        keys, diff_keys, combinations, rejections = set(), set(), Counter(total), Counter()
        combinations.clear()
        combinations.update({key: 0 for key in total})
        action_digest = hashlib.sha256()
        event_index = 0
        for step, record in enumerate(records):
            record_before = typed_hash(record)
            key = record["key"]
            check((key["seed"], key["side"], key["obs_step"]) == (seed, side, step),
                  "row_key", f"{seed}/{side}/{step}")
            check((key["match_idx"], key["match_step"]) == divmod(step, 101),
                  "row_key", f"match coordinates {seed}/{side}/{step}")
            statuses[record["status"]] += 1
            check(record["status"] in ("reset", "decision"), "row_status", f"step {step}")
            action_digest.update(typed_hash(record["native_actions"]).encode())
            event_orders = [event["order"] for event in record.get("events", [])]
            check(len(set(event_orders)) == len(event_orders) and event_orders == sorted(event_orders),
                  "event_order", f"all archived event orders at step {step}")
            for event in record.get("events", []):
                if event["method"] != "_artillery_ok":
                    continue
                check(record["status"] == "decision", "event_status", f"helper decision {step}")
                check(event_index < len(saved), "event_bijection", "output row missing")
                out = saved[event_index]
                event_index += 1
                uid = event["uid"]
                public = record["public"]
                check(type(uid) is int and 0 <= uid < len(public["ally_pos"]), "context", "valid uid")
                check((out["seed"], out["side"], out["step"], out["uid"], out["event_order"]) ==
                      (seed, side, step, uid, event["order"]), "event_bijection", "complete ordered event identity")
                check((step, uid, event["order"]) not in keys, "event_bijection", "unique helper event key")
                keys.add((step, uid, event["order"]))
                check(event["return_status"] == "returned" and type(event["return"]) is bool,
                      "archived_eval", "successful boolean return")
                check(type(out["eval_verdict"]) is bool and out["eval_verdict"] is event["return"],
                      "archived_eval", "saved eval equals original return")
                check(event["arguments"] == event["arguments_after"] and set(event["arguments"]) == {"sap"},
                      "arguments", "stable sole SAP argument")
                sap = event["arguments"]["sap"]
                check(len(sap) == 3 and all(type(value) is int for value in sap), "arguments", "integer SAP triple")
                check(out["estimated_hits"] == sap[2], "arguments", "saved hits")
                unit = event["unit_context"]
                check(unit["position"] == public["ally_pos"][uid] and unit["energy"] == public["ally_ene"][uid]
                      and unit["target"] == public["assigned"].get(str(uid)), "context", "event/public unit agreement")
                check(np.asarray(public["point_tiles"]).shape == (public["W"], public["H"]),
                      "context", "point map dimensions")
                check(len(public["enemy_coords"]) == len(public["enemy_energies"])
                      and np.isfinite(public["ally_ene"]).all() and np.isfinite(public["enemy_energies"]).all(),
                      "context", "enemy alignment and finite energies")
                check(len(public["first_on_tile"]) == len({tuple(x["position"]) for x in public["first_on_tile"]}),
                      "context", "unique first-on-tile positions")
                config = normalized_config(public["config"], defaults)
                check(config == observed_config, "configuration", "full normalized config agreement")
                needed = {"art_surplus", "art_min_hits", "art_safe", "art_splash", "art_splash_hits",
                          "splash_min_drop", "splash_safe_below", "sap_reserve_k", "art_reserve", "art_safe_cheb"}
                check(needed <= set(public["config"]), "configuration", "all helper config explicit")
                training, gates, rejected_at = training_formula(public, event, config)
                check(type(out["training_verdict"]) is bool and out["training_verdict"] is training,
                      "training_formula", f"{seed}/{side}/{step}/{uid}")
                # This caller switch does not enter the helper formula; both
                # settings are checked without pretending to replay a recipe.
                toggled = dict(config, rules_in_training_all=not config["rules_in_training_all"])
                check(training_formula(public, event, toggled)[0] == training,
                      "training_formula", "rules_in_training_all irrelevant within helper")
                expected_hashes = reconstruct_hashes(public, event, config)
                for state_name, digest in expected_hashes.items():
                    check(out["before"].get(state_name) == digest, "state_before", state_name)
                    check(out["after"].get(state_name) == digest, "state_after", state_name)
                check(set(out["before"]) == set(out["after"]) == set(expected_hashes),
                      "state_inventory", "all five state hashes")
                check(out["training_min_hits"] == config["art_min_hits"] and out["training_dropoff"] == 0.0
                      and out["eval_dropoff"] is None and out["eval_source"] == "archived event; not recomputed"
                      and out["eval_dropoff_status"] == "historical estimator posterior unavailable",
                      "interpretation", "exact archived/counterfactual labels")
                combination = f"{str(event['return']).lower()}_{str(training).lower()}"
                combinations[combination] += 1
                rejections[rejected_at or "accepted"] += 1
                if event["return"] != training:
                    diff_keys.add((step, uid, event["order"]))
                event_evidence.append({"seed": seed, "side": side, "step": step, "uid": uid,
                                       "event_order": event["order"], "eval_archived": event["return"],
                                       "training_recomputed": training, "gates": gates,
                                       "first_rejection": rejected_at, "all_state_hashes_reproduced": True})
            check(typed_hash(record) == record_before, "record_unchanged", f"{seed}/{side}/{step}")
        check(event_index == len(saved), "event_bijection", "no surplus output events")
        reconstructed = {
            "key": {"seed": seed, "side": side},
            "trace_rows": len(records), "decision_rows": statuses["decision"],
            "helper_calls": event_index, "unique_step_uid": len({k[:2] for k in keys}),
            "verdict_combinations": dict(combinations), "differing_helper_calls": len(diff_keys),
            "differing_unique_step_uid": len({k[:2] for k in diff_keys}),
            "archived_native_actions_digest": action_digest.hexdigest(),
            "actions_unchanged_in_memory": True, "artifacts": {str(output): file_sha(output)},
        }
        check(reconstructed == report, "report_reproduction", f"all report fields {seed}/{side}")
        check(statuses == {"reset": 3, "decision": 300} and len(records) == 303,
              "trace_completeness", f"303 trace rows {seed}/{side}")
        check(statuses == game["observed"]["statuses"], "trace_completeness", "original status totals")
        reconstructed["first_rejection_counts"] = dict(rejections)
        reconstructed["differing_keys"] = [list(key) for key in sorted(diff_keys)]
        results.append(reconstructed)
        total.update(combinations)
    check(sum(total.values()) == acceptance["helper_calls"], "root_acceptance", "helper count independently reproduced")
    check(total["false_true"] + total["true_false"] == acceptance["different"],
          "root_acceptance", "difference count independently reproduced")
    after = {path: file_sha(path) for path in before}
    for path in before:
        check(before[path] == after[path], "audit_inputs_unchanged", path)
    check(git("rev-parse", "HEAD").decode().strip() == current_head, "audit_inputs_unchanged", "current HEAD")
    prohibited = [name for name in sys.modules if name.split(".")[0] in ("agents", "scripts", "torch", "jax", "luxai_s3", "pytest")]
    check(not prohibited, "scope", f"prohibited runtime imports: {prohibited}")
    return {
        "status": "PASS", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Closed archived-helper diagnosis only; no games/model loading/forwards/updates/pytest/project imports.",
        "audit_script": str(Path(__file__).resolve()), "audit_script_sha256": file_sha(__file__),
        "python": sys.executable, "numpy_version": np.__version__,
        "historical_run_head": HISTORICAL_RUN_HEAD, "historical_trace_head": HISTORICAL_TRACE_HEAD,
        "current_audit_head": current_head, "current_head_is_not_historical_run_head": current_head != HISTORICAL_RUN_HEAD,
        "historical_source_bindings": sources, "original_trace_source_bindings": original_sources,
        "current_source_differences_from_closed_run": current_source_differences,
        "history_reproduced": expected_history,
        "source_binding_note": "Historical repository files were hashed from their recorded Git commits. External runtime files were checked by their current bytes. A later HEAD is not rejected or substituted for the recorded run HEAD.",
        "checks": dict(CHECKS), "checks_total": sum(CHECKS.values()),
        "event_count": sum(total.values()), "verdict_combinations": dict(total),
        "trace_reports_reproduced": results, "per_event_reconstruction": event_evidence,
        "file_sha256_before": before, "file_sha256_after": after,
        "protected": expected_protected, "prohibited_modules_loaded": prohibited,
        "limitations": [
            "The original evaluation boolean is independently recovered from its original event, not recomputed; the step-local estimator posterior was not archived.",
            "All five stored before/after hashes were independently reconstructed from original inputs; no claim that hashing can prove historical execution beyond the archived evidence.",
            "The post-act point/assignment stability premise is supported by the existing separate source review; event-time unit position, energy and target are rechecked for every event here.",
            "Original manifest passivity fields agree, but the historical joint two-policy action digest cannot be regenerated from the archived own-actions stream alone.",
            "Selected correlated states do not measure final action changes, action quality, training effects, prevalence or strength; no training-rule change, new run or promotion follows from this audit.",
        ],
    }


def markdown(report):
    if report["status"] != "PASS":
        return f"# Independent artillery data audit\n\nBLOCKED: {report['error']}\n"
    lines = ["# Independent artillery data audit", "", "PASS", "",
             f"All {report['event_count']} helper events independently reconstructed from the two original compressed traces; {report['checks_total']} checks passed.", "",
             "| Trace | Events | Eval F / Train F | Eval F / Train T | Eval T / Train F | Eval T / Train T |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for item in report["trace_reports_reproduced"]:
        c = item["verdict_combinations"]
        lines.append(f"| {item['key']['seed']}/{item['key']['side']} | {item['helper_calls']} | {c['false_false']} | {c['false_true']} | {c['true_false']} | {c['true_true']} |")
    lines += ["", "The training result uses an independent scalar conjunction: not the first holder on a point, not reserved for an own point when surplus protection is active, sufficient hit count, sufficient energy reserve, and no armed visible enemy in the configured safety distance. Training omits the splash-estimator branch. No production helper or analysis module was imported or executed.", "",
              "Every output key/order, archived evaluation answer, SAP argument, event-time unit context, normalized full configuration, all five before/after state hashes, native-action digest, report field and artifact hash was compared with the original evidence. Both 303-row traces (300 decisions each) are complete; no missing, duplicate or surplus helper events were found.", "",
              f"Historical run source: `{report['historical_run_head']}`. Original trace source: `{report['historical_trace_head']}`. Audit HEAD: `{report['current_audit_head']}`. The {len(report['historical_source_bindings'])} run-source bindings and {len(report['original_trace_source_bindings'])} original trace-source bindings were checked against their historical Git blobs or external runtime bytes, not by equating the closed run with the later HEAD.", "",
              f"All {len(report['file_sha256_before'])} monitored local files stayed byte-identical during this audit, including both V14 weights and Gruppe15.zip. No games, models, forward passes, learning updates, pytest, commits or pushes were executed.", "",
              "Limits:", ""]
    lines.extend(f"- {item}" for item in report["limitations"])
    lines += ["", "Reproduce (from repository root, with the existing NumPy environment):", "",
              "```text", f"{report['python']} -B experiments/analysis/artillery_training_exposure_20261108/operations/independent_data_audit.py", "```", "",
              "The adjacent JSON records every event's independently derived gates and the complete before/after hash inventory.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    try:
        result = audit()
    except Exception as exc:
        result = {"status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}",
                  "checks": dict(CHECKS), "checks_total": sum(CHECKS.values()),
                  "generated_at_utc": datetime.now(timezone.utc).isoformat()}
    (HERE / "independent_data_audit.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    (HERE / "independent_data_audit.md").write_text(markdown(result))
    print(json.dumps({k: result[k] for k in ("status", "checks_total", "event_count", "verdict_combinations", "error") if k in result}))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
