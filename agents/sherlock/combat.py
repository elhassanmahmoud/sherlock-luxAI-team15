"""Kampftechniken gegen starke, koordinierte Gegner (15.11.2026, Schalter in config.py, Standard aus).

Anlass: Gegen den Kaggle-Platz-3-Agenten verliert V14 rund 20 Units pro Match (Gegner fast keine),
die Energie unserer Units faellt in Match 1 von 95 auf 49, die des Gegners steigt auf 215.
Energie entscheidet Kollisionen (hoehere Gesamtenergie auf dem Tile ueberlebt), den Energie-Sog
benachbarter Units und wie oft man schiessen kann. Daraus drei Techniken:

- charge: Units mit wenig Energie, die kein Punkte-Tile halten, tanken am besten erreichbaren
  Energiefeld, bis sie wieder genug haben (Hysterese low/high).
- focus_sap: Das Team plant je Schritt, welche stehenden Gegner es mit mehreren Schuessen sicher
  ausschalten kann (Schaden > Energie + moegliche Feld-Erholung), und weist genau so viele
  Schuetzen zu. Halter schiessen bevorzugt, weil sie ohnehin stehen bleiben.
- hunt: Units mit viel Energie laufen auf schwaechere, stehende Gegner in der Naehe zu, um sie
  per Kollision zu zerstoeren (das eigentliche Rammen am Nachbarfeld uebernimmt rules.ram_move).

Alle Koordinaten sind kanonisch (wie im restlichen Agenten); Saps werden spaeter gespiegelt.
"""
from __future__ import annotations

import math

import numpy as np

from . import geometry as geo
from .rules import first_step


def threat_maps(ctx: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Je Tile: (von sichtbarem Gegner besetzt, groesste Energie eines kardinal benachbarten
    Gegners, Anzahl bewaffneter Gegner in Sap-Reichweite)."""
    W, H = ctx["W"], ctx["H"]
    occ = np.zeros((W, H), dtype=bool)
    adj_max = np.full((W, H), -1.0)
    armed = np.zeros((W, H), dtype=np.int32)
    ec = ctx["enemy_coords"]
    if len(ec) == 0:
        return occ, adj_max, armed
    ee = ctx["enemy_energies"].astype(np.float64)
    R = int(ctx["sap_range"])
    cost = float(ctx["sap_cost"])
    for (ex, ey), e in zip(ec, ee):
        ex, ey = int(ex), int(ey)
        if e < 0:
            continue
        occ[ex, ey] = True
        for d in range(1, 5):
            nx, ny = ex + int(geo.DIR_DX[d]), ey + int(geo.DIR_DY[d])
            if 0 <= nx < W and 0 <= ny < H:
                adj_max[nx, ny] = max(adj_max[nx, ny], e)
        if e >= cost:
            armed[max(0, ex - R):ex + R + 1, max(0, ey - R):ey + R + 1] += 1
    return occ, adj_max, armed


def charge_goal(ctx: dict, uid: int, dist_unit: np.ndarray, radius: int, nebula_drain: float,
                threats: tuple, claimed: set, horizon: float = 10.0):
    """Bestes Tank-Tile fuer eine Unit innerhalb von `radius` BFS-Schritten oder None.

    Wertung: Feldenergie (minus Nebelabzug) abzueglich anteiliger Wegkosten ueber `horizon` Schritte,
    besetzte Tiles und Tiles neben staerkeren Gegnern ausgeschlossen, bewaffnete Gegner in Reichweite
    und schon von anderen tankenden Units gewaehlte Tiles bestraft. None, wenn das eigene Tile
    mindestens so gut ist."""
    occ, adj_max, armed = threats
    x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
    e = float(ctx["ally_ene"][uid])
    em = np.clip(ctx["energy_map"].astype(np.float64), -20.0, 20.0)
    drain = np.where(ctx["nebula"], nebula_drain, 0.0)
    move_cost = float(ctx["move_cost"])

    def score(tx: int, ty: int, d: int) -> float:
        s = em[tx, ty] - drain[tx, ty] - move_cost * d / horizon
        s -= 3.0 * min(int(armed[tx, ty]), 3)
        if (tx, ty) in claimed:
            s -= 4.0
        return s

    here = score(x, y, 0)
    best, best_s = None, here + 1.0
    reach = (dist_unit >= 0) & (dist_unit <= radius)
    for tx, ty in zip(*np.nonzero(reach)):
        tx, ty = int(tx), int(ty)
        if occ[tx, ty] or adj_max[tx, ty] >= e:
            continue
        s = score(tx, ty, int(dist_unit[tx, ty]))
        if s > best_s:
            best, best_s = (tx, ty), s
    return best


def focus_plan(ctx: dict, shooters: list[int], point_tiles: np.ndarray, stationary: np.ndarray,
               holders: set, dropoff: float = 0.25, reserve: float = 10.0, margin: float = 1.0,
               max_gain: float = 20.0) -> dict[int, tuple[int, int, int]]:
    """Gemeinsame Abschuesse: {uid: (dx, dy, getroffene Gegner)}.

    Ziele sind nur sichtbare Gegner, die im letzten Schritt stehen blieben oder auf einem bekannten
    Punkte-Tile stehen (Saps wirken nach der Bewegung). Benoetigter Schaden = Energie + positive
    Feldenergie ihres Tiles (hoechstens max_gain) + margin. Ein Ziel wird nur eingeplant, wenn genug
    Schuetzen in Reichweite sind, um es sicher zu zerstoeren. Streuschaden auf Nachbarn wird mit dem
    vorsichtigen Faktor `dropoff` mitgezaehlt."""
    ec = ctx["enemy_coords"]
    if len(ec) == 0 or not shooters:
        return {}
    ee = ctx["enemy_energies"].astype(np.float64)
    cost = float(ctx["sap_cost"])
    R = int(ctx["sap_range"])
    em = ctx["energy_map"]
    pos = {u: (int(ctx["ally_pos"][u][0]), int(ctx["ally_pos"][u][1])) for u in shooters}
    energy = {u: float(ctx["ally_ene"][u]) for u in shooters}
    free = [u for u in shooters if energy[u] >= cost + reserve]
    on_pt = np.array([bool(point_tiles[int(x), int(y)]) for x, y in ec])
    alive = ee >= 0
    still = (stationary | on_pt) & alive
    need = ee + np.clip([float(em[int(x), int(y)]) for x, y in ec], 0.0, max_gain) + margin
    dmg = np.zeros(len(ec))
    order = sorted(np.nonzero(still)[0], key=lambda j: (-int(on_pt[j]), math.ceil(need[j] / cost), need[j]))
    plan: dict[int, tuple[int, int, int]] = {}
    for j in order:
        rest = need[j] - dmg[j]
        if rest <= 0:
            continue
        tx, ty = int(ec[j][0]), int(ec[j][1])
        cand = [u for u in free if u not in plan and abs(pos[u][0] - tx) <= R and abs(pos[u][1] - ty) <= R]
        n = math.ceil(rest / cost)
        if n <= 0 or len(cand) < n:
            continue
        chosen = sorted(cand, key=lambda u: (u not in holders, -energy[u]))[:n]
        cheb = np.maximum(np.abs(ec[:, 0] - tx), np.abs(ec[:, 1] - ty))
        hit = (cheb <= 1) & alive
        for u in chosen:
            dmg += np.where(cheb == 0, cost, np.where(cheb == 1, cost * dropoff, 0.0))
            plan[u] = (tx - pos[u][0], ty - pos[u][1], int(hit.sum()))
    return plan


def hunt_target(ctx: dict, uid: int, dist_unit: np.ndarray, point_tiles: np.ndarray,
                stationary: np.ndarray, min_energy: float, radius: int, margin: float, taken: set):
    """Tile eines schwaecheren, stehenden Gegners, den die Unit erreichen und per Kollision
    zerstoeren kann, oder None. Gegner auf Punkte-Tiles zaehlen doppelt."""
    e = float(ctx["ally_ene"][uid])
    if e < min_energy:
        return None
    ec = ctx["enemy_coords"]
    if len(ec) == 0:
        return None
    ee = ctx["enemy_energies"].astype(np.float64)
    move_cost = float(ctx["move_cost"])
    tiles: dict[tuple[int, int], list[int]] = {}
    for j, (x, y) in enumerate(ec):
        if ee[j] >= 0:
            tiles.setdefault((int(x), int(y)), []).append(j)
    best, best_v = None, 0.0
    for (tx, ty), js in tiles.items():
        if (tx, ty) in taken or not (stationary[js].any() or point_tiles[tx, ty]):
            continue
        d = int(dist_unit[tx, ty])
        if d < 1 or d > radius:
            continue
        e_arrive = e - d * move_cost
        enemy_e = float(ee[js].sum()) + 20.0  # Gegner kann bis zur Ankunft noch tanken
        if e_arrive <= enemy_e + margin:
            continue
        v = (2.0 if point_tiles[tx, ty] else 1.0) * len(js) - 0.15 * d
        if v > best_v:
            best, best_v = (tx, ty), v
    return best


def step_to(ctx: dict, paths, uid: int, mask: np.ndarray, goal) -> int | None:
    """Erlaubter erster Schritt der BFS-Route zu `goal` (STAY, wenn schon dort)."""
    x, y = int(ctx["ally_pos"][uid][0]), int(ctx["ally_pos"][uid][1])
    if (x, y) == tuple(goal):
        return geo.STAY if mask[geo.STAY] else None
    dist = paths.get(ctx["step"], ctx["passable"], goal)
    return first_step(dist, (x, y), mask, ctx["energy_map"])
