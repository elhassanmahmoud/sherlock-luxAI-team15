"""Regel vom 30.10.2026: splash_dodge (Nachbarn vorhergesagter Ziele weichen dem Streuschaden aus)."""
import numpy as np

from agents.sherlock import geometry as geo
from tests.conftest import make_obs
from tests.test_rules_1910 import _stay_agent

# Schuetze (7, 6) auf Punkte-Tile, Sap-Kosten 40, Reichweite 4. Ziel nach dem Solution_92-Modell ist Unit 1
# (5, 5), die hoechste ID in Reichweite. Unit 0 (5, 4) steht daneben: Streuschaden 0,5 * 40 * Streufaktor
# (Schuetze im ersten Step noch nicht als stehend bekannt). Nur nach oben (5, 3) ist sie ausser Streuweite.


def _act(dropoff, e0=30, **cfg):
    a = _stay_agent(**cfg)
    a.belief.point_tiles[7, 6] = True
    if dropoff is not None:  # Schaetzung sicher auf einem Wert
        a.param_est.log_drop = np.array([0.0 if d == dropoff else -50.0 for d in (0.25, 0.5, 1.0)])
        a.param_est.n_drop = 5
    act = a.act(10, make_obs(10, 10, units=[(5, 4, e0), (5, 5, 200)], enemies=[(7, 6, 80)], relics=[(8, 8)]))
    return int(act[0, 0]), int(act[1, 0])


def test_neighbour_of_predicted_target_steps_out_of_splash():
    assert _act(1.0, splash_dodge=True) == (geo.UP, geo.STAY)
    assert _act(1.0) == (geo.STAY, geo.STAY)                      # Schalter aus


def test_only_with_confident_half_or_full_splash_and_enough_damage():
    for dropoff in (None, 0.25):
        assert _act(dropoff, splash_dodge=True) == (geo.STAY, geo.STAY)
    assert _act(1.0, e0=200, splash_dodge=True) == (geo.STAY, geo.STAY)   # 20 < 0,5 * 200
    assert _act(0.5, splash_dodge=True) == (geo.STAY, geo.STAY)           # 10 < 0,5 * 30
    assert _act(0.5, e0=15, splash_dodge=True) == (geo.UP, geo.STAY)      # 10 >= 0,5 * 15


def test_unit_does_not_walk_back_into_the_splash_zone():
    import torch

    class Down(torch.nn.Module):
        def forward(self, x):
            q = torch.zeros(x.shape[0], 6)
            q[:, geo.DOWN] = 1.0
            return q

    def act(**cfg):
        a = _stay_agent(**cfg)
        a.q = Down()
        a.belief.point_tiles[7, 6] = True
        a.param_est.log_drop = np.array([-50.0, -50.0, 0.0])  # Streufaktor sicher 1,0
        a.param_est.n_drop = 5
        # Unit 0 (5, 3) will nach unten auf (5, 4), direkt neben das vorhergesagte Ziel Unit 1 (5, 5)
        obs = make_obs(10, 10, units=[(5, 3, 30), (5, 5, 200)], enemies=[(7, 6, 80)], relics=[(8, 8)])
        return int(a.act(10, obs)[0, 0])
    assert act() == geo.DOWN
    got = act(splash_dodge=True)
    dx, dy = (0, 0) if got == geo.STAY else (int(geo.DIR_DX[got]), int(geo.DIR_DY[got]))
    assert max(abs(5 + dx - 5), abs(3 + dy - 5)) >= 2, got  # bleibt ausserhalb der Streuweite von (5, 5)


def test_dodge_distrust_trusts_first_and_switches_off_after_misses():
    units = lambda e1: [(5, 5, 200), (6, 7, e1)]  # Unit 1 ist das vorhergesagte Ziel des Schuetzen (7, 6)

    def agent(**cfg):
        a = _stay_agent(dodge=True, **cfg)
        a.belief.point_tiles[7, 6] = True
        return a

    a = agent(dodge_distrust=0.35)
    act = a.act(10, make_obs(10, 10, units=units(15), enemies=[(7, 6, 80)], relics=[(8, 8)]))
    assert int(act[1, 0]) != geo.STAY            # vertraut von Anfang an: toedlicher Treffer -> ausweichen
    b = agent(dodge_distrust=0.35)
    for step in range(10, 17):                   # 7 nicht toedliche Vorhersagen, Ziel bleibt stehen, kein Treffer
        b.act(step, make_obs(step, step, units=units(200), enemies=[(7, 6, 80)], relics=[(8, 8)]))
    assert b._pred_n >= 6 and b._pred_hit == 0
    act = b.act(17, make_obs(17, 17, units=units(15), enemies=[(7, 6, 80)], relics=[(8, 8)]))
    assert int(act[1, 0]) == geo.STAY            # Modell hat sich als falsch erwiesen -> kein Ausweichen mehr
