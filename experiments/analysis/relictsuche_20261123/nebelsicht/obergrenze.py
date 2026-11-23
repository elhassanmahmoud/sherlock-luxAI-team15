"""Necessary one-step geometric conditions, from existing V16 traces and deterministic referee maps."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "punktspeicher"
DX = (0, 0, 1, 0, -1)
DY = (0, -1, 0, 1, 0)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archived(group):
    path = SOURCE / group / "beobachtungen.jsonl.gz"
    assert sha(path) == json.loads((SOURCE / group / "ergebnis.json").read_text())["raw_sha256"]
    with gzip.open(path, "rt") as stream:
        return [json.loads(line) for line in stream]


def has(grid, cell):
    return bool(int(grid, 16) >> cell & 1)


@jax.jit
def drift_changes(speed):
    t = jnp.arange(100, dtype=jnp.int32)
    return ((t-1)*jnp.abs(speed)) % 1 > (t*jnp.abs(speed)) % 1


def geometry(env, seed):
    _, info = env.reset(seed=seed)
    assert info["params"]["unit_sensor_range"] == 1
    params, state = env.env_params, env.state
    speed = params.nebula_tile_drift_speed
    drift = np.asarray(drift_changes(speed), bool)
    sign = int(np.sign(float(speed)))
    grid = np.asarray(state.map_features.tile_type).copy()
    grids = []
    for change in drift:
        grids.append(grid)
        if change:
            grid = np.roll(grid, (sign, -sign), (0,1))
    nodes = np.asarray(state.relic_nodes, int)
    schedule = np.asarray(state.relic_spawn_schedule, int)
    starts = np.asarray(state.relic_nodes_mask, bool)
    return nodes, schedule, starts, grids, int(params.nebula_tile_vision_reduction)


def inspect(raw, board):
    nodes, schedule, reset, grids, reduction = board
    modes = [reset] + [(schedule >= 0) & (schedule <= t) for t in range(100)]
    sight = 101
    first_credit = 101
    for t in range(101):
        p, monitor = raw["public"][t], raw["policy"][t]
        mask = [bool(active) and has(monitor["visible"], int(x)*24+int(y)) for (x,y),active in zip(nodes,modes[t],strict=True)]
        assert bool(mask[0] or mask[3]) == p["epoch_seen"] and sum(bool(v) for v in modes[t]) <= 2
        if any(mask): sight = min(sight,t)
        if p["points"] > 0: first_credit = min(first_credit,t)
    choices = []
    free_times = 0
    original_actions = 0
    for t in range(min(sight-1,100)):
        data, observed = raw["policy"][t], raw["public"][t]
        points = int(data["point"], 16)
        seen_free = False
        active = [(int(x),int(y)) for (x,y),live in zip(nodes,modes[t+1],strict=True) if live]
        terrain = grids[t]
        hidden_nebula = [(x,y) for x,y in active if terrain[x,y] == 1 and reduction > 0]
        for uid, origin, submitted, assigned, legality in data["free"]:
            if points >> origin & 1 or (assigned is not None and points >> assigned & 1):
                continue
            seen_free = True
            x,y = divmod(origin,24)
            for direction in range(1,5):
                if direction == submitted:
                    continue
                a,b = x+DX[direction],y+DY[direction]
                if not (0 <= a < 24 and 0 <= b < 24) or terrain[a,b] == 2:
                    continue
                original_actions += 1
                near = [24*i+j for i,j in hidden_nebula if max(abs(i-a),abs(j-b)) == 1]
                if near:
                    choices.append(dict(t=t,uid=uid,original=submitted,origin=origin,d=direction,to=a*24+b,
                                        local_mask=bool(legality>>direction&1), nodes=near, precredit=observed["points"]==0))
        free_times += seen_free
    return dict(seed=raw["seed"],team=raw["team"],sight=sight,credit=first_credit,reduction=reduction,
                free_times=free_times, physically_legal_alternatives=original_actions, choices=choices)


def main():
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for group in ("archiv", "frisch"):
            games = archived(group)
            result = []
            board = None
            last = None
            for raw in games:
                if raw["seed"] != last:
                    board = geometry(env,raw["seed"]); last = raw["seed"]
                result.append(inspect(raw,board))
            folder = HERE/group
            folder.mkdir(exist_ok=True)
            data = (json.dumps(result,sort_keys=True, separators=(",", ":"))+"\n").encode()
            path=folder/"geometrie.json.gz"
            if path.exists():
                assert gzip.decompress(path.read_bytes())==data
            else:
                path.write_bytes(gzip.compress(data,mtime=0))
            print(group,len(result),"archived original openings geometrically checked",flush=True)
    finally:
        env.close()


if __name__ == "__main__":
    main()
