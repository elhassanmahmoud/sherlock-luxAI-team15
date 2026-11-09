"""Accepted 36+2 ensembles, loader check, then separate fixed 200-game screen."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import sys
import time

from scripts.early_curriculum_study import digest, hashes, require, source_identity
from scripts.final_training_supervisor import safe_path
from scripts.threat_warmstart import V14_SHA, ZIP_SHA
from scripts.threat_warmstart_compare import bound, read_bound, write, state_equal

ROOT = Path(__file__).resolve().parents[1]
PROFILE = "match_weight_compare_20261109"
ROLES = ("v14", "control", "match")
JOBS = ("v14_solution", "control_solution", "match_solution", "match_v14", "match_control")
COHORTS = {"solution": list(range(9970000, 9970020)),
           "direct_v14": list(range(9970100, 9970120)),
           "direct_control": list(range(9970200, 9970220))}


def output_dir(a):
    out = safe_path(a["out"])
    require(out.parent == ROOT/"experiments/analysis"/PROFILE and out.name == a["stage"]+"_v1",
            "Wrong exclusive phase output")
    require(all(out != Path(p) and out not in Path(p).parents for p in a["inputs"]), "Output overlaps input")
    return out


def fixed_cohorts(a):
    require(set(a["cohorts"]) == set(COHORTS), "Exactly three fixed cohorts required")
    cohorts = {k: read_bound(a, p) for k, p in a["cohorts"].items()}
    require(cohorts == COHORTS and all(type(s) is int for seeds in cohorts.values() for s in seeds),
            "Cards differ from fixed plan")
    proof = read_bound(a, a["seed_acceptance"])
    require(proof.get("status") == "PASS" and proof.get("profile") == PROFILE
            and proof.get("cohorts") == cohorts and proof.get("no_observed_conflicts") is True
            and bool(proof.get("limitations")) and bool(proof.get("files")), "Missing fixed-card acceptance")
    for path, sha in proof["files"].items(): require(digest(bound(a, path)) == sha, "Seed evidence changed")
    return cohorts


def accepted_training(a):
    """Consume a closed historical receipt; never re-admit old source against current HEAD.

    The sealed Root completion JSON binds both original owner states, admissions
    and all four accepted final receipts from the completed training.
    """
    closure = read_bound(a, a["training_completion"])
    require(closure.get("profile") == "match_weight_20261109"
            and closure.get("status") == "COMPLETE_TRAINING_NO_STRENGTH_CLAIM"
            and closure.get("source_and_input_bindings_valid") is True
            and closure.get("protected") == a["protected"]
            and closure.get("actual") == dict(technical_games=4, prefill_games=160,
                                               learning_games=1600, optimizer_updates=240000)
            and set(closure["pairs"]) == {"48", "49"}, "Both training starts must be accepted")
    finals = {r: [] for r in ("control", "match")}
    for start in (48, 49):
        entry = closure["pairs"][str(start)]
        train_path = bound(a, entry["admission"]); train_sha = digest(train_path)
        train = json.loads(train_path.read_text())
        owner_path = bound(a, entry["state"]); owner = json.loads(owner_path.read_text())
        require(train_sha == entry["admission_sha256"] and digest(owner_path) == entry["state_sha256"]
                and train.get("profile") == "match_weight_20261109" and train.get("stage") == f"pair{start}"
                and train.get("start") == start and train.get("protected") == a["protected"]
                and owner_path == safe_path(Path(train["out"])/"state.json")
                and owner.get("profile") == train["profile"] and owner.get("stage") == train["stage"]
                and owner.get("start") == start and owner.get("status") == "complete" and not owner.get("active")
                and set(owner.get("jobs", {})) == {"control", "match"}
                and all(owner["jobs"][role].get("returncode") == 0 for role in ("control", "match"))
                and owner.get("source") == train["source"] and owner.get("admission_sha256") == train_sha
                and set(entry["models"]) == {"control", "match"}, "Historical pair binding differs")
        for role in ("control", "match"):
            record = entry["models"][role]
            final = bound(a, record["path"]); receipt_path = bound(a, record["receipt"])
            receipt = json.loads(receipt_path.read_text()); check = owner["final_checks"][role]
            require(final == safe_path(Path(train["out"])/role/"final.pth")
                    and receipt_path == final.parent/"receipt.json"
                    and digest(final) == record["sha256"]
                    and digest(receipt_path) == record["receipt_sha256"]
                    and owner["receipts"][role] == dict(path=str(receipt_path), sha256=digest(receipt_path))
                    and check == dict(status="PASS", role=role, start=start, games=440,
                                      learn_steps=60000, receipt_sha256=digest(receipt_path))
                    and receipt.get("status") == "complete" and receipt.get("profile") == train["profile"]
                    and receipt.get("stage") == train["stage"] and receipt.get("start") == start
                    and receipt.get("role") == role and receipt.get("source") == train["source"]
                    and receipt.get("admission_sha256") == train_sha and len(receipt["games"]) == 440
                    and receipt["files"].get(str(final)) == digest(final), "Accepted final binding differs")
            finals[role].append(dict(path=final, start=start, source=train["source"],
                                     identity=receipt["final_identity"], config=train["config"][role]))
    return finals


def admission(path, sha, stage):
    require(digest(path) == sha, "Admission digest differs")
    a = json.loads(Path(path).read_text())
    require(a.get("schema_version") == 1 and a.get("profile") == PROFILE and a.get("stage") == stage
            and stage in ("technical", "performance") and a.get("start_authorized") is True
            and a.get("allow_battery") is True, "Explicit separate phase admission required")
    require(safe_path(a["root"]) == ROOT == Path.cwd().resolve(), "Wrong checkout")
    require(source_identity(ROOT, a["python"], a["plans"]) == a["source"], "Comparison source differs")
    protected = {str(ROOT/f"agents/sherlock/weights/agent_p{i}.pth"): V14_SHA for i in (0, 1)}
    protected[str(ROOT/"Gruppe15.zip")] = ZIP_SHA
    require(a["protected"] == protected and hashes(protected) == protected
            and hashes(a["inputs"]) == a["inputs"], "Protected/input bytes differ")
    output_dir(a); accepted_training(a)
    require(digest(bound(a, a["v14_source"])) == V14_SHA, "Original V14 required")
    if stage == "performance":
        receipt = read_bound(a, a["technical_receipt"]); approval = read_bound(a, a["technical_acceptance"])
        check_technical(receipt)
        require(receipt.get("source") == a["source"]
                and receipt.get("training_completion_sha256") == digest(a["training_completion"])
                and approval.get("status") == "PASS" and approval.get("profile") == PROFILE
                and approval.get("source") == a["source"]
                and approval.get("technical_receipt_sha256") == digest(a["technical_receipt"]),
                "Separate Root loader/assembly acceptance required")
        require(set(a["models"]) == set(ROLES), "Exactly three eval copies required")
        for role in ROLES:
            model = bound(a, a["models"][role])
            require(str(model) == receipt["models"][role]["path"]
                    and digest(model) == receipt["models"][role]["sha256"], "Wrong eval copy")
        fixed_cohorts(a)
    return a


def inference_config(source):
    from agents.sherlock.config import AgentConfig
    cfg = AgentConfig.from_dict(source["cfg"]).to_dict()
    require(not cfg["threat_feats"] and not cfg["cand_stall_rescue"], "Unexpected original inference method")
    cfg["frozen"] = False
    return cfg


def mount(source, finals):
    """Original primary + original 35 extras + (start48, start49), no training config copy."""
    require(len(source["ensemble"]) == 35 and len(finals) in (0, 2), "Wrong member count")
    cp = copy.deepcopy(source); cp["cfg"] = inference_config(source)
    cp["ensemble"] = copy.deepcopy([*source["ensemble"], *(f["q"] for f in finals)])
    cp["ensemble_dims"] = [79]*len(cp["ensemble"])
    return cp


def validate_and_load(path, cp, expected):
    import torch
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.main import Agent_x
    from agents.sherlock.model import QNet, checkpoint_ensemble_dims
    require(cp["feature_dim"] == 79 and cp["n_actions"] == 6 and not cp.get("cnn_policy")
            and len(expected) in (36, 38) and checkpoint_ensemble_dims(cp, 79) == [79]*(len(expected)-1)
            and state_equal([cp["q"], *cp["ensemble"]], expected), "Assembly order/architecture differs")
    template = QNet(79, 6, hidden=cp["cfg"]["hidden"], dueling=cp["cfg"]["dueling"]).state_dict()
    for sd in [*expected, cp["target_q"]]:
        require(set(sd) == set(template) and all(isinstance(v, torch.Tensor) and v.shape == template[k].shape
                and v.dtype == template[k].dtype and torch.isfinite(v).all() for k,v in sd.items()),
                "Member keys/shape/dtype/finiteness differs")
    # Default config-loading path is the one used by par_eval and its self: opponent.
    agent = Agent_x("player_0", agent_path=str(path), train=False, seed=0)
    agent.set_to_eval_mode(); agent.autosave_on_terminate = False
    actual = [agent.q, *agent.extra_q]
    require(not agent.training and not agent.cfg.frozen and agent.cnn_policy is None
            and agent.cfg.to_dict() == AgentConfig.from_dict(cp["cfg"]).to_dict()
            and agent.feat_dim == 79 and len(actual) == len(expected)
            and state_equal(agent.target_q.state_dict(), cp["target_q"])
            and state_equal([m.state_dict() for m in actual], expected), "Actual stock loader fallback/difference")
    # Fixed synthetic input, no real cards/replay selection, no action-strength conclusion.
    with torch.no_grad():
        x = torch.linspace(-1., 1., 16*79, device=agent.device).reshape(16, 79)
        for count in (1, 8, 16):
            q = torch.stack([m(x[:count]) for m in actual]).mean(0)
            require(q.shape == (count, 6) and torch.isfinite(q).all(), "Nonfinite actual 36/38 mean")
    return agent


def run_technical(a, path, sha, state_path):
    import torch
    from scripts.ensemble_diversity_train import _source
    from scripts.experiment import state_sha256
    check_owned(a, path, sha, state_path)
    finals = accepted_training(a)
    source, originals, _ = _source(bound(a, a["v14_source"]))
    models = {}; out = output_dir(a)
    for role in ROLES:
        check_owned(a, path, sha, state_path); additions = []
        for record in finals.get(role, []):
            f = torch.load(record["path"], map_location="cpu", weights_only=True)
            require(f.get("feature_dim") == 79 and f.get("n_actions") == 6 and not f.get("ensemble")
                    and f.get("cfg") == record["config"] and f.get("env_steps") == 193320
                    and f.get("learn_steps") == 60000
                    and state_sha256(f["q"]) == record["identity"]["q"]
                    and f.get("match_weight") == dict(profile="match_weight_20261109", status="complete",
                        role=role, start=record["start"], source=record["source"], completed_games=440, component_index=18),
                    "Not the accepted final single net")
            additions.append(f)
        cp = mount(source, additions); model_path = safe_path(out/(role+".pth"))
        require(not model_path.exists() and cp["cfg"] == inference_config(source), "Eval copy/config differs")
        with model_path.open("xb") as handle: torch.save(cp, handle)
        saved = torch.load(model_path, map_location="cpu", weights_only=True)
        expected = [*originals, *(f["q"] for f in additions)]
        require(saved["cfg"] == inference_config(source) and state_equal(saved["target_q"], source["target_q"]),
                "Saved original inference config/target changed")
        agent = validate_and_load(model_path, saved, expected)
        models[role] = dict(path=str(model_path), sha256=digest(model_path), members=len(expected),
            member_sha256=[state_sha256(sd) for sd in expected], loader_pass=True, batches=[1,8,16])
        del agent, cp, saved, additions
    check_owned(a, path, sha, state_path)
    receipt = dict(status="complete", profile=PROFILE, source=a["source"], admission_sha256=sha,
        training_completion_sha256=digest(a["training_completion"]), command=technical_command(a,path,sha),
        models=models, games=0, no_strength_claim=True)
    check_technical(receipt); write(out/"technical-receipt.json", receipt)


def check_technical(receipt):
    require(receipt.get("status") == "complete" and receipt.get("profile") == PROFILE
            and receipt.get("games") == 0 and receipt.get("no_strength_claim") is True
            and set(receipt["models"]) == set(ROLES), "Incomplete assembly/loader check")
    for role in ROLES:
        model = receipt["models"][role]; count = 36 if role == "v14" else 38
        require(model["members"] == count and len(model["member_sha256"]) == count
                and model["loader_pass"] is True and model["batches"] == [1,8,16], "Actual loader check missing")
        require(model["member_sha256"][:36] == receipt["models"]["v14"]["member_sha256"], "Original member order changed")


def technical_command(a, path, sha):
    return [a["python"], "-B", "-m", "scripts.match_weight_compare", "technical",
            "--admission", str(path), "--admission-sha", sha, "--owner-state", str(output_dir(a)/"state.json")]


def check_owned(a, path, sha, state_path):
    # spawn_owned publishes the exact PID record just after starting its child.
    deadline = time.monotonic()+5
    while True:
        state = json.loads(Path(state_path).read_text())
        job = state.get("jobs", {}).get("technical", {})
        if job or time.monotonic() >= deadline: break
        time.sleep(.05)
    command = technical_command(a, path, sha)
    actual = getattr(sys, "orig_argv", [])
    require(state.get("status") == "running" and state.get("profile") == PROFILE
            and state.get("active") == ["technical"] and state.get("admission_sha256") == sha
            and state.get("owner_pid") == job.get("owner_pid") == os.getppid() > 1
            and job.get("pid") == job.get("pgid") == os.getpid() == os.getpgrp()
            and job.get("argv") == command and actual[1:] == command[1:]
            and sys.executable == a["python"] and digest(path) == sha,
            "Technical worker lacks exact live ownership")
    require(all(state.get(k) == a[k] for k in ("root", "out", "source", "inputs", "protected",
            "stop_file", "allow_battery", "python", "plans")), "Owner/input binding differs")
    from scripts.fog_reward_supervisor import guard
    guard(state, {}, allow_battery=True)



def job_spec(a, name):
    require(name in JOBS, "Unknown fixed job")
    role, suffix = name.split("_", 1)
    cohort = "solution" if suffix == "solution" else "direct_"+suffix
    opponent = "solution92" if suffix == "solution" else "self:"+a["models"][suffix]
    return dict(role=role, cohort=cohort, opponent=opponent, csv=str(output_dir(a)/(name+".csv")))


def performance_command(a, name):
    spec = job_spec(a, name)
    return [a["python"], "-B", "-m", "scripts.par_eval", "--weights", a["models"][spec["role"]],
            "--seed-list", a["cohorts"][spec["cohort"]], "--workers", "1",
            "--opponents", spec["opponent"], "--out", spec["csv"]]


def validate_csv(a, name):
    import numpy as np
    import pandas as pd
    from scripts.compare_report import validated_results
    spec = job_spec(a, name); df = pd.read_csv(spec["csv"])
    checked = validated_results(df, name)
    seeds = read_bound(a, a["cohorts"][spec["cohort"]])
    expected = {(spec["opponent"], s, side) for s in seeds for side in ("player_0","player_1")}
    require(len(df) == 40 and set(checked[["opponent","seed","side"]].itertuples(index=False,name=None)) == expected,
            "Wrong/missing fixed games")
    for key in ("steps","point_counting_version","our_points","opp_points","our_wins","opp_wins","game_win"):
        values = pd.to_numeric(df[key], errors="raise")
        require(np.isfinite(values).all() and (values >= 0).all() and (values == np.floor(values)).all(),
                "Invalid integer game metric")
    require(df["steps"].eq(303).all() and df["point_counting_version"].eq(2).all()
            and (df["our_wins"]+df["opp_wins"] <= 3).all()
            and np.array_equal(df["result"], np.where(df["our_wins"] > df["opp_wins"],1.,
                np.where(df["our_wins"] == df["opp_wins"],.5,0.)))
            and np.array_equal(df["game_win"], df["result"].eq(1).astype(int))
            and np.array_equal(df["point_win"], np.where(df["our_points"] > df["opp_points"],1.,
                np.where(df["our_points"] == df["opp_points"],.5,0.))), "Incomplete/inconsistent result")
    return df


def analyze(a):
    from scripts.compare_report import compare_results
    from scripts.league_gates import direct_result
    frames = {name: validate_csv(a,name) for name in JOBS}
    counts = {name: dict(wins=int(df.result.eq(1).sum()), draws=int(df.result.eq(.5).sum()),
                        losses=int(df.result.eq(0).sum())) for name,df in frames.items()}
    w = {k:v["wins"] for k,v in counts.items()}
    gates = dict(solution_v14=w["match_solution"] >= w["v14_solution"],
                 solution_control=w["match_solution"] >= w["control_solution"],
                 direct_v14=w["match_v14"] >= 24, direct_control=w["match_control"] >= 24)
    return dict(profile=PROFILE, games=200, counts=counts, gates=gates, nominated=all(gates.values()),
        solution={role:compare_results(frames["match_solution"],frames[role+"_solution"])
                  for role in ("v14","control")},
        direct={role:direct_result(frames["match_"+role],job_spec(a,"match_"+role)["opponent"])
                for role in ("v14","control")},
        files={job_spec(a,n)["csv"]:digest(job_spec(a,n)["csv"]) for n in JOBS},
        interpretation="5000 whole-map bootstrap draws, descriptive score intervals (draw=0.5); "
                       "gates count actual wins. Two fixed training starts, repeated project selection, "
                       "no multiplicity correction. Nomination only, no promotion or extra games.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("technical",))
    p.add_argument("--admission", type=Path, required=True); p.add_argument("--admission-sha", required=True)
    p.add_argument("--owner-state", type=Path, required=True)
    args = p.parse_args()
    a = admission(args.admission,args.admission_sha,"technical")
    run_technical(a,args.admission.resolve(),args.admission_sha,args.owner_state.resolve())


if __name__ == "__main__": main()
