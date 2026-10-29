"""Battle-Abgabe: Gruppe15.zip im Format der Prof-Mail, Gewichte werden auch ueber fremde Pfade gefunden."""
import sys
import zipfile

import pytest

from agents.sherlock import main as sherlock_main
from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x, resolve_weights
from scripts import build_submission


def small_checkpoint(path):
    agent = Agent_x("player_0", cfg=AgentConfig(
        hidden=32, buffer_capacity=1000, learn_start=16, batch_size=16, use_sap=False), seed=1)
    agent.env_steps = 123
    agent.save_agent(str(path))
    return path


def test_existing_path_is_used_unchanged(tmp_path):
    p = small_checkpoint(tmp_path / "agent.pth")
    assert resolve_weights(str(p)) == str(p)
    assert resolve_weights(None) is None


def test_missing_path_falls_back_to_file_next_to_main(tmp_path, monkeypatch):
    pkg = tmp_path / "agents" / "Gruppe15"
    pkg.mkdir(parents=True)
    small_checkpoint(pkg / "agent.pth")
    monkeypatch.setattr(sherlock_main, "__file__", str(pkg / "main.py"))
    monkeypatch.chdir(tmp_path)  # Prof startet in der Projektwurzel, Pfad ohne agents/
    assert resolve_weights("Gruppe15/agent.pth") == str(pkg / "agent.pth")
    a = Agent_x("player_1", agent_path="Gruppe15/agent.pth")
    # Gewichte und Config kommen aus der Datei, nicht aus den Standardwerten
    assert a.env_steps == 123 and a.cfg.hidden == 32 and not a.cfg.use_sap


def test_no_fallback_without_file_next_to_main(tmp_path, monkeypatch):
    monkeypatch.setattr(sherlock_main, "__file__", str(tmp_path / "main.py"))
    path = str(tmp_path / "run" / "weights" / "agent.pth")
    assert resolve_weights(path) == path  # neues Training startet weiter frisch
    assert Agent_x("player_0", agent_path=path).env_steps == 0


def test_repo_package_has_no_weights_next_to_main():
    """Sonst koennte der Rueckfall im Repo eine falsche Datei laden."""
    assert not list(build_submission.SRC.glob("*.pth"))


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    src = tmp_path / "project" / "agents" / "sherlock"
    (src / "weights").mkdir(parents=True)
    (src / "main.py").write_text("# packaging fixture\n")
    (src / "belief.py").write_text("# packaging fixture\n")
    monkeypatch.setattr(build_submission, "SRC", src)
    return src / "weights"


def build(monkeypatch, out, *args):
    monkeypatch.setattr(sys, "argv", ["build_submission", "--battle", "--out", str(out), "--no-check", *args])
    build_submission.main()
    with zipfile.ZipFile(out) as z:
        return {n: z.read(n) for n in z.namelist()}


def test_battle_zip_with_identical_weights_ships_one_agent_pth(sandbox, tmp_path, monkeypatch):
    for side in (0, 1):
        (sandbox / f"agent_p{side}.pth").write_bytes(b"same-weights")
    files = build(monkeypatch, tmp_path / "Gruppe15.zip")
    assert sorted(files) == ["Gruppe15/LIESMICH.txt", "Gruppe15/__init__.py", "Gruppe15/agent.pth",
                             "Gruppe15/agents.yaml", "Gruppe15/belief.py", "Gruppe15/main.py"]
    assert files["Gruppe15/agent.pth"] == b"same-weights"
    readme = files["Gruppe15/LIESMICH.txt"].decode()
    assert "Gruppe15.main.Agent_x" in readme
    assert "15;Gruppe15.main.Agent_x;Gruppe15/agent.pth;Gruppe15/agent.pth" in readme
    assert (sandbox / "agent_p0.pth").read_bytes() == b"same-weights"


def test_battle_zip_with_different_weights_ships_both_sides(sandbox, tmp_path, monkeypatch):
    (sandbox / "agent_p0.pth").write_bytes(b"zero")
    (sandbox / "agent_p1.pth").write_bytes(b"one")
    files = build(monkeypatch, tmp_path / "Gruppe15.zip")
    assert files["Gruppe15/agent_0.pth"] == b"zero" and files["Gruppe15/agent_1.pth"] == b"one"
    assert "Gruppe15/agent.pth" not in files
    assert "LOAD_PATH_P1: 'Gruppe15/agent_1.pth'" in files["Gruppe15/agents.yaml"].decode()


def test_battle_zip_cannot_overwrite_released_weight(sandbox, monkeypatch):
    for side in (0, 1):
        (sandbox / f"agent_p{side}.pth").write_bytes(b"released")
    with pytest.raises(SystemExit):
        build(monkeypatch, sandbox / "agent_p0.pth")
    assert (sandbox / "agent_p0.pth").read_bytes() == b"released"
