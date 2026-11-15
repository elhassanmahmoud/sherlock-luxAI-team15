"""Kaggle-Platz-3-Agent als Gegner im Kursformat (15.11.2026). Nur Testgegner, nie Teil der Abgabe.

Der Agent (lux3-bot 0.4.8_fn, Apache-2.0) haelt seinen Spielzustand in Klassenattributen (Global).
Darum werden seine Module fuer jedes Spiel frisch importiert. Sein Ordner wird ans ENDE von sys.path
gehaengt, damit er keine Projekt- oder Bibliotheksmodule verdecken kann. Herunterladen mit
`python -m scripts.fetch_kaggle3`.
"""
from __future__ import annotations

import importlib
import os
import sys

import numpy as np

from scripts.fetch_kaggle3 import TARGET

CFG_KEYS = ("max_units", "unit_move_cost", "unit_sap_cost", "unit_sap_range", "unit_sensor_range")


class Kaggle3Opponent:
    """Kurs-Schnittstelle (set_env_cfg/act) um den Kaggle-Agenten. Ein Objekt = ein Spiel."""

    def __init__(self, player: str, bot_dir: str | os.PathLike = TARGET, name: str = "Kaggle3 lux3-bot 0.4.8_fn"):
        bot_dir = os.path.realpath(bot_dir)
        if not os.path.isfile(os.path.join(bot_dir, "agent", "agent.py")):
            raise FileNotFoundError(f"Kaggle-Agent fehlt in {bot_dir}: zuerst `python -m scripts.fetch_kaggle3`")
        self.player = player
        self.name = name
        self.bot_dir = bot_dir
        for mod in list(sys.modules):
            if mod == "agent" or mod.startswith("agent."):
                del sys.modules[mod]
        if bot_dir not in sys.path:
            sys.path.append(bot_dir)
        self.base = importlib.import_module("agent.base")
        if not os.path.realpath(self.base.__file__).startswith(bot_dir + os.sep):
            raise RuntimeError(f"Falsches Paket 'agent' geladen: {self.base.__file__}")
        self.base.Global.VERBOSITY = -1
        # NUM_MATCHES_IN_GAME bleibt bewusst 5 (Kaggle): Mit 3 haelt der Agent das Spiel nach zwei
        # Matchsiegen fuer entschieden und schaltet in Match 3 in GameOverParams (spielt kaum noch),
        # ausserdem bleibt sein Netzmerkmal match_number/5 so wie im Training.
        self._module = importlib.import_module("agent.agent")
        self.agent = None

    def set_env_cfg(self, env_cfg) -> None:
        cfg = {k: int(np.asarray(env_cfg[k])) for k in CFG_KEYS}
        weights = os.path.join(self.bot_dir, "imitation_learning", "weights")
        self.agent = self._module.Agent(self.player, cfg, weights)

    def act(self, step: int, obs) -> np.ndarray:
        if self.agent is None:
            raise RuntimeError("set_env_cfg() muss vor act() aufgerufen werden")
        o = {k: ({kk: np.asarray(vv) for kk, vv in v.items()} if isinstance(v, dict) else np.asarray(v))
             for k, v in obs.items()}
        return np.asarray(self.agent.act(step, o, 60), dtype=int)
