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


def better_sap_geometry(ctx: dict, uid: int, current: tuple[int, int, int],
                        current_score: float, dropoff: float = 0.5) -> tuple[int, int, int]:
    """Nur das Ziel eines bereits verfuegbaren Sap verbessern, nicht seine Maske.

    Gleicher Energiescore wie Agent_x._best_sap_target, keine Killboni oder
    Teamplanung. Negative sichtbare Gegner: unveraendertes altes Ziel, weil
    sie vor der Aktion entfernt werden und Energiescores verzerren koennen.
    Neue leere Zentren bekommen keinen Gegner-auf-Punkte-Tile-Bonus.
    Alte Gleichstaende bleiben erhalten; neue Zentren sind
    lexikografisch sortiert. Die Kandidaten-Gegner-Matrix hat hoechstens 144x16
    Eintraege. Gegnerenergie kommt als float32 aus make_context.
    """
    if np.any(ctx["enemy_energies"] < 0):
        return current
    ec = ctx["enemy_coords"]
    x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
    offsets = np.array([(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)],
                       dtype=np.int32)
    centers = np.unique((ec[:, None, :] + offsets).reshape(-1, 2), axis=0)
    radius = int(ctx["sap_range"])
    valid = ((centers[:, 0] >= 0) & (centers[:, 0] < ctx["W"])
             & (centers[:, 1] >= 0) & (centers[:, 1] < ctx["H"])
             & (np.abs(centers[:, 0] - x) <= radius)
             & (np.abs(centers[:, 1] - y) <= radius))
    centers = centers[valid]
    if len(centers) == 0:
        return current
    cheb = np.abs(centers[:, None, :] - ec[None, :, :]).max(axis=2)
    # Besetzte Zentren wurden schon im alten Pfad bewertet.
    new = ~(cheb == 0).any(axis=1)
    centers, cheb = centers[new], cheb[new]
    if len(centers) == 0:
        return current
    direct, splash = cheb == 0, cheb == 1
    energies = ctx["enemy_energies"]
    scores = ((direct * energies).sum(axis=1)
              + dropoff * (splash * energies).sum(axis=1))
    k = int(np.argmax(scores))
    if float(scores[k]) <= current_score:
        return current
    tx, ty = centers[k]
    return int(tx) - x, int(ty) - y, int((direct[k] | splash[k]).sum())


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


def fog_sap(ctx: dict, uid: int, belief, planned_fog: np.ndarray, dropoff: float = 0.5,
            min_frac: float = 0.6):
    """Sap auf unsichtbare Gegner auf ihren Punkte-Tiles (Schalter `fog_sap`).

    Der Gegner punktet pro Step mit jedem besetzten Punkte-Tile. Bringt er mehr
    Punkte, als sichtbare Gegner auf bekannten Punkte-Tiles erklaeren, stehen
    die uebrigen auf Punkte-Tiles, die wir gerade nicht sehen. Kandidaten sind
    bekannte Punkte-Tiles in der GEGNERHAELFTE ohne aktuelle Sicht; jedes wird
    mit Wahrscheinlichkeit versteckt / Kandidaten als besetzt angenommen.
    Gewaehlt wird das Zieltile mit dem groessten erwarteten Schaden (3x3).
    `planned_fog` merkt sich bereits beschossene Tiles dieses Steps.
    Rueckgabe (dx, dy) oder None.
    """
    W, H = ctx["W"], ctx["H"]
    pt = belief.point_tiles
    visible = belief.last_seen == belief.match_step
    xs, ys = np.meshgrid(np.arange(W), np.arange(H), indexing="ij")
    enemy_half = xs + ys > W - 1
    seen_occ = 0
    for ex, ey in ctx["enemy_coords"]:
        if pt[ex, ey]:
            seen_occ += 1
    hidden = int(belief.opp_gain) - seen_occ
    if hidden <= 0:
        return None
    cand = pt & ~visible & enemy_half & ~planned_fog
    n = int(cand.sum())
    if n == 0:
        return None
    p = min(1.0, hidden / n)
    x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
    R = int(ctx["sap_range"])
    cost = float(ctx["sap_cost"])
    best, best_v = None, 0.0
    cx, cy = np.nonzero(cand)
    targets = set()
    for tx, ty in zip(cx, cy):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                a, b = int(tx) + dx, int(ty) + dy
                if 0 <= a < W and 0 <= b < H and abs(a - x) <= R and abs(b - y) <= R:
                    targets.add((a, b))
    for a, b in targets:
        cheb = np.maximum(np.abs(cx - a), np.abs(cy - b))
        v = p * cost * (float((cheb == 0).sum()) + dropoff * float((cheb == 1).sum()))
        if v > best_v:
            best, best_v = (a, b), v
    if best is None or best_v < min_frac * cost:
        return None
    a, b = best
    planned_fog[max(0, a - 1):a + 2, max(0, b - 1):b + 2] = True
    return a - x, b - y


def ram_move(ctx: dict, uid: int, mask: np.ndarray, point_tiles: np.ndarray,
             rammed: set, margin: float = 10.0):
    """Schalter `ram`: auf ein Nachbar-Tile mit schwaecherem Gegner fahren.

    Kollisionsregel der Engine: Stehen am Ende eines Schritts Units beider Teams
    auf demselben Tile, ueberlebt das Team mit mehr Gesamtenergie, die anderen
    Units werden entfernt (gewertet mit der Energie NACH der Bewegung, vor Saps).
    Solution_92 laesst seine Units still auf Punkte-Tiles stehen. Ist unsere
    Energie nach der Bewegung um `margin` groesser als die aller sichtbaren
    Gegner auf dem Nachbar-Tile, zerstoert die Bewegung sie.
    Eine Unit auf einem eigenen Punkte-Tile rammt nur auf ein Punkte-Tile.
    `rammed` verhindert, dass zwei Units dasselbe Tile rammen.
    Rueckgabe Richtung oder None.
    """
    ec = ctx["enemy_coords"]
    if len(ec) == 0:
        return None
    from . import geometry as geo
    x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
    e_after = float(ctx["ally_ene"][uid]) - float(ctx["move_cost"])
    on_point = bool(point_tiles[x, y])
    best, best_v = None, 0.0
    for d in range(1, 5):
        if not mask[d]:
            continue
        tx, ty = x + int(geo.DIR_DX[d]), y + int(geo.DIR_DY[d])
        if (tx, ty) in rammed:
            continue
        here = (ec[:, 0] == tx) & (ec[:, 1] == ty)
        if not here.any():
            continue
        enemy_e = float(ctx["enemy_energies"][here].sum())
        if e_after <= enemy_e + margin:
            continue
        tile_pt = bool(point_tiles[tx, ty])
        if on_point and not tile_pt:
            continue
        v = 2.0 * int(here.sum()) + (3.0 if tile_pt else 0.0)
        if v > best_v:
            best, best_v = d, v
    if best is not None:
        rammed.add((x + int(geo.DIR_DX[best]), y + int(geo.DIR_DY[best])))
    return best
