"""Collect the six fixed four-game holdout blocks and eight training blocks."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import random
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from scripts.experiment import limit_threads

limit_threads()
from luxai_s3.wrappers import LuxAIS3GymEnv
from scripts.common import make_opponent
from scripts.fetch_kaggle3 import verify
from scripts.imitate import SideRecord
from scripts.kaggle3_opponent import Kaggle3Opponent
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent

RELEASE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
V16 = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"


def games():
    for split, start, count in (("train", 160345000, 32), ("valid", 160345100, 24)):
        for index in range(count):
            yield split, start + index, f"player_{index % 2}", ("kaggle3", "solution92")[(index // 2) % 2]


def record(env, out, split, seed, side, opponent):
    random.seed(seed)
    np.random.seed(seed)
    other = "player_1" if side == "player_0" else "player_0"
    actor = r3_package_agent(side, RELEASE)
    rival = make_opponent(opponent, other)
    teacher = Kaggle3Opponent(side)
    for player, seat in ((actor, side), (rival, other)):
        if hasattr(player, "new_game"):
            player.new_game(seat)
    obs, info = env.reset(seed=seed)
    for player in (actor, rival, teacher):
        if hasattr(player, "set_env_cfg"):
            player.set_env_cfg(info["params"])
    archive = SideRecord()
    for step in range(303):
        label = np.asarray(teacher.act(step, obs[side]))
        actions = {side: np.asarray(actor.act(step, obs[side])), other: np.asarray(rival.act(step, obs[other]))}
        student = actor._imitation
        if student.last_fz is not None:
            archive.add(student.last_fz, label, student.belief.mirrored)
        obs, _, terminated, truncated, _ = env.step(actions)
        teacher.remember_played_actions(actions[side])
        if bool(terminated[side]) or bool(truncated[side]):
            if step != 302:
                raise ValueError(f"Unexpected last step {step} on {seed}")
            break
    else:
        raise ValueError(f"No terminal on {seed}")
    require_no_agent_errors(actor, rival)
    meta = dict(split=split, seed=seed, side=side, opponent=opponent, steps=303,
                student=V16, teacher_history="played_student_actions")
    path = out / f"g{seed}.npz"
    temporary = out / f"g{seed}.pending.npz"
    count = archive.save(temporary, meta)
    if count <= 0:
        raise ValueError("Empty supervised game")
    temporary.replace(path)
    return dict(**meta, file=path.name, rows=count, sha256=sha256(path.read_bytes()).hexdigest())


def collect(out, offset, stride):
    if sha256(RELEASE.read_bytes()).hexdigest() != V16 or not verify():
        raise ValueError("Reference players differ from the verified study inputs")
    out.mkdir(exist_ok=True, parents=True)
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for split, seed, side, opponent in list(games())[offset::stride]:
            receipt = out / f"{seed}.json"
            if receipt.exists():
                row = json.loads(receipt.read_text())
                if sha256((out / row["file"]).read_bytes()).hexdigest() != row["sha256"]:
                    raise ValueError(f"Invalid receipt {seed}")
                continue
            row = record(env, out, split, seed, side, opponent)
            pending = receipt.with_suffix(".tmp")
            pending.write_text(json.dumps(row, sort_keys=True) + "\n")
            pending.replace(receipt)
            print(seed, split, row["rows"], flush=True)
    finally:
        env.close()


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("out", type=Path)
    cli.add_argument("--offset", type=int, default=0)
    cli.add_argument("--stride", type=int, default=1)
    args = cli.parse_args()
    if not 0 <= args.offset < args.stride:
        cli.error("Offset must be smaller than the positive stride")
    collect(args.out, args.offset, args.stride)
