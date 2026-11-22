"""Capture real paired R3/V16 public histories, and reproduce the original archived scores."""
import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent / "solution"))
from sitzvergleich import ANALYSIS, SOURCES, solution_rows
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent

PACKAGES = {
    "r3": ("20261116_r3_finale", "8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d"),
    "v16": ("20261117_sherlock_v16", "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"),
}


def sample():
    data = json.loads((HERE.parent / "kartenparameter/ergebnis.json").read_text())["maps"]
    configs = {r["seed"]: r["unit_sensor_range"] for r in data}
    rows = []
    for panel, (start, tables) in SOURCES.items():
        policies = {name: solution_rows(ANALYSIS / filename, digest, start)
                    for name, (filename, digest) in tables.items()}
        discrepant = set()
        def add(seed, side, group):
            rows.append(dict(panel=panel, seed=seed, side=side, group=group, sensor=configs[seed],
                             expected={k: v[seed, side] for k, v in policies.items()}))
        for seed, side in sorted(policies["v16"]):
            if configs[seed] > 2:
                continue
            v, r = (policies[k][seed, side]["win"] for k in ("v16", "r3"))
            if r != v:
                add(seed, side, "r3_only" if r else "v16_only")
                discrepant.add(seed)
        n = 0
        for seed in range(start, start + 400):
            side = f"player_{n % 2}"
            if configs[seed] <= 2 and seed not in discrepant and all(p[seed, side]["win"] for p in policies.values()):
                add(seed, side, "both")
                n += 1
                if n == 8:
                    break
    if len(rows) != 46 or len({(r["seed"], r["side"]) for r in rows}) != len(rows):
        raise ValueError("Invalid 46-seat diagnostic panel")
    return rows


class Recorder:
    def __init__(self, agent):
        self.base = agent
        self.history = defaultdict(list)

    def __getattr__(self, name):
        return getattr(self.base, name)

    def act(self, step, obs):
        actions = np.asarray(self.base.act(step, obs)).copy()
        if step != len(self.history["commands"]):
            raise ValueError("Decision order changed")
        self.history["commands"].append(actions)
        for key, value in obs.items():
            if isinstance(value, dict):
                for field, leaf in value.items():
                    self.history[key + "/" + field].append(np.array(leaf, copy=True))
            else:
                self.history[key].append(np.array(value, copy=True))
        return actions


def collect(agent_name, destination, offset, stride):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    name, expected_sha = PACKAGES[agent_name]
    package = ROOT / "experiments/releases" / name / "agent.zip"
    if sha256(package.read_bytes()).hexdigest() != expected_sha:
        raise ValueError("Agent identity mismatch")
    destination.mkdir(exist_ok=True, parents=True)
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for seat in sample()[offset::stride]:
            seed, side = seat["seed"], seat["side"]
            stem = f"{agent_name}_{seed}_{side}"
            receipt = destination / (stem + ".json")
            path = destination / (stem + ".npz")
            if receipt.exists():
                saved = json.loads(receipt.read_text())
                if saved["sha256"] != sha256(path.read_bytes()).hexdigest() or saved["seat"] != seat:
                    raise ValueError("Previously stored trajectory differs")
                continue
            actor = Recorder(r3_package_agent(side, package))
            rival = make_opponent("solution92", "player_1" if side == "player_0" else "player_0")
            result = play_game(env, actor, rival, seed, side, train=False)
            require_no_agent_errors(actor.base, rival)
            if len(actor.history["commands"]) != 303 or result["steps"] != 303 or result["point_counting_version"] != 2:
                raise ValueError("Incomplete course game")
            actual = dict(win=result["game_win"], matches=result["our_wins"], points=result["our_points"],
                          opponent_points=result["opp_points"])
            if actual != seat["expected"][agent_name]:
                raise ValueError(f"Archived scores differ {stem}: {actual} vs {seat['expected'][agent_name]}")
            temporary = destination / (stem + ".pending.npz")
            np.savez_compressed(temporary, **{k: np.stack(v) for k, v in actor.history.items()})
            temporary.replace(path)
            report = dict(agent=agent_name, package=expected_sha, seat=seat, actual=actual,
                          filename=path.name, sha256=sha256(path.read_bytes()).hexdigest())
            pending = receipt.with_suffix(".tmp")
            pending.write_text(json.dumps(report, sort_keys=True) + "\n")
            pending.replace(receipt)
            print(stem, flush=True)
    finally:
        env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("agent", choices=PACKAGES)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--stride", type=int, default=1)
    args = parser.parse_args()
    if not 0 <= args.offset < args.stride:
        parser.error("Invalid worker partition")
    collect(args.agent, args.destination, args.offset, args.stride)
