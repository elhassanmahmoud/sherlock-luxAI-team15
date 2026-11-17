"""Kurspaket "reiner Schüler" (scripts/build_student_package.py, 17.11.2026)."""
import io
import zipfile

import pytest

from scripts import build_student_package as b


def _student():
    from agents.sherlock_r3t.agent import STUDENTS

    path = STUDENTS["ens8"]
    if not path.is_file():
        pytest.skip("Schülergewichte liegen nur lokal vor")
    return path


def test_package_layout_and_switches(tmp_path):
    import torch

    src = _student()
    out = tmp_path / "agent.zip"
    sha = b.build("ens8", out)
    assert len(sha) == 64
    with zipfile.ZipFile(out) as z:
        names = set(z.namelist())
        assert {"paths.csv", "sherlock/__init__.py", "sherlock/agents.yaml", "sherlock/main.py",
                "sherlock/imitation_agent.py", "sherlock/weights/agent.pth"} <= names
        assert not any("kaggle" in n.lower() for n in names)
        assert "agents.sherlock.main.Agent_x;agents/sherlock/weights/agent.pth" in z.read("paths.csv").decode()
        for f in (b.SRC).glob("*.py"):
            if f.name != "__init__.py":
                assert z.read(f"sherlock/{f.name}") == f.read_bytes()
        ck = torch.load(io.BytesIO(z.read("sherlock/weights/agent.pth")), map_location="cpu", weights_only=False)
    orig = torch.load(src, map_location="cpu", weights_only=False)
    assert ck["kind"] == "imitation" and ck["cfg"]["imit_stay_bias"] == 1.5 and ck["cfg"]["imit_unstack"] is True
    assert ck["cfg"]["frozen"] is True
    assert not any(k in ck for k in b.DROP_KEYS)
    assert all("/" not in m for m in ck.get("members", []))
    for k, v in orig["policy"].items():
        assert torch.equal(ck["policy"][k], v)
    for m_new, m_old in zip(ck["imitation_ensemble"], orig["imitation_ensemble"]):
        for k, v in m_old["policy"].items():
            assert torch.equal(m_new["policy"][k], v)
    # Bau ist reproduzierbar
    assert b.build("ens8", tmp_path / "again.zip") == sha


def test_course_agent_plays_student_with_switches(tmp_path):
    import numpy as np

    _student()
    out = tmp_path / "agent.zip"
    b.build("ens8", out)
    with zipfile.ZipFile(out) as z:
        z.extract("sherlock/weights/agent.pth", tmp_path)
    from agents.sherlock.main import Agent_x

    agent = Agent_x("player_0", agent_path=str(tmp_path / "sherlock/weights/agent.pth"), train=True)
    student = agent._imitation
    assert student is not None and student.cfg.imit_stay_bias == 1.5 and student.cfg.imit_unstack
    assert len(student.extra_nets) == 1
    before = (tmp_path / "sherlock/weights/agent.pth").read_bytes()
    agent.save_agent()
    agent.update(0, None, 0.0, np.zeros((16, 3), int), True, None)
    assert (tmp_path / "sherlock/weights/agent.pth").read_bytes() == before


def test_package_refuses_protected_targets(tmp_path):
    _student()
    for target in (b.ROOT / "dist/agent.zip", b.ROOT / "Gruppe15.zip", b.R3_DIR / "neu.zip",
                   b.SRC / "weights" / "neu.zip"):
        with pytest.raises(SystemExit):
            b.build("ens8", target)
    with pytest.raises(ValueError):
        b.build("ens8", tmp_path / "x.zip", {"gibt_es_nicht": 1})


def test_package_keeps_beast_switches(tmp_path):
    """17.11.2026, abends: Text- und Zahlenschalter der Taktikschicht und des Matchende-Sturms landen im Paket."""
    import torch

    _student()
    out = tmp_path / "agent.zip"
    b.build("ens8", out, switches={"imit_stay_bias": 1.0, "imit_unstack": True, "imit_hold_points": True,
                                   "imit_end_fill": 10, "imit_tactics": "granate+sog"})
    with zipfile.ZipFile(out) as z:
        assert "sherlock/tactics_layer.py" in z.namelist()
        ck = torch.load(io.BytesIO(z.read("sherlock/weights/agent.pth")), map_location="cpu", weights_only=False)
    assert ck["cfg"]["imit_end_fill"] == 10 and ck["cfg"]["imit_tactics"] == "granate+sog"
