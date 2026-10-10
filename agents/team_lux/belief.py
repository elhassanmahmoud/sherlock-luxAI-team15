"""Gedächtnis über die Spielzeit: Relics, Kandidaten-/Punkte-Tiles, erkundete Tiles, Karte."""
import numpy as np


class Belief:
    def __init__(self, team_id: int, W: int = 24, H: int = 24):
        self.team_id = team_id
        self.W, self.H = W, H
        self.relic_positions = set()             # über Matches hinweg gemerkt
        self.candidate_tiles = np.zeros((W, H), bool)  # 5x5 um Relics, noch ungeklärt
        self.point_tiles = np.zeros((W, H), bool)      # bewiesene Punkte-Tiles
        self.explored = np.zeros((W, H), bool)
        self.tile_type = np.full((W, H), -1)           # letzte bekannte Werte
        self.energy = np.zeros((W, H))
        self.last_points = 0

    def update(self, step: int, obs) -> None:
        # TODO (Phase 2): Relics/Sicht/Karte übernehmen, Punkte-Tiles aus Punktzuwachs ableiten
        pass
