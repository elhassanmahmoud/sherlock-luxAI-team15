"""Tests der Taktikschicht über R3 (agents/sherlock_r3t/tactics.py, 17.11.2026)."""
import numpy as np
import pytest

from agents.sherlock_r3t.tactics import DOWN, LEFT, RIGHT, SAP, STAY, UP, Tactics, TacticsCfg

W = H = 24
ENV = {"unit_move_cost": 2, "unit_sap_cost": 40, "unit_sap_range": 4, "max_units": 16}


def make_obs(ours, theirs, *, team=0, field=None, tile=None, match_steps=10, team_points=(0, 0), seen=None):
    """ours/theirs: {slot: ((x, y), energy)}; Gegner sind sichtbar."""
    pos = np.full((2, 16, 2), -1, dtype=int)
    ene = np.full((2, 16), -1, dtype=int)
    mask = np.zeros((2, 16), dtype=bool)
    for t, units in ((team, ours), (1 - team, theirs)):
        for u, (p, e) in units.items():
            pos[t, u], ene[t, u], mask[t, u] = p, e, True
    return {
        "units": {"position": pos, "energy": ene},
        "units_mask": mask,
        "map_features": {"tile_type": np.zeros((W, H), int) if tile is None else tile,
                         "energy": np.zeros((W, H), int) if field is None else field},
        "sensor_mask": np.ones((W, H), dtype=bool) if seen is None else seen,
        "match_steps": match_steps,
        "team_points": np.array(team_points),
    }


def run(cfg, obs, actions=None, *, points=None, dropoff=0.5, assigned=None, tactics=None):
    t = tactics or Tactics(TacticsCfg.parse(cfg) if isinstance(cfg, str) else cfg)
    acts = np.zeros((16, 3), int) if actions is None else np.array(actions)
    pts = np.zeros((W, H), bool) if points is None else points
    out = t.apply(acts, obs, 0, ENV, point_tiles=pts, energy_map=np.zeros((W, H)), nebula_map=np.zeros((W, H), bool),
                  nebula_drain=0.0, dropoff=dropoff, assigned=assigned or {})
    return out, t


def test_parse_flags_and_values():
    cfg = TacticsCfg.parse("granate,sog,granate_keep=0.5,sog_vf=0.375")
    assert cfg.granate and cfg.sog and not cfg.tanken
    assert cfg.granate_keep == 0.5 and cfg.sog_vf == 0.375
    with pytest.raises(ValueError):
        TacticsCfg.parse("granaten")
    assert not TacticsCfg.parse("").active()


def test_without_switches_actions_are_unchanged():
    obs = make_obs({0: ((5, 5), 200)}, {0: ((7, 5), 300)})
    acts = np.zeros((16, 3), int)
    acts[0] = (RIGHT, 0, 0)
    out, _ = run("", obs, acts)
    assert np.array_equal(out, acts)


def test_match_start_is_left_alone():
    obs = make_obs({0: ((5, 5), 200)}, {0: ((7, 5), 10)}, match_steps=0)
    out, _ = run("granate", obs)
    assert out[0, 0] == STAY


def test_granate_shoots_standing_holder_and_respects_energy_reserve():
    points = np.zeros((W, H), bool)
    points[8, 5] = True
    obs = make_obs({0: ((5, 5), 200), 1: ((5, 6), 60)}, {0: ((8, 5), 30)})
    out, t = run("granate", obs, points=points)
    assert tuple(out[0]) == (SAP, 3, 0)  # Halter auf (8, 5), erwarteter Abschuss
    assert out[1, 0] == STAY  # 60 - 40 < 1 x Schusskosten Reserve
    assert t.counts["granate_zusatz"] == 1


def test_granate_prefers_splash_on_a_cluster():
    # drei stehende Gegner nebeneinander, voller Streuschaden: Mitte trifft alle drei
    obs = make_obs({0: ((5, 5), 300)}, {0: ((8, 4), 300), 1: ((8, 5), 300), 2: ((8, 6), 300)})
    t = Tactics(TacticsCfg.parse("granate"))
    t.prev_enemy = {0: (8, 4), 1: (8, 5), 2: (8, 6)}  # standen schon im letzten Schritt
    out, _ = run(None, obs, dropoff=1.0, tactics=t)
    assert tuple(out[0]) == (SAP, 3, 0)


def test_granate_does_not_fire_without_value():
    obs = make_obs({0: ((5, 5), 300)}, {0: ((15, 15), 300)})  # außer Reichweite
    out, _ = run("granate", obs)
    assert out[0, 0] == STAY


def test_granate_retargets_r3_shot_only_with_clear_gain():
    obs = make_obs({0: ((5, 5), 300)}, {0: ((8, 4), 300), 1: ((8, 5), 300), 2: ((8, 6), 300)})
    t = Tactics(TacticsCfg.parse("granate"))
    t.prev_enemy = {0: (8, 4), 1: (8, 5), 2: (8, 6)}
    acts = np.zeros((16, 3), int)
    acts[0] = (SAP, 3, -1)  # R3 zielt auf den Rand des Haufens
    out, _ = run(None, obs, acts, dropoff=1.0, tactics=t)
    assert tuple(out[0]) == (SAP, 3, 0)
    assert t.counts["granate_neu_gezielt"] == 1


def test_sog_avoids_lethal_move_next_to_strong_enemy():
    # schwache Unit (10 Energie) will neben einen Gegner mit 300 Energie ziehen: Sog 0,25 * 300 = 75 -> tot
    obs = make_obs({0: ((5, 5), 10)}, {0: ((7, 5), 300)})
    t = Tactics(TacticsCfg.parse("sog"))
    t.prev_enemy = {0: (7, 5)}
    acts = np.zeros((16, 3), int)
    acts[0] = (RIGHT, 0, 0)
    out, _ = run(None, obs, acts, tactics=t)
    assert out[0, 0] != RIGHT
    assert t.counts["sog_ausweichen"] == 1


def test_sog_keeps_safe_moves():
    obs = make_obs({0: ((5, 5), 200)}, {0: ((7, 5), 100)})
    acts = np.zeros((16, 3), int)
    acts[0] = (RIGHT, 0, 0)
    out, _ = run("sog", obs, acts)
    assert out[0, 0] == RIGHT


def test_sog_avoids_collision_with_stronger_standing_enemy():
    obs = make_obs({0: ((5, 5), 100)}, {0: ((6, 5), 250)})
    t = Tactics(TacticsCfg.parse("sog"))
    t.prev_enemy = {0: (6, 5)}
    acts = np.zeros((16, 3), int)
    acts[0] = (RIGHT, 0, 0)
    out, _ = run(None, obs, acts, tactics=t)
    assert out[0, 0] in (UP, DOWN, LEFT)  # weg vom Gegner, nicht stehen bleiben neben ihm


def test_tanken_moves_idle_unit_to_better_field_but_not_holders():
    field = np.zeros((W, H), int)
    field[6, 5] = 8
    field[10, 11] = 8
    points = np.zeros((W, H), bool)
    points[10, 10] = True
    obs = make_obs({0: ((5, 5), 100), 1: ((10, 10), 100)}, {}, field=field)
    out, t = run("tanken", obs, points=points)
    assert out[0, 0] == RIGHT
    assert out[1, 0] == STAY  # Halter bleibt auf dem Punktefeld
    assert t.counts["tanken"] == 1


def test_tanken_respects_reached_target():
    field = np.zeros((W, H), int)
    field[6, 5] = 8
    obs = make_obs({0: ((5, 5), 100)}, {}, field=field)
    out, _ = run("tanken", obs, assigned={0: (5, 5)})
    assert out[0, 0] == STAY


def test_prediction_is_a_distribution_and_avoids_asteroids():
    t = Tactics(TacticsCfg())
    tile = np.zeros((W, H), int)
    tile[8, 4] = 2
    for prev in (None, (8, 5), (7, 5)):
        d = t._predict((8, 5), prev, 200, 2, tile, False, W, H)
        assert abs(sum(d.values()) - 1.0) < 1e-9
        assert (8, 4) not in d
    assert t._predict((8, 5), (7, 5), 200, 2, tile, False, W, H)[(9, 5)] == pytest.approx(0.45)
    assert t._predict((8, 5), None, 1, 2, tile, False, W, H) == {(8, 5): 1.0}


def test_player_one_actions_use_world_coordinates():
    # Team 1: die Schicht rechnet in Weltkoordinaten wie die Engine
    obs = make_obs({0: ((18, 18), 200)}, {0: ((15, 18), 30)}, team=1)
    points = np.zeros((W, H), bool)
    points[15, 18] = True
    t = Tactics(TacticsCfg.parse("granate"))
    out = t.apply(np.zeros((16, 3), int), obs, 1, ENV, point_tiles=points, energy_map=np.zeros((W, H)),
                  nebula_map=np.zeros((W, H), bool), nebula_drain=0.0, dropoff=0.5, assigned={})
    assert tuple(out[0]) == (SAP, -3, 0)


def test_nebel_shoots_hidden_holder_when_enemy_points_are_unexplained():
    points = np.zeros((W, H), bool)
    points[8, 5] = True
    seen = np.ones((W, H), bool)
    seen[8, 5] = False
    t = Tactics(TacticsCfg.parse("granate,nebel"))
    run(None, make_obs({0: ((5, 5), 300)}, {}, match_steps=9, team_points=(0, 10), seen=seen), points=points, tactics=t)
    out, _ = run(None, make_obs({0: ((5, 5), 300)}, {}, match_steps=10, team_points=(0, 11), seen=seen), points=points,
                 tactics=t)
    assert tuple(out[0]) == (SAP, 3, 0)


def test_nebel_needs_unexplained_points():
    points = np.zeros((W, H), bool)
    points[8, 5] = True
    seen = np.ones((W, H), bool)
    seen[8, 5] = False
    t = Tactics(TacticsCfg.parse("granate,nebel"))
    run(None, make_obs({0: ((5, 5), 300)}, {}, match_steps=9, team_points=(0, 10), seen=seen), points=points, tactics=t)
    out, _ = run(None, make_obs({0: ((5, 5), 300)}, {}, match_steps=10, team_points=(0, 10), seen=seen), points=points,
                 tactics=t)
    assert out[0, 0] == STAY


def test_erobern_takes_tile_of_weaker_holder_only():
    points = np.zeros((W, H), bool)
    points[6, 5] = True
    out, t = run("erobern", make_obs({0: ((5, 5), 200)}, {0: ((6, 5), 50)}), points=points)
    assert out[0, 0] == RIGHT and t.counts["erobern"] == 1
    out, _ = run("erobern", make_obs({0: ((5, 5), 200)}, {0: ((6, 5), 250)}), points=points)
    assert out[0, 0] == STAY


def test_erobern_counts_enemies_that_could_join_the_tile():
    points = np.zeros((W, H), bool)
    points[6, 5] = True
    out, _ = run("erobern", make_obs({0: ((5, 5), 200)}, {0: ((6, 5), 50), 1: ((7, 5), 180)}), points=points)
    assert out[0, 0] == STAY


def test_erobern_keeps_own_holders_on_their_tiles():
    points = np.zeros((W, H), bool)
    points[6, 5] = points[5, 5] = True
    out, _ = run("erobern", make_obs({0: ((5, 5), 200)}, {0: ((6, 5), 50)}), points=points)
    assert out[0, 0] == STAY


def test_sparen_stops_weak_holder_from_firing_unless_sure_kill():
    points = np.zeros((W, H), bool)
    points[5, 5] = True
    acts = np.zeros((16, 3), int)
    acts[0] = (SAP, 3, 0)
    out, t = run("sparen", make_obs({0: ((5, 5), 70)}, {0: ((8, 5), 100)}), acts, points=points)
    assert out[0, 0] == STAY and t.counts["sparen"] == 1
    out, _ = run("sparen", make_obs({0: ((5, 5), 70)}, {0: ((8, 5), 30)}), acts, points=points)
    assert tuple(out[0]) == (SAP, 3, 0)  # sicherer Abschuss
    out, _ = run("sparen", make_obs({0: ((5, 5), 200)}, {0: ((8, 5), 100)}), acts, points=points)
    assert tuple(out[0]) == (SAP, 3, 0)  # genug Energie


def test_wechsel_swaps_weak_holder_with_strong_neighbour():
    points = np.zeros((W, H), bool)
    points[5, 5] = True
    out, t = run("wechsel", make_obs({0: ((5, 5), 20), 1: ((5, 6), 150)}, {}), points=points)
    assert out[0, 0] == DOWN and out[1, 0] == UP and t.counts["wechsel"] == 1
    out, _ = run("wechsel", make_obs({0: ((5, 5), 20), 1: ((5, 6), 60)}, {}), points=points)
    assert out[0, 0] == STAY and out[1, 0] == STAY  # Nachbar zu schwach


def test_student_switch_is_a_layer_option_not_a_tactic():
    cfg = TacticsCfg.parse("schueler=ens8,schueler_radius=4")
    assert cfg.schueler == "ens8" and cfg.schueler_radius == 4
    assert cfg.layer_active() and not cfg.active()
    assert not TacticsCfg.parse("").layer_active()
