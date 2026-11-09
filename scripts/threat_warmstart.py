"""Fixed two-arm threat-feature warmstart; no promotion, resume, or auto release."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import tempfile
import time

import numpy as np
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.config import AgentConfig
from agents.sherlock.features import threat_features
from agents.sherlock.main import Agent_x
from agents.sherlock.model import checkpoint_ensemble_dims
from agents.sherlock.replay_buffer import ReplayBuffer
from agents.sherlock.reward import surviving
from scripts.early_curriculum_study import digest, hashes, require, source_identity
from scripts.experiment import state_sha256

ROOT = Path(__file__).resolve().parents[1]
PROFILE = "threat_warmstart_20261109"
ARMS = ("control", "threat")
V14_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
ZIP_SHA = "88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6"
TECH_KEYS = ((831006, "player_1"), (831000, "player_0"))
COHORTS = {"train": list(range(9950000, 9950200)), "prefill": list(range(9950300, 9950320))}


def plain(value):
    if isinstance(value, dict): return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [plain(v) for v in value]
    if hasattr(value, "tolist"): return value.tolist()
    return value


def write(path, value):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix="."+path.name+".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(plain(value), stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
        os.link(temporary, path)  # Publish complete bytes atomically; an existing name fails.
    finally:
        Path(temporary).unlink(missing_ok=True)


def rollout_plan():
    rng = np.random.default_rng(47)
    opponents = rng.choice(["solution92", "sol92_sq", "default", "rush"], size=440, p=[.6, .2, .1, .1])
    keys = [(phase, game, start+game//2, ("player_0", "player_1")[game % 2])
            for phase, count, start in (("prefill", 40, 9950300), ("train", 400, 9950000))
            for game in range(count)]
    return [dict(phase=p, game=g, seed=seed, side=side, opponent=str(opp))
            for (p, g, seed, side), opp in zip(keys, opponents)]


def training_config(source):
    cfg = AgentConfig.from_dict(source).to_dict()
    require(cfg["hidden"] == 256 and cfg["dueling"] and cfg["canonical"] and cfg["use_belief"]
            and cfg["eps_end"] == .05 and cfg["eps_decay_steps"] == 60000, "Unexpected V14 architecture/epsilon")
    cfg.update(threat_feats=True, frozen=False, lr=.00005, rules_in_training=True,
               rules_in_training_all=True, rescue_in_training=True,
               fog_unknown_reward_neutral=False, art_splash_in_training=False)
    return cfg


def expand_state(original):
    require(isinstance(original, dict) and "body.0.weight" in original, "Missing original first layer")
    require(all(isinstance(t, torch.Tensor) and torch.isfinite(t).all() for t in original.values()),
            "Nonfinite/non-tensor source state")
    weight = original["body.0.weight"]
    require(weight.shape == (256, 79) and weight.dtype == torch.float32, "Expected 256x79 first layer")
    result = {k: v.detach().cpu().clone() for k, v in original.items()}
    expanded = weight.new_zeros((256, 101), device="cpu")
    expanded[:, :79] = weight.detach().cpu()
    result["body.0.weight"] = expanded
    return result


class CheckedReplay(ReplayBuffer):
    def __init__(self, owner, capacity):
        super().__init__(capacity, 101)
        self.owner = owner

    def push(self, s, a, r, ns, done, next_mask):
        self.owner.check_transition(s, a, r, ns, done, next_mask)
        return super().push(s, a, r, ns, done, next_mask)

    def sample(self, batch_size, rng=None):
        result = super().sample(batch_size, rng)
        self.owner.check_batch(result)
        return result


class ThreatAgent(Agent_x):
    """Only control feature tails differ; core actions, replay target and reward stay original."""
    def __init__(self, *args, role, **kwargs):
        require(role in ARMS, "Unknown feature role")
        self.role = role
        super().__init__(*args, **kwargs)
        require(self.feat_dim == 101 and self.n_actions == 6 and self.cfg.threat_feats
                and not self.cfg.frozen and self.feat_belief is self.belief, "Expected canonical 101-feature learner")
        self.buffer = CheckedReplay(self, self.cfg.buffer_capacity)
        self.autosave_on_terminate = False
        self.learn_enabled = False
        self.learning_audit = Counter()
        self.begin_game()

    def begin_game(self):
        self.game_audit = Counter()
        self._replay_prefix = hashlib.sha256()
        self._replay_full = hashlib.sha256()
        self.examples = []
        self._transition_uids = []

    def _decide(self, obs):
        ctx, ids, features, masks, targets = super()._decide(obs)
        public, adapted = {}, {}
        for uid in ids:
            f = np.asarray(features[uid], dtype=np.float32)
            tail = threat_features(ctx, uid)
            require(f.shape == (101,) and tail.shape == (22,) and np.isfinite(f).all()
                    and np.isfinite(tail).all(), "Invalid public features")
            public[uid] = np.concatenate((f[:79], tail))
            if self.role == "threat":
                require(np.array_equal(f[79:], tail), "Existing threat feature path differs")
                adapted[uid] = f
            else:
                adapted[uid] = f.copy(); adapted[uid][79:] = 0
        self._public_features = public
        self._cache = (self._cache[0], ctx, ids, adapted, masks, targets)
        return self._cache[1:]

    def _act(self, step, obs):
        actions = super()._act(step, obs)
        self._native_actions = actions.copy()
        self._action_public = ({u: f.copy() for u, f in self._public_features.items()}
                               if self._prev_ctx is not None else {})
        return actions

    def _update(self, step, obs, reward, action, terminated, next_obs):
        self._transition_uids = list(self._prev_feats) if self._prev_ctx is not None and self.training else []
        self._transition_terminated = bool(terminated)
        require(np.array_equal(action, self._native_actions), "Submitted/native action mismatch")
        super()._update(step, obs, reward, action, terminated, next_obs)
        require(not self._transition_uids, "Missing expected replay rows")

    def check_features(self, actual, public):
        require(np.asarray(actual).shape == (101,) and np.isfinite(actual).all()
                and np.array_equal(actual[:79], public[:79]), "Replay feature prefix/shape differs")
        expected_tail = np.zeros(22) if self.role == "control" else public[79:]
        require(np.array_equal(actual[79:], expected_tail), "Replay public feature tail differs")

    def check_transition(self, s, action, reward, ns, done, next_mask):
        require(bool(self._transition_uids), "Replay row outside original update")
        uid = self._transition_uids[0]
        ctx, _, features, masks, _ = self._cache[1:]
        canonical = int(self._native_actions[uid, 0])
        if self.belief.mirrored and canonical < geo.SAP: canonical = geo.mirror_dir(canonical)
        require(action == canonical == self._prev_actions[uid] and 0 <= action < 6
                and math.isfinite(float(reward)), "Final replay label/reward differs")
        require(np.array_equal(s, self._prev_feats[uid]), "Current replay row differs")
        self.check_features(s, self._action_public[uid])
        alive = uid in surviving(self.cfg, self._prev_ctx, ctx)
        expected_ns = features[uid] if alive else np.zeros(101, np.float32)
        expected_mask = masks[uid] if alive else np.array([True, False, False, False, False, False])
        expected_done = self._transition_terminated or ctx["match_step"] == 0 or not alive
        require(np.array_equal(ns, expected_ns) and np.array_equal(next_mask, expected_mask)
                and bool(done) == expected_done, "Actual next replay features/mask/done differ")
        next_public = self._public_features[uid] if alive else np.zeros(101, np.float32)
        self.check_features(ns, next_public)
        self._transition_uids.pop(0)
        self.game_audit["replay_rows"] += 1
        # Fog SAP and other original post-network rules can deliberately select
        # an action outside the earlier network mask. Preserve the final label.
        self.game_audit["masked_final_rule_actions"] += int(not self._prev_masks[uid][action])
        self.game_audit["public_nonzero_rows"] += int(np.any(self._action_public[uid][79:]))
        self.game_audit["actual_nonzero_rows"] += int(np.any(s[79:]))
        self.game_audit["public_next_nonzero_rows"] += int(np.any(next_public[79:]))
        row = (np.asarray(s, np.float32), int(action), np.float32(reward), np.asarray(ns, np.float32),
               np.float32(done), np.asarray(next_mask, bool))
        self._replay_full.update(state_sha256(row).encode())
        self._replay_prefix.update(state_sha256((row[0][:79], *row[1:3], row[3][:79], *row[4:])).encode())
        # Four bounded examples per game; all transitions are checked live.
        if len(self.examples) < 4 and (np.any(next_public[79:]) or np.any(self._action_public[uid][79:])):
            self.examples.append(dict(uid=uid, action=int(action), reward=float(reward), done=bool(done),
                current_mask=self._prev_masks[uid].tolist(), s=np.asarray(s).tolist(), ns=np.asarray(ns).tolist(),
                next_mask=np.asarray(next_mask).tolist(), public_tail=self._action_public[uid][79:].tolist(),
                public_next_tail=next_public[79:].tolist()))

    def check_batch(self, batch):
        s, actions, rewards, ns, done, masks = batch
        require(s.shape == ns.shape == (self.cfg.batch_size, 101) and masks.shape == (len(s), 6)
                and np.isfinite(s).all() and np.isfinite(ns).all() and np.isfinite(rewards).all()
                and masks.any(1).all() and ((actions >= 0) & (actions < 6)).all(), "Invalid actual learning batch")
        if self.role == "control": require(not np.any(s[:, 79:]) and not np.any(ns[:, 79:]), "Control batch tail is nonzero")
        self.learning_audit["sampled_batches"] += 1
        self.learning_audit["sampled_exposed_rows"] += int(np.any(s[:, 79:], axis=1).sum())
        self.learning_audit["sampled_exposed_next_rows"] += int(np.any(ns[:, 79:], axis=1).sum())

    def _learn(self):
        require(self.learn_enabled, "Gradient update before explicit release")
        before = self.learn_steps
        super()._learn()
        require(self.learn_steps == before+1, "Unexpected optimizer update count")
        gradient = self.q.body[0].weight.grad[:, 79:]
        require(torch.isfinite(gradient).all(), "Nonfinite added-column gradient")
        self.learning_audit["tail_gradient_steps"] += int(bool(torch.count_nonzero(gradient)))
        if self.role == "control":
            require(not torch.count_nonzero(gradient) and not torch.count_nonzero(self.q.body[0].weight[:, 79:]),
                    "Control columns changed despite zero input")

    def game_proof(self):
        return dict(self.game_audit, replay_prefix_sha256=self._replay_prefix.hexdigest(),
                    replay_full_sha256=self._replay_full.hexdigest(), examples=self.examples)


def model_identity(agent):
    values = dict(q=agent.q.state_dict(), target=agent.target_q.state_dict(), optimizer=agent.opt.state_dict())
    return {k: state_sha256(v) for k, v in values.items()}


def replay_identity(buffer):
    n = len(buffer)
    indices = np.arange(n) if n < buffer.capacity else (np.arange(n)+buffer.pos) % buffer.capacity
    data = {k: getattr(buffer, k)[indices] for k in ("s", "ns", "a", "r", "done", "mask")}
    prefix = dict(data, s=data["s"][:, :79], ns=data["ns"][:, :79])
    return dict(size=n, full=state_sha256(data), prefix=state_sha256(prefix))


def compare_prefills(control, threat):
    for role, proof in zip(ARMS, (control, threat)):
        require(proof["status"] == "prefill_ready" and proof["profile"] == PROFILE and proof["role"] == role
                and proof["games"] == 40 and proof["learn_steps"] == 0 and proof["env_steps"] == 72120
                and proof["replay_size"] >= 5000 and proof["initial"] == proof["current"]
                and proof["public_nonzero_rows"] > 0, "Incomplete/changed/unexposed prefill")
        require([r["key"] for r in proof["paired_rows"]] == rollout_plan()[:40], "Prefill chronology differs")
    require(control["actual_nonzero_rows"] == 0 and threat["actual_nonzero_rows"] == threat["public_nonzero_rows"] > 0
            and control["public_nonzero_rows"] == threat["public_nonzero_rows"],
            "Missing intended zero/real feature contrast")
    for key in ("initial", "replay_size", "replay_prefix_sha256", "paired_rows"):
        require(control[key] == threat[key], "Paired prefill differs: "+key)
    return dict(status="PASS", profile=PROFILE, games_per_arm=40)


def validate_release(release, admission_sha, pins):
    require(release.get("profile") == PROFILE and release.get("status") == "approved"
            and release.get("admission_sha256") == admission_sha and set(pins) == set(ARMS)
            and release.get("prefill_sha256") == pins and bool(release.get("root_review_sha256")),
            "Missing/stale explicit Root prefill approval")
    return release


def bound(a, path):
    path = Path(path).resolve()
    require(a["inputs"].get(str(path)) == digest(path), "Unbound/changed input")
    return json.loads(path.read_text())


def admission(path, expected_sha, stage):
    path = Path(path).resolve()
    require(digest(path) == expected_sha, "Root admission hash differs")
    a = json.loads(path.read_text())
    require(a.get("profile") == PROFILE and a.get("schema_version") == 1
            and a.get("stage") == stage and a.get("start_authorized") is True
            and type(a.get("allow_battery")) is bool, "Explicit phase admission required")
    require(Path(a["root"]).resolve() == ROOT == Path.cwd().resolve(), "Wrong checkout")
    require(source_identity(ROOT, a["python"], a["plans"]) == a["source"], "Frozen sources differ")
    protected = {str(ROOT/f"agents/sherlock/weights/agent_p{i}.pth"): V14_SHA for i in (0, 1)}
    protected[str(ROOT/"Gruppe15.zip")] = ZIP_SHA
    require(a["protected"] == protected and hashes(protected) == protected
            and hashes(a["inputs"]) == a["inputs"], "Protected/input files differ")
    config = bound(a, a["config_manifest"])
    require(config["source_sha256"] == V14_SHA and a["config"] == training_config(config["source_config"])
            and a["rollout_plan"] == rollout_plan(), "Config/fixed plan differs")
    seeds = bound(a, a["seed_acceptance"])
    require(seeds.get("status") == "PASS" and seeds.get("profile") == PROFILE
            and seeds.get("cohorts") == COHORTS and seeds.get("no_observed_conflicts") is True
            and bool(seeds.get("limitations")) and bool(seeds.get("files")), "Missing fixed seed acceptance")
    require(all(a["inputs"].get(p) == h == digest(p) for p, h in seeds["files"].items()), "Seed evidence changed")
    out = Path(a["out"]).resolve()
    require(out.parent == ROOT/"experiments/analysis"/PROFILE
            and out.name == ("technical_v1" if stage == "technical" else "training_v1")
            and all(out != Path(p) and out not in Path(p).parents for p in a["inputs"]), "Unsafe phase output")
    if stage == "training":
        tech = bound(a, a["technical_receipt"])
        require(tech.get("status") == "complete" and tech.get("source") == a["source"]
                and tech.get("config") == a["config"], "Technical source/config differs")
        check_technical(tech["games"])
        require(all(a["inputs"].get(p) == h == digest(p) for p, h in tech["files"].items()), "Technical files unbound")
    return a


def worker_command(a, path, sha, state_path, role):
    return [a["python"], "-B", "-m", "scripts.threat_warmstart", "worker",
            "--admission", str(path), "--admission-sha", sha,
            "--owner-state", str(state_path), "--role", role]


def check_worker(state, a, sha, role, command, *, pid, pgid, ppid, executable, actual):
    job = state.get("jobs", {}).get(role, {})
    expected_roles = {"technical"} if a["stage"] == "technical" else set(ARMS)
    require(role in expected_roles and state.get("profile") == PROFILE and state.get("status") == "running"
            and role in state.get("active", []) and 1 <= len(state["active"]) <= 2
            and set(state["active"]) <= expected_roles and state.get("owner_pid") == ppid and ppid > 1
            and job.get("owner_pid") == ppid and job.get("pid") == job.get("pgid") == pid == pgid
            and job.get("argv") == command and executable == a["python"]
            and isinstance(actual, list) and len(actual) == len(command) and actual[1:] == command[1:]
            and state.get("admission_sha256") == sha, "Worker lacks exact live ownership")
    require(all(state.get(k) == a[k] for k in ("root", "out", "python", "plans", "source", "protected",
                                             "stop_file", "allow_battery")), "Owner admission binding differs")


class WorkerGuard:
    def __init__(self, a, path, sha, state_path, role, stop):
        self.a, self.path, self.sha = a, Path(path), sha
        self.state_path, self.role, self.stop = Path(state_path), role, stop
        self.command = worker_command(a, path, sha, state_path, role)
        self.release_sha = None

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


def load_initial(a):
    path = ROOT/"agents/sherlock/weights/agent_p0.pth"
    require(digest(path) == V14_SHA, "Source V14 hash differs")
    cp = torch.load(path, map_location="cpu", weights_only=True)
    require(cp["feature_dim"] == 79 and cp["n_actions"] == 6
            and checkpoint_ensemble_dims(cp, 79) == [79]*35
            and len(cp.get("ensemble", [])) == 35, "Expected homogeneous 36-member V14")
    require(training_config(cp["cfg"]) == a["config"], "Actual source configuration differs")
    # Component zero is cp['q']; fixed component 18 is ensemble entry 17.
    initial = expand_state(cp["ensemble"][17])
    require(digest(path) == V14_SHA, "Source changed during load")
    return initial


def make_learner(a, initial, role):
    from scripts.variants import seed_everything
    seed_everything(47)
    agent = ThreatAgent("player_0", cfg=AgentConfig.from_dict(a["config"]), train=True, seed=47, role=role)
    agent.q.load_state_dict(initial, strict=True)
    agent.target_q.load_state_dict(initial, strict=True)
    agent.env_steps = 60000; agent.learn_steps = 0
    agent.learn_enabled = False; agent.autosave_on_terminate = False
    require(agent.training and math.isclose(agent.epsilon, .05, abs_tol=1e-12, rel_tol=0)
            and not agent.extra_q and agent.cnn_policy is None
            and not agent.opt.state and len(agent.buffer) == 0
            and state_sha256(agent.q.state_dict()) == state_sha256(agent.target_q.state_dict()) == state_sha256(initial),
            "Warmstart is not exact/fresh")
    return agent


class TraceEnv:
    """Compact public-trajectory/action digests; no raw observations retained."""
    def __init__(self, env):
        self.env = env
        self.native = hashlib.sha256(); self.trajectory = hashlib.sha256()

    def reset(self, seed):
        obs, info = self.env.reset(seed=seed)
        self.obs = obs
        return obs, info

    def step(self, actions):
        result = self.env.step(actions)
        next_obs, reward, terminated, truncated, _ = result
        self.native.update(state_sha256(actions).encode())
        self.trajectory.update(state_sha256((self.obs, actions, next_obs, reward, terminated, truncated)).encode())
        self.obs = next_obs
        return result


def play_one(agent, key, env):
    from scripts.common import make_opponent, play_game
    agent.begin_game()
    before = dict(env_steps=agent.env_steps, learn_steps=agent.learn_steps)
    traced = TraceEnv(env)
    opponent = make_opponent(key["opponent"], "player_1" if key["side"] == "player_0" else "player_0")
    row = play_game(traced, agent, opponent, key["seed"], key["side"], train=True)
    require(row["steps"] == 303 and row["point_counting_version"] == 2 and agent.caught_errors == 0,
            "Incomplete/failed fixed game")
    expected_updates = sum((before["env_steps"]+step+1) % agent.cfg.train_every == 0
                           for step in range(303) if step % 101 != 0) if agent.learn_enabled else 0
    require(agent.env_steps == before["env_steps"]+303
            and agent.learn_steps == before["learn_steps"]+expected_updates, "Unexpected game/update count")
    loss = agent.pop_mean_loss()
    proof = agent.game_proof()
    row.update(key=key, role=agent.role, before=before, env_steps=agent.env_steps, learn_steps=agent.learn_steps,
               loss=loss if math.isfinite(loss) else None, epsilon=agent.epsilon,
               native_sha256=traced.native.hexdigest(), trajectory_sha256=traced.trajectory.hexdigest(), **proof)
    return row


def paired_row(row):
    return {key: row[key] for key in ("key", "native_sha256", "trajectory_sha256", "replay_prefix_sha256")}


def check_technical(rows):
    expected = [(role, seed, side) for role in ARMS for seed, side in TECH_KEYS]
    require(len(rows) == 4 and [(r["role"], r["key"]["seed"], r["key"]["side"]) for r in rows] == expected,
            "Exactly four fixed technical games required")
    for row in rows:
        require(row["steps"] == 303 and row["learn_steps"] == 0 and row["initial"] == row["current"]
                and row["replay_rows"] > 0 and row["point_counting_version"] == 2, "Failed technical identity/replay proof")
    require(rows[0]["initial"] == rows[2]["initial"], "Technical initial states differ")
    for c, t in zip(rows[:2], rows[2:]):
        require(paired_row(c) == paired_row(t)
                and all(c[k] == t[k] for k in ("our_wins", "opp_wins", "our_points", "opp_points", "result"))
                and c["actual_nonzero_rows"] == 0 and t["actual_nonzero_rows"] > 0,
                "Technical 101-arm actions/rewards/prefix/outcomes differ or exposure absent")


def save_artifacts(directory, agent, status, a, completed):
    require(status in ("complete", "incomplete"), "Explicit checkpoint status required")
    stem = "final" if status == "complete" else "incomplete"
    checkpoint, replay = directory/(stem+".pth"), directory/(stem+"_replay.npz")
    require(not checkpoint.exists() and not replay.exists(), "Checkpoint/replay already exists")
    payload = dict(q=agent.q.state_dict(), target_q=agent.target_q.state_dict(), opt=agent.opt.state_dict(),
        cfg=agent.cfg.to_dict(), feature_dim=101, n_actions=6, ensemble=[], ensemble_dims=[],
        env_steps=agent.env_steps, learn_steps=agent.learn_steps,
        threat_warmstart=dict(profile=PROFILE, status=status, role=agent.role, source=a["source"],
                              completed_games=completed, learning_audit=dict(agent.learning_audit), component_index=18))
    require(all(torch.isfinite(t).all() for values in (payload["q"], payload["target_q"]) for t in values.values()),
            "Nonfinite end weights")
    with checkpoint.open("xb") as stream: torch.save(payload, stream)
    agent.buffer.save(replay)
    return hashes((checkpoint, replay))


def prefill_proof(directory, agent, rows, initial):
    require(len(rows) == 40 and not agent.learn_enabled, "Prefill boundary differs")
    replay = directory/"prefill_replay.npz"
    require(not replay.exists(), "Prefill replay already exists")
    agent.buffer.save(replay)
    identity = replay_identity(agent.buffer)
    return dict(status="prefill_ready", profile=PROFILE, role=agent.role, games=40,
        initial=initial, current=model_identity(agent), env_steps=agent.env_steps, learn_steps=agent.learn_steps,
        replay_size=len(agent.buffer), replay_prefix_sha256=identity["prefix"], replay_full_sha256=identity["full"],
        replay_file=str(replay), replay_sha256=digest(replay),
        public_nonzero_rows=sum(r["public_nonzero_rows"] for r in rows),
        actual_nonzero_rows=sum(r["actual_nonzero_rows"] for r in rows), paired_rows=[paired_row(r) for r in rows])


def validate_prefill_file(path):
    proof = json.loads(Path(path).read_text())
    require(digest(proof["replay_file"]) == proof["replay_sha256"], "Prefill replay hash differs")
    with np.load(proof["replay_file"], allow_pickle=False) as archive:
        data = {k: archive[k] for k in archive.files}
    n = proof["replay_size"]
    require(set(data) == {"s", "ns", "a", "r", "done", "mask"}
            and data["s"].shape == data["ns"].shape == (n, 101) and data["mask"].shape == (n, 6)
            and all(np.isfinite(v).all() for v in data.values()), "Invalid saved prefill replay")
    require(state_sha256(data) == proof["replay_full_sha256"]
            and state_sha256(dict(data, s=data["s"][:, :79], ns=data["ns"][:, :79])) == proof["replay_prefix_sha256"],
            "Actual saved replay identity differs")
    if proof["role"] == "control": require(not np.any(data["s"][:, 79:]) and not np.any(data["ns"][:, 79:]), "Saved control tail nonzero")
    else: require(np.any(data["s"][:, 79:]), "Saved threat replay lacks exposure")
    return proof


def approve_prefill(a, sha, review_path, review_sha):
    directory = Path(a["out"])
    paths = {role: directory/role/"prefill.json" for role in ARMS}
    pins = {role: digest(path) for role, path in paths.items()}
    proofs = [validate_prefill_file(paths[role]) for role in ARMS]
    require(all(p["source"] == a["source"] and p["admission_sha256"] == sha
                and p["config"] == a["config"] for p in proofs), "Prefill source/admission/config differs")
    compare_prefills(*proofs)
    state = json.loads((directory/"state.json").read_text())
    require(state.get("status") == "running" and set(state.get("active", [])) == set(ARMS)
            and state.get("admission_sha256") == sha, "Both original workers must wait at this boundary")
    review_path = Path(review_path).resolve()
    require(digest(review_path) == review_sha, "Root review hash differs")
    review = json.loads(review_path.read_text())
    require(review.get("status") == "PASS" and review.get("profile") == PROFILE
            and review.get("source") == a["source"] and review.get("admission_sha256") == sha
            and review.get("prefill_sha256") == pins, "Root review does not accept these actual prefills")
    release = dict(profile=PROFILE, status="approved", admission_sha256=sha, prefill_sha256=pins,
                   root_review=str(review_path), root_review_sha256=review_sha)
    write(directory/"release.json", release)
    return release


def wait_release(a, sha, guard):
    directory = Path(a["out"]); path = directory/"release.json"
    while not path.exists():
        guard(); time.sleep(1)
    pins = {role: digest(directory/role/"prefill.json") for role in ARMS}
    release = validate_release(json.loads(path.read_text()), sha, pins)
    require(digest(release["root_review"]) == release["root_review_sha256"], "Accepted Root review changed")
    guard.release_sha = digest(path)
    guard()
    return release


def run_worker(a, path, sha, state_path, role):
    from scripts.experiment import limit_threads
    limit_threads()
    stop = [False]
    handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    for sig in handlers: signal.signal(sig, lambda *_: stop.__setitem__(0, True))
    guard = WorkerGuard(a, path, sha, state_path, role, stop)
    # spawn_owned writes the registration immediately after fork; never load a net before it exists.
    deadline = time.monotonic()+15
    expected_jobs = {"technical"} if a["stage"] == "technical" else set(ARMS)
    while not expected_jobs <= set(json.loads(Path(state_path).read_text()).get("jobs", {})):
        require(not stop[0] and not Path(a["stop_file"]).exists() and time.monotonic() < deadline,
                "Initial worker registration missing/STOP")
        time.sleep(.05)
    guard()
    directory = Path(a["out"])/role; directory.mkdir(exist_ok=False)
    agent = None; env = None; rows = []
    try:
        initial_weights = load_initial(a)
        from luxai_s3.wrappers import LuxAIS3GymEnv
        env = LuxAIS3GymEnv(numpy_output=True)
        with (directory/"games.jsonl").open("x") as stream:
            roles = ARMS if role == "technical" else (role,)
            for feature_role in roles:
                agent = make_learner(a, initial_weights, feature_role)
                initial = model_identity(agent)
                write(directory/(feature_role+"_initial.json"), dict(initial=initial, config=a["config"],
                    env_steps=agent.env_steps, learn_steps=agent.learn_steps, replay_size=len(agent.buffer)))
                selected = ([dict(phase="technical", game=i, seed=seed, side=side, opponent="solution92")
                             for i, (seed, side) in enumerate(TECH_KEYS)] if role == "technical" else rollout_plan())
                for key in selected:
                    guard()
                    row = play_one(agent, key, env)
                    if role == "technical": row.update(initial=initial, current=model_identity(agent))
                    stream.write(json.dumps(plain(row), allow_nan=False)+"\n"); stream.flush(); os.fsync(stream.fileno())
                    rows.append(row)
                    guard()  # STOP/Quota/signals finish the current game before incomplete saving.
                    if role != "technical" and key["phase"] == "prefill" and key["game"] == 39:
                        proof = prefill_proof(directory, agent, rows, initial)
                        proof.update(source=a["source"], admission_sha256=sha, config=a["config"])
                        write(directory/"prefill.json", proof)
                        wait_release(a, sha, guard)
                        agent.learn_enabled = True
        if role == "technical":
            check_technical(rows)
            files = hashes(p for p in directory.iterdir() if p.is_file())
        else:
            require(len(rows) == 440 and agent.env_steps == 193320 and agent.learn_steps > 0
                    and agent.learning_audit["sampled_batches"] == agent.learn_steps, "Incomplete final learner")
            if role == "control": require(not torch.count_nonzero(agent.q.body[0].weight[:, 79:]), "Control columns changed")
            else:
                require(agent.learning_audit["sampled_exposed_rows"] > 0 and agent.learning_audit["tail_gradient_steps"] > 0
                        and torch.count_nonzero(agent.q.body[0].weight[:, 79:]) > 0, "Threat arm did not learn exposed features")
            save_artifacts(directory, agent, "complete", a, len(rows))
            files = hashes(p for p in directory.iterdir() if p.is_file())
        guard()
        receipt = dict(status="complete", profile=PROFILE, stage=a["stage"], role=role, source=a["source"],
            config=a["config"], admission_sha256=sha, command=guard.command, games=rows, files=files,
            final_identity=model_identity(agent), learning_audit=dict(agent.learning_audit),
            final_replay=replay_identity(agent.buffer),
            release_sha256=guard.release_sha, no_strength_claim=True)
        write(directory/"receipt.json", receipt)
        return receipt
    except BaseException as exc:
        files = {}
        if agent is not None:
            try: files = save_artifacts(directory, agent, "incomplete", a, len(rows))
            except BaseException as save_error: files = {"save_error": f"{type(save_error).__name__}: {save_error}"}
        write(directory/"incomplete.json", dict(status="incomplete", profile=PROFILE, role=role,
              completed_games=len(rows), error=f"{type(exc).__name__}: {exc}", artifacts=files, eligible=False))
        raise
    finally:
        try:
            if env is not None: env.close()
        finally:
            for sig, handler in handlers.items(): signal.signal(sig, handler)


def validate_final_receipt(path, a, sha, role):
    """Inspect only completed artifacts; call after both training workers have exited."""
    path = Path(path); directory = path.parent
    receipt = json.loads(path.read_text())
    require(receipt.get("status") == "complete" and receipt.get("profile") == PROFILE
            and receipt.get("role") == role and receipt.get("source") == a["source"]
            and receipt.get("config") == a["config"] and receipt.get("admission_sha256") == sha,
            "Incomplete or mismatched final receipt")
    require(hashes(receipt["files"]) == receipt["files"], "End files changed")
    rows = [json.loads(line) for line in (directory/"games.jsonl").read_text().splitlines()]
    require(rows == receipt["games"] and [r["key"] for r in rows] == rollout_plan(), "Final 440-game chronology differs")
    prefill = validate_prefill_file(directory/"prefill.json")
    require(prefill["initial"] == prefill["current"] and prefill["paired_rows"] == [paired_row(r) for r in rows[:40]],
            "Preserved prefill differs")
    release_path = Path(a["out"])/"release.json"
    require(digest(release_path) == receipt["release_sha256"], "Final Root release changed")
    pins = {arm: digest(Path(a["out"])/arm/"prefill.json") for arm in ARMS}
    validate_release(json.loads(release_path.read_text()), sha, pins)
    cp = torch.load(directory/"final.pth", map_location="cpu", weights_only=True)
    require(cp["cfg"] == a["config"] and cp["feature_dim"] == 101 and cp["n_actions"] == 6
            and not cp["ensemble"] and not cp["ensemble_dims"] and cp["env_steps"] == 193320
            and cp["learn_steps"] == rows[-1]["learn_steps"] > 0
            and cp["threat_warmstart"]["status"] == "complete" and cp["threat_warmstart"]["role"] == role
            and cp["threat_warmstart"]["completed_games"] == 440, "End checkpoint counters/role differ")
    require({"q": state_sha256(cp["q"]), "target": state_sha256(cp["target_q"]),
             "optimizer": state_sha256(cp["opt"])} == receipt["final_identity"], "Actual final tensors/optimizer differ")
    require(cp["opt"]["state"] and all(int(v["step"]) == cp["learn_steps"] for v in cp["opt"]["state"].values()),
            "Actual Adam update counts differ")
    for key in ("q", "target_q"):
        require(cp[key]["body.0.weight"].shape == (256, 101)
                and all(torch.isfinite(v).all() for v in cp[key].values()), "Invalid final model tensor")
        require(bool(torch.count_nonzero(cp[key]["body.0.weight"][:, 79:])) == (role == "threat"),
                "Final added-column learning contrast missing")
    audit = receipt["learning_audit"]
    require(audit["sampled_batches"] == cp["learn_steps"] and cp["threat_warmstart"]["learning_audit"] == audit,
            "Saved actual learning audit differs")
    require((audit.get("sampled_exposed_rows", 0) > 0 and audit.get("tail_gradient_steps", 0) > 0)
            if role == "threat" else audit.get("sampled_exposed_rows", 0) == audit.get("tail_gradient_steps", 0) == 0,
            "Actual sampled-feature/gradient contrast missing")
    with np.load(directory/"final_replay.npz", allow_pickle=False) as archive:
        replay = {k: archive[k] for k in archive.files}
    require(replay["s"].shape == replay["ns"].shape == (receipt["final_replay"]["size"], 101)
            and all(np.isfinite(v).all() for v in replay.values())
            and state_sha256(replay) == receipt["final_replay"]["full"]
            and state_sha256(dict(replay, s=replay["s"][:, :79], ns=replay["ns"][:, :79])) == receipt["final_replay"]["prefix"],
            "Saved final replay differs")
    require(not np.any(replay["s"][:, 79:]) and not np.any(replay["ns"][:, 79:])
            if role == "control" else np.any(replay["s"][:, 79:]), "Saved final replay feature contrast missing")
    return dict(status="PASS", role=role, games=440, learn_steps=cp["learn_steps"], receipt_sha256=digest(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    worker = sub.add_parser("worker")
    approve = sub.add_parser("approve-prefill")
    for p in (worker, approve):
        p.add_argument("--admission", type=Path, required=True)
        p.add_argument("--admission-sha", required=True)
    worker.add_argument("--owner-state", type=Path, required=True)
    worker.add_argument("--role", choices=("technical", *ARMS), required=True)
    approve.add_argument("--review", type=Path, required=True)
    approve.add_argument("--review-sha", required=True)
    args = parser.parse_args()
    stage = "technical" if args.command == "worker" and args.role == "technical" else "training"
    a = admission(args.admission, args.admission_sha, stage)
    if args.command == "worker": run_worker(a, args.admission.resolve(), args.admission_sha, args.owner_state.resolve(), args.role)
    else: approve_prefill(a, args.admission_sha, args.review, args.review_sha)


if __name__ == "__main__": main()
