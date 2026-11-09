"""Fixed V14-member-18 reward study; no validation, resume, or automatic release."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import time

import numpy as np
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x
from agents.sherlock.reward import match_outcome, surviving, unit_rewards
from scripts.early_curriculum_study import digest, hashes, require, source_identity
from scripts.experiment import state_sha256
from scripts.final_rescue_train import action_audit
from scripts.final_training_supervisor import safe_path
from scripts.fog_reward_study import replay_without_reward
from scripts.threat_warmstart import TraceEnv, V14_SHA, ZIP_SHA, model_identity, plain, write

ROOT = Path(__file__).resolve().parents[1]
PROFILE = "match_weight_20261109"
ARMS = ("control", "match")
TECH_KEYS = ((9946007, "player_0"), (831006, "player_1"))
COHORTS = {"train48": list(range(9960000, 9960200)), "prefill48": list(range(9960300, 9960320)),
           "train49": list(range(9961000, 9961200)), "prefill49": list(range(9961300, 9961320)),
           "solution": list(range(9970000, 9970020)), "direct_v14": list(range(9970100, 9970120)),
           "direct_control": list(range(9970200, 9970220))}


def training_config(source, role):
    require(role in ARMS, "Unknown fixed role")
    cfg = AgentConfig.from_dict(source).to_dict()
    require(cfg["hidden"] == 256 and cfg["dueling"] and cfg["canonical"] and cfg["use_belief"]
            and cfg["use_sap"] and cfg["eps_end"] == .05 and cfg["eps_decay_steps"] == 60000
            and cfg["train_every"] == 2 and cfg["use_shaping"], "Unexpected V14 configuration")
    cfg.update(w_match=2 if role == "control" else 20, frozen=False, lr=5e-5,
               rules_in_training=True, rules_in_training_all=True, rescue_in_training=True,
               cand_stall_rescue=False, threat_feats=False, fog_unknown_reward_neutral=False,
               art_splash_in_training=False)
    return cfg


def rollout_plan(start):
    require(type(start) is int and start in (48, 49), "Only starts 48/49 admitted")
    base = 9960000 + (start-48)*1000
    opponents = np.random.default_rng(start).choice(
        ["solution92", "sol92_sq", "default", "rush"], 440, p=[.6, .2, .1, .1])
    keys = [(phase, i, base+offset+i//2, ("player_0", "player_1")[i % 2])
            for phase, count, offset in (("prefill", 40, 300), ("train", 400, 0)) for i in range(count)]
    return [dict(phase=p, game=i, seed=seed, side=side, opponent=str(opp))
            for (p, i, seed, side), opp in zip(keys, opponents)]


def replay_data(buffer):
    idx = np.arange(buffer.size)
    if buffer.size == buffer.capacity: idx = (idx+buffer.pos) % buffer.capacity
    return {k: getattr(buffer, k)[idx].copy() for k in ("s", "a", "r", "ns", "done", "mask")}


def check_reward_arrays(data, stored, role):
    require(role in ARMS and set(data) == {"uid", "outcome", *ARMS}, "Reward evidence schema differs")
    n = len(stored)
    require(all(np.asarray(v).shape == (n,) and np.isfinite(v).all() for v in data.values())
            and np.asarray(stored).dtype == np.float32 and np.isfinite(stored).all(), "Invalid reward evidence")
    c, m, outcome = (np.asarray(data[k], dtype=np.float64) for k in ("control", "match", "outcome"))
    require(np.isin(outcome, [-1., 0., 1.]).all()
            and np.allclose(m-c, 18*outcome, atol=1e-10, rtol=1e-12), "Original formula contrast differs")
    require(np.array_equal(stored, np.asarray(data[role], dtype=np.float32)), "Stored original reward differs")
    # Quantization is computed from each original value, never an adjustable epsilon.
    c32, m32 = c.astype(np.float32).astype(np.float64), m.astype(np.float32).astype(np.float64)
    residual = (m32-c32)-18*outcome-((m32-m)-(c32-c))
    require(np.allclose(residual, 0., atol=1e-10, rtol=0.), "Unexplained stored contrast residual")


@contextmanager
def reward_audit(agent, *, retain=False):
    """Observe this instance's real pushes; never replace Core reward/update methods."""
    original_update, original_push = agent.update, agent.buffer.push
    missing = object()
    prior_update, prior_push = vars(agent).get("update", missing), vars(agent.buffer).get("push", missing)
    configs = {role: AgentConfig.from_dict(dict(agent.cfg.to_dict(), w_match=2 if role == "control" else 20))
               for role in ARMS}
    require(agent.role in ARMS and agent.cfg.w_match == configs[agent.role].w_match
            and not agent.cfg.fog_unknown_reward_neutral, "Unexpected actual reward configuration")
    proof = dict(transitions=0, updates=0, nonzero_outcome_rows=0, masked_final_actions=0)
    digests = {k: hashlib.sha256() for k in ("nonreward", "counterfactual")}
    records = {k: [] for k in ("uid", "outcome", *ARMS)}
    pending, formulas = [], {}
    active = False; terminal = False

    def push(s, action, reward, ns, done, mask):
        require(active and pending, "Unowned or extra replay push")
        uid = pending.pop(0)
        require(agent._cache is not None, "Missing actual next-context cache")
        _, nxt, _, feats, masks, _ = agent._cache
        if not formulas:
            formulas.update({role: unit_rewards(cfg, agent._prev_ctx, nxt, agent._prev_actions, agent._sap_hits)
                             for role, cfg in configs.items()})
            formulas["outcome"] = match_outcome(agent._prev_ctx, nxt)
            formulas["alive"] = surviving(agent.cfg, agent._prev_ctx, nxt)
        expected = {role: formulas[role].get(uid, 0.) for role in ARMS}
        require(math.isclose(expected["match"]-expected["control"], 18*formulas["outcome"],
                             abs_tol=1e-10, rel_tol=1e-12), "Original formula contrast differs")
        alive = uid in formulas["alive"]
        want_ns = feats[uid] if alive else np.zeros(79, np.float32)
        want_mask = masks[uid] if alive else np.array([True, False, False, False, False, False])
        want_done = terminal or nxt["match_step"] == 0 or not alive
        require(np.array_equal(s, agent._prev_feats[uid]) and int(action) == agent._prev_actions[uid]
                and np.array_equal(ns, want_ns) and bool(done) == want_done and np.array_equal(mask, want_mask),
                "Actual UID/final-label/next-feature/terminal replay mismatch")
        require(math.isfinite(reward) and reward == expected[agent.role], "Actual original push reward differs")
        pos = agent.buffer.pos
        original_push(s, action, reward, ns, done, mask)
        require(agent.buffer.pos == (pos+1) % agent.buffer.capacity
                and agent.buffer.r[pos] == np.float32(expected[agent.role])
                and int(agent.buffer.a[pos]) == action and agent.buffer.done[pos] == float(done)
                and np.array_equal(agent.buffer.s[pos], s) and np.array_equal(agent.buffer.ns[pos], ns)
                and np.array_equal(agent.buffer.mask[pos], mask), "Actual stored replay differs")
        row = dict(uid=int(uid), outcome=formulas["outcome"], **expected)
        digests["counterfactual"].update(state_sha256(row).encode())
        digests["nonreward"].update(state_sha256((int(uid), s, int(action), ns, bool(done), mask)).encode())
        if retain:
            for k in records: records[k].append(row[k])
        proof["transitions"] += 1
        proof["nonzero_outcome_rows"] += int(formulas["outcome"] != 0)
        proof["masked_final_actions"] += int(not agent._prev_masks[uid][action])

    def update(*args, **kwargs):
        nonlocal active, terminal
        require(not active and not pending, "Overlapping update audit")
        terminal = bool(kwargs.get("terminated", args[4] if len(args) > 4 else False))
        pending.extend(agent._prev_feats if agent._prev_ctx is not None else [])
        formulas.clear(); active = True
        try:
            result = original_update(*args, **kwargs)
            require(not pending, "Missing real replay pushes")
            proof["updates"] += 1
            return result
        finally: active = False

    agent.update, agent.buffer.push = update, push
    try:
        yield proof
        require(not pending and not active, "Unfinished replay audit")
    finally:
        for obj, name, prior in ((agent, "update", prior_update), (agent.buffer, "push", prior_push)):
            if prior is missing: vars(obj).pop(name, None)
            else: setattr(obj, name, prior)
        proof.update({k+"_sha256": h.hexdigest() for k, h in digests.items()})
        if retain: proof["records"] = {k: np.asarray(v, dtype=np.int64 if k == "uid" else np.float64)
                                      for k, v in records.items()}


def load_initial(a):
    from scripts.ensemble_diversity_train import _source
    path = ROOT/"agents/sherlock/weights/agent_p0.pth"
    _, states, cfg = _source(path)
    require({r: training_config(cfg, r) for r in ARMS} == a["config"] and digest(path) == V14_SHA,
            "Actual original source/config differs")
    return {k: v.detach().cpu().clone() for k, v in states[18].items()}


def make_learner(a, initial, role):
    from scripts.variants import seed_everything
    seed_everything(a["start"])
    agent = Agent_x("player_0", cfg=AgentConfig.from_dict(a["config"][role]), train=True, seed=a["start"])
    agent.role = role
    agent.q.load_state_dict(initial, strict=True); agent.target_q.load_state_dict(initial, strict=True)
    agent.env_steps, agent.learn_steps = 60000, 0
    agent.learn_enabled = agent.autosave_on_terminate = False
    require(agent.training and agent.feat_dim == 79 and agent.n_actions == 6 and not agent.extra_q
            and agent.cnn_policy is None and not agent.opt.state and len(agent.buffer) == 0
            and math.isclose(agent.epsilon, .05, abs_tol=1e-12, rel_tol=0)
            and state_sha256(agent.q.state_dict()) == state_sha256(agent.target_q.state_dict()) == state_sha256(initial),
            "Initial learner is not exact/fresh")
    return agent


def play_one(agent, key, env):
    from scripts.common import make_opponent, play_game
    from scripts.par_eval import require_no_agent_errors
    before = dict(env_steps=agent.env_steps, learn_steps=agent.learn_steps)
    traced = TraceEnv(env)
    opponent = make_opponent(key["opponent"], "player_1" if key["side"] == "player_0" else "player_0")
    with reward_audit(agent, retain=key["phase"] != "train") as audit, action_audit(agent) as labels:
        row = play_game(traced, agent, opponent, key["seed"], key["side"], train=True)
    require_no_agent_errors(agent, opponent)
    records = audit.pop("records", None)
    require(row["steps"] == 303 and row["point_counting_version"] == 2 and agent.caught_errors == 0
            and audit["updates"] == labels["update_calls"] == labels["act_calls"] == 303
            and audit["transitions"] == labels["checked_replay_transitions"] > 0, "Incomplete game/replay audit")
    expected_updates = sum((before["env_steps"]+i+1) % agent.cfg.train_every == 0
                           for i in range(303) if i % 101 != 0) if agent.learn_enabled else 0
    require(agent.env_steps == before["env_steps"]+303
            and agent.learn_steps == before["learn_steps"]+expected_updates, "Unexpected game/update counts")
    loss = agent.pop_mean_loss()
    require(not agent.learn_enabled or math.isfinite(loss), "Nonfinite actual learning loss")
    row.update(key=key, role=agent.role, before=before, env_steps=agent.env_steps, learn_steps=agent.learn_steps,
               loss=loss if math.isfinite(loss) else None, epsilon=agent.epsilon, reward_audit=audit,
               final_action_audit=labels, native_sha256=traced.native.hexdigest(),
               trajectory_sha256=traced.trajectory.hexdigest())
    return row, records


def paired_row(row):
    return {k: row[k] for k in ("key", "native_sha256", "trajectory_sha256", "reward_audit",
            "final_action_audit", "our_wins", "opp_wins", "our_points", "opp_points", "result")}


def save_reward_evidence(path, records):
    with Path(path).open("xb") as stream: np.savez_compressed(stream, **records)
    return dict(path=str(path), sha256=digest(path), arrays_sha256=state_sha256(records))


def check_technical(receipt):
    rows = receipt["games"]
    expected = [(r, seed, side) for r in ARMS for seed, side in TECH_KEYS]
    require(receipt.get("profile") == PROFILE and receipt.get("stage") == "technical"
            and receipt.get("start") == 48 and receipt.get("status") == "complete"
            and len(rows) == 4 and [(r["role"], r["key"]["seed"], r["key"]["side"]) for r in rows] == expected,
            "Exactly four fixed technical games required")
    for row in rows:
        require(row["steps"] == 303 and row["point_counting_version"] == 2 and row["learn_steps"] == 0
                and row["initial"] == row["current"] and row["reward_audit"]["transitions"] > 0,
                "Technical identity/replay failure")
        evidence = row["reward_evidence"]
        require(receipt["files"].get(evidence["path"]) == evidence["sha256"] == digest(evidence["path"]),
                "Technical reward evidence changed")
        with np.load(evidence["path"], allow_pickle=False) as f: data = {k: f[k] for k in f.files}
        require(state_sha256(data) == evidence["arrays_sha256"]
                and len(data["uid"]) == row["reward_audit"]["transitions"]
                and np.count_nonzero(data["outcome"]) == row["reward_audit"]["nonzero_outcome_rows"],
                "Technical numerical evidence differs")
        check_reward_arrays(data, data[row["role"]].astype(np.float32), row["role"])
    require(rows[0]["initial"] == rows[2]["initial"], "Technical initial states differ")
    for c, m in zip(rows[:2], rows[2:]):
        require(paired_row(c) == paired_row(m), "Technical native/public/nonreward/formula evidence differs")
    require(sum(r["reward_audit"]["nonzero_outcome_rows"] for r in rows[:2]) > 0,
            "Technical match-term exposure absent")


def bound(a, path):
    path = Path(path).resolve()
    require(a["inputs"].get(str(path)) == digest(path), "Unbound/changed input")
    return json.loads(path.read_text())


def output_dir(a):
    out = safe_path(a["out"])
    require(out.parent == ROOT/"experiments/analysis"/PROFILE and out.name == a["stage"]+"_v1"
            and all(out != Path(p) and out not in Path(p).parents for p in a["inputs"]), "Unsafe fixed output")
    return out


def admission(path, expected_sha, stage):
    path = Path(path).resolve()
    require(stage in ("technical", "pair48", "pair49") and digest(path) == expected_sha, "Admission hash/stage differs")
    a = json.loads(path.read_text())
    require(a.get("profile") == PROFILE and a.get("schema_version") == 1 and a.get("stage") == stage
            and a.get("start") == (49 if stage == "pair49" else 48) and a.get("start_authorized") is True
            and type(a.get("allow_battery")) is bool, "Explicit fixed phase admission required")
    require(Path(a["root"]).resolve() == ROOT == Path.cwd().resolve(), "Wrong checkout")
    require(source_identity(ROOT, a["python"], a["plans"]) == a["source"], "Frozen sources differ")
    protected = {str(ROOT/f"agents/sherlock/weights/agent_p{i}.pth"): V14_SHA for i in (0, 1)}
    protected[str(ROOT/"Gruppe15.zip")] = ZIP_SHA
    require(a["protected"] == protected and hashes(protected) == protected and hashes(a["inputs"]) == a["inputs"],
            "Protected/input files differ")
    config = bound(a, a["config_manifest"])
    require(config["source_sha256"] == V14_SHA
            and a["config"] == {r: training_config(config["source_config"], r) for r in ARMS}
            and a["rollout_plan"] == rollout_plan(a["start"]), "Config/fixed plan differs")
    seeds = bound(a, a["seed_acceptance"])
    require(seeds.get("status") == "PASS" and seeds.get("profile") == PROFILE and seeds.get("cohorts") == COHORTS
            and seeds.get("no_observed_conflicts") is True and bool(seeds.get("limitations"))
            and bool(seeds.get("files")), "Missing fixed seed acceptance")
    require(all(a["inputs"].get(p) == h == digest(p) for p, h in seeds["files"].items()), "Seed evidence differs")
    output_dir(a)
    if stage != "technical":
        tech = bound(a, a["technical_receipt"])
        require(tech["source"] == a["source"] and tech["config"] == a["config"], "Technical source/config differs")
        check_technical(tech)
        require(all(a["inputs"].get(p) == h == digest(p) for p, h in tech["files"].items()), "Unbound technical files")
    if stage == "pair49":
        closure = bound(a, a["pair48_closure"])
        require(closure.get("profile") == PROFILE and closure.get("status") == "PASS"
                and closure.get("start") == 48 and closure.get("source") == a["source"]
                and set(closure.get("receipts", {})) == set(ARMS), "Pair48 must first be accepted")
        for role in ARMS:
            prior = bound(a, closure["receipts"][role])
            require(digest(closure["receipts"][role]) == closure["receipt_sha256"][role]
                    and prior["status"] == "complete" and prior["start"] == 48 and prior["role"] == role,
                    "Pair48 receipt differs")
    return a


def worker_command(a, path, sha, state_path, role):
    return [a["python"], "-B", "-m", "scripts.match_weight_study", "worker", "--admission", str(path),
            "--admission-sha", sha, "--owner-state", str(state_path), "--role", role]


def check_worker(state, a, sha, role, command, *, pid, pgid, ppid, executable, actual):
    roles = {"technical"} if a["stage"] == "technical" else set(ARMS)
    job = state.get("jobs", {}).get(role, {})
    require(role in roles and state.get("profile") == PROFILE and state.get("status") == "running"
            and role in state.get("active", []) and 1 <= len(state["active"]) <= 2 and set(state["active"]) <= roles
            and state.get("owner_pid") == ppid and ppid > 1 and job.get("owner_pid") == ppid
            and job.get("pid") == job.get("pgid") == pid == pgid and job.get("argv") == command
            and executable == a["python"] and isinstance(actual, list) and len(actual) == len(command)
            and actual[1:] == command[1:] and state.get("admission_sha256") == sha,
            "Worker lacks exact live ownership")
    require(all(state.get(k) == a[k] for k in ("root", "out", "python", "plans", "source", "protected",
            "stop_file", "allow_battery", "stage", "start")), "Owner admission binding differs")


class WorkerGuard:
    def __init__(self, a, path, sha, state_path, role, stop):
        self.a, self.path, self.sha, self.state_path = a, Path(path), sha, Path(state_path)
        self.role, self.stop, self.release_sha = role, stop, None
        self.command = worker_command(a, path, sha, state_path, role)

    def __call__(self):
        from scripts.fog_reward_supervisor import guard
        require(not self.stop[0], "Worker signal: stop at completed game boundary")
        state = json.loads(self.state_path.read_text())
        check_worker(state, self.a, self.sha, self.role, self.command, pid=os.getpid(), pgid=os.getpgrp(),
                     ppid=os.getppid(), executable=sys.executable, actual=getattr(sys, "orig_argv", None))
        require(digest(self.path) == self.sha and state["inputs"].get(str(self.path)) == self.sha
                and all(state["inputs"].get(p) == h for p, h in self.a["inputs"].items()), "Bound admission changed")
        if self.release_sha:
            require(digest(Path(self.a["out"])/"release.json") == self.release_sha, "Root release changed")
        guard(state, {}, allow_battery=self.a["allow_battery"])


def save_replay(path, buffer):
    with Path(path).open("xb") as stream: np.savez_compressed(stream, **replay_data(buffer))


def save_checkpoint(path, agent, a, status, completed):
    require(status in ("prefill", "complete", "incomplete"), "Explicit checkpoint status required")
    payload = dict(q=agent.q.state_dict(), target_q=agent.target_q.state_dict(), opt=agent.opt.state_dict(),
        cfg=agent.cfg.to_dict(), feature_dim=79, n_actions=6, ensemble=[], ensemble_dims=[],
        env_steps=agent.env_steps, learn_steps=agent.learn_steps,
        match_weight=dict(profile=PROFILE, status=status, role=agent.role, start=a["start"], source=a["source"],
                          completed_games=completed, component_index=18))
    require(all(torch.isfinite(v).all() for k in ("q", "target_q") for v in payload[k].values()), "Nonfinite weights")
    with Path(path).open("xb") as stream: torch.save(payload, stream)


def prefill_proof(directory, agent, a, sha, rows, initial, records):
    require(len(rows) == 40 and not agent.learn_enabled and agent.learn_steps == 0
            and initial == model_identity(agent) and len(agent.buffer) >= agent.cfg.learn_start,
            "Prefill changed weights/optimizer or is insufficient")
    audit = {k: np.concatenate([r[k] for r in records]) for k in records[0]}
    require(len(audit["uid"]) == len(agent.buffer), "Prefill ring overflow: full ordered evidence required")
    check_reward_arrays(audit, replay_data(agent.buffer)["r"], agent.role)
    replay, checkpoint, rewards = (directory/name for name in ("prefill-replay.npz", "prefill.pth", "prefill-reward-audit.npz"))
    save_replay(replay, agent.buffer); save_checkpoint(checkpoint, agent, a, "prefill", 40)
    with rewards.open("xb") as stream: np.savez_compressed(stream, **audit)
    return dict(status="prefill_ready", profile=PROFILE, role=agent.role, start=a["start"], stage=a["stage"],
        source=a["source"], admission_sha256=sha, config=a["config"][agent.role], games=40,
        initial=initial, current=model_identity(agent), env_steps=agent.env_steps, learn_steps=agent.learn_steps,
        replay_size=len(agent.buffer), replay_metadata=dict(size=agent.buffer.size, pos=agent.buffer.pos,
            capacity=agent.buffer.capacity, mask_dim=agent.buffer._mask_dim),
        replay_without_reward_sha256=replay_without_reward(agent.buffer), replay_sha256=state_sha256(replay_data(agent.buffer)),
        reward_audit_sha256=state_sha256(audit), nonzero_outcome_rows=int(np.count_nonzero(audit["outcome"])),
        files=hashes((replay, checkpoint, rewards)), paired_rows=[paired_row(r) for r in rows])


def validate_prefill_file(path):
    path = Path(path); proof = json.loads(path.read_text()); directory = path.parent
    require(proof.get("profile") == PROFILE and proof.get("status") == "prefill_ready"
            and proof["role"] in ARMS and proof["start"] in (48, 49) and proof["games"] == 40
            and proof["env_steps"] == 72120 and proof["learn_steps"] == 0 and proof["initial"] == proof["current"],
            "Invalid unchanged prefill")
    require(hashes(proof["files"]) == proof["files"] and set(proof["files"]) ==
            {str(directory/n) for n in ("prefill.pth", "prefill-replay.npz", "prefill-reward-audit.npz")}, "Prefill files differ")
    with np.load(directory/"prefill-replay.npz", allow_pickle=False) as f: replay = {k: f[k] for k in f.files}
    with np.load(directory/"prefill-reward-audit.npz", allow_pickle=False) as f: audit = {k: f[k] for k in f.files}
    n = proof["replay_size"]
    require(set(replay) == {"s", "a", "r", "ns", "done", "mask"}
            and replay["s"].shape == replay["ns"].shape == (n, 79) and replay["mask"].shape == (n, 6)
            and all(np.isfinite(v).all() for v in replay.values()), "Invalid prefill replay")
    without = dict(proof["replay_metadata"], **{k: v for k, v in replay.items() if k != "r"})
    require(state_sha256(without) == proof["replay_without_reward_sha256"]
            and state_sha256(replay) == proof["replay_sha256"] and state_sha256(audit) == proof["reward_audit_sha256"],
            "Saved prefill identity differs")
    check_reward_arrays(audit, replay["r"], proof["role"])
    require(proof["nonzero_outcome_rows"] == np.count_nonzero(audit["outcome"]) > 0, "No actual match exposure")
    cp = torch.load(directory/"prefill.pth", map_location="cpu", weights_only=True)
    require({"q": state_sha256(cp["q"]), "target": state_sha256(cp["target_q"]), "optimizer": state_sha256(cp["opt"])}
            == proof["initial"] and cp["cfg"] == proof["config"] and cp["env_steps"] == 72120
            and cp["learn_steps"] == 0 and not cp["opt"]["state"], "Actual prefill tensors/optimizer differ")
    return proof


def compare_prefills(control, match):
    require((control["role"], match["role"]) == ARMS, "Both fixed roles required")
    same = ("profile", "start", "stage", "source", "admission_sha256", "games", "initial", "current",
            "env_steps", "learn_steps", "replay_size", "replay_metadata", "replay_without_reward_sha256",
            "reward_audit_sha256", "nonzero_outcome_rows", "paired_rows")
    require(all(control[k] == match[k] for k in same) and control["nonzero_outcome_rows"] > 0,
            "Paired prefill actions/public/replay/formulas differ")
    require(control["config"]["w_match"] == 2 and match["config"]["w_match"] == 20
            and dict(control["config"], w_match=20) == match["config"], "Prefill config contrast differs")


def validate_release(release, a, sha, pins):
    require(release.get("profile") == PROFILE and release.get("status") == "approved"
            and release.get("start") == a["start"] and release.get("source") == a["source"]
            and release.get("roles") == list(ARMS) and release.get("admission_sha256") == sha
            and set(pins) == set(ARMS) and release.get("prefill_sha256") == pins
            and bool(release.get("root_review_sha256")), "Missing/stale explicit Root prefill approval")
    return release


def approve_prefill(a, sha, review_path, review_sha):
    require(a["stage"] in ("pair48", "pair49"), "Only a training pair can be released")
    directory = Path(a["out"])
    paths = {r: directory/r/"prefill.json" for r in ARMS}; pins = {r: digest(p) for r, p in paths.items()}
    proofs = [validate_prefill_file(paths[r]) for r in ARMS]
    compare_prefills(*proofs)
    require(all(p["source"] == a["source"] and p["admission_sha256"] == sha and p["start"] == a["start"]
                and p["config"] == a["config"][p["role"]] for p in proofs), "Prefill admission differs")
    state = json.loads((directory/"state.json").read_text())
    require(state.get("status") == "running" and set(state.get("active", [])) == set(ARMS)
            and state.get("admission_sha256") == sha and state.get("start") == a["start"], "Both workers must wait")
    for r in ARMS:
        waiting = json.loads((directory/r/"waiting.json").read_text())
        require(waiting == dict(profile=PROFILE, role=r, start=a["start"], admission_sha256=sha,
                                prefill_sha256=pins[r]), "Original prefill waiting marker differs")
    review_path = Path(review_path).resolve()
    require(digest(review_path) == review_sha, "Root review changed")
    review = json.loads(review_path.read_text())
    require(review.get("status") == "PASS" and review.get("profile") == PROFILE
            and review.get("start") == a["start"] and review.get("source") == a["source"]
            and review.get("admission_sha256") == sha and review.get("prefill_sha256") == pins,
            "Root review does not accept these prefills")
    release = dict(profile=PROFILE, status="approved", start=a["start"], roles=list(ARMS), source=a["source"],
        admission_sha256=sha, prefill_sha256=pins, root_review=str(review_path), root_review_sha256=review_sha)
    write(directory/"release.json", release)
    return release


def wait_release(a, sha, guard):
    directory = Path(a["out"]); path = directory/"release.json"
    while not path.exists(): guard(); time.sleep(1)
    pins = {r: digest(directory/r/"prefill.json") for r in ARMS}
    release = validate_release(json.loads(path.read_text()), a, sha, pins)
    require(digest(release["root_review"]) == release["root_review_sha256"], "Accepted Root review changed")
    guard.release_sha = digest(path); guard()
    return release


def run_worker(a, path, sha, state_path, role):
    from scripts.experiment import limit_threads
    limit_threads()
    stop = [False]
    handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    for sig in handlers: signal.signal(sig, lambda *_: stop.__setitem__(0, True))
    agent = env = directory = None; rows = []
    guard = WorkerGuard(a, path, sha, state_path, role, stop)
    try:
        deadline = time.monotonic()+15
        expected = {"technical"} if a["stage"] == "technical" else set(ARMS)
        while not expected <= set(json.loads(Path(state_path).read_text()).get("jobs", {})):
            require(not stop[0] and not Path(a["stop_file"]).exists() and time.monotonic() < deadline,
                    "Initial worker registration missing/STOP")
            time.sleep(.05)
        guard()
        directory = Path(a["out"])/role; directory.mkdir(exist_ok=False)
        initial_weights = load_initial(a)
        from luxai_s3.wrappers import LuxAIS3GymEnv
        env = LuxAIS3GymEnv(numpy_output=True)
        with (directory/"games.jsonl").open("x") as stream:
            for arm in (ARMS if role == "technical" else (role,)):
                agent = make_learner(a, initial_weights, arm); initial = model_identity(agent); records = []
                write(directory/(arm+"-initial.json"), dict(initial=initial, config=a["config"][arm], start=a["start"]))
                keys = ([dict(phase="technical", game=i, seed=s, side=side, opponent="solution92")
                         for i, (s, side) in enumerate(TECH_KEYS)] if role == "technical" else rollout_plan(a["start"]))
                for key in keys:
                    guard(); row, reward_records = play_one(agent, key, env)
                    if role == "technical":
                        evidence = save_reward_evidence(directory/f"{arm}-{key['game']}-reward-audit.npz", reward_records)
                        row.update(initial=initial, current=model_identity(agent), reward_evidence=evidence)
                    stream.write(json.dumps(plain(row), allow_nan=False)+"\n"); stream.flush(); os.fsync(stream.fileno())
                    rows.append(row)
                    if role != "technical" and reward_records is not None: records.append(reward_records)
                    guard()
                    if role != "technical" and key["phase"] == "prefill" and key["game"] == 39:
                        proof = prefill_proof(directory, agent, a, sha, rows, initial, records)
                        write(directory/"prefill.json", proof); records.clear()
                        write(directory/"waiting.json", dict(profile=PROFILE, role=role, start=a["start"],
                              admission_sha256=sha, prefill_sha256=digest(directory/"prefill.json")))
                        wait_release(a, sha, guard); agent.learn_enabled = True
        if role != "technical":
            require(len(rows) == 440 and agent.env_steps == 193320 and agent.learn_steps == 60000
                    and model_identity(agent)["q"] != initial["q"], "Incomplete/unchanged final learner")
            save_checkpoint(directory/"final.pth", agent, a, "complete", len(rows))
            save_replay(directory/"final-replay.npz", agent.buffer)
        guard()
        receipt = dict(status="complete", profile=PROFILE, stage=a["stage"], start=a["start"], role=role,
            source=a["source"], config=a["config"], admission_sha256=sha, command=guard.command, games=rows,
            files=hashes(p for p in directory.iterdir() if p.is_file()), final_identity=model_identity(agent),
            final_replay_sha256=state_sha256(replay_data(agent.buffer)), release_sha256=guard.release_sha,
            no_strength_claim=True)
        if role == "technical": check_technical(receipt)
        write(directory/"receipt.json", receipt)
        return receipt
    except BaseException as exc:
        if directory is not None:
            artifacts = {}
            if agent is not None:
                try:
                    save_checkpoint(directory/"incomplete.pth", agent, a, "incomplete", len(rows))
                    artifacts = hashes((directory/"incomplete.pth",))
                except BaseException as error: artifacts = {"save_error": str(error)}
            write(directory/"incomplete.json", dict(status="incomplete", profile=PROFILE, role=role,
                  start=a["start"], completed_games=len(rows), error=f"{type(exc).__name__}: {exc}",
                  artifacts=artifacts, eligible=False))
        raise
    finally:
        try:
            if env is not None: env.close()
        finally:
            for sig, handler in handlers.items(): signal.signal(sig, handler)


def validate_final_receipt(path, a, sha, role):
    """Run only after both original workers exited; inspect their actual end files."""
    path = Path(path); directory = path.parent; receipt = json.loads(path.read_text())
    require(receipt.get("status") == "complete" and receipt.get("profile") == PROFILE
            and receipt.get("stage") == a["stage"] and receipt.get("start") == a["start"]
            and receipt.get("role") == role and receipt.get("source") == a["source"]
            and receipt.get("config") == a["config"] and receipt.get("admission_sha256") == sha,
            "Final receipt binding differs")
    require(hashes(receipt["files"]) == receipt["files"], "Actual final files changed")
    rows = [json.loads(line) for line in (directory/"games.jsonl").read_text().splitlines()]
    require(rows == receipt["games"] and [r["key"] for r in rows] == rollout_plan(a["start"]), "Final chronology differs")
    prefill = validate_prefill_file(directory/"prefill.json")
    require(prefill["paired_rows"] == [paired_row(r) for r in rows[:40]], "Preserved prefill differs")
    for i, row in enumerate(rows):
        expected_before = 60000+303*i
        require(row["before"]["env_steps"] == expected_before and row["env_steps"] == expected_before+303
                and row["learn_steps"] == (0 if i < 40 else 150*(i-39))
                and row["steps"] == 303 and row["point_counting_version"] == 2
                and (row["loss"] is None if i < 40 else math.isfinite(row["loss"])), "Final counters/loss differ")
    release_path = Path(a["out"])/"release.json"
    require(digest(release_path) == receipt["release_sha256"], "Final release changed")
    release = validate_release(json.loads(release_path.read_text()), a, sha,
                              {r: digest(Path(a["out"])/r/"prefill.json") for r in ARMS})
    require(digest(release["root_review"]) == release["root_review_sha256"], "Final Root review changed")
    cp = torch.load(directory/"final.pth", map_location="cpu", weights_only=True)
    require(cp["cfg"] == a["config"][role] and cp["feature_dim"] == 79 and cp["n_actions"] == 6
            and not cp["ensemble"] and not cp["ensemble_dims"] and cp["env_steps"] == 193320
            and cp["learn_steps"] == 60000 and cp["match_weight"] == dict(profile=PROFILE, status="complete",
                role=role, start=a["start"], source=a["source"], completed_games=440, component_index=18),
            "Final checkpoint metadata differs")
    actual = {"q": state_sha256(cp["q"]), "target": state_sha256(cp["target_q"]), "optimizer": state_sha256(cp["opt"])}
    require(actual == receipt["final_identity"] and actual["q"] != prefill["initial"]["q"]
            and cp["opt"]["state"] and all(int(v["step"]) == 60000 for v in cp["opt"]["state"].values()),
            "Final tensors/actual Adam counts differ")
    for key in ("q", "target_q"):
        require(cp[key]["body.0.weight"].shape == (256, 79)
                and all(torch.isfinite(v).all() for v in cp[key].values()), "Invalid final weights")
    with np.load(directory/"final-replay.npz", allow_pickle=False) as f: replay = {k: f[k] for k in f.files}
    require(replay["s"].shape == replay["ns"].shape == (len(replay["r"]), 79)
            and all(np.isfinite(v).all() for v in replay.values())
            and state_sha256(replay) == receipt["final_replay_sha256"], "Actual final replay differs")
    return dict(status="PASS", role=role, start=a["start"], games=440, learn_steps=60000, receipt_sha256=digest(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    worker, approve = sub.add_parser("worker"), sub.add_parser("approve-prefill")
    for p in (worker, approve):
        p.add_argument("--admission", type=Path, required=True); p.add_argument("--admission-sha", required=True)
    worker.add_argument("--owner-state", type=Path, required=True)
    worker.add_argument("--role", choices=("technical", *ARMS), required=True)
    approve.add_argument("--review", type=Path, required=True); approve.add_argument("--review-sha", required=True)
    args = parser.parse_args()
    stage = json.loads(args.admission.read_text())["stage"]
    a = admission(args.admission, args.admission_sha, stage)
    if args.command == "worker":
        run_worker(a, args.admission.resolve(), args.admission_sha, args.owner_state.resolve(), args.role)
    else: approve_prefill(a, args.admission_sha, args.review, args.review_sha)


if __name__ == "__main__": main()
