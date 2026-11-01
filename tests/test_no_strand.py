"""Regel vom 01.11.2026: no_strand. Die Engine kappt die Energie bei 0; eine Unit, die mit der letzten Zugenergie
auf ein Feld ohne Energiegewinn zieht, steht dort bis zum Matchende fest (Diagnose 812256)."""
import torch

from agents.sherlock import geometry as geo
from tests.conftest import make_obs
from tests.test_rules_1910 import _stay_agent


class _Right(torch.nn.Module):
    def forward(self, x):
        q = torch.zeros(x.shape[0], 6)
        q[:, geo.RIGHT] = 1.0
        return q


def _move(energy, fields=(), pts=(), **cfg):
    a = _stay_agent(**cfg)
    a.q = _Right()
    for x, y in pts:
        a.belief.point_tiles[x, y] = True
    obs = make_obs(10, 10, units=[(5, 5, energy)], relics=[(20, 20)])
    for (x, y), v in fields:
        obs["map_features"]["energy"][x, y] = v
    return int(a.act(10, obs)[0, 0])


def test_no_strand_waits_instead_of_spending_the_last_move_on_a_dead_field():
    # Zugkosten 3: mit 5 Energie bleiben nach dem Zug 2 < 3, das Feld (6, 5) bringt nichts
    assert _move(5) == geo.RIGHT                                   # Schalter aus: wie V12
    assert _move(5, no_strand=True) == geo.STAY
    assert _move(5, fields=[((6, 5), 4)], no_strand=True) == geo.RIGHT   # dort laedt die Unit wieder auf
    assert _move(10, no_strand=True) == geo.RIGHT                  # 10 - 3 = 7: kann danach weiterziehen


def test_no_strand_moves_to_a_charging_neighbour():
    fields = [((5, 5), -2), ((5, 4), 3)]
    assert _move(5, fields=fields, no_strand=True) == geo.UP


def test_no_strand_still_steps_onto_a_point_tile():
    assert _move(5, pts=[(6, 5)], no_strand=True) == geo.RIGHT
