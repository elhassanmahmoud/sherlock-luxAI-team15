import numpy as np
import pytest

from scripts.v14_packed_parity import SIDES, checked_stream, compare_case, world_orders


def test_first_opponent_difference_at_match_restart():
    a = np.zeros((303, 2, 16, 3), dtype="<i2")
    b = a.copy()
    b[101, 1, 15] = (5, -2, 3)
    same_score = {"score": {"result": 1}, "matches": []}
    result = compare_case(a, b, same_score, same_score)
    assert result["diff_steps"] == 1
    assert result["different_unit_orders"] == {"player_0": 0, "player_1": 1}
    assert result["first"] == dict(step=101, side="player_1", uid=15, native=[0, 0, 0], packed=[5, -2, 3])
    assert not result["pass"]
    assert not compare_case(a, a, same_score, dict(same_score, matches=[{}]))["pass"]


def test_preserve_both_world_arrays_and_reject_incomplete_game():
    arr = np.zeros((16, 3), dtype=int)
    arr[4] = (5, -3, 2)
    orders = world_orders({SIDES[1]: -arr, SIDES[0]: arr})
    np.testing.assert_array_equal(orders[:, 4], [[5, -3, 2], [-5, 3, -2]])
    with pytest.raises(ValueError):
        checked_stream(np.repeat(orders[None], 302, axis=0))
    with pytest.raises(ValueError):
        world_orders({SIDES[0]: arr, SIDES[1]: arr.astype(float)})
