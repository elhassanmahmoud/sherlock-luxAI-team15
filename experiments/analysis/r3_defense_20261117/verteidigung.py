"""Research-only defensive advice. The native R3 plan is the default on every turn."""
from pathlib import Path
import sys

import numpy as np

from agents.sherlock.belief import TILE_ASTEROID
from agents.sherlock.geometry import mirror_map
from scripts.r3_v4_contact_agent import ContactAgent, sync
from feldbeschuss import switches

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "unit_handoff_20261116"))
from feldplan import endpoint


class Defense(ContactAgent):
    def act(self, step, obs):
        base = np.asarray(self.r3.act(step, obs))
        advice = np.asarray(self.v4.act(step, obs))
        pos = np.asarray(obs["units"]["position"])
        energy = np.asarray(obs["units"]["energy"]).reshape(pos.shape[:2])
        live = np.asarray(obs["units_mask"], dtype=bool) & (energy >= 0)
        if base.shape != (pos.shape[1], 3) or advice.shape != base.shape:
            raise ValueError("Unexpected recommendations")
        actual = base.copy()
        self.last_base = base.copy()
        belief = self.r3.belief
        if int(obs["match_steps"]) > 0 and belief.point_tiles.any() and np.any(advice[live[self.team], 0] == 5):
            points = belief.point_tiles
            blocks = belief.tile_type == TILE_ASTEROID
            if belief.mirrored:
                points, blocks = mirror_map(points), mirror_map(blocks)
            known = set(map(tuple, np.argwhere(points)))
            blocked = set(map(tuple, np.argwhere(blocks)))
            ours = [(int(u), tuple(pos[self.team, u]), int(energy[self.team, u])) for u in np.flatnonzero(live[self.team])]
            enemies = {tuple(p) for p in pos[1 - self.team, live[1 - self.team]]}
            cfg = self.r3.env_cfg
            planned = {u: endpoint(p, int(base[u, 0]), e, cfg["unit_move_cost"], blocked, points.shape)
                       for u, p, e in ours}
            chosen = switches(ours, enemies, known, planned, base, advice, cfg["unit_sap_cost"], cfg["unit_sap_range"])
            for uid, target in chosen:
                actual[uid] = advice[uid]
                self.counts["r3_was_sap"] += int(base[uid, 0] == 5)
                self.counts["shooter_held_known"] += int(tuple(pos[self.team, uid]) in known)
                self.counts["no_visible_enemy_in_splash"] += int(not any(max(abs(x-target[0]), abs(y-target[1])) <= 1 for x,y in enemies))
            self.counts["changed_unit_actions"] += len(chosen)
            self.counts["changed_turns"] += int(bool(chosen))
        for actor, estimator in ((self.r3, True), (self.v4.v14, True), (self.v4.student, False)):
            sync(actor, obs, actual, estimator=estimator)
        if any(getattr(actor, "caught_errors", 0) for actor in (self.r3, self.v4, self.v4.v14, self.v4.student)):
            raise RuntimeError("Defensive policy error")
        return actual
