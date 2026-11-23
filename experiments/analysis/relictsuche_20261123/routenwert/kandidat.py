"""Learn a single opening route from paired outcomes after real interventions."""
from collections import deque
from functools import lru_cache
import json
from pathlib import Path

import numpy as np

from agents.sherlock import geometry as geo
from agents.sherlock.features import FEATURE_NAMES
from scripts.r3_package import r3_package_agent

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PACKAGE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
POINT = [FEATURE_NAMES.index(name + "_point") for name in "curdl"]
THREAT = FEATURE_NAMES.index("enemies_in_sap")
XY = np.indices((24, 24)).transpose(1, 2, 0)
RELEASE = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"


def landmarks():
    return ((18, 5), (5, 18), (13, 13))


@lru_cache(maxsize=96)
def distances(target, shape, walls):
    blocked = np.frombuffer(walls, dtype=bool).reshape(shape)
    free = np.argwhere(~blocked)
    result = np.full(shape, 999, dtype=np.int16)
    if not len(free):
        return result
    nearest = tuple(free[int(np.abs(free - target).sum(1).argmin())])
    result[nearest] = 0
    fringe = deque([nearest])
    while fringe:
        x, y = fringe.popleft()
        d = result[x, y] + 1
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < shape[0] and 0 <= ny < shape[1] and not blocked[nx, ny] and result[nx, ny] > d:
                result[nx, ny] = d
                fringe.append((nx, ny))
    return result


def move_towards(position, target, legal, walls, original):
    x, y = map(int, position)
    d = distances(tuple(target), walls.shape, walls.tobytes())
    choices = []
    for action in np.flatnonzero(legal[1:5]) + 1:
        nx, ny = x + geo.DIR_DX[action], y + geo.DIR_DY[action]
        if 0 <= nx < walls.shape[0] and 0 <= ny < walls.shape[1] and d[nx, ny] < d[x, y]:
            choices.append((int(d[nx, ny]), int(action != original), int(action)))
    return min(choices)[2] if choices else None


def paired_gain(original, alternative):
    sight = np.clip(original[0] - alternative[0], -45, 45)
    credit = np.clip(original[1] - alternative[1], -45, 45)
    score = np.clip(alternative[2] - original[2], -60, 60)
    return float(.70 * sight + .22 * credit + .08 * score)


def choose_path(predictions, threshold):
    i = int(np.argmax(predictions))
    return i if predictions[i] >= threshold else None


def describe(goal, position, fleet, direction, terrain, seen, ctx, uid):
    target = np.array(goal)
    displacement = target - position
    team_dist = np.abs(fleet - target).sum(1)
    midpoint = (position + target) / 2.
    near = np.abs(XY - midpoint).sum(2) <= 5
    end = np.abs(XY - target).sum(2) <= 5
    landing = position + [geo.DIR_DX[direction], geo.DIR_DY[direction]]
    length = max(np.abs(displacement).sum(), 1)
    direction_gain = length - np.abs(target - landing).sum()
    dx, dy = displacement
    return [
        length / 40, min(abs(dx), abs(dy)) / 20, (goal[0] == goal[1]) * 1.,
        float(direction_gain), float(np.linalg.norm(displacement)) / 32,
        (np.min(team_dist) - length) / 35, np.mean(team_dist <= length + 2), np.mean(team_dist) / 40,
        seen[near].mean(), seen[end].mean(), terrain[near].mean(), terrain[end].mean(),
        min(ctx["ally_ene"][uid], 400) / 400, ctx["move_cost"] / 5,
        ctx["match_step"] / 50, min(len(fleet), 16) / 16, seen.mean(),
        (abs(dx) - abs(dy)) * (position[1] - position[0]) / 300,
    ]


class OpeningRoute:
    def __init__(self, side, forced=None, model=None):
        self.base = r3_package_agent(side, PACKAGE)
        self.model = model
        self.forced = forced
        self.changes = 0
        self.uid = None
        self.start = None
        self.selected = None
        self.event = None
        self.completed = False
        self.seen = np.zeros((24, 24), dtype=bool)

    def __getattr__(self, name):
        return getattr(self.base, name)

    def act(self, step, obs):
        command = self.base.act(step, obs)
        if self.completed or step > 76:
            return command
        policy = self.base._imitation
        if int(policy.belief.sensor_range) != 1 or step >= 101:
            self.completed = True
            return command
        if np.any(obs["relic_nodes_mask"]) or int(obs["team_points"][int(self.base.player[-1])]) > 0:
            self.completed = True
            return command
        current = np.asarray(obs["sensor_mask"], dtype=bool)
        self.seen |= geo.mirror_map(current) if policy.belief.mirrored else current
        fz = getattr(policy, "last_fz", None)
        if step < 14 or fz is None:
            return command
        ctx, ids, features, masks, _, _, positions = fz
        ids = np.asarray(ids, dtype=int)
        if len(ids) < 2:
            return command
        energy = np.asarray(ctx["ally_ene"])[ids]
        safe = ((energy >= 3 * ctx["move_cost"]) & (command[ids, 0] <= 4) &
                (features[:, POINT].max(axis=1) == 0) & (features[:, THREAT] == 0))
        safe_ids = np.flatnonzero(safe)
        walls = np.asarray(~ctx["passable"], dtype=bool)
        if self.start is None:
            if step > 38 or not len(safe_ids):
                return command
            # A ship close to teammates can leave a duplicated search corridor.
            occupied = np.abs(positions[:, None] - positions[None, :]).sum(2)
            np.fill_diagonal(occupied, 1000)
            k = min(safe_ids, key=lambda i: (int(occupied[i].min()), -int(energy[i]), int(ids[i])))
            self.uid, self.start = int(ids[k]), int(step)
            original = int(command[self.uid, 0])
            canonical = geo.mirror_dir(original) if policy.belief.mirrored else original
            teammates = np.delete(positions, k, axis=0)
            x = np.asarray([describe(goal, positions[k], teammates, canonical, walls, self.seen, ctx, self.uid)
                            for goal in landmarks()], dtype=float)
            self.event = dict(step=int(step), uid=self.uid, pos=positions[k].tolist(), x=x.tolist())
            if self.forced is not None:
                self.selected = self.forced if self.forced >= 0 else None
            else:
                standardized = (x - np.asarray(self.model["mean"])) / np.asarray(self.model["scale"])
                prediction = self.model["intercept"] + standardized @ self.model["weights"]
                self.selected = choose_path(prediction, self.model["threshold"])
        if self.selected is None or step >= self.start + 24:
            self.completed = True
            return command
        current_id = np.flatnonzero(ids == self.uid)
        if len(current_id) != 1 or not safe[current_id[0]]:
            self.completed = True
            return command
        k = current_id[0]
        orig = int(command[self.uid, 0])
        canonical = geo.mirror_dir(orig) if policy.belief.mirrored else orig
        alt = move_towards(positions[k], landmarks()[self.selected], masks[k], walls, canonical)
        if alt is None:
            self.completed = True
            return command
        if alt == canonical:
            return command
        out = command.copy()
        out[self.uid] = [geo.mirror_dir(alt) if policy.belief.mirrored else alt, 0, 0]
        policy._prev_actions[self.uid] = alt
        policy._sap_hits.pop(self.uid, None)
        policy.param_est.record_played_actions(out)
        self.changes += 1
        return out


def create(side):
    return OpeningRoute(side, model=json.loads((HERE / "modell.json").read_text()))
