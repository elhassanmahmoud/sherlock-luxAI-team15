"""Gegnermodell fuer Solution_92 (21.10.2026).

Aus dem Code von Solution_92 (agents/Solution_92_Kaggle/agent.py, `harvest`): Ein Schiff,
das auf seinem Ziel-Punkte-Tile angekommen ist, bleibt dort stehen. Hat es mindestens
Sap-Kosten Energie, sappt es in jedem Schritt die LETZTE von ihm sichtbare gegnerische
Unit (Schleife ueber die Unit-IDs, kein `break`) mit Manhattan-Abstand <= Sap-Reichweite,
und zwar auf deren aktuelle Position. Alle Schiffe in Reichweite feuern also auf
unsere Unit mit der hoechsten ID - Fokusfeuer, ohne Vorhersage der Bewegung.

Alles im kanonischen Raum unseres Agenten (Manhattan- und Chebyshev-Abstaende bleiben unter
der Spiegelung gleich). Nur sichtbare Gegner lassen sich vorhersagen.

30.10.2026: shape="cheb" fuer Gegner, die wie die Engine im ganzen Sap-Quadrat zielen
(scripts/style_opponents.Sol92Variant(square=True), sonst gleiche Zielwahl).
"""
from __future__ import annotations

import numpy as np


def predict_sol92_saps(ctx: dict, belief, visibility: str = "sensor",
                       shape: str = "man") -> list[tuple[int, int]]:
    """Vorhergesagte Saps: Liste (Index in ctx['enemy_coords'], Ziel-Unit-ID).

    Schuetze = sichtbarer Gegner auf einem bekannten Punkte-Tile mit Energie >= Sap-Kosten.
    Ziel = unsere Unit mit der hoechsten ID in Reichweite (shape "man": Manhattan-Raute wie
    Solution_92, "cheb": ganzes Quadrat), die der Gegner sieht.
    visibility="sensor": sichtbar, wenn irgendein sichtbarer Gegner sie im Sensor-Quadrat
    hat (Naeherung, Nebel und unsichtbare Gegner ignoriert); "all": alle unsere Units.
    """
    ec = ctx["enemy_coords"]
    if len(ec) == 0 or len(ctx["ally_ids"]) == 0:
        return []
    ee = ctx["enemy_energies"]
    R = int(ctx["sap_range"])
    cost = float(ctx["sap_cost"])
    ids = np.array([int(u) for u in ctx["ally_ids"].tolist()])
    pos = np.array([[int(ctx["ally_pos"][u][0]), int(ctx["ally_pos"][u][1])] for u in ids])
    if visibility == "sensor":
        S = int(ctx.get("sensor_range", 2))
        cheb = np.maximum(np.abs(pos[:, None, 0] - ec[None, :, 0]),
                          np.abs(pos[:, None, 1] - ec[None, :, 1]))
        seen = (cheb <= S).any(axis=1)
    else:
        seen = np.ones(len(ids), dtype=bool)
    out = []
    for k, (x, y) in enumerate(ec.tolist()):
        if ee[k] < cost or not belief.point_tiles[x, y]:
            continue
        if shape == "cheb":
            dist = np.maximum(np.abs(pos[:, 0] - x), np.abs(pos[:, 1] - y))
        else:
            dist = np.abs(pos[:, 0] - x) + np.abs(pos[:, 1] - y)
        cand = seen & (dist <= R)
        if cand.any():
            out.append((k, int(ids[cand].max())))
    return out
