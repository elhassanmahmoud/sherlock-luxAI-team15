"""Reward: Stacking-Strafe, Vorzeichen des Potential-Shapings, Matchgrenze."""
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from agents.team_lux.config import AgentConfig
from agents.team_lux.reward import unit_rewards
from tests.conftest import H, W

ZERO = dict(w_point=0.0, w_shape=0.0, w_explore=0.0, w_energy=0.0, w_stack=0.0,
            w_death=0.0, w_match=0.0, w_discovery=0.0, w_sap_hit=0.0)


def only(**w):
    return replace(AgentConfig(), **{**ZERO, **w})


def ctx(units, point_tiles=(), assigned=None, wins=(0, 0)):
    pos = np.full((16, 2), -1)
    ene = np.zeros(16)
    first = {}
    for uid, (x, y) in units.items():
        pos[uid] = (x, y)
        ene[uid] = 100
        first.setdefault((x, y), uid)
    pt = np.zeros((W, H), dtype=bool)
    for x, y in point_tiles:
        pt[x, y] = True
    return dict(ally_ids=np.array(sorted(units)), ally_pos=pos, ally_ene=ene,
                first_on_tile=first, point_tiles=pt, W=W, H=H,
                assigned=assigned or {}, own_wins=wins[0], opp_wins=wins[1],
                belief=SimpleNamespace(newly_explored=0, newly_proven=0))


def test_stacking_penalty_only_for_redundant_unit():
    cfg = only(w_point=1.0, w_stack=0.3)
    c0 = ctx({0: (4, 4), 1: (6, 6)}, point_tiles=[(5, 5)])
    c1 = ctx({0: (5, 5), 1: (5, 5)}, point_tiles=[(5, 5)])
    r = unit_rewards(cfg, c0, c1, {}, {})
    assert r[0] == pytest.approx(1.0)
    assert r[1] == pytest.approx(-0.3)


def test_potential_shaping_sign():
    cfg = only(w_shape=1.0)
    tgt = {0: (10, 10)}
    far, near = ctx({0: (2, 2)}, assigned=tgt), ctx({0: (3, 2)}, assigned=tgt)
    assert unit_rewards(cfg, far, near, {}, {})[0] > 0   # naeher ran
    assert unit_rewards(cfg, near, far, {}, {})[0] < 0   # weg vom Ziel


def test_potential_shaping_telescopes_on_loop():
    """Hin und zurueck ergibt (mit gamma=1) netto 0 - kein Belohnungs-Farming."""
    cfg = replace(only(w_shape=1.0), gamma=1.0)
    tgt = {0: (10, 10)}
    a, b = ctx({0: (2, 2)}, assigned=tgt), ctx({0: (3, 2)}, assigned=tgt)
    total = unit_rewards(cfg, a, b, {}, {})[0] + unit_rewards(cfg, b, a, {}, {})[0]
    assert total == pytest.approx(0.0)


@pytest.mark.parametrize("shaping", [True, False])
def test_match_reward_only_when_wins_change(shaping):
    """Env-Reward ist team_wins kumulativ; belohnt wird nur der Step des Sieges."""
    cfg = replace(only(w_match=2.0), use_shaping=shaping)
    after_win = ctx({0: (1, 1)}, wins=(1, 0))
    later = ctx({0: (1, 2)}, wins=(1, 0))
    assert unit_rewards(cfg, ctx({0: (1, 1)}, wins=(0, 0)), after_win, {}, {})[0] == 2.0
    assert unit_rewards(cfg, after_win, later, {}, {})[0] == 0.0
    assert unit_rewards(cfg, after_win, ctx({0: (1, 1)}, wins=(1, 1)), {}, {})[0] == -2.0


def test_no_shaping_keeps_only_points_and_match():
    cfg = replace(AgentConfig(), use_shaping=False)
    c0 = ctx({0: (4, 4), 1: (6, 6), 2: (9, 9)}, point_tiles=[(5, 5)], assigned={2: (20, 20)})
    c1 = ctx({0: (5, 5), 1: (5, 5), 2: (10, 9)}, point_tiles=[(5, 5)], assigned={2: (20, 20)})
    r = unit_rewards(cfg, c0, c1, {}, {})
    assert r == {0: cfg.w_point, 1: 0.0, 2: 0.0}


def test_match_boundary_transitions_in_real_game(env):
    """Am echten Env: kein Uebergang ab match_step 0 (Reste des alten Matches,
    sonst falsche Tod-Strafe) und Matchende beendet die Unit-Episode."""
    from agents.team_lux.main import Agent_x
    from agents.default.default import DefaultAgent
    from scripts.common import play_game

    a = Agent_x("player_0", cfg=replace(AgentConfig(), learn_start=10**9), seed=0)
    pushed = []
    orig = a.buffer.push

    def spy(s, act, r, ns, done, mask):
        pushed.append((a._prev_ctx["match_step"], done))
        orig(s, act, r, ns, done, mask)

    a.buffer.push = spy
    play_game(env, a, DefaultAgent("player_1"), seed=3, our_side="player_0", train=True)
    steps = {ms for ms, _ in pushed}
    assert 0 not in steps
    assert all(done for ms, done in pushed if ms == 100)
