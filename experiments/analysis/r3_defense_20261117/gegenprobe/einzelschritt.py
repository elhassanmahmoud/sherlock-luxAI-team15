"""Observe the one-turn effect of reverting only defensive overrides; no agent sees hidden state."""
import jax
import numpy as np

from scripts.scoring import match_points_after_step, point_tile_map


def same_state(expected, actual):
    left, shape = jax.tree_util.tree_flatten(expected)
    right, other_shape = jax.tree_util.tree_flatten(actual)
    return shape == other_shape and all(
        np.array_equal(np.asarray(a), np.asarray(b), equal_nan=True)
        for a, b in zip(left, right, strict=True)
    )


def scoring_fields(state, team):
    points = point_tile_map(state)
    energy = np.asarray(state.units.energy)[team, :, 0]
    live = np.asarray(state.units_mask)[team] & (energy >= 0)
    pos = np.asarray(state.units.position)[team, live]
    return {tuple(map(int, field)) for field in pos if points[tuple(field)]}


def energy_sum(state, team):
    energy = np.asarray(state.units.energy)[team, :, 0]
    live = np.asarray(state.units_mask)[team] & (energy >= 0)
    return int(energy[live].sum())


class StepFork:
    """Subset wrapper for scripts.common.play_game on a single diagnostic game."""

    def __init__(self, env, candidate, side):
        self.env = env
        self.candidate = candidate
        self.side = side
        self.team = ("player_0", "player_1").index(side)
        self.events = []

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self.events.clear()
        self.obs = obs[self.side]
        return obs, info

    def step(self, commands):
        own = np.asarray(commands[self.side])
        base = np.asarray(self.candidate.last_base)
        if base.shape != own.shape or own.shape != (16, 3) or base.dtype != own.dtype:
            raise ValueError("R3 and actual world command matrices differ in shape or dtype")
        units = np.flatnonzero(np.any(own != base, axis=1))
        if len(units):
            source = self.env.state
            next_key, step_key = jax.random.split(self.env.rng_key)
            native_step = self.env.jax_env.step
            params = self.env.env_params
            _, control_state, _, _, _, _ = native_step(step_key, source, commands, params)
            _, alt_state, _, _, _, alt_info = native_step(
                step_key, source, {**commands, self.side: base}, params
            )
        result = self.env.step(commands)
        after = result[0][self.side]
        if len(units):
            if not same_state(control_state, self.env.state) or not np.array_equal(
                jax.random.key_data(next_key), jax.random.key_data(self.env.rng_key)
            ):
                raise ValueError("Native identical-action control failed")
            actual_points = match_points_after_step(self.obs, after, result[-1])
            alt_points = match_points_after_step(
                self.obs, {"team_points": alt_state.team_points, "match_steps": alt_state.match_steps}, alt_info
            )
            actual_gain = actual_points - self.obs["team_points"]
            alt_gain = alt_points - self.obs["team_points"]
            order = (self.team, 1 - self.team)
            actual_fields = [scoring_fields(self.env.state, team) for team in order]
            alt_fields = [scoring_fields(alt_state, team) for team in order]
            if (not all(len(a) == actual_gain[t] for a, t in zip(actual_fields, order))
                    or not all(len(a) == alt_gain[t] for a, t in zip(alt_fields, order))):
                raise ValueError("Scored field count disagrees with official score")
            held_before = [scoring_fields(source, team) for team in order]
            self.events.append(dict(
                step=int(self.obs["steps"]), turn=int(self.obs["match_steps"]),
                match=int(np.asarray(self.obs["team_wins"]).sum()) + 1,
                units=units.tolist(), r3_orders=base[units].tolist(), played_orders=own[units].tolist(),
                actual_gain=[int(actual_gain[t]) for t in order],
                r3_gain=[int(alt_gain[t]) for t in order],
                own_fields_gained=sorted(actual_fields[0] - alt_fields[0]),
                own_fields_lost=sorted(alt_fields[0] - actual_fields[0]),
                enemy_fields_denied=sorted(alt_fields[1] - actual_fields[1]),
                enemy_fields_conceded=sorted(actual_fields[1] - alt_fields[1]),
                previous_own_fields_saved=sorted((actual_fields[0] - alt_fields[0]) & held_before[0]),
                previous_own_fields_abandoned=sorted((alt_fields[0] - actual_fields[0]) & held_before[0]),
                previous_enemy_fields_denied=sorted((alt_fields[1] - actual_fields[1]) & held_before[1]),
                previous_enemy_fields_conceded=sorted((actual_fields[1] - alt_fields[1]) & held_before[1]),
                energy_actual_minus_r3=[energy_sum(self.env.state, t) - energy_sum(alt_state, t) for t in order],
            ))
        self.obs = after
        return result
