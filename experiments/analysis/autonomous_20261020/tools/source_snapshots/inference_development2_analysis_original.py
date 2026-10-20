"""Analyze the complete, frozen three-CSV inference development experiment.

Run from any directory after its state is complete:
  .venv/bin/python -B /tmp/sherlock-inference-development2-analysis-20261020.py --run

No model imports, jobs, promotion, or checkpoint writes. --self-test uses only
stdlib and synthetic data. NumPy is loaded only after real input validation.
Reports use exclusive creation under experiments/analysis/autonomous_20261020.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15")
OUT = ROOT / "experiments/compare/autonomous_20261020/inference_development2"
ANALYSIS = ROOT / "experiments/analysis/autonomous_20261020"
JSON_OUT = ANALYSIS / "inference_development2_analysis.json"
MD_OUT = ANALYSIS / "inference_development2_analysis.md"
REFERENCE = ROOT / "experiments/compare/autonomous_20261020/dev_reference.csv"
WEIGHTS = ROOT / "experiments/candidates/all18_v3.pth"
V3_SHA = "aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935"
LABELS = ("reference", "active", "sap")
SEEDS = tuple(range(500720, 500780))
SIDES = ("player_0", "player_1")
OPPONENTS = ("default", "solution92")
OVERRIDES = {
    "reference": ["active_targets=false", "sap_geometry=false"],
    "active": ["active_targets=true", "sap_geometry=false"],
    "sap": ["active_targets=false", "sap_geometry=true"],
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_csv(text):
    reader = csv.DictReader(io.StringIO(text))
    fields = reader.fieldnames
    require(fields is not None and len(fields) == len(set(fields)), "Missing/duplicate columns")
    required = {"seed", "side", "opponent", "result", "our_wins", "opp_wins",
                "our_points", "opp_points", "steps", "point_counting_version"}
    require(required <= set(fields), "Required columns missing")
    indexed = {}
    for row in reader:
        require(None not in row and all(v is not None for v in row.values()), "Malformed CSV row")
        key = tuple(row[k] for k in ("seed", "side", "opponent"))
        require(key not in indexed, f"Duplicate key: {key}")
        require(row["steps"] == "303" and row["point_counting_version"] == "2",
                "Incomplete game or wrong scoring version")
        for key_name, value in row.items():
            if key_name not in ("side", "opponent"):
                require(math.isfinite(float(value)), f"Nonfinite field: {key_name}")
        own, opp = float(row["our_wins"]), float(row["opp_wins"])
        require(own.is_integer() and opp.is_integer() and 0 <= own <= 3
                and 0 <= opp <= 3 and own + opp <= 3, "Invalid match totals")
        require(float(row["result"]) == (1 if own > opp else 0 if own < opp else .5),
                "Result inconsistent with match totals")
        require(float(row["our_points"]) >= 0 and float(row["opp_points"]) >= 0,
                "Negative point total")
        indexed[key] = row
    expected = {(str(seed), side, opp) for seed in SEEDS for side in SIDES for opp in OPPONENTS}
    require(len(indexed) == 240 and set(indexed) == expected, "Expected exact 240 development keys")
    return fields, indexed


def compare(indexed):
    import numpy as np
    comparisons = {}
    for candidate in ("active", "sap"):
        comparisons[candidate] = {}
        for opponent in OPPONENTS:
            values = {}
            for label in ("reference", candidate):
                values[label] = np.array([
                    sum(float(indexed[label][str(seed), side, opponent]["result"])
                        for side in SIDES) / 2
                    for seed in SEEDS
                ], dtype=np.float64)
            differences = values[candidate] - values["reference"]
            rng = np.random.default_rng(0)
            sampled = rng.choice(differences, size=(5000, 60), replace=True).mean(axis=1)
            low, high = map(float, np.percentile(sampled, [2.5, 97.5]))
            units = sum(
                int(2 * float(indexed[candidate][str(seed), side, opponent]["result"]))
                - int(2 * float(indexed["reference"][str(seed), side, opponent]["result"]))
                for seed in SEEDS for side in SIDES
            )
            comparisons[candidate][opponent] = {
                "reference_mean_result": float(values["reference"].mean()),
                "candidate_mean_result": float(values[candidate].mean()),
                "delta": float(differences.mean()),
                "delta_half_result_units": units, "half_result_denominator": 240,
                "paired_map_bootstrap_95": [low, high],
                "maps": 60, "games_per_configuration": 120,
                "bootstrap_samples": 5000, "bootstrap_seed": 0,
            }
    return comparisons


def select(comparisons):
    eligible = []
    detail = {}
    for candidate in ("active", "sap"):
        sol, default = comparisons[candidate]["solution92"], comparisons[candidate]["default"]
        tests = {
            "solution92_delta_positive": sol["delta_half_result_units"] > 0,
            "solution92_lower95_positive": sol["paired_map_bootstrap_95"][0] > 0,
            # Exact boundary: default delta >= -0.02; 120 games, half results.
            "default_loss_at_most_2pp": default["delta_half_result_units"] * 100 >= -2 * 240,
        }
        detail[candidate] = {"checks": tests, "eligible": all(tests.values())}
        if all(tests.values()):
            eligible.append(candidate)
    selected, reason = None, "no_eligible_candidate"
    if len(eligible) == 1:
        selected, reason = eligible[0], "one_eligible_candidate"
    elif len(eligible) == 2:
        active_delta = comparisons["active"]["solution92"]["delta_half_result_units"]
        sap_delta = comparisons["sap"]["solution92"]["delta_half_result_units"]
        if active_delta == sap_delta:
            reason = "equal_solution92_delta_no_selection"
        else:
            selected = "active" if active_delta > sap_delta else "sap"
            reason = "higher_solution92_delta_among_two_eligible_candidates"
    return {
        "checks": detail, "eligible": eligible,
        "selected_for_fresh_confirmation": selected, "reason": reason,
        "promotion_authorized": False, "job_started": False,
        "rule": "Solution92 delta > 0 and lower95 > 0; default delta >= -0.02. "
                "If two qualify, larger Solution92 delta; exact tie selects none.",
        "scope": "Development selection only; repeated maps and two candidate comparisons. "
                 "Unadjusted map intervals are not a fresh confirmation or promotion proof.",
    }


def validated_inputs():
    state_path = OUT / "state.json"
    hashes = {str(state_path): sha(state_path)}
    state = json.loads(state_path.read_text())
    require(state.get("status") == "complete" and state.get("complete") is True
            and not state.get("error"), "Experiment not complete")
    require(state["final_identity"] == state["baseline"], "Final frozen identity mismatch")
    baseline = state["baseline"]
    require(baseline["protected_sha256"][str(WEIGHTS)] == V3_SHA, "Wrong V3 baseline")
    require(state["reference"] == str(REFERENCE), "Wrong previous reference")
    require([j["label"] for j in state["jobs"]] == list(LABELS), "Missing/extra/reordered jobs")
    tables, fields, previous_end = {}, {}, None
    for job in state["jobs"]:
        label = job["label"]
        path = OUT / f"phase2_{label}.csv"
        require(job.get("complete") is True and job.get("returncode") == 0
                and job.get("rows") == 240 and job.get("exact_keys_valid") is True,
                f"{label}: incomplete/invalid job")
        require(job["output"] == str(path) and sha(path) == job["csv_sha256"],
                f"{label}: CSV path/hash mismatch")
        start, end = (datetime.fromisoformat(job[k]) for k in ("started_at", "finished_at"))
        require(end >= start and (previous_end is None or start >= previous_end),
                "Invalid/overlapping evaluation timing")
        previous_end = end
        expected = [str(ROOT / ".venv/bin/python"), "-B", "-m", "scripts.par_eval",
                    "--weights", str(WEIGHTS), "--first", "720", "--n", "60",
                    "--workers", "2", "--opponents", "default,solution92", "--out", str(path)]
        for setting in OVERRIDES[label]:
            expected += ["--set", setting]
        require(job["command"] == expected, f"{label}: unexpected evaluation command/config")
        fields[label], tables[label] = parse_csv(path.read_text())
        hashes[str(path)] = job["csv_sha256"]
    require(state["jobs"][0].get("baseline_non_time_exact") is True,
            "Reference reproduction not recorded")
    old_fields, old = parse_csv(REFERENCE.read_text())
    require(all(set(f) == set(old_fields) for f in fields.values()), "CSV schemas differ")
    for key, row in tables["reference"].items():
        require({k: v for k, v in row.items() if k != "secs"} ==
                {k: v for k, v in old[key].items() if k != "secs"},
                f"Previous baseline differs outside timing: {key}")
    # Read-only recheck of the recorded files; no code/model import is required.
    hashes.update(baseline["protected_sha256"])
    hashes.update(baseline["python_sources"])
    hashes[baseline["python_path"]] = baseline["python_sha256"]
    hashes[str(Path(__file__).resolve())] = sha(Path(__file__).resolve())
    require(all(sha(path) == expected for path, expected in hashes.items()),
            "A source, protected artifact or input changed")
    return state, tables, hashes


def markdown(report):
    lines = [
        "# Inference development comparison",
        "",
        "All three datasets passed the completion, exact-key, frozen-file and baseline "
        "reproduction checks. Scores are mean result; draws count as 0.5.",
        "",
        "| Candidate | Opponent | Reference | Candidate | Delta | 95% paired-map interval |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for candidate, opponents in report["comparisons"].items():
        for opponent, row in opponents.items():
            lo, hi = row["paired_map_bootstrap_95"]
            lines.append(f"| {candidate} | {opponent} | {row['reference_mean_result']:.2%} | "
                         f"{row['candidate_mean_result']:.2%} | {100*row['delta']:+.2f} pp | "
                         f"[{100*lo:+.2f}, {100*hi:+.2f}] pp |")
    decision = report["selection"]
    lines += [
        "",
        f"Selected for fresh confirmation: **{decision['selected_for_fresh_confirmation'] or 'none'}**.",
        f"Reason: `{decision['reason']}`.",
        "",
        decision["rule"],
        "",
        "Each comparison uses the same 60 maps on both sides, 5,000 whole-map bootstrap "
        "draws with RNG seed 0. The two candidate intervals are unadjusted. These reused "
        "development maps select a direction; they do not constitute fresh confirmation.",
        "",
        "No job or promotion is triggered. A selected candidate still needs the separately "
        "reserved fresh comparison and technical release checks.",
        "",
        f"Frozen experiment HEAD: `{report['source_head']}`.",
        "",
    ]
    return "\n".join(lines)


def self_test():
    import unittest

    class Fixtures(unittest.TestCase):
        def metrics(self, active=12, sap=18, active_low=.01, sap_low=.01,
                    active_default=0, sap_default=0):
            return {
                label: {
                    "solution92": {"delta_half_result_units": units,
                                   "paired_map_bootstrap_95": [low, .2]},
                    "default": {"delta_half_result_units": default},
                }
                for label, units, low, default in (
                    ("active", active, active_low, active_default),
                    ("sap", sap, sap_low, sap_default))
            }

        def test_selection_and_strict_boundaries(self):
            self.assertEqual(select(self.metrics())["selected_for_fresh_confirmation"], "sap")
            self.assertIsNone(select(self.metrics(sap=12))["selected_for_fresh_confirmation"])
            self.assertEqual(select(self.metrics(sap_low=0))["selected_for_fresh_confirmation"], "active")
            self.assertIsNone(select(self.metrics(active_low=0, sap_low=0))["selected_for_fresh_confirmation"])
            self.assertEqual(select(self.metrics(sap_default=-5))["selected_for_fresh_confirmation"], "active")
            self.assertEqual(select(self.metrics(sap_default=-4))["selected_for_fresh_confirmation"], "sap")
            self.assertIsNone(select(self.metrics(active=0, sap=0))["selected_for_fresh_confirmation"])
            self.assertIsNone(select(self.metrics(active=-1, sap=-1))["selected_for_fresh_confirmation"])

        def fixture_csv(self):
            text = io.StringIO()
            writer = csv.writer(text)
            writer.writerow(["seed", "side", "opponent", "result", "our_wins", "opp_wins",
                             "our_points", "opp_points", "steps", "point_counting_version"])
            for seed in SEEDS:
                for side in SIDES:
                    for opponent in OPPONENTS:
                        writer.writerow([seed, side, opponent, .5, 1, 1, 100, 100, 303, 2])
            return text.getvalue()

        def test_exact_keys_and_match_draws(self):
            text = self.fixture_csv()
            self.assertEqual(len(parse_csv(text)[1]), 240)
            lines = text.splitlines()
            for invalid in ("\n".join(lines[:-1]), text + lines[-1] + "\n",
                            text.replace("500720", "599999"),
                            text.replace(",303,2", ",302,2"),
                            text.replace(",0.5,1,1,", ",1,1,1,"),
                            text.replace(",100,100,", ",nan,100,"),
                            text.replace(",0.5,1,1,", ",0.5,2,2,")):
                with self.assertRaises((RuntimeError, ValueError)):
                    parse_csv(invalid)
            for original, replacement in ((",0.5,1,1,", ",0.5,0,0,"),
                                          (",0.5,1,1,", ",1,2,0,")):
                self.assertEqual(len(parse_csv(text.replace(original, replacement))[1]), 240)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Fixtures))
    if not result.wasSuccessful():
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    require(not JSON_OUT.exists() and not MD_OUT.exists(), "Refusing existing reports")
    state, tables, hashes = validated_inputs()
    results = compare(tables)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "technical_validation_passed": True, "source_head": state["baseline"]["head"],
        "input_sha256": hashes, "comparisons": results, "selection": select(results),
    }
    require(all(sha(path) == expected for path, expected in hashes.items()),
            "Input changed during analysis")
    encoded = json.dumps(report, indent=2, allow_nan=False) + "\n"
    text = markdown(report)
    with JSON_OUT.open("x", encoding="utf-8") as stream:
        stream.write(encoded)
    with MD_OUT.open("x", encoding="utf-8") as stream:
        stream.write(text)
    print(report["selection"]["selected_for_fresh_confirmation"] or "none")
    print(JSON_OUT)
    print(MD_OUT)


if __name__ == "__main__":
    main()
