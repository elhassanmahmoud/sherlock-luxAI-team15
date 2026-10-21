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
