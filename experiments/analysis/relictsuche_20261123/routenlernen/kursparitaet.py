"""Compare every course action on four recorded games, including normal-sight controls."""
import argparse
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import numpy as np
import torch


def compare(folder, archive, out):
    torch.set_num_threads(1)
    samples = sorted(folder.glob("*.npz"))
    if len(samples) != 4:
        raise ValueError("Expected two seats on each of two distinct sensor ranges")
    results = []
    with TemporaryDirectory() as temp:
        root = Path(temp)
        agents = root / "agents"
        agents.mkdir()
        (agents / "__init__.py").touch()
        with ZipFile(archive) as package:
            package.extractall(agents)
            fields = package.read("paths.csv").decode().strip().splitlines()[1].split(";")
        sys.path.insert(0, str(root))
        dotted, class_name = fields[1].rsplit(".", 1)
        module = import_module(dotted)
        if Path(module.__file__).resolve() != (agents / "sherlock/main.py").resolve():
            raise ValueError("Imported different implementation")
        for file in samples:
            with np.load(file, allow_pickle=False) as data:
                meta = json.loads(str(data["metadata"]))
                arrays = {k: data[k] for k in data.files if k != "metadata"}
            side = meta["side"]
            actor = getattr(module, class_name)(side, agent_path=str(root / fields[2 + int(side[-1])]))
            actor.set_to_eval_mode()
            actor.new_game(side)
            actor.set_env_cfg(meta["cfg"])
            for step, command in enumerate(arrays["commands"]):
                obs = {}
                for key, data in arrays.items():
                    if key != "commands":
                        if "/" in key:
                            path, leaf = key.split("/", 1)
                            obs.setdefault(path, {})[leaf] = data[step]
                        else:
                            obs[key] = data[step]
                if not np.array_equal(actor.act(step, obs), command):
                    raise ValueError(f"Different course command at {side} turn {step}")
            if (len(arrays["commands"]) != 303 or actor.changes != meta["changes"] or actor.caught_errors
                    or bool(actor.changes) != (meta["cfg"]["unit_sensor_range"] == 1)):
                raise ValueError("Different trip count, eligibility or policy errors")
            results.append(dict(seed=meta["seed"], side=side, sensor=meta["cfg"]["unit_sensor_range"],
                                changes=actor.changes, same_commands=int(np.prod(arrays["commands"].shape[:2]))))
    checked = sum(r["same_commands"] for r in results)
    report = dict(python=sys.version.split()[0], zip_sha256=sha256(archive.read_bytes()).hexdigest(),
                  games=results, unit_commands=checked, differences=0)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(report["python"], checked, flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("tapes", "archive", "out"):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    compare(a.tapes, a.archive, a.out)
