"""Öffentlicher einzelner Suchauftrag neben der eingefrorenen V16-Policy."""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
from scipy.signal import convolve2d

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.r3_package import r3_package_agent

PACKAGE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
DIRS = ((0,0), (0,-1), (1,0), (0,1), (-1,0))
MIRROR = (0,2,1,4,3)


class Scout:
    def __init__(self, side, enable=True):
        self.base = r3_package_agent(side, PACKAGE)
        self.enable = enable

    def __getattr__(self, key):
        return getattr(self.base, key)

    def new_game(self, side):
        self.base.new_game(side)
        self.uid = self.goal = self.start = None
        self.finished = False
        self.reason = None
        self.changes = []
        self.pair_turn = self.known_at_third = None

    def end(self, why):
        self.finished = True
        self.reason = why

    def act(self, step, obs):
        original = self.base.act(step, obs)
        inner = self.base._imitation
        b = inner.belief
        t = b.match_step
        if b.match_idx == 2 and t == 1:
            self.known_at_third = int(b.point_tiles.sum())
        if b.match_idx != 1:
            return original
        if b.known_pairs() >= 2 and self.pair_turn is None:
            self.pair_turn = t
        if not self.enable or self.finished or t < 50:
            return original
        if b.known_pairs() >= 2:
            self.end("zweites_paar")
            return original
        if t > 79 or (self.start is not None and t >= self.start + 20):
            self.end("suchzeit")
            return original
        if b.known_pairs() != 1 or (self.start is None and b.candidate.any()):
            return original
        cache = inner.last_fz
        if cache is None:
            if self.uid is not None:
                self.end("keine_einheit")
            return original
        ctx, ids, _, masks, _, _, _ = cache
        pos = np.asarray(ctx["ally_pos"])
        blocked = np.asarray(ctx["ally_count"]) > 0
        enemies = np.asarray(ctx["enemy_coords"], dtype=int).reshape(-1, 2)
        blocked[enemies[:, 0], enemies[:, 1]] = True
        board = b.passable & ~b.nebula & ~b.point_tiles & ~blocked
        affordable = max(20, 6 * float(ctx["move_cost"]))
        rows = []
        for i, uid in enumerate(ids):
            uid = int(uid)
            if self.uid is not None and self.uid != uid:
                continue
            x, y = map(int, pos[uid])
            base_d = int(original[uid][0])
            if (base_d == 5 or b.point_tiles[x, y] or ctx["ally_ene"][uid] < affordable):
                continue
            if b.mirrored:
                base_d = MIRROR[base_d]
            dx, dy = DIRS[base_d]
            bx, by = x+dx, y+dy
            if 0 <= bx < b.W and 0 <= by < b.H and b.point_tiles[bx, by]:
                continue
            rows.append((uid, i, x, y, base_d))
        if not rows:
            if self.uid is not None:
                self.end("einheit_gebunden_oder_zu_wenig_energie")
            return original
        from sherlock.features import bfs_maps
        walk = board.copy()
        # Eigener Start ist belegt, jedoch ein angemessener freier virtueller Start.
        starts = [(x,y) for _,_,x,y,_ in rows]
        # bfs_maps initialisiert die Startkachel selbst und darf durch keine andere
        # bereits belegte Startkachel laufen.
        dist = bfs_maps(walk, np.asarray(starts))
        xx, yy = np.indices(board.shape)
        unseen = b.last_seen < 49
        allowed = board & unseen & (xx+yy <= b.W-1)
        vision = int(inner.env_cfg["unit_sensor_range"])
        reach = np.arange(-vision, vision+1)
        window = np.abs(reach[:, None]) + np.abs(reach[None, :]) <= vision
        gain = convolve2d(unseen.astype(np.int16), window.astype(np.int16), mode="same")
        candidates = []
        for j,(uid,i,x,y,base_d) in enumerate(rows):
            possible = allowed & (dist[j] > 0)
            if self.goal is not None and possible[self.goal]:
                positions = [self.goal]
            else:
                positions = map(tuple, np.argwhere(possible))
            for gx, gy in positions:
                d = int(dist[j,gx,gy])
                g = int(gain[gx,gy])
                if g:
                    candidates.append((g/(1+d), -d, float(ctx["ally_ene"][uid]), -uid, -int(gx), -int(gy), j))
        if not candidates:
            if self.uid is not None:
                self.end("kein_suchziel")
            return original
        # Weg vom Ziel ermitteln. Die echte Aktionsmaske bleibt für jeden ersten Schritt verbindlich.
        _, neg_d, _, _, nx, ny, j = max(candidates)
        uid, i, x, y, base_d = rows[j]
        target = (-nx, -ny)
        backwards = bfs_maps(walk, np.asarray([target]))[0]
        best = []
        for direction, (dx,dy) in enumerate(DIRS[1:], start=1):
            ax, ay = x+dx, y+dy
            if (0 <= ax < b.W and 0 <= ay < b.H and masks[i][direction] and board[ax,ay]
                    and backwards[ax,ay] == -neg_d-1):
                best.append(direction)
        if not best:
            if self.uid is not None:
                self.end("kein_erlaubter_weg")
            return original
        d = base_d if base_d in best else best[0]
        if self.uid is None:
            self.uid, self.start = uid, t
        self.goal = target
        if d == base_d:
            return original
        changed = original.copy()
        changed[uid] = [MIRROR[d] if b.mirrored else d, 0, 0]
        if not masks[i][d] or np.count_nonzero(np.any(changed != original, axis=1)) != 1:
            raise ValueError("Verletzte Aktionsbedingung")
        inner._prev_actions[uid] = d
        self.changes.append([t, uid, int(original[uid,0]), int(changed[uid,0]), int(target[0]), int(target[1])])
        return changed
