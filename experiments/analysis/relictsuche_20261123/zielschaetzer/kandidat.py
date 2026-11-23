"""Use public absence of relics and points to choose one reachable search route."""
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PACKAGE = ROOT/"experiments/releases/20261117_sherlock_v16/agent.zip"
V16 = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
COORD = np.array([(x, y) for x in range(24) for y in range(24) if x+y < 24], np.int16)
XY = np.indices((24, 24), dtype=np.int16).reshape(2, -1).T
PAIR_END = np.stack((COORD, 23-COORD[:, ::-1]), axis=1)
PAIR_FLAT = PAIR_END[..., 0]*24 + PAIR_END[..., 1]
MIRROR = np.array([0, 2, 1, 4, 3], np.int16)
DELTA = np.array([(0, 0), (0, -1), (1, 0), (0, 1), (-1, 0)], np.int16)
SPAWN = np.arange(1, 51, dtype=np.int16)
OFFSET = np.indices((5, 5), dtype=np.int16).reshape(2, -1).T-2
ZONE = COORD[:, None, :]+OFFSET
VALID_ZONE = ((ZONE >= 0) & (ZONE < 24)).all(2)
POINT_COORD = np.where(VALID_ZONE, ZONE[:, :, 0]*24 + ZONE[:, :, 1], 576)
HIST_OFFSET = np.arange(len(COORD), dtype=np.int32)[:, None]*51
ADJ = np.indices((3, 3), dtype=np.int16).reshape(2, -1).T-1
PERP = {1: (2, 4), 2: (1, 3), 3: (2, 4), 4: (1, 3)}
OPPOSITE = (0, 3, 4, 1, 2)
HORIZON = 8
LOCAL = 2*(HORIZON+1)+1
CENTER = HORIZON+1


def route_library():
    sequences = set()
    for a in range(1, 5):
        for length in (4, 6, HORIZON):
            sequences.add((a,)*length)
            for b in PERP[a]:
                for first in range(1, length):
                    sequences.add((a,)*first + (b,)*(length-first))
                if length == HORIZON:
                    for first, mid in ((2, 2), (2, 3), (3, 2)):
                        for last in (a, OPPOSITE[a]):
                            sequences.add((a,)*first + (b,)*mid + (last,)*(length-first-mid))
    routes = sorted(sequences)
    # A padded route repeats its endpoint; it never gains a fresh view from padding.
    moves = np.zeros((len(routes), HORIZON), np.int16)
    for i, seq in enumerate(routes):
        moves[i, :len(seq)] = seq
    rel = DELTA[moves].cumsum(1).astype(np.int16)
    center_weights = np.zeros((len(routes), LOCAL*LOCAL+1), np.float32)
    side_weights = np.zeros_like(center_weights)
    rows = np.arange(len(routes))
    for t in range(HORIZON):
        x, y = (rel[:, t] + CENTER).T
        discount = .965**t
        center_weights[rows, x*LOCAL+y] = np.maximum(center_weights[rows, x*LOCAL+y], discount)
        for dx, dy in ADJ:
            cells = (x+dx)*LOCAL + y+dy
            side_weights[rows, cells] = np.maximum(side_weights[rows, cells], discount)
    return moves, rel, center_weights, side_weights


MOVES, ROUTES, THROUGH, AROUND = route_library()


@lru_cache(maxsize=12)
def indexed_routes(x, y):
    start = np.array([x, y])
    paths = ROUTES + start
    inside = ((paths >= 0) & (paths < 24)).all((1, 2))
    indices = np.flatnonzero(inside)
    paths = paths[indices]
    flat_paths = paths[:, :, 0]*24+paths[:, :, 1]
    local = PAIR_END-start+CENTER
    valid = ((local >= 0) & (local < LOCAL)).all(2)
    pair = np.where(valid, local[:, :, 0]*LOCAL+local[:, :, 1], LOCAL*LOCAL)
    # Only pairs that a route from this ship can reach can affect its score.
    subset = np.flatnonzero(valid.any(1))
    pair = pair[subset]
    return (indices, flat_paths, subset, THROUGH[indices][:, pair], AROUND[indices][:, pair])


@lru_cache(maxsize=1)
def parameters():
    p = json.loads((HERE/"ort.json").read_bytes())
    counts = np.asarray(p["counts"], float)
    if not p["eligible"] or len(counts) != 300 or counts.sum() != p["train"][1]:
        raise ValueError("Unqualified first-pair estimator")
    return (counts+.5)/(counts.sum()+150), float(p["point_bit_density"])


class Evidence:
    def __init__(self):
        self.prior, self.point_rate = parameters()
        self.seen = np.zeros((24, 24), np.int16)
        self.occupied = np.zeros((24, 24), np.int16)

    def observe(self, step, obs, team):
        sensor = np.asarray(obs["sensor_mask"], bool)
        live = np.asarray(obs["units_mask"][team], bool) & (np.asarray(obs["units"]["energy"][team]).reshape(-1) >= 0)
        pos = np.asarray(obs["units"]["position"][team])[live]
        # Fold both world ends of each symmetric pair. The result is already side invariant.
        self.seen[sensor | sensor[::-1, ::-1].T] = min(step, 50)
        if len(pos):
            for loc in (pos, 23-pos[:, ::-1]):
                self.occupied[loc[:, 0], loc[:, 1]] = min(step, 50)

    def density(self, step, horizon=0, use_points=True):
        # Each of the 50 activation times is the first PUBLIC observation carrying that spawn.
        last = self.seen[COORD[:, 0], COORD[:, 1]]
        feasible = (SPAWN[None, :] > last[:, None]) & (SPAWN[None, :] <= min(50, step+horizon))
        if not use_points:
            return feasible.mean(1)
        visit = np.append(self.occupied, 0)[POINT_COORD]
        # Same hidden scoring bit at a tile and its mirror. Repeated occupations count once.
        histogram = np.bincount((HIST_OFFSET+visit).ravel(), minlength=len(COORD)*51).reshape(-1, 51)
        counts = np.cumsum(histogram[:, :0:-1], axis=1)[:, ::-1]
        return (feasible*(1-self.point_rate)**counts).mean(1)

    def location_weights(self, step, horizon=0):
        return self.prior*self.density(step, horizon)


class Scout:
    def __init__(self, base):
        self.base = base
        self.team = int(base.player[-1])
        self.reset()

    def __getattr__(self, name):
        return getattr(self.base, name)

    def reset(self):
        self.evidence = Evidence()
        self.changes = 0
        self.finished = False
        self.ship = None
        self.planned = []
        self.expected = None
        self.last = None

    def new_game(self, player=None):
        self.base.new_game(player)
        self.team = int(self.base.player[-1])
        self.reset()

    def set_env_cfg(self, cfg):
        return self.base.set_env_cfg(cfg)

    def act(self, step, obs):
        original = self.base.act(step, obs)
        self.last = None
        if int(self.base.env_cfg["unit_sensor_range"]) != 1 or step >= 101:
            return original
        if np.any(obs["relic_nodes_mask"]) or int(obs["team_points"][self.team]) > 0:
            self.finished = True
            return original
        self.evidence.observe(step, obs, self.team)
        p = self.base._imitation
        if self.finished or not 12 <= step <= 94 or p.last_fz is None:
            return original
        ctx, ids, features, masks, _, _, pos = p.last_fz
        ids = np.asarray(ids, dtype=int)
        actions = np.asarray(original[ids, 0])
        move = np.where(actions <= 4, actions, 0)
        if self.team:
            move = MIRROR[move]
        energy = np.asarray(ctx["ally_ene"])[ids]
        # Confirmed point holders, near-point ships, shots and ships threatened by a visible enemy are protected.
        name = feature_columns()
        free = ((actions <= 4) & (energy >= max(10, 3*ctx["move_cost"])) &
                (features[:, name[0]].max(1) == 0) & (features[:, name[1]] == 0) & masks[:, 1:5].any(1))
        valid = np.flatnonzero(free)
        if self.ship is not None:
            live = np.flatnonzero(ids == self.ship)
            if not len(live) or energy[live[0]] < 0:
                self.finished = True
                return original
            k = live[0]
            if not free[k]:
                self.planned.clear()
                return original
        elif len(valid):
            # Choose an established forward ship, preferring energy and separation from teammates at a tie.
            peer_dist = np.abs(pos[valid, None, :]-pos[None, :, :]).sum(2)
            crowd = ((peer_dist <= 2) & (energy[None, :] >= 0)).sum(1)
            rank = pos[valid].sum(1) + np.minimum(energy[valid], 120)/80 - .65*crowd
            k = valid[np.argmax(rank)]
            self.ship = int(ids[k])
            self.planned.clear()
        else:
            return original
        x, y = map(int, pos[k])
        dest = np.clip(pos+DELTA[move], 0, 23)
        peers = (ids != ids[k]) & (energy >= 0)
        peer_dest = dest[peers]
        peer_flat = peer_dest[:, 0]*24+peer_dest[:, 1]
        allowed = np.asarray(masks[k, :5], bool).copy()
        first = DELTA+pos[k]
        allowed &= ((first >= 0) & (first < 24)).all(1)
        allowed &= ~np.isin(first[:, 0]*24+first[:, 1], peer_flat)
        allowed[0] = False
        if not allowed.any():
            self.planned.clear()
            return original
        if self.expected != (x, y) or (self.planned and not allowed[self.planned[0]]):
            self.planned.clear()
        if not self.planned:
            projected = np.clip(peer_dest+DELTA[move[peers]], 0, 23)
            board = np.asarray(p.belief.tile_type).reshape(-1)
            blocked = board[projected[:, 0]*24+projected[:, 1]] == 2
            projected[blocked] = peer_dest[blocked]
            probabilities = self.evidence.location_weights(step, HORIZON)
            self.planned = self.plan(x, y, int(move[k]), allowed, board, peer_dest, projected, probabilities)
        if not self.planned:
            return original
        d = self.planned.pop(0)
        self.expected = (x+int(DELTA[d, 0]), y+int(DELTA[d, 1]))
        cmd = int(MIRROR[d]) if self.team else d
        self.last = (self.ship, cmd)
        if int(actions[k]) == cmd:
            return original
        output = original.copy()
        output[self.ship] = [cmd, 0, 0]
        p._prev_actions[self.ship] = d
        p._sap_hits.pop(self.ship, None)
        p.param_est.record_played_actions(output)
        self.changes += 1
        return output

    @staticmethod
    def plan(x, y, base_dir, allowed, board, peer_dest, projected, probabilities):
        indices, flat, subset, centers, sight = indexed_routes(x, y)
        clear = allowed[MOVES[indices, 0]] & ~(board[flat] == 2).any(1)
        if not clear.any():
            return []
        ends = PAIR_END[subset]
        cells = PAIR_FLAT[subset]
        # At sight 1 a lone ship reveals nebula reliably by standing on it. Unknown terrain is discounted.
        reliability = np.where(board[cells] == 1, .12, np.where(board[cells] < 0, .82, 1.0))
        visibility = np.maximum(centers, sight*reliability).max(2)
        if len(peer_dest):
            locations = np.concatenate((peer_dest, projected))
            closest = np.abs(ends[:, :, None, :]-locations).max(3).min((1, 2))
            separate = np.choose(np.minimum(closest, 4), [.10, .20, .60, .86, 1.])
        else:
            separate = 1.
        score = (visibility*(probabilities[subset]*separate)).sum(1)
        score[~clear] = -1
        best = int(np.argmax(score))
        if score[best] <= 0:
            return []
        # Prefer the original command when it starts an almost-as-promising eight-step route.
        begins_original = clear & (MOVES[indices, 0] == base_dir)
        if begins_original.any():
            keep = int(np.argmax(np.where(begins_original, score, -1)))
            if score[keep] >= .92*score[best]:
                best = keep
        return MOVES[indices[best], :3].tolist()


@lru_cache(maxsize=1)
def feature_columns():
    # Use the version inside the loaded V16 ZIP, including its original feature order.
    from sherlock.features import FEATURE_NAMES
    return [FEATURE_NAMES.index(n+"_point") for n in "curdl"], FEATURE_NAMES.index("enemies_in_sap")


def create(side):
    if sha256(PACKAGE.read_bytes()).hexdigest() != V16:
        raise ValueError("Original V16 archive differs")
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.r3_package import r3_package_agent
    return Scout(r3_package_agent(side, PACKAGE))
