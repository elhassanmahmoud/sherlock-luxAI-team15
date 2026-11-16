"""Letzte eigene Bewegung je Einheit als zusätzliche Netzeingabe (16.11.2026, Schüler v6).

Befund vom 15.11.: Die mehrschrittigen Pläne des Lehrers sind in den Eingaben unsichtbar. „Wiederhole den letzten
Zug“ trifft schon 69 % seiner Bewegungen, das Netz bleibt im Zweifel stehen (58–67 % Stehen statt 46 %).
Deshalb bekommt jede Einheit fünf Zusatzmerkmale: eine 1 für ihre Bewegung vom letzten auf diesen Zug
(stehen, hoch, rechts, runter, links; kanonischer Raum). Unbekannt (Matchbeginn, fehlender Zug, neue Einheit,
Sprung) = alle 0.

Abgeleitet wird nur aus der eigenen Positionsänderung. Im Training kommt sie aus den gespeicherten Zeilen
(Bildindex, Unit-ID, Position, Matchschritt), im Spiel aus den letzten eigenen Beobachtungen. Beide Wege
nutzen dieselbe Regel; nur Einheiten mit Energie >= 0 werden gemerkt (so filtert auch das Archiv).
"""
from __future__ import annotations

import numpy as np

from . import geometry as geo

N_PREV = 5  # stehen, hoch, rechts, runter, links


def _shift_table() -> dict[tuple[int, int], int]:
    table = {(0, 0): geo.STAY}
    for a in range(1, 5):
        table[(int(geo.DIR_DX[a]), int(geo.DIR_DY[a]))] = a
    return table


CLASS_OF_SHIFT = _shift_table()


def archive_onehot(step: np.ndarray, uid: np.ndarray, pos: np.ndarray, mstep: np.ndarray) -> np.ndarray:
    """[N, 5] für die Zeilen eines gespeicherten Spiels (eine Seite).

    step = Bildindex (aufsteigend, ein Bild je gespeichertem Zug), mstep = Matchschritt der Zeile.
    Vorgänger ist dieselbe Unit-ID im direkt davor gespeicherten Bild, wenn dieses genau den Matchschritt
    davor zeigt (gleiches Match, kein ausgelassener Zug)."""
    step = np.asarray(step, dtype=np.int64)
    uid = np.asarray(uid, dtype=np.int64)
    pos = np.asarray(pos, dtype=np.int64).reshape(-1, 2)
    mstep = np.asarray(mstep, dtype=np.int64)
    n = len(step)
    out = np.zeros((n, N_PREV), dtype=np.float32)
    if n == 0:
        return out
    if np.any(step[1:] < step[:-1]) or step.min() < 0 or np.any((uid < 0) | (uid >= 64)):
        raise ValueError("Unsortierte Bilder oder ungültige Unit-IDs")
    n_frames = int(step.max()) + 1
    frame_ms = np.full(n_frames, -1, dtype=np.int64)
    frame_ms[step] = mstep
    index = np.full((n_frames, 64), -1, dtype=np.int64)
    if np.unique(step * 64 + uid).size != n:
        raise ValueError("Doppelte Unit-ID in einem Bild")
    index[step, uid] = np.arange(n)
    has_prev_frame = step >= 1
    prev_frame = np.where(has_prev_frame, step - 1, 0)
    prev_row = np.where(has_prev_frame, index[prev_frame, uid], -1)
    valid = (has_prev_frame & (mstep > 1) & (frame_ms[prev_frame] == mstep - 1) & (prev_row >= 0))
    rows = np.flatnonzero(valid)
    shift = pos[rows] - pos[prev_row[rows]]
    for r, (dx, dy) in zip(rows.tolist(), shift.tolist()):
        cls = CLASS_OF_SHIFT.get((int(dx), int(dy)))
        if cls is not None:
            out[r, cls] = 1.0
    return out


class MoveTracker:
    """Gleiche Regel im Spiel: merkt sich je Zug die Positionen der lebenden eigenen Units (kanonisch)."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.ms: int | None = None
        self.pos: dict[int, tuple[int, int]] = {}

    def features(self, ms: int, ids, pos) -> np.ndarray:
        out = np.zeros((len(ids), N_PREV), dtype=np.float32)
        if self.ms is None or ms <= 1 or self.ms != ms - 1:
            return out
        for k, uid in enumerate(ids):
            last = self.pos.get(int(uid))
            if last is None:
                continue
            cls = CLASS_OF_SHIFT.get((int(pos[k][0]) - last[0], int(pos[k][1]) - last[1]))
            if cls is not None:
                out[k, cls] = 1.0
        return out

    def record(self, ms: int, ids, pos, live) -> None:
        self.ms = int(ms)
        self.pos = {int(uid): (int(pos[k][0]), int(pos[k][1])) for k, uid in enumerate(ids) if bool(live[k])}
