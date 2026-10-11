"""Aktionsmaske (Rand, Asteroid, Energie, Sap ohne Ziel) und Aktionsausgabe je Seite."""
import numpy as np
import pytest
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.main import Agent_x
from tests.conftest import ENV_CFG, H, W, make_obs


def ctx_for(x, y, energy, asteroids=()):
    passable = np.ones((W, H), dtype=bool)
    for ax, ay in asteroids:
        passable[ax, ay] = False
    pos = np.full((16, 2), -1)
    pos[0] = (x, y)
    ene = np.zeros(16)
    ene[0] = energy
    return dict(W=W, H=H, ally_pos=pos, ally_ene=ene, passable=passable,
                move_cost=3.0, sap_cost=40.0)


@pytest.fixture
def agent():
    a = Agent_x("player_0", train=False)
    a.set_env_cfg(ENV_CFG)
    return a


def test_map_edge_is_masked(agent):
    m = agent._action_mask(ctx_for(0, 0, 100), 0, None)
    assert m[geo.STAY] and not m[geo.UP] and not m[geo.LEFT]
    assert m[geo.RIGHT] and m[geo.DOWN]
    m = agent._action_mask(ctx_for(W - 1, H - 1, 100), 0, None)
    assert not m[geo.RIGHT] and not m[geo.DOWN]


def test_asteroid_is_masked(agent):
    m = agent._action_mask(ctx_for(5, 5, 100, asteroids=[(6, 5), (5, 4)]), 0, None)
    assert not m[geo.RIGHT] and not m[geo.UP]
    assert m[geo.LEFT] and m[geo.DOWN]


def test_too_little_energy_only_allows_stay(agent):
    m = agent._action_mask(ctx_for(5, 5, 2), 0, (1, 1, 1))
    assert m.tolist() == [True, False, False, False, False, False]


def test_sap_needs_target_and_energy(agent):
    assert not agent._action_mask(ctx_for(5, 5, 100), 0, None)[geo.SAP]
    assert agent._action_mask(ctx_for(5, 5, 100), 0, (2, 0, 1))[geo.SAP]
    assert not agent._action_mask(ctx_for(5, 5, 39), 0, (2, 0, 1))[geo.SAP]


def test_no_sap_variant_has_five_actions():
    from agents.sherlock.config import AgentConfig
    a = Agent_x("player_0", cfg=AgentConfig(use_sap=False), train=False)
    assert a.n_actions == 5
    assert len(a._action_mask(ctx_for(5, 5, 100), 0, None)) == 5


class FixedQ(torch.nn.Module):
    def __init__(self, best: int, n: int = 6):
        super().__init__()
        self.best, self.n = best, n

    def forward(self, x):
        q = torch.zeros(x.shape[0], self.n)
        q[:, self.best] = 1.0
        return q


@pytest.mark.parametrize("team,start", [(0, (5, 5)), (1, (18, 18))])
def test_act_translates_canonical_choice_to_real_move(team, start):
    """Wählt das Netz kanonisch 'right', bewegt sich die Unit im echten Raum so,
    dass die kanonische Position um +1 in x wandert - fuer BEIDE Seiten."""
    a = Agent_x(f"player_{team}", train=False)
    a.set_env_cfg(ENV_CFG)
    a.set_to_eval_mode()
    a.q = FixedQ(geo.RIGHT)
    obs = make_obs(10, 10, team=team, units=[(*start, 100)])
    act = a.act(10, obs)
    d = int(act[0, 0])
    real_next = (start[0] + geo.DIR_DX[d], start[1] + geo.DIR_DY[d])
    canon = geo.mirror_xy(*start) if team else start
    canon_next = geo.mirror_xy(*real_next) if team else real_next
    assert canon_next == (canon[0] + 1, canon[1])


def test_explore_memory_prefers_never_seen_tiles():
    import numpy as np
    from agents.sherlock.belief import Belief
    from agents.sherlock.features import assign_targets
    b = Belief(0)
    b.explored_ever[:, :12] = True        # obere Haelfte frueher schon gesehen
    unit = np.array([[5, 11]])
    old = assign_targets(b, [0], unit, 24, 24)
    new = assign_targets(b, [0], unit, 24, 24, seen_before_penalty=300.0)
    assert old[0][1] <= 11 or old[0] == (5, 12)   # ohne Malus: naechstes Tile
    assert new[0][1] >= 12                        # mit Malus: nie gesehenes Gebiet
