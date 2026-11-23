"""Record one decision and its fifteen observed consequences in matched rollouts."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
SIBLING = HERE.parent / "mitte2"
sys.path.insert(0, str(SIBLING))
from mitte import MODEL_SHA, PACKAGE, V16, Policy, choose, g, model, optionen, r3_package_agent, sha
from verlauf import Track, save
from luxai_s3.wrappers import LuxAIS3GymEnv
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import require_no_agent_errors

NAMES = ("instant_prediction", "network_gap", "team_plans_original", "team_plans_alternative",
         "friendly_original", "friendly_alternative", "known_point_original", "known_point_alternative",
         "enemy_energy_original", "enemy_energy_alternative", "time", "score_margin", "match_margin")


def sources():
    files = (HERE/"PLAN.md", HERE/"erheben.py", SIBLING/"mitte.py", SIBLING/"optionen.py",
             SIBLING/"verlauf.py", HERE.parent/"zugnutzen/berater.py")
    return {str(path.relative_to(HERE.parent)): sha(path) for path in files}


def cases(split):
    first, size = {"train": (160390000, 160), "test": (160391000, 80)}[split]
    return [(first+i, i%2, ("solution92", "kaggle3")[i//2%2], (26, 40, 54)[i%3]) for i in range(size)]


class Proposal(Policy):
    def __init__(self, team, net, first, intervene):
        super().__init__(r3_package_agent(f"player_{team}", PACKAGE), net)
        self.team = team
        self.first = first
        self.apply = intervene
        self.original = None
        self.event = None

    def act(self, step, obs):
        command = self.base.act(step, obs)
        self.original = command
        turn = int(obs["match_steps"])
        pts = np.asarray(obs["team_points"], dtype=int)
        margin = int(pts[self.team] - pts[1-self.team])
        if self.event or not 101 <= step < 202 or not self.first <= turn <= 75 or margin > 0:
            return command
        options = optionen.options(self, command)
        choice = choose(self.net, options)
        if choice is None:
            return command
        uid, world = choice["uid"], choice["world"]
        feature, = [r[3] for r in options if (r[1], r[2]) == (uid, world)]
        if sha256(np.ascontiguousarray(feature).tobytes()).hexdigest() != choice["public_features"]:
            raise ValueError("Incorrect team member or action")
        wins = np.asarray(obs["team_wins"])
        x = [choice["value"], *map(float, feature[-9:]), turn / 100,
             float(np.clip(margin/100, -1, 0)), int(wins[self.team] - wins[1-self.team])]
        if len(x) != len(NAMES) or not np.isfinite(x).all():
            raise ValueError("Invalid public decision inputs")
        self.event = dict(**choice, step=step, x=x)
        if not self.apply:
            return command
        actor = self.base._imitation
        canon = g.mirror_dir(world) if actor.belief.mirrored else world
        found = np.flatnonzero(np.asarray(actor.last_fz[1]) == uid)
        if len(found) != 1 or not actor.last_fz[3][int(found[0]), canon] or world == command[uid, 0]:
            raise ValueError("Invalid alternate move")
        out = command.copy()
        out[uid] = [world, 0, 0]
        actor._prev_actions[uid] = canon
        actor._sap_hits.pop(uid, None)
        actor.param_est.record_played_actions(out)
        return out


def rollout(env, case, net, apply):
    seed, team, kind, first = case
    side, other = f"player_{team}", f"player_{1-team}"
    actor = Proposal(team, net, first, apply)
    rival = make_opponent(kind, other)
    for player, who in ((actor, side), (rival, other)):
        if hasattr(player, "new_game"):
            player.new_game(who)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    tracer = Track(env, actor, team)
    obs, info = tracer.reset(seed=seed)
    for player in (actor, rival):
        if hasattr(player, "set_env_cfg"):
            player.set_env_cfg(info["params"])
    for step in range(201):
        commands = {side: actor.act(step, obs[side]), other: rival.act(step, obs[other])}
        current_turn = int(obs[side]["match_steps"])
        obs, _, done, cutoff, _ = tracer.step(commands)
        if bool(done[side]) or bool(cutoff[side]):
            raise ValueError("Truncated rollout before the comparison")
        if actor.event and step == actor.event["step"]+14:
            break
        if actor.event is None and step > 101 and current_turn >= 75:
            break
    require_no_agent_errors(actor.base, rival)
    if actor.event is None:
        return None
    gains = np.asarray(tracer.gains[actor.event["step"]:], dtype=int)
    if len(gains) != 15 or tracer.pivot is None:
        raise ValueError("Missing matched horizon")
    return dict(event=actor.event, pivot=tracer.pivot, gains=gains.cumsum(axis=0)[[0,4,14]].tolist())


def run(directory, split, offset, stride):
    if os.getenv("PYTHONHASHSEED") != "0" or not verify():
        raise ValueError("Opponent or hash seed differs")
    limit_threads()
    net = model()
    spec = sources()
    directory.mkdir(exist_ok=True, parents=True)
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for case in cases(split)[offset::stride]:
            seed = case[0]
            dst = directory / f"{seed}.json"
            identity = dict(case=list(case), source=spec, weights=MODEL_SHA, release=V16)
            if dst.exists():
                old = json.loads(dst.read_text())
                if any(old[k] != v for k, v in identity.items()):
                    raise ValueError("Different source on an existing map")
                continue
            left = rollout(env, case, net, False)
            right = rollout(env, case, net, True) if left else None
            if left and (not right or left["event"] != right["event"] or left["pivot"] != right["pivot"]):
                raise ValueError(f"Paired observations, histories or own commands disagree on {seed}")
            save(dst, dict(**identity, original=left, alternative=right))
            print(seed, int(left is not None), flush=True)
    finally:
        env.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("split", choices=("train", "test"))
    p.add_argument("offset", type=int)
    p.add_argument("stride", type=int)
    a = p.parse_args()
    if not 0 <= a.offset < a.stride:
        p.error("Invalid partition")
    run(a.directory, a.split, a.offset, a.stride)
