"""Warm-start provenance and paired pilot configuration; no Lux games."""
from __future__ import annotations

import hashlib
import json
import sys

import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet
from scripts import night_train_pilot as pilot
from scripts.variants import VARIANTS, variant_cfg


@pytest.fixture
def source_checkpoint(tmp_path):
    # Hidden width 4 keeps these synthetic checkpoints small; all 79 inputs and
    # six actions still pass the real QNet state loader.
    cfg = AgentConfig(hidden=4, frozen=True, cand_rescue=True, rescue_after=30)
    state = QNet(79, 6, hidden=4).state_dict()
    first = {key: torch.zeros_like(value) for key, value in state.items()}
    selected = {key: torch.full_like(value, 0.125) for key, value in state.items()}
    checkpoint = {
        "q": first, "target_q": first, "opt": {"unrelated": "ensemble optimizer"},
        "ensemble": [first] * 17 + [selected], "ensemble_dims": [79] * 18,
        "feature_dim": 79, "n_actions": 6, "cfg": cfg.to_dict(),
        "env_steps": 0, "learn_steps": 123456,
    }
    source = tmp_path / "source.pth"
    torch.save(checkpoint, source)
    return source


def prepare_synthetic(source, out, **kwargs):
    return pilot.prepare(source, out, expected_source_sha=hashlib.sha256(source.read_bytes()).hexdigest(), **kwargs)


def test_prepare_extracts_component_18_with_fresh_optimizer_and_identical_target(source_checkpoint, tmp_path):
    before = source_checkpoint.read_bytes()
    out = tmp_path / "init"
    manifest = prepare_synthetic(source_checkpoint, out)
    prepared = torch.load(out / "weights" / "agent.pth", weights_only=True)

    assert source_checkpoint.read_bytes() == before
    assert "opt" not in prepared and prepared["learn_steps"] == 0
    assert prepared["ensemble"] == [] and prepared["ensemble_dims"] == []
    assert prepared["feature_dim"] == 79 and prepared["n_actions"] == 6
    for key, value in prepared["q"].items():
        assert torch.equal(value, torch.full_like(value, 0.125))
        assert torch.equal(prepared["target_q"][key], value)
        assert prepared["target_q"][key].data_ptr() != value.data_ptr()
    cfg = prepared["cfg"]
    assert not cfg["frozen"] and cfg["rules_in_training"] and cfg["rules_in_training_all"]
    assert cfg["cand_rescue"] and cfg["rescue_after"] == 30
    assert cfg["fog_sap"] and cfg["est_censor"] and cfg["neb_cross"]
    assert cfg["w_discovery"] == 0.5 and cfg["w_explore"] == 0.3
    assert cfg["lr"] == 0.0001
    assert prepared["env_steps"] >= cfg["eps_decay_steps"] and cfg["eps_end"] == 0.05
    assert manifest["component_index"] == 18
    assert manifest["optimizer"] == "fresh Adam; not resumed"
    assert manifest["source_sha256"] == hashlib.sha256(before).hexdigest()
    assert manifest["tensor_sha256"] == pilot.tensor_sha256(prepared["q"])
    assert manifest["prepared_utc"]
    assert json.loads((out / "manifest.json").read_text()) == manifest


@pytest.mark.parametrize("index", [-1, 19, True])
def test_invalid_component_index_creates_no_output(source_checkpoint, tmp_path, index):
    out = tmp_path / "invalid"
    with pytest.raises(ValueError, match="index"):
        prepare_synthetic(source_checkpoint, out, component_index=index)
    assert not out.exists()


def test_prepare_requires_existing_source_and_expected_sha(source_checkpoint, tmp_path):
    with pytest.raises(FileNotFoundError):
        pilot.prepare(tmp_path / "absent.pth", tmp_path / "missing")
    with pytest.raises(ValueError, match="SHA"):
        pilot.prepare(source_checkpoint, tmp_path / "wrong_sha")
    assert not (tmp_path / "missing").exists()
    assert not (tmp_path / "wrong_sha").exists()


def test_prepare_refuses_existing_output_without_mutating_it(source_checkpoint, tmp_path):
    out = tmp_path / "existing"
    out.mkdir()
    sentinel = out / "sentinel"
    sentinel.write_text("preserve me")
    with pytest.raises(FileExistsError):
        prepare_synthetic(source_checkpoint, out)
    assert sentinel.read_text() == "preserve me"
    assert list(out.iterdir()) == [sentinel]


def test_prepare_rejects_malformed_selected_state_before_creating_output(source_checkpoint, tmp_path):
    checkpoint = torch.load(source_checkpoint, weights_only=True)
    checkpoint["ensemble"][17] = {"body.0.weight": torch.ones(4, 79)}
    torch.save(checkpoint, source_checkpoint)
    with pytest.raises((ValueError, RuntimeError)):
        prepare_synthetic(source_checkpoint, tmp_path / "bad_state")
    assert not (tmp_path / "bad_state").exists()


def test_run_arm_requires_real_untampered_init_before_training(source_checkpoint, tmp_path):
    out = tmp_path / "init"
    prepare_synthetic(source_checkpoint, out)
    (out / "weights" / "agent.pth").unlink()
    with pytest.raises(FileNotFoundError):
        pilot.run_arm(out, "control", "pilot_control")


def test_run_arm_restores_registry_and_argv_after_downstream_failure(source_checkpoint, tmp_path, monkeypatch):
    from scripts import finetune

    out = tmp_path / "init"
    prepare_synthetic(source_checkpoint, out)
    monkeypatch.setattr(finetune, "RUNS", tmp_path / "runs")
    original_registry = dict(VARIANTS)
    original_argv = sys.argv
    observations = []

    def no_games():
        # Training itself is deliberately replaced: this test exercises the
        # real registry/config and the exact downstream invocation boundary.
        argv = sys.argv[1:]
        get = lambda flag: argv[argv.index(flag) + 1]
        observations.append((variant_cfg(get("--variant")).to_dict(), argv[:]))
        raise RuntimeError("stop before any environment")

    monkeypatch.setattr(finetune, "main", no_games)
    for arm in ("control", "discovery"):
        with pytest.raises(RuntimeError, match="stop before"):
            pilot.run_arm(out, arm, "pilot_" + arm)
        assert VARIANTS == original_registry
        assert sys.argv is original_argv

    control, treatment = observations[0][0], observations[1][0]
    assert {key for key in control if control[key] != treatment[key]} == {"w_discovery"}
    assert control["w_discovery"] == 0.5 and treatment["w_discovery"] == 2.0
    for _, argv in observations:
        get = lambda flag: argv[argv.index(flag) + 1]
        assert get("--games") == "600" and get("--seed") == "9"
        assert get("--map-offset") == "4200" and get("--prefill-games") == "120"
        assert get("--val-every") == "300" and get("--n-val") == "8"
        assert get("--lr") == "0.0001"
        assert get("--mix") == "solution92=0.6,sol92_sq=0.2,default=0.1,rush=0.1"
        assert "--no-test" in argv and "--keep-final" in argv
        assert "--pool" not in argv


def test_run_arm_refuses_changed_source_and_existing_destination(source_checkpoint, tmp_path, monkeypatch):
    from scripts import finetune

    out = tmp_path / "init"
    prepare_synthetic(source_checkpoint, out)
    runs = tmp_path / "runs"
    monkeypatch.setattr(finetune, "RUNS", runs)
    (runs / "already").mkdir(parents=True)
    with pytest.raises(FileExistsError):
        pilot.run_arm(out, "control", "already")
    source_checkpoint.write_bytes(b"changed")
    with pytest.raises(ValueError, match="source|Source"):
        pilot.run_arm(out, "control", "new")
    assert not (runs / "new").exists()
