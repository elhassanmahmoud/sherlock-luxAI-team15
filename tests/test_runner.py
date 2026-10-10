"""Der Agent ist ueber lux/runner.py ladbar und spielt ein echtes Spiel durch."""
import inspect
import shutil

import pandas as pd

import lux.runner as runner
from tests.conftest import ROOT

GROUP = 15
REQUIRED = ["act", "update", "save_agent", "load_agent", "set_to_eval_mode", "set_env_cfg"]


def paths_row():
    df = pd.read_csv(ROOT / "Paths.csv", encoding="cp1252", sep=";")
    return df.loc[df["Moodle Gruppe"] == GROUP].iloc[0]


def test_paths_csv_entry_resolves_to_agent_class():
    row = paths_row()
    cls = runner.load_class_from_path(row["Import_Path"])
    assert cls.__name__ == "Agent_x"
    for m in REQUIRED:
        assert callable(getattr(cls, m, None)), m
    assert "agent_path" in inspect.signature(cls.__init__).parameters
    for col in ("Load_Path_P0", "Load_Path_P1"):
        assert (ROOT / row[col]).is_file(), f"{row[col]} fehlt"


def test_short_real_game_via_runner(tmp_path, monkeypatch):
    """Ein Spiel ueber run_agents (ohne Training) - Replay landet im tmp-Ordner."""
    shutil.copy(ROOT / "Paths.csv", tmp_path / "Paths.csv")
    for p in ("agents",):
        (tmp_path / p).symlink_to(ROOT / p)
    monkeypatch.setattr(runner, "_base_dir", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    runner.run_agents(GROUP, 1, games_to_play=1, train=False)
    replays = list((tmp_path / "replays" / f"{GROUP}_vs_1").glob("*.json"))
    assert replays, "kein Replay geschrieben"


def test_short_game_both_sides_without_errors(env):
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent, play_game

    a = Agent_x("player_0", agent_path=str(ROOT / paths_row()["Load_Path_P0"]), train=False)
    a.set_to_eval_mode()
    for side, opp in (("player_0", "default"), ("player_1", "solution92")):
        o = make_opponent(opp, "player_1" if side == "player_0" else "player_0")
        r = play_game(env, a, o, seed=11, our_side=side, train=False)
        assert r["steps"] > 300 and r["unit_steps"] > 0
        assert r["invalid_frac"] == 0.0  # Maske verhindert wirkungslose Zuege
