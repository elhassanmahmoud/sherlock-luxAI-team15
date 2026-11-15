"""Zwei DAgger-Schritte mit dem echten Kaggle-Aktionsgedaechtnis, ohne Modelle oder Spiel."""
import importlib
from types import SimpleNamespace

import numpy as np
import pytest

from scripts.fetch_kaggle3 import TARGET


@pytest.mark.skipif(not (TARGET / "agent" / "agent.py").is_file(), reason="Kaggle-Lehrerquelle fehlt")
def test_dagger_teacher_remembers_only_the_played_native_actions(monkeypatch, tmp_path):
    from luxai_s3 import wrappers
    from agents.sherlock import imitation_agent
    from scripts import experiment, imitate, kaggle3_opponent

    # Seite 1: SAP-Deltas in Weltkoordinaten. Die freie ID 0 soll keinen Schuss erzeugen.
    side = "player_1"
    played = np.zeros((16, 3), dtype=int)
    played[0] = [5, 1, 1]
    played[7] = [5, -2, 3]
    observed_maps = []
    labels = []

    def configure_without_models(teacher, cfg):
        path = importlib.import_module("agent.path")
        tasks = importlib.import_module("agent.tasks")
        state = teacher._module.State(1)
        for uid, position in ((3, (3, 3)), (7, (14, 12))):
            ship = state.fleet.ships[uid]
            ship.node = state.space.get_node(*position)
            ship.energy = 100

        def advise(step, obs, time_left):
            observed_maps.append(tasks.get_sap_array(state.copy()))
            # Der Lehrer wuerde mit Schiff 3 schiessen, mit Schiff 7 stehen bleiben.
            state.fleet.ships[3].action_queue = [path.Action(path.ActionType.sap, 2, 1)]
            state.fleet.ships[7].action_queue = []
            return state.create_actions_array()

        teacher.agent = SimpleNamespace(state=state, act=advise)

    class Student:
        last_fz = object()
        belief = SimpleNamespace(mirrored=True)

        def set_to_eval_mode(self):
            pass

        def act(self, step, obs):
            return played

    obs = {p: {"team_wins": [0, 0]} for p in ("player_0", "player_1")}

    class TwoSteps:
        steps = 0

        def reset(self, seed):
            return obs, {"params": {}}

        def step(self, actions):
            np.testing.assert_array_equal(actions[side], played)
            self.steps += 1
            return obs, {}, {side: self.steps == 2}, {side: False}, {}

        def close(self):
            pass

    monkeypatch.setattr(experiment, "limit_threads", lambda: None)
    monkeypatch.setattr(wrappers, "LuxAIS3GymEnv", lambda **kw: TwoSteps())
    monkeypatch.setattr(imitation_agent, "ImitationAgent", lambda *args, **kw: Student())
    monkeypatch.setattr(imitate, "make_player", lambda kind, side: Student())
    monkeypatch.setattr(kaggle3_opponent.Kaggle3Opponent, "set_env_cfg", configure_without_models)
    monkeypatch.setattr(imitate.SideRecord, "add", lambda self, fz, label, mirrored: labels.append(label.copy()))
    imitate._dagger_worker(([(123, side, "v14")], tmp_path, "unused"))

    assert len(labels) == len(observed_maps) == 2
    for label in labels:
        np.testing.assert_array_equal(label[3], [5, 2, 1])
        assert label[7, 0] == 0
    assert not observed_maps[0].any()
    # Die originale Lehrerfunktion liefert [y, x]. Der Mittelpunkt des Schusses
    # hat mehr Gewicht als die Nachbarfelder. Der Lehrer-Vorschlag bleibt aus.
    current = observed_maps[1]
    assert current[4, 5] == 0
    assert current[15, 12] > 0
    assert np.unravel_index(np.argmax(current), current.shape) == (15, 12)
