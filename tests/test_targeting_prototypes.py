"""Bounded owner swaps and the early artillery cancellation guard."""
from copy import deepcopy

import numpy as np
import pytest
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.belief import Belief, TILE_NEBULA
from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x
from tests.conftest import ENV_CFG, make_obs


def _cfg(**changes):
    cfg = AgentConfig(hidden=8, buffer_capacity=8, reach_assign=True,
                      eps_start=0, eps_end=0)
    # Also exercises behavioral RED before the new config fields exist.
    for key, value in changes.items():
        setattr(cfg, key, value)
    return cfg


class _Policy(torch.nn.Module):
    def __init__(self, action=geo.RIGHT):
        super().__init__()
        self.action, self.calls, self.inputs = action, 0, None

    def forward(self, x):
        self.calls += 1
        self.inputs = x.detach().cpu().numpy().copy()
        q = torch.zeros((len(x), 6), device=x.device)
        q[:, self.action] = 1
        return q


def _agent(action=geo.RIGHT, team=0, train=False, **changes):
    a = Agent_x(f"player_{team}", cfg=_cfg(**changes), train=train, seed=13)
    a.set_env_cfg(ENV_CFG)
    a.q = _Policy(action)
    return a


def _pair_context(positions=((0, 0), (3, 0)), goals=((4, 0), (2, 0)),
                  team=0, canonical=True, energies=None):
    b = Belief(team, canonical=canonical)
    for goal in goals:
        b.point_tiles[goal] = True
    ctx = dict(belief=b, W=24, H=24, ally_ids=np.arange(len(positions)),
               ally_pos=np.array(positions),
               ally_ene=np.array(energies if energies is not None else [100] * len(positions)),
               assigned=dict(enumerate(goals)), passable=b.passable,
               point_tiles=b.point_tiles, move_cost=3, first_on_tile={})
    return ctx, {u: np.ones(6, dtype=bool) for u in ctx["ally_ids"]}


def _improve(ctx, masks, **changes):
    from agents.sherlock.assignment import improve_point_assignment
    return improve_point_assignment(ctx, masks, _cfg(point_pair_swap=True, **changes))


def test_pair_swap_improves_five_to_three_without_mutating_inputs_or_target_set():
    ctx, masks = _pair_context()
    before, mask_before = deepcopy(ctx), deepcopy(masks)
    assigned, gain = _improve(ctx, masks)
    assert assigned == {0: (2, 0), 1: (4, 0)}
    assert gain == 2
    assert sorted(assigned.values()) == [(2, 0), (4, 0)]
    assert ctx["assigned"] == before["assigned"]
    for key in ("ally_pos", "ally_ene", "passable", "point_tiles"):
        np.testing.assert_array_equal(ctx[key], before[key])
    for uid in masks:
        np.testing.assert_array_equal(masks[uid], mask_before[uid])


def test_pair_swap_selects_one_best_pair_without_iterating():
    ctx, masks = _pair_context(((0, 0), (3, 0), (6, 0), (9, 0)),
                               ((10, 0), (7, 0), (4, 0), (1, 0)))
    assert _improve(ctx, masks) == ({0: (1, 0), 1: (7, 0), 2: (4, 0), 3: (10, 0)}, 16)


def test_pair_swap_ties_use_sorted_unit_ids_even_for_stacked_units():
    ctx, masks = _pair_context(((0, 0), (0, 0), (3, 0)), ((4, 0), (5, 0), (2, 0)))
    ctx["ally_ids"] = np.array([2, 1, 0])
    assert _improve(ctx, masks) == ({0: (2, 0), 1: (5, 0), 2: (4, 0)}, 2)


def test_pair_swap_allows_live_stacker_but_keeps_productive_holder():
    ctx, masks = _pair_context(((0, 0), (0, 0), (3, 0)), ((0, 0), (4, 0), (2, 0)))
    assert _improve(ctx, masks) == ({0: (0, 0), 1: (2, 0), 2: (4, 0)}, 2)


def test_pair_swap_gain_uses_routes_around_known_wall():
    ctx, masks = _pair_context(((0, 0), (4, 0)), ((3, 0), (1, 0)))
    ctx["passable"][2, :4] = False
    # Each original route is 11 steps around the wall; the swapped routes are 1 each.
    assert _improve(ctx, masks) == ({0: (1, 0), 1: (3, 0)}, 20)


@pytest.mark.parametrize("changes", [dict(use_belief=False), dict(reach_assign=False),
    dict(home_first=True), dict(home_penalty=1), dict(home_penalty=-1),
    dict(energy_pref=1), dict(sticky=1)])
def test_pair_swap_preserves_assignment_for_incompatible_configuration(changes):
    ctx, masks = _pair_context()
    assert _improve(ctx, masks, **changes) == (ctx["assigned"], 0)


@pytest.mark.parametrize("case", ["negative", "immobile", "holder", "dead_legacy_holder",
    "unknown_goal", "enemy_goal", "blocked_origin", "blocked_goal", "unreachable",
    "masked_swap_step", "masked_original_step", "same_goal", "no_gain", "tie"])
def test_pair_swap_rejects_ineligible_or_unusable_pairs(case):
    ctx, masks = _pair_context()
    if case in ("negative", "immobile"):
        ctx["ally_ene"][0] = -1 if case == "negative" else 2
    elif case in ("holder", "dead_legacy_holder"):
        ctx["point_tiles"][0, 0] = True
        if case == "dead_legacy_holder":
            ctx["ally_ids"] = np.array([0, 1, 2])
            ctx["ally_pos"] = np.array([[0, 0], [0, 0], [3, 0]])
            ctx["ally_ene"] = np.array([-1, 100, 100])
            ctx["assigned"] = {0: (0, 0), 1: (4, 0), 2: (2, 0)}
            ctx["first_on_tile"] = {(0, 0): 0}
            masks[2] = np.ones(6, bool)
    elif case == "unknown_goal":
        ctx["point_tiles"][4, 0] = False
    elif case == "enemy_goal":
        ctx["assigned"][0] = (23, 23)
        ctx["point_tiles"][23, 23] = True
    elif case.startswith("blocked_"):
        ctx["passable"][(0, 0) if case == "blocked_origin" else (4, 0)] = False
    elif case == "unreachable":
        ctx["passable"][1, :] = False
    elif case.startswith("masked_"):
        # Unit 1 needs RIGHT for the swapped goal, LEFT for its current goal.
        masks[1][geo.RIGHT if case == "masked_swap_step" else geo.LEFT] = False
    elif case == "same_goal":
        ctx["assigned"][1] = (4, 0)
    elif case == "no_gain":
        ctx["assigned"] = {0: (2, 0), 1: (4, 0)}
    elif case == "tie":
        ctx["ally_pos"][1] = (0, 0)
    out, gain = _improve(ctx, masks)
    assert (out, gain) == (ctx["assigned"], 0)
    assert out is not ctx["assigned"]


@pytest.mark.parametrize("team,canonical,positions,goals", [
    (0, True, ((0, 0), (3, 0)), ((4, 0), (2, 0))),
    (0, False, ((0, 0), (3, 0)), ((4, 0), (2, 0))),
    (1, True, ((0, 0), (3, 0)), ((4, 0), (2, 0))),
    (1, False, ((23, 23), (23, 20)), ((23, 19), (23, 21))),
])
def test_pair_swap_uses_belief_orientation(team, canonical, positions, goals):
    ctx, masks = _pair_context(positions, goals, team, canonical)
    assert _improve(ctx, masks) == ({0: goals[1], 1: goals[0]}, 2)


def test_pair_swap_skips_bfs_with_fewer_than_two_eligible_units(monkeypatch):
    from agents.sherlock import features
    ctx, masks = _pair_context(energies=[-1, 100])
    def forbidden(*args):
        pytest.fail("BFS must not run for fewer than two eligible units")
    monkeypatch.setattr(features, "bfs_maps", forbidden)
    assert _improve(ctx, masks) == (ctx["assigned"], 0)


def test_pair_swap_never_evaluates_more_than_120_pairs():
    positions = [(x, 0) for x in range(17)]
    goals = [(x, 1) for x in range(17)]
    goals[14], goals[16] = goals[16], goals[14]
    ctx, masks = _pair_context(positions, goals)
    # Only pair (14,16) improves; it lies beyond the first 120 sorted pairs.
    assert _improve(ctx, masks) == (ctx["assigned"], 0)


@pytest.mark.parametrize("enabled,training,rules,use_belief,want", [
    (False, False, False, True, {0: (4, 0), 1: (2, 0)}),
    (True, False, False, True, {0: (2, 0), 1: (4, 0)}),
    (True, True, False, True, {0: (4, 0), 1: (2, 0)}),
    (True, True, True, True, {0: (2, 0), 1: (4, 0)}),
    (True, False, False, False, {0: (4, 0), 1: (2, 0)}),
])
def test_decide_swaps_before_features_with_training_and_memory_gates(enabled, training, rules, use_belief, want):
    a = _agent(train=training, point_pair_swap=enabled, rules_in_training=rules, use_belief=use_belief)
    a.belief.point_tiles[4, 0] = a.belief.point_tiles[2, 0] = True
    obs = make_obs(10, 10, units=[(0, 0, 100), (3, 0, 100)])
    a.belief.observe(obs)
    rng_before = deepcopy(a.rng.bit_generator.state)
    ctx, ids, feats, masks, _ = a._decide(obs)
    assert ctx["assigned"] == want
    if use_belief:
        assert feats[0][30] == pytest.approx(want[0][0] / 24)
        assert feats[1][30] == pytest.approx((want[1][0] - 3) / 24)
    expected_gain = 2 if want[0] == (2, 0) else 0
    assert a.ep_stats.get("point_pair_bfs_gain", 0) == expected_gain
    assert a.ep_stats.get("point_pair_swaps", 0) == int(expected_gain > 0)
    assert a._decide(obs)[0] is ctx
    assert a.ep_stats.get("point_pair_bfs_gain", 0) == expected_gain
    assert a.rng.bit_generator.state == rng_before
    assert a.q.calls == 0


def test_pair_swap_respects_actual_safe_move_mask():
    a = _agent(point_pair_swap=True, safe_moves=True)
    a.belief.point_tiles[4, 0] = a.belief.point_tiles[2, 0] = True
    obs = make_obs(10, 10, units=[(0, 0, 100), (3, 0, 100)], enemies=[(4, 0, 200)])
    a.belief.observe(obs)
    ctx, _, _, masks, _ = a._decide(obs)
    assert not masks[1][geo.RIGHT]
    assert ctx["assigned"] == {0: (4, 0), 1: (2, 0)}


@pytest.mark.parametrize("enabled", [False, True])
def test_decide_preserves_default_order_and_reuses_enabled_masks(monkeypatch, enabled):
    import agents.sherlock.main as main
    a = _agent(point_pair_swap=enabled)
    a.belief.point_tiles[4, 0] = a.belief.point_tiles[2, 0] = True
    obs = make_obs(10, 10, units=[(0, 0, 100), (3, 0, 100)])
    a.belief.observe(obs)
    events, made_masks = [], {}
    real_features, real_mask, real_sap = main.build_features, a._action_mask, a._best_sap_target
    def features(ctx, uid):
        events.append(("feature", uid))
        return real_features(ctx, uid)
    def mask(ctx, uid, sap):
        events.append(("mask", uid))
        made_masks[uid] = real_mask(ctx, uid, sap)
        return made_masks[uid]
    def sap(ctx, uid):
        events.append(("sap", uid))
        return real_sap(ctx, uid)
    monkeypatch.setattr(main, "build_features", features)
    monkeypatch.setattr(a, "_action_mask", mask)
    monkeypatch.setattr(a, "_best_sap_target", sap)
    _, _, _, masks, _ = a._decide(obs)
    middle = [("mask", 0), ("mask", 1), ("feature", 0), ("feature", 1)] if enabled else [
        ("feature", 0), ("feature", 1), ("mask", 0), ("mask", 1)]
    assert events == [("sap", 0), ("sap", 1)] + middle
    assert all(masks[u] is made_masks[u] for u in (0, 1))
    a._decide(obs)
    assert len(events) == 6


def test_point_swap_features_reach_q_in_one_forward_and_one_observation(monkeypatch):
    a = _agent(point_pair_swap=True)
    a.belief.point_tiles[4, 0] = a.belief.point_tiles[2, 0] = True
    obs = make_obs(10, 10, units=[(0, 0, 100), (3, 0, 100)])
    observed = []
    real_observe = a.belief.observe
    def observe(value):
        observed.append(value)
        return real_observe(value)
    monkeypatch.setattr(a.belief, "observe", observe)
    a.act(10, obs)
    assert len(observed) == 1
    assert a.q.calls == 1
    np.testing.assert_allclose(a.q.inputs[:, 30], [2 / 24, 1 / 24])


def _art_case(flag=True, action=geo.RIGHT, energy=35, training=False, rules=False, overkill=True):
    a = _agent(action=action, train=training, art_move_guard=flag, art_sap=True,
               art_min_hits=1, art_safe=False, sap_no_overkill=overkill, rules_in_training=rules)
    obs = make_obs(10, 10, units=[(5, 4, 100), (5, 6, 100)], enemies=[(8, 5, energy)])
    return a, obs


@pytest.mark.parametrize("flag,action,energy,training,rules,overkill,want,kept", [
    (True, geo.RIGHT, 35, False, False, True, geo.RIGHT, 1),
    (False, geo.RIGHT, 35, False, False, True, geo.STAY, 0),
    (True, geo.RIGHT, 100, False, False, True, geo.SAP, 0),
    (True, geo.SAP, 35, False, False, True, geo.STAY, 0),
    (True, geo.STAY, 35, False, False, True, geo.STAY, 0),
    (True, geo.RIGHT, 35, False, False, False, geo.SAP, 0),
    (True, geo.RIGHT, 35, True, False, True, geo.SAP, 0),
    (True, geo.RIGHT, 35, True, True, True, geo.RIGHT, 1),
])
def test_art_guard_only_keeps_pre_art_moves_for_already_rejected_shots(flag, action, energy, training, rules, overkill, want, kept):
    a, obs = _art_case(flag, action, energy, training, rules, overkill)
    actions = a.act(10, obs)
    assert actions[0, 0] == geo.SAP
    assert actions[1, 0] == want
    assert a._prev_actions[1] == want
    assert a.ep_stats.get("art_move_kept", 0) == kept
    assert a.q.calls == 1


def test_art_guard_kept_move_still_runs_through_real_nebula_safety():
    a, obs = _art_case()
    a.cfg.nebula_avoid = True
    a.cfg.nebula_avoid_mode = "soft"
    from agents.sherlock.param_est import NEBULA_REDUCTIONS
    a.param_est.log_neb = np.array([0 if v == 25 else -50 for v in NEBULA_REDUCTIONS], float)
    a.param_est.n_neb = 5
    obs["units"]["energy"][0, 1] = 45  # enough to sap; not enough for the nebula
    obs["map_features"]["tile_type"][6, 6] = TILE_NEBULA
    for tile in ((4, 6), (5, 5), (5, 7)):
        obs["map_features"]["tile_type"][tile] = 2
    actions = a.act(10, obs)
    assert actions[1, 0] == geo.STAY
    assert a.ep_stats.get("art_move_kept", 0) == 1
    assert a.ep_stats.get("nebula_detours", 0) == 1
    assert a.ep_stats.get("overkill_skips", 0) == 0


@pytest.mark.parametrize("action", [geo.UP, geo.RIGHT, geo.DOWN, geo.LEFT])
def test_art_guard_keeps_each_legal_move_direction(action):
    a, obs = _art_case(action=action)
    assert a.act(10, obs)[1, 0] == action


def test_art_guard_uses_existing_recovery_aware_overkill_decision():
    a, obs = _art_case()
    a.cfg.sap_overkill_recovery = True
    assert a.act(10, obs)[1, 0] == geo.SAP
    assert a.ep_stats.get("art_move_kept", 0) == 0


def test_checkpoint_without_new_flags_keeps_baseline_behavior():
    cfg = AgentConfig.from_dict({"art_sap": True, "reach_assign": True})
    assert getattr(cfg, "art_move_guard", None) is False
    assert getattr(cfg, "point_pair_swap", None) is False
