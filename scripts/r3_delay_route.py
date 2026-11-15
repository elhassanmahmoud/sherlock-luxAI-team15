"""R3 restart routing from the first decision strictly after the calibrated median."""
from scripts.r3_restart_route import RestartRouteAgent


MEDIAN = 12.5


class DelayedRouteAgent(RestartRouteAgent):
    def _finish_advice(self, obs, base, advice):
        restore = self.restore
        try:
            self.restore = restore and int(obs["match_steps"]) > MEDIAN
            return super()._finish_advice(obs, base, advice)
        finally:
            self.restore = restore
