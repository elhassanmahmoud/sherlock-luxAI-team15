"""Re-run each promising decision with every legal cardinal direction and the original STAY."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random

import jax
import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.scoring import match_points_after_step
from steuern import AntiStall, HERE, PACKAGE, outcome


def roster(split):
    first, n = {"train": (161500000, 768), "hold": (161510000, 160)}[split]
    seeds = np.arange(first, first + n*8, dtype=np.int32)
    answer = seeds[np.asarray(jax.jit(jax.vmap(sensor))(seeds)) == 1][:n]
    if len(answer) != n:
        raise ValueError("Missing sensor=1 cards")
    return answer


def game(env, seed, team, direction):
    side, other = f"player_{team}", f"player_{1-team}"
    policy = AntiStall(side, force=direction)
    rival = make_opponent("solution92", other)
    for player, seat in ((policy, side), (rival, other)):
        if hasattr(player, "new_game"):
            player.new_game(seat)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    obs, cfg = env.reset(seed=seed)
    if int(cfg["params"]["unit_sensor_range"]) != 1:
        raise ValueError("Sensor selection")
    for a in (policy, rival):
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(cfg["params"])
    signature = hashlib.sha256()
    anchor = None
    first = credit = 101
    for t in range(101):
        own = obs[side]
        if int(own["match_steps"]) != t:
            raise ValueError("Mismatched timeline")
        if np.any(own["relic_nodes_mask"]):
            first = min(first, t)
        had_event = policy.event is not None
        com = policy.act(t, own)
        foe = rival.act(t, obs[other])
        if not had_event:
            for a in (own["units"]["position"], own["units"]["energy"], own["sensor_mask"], foe):
                signature.update(np.asarray(a).tobytes())
            if policy.event:
                anchor = signature.hexdigest()
            else:
                signature.update(com.tobytes())
        obs, _, done, trunc, info = env.step({side: com, other: foe})
        if done[side] or trunc[side]:
            raise ValueError("Premature game end")
        points = np.asarray(match_points_after_step(own, obs[side], info), int)
        if points[team] > 0:
            credit = min(t, credit)
    wins = np.asarray(obs[side]["team_wins"], int)
    if wins.sum() != 1:
        raise ValueError("Match not complete")
    require_no_agent_errors(policy.base, rival)
    return policy.event, anchor, dict(y=outcome(first, credit, points[team], points[1-team]),
                                      changes=policy.changes, win=int(wins[team]))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", type=Path)
    p.add_argument("split", choices=("train", "hold"))
    p.add_argument("lane", type=int)
    p.add_argument("stride", type=int)
    a = p.parse_args()
    if not 0 <= a.lane < a.stride or os.getenv("PYTHONHASHSEED") != "0":
        raise ValueError("Worker or randomness configuration")
    limit_threads()
    files = (HERE/"PLAN.md", HERE/"steuern.py", HERE/"zweige.py",
             HERE.parent/"zielschaetzer/kandidat.py", HERE.parent/"zielschaetzer/ort.json", PACKAGE)
    signature = {str(f.relative_to(HERE.parents[3])): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    output = a.folder/a.split
    output.mkdir(parents=True, exist_ok=True)
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for i, seed in enumerate(roster(a.split)):
            if i % a.stride != a.lane:
                continue
            seed, team = int(seed), i % 2
            path = output/f"{seed}.json"
            if path.exists():
                if json.loads(path.read_text())["files"] != signature:
                    raise ValueError("Pre-existing result from other sources")
                continue
            event, anchor, original = game(env, seed, team, 0)
            trials = {}
            if event:
                for key in event["x"]:
                    event2, anchor2, result = game(env, seed, team, int(key))
                    if event != event2 or anchor != anchor2 or not 1 <= result["changes"] <= 3:
                        raise ValueError(f"Unmatched replay or invalid intervention on {seed}/{key}")
                    trials[key] = result
            record = dict(index=i, seed=seed, team=team, files=signature, anchor=anchor, event=event,
                          original=original, trials=trials)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(record, allow_nan=False))
            tmp.replace(path)
            print(seed, len(trials), flush=True)
    finally:
        env.close()


if __name__ == "__main__":
    main()
