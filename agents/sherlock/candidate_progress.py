"""Conservative public-observation history for optional early candidate rescue."""
from __future__ import annotations

import numpy as np


class CandidateProgress:
    def __init__(self):
        self.reset("initial")

    def reset(self, reason):
        self.previous = None
        self.step = None
        self.age = 0
        self.ready = False
        self.progress = False
        self.reset_reason = reason
        self.early_uids = set()

    def status(self):
        return dict(step=self.step, age=self.age, ready=self.ready,
                    progress=self.progress, reset_reason=self.reset_reason,
                    early_uids=sorted(self.early_uids))

    def observe(self, ctx, side, dead_tiles):
        required = ("step", "match_idx", "match_step", "candidate", "point_tiles",
                    "relic_coords", "own_points", "ally_ids", "ally_pos", "ally_ene")
        if dead_tiles is None or any(k not in ctx for k in required):
            self.reset("incomplete")
            return
        identity = (side, int(ctx["match_idx"]))
        step = int(ctx["step"])
        old = self.previous
        if old is not None and old["identity"] == identity and old["step"] == step:
            return  # Repeated hook/observation cannot invent another transition.
        candidate = np.array(ctx["candidate"], dtype=bool, copy=True)
        points = np.array(ctx["point_tiles"], dtype=bool, copy=True)
        dead = np.array(dead_tiles, dtype=bool, copy=True)
        if candidate.ndim != 2 or points.shape != candidate.shape or dead.shape != candidate.shape:
            self.reset("incomplete")
            return
        relics = frozenset(tuple(map(int, p)) for p in ctx["relic_coords"])
        score = float(ctx["own_points"])
        window = bool(identity[1] == 0 and int(ctx["match_step"]) > 0
                      and len(ctx["ally_ids"]) and relics and candidate.any() and not points.any())
        complete = (old is not None and old["identity"] == identity
                    and old["step"] + 1 == step and old["candidate"].shape == candidate.shape)
        self.step, self.ready, self.progress = step, False, False
        self.early_uids.clear()
        self.reset_reason = None
        withdrawn = False
        if complete:
            occupied = any(float(ctx["ally_ene"][uid]) >= 0
                           and 0 <= int(ctx["ally_pos"][uid][0]) < candidate.shape[0]
                           and 0 <= int(ctx["ally_pos"][uid][1]) < candidate.shape[1]
                           and old["candidate"][tuple(map(int, ctx["ally_pos"][uid]))]
                           for uid in ctx["ally_ids"])
            self.progress = bool(occupied or score > old["score"] or relics - old["relics"]
                                 or (points & ~old["points"]).any() or (dead & ~old["dead"]).any())
            withdrawn = bool(old["relics"] - relics or (old["points"] & ~points).any()
                             or (old["dead"] & ~dead).any() or score < old["score"])
        if not complete:
            self.age, self.reset_reason = 0, "discontinuity"
        elif not window or not old["window"]:
            self.age, self.reset_reason = 0, "outside_window"
        elif withdrawn:
            self.age, self.reset_reason = 0, "knowledge_withdrawal"
        elif self.progress:
            self.age, self.reset_reason = 0, "progress"
        else:
            self.age += 1
        self.ready = bool(window and self.age >= 12)
        self.previous = dict(identity=identity, step=step, candidate=candidate,
                             points=points, dead=dead, relics=relics, score=score, window=window)
