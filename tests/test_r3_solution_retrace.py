import numpy as np
from types import SimpleNamespace

from scripts.r3_solution_retrace import changes, endpoint


def test_actual_player_one_holder_departs_and_unaffordable_order_does_not_move():
    # Public origin (3,1) maps to the V14 canonical holder (2,0) on this 4x4 board.
    tiles = np.zeros((4, 4), int)
    obs = {"units_mask": [[False], [True]], "units": {"position": [[[0, 0]], [[3, 1]]],
           "energy": [[[0]], [[8]]]}, "map_features": {"tile_type": tiles}}
    actor = SimpleNamespace(team_id=1, env_cfg={"unit_move_cost": 3},
                            belief=SimpleNamespace(mirrored=True), _prev_ctx={"first_on_tile": {(2, 0): 0}})
    known = np.zeros_like(tiles, bool)
    known[3, 1] = True
    events = changes(actor, obs, np.array([[0, 0, 0]]), np.array([[4, 0, 0]]), known)
    assert len(events) == 1
    assert events[0]["leaves_holder_v14_would_keep"] and events[0]["r3_intended"] == (2, 1)
    assert endpoint([4, 0, 0], [3, 1], 2, 3, tiles) == (3, 1)
    tiles[2, 1] = 2
    assert endpoint([4, 0, 0], [3, 1], 8, 3, tiles) == (3, 1)
