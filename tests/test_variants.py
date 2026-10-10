"""Jede Ablation unterscheidet sich von `full` in genau EINEM Config-Feld."""
import pytest

from scripts import protocol as P
from scripts.variants import ABLATIONS, variant_cfg


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
