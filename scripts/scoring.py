"""Vollstaendige Matchpunkte, nur fuer externe Messungen (nicht fuer Agenten).

LuxAI S3 0.2.1 setzt team_points im letzten Matchschritt zurueck, behaelt
aber die Einheiten im final_state bis zum naechsten Schritt. Daraus laesst
sich genau der letzte Zuwachs rekonstruieren (env.py: team_relic_score).
"""
import numpy as np

POINT_COUNTING_VERSION = 2


def point_tile_map(state) -> np.ndarray:
    """Aktive Punktefelder gemaess der Engine, inklusive Relic-Spawn-Maske."""
    weights = np.asarray(state.relic_nodes_map_weights)
    active_pairs = int(np.asarray(state.relic_nodes_mask).sum()) // 2
    return (weights > 0) & (weights <= active_pairs)


def match_points_after_step(previous_obs, next_obs, info) -> np.ndarray:
    """Matchstand NACH einem Schritt, am Reset noch vor dem Nullsetzen.

    Nur nach env.step aufrufen. info['final_state'] funktioniert auch durch
    RecordEpisode; keinen versteckten Zustand an act/update weiterreichen.
    Ein fehlender Zustand am Reset ist ein Fehler, keine stille Unterzaehlung.
    """
    if int(np.asarray(next_obs["match_steps"])) != 0:
        return np.asarray(next_obs["team_points"], dtype=np.int64).copy()

    state = info["final_state"]
    tiles = point_tile_map(state)
    position = np.asarray(state.units.position)
    eligible = np.asarray(state.units_mask, dtype=bool) & (
        np.asarray(state.units.energy)[..., 0] >= 0)
    points = np.asarray(previous_obs["team_points"], dtype=np.int64).copy()
    for team in (0, 1):
        occupied = np.zeros_like(tiles, dtype=bool)
        p = position[team][eligible[team]]
        occupied[p[:, 0], p[:, 1]] = True
        points[team] += np.count_nonzero(occupied & tiles)
    return points
