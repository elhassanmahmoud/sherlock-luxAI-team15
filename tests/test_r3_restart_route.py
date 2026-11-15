from types import SimpleNamespace

import numpy as np
import pytest

from agents.sherlock.rules import PathCache
from scripts.r3_restart_route import proposals
from scripts.r3_restart_study import compare_streams


def fixture(team=0):
    # Detour below a wall is necessary; moving DOWN increases Manhattan distance but lowers BFS distance.
    n = 5
    pos, target = (1, 1), (3, 0)
    passable = np.ones((n, n), dtype=bool)
    passable[2, 0:3] = False
    point = np.zeros_like(passable)
    point[target] = True
    ctx = dict(ally_pos=np.array([pos]), step=106, match_idx=1, match_step=5, own_points=0,
               assigned={0:target}, point_tiles=point, passable=passable)
    actor = SimpleNamespace(_prev_ctx=ctx, belief=SimpleNamespace(mirrored=bool(team)), team_id=team,
                            route_paths=PathCache(), env_cfg={"unit_move_cost":3})
    units = np.zeros((2,1,2),dtype=int)
    units[team,0] = (3,3) if team else pos
    tiles = (~passable).astype(int)*2
    obs = dict(units_mask=np.ones((2,1),bool), units={"position":units,"energy":np.full((2,1,1),100)},
               map_features={"tile_type":tiles[::-1,::-1].T if team else tiles})
    v14 = np.array([[4 if team else 3,0,0]])  # canonical DOWN
    r3 = np.array([[0,0,0]])
    return actor, obs, v14, r3


@pytest.mark.parametrize("team", [0,1])
def test_strict_bfs_progress_for_the_actual_assigned_uid_on_either_seat(team):
    args = fixture(team)
    found = proposals(*args)
    assert len(found)==1 and found[0]["distances"]==[7,6,7]
    assert found[0]["world_target"]==([3,0] if team==0 else [4,1])
    assert proposals(*args)==found


@pytest.mark.parametrize("off", ["match1","scored","unconfirmed","unassigned","cant_pay","dead","sap","v14_sap","same_progress"])
def test_guard_conditions_leave_r3_alone(off):
    a, obs, base, r3 = fixture()
    c = a._prev_ctx
    if off=="match1": c["match_idx"]=0
    elif off=="scored": c["own_points"]=1
    elif off=="unconfirmed":
        c["point_tiles"][:]=False
        c["point_tiles"][0,0]=True
    elif off=="unassigned": c["assigned"].clear()
    elif off=="cant_pay": obs["units"]["energy"][:]=2
    elif off=="dead": obs["units_mask"][:]=False
    elif off=="sap": r3[0,0]=5
    elif off=="v14_sap": base[0,0]=5
    elif off=="same_progress":
        c["passable"][:]=True
        obs["map_features"]["tile_type"][:]=0
        c["assigned"][0]=(3,3)
        c["point_tiles"][3,3]=True
        r3[0,0]=2
    assert proposals(a,obs,base,r3)==[]


def test_prefix_verifies_both_players_and_world_orders_at_first_reversion():
    a = np.zeros((303,2,16,3),dtype=np.int16)
    b = a.copy()
    b[115,0,7,0]=3
    event=dict(step=115,uid=7,r3_world=[0,0,0],v14_world=[3,0,0])
    potential, applied = [{**event,"applied":False}], [{**event,"applied":True}]
    assert compare_streams(a,b,potential,applied,0)["first_actual_step"]==115
    b[115,1,0,0]=1
    with pytest.raises(ValueError,match="Opponent"):
        compare_streams(a,b,potential,applied,0)
    b[0,0,0,0]=1
    with pytest.raises(ValueError,match="histories"):
        compare_streams(a,b,potential,applied,0)
    assert compare_streams(a,a,[],[],0)["equal_steps_before_first_change"]==303
