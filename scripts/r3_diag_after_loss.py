"""Use the unchanged V14 order after a publicly lost first match of the two-view R3 policy."""
from scripts.r3_diagonal import DiagonalAgent


class AfterLossAgent(DiagonalAgent):
    def _reset_episode_state(self):
        super()._reset_episode_state()
        self.first_match_lost = None

    def _advise(self, step, obs, base):
        # SelectiveAdviceAgent._act has already computed the genuine V14 world orders.
        # Agent_x._act_est remembers exactly the array returned here.
        if self.first_match_lost is None:
            wins = tuple(int(x) for x in obs["team_wins"])
            if sum(wins) == 1:
                self.first_match_lost = wins[self.team_id] == 0
            elif sum(wins) != 0:
                raise ValueError("Missing the first public match decision")
        if self.first_match_lost:
            self.selective_counts["fallback_calls"] += 1
            return base
        return super()._advise(step, obs, base)
