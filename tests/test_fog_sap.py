"""Regel vom 31.10.2026: fog_v2 (Nebel-Sap mit echter Sicht statt Sensor plus Spiegelbild)."""
from agents.sherlock import geometry as geo
from tests.conftest import make_obs
from tests.test_rules_1910 import _stay_agent

# Halter (10, 11) auf einem Punkte-Tile, dessen Spiegelbild (12, 13) ebenfalls Punkte-Tile ist. Der Gegner
# punktet 1, kein Gegner ist sichtbar. Der Sensor zeigt nur das 3x3 um den Halter; (12, 13) ist unsichtbar,
# gilt mit use_symmetry aber als gesehen, weil es das Spiegelbild des Halter-Tiles ist.


def _act(enemies=(), pts=((10, 11), (12, 13)), unit=(10, 11), **cfg):
    a = _stay_agent(use_symmetry=True, fog_sap=True, **cfg)
    for x, y in pts:
        a.belief.point_tiles[x, y] = True
    obs = make_obs(10, 10, units=[(*unit, 200)], enemies=list(enemies), points=(1, 1), relics=[(11, 12)],
                   sensor_all=False)
    ux, uy = unit
    obs["sensor_mask"][ux - 1:ux + 2, uy - 1:uy + 2] = True
    return tuple(int(v) for v in a.act(10, obs)[0])


def test_enemy_tile_hidden_by_the_mirror_is_a_target_only_with_v2():
    assert _act() == (geo.STAY, 0, 0)                   # alt: (12, 13) gilt als gesehen und leer
    assert _act(fog_v2=True) == (geo.SAP, 2, 2)


def test_v2_also_targets_hidden_point_tiles_on_our_half():
    # Halter auf der Diagonale (11, 12) ist sein eigenes Spiegelbild; (13, 9) liegt in unserer Haelfte
    kw = dict(unit=(11, 12), pts=[(11, 12), (13, 9)])
    assert _act(**kw) == (geo.STAY, 0, 0)
    assert _act(fog_v2=True, **kw) == (geo.SAP, 2, -3)
    assert _act(fog_sap_max_sensor=1, fog_v2=True, **kw) == (geo.STAY, 0, 0)   # Sensorreichweite 2 > 1


def test_v2_keeps_a_visible_target():
    # Sichtbarer Gegner (9, 12) neben dem Halter: pt_sap schiesst auf ihn, der Nebel-Sap ueberschreibt das nicht
    assert _act(enemies=[(9, 12, 80)], pt_sap=True, fog_v2=True) == (geo.SAP, -1, 1)
    assert _act(fog_v2=True, pt_sap=True) == (geo.SAP, 2, 2)
