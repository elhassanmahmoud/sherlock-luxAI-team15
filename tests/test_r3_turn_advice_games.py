import pytest

from scripts.r3_turn_advice_games import eligibility, turn_count


def test_turn_count_requires_explicit_whole_number_and_consistent_totals():
    for explicit in (0, 1, 3):
        assert turn_count({"study":{"turn_extra_played":explicit, "movement":3, "changed_unit_orders":3}}) == explicit
    for counters in (
        {"movement":3, "changed_unit_orders":3},
        {"turn_extra_played":False, "movement":3, "changed_unit_orders":3},
        {"turn_extra_played":1.0, "movement":3, "changed_unit_orders":3},
        {"turn_extra_played":-1, "movement":3, "changed_unit_orders":3},
        {"turn_extra_played":4, "movement":3, "changed_unit_orders":3},
        {"turn_extra_played":1, "movement":3, "changed_unit_orders":2},
    ):
        with pytest.raises((ValueError, KeyError, TypeError)):
            turn_count({"study":counters})


def report(external=1, solution=0, failed_gate=None):
    gates = {name:name != failed_gate for name in
             ("solution_at_least_reference","direct_majority","two_additional_external_wins")}
    return {
        "gates":gates, "game_gates_pass":all(gates.values()),
        "external":{"net_wins":2 if gates["two_additional_external_wins"] else 1},
        "by_opponent":{"solution92":{"net_wins":0 if gates["solution_at_least_reference"] else -1}},
        "direct":{"winrate":.625 if gates["direct_majority"] else .5},
        "against_r3":{"external":{"net_wins":external},"by_opponent":{"solution92":{"net_wins":solution}}},
    }


@pytest.mark.parametrize("external,solution,totals,passed", [
    (1,0,(1,1),True), (0,1,(1,1),False), (1,-1,(1,1),False),
    (1,0,(0,5),False), (1,0,(5,0),False),
])
def test_screen_requires_r3_improvement_and_both_seats(external,solution,totals,passed):
    checks = eligibility(report(external,solution),dict(zip(("player_0","player_1"),totals)))
    assert all(checks.values()) is passed


@pytest.mark.parametrize("failed_gate", ["solution_at_least_reference","direct_majority","two_additional_external_wins"])
def test_v14_gates_are_individually_binding(failed_gate):
    checks = eligibility(report(external=7,solution=2,failed_gate=failed_gate),{"player_0":3,"player_1":2})
    assert checks[failed_gate] is False
    assert not all(checks.values())
