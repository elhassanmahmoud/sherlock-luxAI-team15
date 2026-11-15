from collections import Counter
from types import SimpleNamespace

import numpy as np
import pytest

from agents.sherlock import geometry as geo
from agents.sherlock.main import Agent_x
from scripts.combat_teacher_counterfactual import substitute
from scripts.coverage_restore import CoverageRestoreAgent, choose_restorations
from scripts.selective_advice_agent import SelectiveAdviceAgent


def situation(positions, points, *, side=0, energy=None, enemy=(), enemy_energy=()):
    n = max(len(positions), len(enemy))
    world = np.full((2,n,2), -1, dtype=int)
    energy_arr = np.zeros((2,n), int)
    mask = np.zeros((2,n), bool)
    def world_xy(coords):
        p = np.asarray(coords, dtype=int).reshape(-1,2)
        return 23-p[:,::-1] if side else p
    for team, coords, energies in ((side, positions, energy or [30]*len(positions)),
                                    (1-side, enemy, enemy_energy)):
        world[team,:len(coords)] = world_xy(coords)
        energy_arr[team,:len(coords)] = energies
        mask[team,:len(coords)] = True
    known = np.zeros((24,24), bool)
    for tile in points:
        known[tile] = True
    public = dict(match_steps=5, units=dict(position=world,energy=energy_arr), units_mask=mask,
                  map_features=dict(tile_type=np.zeros((24,24), int)))
    ctx = dict(ally_pos=np.asarray(positions),point_tiles=known,passable=np.ones_like(known),
               enemy_coords=np.asarray(enemy,dtype=int).reshape(-1,2),
               enemy_energies=np.asarray(enemy_energy),sap_range=2)
    return public,ctx


def actions(directions, side=0):
    return np.array([[geo.mirror_dir(d) if side and d<5 else d, 0, 0] for d in directions])


def choose(pub,ctx,base,mixed,side=0):
    return choose_restorations(pub,ctx,side,bool(side),dict(unit_move_cost=3),base,mixed,Counter())


@pytest.mark.parametrize('side',[0,1])
def test_canonical_order_protects_last_coverage_then_breaks_uid_ties(side):
    # A and B would be restored by moving the last two ships off C. Only A comes first.
    # UID2 provides another eligible, higher-UID way of restoring A.
    pub,ctx = situation([(4,5),(6,5),(4,6)],[(4,5),(5,5),(6,5)],side=side)
    base = actions([0,0,1],side)
    mixed = actions([2,4,0],side)
    assert choose(pub,ctx,base,mixed,side) == [0]
    assert mixed[:,0].tolist() == actions([2,4,0],side)[:,0].tolist()


@pytest.mark.parametrize('opponent_energy,restore',[(0,[]),(-1,[0])])
def test_diagonal_exact_sap_radius_and_inactive_enemy(opponent_energy,restore):
    pub,ctx = situation([(3,4)],[(4,4)],enemy=[(6,6)],enemy_energy=[opponent_energy])
    assert choose(pub,ctx,actions([2]),actions([0])) == restore
    ctx['enemy_coords'][0] = [7,6]
    assert choose(pub,ctx,actions([2]),actions([0])) == [0]


def test_live_energy_asteroid_saps_and_last_other_point():
    pub,ctx = situation([(4,4),(3,6),(7,7),(9,9),(12,12),(17,17)],
        [(5,4),(4,6),(8,7),(9,9),(12,12),(13,12),(18,17)],energy=[2,40,-1,30,30,30])
    base = actions([2,2,2,5,2,2]); mixed=actions([0,0,0,5,0,0])
    ctx['passable'][4,6]=False
    pub['map_features']['tile_type'][18,17]=2
    # Unaffordable; known asteroid; inactive; shot; would vacate (12,12); direct asteroid.
    assert choose(pub,ctx,base,mixed) == []
    ctx['point_tiles'][12,12]=False
    assert choose(pub,ctx,base,mixed) == [4]
    ctx['point_tiles'][13,12]=False
    assert choose(pub,ctx,base,mixed) == []


def test_final_commands_and_estimator_bookkeeping_for_player_one(monkeypatch):
    pub,ctx = situation([(4,4),(8,8)],[(5,4)],side=1)
    base = actions([2,5],1); base[1]=[5,-2,1]
    mixed = actions([0,5],1); mixed[1]=base[1]
    agent=object.__new__(CoverageRestoreAgent)
    agent.team_id,agent.training,agent._imitation,agent.mode=1,False,None,'movement'
    agent.belief=SimpleNamespace(mirrored=True)
    agent.env_cfg=dict(unit_move_cost=3)
    agent.cfg=SimpleNamespace(frozen=False,nebula_avoid=True,dodge_verify=False,dodge_distrust=0,dodge_shape=False)
    agent.coverage_counts,agent.selective_counts=Counter(),Counter()
    agent._prev_actions={0:2,1:5}
    agent._sap_hits,agent._sap_unknown,agent._prev_ctx={1:1},{1},ctx
    agent.ep_stats=dict(sap_attempts=1,sap_hits_est=1)
    remembered=[]
    agent.param_est=SimpleNamespace(observe=lambda *x:None,remember=lambda o,t,a:remembered.append(a.copy()))
    monkeypatch.setattr(Agent_x,'_act',lambda self,step,obs:base.copy())
    def actual_r2(self,step,obs,original):
        return substitute(self,obs,original,mixed,'movement',self.selective_counts)
    monkeypatch.setattr(SelectiveAdviceAgent,'_advise',actual_r2)
    final=agent.act(5,pub)
    assert np.array_equal(final,base) and len(remembered)==1 and np.array_equal(remembered[0],base)
    assert agent._prev_actions=={0:2,1:5} and agent._sap_hits=={1:1} and agent._sap_unknown=={1}
    assert agent.coverage_counts['restored_fields']==agent.coverage_counts['changed_unit_orders']==1
    assert agent.selective_counts['changed_unit_orders']==1


def test_runner_keeps_r2_source_binding_and_adds_both_new_files(monkeypatch):
    from scripts import coverage_restore_compare as runner
    args=SimpleNamespace(candidate='coverage_restore',model='r2.pth')
    common=dict(model='r2-weight-sha',weights='v14-weight-sha',sources={'scripts/old.py':'unchanged'})
    def r2_contract(settings):
        assert settings.candidate=='selective_movement' and settings.model==args.model
        return dict(common,sources=dict(common['sources']))
    monkeypatch.setattr(runner.compare,'contract',r2_contract)
    actual=runner.contract(args)
    assert actual['candidate']=='coverage_restore' and actual['model']==common['model']
    assert actual['sources']['scripts/old.py']=='unchanged'
    assert {k for k in actual['sources'] if k not in common['sources']}=={
        'scripts/coverage_restore.py','scripts/coverage_restore_compare.py'}
    assert args.candidate=='coverage_restore'
