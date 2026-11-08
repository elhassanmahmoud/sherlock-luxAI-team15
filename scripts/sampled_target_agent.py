"""Experimental submitted-successor TD, external TEXT PREPARATION ONLY.

No runner, no CLI, no changes to the production Agent_x.  This module and its
synthetic tests have not been imported or executed during the performance freeze.
Labels represent commands submitted to the engine within Core-defined episodes,
not biological identity or guaranteed engine effects.  Historical replay makes
this SARSA-like TD, not strictly on-policy SARSA.  Bundle reload is inspection-only.
"""
from __future__ import annotations

import copy
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from numbers import Integral
from pathlib import Path
from typing import Callable

import numpy as np
import torch
from torch import nn

from agents.sherlock import geometry as geo
from agents.sherlock.main import Agent_x
from agents.sherlock.replay_buffer import ReplayBuffer

MODES = frozenset(("double_dqn", "sampled_successor"))
BASE_ARRAYS = ("s", "a", "r", "ns", "done", "mask")
EXTRA_DTYPES = dict(next_action="int8", episode_id="int32", source_step="int16",
                    match_idx="int8", uid="int8", next_action_env_steps="int64")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, low, high, name):
    require(isinstance(value, Integral) and not isinstance(value, (bool, np.bool_))
            and low <= int(value) <= high, f"Invalid {name}")
    return int(value)


def array(value, shape, dtype, name):
    result = np.asarray(value)
    require(result.shape == shape and result.dtype == np.dtype(dtype), f"Invalid {name} schema")
    if result.dtype.kind == "f":
        require(np.isfinite(result).all(), f"Nonfinite {name}")
    return result


def byte_equal(left, right):
    left, right = np.asarray(left), np.asarray(right)
    return left.dtype == right.dtype and left.shape == right.shape and left.tobytes() == right.tobytes()


def state_hash(value):
    # Existing typed hash; no policy/model construction or random sampling.
    from scripts.experiment import state_sha256
    return state_sha256(value)


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass
class ActionFrame:
    episode_id: int
    match_idx: int
    step: int
    env_steps: int
    native: np.ndarray
    features: dict
    masks: dict
    actions: dict
    observation_hash: str

    @property
    def key(self):
        return (self.episode_id, self.match_idx, self.step)


class SuccessorReplay(ReplayBuffer):
    """Only complete rows enter the ring; one bounded pending capture outside it."""

    def __init__(self, capacity, obs_dim, *, event_sink: Callable | None = None):
        require(int(capacity) > 0 and obs_dim == 79, "Pilot replay requires 79 features")
        super().__init__(capacity, obs_dim)
        for name, dtype in EXTRA_DTYPES.items():
            setattr(self, name, np.full(self.capacity, -1, dtype=dtype))
        self._capture = self._pending = self._attached = None
        self._last_capture = None
        self.event_sink = event_sink
        self.counts = Counter()

    def emit(self, event):
        if self.event_sink is not None:
            self.event_sink(copy.deepcopy(event))

    def assert_idle(self):
        require(self._capture is None and self._pending is None and self._attached is None,
                "Incomplete capture/successor evidence")

    def begin_capture(self, source_rows, meta):
        self.assert_idle()
        require(set(meta) == {"episode_id", "source_step", "match_idx", "next_step"}, "Capture metadata differs")
        meta = dict(meta)
        meta["episode_id"] = integer(meta["episode_id"], 0, 2**31 - 1, "episode_id")
        meta["source_step"] = integer(meta["source_step"], 0, 32766, "source_step")
        meta["match_idx"] = integer(meta["match_idx"], 0, 2, "match_idx")
        require(meta["next_step"] == meta["source_step"] + 1, "Capture successor step differs")
        key = (meta["episode_id"], meta["source_step"])
        require(self._last_capture is None or key > self._last_capture, "Repeated/out-of-order capture")
        require(len(source_rows) <= 16, "Too many captured units")
        expected = []
        for uid, (s, a) in source_rows.items():
            expected.append((integer(uid, 0, 15, "uid"),
                             array(s, (79,), "float32", "source s").copy(),
                             integer(a, 0, 5, "source action")))
        self._capture = dict(meta=meta, expected=expected, rows=[])
        self._last_capture = key

    def push(self, s, a, r, ns, done, next_mask):
        capture = self._capture
        require(capture is not None, "Replay push outside capture")
        index = len(capture["rows"])
        require(index < len(capture["expected"]), "Too many Core pushes")
        uid, expected_s, expected_a = capture["expected"][index]
        s = array(s, (79,), "float32", "s")
        ns = array(ns, (79,), "float32", "ns")
        next_mask = array(next_mask, (6,), "bool", "next_mask")
        require(byte_equal(s, expected_s) and integer(a, 0, 5, "action") == expected_a,
                "Core push differs from submitted source action/state")
        require(float(done) in (0., 1.) and np.isfinite(float(r)), "Invalid reward/terminal flag")
        require(next_mask.any(), "Empty next mask")
        row = dict(s=s.copy(), a=int(a), r=float(r), ns=ns.copy(), done=float(done),
                   mask=next_mask.copy(), uid=uid, next_action=-1, next_action_env_steps=-1,
                   **{k: capture["meta"][k] for k in ("episode_id", "source_step", "match_idx")})
        capture["rows"].append(row)
        self.counts["captured"] += 1
        self.emit(dict(event="capture", identity=[row["episode_id"], row["source_step"], uid],
            match_idx=row["match_idx"], action=row["a"], done=row["done"],
            s_sha256=state_hash(s), ns_sha256=state_hash(ns), mask_sha256=state_hash(next_mask)))

    def finish_capture(self, next_context):
        capture = self._capture
        require(capture is not None and len(capture["rows"]) == len(capture["expected"]),
                "Missing Core replay pushes")
        rows, meta = capture["rows"], capture["meta"]
        if not rows:
            require(next_context is None, "Empty capture must not invent a successor context")
            self._capture = None
            self.counts["empty_captures"] += 1
            return
        require(isinstance(next_context, dict) and next_context.get("step") == meta["next_step"],
                "Missing/stale next context")
        if any(not row["done"] for row in rows):
            require(next_context.get("match_idx") == meta["match_idx"]
                    and next_context.get("match_step") != 0, "Nonterminal row crosses a Core match boundary")
            self._pending = dict(rows=rows, next_key=(meta["episode_id"], meta["match_idx"], meta["next_step"]))
            self._capture = None
        else:
            self._commit(rows, None)
            self._capture = None

    def attach_successor(self, frame):
        if self._pending is None:
            require(self._attached is None, "Orphan successor attachment")
            return
        require(self._attached is None and frame.key == self._pending["next_key"],
                "Missing/repeated/different successor frame")
        clock = integer(frame.env_steps, 0, 2**63 - 1, "successor env_steps")
        labels = {}
        for row in self._pending["rows"]:
            if row["done"]:
                continue
            uid = row["uid"]
            require(uid in frame.features and uid in frame.masks and uid in frame.actions,
                    "Missing Core-defined surviving uid")
            require(byte_equal(row["ns"], frame.features[uid]) and byte_equal(row["mask"], frame.masks[uid]),
                    "Actual successor features/mask differ from captured ns")
            labels[uid] = (integer(frame.actions[uid], 0, 5, "successor action"), clock)
        self._attached = dict(key=frame.key, native=frame.native.copy(), labels=labels)

    def commit_confirmed(self, action, frame_key):
        if self._pending is None:
            require(self._attached is None, "Orphan successor attachment")
            return
        attached = self._attached
        require(attached is not None and tuple(frame_key) == attached["key"]
                and byte_equal(action, attached["native"]), "Unconfirmed successor command")
        rows = [dict(row) for row in self._pending["rows"]]
        for row in rows:
            if not row["done"]:
                row["next_action"], row["next_action_env_steps"] = attached["labels"][row["uid"]]
        self._commit(rows, attached["key"])
        self._pending = self._attached = None

    def _commit(self, rows, successor_key):
        for row in rows:
            require((row["done"] == 1 and row["next_action"] == row["next_action_env_steps"] == -1)
                    or (row["done"] == 0 and 0 <= row["next_action"] <= 5 and row["next_action_env_steps"] >= 0),
                    "Incomplete committed label")
        for row in rows:
            slot = self.pos
            super().push(*(row[name] for name in BASE_ARRAYS))
            for name in EXTRA_DTYPES:
                getattr(self, name)[slot] = row[name]
            self.counts["committed"] += 1
            self.counts["terminal" if row["done"] else "nonterminal"] += 1
            self.emit(dict(event="commit", identity=[row["episode_id"], row["source_step"], row["uid"]],
                successor_key=successor_key if not row["done"] else None, action=row["a"],
                done=row["done"], next_action=row["next_action"],
                next_action_env_steps=row["next_action_env_steps"], ordinal=self.counts["committed"]))

    def sample_with_successor(self, batch_size, rng):
        require(self.size > 0, "Empty replay")
        index = rng.integers(0, self.size, size=batch_size)
        return (*(getattr(self, name)[index] for name in BASE_ARRAYS), self.next_action[index],
                {name: getattr(self, name)[index] for name in EXTRA_DTYPES if name != "next_action"})

    def save(self, path):
        self.assert_idle()
        index = (np.arange(self.size) if self.size < self.capacity
                 else (np.arange(self.size) + self.pos) % self.capacity)
        data = {name: getattr(self, name)[index] for name in (*BASE_ARRAYS, *EXTRA_DTYPES)}
        if not self.size:
            data["mask"] = np.ones((0, 6), dtype=bool)
        np.savez(path, schema_version=np.array(1, dtype=np.int64), **data)

    def read_validated(self, path):
        """Validate the complete serialized input before changing an empty ring."""
        with np.load(path, allow_pickle=False) as stored:
            require(set(stored.files) == {*BASE_ARRAYS, *EXTRA_DTYPES, "schema_version"}, "Replay schema keys differ")
            data = {name: stored[name] for name in stored.files}
        version = array(data.pop("schema_version"), (), "int64", "schema_version")
        require(int(version) == 1, "Unsupported replay schema")
        require(data["a"].ndim == 1, "Invalid action rank")
        n = len(data["a"])
        require(n <= self.capacity, "Replay exceeds capacity")
        for name, dtype in {"s": "float32", "ns": "float32", "a": "int64", "r": "float32",
                            "done": "float32", "mask": "bool", **EXTRA_DTYPES}.items():
            shape = (n, 79) if name in ("s", "ns") else (n, 6) if name == "mask" else (n,)
            array(data[name], shape, dtype, name)
        require(np.isin(data["done"], [0., 1.]).all() and ((data["a"] >= 0) & (data["a"] <= 5)).all(),
                "Invalid action/terminal values")
        terminal = data["done"] == 1
        require(((data["next_action"][terminal] == -1) & (data["next_action_env_steps"][terminal] == -1)).all(),
                "Terminal sentinel differs")
        require(((data["next_action"][~terminal] >= 0) & (data["next_action"][~terminal] <= 5)
                 & (data["next_action_env_steps"][~terminal] >= 0)).all(), "Missing nonterminal labels")
        require(data["mask"].any(axis=1).all(), "Empty serialized next mask")
        for name, maximum in (("episode_id", 2**31 - 1), ("source_step", 32766), ("match_idx", 2), ("uid", 15)):
            require(((data[name] >= 0) & (data[name] <= maximum)).all(), f"Invalid {name}")
        identities = list(zip(data["episode_id"].tolist(), data["source_step"].tolist(), data["uid"].tolist()))
        require(len(set(identities)) == n, "Duplicate transition identities")
        times = [(episode, step) for episode, step, _ in identities]
        require(times == sorted(times), "Replay chronology differs")
        return data

    def install_validated(self, data):
        self.assert_idle()
        require(self.size == self.pos == 0, "Load requires empty replay")
        n = len(data["a"])
        if n:
            self._ensure_mask(6)
            for name in (*BASE_ARRAYS, *EXTRA_DTYPES):
                getattr(self, name)[:n] = data[name]
            self._last_capture = (int(data["episode_id"][-1]), int(data["source_step"][-1]))
        self.size, self.pos = n, n % self.capacity
        self.counts["loaded"] = n
        return n

    def load(self, path):
        self.assert_idle()
        require(self.size == self.pos == 0, "Load requires empty replay")
        return self.install_validated(self.read_validated(path))


def bootstrap_targets(online, target, reward, done, mask, next_action, gamma):
    require(online.ndim == 2 and online.shape[1] == 6 and target.shape == online.shape,
            "Invalid Q shapes")
    n = len(online)
    require(reward.shape == done.shape == (n, 1) and mask.shape == (n, 6)
            and mask.dtype == torch.bool and next_action.shape == (n,), "Invalid target inputs")
    require(all(bool(torch.isfinite(value).all()) for value in (online, target, reward, done)), "Nonfinite target input")
    require(bool(((done == 0) | (done == 1)).all()) and bool(mask.any(dim=1).all()), "Invalid done/mask")
    live = done[:, 0] == 0
    require(next_action.dtype in (torch.int8, torch.int16, torch.int32, torch.int64)
            and bool(((next_action[live] >= 0) & (next_action[live] <= 5)).all())
            and bool((next_action[~live] == -1).all()), "Missing/invalid successor label")
    best = online.masked_fill(~mask, -float("inf")).argmax(dim=1, keepdim=True)
    ddqn_q = torch.nan_to_num(target.gather(1, best), neginf=0.0)
    sampled_q = torch.zeros_like(ddqn_q)
    # Never gather terminal -1; final commands outside the proposal mask remain labels.
    sampled_q[live] = target[live].gather(1, next_action[live].long().unsqueeze(1))
    return (reward + (1.0 - done) * gamma * ddqn_q,
            reward + (1.0 - done) * gamma * sampled_q, best)


class SampledTargetAgent(Agent_x):
    def __init__(self, *args, bootstrap_mode="double_dqn", event_sink=None, **kwargs):
        require(bootstrap_mode in MODES, "Unknown bootstrap mode")
        self.bootstrap_mode = bootstrap_mode
        self._episode = self._bound_episode = self._frame = None
        self._episode_complete = True
        self._faulted = self._inspection_only = False
        self._last_episode_id = -1
        self._last_act_step = None
        self.bootstrap_stats = Counter()
        self._initializing = True
        super().__init__(*args, **kwargs)
        self._initializing = False
        require(self.feat_dim == 79 and self.n_actions == 6 and self.cfg.double_dqn
                and not self.cfg.frozen and not self.extra_q and self.cnn_policy is None,
                "Pilot requires unfrozen 79-feature six-action single Double-DQN")
        require(len(self.buffer) == 0, "Constructor must not inherit replay")
        del self.buffer  # release base arrays before allocating the enlarged ring
        self.buffer = SuccessorReplay(self.cfg.buffer_capacity, self.feat_dim, event_sink=event_sink)
        self.autosave_on_terminate = False

    def assert_boundary(self):
        require(not self._faulted and self._frame is None and self._episode_complete,
                "Not a clean completed-game boundary")
        self.buffer.assert_idle()

    def bind_episode(self, meta):
        self.assert_boundary()
        require(not self._inspection_only and self._bound_episode is None, "Inspection-only/already bound agent")
        require(set(meta) == {"episode_id", "seed", "side", "phase", "game", "opponent"}, "Episode fields differ")
        episode = integer(meta["episode_id"], 0, 2**31 - 1, "episode_id")
        require(episode > self._last_episode_id and meta["side"] in ("player_0", "player_1")
                and meta["phase"] in ("prefill", "train") and isinstance(meta["opponent"], str), "Invalid episode binding")
        integer(meta["seed"], 0, 2**63 - 1, "seed")
        integer(meta["game"], 0, 2**31 - 1, "game")
        self._bound_episode = dict(meta)

    def new_game(self, player=None):
        self.assert_boundary()
        require(not self._inspection_only and self._bound_episode is not None, "Bind an episode before new_game")
        require((player or self.player) == self._bound_episode["side"], "Episode side differs")
        super().new_game(player)
        self._episode, self._bound_episode = self._bound_episode, None
        self._last_episode_id = self._episode["episode_id"]
        self._episode_complete = False
        self._last_act_step = None
        self.buffer.emit(dict(event="episode", **self._episode))

    def set_to_eval_mode(self):
        self.assert_boundary()
        super().set_to_eval_mode()

    def set_to_train_mode(self):
        self.assert_boundary()
        require(not self._inspection_only, "Bundle reload is not study resume")
        super().set_to_train_mode()

    def _act_est(self, step, obs):
        try:
            require(not self._faulted and not self._inspection_only and self.training
                    and self._episode is not None and not self._episode_complete and self._frame is None,
                    "Unexpected act lifecycle")
            observed_step = int(np.asarray(obs["steps"]))
            require(step == observed_step and (self._last_act_step is None or observed_step == self._last_act_step + 1),
                    "Repeated/skipped observation step")
            clock = self.env_steps
            output = super()._act_est(step, obs)
            require(self.env_steps == clock, "act changed env_steps")
            native = np.asarray(output)
            require(native.ndim == 2 and native.shape[1] == 3 and native.shape[0] <= 16
                    and native.dtype.kind in "iu", "Invalid native action array")
            ids = list(self._prev_feats)
            require(set(ids) == set(self._prev_actions) == set(self._prev_masks), "Act feature/action/mask identities differ")
            context = self._prev_ctx
            if ids:
                require(context is not None and context["step"] == observed_step, "Missing source context")
            match = int(context["match_idx"] if context is not None else self.belief.match_idx)
            actions, features, masks = {}, {}, {}
            for uid in ids:
                integer(uid, 0, min(15, len(native) - 1), "acted uid")
                canonical = integer(self._prev_actions[uid], 0, 5, "canonical action")
                expected = geo.mirror_dir(canonical) if self.belief.mirrored and canonical < 5 else canonical
                require(int(native[uid, 0]) == expected, "Native/canonical final action differs")
                if canonical < 5:
                    require((native[uid, 1:] == 0).all(), "Movement carries SAP displacement")
                else:
                    require(uid in self._sap_hits and (np.abs(native[uid, 1:]) <= context["sap_range"]).all(),
                            "SAP output lacks its Core target evidence")
                actions[uid] = canonical
                features[uid] = array(self._prev_feats[uid], (79,), "float32", "acted features").copy()
                masks[uid] = array(self._prev_masks[uid], (6,), "bool", "acted mask").copy()
            frame = ActionFrame(self._episode["episode_id"], match, observed_step, clock,
                                native.copy(), features, masks, actions, state_hash(obs))
            self.buffer.attach_successor(frame)
            self._frame, self._last_act_step = frame, observed_step
            self.buffer.emit(dict(event="frame", key=frame.key, env_steps=clock,
                observation_sha256=frame.observation_hash, native=native.tolist(),
                units=[dict(uid=uid, action=actions[uid], features_sha256=state_hash(features[uid]),
                            mask_sha256=state_hash(masks[uid])) for uid in ids]))
            return output
        except BaseException:
            self._faulted = True
            raise

    def _update(self, step, obs, reward, action, terminated, next_obs):
        try:
            frame = self._frame
            require(not self._faulted and frame is not None and step == frame.step
                    and frame.episode_id == self._episode["episode_id"]
                    and frame.observation_hash == state_hash(obs) and byte_equal(action, frame.native)
                    and self.env_steps == frame.env_steps, "Unmatched act/env.step/update")
            next_step = int(np.asarray(next_obs["steps"]))
            require(next_step == frame.step + 1, "Unexpected next observation step")
            self.buffer.commit_confirmed(action, frame.key)
            self.buffer.begin_capture({uid: (frame.features[uid], a) for uid, a in frame.actions.items()},
                dict(episode_id=frame.episode_id, source_step=frame.step, match_idx=frame.match_idx, next_step=next_step))
            super()._update(step, obs, reward, action, terminated, next_obs)
            require(self.env_steps == frame.env_steps + 1, "Parent env_steps increment differs")
            # Matchstep0/empty-UID captures must not consult a missing or stale cache.
            context = self._cache[1] if frame.actions and self._cache is not None else None
            self.buffer.finish_capture(context)
            self.buffer.emit(dict(event="confirmed", key=frame.key, native_sha256=state_hash(action)))
            self._frame = None
            if terminated:
                self._episode_complete = True
                self.assert_boundary()
        except BaseException:
            self._faulted = True
            raise

    def _learn(self):
        require(not self._faulted and not self._inspection_only, "Learning disabled after error/inspection reload")
        c = self.cfg
        s, a, r, ns, done, nmask, next_action, metadata = self.buffer.sample_with_successor(c.batch_size, self.rng)
        dev = self.device
        s = torch.as_tensor(s, device=dev)
        ns = torch.as_tensor(ns, device=dev)
        a = torch.as_tensor(a, device=dev).unsqueeze(1)
        r = torch.as_tensor(r, device=dev).unsqueeze(1)
        done = torch.as_tensor(done, device=dev).unsqueeze(1)
        nmask = torch.as_tensor(nmask, device=dev)
        na = torch.as_tensor(next_action, device=dev)
        q = self.q(s).gather(1, a)
        with torch.no_grad():
            control_y, sampled_y, best = bootstrap_targets(self.q(ns), self.target_q(ns), r, done, nmask, na, c.gamma)
            y = control_y if self.bootstrap_mode == "double_dqn" else sampled_y
            live = done[:, 0] == 0
            ages = self.env_steps - metadata["next_action_env_steps"][done[:, 0].cpu().numpy() == 0]
            require((ages >= 1).all(), "Successor timestamp is not before this update")
            delta = sampled_y - control_y
            self.bootstrap_stats.update(updates=1, nonterminal=int(live.sum()),
                different_index=int((best[:, 0][live] != na[live]).sum()),
                different_target=int((sampled_y != control_y).sum()),
                outside_mask=int((~nmask[live].gather(1, na[live].long().unsqueeze(1))).sum()),
                target_delta_positive=int((delta[live] > 0).sum()),
                target_delta_negative=int((delta[live] < 0).sum()),
                target_delta_sum=float(delta.double().sum()), label_age_sum=int(ages.sum()))
        loss = nn.functional.smooth_l1_loss(q, y)
        require(bool(torch.isfinite(loss)), "Nonfinite loss")
        self.opt.zero_grad(set_to_none=True)
        loss.backward()
        require(all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in self.q.parameters()), "Nonfinite gradients")
        nn.utils.clip_grad_norm_(self.q.parameters(), c.grad_clip)
        self.opt.step()
        require(all(bool(torch.isfinite(p).all()) for p in self.q.parameters()), "Nonfinite learned parameters")
        self.learn_steps += 1
        self.recent_losses.append(float(loss.item()))
        if len(self.recent_losses) > 2000:
            self.recent_losses = self.recent_losses[-2000:]
        if self.learn_steps % c.target_update_every == 0:
            self.target_q.load_state_dict(self.q.state_dict())

    def save_agent(self, path=None):
        self.assert_boundary()
        return super().save_agent(path)

    def save_buffer(self, path):
        self.assert_boundary()
        return self.buffer.save(path)

    def load_buffer(self, path):
        raise ValueError("Pilot replay requires hash-bound load_pilot_bundle; no legacy/resume load")

    def load_agent(self, path):
        require(self._initializing, "After construction use hash-bound load_pilot_bundle")
        return super().load_agent(path)


def save_pilot_bundle(agent, directory, metadata):
    """Boundary-only artifact preparation; does not issue a final study receipt."""
    agent.assert_boundary()
    require(agent._episode is not None and set(metadata) == {"arm", "input_hashes", "rollout_progress"}
            and isinstance(metadata["arm"], str) and isinstance(metadata["input_hashes"], dict)
            and isinstance(metadata["rollout_progress"], dict), "Invalid bundle metadata")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    agent.save_agent(str(directory / "agent.pth"))
    agent.save_buffer(directory / "agent.buffer.npz")
    from scripts.experiment import _global_rng_state
    state = dict(schema_version=1, bootstrap_mode=agent.bootstrap_mode, **copy.deepcopy(metadata),
        config=agent.cfg.to_dict(), env_steps=agent.env_steps, learn_steps=agent.learn_steps,
        episode=copy.deepcopy(agent._episode), replay_size=len(agent.buffer),
        replay_counts=dict(agent.buffer.counts), bootstrap_stats=dict(agent.bootstrap_stats),
        agent_rng_sha256=state_hash(agent.rng.bit_generator.state), global_rng_sha256=state_hash(_global_rng_state()),
        files={name: file_hash(directory / name) for name in ("agent.pth", "agent.buffer.npz")})
    with (directory / "pilot_state.json").open("x") as sink:
        json.dump(state, sink, indent=2, allow_nan=False)
        sink.write("\n")
    return state


def load_pilot_bundle(agent, directory, expected):
    """Validate before mutation; restore for artifact inspection, never study resume."""
    agent.assert_boundary()
    require(agent._episode is None and agent._bound_episode is None and len(agent.buffer) == 0
            and agent.buffer.pos == 0, "Bundle load requires fresh empty lifecycle")
    require(set(expected) == {"arm", "bootstrap_mode", "state_sha256"}, "External arm/mode/state-hash binding required")
    directory = Path(directory)
    require(file_hash(directory / "pilot_state.json") == expected["state_sha256"], "Bundle state hash mismatch")
    state = json.loads((directory / "pilot_state.json").read_text())
    require(isinstance(state, dict) and state.get("schema_version") == 1
            and all(state.get(k) == expected[k] for k in ("arm", "bootstrap_mode"))
            and state.get("bootstrap_mode") == agent.bootstrap_mode and state.get("config") == agent.cfg.to_dict(),
            "Bundle role/mode/config mismatch")
    require(set(state.get("files", {})) == {"agent.pth", "agent.buffer.npz"}
            and all(file_hash(directory / name) == digest for name, digest in state["files"].items()),
            "Bundle file hash mismatch")
    data = agent.buffer.read_validated(directory / "agent.buffer.npz")
    integer(state.get("env_steps"), 0, 2**63 - 1, "bundle env_steps")
    integer(state.get("learn_steps"), 0, 2**63 - 1, "bundle learn_steps")
    require(isinstance(state.get("episode"), dict), "Missing bundle episode")
    last_episode = integer(state["episode"].get("episode_id"), 0, 2**31 - 1, "bundle episode_id")
    live = data["done"] == 0
    require((data["episode_id"] <= last_episode).all()
            and (data["next_action_env_steps"][live] < state["env_steps"]).all(), "Replay provenance exceeds bundle endpoint")
    checkpoint = torch.load(directory / "agent.pth", map_location=agent.device, weights_only=False)
    require(isinstance(checkpoint, dict) and checkpoint.get("cfg") == state["config"]
            and checkpoint.get("feature_dim") == 79 and checkpoint.get("n_actions") == 6
            and checkpoint.get("ensemble") == [] and checkpoint.get("ensemble_dims") == []
            and checkpoint.get("env_steps") == state["env_steps"]
            and checkpoint.get("learn_steps") == state["learn_steps"] and len(data["a"]) == state["replay_size"],
            "Bundle checkpoint/replay metadata mismatch")
    for name in ("q", "target_q"):
        current, saved = getattr(agent, name).state_dict(), checkpoint.get(name)
        require(isinstance(saved, dict) and current.keys() == saved.keys(), "Network keys differ")
        require(all(isinstance(saved[k], torch.Tensor) and saved[k].shape == current[k].shape
                    and saved[k].dtype == current[k].dtype and bool(torch.isfinite(saved[k]).all()) for k in current),
                "Invalid network tensors")
    # Unlike Core.load_agent, optimizer incompatibility must not be swallowed.
    saved_optimizer = checkpoint.get("opt")
    require(isinstance(saved_optimizer, dict) and isinstance(saved_optimizer.get("state"), dict),
            "Missing Adam state mapping")
    if state["learn_steps"] > 0:
        require(all(isinstance(values, dict) and {"step", "exp_avg", "exp_avg_sq"} <= set(values)
                    for values in saved_optimizer["state"].values()), "Missing required Adam fields")
    else:
        require(not saved_optimizer["state"], "Fresh optimizer must have no learned Adam state")
    probe_optimizer = copy.deepcopy(agent.opt)
    probe_optimizer.load_state_dict(saved_optimizer)
    parameters = {parameter for group in probe_optimizer.param_groups for parameter in group["params"]}
    if state["learn_steps"] > 0:
        require(set(probe_optimizer.state) == parameters, "Missing/extra per-parameter Adam state")
    require(all(not isinstance(v, torch.Tensor) or bool(torch.isfinite(v).all())
                for value in probe_optimizer.state.values() for v in value.values()), "Nonfinite optimizer state")
    require(all(group["lr"] == agent.cfg.lr for group in probe_optimizer.param_groups), "Optimizer learning rate differs")
    for parameter, values in probe_optimizer.state.items():
        require(set(values) <= {"step", "exp_avg", "exp_avg_sq", "max_exp_avg_sq"}, "Unexpected Adam state")
        step = values["step"]
        require(isinstance(step, torch.Tensor) and step.ndim == 0 and bool(torch.isfinite(step))
                and 0 <= step.item() == state["learn_steps"], "Adam step differs from learned progress")
        for name in ("exp_avg", "exp_avg_sq", "max_exp_avg_sq"):
            if name in values:
                require(isinstance(values[name], torch.Tensor) and values[name].shape == parameter.shape
                        and values[name].dtype == parameter.dtype,
                        "Adam moment shape/dtype differs")
    del probe_optimizer
    agent.q.load_state_dict(checkpoint["q"], strict=True)
    agent.target_q.load_state_dict(checkpoint["target_q"], strict=True)
    agent.opt.load_state_dict(checkpoint["opt"])
    agent.buffer.install_validated(data)
    agent.env_steps, agent.learn_steps = state["env_steps"], state["learn_steps"]
    agent._inspection_only = True
    agent.set_to_eval_mode()
    return state
