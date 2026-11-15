import pytest

from scripts.r3_delay_route import DelayedRouteAgent, MEDIAN
from scripts.r3_restart_route import RestartRouteAgent
from scripts.r3_delay_study import outcome


@pytest.mark.parametrize("step,active", [(0, False), (12, False), (13, True), (99, True)])
def test_only_delays_restore_and_preserves_parent_bookkeeping(monkeypatch, step, active):
    agent = object.__new__(DelayedRouteAgent)
    agent.restore = True
    calls = []
    def parent(self, obs, base, advice):
        calls.append((self.restore, obs, base, advice))
        return "parent world orders"
    monkeypatch.setattr(RestartRouteAgent, "_finish_advice", parent)
    obs = {"match_steps": step}
    assert MEDIAN == 12.5
    assert agent._finish_advice(obs, "base", "r3") == "parent world orders"
    assert calls == [(active, obs, "base", "r3")]
    assert agent.restore is True
    agent.restore = False
    agent._finish_advice(obs, "base", "r3")
    assert agent.restore is False and not calls[-1][0]


def test_public_point_clock_on_terminal_reset():
    game = dict(result=1, wins=2, points=101, opp_points=50)
    matches = [dict(first_own_point=k) for k in (2, 100, None)]
    assert [m["first_public_positive"] for m in outcome(dict(game=game,matches=matches))["matches"]] == [3, None, None]
