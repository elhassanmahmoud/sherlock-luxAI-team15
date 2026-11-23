"""Real course opening, exact public prefix and original V16 proposal checks."""
import hashlib
import random
from pathlib import Path
import sys

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "vergleich"))
from spielen import Monitor, PACKAGE, make_opponent, play_game, require, require_no_agent_errors, r3_package_agent
from kandidat import LateSearch


class OpeningDone(Exception):
    pass


class Opening(Monitor):
    def __init__(self, env, team, actor, only_qualifying, normal=False):
        super().__init__(env, team, "general" if normal else "confirm", actor)
        self.qualify_only = only_qualifying
        self.observations = hashlib.sha256()

    def hash_obs(self, obs):
        def update(node):
            if isinstance(node, dict):
                for k, v in sorted(node.items()):
                    self.observations.update(k.encode())
                    update(v)
            else:
                a = np.asarray(node)
                self.observations.update(str((a.dtype.str, a.shape)).encode())
                self.observations.update(a.tobytes())
        update(obs)

    def step(self, actions):
        if self.turn < 55:
            self.hash_obs(self.old)
        out = super().step(actions)
        if self.turn == 55:
            self.hash_obs(self.old)
            self.prefix_commands = self.digest.hexdigest()
            self.eligible = self.first_sight == 101 and not np.any(self.old["relic_nodes_mask"]) and self.first_credit == 101
            if self.qualify_only and not self.eligible:
                raise OpeningDone
        if self.turn == 101:
            raise OpeningDone
        return out


def play(env, seed, team, opponent, arm, *, only_qualifying=True, normal=False):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    side, other = f"player_{team}", f"player_{1-team}"
    base = r3_package_agent(side, PACKAGE) if arm == "original" else LateSearch(side, arm)
    rival = make_opponent("solution92", other) if opponent == "solution92" else r3_package_agent(other, PACKAGE)
    capture = Opening(env, team, None if arm == "original" else base, only_qualifying, normal)
    try:
        play_game(capture, base, rival, seed, side, False)
    except OpeningDone:
        pass
    require_no_agent_errors(getattr(base, "base", base), rival)
    require(capture.turn == (55 if only_qualifying and not capture.eligible else 101), "Wrong opening length")
    require(all(e[0] >= 55 and e[0] < capture.first_sight and e[0] <= capture.first_credit for e in capture.events), "Change outside the late window")
    require(len({e[1] for e in capture.events}) <= 1, "Changed two scouts")
    r = dict(seed=seed, team=team, opponent=opponent, arm=arm, sensor=capture.sensor, eligible=bool(capture.eligible),
             prefix_commands=capture.prefix_commands, prefix_observations=capture.observations.hexdigest(), turns=capture.turn,
             action_hash=capture.digest.hexdigest(), events=capture.events, caught_errors=[0,0])
    if capture.turn == 101:
        r.update(sight=capture.first_sight, credit=capture.first_credit, after70=capture.after_70, match=capture.matches[0])
    if isinstance(base, LateSearch):
        r.update(features=base.features, choice=base.choice)
        require(not base.features or capture.eligible, "Ineligible decision")
    return r
