"""Messe Zugang und spätere Nutzung derselben Punktefelder mit dem eingefrorenen V16."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.r3_package import r3_package_agent
from scripts.scoring import match_points_after_step, point_tile_map

PACKAGE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
ARCHIVE = ROOT / "experiments/analysis/devf_20261117/bestaetigung3_kandidat.csv"
DIGEST = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
SEEDS = range(7261000, 7261008)


class Record:
    def __init__(self, env):
        self.env = env
        self.frames = []

    def reset(self, **kwargs):
        self.frames.clear()
        obs, info = self.env.reset(**kwargs)
        self.previous = obs["player_0"]
        return obs, info

    def step(self, actions):
        result = self.env.step(actions)
        obs, info = result[0]["player_0"], result[4]
        state = info["final_state"]
        tiles = point_tile_map(state)
        position = np.asarray(state.units.position)
        alive = np.asarray(state.units_mask) & (np.asarray(state.units.energy)[..., 0] >= 0)
        fields = tuple({tuple(p) for p in position[t, alive[t]] if tiles[tuple(p)]} for t in (0, 1))
        gains = match_points_after_step(self.previous, obs, info) - self.previous["team_points"]
        if tuple(map(len, fields)) != tuple(gains):
            raise ValueError(f"Felder stimmen nicht mit Punktezuwachs überein: {gains}")
        self.frames.append(fields)
        self.previous = obs
        return result


def measure(frames, team):
    # Frame 0 entspricht der ersten Entscheidung, Frame 100 der letzten vor dem Reset.
    own = [f[team] for f in frames]
    early = set.union(*own[:71])
    late = own[81:101]
    late_early = sum(len(f & early) for f in late)
    return {
        "early_tiles": len(early),
        "all_tiles": len(set.union(*own)),
        "early_tile_points_late": late_early,
        "new_tile_points_late": sum(len(f - early) for f in late),
        "early_tile_slots_late": len(late) * len(early),
        "points": sum(map(len, own)),
    }


def run():
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    if hashlib.sha256(PACKAGE.read_bytes()).hexdigest() != DIGEST:
        raise ValueError("Falsches Abgabepaket")
    with ARCHIVE.open() as src:
        archive = {int(row["seed"]): row for row in csv.DictReader(src)
                   if row["opponent"] == "kaggle3" and row["side"] == "player_0"}
    env = Record(LuxAIS3GymEnv(numpy_output=True))
    results = []
    for seed in SEEDS:
        agent = r3_package_agent("player_0", PACKAGE)
        opponent = make_opponent("kaggle3", "player_1")
        score = play_game(env, agent, opponent, seed, "player_0", train=False)
        keys = ("our_points", "opp_points", "our_wins", "opp_wins", "steps")
        expected = {k: int(archive[seed][k]) for k in keys}
        actual = {k: score[k] for k in keys}
        if actual != expected or len(env.frames) != 303:
            raise ValueError(f"Abweichung vom Archiv bei {seed}: {actual}, erwartet {expected}")
        matches = []
        for start in (0, 101, 202):
            frames = env.frames[start:start + 101]
            matches.append({name: measure(frames, t) for t, name in enumerate(("V16", "Kaggle"))})
        for team, key in (("V16", "our_points"), ("Kaggle", "opp_points")):
            if sum(m[team]["points"] for m in matches) != actual[key]:
                raise ValueError("Abweichende Matchsumme")
        results.append({"seed": seed, "side": "player_0", **actual, "matches": matches})
        print(seed, actual, flush=True)
    output = {"v16_sha256": DIGEST, "opponent": "kaggle3", "games": results}
    (HERE / "feldverlauf.json").write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    run()
