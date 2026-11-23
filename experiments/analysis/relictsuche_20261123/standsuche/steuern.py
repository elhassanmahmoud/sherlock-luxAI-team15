"""Explore for three steps with one ship after repeated idle commands in hard openings."""
import json
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import (
    DELTA, MIRROR, PAIR_END, PACKAGE, Evidence, feature_columns,
)
from scripts.r3_package import r3_package_agent

HERE = Path(__file__).resolve().parent
FEATURES = (
    "relic_mass", "extra_mass", "new_cells", "fresh_cells", "new_mirror_pairs",
    "overlap_now", "closest_ally", "distance_gain_ally", "walkable_length",
    "move_cost", "start_energy", "energy_gain", "recent_gain", "idle_duration",
    "turn", "crowding", "outward", "target_nebula", "tile_energy", "optical_coverage",
    "known_fraction", "visible_fraction", "timed_novelty", "late_mass", "nearby_relic_mass",
)
CELLS = np.indices((24, 24), dtype=np.int16).transpose(1, 2, 0)


def outcome(first, credit, own, other):
    return [int(first), int(credit), int(own - other)]


def value_of(original, alternative):
    d = (np.asarray(alternative) - original) * [-1, -1, 1]
    return float(np.clip(d, -45, 45) @ [.55, .30, .15])


class StationaryHistory:
    def __init__(self):
        self.stays = np.zeros(16, np.int16)
        self.last = np.full((16, 2), -1, np.int16)
        self.initial_energy = np.zeros(16, float)
        self.energy_gain = np.zeros(16, float)
        self.last_energy = np.zeros(16, float)
        self.recent_gain = np.zeros(16, float)

    def update(self, ids, pos, actions, energy):
        existing = np.zeros(16, dtype=bool)
        for uid, xy, a, e in zip(ids, pos, actions, energy, strict=True):
            if e < 0:
                continue
            existing[uid] = True
            same = np.array_equal(xy, self.last[uid])
            self.recent_gain[uid] = e - self.last_energy[uid] if same else 0
            if a == 0:
                if not same or self.stays[uid] == 0:
                    self.initial_energy[uid] = e
                    self.stays[uid] = 0
                self.stays[uid] += 1
            else:
                self.stays[uid] = 0
                self.initial_energy[uid] = e
            self.energy_gain[uid] = e - self.initial_energy[uid]
            self.last[uid] = xy
            self.last_energy[uid] = e
        self.stays[~existing] = 0
        self.last[~existing] = -1


def alternative_features(direction, k, state, peer, occ, prior, last, history):
    ctx, ids, _, masks, _, _, pos = state
    if not masks[k, direction]:
        return None
    start = pos[k]
    coords = []
    for length in range(1, 4):
        q = start + length * DELTA[direction]
        if ((q < 0) | (q >= 24)).any():
            break
        if not ctx["passable"][tuple(q)] or (not coords and tuple(q) in occ):
            break
        coords.append(q)
    if not coords:
        return None
    path = np.array(coords)
    swept = np.abs(CELLS[:, :, None] - path).max(3).min(2) <= 1
    sight_here = np.abs(CELLS - start).max(2) <= 1
    have = (np.abs(CELLS[:, :, None] - peer).max(3).min(2) <= 1 if len(peer)
            else np.zeros((24, 24), bool))
    def mass(mask):
        scores = mask[PAIR_END[..., 0], PAIR_END[..., 1]].any(1)
        return float(prior[scores].sum())
    final = path[-1]
    before_d = np.abs(peer - start).sum(1)
    after_d = np.abs(peer - final).sum(1)
    new = swept & ~sight_here & ~have
    old = last < 0
    turn, uid = int(ctx["match_step"]), ids[k]
    near = np.abs(CELLS - start).sum(2) <= 5
    weighted_mass = mass(new)
    tiles = tuple(path.T)
    return [
        mass(swept), weighted_mass, float((new & old).sum()) / 12,
        float((new & (last < turn - 12)).sum()) / 12,
        float((new & old & old[::-1, ::-1].T).sum()) / 12,
        float((swept & have).sum()) / max(1, swept.sum()), min(after_d, default=48) / 24,
        (min(after_d, default=48) - min(before_d, default=48)) / 3, len(path) / 3,
        ctx["move_cost"]/5, min(ctx["ally_ene"][uid], 300)/300,
        np.clip(history.energy_gain[uid]/50, -1, 1), np.clip(history.recent_gain[uid]/15, -1, 1),
        min(history.stays[uid], 20)/20, turn/100, float((before_d <= 2).sum())/6,
        (sum(final)-sum(start))/3, np.mean(ctx["nebula"][tiles]), np.mean(ctx["energy_map"][tiles])/20,
        sight_here.sum()/9, (last >= 0).mean(), (last == turn).mean(),
        np.clip((turn - last[new]).mean()/50, 0, 2) if new.any() else 0, weighted_mass * turn/60,
        mass(near),
    ]


class AntiStall:
    def __init__(self, side, force=None, model=None):
        self.base = r3_package_agent(side, PACKAGE)
        self.team = int(side[-1])
        self.force = force
        self.model = model
        self.reset()

    def reset(self):
        self.history = StationaryHistory()
        self.evidence = Evidence()
        self.last_seen = np.full((24, 24), -1, np.int16)
        self.changes = 0
        self.event = None
        self.selected = None
        self.expected = None
        self.over = False

    def __getattr__(self, name):
        return getattr(self.base, name)

    def new_game(self, player=None):
        self.base.new_game(player)
        self.reset()

    def act(self, step, obs):
        original = self.base.act(step, obs)
        if self.over:
            return original
        if (step > 78 or int(self.base.env_cfg["unit_sensor_range"]) != 1
                or np.any(obs["relic_nodes_mask"]) or int(obs["team_points"][self.team]) > 0):
            self.over = True
            return original
        self.evidence.observe(step, obs, self.team)
        sight = np.asarray(obs["sensor_mask"], bool)
        self.last_seen[sight[::-1, ::-1].T if self.team else sight] = step
        policy = self.base._imitation
        state = getattr(policy, "last_fz", None)
        if state is None:
            self.history.update([], [], [], [])
            return original
        ctx, ids, f, masks, _, _, pos = state
        ids = np.asarray(ids, int)
        energy = np.asarray(ctx["ally_ene"])[ids]
        acts = np.asarray(original[ids, 0])
        canon = np.where(acts < 5, acts, 0)
        if self.team:
            canon = MIRROR[canon]
        projected = pos + DELTA[canon]
        points, threat = feature_columns()
        free = ((energy >= max(45, 8*ctx["move_cost"])) & (acts <= 4)
                & (f[:, points].max(1) == 0) & (f[:, threat] == 0))
        self.history.update(ids, pos, acts, energy)
        if self.event is None:
            if not 22 <= step <= 75:
                return original
            waiting = np.flatnonzero(free & (self.history.stays[ids] >= 4))
            if not len(waiting):
                return original
            prior = self.evidence.location_weights(step, 3)
            prior /= max(1e-12, prior.sum())
            for k in sorted(waiting, key=lambda i: (-self.history.stays[ids[i]], -energy[i], int(ids[i]))):
                others = (ids != ids[k]) & (energy >= 0)
                peer = projected[others]
                occ = set(map(tuple, peer))
                x = {}
                for d in range(1, 5):
                    row = alternative_features(d, k, state, peer, occ, prior, self.last_seen, self.history)
                    if row is not None:
                        x[str(d)] = [float(v) for v in row]
                if len(x) < 2:
                    continue
                self.event = dict(step=int(step), uid=int(ids[k]), pos=pos[k].tolist(), x=x,
                                  idle=int(self.history.stays[ids[k]]), energy=float(energy[k]))
                if self.force is None:
                    self.selected = select(x, self.model)
                else:
                    self.selected = self.force if str(self.force) in x else None
                break
        if self.event is None:
            return original
        if self.selected is None or step >= self.event["step"] + 3:
            self.over = True
            return original
        uid = self.event["uid"]
        row = np.flatnonzero(ids == uid)
        if len(row) != 1:
            self.over = True
            return original
        k, d = row[0], self.selected
        future = pos[k] + DELTA[d]
        others = (ids != uid) & (energy >= 0)
        if (not free[k] or not masks[k, d] or ((future < 0) | (future >= 24)).any()
                or (self.expected is not None and tuple(pos[k]) != self.expected)
                or not ctx["passable"][tuple(future)] or any((projected[others] == future).all(1))):
            self.over = True
            return original
        self.expected = tuple(future)
        if d == canon[k]:
            return original
        out = original.copy()
        out[uid] = [int(MIRROR[d]) if self.team else d, 0, 0]
        policy._prev_actions[uid] = d
        policy._sap_hits.pop(uid, None)
        policy.param_est.record_played_actions(out)
        self.changes += 1
        return out


def predict(x, model):
    if model["kind"] == "prior":
        return x[:, FEATURES.index("extra_mass")]
    z = (x - model["mean"]) / model["scale"]
    if model["kind"] == "mlp":
        z = np.maximum(0, z @ model["hidden_w"] + model["hidden_b"])
    return z @ model["w"] + model["b"]


def select(options, model):
    directions = sorted(options, key=int)
    value = predict(np.array([options[key] for key in directions]), model)
    index = int(np.argmax(value))
    return int(directions[index]) if value[index] >= model["threshold"] else None


def create(side):
    return AntiStall(side, model=json.loads((HERE/"modell.json").read_text()))
