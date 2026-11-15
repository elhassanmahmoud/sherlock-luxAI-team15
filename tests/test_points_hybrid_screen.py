"""Pinned inputs and provenance of the three-arm points-hybrid screen."""
from pathlib import Path

import pytest

from scripts import points_hybrid_screen as screen


V14_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
R2_SHA = "23fa6208d76e81940916388b9ee56c1d290693e8febfa53622442b64b0d33f96"
R3_SHA = "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"

ARMS = [
    ("v14", "kaggle3,solution92", None, None),
    ("points_r2", "kaggle3,solution92", "r2.pth", R2_SHA),
    ("points_r3", "kaggle3,solution92,v14", "r3_soft.pth", R3_SHA),
]


def mock_inputs(monkeypatch, weights, model):
    def fake_contract(args):
        assert args.candidate == "v14"
        return dict(candidate="v14", first=args.first, maps=args.maps,
                    opponents=args.opponents.split(","), weights=weights,
                    model=model if args.model else None,
                    engine={"env.py": "1" * 64},
                    sources={"agents/sherlock/main.py": "2" * 64})

    def fake_digest(path):
        assert str(Path(path).relative_to(screen.base.ROOT)) in {
            "scripts/points_hybrid_screen.py", "agents/__init__.py", "scripts/fetch_kaggle3.py",
            "scripts/protocol.py", "scripts/variants.py",
        }
        return "3" * 64

    monkeypatch.setattr(screen.base, "contract", fake_contract)
    monkeypatch.setattr(screen.base, "digest", fake_digest)
    monkeypatch.setattr(screen, "environment", lambda: {"lux_modules": {"env.py": "1" * 64}})


@pytest.mark.parametrize("arm,opponents,filename,model", ARMS)
def test_pinned_screen_inputs_and_manifest(tmp_path, monkeypatch, arm, opponents, filename, model):
    args = screen.settings(arm, tmp_path)
    assert (args.candidate, args.first, args.maps, args.opponents) == (arm, 7278000, 16, opponents)
    model_dir = tmp_path / "experiments/candidates/movement_dagger_20261115"
    assert args.model == (str(model_dir / filename) if filename else None)

    mock_inputs(monkeypatch, V14_SHA, model)
    manifest = screen.study_contract(args)
    assert manifest["candidate"] == arm
    assert manifest["weights"] == V14_SHA
    assert manifest["model"] == model
    assert manifest["opponents"] == opponents.split(",")
    assert manifest["engine"] == {"env.py": "1" * 64}
    assert manifest["environment"] == {"lux_modules": {"env.py": "1" * 64}}
    assert manifest["sources"]["agents/sherlock/main.py"] == "2" * 64
    assert manifest["sources"]["scripts/points_hybrid_screen.py"] == "3" * 64
    expected = {"mode": "points", "student_overrides": {"imit_stay_bias": 1.5, "imit_unstack": True}}
    assert manifest["hybrid"] == (expected if model else None)


@pytest.mark.parametrize("arm,weights,model", [
    ("v14", "0" * 64, None),
    ("points_r2", "0" * 64, R2_SHA),
    ("points_r3", "0" * 64, R3_SHA),
    ("points_r2", V14_SHA, R3_SHA),
    ("points_r3", V14_SHA, R2_SHA),
])
def test_wrong_v14_or_swapped_student_is_rejected(tmp_path, monkeypatch, arm, weights, model):
    mock_inputs(monkeypatch, weights, model)
    with pytest.raises(ValueError):
        screen.study_contract(screen.settings(arm, tmp_path))


@pytest.mark.parametrize("mismatch", ["extra_source", "runtime"])
def test_external_control_requires_exact_sources_and_environment(tmp_path, monkeypatch, mismatch):
    mock_inputs(monkeypatch, V14_SHA, R2_SHA)

    def run(arm):
        manifest = screen.study_contract(screen.settings(arm, tmp_path))
        return screen.audit.Run(manifest, {}, {})

    reference, control = run("v14"), run("points_r2")
    monkeypatch.setattr(screen, "read_arm", lambda directory, arm: control)
    assert screen.paired_arm(tmp_path, "points_r2", reference) is control
    if mismatch == "extra_source":
        control.manifest["sources"]["agents/sherlock/changed.py"] = "4" * 64
    else:
        control.manifest["environment"]["lux_modules"]["env.py"] = "4" * 64
    with pytest.raises(ValueError):
        screen.paired_arm(tmp_path, "points_r2", reference)
