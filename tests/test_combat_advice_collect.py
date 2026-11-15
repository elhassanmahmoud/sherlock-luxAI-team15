"""Dispatch, teacher history, canonical cache alignment, and exclusive archive admission; no real game."""
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import collect_combat_advice as c
from agents.sherlock import cnn_model


def obs(step, team):
    pos = np.zeros((2, 3, 2), dtype=int)
    pos[team, 1] = [4, 7]
    energy = np.full((2, 3), -1, int)
    energy[team, 1] = 85
    mask = np.zeros((2, 3), bool)
    mask[team, :2] = True  # uid 0 is marked alive but already negative; removed before execution.
    return dict(steps=step, match_steps=step % 101, team_wins=np.array([2, 1]),
                units_mask=mask, units=dict(position=pos, energy=energy))


class Actor:
    def __init__(self):
        self.belief = SimpleNamespace(mirrored=True)
        self.team_id = 1

    def new_game(self, side):
        assert side == "player_1"

    def set_env_cfg(self, cfg):
        pass

    def act(self, step, public):
        a = np.zeros((3, 3), int)
        if step % 101 == 0:
            self._prev_ctx = None
            return a
        ctx = dict(step=step, match_step=step % 101, ally_ene=[-1, 85, -1],
                   ally_pos=np.array([[1, 1], [16, 19], [-1, -1]]))
        self._prev_ctx = ctx
        self._cache = (step, ctx, [0, 1], {1: np.full(79, .5)}, {1: np.ones(6, bool)}, {})
        a[1] = [5, -2, 3] if step % 2 else [1, 0, 0]
        return a


class Teacher:
    def __init__(self):
        self.played = []

    def set_env_cfg(self, cfg):
        pass

    def act(self, step, public):
        assert len(self.played) == step
        labels = np.zeros((3, 3), int)
        labels[1] = [5, 1, -2]
        return labels

    def remember_played_actions(self, played):
        self.played.append(played.copy())


class Course:
    def __init__(self, fail_at=None):
        self.step_ix = 0
        self.fail_at = fail_at

    def boards(self):
        return {k: obs(self.step_ix, t) for t, k in enumerate(c.SIDES)}

    def reset(self, seed):
        return self.boards(), {"params": {"unit_sap_range": 3}}

    def step(self, acts):
        i = self.step_ix
        actual = acts["player_1"][1]
        expected = [0, 0, 0] if i % 101 == 0 else ([5, -2, 3] if i % 2 else [1, 0, 0])
        np.testing.assert_array_equal(actual, expected)
        if i == self.fail_at:
            raise RuntimeError("env.step failed")
        self.step_ix += 1
        done = self.step_ix == 303
        return self.boards(), {}, dict.fromkeys(c.SIDES, done), dict.fromkeys(c.SIDES, False), {}


def run(env, teacher, monkeypatch):
    monkeypatch.setattr(cnn_model, "map_planes", lambda ctx: np.zeros((16, 24, 24), np.float32))
    opponent = SimpleNamespace(set_env_cfg=lambda cfg: None, act=lambda step, public: np.zeros((3, 3), int))
    return c.play(env, Actor(), opponent, teacher, c.FIRST, "player_1")


def test_full_course_keeps_real_actions_and_reuses_exact_cache(monkeypatch):
    teacher = Teacher()
    arrays, game = run(Course(), teacher, monkeypatch)
    assert len(teacher.played) == 303 and game == dict(sap_range=3, our_wins=1, opp_wins=2)
    assert len(arrays["global_step"]) == 300
    assert arrays["global_step"][:2].tolist() == [1, 2]
    assert arrays["global_step"][-1] == 302
    assert not np.isin([0, 101, 202], arrays["global_step"]).any()
    assert np.all(arrays["uid"] == 1) and np.all(arrays["pos"] == [16, 19])
    assert np.all(arrays["mstep"] == arrays["global_step"][arrays["step"]] % 101)
    assert arrays["base_act"][:2].tolist() == [5, 2]
    assert arrays["base_sdx"][:2].tolist() == [-3, 0]
    assert arrays["base_sdy"][:2].tolist() == [2, 0]
    assert np.all(arrays["act"] == 5) and np.all(arrays["sdx"] == 2) and np.all(arrays["sdy"] == -1)


def test_sync_only_after_env_success(monkeypatch):
    teacher = Teacher()
    with pytest.raises(RuntimeError, match="env.step failed"):
        run(Course(fail_at=2), teacher, monkeypatch)
    assert len(teacher.played) == 2


def test_publication_rejects_invalid_or_mismatched_resume(tmp_path, monkeypatch):
    seed, side, binding = c.FIRST, "player_1", "fixed-source"
    assert [c.opponent_for(seed + i) for i in range(4)] == ["kaggle3", "solution92", "v14", "kaggle3"]
    arrays, game = run(Course(), Teacher(), monkeypatch)
    path = tmp_path / c.filename(seed, side)
    meta = dict(seed=seed, side=side, opponent="kaggle3", steps=303, policy="v14", teacher="kaggle3",
                teacher_history="played_v14_actions", protocol_sha256=binding, arrays_sha256="invalid", **game)

    def write(f):
        np.savez_compressed(f, meta=c.canonical_json(meta).decode(), **arrays)

    def check(p):
        return c.check_archive(p, seed, side, binding)

    with pytest.raises(ValueError, match="altered"):
        c.publish(path, write, check)
    assert not path.exists()
    meta["arrays_sha256"] = c.array_digest(arrays)
    assert c.publish(path, write, check) and check(path) == 300
    assert not c.publish(path, write, check)
    with pytest.raises(ValueError, match="identity"):
        c.check_archive(path, seed, side, "other")
    assert not list(tmp_path.glob(".advice-*"))
