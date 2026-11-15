"""Thirty-six public contexts for choosing between two distinct canonical movement commands."""
import numpy as np

from agents.sherlock import geometry as geo

R3_SHA = "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"
HARD_ONLY_PROTOCOL_SHA = "ae1d8f695ccef339cc7c6b6dd73cf190fe9fa76f3823f0f0a44a459950d34990"
PROTOCOL_SHA = "3476e80f57ff23f76fb4d8aa00269e647116ca9c468c0d2d0f6278af85567a03"
CELLS = 36


def cell_indices(features, base, played):
    """Both orders are canonical 0..4. Runtime and stored rows use the same integral offsets."""
    f = np.asarray(features)
    a, b = np.asarray(base, dtype=int), np.asarray(played, dtype=int)
    if f.shape != (len(a),79) or a.shape != b.shape or np.any((a<0)|(a>4)|(b<0)|(b>4)|(a==b)):
        raise ValueError("Contexts require distinct legal movement classes and 79 features")
    # The standard 24x24 features contain relative assigned dx,dy at 30,31, existence at 33.
    offset = np.rint(f[:,30:32].astype(np.float32)*24).astype(int)
    before = np.abs(offset[:,0]-geo.DIR_DX[a]) + np.abs(offset[:,1]-geo.DIR_DY[a])
    after = np.abs(offset[:,0]-geo.DIR_DX[b]) + np.abs(offset[:,1]-geo.DIR_DY[b])
    nearer = 1 + np.where(f[:,33] > 0, np.sign(after - before), 0)
    hold = np.where(a == geo.STAY, 0, np.where(b == geo.STAY, 1, 2))
    on_point = (f[:,34] > 0).astype(int)
    in_sap_range = (f[:,73] > 0).astype(int)
    return ((hold*2 + on_point)*3 + nearer)*2 + in_sap_range


def learn_cells(gain_by_map):
    scores = np.asarray(gain_by_map)
    if scores.ndim != 2 or scores.shape[1] != CELLS or not len(scores):
        raise ValueError("One row per training map and one column per registered context required")
    return scores.sum(axis=0) - np.maximum(scores.max(axis=0), 0) > 0
