"""Play a recorded screening seat with the unchanged, isolated course runner."""
import argparse
import inspect
import json
import os
import random
import runpy
import shutil
import sys
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[4]


def verify(archive, tape, output):
    with np.load(tape, allow_pickle=False) as recording:
        meta = json.loads(str(recording["metadata"]))
        commands = recording["commands"]
    if meta["opponent"] != "solution92" or len(commands) != 303:
        raise ValueError("Expected a full recorded course seat against Solution")
    torch.set_num_threads(1)
    guard = runpy.run_path(str(ROOT / "scripts/xversion_replay.py"))["require_clean_policy"]
    with TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        agents = root / "agents"
        agents.mkdir()
        shutil.copyfile(ROOT / "agents/__init__.py", agents / "__init__.py")
        shutil.copytree(ROOT / "agents/Solution_92_Kaggle", agents / "Solution_92_Kaggle")
        shutil.copytree(ROOT / "lux", root / "lux")
        with ZipFile(archive) as package:
            if "paths.csv" in package.namelist():
                package.extractall(agents)
                header, row = (agents / "paths.csv").read_text().strip().splitlines()
            elif "Gruppe15/agent.pth" in package.namelist():
                package.extractall(root)
                header = "Moodle Gruppe;Import_Path;Load_Path_P0;Load_Path_P1"
                row = "15;Gruppe15.main.Agent_x;Gruppe15/agent.pth;Gruppe15/agent.pth"
            else:
                raise ValueError("Unknown course archive layout")
        (root / "Paths.csv").write_text(header + "\n2;agents.Solution_92_Kaggle.agent.Agent;;\n" + row + "\n")
        sys.path.insert(0, str(root))
        old_cwd = Path.cwd()
        try:
            os.chdir(root)
            runner = import_module("lux.runner")
            group, dotted, weights0, weights1 = row.split(";")
            seat = meta["side"]
            side = int(seat[-1])
            weights = Path((weights0, weights1)[side]).resolve()
            snapshot = sha256(weights.read_bytes()).hexdigest()
            cls = runner.load_class_from_path(dotted)
            orig_act = cls.act
            orig_init = cls.__init__
            if "agent_path" not in inspect.signature(orig_init).parameters:
                raise TypeError("The course cannot pass the checkpoint to this constructor")
            observed = {"steps": 0, "updates": 0, "saves": 0}
            player = []

            def init(self, who, agent_path=None):
                if who != seat or agent_path is None or Path(agent_path).resolve() != weights:
                    raise ValueError("Course did not supply the recorded seat and checkpoint")
                orig_init(self, who, agent_path=agent_path)
                player.append(self)

            def act(self, step, obs):
                action = orig_act(self, step=step, obs=obs)
                guard(self.base, seat)
                if step != observed["steps"] or not np.array_equal(action, commands[step]):
                    raise ValueError(f"Course diverged from its recorded commands at {seat} turn {step}")
                observed["steps"] += 1
                return action

            orig_update, orig_save = cls.update, cls.save_agent

            def update(self, *args, **kwargs):
                value = orig_update(self, *args, **kwargs)
                guard(self.base, seat)
                observed["updates"] += 1
                return value

            def save(self, *args, **kwargs):
                observed["saves"] += 1
                return orig_save(self, *args, **kwargs)

            groups = (15, 2) if side == 0 else (2, 15)
            seeds = iter([meta["seed"]])
            def recorded_seed(*args, **kwargs):
                seed = next(seeds)
                random.seed(seed)
                np.random.seed(seed)
                return seed

            rng = SimpleNamespace(integers=recorded_seed)
            fixed_draw = SimpleNamespace(random=SimpleNamespace(default_rng=lambda: rng))
            with patch.object(runner, "np", fixed_draw), patch.object(cls, "__init__", init), \
                 patch.object(cls, "act", act), patch.object(cls, "update", update), patch.object(cls, "save_agent", save):
                runner.run_agents(*groups, games_to_play=1, train=bool(side))
            if (observed != {"steps": 303, "updates": 303*side, "saves": side}
                    or len(player) != 1 or player[0].changed != meta["changes"]
                    or sha256(weights.read_bytes()).hexdigest() != snapshot):
                raise ValueError("Unexpected runner calls, intervention count or changed weights")
        finally:
            os.chdir(old_cwd)
    result = dict(python=sys.version.split()[0], zip_sha256=sha256(archive.read_bytes()).hexdigest(),
                  runner_sha256=sha256((ROOT/"lux/runner.py").read_bytes()).hexdigest(), checkpoint_sha256=snapshot,
                  seat=seat, seed=meta["seed"], train=bool(side), same_unit_commands=303*16,
                  interventions=meta["changes"], **observed)
    output.write_text(json.dumps(result, indent=2)+"\n")
    print(result)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("archive", "tape", "output"):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    verify(a.archive.resolve(), a.tape.resolve(), a.output.resolve())
