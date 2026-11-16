"""Original contact route with V15's regrouping moves at the start of later matches."""
import numpy as np

from scripts.r3_v4_contact_agent import ContactAgent, routing, sync


def regrouping(public):
    return int(np.asarray(public["team_wins"]).sum()) in (1, 2) and 1 <= int(public["match_steps"]) <= 25


class Blend(ContactAgent):
    def act(self, step, obs):
        base = np.asarray(self.r3.act(step, obs))
        alternative = np.asarray(self.v4.act(step, obs))
        live, near = routing(obs, self.team)
        if base.shape != (len(live), 3) or alternative.shape != base.shape:
            raise ValueError("Invalid parent command")
        extra = live & ~near & regrouping(obs)
        actual = np.where((near | extra)[:, None], alternative, base)
        differs = np.any(base != alternative, axis=1)
        self.counts.update(contact=int(near.sum()), early_outside=int(extra.sum()),
                           early_different=int((extra & differs).sum()),
                           early_add_shot=int((extra & (base[:,0] != 5) & (alternative[:,0] == 5)).sum()))
        for policy, estimator in ((self.r3, True), (self.v4.v14, True), (self.v4.student, False)):
            sync(policy, obs, actual, estimator=estimator)
            if getattr(policy, "caught_errors", 0):
                raise RuntimeError("A parent caught an action error")
        if self.v4.caught_errors:
            raise RuntimeError("The hybrid caught an action error")
        return actual
