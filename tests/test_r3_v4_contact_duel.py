from copy import deepcopy

import pytest

from scripts.r3_v4_contact_duel import MAPS, ROSTER, SEATS, compare, validate


def test_complete_map_pairing_and_whole_map_interval():
    # Alternating seat wins on every map give zero variance between map means.
    rows = {key: {"result": int(key[1] == SEATS[0]), "wins": 2 if key[1] == SEATS[0] else 1}
            for key in ROSTER}
    old = {key: {"result": int(key[0] < MAPS.start + 6), "wins": 2 if key[0] < MAPS.start + 6 else 1}
           for key in ROSTER}
    summary = compare(rows, old)
    assert (summary["contact_wins"], summary["v4_wins"]) == (24, 24)
    assert (summary["contact_match_wins"], summary["v4_match_wins"]) == (72, 72)
    assert summary["contact_ci95"] == [0.5, 0.5]
    assert summary["map_contact_wins_0_1_2"] == [0, 24, 0]
    assert summary["relative_to_r3_vs_same_v4"]["gained"] == 18
    assert summary["relative_to_r3_vs_same_v4"]["lost"] == 6
    with pytest.raises(ValueError):
        compare(dict(list(rows.items())[1:]), old)


def test_official_match_winner_on_tied_points_player_one():
    side = SEATS[1]
    row = dict(seed=MAPS.start, side=side, arm="contact", opponent="v4_mixed", steps=303,
               result=1, wins=2, losses=1, points=15, opp_points=13,
               updates=dict.fromkeys(SEATS, 303), commands_sha256=dict.fromkeys(SEATS, "a"*64),
               matches=[dict(winner=side, world_points=[4,4]), dict(winner=SEATS[0], world_points=[6,4]),
                        dict(winner=side, world_points=[3,7])],
               routing=dict(near_unit_turns=5, far_unit_turns=4, different_near=3, different_far=2))
    assert validate(row, "contact", "v4_mixed") == (MAPS.start, side)
    wrong = deepcopy(row)
    wrong["matches"][0]["winner"] = SEATS[0]
    with pytest.raises(ValueError):
        validate(wrong, "contact", "v4_mixed")
