"""Synthetic public observations; no archive loads, real nets, or games."""
import numpy as np
import pytest
import torch

from agents.sherlock import main, rules
from agents.sherlock.belief import Belief
from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x


@pytest.fixture(autouse=True)
def no_real_models(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('No real QNet or tensor archive in this synthetic test')
    monkeypatch.setattr(main, 'QNet', forbidden)
    monkeypatch.setattr(torch, 'load', forbidden)


def agent(enabled=True, training=False):
    a = object.__new__(Agent_x)
    a.cfg = AgentConfig(cand_rescue=True, rescue_after=30, use_symmetry=False,
                        early_inference=False, nebula_avoid_mode='off')
    a.cfg.cand_stall_rescue = enabled
    a.training = training
    a.player = 'player_0'
    a.team_id = 0
    a.belief = Belief(0, symmetry=False, early_inference=False)
    a.feat_belief = a.belief
    a._reset_episode_state()
    a._rescue = False
    return a


def context(a, step=44):
    b = a.belief
    b.relic_positions = {(5, 5)}
    b.candidate[:] = False
    b.candidate[5, 5] = True
    return dict(step=step, match_step=step, match_idx=0, own_points=0,
                relic_coords=np.array([[5, 5]]), candidate=b.candidate,
                point_tiles=b.point_tiles, ally_ids=np.array([0, 1]),
                ally_pos=np.array([[1, 1], [1, 2]]), ally_ene=np.array([100, 100]),
                assigned={0: (5, 5), 1: (5, 5)})


def observe(a, ctx, step):
    ctx['step'] = ctx['match_step'] = step
    a._update_candidate_progress(ctx)


def mature(a, ctx):
    for step in range(44, 57):
        observe(a, ctx, step)


def test_default_off_and_twelve_complete_transitions_not_twelve_observations():
    assert getattr(AgentConfig(), 'cand_stall_rescue', None) is False
    a = agent(); ctx = context(a)
    for step in range(44, 56):
        observe(a, ctx, step)
        assert not a._rescue_for(ctx, 0)
    observe(a, ctx, 56)
    assert a._rescue_for(ctx, 0)
    assert a.candidate_progress_status()['age'] == 12


def test_old_global_and_zone_fallback_stay_independent_of_new_target_gate():
    a = agent(); ctx = context(a)
    ctx['assigned'] = {}
    a._rescue = True
    assert a._rescue_for(ctx, 123)
    a._rescue = False
    a._rescue_zones = {(5, 5)}
    ctx['assigned'][0] = (5, 5)
    assert a._rescue_for(ctx, 0)


def test_actual_early_queries_count_once_per_uid_and_step_and_status_is_copied():
    a = agent(); ctx = context(a); mature(a, ctx)
    for _ in range(5):
        assert a._rescue_for(ctx, 0)
    assert a._rescue_for(ctx, 1)
    assert a.ep_stats['cand_stall_early_unit_steps'] == 2
    assert a.ep_stats['cand_stall_early_steps'] == 1
    result = a.candidate_progress_status(); result['early_uids'].clear()
    assert a.candidate_progress_status()['early_uids'] == [0, 1]
    observe(a, ctx, 56)  # duplicate must preserve both age and per-UID accounting
    assert a._rescue_for(ctx, 0)
    assert a.ep_stats['cand_stall_early_unit_steps'] == 2
    observe(a, ctx, 57)
    assert a._rescue_for(ctx, 0)
    assert a.ep_stats['cand_stall_early_unit_steps'] == 3
    a._rescue = True
    assert a._rescue_for(ctx, 1)
    assert a.ep_stats['cand_stall_early_unit_steps'] == 3


def test_occupation_uses_copied_previous_mask_even_after_inplace_elimination():
    a = agent(); ctx = context(a)
    observe(a, ctx, 44)
    a.belief.candidate[5, 5] = False
    a.belief.candidate[6, 5] = True
    ctx['ally_pos'][0] = [5, 5]
    observe(a, ctx, 45)
    assert a.candidate_progress_status()['progress']
    assert a.candidate_progress_status()['age'] == 0


def test_repeated_nonnegative_occupation_blocks_timer_but_negative_energy_does_not():
    a = agent(); ctx = context(a)
    ctx['ally_pos'][0] = [5, 5]; ctx['ally_ene'][0] = 0
    for step in range(44, 62):
        observe(a, ctx, step)
        assert not a._rescue_for(ctx, 0)
    ctx['ally_ene'][0] = -1
    for step in range(62, 74): observe(a, ctx, step)
    assert a._rescue_for(ctx, 1)


@pytest.mark.parametrize('kind', ['score', 'relic', 'point', 'dead'])
def test_real_public_progress_resets_including_nonpoint_classification(kind):
    a = agent(); ctx = context(a); mature(a, ctx)
    if kind == 'score': ctx['own_points'] = 1
    elif kind == 'relic': ctx['relic_coords'] = np.array([[5, 5], [8, 8]])
    elif kind == 'point': a.belief.point_tiles[8, 8] = True
    else: a.belief.dead_tiles[8, 8] = True
    observe(a, ctx, 57)
    assert a.candidate_progress_status()['age'] == 0
    assert not a._rescue_for(ctx, 0)


@pytest.mark.parametrize('kind', ['relic_loss', 'dead_loss', 'side', 'match', 'gap', 'backward', 'empty', 'missing'])
def test_incomplete_or_changed_history_cannot_carry_mature_age(kind):
    a = agent(); ctx = context(a)
    a.belief.dead_tiles[8, 8] = True
    mature(a, ctx)
    step = 57
    if kind == 'relic_loss': ctx['relic_coords'] = np.empty((0, 2), int)
    elif kind == 'dead_loss': a.belief.dead_tiles[8, 8] = False
    elif kind == 'side': a.player = 'player_1'
    elif kind == 'match': ctx['match_idx'] = 1
    elif kind == 'gap': step = 58
    elif kind == 'backward': step = 55
    elif kind == 'empty': ctx['ally_ids'] = np.array([], int)
    else: del ctx['own_points']
    observe(a, ctx, step)
    assert not a._rescue_for(ctx, 0)
    assert a.candidate_progress_status()['age'] == 0


def test_no_retroactive_age_and_current_target_required():
    a = agent(); ctx = context(a)
    ctx['relic_coords'] = np.empty((0, 2), int)
    for step in range(1, 44): observe(a, ctx, step)
    ctx['relic_coords'] = np.array([[5, 5]])
    observe(a, ctx, 44)
    assert a.candidate_progress_status()['age'] == 0
    for step in range(45, 57): observe(a, ctx, step)
    ctx['assigned'][0] = (4, 5)
    assert not a._rescue_for(ctx, 0)
    assert a._rescue_for(ctx, 1)
    a.new_game()
    assert not a._rescue_for(ctx, 1)
    assert a.ep_stats['cand_stall_early_unit_steps'] == 0


@pytest.mark.parametrize('enabled,training,cand_rescue', [(False, False, True), (True, True, True), (True, False, False)])
def test_off_training_and_disabled_old_rescue_never_enable_early(enabled, training, cand_rescue):
    a = agent(enabled, training); ctx = context(a)
    a.cfg.cand_rescue = cand_rescue
    mature(a, ctx)
    assert not a._rescue_for(ctx, 0)
    assert a.ep_stats['cand_stall_early_unit_steps'] == 0


class FixedPolicy:
    def __init__(self): self.calls = 0
    def __call__(self, x):
        self.calls += 1
        return torch.tensor([[0., 0., 0., 0., 1., 0.]]).repeat(len(x), 1)


@pytest.mark.parametrize('enabled', [False, True])
def test_original_act_updates_once_changes_final_action_and_keeps_bookkeeping(monkeypatch, enabled):
    # Real core _act and real rescue rules; only observation input and Q source synthetic.
    a = agent(enabled); ctx = context(a)
    if not enabled:
        def forbidden(*args):
            pytest.fail('Default OFF must not observe or copy progress inputs')
        monkeypatch.setattr(a._candidate_progress, 'observe', forbidden)
    ctx.update(W=24, H=24, move_cost=3, sap_cost=40, sap_range=4,
               enemy_coords=np.empty((0, 2), int), enemy_vis_ids=[], enemy_energies=[],
               opp_points=0, passable=np.ones((24, 24), bool), nebula=np.zeros((24, 24), bool),
               energy_map=np.zeros((24, 24)), first_on_tile={}, sensor_range=2)
    a.env_cfg = {'max_units': 16}; a.device = torch.device('cpu')
    a.q = FixedPolicy(); a.extra_q = []; a.cnn_policy = None
    a.rng = np.random.default_rng(9); a._paths = rules.PathCache()
    a.belief.observe = lambda obs: None
    a.belief.match_step = 44
    monkeypatch.setattr(a, '_decide', lambda obs: (ctx, [0, 1], {u:np.zeros(79) for u in (0,1)}, {u:np.array([1,1,1,1,1,0], bool) for u in (0,1)}, {0:None,1:None}))
    for step in range(44, 57):
        ctx['step'] = ctx['match_step'] = a.belief.match_step = step
        actions = a._act(step, {'match_steps': step})
        if step < 56: assert list(actions[:2, 0]) == [4, 4]
    expected = 2 if enabled else 4
    assert list(actions[:2, 0]) == [expected, expected]
    assert a._prev_actions == {0:expected, 1:expected}
    assert a.q.calls == 13
    assert a.ep_stats['cand_stall_early_unit_steps'] == (2 if enabled else 0)
    a._act(57, {'match_steps': 0})
    assert not a.candidate_progress_status()['ready']
