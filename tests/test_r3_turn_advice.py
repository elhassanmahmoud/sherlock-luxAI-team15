from collections import Counter
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from agents.sherlock import geometry as geo
from scripts.r3_turn_advice import TurnAdviceAgent, extra
from scripts.selective_advice_agent import SelectiveAdviceAgent


def test_extra_is_half_open_and_only_a_change_between_moves():
    score = torch.tensor([.499, .50, .69999, .70, .60, .60, .60, .60, .60])
    base = torch.tensor([1,1,1,1,1,0,5,1,1])
    choice = torch.tensor([2,2,2,2,1,2,2,0,5])
    assert extra(score, choice, base).tolist() == [False,True,True,False,False,False,False,False,False]


@pytest.mark.parametrize("team", [0,1])
def test_world_execution_matches_r3_except_one_legal_turn(team):
    # Two medium turns, one into a known asteroid. Other rows cover SAP, HOLD and high confidence.
    base_canonical = [1,2,5,0,1,1,3,2,1]
    picks = [2,2,2,2,5,0,4,3,3]
    conf = [.60,.60,.60,.60,.95,.80,.68,.65,.80]
    n = len(picks)
    active = [u for u in range(n) if u != 7]
    probs = torch.tensor([[(p if a==pick else (1-p)/5) for a in range(6)]
                          for pick,p in zip(picks,conf)])
    logits = probs[active].log()
    net = SimpleNamespace(forward_all=lambda *unused:(logits,None,None))

    def world(a):
        return geo.mirror_dir(a) if team==1 and a!=geo.SAP else a

    original = np.asarray([[world(a),0,0] for a in base_canonical],dtype=np.int32)
    original[2] = [geo.SAP,-1,1]
    grid = np.zeros((5,5),dtype=np.int32)
    blocked = world(4)
    grid[2+geo.DIR_DX[blocked],2+geo.DIR_DY[blocked]] = 2
    energy = np.full((2,n,1),100)
    energy[team,7,0] = -1
    public = dict(steps=22,match_steps=22,units_mask=np.ones((2,n),dtype=bool),map_features={"tile_type":grid},
                  units=dict(position=np.full((2,n,2),2),energy=energy))
    belief = SimpleNamespace(mirrored=bool(team),point_tiles=grid*0,candidate=grid*0,relic_positions=[],
                             explored=grid*0,explored_ever=grid*0,tile_type=grid,energy_map=grid*0,
                             last_seen=grid*0,match_step=22,dead_tiles=grid*0)
    ctx = dict(belief=belief,W=5,H=5,ally_ids=list(range(n)),ally_pos=np.full((n,2),2),
               ally_ene=energy[team,:,0],sap_cost=1,enemy_coords=[],enemy_energies=[],assigned={})
    cache = (ctx,list(range(n)),np.zeros((n,79),np.float32),np.ones((n,6),bool),None)

    def actor():
        player = object.__new__(SelectiveAdviceAgent)
        player.__dict__.update(training=False, previous_enemy=False, own_command_input=False,
                               mode="movement",members=[net],belief=belief,team_id=team,
                               _decide=lambda obs:cache,_prev_ctx=ctx,_prev_actions=dict(enumerate(base_canonical)),
                               _sap_unknown=set(),_sap_hits={},selective_counts=Counter(),ep_stats=Counter(),
                               env_cfg={"unit_move_cost":1},cfg=SimpleNamespace(dodge_verify=False,dodge_distrust=0,dodge_shape=False))
        return player

    parent, child = actor(), actor()
    stock = SelectiveAdviceAgent._advise(parent,22,public,original)
    played = TurnAdviceAgent._advise(child,22,public,original)
    assert np.flatnonzero(np.any(played!=stock,axis=1)).tolist() == [0]
    assert played[0].tolist() == [world(2),0,0] and child._prev_actions[0] == 2
    assert played[2].tolist() == [geo.SAP,-1,1]
    assert played[5,0] == geo.STAY and played[8,0] == world(3)
    assert child.selective_counts["turn_extra_played"] == 1
    assert child.selective_counts["rejected_orders"] == 1
    assert child.selective_counts["changed_steps"] == 1
    assert child.selective_counts["changed_unit_orders"] == 3
    for step, training in ((0,False),(22,True)):
        child.training = training
        assert TurnAdviceAgent._advise(child,step,{"match_steps":step},original) is original
