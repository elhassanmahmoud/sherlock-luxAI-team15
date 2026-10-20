"""Read-only pilot audit; writes two new reports only after every check succeeds.

Run AFTER pilot completion and AFTER all heavy work has stopped:
  .venv/bin/python -B /tmp/sherlock-reward-pilot-analysis-20261020.py \
      --run --confirm-no-heavy-work

No training, evaluation games, source edits or checkpoint writes. The archived
pilot wrapper is imported only inside main(), after the completion gate. It
imports stdlib only; Torch is imported lazily for final CPU tensor validation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15")
ANALYSIS = ROOT / "experiments/analysis/autonomous_20261020"
WRAPPER = ANALYSIS / "tools/reward_pilot.py"
STATE = ANALYSIS / "reward_pilot_state.json"
PLAN = ROOT / "docs/superpowers/plans/2026-10-20-paired-reward-replication.md"
PLAN_SHA = "77b70d41e6a56df688a7478fad2fb7b24c9315c77c605749437ffaf01f2eb369"
JSON_OUT = ANALYSIS / "reward_pilot_analysis.json"
MD_OUT = ANALYSIS / "reward_pilot_analysis.md"
JOBS = ("preflight", "train_control", "checkpoint_control",
        "train_fix", "checkpoint_fix", "eval_control", "eval_fix")
OPPONENTS = ("default", "solution92")
SEEDS = tuple(range(500720, 500780))
SIDES = ("player_0", "player_1")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def check_preflight(wrapper, state):
    preflight = read_json(wrapper.PREFLIGHT)
    require(preflight == state["preflight"], "State/preflight file mismatch")
    require(preflight["seed"] == 46 and preflight["agent_seed"] == 4600,
            "Unexpected initialization seeds")
    left, right = (preflight["arms"][arm] for arm in ("control", "fix"))
    require(set(preflight["arms"]) == {"control", "fix"}, "Unexpected arms")
    for arm, item in preflight["arms"].items():
        cfg = item["config"]
        require(item["q_sha256"] == item["target_q_sha256"],
                f"{arm}: initial q/target mismatch")
        require(item["env_steps"] == item["learn_steps"] == 0,
                f"{arm}: initial learner is not fresh")
        require(cfg["terminal_death_potential"] is (arm == "fix"),
                f"{arm}: wrong reward flag")
        require(all(cfg.get(key, False) is False
                    for key in ("active_targets", "sap_geometry")),
                f"{arm}: unrelated inference feature enabled")
        require(all(cfg.get(key) is True
                    for key in ("reward_fix", "use_shaping", "canonical")),
                f"{arm}: required baseline option missing")
    changed = {k for k in left["config"].keys() | right["config"].keys()
               if left["config"].get(k) != right["config"].get(k)}
    require(changed == {"terminal_death_potential"},
            f"Unexpected config differences: {changed}")
    require(left["q_sha256"] == right["q_sha256"]
            and left["rng_state"] == right["rng_state"],
            "Arms did not start from identical tensors/agent RNG")
    return preflight


def validate_losses(rows, arm):
    previous_env = previous_learn = 0
    nan_games = []
    finite_losses = []
    for game, row in enumerate(rows):
        env_steps, learn_steps = int(row["env_steps"]), int(row["learn_steps"])
        loss = float(row["mean_loss"])
        require(env_steps > previous_env and learn_steps >= previous_learn,
                f"{arm}: counters not monotone at game {game}")
        require(env_steps == 303 * (game + 1),
                f"{arm}: unexpected environment step counter")
        if math.isnan(loss):
            require(learn_steps == 0, f"{arm}: NaN loss after learning at game {game}")
            nan_games.append(game)
        else:
            require(math.isfinite(loss), f"{arm}: non-finite loss at game {game}")
            finite_losses.append(loss)
        previous_env, previous_learn = env_steps, learn_steps
    require(previous_learn > 0 and math.isfinite(float(rows[-1]["mean_loss"])),
            f"{arm}: final loss must be finite after actual learning")
    return {"nan_before_learning_games": nan_games,
            "final_mean_loss": float(rows[-1]["mean_loss"]),
            "max_finite_mean_loss": max(finite_losses),
            "env_steps": previous_env, "learn_steps": previous_learn,
            "interpretation": "Numerical diagnostic only; loss is not a strength measure."}


def validate_tensors(wrapper, state):
    # This import is intentionally after complete-state/source/CSV checks.
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[key] = "1"
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    records = {}
    for arm, spec in wrapper.ARMS.items():
        path = spec["run"] / "weights/agent.pth"
        final = state["arms"][arm]["training"]["final"]
        require(sha(path) == final["file_sha256"], f"{arm}: checkpoint changed")
        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        require(checkpoint["cfg"] == final["config"], f"{arm}: checkpoint config mismatch")
        require(not checkpoint.get("ensemble"), f"{arm}: unexpected ensemble")
        for key in ("env_steps", "learn_steps"):
            require(checkpoint[key] == final[key] and checkpoint[key] > 0,
                    f"{arm}: checkpoint {key} mismatch")
        counts = {}
        require(set(checkpoint["q"]) == set(checkpoint["target_q"]),
                f"{arm}: q/target tensor names differ")
        for network in ("q", "target_q"):
            tensors = checkpoint[network]
            require(bool(tensors), f"{arm}: empty {network}")
            count = 0
            for name, tensor in tensors.items():
                require(isinstance(tensor, torch.Tensor)
                        and bool(torch.isfinite(tensor).all().item()),
                        f"{arm}: invalid/non-finite {network}.{name}")
                peer = checkpoint["target_q" if network == "q" else "q"][name]
                require(tensor.shape == peer.shape and tensor.dtype == peer.dtype,
                        f"{arm}: q/target shape or dtype mismatch for {name}")
                count += tensor.numel()
            require(wrapper.tensor_hash(tensors) == final[f"{network}_sha256"],
                    f"{arm}: {network} tensor identity differs from final record")
            counts[network] = {"tensor_count": len(tensors), "elements": count, "finite": True}
        require(sha(path) == final["file_sha256"], f"{arm}: checkpoint changed during audit")
        records[arm] = counts
        del checkpoint
    return records


def comparisons(eval_rows):
    import numpy as np
    keyed = {
        arm: {(int(r["seed"]), r["side"], r["opponent"]): r for r in rows}
        for arm, rows in eval_rows.items()
    }
    results = {}
    metrics = {
        "result": lambda r: float(r["result"]),
        "match_win_margin": lambda r: float(r["our_wins"]) - float(r["opp_wins"]),
        "point_margin": lambda r: float(r["our_points"]) - float(r["opp_points"]),
    }
    for opponent in OPPONENTS:
        results[opponent] = {}
        for metric, get in metrics.items():
            values = {}
            for arm in ("control", "fix"):
                values[arm] = np.array([
                    sum(get(keyed[arm][seed, side, opponent]) for side in SIDES) / 2
                    for seed in SEEDS
                ], dtype=np.float64)
            delta = values["fix"] - values["control"]
            require(bool(np.isfinite(delta).all()), f"{opponent}/{metric}: non-finite comparison")
            # Same algorithm as compare_report: each draw is an entire map,
            # already averaged over its two sides. Reset seed per comparison.
            rng = np.random.default_rng(0)
            bootstrap = rng.choice(delta, size=(5000, len(SEEDS)), replace=True).mean(axis=1)
            low, high = map(float, np.percentile(bootstrap, [2.5, 97.5]))
            results[opponent][metric] = {
                "role": "primary" if metric == "result" else "diagnostic_only",
                "maps": 60, "games_per_arm": 120,
                "control_mean": float(values["control"].mean()),
                "fix_mean": float(values["fix"].mean()),
                "delta_fix_minus_control": float(delta.mean()),
                "paired_map_bootstrap_95": [low, high],
                "bootstrap_samples": 5000, "bootstrap_seed": 0,
            }
            if metric == "result":
                results[opponent][metric]["delta_half_result_units"] = sum(
                    int(2 * float(keyed["fix"][seed, side, opponent]["result"]))
                    - int(2 * float(keyed["control"][seed, side, opponent]["result"]))
                    for seed in SEEDS for side in SIDES
                )
    return results


def continuation_gate(results):
    sol, default = results["solution92"]["result"], results["default"]["result"]
    reasons = []
    # Exact integer arithmetic at the -5/-2 percentage-point boundaries:
    # 120 games/arm, result increments 0.5, hence a denominator of 240.
    if sol["delta_half_result_units"] * 100 <= -5 * 240 and sol["paired_map_bootstrap_95"][1] < 0:
        reasons.append("solution92_delta_at_most_minus_5pp_and_upper95_below_zero")
    if default["delta_half_result_units"] * 100 < -2 * 240:
        reasons.append("default_observed_delta_below_minus_2pp")
    return {
        "decision": "stop_and_investigate" if reasons else "eligible_for_replication",
        "reasons": reasons,
        "automatic_training_authorization": False,
        "method_strength_claim": False,
        "independent_initializations": 1,
        "run_seed": 46,
        "scope": "One paired initialization, 400 games/arm, reused development maps only.",
        "plan_sha256": PLAN_SHA,
    }


def markdown(report):
    lines = [
        "# Paired reward pilot — seed 46",
        "",
        "Technical audit passed: 400 training games and 240 evaluation games per arm; "
        "source/protected-weight identity, equal fresh initialization, final checkpoint "
        "records and finite learned q/target tensors verified.",
        "",
        "| Opponent | Control result | Fix result | Fix − control | 95% paired-map interval |",
        "|---|---:|---:|---:|---:|",
    ]
    for opponent in OPPONENTS:
        row = report["comparisons"][opponent]["result"]
        lo, hi = row["paired_map_bootstrap_95"]
        lines.append(f"| {opponent} | {row['control_mean']:.2%} | {row['fix_mean']:.2%} | "
                     f"{100*row['delta_fix_minus_control']:+.2f} pp | "
                     f"[{100*lo:+.2f}, {100*hi:+.2f}] pp |")
    lines += [
        "",
        "`result` counts a draw as 0.5. Each opponent has 60 maps × both sides. "
        "Intervals resample whole maps 5,000 times, RNG seed 0.",
        "",
        f"**Continuation gate: {report['gate']['decision']}.**",
        "Reasons: " + (", ".join(report["gate"]["reasons"]) or "Neither predefined harm threshold met."),
        "",
        "Eligibility authorizes no automatic job and proves no benefit. This is exactly "
        "one paired initialization (seed 46), not evidence of average reward-method "
        "performance across initializations. Maps are reused development maps. "
        "Card intervals do not measure training-seed variability.",
        "",
        "Diagnostic differences (fix minus control; excluded from the continuation gate):",
        "",
        "| Opponent | Match-win margin/game | Point margin/game |",
        "|---|---:|---:|",
    ]
    for opponent in OPPONENTS:
        rows = report["comparisons"][opponent]
        lines.append(f"| {opponent} | "
                     f"{rows['match_win_margin']['delta_fix_minus_control']:+.3f} | "
                     f"{rows['point_margin']['delta_fix_minus_control']:+.3f} |")
    lines += [
        "",
        "The 400-game curriculum has 100 default-only games; fresh 3,000-game runs "
        "have 750. Pilot performance therefore need not predict the longer curriculum. "
        "Training loss is a numerical diagnostic, not a strength measure.",
        "",
        f"Prespecified continuation plan SHA-256: `{PLAN_SHA}`.",
        f"Source HEAD: `{report['source_head']}`.",
        "Exact source/input/checkpoint hashes and diagnostic intervals are in the JSON report.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", required=True)
    parser.add_argument("--confirm-no-heavy-work", action="store_true", required=True)
    parser.parse_args()
    require(not JSON_OUT.exists() and not MD_OUT.exists(), "Refusing existing report output")
    state_sha = sha(STATE)
    state = read_json(STATE)
    require(state.get("complete") is True and state.get("status") == "complete"
            and state.get("final_integrity_ok") is True, "Pilot is not completely validated")
    require(not state.get("error") and not state.get("integrity_error"), "Pilot records an error")
    require([j["label"] for j in state["jobs"]] == list(JOBS), "Unexpected/missing pilot jobs")
    previous_end = None
    for job in state["jobs"]:
        require(job.get("complete") is True and job.get("returncode") == 0,
                f"Incomplete/failed job: {job['label']}")
        start, end = (datetime.fromisoformat(job[k]) for k in ("started_at", "finished_at"))
        require(end >= start and (previous_end is None or start >= previous_end),
                "Pilot jobs overlap or have invalid timestamps")
        previous_end = end
    require(sha(PLAN) == PLAN_SHA, "Prespecified continuation plan changed")
    require(sha(WRAPPER) == state["baseline"]["code"]["python_sources"][str(WRAPPER)],
            "Archived pilot wrapper changed")
    module_spec = importlib.util.spec_from_file_location("audited_pilot_wrapper", WRAPPER)
    wrapper = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(wrapper)
    require(wrapper.source_identity() == state["baseline"]["code"],
            "Source HEAD/Python/source hashes changed since pilot")
    require(wrapper.protected_hashes() == state["baseline"]["protected"],
            "Protected release/candidate/rollback files changed")
    preflight = check_preflight(wrapper, state)
    audits, eval_rows, input_hashes = {}, {}, {
        str(STATE): state_sha, str(wrapper.PREFLIGHT): sha(wrapper.PREFLIGHT),
        str(PLAN): PLAN_SHA, str(WRAPPER): sha(WRAPPER),
        str(Path(__file__).resolve()): sha(Path(__file__).resolve()),
    }
    require(set(state["arms"]) == {"control", "fix"}, "Unexpected state arms")
    for arm, spec in wrapper.ARMS.items():
        record = state["arms"][arm]
        require(record["variant"] == spec["variant"] and record["run"] == str(spec["run"])
                and record["eval"] == str(spec["eval"])
                and record["experiment_argv"] == wrapper.experiment_args(arm),
                f"{arm}: path/variant/argument record mismatch")
        train = wrapper.validate_training(arm)
        evaluation = wrapper.validate_evaluation(arm)
        require(train == record["training"] and evaluation == record["evaluation"],
                f"{arm}: stored audit changed")
        manifest = read_json(spec["run"] / "manifest.json")
        require(manifest["git"]["commit"] == state["baseline"]["code"]["head"],
                f"{arm}: manifest source HEAD mismatch")
        # experiment.main(argv) records sys.argv, i.e. the wrapper child argv.
        # Its explicit experiment arguments are separately audited in state.
        require(manifest["argv"] == [str(WRAPPER), "--child", "train", "--arm", arm],
                f"{arm}: recorded training child argument mismatch")
        rows = read_csv(spec["run"] / "train.csv")
        losses = validate_losses(rows, arm)
        audits[arm] = {"training": train, "evaluation": evaluation,
                      "loss_checks": losses, "manifest_runtime_secs": manifest["runtime_secs"]}
        eval_rows[arm] = read_csv(spec["eval"])
        for path in [spec["eval"], *(spec["run"] / name for name in
                     ("manifest.json", "train.csv", "initial_identity.json", "final_identity.json"))]:
            input_hashes[str(path)] = sha(path)
    tensors = validate_tensors(wrapper, state)
    results = comparisons(eval_rows)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "technical_audit_passed": True,
        "source_head": state["baseline"]["code"]["head"],
        "source_identity": state["baseline"]["code"],
        "protected_hashes": state["baseline"]["protected"],
        "input_hashes": input_hashes,
        "initial_identity": preflight, "arm_audits": audits,
        "finite_tensor_audit": tensors, "comparisons": results,
        "gate": continuation_gate(results),
    }
    require(all(sha(path) == expected for path, expected in input_hashes.items()),
            "An analysis input changed during audit")
    require(wrapper.source_identity() == state["baseline"]["code"]
            and wrapper.protected_hashes() == state["baseline"]["protected"],
            "Final source/protected-weight identity changed")
    encoded = json.dumps(report, indent=2, allow_nan=False) + "\n"
    text = markdown(report)
    # Exclusive files only: never update the wrapper's state or an existing report.
    with JSON_OUT.open("x", encoding="utf-8") as stream:
        stream.write(encoded)
    with MD_OUT.open("x", encoding="utf-8") as stream:
        stream.write(text)
    print(report["gate"]["decision"])
    print(JSON_OUT)
    print(MD_OUT)


if __name__ == "__main__":
    main()
