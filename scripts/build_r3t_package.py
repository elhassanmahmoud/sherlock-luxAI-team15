"""Kurspaket "R3 + Taktikschicht" bauen (17.11.2026).

Übernimmt das freigegebene R3-Paket Datei für Datei (Code unverändert), legt die Taktikschicht als
`sherlock/r3t_tactics.py` dazu und ersetzt `sherlock/main.py` durch einen Einstieg, der R3s eigene Aktionswahl um die
Taktiken mit festen Schaltern ergänzt. Ohne Schüler bleibt auch `sherlock/weights/agent.pth` bytegleich.

Mit `schueler=` kommt der neuere Schüler-Code als Unterpaket `sherlock/stud/` (Kopie von agents/sherlock/*.py) dazu,
und `agent.pth` enthält zusätzlich die Schülergewichte (R3s v14- und r3-Teile bleiben bytegleich und werden wie in R3
per SHA-256 geprüft, der Schüler ebenso).

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
STUDENT_SHA = {student_sha!r}
STUDENT_OVERRIDES = {{"imit_stay_bias": 1.5, "imit_unstack": True}}


def check_payload(bundle):
    if bundle["kind"] != KIND:
        raise ValueError("Expected the registered R3 selective movement candidate")
    for key, expected in (("v14", V14_SHA), ("r3", R3_SHA)) + ((("student", STUDENT_SHA),) if STUDENT_SHA else ()):
        if not isinstance(bundle[key], bytes) or sha256(bundle[key]).hexdigest() != expected:
            raise ValueError(f"Unexpected {{key}} checkpoint")


def _tactics_class():
    from .r3_adviser import SelectiveAdviceAgent
    from .v14 import geometry as geo
    from .v14.imitation_agent import canonical_action

    class R3TacticsAgent(SelectiveAdviceAgent):
        def __init__(self, *args, tactics, student=None, **kwargs):
            self.tactics = tactics
            self.student = student
            super().__init__(*args, **kwargs)

        def _reset_episode_state(self):
            super()._reset_episode_state()
            if getattr(self, "tactics", None) is not None:
                self.tactics.reset()

        def _student_mix(self, step, obs, actions):
            student_actions = np.asarray(self.student.act(step, obs))
            ctx = self._prev_ctx
            if ctx is None or int(obs["match_steps"]) == 0:
                return actions
            out = actions.copy()
            ec = np.asarray(ctx.get("enemy_coords", np.zeros((0, 2), dtype=int))).reshape(-1, 2)
            radius = int(self.tactics.cfg.schueler_radius)
            for uid in ctx["ally_ids"].tolist():
                uid = int(uid)
                x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
                near = bool(len(ec)) and bool((np.maximum(np.abs(ec[:, 0] - x), np.abs(ec[:, 1] - y)) <= radius).any())
                holder = bool(self.belief.point_tiles[x, y]) and ctx["first_on_tile"].get((x, y)) == uid
                tgt = ctx["assigned"].get(uid)
                to_point = tgt is not None and bool(self.belief.point_tiles[int(tgt[0]), int(tgt[1])])
                keep = holder or to_point
                if (near and not (keep and self.tactics.cfg.schueler_halter)) or not keep:
                    out[uid] = student_actions[uid]
            return out

        def _sync(self, base, new):
            for uid in np.flatnonzero(np.any(new != base, axis=1)):
                a, _, _ = canonical_action(new[uid], self.belief.mirrored)
                self._prev_actions[int(uid)] = a

        def _act(self, step, obs):
            base = super()._act(step, obs)
            if self.training or not self.tactics.cfg.layer_active():
                return base
            mixed = self._student_mix(step, obs, base) if self.student is not None else base
            if int(obs["match_steps"]) == 0:
                return base
            if not self.tactics.cfg.active():
                self._sync(base, mixed)
                return mixed
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
            new = self.tactics.apply(mixed, obs, self.team_id, self.env_cfg or {{}}, point_tiles=points,
                                     energy_map=energy, nebula_map=nebula, nebula_drain=drain, dropoff=dropoff,
                                     assigned=assigned)
            self._sync(base, new)
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
            student = None
            if STUDENT_SHA:
                from dataclasses import replace

                from .stud.config import AgentConfig
                from .stud.imitation_agent import ImitationAgent
                from .stud.main import Agent_x as StudentBase

                sp = Path(tmp) / "student.pth"
                sp.write_bytes(bundle["student"])
                cfg = replace(StudentBase._cfg_from_checkpoint(str(sp)) or AgentConfig(), **STUDENT_OVERRIDES)
                student = ImitationAgent(self.player, agent_path=str(sp), cfg=cfg, train=False)
                student.set_to_eval_mode()
            actor = _tactics_class()(self.player, str(v14), name=self.name, train=False, seed=0,
                                     advice_path=BytesIO(bundle["r3"]), mode="movement",
                                     tactics=Tactics(TacticsCfg.parse(SPEC)), student=student)
        self._student = student
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
        if self._student is not None:
            self._student.new_game(self.player)

    def set_env_cfg(self, env_cfg):
        self.env_cfg = env_cfg
        self._actor.set_env_cfg(env_cfg)
        if self._student is not None:
            self._student.set_env_cfg(env_cfg)

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
    import io

    import torch

    from agents.sherlock_r3t.agent import STUDENTS

    cfg = TacticsCfg.parse(spec)
    student = Path(STUDENTS.get(cfg.schueler, cfg.schueler)).read_bytes() if cfg.schueler else b""
    out = out.resolve()
    if out in PROTECTED or R3_ZIP.parent in out.parents:
        raise SystemExit(f"Geschützte Datei oder Verzeichnis: {out}")
    if out.exists():
        raise SystemExit(f"{out} existiert schon")
    if sha256(R3_ZIP.read_bytes()).hexdigest() != R3_SHA:
        raise SystemExit("R3-Paket hat nicht die freigegebene Prüfsumme")
    out.parent.mkdir(parents=True, exist_ok=True)
    student_sha = sha256(student).hexdigest() if student else ""
    extra = {"sherlock/r3t_tactics.py": (ROOT / "agents/sherlock_r3t/tactics.py").read_bytes()}
    if student:
        extra["sherlock/stud/__init__.py"] = b""
        for f in sorted((ROOT / "agents/sherlock").glob("*.py")):
            if f.name != "__init__.py":
                extra[f"sherlock/stud/{f.name}"] = f.read_bytes()

    def put(dst, name, data, attr=0o644 << 16):
        info = zipfile.ZipInfo(name, FIXED_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = attr
        dst.writestr(info, data)

    with zipfile.ZipFile(R3_ZIP) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "sherlock/main.py":
                data = MAIN_TEMPLATE.format(spec=spec, student_sha=student_sha).encode()
            elif info.filename == "sherlock/weights/agent.pth" and student:
                bundle = torch.load(io.BytesIO(data), map_location="cpu", weights_only=True)
                bundle["student"] = student
                buf = io.BytesIO()
                torch.save(bundle, buf)
                data = buf.getvalue()
            put(dst, info.filename, data, info.external_attr)
        for name, data in extra.items():
            put(dst, name, data)
    return sha256(out.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="Taktik-Schalter wie bei r3t:, z. B. granate,sog,tanken")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print(f"{a.out}: SHA-256 {build(a.spec, Path(a.out))}")


if __name__ == "__main__":
    main()
