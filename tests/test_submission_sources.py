"""Source selection uses disposable files, without loading models or an engine."""
import pytest

from scripts import build_submission


@pytest.fixture
def source_tree(tmp_path, monkeypatch):
    source = tmp_path / "sherlock"
    weights = source / "weights"
    weights.mkdir(parents=True)
    for name in ("__init__.py", "belief.py", "config.py", "main.py", "reward.py"):
        (source / name).write_text("# source fixture\n")
    for side in (0, 1):
        (weights / f"agent_p{side}.pth").write_bytes(f"dummy-side-{side}".encode())
    monkeypatch.setattr(build_submission, "SRC", source)
    return source


@pytest.mark.parametrize("name", [
    "config 2.py", "reward 2.py", "agent-copy.py", "agent.old.py", "2agent.py",
    ".py", "class.py", "for.py", "async.py", "None.py", "True.py",
])
def test_sources_excludes_non_module_names_and_hard_keywords(source_tree, tmp_path, name):
    duplicate = source_tree / name
    duplicate.write_text("# preserve this local file\n")

    files, _, _ = build_submission.sources(tmp_path / "output" / "agent.zip", None)

    assert [path.name for path in files] == ["belief.py", "config.py", "main.py", "reward.py"]
    assert duplicate.read_text() == "# preserve this local file\n"


def test_sources_keeps_identifiers_including_unicode_and_soft_keywords(source_tree, tmp_path):
    for name in ("_helper.py", "agent2.py", "case.py", "match.py", "type.py",
                 "π_policy.py", "license.py", "provenance.py"):
        (source_tree / name).write_text("# importable module\n")

    files, _, _ = build_submission.sources(tmp_path / "agent.zip", None)

    assert [path.name for path in files] == [
        "_helper.py", "agent2.py", "belief.py", "case.py", "config.py", "license.py",
        "main.py", "match.py", "provenance.py", "reward.py", "type.py", "π_policy.py",
    ]


@pytest.mark.parametrize("from_run", [False, True])
def test_sources_preserves_weight_selection_and_separate_package_initializer(
        source_tree, tmp_path, from_run):
    run = tmp_path / "run" if from_run else None
    if run is not None:
        (run / "weights").mkdir(parents=True)
        shared = run / "weights" / "agent.pth"
        shared.write_bytes(b"dummy-shared-run-weight")
        expected_weights = [shared, shared]
    else:
        expected_weights = [source_tree / "weights" / f"agent_p{side}.pth" for side in (0, 1)]
    before = {path: path.read_bytes() for path in expected_weights}
    target = tmp_path / "output" / "agent.zip"

    files, weights, out = build_submission.sources(target, run)

    assert source_tree / "__init__.py" not in files
    assert weights == expected_weights
    assert {path: path.read_bytes() for path in weights} == before
    assert out == target.resolve()
    assert out.parent.is_dir()
    assert not out.exists()
