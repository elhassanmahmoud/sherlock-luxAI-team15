"""Collect reference openings and gold first-pair labels on reserved map splits."""
import argparse
import random
import sys
from hashlib import sha256
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np

from routes import HERE, NAMES, STEPS, SearchHistory, current, route_features

ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from luxai_s3.params import EnvParams, env_params_ranges
from luxai_s3.state import gen_map
from luxai_s3.wrappers import LuxAIS3GymEnv
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent

PACKAGE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
EXPECTED = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
OUT = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/routenlernen")
SPLITS = {"train": (161030000, 10000, 320),
          "valid": (161040000, 10000, 128), "replay": (161050000, 10000, 32)}


def sensor(seed):
    key, _ = jax.random.split(jax.random.key(seed))
    for field, choices in env_params_ranges.items():
        key, subkey = jax.random.split(key)
        if field == "unit_sensor_range":
            return jax.random.choice(subkey, jnp.array(choices))
    raise KeyError("unit_sensor_range")


def seeds_for(split, normal=False):
    start, width, n = SPLITS[split]
    seeds = np.arange(start, start + min(width, n * 6 + 512), dtype=np.int32)
    values = np.asarray(jax.jit(jax.vmap(sensor))(seeds))
    selected = seeds[(values > 1) if normal else (values == 1)][:n]
    if len(selected) != n:
        raise ValueError("Insufficient maps in fixed split")
    return selected


def gold(seed):
    """Exactly the gym reset's map key. This function lives only in the collector."""
    _, reset_key = jax.random.split(jax.random.key(seed))
    m = gen_map(reset_key, EnvParams(), 1, 24, 24, 6, 6, 5)
    return jnp.concatenate((m["relic_nodes"][0], m["relic_nodes"][3], m["relic_spawn_schedule"][:1]))


def open_game(env, seed, team):
    side, other = f"player_{team}", f"player_{1-team}"
    agent = r3_package_agent(side, PACKAGE)
    opponent = make_opponent("solution92", other)
    for a, s in ((agent, side), (opponent, other)):
        if hasattr(a, "new_game"):
            a.new_game(s)
    random.seed(seed)
    np.random.seed(seed)
    obs, info = env.reset(seed=seed)
    if int(info["params"]["unit_sensor_range"]) != 1:
        raise ValueError("Nonmatching public range")
    for a in (agent, opponent):
        a.set_env_cfg(info["params"])
    return agent, opponent, side, other, obs


def oracle(frame, choices, gold, onset, turn):
    """Training labels for candidate *paths*. Never called by the playing policy."""
    _, _, _, sx, sy = choices
    ax, ay = gold.T
    def travel(x, y):
        return (np.maximum(0, np.abs(x[..., None] - ax) - 1)
                + np.maximum(0, np.abs(y[..., None] - ay) - 1)).min(-1)
    start = float(travel(*frame.origin))
    teammate = float(travel(frame.next_others[:, 0], frame.next_others[:, 1]).min())
    remaining = travel(sx, sy)
    # A stepped direction that merely chases a closer teammate receives less credit.
    # Per-step distances include crossed curves, even when the last tile is farther away.
    advantage = .45 * (start - remaining) + .55 * (min(start, teammate) - np.minimum(teammate, remaining))
    active = (np.arange(1, STEPS + 1) + turn >= onset)
    contact = (remaining == 0) & active
    contact_bonus = (contact * np.linspace(4, 2, STEPS)).max(1)
    return (.5 * advantage.mean(1) + .5 * advantage.max(1) + contact_bonus).astype(np.float32)


def collect(split):
    env = LuxAIS3GymEnv(numpy_output=True)
    directory = OUT / ("direction_" + split)
    directory.mkdir(exist_ok=True)
    try:
        for i, s in enumerate(seeds_for(split)):
            seed, team = int(s), i % 2
            path = directory / f"{seed}.npz"
            if path.exists():
                continue
            agent, foe, side, other, obs = open_game(env, seed, team)
            labels = np.asarray(env.state.relic_nodes)[[0, 3]]
            onset = int(np.asarray(env.state.relic_spawn_schedule)[0]) + 1
            real_gold = np.asarray(gold(seed))
            if not np.array_equal(labels.ravel(), real_gold[:4]) or onset != int(real_gold[-1]) + 1:
                raise ValueError("Gym reset and offline labels disagree")
            features, targets, ticks, selections, offsets = [], [], [], [], [0]
            memory = SearchHistory()
            for t in range(92):
                memory.observe(t, obs[side], team)
                if memory.finished or t == 91:
                    break
                original = agent.act(t, obs[side])
                if t >= 10 and (t - 10) % 4 == 0:
                    frame = current(agent, original, memory)
                    if frame is not None:
                        options = route_features(frame, memory, t)
                        if options is not None:
                            memory.scout = frame.uid
                            features.append(options[0])
                            targets.append(oracle(frame, options, labels, onset, t))
                            selections.append(options[1])
                            ticks.append(t)
                            offsets.append(offsets[-1] + len(options[0]))
                acts = {side: original, other: foe.act(t, obs[other])}
                obs, _, _, _, _ = env.step(acts)
            require_no_agent_errors(agent, foe)
            x = np.concatenate(features) if features else np.empty((0, len(NAMES)), np.float32)
            np.savez_compressed(path, x=x, y=np.concatenate(targets) if targets else [],
                                selections=np.concatenate(selections) if selections else [],
                                offsets=offsets, ticks=ticks, labels=labels, onset=onset, team=team,
                                event=t if memory.finished else -1)
            if (i + 1) % 20 == 0:
                print(split, i + 1, seed, flush=True)
    finally:
        env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("split", choices=("train", "valid", "all"))
    args = parser.parse_args()
    limit_threads()
    if sha256(PACKAGE.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError("V16 file differs")
    OUT.mkdir(parents=True, exist_ok=True)
    for split in ("train", "valid"):
        if args.split in ("all", split):
            collect(split)
