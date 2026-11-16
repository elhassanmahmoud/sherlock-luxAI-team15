"""R3 scouts the first match. Hand off the opening once a scoring tile is known."""
import numpy as np

from kombination import regrouping
from scripts.r3_v4_contact_agent import ContactAgent, routing, sync


class Field(ContactAgent):
    def act(self, step, obs):
        base = np.asarray(self.r3.act(step, obs))
        alternative = np.asarray(self.v4.act(step, obs))
        live, near = routing(obs, self.team)
        if base.shape != (len(live), 3) or alternative.shape != base.shape:
            raise ValueError("Invalid parent command")
        later = int(np.asarray(obs["team_wins"]).sum()) in (1, 2)
        known = bool(np.any(self.r3.belief.point_tiles))
        use_contact = near & later
        use_opening = live & ~near & regrouping(obs) & known
        use_v15 = use_contact | use_opening
        actual = np.where(use_v15[:, None], alternative, base)
        differs = np.any(base != alternative, axis=1)
        self.counts.update(first_match_contact_differences=int((near & differs).sum()) if not later else 0,
                           field_opening_differences=int((use_opening & differs).sum()),
                           later_contact_differences=int((use_contact & differs).sum()),
                           opening_deferred_unknown=int((live & ~near & differs).sum()) if regrouping(obs) and not known else 0)
        for actor, estimator in ((self.r3, True), (self.v4.v14, True), (self.v4.student, False)):
            sync(actor, obs, actual, estimator=estimator)
        if any(getattr(actor, "caught_errors", 0) for actor in (self.r3, self.v4, self.v4.v14, self.v4.student)):
            raise RuntimeError("A parent caught an action error")
        return actual
