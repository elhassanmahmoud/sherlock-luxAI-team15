import numpy as np
import pytest

from scripts.r3_v4_wl_games import Record, SEATS, verify_pair


class Boundary:
    def reset(self):
        return {s:{"match_steps":99,"team_wins":[0,0]} for s in SEATS}, {}

    def step(self, actions):
        obs = {s:{"match_steps":100,"team_wins":[0,0]} for s in SEATS}
        return obs,{},dict.fromkeys(SEATS,False),dict.fromkeys(SEATS,False),{}


def test_prefix_records_both_actual_seats_before_match_three():
    from hashlib import sha256
    env = Record(Boundary(), "player_1")
    env.reset()
    env.steps = 200
    commands = {s:np.zeros((16,3),np.int16) for s in SEATS}
    commands["player_1"][5,0] = 2
    env.step(commands)
    assert not env.prefix

    # The second step is an official boundary. Make engine bookkeeping explicit without a real game.
    def boundary_step(actions):
        obs = {s:{"match_steps":1,"team_wins":[1,0],"team_points":[10,2]} for s in SEATS}
        return obs,{},dict.fromkeys(SEATS,False),dict.fromkeys(SEATS,False),{}
    env.env.step = boundary_step
    env.step(commands)
    assert env.prefix == {s:sha256(commands[s].astype("<i8").tobytes()*2).hexdigest() for s in SEATS}

    before = env.prefix.copy()
    env.env.step = lambda actions: ({s:{"match_steps":2,"team_wins":[1,0]} for s in SEATS},
                                    {},dict.fromkeys(SEATS,False),dict.fromkeys(SEATS,False),{})
    commands["player_0"][3,0] = 4
    env.step(commands)
    assert env.prefix == before
    assert env.commands() != env.prefix


def test_unswitched_full_stream_and_wl_prefix():
    from copy import deepcopy
    base = dict(prefix_sha256=dict.fromkeys(SEATS,"prefix"),commands_sha256=dict.fromkeys(SEATS,"full"),
                sequence="LWW",matches=[0,1,1])
    changed = deepcopy(base)
    changed["commands_sha256"]["player_1"] = "different"
    with pytest.raises(ValueError,match="Untreated"):
        verify_pair(base,changed)
    base["sequence"] = "WLW"
    changed["matches"][2] = 0
    verify_pair(base,changed)
    changed["prefix_sha256"]["player_0"] = "another prefix"
    with pytest.raises(ValueError,match="First two"):
        verify_pair(base,changed)
