"""Jede Ablation unterscheidet sich von `full` in genau EINEM Config-Feld."""
import pytest

from scripts import protocol as P
from scripts.variants import ABLATIONS, VARIANTS, variant_cfg


@pytest.mark.parametrize("name", ABLATIONS)
def test_ablation_differs_in_exactly_one_flag(name):
    full, v = variant_cfg("full").to_dict(), variant_cfg(name).to_dict()
    diff = [k for k in full if full[k] != v[k]]
    assert len(diff) == 1, diff


def test_expected_ablations_present():
    assert set(ABLATIONS) == {"no_belief", "no_shaping", "no_sap",
                              "no_guided_explore", "no_canonical"}


def test_seed_sets_are_disjoint():
    train = {P.train_seed(r, g) for r in range(3) for g in range(3000)}
    assert not train & set(P.val_seeds()) and not train & set(P.test_seeds())
    assert not set(P.val_seeds()) & set(P.test_seeds())
    assert len(P.test_seeds()) == 30


def test_curriculum_uses_both_opponents_after_warmup():
    opps = [P.train_opponent(g, 3000) for g in range(3000)]
    assert set(opps[:750]) == {"default"}
    assert abs(opps[750:].count("solution92") - opps[750:].count("default")) <= 2


def test_terminal_pilot_differs_only_in_death_potential_flag():
    assert "full_rules_v3_terminal" in VARIANTS
    base = variant_cfg("full_rules_v3").to_dict()
    pilot = variant_cfg("full_rules_v3_terminal").to_dict()
    assert {key for key in base if base[key] != pilot[key]} == {"terminal_death_potential"}
    assert base["terminal_death_potential"] is False
    assert pilot["terminal_death_potential"] is True
    assert VARIANTS["full_rules_v3_terminal"][0] == VARIANTS["full_rules_v3"][0] == "sherlock"
    assert "full_rules_v3_terminal" not in ABLATIONS


def test_terminal_pilot_does_not_mutate_base_or_share_override_dictionary():
    assert "full_rules_v3_terminal" in VARIANTS
    base_overrides = dict(VARIANTS["full_rules_v3"][1])
    pilot_overrides = dict(VARIANTS["full_rules_v3_terminal"][1])
    assert "terminal_death_potential" not in base_overrides
    assert pilot_overrides == {**base_overrides, "terminal_death_potential": True}
    assert VARIANTS["full_rules_v3_terminal"][1] is not VARIANTS["full_rules_v3"][1]
    local = variant_cfg("full_rules_v3_terminal")
    local.far_opp = 999
    local.terminal_death_potential = False
    assert VARIANTS["full_rules_v3"][1] == base_overrides
    assert VARIANTS["full_rules_v3_terminal"][1] == pilot_overrides
    assert variant_cfg("full_rules_v3").far_opp == 10
    assert variant_cfg("full_rules_v3_terminal").terminal_death_potential is True
