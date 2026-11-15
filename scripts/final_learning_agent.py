"""Experimental V14 scout. Learn four-step own energy returns for legal final movements."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from agents.sherlock import geometry as geo
from agents.sherlock.main import Agent_x

HORIZON = 4
MARGIN = 6.0
DEATH_COST = 40.0
FEATURES = ("bias", "start_energy", "start_field", "match_phase", "start_pressure",
            "stay", "move_cost", "field", "adjacent_best_field", "nebula", "explored",
            "enemy_same", "enemy_adjacent_energy", "enemy_close", "allies_here", "goal_progress",
            "field_when_low", "near_enemy_when_low", "on_candidate")
WEIGHTS = Path(__file__).resolve().parents[1] / "agents/sherlock/weights/agent_p0.pth"
WEIGHT_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.sha256(stream.read()).hexdigest()


def movement_design(ctx, uid, mask, base, spawn=(0, 0)):
    """Final canonical baseline action and public, canonical decision context only."""
    energy = float(ctx["ally_ene"][uid])
    ms = int(ctx["match_step"])
    if not (0 <= base < 5 and ctx["move_cost"] <= energy <= 150
            and 1 <= ms <= ctx["max_match_steps"] - HORIZON - 1):
        return None
    x, y = map(int, ctx["ally_pos"][uid])
    # Same-step death/reuse of an ID at spawn must be detectable throughout the horizon.
    if abs(x - spawn[0]) + abs(y - spawn[1]) <= HORIZON + 1:
        return None
    tx, ty = x + int(geo.DIR_DX[base]), y + int(geo.DIR_DY[base])
    if (not mask[base] or ctx["point_tiles"][x, y] or ctx["point_tiles"][tx, ty]):
        return None
    legal = np.asarray(mask[:5], bool).copy()
    if legal.sum() < 2:
        return None
    design = np.zeros((5, len(FEATURES)))
    field, explored = ctx["energy_map"], ctx["explored"]
    enemies, strengths = ctx["enemy_coords"], ctx["enemy_energies"]
    origin_dist = np.abs(enemies - [x, y]).sum(axis=1)
    pressure = float(np.max(strengths[origin_dist <= 3], initial=0)) / 200
    goal = ctx["assigned"].get(uid)
    low = (150 - energy) / 150
    for action in np.flatnonzero(legal):
        dx, dy = int(geo.DIR_DX[action]), int(geo.DIR_DY[action])
        nx, ny = x + dx, y + dy
        adjacent = [(nx + int(ax), ny + int(ay)) for ax, ay in zip(geo.DIR_DX, geo.DIR_DY)]
        nearby = [float(field[i, j]) for i, j in adjacent
                  if 0 <= i < ctx["W"] and 0 <= j < ctx["H"] and ctx["passable"][i, j] and explored[i, j]]
        dists = np.abs(enemies - [nx, ny]).sum(axis=1)
        same = float(strengths[dists == 0].sum()) / 200
        near = float(strengths[dists == 1].sum()) / 200
        close = float((dists <= 3).sum()) / 3
        gain = float(field[nx, ny]) / 20
        progress = (abs(x-goal[0]) + abs(y-goal[1]) - abs(nx-goal[0]) - abs(ny-goal[1])
                    if goal is not None else 0)
        design[action] = (1, energy/150, float(field[x,y])/20, ms/100, pressure,
                          action == 0, ctx["move_cost"]*(action != 0)/5, gain, max(nearby, default=0)/20,
                          ctx["nebula"][nx,ny], explored[nx,ny], same, near, close,
                          max(0, int(ctx["ally_count"][nx,ny]) - int(action == 0))/3,
                          progress, gain*low, near*low, ctx["candidate"][nx,ny])
    return design, legal


def choose(values, legal, base, threshold=MARGIN):
    best = int(np.argmax(np.where(legal, values, -np.inf)))
    return best if float(values[best] - values[base]) >= threshold else base


def tracking_result(event, step, obs, team):
    u = event["uid"]
    pos = tuple(map(int, np.asarray(obs["units"]["position"])[team, u]))
    energy = float(np.asarray(obs["units"]["energy"]).reshape(2, -1)[team, u])
    alive = bool(np.asarray(obs["units_mask"])[team, u])
    moved = sum(abs(i-j) for i, j in zip(pos, event["last_pos"]))
    if not alive or energy < 0 or moved > 1:
        return -event["initial"] - DEATH_COST, True
    event["last_pos"] = pos
    if step == event["step"] + HORIZON:
        return energy - event["initial"], False
    return None


def apply_world_action(actions, bookkeeping, uid, canonical, mirrored):
    actions[uid] = (geo.mirror_dir(canonical) if mirrored else canonical, 0, 0)
    bookkeeping[uid] = canonical


def load_model(path):
    obj = json.loads(Path(path).read_text())
    if (obj.get("schema") != 1 or obj.get("features") != list(FEATURES)
            or obj.get("v14") != WEIGHT_SHA or obj.get("horizon") != HORIZON or obj.get("margin") != MARGIN):
        raise ValueError("Model inputs do not match this experiment")
    weights = np.asarray(obj["coefficients"], dtype=float)
    if weights.shape != (len(FEATURES),) or not np.isfinite(weights).all():
        raise ValueError("Invalid fitted coefficients")
    return weights


class EnergyReturnAgent(Agent_x):
    """Ensemble plays normally. Postprocess one final legal scout move per four-step window."""

    def __init__(self, *args, model_path=None, collect=False, **kwargs):
        if (model_path is None) != bool(collect):
            raise ValueError("Choose either randomized collection or a frozen model")
        super().__init__(*args, **kwargs)
        if self.training or sha(self.agent_path) != WEIGHT_SHA or len(self.extra_q) != 35:
            raise ValueError("Requires exact V14 in evaluation mode")
        self.coefficients = load_model(model_path) if model_path is not None else None
        self.collect = collect
        self.buffer = self.opt = None
        self.autosave_on_terminate = False
        self.new_game(self.player)

    def new_game(self, player=None):
        super().new_game(player)
        self.pending = None
        self.next_probe = 0
        self.rows = []
        self.probes = self.changes = 0
        self.explore_rng = None

    def set_trial_seed(self, seed):
        self.trial_seed = seed

    def episode_stats(self):
        return dict(super().episode_stats(), energy_probes=self.probes, energy_changes=self.changes)

    def act(self, step, obs):
        actions = super().act(step, obs)
        if self.caught_errors:
            raise RuntimeError("Energy scout or V14 caught an error while acting")
        return actions

    def _act(self, step, obs):
        if self.pending is not None:
            result = tracking_result(self.pending, step, obs, self.team_id)
            if result is not None:
                self.rows.append(dict(**self.pending["row"], y=result[0], died=result[1]))
                self.pending = None
        actions = super()._act(step, obs)
        ctx = self._prev_ctx
        if ctx is None or step < self.next_probe:
            return actions
        ids = sorted(self._prev_masks)
        if not ids:
            return actions
        offset = (step // HORIZON) % len(ids)
        mirrored = self.belief.mirrored
        spawn = (0, 0) if self.team_id == 0 or mirrored else (ctx["W"]-1, ctx["H"]-1)
        for uid in ids[offset:] + ids[:offset]:
            world = int(actions[uid, 0])
            if world >= 5:
                continue
            base = geo.mirror_dir(world) if mirrored else world
            design = movement_design(ctx, uid, self._prev_masks[uid], base, spawn)
            if design is None:
                continue
            x, legal = design
            if self.collect:
                if self.explore_rng is None:
                    self.explore_rng = np.random.default_rng([self.trial_seed, self.team_id, 0xF14])
                chosen = int(self.explore_rng.choice(np.flatnonzero(legal)))
                self.pending = dict(initial=float(ctx["ally_ene"][uid]), step=step, uid=uid,
                                    last_pos=tuple(map(int, np.asarray(obs["units"]["position"])[self.team_id,uid])),
                                    row=dict(seed=self.trial_seed, side=self.team_id, step=step, uid=int(uid),
                                             base=base, chosen=chosen, legal=legal.tolist(), x=x.tolist()))
            else:
                chosen = choose(x @ self.coefficients, legal, base)
            self.probes += 1
            self.next_probe = step + HORIZON
            if chosen != base:
                apply_world_action(actions, self._prev_actions, uid, chosen, mirrored)
                if chosen != geo.STAY:
                    self._pred_pending = [p for p in self._pred_pending if p[0] != uid]
                    self._shape_pending = [p for p in self._shape_pending if p[0] != uid]
                self.changes += 1
            break
        return actions
