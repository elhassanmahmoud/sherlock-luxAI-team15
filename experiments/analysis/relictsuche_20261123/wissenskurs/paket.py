"""Construct the competition layout for the proven-point study separately from the official V16 submission."""
import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from experiments.analysis.relictsuche_20261123.flottenkurs.paket import BASE, OFFICIAL, ROOT, WEIGHT
from experiments.analysis.relictsuche_20261123.punktwissen.spiele import HERE as STUDY, frozen, sha
from scripts.build_submission import battle_paths, check_battle

HERE = Path(__file__).resolve().parent
WRAPPER = '''from .punktwissen import Knowledge
from .v16_main import Agent_x as V16


class Agent_x(Knowledge):
    def __init__(self, player, agent_path=None, name="Sherlock Agent_X", cfg=None, train=True, seed=None):
        base = V16(player, agent_path=agent_path, name=name, cfg=cfg, train=train, seed=seed)
        super().__init__(base)

    @property
    def changed(self):
        return len(self.events)

    def update(self, *args, **kwargs):
        return self.base.update(*args, **kwargs)

    def set_to_eval_mode(self):
        return self.base.set_to_eval_mode()

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
    from hashlib import sha256
    assert out.name == "Gruppe15.zip" and sha(BASE) == OFFICIAL
    if any(out.resolve().is_relative_to((ROOT / d).resolve()) for d in ("agents", "dist", "experiments/releases")):
        raise ValueError("Use a separate research directory")
    gate = json.loads((STUDY / "ergebnis.json").read_text())
    assert gate["passed"] and gate["source"] == frozen()
    with ZipFile(BASE) as z:
        files = {name: z.read(name) for name in z.namelist()}
    assert sha256(files["Gruppe15/agent.pth"]).hexdigest() == WEIGHT
    for name in list(files):
        if name.endswith(".py"):
            files[name] = files[name].replace(b"from .main import ", b"from .v16_main import ")
    files["Gruppe15/v16_main.py"] = files["Gruppe15/main.py"]
    files["Gruppe15/main.py"] = WRAPPER.encode()
    proofs = STUDY.parent / "punktspeicher/beweise.py"
    source = STUDY / "kandidat.py"
    original = source.read_text().split("\ndef create(side):")[0]
    original = original.replace("from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import", "from .beweise import")
    kept = [line for line in original.splitlines() if not line.startswith(("from pathlib import Path", "from scripts.r3_package import ", "PACKAGE ="))]
    module = "\n".join(kept).strip() + "\n"
    assert "from experiments" not in module and "from scripts" not in module
    files["Gruppe15/punktwissen.py"] = module.encode()
    files["Gruppe15/beweise.py"] = proofs.read_bytes()
    files["Gruppe15/LIESMICH.txt"] = ("Team 15 – Sherlock\n\n"
        "Agent-Klasse einschließlich act und update: Gruppe15.main.Agent_x\n"
        "Gewichte für Player 0 und Player 1: Gruppe15/agent.pth\n"
        "Bei geringer Sicht leitet das Kartengedächtnis zusätzliche sichere Punktefelder aus dem Spielstand ab.\n"
        "Die Kursumgebung benötigt NumPy und PyTorch zur Ausführung.\n").encode()
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists():
        with ZipFile(out, "x") as z:
            for name, content in sorted(files.items()):
                entry = ZipInfo(name, (2026, 11, 23, 0, 0, 0))
                entry.compress_type = ZIP_DEFLATED
                entry.external_attr = 0o644 << 16
                z.writestr(entry, content)
    with ZipFile(out) as z:
        assert z.testzip() is None and set(z.namelist()) == set(files) and all(z.read(k)==v for k,v in files.items())
    check_battle(out, battle_paths(15, True))
    evidence = dict(archive=sha(out), official=OFFICIAL, weights=WEIGHT, pilot=gate["source"],
                    inputs={p.name:sha(p) for p in (source, proofs)}, class_path="Gruppe15.main.Agent_x",
                    weights_path="Gruppe15/agent.pth")
    (HERE / "paket.json").write_text(json.dumps(evidence, indent=2)+"\n")
    print(evidence)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("out", type=Path)
    build(p.parse_args().out)
