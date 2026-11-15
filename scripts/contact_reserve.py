"""Experimental V14 movement override for expensive visible enemy energy voids.

The next enemy positions and the map's void factor are hidden. Assume visible
opponents hold their observed positions and use one fixed plausible factor of
1/8. Only a planned STAY or move can change. This is a forecast, not a damage
measurement; collision prediction and incoming SAP damage are outside it.
"""
from __future__ import annotations

from collections import Counter

import numpy as np

from agents.sherlock import geometry as geo
from agents.sherlock.main import Agent_x

DIRECTIONS = tuple(zip(geo.DIR_DX.tolist(), geo.DIR_DY.tolist()))


def contact_maps(ctx: dict) -> tuple[np.ndarray, np.ndarray]:
    """Sum visible enemy energy at cardinal neighbors without wrapping at walls."""
    mass = np.zeros(ctx["passable"].shape, dtype=np.int32)
    occupied = np.zeros_like(mass, dtype=bool)
    for (x, y), energy in zip(ctx["enemy_coords"], ctx["enemy_energies"]):
        if energy >= 0:
            mass[x, y] += int(energy)
            occupied[x, y] = True
    sources = np.zeros_like(mass)
    sources[1:, :] += mass[:-1, :]
    sources[:-1, :] += mass[1:, :]
    sources[:, 1:] += mass[:, :-1]
    sources[:, :-1] += mass[:, 1:]
    return sources, occupied


def destination(ctx, uid, action):
    x, y = map(int, ctx["ally_pos"][uid])
    if not 1 <= action <= 4 or ctx["ally_ene"][uid] < ctx["move_cost"]:
        return x, y
    dx, dy = DIRECTIONS[action]
    tx, ty = x + dx, y + dy
    w, h = ctx["passable"].shape
    if 0 <= tx < w and 0 <= ty < h and ctx["passable"][tx, ty]:
        return tx, ty
    return x, y


def _forecast(ctx, uid, tile, stack, sources, nebula_drain):
    # The engine sums sources, divides by allied stack size and floors once.
    drain = int(sources[tile]) // (8 * stack)
    moved = tile != tuple(ctx["ally_pos"][uid])
    before_field = float(ctx["ally_ene"][uid]) - moved * ctx["move_cost"] - drain
    gain = float(ctx["energy_map"][tile]) - bool(ctx["nebula"][tile]) * nebula_drain
    remaining = before_field + gain
    if before_field >= 0 or remaining >= 0:
        remaining = min(400.0, max(0.0, remaining))
    return drain, remaining


def contact_adjustments(ctx: dict, planned: dict, masks: dict, nebula_drain: float) -> dict[int, int]:
    """Changes to canonical orders, in stable UID order, using the team's final plans."""
    if not len(ctx["enemy_coords"]):
        return {}
    sources, occupied = contact_maps(ctx)
    tiles = {u: destination(ctx, u, a) for u, a in planned.items() if ctx["ally_ene"][u] >= 0}
    counts = Counter(tiles.values())
    changes = {}
    for uid, old_tile in tiles.items():
        if planned[uid] == geo.SAP or occupied[old_tile] or not sources[old_tile]:
            continue
        old_drain, old_energy = _forecast(ctx, uid, old_tile, counts[old_tile], sources, nebula_drain)
        if not old_drain or old_energy >= ctx["sap_cost"]:
            continue
        keep_point = old_energy >= 0 and ctx["point_tiles"][old_tile] and counts[old_tile] == 1
        goal = ctx["assigned"].get(uid)
        best_key, best_move = None, None
        for move in range(5):
            if not masks[uid][move]:
                continue
            tile = destination(ctx, uid, move)
            if tile == old_tile or occupied[tile] or (move and tile == tuple(ctx["ally_pos"][uid])):
                continue
            adds_point = bool(ctx["point_tiles"][tile]) and counts[tile] == 0
            if keep_point and not adds_point:
                continue
            drain, energy = _forecast(ctx, uid, tile, counts[tile] + 1, sources, nebula_drain)
            if drain >= old_drain or energy < 0:
                continue
            # Rescue a predicted death, or save at least half a shot in energy.
            if old_energy >= 0 and energy - old_energy < ctx["sap_cost"] / 2:
                continue
            distance = 0 if goal is None else abs(tile[0] - goal[0]) + abs(tile[1] - goal[1])
            key = (adds_point, energy, -distance, move == geo.STAY, -move)
            if best_key is None or key > best_key:
                best_key, best_move = key, move
        if best_move is not None:
            counts[old_tile] -= 1
            counts[destination(ctx, uid, best_move)] += 1
            changes[uid] = best_move
    return changes


class ContactReserveAgent(Agent_x):
    """Run stock V14 first and amend only the final movement of threatened units."""

    def _reset_episode_state(self):
        super()._reset_episode_state()
        self.study_stats = {"contact_reserve_changes": 0, "contact_reserve_steps": 0}

    def _act(self, step, obs):
        actions = super()._act(step, obs)
        ctx = self._prev_ctx
        if self.training or ctx is None or not len(ctx["enemy_coords"]):
            return actions
        mirrored = self.belief.mirrored
        planned = {}
        for uid in ctx["ally_ids"]:
            action = int(actions[uid, 0])
            planned[int(uid)] = geo.mirror_dir(action) if mirrored and action != geo.SAP else action
        changes = contact_adjustments(ctx, planned, self._prev_masks, self.param_est.nebula(default=0))
        if changes:
            self.study_stats["contact_reserve_steps"] += 1
            self.study_stats["contact_reserve_changes"] += len(changes)
            # The optional opponent model logs hits on stationary ships only.
            moved = {uid for uid, direction in changes.items() if direction != geo.STAY}
            self._pred_pending = [p for p in self._pred_pending if p[0] not in moved]
            self._shape_pending = [p for p in self._shape_pending if p[0] not in moved]
        for uid, move in changes.items():
            actions[uid] = (geo.mirror_dir(move) if mirrored else move, 0, 0)
            self._prev_actions[uid] = move
        return actions
