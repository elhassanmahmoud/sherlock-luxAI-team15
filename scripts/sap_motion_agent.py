"""Eval-only SAP prototype with a public, per-game relative motion model.

Counts describe observed UID trajectories, not guaranteed unit identities. Other
visible enemies are assumed stationary for the score comparison. The two-sigma
margin is a heuristic selection rule, not a calibrated confidence interval.
"""
import math

import numpy as np

from agents.sherlock import geometry as geo
from agents.sherlock.main import Agent_x
from scripts.sap_leading_agent import SapLeadingAgent


class SapMotionAgent(SapLeadingAgent):
    def __init__(self, player, agent_path=None, name="SAP-motion prototype", cfg=None,
                 train=False, seed=None, *, lead_enabled=False):
        super().__init__(player, agent_path, name, cfg, train, seed,
                         lead_enabled=lead_enabled)

    def _reset_episode_state(self):
        super()._reset_episode_state()
        self._motion_history = []
        # One opponent team per game; new_game also resets these on a side swap.
        self.motion_counts = np.zeros(5, dtype=np.int64)

    @staticmethod
    def _relative_vectors(direction):
        dx, dy = direction
        return ((dx, dy), (-dy, dx), (-dx, -dy), (dy, -dx), (0, 0))

    @staticmethod
    def _consecutive(previous, current):
        return (previous[0]+1 == current[0] and previous[1]+1 == current[1]
                and previous[2:4] == current[2:4])

    def _observe_motion(self, current, move_cost):
        """Label only the just-completed t-1 -> t movement; never forecast labels."""
        history = self._motion_history
        if history and not self._consecutive(history[-1], current):
            history.clear()
        previous = history[-1] if history else None
        if len(history) == 2:
            older = history[0]
            for uid, (position, energy) in current[4].items():
                if uid not in older[4] or uid not in previous[4]:
                    continue
                origin, _ = older[4][uid]
                last, prior_energy = previous[4][uid]
                direction = last[0]-origin[0], last[1]-origin[1]
                movement = position[0]-last[0], position[1]-last[1]
                if (abs(direction[0])+abs(direction[1]) != 1
                        or abs(movement[0])+abs(movement[1]) > 1
                        or not math.isfinite(prior_energy) or not math.isfinite(energy)
                        or prior_energy < 0 or energy < 0 or prior_energy < move_cost):
                    continue
                label = self._relative_vectors(direction).index(movement)
                self.motion_counts[label] += 1
                self.leading_stats["motion_labels"] += 1
                name = ("forward", "right", "backward", "left", "stay")[label]
                self.leading_stats["motion_"+name] += 1
        history.append(current)
        del history[:-2]
        self._leading_previous = current
        return previous

    def _score_candidate(self, ctx, candidate, sensor, drop):
        old, new = candidate["old_center"], candidate["new_center"]
        direction = new[0]-old[0], new[1]-old[1]
        positions, blocked, unknown = [], [], []
        for kind, (dx, dy) in enumerate(self._relative_vectors(direction)):
            position = old[0]+dx, old[1]+dy
            in_bounds = 0 <= position[0] < ctx["W"] and 0 <= position[1] < ctx["H"]
            if not in_bounds or (sensor[position] and not ctx["passable"][position]):
                position = old
                blocked.append(kind)
            elif not sensor[position]:
                # Unknown terrain remains a model assumption, not a known obstacle.
                unknown.append(kind)
            positions.append(position)

        def weight(center, position):
            distance = max(abs(center[0]-position[0]), abs(center[1]-position[1]))
            return 1.0 if distance == 0 else float(drop) if distance == 1 else 0.0

        gains = np.array([weight(new, p)-weight(old, p) for p in positions])
        other_gain = sum(weight(new, p)-weight(old, p)
                         for uid, p, energy in zip(ctx["enemy_vis_ids"], ctx["enemy_coords"],
                                                   ctx["enemy_energies"])
                         if int(uid) != candidate["enemy_uid"]
                         and math.isfinite(float(energy)) and energy >= 0)
        count = int(self.motion_counts.sum())
        mass = count+5
        probabilities = (self.motion_counts+1)/mass
        focus_mean = float(probabilities @ gains)
        mean = float(other_gain+focus_mean)
        variance = max(float((probabilities @ (gains*gains)-focus_mean**2)/(mass+1)), 0.0)
        return dict(sample_count=count, counts=tuple(map(int, self.motion_counts)),
                    probabilities=tuple(map(float, probabilities)),
                    focus_gains=tuple(map(float, gains)), other_gain=float(other_gain),
                    mean=mean, variance=variance, lower_bound=mean-2*math.sqrt(variance),
                    next_positions=tuple(positions), blocked_classes=tuple(blocked),
                    unknown_classes=tuple(unknown))

    def _act(self, step, obs):
        if self.training:
            raise RuntimeError("SAP-motion prototype is eval only")
        # Bypass the parent's unconditional leading hook. The original core runs
        # exactly once; original _act_est will remember the final native command.
        actions = Agent_x._act(self, step, obs)
        self.leading_last = None
        if not self.lead_enabled:
            self._motion_history.clear()
            self._leading_previous = None
            return actions

        stats = self.leading_stats
        stats["calls"] += 1
        sap_ids = np.flatnonzero(actions[:, 0] == geo.SAP).tolist()
        stats["sap_total"] += len(sap_ids)
        sid, ms = int(np.asarray(obs["steps"])), int(np.asarray(obs["match_steps"]))
        if ms == 0:
            self._motion_history.clear()
            self._leading_previous = None
            stats["reset_calls"] += 1
            stats["excluded_reset"] += len(sap_ids)
            return actions
        cache = self._cache
        if (cache is None or cache[0] != sid or cache[1]["step"] != sid
                or cache[1]["match_step"] != ms or self._prev_ctx is not cache[1]):
            self._motion_history.clear()
            self._leading_previous = None
            stats["excluded_cache"] += len(sap_ids)
            return actions
        ctx = cache[1]
        mirrored = bool(self.belief.mirrored)
        current = (sid, ms, int(ctx["match_idx"]), mirrored,
                   {int(uid): (tuple(map(int, position)), float(energy))
                    for uid, position, energy in zip(ctx["enemy_vis_ids"],
                                                    ctx["enemy_coords"], ctx["enemy_energies"])})
        previous = self._observe_motion(current, ctx["move_cost"])
        sensor = np.asarray(obs["sensor_mask"], dtype=bool)
        if mirrored:
            sensor = geo.mirror_map(sensor)
        candidates = []
        for uid in sap_ids:
            reason, candidate = self._candidate(ctx, uid, actions[uid], sensor, previous, current)
            if reason:
                stats["excluded_"+reason] += 1
            else:
                candidates.append(candidate)
        stats["public_eligible_saps"] += len(candidates)
        if not candidates:
            return actions
        c = self.cfg
        estimator_active = (c.nebula_avoid or c.dodge_auto or c.sap_dropoff_est
                            or c.art_splash or c.sap_still_splash)
        drop = self.param_est.dropoff(default=1.0, min_conf=0.9) if estimator_active else 1.0
        if not (0 <= drop < 1):
            stats["excluded_parameter"] += len(candidates)
            return actions
        if int(self.motion_counts.sum()) < 32:
            stats["excluded_samples"] += len(candidates)
            return actions
        eligible = []
        for candidate in candidates:
            score = self._score_candidate(ctx, candidate, sensor, drop)
            if score["lower_bound"] > 0:
                eligible.append(dict(candidate, **score))
            else:
                stats["excluded_gain"] += 1
        stats["eligible_saps"] += len(eligible)
        if not eligible:
            return actions
        stats["eligible_steps"] += 1
        stats["capped_eligible_saps"] += len(eligible)-1
        chosen = eligible[0]  # flatnonzero above orders shooters by ascending UID.
        uid, target = chosen["uid"], chosen["new_center"]
        origin = ctx["ally_pos"][uid]
        dx, dy = int(target[0]-origin[0]), int(target[1]-origin[1])
        if mirrored:
            dx, dy = geo.mirror_delta(dx, dy)
        actions[uid, 1:] = dx, dy
        # Preserve the original visible-3x3 bookkeeping convention, including its
        # energy handling, even though the motion score excludes negative energy.
        new_hits = int((np.max(np.abs(ctx["enemy_coords"]-target), axis=1) <= 1).sum())
        old_hits = self._sap_hits[uid]
        self._sap_hits[uid] = new_hits
        self.ep_stats["sap_hits_est"] += int(new_hits > 0)-int(old_hits > 0)
        self._sap_unknown.discard(uid)
        stats["changes"] += 1
        self.leading_last = dict(chosen, step=sid, match_step=ms, match_idx=current[2],
                                 dropoff=float(drop), native_action=tuple(map(int, actions[uid])))
        return actions
