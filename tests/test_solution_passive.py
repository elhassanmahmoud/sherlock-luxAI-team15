from types import SimpleNamespace

import numpy as np
import pytest

from scripts.solution_passive import ScoreObserver, finish_match, occupied, score_frame


def example():
    # Team 0 has two units on one owned field and a negative unit on a different field.
    pos = np.array([[[0,0],[0,0],[1,1]], [[2,2],[1,2],[2,1]]])
    energy = np.array([[[5],[4],[-8]], [[1],[1],[99]]])
    mask = np.array([[1,1,1],[1,1,0]], bool)
    weights = np.zeros((3,3), int)
    for x,y in [(0,0),(1,1),(2,2),(1,2)]:
        weights[x,y] = 1
    state = SimpleNamespace(units=SimpleNamespace(position=pos, energy=energy),
                            units_mask=mask, relic_nodes_map_weights=weights,
                            relic_nodes_mask=np.array([True,True]), team_wins=np.array([1,1]))
    def obs(t, ms, points, wins):
        value = dict(steps=t, match_steps=ms, team_points=np.array(points), team_wins=np.array(wins),
                     units_mask=mask, units=dict(position=pos, energy=energy))
        return {"player_0":value,"player_1":value}
    return obs(201,100,[1,0],[1,0]), obs(202,0,[0,0],[1,1]), {"final_state":state}


def test_terminal_fields_include_last_gain_and_raw_negative_energy_in_tiebreak():
    before, after, info = example()
    assert occupied(info["final_state"]) == ([[(0,0)],[(1,2),(2,2)]], [1,2])
    frame = score_frame(before, after, info)
    assert frame["points_before"] == [1,0] and frame["points_after"] == [2,2]
    assert frame["points_gained"] == [1,2]
    assert frame["match_end"] == dict(winner=1, decided_by="energy_tiebreak",final_energy=[1,2])
    assert finish_match([0,0],[1,0],[3,3],[0,0])["decided_by"] == "engine_lot_after_double_tie"
    with pytest.raises(ValueError):
        finish_match([0,0],[0,1],[2,1],[0,8])


def test_passive_wrapper_preserves_exact_argument_and_result_objects():
    before, after, info = example()
    reset_result = before, {"params": {}}
    step_result = after, {}, {}, {}, info
    commands = {"player_0": np.zeros((3,3))}
    def fake_step(received):
        assert received is commands
        return step_result
    wrapper = ScoreObserver(SimpleNamespace(reset=lambda **kw: reset_result, step=fake_step))
    obs, meta = wrapper.reset(seed=42)
    assert obs is before and meta is reset_result[1]
    assert wrapper.step(commands) is step_result
    assert len(wrapper.frames) == 1


def test_match_trace_reports_points_on_last_step(monkeypatch):
    from agents.sherlock import main as sherlock
    from luxai_s3 import wrappers
    from scripts import common, experiment, match_trace, par_eval

    before, after, info = example()
    class Dummy:
        def __init__(self, *args, **kwargs): pass
        def set_to_eval_mode(self): pass
        def act(self, **kwargs): return np.zeros((3,3),int)
    fake = SimpleNamespace(reset=lambda **kw:(before,{"params":{}}),
                           step=lambda actions:(after, {}, {"player_0":True},{"player_0":False},info),
                           close=lambda:None)
    monkeypatch.setattr(wrappers, "LuxAIS3GymEnv", lambda **kw:fake)
    monkeypatch.setattr(sherlock, "Agent_x", Dummy)
    monkeypatch.setattr(common, "make_opponent", lambda *args:Dummy())
    monkeypatch.setattr(par_eval, "build_cfg", lambda *args:None)
    monkeypatch.setattr(experiment, "limit_threads", lambda:None)
    [row] = match_trace.play(("unused", [], "solution92", 7, "player_0"))
    assert [row["our_points"],row["opp_points"]] == [2,2]
    assert row["opp_first_point"] == 101
