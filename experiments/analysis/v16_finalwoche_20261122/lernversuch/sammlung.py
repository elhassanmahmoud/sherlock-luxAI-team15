"""Collect DAgger labels on the actual released V16; no game-state access."""
import hashlib
import json
from pathlib import Path
import random
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
RELEASE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
ZIP_SHA = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(out):
    from scripts.experiment import limit_threads
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.common import make_opponent
    from scripts.fetch_kaggle3 import verify
    from scripts.imitate import SideRecord
    from scripts.kaggle3_opponent import Kaggle3Opponent
    from scripts.par_eval import require_no_agent_errors
    from scripts.r3_package import r3_package_agent
    if sha(RELEASE) != ZIP_SHA or not verify():
        raise ValueError("Release or teacher archive mismatch")
    out.mkdir(exist_ok=False, parents=True)
    env = LuxAIS3GymEnv(numpy_output=True)
    receipts = []
    for split, first, count in (("train", 19376200, 8), ("valid", 19376220, 4)):
        for i in range(count):
            seed = first + i
            side = f"player_{i % 2}"
            other = f"player_{1 - i % 2}"
            opponent = ("kaggle3", "solution92")[(i // 2) % 2]
            random.seed(seed)
            np.random.seed(seed)
            player = r3_package_agent(side, RELEASE)
            rival = make_opponent(opponent, other)
            teacher = Kaggle3Opponent(side)
            for p, s in ((player, side), (rival, other)):
                if hasattr(p, "new_game"):
                    p.new_game(s)
            obs, info = env.reset(seed=seed)
            for p in (player, teacher, rival):
                if hasattr(p,"set_env_cfg"):
                    p.set_env_cfg(info["params"])
            rec = SideRecord()
            step = 0
            while True:
                label = np.asarray(teacher.act(step, obs[side]))
                moves = {side: np.asarray(player.act(step, obs[side])), other: np.asarray(rival.act(step, obs[other]))}
                student = player._imitation
                if student.last_fz is not None:
                    rec.add(student.last_fz, label, student.belief.mirrored)
                obs, _, term, trunc, _ = env.step(moves)
                teacher.remember_played_actions(moves[side])
                step += 1
                if bool(np.asarray(term[side])) or bool(np.asarray(trunc[side])):
                    break
            require_no_agent_errors(player, rival)
            if step != 303:
                raise ValueError(f"Incomplete game {seed}")
            meta = dict(seed=seed, side=side, opponent=opponent, steps=step, student=ZIP_SHA,
                        teacher_history="played_student_actions", split=split)
            path = out / f"g{seed}_{side}_{opponent}.npz"
            n = rec.save(path, meta)
            receipts.append(dict(**meta, rows=n, sha256=sha(path), file=path.name))
            print(split, seed, side, opponent, n, flush=True)
    env.close()
    (out / "sammlung.json").write_text(json.dumps(receipts,indent=2)+"\n")


if __name__ == "__main__":
    collect(Path(sys.argv[1]))
