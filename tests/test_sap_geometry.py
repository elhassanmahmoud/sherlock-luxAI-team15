"""Aim-only geometry: hand-derived targets, no rollout or network allocation."""
from types import SimpleNamespace

import numpy as np

from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x


def _agent(enabled):
    agent = Agent_x.__new__(Agent_x)
    agent.n_actions = 6
    agent.cfg = AgentConfig()
    # Also lets the behavioral tests run RED before the config field exists.
    agent.cfg.sap_geometry = enabled
    agent.belief = SimpleNamespace(point_tiles=np.zeros((24, 24), dtype=bool))
    return agent


def _ctx(unit, enemies, radius=5):
    return dict(
        W=24, H=24, ally_pos=np.array([unit], dtype=np.int32),
        enemy_coords=np.array(enemies, dtype=np.int32).reshape(-1, 2),
        enemy_energies=np.full(len(enemies), 100, dtype=np.float32),
        sap_range=radius,
    )


def test_empty_cluster_center_is_strictly_better():
    # Four corners: occupied center hits one (score 100), empty middle four (200).
    ctx = _ctx((2, 5), [(4, 4), (4, 6), (6, 4), (6, 6)])
    assert _agent(True)._best_sap_target(ctx, 0) == (3, 0, 4)


def test_flag_off_preserves_old_target_and_hit_count():
    ctx = _ctx((2, 5), [(4, 4), (4, 6), (6, 4), (6, 6)])
    assert _agent(False)._best_sap_target(ctx, 0) == (2, -1, 1)


def test_equal_new_score_keeps_old_enemy_order():
    # Two separated enemies: middle splash 50+50 ties a direct 100.
    ctx = _ctx((2, 5), [(6, 5), (4, 5)])
    assert _agent(True)._best_sap_target(ctx, 0) == (4, 0, 1)
    ctx = _ctx((2, 5), [(4, 5), (6, 5)])
    assert _agent(True)._best_sap_target(ctx, 0) == (2, 0, 1)


def test_range_edge_only_splash_does_not_unlock_sap():
    ctx = _ctx((5, 5), [(9, 5)], radius=3)
    assert _agent(True)._best_sap_target(ctx, 0) is None
    assert _agent(False)._best_sap_target(ctx, 0) is None


def test_existing_none_for_no_enemies_stays_none():
    assert _agent(True)._best_sap_target(_ctx((5, 5), []), 0) is None


def test_cluster_at_map_edge_uses_legal_center():
    ctx = _ctx((0, 0), [(0, 0), (0, 2), (2, 0), (2, 2)], radius=2)
    assert _agent(True)._best_sap_target(ctx, 0) == (1, 1, 4)


def test_higher_scoring_center_outside_range_is_rejected():
    # Center (5,5) scores 200 but is beyond radius 2 from (2,5).
    # Existing legal target (4,4) must remain.
    ctx = _ctx((2, 5), [(4, 4), (4, 6), (6, 4), (6, 6)], radius=2)
    assert _agent(True)._best_sap_target(ctx, 0) == (2, -1, 1)


def test_unique_winner_mirrors_across_antidiagonal():
    # Mirror of the first fixture under (x,y) -> (23-y,23-x).
    ctx = _ctx((18, 21), [(19, 19), (17, 19), (19, 17), (17, 17)])
    assert _agent(True)._best_sap_target(ctx, 0) == (0, -3, 4)


def test_new_equal_winners_use_deterministic_coordinate_order():
    # Two disjoint corner clusters: centers (5,5) and (9,5) both score 200.
    ctx = _ctx((7, 5), [(8, 4), (8, 6), (10, 4), (10, 6),
                         (4, 4), (4, 6), (6, 4), (6, 6)], radius=5)
    assert _agent(True)._best_sap_target(ctx, 0) == (-2, 0, 4)


def test_point_priority_remains_part_of_existing_score():
    ctx = _ctx((2, 5), [(4, 4), (4, 6), (6, 4), (6, 6)])
    agent = _agent(True)
    agent.cfg.sap_pt_first = True
    agent.belief.point_tiles[4, 4] = True
    assert agent._best_sap_target(ctx, 0) == (2, -1, 1)


def test_negative_enemy_context_preserves_original_direct_target():
    # The -150 enemy vanishes before SAP. Removing its negative score by
    # switching to splash would reduce damage to the surviving +100 enemy.
    ctx = _ctx((2, 5), [(5, 5), (4, 5)])
    ctx["enemy_energies"] = np.array([100, -150], np.float32)
    assert _agent(False)._best_sap_target(ctx, 0) == (3, 0, 2)
    assert _agent(True)._best_sap_target(ctx, 0) == (3, 0, 2)


def test_empty_point_center_does_not_receive_priority_bonus():
    ctx = _ctx((2, 5), [(5, 5)])
    agent = _agent(True)
    agent.cfg.sap_pt_first = True
    agent.belief.point_tiles[6, 5] = True  # Empty; it is not a scoring enemy.
    assert agent._best_sap_target(ctx, 0) == (3, 0, 1)
