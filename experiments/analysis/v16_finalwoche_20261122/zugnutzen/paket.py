"""Build a portable experimental archive from the selected model and frozen V16."""
import argparse
import ast
from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
V16=ROOT/"experiments/releases/20261117_sherlock_v16/agent.zip"
ARTIFACTS={
    V16:"0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099",
    HERE/"wertberater.npz":"67d6f11e7c87b20f068f0b800fc352362b962d2577903a2182658d50f56c06fb",
    HERE/"berater.py":"315cce8f84389355ee0bd1482e3e92bb24ff3b74da5d30a1e268a01d27fc6b8c",
}


def portable_source():
    original=(HERE/"berater.py").read_text()
    nodes=[]
    for node in ast.parse(original).body:
        if isinstance(node,ast.ClassDef) and node.name in ("ValueNet","Policy"):
            nodes.append(node)
        if (isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name)
                and node.targets[0].id in ("NAMES","POINT","IDENTITY")):
            nodes.append(node)
    if len(nodes)!=5: raise ValueError("Unexpected frozen policy components")
    header="""from collections import Counter
from pathlib import Path

import numpy as np
import torch
from scipy.special import logsumexp
from . import geometry as g
from .features import FEATURE_NAMES
from .v16_main import Agent_x as Original
"""
    wrapper="""
class Agent_x(Policy):
    def __init__(self, player, agent_path=None, name="Sherlock Agent_X", cfg=None, train=True, seed=None):
        base = Original(player, agent_path=agent_path, name=name, cfg=cfg, train=train, seed=seed)
        net = ValueNet().eval()
        with np.load(Path(__file__).with_name("wertberater.npz"), allow_pickle=False) as weights:
            net.load_state_dict({key: torch.from_numpy(weights[key]) for key in weights.files})
        super().__init__(base, net)

    def new_game(self, player=None):
        self.changed = 0
        self.last = []
        self.base.new_game(player)

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
        super().__init__(base, self.net)


Agent = Agent_x
"""
    return (header+"\n\n"+"\n\n\n".join(ast.get_source_segment(original,n) for n in nodes)+"\n\n"+wrapper).encode()


def build(out):
    out=out.resolve()
    for file,digest in ARTIFACTS.items():
        if sha256(file.read_bytes()).hexdigest()!=digest:
            raise ValueError(f"Source changed: {file.name}")
    for directory in (ROOT/"dist",ROOT/"agents",ROOT/"experiments/releases"):
        if out.is_relative_to(directory.resolve()):
            raise ValueError("This builder is for a separate experimental candidate")
    if out.exists():
        raise FileExistsError(out)
    with ZipFile(V16) as base:
        files={name:base.read(name) for name in base.namelist()}
    files["sherlock/v16_main.py"]=files["sherlock/main.py"]
    # Archived PPO and imitation classes inherit from the original Agent_x.
    # Keep their internal inheritance graph pointed at the relocated class.
    for name,content in list(files.items()):
        if name.endswith(".py"):
            files[name]=content.replace(b"from .main import ", b"from .v16_main import ")
    files["sherlock/main.py"]=portable_source()
    files["sherlock/wertberater.npz"]=(HERE/"wertberater.npz").read_bytes()
    out.parent.mkdir(exist_ok=True,parents=True)
    with ZipFile(out,"x",compression=ZIP_DEFLATED) as package:
        for name,value in sorted(files.items()):
            entry=ZipInfo(name,date_time=(2026,11,23,0,0,0))
            entry.compress_type=ZIP_DEFLATED
            entry.external_attr=0o644<<16
            package.writestr(entry,value)
    with ZipFile(out) as package, ZipFile(V16) as original:
        if package.testzip() or package.read("sherlock/weights/agent.pth")!=original.read("sherlock/weights/agent.pth"):
            raise ValueError("Corrupt package or rewritten V16 weights")
    return sha256(out.read_bytes()).hexdigest()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("out",type=Path)
    print(build(p.parse_args().out))
