"""Bundle the trained movement policy with the released course files."""
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

from routes import HERE
from collect import EXPECTED, OUT, PACKAGE

SOURCE = HERE.parents[1] / "v16_finalwoche_20261122/zugnutzen/paket.py"
WRAPPER = """
from .kandidat import RouteAgent
from .v16_main import Agent_x as Original


class Agent_x(RouteAgent):
    def __init__(self, player, agent_path=None, name="Sherlock Agent_X", cfg=None, train=True, seed=None):
        super().__init__(Original(player, agent_path=agent_path, name=name, cfg=cfg, train=train, seed=seed))

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
        self.base = Original(self.base.player, agent_path=load_path, name=self.base.name, train=False)
        if cfg is not None:
            self.base.set_env_cfg(cfg)
        self.clear()


Agent = Agent_x
"""


def build():
    if sha256(PACKAGE.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError("V16 differs")
    spec = spec_from_file_location("archived_course_package", SOURCE)
    bundle = module_from_spec(spec)
    spec.loader.exec_module(bundle)
    files = bundle.archived_base()
    files["sherlock/main.py"] = WRAPPER.encode()
    # Only the runtime definitions up to the research-only working-tree factory are shipped.
    code = (HERE / "kandidat.py").read_text().split("\ndef create(side):")[0]
    start = code.index('if __package__')
    end = code.index('HERE = Path', start)
    local_import = "from .routes import DIRECTIONS, DX, DY, MIRROR_DIR, NAMES, SearchHistory, current, route_features"
    files["sherlock/kandidat.py"] = (code[:start] + local_import + "\n\n" + code[end:]).encode()
    for name in ("routes.py", "routengewichte.json"):
        files["sherlock/" + name] = (HERE / name).read_bytes()
    path = OUT / "sherlock_routenlernen_kurs.zip"
    if path.exists():
        from zipfile import ZipFile
        with ZipFile(path) as archive:
            if set(archive.namelist()) != set(files) or any(v != archive.read(k) for k, v in files.items()):
                raise ValueError("Existing immutable package differs")
        digest = sha256(path.read_bytes()).hexdigest()
    else:
        digest = bundle.write_experimental(path, files)
    source = {n: sha256((HERE / n).read_bytes()).hexdigest()
              for n in ("kandidat.py", "routes.py", "routengewichte.json")}
    report = dict(candidate=str(path), sha256=digest, original_sha256=EXPECTED, source=source)
    (HERE / "paket.json").write_text(json.dumps(report, indent=2) + "\n")
    print(path, digest, flush=True)


if __name__ == "__main__":
    build()
