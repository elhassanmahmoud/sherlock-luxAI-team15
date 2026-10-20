"""Exact archived helper used only by the read-only Sap observer."""
from __future__ import annotations

import numpy as np


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
