import pytest

from scripts.midpoint_turn_archive import comparison, contrasts


def test_joint_rule_separates_the_weight_and_window_effects_with_paired_seats():
    rows = [
        dict(seed=seed, rows=100, r3=60, midpoint=61, r3_turn=62, midpoint_turn=66)
        for seed in (8, 9) for _ in range(2)
    ]
    effects = contrasts(rows)
    assert effects["combined_vs_original_turn"] == dict(net=16, pp=4, ci95_pp=[4,4], maps=2)
    assert effects["combined_vs_midpoint"]["net"] == 20
    assert effects["midpoint_vs_r3"]["net"] == 4
    with pytest.raises(ValueError, match="Both seats"):
        comparison(rows[:3], "midpoint_turn", "r3_turn")
