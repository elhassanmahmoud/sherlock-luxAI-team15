"""Feed extra public information to the existing knowledge candidate, preserving the original control path."""
from experiments.analysis.relictsuche_20261123.punktgrenzen.grenzen import PublicBounds,public_row
from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import Knowledge


class BoundInput(PublicBounds):
    def observe(self,row):
        assert all(row[k]==self.current[k] for k in ("step","ms","points","occupied","epoch_seen"))
        return super().observe(self.current)


class AreaKnowledge(Knowledge):
    def reset(self):
        super().reset()
        self.proof=BoundInput()

    def act(self,step,obs):
        if int(self.base.env_cfg["unit_sensor_range"])==1:
            self.proof.current=public_row(step,self.base.team_id,obs["units"]["position"],obs["units"]["energy"],
                                          obs["units_mask"],obs["team_points"],obs["relic_nodes_mask"],obs["relic_nodes"])
        return super().act(step,obs)
