"""Regel vom 31.10.2026: end_sap verschiesst in den letzten Schritten eines Matches die Restenergie auf
gegnerische Halter. Am Matchende entfernt die Engine alle Units, die Energie verfaellt dann ohnehin."""
import numpy as np

from agents.sherlock import geometry as geo
from tests.conftest import make_obs
from tests.test_rules_1910 import _stay_agent


def _act(ms, units, enemies, pts=((7, 6),), **cfg):
    a = _stay_agent(**cfg)
    for x, y in pts:
        a.belief.point_tiles[x, y] = True
    act = a.act(ms, make_obs(ms, ms, units=units, enemies=enemies))
    return [tuple(int(v) for v in act[u]) for u in range(len(units))]


def test_end_sap_only_in_the_last_steps_and_off_by_default():
    unit, enemy = [(5, 5, 100)], [(7, 6, 80)]                     # Gegner auf dem Punkte-Tile (7, 6)
    assert _act(95, unit, enemy) == [(geo.STAY, 0, 0)]             # Schalter aus
    assert _act(89, unit, enemy, end_sap=10) == [(geo.STAY, 0, 0)]  # noch 11 Schritte
    assert _act(90, unit, enemy, end_sap=10) == [(geo.SAP, 2, 1)]
    assert _act(99, unit, enemy, end_sap=10) == [(geo.SAP, 2, 1)]


def test_end_sap_prefers_holders_then_any_enemy():
    # (7, 6) steht auf einem Punkte-Tile (80 Energie), (6, 7) zieht mit 20: zuerst der Halter
    assert _act(95, [(5, 5, 100)], [(7, 6, 80), (6, 7, 20)], end_sap=10) == [(geo.SAP, 2, 1)]
    # ohne Halter in Reichweite der schwaechste andere Gegner: die Energie verfiele sonst
    assert _act(95, [(5, 5, 100)], [(6, 7, 20), (8, 8, 50)], pts=(), end_sap=10) == [(geo.SAP, 1, 2)]
    # unbewegte Gegner vor ziehenden
    a = _stay_agent(end_sap=10)
    a.act(95, make_obs(95, 95, units=[(5, 5, 100)], enemies=[(8, 8, 50), (6, 7, 20)]))
    act = a.act(96, make_obs(96, 96, units=[(5, 5, 100)], enemies=[(8, 8, 50), (6, 8, 20)]))
    assert tuple(int(v) for v in act[0]) == (geo.SAP, 3, 3)        # (8, 8) stand still, (6, 8) ist gezogen


def test_end_sap_focuses_the_weakest_holder_then_the_next():
    # Gegner (7, 6) mit 30 Energie stirbt am ersten Sap (40); die zweite Unit nimmt dann (6, 8)
    acts = _act(95, [(5, 5, 100), (5, 6, 100)], [(7, 6, 30), (6, 8, 90)], pts=((7, 6), (6, 8)),
                end_sap=10, sap_no_overkill=True)
    assert acts == [(geo.SAP, 2, 1), (geo.SAP, 1, 2)]


def test_end_sap_holder_keeps_energy_until_the_last_step():
    pts = ((5, 5), (7, 6))                                         # eigene Unit haelt (5, 5)
    assert _act(95, [(5, 5, 70)], [(7, 6, 80)], pts=pts, end_sap=10) == [(geo.STAY, 0, 0)]   # 70 - 40 < 40
    assert _act(95, [(5, 5, 80)], [(7, 6, 80)], pts=pts, end_sap=10) == [(geo.SAP, 2, 1)]
    assert _act(99, [(5, 5, 45)], [(7, 6, 80)], pts=pts, end_sap=10) == [(geo.SAP, 2, 1)]    # letzter Schritt


def test_end_sap_lets_units_walk_to_a_reachable_point_tile():
    a = _stay_agent(end_sap=10)
    a.belief.point_tiles[7, 6] = True
    a.belief.point_tiles[5, 8] = True                              # Ziel der Unit, 3 Schritte entfernt
    ctx = dict(max_match_steps=100, match_step=95, ally_pos={0: (5, 5)}, ally_ene={0: 100.0}, sap_cost=40,
               first_on_tile={}, assigned={0: (5, 8)}, enemy_coords=np.array([[7, 6]]),
               enemy_energies=np.array([80]), sap_range=4)
    still = np.array([False])
    assert a._end_sap(ctx, 0, geo.DOWN, np.zeros(1), still) is None          # 5 Schritte uebrig: weiterlaufen
    ctx["match_step"] = 97
    assert a._end_sap(ctx, 0, geo.DOWN, np.zeros(1), still) == (2, 1, 1)     # 3 Schritte: kommt zu spaet an
    assert a._end_sap(ctx, 0, geo.STAY, np.zeros(1), still) == (2, 1, 1)
    # Kandidaten-Tiles pruefen geht vor (findet Punkte-Tiles fuer die naechsten Matches)
    a.belief.point_tiles[5, 8] = False
    a.belief.candidate[5, 8] = True
    ctx["match_step"] = 95
    assert a._end_sap(ctx, 0, geo.DOWN, np.zeros(1), still) is None
