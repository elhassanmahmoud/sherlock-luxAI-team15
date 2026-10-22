"""Taktik-Planer mit einem Schritt Vorausschau (22.10.2026, ENTWURF, im Agenten nicht eingebunden).

`simulate()` bildet einen Engine-Schritt nach und wurde gegen luxai_s3 geprueft (2 Spiele, ~6900
Unit-Schritte je Seite: Abweichungen nur bei Neuspawns und am letzten Matchschritt).

Fuer eigene Units in Gegnernaehe werden Bewegungs- und Sap-Alternativen gemeinsam gegen eine
Ein-Schritt-Simulation der Engine bewertet (Reihenfolge wie luxai_s3/env.py: Bewegung, Sap,
Kollision und Void auf Energie nach Bewegung, Energiefeld/Nebel). Gegner: sapfaehige Schiffe auf
bekannten Punkte-Tiles sappen wie Solution_92 (opp_model) die aktuelle Position ihres Ziels und
bleiben stehen; alle anderen Gegner bleiben stehen und sappen nicht (Vereinfachung).

Bewertung des Folgezustands: besetzte bekannte Punkte-Tiles (je einmal), eigene Tode und
Energieverluste, gegnerische Tode und Energieverluste, plus ein kleiner Bonus fuer die vom Netz
bevorzugte Aktion (normierte Q-Werte), damit langfristige Planung des Netzes erhalten bleibt.
Optimierung: koordinatenweise ab der bisherigen Aktion (Netz + Regeln), zwei Durchgaenge.
Alles im kanonischen Raum des Agenten, nur Beobachtung/Belief (keine Engine-Wahrheit).
"""
from __future__ import annotations

import numpy as np

from . import geometry as geo

STAY, SAP = geo.STAY, geo.SAP


class Situation:
    """Feste Groessen eines Schritts fuer die Simulation."""

    def __init__(self, ctx: dict, belief, dropoff: float, void: float, nebula_red: float,
                 enemy_saps: dict[int, tuple], enemy_moves: dict[int, tuple] | None = None) -> None:
        self.W, self.H = ctx["W"], ctx["H"]
        self.ids = [int(u) for u in ctx["ally_ids"].tolist()]
        self.pos = {u: (int(ctx["ally_pos"][u][0]), int(ctx["ally_pos"][u][1])) for u in self.ids}
        self.ene = {u: float(ctx["ally_ene"][u]) for u in self.ids}
        self.ec = [tuple(int(v) for v in c) for c in ctx["enemy_coords"].tolist()]
        self.ee = [float(e) for e in ctx["enemy_energies"].tolist()]
        self.move_cost = float(ctx["move_cost"])
        self.sap_cost = float(ctx["sap_cost"])
        self.sap_range = int(ctx["sap_range"])
        self.dropoff = float(dropoff)
        self.void = float(void)
        self.nebula_red = float(nebula_red)
        self.passable = ctx["passable"]
        self.field = ctx["energy_map"]
        self.nebula = ctx["nebula"]
        self.points = belief.point_tiles
        self.enemy_saps = dict(enemy_saps)  # Gegnerindex -> Zielposition (x, y)
        self.enemy_moves = dict(enemy_moves or {})  # Gegnerindex -> Position nach Bewegung


def destination(sit: Situation, u: int, a: int) -> tuple[int, int]:
    x, y = sit.pos[u]
    if 1 <= a <= 4 and sit.ene[u] >= sit.move_cost:
        nx, ny = x + int(geo.DIR_DX[a]), y + int(geo.DIR_DY[a])
        if 0 <= nx < sit.W and 0 <= ny < sit.H and sit.passable[nx, ny]:
            return nx, ny
    return x, y


def _sap_damage(cost: float, drop: float, n_direct: int, n_adj: int) -> float:
    # Engine: cost je direktem Treffer, daneben int16(cost * dropoff * Anzahl) zusammen
    return cost * n_direct + int(cost * drop * n_adj)


def _field(e: float, gain: float) -> float:
    # Engine: clip(e + gain, 0, 400); bleibt e < 0 auch mit Feld negativ, unveraendert (Entfernung)
    if e < 0 and e + gain < 0:
        return e
    return min(400.0, max(0.0, e + gain))


def simulate(sit: Situation, actions: dict[int, tuple]) -> dict:
    """actions: uid -> (a, dx, dy). Liefert Endpositionen/-energien und Tode beider Seiten.

    Nachbau von luxai_s3/env.py step: Bewegung (Kosten nur bei echter Bewegung), Saps mit der
    Energie nach Bewegung, Kollision (Summen der Energie nach Bewegung; die Gegenseite zaehlt nur
    mit Units, deren Energie nach Sap >= 0 ist), Void (Quelle Energie nach Bewegung, geteilt durch
    eigene Units mit Energie >= 0 auf dem Tile), Energiefeld/Nebel.
    """
    pos, ene = {}, {}
    for u in sit.ids:
        a = actions.get(u, (STAY, 0, 0))[0]
        pos[u] = destination(sit, u, a)
        ene[u] = sit.ene[u] - (sit.move_cost if pos[u] != sit.pos[u] else 0.0)
    orig = dict(ene)
    epos = [sit.enemy_moves.get(k, p) for k, p in enumerate(sit.ec)]
    eorig = [e - (sit.move_cost if epos[k] != sit.ec[k] else 0.0) for k, e in enumerate(sit.ee)]
    eene = list(eorig)
    cost, drop = sit.sap_cost, sit.dropoff
    n = len(epos)
    # eigene Saps
    e_dir, e_adj = [0] * n, [0] * n
    for u in sit.ids:
        a, dx, dy = actions.get(u, (STAY, 0, 0))
        if a != SAP or orig[u] < cost or max(abs(dx), abs(dy)) > sit.sap_range:
            continue
        tx, ty = pos[u][0] + dx, pos[u][1] + dy
        if not (0 <= tx < sit.W and 0 <= ty < sit.H):
            continue
        ene[u] -= cost
        for k, (ex, ey) in enumerate(epos):
            d = max(abs(ex - tx), abs(ey - ty))
            if d == 0:
                e_dir[k] += 1
            elif d == 1:
                e_adj[k] += 1
    for k in range(n):
        if e_dir[k] or e_adj[k]:
            eene[k] -= _sap_damage(cost, drop, e_dir[k], e_adj[k])
    # gegnerische Saps (Solution_92: auf die aktuelle Position ihres Ziels)
    u_dir: dict[int, int] = {}
    u_adj: dict[int, int] = {}
    for k, (tx, ty) in sit.enemy_saps.items():
        if eorig[k] < cost:
            continue
        eene[k] -= cost
        for u in sit.ids:
            d = max(abs(pos[u][0] - tx), abs(pos[u][1] - ty))
            if d == 0:
                u_dir[u] = u_dir.get(u, 0) + 1
            elif d == 1:
                u_adj[u] = u_adj.get(u, 0) + 1
    for u in set(u_dir) | set(u_adj):
        ene[u] -= _sap_damage(cost, drop, u_dir.get(u, 0), u_adj.get(u, 0))
    # Kollisionen
    ours_at: dict = {}
    for u in sit.ids:
        ours_at.setdefault(pos[u], []).append(u)
    theirs_at: dict = {}
    for k, p in enumerate(epos):
        theirs_at.setdefault(p, []).append(k)
    dead = set()
    edead = set()
    for p in set(ours_at) & set(theirs_at):
        mine = sum(orig[u] for u in ours_at[p])
        other = sum(eorig[k] for k in theirs_at[p])
        if any(eene[k] >= 0 for k in theirs_at[p]) and not other < mine:
            dead.update(ours_at[p])
        if any(ene[u] >= 0 for u in ours_at[p]) and not mine < other:
            edead.update(theirs_at[p])
    # Void
    if sit.void > 0:
        for u in sit.ids:
            x, y = pos[u]
            src = sum(eorig[k] for k, (ex, ey) in enumerate(epos) if abs(ex - x) + abs(ey - y) == 1)
            if src:
                cnt = sum(1 for v in ours_at[pos[u]] if ene[v] >= 0) or 1
                ene[u] -= int(sit.void * src / cnt)
        for k, (ex, ey) in enumerate(epos):
            src = sum(orig[u] for u in sit.ids if abs(pos[u][0] - ex) + abs(pos[u][1] - ey) == 1)
            if src:
                cnt = sum(1 for j in theirs_at[(ex, ey)] if eene[j] >= 0) or 1
                eene[k] -= int(sit.void * src / cnt)
    # Energiefeld / Nebel (Gegner: unsere Schaetzung des Feldes)
    for u in sit.ids:
        x, y = pos[u]
        ene[u] = _field(ene[u], float(sit.field[x, y]) - (sit.nebula_red if sit.nebula[x, y] else 0.0))
        if ene[u] < 0:
            dead.add(u)
    for k, (ex, ey) in enumerate(epos):
        eene[k] = _field(eene[k], float(sit.field[ex, ey]) - (sit.nebula_red if sit.nebula[ex, ey] else 0.0))
        if eene[k] < 0:
            edead.add(k)
    return dict(pos=pos, ene=ene, dead=dead, epos=epos, eene=eene, edead=edead)


def score(sit: Situation, out: dict, w: dict) -> float:
    held = {out["pos"][u] for u in sit.ids if u not in out["dead"] and sit.points[out["pos"][u]]}
    s = w["point"] * len(held)
    for u in sit.ids:
        if u in out["dead"]:
            s -= w["death"] + w["energy"] * max(sit.ene[u], 0.0)
        else:
            s -= w["energy"] * max(sit.ene[u] - out["ene"][u], 0.0)
    for k in range(len(sit.ec)):
        if sit.ee[k] < 0:
            continue  # schon tot, verschwindet vor diesem Schritt
        if k in out["edead"]:
            s += w["kill"] + w["energy"] * sit.ee[k]
        else:
            s += w["energy"] * max(sit.ee[k] - out["eene"][k], 0.0)
    return s


def plan(sit: Situation, base: dict[int, tuple], options: dict[int, list], qpref: dict[int, dict],
         w: dict, passes: int = 2) -> dict[int, tuple]:
    """Koordinatenweise Verbesserung der Aktionen ausgewaehlter Units (options: uid -> Alternativen)."""
    cur = dict(base)
    best = score(sit, simulate(sit, cur), w) + sum(qpref.get(u, {}).get(cur[u][0], 0.0) for u in cur)
    for _ in range(passes):
        changed = False
        for u, alts in options.items():
            for alt in alts:
                if alt == cur[u]:
                    continue
                trial = dict(cur)
                trial[u] = alt
                val = score(sit, simulate(sit, trial), w) + sum(
                    qpref.get(v, {}).get(trial[v][0], 0.0) for v in trial)
                if val > best + 1e-9:
                    best, cur, changed = val, trial, True
        if not changed:
            break
    return cur
