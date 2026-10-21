"""Regel vom 21.10.2026: art_sap (Sap aus sicherer Position in einen Gegnerhaufen)."""
from agents.sherlock import geometry as geo
from tests.conftest import make_obs
from tests.test_rules_1910 import _stay_agent

# ENV_CFG: Sap-Kosten 40, Reichweite 4. Gegner bei (8, 8)/(9, 8): Chebyshev 3 bzw. 4,
# Manhattan 6 bzw. 7 von (5, 5) -> treffbar, Solution_92 schiesst nicht zurueck.
PAIR = [(8, 8, 80), (9, 8, 80)]


def _act(units, enemies, **cfg):
    a = _stay_agent(**cfg)
    return a, a.act(10, make_obs(10, 10, units=units, enemies=enemies, relics=[(12, 12)]))


def test_art_sap_fires_into_pair_from_safe_square():
    _, act = _act([(5, 5, 100)], PAIR)
    assert int(act[0, 0]) == geo.STAY
    _, act = _act([(5, 5, 100)], PAIR, art_sap=True)
    assert int(act[0, 0]) == geo.SAP and (int(act[0, 1]), int(act[0, 2])) == (3, 3)


def test_art_sap_needs_two_hits():
    _, act = _act([(5, 5, 100)], PAIR[:1], art_sap=True)
    assert int(act[0, 0]) == geo.STAY
    _, act = _act([(5, 5, 100)], PAIR[:1], art_sap=True, art_min_hits=1)
    assert int(act[0, 0]) == geo.SAP


def test_art_sap_not_when_armed_enemy_in_manhattan_range():
    near = PAIR + [(7, 6, 60)]  # Manhattan 3 <= 4, Energie 60 >= 40
    _, act = _act([(5, 5, 100)], near, art_sap=True)
    assert int(act[0, 0]) == geo.STAY
    _, act = _act([(5, 5, 100)], near, art_sap=True, art_safe=False)
    assert int(act[0, 0]) == geo.SAP
    weak = PAIR + [(7, 6, 30)]  # kann nicht sappen -> keine Gefahr
    _, act = _act([(5, 5, 100)], weak, art_sap=True)
    assert int(act[0, 0]) == geo.SAP


def test_art_sap_respects_reserve_and_leaves_point_tile_holder_to_pt_sap():
    _, act = _act([(5, 5, 100)], PAIR, art_sap=True, art_reserve=70)
    assert int(act[0, 0]) == geo.STAY  # 100 < 40 + 70
    a = _stay_agent(art_sap=True)
    a.belief.point_tiles[5, 5] = True
    act = a.act(10, make_obs(10, 10, units=[(5, 5, 100)], enemies=PAIR, relics=[(12, 12)]))
    assert int(act[0, 0]) == geo.STAY


def test_art_sap_mirrors_delta_for_player_1():
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.main import Agent_x
    from tests.conftest import ENV_CFG

    a = _stay_agent(art_sap=True)
    b = Agent_x("player_1", cfg=AgentConfig(art_sap=True), train=False)
    b.set_env_cfg(ENV_CFG)
    b.set_to_eval_mode()
    b.q = a.q
    mx = lambda x, y, e: (*geo.mirror_xy(x, y), e)  # noqa: E731
    obs = make_obs(10, 10, team=1, units=[mx(5, 5, 100)], enemies=[mx(*p) for p in PAIR],
                   relics=[geo.mirror_xy(12, 12)])
    act = b.act(10, obs)
    assert int(act[0, 0]) == geo.SAP
    assert (int(act[0, 1]), int(act[0, 2])) == geo.mirror_delta(3, 3)


# --- siege (Belagerung einer Punkte-Festung) ---------------------------------------
FORT = [(10, 10, 80), (10, 11, 80), (11, 10, 80)]


def _siege_agent(units, enemies=FORT, opp_gain=None, visible=True, **cfg):
    a = _stay_agent(siege=True, **cfg)
    for x, y, _ in FORT:
        a.belief.point_tiles[x, y] = True
    obs = make_obs(10, 10, units=units, enemies=enemies if visible else [], relics=[(12, 12)],
                   sensor_all=True)
    return a, obs


def test_siege_plan_spots_are_outside_manhattan_but_inside_square():
    from agents.sherlock import rules
    a, obs = _siege_agent([(6, 6, 100)])
    ctx = a._decide(obs)[0]
    plan = rules.SiegePlan(ctx, a.belief)
    assert plan.fortress[10, 10] and plan.fortress[10, 11] and plan.fortress[11, 10]
    assert plan.spots[6, 6]          # Manhattan 8 > 4, Chebyshev 4 <= 4
    assert not plan.spots[7, 10]     # Manhattan 3 -> Solution_92 trifft
    assert not plan.spots[2, 2]      # zu weit fuer einen eigenen Treffer
    assert plan.best_shot(6, 6) == (4, 4, 2.0)


def test_siege_fires_from_spot_instead_of_walking_in():
    a, obs = _siege_agent([(6, 6, 100)])
    act = a.act(10, obs)
    assert int(act[0, 0]) == geo.SAP and (int(act[0, 1]), int(act[0, 2])) == (4, 4)
    b, obs = _siege_agent([(6, 6, 100)])
    b.cfg.siege = False
    assert int(b.act(10, obs)[0, 0]) == geo.STAY


def test_siege_without_energy_waits_on_spot():
    a, obs = _siege_agent([(6, 6, 30)])
    act = a.act(10, obs)
    assert int(act[0, 0]) == geo.STAY


def test_siege_walks_toward_nearest_spot():
    from agents.sherlock import rules
    a, obs = _siege_agent([(2, 4, 100)])
    act = a.act(10, obs)
    ctx = a._prev_ctx
    plan = rules.SiegePlan(ctx, a.belief)
    d0 = rules.distance_map(ctx["passable"], (2, 4))
    nearest = int(d0[plan.spots].min())
    d = int(act[0, 0])
    assert d in (geo.RIGHT, geo.DOWN)
    nx, ny = 2 + int(geo.DIR_DX[d]), 4 + int(geo.DIR_DY[d])
    assert int(rules.distance_map(ctx["passable"], (nx, ny))[plan.spots].min()) == nearest - 1


def test_siege_leaves_point_tile_holder_alone():
    a, obs = _siege_agent([(10, 12, 100)])
    a.belief.point_tiles[10, 12] = True   # eigenes Punkte-Tile direkt an der Festung
    act = a.act(10, obs)
    assert int(act[0, 0]) == geo.STAY


def test_siege_counts_hidden_occupants_from_opponent_gain():
    from agents.sherlock import rules
    a, obs = _siege_agent([(6, 6, 100)], visible=False)
    a.act(10, obs)
    a.belief.last_seen[10:12, 10:12] = -1   # Festung liegt im Nebel
    a.belief.opp_gain = 3                    # drei Punkte -> drei versteckte Besetzer
    plan = rules.SiegePlan(a._prev_ctx, a.belief)
    assert plan.fortress[10, 10] and plan.fortress[11, 10]
    assert not plan.spots[7, 10]
    a.belief.opp_gain = 0
    assert not rules.SiegePlan(a._prev_ctx, a.belief).fortress.any()


# --- threat_feats (Gefahr-Merkmale fuer neue Netze) ------------------------------------
def test_threat_features_count_manhattan_and_square_threat():
    from agents.sherlock.features import THREAT_DIM, THREAT_NAMES, threat_features
    a = _stay_agent(threat_feats=True)
    obs = make_obs(10, 10, units=[(5, 5, 100)], enemies=[(8, 8, 80), (9, 8, 30), (6, 5, 50)],
                   relics=[(12, 12)])
    a.belief.point_tiles[8, 8] = True
    ctx = a._decide(obs)[0]
    f = dict(zip(THREAT_NAMES, threat_features(ctx, 0)))
    assert len(THREAT_NAMES) == THREAT_DIM == 22
    # stehen auf (5, 5): (6,5) Manhattan 1, (8,8) Manhattan 6 > 4; (9,8) kann nicht sappen
    assert f["c_threat_man"] == 0.25 and f["c_threat_sq"] == 0.5
    assert f["c_enemy_adj"] == 50 / 400 and f["c_enemy_here"] == 0.0
    assert f["r_enemy_here"] == 50 / 400          # Zug nach rechts landet auf dem Gegner
    assert f["best_sap_hits"] == 0.5              # (8,8)+(9,8) in einem 3x3
    assert f["enemy_on_points"] == 1 / 8


def test_threat_agent_has_larger_input_and_roundtrips(tmp_path):
    import numpy as np
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.features import FEATURE_DIM, THREAT_DIM
    from agents.sherlock.main import Agent_x
    from tests.conftest import ENV_CFG
    a = Agent_x("player_0", cfg=AgentConfig(threat_feats=True), train=False)
    a.set_env_cfg(ENV_CFG)
    obs = make_obs(10, 10, units=[(5, 5, 100)], enemies=[(7, 6, 80)], relics=[(12, 12)])
    a.act(10, obs)
    assert a.feat_dim == FEATURE_DIM + THREAT_DIM
    assert a._prev_feats[0].shape == (FEATURE_DIM + THREAT_DIM,)
    path = str(tmp_path / "t.pth")
    a.save_agent(path)
    b = Agent_x("player_0", agent_path=path, train=False)
    assert b.cfg.threat_feats and b.feat_dim == a.feat_dim
    x = np.zeros((1, a.feat_dim), np.float32)
    import torch
    assert torch.allclose(a.q(torch.as_tensor(x)), b.q(torch.as_tensor(x)))
    assert Agent_x("player_0", train=False).feat_dim == FEATURE_DIM


def test_mixed_ensemble_feeds_old_nets_their_first_features(tmp_path, monkeypatch):
    import sys

    import numpy as np
    import pytest
    import torch
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.features import FEATURE_DIM
    from agents.sherlock.main import Agent_x
    from scripts import build_ensemble
    from tests.conftest import ENV_CFG

    new = Agent_x("player_0", cfg=AgentConfig(threat_feats=True), train=False)
    old = Agent_x("player_0", train=False)
    pn, po, out = (str(tmp_path / n) for n in ("new.pth", "old.pth", "mix.pth"))
    new.save_agent(pn)
    old.save_agent(po)
    monkeypatch.setattr(sys, "argv", ["x", "--out", out, pn, po])
    with pytest.raises(SystemExit):
        build_ensemble.main()   # ohne --mixed abgewiesen
    monkeypatch.setattr(sys, "argv", ["x", "--mixed", "--out", out, pn, po])
    build_ensemble.main()
    mix = Agent_x("player_0", agent_path=out, train=False)
    mix.set_env_cfg(ENV_CFG)
    assert [m.feat_dim for m in mix.extra_q] == [FEATURE_DIM]
    obs = make_obs(10, 10, units=[(5, 5, 100)], enemies=[(7, 6, 80)], relics=[(12, 12)])
    feats = torch.as_tensor(mix._decide(obs)[2][0][None])
    want = (new.q(feats) + old.q(feats[:, :FEATURE_DIM])) / 2
    got = torch.stack([mix.q(feats), mix.extra_q[0](feats[:, :FEATURE_DIM])]).mean(0)
    assert torch.allclose(got, want)
    mix.set_to_eval_mode()
    assert np.asarray(mix.act(10, obs)).shape == (16, 3)
    resaved = str(tmp_path / "re.pth")
    mix.save_agent(resaved)
    assert torch.load(resaved, weights_only=False)["ensemble_dims"] == [FEATURE_DIM]


# --- opp_model + dodge -------------------------------------------------------------
def test_sol92_model_targets_highest_visible_id_in_manhattan_range():
    from agents.sherlock.opp_model import predict_sol92_saps
    a = _stay_agent()
    a.belief.point_tiles[7, 6] = True
    # Gegner auf Punkte-Tile (7, 6); unsere Units 0 (5, 5) und 1 (6, 7) in Reichweite 4,
    # Unit 2 (1, 1) zu weit weg -> Ziel ist Unit 1
    obs = make_obs(10, 10, units=[(5, 5, 50), (6, 7, 50), (1, 1, 50)], enemies=[(7, 6, 80)],
                   relics=[(8, 8)])
    ctx = a._decide(obs)[0]
    assert predict_sol92_saps(ctx, a.belief) == [(0, 1)]
    weak = make_obs(11, 11, units=[(5, 5, 50)], enemies=[(7, 6, 30)], relics=[(8, 8)])
    assert predict_sol92_saps(a._decide(weak)[0], a.belief) == []   # 30 < Sap-Kosten 40


def test_dodge_moves_lethally_targeted_unit_to_free_point_tile():
    for flag, energy, want in ((False, 15, geo.STAY), (True, 15, geo.DOWN), (True, 50, geo.STAY)):
        a = _stay_agent(dodge=flag)
        a.belief.point_tiles[7, 6] = True
        a.belief.point_tiles[5, 5] = True
        a.belief.point_tiles[5, 6] = True
        obs = make_obs(10, 10, units=[(5, 5, energy)], enemies=[(7, 6, 80)], relics=[(8, 8)])
        assert int(a.act(10, obs)[0, 0]) == want, (flag, energy)


def test_dodge_always_mode_and_untargeted_units_stay():
    a = _stay_agent(dodge=True, dodge_mode="always")
    a.belief.point_tiles[7, 6] = True
    obs = make_obs(10, 10, units=[(5, 5, 200), (6, 7, 200)], enemies=[(7, 6, 80)], relics=[(8, 8)])
    act = a.act(10, obs)
    assert int(act[0, 0]) == geo.STAY       # Unit 0 ist nicht das Ziel
    assert int(act[1, 0]) != geo.STAY       # Unit 1 (hoechste ID) weicht aus


def test_dodge_survives_multi_unit_step_with_saps():
    # Regression 21.10.: ein Sap einer Unit darf die Trefferliste der naechsten nicht ueberschreiben
    a = _stay_agent(dodge=True, pt_sap=True)
    for t in ((7, 6), (5, 5), (5, 6)):
        a.belief.point_tiles[t] = True
    obs = make_obs(10, 10, units=[(5, 5, 100), (6, 7, 15)], enemies=[(7, 6, 80)], relics=[(8, 8)])
    act = a.act(10, obs)
    assert int(act[0, 0]) == geo.SAP        # Unit 0 sappt vom Punkte-Tile (pt_sap)
    assert int(act[1, 0]) != geo.STAY       # Unit 1 ist das Ziel und weicht aus


def test_seed_file_rejects_validation_overlap(tmp_path):
    import json

    import pytest
    from scripts import experiment
    f = tmp_path / "hard.json"
    f.write_text(json.dumps([360001, 500003]))
    with pytest.raises(SystemExit):
        experiment.main(["--variant", "full_rules_v3", "--games", "4", "--no-test",
                         "--seed-file", str(f), "--out", str(tmp_path / "run")])
    assert not (tmp_path / "run").exists()


def test_tactics_when_behind_gates_art_sap_on_score():
    for points, want in (((10, 5), geo.STAY), ((5, 10), geo.SAP)):
        a = _stay_agent(art_sap=True, tactics_when_behind=True)
        obs = make_obs(10, 10, units=[(5, 5, 100)], enemies=PAIR, relics=[(12, 12)], points=points)
        assert int(a.act(10, obs)[0, 0]) == want, points


def _with_nebula_estimate(a, value):
    import numpy as np
    from agents.sherlock.param_est import NEBULA_REDUCTIONS
    a.param_est.log_neb = np.array([0.0 if r == value else -50.0 for r in NEBULA_REDUCTIONS])
    a.param_est.n_neb = 5
    return a


def test_nebula_avoid_masks_moves_into_harmful_nebula_and_leaves_it():
    import numpy as np
    from tests.conftest import make_obs as mk
    obs = mk(10, 10, units=[(5, 5, 100)], relics=[(12, 12)])
    obs["map_features"]["tile_type"] = np.zeros((24, 24), np.int32)
    obs["map_features"]["tile_type"][6, 5] = 1   # Nebel rechts
    for flag, value, right_ok in ((False, 25, True), (True, 5, True), (True, 25, False)):
        a = _with_nebula_estimate(_stay_agent(nebula_avoid=flag), value)
        a.act(10, obs)
        assert bool(a._prev_masks[0][geo.RIGHT]) == right_ok, (flag, value)
    inside = mk(11, 11, units=[(6, 5, 100)], relics=[(12, 12)])
    inside["map_features"]["tile_type"] = np.zeros((24, 24), np.int32)
    inside["map_features"]["tile_type"][6, 5] = 1
    a = _with_nebula_estimate(_stay_agent(nebula_avoid=True), 25)
    assert int(a.act(11, inside)[0, 0]) != geo.STAY   # verlaesst den Nebel


def test_sap_kill_safe_prefers_killable_living_enemy_not_dead_one():
    def target(enemies, **cfg):
        a = _stay_agent(pt_sap=True, **cfg)
        a.belief.point_tiles[5, 5] = True
        act = a.act(10, make_obs(10, 10, units=[(5, 5, 100)], enemies=enemies, relics=[(12, 12)]))
        assert int(act[0, 0]) == geo.SAP
        return int(act[0, 1]), int(act[0, 2])
    # nur der schon tote Gegner (5,8) wirkt "toetbar": alte Regel verschwendet den Sap darauf
    dead_only = [(7, 6, 150), (3, 5, 45), (5, 8, -5)]
    assert target(dead_only, sap_kill_first=True) == (0, 3)
    assert target(dead_only, sap_kill_safe=True) == (2, 1) == target(dead_only)
    # ein lebender, sicher toetbarer Gegner wird bevorzugt
    killable = [(7, 6, 150), (3, 5, 20), (5, 8, -5)]
    assert target(killable, sap_kill_safe=True) == (-2, 0)


def test_dodge_auto_follows_estimated_dropoff():
    import numpy as np
    from agents.sherlock.param_est import DROPOFFS
    for drop, want_move in ((None, True), (0.25, True), (1.0, False)):
        a = _stay_agent(dodge_auto=True, dodge_mode="always")
        if drop is not None:
            a.param_est.log_drop = np.array([0.0 if d == drop else -50.0 for d in DROPOFFS])
            a.param_est.n_drop = 5
        a.belief.point_tiles[7, 6] = True
        obs = make_obs(10, 10, units=[(5, 5, 200), (6, 7, 200)], enemies=[(7, 6, 80)], relics=[(8, 8)])
        assert (int(a.act(10, obs)[1, 0]) != geo.STAY) == want_move, drop


def test_stack_guard_masks_move_onto_own_point_tile():
    for flag, ok in ((False, True), (True, False)):
        a = _stay_agent(stack_guard=flag)
        a.belief.point_tiles[6, 5] = True
        a.act(10, make_obs(10, 10, units=[(5, 5, 100), (6, 5, 100)], relics=[(12, 12)]))
        assert bool(a._prev_masks[0][geo.RIGHT]) == ok


def test_sap_dropoff_est_changes_target_scoring():
    import numpy as np
    from agents.sherlock.param_est import DROPOFFS
    # Zentrum A (7,6): 60 Energie, Nachbarn 2 x 50; Zentrum B (3,5): 100 Energie allein
    enemies = [(7, 6, 60), (8, 6, 50), (7, 7, 50), (3, 5, 100)]
    for drop, want in ((1.0, (2, 1)), (0.25, (-2, 0))):
        a = _stay_agent(pt_sap=True, sap_dropoff_est=True)
        a.param_est.log_drop = np.array([0.0 if d == drop else -50.0 for d in DROPOFFS])
        a.param_est.n_drop = 5
        a.belief.point_tiles[5, 5] = True
        act = a.act(10, make_obs(10, 10, units=[(5, 5, 100)], enemies=enemies, relics=[(12, 12)]))
        assert int(act[0, 0]) == geo.SAP and (int(act[0, 1]), int(act[0, 2])) == want, drop


def test_relic_search_assigns_one_sticky_searcher_in_later_matches():
    a = _stay_agent(relic_search=True)
    a.belief.point_tiles[3, 3] = True
    # Match 2 (match_idx 1), nur ein Relic-Paar bekannt -> ein Sucher
    obs = make_obs(110, 9, units=[(3, 3, 100), (1, 1, 120), (2, 0, 80)], relics=[(4, 4)],
                   sensor_all=False)
    a.act(110, obs)
    st = a._searcher
    assert st is not None and st[0] == 1 and st[1] == 1   # hoechste Energie, nicht auf Punkte-Tile
    goal = st[2]
    assert goal[0] + goal[1] <= 23
    assert a._prev_ctx["assigned"][1] == goal
    a.act(111, make_obs(111, 10, units=[(3, 3, 100), (1, 2, 118), (2, 0, 80)], relics=[(4, 4)],
                        sensor_all=False))
    assert a._searcher[1] == 1                            # bleibt derselbe Sucher
    # Match 1 (match_idx 0): keine Suche
    b = _stay_agent(relic_search=True)
    b.act(10, make_obs(10, 10, units=[(1, 1, 120)], relics=[(4, 4)], sensor_all=False))
    assert b._searcher is None
