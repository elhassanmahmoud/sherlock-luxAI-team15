"""R3 mit Taktikschicht (17.11.2026): das unveränderte R3-Paket plus agents/sherlock_r3t/tactics.py.

Lädt den Code und die Gewichte genau aus dem freigegebenen R3-Paket (scripts/r3_package.py) und hängt die
Taktikschicht hinter R3s eigene Aktionswahl. Weil die Schicht in `_act` sitzt, sieht R3s Parameterschätzer die
tatsächlich gespielten Befehle. Ohne Schalter spielt der Agent exakt wie R3.

    from agents.sherlock_r3t.agent import make_r3t
    agent = make_r3t("player_0", "experiments/releases/20261116_r3_finale/agent.zip", "granate,sog")
"""
from __future__ import annotations

from importlib import import_module
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from .tactics import Tactics, TacticsCfg

PREFIX = "r3t:"
DEFAULT_ZIP = Path(__file__).resolve().parents[2] / "experiments/releases/20261116_r3_finale/agent.zip"
_CLASSES: dict[str, type] = {}


def is_spec(name) -> bool:
    return isinstance(name, str) and name.startswith(PREFIX)


def _r3t_class(zip_path: Path):
    """Unterklasse von R3s SelectiveAdviceAgent aus dem geladenen Paket (Modul `sherlock`)."""
    key = str(zip_path)
    if key in _CLASSES:
        return _CLASSES[key]
    from scripts import r3_package

    r3_package._module_for(zip_path)
    base = import_module("sherlock.r3_adviser").SelectiveAdviceAgent
    geo = import_module("sherlock.v14.geometry")
    canonical_action = import_module("sherlock.v14.imitation_agent").canonical_action

    class R3TacticsAgent(base):
        def __init__(self, *args, tactics: Tactics, **kwargs):
            self.tactics = tactics
            super().__init__(*args, **kwargs)

        def _reset_episode_state(self):
            super()._reset_episode_state()
            if getattr(self, "tactics", None) is not None:
                self.tactics.reset()

        def _world_maps(self):
            b = self.belief
            maps = [b.point_tiles, b.energy_map, b.nebula]
            if b.mirrored:
                maps = [geo.mirror_map(m) for m in maps]
            return maps

        def _act(self, step, obs):
            base_actions = super()._act(step, obs)
            if self.training or int(obs["match_steps"]) == 0 or not self.tactics.cfg.active():
                return base_actions
            points, energy, nebula = self._world_maps()
            ctx = self._prev_ctx or {}
            assigned = {}
            W, H = points.shape
            for uid, t in (ctx.get("assigned") or {}).items():
                if t is not None:
                    t = (int(t[0]), int(t[1]))
                    assigned[int(uid)] = geo.mirror_xy(*t, W, H) if self.belief.mirrored else t
            est = getattr(self, "param_est", None)
            dropoff = est.dropoff(default=0.5) if est is not None else 0.5
            drain = est.nebula(default=None) if est is not None else None
            new = self.tactics.apply(base_actions, obs, self.team_id, self.env_cfg or {}, point_tiles=points,
                                     energy_map=energy, nebula_map=nebula, nebula_drain=drain, dropoff=dropoff,
                                     assigned=assigned)
            for uid in np.flatnonzero(np.any(new != base_actions, axis=1)):
                a, dx, dy = canonical_action(new[uid], self.belief.mirrored)
                self._prev_actions[int(uid)] = a
                self.ep_stats["sap_attempts"] += int(new[uid, 0] == geo.SAP) - int(base_actions[uid, 0] == geo.SAP)
            return new

    _CLASSES[key] = R3TacticsAgent
    return R3TacticsAgent


class R3TAgent:
    """Kursschnittstelle wie R3s eigenes Agent_x, nur mit Taktikschicht."""

    def __init__(self, player, zip_path=DEFAULT_ZIP, spec: str = "", name="Sherlock R3T"):
        import torch

        zip_path = Path(zip_path).resolve()
        cls = _r3t_class(zip_path)
        main = import_module("sherlock.main")
        from scripts import r3_package

        tmp, _ = r3_package._module_for(zip_path)
        bundle = torch.load(tmp / "sherlock" / "weights" / "agent.pth", map_location="cpu", weights_only=True)
        main.check_payload(bundle)
        self.player, self.name, self.env_cfg, self.spec = player, name, None, spec
        self.tactics = Tactics(TacticsCfg.parse(spec))
        with TemporaryDirectory(prefix="sherlock_r3t_") as d:
            v14 = Path(d) / "v14.pth"
            v14.write_bytes(bundle["v14"])
            actor = cls(player, str(v14), name=name, train=False, seed=0, advice_path=BytesIO(bundle["r3"]),
                        mode="movement", tactics=self.tactics)
        actor.cfg.frozen = True
        actor.set_to_eval_mode()
        self._actor = actor

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

    def update(self, *args, **kwargs):
        return

    def save_agent(self, path=None):
        return

    def episode_stats(self) -> dict:
        stats = dict(self._actor.episode_stats()) if hasattr(self._actor, "episode_stats") else {}
        stats.update({f"t_{k}": v for k, v in self.tactics.counts.items()})
        return stats


def make_r3t(player, zip_path=DEFAULT_ZIP, spec: str = ""):
    agent = R3TAgent(player, zip_path, spec)
    agent.set_to_eval_mode()
    return agent
