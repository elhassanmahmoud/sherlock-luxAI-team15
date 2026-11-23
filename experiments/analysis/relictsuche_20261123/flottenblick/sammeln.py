"""Trace actual eight-tick future visibility separately for every chosen stationary scout."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys

import jax
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from flotte import CHANNELS, DIRECTIONS, History, POWER, STEPS, flat, inputs, option_frame, support
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from luxai_s3.wrappers import LuxAIS3GymEnv
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent

OUT = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/flottenblick")
PACKAGE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
V16 = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
SPLITS = {"train": (161600000, 480), "valid": (161610000, 160), "real": (161615000, 64)}


def panel(split):
    start, n = SPLITS[split]
    seeds = np.arange(start, start + 6*n + 256, dtype=np.int32)
    selected = seeds[np.asarray(jax.jit(jax.vmap(sensor))(seeds)) == 1][:n]
    if len(selected) != n:
        raise ValueError("Insufficient sensor-1 maps")
    return selected.tolist()


def initialize(env, seed, index):
    team = index % 2
    side, other = f"player_{team}", f"player_{1-team}"
    opponent = ("solution92", "v16")[(index // 2) % 2]
    agent = r3_package_agent(side, PACKAGE)
    foe = r3_package_agent(other, PACKAGE) if opponent == "v16" else make_opponent(opponent, other)
    for a, s in ((agent, side), (foe, other)):
        if hasattr(a, "new_game"):
            a.new_game(s)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    obs, info = env.reset(seed=seed)
    if info["params"]["unit_sensor_range"] != 1:
        raise ValueError("Wrong actual range")
    for a in (agent, foe):
        a.set_env_cfg(info["params"])
    return team, side, other, opponent, agent, foe, obs


def ablation_function(env):
    @jax.jit
    def exact(state, params, terrain_at_measurement, team, uid):
        masked = state.units_mask.at[team, uid].set(False)
        before_drift = state.map_features.replace(tile_type=terrain_at_measurement)
        counter = state.replace(units_mask=masked, map_features=before_drift)
        actual = env.jax_env.compute_sensor_masks(counter, params)
        return actual.vision_power_map[team]
    return exact


def capture(env, team, side, obs):
    state = env.state
    power = np.asarray(state.vision_power_map[team], np.int16)
    sensor_ok = np.array_equal(power > 0, np.asarray(obs[side]["sensor_mask"], bool))
    if not sensor_ok:
        raise ValueError("Saved full sensor power differs from actual public observation")
    positions = np.asarray(state.units.position[team], np.int16)
    mask = np.asarray(state.units_mask[team], bool)
    if not np.array_equal(mask, obs[side]["units_mask"][team]) or not np.array_equal(
            positions[mask], np.asarray(obs[side]["units"]["position"])[team][mask]):
        raise ValueError("Own ship positions/flags disagree with public data")
    if team:
        power = power[::-1, ::-1].T
        positions = 23 - positions[:, ::-1]
    return power.copy(), positions.copy(), mask.copy()


def without(frame, uid):
    base, positions, mask = frame
    if not mask[uid]:
        return base.copy()
    return base - POWER[int(flat(positions[uid]))].reshape(24, 24)


def real_check(exact, env, before, team, uid, sample):
    physical = np.asarray(exact(env.state, env.env_params, before, team, uid))
    if team:
        physical = physical[::-1, ::-1].T
    if not np.array_equal(physical, without(sample, uid)):
        raise ValueError("Original engine's recomputed no-scout power is different")


def source():
    paths = [HERE / n for n in ("flotte.py", "sammeln.py", "PLAN.md")]
    paths += [HERE.parent/"routenlernen/routes.py", HERE.parent/"vergleich/panel.py", PACKAGE]
    if sha256(PACKAGE.read_bytes()).hexdigest() != V16:
        raise ValueError("Wrong V16")
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in paths}


def collection(env, exact, seed, index, out):
    team, side, other, opponent, agent, foe, obs = initialize(env, seed, index)
    history = History()
    samples, snapshots = [], []
    last_tick = 0
    checks = 0
    for t in range(85):
        current = capture(env, team, side, obs)
        snapshots.append(current)
        history.observe(t, obs[side], team)
        # Include eight ticks after the last usable pre-discovery prefix.
        if t and (history.finished or t > 76) and t >= last_tick + STEPS:
            break
        original = agent.act(t, obs[side])
        state = getattr(agent._imitation, "last_fz", None)
        history.proposals(state, original, team)
        if 16 <= t <= 76 and (t - 16) % 4 == 0 and not history.finished:
            frm = option_frame(state, original, history, team)
            if frm is not None:
                ids, lengths, path = support(frm)
                if len(np.unique(DIRECTIONS[ids, 0])) >= 2:
                    x, projections = inputs(frm, history, t)
                    samples.append(dict(turn=t, uid=frm["uid"], x=x.astype(np.float16),
                                        projections=projections, last=history.last_seen.copy(),
                                        ids=ids, lengths=lengths, paths=path))
                    last_tick = t
        before = env.state.map_features.tile_type
        enemy = foe.act(t, obs[other])
        obs, _, _, _, _ = env.step({side: original, other: enemy})
        if samples and (checks == 0 or t == samples[0]["turn"] + STEPS - 1 and checks == 1):
            uid = samples[0]["uid"]
            real_check(exact, env, before, team, uid, capture(env, team, side, obs))
            checks += 1
    require_no_agent_errors(agent, foe)
    features, projections, last, future, true_full = [], [], [], [], []
    turns, uids, ids, lens, paths, offsets = [], [], [], [], [], [0]
    for r in samples:
        seq = snapshots[r["turn"]+1:r["turn"]+STEPS+1]
        if len(seq) != STEPS:
            raise ValueError("Incomplete eight-step future label")
        residual = np.stack([without(s, r["uid"]) for s in seq])
        full = np.stack([s[0] for s in seq])
        if np.any(residual > full):
            raise ValueError("Removing a ship increased sensor power")
        features.append(r["x"]); projections.append(r["projections"]); last.append(r["last"])
        future.append(residual); true_full.append(np.any(full > 0, axis=0))
        turns.append(r["turn"]); uids.append(r["uid"]); ids.extend(r["ids"]); lens.extend(r["lengths"])
        paths.extend(r["paths"]); offsets.append(len(ids))
    def stack(seq, dtype, shape):
        return np.array(seq, dtype=dtype).reshape((-1, *shape))
    if samples and checks < 2:
        raise ValueError("Missing original-engine ablation checks")
    np.savez_compressed(out, x=stack(features, np.float16, (len(CHANNELS), 24, 24)),
                        projections=stack(projections, np.int8, (3, 24, 24)), last=stack(last, np.int8, (24,24)),
                        remaining=stack(future, np.int16, (STEPS, 24, 24)), full=stack(true_full, bool, (24,24)),
                        turn=np.array(turns, np.int8), uid=np.array(uids, np.int8), route=np.array(ids, np.int8),
                        length=np.array(lens, np.int8), paths=stack(paths, np.int16, (STEPS,)), offsets=offsets,
                        checks=checks, seed=seed, team=team, opponent=opponent, observed=len(snapshots))
    return len(samples), checks


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("split", choices=("train", "valid", "all"))
    p.add_argument("--lane", type=int, default=0)
    p.add_argument("--stride", type=int, default=1)
    args = p.parse_args()
    if not (0 <= args.lane < args.stride and os.environ.get("PYTHONHASHSEED") == "0"):
        raise ValueError("Invalid deterministic lane")
    limit_threads()
    binding = source()
    env = LuxAIS3GymEnv(numpy_output=True)
    exact = ablation_function(env)
    try:
        for split in ("train", "valid") if args.split == "all" else (args.split,):
            folder = OUT / split
            folder.mkdir(exist_ok=True, parents=True)
            for i, seed in enumerate(panel(split)):
                if i % args.stride != args.lane:
                    continue
                meta, data = folder/f"{seed}.json", folder/f"{seed}.npz"
                if meta.exists():
                    r = json.loads(meta.read_text())
                    if r["source"] != binding or r["sha256"] != sha256(data.read_bytes()).hexdigest():
                        raise ValueError("Changed source or sample")
                    continue
                pending = data.with_suffix(".tmp.npz")
                samples, checks = collection(env, exact, seed, i, pending)
                pending.replace(data)
                r = dict(seed=seed, index=i, source=binding, samples=samples, checks=checks,
                         sha256=sha256(data.read_bytes()).hexdigest())
                tmp = meta.with_suffix(".tmp")
                tmp.write_text(json.dumps(r) + "\n")
                tmp.replace(meta)
                if (i // args.stride + 1) % 20 == 0:
                    print(split, i, seed, flush=True)
    finally:
        env.close()


if __name__ == "__main__":
    main()
