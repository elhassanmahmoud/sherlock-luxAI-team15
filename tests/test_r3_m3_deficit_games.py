from types import SimpleNamespace

import numpy as np
import pytest

from scripts import r3_m3_deficit_agent as policy
from scripts import r3_m3_deficit_games as games


class Parent:
    def __init__(self, order):
        self.order = np.tile(order, (16,1))
        self.observed = []
        self.caught_errors = 0

    def act(self, step, obs):
        self.observed.append(step)
        return self.order

    def new_game(self, side):
        self.observed.clear()


@pytest.mark.parametrize("side", [0, 1])
def test_latch_is_public_and_both_parents_retain_actual_orders(monkeypatch, side):
    a = policy.DeficitAgent.__new__(policy.DeficitAgent)
    a.r3 = Parent([1,0,0])
    a.shadow = Parent([5,2,1])
    a.shadow.v14 = SimpleNamespace(caught_errors=0)
    a.shadow.student = SimpleNamespace(caught_errors=0)
    a.new_game(f"player_{side}")
    calls = []
    monkeypatch.setattr(policy, "sync", lambda child, public, action, estimator:
                        calls.append((child, action[0].tolist(), estimator)))
    for step,t,wins,own,opp,switch in [
        (150,49,[1,0],1,2,False), (251,49,[1,1],1,2,False),
        (252,50,[1,1],2,2,False), (253,51,[1,1],1,2,True), (254,52,[1,1],4,2,True),
    ]:
        points = [own,opp] if side == 0 else [opp,own]
        obs = dict(match_steps=t,team_wins=wins,team_points=points,units_mask=np.ones((2,16),bool),
                   units={"energy":np.zeros((2,16,1))})
        calls.clear()
        final = a.act(step,obs)
        order = ([5,2,1] if switch else [1,0,0])
        assert final[0].tolist() == order
        assert calls == ([(a.r3,order,True)] if switch else
                         [(a.shadow.v14,order,True),(a.shadow.student,order,False)])
    assert a.decision == dict(global_step=253,match_step=51,points=1,opponent_points=2)
    assert a.r3.observed == a.shadow.observed == [150,251,252,253,254]
    assert a.v4_steps == 2 and a.different_active == 32
    a.new_game(f"player_{side}")
    assert a.decision is None and a.v4_steps == 0


@pytest.mark.parametrize("bad_side", [0, 1])
def test_entire_both_sided_prefix_includes_last_command_before_switch(bad_side):
    old = np.zeros((303,2,16,3),dtype="<i8")
    switched = old.copy()
    trigger = dict(global_step=252,match_step=50,points=4,opponent_points=7)
    switched[252, 0, 15, 1] = 2
    assert len(games.check_prefix(switched,old,trigger)) == 2
    switched[251, bad_side, 15, 2] = -1
    with pytest.raises(ValueError,match="World commands differ"):
        games.check_prefix(switched,old,trigger)
