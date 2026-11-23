"""Record both candidate sides for the existing unchanged-runner verification."""
from collections import defaultdict
import json
import sys

import numpy as np

from collect import OUT, ROOT, seeds_for
from routes import HERE
sys.path.insert(0, str(ROOT))
from experiments.analysis.relictsuche_20261123.routenlernen.kandidat import create
from luxai_s3.wrappers import LuxAIS3GymEnv
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors


class Recorder:
    def __init__(self, side):
        self.agent = create(side)
        self.rows = defaultdict(list)

    def __getattr__(self, name):
        return getattr(self.agent, name)

    def act(self, step, obs):
        original = self.agent.act(step, obs)
        if len(self.rows["commands"]) != step:
            raise ValueError("Chronology mismatch")
        self.rows["commands"].append(original.copy())
        for key, value in obs.items():
            if isinstance(value, dict):
                for k, a in value.items():
                    self.rows[key + "/" + k].append(np.array(a, copy=True))
            else:
                self.rows[key].append(np.array(value, copy=True))
        return original


def record():
    limit_threads()
    data = OUT / "tapes"
    data.mkdir(exist_ok=True)
    # Two public sight-1 smoke openings and both normal-sight controls from the same seeds.
    seeds = [int(v[0]) for v in (seeds_for("replay"), seeds_for("replay", normal=True))]
    old = {(r["seed"], r["side"]): r for r in json.loads((HERE / "smoke.json").read_text())}
    from hashlib import sha256
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed in seeds:
            for team in (0, 1):
                side = f"player_{team}"
                recorder = Recorder(side)
                rival = make_opponent("solution92", f"player_{1-team}")
                result = play_game(env, recorder, rival, seed, side, False)
                require_no_agent_errors(recorder.base, rival)
                commands = np.asarray(recorder.rows["commands"], dtype="<i2")
                reference = old[seed, team]
                if (result["steps"] != 303 or recorder.changes != reference["changes"]
                        or sha256(commands[:101].tobytes()).hexdigest() != reference["digest"]):
                    raise ValueError("Stored opening does not reproduce")
                meta = dict(cfg=recorder.agent.base.env_cfg, seed=seed, side=side,
                            opponent="solution92", changes=recorder.changes)
                np.savez_compressed(data / f"{seed}_{side}.npz", metadata=np.array(json.dumps(meta)),
                                    **{k: np.stack(a) for k, a in recorder.rows.items()})
    finally:
        env.close()


if __name__ == "__main__":
    record()
