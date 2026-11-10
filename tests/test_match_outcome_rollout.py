"""Synthetic-only match outcome contracts; no engine games or checkpoints."""
from types import SimpleNamespace
import numpy as np
import pytest
from scripts import match_outcome_rollout as m


def ctx(ms=40):
    return dict(step=ms, match_step=ms, max_match_steps=100)


def test_smallest_gap_current_step_with_uid_and_action_ties():
    q = np.array([[2., 2., 0., 0., 0., 0.], [4., 4., 0., 0., 0., 0.]])
    o = m.choose_opportunity(ctx(), [9, 3], np.ones((2, 6), bool), q, set())
    assert (o['uid'], o['proposal'], o['alternative'], o['gap']) == (3, 0, 1, 0.)


@pytest.mark.parametrize('ms,want', [(0, False), (39, False), (40, True), (70, True), (71, False)])
def test_window_and_consumed_match(ms, want):
    q = np.arange(6.)[None, :]
    assert bool(m.choose_opportunity(ctx(ms), [0], np.ones((1, 6), bool), q, set())) == want
    assert m.choose_opportunity(ctx(ms), [0], np.ones((1, 6), bool), q, {0}) is None


def test_mask_and_finite_values_and_no_runner_up():
    q = np.array([[9., 8., 7., np.nan, np.inf, -np.inf]])
    mask = np.array([[False, True, True, False, False, False]])
    o = m.choose_opportunity(ctx(), [2], mask, q, set())
    assert (o['proposal'], o['alternative']) == (1, 2)
    mask[0, 2] = False
    assert m.choose_opportunity(ctx(), [2], mask, q, set()) is None
    mask[0, 3] = True
    with pytest.raises(ValueError, match='finite'): m.choose_opportunity(ctx(), [2], mask, q, set())


def test_adapter_changes_only_selected_proposal_and_consumes_opportunity():
    a = object.__new__(m.MatchOutcomeAgent)
    a.collect = True; a.used_matches = set(); a.candidate = None
    a.intervention = None; a.intervention_hits = 0
    a.probe_q = np.array([[3., 2., 0., 0., 0., 0.], [5., 4.5, 0., 0., 0., 0.]])
    a.probe_features = np.zeros((2, 79), np.float32)
    masks = np.ones((2, 6), bool); greedy = np.array([0, 0])
    assert np.array_equal(a._policy_greedy(ctx(), [0, 1], masks, greedy), greedy)
    assert a.candidate['uid'] == 1 and a.used_matches == {0}
    a.collect = False; a.intervention = a.candidate.copy()
    result = a._policy_greedy(ctx(), [0, 1], masks, greedy)
    assert result.tolist() == [0, 1] and greedy.tolist() == [0, 0]
    assert a.intervention_hits == 1


def info(energy):
    return {'final_state': SimpleNamespace(units=SimpleNamespace(energy=np.array(energy).reshape(2,2,1)), units_mask=np.array([[1,1],[1,0]], bool))}


@pytest.mark.parametrize('points,energy,winner,reason', [
    ([8,7], [[1,1],[9,99]], 0, 'points'),
    ([0,0], [[2,-1],[3,99]], 1, 'energy'),
    ([0,0], [[2,1],[3,99]], 1, 'random'),
])
def test_terminal_label_uses_actual_wins_and_masked_energy(points, energy, winner, reason):
    before = {'team_wins': np.array([1,0])}
    after = {'match_steps': 0, 'team_wins': np.array([1,0])+np.eye(2,dtype=int)[winner]}
    result = m.terminal_outcome(before, after, points, info(energy))
    assert result['winner'] == winner and result['reason'] == reason
    assert result['energies'] == [sum(energy[0]),energy[1][0]]


def test_terminal_winner_must_agree_with_points_and_be_one_increment():
    before={'team_wins':np.array([0,0])}
    after={'match_steps':0, 'team_wins':np.array([0,1])}
    with pytest.raises(ValueError): m.terminal_outcome(before,after,[3,2],info([[1,1],[1,9]]))
    after['team_wins']=np.array([0,0])
    with pytest.raises(ValueError): m.terminal_outcome(before,after,[0,0],info([[1,1],[1,9]]))


@pytest.mark.parametrize('ms', [40, 70])
def test_rollout_stops_after_last_match_action_preserves_h12_and_actual_winner(monkeypatch, ms):
    import copy
    from contextlib import nullcontext
    class Snap:
        def __init__(self):
            self.agent=SimpleNamespace(caught_errors=0)
            self.env=SimpleNamespace(clock=ms)
            self.opponent=None
            self.obs={'player_0':{'match_steps':ms}}
        def fork(self): return copy.deepcopy(self)
        def activate(self): return nullcontext(self)
    calls=[]
    def fake_step(env,agent,opp,obs,side,step,on_env_step):
        calls.append(env.clock);on_env_step()
        if env.clock==ms and agent.intervention is not None: agent.intervention_hits+=1
        final=env.clock==100
        # Positive early points yet final loss; no inference of wins from H12.
        points=[20,1] if not final else [20,30]
        frame=dict(terminal={'winner':1,'reason':'points','points':points,'energies':[1,1]} if final else None,
                   point_state=points,done=final)
        env.clock+=1
        return {'player_0':{'match_steps':0 if final else env.clock}},frame
    monkeypatch.setattr(m,'step_frame',fake_step)
    o={'step':ms,'match_step':ms,'uid':0,'proposal':0,'alternative':1}
    result=m.rollout_to_match_end(Snap(),'player_0',o,True)
    assert calls==list(range(ms,101)) and len(result['frames'])==101-ms
    assert result['h12_points']==[20,1] and result['won']==0 and result['point_margin']==-10


def test_identical_final_team_actions_cannot_hide_different_continuation(monkeypatch):
    def branch(snapshot,side,opportunity,alternative=False,**kwargs):
        return dict(frames=[{'actions':{'player_0':[[5,2,3]],'player_1':[[0,0,0]]}}],
                    won=int(alternative),point_margin=int(alternative),h12_points=[0,0])
    monkeypatch.setattr(m,'rollout_to_match_end',branch)
    with pytest.raises(ValueError,match='Identical emitted'):
        m.paired_match_outcome(None,'player_0',{})


def test_actual_act_chain_rules_sap_offsets_and_later_unit_damage_plan():
    import torch
    from collections import defaultdict
    class Flags:
        sap_no_overkill=True
        def __getattr__(self,_):return False
    a=object.__new__(m.MatchOutcomeAgent)
    a.cfg=Flags();a.training=False;a.device='cpu';a.cnn_policy=None;a.env_cfg={'max_units':2}
    a.belief=SimpleNamespace(observe=lambda obs:None,relic_positions=[],mirrored=False)
    a.ep_stats=defaultdict(int);a.collect=False;a.used_matches=set();a.intervention_hits=0
    a.intervention={'step':40,'uid':0,'proposal':0,'alternative':1}
    c=ctx();c.update(enemy_coords=np.array([[2,3]]),W=6,H=6)
    a._decide=lambda obs:(c,[0,1],{u:np.zeros(79,np.float32) for u in (0,1)},
                           {u:np.ones(6,bool) for u in (0,1)},{0:(2,3,1),1:(2,3,1)})
    a._network_values=lambda features:torch.tensor([[4.,3.,0.,0.,0.,0.],[0.,0.,0.,0.,0.,4.]])
    a._enemy_stationary=lambda c:{};a._rescue_for=lambda c,u:False;a._harmful_nebula=lambda:0
    seen=[]
    def rule(c,u,mask,action):
        seen.append((u,action));return 5 if action==1 else action
    a._rule_override=rule
    a._overkill=lambda c,u,sap,planned:bool(planned[0]>=100)
    def damage(c,u,sap,planned):planned[0]+=100
    a._plan_damage=damage
    output=a._act(40,{'match_steps':40})
    assert seen==[(0,1),(1,5)]
    assert output.tolist()==[[5,2,3],[0,0,0]]
    assert a._prev_actions=={0:5,1:0} and a.intervention_hits==1
    # Negative control: remove only intervention, keep identical entire chain.
    a.intervention=None;seen.clear()
    assert a._act(40,{'match_steps':40}).tolist()==[[0,0,0],[5,2,3]]
