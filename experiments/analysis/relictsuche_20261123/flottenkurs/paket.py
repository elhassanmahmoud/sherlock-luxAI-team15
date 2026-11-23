"""Build only the separate tournament-layout candidate and bind its sources to the evaluated pilot."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
FLEET=HERE.parent/"flottenblick"
BASE=ROOT/"dist/Gruppe15.zip"
OFFICIAL="8347ea2bb6e3547bc7881999ebef82d8b09582a2d98a53a3c74e0d8a52b6ae95"
WEIGHT="8ed7412856d6176b81e257360c8eac4a41b844fec935db33aff9e19221d86495"
WRAPPER='''from .kundschafter import FleetScout
from .vorhersage import load
from .v16_main import Agent_x as V16


class Agent_x(FleetScout):
    def __init__(self, player, agent_path=None, name="Sherlock Agent_X", cfg=None, train=True, seed=None):
        super().__init__(V16(player, agent_path=agent_path, name=name, cfg=cfg, train=train, seed=seed), *load())

    @property
    def changed(self):
        return self.changes

    def set_to_eval_mode(self):
        return self.base.set_to_eval_mode()

    def update(self, *args, **kwargs):
        return self.base.update(*args, **kwargs)

    def save_agent(self, path=None):
        return self.base.save_agent(path)

    def load_agent(self, load_path):
        cfg = self.base.env_cfg
        self.base = V16(self.base.player, agent_path=load_path, name=self.base.name, train=False)
        if cfg is not None:
            self.base.set_env_cfg(cfg)
        self.reset()


Agent = Agent_x
'''


def build(out):
    from scripts.build_submission import battle_paths,check_battle
    if out.name!="Gruppe15.zip" or any(out.resolve().is_relative_to((ROOT/d).resolve()) for d in ("dist","agents","experiments/releases")):
        raise ValueError("Separate candidate folder required")
    if sha256(BASE.read_bytes()).hexdigest()!=OFFICIAL:
        raise ValueError("Official submission changed")
    series=json.loads((FLEET/"ganzspiel/serie.json").read_text())
    seen=json.dumps(series)
    with ZipFile(BASE) as z:
        contents={n:z.read(n) for n in z.namelist()}
    assert sha256(contents["Gruppe15/agent.pth"]).hexdigest()==WEIGHT
    for k in list(contents):
        if k.endswith(".py"):
            contents[k]=contents[k].replace(b"from .main import ",b"from .v16_main import ")
    contents["Gruppe15/v16_main.py"]=contents["Gruppe15/main.py"]
    contents["Gruppe15/main.py"]=WRAPPER.encode()
    originals=[FLEET/"kandidat.py",FLEET/"flotte.py",FLEET/"vorhersage.py",FLEET/"modell.json",
               FLEET/"flottengewichte.npz",HERE.parent/"routenlernen/routes.py"]
    fingerprints={p.name:sha256(p.read_bytes()).hexdigest() for p in originals}
    for p in originals:
        if fingerprints[p.name] not in seen:
            raise ValueError(f"Missing frozen source {p.name}")
        target = "kundschafter.py" if p.name=="kandidat.py" else p.name
        payload=p.read_bytes()
        if p.suffix==".py":
            code=payload.decode().replace("from experiments.analysis.relictsuche_20261123.flottenblick.", "from .")
            code=code.replace("from experiments.analysis.relictsuche_20261123.routenlernen.routes import","from .routes import")
            if p.name=="kandidat.py":
                code=code[:code.index("\ndef create(side):")]
                code=code.replace("from scripts.r3_package import r3_package_agent","")
                code="\n".join(line for line in code.splitlines() if not line.startswith(("PACKAGE =","HERE =","from pathlib import Path")))
            if "from experiments" in code or "from scripts" in code:
                raise ValueError(f"Nonportable runtime source {p.name}")
            payload=(code.rstrip()+"\n").encode()
        contents["Gruppe15/"+target]=payload
    contents["Gruppe15/LIESMICH.txt"]=("""Team 15 – Sherlock mit gelerntem Kundschafter

Agent-Klasse einschließlich act und update: Gruppe15.main.Agent_x
Gewichte für beide Startseiten: Gruppe15/agent.pth
Das zusätzliche Suchmodell lädt flottengewichte.npz und modell.json aus demselben Ordner.
In der Kursumgebung genügen die standardmäßig verwendeten CPU-Pakete NumPy und PyTorch.
""").encode()
    out.parent.mkdir(parents=True,exist_ok=True)
    if not out.exists():
        with ZipFile(out,"x") as z:
            for k,v in sorted(contents.items()):
                entry=ZipInfo(k,(2026,11,23,0,0,0))
                entry.compress_type=ZIP_DEFLATED
                entry.external_attr=0o644<<16
                z.writestr(entry,v)
    with ZipFile(out) as z:
        if z.testzip() or set(z.namelist())!=contents.keys() or any(z.read(k)!=v for k,v in contents.items()):
            raise ValueError("Wrong existing package")
    check_battle(out,battle_paths(15,True))
    result=dict(path=str(out),package=sha256(out.read_bytes()).hexdigest(),official=OFFICIAL,base_weights=WEIGHT,source=fingerprints)
    (HERE/"paket.json").write_text(json.dumps(result,indent=2)+"\n")
    print(result["package"])


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("out",type=Path)
    build(p.parse_args().out)
