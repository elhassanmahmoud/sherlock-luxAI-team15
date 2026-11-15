"""Synthetic public transitions, including a nonpublic terminal energy tiebreak."""
import json
from types import SimpleNamespace

import numpy as np
import pytest

from scripts.r3_solution_observation import Observation


def recorded_game(first_score=30):
    observer = Observation(1)
    pos = np.zeros((2, 4, 2), dtype=int)
    ene = np.zeros((2, 4), dtype=int)
    mask = np.zeros((2, 4), dtype=bool)
    points = np.zeros(2, dtype=int)
    wins = np.zeros(2, dtype=int)
    tile = np.zeros((3, 3), dtype=int)
    tile[1, 0] = 1

    def public(t):
        # The observer is player_1 and never sees the opponent in this fixture.
        visible = mask.copy()
        visible[0] = False
        return dict(steps=t, match_steps=t % 101, team_points=points.copy(), team_wins=wins.copy(),
                    units_mask=visible, units=dict(position=np.where(visible[..., None], pos, -1),
                                                   energy=np.where(visible, ene, -1)))

    for t in range(303):
        match, m = divmod(t, 101)
        before = public(t)
        known = (tile > 0) if t >= 33 else np.zeros_like(tile, bool)
        if m == 0:
            mask[:] = False
            mask[:, 0] = True
            pos[:, 0] = (1, 1)
            ene[:, 0] = 6
            if match == 0:
                mask[1, 1:] = True
                ene[1, 1:] = 3
                pos[1, 1:] = (0, 0)
            if match == 1:
                mask[1, 1] = True
                ene[1, 1] = 1
                pos[1, 1] = (0, 0)
                ene[0, 0] = 2
        if match == 0:
            if m == 8:
                ene[1, 1] = -1
            if m == 9:
                mask[1, 1] = False
            if m == first_score:
                pos[1, 0] = (1, 0)
            if first_score < 33 and m in (33, 34):
                pos[1, 0] = (1, 1) if m == 33 else (1, 0)
            if m == 65:
                pos[1, 2] = (2, 2)  # immediate slot replacement at player_1's spawn
            if m == 67:
                mask[1, 3] = False
            if tuple(pos[1, 0]) == (1, 0):
                points[1] += 1
        if match == 1 and m == 100:
            ene[1, 1] = -8  # still masked; counts for the final energy sum
        info = {}
        if m == 100:
            wins[1 if match == 0 else 0] += 1
            info["final_state"] = SimpleNamespace(
                relic_nodes_map_weights=tile, relic_nodes_mask=np.ones(2, bool), units_mask=mask.copy(),
                units=SimpleNamespace(position=pos.copy(), energy=ene[..., None].copy()))
            points[:] = 0
        observer.record(before, public(t + 1), info, known)
    return observer.report()


def test_proof_is_pre_action_public_and_retained_across_matches():
    report = recorded_game()
    first, second, third = report["matches"]
    assert first["first_own_point_gain"] == dict(global_step=30, match_step=30, gain=1, source="public_score")
    assert first["first_confirmed"]["global_step"] == 33
    assert not first["first_confirmed"]["inherited_from_previous_match"]
    for key, step in (("first_known_occupied_before", 33), ("first_known_occupied_after", 34),
                      ("first_known_held_through_action", 35)):
        assert first[key] == dict(global_step=step, match_step=step, world_cells=[[1, 0]])
    for row in (second, third):
        assert row["first_confirmed"]["match_step"] == 0 and row["first_confirmed"]["inherited_from_previous_match"]
        assert row["first_known_occupied_before"] is None
        assert row["first_known_occupied_after"] is None
    assert list(first["sections"][s]["steps"] for s in ("boundary_0", "1-33", "34-66", "67-100")) == [1, 33, 33, 34]
    assert first["sections"]["boundary_0"]["mean_active_units"] == 4
    assert first["sections"]["boundary_0"]["mean_team_active_energy"] == 15
    assert first["sections"]["1-33"]["newly_negative"] == 1
    assert first["sections"]["34-66"]["detectable_slot_reuses"] == 1
    assert first["sections"]["67-100"]["mask_losses"] == 1
    assert first["summary"]["plausible_uid_departures"] == 3
    assert second["sections"]["boundary_0"]["plausible_uid_departures"] == 0
    json.dumps(report, allow_nan=False)


def test_official_winner_final_score_and_both_tiebreaks():
    report = recorded_game()
    points, energy, lottery = (r["final"] for r in report["matches"])
    assert report["team_points_total"] == [0, 70]
    assert points["team_points"] == [0, 70] and points["decided_by"] == "points" and points["own_won"]
    assert energy["winner"] == 0 and energy["decided_by"] == "energy_tiebreak" and energy["final_energy"] == [2, -2]
    assert lottery["winner"] == 0 and lottery["decided_by"] == "engine_lot_after_double_tie"
    with pytest.raises(ValueError, match="complete game"):
        Observation(0).report()


def test_first_score_on_last_action_marks_external_reconstruction():
    match = recorded_game(first_score=100)["matches"][0]
    assert match["first_own_point_gain"] == dict(global_step=100, match_step=100, gain=1, source="external_final_score")
    assert match["final"]["team_points"] == [0, 1]
