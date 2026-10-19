"""Regel-Bausteine, die die Netz-Aktion in klaren Situationen ueberschreiben.

Alle Funktionen arbeiten im kanonischen Raum (eigener Spawn auf (0, 0)).
Die Schalter stehen in config.py (Default aus, alte Checkpoints unveraendert).

Analyse 19.10.2026 (m1_early gegen Solution_92, 40 Val-Karten): Units mit einem
bewiesenen Punkte-Tile als Ziel warten unterwegs in ~21 % der Steps, und in
Match 3 laufen im Mittel 4,2 Units zu Punkte-Tiles in der Gegnerhaelfte
(Distanz ~14), von denen nur 0,34 besetzt werden.
"""
from __future__ import annotations

from collections import deque

import numpy as np

from . import geometry as geo


def distance_map(passable: np.ndarray, goal: tuple[int, int]) -> np.ndarray:
    """BFS-Schrittzahl jedes Tiles zum Ziel (4er-Nachbarschaft, nur passierbar).

    Unerreichbar = -1. Das Ziel selbst ist immer erreichbar (auch wenn dort
    gerade ein Asteroid vermutet wird, z. B. weil Asteroiden driften).
    """
    W, H = passable.shape
    dist = np.full((W, H), -1, dtype=np.int32)
    gx, gy = int(goal[0]), int(goal[1])
    dist[gx, gy] = 0
    q = deque([(gx, gy)])
    while q:
        x, y = q.popleft()
        d = dist[x, y] + 1
        for k in range(1, 5):
            nx, ny = x + int(geo.DIR_DX[k]), y + int(geo.DIR_DY[k])
            if 0 <= nx < W and 0 <= ny < H and dist[nx, ny] < 0 and passable[nx, ny]:
                dist[nx, ny] = d
                q.append((nx, ny))
    return dist


def first_step(dist: np.ndarray, pos: tuple[int, int], mask: np.ndarray,
               energy_map: np.ndarray | None = None) -> int | None:
    """Erlaubte Richtung, die die BFS-Distanz um 1 senkt (bei Gleichstand: mehr
    Feldenergie). None, wenn kein solcher Schritt moeglich ist."""
    W, H = dist.shape
    x, y = int(pos[0]), int(pos[1])
    here = dist[x, y]
    best, best_e = None, -np.inf
    for k in range(1, 5):
        if not mask[k]:
            continue
        nx, ny = x + int(geo.DIR_DX[k]), y + int(geo.DIR_DY[k])
        if not (0 <= nx < W and 0 <= ny < H):
            continue
        nd = dist[nx, ny]
        if nd < 0:
            continue
        if here < 0 or nd < here:
            e = float(energy_map[nx, ny]) if energy_map is not None else 0.0
            if best is None or e > best_e:
                best, best_e = k, e
    return best


class PathCache:
    """Distanzkarten pro Ziel, gueltig fuer genau einen Step."""

    def __init__(self) -> None:
        self.step = None
        self.maps: dict[tuple[int, int], np.ndarray] = {}

    def get(self, step: int, passable: np.ndarray, goal) -> np.ndarray:
        if step != self.step:
            self.step = step
            self.maps = {}
        key = (int(goal[0]), int(goal[1]))
        m = self.maps.get(key)
        if m is None:
            m = distance_map(passable, key)
            self.maps[key] = m
        return m


def plan_sap(ctx: dict, uid: int, planned: np.ndarray, stationary: np.ndarray,
             point_tiles: np.ndarray, dropoff: float = 0.5,
             min_value: float | None = None):
    """Sap-Ziel mit Abstimmung im Team (Schalter `smart_sap`).

    Bewertet jedes Tile in Reichweite, auf oder neben dem ein sichtbarer Gegner
    steht. Wert = erwarteter nuetzlicher Schaden (nicht mehr als die Restenergie
    des Gegners nach den schon geplanten Saps dieses Steps), stehende Gegner und
    Gegner auf Punkte-Tiles zaehlen mehr (sie bewegen sich kaum, ein Treffer
    nimmt dem Gegner Punkte), plus Bonus fuer einen Abschuss.
    `planned` (je sichtbarem Gegner) wird fuer das gewaehlte Ziel erhoeht.
    Rueckgabe (dx, dy, getroffene Gegner) oder None, wenn sich kein Sap lohnt.
    """
    ec = ctx["enemy_coords"]
    if len(ec) == 0:
        return None
    x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
    R = int(ctx["sap_range"])
    cost = float(ctx["sap_cost"])
    W, H = ctx["W"], ctx["H"]
    cand = set()
    for ex, ey in ec:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                tx, ty = int(ex) + dx, int(ey) + dy
                if 0 <= tx < W and 0 <= ty < H and abs(tx - x) <= R and abs(ty - y) <= R:
                    cand.add((tx, ty))
    if not cand:
        return None
    energies = ctx["enemy_energies"].astype(np.float64)
    on_pt = point_tiles[ec[:, 0], ec[:, 1]]
    still = stationary | on_pt
    remaining = energies - planned
    best, best_v, best_dmg = None, -1.0, None
    for tx, ty in cand:
        cheb = np.maximum(np.abs(ec[:, 0] - tx), np.abs(ec[:, 1] - ty))
        direct = cheb == 0
        near = cheb <= 1
        if not near.any():
            continue
        dmg = np.where(direct, cost, cost * dropoff) * near
        p = np.where(direct, np.where(still, 0.9, 0.5), np.where(still, 0.7, 0.4))
        alive = remaining >= 0
        useful = np.minimum(dmg, np.maximum(remaining + 1, 0)) * alive
        weight = np.where(on_pt, 1.5, 1.0)
        v = float((p * useful * weight).sum())
        kill = alive & near & (dmg > remaining + 5)
        v += float((p * kill * np.where(on_pt, 120.0, 60.0)).sum())
        if v > best_v:
            best, best_v, best_dmg = (tx, ty), v, dmg
    threshold = 0.3 * cost if min_value is None else min_value
    if best is None or best_v < threshold:
        return None
    planned += best_dmg
    hits = int((best_dmg > 0).sum())
    return best[0] - x, best[1] - y, hits
