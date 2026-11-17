"""Paket R3 + Taktikschicht (scripts/build_r3t_package.py, 17.11.2026)."""
import zipfile

import pytest

from scripts import build_r3t_package as b


def test_package_keeps_r3_files_and_adds_tactics(tmp_path):
    out = tmp_path / "agent.zip"
    b.build("granate,sog", out)
    with zipfile.ZipFile(b.R3_ZIP) as src, zipfile.ZipFile(out) as dst:
        names = set(dst.namelist())
        assert names == set(src.namelist()) | {"sherlock/r3t_tactics.py"}
        for name in src.namelist():
            if name != "sherlock/main.py":
                assert src.read(name) == dst.read(name), name
        main = dst.read("sherlock/main.py").decode()
        assert "SPEC = 'granate,sog'" in main and "from .r3t_tactics import" in main
        assert dst.read("sherlock/r3t_tactics.py") == (b.ROOT / "agents/sherlock_r3t/tactics.py").read_bytes()


def test_package_refuses_protected_targets_and_student(tmp_path):
    for target in (b.ROOT / "dist/agent.zip", b.ROOT / "Gruppe15.zip", b.R3_ZIP.parent / "neu.zip"):
        with pytest.raises(SystemExit):
            b.build("granate", target)
    with pytest.raises(ValueError):
        b.build("unbekannt", tmp_path / "y.zip")


def test_package_with_student_adds_code_and_weights(tmp_path):
    import io

    import torch

    from agents.sherlock_r3t.agent import STUDENTS

    if not STUDENTS["ens8"].is_file():
        pytest.skip("Schülergewichte liegen nur lokal vor")
    out = tmp_path / "agent.zip"
    b.build("schueler=ens8,granate", out)
    with zipfile.ZipFile(b.R3_ZIP) as src, zipfile.ZipFile(out) as dst:
        names = set(dst.namelist())
        assert "sherlock/stud/imitation_agent.py" in names and "sherlock/stud/__init__.py" in names
        old = torch.load(io.BytesIO(src.read("sherlock/weights/agent.pth")), weights_only=True)
        new = torch.load(io.BytesIO(dst.read("sherlock/weights/agent.pth")), weights_only=True)
        assert new["v14"] == old["v14"] and new["r3"] == old["r3"] and new["kind"] == old["kind"]
        assert new["student"] == STUDENTS["ens8"].read_bytes()
        assert "STUDENT_SHA = '" in dst.read("sherlock/main.py").decode()
