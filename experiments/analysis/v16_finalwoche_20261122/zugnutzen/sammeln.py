"""One-ply paired engine interventions. The real season always continues with the released policy."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import random

import jax
import numpy as np
import torch

from berater import HERE, NAMES, PACKAGE, Policy, V16
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import point_tile_map, match_points_after_step
from luxai_s3.wrappers import LuxAIS3GymEnv


def occupations(state):
    tiles = point_tile_map(state)
    xy = np.asarray(state.units.position)
    alive = np.asarray(state.units_mask) & (np.asarray(state.units.energy[..., 0]) >= 0)
    amount = []
    for team in range(2):
        pos = xy[team, alive[team]]
        fields = set(map(tuple, pos[tiles[pos[:,0], pos[:,1]]]))
        amount.append(len(fields))
    return np.array(amount, np.int16)


def games(split):
    start, n = (160364000, 96) if split == "train" else (160364200, 32)
    for i in range(n):
        yield start+i, "player_" + str(i%2), ("solution92", "kaggle3")[i//2%2]


def run(out, split, offset, stride):
    if os.getenv("PYTHONHASHSEED") != "0" or sha256(PACKAGE.read_bytes()).hexdigest() != V16 or not verify():
        raise ValueError("Experiment identity mismatch")
    limit_threads()
    env = LuxAIS3GymEnv(numpy_output=True)
    out.mkdir(parents=True, exist_ok=True)
    spec = sha256((HERE/"PLAN.md").read_bytes() + (HERE/"berater.py").read_bytes() + (HERE/"sammeln.py").read_bytes()).hexdigest()
    try:
        for seed, side, kind in list(games(split))[offset::stride]:
            record = out / f"{seed}.json"
            path = out / f"{seed}.npz"
            if record.exists():
                r = json.loads(record.read_text())
                if r["source"] != spec or r["sha256"] != sha256(path.read_bytes()).hexdigest():
                    raise ValueError("Different cached training sample")
                continue
            team = int(side[-1])
            other = "player_" + str(1-team)
            actor = Policy(r3_package_agent(side, PACKAGE))
            rival = make_opponent(kind, other)
            if hasattr(rival, "new_game"):
                rival.new_game(other)
            actor.new_game(side)
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
            obs, info = env.reset(seed=seed)
            for p in (actor, rival):
                if hasattr(p, "set_env_cfg"):
                    p.set_env_cfg(info["params"])
            features, labels, turns, ids, directions = [], [], [], [], []
            calibration = False
            for step in range(303):
                act = actor.act(step, obs[side])
                enemy = rival.act(step, obs[other])
                pair = {side: act, other: enemy}
                matching = None
                counter = []
                if actor.last:
                    _, key = jax.random.split(env.rng_key)
                    def branch(commands):
                        info_alt = env.jax_env.step(key, env.state, commands, env.env_params)[-1]
                        return occupations(info_alt["final_state"])
                    if not calibration:
                        matching = branch(pair)
                    for _, uid, alt, x in actor.last:
                        changed = act.copy()
                        changed[uid] = [alt, 0, 0]
                        if np.count_nonzero(np.any(changed != act, axis=1)) != 1:
                            raise ValueError("Not a single-ship intervention")
                        counter.append((branch({side: changed, other: enemy}), uid, alt, x))
                nxt, _, term, trunc, info = env.step(pair)
                if counter:
                    actual = occupations(info["final_state"])
                    gain = match_points_after_step(obs[side], nxt[side], info) - obs[side]["team_points"]
                    if not np.array_equal(actual, gain) or (matching is not None and not np.array_equal(matching, actual)):
                        raise ValueError("Counterfactual and true engine diverge")
                    calibration = True
                    for cf, uid, alt, x in counter:
                        delta = cf - actual
                        features.append(x)
                        labels.append((int(delta[team]), int(delta[1-team])))
                        turns.append(step)
                        ids.append(uid)
                        directions.append([int(act[uid, 0]), alt])
                obs = nxt
                if (bool(term[side]) or bool(trunc[side])) != (step == 302):
                    raise ValueError("Incomplete official season")
            require_no_agent_errors(actor.base, rival)
            tmp = path.with_suffix(".pending.npz")
            np.savez_compressed(tmp, x=np.asarray(features, dtype=np.float32).reshape(-1, len(NAMES)),
                                delta=np.asarray(labels, dtype=np.int16).reshape(-1,2),
                                step=np.asarray(turns, np.int16), uid=np.asarray(ids, np.int8),
                                actions=np.asarray(directions, np.int8).reshape(-1,2))
            tmp.replace(path)
            row = dict(source=spec, package=V16, sha256=sha256(path.read_bytes()).hexdigest(), seed=seed,
                       side=side, opponent=kind, split=split, steps=303, alternatives=len(labels),
                       calibration=calibration, final_matches=np.asarray(obs[side]["team_wins"]).tolist())
            tmp = record.with_suffix(".pending")
            tmp.write_text(json.dumps(row) + "\n")
            tmp.replace(record)
            print(seed, len(labels), flush=True)
    finally:
        env.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("out", type=Path)
    p.add_argument("split", choices=("train", "valid"))
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--stride", type=int, default=1)
    a = p.parse_args()
    if not 0 <= a.offset < a.stride:
        p.error("Invalid lane")
    run(a.out, a.split, a.offset, a.stride)
