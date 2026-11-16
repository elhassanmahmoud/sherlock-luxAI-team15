"""Research-only R3 policy with selective, team-coverage-preserving V15 moves."""
import numpy as np

from agents.sherlock.belief import TILE_ASTEROID
from agents.sherlock.geometry import mirror_map
from scripts.r3_v4_contact_agent import ContactAgent, sync
from feldplan import endpoint, select


class UnitHandoff(ContactAgent):
    def new_game(self, player=None):
        super().new_game(player)
        self.pending = []
        self.protected = set()

    def act(self, step, obs):
        base = np.asarray(self.r3.act(step, obs))
        other = np.asarray(self.v4.act(step, obs))
        positions = np.asarray(obs["units"]["position"])
        energies = np.asarray(obs["units"]["energy"]).reshape(positions.shape[:2])
        live = np.asarray(obs["units_mask"], dtype=bool) & (energies >= 0)
        ours = [(int(uid), tuple(positions[self.team, uid]), energies[self.team, uid])
                for uid in np.flatnonzero(live[self.team])]
        if base.shape != (positions.shape[1], 3) or other.shape != base.shape:
            raise ValueError("Unexpected recommendations")
        if self.pending:
            next_positions = {uid: pos for uid, pos, _ in ours}
            covered = set(next_positions.values())
            self.counts["observed_own_unit"] += sum(next_positions.get(u) == p for u, p in self.pending)
            self.counts["observed_any_ally"] += sum(p in covered for _, p in self.pending)
            all_retained = self.protected.issubset(covered)
            self.counts["turns_all_retained"] += int(all_retained)
            self.counts["turns_all_retained_and_gained"] += int(all_retained and all(p in covered for _, p in self.pending))
        self.pending = []
        self.protected = set()
        actual = base.copy()
        turn = int(obs["match_steps"])
        if 1 <= turn <= 99:
            belief = self.r3.belief
            known = belief.point_tiles
            if known.any():
                blocks = belief.tile_type == TILE_ASTEROID
                if belief.mirrored:
                    known, blocks = mirror_map(known), mirror_map(blocks)
                foe = 1 - self.team
                enemies = {tuple(pos) for pos in positions[foe, live[foe]]}
                points = set(map(tuple, np.argwhere(known)))
                blocked = set(map(tuple, np.argwhere(blocks)))
                cost = int(self.r3.env_cfg["unit_move_cost"])
                self.pending = select(ours, enemies, points, blocked, cost, known.shape, base, other)
                if self.pending:
                    self.protected = points & {
                        endpoint(pos, int(base[uid][0]), energy, cost, blocked, known.shape)
                        for uid, pos, energy in ours
                    }
                for uid, _ in self.pending:
                    actual[uid] = other[uid]
                self.counts["handoffs"] += len(self.pending)
                self.counts["turns_with_handoff"] += int(bool(self.pending))
                if turn <= 25:
                    self.counts["early_handoffs"] += len(self.pending)
        for actor, estimator in ((self.r3, True), (self.v4.v14, True), (self.v4.student, False)):
            sync(actor, obs, actual, estimator=estimator)
        if any(getattr(actor, "caught_errors", 0) for actor in (self.r3, self.v4, self.v4.v14, self.v4.student)):
            raise RuntimeError("A parent policy caught an error")
        return actual
