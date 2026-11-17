"""Gewichtspfad im Nachspiel-Werkzeug scripts/xversion_replay.py (17.11.2026)."""
import pytest

from scripts.xversion_replay import weights_path


def test_battle_layout_uses_file_next_to_main(tmp_path):
    (tmp_path / "agents" / "Gruppe15").mkdir(parents=True)
    (tmp_path / "agents" / "Gruppe15" / "agent.pth").write_bytes(b"x")
    assert weights_path(str(tmp_path), "Gruppe15") == "Gruppe15/agent.pth"


def test_course_package_layout_reads_paths_csv(tmp_path):
    w = tmp_path / "agents" / "sherlock" / "weights"
    w.mkdir(parents=True)
    (w / "agent.pth").write_bytes(b"x")
    (tmp_path / "agents" / "paths.csv").write_text(
        "Moodle Gruppe;Import_Path;Load_Path_P0;Load_Path_P1\n"
        "15;agents.sherlock.main.Agent_x;agents/sherlock/weights/agent.pth;agents/sherlock/weights/agent.pth\n")
    assert weights_path(str(tmp_path), "sherlock") == "agents/sherlock/weights/agent.pth"


def test_missing_weights_stop_instead_of_playing_untrained(tmp_path):
    (tmp_path / "agents" / "sherlock").mkdir(parents=True)
    (tmp_path / "agents" / "paths.csv").write_text(
        "Moodle Gruppe;Import_Path;Load_Path_P0;Load_Path_P1\n15;x;agents/sherlock/weights/agent.pth;x\n")
    with pytest.raises(FileNotFoundError):
        weights_path(str(tmp_path), "sherlock")
