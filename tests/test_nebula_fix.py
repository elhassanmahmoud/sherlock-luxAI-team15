"""Korrekturen vom 01.11.2026 zur Nebel-Meidung (Diagnose 812584, Nebelabzug 25, Bewegungskosten 5).

est_censor: Die Engine kappt die Energie nach Feld und Nebel bei 0. Eine Unit mit 0 Energie im Nebel auf einem
Feld ohne Energie zeigte "Verlust 0" und kippte die Schaetzung des Nebelabzugs von 25 auf 0.
neb_cross: In den Nebel nur mit Energie fuer die ganze Durchquerung statt pauschal 2x Abzug.
"""
import numpy as np
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.param_est import ParamEstimator
from tests.conftest import ENV_CFG, make_obs
from tests.test_rules_1910 import _stay_agent
from tests.test_rules_2110 import _with_nebula_estimate


def _nebula_obs(ms, energy, pos=(5, 5)):
    obs = make_obs(ms, ms, units=[(pos[0], pos[1], energy)])
    obs["map_features"]["tile_type"][pos] = 1  # Nebel, Feldenergie 0
    return obs


def _feed(est, energies):
    """Unit steht (Aktion 0) auf einem Nebel-Tile; je Schritt die beobachtete Energie."""
    stay = np.zeros((16, 3), dtype=int)
    for i, e in enumerate(energies):
        obs = _nebula_obs(10 + i, e)
        est.observe(obs, 0, None, ENV_CFG)
        est.remember(obs, 0, stay)


def test_clipped_zero_energy_no_longer_flips_the_nebula_estimate():
    seq = [100, 75, 50, 25, 0, 0, 0, 0, 0, 0]          # Abzug 25, danach bei 0 gekappt
    old, new = ParamEstimator(), ParamEstimator(censor=True)
    _feed(old, seq)
    _feed(new, seq)
    assert old.nebula() == 0                            # der Fehler: 6x "Verlust 0" schlagen 3x "Verlust 25"
    assert new.nebula() == 25
    assert new.n_neb == 3


def test_censor_keeps_ordinary_observations():
    est = ParamEstimator(censor=True)
    _feed(est, [100, 97])                               # Abzug 3, keine Kappung
    assert est.nebula() == 3
    assert ParamEstimator(censor=True).nebula(default=None) is None


def test_agent_passes_the_switch_to_the_estimator():
    assert _stay_agent().param_est.censor is False
    assert _stay_agent(est_censor=True).param_est.censor is True


class _Right(torch.nn.Module):
    def forward(self, x):
        q = torch.zeros(x.shape[0], 6)
        q[:, geo.RIGHT] = 1.0
        return q


def _band_move(energy, unit=(5, 5), **cfg):
    """Nebelstreifen x = 6..8 ueber die ganze Hoehe, Ziel Punkte-Tile (10, 5) dahinter, Netz will nach rechts."""
    a = _with_nebula_estimate(_stay_agent(nebula_avoid=True, nebula_avoid_mode="soft", **cfg), 25)
    a.q = _Right()
    a.belief.point_tiles[10, 5] = True
    obs = make_obs(10, 10, units=[(unit[0], unit[1], energy)], relics=[(12, 12)])
    obs["map_features"]["tile_type"][6:9, :] = 1
    return int(a.act(10, obs)[0, 0])


def test_neb_cross_needs_energy_for_the_whole_band():
    # 3 Nebel-Tiles x (3 Zug + 25 Abzug) + 3 hinaus = 87
    assert _band_move(80, neb_cross=True) == geo.STAY      # wartet und sammelt Energie
    assert _band_move(90, neb_cross=True) == geo.RIGHT
    assert _band_move(60) == geo.RIGHT                     # Schalter aus: wie V12 ab 2 x 25 = 50 hinein
    assert _band_move(40) == geo.STAY


def test_neb_cross_reaches_a_point_tile_inside_the_nebula():
    a = _with_nebula_estimate(_stay_agent(nebula_avoid=True, nebula_avoid_mode="soft", neb_cross=True), 25)
    a.q = _Right()
    a.belief.point_tiles[7, 5] = True                      # Ziel liegt im Nebel, 2 Tiles weit
    obs = make_obs(10, 10, units=[(5, 5, 35)], relics=[(12, 12)])
    obs["map_features"]["tile_type"][6:9, :] = 1
    # (6, 5) kostet 3 + 25, der Zug auf das Ziel nur noch 3: 31 genuegen, 0 Energie dort punktet weiter
    assert int(a.act(10, obs)[0, 0]) == geo.RIGHT


def test_neb_cross_leaves_the_nebula_when_the_way_ahead_is_too_long():
    a = _with_nebula_estimate(_stay_agent(nebula_avoid=True, nebula_avoid_mode="soft", neb_cross=True), 25)
    a.q = _Right()
    a.belief.point_tiles[12, 5] = True
    obs = make_obs(10, 10, units=[(6, 5, 40)], relics=[(14, 14)])
    obs["map_features"]["tile_type"][6:11, :] = 1           # steht am Rand eines 5 Tiles breiten Streifens
    assert int(a.act(10, obs)[0, 0]) == geo.LEFT            # zurueck auf (5, 5) statt im Nebel festzusitzen
