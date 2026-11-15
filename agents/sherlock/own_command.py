"""Own previous issued action, canonical to the seat. Uncertain continuity is an all-zero feature."""
import numpy as np

from . import geometry as geo

KIND = "selective_movement_own_command_v1"
DELTA = np.array([(0,0), (0,-1), (1,0), (0,1), (-1,0), (0,0)], dtype=np.int16)


def encode(step, ms, pos, last_step, last_ms, last_pos, last_action):
    """Vectorized across live units. Missing entries have a negative prior action."""
    pos = np.asarray(pos, dtype=np.int16)
    move = np.asarray(last_action, dtype=int)
    shift = pos - last_pos
    valid = ((step == last_step + 1) & (ms == last_ms + 1) & (ms > 1)
             & (move >= 0) & (move <= 5) & pos.any(axis=1) & last_pos.any(axis=1)
             & ((shift == 0).all(axis=1) | (shift == DELTA[move.clip(0,5)]).all(axis=1)))
    result = np.zeros((len(pos), 6), dtype=np.int8)
    result[np.flatnonzero(valid), move[valid]] = 1
    return result


def archive_features(data):
    """One seat of one game, never crossing a game, match, missing step, UID or spawn."""
    uid = data["uid"].astype(int)
    step = data["global_step"][data["step"]].astype(int)
    ms, pos = data["mstep"], data["pos"]
    move = data["played_act"] if "played_act" in data else data["base_act"]
    if (np.any((step <= 0) | (step > 302) | (uid < 0) | (uid >= 16) | (move < 0) | (move > 5))
            or not np.array_equal(step % 101, ms) or np.unique(step * 16 + uid).size != len(step)):
        raise ValueError("Invalid archived live-unit timeline")
    index = np.full((303,16), -1, dtype=int)
    index[step,uid] = np.arange(len(step))
    previous = index[step-1,uid]
    safe = np.maximum(previous, 0)
    return encode(step, ms, pos, step[safe], ms[safe], pos[safe], np.where(previous >= 0, move[safe], -1))


class PlayedCommands:
    def __init__(self):
        self.step = self.ms = -1
        self.pos = np.zeros((16, 2), dtype=np.int16)
        self.actions = np.full(16, -1, dtype=np.int16)

    def features(self, step, ms, ids, positions):
        idx = np.asarray(ids, dtype=int)
        return encode(step, ms, positions, self.step, self.ms, self.pos[idx], self.actions[idx])

    def record(self, step, ms, ids, positions, native, mirrored):
        self.step, self.ms = step, ms
        self.actions.fill(-1)
        idx = np.asarray(ids, dtype=int)
        self.pos[idx] = np.asarray(positions).reshape(-1,2)
        actions = np.asarray(native)[idx,0].copy()
        if mirrored:
            moving = actions != geo.SAP
            actions[moving] = geo.MIRROR_DIR[actions[moving]]
        self.actions[idx] = actions
