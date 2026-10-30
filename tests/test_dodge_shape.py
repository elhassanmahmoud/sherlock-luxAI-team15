"""Regel vom 30.10.2026: dodge_shape (opp_model erkennt Raute oder Quadrat als Sap-Form des Gegners)."""
import numpy as np

from agents.sherlock import geometry as geo
from tests.conftest import make_obs
from tests.test_rules_1910 import _stay_agent

# Schuetze (7, 6) auf Punkte-Tile, Sap-Kosten 40, Reichweite 4. Unit 0 (6, 5) liegt in Raute und
# Quadrat, Unit 1 (4, 3) nur im Quadrat (Manhattan 6, Chebyshev 3); der Spaeher (3, 2) ohne
# Sap-Energie macht Unit 1 fuer den Gegner sichtbar (Sensorreichweite 2).
ENEMIES = [(7, 6, 80), (3, 2, 10)]


def _obs(step, e1=200):
    return make_obs(step, step, units=[(6, 5, 200), (4, 3, e1)], enemies=ENEMIES, relics=[(8, 8)])


def _agent(**cfg):
    a = _stay_agent(dodge=True, dodge_mode="always", **cfg)
    a.belief.point_tiles[7, 6] = True
    return a


def test_model_targets_highest_id_in_diamond_or_square():
    from agents.sherlock.opp_model import predict_sol92_saps
    a = _agent()
    ctx = a._decide(_obs(10))[0]
    assert predict_sol92_saps(ctx, a.belief) == [(0, 0)]
    assert predict_sol92_saps(ctx, a.belief, shape="man") == [(0, 0)]
    assert predict_sol92_saps(ctx, a.belief, shape="cheb") == [(0, 1)]


def test_square_hit_switches_the_model():
    a = _agent(dodge_shape=True)
    act = a.act(10, _obs(10))
    assert int(act[0, 0]) != geo.STAY and int(act[1, 0]) == geo.STAY  # Raute: Unit 0 weicht aus
    assert [p[0] for p in a._shape_pending] == [1] and a._shape_pending[0][-1] == "cheb"
    act = a.act(11, _obs(11, e1=160))  # Unit 1 stand und verlor die Sap-Kosten 40
    assert a._shape_ev == {"man": 0, "cheb": 1}
    assert int(act[1, 0]) != geo.STAY and int(act[0, 0]) == geo.STAY  # Quadrat: Unit 1 weicht aus


def test_no_hit_keeps_the_diamond_and_switch_off_changes_nothing():
    a = _agent(dodge_shape=True)
    a.act(10, _obs(10))
    act = a.act(11, _obs(11))
    assert a._shape_ev == {"man": 0, "cheb": 0}
    assert int(act[0, 0]) != geo.STAY and int(act[1, 0]) == geo.STAY
    b = _agent()
    b.act(10, _obs(10))
    act = b.act(11, _obs(11, e1=160))
    assert b._shape_pending == [] and b._shape_ev == {"man": 0, "cheb": 0}
    assert int(act[0, 0]) != geo.STAY and int(act[1, 0]) == geo.STAY


def test_no_evidence_with_confident_full_splash_or_after_match_reset():
    a = _agent(dodge_shape=True)
    a.param_est.log_drop = np.array([-50.0, -50.0, 0.0])  # Streufaktor sicher 1,0
    a.param_est.n_drop = 5
    a.act(10, _obs(10))
    a.act(11, _obs(11, e1=160))
    assert a._shape_ev == {"man": 0, "cheb": 0}
    b = _agent(dodge_shape=True)
    b.act(99, _obs(99))
    b.act(101, make_obs(101, 0, units=[], enemies=[]))  # Match-Reset: Units verschwinden
    assert b._shape_pending == [] and b._shape_ev == {"man": 0, "cheb": 0}


def test_bait_stays_inside_the_square_once_the_square_is_known():
    # Schuetze (7, 7) auf Punkte-Tile, Halter Unit 0 auf (6, 8). Koeder Unit 1 (hoechste ID) auf (3, 5):
    # Manhattan 6, Chebyshev 4 -> nur im Quadrat Ziel; der Spaeher (2, 7) macht ihn sichtbar.
    # Links (2, 5) liegt ein freies Punkte-Tile, aber ausserhalb des Quadrats (Chebyshev 5).
    def act(ev):
        a = _stay_agent(dodge=True, dodge_mode="always", dodge_bait=True, dodge_shape=True)
        for t in ((7, 7), (6, 8), (2, 5)):
            a.belief.point_tiles[t] = True
        a._shape_ev = dict(ev)
        obs = make_obs(10, 10, units=[(6, 8, 200), (3, 5, 200)], enemies=[(7, 7, 80), (2, 7, 10)],
                       relics=[(9, 9)])
        return int(a.act(10, obs)[1, 0])
    assert act({"man": 0, "cheb": 0}) == geo.STAY  # Raute: Unit 1 ist kein Ziel
    got = act({"man": 0, "cheb": 2})
    assert got not in (geo.STAY, geo.LEFT), got  # Quadrat: ausweichen, aber in Reichweite bleiben
