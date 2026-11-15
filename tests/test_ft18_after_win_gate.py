from copy import deepcopy
from types import SimpleNamespace

import pytest

from scripts import ft18_after_win_gate as gate


def test_exact_registered_panels():
    def keys(stage, side):
        a = gate.spec(stage, side)
        return {(seed, seat, opp) for seed in range(a.first, a.first + a.maps) for seat in (0, 1)
                for opp in a.opponents.split(",")}
    screen = keys("screen", "candidate")
    control = keys("screen", "v14")
    confirm = keys("confirm", "candidate")
    direct = keys("confirm", "direct")
    assert len(screen) == 96 and len(control) == 64 and control == {k for k in screen if k[2] != "v14"}
    assert {k[0] for k in screen} == set(range(7279000, 7279016))
    assert confirm == keys("confirm", "v14") and len(confirm) == 240
    assert {k[0] for k in confirm} == set(range(7279100, 7279160))
    assert len(direct) == 120 and {k[0] for k in direct} == set(range(7279200, 7279260))
    with pytest.raises(ValueError):
        gate.spec("screen", "direct")


def report(solution=3, kaggle=-1, direct=17/32, lower=(.01, .01, .51)):
    return {"by_opponent": {"kaggle3": {"net_wins": kaggle},
                            "solution92": {"net_wins": solution, "difference_ci95": [lower[1], .2]}},
            "external": {"net_wins": kaggle + solution, "difference_ci95": [lower[0], .2]},
            "direct": {"winrate": direct, "winrate_ci95": [lower[2], .8]}}


def test_strict_gate_boundaries():
    assert all(gate.gates("screen", report()).values())
    for alternative in (report(0, 3), report(4, -2), report(1, 0), report(direct=.5)):
        assert not all(gate.gates("screen", alternative).values())
    assert all(gate.gates("confirm", report()).values())
    for limits in ((0, .01, .51), (.01, 0, .51), (.01, .01, .50)):
        assert not all(gate.gates("confirm", report(lower=limits)).values())


def test_seat_aware_prefix_and_no_switch_check():
    candidate = dict(candidate=gate.ARM, side="player_1", first_won=False,
                     movement_changes_by_match=[0, 0, 0], wins=1, losses=2, result=0, points=11, opp_points=20,
                     first_match=dict(steps=101, actions_sha256="c"*64, wins_world=[1, 0], points_world=[5, 2]))
    gate.check_first_match(candidate)
    control = deepcopy(candidate)
    control["candidate"] = "v14"
    key = ("kaggle3", 7279001, "player_1")
    pair = SimpleNamespace(games={key: control}), SimpleNamespace(games={key: candidate})
    gate.compare_prefixes(*pair)
    candidate["movement_changes_by_match"] = [0, 1, 0]
    with pytest.raises(ValueError, match="routing"):
        gate.check_first_match(candidate)
    candidate["movement_changes_by_match"] = [0, 0, 0]
    candidate["points"] += 1
    with pytest.raises(ValueError, match="unchanged"):
        gate.compare_prefixes(*pair)
    candidate["first_match"]["actions_sha256"] = "a"*64
    with pytest.raises(ValueError, match="first-match actions"):
        gate.compare_prefixes(*pair)


def test_failed_original_selection_blocks_confirmation(monkeypatch, tmp_path):
    monkeypatch.setattr(gate, "phase_report", lambda *_: ({"game_gates_pass": False, "gates": {}}, None))
    with pytest.raises(ValueError, match="did not nominate"):
        gate.nomination(tmp_path)
