"""Fixed candidate-progress rescue screen: four technical games, then 120; no promotion."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from scripts.early_curriculum_study import digest, hashes, require, source_identity
from scripts.final_training_supervisor import safe_path
from scripts.threat_warmstart import V14_SHA, ZIP_SHA
from scripts.threat_warmstart_compare import bound, read_bound, write, state_equal, loaded_agent, validate_model

ROOT = Path(__file__).resolve().parents[1]
PROFILE = "candidate_progress_20261109"
ROLES = ("off", "on")
JOBS = ("off_solution", "on_solution", "on_off")
TECH_KEYS = ((9946007, "player_0"), (831006, "player_1"))
COHORTS = {"solution": list(range(9948000, 9948020)), "direct": list(range(9948100, 9948120))}
BASELINE_FIELDS = ("seed", "side", "steps", "reset_steps", "decision_steps", "our_wins", "opp_wins",
                   "our_points", "opp_points", "result", "point_counting_version", "matches", "action_sha256", "caught_errors")


def output_dir(a):
    out = safe_path(a["out"])
    require(out.parent == ROOT/"experiments/analysis"/PROFILE and out.name == a["stage"]+"_v1",
            "Wrong exclusive phase output")
    require(all(out != Path(p) and out not in Path(p).parents for p in a["inputs"]), "Output overlaps input")
    return out


def fixed_cohorts(a):
    require(set(a["cohorts"]) == set(COHORTS), "Exactly two fixed cohorts required")
    cohorts = {k: read_bound(a, p) for k, p in a["cohorts"].items()}
    require(cohorts == COHORTS and all(type(x) is int for values in cohorts.values() for x in values),
            "Fixed cards differ")
    proof = read_bound(a, a["seed_acceptance"])
    require(proof.get("status") == "PASS" and proof.get("profile") == PROFILE
            and proof.get("cohorts") == cohorts and proof.get("no_observed_conflicts") is True
            and bool(proof.get("limitations")) and bool(proof.get("files")), "Missing fixed seed acceptance")
    for p, h in proof["files"].items(): require(digest(bound(a, p)) == h, "Seed evidence changed")
    return cohorts


def admission(path, sha, stage):
    require(digest(path) == sha, "Admission hash differs")
    a = json.loads(Path(path).read_text())
    require(a.get("schema_version") == 1 and a.get("profile") == PROFILE and a.get("stage") == stage
            and a.get("start_authorized") is True and a.get("allow_battery") is True, "Explicit phase admission required")
    require(safe_path(a["root"]) == ROOT == Path.cwd().resolve(), "Wrong checkout")
    require(source_identity(ROOT, a["python"], a["plans"]) == a["source"], "Frozen comparison source differs")
    protected = {str(ROOT/f"agents/sherlock/weights/agent_p{i}.pth"): V14_SHA for i in (0, 1)}
    protected[str(ROOT/"Gruppe15.zip")] = ZIP_SHA
    require(a["protected"] == protected and hashes(protected) == protected
            and hashes(a["inputs"]) == a["inputs"], "Protected/input bytes differ")
    output_dir(a)
    if stage == "technical":
        require(digest(bound(a, a["v14_source"])) == V14_SHA, "Wrong V14 source")
        require(set(a["baseline_manifests"]) == {f"{seed}_{side}" for seed, side in TECH_KEYS}, "Wrong technical keys")
        for seed, side in TECH_KEYS:
            baseline_row(read_bound(a, a["baseline_manifests"][f"{seed}_{side}"]), seed, side)
    else:
        technical = read_bound(a, a["technical_receipt"])
        approval = read_bound(a, a["technical_acceptance"])
        require(technical.get("status") == "complete" and technical.get("profile") == PROFILE
                and technical.get("source") == a["source"], "Technical comparison source differs")
        require(approval.get("status") == "PASS" and approval.get("profile") == PROFILE
                and approval.get("source") == a["source"]
                and approval.get("technical_receipt_sha256") == digest(a["technical_receipt"]), "Root technical acceptance missing")
        check_technical(technical)
        require(set(a["models"]) == set(ROLES), "Exactly two admitted eval copies required")
        for role in ROLES:
            p = bound(a, a["models"][role])
            require(str(p) == technical["models"][role]["path"] and digest(p) == technical["models"][role]["sha256"],
                    "Eval model binding differs")
        fixed_cohorts(a)
    return a


def inference_config(source_cfg, role):
    from agents.sherlock.config import AgentConfig
    require(role in ROLES, "Unknown eval role")
    cfg = AgentConfig.from_dict(source_cfg).to_dict()
    cfg.update(frozen=False, cand_stall_rescue=role == "on")
    return cfg


def mount(source, role):
    require(role in ROLES and source["cfg"].get("cand_rescue") is True
            and source["cfg"].get("rescue_after") == 30 and not source["cfg"].get("zone_rescue")
            and not source["cfg"].get("cand_stall_rescue", False), "Wrong fixed V14 rescue method")
    cp = copy.deepcopy(source)
    cp["cfg"] = inference_config(source["cfg"], role)
    validate_model(cp, cp["cfg"], "v14")
    require(state_equal([cp["q"], *cp["ensemble"], cp["target_q"]],
                        [source["q"], *source["ensemble"], source["target_q"]]), "Eval tensor order/bytes changed")
    return cp


def baseline_row(document, seed, side):
    require(document.get("status") == "complete", "Historical probe incomplete")
    matches = [r for r in document["games"] if (r["key"]["seed"], r["key"]["side"]) == (seed, side)]
    require(len(matches) == 1, "Historical key absent/duplicated")
    record = matches[0]; row = record["observed"]
    require(record.get("complete") is True and record.get("passivity") and all(record["passivity"].values())
            and record.get("baseline_reproduction") and all(record["baseline_reproduction"].values())
            and all(row[k] == record["unobserved"][k] for k in BASELINE_FIELDS)
            and row["steps"] == 303 and row["point_counting_version"] == 2 and row["caught_errors"] == 0,
            "Historical probe not passive/complete")
    return row


class NativeTrace:
    """Only measurement after policy choice; no private information is passed to either agent."""
    def __init__(self, env, side):
        self.env, self.side = env, side
        self.native = hashlib.sha256(); self.matches = []; self.reset_steps = 0

    def reset(self, seed):
        self.obs, info = self.env.reset(seed=seed)
        return self.obs, info

    def step(self, actions):
        import numpy as np
        from scripts.targeting_probe import action_bytes
        from scripts.scoring import match_points_after_step
        self.native.update(action_bytes(actions))
        previous = self.obs[self.side]
        self.reset_steps += int(int(np.asarray(previous["match_steps"])) == 0)
        result = self.env.step(actions)
        nxt, _, terminated, truncated, info = result
        done = bool(np.asarray(terminated[self.side])) or bool(np.asarray(truncated[self.side]))
        if int(np.asarray(nxt[self.side]["match_steps"])) == 0 or done:
            points = match_points_after_step(previous, nxt[self.side], info)
            self.matches.append(dict(match_idx=len(self.matches), points=points.tolist(),
                                     cumulative_wins=np.asarray(nxt[self.side]["team_wins"]).tolist()))
        self.obs = nxt
        return result


def check_technical(receipt):
    rows = receipt["games"]
    require([(r["role"],r["seed"],r["side"]) for r in rows] ==
            [(role,seed,side) for role in ROLES for seed,side in TECH_KEYS], "Exactly four fixed technical games required")
    for row in rows:
        require(row["steps"] == 303 and row["reset_steps"] == 3 and row["decision_steps"] == 300
                and row["point_counting_version"] == 2 and len(row["matches"]) == 3
                and row["caught_errors"] == 0, "Incomplete/failed technical game")
    require(all(r["baseline_equal"] is True and r["cand_stall_early_unit_steps"] == 0 for r in rows[:2]),
            "OFF does not exactly reproduce archived V14")
    require(any(on["cand_stall_early_unit_steps"] > 0 and on["action_sha256"] != off["action_sha256"]
                for off,on in zip(rows[:2],rows[2:])), "ON lacks actual early rescue and native divergence")


def technical_command(a, path, sha):
    return [a["python"], "-B", "-m", "scripts.candidate_progress_eval", "technical",
            "--admission", str(path), "--admission-sha", sha, "--owner-state", str(output_dir(a)/"state.json")]


def check_owned(a, path, sha, state_path):
    deadline = time.monotonic()+5
    while True:
        state = json.loads(Path(state_path).read_text()); job = state.get("jobs",{}).get("technical",{})
        if job or time.monotonic() >= deadline: break
        time.sleep(.05)
    command = technical_command(a,path,sha)
    require(state.get("status") == "running" and state.get("profile") == PROFILE
            and state.get("active") == ["technical"] and state.get("admission_sha256") == sha
            and state.get("owner_pid") == job.get("owner_pid") == os.getppid() > 1
            and job.get("pid") == job.get("pgid") == os.getpid() == os.getpgrp()
            and job.get("argv") == command and getattr(sys,"orig_argv",[])[1:] == command[1:]
            and sys.executable == a["python"] and digest(path) == sha, "Technical worker ownership differs")
    require(all(state.get(k) == a[k] for k in ("root","out","python","plans","source","inputs",
                                             "protected","stop_file","allow_battery")), "Owner binding differs")
    from scripts.fog_reward_supervisor import guard
    guard(state,{},allow_battery=True)


def run_technical(a, path, sha, state_path):
    import torch
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.common import make_opponent, play_game
    from scripts.experiment import limit_threads, state_sha256
    limit_threads(); check_owned(a,path,sha,state_path)
    out = output_dir(a)
    source = torch.load(bound(a,a["v14_source"]), map_location="cpu", weights_only=True)
    models = {}; games = []; env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for role in ROLES:
            cp = mount(source,role); model_path = out/(role+"36.pth")
            with model_path.open("xb") as stream:
                torch.save(cp,stream); stream.flush(); os.fsync(stream.fileno())
            saved = torch.load(model_path,map_location="cpu",weights_only=True)
            require(state_equal(saved,cp), "Saved eval copy differs")
            agent = loaded_agent(model_path,saved)
            require(agent.cfg.cand_stall_rescue is (role == "on") and agent.cfg.to_dict() == cp["cfg"],
                    "Actual inference configuration differs")
            initial = state_sha256([agent.q.state_dict(),agent.target_q.state_dict(),*[m.state_dict() for m in agent.extra_q]])
            for seed,side in TECH_KEYS:
                check_owned(a,path,sha,state_path)
                historical = baseline_row(read_bound(a,a["baseline_manifests"][f"{seed}_{side}"]),seed,side)
                require(inference_config(historical["config"],role) == cp["cfg"],
                        "Historical V14 configuration differs")
                traced = NativeTrace(env,side)
                opponent = make_opponent("solution92","player_1" if side == "player_0" else "player_0")
                row = play_game(traced,agent,opponent,seed,side,train=False)
                row.update(role=role, action_sha256=traced.native.hexdigest(), matches=traced.matches,
                    reset_steps=traced.reset_steps, decision_steps=row["steps"]-traced.reset_steps,
                    caught_errors=agent.caught_errors,
                    cand_stall_early_unit_steps=int(agent.episode_stats().get("cand_stall_early_unit_steps",0)),
                    cand_stall_early_steps=int(agent.episode_stats().get("cand_stall_early_steps",0)))
                row["baseline_equal"] = all(row[k] == historical[k] for k in BASELINE_FIELDS)
                require(initial == state_sha256([agent.q.state_dict(),agent.target_q.state_dict(),
                         *[m.state_dict() for m in agent.extra_q]]), "Technical game mutated eval tensors")
                games.append(row)
                write(out/f"{role}_{seed}_{side}.json",row)
                check_owned(a,path,sha,state_path)
            models[role] = dict(path=str(model_path),sha256=digest(model_path),member_count=36,
                                config=cp["cfg"],tensor_sha256=initial)
    finally: env.close()
    receipt = dict(status="complete",profile=PROFILE,source=a["source"],admission_sha256=sha,
                   command=technical_command(a,path,sha),models=models,games=games,
                   baseline_files={p:digest(p) for p in a["baseline_manifests"].values()}, no_strength_claim=True)
    check_technical(receipt); check_owned(a,path,sha,state_path)
    write(out/"technical-receipt.json",receipt)


def job_spec(a,name):
    require(name in JOBS,"Unknown fixed job")
    role,suffix = name.split("_",1)
    return dict(role=role,cohort="solution" if suffix == "solution" else "direct",
        opponent="solution92" if suffix == "solution" else "self:"+a["models"]["off"],
        csv=str(output_dir(a)/(name+".csv")))


def performance_command(a,name):
    spec = job_spec(a,name)
    return [a["python"],"-B","-m","scripts.par_eval","--weights",a["models"][spec["role"]],
            "--seed-list",a["cohorts"][spec["cohort"]],"--workers","1","--opponents",spec["opponent"],"--out",spec["csv"]]


def validate_csv(a,name):
    import numpy as np
    import pandas as pd
    from scripts.compare_report import validated_results
    spec = job_spec(a,name); df = pd.read_csv(spec["csv"])
    checked = validated_results(df,name); seeds = read_bound(a,a["cohorts"][spec["cohort"]])
    expected = {(spec["opponent"],seed,side) for seed in seeds for side in ("player_0","player_1")}
    require(len(df) == 40 and set(checked[["opponent","seed","side"]].itertuples(index=False,name=None)) == expected,
            "Wrong/missing fixed games")
    for key in ("steps","point_counting_version","our_points","opp_points","our_wins","opp_wins","game_win"):
        values = pd.to_numeric(df[key],errors="raise")
        require(np.isfinite(values).all() and (values >= 0).all() and (values == np.floor(values)).all(), "Invalid integer game metric")
    require(df.steps.eq(303).all() and df.point_counting_version.eq(2).all()
            and (df.our_wins+df.opp_wins <= 3).all()
            and np.array_equal(df.result,np.where(df.our_wins > df.opp_wins,1.,np.where(df.our_wins == df.opp_wins,.5,0.)))
            and np.array_equal(df.game_win,df.result.eq(1).astype(int))
            and np.array_equal(df.point_win,np.where(df.our_points > df.opp_points,1.,np.where(df.our_points == df.opp_points,.5,0.))),
            "Incomplete/inconsistent result")
    return df


def analyze(a):
    from scripts.compare_report import compare_results
    from scripts.league_gates import direct_result
    frames = {n:validate_csv(a,n) for n in JOBS}
    counts = {n:dict(wins=int(df.result.eq(1).sum()),draws=int(df.result.eq(.5).sum()),losses=int(df.result.eq(0).sum()))
              for n,df in frames.items()}
    gates = dict(solution=counts["on_solution"]["wins"] >= counts["off_solution"]["wins"],
                 direct=counts["on_off"]["wins"] >= 24)
    return dict(profile=PROFILE,games=120,counts=counts,gates=gates,nominated=all(gates.values()),
        solution=compare_results(frames["on_solution"],frames["off_solution"]),
        direct=direct_result(frames["on_off"],job_spec(a,"on_off")["opponent"]),
        files={job_spec(a,n)["csv"]:digest(job_spec(a,n)["csv"]) for n in JOBS},
        interpretation="5000 whole-card PCG64 seed-0 draws; descriptive 95% score intervals, draw=0.5. "
            "Gates use actual wins. Repeated project selection, no multiplicity correction; nomination only, no promotion.")


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("command",choices=("technical",))
    p.add_argument("--admission",type=Path,required=True); p.add_argument("--admission-sha",required=True)
    p.add_argument("--owner-state",type=Path,required=True); args = p.parse_args()
    a = admission(args.admission,args.admission_sha,"technical")
    run_technical(a,args.admission.resolve(),args.admission_sha,args.owner_state.resolve())


if __name__ == "__main__": main()
