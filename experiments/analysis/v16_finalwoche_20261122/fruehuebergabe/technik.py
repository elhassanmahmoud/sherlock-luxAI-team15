"""Whole-game validation of both relay phases and the high-visibility identity."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import random

import numpy as np
import torch
from staffel import HERE, R3, R3_SHA, V16, V16_SHA, Relay, r3_package_agent
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors


class Witness:
    def __init__(self, side, gold, low):
        self.relay = Relay(side)
        self.v16 = r3_package_agent(side, V16)
        self.gold = gold
        self.low = low
        self.count = 0
        self.earlier_difference = 0
        self.seen = False

    def new_game(self, side):
        self.relay.new_game(side)
        self.v16.new_game(side)

    def set_env_cfg(self, cfg):
        if self.low != (int(cfg["unit_sensor_range"]) <= 2):
            raise ValueError("Unexpected known technical seed")
        self.relay.set_env_cfg(cfg)
        self.v16.set_env_cfg(cfg)

    def act(self, step, obs):
        actual = self.relay.act(step, obs)
        reference = self.v16.act(step, obs)
        if self.low and step <= 40:
            expected = self.gold[step]
            if not np.array_equal(actual, expected):
                raise ValueError(f"R3 package diverged from original archive at {step}")
            self.earlier_difference += int(np.any(actual != reference))
            # Independent reference follows only the original R3 commands committed to the archive.
            model = self.v16._imitation
            for uid in model._prev_actions:
                code = int(expected[uid, 0])
                model._prev_actions[uid] = (0,2,1,4,3,5)[code] if model.belief.mirrored else code
            if model.param_est._prev is not None:
                model.param_est._prev["act"] = expected.copy()
            model._sap_hits.clear()
        elif not np.array_equal(actual, reference):
            raise ValueError(f"Relay differed from independently followed V16 at {step}")
        if self.low and step == 41:
            self.seen = True
        self.count += 1
        return actual


def run(lane, raw):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    if sha256(R3.read_bytes()).hexdigest() != R3_SHA or sha256(V16.read_bytes()).hexdigest() != V16_SHA:
        raise ValueError("Unrecognized package")
    side, other = f"player_{lane}", f"player_{1-lane}"
    env = LuxAIS3GymEnv(numpy_output=True)
    summary = []
    try:
        for low in (True, False):
            seed = (7261004, 7261005)[lane] if low else 7261000
            gold = None
            raw_sha = None
            if low:
                receipt = json.loads((raw / f"r3_{seed}_{side}.json").read_text())
                path = raw / receipt["filename"]
                raw_sha = sha256(path.read_bytes()).hexdigest()
                if raw_sha != receipt["sha256"] or receipt["package"] != R3_SHA:
                    raise ValueError("Invalid archived original")
                with np.load(path, allow_pickle=False) as histories:
                    gold = histories["commands"]
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
            witness = Witness(side, gold, low)
            opponent = make_opponent("solution92", other)
            result = play_game(env, witness, opponent, seed, side, False)
            require_no_agent_errors(witness.relay.base, opponent)
            require_no_agent_errors(witness.v16, opponent)
            if low:
                require_no_agent_errors(witness.relay.r3, opponent)
            if (result["steps"] != 303 or witness.count != 303 or witness.relay.early != (41 if low else 0)
                    or (low and (not witness.seen or not witness.earlier_difference))):
                raise ValueError("Incomplete phase test")
            summary.append(dict(seed=seed, side=side, sensor=witness.relay.base.env_cfg["unit_sensor_range"],
                                original_archive_sha=raw_sha, r3_identical=witness.relay.early,
                                v16_identical=303-witness.relay.early, divergent_r3_steps=witness.earlier_difference))
    finally:
        env.close()
    (HERE/f"technik_{lane}.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("lane", type=int, choices=(0,1))
    p.add_argument("original_records", type=Path)
    a = p.parse_args()
    run(a.lane, a.original_records)
