"""Optional, read-only observation of the frozen teacher's existing action scores, before its SAP fallback."""
from __future__ import annotations

from contextlib import contextmanager

import numpy as np

from agents.sherlock import geometry as geo
from scripts.kaggle3_opponent import Kaggle3Opponent

RAW_COLUMNS = ("teacher_action_scores", "teacher_selected", "teacher_frame_status")


@contextmanager
def observe_set_action(namespace, state, event):
    original = namespace["set_action"]
    def observe(current, ship, policy):
        if current is state:
            if event["board"] is None:
                # The released bot later mutates its numpy view in-place before retrying failed SAPs.
                event["board"] = np.array(policy, copy=True)
            event["selected"].add(int(ship.unit_id))
        return original(current, ship, policy)
    namespace["set_action"] = observe
    try:
        yield
    finally:
        namespace["set_action"] = original


def align(event, state, obs, mirrored, opposite, world_classes):
    """Map teacher [class,y,x] to canonical row labels. Do not infer selected IDs from predicted classes."""
    team = int(state.team_id)
    mask = np.asarray(obs["units_mask"])[team].astype(bool)
    energy = np.asarray(obs["units"]["energy"])[team].reshape(-1)
    pos = np.asarray(obs["units"]["position"])[team]
    n = len(mask)
    scores = np.full((n,6), np.nan, np.float32)
    chosen = np.full(n, -1, np.int8)
    board = event["board"]
    if board is None:
        return 0, scores, chosen
    canon = [geo.mirror_dir(w) if mirrored and w < 5 else w for w in world_classes]
    if board.shape != (6,24,24) or board.dtype != np.float32 or sorted(canon) != list(range(6)):
        return -1, scores, chosen
    # Negative-energy masked units participate in the teacher's stack-size cutoff.
    groups = {}
    for uid in np.flatnonzero(mask):
        groups.setdefault(tuple(pos[uid].tolist()), []).append(int(uid))
    expected = set()
    for group in groups.values():
        ordered = sorted(group, key=lambda uid: (-float(energy[uid]),uid))
        expected.update(ordered[:max(1,len(ordered)//2)])
    if event["selected"] != expected:
        return -1, scores, chosen
    for uid in np.flatnonzero(mask & (energy >= 0)):
        x, y = map(int, pos[uid])
        tx, ty = opposite(x,y) if team else (x,y)
        if (not (0 <= tx < 24 and 0 <= ty < 24) or not np.isfinite(board[:,ty,tx]).all()
                or (team and (tx,ty) != geo.mirror_xy(x,y))):
            scores.fill(np.nan)
            chosen.fill(-1)
            return -1, scores, chosen
        scores[uid,canon] = board[:,ty,tx]
        chosen[uid] = int(uid in event["selected"])
    return 1, scores, chosen


class TracedTeacher(Kaggle3Opponent):
    def act(self,step,obs):
        # Each teacher has its own freshly imported agent package. Never wrap the opposing bot.
        tasks = self._module.find_moves.__globals__
        namespace = tasks["apply_nn"].__globals__
        event = dict(board=None, selected=set())
        with observe_set_action(namespace, self.agent.state, event):
            actions = super().act(step,obs)
        team = self.agent.state.team_id
        enum = self._path.ActionType
        world = [int(enum(i).transpose(reflective=True)) if team else i for i in range(6)]
        self.raw_status, self.raw_scores, self.raw_selected = align(
            event, self.agent.state, obs, bool(team), self.base.get_opposite, world)
        self.raw_step = int(step)
        return actions
