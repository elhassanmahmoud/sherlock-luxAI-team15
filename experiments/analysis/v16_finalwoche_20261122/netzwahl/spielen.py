"""Measure the qualified two-net weighting on the predeclared fresh games."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import random

import numpy as np
import torch

from vorhersagen import FEATURES, HERE, RELEASE, V16
from agents.sherlock.features import FEATURE_NAMES
from luxai_s3.wrappers import LuxAIS3GymEnv
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import verify
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent


def install(agent, params):
    if list(FEATURES) != params["features"] or params["release"] != V16:
        raise ValueError("Model identity or feature order mismatch")
    policy = agent._imitation
    weights = torch.tensor(params["context_weights"], dtype=torch.float32)
    indices = [FEATURE_NAMES.index(name) for name in FEATURES]
    if len(policy.extra_nets) != 1 or weights.shape != (len(indices),):
        raise ValueError("Expected the verified two-net policy")

    def weighted_forward(original, sign):
        def predict(planes, steps, pos, feats):
            actions, value, target_map = original(planes, steps, pos, feats)
            d = 0.65 * torch.tanh(feats[:, indices] @ weights + params["context_bias"])
            return actions * (1 + sign * d[:, None]), value, target_map
        return predict

    for network, sign in ((policy.net, 1), (policy.extra_nets[0], -1)):
        network.forward_all = weighted_forward(network.forward_all, sign)


def cases():
    for seed in range(160345200, 160345232):
        for side in ("player_0", "player_1"):
            for rival in ("solution92", "kaggle3", "v16"):
                for arm in (("context",) if rival == "v16" else ("base", "context")):
                    yield seed, side, rival, arm


def measure(out, choice, offset, stride):
    if os.environ.get("PYTHONHASHSEED") != "0" or sha256(RELEASE.read_bytes()).hexdigest() != V16 or not verify():
        raise ValueError("Reference player or seed configuration mismatch")
    params = json.loads(choice.read_text())
    if params["eligible"] is not True or not all(params["gates"].values()):
        raise ValueError("Independent offline evidence required before playing")
    if params["plan_sha256"] != sha256((HERE / "PLAN.md").read_bytes()).hexdigest():
        raise ValueError("The study plan changed")
    choice_hash = sha256(choice.read_bytes()).hexdigest()
    limit_threads()
    env = LuxAIS3GymEnv(numpy_output=True)
    out.mkdir(exist_ok=True, parents=True)
    try:
        for seed, side, opponent, arm in list(cases())[offset::stride]:
            target = out / f"{seed}_{side}_{opponent}_{arm}.json"
            if target.exists():
                row = json.loads(target.read_text())
                if (row["choice"] != choice_hash or row["steps"] != 303
                        or (row["seed"], row["side"], row["opponent"], row["arm"]) != (seed, side, opponent, arm)):
                    raise ValueError(f"Invalid existing seat {target}")
                continue
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
            other = "player_1" if side == "player_0" else "player_0"
            actor = r3_package_agent(side, RELEASE)
            if arm == "context":
                install(actor, params)
            rival = r3_package_agent(other, RELEASE) if opponent == "v16" else make_opponent(opponent, other)
            game = play_game(env, actor, rival, seed, side, train=False)
            require_no_agent_errors(actor, rival)
            row = {k: game[k] for k in ("seed", "side", "steps", "point_counting_version", "our_wins",
                                        "opp_wins", "our_points", "opp_points", "game_win")}
            if (row["steps"] != 303 or row["point_counting_version"] != 2 or
                    row["our_wins"] + row["opp_wins"] != 3 or row["game_win"] != int(row["our_wins"] >= 2)):
                raise ValueError("Invalid completed game")
            row.update(opponent=opponent, arm=arm, choice=choice_hash)
            tmp = target.with_suffix(".tmp")
            tmp.write_text(json.dumps(row) + "\n")
            tmp.replace(target)
            print(target.name, flush=True)
    finally:
        env.close()


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("out", type=Path)
    cli.add_argument("choice", type=Path)
    cli.add_argument("--offset", type=int, default=0)
    cli.add_argument("--stride", type=int, default=1)
    args = cli.parse_args()
    if not 0 <= args.offset < args.stride:
        cli.error("Invalid worker partition")
    measure(args.out, args.choice, args.offset, args.stride)
