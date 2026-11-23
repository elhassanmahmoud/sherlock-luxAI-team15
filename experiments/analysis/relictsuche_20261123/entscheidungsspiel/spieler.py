"""Hand the decider to native R3 only after V16 won match one and lost match two."""
from experiments.analysis.relictsuche_20261123.folgewahl.politik import Switch,immutable_observation,feedback,r3_player


class Decider(Switch):
    def act(self,step,obs):
        if int(self.cfg["unit_sensor_range"])!=1:
            return self.base.act(step,obs)
        team=self.base.team_id
        if step==101:
            self.first_won=int(obs["team_wins"][team])==1
            if not self.first_won:self.history.clear()
        if step<202:
            cmd=self.base.act(step,obs)
            if step<101 or self.first_won:self.history.append((immutable_observation(obs),cmd.copy()))
            return cmd
        if step==202:
            self.chosen=self.first_won and int(obs["team_wins"][team])==1
            if self.chosen:
                assert len(self.history)==202
                self.r3=r3_player(self.side)
                self.r3.new_game(self.side)
                self.r3.set_env_cfg(self.cfg)
                for t,(seen,played) in enumerate(self.history):
                    suggested=self.r3.act(t,seen)
                    feedback(self.r3,seen,suggested,played)
            self.history.clear()
        return self.r3.act(step,obs) if self.chosen else self.base.act(step,obs)
