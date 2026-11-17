"""Schalter imit_hold_points und imit_fill_points des Imitations-Schülers (17.11.2026)."""
from types import SimpleNamespace

import numpy as np
import pytest

from agents.sherlock.imitation_agent import ImitationAgent


def test_point_holder_rows_only_first_unit_on_known_point_tile():
    points = np.zeros((24, 24), dtype=bool)
    points[3, 4] = points[10, 10] = True
    fake = SimpleNamespace(belief=SimpleNamespace(point_tiles=points))
    ctx = {"first_on_tile": {(3, 4): 7, (10, 10): 2, (5, 5): 1}}
    ids = [7, 8, 1, 2]
    pos = np.array([[3, 4], [3, 4], [5, 5], [11, 10]])
    # Unit 7 ist erster Halter auf einem Punktefeld; 8 steht dort nur zusätzlich; 1 hält ein Feld ohne Punkte;
    # Unit 2 ist als Halter von (10, 10) eingetragen, steht aber woanders
    assert ImitationAgent._point_holder_rows(fake, ctx, ids, pos) == [0]


def _student_game(cfg_updates, steps=120, seed=7256950):
    from dataclasses import replace

    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock_r3t.agent import STUDENTS, STUDENT_OVERRIDES
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent

    path = STUDENTS["ens8"]
    if not path.is_file():
        pytest.skip("Schülergewichte liegen nur lokal vor")
    cfg = replace(Agent_x._cfg_from_checkpoint(str(path)) or AgentConfig(), **STUDENT_OVERRIDES, **cfg_updates)
    me = ImitationAgent("player_0", agent_path=str(path), cfg=cfg, train=False)
    me.set_to_eval_mode()
    opp = make_opponent("solution92", "player_1")
    env = LuxAIS3GymEnv(numpy_output=True)
    obs, info = env.reset(seed=seed)
    for a, side in ((me, "player_0"), (opp, "player_1")):
        if hasattr(a, "new_game"):
            a.new_game(side)
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(info["params"])
    actions = []
    for step in range(steps):
        act = {"player_0": me.act(step, obs["player_0"]), "player_1": opp.act(step, obs["player_1"])}
        actions.append(np.asarray(act["player_0"]).copy())
        obs, *_ = env.step(act)
    env.close()
    return me, actions


def test_hold_points_counts_holders_and_changes_play_only_after_first_holder():
    off, a_off = _student_game({})
    assert off.ep_stats.get("hold_points", 0) == 0
    on, a_on = _student_game({"imit_hold_points": True})
    assert on.ep_stats.get("hold_points", 0) > 0
    # Bis zum ersten Halter auf einem bekannten Punktefeld spielen beide gleich
    first = next((i for i, (x, y) in enumerate(zip(a_off, a_on)) if not np.array_equal(x, y)), None)
    assert first is None or first > 0


def _fake(points):
    return SimpleNamespace(belief=SimpleNamespace(point_tiles=points), ep_stats={})


def test_fill_points_sends_nearest_free_unit_by_best_closing_move():
    from agents.sherlock import geometry as geo

    points = np.zeros((24, 24), dtype=bool)
    points[5, 5] = True
    ids = [0, 1, 2]
    pos = np.array([[3, 5], [5, 9], [10, 10]])
    logp = np.zeros((3, 6), dtype=np.float32)
    logp[0, geo.STAY] = 0.0
    logp[0, 2] = -1.0  # rechts: verkleinert den Abstand zu (5, 5)
    logp[0, 3] = -0.1  # runter: vergrößert ihn nicht, verkleinert ihn aber auch nicht
    acts = np.array([geo.STAY, geo.STAY, geo.STAY])
    fake = _fake(points)
    out = ImitationAgent._fill_points(fake, {}, ids, pos, logp, acts, 6)
    assert out.tolist() == [2, geo.STAY, geo.STAY]  # nur die nächste Unit, mit der besten Annäherung
    assert fake.ep_stats["fill_moves"] == 1
    assert acts.tolist() == [geo.STAY] * 3  # Eingabe bleibt unverändert


def test_fill_points_skips_shooters_holders_claimed_tiles_and_illegal_moves():
    from agents.sherlock import geometry as geo

    points = np.zeros((24, 24), dtype=bool)
    points[5, 5] = points[8, 8] = points[12, 12] = True
    ids = [0, 1, 2, 3]
    # Unit 0 schießt neben (5, 5); Unit 1 steht auf dem Punktefeld (8, 8); Unit 2 zieht auf (12, 12);
    # Unit 3 steht links von (5, 5), aber der Zug nach rechts ist gesperrt
    pos = np.array([[5, 4], [8, 8], [12, 11], [4, 5]])
    logp = np.zeros((4, 6), dtype=np.float32)
    logp[3, 2] = -np.inf
    acts = np.array([geo.SAP, geo.STAY, 3, geo.STAY])
    out = ImitationAgent._fill_points(_fake(points), {}, ids, pos, logp, acts, 6)
    assert out.tolist() == acts.tolist()
    # Ohne freies Feld in Reichweite bleibt alles gleich
    far = np.zeros((24, 24), dtype=bool)
    far[20, 20] = True
    assert ImitationAgent._fill_points(_fake(far), {}, [0], np.array([[1, 1]]), np.zeros((1, 6)), np.array([0]),
                                       6).tolist() == [0]


def test_fill_points_lets_stacked_second_unit_leave_point_tile():
    from agents.sherlock import geometry as geo

    points = np.zeros((24, 24), dtype=bool)
    points[5, 5] = points[5, 7] = True
    ids = [3, 4]
    pos = np.array([[5, 5], [5, 5]])  # Unit 3 hält (5, 5), Unit 4 steht zusätzlich darauf
    logp = np.zeros((2, 6), dtype=np.float32)
    acts = np.array([geo.STAY, geo.STAY])
    out = ImitationAgent._fill_points(_fake(points), {"first_on_tile": {(5, 5): 3}}, ids, pos, logp, acts, 6)
    assert out.tolist() == [geo.STAY, 3]  # Unit 4 zieht nach unten Richtung (5, 7)
