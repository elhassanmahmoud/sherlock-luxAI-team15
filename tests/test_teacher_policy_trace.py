from types import SimpleNamespace

import numpy as np
import pytest

from scripts.teacher_policy_trace import align, observe_set_action
from agents.sherlock.geometry import mirror_xy


def test_raw_policy_copy_precedes_sap_fallback_and_restores_actual_callable():
    state, ship = object(), SimpleNamespace(unit_id=5)
    board = np.arange(6*24*24,dtype=np.float32).reshape(6,24,24)
    desired = board.copy()
    calls = []
    def original(st, unit, policy):
        calls.append((st, unit, id(policy)))
        return 17
    scope = {"set_action":original}
    ev = dict(board=None,selected=set())
    with observe_set_action(scope,state,ev):
        assert scope["set_action"](state,ship,board) == 17
        board[5] = -10000
        assert scope["set_action"](state,ship,board) == 17
    assert scope["set_action"] is original and ev["selected"] == {5}
    assert calls == [(state,ship,id(board))]*2
    np.testing.assert_array_equal(ev["board"],desired)
    with pytest.raises(RuntimeError):
        with observe_set_action(scope,state,ev):
            raise RuntimeError("simulation aborted")
    assert scope["set_action"] is original


@pytest.mark.parametrize("team",[0,1])
def test_coordinate_axis_direction_ties_and_negative_teammates(team):
    energies = np.tile([80,80,20,-2],(2,1))
    positions = np.tile(np.array([4,7]),(2,4,1))
    obs = dict(units_mask=np.ones((2,4),bool),units=dict(energy=energies,position=positions))
    board = np.arange(6*24*24,dtype=np.float32).reshape(6,24,24)
    def opposite(x,y): return (23-y,23-x)
    world = [0,2,1,4,3,5] if team else list(range(6))
    state = SimpleNamespace(team_id=team)
    event = dict(board=board,selected={0,1})
    status,scores,chosen = align(event,state,obs,bool(team),opposite,world)
    assert status == 1 and chosen.tolist() == [1,1,0,-1]
    tx,ty = mirror_xy(4,7) if team else (4,7)
    assert (scores[0] == board[:,ty,tx]).all()
    assert (scores[2] == scores[0]).all() and np.isnan(scores[3]).all()
    # One negative disappears: stable equal-energy rank selects only the smaller UID of a three-unit stack.
    obs["units_mask"][team,3] = False
    event["selected"] = {0}
    assert align(event,state,obs,bool(team),opposite,world)[2].tolist() == [1,0,0,-1]
    event["selected"] = {1}
    status,scores,chosen = align(event,state,obs,bool(team),opposite,world)
    assert status == -1 and np.isnan(scores).all() and (chosen==-1).all()
    event["board"] = None
    assert align(event,state,obs,bool(team),opposite,world)[0] == 0
