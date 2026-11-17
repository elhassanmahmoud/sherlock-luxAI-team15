"""Taktikschicht über den fertigen R3-Befehlen (17.11.2026): Granaten, Schutz vor Sog, Tanken.

Grundlage ist die Messung R3 gegen Kaggle (experiments/analysis/r3_kaggle_20261117): R3 verliert je Match etwa
24 Units (Kaggle 3), meist mit nur rund 20 Energie: Halter auf Punktefeldern durch Schüsse aus der Ferne, schwache
Units durch den Energie-Sog neben starken Gegnern oder durch Zusammenstöße. Kaggle schießt doppelt so oft und trifft
mit dem Streuschaden oft mehrere Units.

Die Schicht ändert nur einzelne Units und nur, wenn ihre Rechnung einen klaren Vorteil zeigt. Alle Schalter sind
standardmäßig aus; ohne Schalter kommen die R3-Befehle unverändert zurück. Gerechnet wird in Weltkoordinaten nach
den Regeln der Engine (luxai_s3/env.py): erst Bewegung, dann Saps auf die neuen Positionen (Ziel voller Schaden,
die 8 Nachbarfelder Schaden mal Streufaktor), dann Zusammenstöße (die Seite mit mehr Energie auf dem Feld bleibt),
dann der Sog (Sog-Faktor mal Energie der gegnerischen Units auf den 4 Nachbarfeldern), zuletzt das Energiefeld.
Eine Unit stirbt, wenn ihre Energie danach unter 0 liegt und auch das Feld sie nicht mehr über 0 hebt.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields

import numpy as np

STAY, UP, RIGHT, DOWN, LEFT, SAP = range(6)
DXY = ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0))
ADJ4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass
class TacticsCfg:
    granate: bool = False
    """Schüsse nach erwartetem Schaden samt Streuung auf die vorhergesagten Positionen, im Team abgestimmt."""
    granate_min: float = 1.0
    """Ein neuer Schuss muss mindestens so viel erwarteten Wert bringen (in Schusskosten)."""
    granate_keep: float = 1.0
    """Nach einem neuen Schuss bleibt mindestens so viel Energie (in Schusskosten): Halter sollen einen Treffer
    überleben. Die meisten R3-Units starben auf Punktefeldern mit rund 20 Energie."""
    granate_new: bool = True
    """Stehende Units ohne R3-Schuss dürfen neu feuern."""
    granate_retarget: float = 0.25
    """R3-Schüsse auf sichtbare Gegner bekommen ein neues Ziel, wenn es so viel mehr Wert bringt (in Schusskosten)."""
    kill_bonus: float = 1.0
    """Zusätzlicher Wert eines erwarteten Abschusses (in Schusskosten)."""
    holder_bonus: float = 0.5
    """Schaden an Gegnern auf bekannten Punktefeldern zählt um diesen Anteil mehr."""
    sog: bool = False
    """Bewegungen und Stehenbleiben meiden, die durch Sog oder Zusammenstoß wahrscheinlich tödlich sind."""
    sog_vf: float = 0.25
    """Angenommener Sog-Faktor (die Engine zieht ihn aus 0,0625/0,125/0,25/0,375; Mittel 0,2)."""
    sog_risk: float = 0.5
    """Ab diesem Todesrisiko weicht eine Unit aus, wenn eine Alternative mindestens 0,25 sicherer ist."""
    sog_holder_risk: float = 0.75
    """Halter auf bekannten Punktefeldern verlassen ihr Feld erst ab diesem Risiko."""
    tanken: bool = False
    """Stehende Units ohne Punktefeld und ohne erreichtes Ziel ziehen auf ein deutlich besseres Nachbarfeld."""
    tanken_gain: float = 3.0
    """Mindestens so viel mehr Feldenergie je Schritt als hier, nach Abzug der Zugkosten."""

    @classmethod
    def parse(cls, spec: str) -> "TacticsCfg":
        """'granate,sog,granate_keep=0.5' -> Schalter an bzw. Werte gesetzt."""
        kinds = {f.name: f.type for f in fields(cls)}
        out = {}
        for part in filter(None, (p.strip() for p in (spec or "").split(","))):
            key, _, val = part.partition("=")
            if key not in kinds:
                raise ValueError(f"Unbekannter Taktik-Schalter: {key}")
            default = getattr(cls, key)
            if isinstance(default, bool):
                out[key] = True if not val else val.lower() in ("1", "true", "ja", "on")
            else:
                out[key] = type(default)(val)
        return cls(**out)

    def active(self) -> bool:
        return self.granate or self.sog or self.tanken


def _cheb(a, b) -> int:
    return max(abs(int(a[0]) - int(b[0])), abs(int(a[1]) - int(b[1])))


class Tactics:
    """Zustand über die Schritte eines Spiels (letzte Gegnerpositionen) und Zähler je Spiel."""

    def __init__(self, cfg: TacticsCfg):
        self.cfg = cfg
        self.reset()

    def reset(self) -> None:
        self.prev_enemy: dict[int, tuple[int, int]] = {}
        self.counts: Counter = Counter()

    # ------------------------------------------------------------------ Lage
    def _situation(self, obs, team: int, env_cfg: dict, point_tiles, energy_map, nebula_map, nebula_drain):
        W, H = np.asarray(obs["map_features"]["tile_type"]).shape
        pos = np.asarray(obs["units"]["position"]).astype(int)
        ene = np.asarray(obs["units"]["energy"]).reshape(2, -1).astype(int)
        mask = np.asarray(obs["units_mask"]).astype(bool)
        tile = np.asarray(obs["map_features"]["tile_type"]).astype(int)
        seen = np.asarray(obs["sensor_mask"]).astype(bool)
        field = np.where(seen, np.asarray(obs["map_features"]["energy"]), energy_map).astype(float)
        nebula = np.where(seen, tile == 1, nebula_map).astype(bool)
        gain = field - nebula * float(nebula_drain or 0.0)
        opp = 1 - team
        allies = [int(u) for u in np.flatnonzero(mask[team] & (ene[team] >= 0))]
        enemies = []
        mc = int(env_cfg.get("unit_move_cost", 2))
        for e in np.flatnonzero(mask[opp] & (ene[opp] >= 0)):
            q = (int(pos[opp, e, 0]), int(pos[opp, e, 1]))
            enemies.append(dict(id=int(e), q=q, E=int(ene[opp, e]), holder=bool(point_tiles[q]),
                                dist=self._predict(q, self.prev_enemy.get(int(e)), int(ene[opp, e]), mc, tile,
                                                   bool(point_tiles[q]), W, H)))
        return dict(W=W, H=H, pos=pos[team], ene=ene[team], allies=allies, enemies=enemies, tile=tile,
                    gain=gain, nebula=nebula, point_tiles=point_tiles, mc=mc,
                    cost=int(env_cfg.get("unit_sap_cost", 40)), rng=int(env_cfg.get("unit_sap_range", 4)))

    @staticmethod
    def _passable(tile, x, y, W, H) -> bool:
        return 0 <= x < W and 0 <= y < H and tile[x, y] != 2

    def _predict(self, q, prev, E, mc, tile, holder, W, H) -> dict:
        """Wahrscheinliche Position des Gegners nach seinem Zug: Halter und stehende Gegner bleiben eher stehen,
        laufende laufen eher weiter."""
        if E < mc:
            return {q: 1.0}
        opts = [(d, (q[0] + dx, q[1] + dy)) for d, (dx, dy) in enumerate(DXY) if d == STAY
                or self._passable(tile, q[0] + dx, q[1] + dy, W, H)]
        if holder:
            p_stay, cont = 0.85, None
        elif prev is None:
            p_stay, cont = 0.5, None
        elif tuple(prev) == tuple(q):
            p_stay, cont = 0.75, None
        else:
            p_stay = 0.25
            step = (q[0] - prev[0], q[1] - prev[1])
            cont = (q[0] + step[0], q[1] + step[1]) if abs(step[0]) + abs(step[1]) == 1 else None
        dist = {q: p_stay}
        movers = [t for d, t in opts if d != STAY]
        if cont in movers:
            dist[cont] = 0.45
        rest = [t for t in movers if t not in dist]
        left = 1.0 - sum(dist.values())
        for t in rest:
            dist[t] = dist.get(t, 0.0) + left / len(rest)
        if not rest:
            dist[q] += left
        return dist

    # ------------------------------------------------------------------ Einstieg
    def apply(self, actions, obs, team: int, env_cfg: dict, *, point_tiles, energy_map, nebula_map,
              nebula_drain: float | None = None, dropoff: float = 0.5, assigned: dict | None = None) -> np.ndarray:
        """Weltaktionen (n, 3) -> geänderte Kopie. point_tiles/energy_map/nebula_map in Weltkoordinaten."""
        out = np.array(actions, dtype=int, copy=True)
        if not self.cfg.active() or int(obs["match_steps"]) == 0:
            self._remember(obs, team)
            return out
        s = self._situation(obs, team, env_cfg or {}, point_tiles, energy_map, nebula_map, nebula_drain)
        locked: set[int] = set()
        if self.cfg.sog:
            locked |= self._sog(out, s)
        if self.cfg.tanken:
            locked |= self._tanken(out, s, assigned or {}, locked)
        if self.cfg.granate:
            self._granate(out, s, float(dropoff), locked)
        self._remember(obs, team)
        return out

    def _remember(self, obs, team: int) -> None:
        opp = 1 - team
        pos = np.asarray(obs["units"]["position"]).astype(int)
        mask = np.asarray(obs["units_mask"]).astype(bool)
        self.prev_enemy = {int(e): (int(pos[opp, e, 0]), int(pos[opp, e, 1])) for e in np.flatnonzero(mask[opp])}

    # ------------------------------------------------------------------ Sog und Zusammenstoß
    def _risk(self, s, dest, e_post: float) -> float:
        """Todesrisiko einer eigenen Unit mit Energie e_post (nach eigenen Kosten) auf dest."""
        coll_survive, void = 1.0, 0.0
        adj = {(dest[0] + dx, dest[1] + dy) for dx, dy in ADJ4}
        for en in s["enemies"]:
            for t, p in en["dist"].items():
                e_after = en["E"] - (s["mc"] if t != en["q"] else 0)
                if t == dest and e_after >= e_post:
                    coll_survive *= 1.0 - p
                elif t in adj:
                    void += p * e_after
        coll = 1.0 - coll_survive
        lethal = e_post - self.cfg.sog_vf * void + float(s["gain"][dest]) < 0
        return max(coll, 1.0 if lethal else 0.0)

    def _options(self, s, u):
        """Erlaubte Bewegungen der Unit u: (Aktion, Ziel, Energie nach Kosten)."""
        x, y = map(int, s["pos"][u])
        e = int(s["ene"][u])
        out = [(STAY, (x, y), float(e))]
        if e >= s["mc"]:
            for d in (UP, RIGHT, DOWN, LEFT):
                nx, ny = x + DXY[d][0], y + DXY[d][1]
                if self._passable(s["tile"], nx, ny, s["W"], s["H"]):
                    out.append((d, (nx, ny), float(e - s["mc"])))
        return out

    def _sog(self, out, s) -> set[int]:
        changed = set()
        if not s["enemies"]:
            return changed
        for u in s["allies"]:
            a = int(out[u, 0])
            if a == SAP:
                continue
            opts = self._options(s, u)
            here = next(o for o in opts if o[0] == STAY)
            cur = next((o for o in opts if o[0] == a), here)
            r0 = self._risk(s, cur[1], cur[2])
            holder = bool(s["point_tiles"][here[1]]) and a == STAY
            if r0 < (self.cfg.sog_holder_risk if holder else self.cfg.sog_risk):
                continue
            want = cur[1]
            best = None
            for o in opts:
                r = self._risk(s, o[1], o[2])
                key = (r, abs(o[1][0] - want[0]) + abs(o[1][1] - want[1]), -float(s["gain"][o[1]]))
                if best is None or key < best[0]:
                    best = (key, o)
            if best is not None and best[1][0] != a and best[0][0] <= r0 - 0.25:
                out[u] = (best[1][0], 0, 0)
                changed.add(u)
                self.counts["sog_ausweichen"] += 1
                if holder:
                    self.counts["sog_halter_weg"] += 1
        return changed

    # ------------------------------------------------------------------ Tanken
    def _tanken(self, out, s, assigned: dict, locked: set[int]) -> set[int]:
        changed = set()
        for u in s["allies"]:
            if u in locked or int(out[u, 0]) != STAY:
                continue
            here = (int(s["pos"][u][0]), int(s["pos"][u][1]))
            if s["point_tiles"][here] or assigned.get(u) == here:
                continue
            base = float(s["gain"][here])
            best = None
            for d, dest, e_post in self._options(s, u):
                if d == STAY:
                    continue
                g = float(s["gain"][dest]) - base - s["mc"]
                if g >= self.cfg.tanken_gain and self._risk(s, dest, e_post) < 0.2 and (best is None or g > best[0]):
                    best = (g, d)
            if best is not None:
                out[u] = (best[1], 0, 0)
                changed.add(u)
                self.counts["tanken"] += 1
        return changed

    # ------------------------------------------------------------------ Granaten
    def _granate(self, out, s, drop: float, locked: set[int]) -> None:
        cost, rng = s["cost"], s["rng"]
        if not s["enemies"] or cost <= 0:
            return
        planned = [dict.fromkeys(en["dist"], 0.0) for en in s["enemies"]]
        visible = {en["q"] for en in s["enemies"]}

        def value(k, T, extra=None):
            en = s["enemies"][k]
            tot = 0.0
            for t, p in en["dist"].items():
                d = cost if t == T else (cost * drop if _cheb(t, T) == 1 else 0.0)
                if d == 0.0:
                    continue
                e_after = en["E"] - (s["mc"] if t != en["q"] else 0)
                cap = max(e_after + float(s["gain"][t]), 0.0) + 1.0
                before = planned[k][t] if extra is None else extra
                w = 1.0 + self.cfg.holder_bonus * en["holder"]
                gained = (min(before + d, cap) - min(before, cap)) * w
                if before < cap <= before + d:
                    gained += self.cfg.kill_bonus * cost
                tot += p * gained
            return tot

        targets = set()
        for en in s["enemies"]:
            for t in en["dist"]:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        T = (t[0] + dx, t[1] + dy)
                        if 0 <= T[0] < s["W"] and 0 <= T[1] < s["H"]:
                            targets.add(T)

        def best_target(u):
            p = s["pos"][u]
            best = (0.0, None)
            for T in targets:
                if _cheb(T, p) > rng:
                    continue
                v = sum(value(k, T) for k in range(len(s["enemies"])))
                if v > best[0]:
                    best = (v, T)
            return best

        def commit(T):
            for k, en in enumerate(s["enemies"]):
                for t in en["dist"]:
                    planned[k][t] += cost if t == T else (cost * drop if _cheb(t, T) == 1 else 0.0)

        # 1) R3-Schüsse auf sichtbare Ziele zuerst (sie wollten ohnehin schießen), Nebelschüsse bleiben unberührt
        shooters = [u for u in s["allies"] if int(out[u, 0]) == SAP and u not in locked]
        for u in sorted(shooters, key=lambda u: -int(s["ene"][u])):
            p = s["pos"][u]
            T0 = (int(p[0] + out[u, 1]), int(p[1] + out[u, 2]))
            if not any(_cheb(T0, q) <= 1 for q in visible):
                continue
            v0 = sum(value(k, T0) for k in range(len(s["enemies"])))
            v, T = best_target(u)
            if T is not None and T != T0 and v >= v0 + self.cfg.granate_retarget * cost:
                out[u] = (SAP, T[0] - int(p[0]), T[1] - int(p[1]))
                self.counts["granate_neu_gezielt"] += 1
                commit(T)
            else:
                commit(T0)
        # 2) Stehende Units mit genug Energie feuern zusätzlich, wenn sich der Schuss lohnt
        if not self.cfg.granate_new:
            return
        idle = [u for u in s["allies"] if int(out[u, 0]) == STAY and u not in locked
                and s["ene"][u] - cost >= self.cfg.granate_keep * cost]
        for u in sorted(idle, key=lambda u: -int(s["ene"][u])):
            v, T = best_target(u)
            if T is not None and v >= self.cfg.granate_min * cost:
                p = s["pos"][u]
                out[u] = (SAP, T[0] - int(p[0]), T[1] - int(p[1]))
                self.counts["granate_zusatz"] += 1
                commit(T)
