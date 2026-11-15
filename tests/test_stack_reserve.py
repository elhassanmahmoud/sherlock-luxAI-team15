from collections import Counter
from types import SimpleNamespace

import numpy as np
import pytest

from agents.sherlock.main import Agent_x
from scripts.stack_reserve import StackReserveAgent, held_movers


def observation(positions, energies, masks=None):
    # Seat 0 occupies distinct cells. The stack under test belongs to seat 1.
    n = len(positions)
    other = [(i, 0) for i in range(n)]
    return dict(match_steps=5, units=dict(position=np.array([other, positions]),
                energy=np.array([[90] * n, energies])),
                units_mask=np.array([[True] * n, masks if masks is not None else [True] * n]),
                map_features={"tile_type": np.zeros((24, 24), dtype=int)})


@pytest.mark.parametrize("energy,held", [
    ([12], []), ([0, 8], [0]), ([4, 14, 4], [0, 2]), ([9, 9, 9, 9], [2, 3]),
    ([100, 50, 0, -1], [2]),
])
def test_rank_all_public_units_by_energy_then_uid(energy, held):
    obs = observation([(19, 4)] * len(energy), energy)
    base = np.tile([2, 0, 0], (len(energy), 1))
    assert sorted(held_movers(obs, 1, base)) == held
    assert held_movers(obs, 0, base) == []


def test_excluded_slots_and_existing_saps_or_stays():
    # A masked-out (high energy) slot at the same world position does not count.
    # The leading SAP uses its rank; the reserve cannot take the unused permission.
    obs = observation([(18, 5)] * 3 + [(9, 7)] * 2, [80, 12, 90, 5, 4],
                      [True, True, False, True, True])
    base = np.array([[5, -1, 2], [3, 0, 0], [2, 0, 0], [2, 0, 0], [0, 0, 0]])
    assert held_movers(obs, 1, base) == [1]
    obs["units_mask"][1, 0] = False
    assert held_movers(obs, 1, base) == []  # The only friendly ship left at (18, 5) may move.
    obs["units_mask"][1, 0] = True
    base[1] = [5, 2, -1]
    assert held_movers(obs, 1, base) == []


def test_executed_world_stay_and_accounting_in_seat_one(monkeypatch):
    actor = object.__new__(StackReserveAgent)
    actor.training, actor.team_id = False, 1
    actor.belief = SimpleNamespace(mirrored=True)
    actor.cfg = SimpleNamespace(frozen=False, nebula_avoid=True, rules_in_training_all=False,
                                dodge_verify=False, dodge_distrust=0, dodge_shape=False)
    actor._prev_actions = {0:5, 1:2}
    actor._sap_hits, actor._sap_unknown = {0:1}, {0}
    actor._prev_ctx, actor.env_cfg, actor.study_stats = {}, {}, Counter()
    actor.ep_stats = dict(sap_attempts=1, sap_hits_est=1)
    remembered = []
    actor.param_est = SimpleNamespace(observe=lambda *args: None,
                                      remember=lambda obs, team, actions: remembered.append(actions.tolist()))
    obs = observation([(22, 1)] * 2, [35, 5])
    base = np.array([[5, -1, 1], [1, 0, 0]])
    monkeypatch.setattr(Agent_x, "_act", lambda *args: base)
    played = actor.act(5, obs)
    assert played.tolist() == [[5, -1, 1], [0, 0, 0]]
    assert remembered == [played.tolist()] and base[1, 0] == 1
    assert actor._prev_actions == {0:5, 1:0}
    assert actor._sap_hits == {0:1} and actor._sap_unknown == {0}
    assert actor.study_stats["changed_unit_orders"] == actor.study_stats["movement"] == 1
    assert actor.ep_stats == dict(sap_attempts=1, sap_hits_est=1)
    obs["match_steps"] = 0
    assert actor._act(6, obs) is base
