"""Online-Schaetzung versteckter Spielparameter aus eigenen Energieverlaeufen (21.10.2026).

Analyse auf 2000 Karten (experiments/analysis/hard_map_training_20261021/): V3 gewinnt gegen
Solution_92 bei Sap-Streuschaden 0,25 / 0,5 / 1,0 nur 65,9 / 76,3 / 85,4 %, bei
Nebel-Energieabzug 25 nur 65,5 %. Beide Werte stehen nicht in env_cfg, lassen sich aber aus
den Energieaenderungen der eigenen Units ableiten (Engine-Reihenfolge: Bewegung, Sap, Kollision
und Void, Energiefeld/Nebel; luxai_s3/env.py):

    e_neu = e_alt - Zugkosten - eigene Sapkosten - Sap-Schaden - Void + Feld(t) - Nebel

Feld(t) ist das im vorigen Schritt beobachtete Energiefeld am Zielfeld. Ausgewertet werden nur
Units ohne Kappung (0 <= e_neu - Gewinn, e_neu < 400), mit sichtbarem Zielfeld, ohne Gegner
kardinal daneben (sonst Void unklar) und mit eindeutig ausgefuehrter Bewegung.
Alles in Weltkoordinaten der Beobachtung; reine Beobachtung, kein Engine-Zugriff.
"""
from __future__ import annotations

import math

import numpy as np

DROPOFFS = (0.25, 0.5, 1.0)
NEBULA_REDUCTIONS = (0, 1, 2, 3, 5, 25)
DIRS = ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0))
NOISE = 0.3  # Anteil unerklaerter Verluste in der robusten Likelihood (dropoff)
MIN_LOSS = 7


def _loss_likelihood(loss: int, cost: int, drop: float, tol: int = 2) -> float:
    """P(Verlust | Streufaktor) mit geometrischen Prioren fuer direkte Treffer und Streutreffer.
    tol: Messrauschen der Buchhaltung (22.10.2026: ohne Gegner ~10 % der Faelle |Fehler| <= 6)."""
    p = 0.0
    for nd in range(5):
        for na in range(9):
            if abs(nd * cost + int(cost * drop * na) - loss) <= tol:
                p += 0.5 ** nd * 0.5 ** na
    return p


class ParamEstimator:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.log_drop = np.zeros(len(DROPOFFS))
        self.log_neb = np.zeros(len(NEBULA_REDUCTIONS))
        self.n_drop = 0
        self.n_neb = 0
        self._prev = None

    # ------------------------------------------------------------- Schaetzwerte
    def dropoff(self, default: float = 0.5, min_conf: float = 0.9) -> float:
        p = self._posterior(self.log_drop)
        k = int(np.argmax(p))
        return DROPOFFS[k] if self.n_drop and p[k] >= min_conf else default

    def nebula(self, default: float | None = None, min_conf: float = 0.9):
        p = self._posterior(self.log_neb)
        k = int(np.argmax(p))
        return NEBULA_REDUCTIONS[k] if self.n_neb and p[k] >= min_conf else default

    @staticmethod
    def _posterior(logp: np.ndarray) -> np.ndarray:
        q = np.exp(logp - logp.max())
        return q / q.sum()

    # --------------------------------------------------------------- Update
    def observe(self, obs, team: int, actions, cfg: dict) -> None:
        """Mit der neuen Beobachtung aufrufen, danach `remember(obs, team, actions)`."""
        prev = self._prev
        if prev is None or int(np.asarray(obs["match_steps"])) <= 1:
            return
        pos = np.asarray(obs["units"]["position"])[team]
        ene = np.asarray(obs["units"]["energy"])[team]
        mask = np.asarray(obs["units_mask"])[team]
        opp = 1 - team
        epos = np.asarray(obs["units"]["position"])[opp]
        emask = np.asarray(obs["units_mask"])[opp]
        enemies = {(int(x), int(y)) for (x, y), m in zip(epos, emask) if m}
        move_cost = int(cfg.get("unit_move_cost", 2))
        sap_cost = int(cfg.get("unit_sap_cost", 30))
        sap_range = int(cfg.get("unit_sap_range", 4))
        W = prev["field"].shape[0]
        field_now = np.asarray(obs["map_features"]["energy"])
        for u in range(len(mask)):
            if not (mask[u] and prev["mask"][u]):
                continue
            x0, y0 = prev["pos"][u]
            x1, y1 = int(pos[u][0]), int(pos[u][1])
            a = int(prev["act"][u][0]) if u < len(prev["act"]) else 0
            moved = (x1, y1) != (x0, y0)
            if moved:
                if not (1 <= a <= 4) or (x0 + DIRS[a][0], y0 + DIRS[a][1]) != (x1, y1):
                    continue  # Respawn oder unklare Bewegung
            elif 1 <= a <= 4:
                continue  # Zug blockiert/Kartenrand: Kosten unklar
            if not prev["visible"][x1, y1]:
                continue
            e0 = int(prev["ene"][u])
            e1 = int(ene[u])
            costs = move_cost * moved + (sap_cost if a == 5 and e0 >= sap_cost else 0)
            gain = int(prev["field"][x1, y1])
            if int(field_now[x1, y1]) != gain:
                continue  # Energiefeld wandert gerade: Gewinn dieses Schritts unklar (22.10.2026)
            nebula = prev["tile"][x1, y1] == 1
            if e1 >= 400 or e1 - gain < 0 or e0 - costs < 0:
                continue
            if any((x1 + dx, y1 + dy) in enemies for dx, dy in DIRS[1:]):
                continue  # Void moeglich
            loss = e0 - costs + gain - e1
            if nebula:
                near = any(max(abs(ex - x1), abs(ey - y1)) <= sap_range + 1
                           for ex, ey in enemies | prev["enemies"])
                if not near and loss in NEBULA_REDUCTIONS:
                    self.log_neb += np.array([0.0 if r == loss else -6.0 for r in NEBULA_REDUCTIONS])
                    self.n_neb += 1
                continue  # Nebelverlust unbekannt -> nicht fuer den Streufaktor
            if loss < MIN_LOSS:
                continue  # Rauschen (kleinster moeglicher Streuschaden: int(30 * 0,25) = 7)
            if not any(max(abs(ex - x1), abs(ey - y1)) <= sap_range + 1 for ex, ey in prev["enemies"]):
                continue  # kein sichtbarer Schuetze in Reichweite -> Verlust nicht von Saps
            like = np.array([_loss_likelihood(loss, sap_cost, d) for d in DROPOFFS])
            if like.sum() == 0:
                continue  # nicht durch Saps erklaerbar (z. B. unsichtbarer Void)
            # robuste Mischung: ein Teil der Verluste stammt aus nicht modellierten Quellen
            # (unsichtbare Gegner, Void im Nebel); sonst kippt ein einzelner Ausreisser die Schaetzung
            like = (1 - NOISE) * like / like.sum() * (like > 0) + NOISE / len(DROPOFFS)
            self.log_drop += np.log(like)
            self.n_drop += 1

    def remember(self, obs, team: int, actions) -> None:
        opp = 1 - team
        epos = np.asarray(obs["units"]["position"])[opp]
        emask = np.asarray(obs["units_mask"])[opp]
        self._prev = dict(
            pos=[(int(p[0]), int(p[1])) for p in np.asarray(obs["units"]["position"])[team]],
            ene=np.asarray(obs["units"]["energy"])[team].copy(),
            mask=np.asarray(obs["units_mask"])[team].copy(),
            act=np.asarray(actions).copy(),
            field=np.asarray(obs["map_features"]["energy"]).copy(),
            tile=np.asarray(obs["map_features"]["tile_type"]).copy(),
            visible=np.asarray(obs["sensor_mask"]).astype(bool).copy(),
            enemies={(int(x), int(y)) for (x, y), m in zip(epos, emask) if m},
        )
