"""Use the identical proved-point update at each of the tournament's public sight ranges."""
from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import Knowledge


class AllSight(Knowledge):
    def act(self,step,obs):
        t=int(obs["steps"])
        if t==self.last_step+1:
            self.remember(t,obs)
            self.last_step=t
        elif t!=self.last_step:
            raise ValueError("Non-sequential public point memory")
        return self.base.act(step,obs)
