"""Hybrid aus V14 und nachgeahmter Policy (15.11.2026, Umbau).

Befund: Der Imitations-Schueler kaempft und ueberlebt wie der Lehrer (gegen Solution_92 in Match 1 im Mittel 0,8
statt 7,7 verlorene Units, vierfache Energie), punktet aber schlechter als V14 (181 statt 292 Punkte in Match 1).
V14 besetzt Punktefelder besser (Gedaechtnis, Zuweisung, Halterregeln). Der Hybrid laesst beide auf dieselbe
Beobachtung entscheiden und waehlt je Unit:

- mode "points": Halter auf bewiesenen Punktefeldern und Units, die V14 einem bewiesenen Punktefeld zuweist,
  spielen V14; alle anderen den Schueler.
- mode "combat": Units mit sichtbarem Gegner im Umkreis `combat_radius` (Chebyshev) spielen den Schueler, sonst V14.
- mode "sap": Will der Schueler schiessen, gilt sein Schuss; sonst V14.

Beide Teilagenten fuehren ihr eigenes Gedaechtnis aus denselben Beobachtungen.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from . import geometry as geo

MODES = ("points", "combat", "sap")


class HybridAgent:
    def __init__(self, player: str, v14_path: str, student_path: str, mode: str = "points",
                 combat_radius: int = 5, name: str = "Sherlock Hybrid", student_cfg=None, v14_cfg=None) -> None:
        from .imitation_agent import ImitationAgent
        from .main import Agent_x
        if mode not in MODES:
            raise ValueError(f"mode {mode!r} nicht in {MODES}")
        self.name = name
        self.player = player
        self.mode = mode
        self.combat_radius = int(combat_radius)
        self.v14 = Agent_x(player, agent_path=v14_path, cfg=v14_cfg, train=False, seed=0)
        self.v14.set_to_eval_mode()
        self.v14.autosave_on_terminate = False
        self.student = ImitationAgent(player, agent_path=student_path, cfg=student_cfg, train=False)
        self.student.set_to_eval_mode()
        self.caught_errors = 0
        self.stats = {"v14": 0, "student": 0}

    # Kurs-Schnittstelle -------------------------------------------------------------------------
    def new_game(self, player: Optional[str] = None) -> None:
        if player is not None:
            self.player = player
        self.v14.new_game(player)
        self.student.new_game(player)
        self.stats = {"v14": 0, "student": 0}

    def set_env_cfg(self, env_cfg) -> None:
        self.v14.set_env_cfg(env_cfg)
        self.student.set_env_cfg(env_cfg)

    def set_to_eval_mode(self) -> None:
        return

    def update(self, *args, **kwargs) -> None:
        return

    def save_agent(self, path: Optional[str] = None) -> None:
        return

    def load_agent(self, load_path: str) -> None:
        return

    def episode_stats(self) -> dict:
        n = max(1, self.stats["v14"] + self.stats["student"])
        return {"student_share": self.stats["student"] / n}

    def act(self, step: int, obs) -> np.ndarray:
        a14 = np.asarray(self.v14.act(step, obs))
        ast = np.asarray(self.student.act(step, obs))
        ctx = self.v14._prev_ctx
        if ctx is None:
            return a14
        out = a14.copy()
        belief = self.v14.belief
        for uid in ctx["ally_ids"].tolist():
            uid = int(uid)
            if self._use_student(ctx, belief, uid, ast[uid]):
                out[uid] = ast[uid]
                self.stats["student"] += 1
            else:
                self.stats["v14"] += 1
        return out

    def _use_student(self, ctx, belief, uid: int, student_action) -> bool:
        x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
        if self.mode == "sap":
            return int(student_action[0]) == geo.SAP
        if self.mode == "combat":
            ec = ctx["enemy_coords"]
            if len(ec) == 0:
                return False
            d = np.maximum(np.abs(ec[:, 0] - x), np.abs(ec[:, 1] - y))
            return bool((d <= self.combat_radius).any())
        # points: Halter und Units mit bewiesenem Punktefeld als Ziel bleiben bei V14
        holder = bool(belief.point_tiles[x, y]) and ctx["first_on_tile"].get((x, y)) == uid
        tgt = ctx["assigned"].get(uid)
        to_point = tgt is not None and bool(belief.point_tiles[int(tgt[0]), int(tgt[1])])
        return not (holder or to_point)
