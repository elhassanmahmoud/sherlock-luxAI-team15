"""Default publication copies the admitted ZIP. Explicit builds retain their own sources."""
from hashlib import sha256
import os
from pathlib import Path
import sys
import zipfile

import pytest

from scripts import build_submission as builder


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    source = tmp_path / "agents/sherlock"
    monkeypatch.setattr(builder, "SRC", source)
    (source / "weights").mkdir(parents=True)
    (source / "main.py").write_text("# fixture\n")
    for side in (0, 1):
        (source / f"weights/agent_p{side}.pth").write_bytes(b"old")
    release = tmp_path / builder.FINAL_RELEASE
    release.parent.mkdir(parents=True)
    with zipfile.ZipFile(release, "x") as archive:
        archive.writestr("release-marker", b"published")
    monkeypatch.setattr(builder, "FINAL_ZIP_SHA256", sha256(release.read_bytes()).hexdigest())
    return release


def test_final_release_is_k_and_r3_stays_available():
    """17.11.2026: Abgabe ist K; das R3-Release bleibt als Rückweg mit seiner Prüfsumme erhalten."""
    real_root = Path(builder.__file__).resolve().parents[1]
    k = real_root / builder.FINAL_RELEASE
    r3 = real_root / builder.R3_RELEASE
    assert builder.FINAL_RELEASE == "experiments/releases/20261117_sherlock_v16/agent.zip"
    assert sha256(k.read_bytes()).hexdigest() == builder.FINAL_ZIP_SHA256
    assert sha256(r3.read_bytes()).hexdigest() == builder.R3_ZIP_SHA256


def invoke(monkeypatch, *options):
    monkeypatch.setattr(sys, "argv", ["build_submission", "--no-check", *map(str, options)])
    builder.main()


def test_default_copies_the_verified_release(project, monkeypatch):
    invoke(monkeypatch)
    assert (builder.ROOT / "dist/agent.zip").read_bytes() == project.read_bytes()


@pytest.mark.parametrize("fault", ["changed", "missing"])
def test_damaged_release_preserves_existing_output(project, monkeypatch, fault):
    out = builder.ROOT / "existing.zip"
    out.write_bytes(b"original")
    if fault == "changed":
        project.write_bytes(b"invalid")
    else:
        project.unlink()
    with pytest.raises(SystemExit):
        invoke(monkeypatch, "--out", out)
    assert out.read_bytes() == b"original"


@pytest.mark.parametrize("target", ["raw_weight", "raw_hardlink", "release", "release_hardlink", "symlink"])
def test_protected_output_is_rejected(project, monkeypatch, target):
    weight = builder.SRC / "weights/agent_p0.pth"
    out = builder.ROOT / "alias.zip"
    if target == "raw_weight":
        out = weight
    elif target == "release":
        out = project
    elif target == "symlink":
        out.symlink_to(project)
    else:
        os.link(weight if target == "raw_hardlink" else project, out)
    old = out.read_bytes()
    with pytest.raises(SystemExit):
        invoke(monkeypatch, "--out", out)
    assert out.read_bytes() == old


@pytest.mark.parametrize(("options", "member", "data"), [
    (["--team-name", "other"], "other/weights/agent_p0.pth", b"old"),
    (["--group", "2"], "sherlock/weights/agent_p0.pth", b"old"),
    (["--from-run", "run"], "sherlock/weights/agent_p0.pth", b"explicit"),
])
def test_explicit_build_uses_requested_sources(project, monkeypatch, options, member, data):
    monkeypatch.chdir(builder.ROOT)
    (Path("run") / "weights").mkdir(parents=True)
    (Path("run") / "weights/agent.pth").write_bytes(b"explicit")
    project.unlink()
    invoke(monkeypatch, *options)
    with zipfile.ZipFile(builder.ROOT / "dist/agent.zip") as archive:
        assert archive.read(member) == data
