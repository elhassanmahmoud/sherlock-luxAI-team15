"""Kurspaket "R3 + Taktikschicht" bauen (17.11.2026).

Übernimmt das freigegebene R3-Paket Datei für Datei (Code und Gewichte unverändert), legt die Taktikschicht als
`sherlock/r3t_tactics.py` dazu und ersetzt nur `sherlock/main.py` durch einen Einstieg, der R3s eigene Aktionswahl
um die Taktiken mit festen Schaltern ergänzt. Der Schüler-Mix (`schueler=`) wird nicht verpackt.

    python -m scripts.build_r3t_package --spec granate,sog,tanken --out experiments/candidates/r3t_20261117/agent.zip

Schreibt nie auf die Abgabedateien (`dist/agent.zip`, `Gruppe15.zip`) oder in das R3-Releaseverzeichnis.
"""
from __future__ import annotations

import argparse
import zipfile
from hashlib import sha256
from pathlib import Path

from agents.sherlock_r3t.tactics import TacticsCfg

ROOT = Path(__file__).resolve().parents[1]
R3_ZIP = ROOT / "experiments/releases/20261116_r3_finale/agent.zip"
R3_SHA = "8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d"
PROTECTED = {ROOT / "dist/agent.zip", ROOT / "Gruppe15.zip"}
FIXED_TIME = (1980, 1, 1, 0, 0, 0)

MAIN_TEMPLATE = '''"""Kurs-Einstieg: R3 (unverändert) + Taktikschicht r3t_tactics.py, gebaut von scripts/build_r3t_package.py."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

KIND = "sherlock_r3_selective_movement_0105658"
V14_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
R3_SHA = "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"
SPEC = {spec!r}


def check_payload(bundle):
    if bundle["kind"] != KIND:
        raise ValueError("Expected the registered R3 selective movement candidate")
    for key, expected in (("v14", V14_SHA), ("r3", R3_SHA)):
        if not isinstance(bundle[key], bytes) or sha256(bundle[key]).hexdigest() != expected:
            raise ValueError(f"Unexpected {{key}} checkpoint")


def _tactics_class():
    from .r3_adviser import SelectiveAdviceAgent
    from .v14 import geometry as geo
    from .v14.imitation_agent import canonical_action

    class R3TacticsAgent(SelectiveAdviceAgent):
        def __init__(self, *args, tactics, **kwargs):
            self.tactics = tactics
            super().__init__(*args, **kwargs)

        def _reset_episode_state(self):
            super()._reset_episode_state()
            if getattr(self, "tactics", None) is not None:
                self.tactics.reset()

        def _act(self, step, obs):
            base = super()._act(step, obs)
            if self.training or int(obs["match_steps"]) == 0 or not self.tactics.cfg.active():
                return base
            b = self.belief
            maps = [b.point_tiles, b.energy_map, b.nebula]
            if b.mirrored:
                maps = [geo.mirror_map(m) for m in maps]
            points, energy, nebula = maps
            W, H = points.shape
            assigned = {{}}
            for uid, t in ((self._prev_ctx or {{}}).get("assigned") or {{}}).items():
                if t is not None:
                    t = (int(t[0]), int(t[1]))
                    assigned[int(uid)] = geo.mirror_xy(*t, W, H) if b.mirrored else t
            est = getattr(self, "param_est", None)
            dropoff = est.dropoff(default=0.5) if est is not None else 0.5
            drain = est.nebula(default=None) if est is not None else None
            new = self.tactics.apply(base, obs, self.team_id, self.env_cfg or {{}}, point_tiles=points,
                                     energy_map=energy, nebula_map=nebula, nebula_drain=drain, dropoff=dropoff,
                                     assigned=assigned)
            for uid in np.flatnonzero(np.any(new != base, axis=1)):
                a, _, _ = canonical_action(new[uid], b.mirrored)
                self._prev_actions[int(uid)] = a
            return new

    return R3TacticsAgent


class Agent_x:
    def __init__(self, player, agent_path=None, name="Sherlock R3T Agent_X", train=False):
        self.player, self.name, self.env_cfg = player, name, None
        self.load_agent(agent_path or "agent.pth")

    def load_agent(self, load_path):
        import torch

        from .r3t_tactics import Tactics, TacticsCfg

        path = Path(load_path)
        if not path.is_file():
            path = Path(__file__).resolve().parent / "weights" / path.name
        bundle = torch.load(path, map_location="cpu", weights_only=True)
        check_payload(bundle)
        with TemporaryDirectory(prefix="sherlock_r3t_") as tmp:
            v14 = Path(tmp) / "v14.pth"
            v14.write_bytes(bundle["v14"])
            actor = _tactics_class()(self.player, str(v14), name=self.name, train=False, seed=0,
                                     advice_path=BytesIO(bundle["r3"]), mode="movement",
                                     tactics=Tactics(TacticsCfg.parse(SPEC)))
        actor.cfg.frozen = True
        actor.set_to_eval_mode()
        if self.env_cfg is not None:
            actor.set_env_cfg(self.env_cfg)
        self.agent_path, self._actor = str(path.resolve()), actor

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_actor"), name)

    def new_game(self, player=None):
        if player is not None:
            self.player = player
        self._actor.new_game(self.player)

    def set_env_cfg(self, env_cfg):
        self.env_cfg = env_cfg
        self._actor.set_env_cfg(env_cfg)

    def set_to_eval_mode(self):
        self._actor.set_to_eval_mode()

    def act(self, step, obs):
        return self._actor.act(step, obs)

    def update(self, step, obs, reward, action, terminated, next_obs):
        return

    def save_agent(self, path=None):
        return


Agent = Agent_x
'''


def build(spec: str, out: Path) -> str:
    cfg = TacticsCfg.parse(spec)
    if cfg.schueler:
        raise SystemExit("Der Schüler-Mix wird nicht verpackt (eigene Gewichte und neuerer Code nötig)")
    out = out.resolve()
    if out in PROTECTED or R3_ZIP.parent in out.parents:
        raise SystemExit(f"Geschützte Datei oder Verzeichnis: {out}")
    if out.exists():
        raise SystemExit(f"{out} existiert schon")
    if sha256(R3_ZIP.read_bytes()).hexdigest() != R3_SHA:
        raise SystemExit("R3-Paket hat nicht die freigegebene Prüfsumme")
    out.parent.mkdir(parents=True, exist_ok=True)
    tactics_src = (ROOT / "agents/sherlock_r3t/tactics.py").read_bytes()
    with zipfile.ZipFile(R3_ZIP) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "sherlock/main.py":
                data = MAIN_TEMPLATE.format(spec=spec).encode()
            new = zipfile.ZipInfo(info.filename, FIXED_TIME)
            new.compress_type = zipfile.ZIP_DEFLATED
            new.external_attr = info.external_attr
            dst.writestr(new, data)
        new = zipfile.ZipInfo("sherlock/r3t_tactics.py", FIXED_TIME)
        new.compress_type = zipfile.ZIP_DEFLATED
        new.external_attr = 0o644 << 16
        dst.writestr(new, tactics_src)
    return sha256(out.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="Taktik-Schalter wie bei r3t:, z. B. granate,sog,tanken")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print(f"{a.out}: SHA-256 {build(a.spec, Path(a.out))}")


if __name__ == "__main__":
    main()
