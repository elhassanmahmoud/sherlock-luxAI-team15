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
    with pytest.raises(SystemExit):
        b.build("schueler=ens8", tmp_path / "x.zip")
    with pytest.raises(ValueError):
        b.build("unbekannt", tmp_path / "y.zip")
