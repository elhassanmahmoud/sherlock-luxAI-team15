"""Paired real openings with four precommitted search routes on disjoint low-vision maps."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import sys

import jax
import jax.numpy as jnp
import numpy as np
import torch
from luxai_s3.params import env_params_ranges
from luxai_s3.wrappers import LuxAIS3GymEnv

from kandidat import HERE, PACKAGE, RELEASE, OpeningRoute
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.scoring import match_points_after_step


def sensor(seed):
    key, _ = jax.random.split(jax.random.key(seed))
    for name, choices in env_params_ranges.items():
        key, subkey = jax.random.split(key)
        if name == "unit_sensor_range":
            return jax.random.choice(subkey, jnp.asarray(choices))
    raise KeyError("unit_sensor_range")


def maps(split):
    start, count = {"train": (161300000, 320), "check": (161310000, 80)}[split]
    pool = np.arange(start, start + count * 8, dtype=np.int32)
    sensed = jax.jit(jax.vmap(sensor))(pool)
    selected = pool[np.asarray(sensed) == 1][:count]
    if len(selected) != count:
        raise ValueError("Insufficient low-vision maps")
    return selected


def play(env, seed, team, arm):
    side, other = f"player_{team}", f"player_{1-team}"
    actor = OpeningRoute(side, forced=arm)
    enemy = make_opponent("solution92", other)
    for agent, label in ((actor, side), (enemy, other)):
        if hasattr(agent, "new_game"):
            agent.new_game(label)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    obs, setup = env.reset(seed=seed)
    if int(setup["params"]["unit_sensor_range"]) != 1:
        raise ValueError("Generator and course disagree")
    for a in (actor, enemy):
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(setup["params"])
    first_sight = first_credit = 101
    prefix = hashlib.sha256()
    anchor = None
    for turn in range(101):
        view = obs[side]
        if int(view["match_steps"]) != turn:
            raise ValueError("Match was not contiguous")
        if np.any(view["relic_nodes_mask"]):
            first_sight = min(turn, first_sight)
        previous = actor.event
        a = actor.act(turn, view)
        b = enemy.act(turn, obs[other])
        if previous is None and actor.event:
            for array in (view["units"]["position"], view["units"]["energy"], view["sensor_mask"], b):
                prefix.update(np.asarray(array).tobytes())
            anchor = prefix.hexdigest()
        if actor.event is None:
            prefix.update(np.asarray(a).tobytes())
            prefix.update(np.asarray(b).tobytes())
        obs, _, done, truncated, info = env.step({side: a, other: b})
        if done[side] or truncated[side]:
            raise ValueError("Early end")
        pts = np.asarray(match_points_after_step(view, obs[side], info), dtype=int)
        if pts[team] > 0:
            first_credit = min(turn, first_credit)
        if turn == 70:
            margin = int(pts[team] - pts[1-team])
    require_no_agent_errors(actor.base, enemy)
    return actor.event, anchor, dict(y=[first_sight, first_credit, margin], changes=actor.changes,
                                     win=int(obs[side]["team_wins"][team]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("split", choices=("train", "check"))
    parser.add_argument("lane", type=int)
    parser.add_argument("stride", type=int)
    args = parser.parse_args()
    if not 0 <= args.lane < args.stride or os.environ.get("PYTHONHASHSEED") != "0":
        raise ValueError("Worker setup")
    limit_threads()
    fingerprint = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in (HERE/"PLAN.md", HERE/"kandidat.py", HERE/"spuren.py", PACKAGE)}
    if fingerprint[PACKAGE.name] != RELEASE:
        raise ValueError("Unexpected incumbent")
    output = args.folder / args.split
    output.mkdir(parents=True, exist_ok=True)
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for number, seed in enumerate(maps(args.split)):
            if number % args.stride != args.lane:
                continue
            seed, team = int(seed), number % 2
            dest = output / f"{seed}.json"
            if dest.exists():
                if json.loads(dest.read_text())["sources"] != fingerprint:
                    raise ValueError("Different sources")
                continue
            event, anchor, original = play(env, seed, team, -1)
            trials = []
            if event:
                for arm in range(3):
                    other_event, other_anchor, values = play(env, seed, team, arm)
                    if event != other_event or anchor != other_anchor:
                        raise ValueError(f"Divergent predecision state on seed {seed}, arm {arm}")
                    trials.append(values)
            temp = dest.with_suffix(".tmp")
            temp.write_text(json.dumps(dict(seed=seed, team=team, event=event, anchor=anchor,
                                            original=original, trials=trials, sources=fingerprint)))
            temp.replace(dest)
            print(seed, team, original["y"], [r["changes"] for r in trials], flush=True)
    finally:
        env.close()


if __name__ == "__main__":
    main()
