"""Start low-visibility games with the original R3, then use the original V16."""
from functools import lru_cache
from hashlib import sha256
import importlib
import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from scripts.r3_package import r3_package_agent

R3 = ROOT / "experiments/releases/20261116_r3_finale/agent.zip"
V16 = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
R3_SHA = "8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d"
V16_SHA = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"


@lru_cache(maxsize=1)
def separate_r3():
    if sha256(R3.read_bytes()).hexdigest() != R3_SHA:
        raise ValueError("Unexpected R3 package")
    space = TemporaryDirectory(prefix="sherlock_original_r3_")
    with ZipFile(R3) as archive:
        archive.extractall(space.name)
    folder = (Path(space.name) / "sherlock").resolve()
    alias = "sherlock_course_r3"
    spec = importlib.util.spec_from_file_location(
        alias, folder / "__init__.py", submodule_search_locations=[str(folder)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    main = importlib.import_module(alias + ".main")
    if Path(main.__file__).resolve() != folder / "main.py":
        raise ValueError("Mixed package namespace")
    return space, main.Agent_x, folder / "weights/agent.pth"


def r3_player(side):
    _, cls, weight = separate_r3()
    agent = cls(side, agent_path=str(weight))
    agent.set_to_eval_mode()
    return agent


def played_history(agent, actions):
    """Record only actions actually played. Its MoveTracker independently reads observed positions."""
    model = agent._imitation
    native = importlib.import_module(type(model).__module__)
    for uid in model._prev_actions:
        model._prev_actions[uid] = native.canonical_action(actions[uid], model.belief.mirrored)[0]
    model._sap_hits.clear()  # Training-only counter has no measured hits for an overridden plan.
    model.param_est.record_played_actions(actions)


class Relay:
    def __init__(self, side):
        self.side = side
        self.base = r3_package_agent(side, V16)
        self.r3 = None
        self.early = 0
        self.changed_units = 0
        self.changed_steps = 0

    def __getattr__(self, key):
        return getattr(self.base, key)

    def new_game(self, side):
        self.side = side
        self.base.new_game(side)
        self.r3 = None
        self.early = self.changed_steps = self.changed_units = 0

    def set_env_cfg(self, cfg):
        self.base.set_env_cfg(cfg)
        if int(cfg["unit_sensor_range"]) in (1, 2):
            self.r3 = r3_player(self.side)
            self.r3.new_game(self.side)
            self.r3.set_env_cfg(cfg)

    def act(self, step, obs):
        v16 = self.base.act(step, obs)
        if self.r3 is None or step > 40:
            return v16
        if int(np.asarray(obs["match_steps"])) != step:
            raise ValueError("Unexpected match boundary during opening")
        played = self.r3.act(step, obs)
        differences = int(np.count_nonzero(np.any(v16 != played, axis=1)))
        self.changed_units += differences
        self.changed_steps += int(differences > 0)
        self.early += 1
        played_history(self.base, played)
        return played
