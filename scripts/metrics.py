"""Agentenunabhaengige Kennzahlen pro Spiel (aus Beobachtung + ausgefuehrter Aktion).

Funktioniert fuer jeden Agenten (auch den Prof-DQN), weil nur echte Env-Daten
im Original-Koordinatensystem benutzt werden:

  wait_frac      Anteil Unit-Steps mit Aktion 0 (stay)
  invalid_frac   Anteil Unit-Steps mit wirkungsloser Aktion: Bewegung aus der
                 Karte / auf sichtbaren Asteroiden / mit zu wenig Energie,
                 Sap ausser Reichweite oder mit zu wenig Energie
  sap_attempts   Anzahl Sap-Aktionen
  sap_hits       Saps, deren 3x3-Zielbereich einen sichtbaren Gegner enthielt
  stack_frac     Anteil Unit-Steps auf einem Tile mit weiterer eigener Unit
  relics_seen    verschiedene Relic-Positionen, die im Spiel sichtbar waren
"""
from __future__ import annotations

import numpy as np

DX = np.array([0, 0, 1, 0, -1])
DY = np.array([0, -1, 0, 1, 0])


class GameTracker:
    def __init__(self, team_id: int, env_cfg: dict):
        self.team = int(team_id)
        self.opp = 1 - self.team
        self.W = int(env_cfg.get("map_width", 24))
        self.H = int(env_cfg.get("map_height", 24))
        self.move_cost = float(env_cfg.get("unit_move_cost", 3))
        self.sap_cost = float(env_cfg.get("unit_sap_cost", 40))
        self.sap_range = int(env_cfg.get("unit_sap_range", 5))
        self.unit_steps = 0
        self.wait = 0
        self.invalid = 0
        self.sap_attempts = 0
        self.sap_hits = 0
        self.stacked = 0
        self.relics: set[tuple[int, int]] = set()

    def record(self, obs, actions) -> None:
        actions = np.asarray(actions)
        mask = np.asarray(obs["units_mask"], dtype=bool)
        pos = np.asarray(obs["units"]["position"])
        ene = np.asarray(obs["units"]["energy"])
        if ene.ndim == 3:
            ene = ene[..., 0]
        tile = np.asarray(obs["map_features"]["tile_type"])

        rel = np.asarray(obs["relic_nodes"])
        for i in np.nonzero(np.asarray(obs["relic_nodes_mask"], dtype=bool))[0]:
            self.relics.add((int(rel[i][0]), int(rel[i][1])))

        ids = np.nonzero(mask[self.team])[0]
        if len(ids) == 0:
            return
        my_pos = pos[self.team]
        enemy = pos[self.opp][mask[self.opp]]
        enemy = enemy[enemy[:, 0] >= 0]

        tiles, counts = np.unique(my_pos[ids], axis=0, return_counts=True)
        crowded = {tuple(t) for t, c in zip(tiles.tolist(), counts) if c > 1}

        for u in ids:
            x, y = int(my_pos[u][0]), int(my_pos[u][1])
            e = float(ene[self.team][u])
            a = int(actions[u][0])
            self.unit_steps += 1
            if (x, y) in crowded:
                self.stacked += 1
            if a == 0:
                self.wait += 1
            elif 1 <= a <= 4:
                tx, ty = x + DX[a], y + DY[a]
                off = not (0 <= tx < self.W and 0 <= ty < self.H)
                if off or e < self.move_cost or tile[tx, ty] == 2:
                    self.invalid += 1
            elif a == 5:
                self.sap_attempts += 1
                dx, dy = int(actions[u][1]), int(actions[u][2])
                if max(abs(dx), abs(dy)) > self.sap_range or e < self.sap_cost:
                    self.invalid += 1
                    continue
                tx, ty = x + dx, y + dy
                if len(enemy) and (np.maximum(np.abs(enemy[:, 0] - tx),
                                              np.abs(enemy[:, 1] - ty)) <= 1).any():
                    self.sap_hits += 1

    def summary(self) -> dict:
        n = max(1, self.unit_steps)
        return dict(
            unit_steps=self.unit_steps,
            wait_frac=self.wait / n,
            invalid_frac=self.invalid / n,
            sap_attempts=self.sap_attempts,
            sap_hits=self.sap_hits,
            stack_frac=self.stacked / n,
            relics_seen=len(self.relics),
        )
