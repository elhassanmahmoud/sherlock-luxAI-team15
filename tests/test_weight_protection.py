"""Training and packaging must leave the released checkpoints untouched."""
import sys
import zipfile

import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x
from scripts import build_submission, train


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Even the old, unsafe implementation can only overwrite disposable files."""
    root = tmp_path / "project"
    weights = root / "agents" / "sherlock" / "weights"
    weights.mkdir(parents=True)
    (weights.parent / "main.py").write_text("# packaging fixture\n")
    (weights / "agent_p0.pth").write_bytes(b"released-player-zero")
    (weights / "agent_p1.pth").write_bytes(b"released-player-one")
    monkeypatch.setattr(train, "ROOT", root)
    monkeypatch.setattr(train, "WEIGHTS", weights)
    monkeypatch.setattr(build_submission, "SRC", weights.parent)
    return root, weights


def invoke(monkeypatch, module, *args):
    monkeypatch.setattr(sys, "argv", [module.__name__, *map(str, args)])
    module.main()


def released_bytes(weights):
    return {p.name: p.read_bytes() for p in weights.iterdir()}


def small_checkpoint(path):
    agent = Agent_x("player_0", cfg=AgentConfig(
        hidden=32, buffer_capacity=1000, learn_start=16, batch_size=16), seed=1)
    agent.save_agent(str(path))
    return path


def test_default_training_creates_separate_runs_without_touching_release(sandbox, monkeypatch):
    root, weights = sandbox
    before = released_bytes(weights)
    for _ in range(2):
        invoke(monkeypatch, train, "--games", 0)
    assert released_bytes(weights) == before
    runs = list((root / "experiments" / "runs").iterdir())
    assert len(runs) == 2
    for run in runs:
        assert (run / "weights" / "agent_p0.pth").is_file()
        assert (run / "weights" / "agent_p1.pth").is_file()
        assert (run / "train.csv").is_file()


def test_resume_selfplay_best_and_final_saves_stay_in_new_run(sandbox, tmp_path, monkeypatch):
    _, weights = sandbox
    source = small_checkpoint(tmp_path / "source.pth")
    before_source = source.read_bytes()
    before_release = released_bytes(weights)
    out = tmp_path / "new-run"
    invoke(monkeypatch, train, "--games", 1, "--resume", source,
           "--output-dir", out, "--opponent", "self", "--self-update", 1,
           "--eval-every", 1, "--eval-games", 1)
    assert released_bytes(weights) == before_release
    assert source.read_bytes() == before_source
    names = {p.name for p in (out / "weights").iterdir()}
    assert names == {"agent_p0.pth", "agent_p1.pth", "agent_best.pth", "agent_selfplay_snapshot.pth"}
    ckpt = torch.load(out / "weights" / "agent_p0.pth", weights_only=False)
    assert ckpt["learn_steps"] > 0
    assert ckpt["cfg"]["hidden"] == 32
    assert (out / "weights" / "agent_p0.pth").read_bytes() == (out / "weights" / "agent_p1.pth").read_bytes()


@pytest.mark.parametrize("failure", [KeyboardInterrupt, RuntimeError])
def test_interrupted_training_saves_only_to_run(sandbox, tmp_path, monkeypatch, failure):
    _, weights = sandbox
    before = released_bytes(weights)
    out = tmp_path / "interrupted-run"

    def interrupted_game(*args, **kwargs):
        raise failure("test interruption")

    monkeypatch.setattr(train, "play_game", interrupted_game)
    if failure is RuntimeError:
        with pytest.raises(RuntimeError, match="test interruption"):
            invoke(monkeypatch, train, "--games", 1, "--output-dir", out)
    else:
        invoke(monkeypatch, train, "--games", 1, "--output-dir", out)
    assert released_bytes(weights) == before
    assert (out / "weights" / "agent_p0.pth").is_file()
    assert (out / "weights" / "agent_p1.pth").is_file()


@pytest.mark.parametrize("target", ["protected", "child", "alias", "existing"])
def test_training_rejects_protected_or_existing_output_before_writing(sandbox, tmp_path, monkeypatch, capsys, target):
    _, weights = sandbox
    alias = tmp_path / "alias"
    alias.symlink_to(weights, target_is_directory=True)
    existing = tmp_path / "existing-run"
    existing.mkdir()
    sentinel = existing / "train.csv"
    sentinel.write_text("previous results")
    out = {"protected": weights, "child": weights / "new-run",
           "alias": alias / "new-run", "existing": existing}[target]
    before = released_bytes(weights)
    with pytest.raises(SystemExit) as exc:
        invoke(monkeypatch, train, "--games", 0, "--output-dir", out)
    assert exc.value.code != 0
    assert "unrecognized arguments" not in capsys.readouterr().err
    assert released_bytes(weights) == before
    assert sentinel.read_text() == "previous results"


@pytest.mark.parametrize("source_kind", ["missing", "ensemble", "bad_features", "bad_actions", "bad_ensemble"])
def test_resume_refuses_invalid_source_without_creating_run(sandbox, tmp_path, monkeypatch, capsys, source_kind):
    _, weights = sandbox
    source = tmp_path / "source.pth"
    if source_kind != "missing":
        small_checkpoint(source)
        ckpt = torch.load(source, weights_only=False)
        if source_kind in ("ensemble", "bad_ensemble"):
            ckpt["ensemble"] = [ckpt["q"]]
        if source_kind in ("bad_features", "bad_ensemble"):
            ckpt["feature_dim"] += 1
        if source_kind == "bad_actions":
            ckpt["n_actions"] += 1
        torch.save(ckpt, source)
    out = tmp_path / "new-run"
    before = released_bytes(weights)
    with pytest.raises(SystemExit) as exc:
        invoke(monkeypatch, train, "--games", 0, "--resume", source, "--output-dir", out)
    assert exc.value.code != 0
    assert "unrecognized arguments" not in capsys.readouterr().err
    assert not out.exists()
    assert released_bytes(weights) == before


def test_zip_hardlink_to_nested_release_checkpoint_is_rejected(sandbox, tmp_path, monkeypatch):
    _, weights = sandbox
    backup = weights / "backup" / "agent.pth"
    backup.parent.mkdir()
    backup.write_bytes(b"protected-backup")
    out = tmp_path / "output.zip"
    out.hardlink_to(backup)
    with pytest.raises(SystemExit):
        invoke(monkeypatch, build_submission, "--out", out, "--no-check")
    assert backup.read_bytes() == b"protected-backup"


@pytest.mark.parametrize("operation", ["training", "packaging"])
def test_case_alias_cannot_create_output_inside_protected_directory(sandbox, monkeypatch, operation):
    _, weights = sandbox
    alias = weights.with_name("WEIGHTS")
    if not alias.exists():
        pytest.skip("filesystem distinguishes case")
    out = alias / ("new-run" if operation == "training" else "candidate.zip")
    with pytest.raises(SystemExit):
        if operation == "training":
            invoke(monkeypatch, train, "--games", 0, "--output-dir", out)
        else:
            invoke(monkeypatch, build_submission, "--out", out, "--no-check")
    assert not out.exists()


@pytest.mark.parametrize("split", [False, True])
def test_build_from_run_packages_selected_weights_without_installing(sandbox, tmp_path, monkeypatch, split):
    _, weights = sandbox
    before = released_bytes(weights)
    run = tmp_path / "candidate"
    (run / "weights").mkdir(parents=True)
    if split:
        (run / "weights" / "agent_p0.pth").write_bytes(b"candidate-zero")
        (run / "weights" / "agent_p1.pth").write_bytes(b"candidate-one")
        expected = [b"candidate-zero", b"candidate-one"]
    else:
        (run / "weights" / "agent.pth").write_bytes(b"candidate-shared")
        expected = [b"candidate-shared", b"candidate-shared"]
    out = tmp_path / "candidate.zip"
    invoke(monkeypatch, build_submission, "--from-run", run, "--out", out, "--no-check")
    assert released_bytes(weights) == before
    with zipfile.ZipFile(out) as z:
        assert [z.read(f"sherlock/weights/agent_p{i}.pth") for i in (0, 1)] == expected


def test_build_missing_second_checkpoint_does_not_partially_install(sandbox, tmp_path, monkeypatch):
    _, weights = sandbox
    before = released_bytes(weights)
    run = tmp_path / "incomplete"
    (run / "weights").mkdir(parents=True)
    (run / "weights" / "agent_p0.pth").write_bytes(b"candidate-zero")
    out = tmp_path / "candidate.zip"
    with pytest.raises(SystemExit):
        invoke(monkeypatch, build_submission, "--from-run", run, "--out", out, "--no-check")
    assert released_bytes(weights) == before
    assert not out.exists()


@pytest.mark.parametrize("alias_kind", ["direct", "symlink", "hardlink"])
def test_zip_output_cannot_overwrite_released_weight(sandbox, tmp_path, monkeypatch, alias_kind):
    _, weights = sandbox
    before = released_bytes(weights)
    out = weights / "agent_p0.pth"
    if alias_kind == "symlink":
        out = tmp_path / "output.zip"
        out.symlink_to(weights / "agent_p0.pth")
    elif alias_kind == "hardlink":
        out = tmp_path / "output.zip"
        out.hardlink_to(weights / "agent_p0.pth")
    with pytest.raises(SystemExit):
        invoke(monkeypatch, build_submission, "--out", out, "--no-check")
    assert released_bytes(weights) == before


@pytest.mark.parametrize("alias_kind", ["direct", "hardlink"])
def test_zip_output_cannot_overwrite_selected_run_input(sandbox, tmp_path, monkeypatch, alias_kind):
    run = tmp_path / "candidate"
    (run / "weights").mkdir(parents=True)
    source = run / "weights" / "agent.pth"
    source.write_bytes(b"candidate-shared")
    out = source
    if alias_kind == "hardlink":
        out = tmp_path / "output.zip"
        out.hardlink_to(source)
    with pytest.raises(SystemExit):
        invoke(monkeypatch, build_submission, "--from-run", run, "--out", out, "--no-check")
    assert source.read_bytes() == b"candidate-shared"


@pytest.mark.parametrize("alias_kind", ["symlink", "hardlink"])
def test_save_checks_all_targets_before_writing_first_checkpoint(sandbox, tmp_path, alias_kind):
    _, weights = sandbox
    before = released_bytes(weights)
    out = tmp_path / "run-weights"
    out.mkdir()
    (out / "agent_p0.pth").write_bytes(b"previous-run-state")
    second = out / "agent_p1.pth"
    if alias_kind == "symlink":
        second.symlink_to(weights / "agent_p1.pth")
    else:
        second.hardlink_to(weights / "agent_p1.pth")
    agent = Agent_x("player_0", cfg=AgentConfig(hidden=32, buffer_capacity=1000))
    with pytest.raises(ValueError):
        train.save_all(agent, out)
    assert (out / "agent_p0.pth").read_bytes() == b"previous-run-state"
    assert released_bytes(weights) == before
