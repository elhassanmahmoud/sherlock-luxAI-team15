from types import SimpleNamespace

import numpy as np
import pytest

from scripts.par_eval import require_no_agent_errors
from scripts.xversion_replay import guard_course_calls


@pytest.mark.parametrize("side", ["agent", "opponent"])
@pytest.mark.parametrize("member", ["v14", "student"])
def test_full_game_detects_nested_errors_even_with_clean_outer_counters(side, member):
    hybrid = SimpleNamespace(v14=SimpleNamespace(caught_errors=0), student=SimpleNamespace(caught_errors=0),
                             caught_errors=0)
    setattr(getattr(hybrid, member), "caught_errors", 1)
    outer = SimpleNamespace(caught_errors=0, _imitation=hybrid)
    clean = SimpleNamespace()
    players = (outer, clean) if side == "agent" else (clean, outer)
    with pytest.raises(RuntimeError, match=rf"{side}\._imitation\.{member} caught a policy error"):
        require_no_agent_errors(*players)


@pytest.mark.parametrize("where", ["act", "update"])
def test_guard_rejects_a_caught_error_even_after_a_valid_all_stay_or_noop_update(where):
    inner = SimpleNamespace(caught_errors=0)
    commands = np.zeros((16, 3), dtype=int)
    calls = []

    class Entrant:
        player = "player_1"

        def act(self, step, obs):
            calls.append(("act", step, obs))
            inner.caught_errors += int(where == "act")
            return commands

        def update(self, step, **kw):
            calls.append(("update", step, kw))
            inner.caught_errors += int(where == "update")

    entrant = Entrant()
    entrant._imitation = SimpleNamespace(v14=inner)
    guard_course_calls(entrant)
    if where == "update":
        assert entrant.act(step=0, obs="public") is commands
    with pytest.raises(RuntimeError, match=rf"player_1\.{where}\._imitation\.v14"):
        getattr(entrant, where)(step=1, obs="public")
    assert calls[-1][0] == where


def test_guard_preserves_missing_update_and_clean_standalone_policy():
    agent = SimpleNamespace(player="player_0", act=lambda: "unchanged")
    assert guard_course_calls(agent).act() == "unchanged"
    assert not hasattr(agent, "update")
