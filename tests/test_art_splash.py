"""Regeln vom 30.10.2026 fuer sicher geschaetzten Sap-Streufaktor 1,0: art_splash (Artillerie wie
art_safe=false + art_min_hits=2) und sap_still_splash (Halter sappen auch ziehende Gegner)."""
import numpy as np

from agents.sherlock import geometry as geo
from tests.conftest import make_obs
from tests.test_rules_1910 import _stay_agent
from tests.test_rules_2110 import PAIR

NEAR = PAIR + [(7, 6, 60)]  # bewaffneter Gegner in Manhattan-Reichweite 4 von (5, 5)
V10_ART = dict(art_sap=True, art_min_hits=3)  # art_safe bleibt True


def _act(dropoff, **cfg):
    a = _stay_agent(**V10_ART, **cfg)
    if dropoff is not None:  # Schaetzung sicher auf einem Wert
        a.param_est.log_drop = np.array([0.0 if d == dropoff else -50.0 for d in (0.25, 0.5, 1.0)])
        a.param_est.n_drop = 5
    return int(a.act(10, make_obs(10, 10, units=[(5, 5, 100)], enemies=NEAR, relics=[(12, 12)]))[0, 0])


def test_art_splash_only_with_confident_full_splash():
    assert _act(1.0) == geo.STAY  # Schalter aus: 3 Treffer noetig und art_safe
    assert _act(1.0, art_splash=True) == geo.SAP
    for dropoff in (None, 0.25, 0.5):
        assert _act(dropoff, art_splash=True) == geo.STAY


def test_art_splash_keeps_one_hit_minimum():
    a = _stay_agent(**V10_ART, art_splash=True)
    a.param_est.log_drop = np.array([-50.0, -50.0, 0.0])
    a.param_est.n_drop = 5
    act = a.act(10, make_obs(10, 10, units=[(5, 5, 100)], enemies=PAIR[:1] + [(7, 6, 60)], relics=[(12, 12)]))
    # (8, 8) und (7, 6) liegen nicht im selben 3x3 -> hoechstens ein Treffer je Sap
    assert int(act[0, 0]) == geo.STAY


def test_sap_still_splash_lets_holder_hit_moving_target_only_with_full_splash():
    # wie test_sap_still_skips_moving_target: Halter (5,5), Gegner zieht von (8,8) nach (8,7)
    for dropoff, want in ((1.0, geo.SAP), (0.5, geo.STAY), (None, geo.STAY)):
        a = _stay_agent(pt_sap=True, sap_still=True, sap_still_splash=True)
        a.belief.point_tiles[5, 5] = True
        if dropoff is not None:
            a.param_est.log_drop = np.array([0.0 if d == dropoff else -50.0 for d in (0.25, 0.5, 1.0)])
            a.param_est.n_drop = 5
        a.act(9, make_obs(9, 9, units=[(5, 5, 200)], enemies=[(8, 8, 60)], relics=[(9, 9)]))
        act = a.act(10, make_obs(10, 10, units=[(5, 5, 200)], enemies=[(8, 7, 60)], relics=[(9, 9)]))
        assert int(act[0, 0]) == want, dropoff


def test_splash_min_drop_extends_the_rules_to_half_splash():
    assert _act(0.5, art_splash=True) == geo.STAY
    assert _act(0.5, art_splash=True, splash_min_drop=0.5) == geo.SAP
    assert _act(0.25, art_splash=True, splash_min_drop=0.5) == geo.STAY
    assert _act(None, art_splash=True, splash_min_drop=0.5) == geo.STAY  # default 0,0 bleibt darunter


def test_splash_safe_below_keeps_safety_at_half_splash():
    half = dict(art_splash=True, splash_min_drop=0.5)
    assert _act(0.5, **half) == geo.SAP                                    # V11-Logik: ohne Sicherheit
    assert _act(0.5, splash_safe_below=1.0, **half) == geo.STAY            # bewaffneter Gegner in Reichweite
    assert _act(1.0, splash_safe_below=1.0, **half) == geo.SAP             # voller Streuschaden wie bisher
