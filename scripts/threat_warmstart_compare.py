"""One technical phase, then a separately admitted 200-game screen; no promotion."""
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

ROOT = Path(__file__).resolve().parents[1]
PROFILE = "threat_warmstart_compare_20261109"
ROLES = ("v14", "control", "threat")
JOBS = ("v14_solution", "control_solution", "threat_solution", "threat_v14", "threat_control")
TECH_KEYS = ((831006, "player_1"), (831000, "player_0"))
COHORTS = {"solution": list(range(9946000, 9946020)), "direct_v14": list(range(9946100, 9946120)),
           "direct_control": list(range(9946200, 9946220))}
FINAL_SHA = {"control": "bcb00242b1b73429c72deb556e5a74fb3386aab288bea02f21f538398af34994",
             "threat": "2acf88f8dedbb1eb060ff4ebc3a4b365dc022ef2d0bb8ecf41dfe60883819c93"}


def write(path, value):
    # Existing atomic, exclusive JSON publication; no second implementation.
    from scripts.threat_warmstart import write as publish
    publish(path, value)


def bound(a, path):
    path = safe_path(path)
    require(a["inputs"].get(str(path)) == digest(path), "Input unbound/changed")
    return path


def read_bound(a, path):
    return json.loads(bound(a, path).read_text())


def output_dir(a):
    out = safe_path(a["out"])
    require(out.parent == ROOT/"experiments/analysis"/PROFILE
            and out.name == a["stage"]+"_v1", "Wrong exclusive phase output")
    require(all(out != Path(p) and out not in Path(p).parents for p in a["inputs"]),
            "Output overlaps accepted input")
    return out


def fixed_cohorts(a):
    cohorts = {name: read_bound(a, a["cohorts"][name])
               for name in ("solution", "direct_v14", "direct_control")}
    require(set(a["cohorts"]) == set(cohorts), "Exactly three fixed cohorts required")
    require(cohorts == COHORTS, "Cards differ from the fixed comparison plan")
    seen = set()
    for values in cohorts.values():
        require(isinstance(values, list) and len(values) == 20
                and all(type(x) is int and x >= 0 for x in values)
                and len(set(values)) == 20 and not seen.intersection(values),
                "20 unique, mutually disjoint cards required")
        seen.update(values)
    from scripts.threat_warmstart import COHORTS as TRAINING_COHORTS
    old = {s for values in TRAINING_COHORTS.values() for s in values}
    old.update(key[0] for key in TECH_KEYS)
    require(not seen.intersection(old), "Training/prefill/technical card reused")
    acceptance = read_bound(a, a["seed_acceptance"])
    require(acceptance.get("status") == "PASS" and acceptance.get("profile") == PROFILE
            and acceptance.get("cohorts") == cohorts
            and acceptance.get("no_observed_conflicts") is True
            and bool(acceptance.get("limitations")) and bool(acceptance.get("files")),
            "Missing separate fixed-card acceptance")
    for p, h in acceptance["files"].items():
        require(digest(bound(a, p)) == h, "Seed evidence differs")
    return cohorts


def admission(path, sha, stage):
    require(digest(path) == sha, "Admission digest differs")
    a = json.loads(Path(path).read_text())
    require(a.get("schema_version") == 1 and a.get("profile") == PROFILE
            and a.get("stage") == stage and a.get("start_authorized") is True
            and a.get("allow_battery") is True, "Explicit phase admission required")
    require(safe_path(a["root"]) == ROOT == Path.cwd().resolve(), "Wrong checkout")
    require(source_identity(ROOT, a["python"], a["plans"]) == a["source"], "Comparison source differs")
    from scripts.threat_warmstart import V14_SHA, ZIP_SHA
    protected = {str(ROOT/f"agents/sherlock/weights/agent_p{i}.pth"): V14_SHA for i in (0, 1)}
    protected[str(ROOT/"Gruppe15.zip")] = ZIP_SHA
    require(a["protected"] == protected and hashes(protected) == protected
            and hashes(a["inputs"]) == a["inputs"], "Input/protected bytes differ")
    output_dir(a)
    if stage == "performance":
        technical = read_bound(a, a["technical_receipt"])
        approval = read_bound(a, a["technical_acceptance"])
        require(technical.get("status") == "complete" and technical.get("profile") == PROFILE
                and technical.get("source") == a["source"] and technical.get("stock_control_accepted") is True,
                "Technical phase must use the same comparison source")
        require(approval.get("status") == "PASS" and approval.get("profile") == PROFILE
                and approval.get("technical_receipt_sha256") == digest(a["technical_receipt"])
                and approval.get("source") == a["source"], "Separate Root technical acceptance required")
        check_technical(technical)
        require(set(a["models"]) == set(ROLES), "Exactly three admitted models")
        for role in ROLES:
            require(str(bound(a, a["models"][role])) == technical["models"][role]["path"]
                    and digest(a["models"][role]) == technical["models"][role]["sha256"], "Wrong eval copy")
        fixed_cohorts(a)
    return a


def state_equal(left, right):
    from scripts.experiment import state_sha256
    return state_sha256(left) == state_sha256(right)  # keys, shape, dtype and exact bytes


def validate_model(cp, source_cfg, role):
    import torch
    from agents.sherlock.model import QNet, checkpoint_ensemble_dims
    width = 79 if role == "v14" else 101
    expected_cfg = dict(source_cfg, frozen=False)
    if role != "v14": expected_cfg["threat_feats"] = True
    require(cp.get("feature_dim") == width and cp.get("n_actions") == 6
            and cp.get("cfg") == expected_cfg and not cp.get("cnn_policy"), "Inference config/architecture differs")
    require(not source_cfg.get("threat_feats") and source_cfg["use_sap"]
            and source_cfg["hidden"] == 256 and source_cfg["dueling"], "Unexpected V14 architecture")
    dims = checkpoint_ensemble_dims(cp, width)
    require(len(cp.get("ensemble", [])) == 35 and dims == [79]*35, "Exactly 36 members, extras all 79")
    templates = {dim: QNet(dim, 6, 256, True).state_dict() for dim in set([width, 79])}
    members = [cp["q"], *cp["ensemble"]]
    for state, dim in zip(members+[cp["target_q"]], [width]+dims+[width]):
        template = templates[dim]
        require(set(state) == set(template) and all(
            isinstance(v, torch.Tensor) and v.shape == template[k].shape
            and v.dtype == template[k].dtype and bool(torch.isfinite(v).all())
            for k, v in state.items()), "Member keys/shape/dtype/finiteness differ")
    if role != "v14":
        require(bool(torch.count_nonzero(cp["q"]["body.0.weight"][:, 79:])) == (role == "threat"),
                "Control zero-column/threat learned-column contrast missing")
    return members


def mount(source, final, role):
    """Pure in-memory assembly; final admission is a separate prerequisite."""
    source_cfg = source["cfg"]
    v14 = copy.deepcopy(source)
    v14["cfg"] = dict(source_cfg, frozen=False)
    originals = validate_model(v14, source_cfg, "v14")
    if role == "v14": return v14
    require(role in ("control", "threat") and final.get("feature_dim") == 101
            and final.get("n_actions") == 6 and not final.get("ensemble"), "Wrong final single model")
    cp = dict(q=copy.deepcopy(final["q"]), target_q=copy.deepcopy(final["q"]),
              ensemble=copy.deepcopy(originals[:18]+originals[19:]), ensemble_dims=[79]*35,
              feature_dim=101, n_actions=6, cfg=dict(source_cfg, threat_feats=True, frozen=False),
              env_steps=0, learn_steps=0)
    actual = validate_model(cp, source_cfg, role)
    require(state_equal(actual[0], final["q"]) and all(state_equal(x, y)
            for x, y in zip(actual[1:], originals[:18]+originals[19:])), "Member replacement differs")
    return cp


def accepted_training(a):
    """Historical training source is intentionally NOT re-admitted against current HEAD."""
    from scripts.threat_warmstart import validate_final_receipt
    training_path = bound(a, a["training_admission"])
    training = json.loads(training_path.read_text())
    closure = read_bound(a, a["training_completion"])
    require(training.get("profile") == "threat_warmstart_20261109" and training.get("stage") == "training"
            and closure.get("status") == "COMPLETE_TRAINING_NO_STRENGTH_CLAIM"
            and closure.get("profile") == training["profile"]
            and closure.get("source") == training["source"]
            and closure.get("admission_sha256") == digest(training_path)
            and closure.get("actual") == dict(technical_games=4,prefill_games=80,learning_games=800,optimizer_updates=120000)
            and closure.get("source_and_input_bindings_valid") is True
            and closure.get("protected") == a["protected"]
            and closure.get("model_sha256") == FINAL_SHA, "Historical Root completion missing")
    owner_path = bound(a, Path(training["out"])/"state.json")
    require(digest(owner_path) == closure["state_sha256"], "Closed training owner state changed")
    owner = json.loads(owner_path.read_text())
    require(owner.get("status") == "complete" and not owner.get("active")
            and owner.get("admission_sha256") == digest(training_path)
            and owner.get("source") == training["source"] and owner.get("stage") == "training"
            and set(owner.get("jobs", {})) == {"control", "threat"}
            and all(j.get("returncode") == 0 for j in owner["jobs"].values()), "Training processes not closed")
    paths = {}
    for role in ("control", "threat"):
        receipt = bound(a, owner["receipts"][role]["path"])
        require(digest(receipt) == owner["receipts"][role]["sha256"], "Historical receipt binding differs")
        validate_final_receipt(receipt, training, digest(training_path), role)
        paths[role] = bound(a, receipt.parent/"final.pth")
        require(str(paths[role]) == closure["models"][role]
                and digest(paths[role]) == closure["model_sha256"][role], "Root accepted final model differs")
    return paths


def loaded_agent(path, cp, *, adapter=False):
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.main import Agent_x
    from scripts.threat_warmstart import ThreatAgent
    cls = ThreatAgent if adapter else Agent_x
    agent = cls("player_0", agent_path=str(path), cfg=AgentConfig.from_dict(cp["cfg"]),
                train=False, seed=0, **({"role": "control"} if adapter else {}))
    agent.set_to_eval_mode(); agent.autosave_on_terminate = False
    actual = [agent.q, *agent.extra_q]
    require(not agent.training and not agent.cfg.frozen and agent.cnn_policy is None
            and len(actual) == 36 and agent.feat_dim == cp["feature_dim"]
            and state_equal(agent.target_q.state_dict(), cp["target_q"])
            and all(state_equal(m.state_dict(), sd) for m, sd in zip(actual, [cp["q"], *cp["ensemble"]])),
            "Loader fallback or wrong actual ensemble")
    return agent


def equal_suffix_batches(agent, ns, mask):
    import numpy as np
    import torch
    from scripts.experiment import state_sha256
    require(agent.q.feat_dim == 101 and len(agent.extra_q) == 35
            and all(m.feat_dim == 79 for m in agent.extra_q), "Wrong actual mixed ensemble")
    require(ns.ndim == 2 and ns.shape[1] == 101 and ns.dtype == np.float32
            and mask.shape == (len(ns), 6) and np.isfinite(ns).all()
            and np.isfinite(mask).all() and np.isin(mask, [0, 1]).all(), "Invalid accepted next states/masks")
    indices = np.flatnonzero(np.any(ns[:, 79:] != 0, axis=1))[:16]
    require(len(indices) == 16, "Need 16 exposed finite real replay rows")
    require(np.any(mask[indices], axis=1).all(), "Each fixed exposed row needs a legal next action")
    proofs = []
    with torch.no_grad():
        for count in (1, 8, 16):
            ids = indices[:count]
            x = torch.as_tensor(ns[ids], device=agent.device)
            z = x.clone(); z[:, 79:] = 0
            means = []
            pairs = []
            for m in [agent.q, *agent.extra_q]:
                real, zero = m(x[:, :m.feat_dim]), m(z[:, :m.feat_dim])
                require(torch.isfinite(real).all() and torch.isfinite(zero).all()
                        and torch.equal(real, zero), "Actual same-width member outputs differ")
                pairs.append((real, zero))
            for position in (0, 1): means.append(torch.stack([p[position] for p in pairs]).mean(0))
            legal = torch.as_tensor(mask[ids], device=agent.device, dtype=torch.bool)
            greedy = [q.masked_fill(~legal, -torch.inf).argmax(-1) for q in means]
            require(torch.equal(*means) and torch.equal(*greedy), "Actual full mean/legal argmax differs")
            proofs.append(dict(indices=ids.tolist(), members=36, equal=True,
                input_sha256=state_sha256(dict(ns=ns[ids], mask=mask[ids])),
                mean_sha256=state_sha256(means[0]), greedy_sha256=state_sha256(greedy[0])))
    return proofs


def technical_command(a, path, sha):
    return [a["python"], "-B", "-m", "scripts.threat_warmstart_compare", "technical",
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


def run_technical(a, path, sha, state_path):
    import numpy as np
    import torch
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.common import make_opponent, play_game
    from scripts.scoring import match_points_after_step
    from scripts.threat_warmstart import TraceEnv, validate_prefill_file
    out = output_dir(a)
    check_owned(a, path, sha, state_path)
    final_paths = accepted_training(a)
    source_path = bound(a, a["v14_source"])
    require(digest(source_path) == a["protected"][str(ROOT/"agents/sherlock/weights/agent_p0.pth")], "Wrong V14 source")
    source = torch.load(source_path, map_location="cpu", weights_only=True)
    models = {}; control_cp = None; control = None
    for role in ROLES:
        final = None if role == "v14" else torch.load(final_paths[role], map_location="cpu", weights_only=True)
        cp = mount(source, final, role)
        model_path = safe_path(out/(role+"36.pth"))
        with model_path.open("xb") as stream:
            torch.save(cp, stream); stream.flush(); os.fsync(stream.fileno())
        saved = torch.load(model_path, map_location="cpu", weights_only=True)
        require(state_equal(saved, cp), "Saved eval copy changed")
        probe = loaded_agent(model_path, saved)
        from scripts.experiment import state_sha256
        models[role] = dict(path=str(model_path), sha256=digest(model_path),
                            member_count=36, feature_dim=cp["feature_dim"], config=cp["cfg"],
                            member_sha256=[state_sha256(sd) for sd in [saved["q"],*saved["ensemble"]]])
        if role == "control": control, control_cp = probe, cp
        else: del probe
    proof_path = bound(a, a["threat_prefill"])
    proof = validate_prefill_file(proof_path)
    require(proof.get("role") == "threat" and proof_path.parent == final_paths["threat"].parent,
            "Batch inputs must belong to accepted threat prefill")
    with np.load(bound(a, proof["replay_file"]), allow_pickle=False) as archive:
        batches = equal_suffix_batches(control, archive["ns"], archive["mask"])

    class MatchTrace(TraceEnv):
        def __init__(self, env, side):
            super().__init__(env); self.side = side; self.points = []
        def step(self, actions):
            previous = self.obs[self.side]
            result = super().step(actions)
            nxt, _, terminated, truncated, info = result
            # All actual per-step v2 match points are compared, including resets.
            self.points.append(match_points_after_step(previous, nxt[self.side], info).tolist())
            return result

    adapter = loaded_agent(models["control"]["path"], control_cp, adapter=True)
    games = []; env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for mode, agent in (("stock", control), ("null_adapter", adapter)):
            for seed, side in TECH_KEYS:
                check_owned(a, path, sha, state_path)
                if hasattr(agent, "begin_game"): agent.begin_game()
                traced = MatchTrace(env, side)
                opponent = make_opponent("solution92", "player_1" if side == "player_0" else "player_0")
                row = play_game(traced, agent, opponent, seed, side, train=False)
                from scripts.experiment import state_sha256
                games.append(dict(mode=mode, seed=seed, side=side, steps=row["steps"],
                    point_counting_version=row["point_counting_version"], native_sha256=traced.native.hexdigest(),
                    trajectory_sha256=traced.trajectory.hexdigest(), points_sha256=state_sha256(traced.points),
                    point_rows=len(traced.points), result=row["result"], our_wins=row["our_wins"],
                    opp_wins=row["opp_wins"], our_points=row["our_points"], opp_points=row["opp_points"]))
                require(agent.caught_errors == 0, "Technical agent caught an error")
    finally: env.close()
    for agent in (control, adapter):
        require(all(state_equal(m.state_dict(), sd) for m,sd in zip(
            [agent.q,*agent.extra_q],[control_cp["q"],*control_cp["ensemble"]])), "Eval mutated model tensors")
    receipt = dict(profile=PROFILE, status="complete", source=a["source"], admission_sha256=sha,
                   training_completion_sha256=digest(a["training_completion"]), command=technical_command(a,path,sha),
                   models=models, batches=batches, games=games, stock_control_accepted=True,
                   batch_replay_sha256=digest(proof["replay_file"]))
    check_technical(receipt); check_owned(a, path, sha, state_path)
    write(out/"technical-receipt.json", receipt)


def check_technical(receipt):
    require(len(receipt["batches"]) == 3 and [len(b["indices"]) for b in receipt["batches"]] == [1,8,16]
            and all(b["equal"] is True and b["members"] == 36 for b in receipt["batches"]), "Missing real batch equality")
    rows = receipt["games"]
    require([(r["mode"],r["seed"],r["side"]) for r in rows] ==
            [(m,s,p) for m in ("stock","null_adapter") for s,p in TECH_KEYS], "Wrong four technical executions")
    for left, right in zip(rows[:2], rows[2:]):
        require(left["steps"] == right["steps"] == left["point_rows"] == right["point_rows"] == 303
                and left["point_counting_version"] == right["point_counting_version"] == 2
                and {k:v for k,v in left.items() if k != "mode"} ==
                    {k:v for k,v in right.items() if k != "mode"}, "Stock/null-adapter behavior differs")


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
    gates = dict(solution_v14=w["threat_solution"] >= w["v14_solution"],
                 solution_control=w["threat_solution"] >= w["control_solution"],
                 direct_v14=w["threat_v14"] >= 24, direct_control=w["threat_control"] >= 24)
    return dict(profile=PROFILE, games=200, counts=counts, gates=gates, nominated=all(gates.values()),
        solution={role:compare_results(frames["threat_solution"],frames[role+"_solution"])
                  for role in ("v14","control")},
        direct={role:direct_result(frames["threat_"+role],job_spec(a,"threat_"+role)["opponent"])
                for role in ("v14","control")},
        files={job_spec(a,n)["csv"]:digest(job_spec(a,n)["csv"]) for n in JOBS},
        interpretation="5000 whole-map bootstrap draws, descriptive score intervals (draw=0.5); "
                       "gates count actual wins. Fixed training start, repeated project selection, "
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
