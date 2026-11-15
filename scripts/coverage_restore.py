"""Optionally restore a lost known point after the trained movement adviser has acted."""
from collections import Counter, defaultdict

import numpy as np

from agents.sherlock import geometry as geo
from scripts.combat_teacher_counterfactual import live_ids, native_order, substitute
from scripts.selective_advice_agent import SelectiveAdviceAgent


def choose_restorations(public, ctx, team, mirrored, cfg, base, mixed, counts):
    """Return UIDs to revert, in canonical target order. Both input arrays are final world commands."""
    known = ctx["point_tiles"]
    if not known.any() or np.array_equal(base, mixed):
        return []
    world_pos = np.asarray(public["units"]["position"])[team]
    energy = np.asarray(public["units"]["energy"])[team].reshape(-1)
    tiles = np.asarray(public["map_features"]["tile_type"])

    def endpoint(uid, order):
        source = tuple(map(int, ctx["ally_pos"][uid]))
        direction = int(order[0])
        if direction in (geo.STAY, geo.SAP):
            return source, direction == geo.STAY
        if not native_order(order, world_pos[uid], energy[uid], cfg, tiles):
            return source, False
        if mirrored:
            direction = geo.mirror_dir(direction)
        x = source[0] + int(geo.DIR_DX[direction])
        y = source[1] + int(geo.DIR_DY[direction])
        if not (0 <= x < known.shape[0] and 0 <= y < known.shape[1] and ctx["passable"][x,y]):
            return source, False
        return (x,y), True

    occupied = Counter()
    candidates = defaultdict(list)
    mixed_end = {}
    for uid in live_ids(public, team):  # ascending UID breaks ties at each target
        uid = int(uid)
        dest, allowed = endpoint(uid, mixed[uid])
        occupied[dest] += 1
        mixed_end[uid] = dest
        if not allowed or base[uid,0] == geo.SAP or base[uid,0] == mixed[uid,0]:
            continue
        target, legal_base = endpoint(uid, base[uid])
        if legal_base and known[target] and target != dest:
            candidates[target].append(uid)
    enemies = ctx["enemy_coords"][np.asarray(ctx["enemy_energies"]) >= 0]
    restored = []
    for target in sorted(candidates):
        if occupied[target]:
            continue
        counts["uncovered_candidate_fields"] += 1
        if len(enemies) and (np.max(np.abs(enemies-target), axis=1) <= ctx["sap_range"]).any():
            counts["fields_with_visible_enemy_in_range"] += 1
            continue
        for uid in candidates[target]:
            donor = mixed_end[uid]
            if known[donor] and occupied[donor] == 1:
                continue
            occupied[donor] -= 1
            occupied[target] += 1
            restored.append(uid)
            break
        else:
            counts["fields_with_only_last_cover"] += 1
    return restored


class CoverageRestoreAgent(SelectiveAdviceAgent):
    def _reset_episode_state(self):
        super()._reset_episode_state()
        self.coverage_counts = Counter()

    def _advise(self, step, obs, base):
        if self.mode != "movement":
            raise ValueError("Coverage restoration requires the movement adviser")
        # This first return value includes the normal confidence, SAP and native-legality filters.
        mixed = super()._advise(step, obs, base)
        if self.training or int(obs["match_steps"]) == 0 or np.array_equal(base,mixed):
            return mixed
        restored = choose_restorations(obs, self._prev_ctx, self.team_id, self.belief.mirrored,
                                       self.env_cfg, base, mixed, self.coverage_counts)
        if not restored:
            return mixed
        final = mixed.copy()
        final[restored] = base[restored]
        # Apply only the reversions. The parent already recorded the original R2 changes.
        # The estimator receives only the returned final array, once, through Agent_x._act_est.
        played = substitute(self, obs, mixed, final, "movement", self.coverage_counts)
        self.coverage_counts["restored_fields"] += len(restored)
        return played
