"""Opt-in corrections for V10 recovery accounting and terrain/sensor ordering."""
import numpy as np
import pytest

from agents.sherlock import geometry as geo
from agents.sherlock.belief import TILE_ASTEROID, TILE_NEBULA, TILE_UNKNOWN
from agents.sherlock.config import AgentConfig
from tests.conftest import ENV_CFG, make_obs
from tests.test_rules_1910 import _stay_agent


def _recovery_case(flag, energy=35, field=10, max_field=None):
    cfg = {"pt_sap": True, "sap_no_overkill": True}
    if flag is not None:
        cfg["sap_overkill_recovery"] = flag
    # Exercise the checkpoint-config path, including old configs without a flag.
    a = _stay_agent(**AgentConfig.from_dict(cfg).to_dict())
    if max_field is not None:
        a.set_env_cfg({**ENV_CFG, "max_energy_per_tile": max_field})
    for tile in ((5, 5), (5, 6), (8, 7)):
        a.belief.point_tiles[tile] = True
    obs = make_obs(10, 10, units=[(5, 5, 200), (5, 6, 200)],
                   enemies=[(8, 7, energy)], relics=[(9, 9)])
    obs["map_features"]["energy"][8, 7] = field
    return a, obs


@pytest.mark.parametrize("flag,want", [(None, geo.STAY), (False, geo.STAY), (True, geo.SAP)])
def test_recovery_keeps_second_sap_for_enemy_revived_by_positive_field(flag, want):
    # 35 - 40 + 10 = +5: canceling the second holder leaves the target alive.
    a, obs = _recovery_case(flag)
    actions = a.act(10, obs)
    assert int(actions[0, 0]) == geo.SAP
    assert int(actions[1, 0]) == want


@pytest.mark.parametrize("energy,field,want", [
    (19, 20, geo.STAY),  # 19 - 40 + maximum 20 = -1: cannot recover.
    (20, 20, geo.SAP),   # Exactly zero survives, including after field recovery.
    (35, 0, geo.SAP),    # Observed zero is not a bound on the next field.
    (35, -20, geo.SAP),  # Neither is an observed negative field.
    (40, -20, geo.SAP),  # Nonnegative pre-field energy is clipped at zero.
])
def test_recovery_cancellation_uses_maximum_gain_and_strict_negative_boundary(energy, field, want):
    a, obs = _recovery_case(True, energy, field)
    assert int(a.act(10, obs)[1, 0]) == want


@pytest.mark.parametrize("energy,want", [(14, geo.STAY), (15, geo.SAP)])
def test_recovery_respects_public_field_bound_override(energy, want):
    a, obs = _recovery_case(True, energy, field=25, max_field=25)
    assert int(a.act(10, obs)[1, 0]) == want


def test_recovery_does_not_treat_unknown_or_stale_map_as_zero():
    a, obs = _recovery_case(True)
    ctx = a._decide(obs)[0]
    # The cancellation contract must also be conservative without a current map.
    # No hidden enemy is synthesized: this is the visible-target decision context.
    ctx.pop("energy_map")
    assert not a._overkill(ctx, 1, (3, 1, 1), np.array([40.0]))


@pytest.mark.parametrize("max_field", [0, -20])
@pytest.mark.parametrize("energy,want", [(39, geo.STAY), (40, geo.SAP)])
def test_nonpositive_field_cannot_revive_negative_energy_or_kill_zero(max_field, energy, want):
    a, obs = _recovery_case(True, energy, field=max_field, max_field=max_field)
    assert int(a.act(10, obs)[1, 0]) == want


def test_recovery_keeps_sap_when_only_adjacent_enemy_can_recover():
    a, obs = _recovery_case(True, energy=10)
    obs["units"]["position"][1, 1] = (9, 7)
    obs["units"]["energy"][1, 1] = 25
    obs["units_mask"][1, 1] = True
    ctx = a._decide(obs)[0]
    assert not a._overkill(ctx, 1, (3, 1, 2), np.array([40.0, 40.0]))


@pytest.mark.parametrize("energy,want_cancel", [(7, True), (8, False)])
def test_recovery_retains_conservative_integer_splash_damage(energy, want_cancel):
    a, obs = _recovery_case(True, energy)
    a.set_env_cfg({**ENV_CFG, "unit_sap_cost": 31})
    ctx = a._decide(obs)[0]
    planned = np.zeros(1)
    for _ in range(4):
        a._plan_damage(ctx, 0, (2, 2, 1), planned)  # Target (7,7), enemy (8,7).
    # Unknown dropoff is at least .25: floor(31*.25)=7 per planned hit.
    # Summing those floors is conservative versus the engine's aggregate floor.
    np.testing.assert_array_equal(planned, [28])
    assert a._overkill(ctx, 1, (3, 1, 1), planned) == want_cancel


@pytest.mark.parametrize("flag,want_energy", [(False, 5), (True, -45)])
def test_recovery_actions_against_one_engine_step(env, flag, want_energy):
    import jax.numpy as jnp
    from luxai_s3.params import EnvParams

    # A deterministic field isolates the surprising engine recovery rule. This
    # is one synthetic step, not a sampled game or a source of agent knowledge.
    params = EnvParams(unit_sap_cost=40, unit_sap_range=4, unit_sensor_range=4,
                       min_energy_per_tile=10, max_energy_per_tile=10,
                       unit_energy_void_factor=0, nebula_tile_drift_speed=0,
                       energy_node_drift_speed=0, spawn_rate=100)
    env.reset(seed=0, options={"params": params})
    a, obs = _recovery_case(flag)
    actions = a.act(10, obs)
    state = env.state
    env.state = state.replace(
        steps=jnp.asarray(10, dtype=state.steps.dtype),
        match_steps=jnp.asarray(10, dtype=state.match_steps.dtype),
        units=state.units.replace(
            position=jnp.asarray(obs["units"]["position"], dtype=state.units.position.dtype),
            energy=jnp.asarray(obs["units"]["energy"], dtype=state.units.energy.dtype)[..., None]),
        units_mask=jnp.asarray(obs["units_mask"]),
        map_features=state.map_features.replace(tile_type=jnp.zeros((24, 24), dtype=jnp.int16)),
        relic_spawn_schedule=jnp.full_like(state.relic_spawn_schedule, -1),
    )
    env.step({"player_0": actions.astype(np.int16),
              "player_1": np.zeros((16, 3), dtype=np.int16)})
    assert int(env.state.units.energy[1, 0, 0]) == want_energy


def _drift_case(flag, direction=1, team=0, infer=True):
    cfg = {"nebula_infer": infer, "drift_track": True}
    if flag is not None:
        cfg["nebula_infer_drift_safe"] = flag
    a = _stay_agent(**AgentConfig.from_dict(cfg).to_dict())
    a.set_env_cfg({**ENV_CFG, "unit_sensor_range": 1})
    a.new_game(f"player_{team}")  # The option must survive game/player resets.
    old = np.zeros((24, 24), dtype=np.int8)
    old[5, 6] = old[4, 4] = TILE_ASTEROID
    old[6, 5] = TILE_NEBULA
    if direction == -1:
        old = old.T.copy()
    a.belief.tile_type[:] = old
    x, y = np.indices(old.shape)
    distance = np.maximum(abs(x - 5), abs(y - 5))
    power = np.where(distance <= 1, 2 - distance, 0)
    power[5, 5] += 10
    # Engine order: sensor power uses OLD terrain, then the terrain rolls.
    sensor = power - 2 * (old == TILE_NEBULA) > 0
    current = np.roll(old, (direction, -direction), axis=(0, 1))
    unit = geo.mirror_xy(5, 5) if team else (5, 5)
    obs = make_obs(10, 10, team=team, units=[(*unit, 100)])
    obs["sensor_mask"] = geo.mirror_map(sensor) if team else sensor
    terrain = geo.mirror_map(current) if team else current
    obs["map_features"]["tile_type"] = np.where(obs["sensor_mask"], terrain, TILE_UNKNOWN)
    obs["map_features"]["energy"] = np.where(obs["sensor_mask"], 0, -1)
    target = (6, 5) if direction == 1 else (5, 6)
    assert not sensor[target] and current[target] == TILE_ASTEROID
    return a, obs, sensor, current, target


@pytest.mark.parametrize("flag,want", [(None, TILE_NEBULA), (False, TILE_NEBULA),
                                       (True, TILE_ASTEROID)])
def test_detected_drift_does_not_relabel_current_asteroid_from_old_sensor(flag, want):
    a, obs, sensor, current, target = _drift_case(flag)
    a.belief.observe(obs)
    assert a.belief.drift_events == 1
    assert a.belief.drift_votes[1] == 1
    assert int(a.belief.tile_type[target]) == want
    assert bool(a.belief.passable[target]) == (want != TILE_ASTEROID)
    np.testing.assert_array_equal(a.belief.tile_type[sensor], current[sensor])


@pytest.mark.parametrize("team,direction", [(0, -1), (1, 1), (1, -1)])
def test_drift_safe_inference_preserves_canonical_direction_after_reset(team, direction):
    a, obs, sensor, current, target = _drift_case(True, direction=direction, team=team)
    a.belief.observe(obs)
    assert a.belief.drift_events == 1
    assert a.belief.drift_votes[direction] == 1
    assert int(a.belief.tile_type[target]) == TILE_ASTEROID
    np.testing.assert_array_equal(a.belief.tile_type[sensor], current[sensor])


@pytest.mark.parametrize("flag,infer,want", [(False, True, TILE_NEBULA),
                                             (True, True, TILE_NEBULA),
                                             (True, False, TILE_ASTEROID)])
def test_drift_safe_keeps_normal_hidden_in_range_inference(flag, infer, want):
    a, obs, sensor, current, target = _drift_case(flag, infer=infer)
    # No drift: one stale hidden asteroid can still be corrected as before.
    current = a.belief.tile_type.copy()
    obs["map_features"]["tile_type"] = np.where(sensor, current, TILE_UNKNOWN)
    a.belief.tile_type[target] = TILE_ASTEROID
    a.belief.tile_type[20, 20] = TILE_UNKNOWN
    a.belief.observe(obs)
    assert a.belief.drift_events == 0
    assert int(a.belief.tile_type[target]) == want
    assert int(a.belief.tile_type[20, 20]) == TILE_UNKNOWN  # No global hidden-state inference.
    np.testing.assert_array_equal(a.belief.tile_type[sensor], current[sensor])


def test_drift_safe_resumes_inference_after_detected_drift():
    a, obs, _, current, target = _drift_case(True)
    a.belief.observe(obs)
    assert int(a.belief.tile_type[target]) == TILE_ASTEROID
    # A later observation sees the same terrain from a reachable empty tile.
    # Remove one remembered tile to make resumed inference observable.
    a.belief.tile_type[7, 4] = TILE_UNKNOWN
    assert current[7, 4] == TILE_NEBULA
    obs = make_obs(12, 12, units=[(6, 4, 100)], sensor_all=False)
    obs["sensor_mask"][5:8, 3:6] = True
    obs["sensor_mask"][7, 4] = False
    obs["map_features"]["tile_type"] = np.where(obs["sensor_mask"], current, TILE_UNKNOWN)
    obs["map_features"]["energy"] = np.where(obs["sensor_mask"], 0, -1)
    a.belief.observe(obs)
    assert a.belief.drift_events == 1
    assert int(a.belief.tile_type[target]) == TILE_ASTEROID
    assert int(a.belief.tile_type[7, 4]) == TILE_NEBULA
