"""Focused no-model tests for the contact reserve experiment."""
from types import SimpleNamespace

import numpy as np
import pytest

from agents.sherlock import geometry as g
from agents.sherlock.main import Agent_x
from scripts.contact_reserve import ContactReserveAgent, contact_adjustments, contact_maps


def scene(allies, enemies, planned):
    shape = (7, 7)
    ctx = dict(
        ally_ids=np.arange(len(allies)), ally_pos=np.array([a[:2] for a in allies]),
        ally_ene=np.array([a[2] for a in allies]), point_tiles=np.zeros(shape, bool),
        passable=np.ones(shape, bool), nebula=np.zeros(shape, bool), energy_map=np.zeros(shape),
        enemy_coords=np.array([e[:2] for e in enemies], int).reshape(-1, 2),
        enemy_energies=np.array([e[2] for e in enemies]), move_cost=2, sap_cost=30, assigned={},
    )
    return ctx, dict(enumerate(planned)), {i: np.ones(6, bool) for i in range(len(allies))}


def test_contact_map_adds_sources_and_limits_each_edge():
    ctx, _, _ = scene([(0, 0, 30)], [(0, 0, 110), (0, 0, 20), (2, 0, 31), (1, 1, -2)], [0])
    sources, occupied = contact_maps(ctx)
    assert sources[1, 0] == 161 and sources[0, 1] == 130
    assert sources[1, 1] == sources[6, 0] == sources[0, 6] == 0
    assert occupied[0, 0] and not occupied[1, 1]


def test_combined_neighbors_trigger_but_one_enemy_preserves_v14():
    allies, enemies = [(2, 3, 64)], [(3, 2, 160), (4, 3, 160)]
    ctx, planned, masks = scene(allies, enemies, [g.RIGHT])
    assert contact_adjustments(ctx, planned, masks, 0) == {0: g.STAY}
    ctx, planned, masks = scene(allies, enemies[:1], [g.RIGHT])
    assert contact_adjustments(ctx, planned, masks, 0) == {}


def test_planned_teammate_shares_loss_and_rounding_happens_after_sum():
    ctx, planned, masks = scene([(2, 3, 41), (3, 3, 38)], [(4, 3, 159)], [g.RIGHT, g.SAP])
    # floor(159/8/2)=9: the mover has exactly one shot left.
    assert contact_adjustments(ctx, planned, masks, 0) == {}
    ctx["ally_ene"][1] = -1  # removed by the engine before actions
    assert contact_adjustments(ctx, planned, masks, 0) == {0: g.STAY}


def test_unoccupied_point_protected_until_predicted_death():
    ctx, planned, masks = scene([(2, 3, 40)], [(4, 3, 250)], [g.RIGHT])
    ctx["point_tiles"][3, 3] = True
    assert contact_adjustments(ctx, planned, masks, 0) == {}
    ctx["ally_ene"][0] = 20
    assert contact_adjustments(ctx, planned, masks, 0) == {0: g.STAY}
    ctx["energy_map"][3, 3] = 14  # field rescues the original point holder
    assert contact_adjustments(ctx, planned, masks, 0) == {}


def test_no_contact_no_deadly_field_or_override():
    ctx, planned, masks = scene([(1, 1, 7)], [], [g.RIGHT])
    ctx["energy_map"][2, 1] = -20
    assert contact_adjustments(ctx, planned, masks, 0) == {}


def test_preserves_shots_and_deliberate_rams():
    ctx, planned, masks = scene([(2, 3, 31), (3, 4, 31)], [(3, 3, 5), (3, 2, 300)], [g.SAP, g.UP])
    assert contact_adjustments(ctx, planned, masks, 0) == {}


def test_no_legal_safe_escape_does_not_create_one():
    ctx, planned, masks = scene([(2, 3, 29)], [(3, 3, 250)], [g.STAY])
    masks[0][:] = False
    masks[0][[g.STAY, g.UP, g.RIGHT]] = True
    ctx["passable"][2, 2] = False
    assert contact_adjustments(ctx, planned, masks, 0) == {}


@pytest.mark.parametrize("mirrored", [False, True])
def test_normal_act_path_returns_world_action_and_preserves_other_shot(monkeypatch, mirrored):
    ctx, planned, masks = scene([(2, 3, 29), (0, 0, 50)], [(3, 3, 250)], [g.STAY, g.SAP])
    masks[0][:] = False
    masks[0][[g.STAY, g.UP]] = True
    original = np.array([[g.STAY, 0, 0], [g.SAP, 1, -1]])
    def stock_act(agent, step, obs):
        agent._prev_ctx = ctx
        agent._prev_masks, agent._prev_actions = masks, planned.copy()
        agent._pred_pending = [(0, 2, 3, 29, False), (1, 0, 0, 50, True)]
        agent._shape_pending = [(0, 2, 3, 29, False, "man")]
        return original.copy()
    monkeypatch.setattr(Agent_x, "_act", stock_act)
    agent = object.__new__(ContactReserveAgent)
    agent.training, agent.ep_stats = False, {}
    agent.study_stats = {"contact_reserve_changes": 0, "contact_reserve_steps": 0}
    agent.cfg = SimpleNamespace(frozen=False, nebula_avoid=False, dodge_auto=False, sap_dropoff_est=False,
                                art_splash=False, sap_still_splash=False)
    agent.belief = SimpleNamespace(mirrored=mirrored)
    agent.param_est = SimpleNamespace(nebula=lambda default: default)
    actions = agent.act(11, {"match_steps": 11})
    assert actions.tolist() == [[g.RIGHT if mirrored else g.UP, 0, 0], [g.SAP, 1, -1]]
    assert agent._prev_actions == {0: g.UP, 1: g.SAP}
    assert agent._pred_pending == [(1, 0, 0, 50, True)] and agent._shape_pending == []
    assert agent.study_stats == {"contact_reserve_changes": 1, "contact_reserve_steps": 1}


def test_per_game_counters_reset(monkeypatch):
    monkeypatch.setattr(Agent_x, "_reset_episode_state", lambda self: None)
    agent = object.__new__(ContactReserveAgent)
    # Stock constructor and new_game both use _reset_episode_state.
    agent._reset_episode_state()
    agent.study_stats["contact_reserve_changes"] = 10
    agent._reset_episode_state()
    assert agent.study_stats == {"contact_reserve_changes": 0, "contact_reserve_steps": 0}
