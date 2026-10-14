"""Endpunkte gegen die echte Engine ohne den abschliessenden Reset pruefen."""
import numpy as np
import pytest

from tests.conftest import ROOT


@pytest.mark.parametrize("side", ["player_0", "player_1"])
@pytest.mark.parametrize("consumer", ["game", "losses", "timing"])
def test_match_end_points_against_engine(env, monkeypatch, side, consumer):
    import jax
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent, play_game
    from scripts.analyze_losses import play_and_measure
    from scripts.analyze_timing import play_and_time

    expected = []
    real_step = env.step

    def audited_step(actions):
        before = env.state
        _, key = jax.random.split(env.rng_key)
        result = real_step(actions)
        obs = result[0][side]
        if int(obs["match_steps"]) == 0:
            # Gleiche Ausgangslage, Aktionen und Zufallszahlen. Nur den
            # Matchabschluss um einen Schritt verschieben, um die Endpunkte
            # direkt aus der Engine vor ihrem Reset lesen zu koennen.
            params = env.env_params.replace(
                max_steps_in_match=env.env_params.max_steps_in_match + 1)
            _, state, *_ = env.jax_env.step(key, before, actions, params)
            expected.append(np.asarray(state.team_points))
        return result

    monkeypatch.setattr(env, "step", audited_step)
    agent = Agent_x(side, agent_path=str(ROOT / "agents/sherlock/weights/agent_p0.pth"),
                    train=False)
    agent.set_to_eval_mode()
    opp = make_opponent("default", "player_1" if side == "player_0" else "player_0")
    us = int(side[-1])
    if consumer == "game":
        from luxai_s3.wrappers import RecordEpisode
        wrapped = RecordEpisode(env, save_on_close=False, save_on_reset=False)
        row = play_game(wrapped, agent, opp, 900011, side, train=False)
        actual = [row["our_points"], row["opp_points"]]
        np.testing.assert_array_equal(actual, np.sum(expected, axis=0)[[us, 1 - us]])
    elif consumer == "losses":
        rows = play_and_measure(env, agent, opp, 900011, side)
        for row in rows:
            assert row["points"] == expected[row["match"]][row["team"]]
    else:
        rows = play_and_time(env, agent, opp, 900011, side)
        for row in rows:
            np.testing.assert_array_equal([row["points"], row["opp_points"]],
                                          expected[row["match"]][[us, 1 - us]])
    assert len(expected) == 3


def test_final_increment_counts_tiles_not_units_and_only_eligible_units():
    from types import SimpleNamespace as NS
    from scripts.scoring import match_points_after_step

    weights = np.array([[1, 1, 2], [0, 1, 1], [0, 0, 0]])
    state = NS(relic_nodes_map_weights=weights, relic_nodes_mask=np.array([1, 1, 0, 0]),
               units_mask=np.array([[1, 1, 1, 1, 1, 0], [0, 0, 0, 0, 0, 0]], bool),
               units=NS(position=np.array([[[0, 0], [0, 0], [0, 1], [0, 2], [1, 1], [1, 2]],
                                           [[0, 0]] * 6]),
                        energy=np.array([[[5], [2], [0], [5], [-1], [10]], [[10]] * 6])))
    before = {"team_points": np.array([0, 0])}
    after = {"match_steps": 0, "team_points": np.array([0, 0])}
    # Stack counts once; zero energy counts; unspawned, negative-energy and
    # dead units do not. First points can arrive on the final step alone.
    np.testing.assert_array_equal(match_points_after_step(before, after, {"final_state": state}), [2, 0])
    np.testing.assert_array_equal(before["team_points"], [0, 0])
    np.testing.assert_array_equal(after["team_points"], [0, 0])
    state.units_mask[:] = False
    np.testing.assert_array_equal(match_points_after_step(before, after, {"final_state": state}), [0, 0])


def test_ordinary_step_uses_observed_points_without_hidden_state():
    from scripts.scoring import match_points_after_step
    np.testing.assert_array_equal(match_points_after_step(
        {"team_points": [3, 2]}, {"match_steps": 75, "team_points": [5, 3]}, {}), [5, 3])


def test_missing_final_state_fails_instead_of_silently_undercounting():
    from scripts.scoring import match_points_after_step
    with pytest.raises(KeyError, match="final_state"):
        match_points_after_step({"team_points": [3, 2]},
                               {"match_steps": 0, "team_points": [0, 0]}, {})


@pytest.mark.parametrize("schema", ["game", "train", "val"])
def test_csv_retains_point_counting_version(schema):
    import csv
    import io
    from scripts.experiment import GAME_FIELDS, VAL_FIELDS, summarize
    from scripts.train import LOG_FIELDS
    row = dict(our_points=20, opp_points=10, our_wins=2, opp_wins=1,
               result=1, point_win=1, point_counting_version=2)
    fields = {"game": GAME_FIELDS, "train": LOG_FIELDS, "val": VAL_FIELDS}[schema]
    if schema == "val":
        row = summarize([row])
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    writer.writerow({k: row.get(k) for k in fields})
    buf.seek(0)
    assert next(csv.DictReader(buf)).get("point_counting_version") == "2"


def test_summary_keeps_legacy_version_and_rejects_mixed_measurements():
    from scripts.experiment import summarize
    row = dict(our_points=20, opp_points=10, our_wins=2, opp_wins=1, result=1, point_win=1)
    assert summarize([row])["point_counting_version"] == 1
    with pytest.raises(ValueError, match="Punktemessungen"):
        summarize([row, {**row, "point_counting_version": 2}])


@pytest.mark.parametrize("consumer", ["losses", "timing"])
@pytest.mark.parametrize("score_at_end", [False, True])
def test_diagnosis_distinguishes_no_score_from_first_point_on_final_step(consumer, score_at_end):
    from types import SimpleNamespace as NS
    from tests.conftest import ENV_CFG, make_obs
    from scripts.analyze_losses import play_and_measure
    from scripts.analyze_timing import play_and_time

    class QuietAgent:
        belief = NS(point_tiles=np.zeros((24, 24), bool), mirrored=False, relic_positions=set())

        def new_game(self, side):
            pass

        def set_env_cfg(self, cfg):
            pass

        def act(self, **kwargs):
            return np.zeros((16, 3), int)

    class FinalTwoSteps:
        """Controlled scoring boundary: nothing before, optionally one final point."""
        def observation(self, ms):
            o = make_obs(100 if ms else 101, ms, units=[(2, 2, 10)])
            return {"player_0": o, "player_1": o}

        def set_state(self, scoring):
            o = self.observation(100)["player_0"]
            w = np.zeros((24, 24), int)
            if scoring:
                w[2, 2] = 1
            self.state = NS(relic_nodes_map_weights=w, relic_nodes_mask=np.array([1, 1]),
                            relic_spawn_schedule=np.array([0, 0]), relic_nodes=np.array([[1, 1], [22, 22]]),
                            sensor_mask=np.ones((2, 24, 24), bool), units_mask=o["units_mask"],
                            units=NS(position=o["units"]["position"], energy=o["units"]["energy"][..., None]))

        def reset(self, **kwargs):
            self.n = 0
            self.set_state(False)
            return self.observation(99), {"params": ENV_CFG}

        def step(self, actions):
            self.n += 1
            done = self.n == 2
            self.set_state(done and score_at_end)
            flags = {"player_0": done, "player_1": done}
            return self.observation(0 if done else 100), {}, flags, flags, {"final_state": self.state}

    fn = play_and_measure if consumer == "losses" else play_and_time
    rows = fn(FinalTwoSteps(), QuietAgent(), QuietAgent(), 0, "player_0")
    row = rows[0]
    key = "first_score_step" if consumer == "losses" else "first_score"
    assert row[key] == (101 if score_at_end else -1)
    assert row["points"] == int(score_at_end)
