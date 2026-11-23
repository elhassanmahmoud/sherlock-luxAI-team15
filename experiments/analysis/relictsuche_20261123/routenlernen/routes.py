"""Fixed eight-move course options built solely from the V16 public context."""
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SIZE = 24
STEPS = 8
DX = np.array([0, 0, 1, 0, -1])
DY = np.array([0, -1, 0, 1, 0])
MIRROR_DIR = np.array([0, 2, 1, 4, 3])
X, Y = np.indices((SIZE, SIZE))
OFFSETS = np.array([(i, j) for i in (-1, 0, 1) for j in (-1, 0, 1)])
GEOMETRY = (
    "own_horizon", "outside_edge", "toward_midline", "toward_center", "toward_origin",
    "end_x_y_gap", "change_team_distance", "end_team_distance", "mean_team_distance",
    "threat", "energy", "fog", "route_length", "turn", "fraction_seen",
    "team_count", "energy_reserve", "original_first_move", "moving",
)
PUBLIC = ("never_seen", "not_seen_since_spawn", "visible_long_ago", "unchecked_near_end",
          "unvisited_route", "recent_visits", "fresh_at_end", "without_team")
PHASES = tuple(f"unobserved_footprint_{i}{j}" for i in range(6) for j in range(i, 6))
NAMES = GEOMETRY + PUBLIC + PHASES
PHASE = np.zeros((6, 6), dtype=int)
for k, (i, j) in enumerate((i, j) for i in range(6) for j in range(i, 6)):
    PHASE[i, j] = PHASE[j, i] = k


def templates():
    result = [[0] * STEPS]
    for d in range(1, 5):
        result.append([d] * STEPS)
        for turn in (1 + (d % 4), 1 + ((d - 2) % 4)):
            for at in (2, 4, 6):
                result.append([d] * at + [turn] * (STEPS - at))
            result.append([d, turn] * 4)
            result.append([d, d, turn, d] * 2)
    return np.asarray(result, dtype=np.int8)


DIRECTIONS = templates()
TRAIL_X = np.cumsum(DX[DIRECTIONS], axis=1)
TRAIL_Y = np.cumsum(DY[DIRECTIONS], axis=1)


class SearchHistory:
    def __init__(self):
        self.last_seen = np.full((SIZE, SIZE), -1, dtype=np.int16)
        self.last_visit = np.full_like(self.last_seen, -1)
        self.scout = None
        self.finished = False

    def observe(self, turn, obs, team):
        if self.finished:
            return
        if np.any(obs["relic_nodes_mask"]) or int(obs["team_points"][team]) > 0:
            self.finished = True
            return
        sensor = np.asarray(obs["sensor_mask"], dtype=bool)
        self.last_seen[sensor | sensor[::-1, ::-1].T] = turn
        alive = (np.asarray(obs["units_mask"])[team]
                 & (np.asarray(obs["units"]["energy"])[team].reshape(-1) >= 0))
        ships = np.asarray(obs["units"]["position"])[team, alive]
        if team:
            ships = SIZE - 1 - ships[:, ::-1]
        if len(ships):
            self.last_visit[tuple(ships.T)] = turn


class PublicOptions:
    """Frame for the single eligible ship. All positions and directions are canonical."""
    def __init__(self, ctx, uid, row, positions, ids, masks, directions, live):
        self.ctx = ctx
        self.uid = uid
        self.row = row
        self.origin = positions[row]
        self.original = int(directions[row])
        self.mask = masks[row]
        self.energy = float(ctx["ally_ene"][uid])
        self.own = positions[live]
        other = live & (np.asarray(ids) != uid)
        moves = directions[other].clip(0, 4)
        moves[directions[other] == 5] = 0
        at = positions[other]
        self.next_others = at + np.column_stack((DX[moves], DY[moves]))
        self.others = np.vstack((at, self.next_others))

    def first_allowed(self, direction):
        if direction not in (1, 2, 3, 4) or not self.mask[direction]:
            return False
        dest = self.origin + np.array([DX[direction], DY[direction]])
        x, y = dest
        return (0 <= x < SIZE and 0 <= y < SIZE and self.ctx["passable"][x, y]
                and not np.any(np.all(self.next_others == dest, axis=1))
                and not self.ctx["point_tiles"][x, y] and not self.ctx["candidate"][x, y]
                and not near_enemies(dest, self.ctx))


def near_enemies(pos, ctx):
    enemies = np.asarray(ctx["enemy_coords"]).reshape(-1, 2)
    return (len(enemies) > 0 and
            bool((np.max(np.abs(enemies - pos), axis=1) <= int(ctx["sap_range"])).any()))


def current(base, actions, history):
    p = base._imitation
    if p.last_fz is None:
        return None
    ctx, ids, _, masks, _, _, positions = p.last_fz
    live = np.asarray([ctx["ally_ene"][u] >= 0 for u in ids])
    if live.sum() < 2:
        return None
    directions = np.asarray(actions)[ids, 0].copy()
    if p.belief.mirrored:
        move = directions <= 4
        directions[move] = MIRROR_DIR[directions[move]]
    ranking = []
    for i, uid in enumerate(ids):
        uid = int(uid)
        if history.scout is not None and uid != history.scout:
            continue
        x, y = positions[i]
        target = ctx["assigned"].get(uid)
        d = int(directions[i])
        if (not live[i] or d > 4 or ctx["ally_ene"][uid] < max(14, 4 * ctx["move_cost"])
                or ctx["point_tiles"][x, y] or ctx["candidate"][x, y]
                or (target is not None and (ctx["point_tiles"][target] or ctx["candidate"][target]))
                or near_enemies(positions[i], ctx)):
            continue
        tx, ty = x + DX[d], y + DY[d]
        if not (0 <= tx < SIZE and 0 <= ty < SIZE) or ctx["point_tiles"][tx, ty] or ctx["candidate"][tx, ty]:
            continue
        others = positions[live & (np.asarray(ids) != uid)]
        crowd = np.min(np.abs(others - positions[i]).sum(1))
        # Prefer a ship whose release opens a second route while another ship covers its vicinity.
        rank = (int(crowd <= 2), min(15, int(x + y)), min(100, ctx["ally_ene"][uid]), -uid)
        ranking.append((rank, PublicOptions(ctx, uid, i, positions, ids, masks, directions, live)))
    for _, candidate in sorted(ranking, key=lambda item: item[0], reverse=True):
        if any(candidate.first_allowed(d) for d in (1, 2, 3, 4)):
            return candidate
    return None


def route_features(frame, history, turn):
    ctx = frame.ctx
    x, y = frame.origin
    sx_all, sy_all = x + TRAIL_X, y + TRAIL_Y
    inside = (sx_all >= 0) & (sx_all < SIZE) & (sy_all >= 0) & (sy_all < SIZE)
    sx, sy = np.clip(sx_all, 0, SIZE - 1), np.clip(sy_all, 0, SIZE - 1)
    clear = inside & ctx["passable"][sx, sy]
    safe_first = np.array([True] + [frame.first_allowed(d) for d in (1, 2, 3, 4)])
    clear[:, 0] &= safe_first[DIRECTIONS[:, 0]]
    prefix = np.logical_and.accumulate(clear, axis=1)
    length = prefix.sum(1)
    selected = np.flatnonzero(length >= 4)
    if len(selected) <= 1:
        return None
    length = length[selected]
    time = np.minimum(np.arange(STEPS)[None, :], length[:, None] - 1)
    sx = np.take_along_axis(sx[selected], time, axis=1)
    sy = np.take_along_axis(sy[selected], time, axis=1)
    ex, ey = sx[:, -1], sy[:, -1]
    teamd = np.min(np.abs(sx[..., None] - frame.others[:, 0])
                   + np.abs(sy[..., None] - frame.others[:, 1]), axis=2)
    original_teamd = np.min(np.abs(frame.others - frame.origin).sum(1))
    en = np.asarray(ctx["enemy_coords"]).reshape(-1, 2)
    risk = (np.min(np.maximum(np.abs(sx[..., None] - en[:, 0]), np.abs(sy[..., None] - en[:, 1])),
                   axis=(1, 2)) if len(en) else np.full(len(sx), 24))
    sensor_x = sx[..., None] + OFFSETS[:, 0]
    sensor_y = sy[..., None] + OFFSETS[:, 1]
    valid = (sensor_x >= 0) & (sensor_x < SIZE) & (sensor_y >= 0) & (sensor_y < SIZE)
    fx = sensor_x.clip(0, SIZE - 1)
    fy = sensor_y.clip(0, SIZE - 1)
    seen = history.last_seen[fx, fy]
    seen_since_activation = (1 - np.clip((seen + 1) / 50., 0, 1))
    freshness = seen_since_activation * valid
    visit = history.last_visit[sx, sy]
    n = len(selected)
    fill = lambda v: np.full(n, v)
    distance_center = lambda a, b: np.abs(a - 11.5) + np.abs(b - 11.5)
    features = [
        (ex + ey) / 46, np.minimum.reduce([ex, ey, 23 - ex, 23 - ey]) / 11,
        (abs(x + y - 23) - abs(ex + ey - 23)) / STEPS,
        (distance_center(x, y) - distance_center(ex, ey)) / STEPS,
        (x + y - ex - ey) / STEPS, abs(ex - ey) / 23,
        (teamd[:, -1] - original_teamd) / STEPS, np.minimum(teamd[:, -1], 16) / 16,
        np.minimum(teamd, 16).mean(1) / 16, np.maximum(0, 8 - risk) / 8,
        np.clip(ctx["energy_map"][sx, sy], -20, 20).mean(1) / 20, ctx["nebula"][sx, sy].mean(1),
        length / STEPS, fill(turn / 100), fill(np.mean(history.last_seen >= 0)), fill(len(frame.own) / 16),
        fill(min(1, frame.energy / 100)), DIRECTIONS[selected, 0] == frame.original, selected != 0,
        ((seen < 0) & valid).mean((1, 2)), freshness.mean((1, 2)),
        ((seen < turn - 12) & valid).mean((1, 2)), freshness[:, -2:].mean((1, 2)),
        (visit < 0).mean(1), (visit > turn - 5).mean(1),
        ((seen[:, -1] < 0) & valid[:, -1]).mean(1), (teamd > 3).mean(1),
    ]
    # Count distinct exposed cells once per eight-step route. These phase features let
    # the distance supervision learn where a new sensor footprint tends to be productive.
    footprint = np.zeros((n, SIZE * SIZE), dtype=np.float32)
    rr = np.broadcast_to(np.arange(n)[:, None, None], fx.shape)
    np.maximum.at(footprint, (rr.ravel(), (fx * SIZE + fy).ravel()), freshness.ravel())
    phase = PHASE[X % 6, Y % 6].ravel()
    features.extend(footprint[:, phase == k].sum(1) / 12 for k in range(len(PHASES)))
    return np.stack(features, axis=1).astype(np.float32), selected, length, sx, sy

