"""Kaggle-Platz-3-Agent als Testgegner (15.11.2026). Wird uebersprungen, solange er nicht geladen ist."""
import numpy as np
import pytest

from scripts.fetch_kaggle3 import TARGET, verify

pytestmark = pytest.mark.skipif(not verify(), reason="Kaggle-Agent nicht geladen (python -m scripts.fetch_kaggle3)")


def test_kaggle3_plays_course_steps_and_resets_state():
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from scripts.common import make_opponent

    env = LuxAIS3GymEnv(numpy_output=True)
    obs, info = env.reset(seed=7159999)
    bots = {p: make_opponent("kaggle3", p) for p in ("player_0", "player_1")}
    for b in bots.values():
        b.set_env_cfg(info["params"])
    for step in range(25):
        actions = {p: bots[p].act(step, obs[p]) for p in bots}
        for a in actions.values():
            assert a.shape == (16, 3)
            assert a[:, 0].min() >= 0 and a[:, 0].max() <= 5
        obs, *_ = env.step(actions)
    env.close()

    old_global = bots["player_0"].base.Global
    old_global._test_marker = 1
    fresh = make_opponent("kaggle3", "player_0")
    assert fresh.base.Global is not old_global
    assert not hasattr(fresh.base.Global, "_test_marker")
    assert fresh.base.Global.NUM_MATCHES_IN_GAME == 5  # kein Spar-Modus in Match 3
    assert str(TARGET.resolve()) in fresh.base.__file__


def test_kaggle3_missing_folder_raises(tmp_path):
    from scripts.kaggle3_opponent import Kaggle3Opponent

    with pytest.raises(FileNotFoundError):
        Kaggle3Opponent("player_0", bot_dir=tmp_path)
