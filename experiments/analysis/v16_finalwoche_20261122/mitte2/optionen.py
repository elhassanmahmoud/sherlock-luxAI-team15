"""Exact frozen option calculation, with the time window delegated to the caller.
The structural identity check in mitte.py compares this body with zugnutzen/berater.py.
"""
from berater import Counter, g, np, logsumexp, POINT, IDENTITY, NAMES


def options(self, actions):
    p = self.base._imitation
    fz = p.last_fz
    if fz is None:
        return []
    ctx, ids, f, masks, _, planes, pos = fz
    live = np.asarray([ctx["ally_ene"][u] >= 0 for u in ids])
    masks = masks.copy()
    masks[:, 5] = [ctx["ally_ene"][u] >= ctx["sap_cost"] for u in ids]
    logp = np.zeros(masks.shape, dtype=np.float32)
    for heads in self.scores:
        valid = np.where(masks, heads, -np.inf)
        logp += valid - logsumexp(valid, axis=1, keepdims=True)
    holders = set(p._point_holder_rows(ctx, ids, pos))
    logp[[i for i in range(len(ids)) if i not in holders], 0] -= float(p.cfg.imit_stay_bias)
    original = actions[ids, 0]
    move = np.where(original <= 4, original, 0)
    if p.belief.mirrored:
        move = g.MIRROR_DIR[move]
    destinations = pos + np.stack((g.DIR_DX[move], g.DIR_DY[move]), axis=1)
    planned = Counter(map(tuple, destinations[live]))
    occupied = Counter(map(tuple, pos[live]))
    live &= (original <= 4) & (f[:, POINT].max(axis=1) > 0) & masks[np.arange(len(ids)), move]
    candidates = []
    for k in np.flatnonzero(live):
        a = int(move[k])
        values = logp[k, :5].copy()
        values[a] = -np.inf
        alt = int(values.argmax())
        if not np.isfinite(values[alt]):
            continue
        gap = float(logp[k, a] - values[alt])
        if abs(gap) > 3:
            continue
        bxy = tuple(destinations[k].tolist())
        cxy = (int(pos[k,0]) + int(g.DIR_DX[alt]), int(pos[k,1]) + int(g.DIR_DY[alt]))
        if not all(0 <= z < 24 for z in (*bxy, *cxy)):
            raise ValueError("Movement outside known legal bounds")
        attr = [gap / 3, min(planned[bxy],4)/4, min(planned[cxy],4)/4,
                min(occupied[bxy],4)/4, min(occupied[cxy],4)/4,
                float(planes[0][bxy]), float(planes[0][cxy]),
                float(planes[11][bxy]), float(planes[11][cxy])]
        x = np.concatenate((f[k], IDENTITY[a], IDENTITY[alt], np.asarray(attr, dtype=np.float32)))
        if x.shape != (len(NAMES),) or not np.isfinite(x).all():
            raise ValueError("Invalid public state")
        real = g.mirror_dir(alt) if p.belief.mirrored else alt
        candidates.append((abs(gap), int(ids[k]), real, x))
    return sorted(candidates, key=lambda item: (item[0], item[1]))[:2]

