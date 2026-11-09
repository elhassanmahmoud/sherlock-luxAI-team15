"""Eval-only public SAP-leading hook; no core changes or second act call.

leading_stats are per-game cumulative diagnostics. Each final SAP either has
one exclusion reason, is eligible but capped, or is the single changed command.
They never affect selection. Public history contains copied immutable values.
"""
from collections import Counter
import math

import numpy as np

from agents.sherlock import geometry as geo
from agents.sherlock.main import Agent_x


class SapLeadingAgent(Agent_x):
    def __init__(self, player, agent_path=None, name="SAP-leading prototype", cfg=None,
                 train=False, seed=None, *, lead_enabled=False):
        if train:
            raise ValueError("SAP-leading prototype is eval only")
        self.lead_enabled = bool(lead_enabled)
        super().__init__(player, agent_path, name, cfg, train, seed)
        self.autosave_on_terminate = False
        self.learn_enabled = False

    def _reset_episode_state(self):
        super()._reset_episode_state()
        self._leading_previous = None
        self.leading_stats = Counter()
        self.leading_last = None

    def set_to_train_mode(self):
        raise RuntimeError("SAP-leading prototype is eval only")

    def update(self, *args, **kwargs):
        raise RuntimeError("SAP-leading prototype cannot update")

    def _act(self, step, obs):
        if self.training:
            raise RuntimeError("SAP-leading prototype is eval only")
        actions = super()._act(step, obs)
        self.leading_last = None
        if not self.lead_enabled:
            self._leading_previous = None
            return actions

        stats = self.leading_stats
        stats["calls"] += 1
        sap_ids = np.flatnonzero(actions[:, 0] == geo.SAP).tolist()
        stats["sap_total"] += len(sap_ids)
        sid, ms = int(np.asarray(obs["steps"])), int(np.asarray(obs["match_steps"]))
        if ms == 0:
            self._leading_previous = None
            stats["reset_calls"] += 1
            stats["excluded_reset"] += len(sap_ids)
            return actions
        cache = self._cache
        if (cache is None or cache[0] != sid or cache[1]["step"] != sid
                or cache[1]["match_step"] != ms or self._prev_ctx is not cache[1]):
            self._leading_previous = None
            stats["excluded_cache"] += len(sap_ids)
            return actions
        ctx = cache[1]
        mirrored = bool(self.belief.mirrored)
        previous = self._leading_previous
        current = (sid, ms, int(ctx["match_idx"]), mirrored,
                   {int(uid): (tuple(map(int, position)), float(energy))
                    for uid, position, energy in zip(ctx["enemy_vis_ids"],
                                                    ctx["enemy_coords"], ctx["enemy_energies"])})
        self._leading_previous = current
        sensor = np.asarray(obs["sensor_mask"], dtype=bool)
        if mirrored:
            sensor = geo.mirror_map(sensor)
        candidates = []
        for uid in sap_ids:  # flatnonzero is sorted: smallest eligible UID wins.
            reason, candidate = self._candidate(ctx, uid, actions[uid], sensor, previous, current)
            if reason:
                stats["excluded_" + reason] += 1
            else:
                candidates.append(candidate)
        stats["public_eligible_saps"] += len(candidates)
        if not candidates:
            return actions

        # Do not invent an additional observe path for configurations unlike V14.
        # These are exactly the eval branches enabling original _act_est.observe.
        c = self.cfg
        estimator_active = (c.nebula_avoid or c.dodge_auto or c.sap_dropoff_est
                            or c.art_splash or c.sap_still_splash)
        drop = self.param_est.dropoff(default=1.0, min_conf=0.9) if estimator_active else 1.0
        if not (0 <= drop < 1):
            stats["excluded_parameter"] += len(candidates)
            return actions
        stats["eligible_saps"] += len(candidates)
        stats["eligible_steps"] += 1
        stats["capped_eligible_saps"] += len(candidates) - 1
        chosen = candidates[0]
        uid = chosen["uid"]
        target = chosen["new_center"]
        origin = ctx["ally_pos"][uid]
        dx, dy = int(target[0]-origin[0]), int(target[1]-origin[1])
        if mirrored:
            dx, dy = geo.mirror_delta(dx, dy)
        actions[uid, 1:] = dx, dy
        # Same convention as _best_sap_target: all visible units in the 3x3.
        new_hits = int((np.max(np.abs(ctx["enemy_coords"] - target), axis=1) <= 1).sum())
        old_hits = self._sap_hits[uid]
        self._sap_hits[uid] = new_hits
        self.ep_stats["sap_hits_est"] += int(new_hits > 0) - int(old_hits > 0)
        self._sap_unknown.discard(uid)
        stats["changes"] += 1
        self.leading_last = dict(chosen, step=sid, match_step=ms, match_idx=current[2],
                                 dropoff=float(drop), native_action=tuple(map(int, actions[uid])))
        # Original _act_est now remembers this native command exactly once.
        return actions

    @staticmethod
    def _candidate(ctx, uid, action, sensor, previous, current):
        def excluded(reason):
            return reason, None
        if uid not in ctx["ally_ids"]:
            return excluded("own_missing")
        if not (math.isfinite(float(ctx["ally_ene"][uid]))
                and ctx["ally_ene"][uid] >= ctx["sap_cost"]):
            return excluded("own_energy")
        dx, dy = map(int, action[1:])
        if current[3]:
            dx, dy = geo.mirror_delta(dx, dy)
        x, y = map(int, ctx["ally_pos"][uid])
        old = (x+dx, y+dy)
        def legal_center(p):
            return (0 <= p[0] < ctx["W"] and 0 <= p[1] < ctx["H"]
                    and max(abs(p[0]-x), abs(p[1]-y)) <= ctx["sap_range"])
        if not legal_center(old):
            return excluded("old_center")
        indices = np.flatnonzero(np.all(ctx["enemy_coords"] == old, axis=1))
        if len(indices) != 1:
            return excluded("target_ambiguous_or_missing")
        enemy = int(ctx["enemy_vis_ids"][indices[0]])
        if (previous is None or previous[0]+1 != current[0] or previous[1]+1 != current[1]
                or previous[2:4] != current[2:4] or enemy not in previous[4]):
            return excluded("history")
        position, prior_energy = previous[4][enemy]
        delta = old[0]-position[0], old[1]-position[1]
        if abs(delta[0])+abs(delta[1]) != 1:
            return excluded("motion")
        energy = float(ctx["enemy_energies"][indices[0]])
        if not (math.isfinite(prior_energy) and math.isfinite(energy)
                and prior_energy >= 0 and energy >= 0 and energy >= ctx["move_cost"]):
            return excluded("enemy_energy")
        target = old[0]+delta[0], old[1]+delta[1]
        if not legal_center(target):
            return excluded("new_center")
        if not sensor[target] or not ctx["passable"][target]:
            return excluded("new_visibility_or_passability")
        return None, dict(uid=int(uid), enemy_uid=enemy, old_center=old, new_center=target)
