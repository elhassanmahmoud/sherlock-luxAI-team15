"""Ordnet eine frühe Reliktsichtung den möglichen Beobachtern im Original-Replay zu."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from kandidat import Scout
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors

HERE = Path(__file__).resolve().parent
SEED = 7261020


class RecordingScout(Scout):
    def new_game(self, side):
        super().new_game(side)
        self.sightings = []

    def act(self, step, obs):
        memory = self.base._imitation.belief
        known = set(memory.relic_positions)
        actions = super().act(step, obs)
        if memory.match_idx != 1 or memory.match_step != self.pair_turn:
            return actions

        # In diesem Nachspiel spielt Sherlock als P0. Karte und Positionen
        # liegen in denselben Weltkoordinaten wie seine interne Darstellung.
        assert not memory.mirrored
        radius = int(self.base._imitation.env_cfg["unit_sensor_range"])
        for target in np.asarray(obs["relic_nodes"])[obs["relic_nodes_mask"]]:
            xy = tuple(map(int, target))
            if xy in known:
                continue
            assert obs["sensor_mask"][xy]
            observers = []
            for uid in np.flatnonzero(obs["units_mask"][0]):
                pos = np.asarray(obs["units"]["position"][0][uid])
                if np.abs(pos - target).max() <= radius:
                    observers.append({"unit": int(uid), "position": pos.tolist()})
            assert observers
            self.sightings.append({"turn": memory.match_step, "target": xy,
                                   "sensor_range": radius, "in_range": observers})
        return actions


def verify(out):
    from luxai_s3.wrappers import LuxAIS3GymEnv

    limit_threads()
    reference = json.loads((HERE / "technik.json").read_text())
    source = hashlib.sha256((HERE / "kandidat.py").read_bytes()).hexdigest()
    assert source == reference["source_sha256"]
    expected = next(row for row in reference["rows"]
                    if row["seed"] == SEED and row["side"] == "player_0" and row["arm"] == "scout")
    player = RecordingScout("player_0")
    opponent = make_opponent("solution92", "player_1")
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        actual = play_game(env, player, opponent, SEED, "player_0", False)
    finally:
        env.close()
    require_no_agent_errors(player.base, opponent)
    assert all(actual[k] == expected[k] for k in ("our_wins", "opp_wins", "our_points", "opp_points", "steps"))
    assert player.changes == expected["changes"] and player.uid == expected["uid"]
    assert player.sightings and all(s["turn"] == expected["pair_turn"] for s in player.sightings)
    out.write_text(json.dumps({"seed": SEED, "side": "player_0", "scout_id": player.uid,
                               "observations": player.sightings}, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "sichtbeleg.json")
    verify(parser.parse_args().out)
