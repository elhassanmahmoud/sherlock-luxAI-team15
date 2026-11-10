import copy

import numpy as np
import pytest
import torch

from scripts.residual_ensemble_train import ResidualReplay, residual_td_loss


class Table(torch.nn.Module):
    def __init__(self, values):
        super().__init__()
        self.values = torch.nn.Parameter(torch.tensor(values, dtype=torch.float32))

    def forward(self, s):
        return self.values[s[:, 0].long()]


def test_ddqn_additive_masked_online_selection_target_and_terminal():
    online = Table([[1, 0, 0, 0, 0, 0], [0, 8, 9, 0, 0, 0]])
    target = Table([[0] * 6, [5, 6, 90, 0, 0, 0]])
    batch = dict(s=np.array([[0], [0]], np.float32), ns=np.array([[1], [1]], np.float32),
                 a=np.array([0, 0]), r=np.array([2., 2.], np.float32),
                 done=np.array([0., 1.], np.float32),
                 mask=np.array([[1, 1, 0, 0, 0, 0]] * 2, bool),
                 base_s=np.array([[10, 0, 0, 0, 0, 0]] * 2, np.float32),
                 base_ns=np.array([[9, 0, 0, 0, 0, 0]] * 2, np.float32))
    # Online total chooses STAY (9 > 8); target total is 9+5, not 6 or 90.
    loss, pred, y = residual_td_loss(batch, online, target, .5)
    assert pred.tolist() == [11., 11.]
    assert y.tolist() == [9., 2.]
    assert loss.item() == pytest.approx((1.5 + 8.5) / 2)
    loss.backward()
    assert online.values.grad is not None and target.values.grad is None
    batch['mask'][:] = False
    batch['mask'][:, 0] = True
    assert torch.equal(residual_td_loss(batch, online, target, .5)[2], y)
    batch['mask'][:] = False
    with pytest.raises(ValueError):
        residual_td_loss(batch, online, target, .5)


def push(buffer, i, identity='model'):
    s = np.full(4, i, np.float32)
    buffer.push(s, 5, float(i), s + 1, False, np.ones(6, bool),
                np.full(6, i * 2, np.float32), np.full(6, (i + 1) * 2, np.float32),
                np.array([5, 2, -1], np.int16), identity=identity)


def test_ring_binding_single_indices_and_roundtrip(tmp_path):
    b = ResidualReplay(3, 4, 'model')
    for i in range(8):
        push(b, i)
    batch = b.sample(30, np.random.default_rng(3))
    assert np.array_equal(batch['base_s'][:, 0], 2 * batch['s'][:, 0])
    assert np.array_equal(batch['generation'], batch['s'][:, 0] + 1)
    assert set(batch['s'][:, 0]) == {5, 6, 7}
    path = tmp_path / 'replay.npz'
    b.save(path)
    other = ResidualReplay.load(path, 'model')
    # Physical ring positions are preserved, hence the same RNG samples match.
    for k, v in b.sample(10, np.random.default_rng(8)).items():
        assert np.array_equal(v, other.sample(10, np.random.default_rng(8))[k])
    with pytest.raises(ValueError):
        ResidualReplay.load(path, 'wrong model')


def test_cache_rejects_wrong_identity_nonfinite_or_mutated_features():
    b = ResidualReplay(3, 4, 'model')
    with pytest.raises(ValueError):
        push(b, 1, 'wrong')
    with pytest.raises(ValueError):
        push(b, float('nan'))
    push(b, 2)
    b.s[0, 0] += 1
    with pytest.raises(ValueError):
        b.sample(1, np.random.default_rng(0))


def test_transition_labels_actual_features_world_action_and_respawn():
    from scripts.residual_ensemble_train import finish_transition
    from types import SimpleNamespace
    cfg = SimpleNamespace(reward_fix=True, use_shaping=False, w_match=2, w_point=1)
    prev = dict(ally_ids=np.array([0, 1]), ally_pos=np.array([[2, 2], [8, 8]]),
                ally_ene=np.array([10., 10.]), own_wins=0, opp_wins=0)
    nxt = dict(prev, ally_pos=np.array([[2, 3], [0, 0]]), own_wins=1,
               match_step=10, W=24, H=24, point_tiles=np.zeros((24, 24), bool),
               first_on_tile={}, belief=SimpleNamespace(newly_explored=0, newly_proven=0))
    # Sparse mode still computes the shared bonus before early return.
    cfg.w_explore = cfg.w_discovery = cfg.w_opp_points = 0
    before = dict(ctx=prev, feats={0:np.zeros(4,np.float32),1:np.ones(4,np.float32)},
                  actions={0:5,1:0}, hits={}, unknown=set(),
                  base={0:np.ones(6,np.float32),1:np.ones(6,np.float32)},
                  world=np.array([[5,2,-1],[0,0,0]],np.int16))
    b = ResidualReplay(3,4,'model')
    next_feats={0:np.full(4,7,np.float32),1:np.full(4,9,np.float32)}
    finish_transition(cfg,b,before,nxt,next_feats,{0:np.ones(6,bool),1:np.ones(6,bool)},
                      {0:np.full(6,14,np.float32),1:np.full(6,18,np.float32)},
                      np.full(6,3,np.float32),False)
    assert b.a[:2].tolist()==[5,0]
    assert b.done[:2].tolist()==[0,1]  # ID1 respawn is not a continuing unit
    assert b.ns[0].tolist()==[7]*4 and b.ns[1].tolist()==[0]*4
    assert b.world[0].tolist()==[5,2,-1]
    assert b.base_ns[1].tolist()==[3]*6


@pytest.fixture
def learner(monkeypatch):
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.main import Agent_x
    from agents.sherlock.residual import ResidualActor, ResidualPolicy
    from scripts.residual_ensemble_train import ResidualLearner
    from tests.conftest import ENV_CFG
    def synthetic_init(self,player,base_path,*,seed,exploration):
        Agent_x.__init__(self,player,cfg=AgentConfig(hidden=16,buffer_capacity=4),train=False,seed=seed)
        self.policy=ResidualPolicy([copy.deepcopy(self.q) for _ in range(19)])
        self.exploration=exploration
        self.last_network=self.last_proposals=None
        self.residual_diagnostics=dict(unit_steps=0,raw_changes=0,explored=0,
                                      final_differs_from_proposal=0,returned_to_raw_base=0)
    monkeypatch.setattr(ResidualActor,'__init__',synthetic_init)
    a=ResidualLearner('player_1','unused',seed=61,exploration=0,capacity=8)
    a.set_env_cfg(ENV_CFG)
    return a


def test_actual_lifecycle_delay_mirror_terminal_and_no_double_observation(learner):
    from tests.conftest import make_obs
    from agents.sherlock import geometry as geo
    a=learner
    one=make_obs(1,1,team=1,units=[(22,22,100)])
    two=make_obs(2,2,team=1,units=[(22,21,97)])
    end=make_obs(3,0,team=1,units=[(22,20,94)],wins=(0,1))
    world=a.act(1,one)
    a.update(1,one,0,world,False,two)
    assert len(a.replay)==0 and a.pending is not None
    with pytest.raises(ValueError): a.new_game()
    world2=a.act(2,two)
    assert len(a.replay)==1 and a.pending is None
    assert np.array_equal(a.replay.ns[0],a._prev_feats[0])
    assert a.replay.a[0]==(geo.MIRROR_DIR[world[0,0]] if world[0,0]<5 else 5)
    assert np.array_equal(a.replay.world[0],world[0])
    belief_step=a.belief.match_step
    a.update(2,two,0,world2,True,end)
    assert len(a.replay)==2 and a.pending is None and a.replay.done[1]==1
    assert a.belief.match_step==belief_step  # terminal shadow did not advance live actor
    assert a.eligible_steps==2
    a.new_game()
    reset=make_obs(0,0,team=1)
    act=a.act(0,reset)
    a.update(0,reset,0,act,False,one)
    assert a.pending is None and len(a.replay)==2
    a.act(1,make_obs(1,1,team=1))  # no units remains a valid actual decision
    assert a.current is not None and a.current['feats']=={}


def test_shadow_isolates_belief_sticky_and_searcher(learner):
    from tests.conftest import make_obs
    a=learner
    obs=make_obs(4,4,team=1,units=[(20,20,99)])
    a.act(4,obs)
    a.cfg.sticky=1
    a.cfg.relic_search=True
    a._sticky_prev=(0,{0:(10,10)})
    a._searcher=(0,0,(10,10))
    before=copy.deepcopy((a._sticky_prev,a._searcher,a.belief.__dict__))
    ctx=a._reward_shadow(make_obs(5,5,team=1,units=[(20,19,96)]),observe=True)
    assert ctx['belief'] is not a.belief
    assert (a._sticky_prev,a._searcher)==before[:2]
    assert a.belief.match_step==before[2]['match_step']
    assert np.array_equal(a.belief.explored,before[2]['explored'])


def test_exploration_precedes_rule_override(learner):
    from tests.conftest import make_obs
    a=learner
    a.exploration=1
    calls=[]
    def rule(ctx,uid,mask,proposal):
        calls.append(proposal)
        return 0
    a._rule_override=rule
    world=a.act(1,make_obs(1,1,team=1,units=[(20,20,100)]))
    assert calls and a.residual_diagnostics['explored']==1
    assert world[0,0]==0 and a.training is False
