import csv
from pathlib import Path

import numpy as np
import pytest

from scripts.check_candidate_runner import prepare_workspace, validate_actions, write_report


def test_workspace_uses_copy_and_preserves_original(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "agents").mkdir()
    original = ("Moodle Gruppe;Import_Path;Load_Path_P0;Load_Path_P1\n"
                "15;agents.sherlock.main.Agent_x;release0.pth;release1.pth\n")
    (root / "Paths.csv").write_text(original)
    weights = root / "candidate.pth"
    weights.write_bytes(b"candidate")
    dest = tmp_path / "isolated"
    prepare_workspace(root, weights, dest)
    rows = list(csv.DictReader((dest / "Paths.csv").open(), delimiter=";"))
    assert Path(rows[0]["Load_Path_P0"]).read_bytes() == b"candidate"
    assert rows[0]["Load_Path_P0"] == rows[0]["Load_Path_P1"]
    assert Path(rows[0]["Load_Path_P0"]).resolve() != weights.resolve()
    assert (root / "Paths.csv").read_text() == original
    assert weights.read_bytes() == b"candidate"
    with pytest.raises(FileExistsError):
        prepare_workspace(root, weights, dest)


def test_report_does_not_overwrite_existing(tmp_path):
    out = tmp_path / "result.json"
    out.write_text("existing")
    with pytest.raises(FileExistsError):
        write_report(out, {"ok": True})
    assert out.read_text() == "existing"


@pytest.mark.parametrize("actions", [
    np.zeros((15, 3)), np.full((16, 3), np.nan),
    np.full((16, 3), 0.5), np.full((16, 3), 6),
    np.full((16, 3), -1),
])
def test_bad_actions_rejected(actions):
    with pytest.raises(ValueError):
        validate_actions(actions, 16)


def test_valid_sap_offsets_can_be_negative():
    actions = np.zeros((16, 3), dtype=int)
    actions[0] = [5, -3, 2]
    validate_actions(actions, 16)


def test_seed_proxy_matches_runner_numpy_api_without_patching_numpy():
    from scripts.check_candidate_runner import seed_proxy
    original = np.random.default_rng
    proxy = seed_proxy([500720, 500721])
    assert proxy.random.default_rng().integers(0, 1_000_000) == 500720
    assert proxy.random.default_rng().integers(0, 1_000_000) == 500721
    assert np.random.default_rng is original


def test_checkpoint_load_and_probe_fail_closed(tmp_path):
    import torch
    from agents.sherlock.main import Agent_x
    from agents.sherlock.config import AgentConfig
    from scripts.check_candidate_runner import verify_loaded
    cfg = AgentConfig(hidden=16, buffer_capacity=10)
    original = Agent_x("player_0", cfg=cfg, train=False)
    path = tmp_path / "candidate.pth"
    original.save_agent(str(path))
    checkpoint = torch.load(path, weights_only=False)
    loaded = Agent_x("player_0", agent_path=str(path), train=False)
    verify_loaded(loaded, checkpoint)
    with torch.no_grad():
        next(loaded.q.parameters()).add_(1)
    with pytest.raises(ValueError, match="weights"):
        verify_loaded(loaded, checkpoint)
    mismatched_config = dict(checkpoint, cfg=dict(checkpoint["cfg"], gamma=cfg.gamma / 2))
    with pytest.raises(ValueError, match="config"):
        verify_loaded(original, mismatched_config)
    checkpoint["feature_dim"] = 1
    with pytest.raises(ValueError, match="architecture"):
        verify_loaded(original, checkpoint)
    torch.save(checkpoint, path)
    with pytest.raises(ValueError, match="q: Eingabedimension"):
        Agent_x("player_0", agent_path=str(path), train=False)
