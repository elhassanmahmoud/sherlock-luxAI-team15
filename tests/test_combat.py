"""Kampftechniken charge/focus_sap/hunt (15.11.2026) auf kleinen kuenstlichen Lagen."""
import numpy as np

from agents.sherlock import combat
from agents.sherlock import geometry as geo
from agents.sherlock.rules import PathCache, distance_map

W = H = 12


def make_ctx(ally, enemies=(), energy=None, sap_cost=30, sap_range=3, move_cost=2):
    """ally: {uid: (x, y, energy)}, enemies: [(x, y, energy)]."""
    pos = np.zeros((16, 2), dtype=int)
    ene = np.zeros(16)
    for u, (x, y, e) in ally.items():
        pos[u] = (x, y)
        ene[u] = e
    ec = np.array([(x, y) for x, y, _ in enemies], dtype=int).reshape(-1, 2)
    ee = np.array([e for _, _, e in enemies], dtype=float)
    return dict(
        W=W, H=H, step=7, ally_pos=pos, ally_ene=ene, enemy_coords=ec, enemy_energies=ee,
        energy_map=np.zeros((W, H), dtype=np.float32) if energy is None else energy,
        nebula=np.zeros((W, H), dtype=bool), passable=np.ones((W, H), dtype=bool),
        sap_cost=sap_cost, sap_range=sap_range, move_cost=move_cost, first_on_tile={},
    )


def test_threat_maps_marks_occupancy_adjacency_and_sap_range():
    ctx = make_ctx({0: (0, 0, 50)}, enemies=[(5, 5, 100), (9, 9, 10)])
    occ, adj, armed = combat.threat_maps(ctx)
    assert occ[5, 5] and occ[9, 9] and not occ[0, 0]
    assert adj[4, 5] == adj[6, 5] == adj[5, 4] == adj[5, 6] == 100
    assert adj[4, 4] == -1  # diagonal zaehlt nicht (Energie-Sog nur kardinal)
    assert armed[2, 2] == 1 and armed[8, 8] == 1 and armed[1, 1] == 0
    assert armed[9, 9] == 0  # ausser Reichweite des starken Gegners; der schwache (10 < 30) ist unbewaffnet


def test_charge_goal_prefers_reachable_energy_and_avoids_stronger_neighbours():
    em = np.zeros((W, H), dtype=np.float32)
    em[4, 2] = 10
    em[2, 6] = 8
    ctx = make_ctx({0: (2, 2, 20)}, energy=em)
    dist = distance_map(ctx["passable"], (2, 2))
    threats = combat.threat_maps(ctx)
    assert combat.charge_goal(ctx, 0, dist, 6, 0.0, threats, set()) == (4, 2)
    ctx2 = make_ctx({0: (2, 2, 20)}, enemies=[(5, 2, 80)], energy=em)
    threats2 = combat.threat_maps(ctx2)
    goal = combat.charge_goal(ctx2, 0, dist, 6, 0.0, threats2, set())
    assert goal != (4, 2)  # neben einem staerkeren Gegner wird nicht getankt
    em_flat = np.zeros((W, H), dtype=np.float32)
    ctx3 = make_ctx({0: (2, 2, 20)}, energy=em_flat)
    assert combat.charge_goal(ctx3, 0, dist, 6, 0.0, combat.threat_maps(ctx3), set()) is None


def test_focus_plan_assigns_exactly_enough_shooters_for_a_safe_kill():
    ctx = make_ctx({0: (2, 2, 100), 1: (3, 5, 100), 2: (11, 11, 100)}, enemies=[(4, 4, 50)])
    stationary = np.array([True])
    pt = np.zeros((W, H), dtype=bool)
    plan = combat.focus_plan(ctx, [0, 1, 2], pt, stationary, holders=set())
    assert set(plan) == {0, 1}  # 50 + 1 Energie braucht zwei Schuesse zu 30, Unit 2 ist zu weit weg
    assert plan[0][:2] == (2, 2) and plan[1][:2] == (1, -1)
    one = combat.focus_plan(ctx, [0, 2], pt, stationary, holders=set())
    assert one == {}  # ein Schuetze reicht nicht fuer einen sicheren Abschuss
    moving = combat.focus_plan(ctx, [0, 1], pt, np.array([False]), holders=set())
    assert moving == {}  # bewegte Gegner ohne Punkte-Tile werden nicht eingeplant
    pt[4, 4] = True
    assert set(combat.focus_plan(ctx, [0, 1], pt, np.array([False]), holders=set())) == {0, 1}


def test_focus_plan_counts_field_recovery_and_reserve():
    em = np.zeros((W, H), dtype=np.float32)
    em[4, 4] = 15  # Ziel tankt nach den Saps 15 Energie zurueck
    ctx = make_ctx({0: (2, 2, 100), 1: (3, 5, 100)}, enemies=[(4, 4, 40)], energy=em)
    plan = combat.focus_plan(ctx, [0, 1], np.zeros((W, H), bool), np.array([True]), holders=set())
    assert set(plan) == {0, 1}  # 40 + 15 + 1 = 56 -> zwei Schuesse
    poor = make_ctx({0: (2, 2, 35), 1: (3, 5, 100)}, enemies=[(4, 4, 20)])
    plan2 = combat.focus_plan(poor, [0, 1], np.zeros((W, H), bool), np.array([True]), holders=set())
    assert set(plan2) == {1}  # Unit 0 haette nach dem Schuss weniger als die Reserve


def test_hunt_target_only_weaker_reachable_stationary_enemies():
    ctx = make_ctx({0: (0, 0, 200)}, enemies=[(3, 0, 50)])
    dist = distance_map(ctx["passable"], (0, 0))
    pt = np.zeros((W, H), dtype=bool)
    assert combat.hunt_target(ctx, 0, dist, pt, np.array([True]), 150, 6, 20, set()) == (3, 0)
    assert combat.hunt_target(ctx, 0, dist, pt, np.array([False]), 150, 6, 20, set()) is None
    strong = make_ctx({0: (0, 0, 200)}, enemies=[(3, 0, 160)])
    assert combat.hunt_target(strong, 0, dist, pt, np.array([True]), 150, 6, 20, set()) is None
    weak_self = make_ctx({0: (0, 0, 100)}, enemies=[(3, 0, 10)])
    assert combat.hunt_target(weak_self, 0, dist, pt, np.array([True]), 150, 6, 20, set()) is None
    assert combat.hunt_target(ctx, 0, dist, pt, np.array([True]), 150, 6, 20, {(3, 0)}) is None


def test_step_to_moves_along_bfs_and_stays_at_goal():
    ctx = make_ctx({0: (2, 2, 100)})
    mask = np.ones(6, dtype=bool)
    paths = PathCache()
    assert combat.step_to(ctx, paths, 0, mask, (2, 2)) == geo.STAY
    assert combat.step_to(ctx, paths, 0, mask, (5, 2)) == geo.RIGHT
    assert combat.step_to(ctx, paths, 0, mask, (2, 0)) == geo.UP
