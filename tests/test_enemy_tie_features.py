"""Optional nearest-enemy tie selection, without model or engine imports."""
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from .conftest import ENV_CFG, make_obs

# agents/__init__.py eagerly discovers every agent (including model backends).
# Load the real empty sherlock package under a private name to avoid that side effect.
_IMPORTS_BEFORE = set(sys.modules)
_PACKAGE = "_enemy_tie_test_sherlock"
_ROOT = Path(__file__).resolve().parents[1] / "agents" / "sherlock"
_spec = importlib.util.spec_from_file_location(
    _PACKAGE, _ROOT / "__init__.py", submodule_search_locations=[str(_ROOT)]
)
_package = importlib.util.module_from_spec(_spec)
sys.modules[_PACKAGE] = _package
_spec.loader.exec_module(_package)
AgentConfig = importlib.import_module(f"{_PACKAGE}.config").AgentConfig
Belief = importlib.import_module(f"{_PACKAGE}.belief").Belief
_features = importlib.import_module(f"{_PACKAGE}.features")
build_features, make_context = _features.build_features, _features.make_context
_IMPORTS_ADDED = set(sys.modules) - _IMPORTS_BEFORE


def context(enemies, team=0, config=None):
    """Actual context builder and belief; synthetic fully explored, empty map."""
    belief = Belief(team_id=team)
    belief.explored[:] = True
    belief.tile_type[:] = 0
    agent = SimpleNamespace(
        cfg=AgentConfig() if config is None else config,
        belief=belief, env_cfg=ENV_CFG,
    )
    obs = make_obs(50, 50, team=team, units=[(10, 10, 125)], enemies=enemies)
    return make_context(agent, obs)


def expected_enemy(dx, dy, distance, energy, count, team):
    # Independent world-to-canonical expectation for the hand-picked enemy.
    if team == 1:
        dx, dy = -dy, -dx
    return np.array([
        dx / 24, dy / 24, distance / 48,
        np.tanh(np.float32((125 - energy) / 100)), min(count / 4, 1), count / 16,
    ], dtype=np.float32)


def legacy_vector(enemy, team):
    """Hand-derived complete legacy vector for context()'s fixed empty map."""
    xy = 10 / 24 if team == 0 else 13 / 24
    return np.array(
        [xy, xy, 125 / 400, 0, .5, 0, 3 / 5, 40 / 50, 4 / 7, 2 / 4]
        + [0] * 4
        + [0, 0, 1, 0] * 5
        + [0, 0, 0, .25, 0]
        + [1, 0, 0, 0, 0, .25]
        + [1, 0, 0, 0, 0, 0] * 4
        + list(enemy)
        + [1 / 16, 0, 1, 0],
        dtype=np.float32,
    )


def test_old_serialized_config_defaults_off_and_roundtrips():
    old = AgentConfig.from_dict({"canonical": True, "unknown_future_option": 1})
    assert getattr(old, "enemy_tie_energy", None) is False
    assert old.to_dict()["enemy_tie_energy"] is False
    enabled = AgentConfig.from_dict({"enemy_tie_energy": True})
    assert AgentConfig.from_dict(enabled.to_dict()).enemy_tie_energy is True


@pytest.mark.parametrize("team", [0, 1])
@pytest.mark.parametrize("flag", [False, None])
@pytest.mark.parametrize("energies", [(-27, 150), (89, 150), (150, 150)])
def test_false_or_missing_context_preserves_complete_legacy_vector(team, flag, energies):
    ctx = context([(11, 9, energies[0]), (10, 8, energies[1])], team)
    if flag is None:
        ctx.pop("enemy_tie_energy", None)
    else:
        ctx["enemy_tie_energy"] = flag
    expected = expected_enemy(1, -1, 2, energies[0], 2, team)
    np.testing.assert_array_equal(build_features(ctx, 0), legacy_vector(expected, team))


@pytest.mark.parametrize("team", [0, 1])
@pytest.mark.parametrize("enemies,selected", [
    ([(11, 9, 89), (10, 8, 150)], (0, -2, 2, 150)),
    ([(11, 9, 150), (10, 8, 150)], (1, -1, 2, 150)),
    ([(11, 9, -27), (10, 8, -10)], (0, -2, 2, -10)),
    ([(11, 10, -27), (10, 8, 150)], (1, 0, 1, -27)),
    ([(11, 9, 89)], (1, -1, 2, 89)),
    # Non-contiguous nearest candidates: farther high energy cannot win.
    ([(11, 9, 89), (13, 10, 300), (10, 8, 150)], (0, -2, 2, 150)),
])
def test_enabled_selects_highest_energy_only_within_nearest_ties(team, enemies, selected):
    ctx = context(enemies, team)
    ctx["enemy_tie_energy"] = True
    expected = expected_enemy(*selected, len(enemies), team)
    np.testing.assert_array_equal(build_features(ctx, 0), legacy_vector(expected, team))


@pytest.mark.parametrize("team", [0, 1])
@pytest.mark.parametrize("flag", [False, True, None])
def test_empty_enemies_keep_legacy_sentinel(team, flag):
    ctx = context([], team)
    if flag is None:
        ctx.pop("enemy_tie_energy", None)
    else:
        ctx["enemy_tie_energy"] = flag
    np.testing.assert_array_equal(
        build_features(ctx, 0), legacy_vector([0, 0, 1, 0, 0, 0], team)
    )


@pytest.mark.parametrize("team", [0, 1])
def test_actual_config_context_wiring_changes_only_enemy_position_and_relative_energy(team):
    enemies = [(11, 9, 89), (10, 8, 150)]
    before = context(enemies, team, AgentConfig.from_dict({}))
    after = context(enemies, team, AgentConfig.from_dict({"enemy_tie_energy": True}))
    assert after.get("enemy_tie_energy") is True
    old_features, new_features = build_features(before, 0), build_features(after, 0)
    assert old_features.shape == new_features.shape == (79,)
    np.testing.assert_array_equal(np.flatnonzero(old_features != new_features), [69, 70, 72])
    np.testing.assert_array_equal(
        new_features[69:75], expected_enemy(0, -2, 2, 150, 2, team)
    )
    # All shared context, including target assignments, counts and enemy order, stays intact.
    assert before.keys() == after.keys()
    for key in before.keys() - {"belief", "enemy_tie_energy"}:
        if isinstance(before[key], np.ndarray):
            np.testing.assert_array_equal(before[key], after[key])
        else:
            assert before[key] == after[key], key


def test_imports_require_no_model_or_engine_backends():
    assert not any(name.split(".")[0] in {"torch", "jax", "luxai_s3"} for name in _IMPORTS_ADDED)
