"""Feature-Vektor pro Einheit (später: Karten-Kanäle für CNN)."""
import numpy as np

FEATURE_DIM = 32  # anpassen, wenn Features feststehen


def unit_features(agent, uid: int, step: int, obs) -> np.ndarray:
    # TODO (Phase 2): Position, Energie, Abstand zu Punkte-/Kandidaten-Tiles, Gegner, Stacking ...
    return np.zeros(FEATURE_DIM, dtype=np.float32)
