"""--battle ohne --from-run verpackt die Finalabgabe bytegleich ins Format der Battle-Mail (19.11.2026)."""
from hashlib import sha256
from pathlib import Path
import sys
import zipfile

import pytest

from scripts import build_submission as builder

RELEASE_FILES = {
    "paths.csv": b"Moodle Gruppe;Import_Path;Load_Path_P0;Load_Path_P1\n15;agents.sherlock.main.Agent_x;x;x\n",
    "sherlock/__init__.py": b"",
    "sherlock/main.py": b"# main of the release\n",
    "sherlock/belief.py": b"# belief of the release\n",
    "sherlock/agents.yaml": b"IMPORT_PATH: 'agents.sherlock.main.Agent_x'\n",
    "sherlock/weights/agent.pth": b"released-weights",
}


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    source = tmp_path / "agents/sherlock"
    (source / "weights").mkdir(parents=True)
    for side in (0, 1):
        (source / f"weights/agent_p{side}.pth").write_bytes(b"v14")
    monkeypatch.setattr(builder, "SRC", source)
    release = tmp_path / builder.FINAL_RELEASE
    release.parent.mkdir(parents=True)
    with zipfile.ZipFile(release, "x") as archive:
        for name, data in RELEASE_FILES.items():
            archive.writestr(name, data)
    monkeypatch.setattr(builder, "FINAL_ZIP_SHA256", sha256(release.read_bytes()).hexdigest())
    return tmp_path


def run(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["build_submission", "--battle", "--no-check", *args])
    builder.main()


def members(path):
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


def test_release_is_repackaged_bytewise(project, monkeypatch):
    out = project / "out" / "Gruppe15.zip"
    run(monkeypatch, "--out", str(out))
    files = members(out)
    assert sorted(files) == ["Gruppe15/LIESMICH.txt", "Gruppe15/__init__.py", "Gruppe15/agent.pth",
                             "Gruppe15/agents.yaml", "Gruppe15/belief.py", "Gruppe15/main.py"]
    assert files["Gruppe15/agent.pth"] == b"released-weights"  # nicht die V14-Gewichte aus agents/sherlock/weights
    assert files["Gruppe15/main.py"] == RELEASE_FILES["sherlock/main.py"]
    assert files["Gruppe15/belief.py"] == RELEASE_FILES["sherlock/belief.py"]
    yaml = files["Gruppe15/agents.yaml"].decode()
    assert "IMPORT_PATH: 'Gruppe15.main.Agent_x'" in yaml and "LOAD_PATH_P1: 'Gruppe15/agent.pth'" in yaml
    readme = files["Gruppe15/LIESMICH.txt"].decode()
    assert "15;Gruppe15.main.Agent_x;Gruppe15/agent.pth;Gruppe15/agent.pth" in readme
    assert "Finalabgabe" in readme and builder.FINAL_ZIP_SHA256[:8] in readme


def test_repackaging_is_reproducible(project, monkeypatch):
    first, second = project / "a" / "Gruppe15.zip", project / "b" / "Gruppe15.zip"
    run(monkeypatch, "--out", str(first))
    run(monkeypatch, "--out", str(second))
    assert first.read_bytes() == second.read_bytes()


def test_default_output_keeps_historic_battle_zip(project, monkeypatch):
    historic = project / "Gruppe15.zip"
    historic.write_bytes(b"V14 battle upload")
    run(monkeypatch)
    assert historic.read_bytes() == b"V14 battle upload"
    assert members(project / "dist" / "Gruppe15.zip")["Gruppe15/agent.pth"] == b"released-weights"


def test_tampered_release_is_refused_and_output_kept(project, monkeypatch):
    out = project / "Gruppe15_final.zip"
    out.write_bytes(b"previous")
    monkeypatch.setattr(builder, "FINAL_ZIP_SHA256", "0" * 64)
    with pytest.raises(SystemExit):
        run(monkeypatch, "--out", str(out))
    assert out.read_bytes() == b"previous"


def test_half_only_with_from_run(project, monkeypatch):
    with pytest.raises(SystemExit):
        run(monkeypatch, "--half", "--out", str(project / "x.zip"))
    assert not (project / "x.zip").exists()


def test_real_final_release_keeps_every_file(tmp_path, monkeypatch):
    real = Path(builder.__file__).resolve().parents[1] / builder.FINAL_RELEASE
    out = tmp_path / "Gruppe15.zip"
    run(monkeypatch, "--out", str(out))
    with zipfile.ZipFile(real) as z:
        source = {n: z.read(n) for n in z.namelist() if n.startswith("sherlock/") and not n.endswith("/")}
    files = members(out)
    assert files["Gruppe15/agent.pth"] == source["sherlock/weights/agent.pth"]
    for name, data in source.items():
        rel = name[len("sherlock/"):]
        if rel not in ("agents.yaml", "weights/agent.pth"):
            assert files[f"Gruppe15/{rel}"] == data, rel
    assert len(files) == len(source) + 1  # agents.yaml neu, weights/agent.pth verschoben, LIESMICH.txt dazu
