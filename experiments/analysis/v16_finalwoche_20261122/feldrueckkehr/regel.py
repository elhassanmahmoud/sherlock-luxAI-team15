"""A one-step return to a recently occupied tile. All inputs come from the playing side."""
from __future__ import annotations

import math
import numpy as np

DIR = ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0))
MIRROR = (0, 2, 1, 4, 3, 5)


class ReturnPolicy:
    def __init__(self, player):
        self.player = player
        self.inner = player._imitation
        self.logp = None
        native = self.inner._unstack_actions

        def record(ctx, ids, pos, logp, actions):
            self.logp = logp
            return native(ctx, ids, pos, logp, actions)

        self.inner._unstack_actions = record
        self.last = {}
        self.streak = {}
        self.established = {}
        self.match = None

    def options(self, obs, base):
        b = self.inner.belief
        if self.match != b.match_idx:
            self.match = b.match_idx
            self.last.clear()
            self.streak.clear()
            self.established.clear()
        step = int(b.match_step)
        if not step or self.inner.last_fz is None:
            self.streak.clear()
            return [], set()
        ctx, ids, _, masks, _, _, pos = self.inner.last_fz
        if self.logp is None or self.logp.shape != masks.shape:
            raise ValueError('No released ensemble decision for this observation')
        alive = [(k, int(uid), tuple(map(int, pos[k]))) for k, uid in enumerate(ids)
                 if ctx['ally_ene'][uid] >= 0]
        occupied = {p for _, _, p in alive}
        for tile in occupied:
            run = self.streak.get(tile, 0) + 1 if self.last.get(tile) == step - 1 else 1
            self.streak[tile] = run
            self.last[tile] = step
            if run >= 2:
                self.established[tile] = step
            else:
                self.established.pop(tile, None)
        if not 65 <= step <= 94:
            return [], set()
        sensor = np.asarray(obs['sensor_mask'], dtype=bool)
        if b.mirrored:
            sensor = sensor[::-1, ::-1].T
        enemies = {tuple(map(int, xy)) for xy in ctx['enemy_coords']}
        canonical = {uid: MIRROR[int(base[uid, 0])] if b.mirrored else int(base[uid, 0]) for _, uid, _ in alive}
        dest = {}
        for _, uid, (x,y) in alive:
            act = canonical[uid]
            dx,dy = DIR[act] if 1 <= act <= 4 else (0,0)
            dest[uid] = (x + dx, y + dy)
        incoming = set(dest.values())
        vacant = {tile for tile, t in self.established.items() if 1 <= step - t <= 8 and b.point_tiles[tile]
                  and sensor[tile] and tile not in occupied and tile not in enemies and tile not in incoming}
        choices = []
        for k, uid, (x,y) in alive:
            a = canonical[uid]
            energy = float(ctx['ally_ene'][uid]) - float(ctx['move_cost'])
            if a == 5 or b.point_tiles[x,y] or b.point_tiles[dest[uid]] or energy < 10:
                continue
            for move,(dx,dy) in enumerate(DIR[1:], 1):
                tile = x+dx, y+dy
                if tile not in vacant or not masks[k,move]:
                    continue
                gap = float(self.logp[k,a] - self.logp[k,move])
                if not math.isfinite(gap) or gap > math.log(8):
                    continue
                w = (b.W-1-tile[1], b.H-1-tile[0]) if b.mirrored else tile
                choices.append(dict(uid=uid, old=int(base[uid,0]), move=MIRROR[move] if b.mirrored else move,
                                    canon=move, tile=list(tile), world=list(w), gap=gap, energy=energy))
        choices.sort(key=lambda c: (c['gap'], -c['energy'], c['uid'], c['tile']))
        return choices, vacant

    def apply(self, base, option):
        result = base.copy()
        uid = option['uid']
        result[uid] = [option['move'], 0, 0]
        self.inner._prev_actions[uid] = option['canon']
        return result
