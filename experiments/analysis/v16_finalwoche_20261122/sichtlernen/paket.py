"""Build the separately evaluated public-visibility policy around the original V16 course code."""
import argparse
import ast
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
shared = importlib.util.spec_from_file_location("sherlock_experimental_bundle", HERE.parent/"zugnutzen/paket.py")
bundle = importlib.util.module_from_spec(shared)
shared.loader.exec_module(bundle)


def create(target):
    src = HERE/"sicht.py"
    fit = json.loads((HERE/"offline.json").read_bytes())
    screen = json.loads((HERE/"auswahl_ergebnis.json").read_bytes())
    if (sha256(src.read_bytes()).hexdigest() != fit["policy"] or not fit["eligible"] or not screen["qualifies"]
           or sha256(bundle.V16.read_bytes()).hexdigest() != bundle.ARTIFACTS[bundle.V16]):
        raise ValueError("Unexpected visibility policy, checkpoint or qualification")
    text = src.read_text()
    tree = ast.parse(text)
    start = next(n.lineno for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=="XY")
    core = "\n".join(text.splitlines()[start-1:])
    header = """import json
from pathlib import Path
import numpy as np
from . import geometry as geo
from .features import FEATURE_NAMES
from .v16_main import Agent_x as Original
"""
    agent = """
class Agent_x(Scout):
    def __init__(self, player, agent_path=None, name="Sherlock Agent_X", cfg=None, train=True, seed=None):
        base = Original(player, agent_path=agent_path, name=name, cfg=cfg, train=train, seed=seed)
        model = json.loads(Path(__file__).with_name("sichtwert.json").read_text())
        if tuple(model["names"]) != NAMES:
            raise ValueError("Incorrect visibility feature order")
        super().__init__(base, (np.asarray(model["w"], dtype=float), float(model["bias"])))

    def new_game(self, player=None):
        self.base.new_game(player)
        self.seen.fill(False)
        self.last = []
        self.changed = 0

    def set_env_cfg(self, cfg):
        return self.base.set_env_cfg(cfg)

    def set_to_eval_mode(self):
        return self.base.set_to_eval_mode()

    def update(self, *args, **kwargs):
        return self.base.update(*args, **kwargs)

    def save_agent(self, path=None):
        return self.base.save_agent(path)

    def load_agent(self, load_path):
        cfg = getattr(self.base, "env_cfg", None)
        base = Original(self.base.player, agent_path=load_path, name=self.base.name, train=False)
        if cfg is not None:
            base.set_env_cfg(cfg)
        super().__init__(base, self.params)


Agent = Agent_x
"""
    files = bundle.archived_base()
    files["sherlock/main.py"] = (header+"\n"+core+"\n\n"+agent).encode()
    files["sherlock/sichtwert.json"] = json.dumps({k:fit["estimate"][k] for k in ("names","w","bias")},
                                                  sort_keys=True,separators=(",",":")).encode()
    return bundle.write_experimental(target, files)


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    print(create(p.parse_args().output))
