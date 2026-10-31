"""Absicherung der Battle-Abgabe (31.10.2026): Mit cfg.frozen faengt der Agent Fehler in act()/update() ab.

Der Kurs-Runner (lux/runner.py) ruft act() und bei train=True update() ohne try/except auf, ein Fehler wuerde das
Spiel abbrechen. Die eingefrorene Abgabe laesst ihre Units dann einen Schritt stehen. Ohne frozen (Training,
Messungen) bleiben Fehler sichtbar.
"""
import numpy as np
import pytest

from agents.sherlock import geometry as geo
from tests.conftest import make_obs
from tests.test_fog_sap import _act
from tests.test_rules_1910 import _stay_agent


def _break(agent, times=None):
    """belief.observe wirft RuntimeError, mit times nur bei den ersten times Aufrufen."""
    orig, calls = agent.belief.observe, []

    def observe(obs):
        calls.append(1)
        if times is None or len(calls) <= times:
            raise RuntimeError("kaputt")
        return orig(obs)

    agent.belief.observe = observe


def _obs():
    return make_obs(10, 10, units=[(10, 11, 200)])


def test_frozen_submission_lets_units_stay_and_reports_once(capsys):
    a = _stay_agent(frozen=True)
    _break(a)
    for _ in range(2):
        act = a.act(10, _obs())
        assert act.shape == (16, 3) and act.dtype.kind == "i" and not act.any()
    a.update(10, _obs(), 0.0, act, False, _obs())
    assert a.caught_errors == 3
    err = capsys.readouterr().err
    assert err.count("abgefangen") == 1 and "RuntimeError: kaputt" in err


def test_frozen_submission_plays_on_after_an_error():
    # Nebel-Sap-Lage aus test_fog_sap: ohne Fehler (SAP, 2, 2), eingefroren genauso
    assert _act(fog_v2=True) == _act(fog_v2=True, frozen=True) == (geo.SAP, 2, 2)
    a = _stay_agent(use_symmetry=True, fog_sap=True, fog_v2=True, frozen=True)
    for x, y in ((10, 11), (12, 13)):
        a.belief.point_tiles[x, y] = True
    obs = make_obs(10, 10, units=[(10, 11, 200)], points=(1, 1), relics=[(11, 12)], sensor_all=False)
    obs["sensor_mask"][9:12, 10:13] = True
    _break(a, times=1)
    assert not a.act(10, obs).any()                                     # Fehler: alle stehen
    assert tuple(int(v) for v in a.act(10, obs)[0]) == (geo.SAP, 2, 2)  # danach wieder normal
    assert a.caught_errors == 1


def test_errors_stay_visible_outside_the_submission():
    a = _stay_agent()
    _break(a)
    with pytest.raises(RuntimeError, match="kaputt"):
        a.act(10, _obs())
    with pytest.raises(RuntimeError, match="kaputt"):
        a.update(10, _obs(), 0.0, np.zeros((16, 3), dtype=int), False, _obs())
    assert a.caught_errors == 0
