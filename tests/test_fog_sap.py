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


# fog_prior / fog_drop_est (31.10.2026, abends): Gewichte nach der letzten eigenen Beobachtung und Streufaktor aus
# param_est. Halter (10, 11), versteckte Kandidaten (12, 13) und (13, 9), ein versteckter Besetzer (Gegner +1).
# Gleich gewichtet traegt jeder Kandidat 0,5 Sap-Kosten, das liegt unter min_frac 0,6: kein Schuss.


def _act_prior(enemy_at=None, empty_at=None, **cfg):
    a = _stay_agent(use_symmetry=True, fog_sap=True, fog_v2=True, **cfg)
    for x, y in ((10, 11), (12, 13), (13, 9)):
        a.belief.point_tiles[x, y] = True
    if enemy_at is not None:
        a.belief.enemy_seen_at[enemy_at] = 5          # in diesem Match bei Schritt 5 mit Gegner gesehen
    if empty_at is not None:
        a.belief.empty_seen_at[empty_at] = 5          # ... bzw. leer gesehen
    obs = make_obs(10, 10, units=[(10, 11, 200)], points=(1, 1), relics=[(11, 12)], sensor_all=False)
    obs["sensor_mask"][9:12, 10:13] = True
    return tuple(int(v) for v in a.act(10, obs)[0])


def test_fog_prior_shoots_where_an_enemy_was_seen_last():
    assert _act_prior(enemy_at=(13, 9), empty_at=(12, 13)) == (geo.STAY, 0, 0)                 # Schalter aus
    assert _act_prior(enemy_at=(13, 9), empty_at=(12, 13), fog_prior=True) == (geo.SAP, 3, -2)
    assert _act_prior(enemy_at=(12, 13), empty_at=(13, 9), fog_prior=True) == (geo.SAP, 2, 2)
    assert _act_prior(fog_prior=True) == (geo.STAY, 0, 0)        # ohne Beobachtung gleich gewichtet wie vorher


def test_fog_prior_bookkeeping_and_reset_at_match_start():
    import numpy as np
    for team in (0, 1):
        a = _stay_agent(use_symmetry=True, fog_sap=True, fog_v2=True, fog_prior=True)
        a.belief.team_id, a.belief.opp_team_id = team, 1 - team
        a.belief.mirrored = a.belief.canonical and team == 1
        unit, enemy = (10, 11, 200), (11, 12, 50)
        obs = make_obs(10, 10, team=team, units=[unit], enemies=[enemy], sensor_all=False)
        obs["sensor_mask"][9:12, 10:13] = True
        a.belief.observe(obs)
        b = a.belief
        ex, ey = (geo.mirror_positions(np.array([enemy[:2]]))[0] if b.mirrored else enemy[:2])
        sx, sy = (geo.mirror_positions(np.array([[9, 10]]))[0] if b.mirrored else (9, 10))
        assert b.enemy_seen_at[ex, ey] == 10 and b.empty_seen_at[ex, ey] == -1
        assert b.empty_seen_at[sx, sy] == 10 and b.enemy_seen_at[sx, sy] == -1
        assert (b.empty_seen_at >= 0).sum() == 8 and (b.enemy_seen_at >= 0).sum() == 1
        b.observe(make_obs(101, 0, team=team))                       # neues Match: alte Zeitstempel weg
        assert (b.enemy_seen_at == -1).all() and (b.empty_seen_at == -1).all()


def test_fog_drop_est_passes_the_safe_estimate(monkeypatch):
    from agents.sherlock import rules
    seen = []
    orig = rules.fog_sap

    def spy(*args, **kw):
        seen.append(kw["dropoff"])
        return orig(*args, **kw)

    monkeypatch.setattr(rules, "fog_sap", spy)
    for flag, want in ((False, 0.5), (True, 0.25)):
        seen.clear()
        a = _stay_agent(use_symmetry=True, fog_sap=True, fog_v2=True, fog_prior=True, fog_drop_est=flag)
        a.param_est.dropoff = lambda default=0.5, min_conf=0.9: 0.25     # sicher geschaetzt 0,25
        for x, y in ((10, 11), (12, 13)):
            a.belief.point_tiles[x, y] = True
        obs = make_obs(10, 10, units=[(10, 11, 200)], points=(1, 1), relics=[(11, 12)], sensor_all=False)
        obs["sensor_mask"][9:12, 10:13] = True
        a.act(10, obs)
        assert seen == [want]
