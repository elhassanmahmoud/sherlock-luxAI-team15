"""Matchende-Sturm (imit_end_fill) und Taktikschicht (imit_tactics) im Imitations-Schüler (17.11.2026, abends)."""
from types import SimpleNamespace

import numpy as np
import pytest

from agents.sherlock import geometry as geo
from agents.sherlock.imitation_agent import ImitationAgent
from agents.sherlock.tactics_layer import TacticsCfg


def _fake(points):
    return SimpleNamespace(belief=SimpleNamespace(point_tiles=points), ep_stats={})


def _ctx(match_step, first=None, enemies=()):
    return {"match_step": match_step, "max_match_steps": 100.0, "first_on_tile": first or {},
            "enemy_coords": np.array(enemies, dtype=int).reshape(-1, 2)}


def test_end_fill_waits_for_the_end_phase():
    points = np.zeros((24, 24), dtype=bool)
    points[5, 5] = True
    acts = np.array([geo.STAY])
    out = ImitationAgent._end_fill(_fake(points), _ctx(80), [0], np.array([[3, 5]]), np.zeros((1, 6)), acts, 10)
    assert out.tolist() == [geo.STAY]
    # Ab 10 verbleibenden punktenden Schritten (match_steps 91..100) greift die Regel
    out = ImitationAgent._end_fill(_fake(points), _ctx(91), [0], np.array([[3, 5]]), np.zeros((1, 6)), acts, 10)
    assert out.tolist() == [geo.RIGHT]


def test_end_fill_keeps_holders_and_sends_nearest_free_unit():
    points = np.zeros((24, 24), dtype=bool)
    points[5, 5] = points[10, 10] = True
    ids = [0, 1, 2]
    pos = np.array([[5, 5], [10, 7], [10, 15]])  # Unit 0 hält (5, 5); (10, 10) ist frei
    logp = np.zeros((3, 6), dtype=np.float32)
    logp[1, geo.DOWN] = -0.5  # verkleinert den Abstand
    logp[1, geo.LEFT] = -0.1  # besser bewertet, verkleinert ihn aber nicht
    acts = np.array([geo.LEFT, geo.LEFT, geo.STAY])  # der Halter will weg
    fake = _fake(points)
    out = ImitationAgent._end_fill(fake, _ctx(95, first={(5, 5): 0}), ids, pos, logp, acts, 10)
    assert out.tolist() == [geo.STAY, geo.DOWN, geo.STAY]  # Unit 2 ist weiter weg (5 statt 3)
    assert fake.ep_stats == {"end_hold": 1, "end_fill_moves": 1}
    assert acts.tolist() == [geo.LEFT, geo.LEFT, geo.STAY]  # Eingabe bleibt unverändert


def test_end_fill_respects_remaining_steps_shooters_enemies_and_claimed_tiles():
    points = np.zeros((24, 24), dtype=bool)
    points[5, 5] = True
    logp = np.zeros((1, 6), dtype=np.float32)
    # Letzter punktender Schritt (match_steps 100): nur noch Abstand 1 lohnt
    assert ImitationAgent._end_fill(_fake(points), _ctx(100), [0], np.array([[4, 5]]), logp, np.array([0]),
                                    10).tolist() == [geo.RIGHT]
    assert ImitationAgent._end_fill(_fake(points), _ctx(100), [0], np.array([[3, 5]]), logp, np.array([0]),
                                    10).tolist() == [geo.STAY]
    # Schützen bleiben Schützen; Felder mit sichtbarem Gegner gelten nicht als frei
    assert ImitationAgent._end_fill(_fake(points), _ctx(95), [0], np.array([[3, 5]]), logp, np.array([geo.SAP]),
                                    10).tolist() == [geo.SAP]
    assert ImitationAgent._end_fill(_fake(points), _ctx(95, enemies=[(5, 5)]), [0], np.array([[3, 5]]), logp,
                                    np.array([0]), 10).tolist() == [geo.STAY]
    # Eine Unit zieht schon auf das Feld: keine zweite, und die erste wird nicht umgeleitet
    two = np.zeros((2, 6), dtype=np.float32)
    out = ImitationAgent._end_fill(_fake(points), _ctx(95), [0, 1], np.array([[4, 5], [5, 7]]), two,
                                   np.array([geo.RIGHT, geo.STAY]), 10)
    assert out.tolist() == [geo.RIGHT, geo.STAY]
    # Gesperrte Annäherung: nichts ändern
    blocked = np.zeros((1, 6), dtype=np.float32)
    blocked[0, geo.RIGHT] = -np.inf
    assert ImitationAgent._end_fill(_fake(points), _ctx(95), [0], np.array([[4, 5]]), blocked, np.array([0]),
                                    10).tolist() == [geo.STAY]


def test_tactics_spec_accepts_plus_separator_and_rejects_unknown_switch():
    cfg = TacticsCfg.parse("granate+nebel+sog_vf=0.375")
    assert cfg.granate and cfg.nebel and cfg.sog_vf == 0.375 and not cfg.sog
    with pytest.raises(ValueError):
        TacticsCfg.parse("schueler=ens8")  # gibt es nur in der R3T-Schicht


def _student_game(cfg_updates, steps=120, seed=7256950):
    from dataclasses import replace

    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.config import AgentConfig
    from agents.sherlock.main import Agent_x
    from agents.sherlock_r3t.agent import STUDENTS
    from scripts.common import make_opponent

    path = STUDENTS["ens9"]
    if not path.is_file():
        pytest.skip("Schülergewichte liegen nur lokal vor")
    base = {"imit_stay_bias": 1.0, "imit_unstack": True, "imit_hold_points": True}
    cfg = replace(Agent_x._cfg_from_checkpoint(str(path)) or AgentConfig(), **{**base, **cfg_updates})
    me = ImitationAgent("player_1", agent_path=str(path), cfg=cfg, train=False)
    me.set_to_eval_mode()
    opp = make_opponent("solution92", "player_0")
    env = LuxAIS3GymEnv(numpy_output=True)
    obs, info = env.reset(seed=seed)
    for a, side in ((me, "player_1"), (opp, "player_0")):
        if hasattr(a, "new_game"):
            a.new_game(side)
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(info["params"])
    actions = []
    for step in range(steps):
        act = {"player_1": me.act(step, obs["player_1"]), "player_0": opp.act(step, obs["player_0"])}
        actions.append(np.asarray(act["player_1"]).copy())
        obs, *_ = env.step(act)
    env.close()
    return me, actions


def test_switches_off_play_like_before_and_switches_on_act_in_a_real_game():
    off, a_off = _student_game({})
    empty, a_empty = _student_game({"imit_tactics": "", "imit_end_fill": 0})
    assert all(np.array_equal(x, y) for x, y in zip(a_off, a_empty))
    assert getattr(off, "_tactics", None) is None and "tactics_units" not in off.ep_stats
    end, a_end = _student_game({"imit_end_fill": 10})
    assert end.ep_stats.get("end_hold", 0) + end.ep_stats.get("end_fill_moves", 0) > 0
    # Vor der Endphase des ersten Matches (match_steps 91) spielt der Matchende-Sturm wie ohne Schalter
    assert all(np.array_equal(x, y) for x, y in zip(a_off[:91], a_end[:91]))
    tac, _ = _student_game({"imit_tactics": "granate+nebel+sog+sparen+wechsel+erobern+tanken"})
    assert tac.ep_stats.get("tactics_units", 0) > 0
    assert sum(tac._tactics.counts.values()) > 0
