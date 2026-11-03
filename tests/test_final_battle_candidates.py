"""Candidate construction must preserve V14 identity and reject unsafe inputs."""
import copy
import hashlib
import importlib
import json
from pathlib import Path

import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet


def module():
    try:
        return importlib.import_module("scripts.final_battle_candidates")
    except ModuleNotFoundError:
        pytest.fail("The fixed, guarded final-battle candidate builder is missing")


@pytest.fixture
def source(tmp_path, monkeypatch):
    b = module()
    monkeypatch.setattr(b, "ROOT", tmp_path)
    cfg = AgentConfig(hidden=8, dueling=True).to_dict()
    cfg.update(cand_rescue=True, rescue_after=30, zone_rescue=False,
               point_pair_swap=False, art_move_guard=False)
    states = []
    template = QNet(79, 6, hidden=8, dueling=True).state_dict()
    for i in range(36):
        states.append({k: torch.full_like(v, (i + 1) / 100) for k, v in template.items()})
    cp = dict(q=states[0], ensemble=states[1:], ensemble_dims=[79] * 35,
              target_q=copy.deepcopy(states[35]), cfg=cfg, feature_dim=79,
              n_actions=6, optimizer={"stale": 1}, opt={"stale": 2},
              env_steps=1234567, learn_steps=99999, ensemble_sources=["missing/history.pth"])
    path = tmp_path / "agents/sherlock/weights/agent_p0.pth"
    path.parent.mkdir(parents=True)
    torch.save(cp, path)
    monkeypatch.setattr(b, "SOURCE_SHA", hashlib.sha256(path.read_bytes()).hexdigest())
    return b, path, cp, states


def output(source, name="candidates"):
    return source[0].ROOT / "experiments/ensembles" / name


def assert_state(actual, expected):
    assert actual.keys() == expected.keys()
    assert all(torch.equal(actual[k], expected[k]) for k in actual)


def test_fixed_rosters_preserve_order_config_and_reset_stale_training_state(source):
    # Wrong q offset, reordered pairs, or inherited target/optimizer changes real checkpoints.
    b, path, original, states = source
    before = path.read_bytes()
    result = b.build(path, output(source))
    expected = {
        "PAIR18": [0,1,3,6,8,10,13,15,16,18,19,21,24,26,28,31,33,34],
        "PAIR24": [0,1,3,5,6,7,8,10,13,15,16,17,18,19,21,23,24,25,26,28,31,33,34,35],
        "FT18": list(range(18,36)), "Z36": list(range(36)),
    }
    assert set(result["candidates"]) == set(expected)
    assert result["status"] == "BUILT_VERIFIED"
    for name, indices in expected.items():
        cp = torch.load(output(source) / f"{name}.pth", weights_only=True)
        nets = [cp["q"], *cp["ensemble"]]
        assert len(nets) == len(indices)
        for state, index in zip(nets, indices):
            assert_state(state, states[index])
        assert_state(cp["target_q"], states[indices[0]])
        assert cp["ensemble_dims"] == [79] * (len(indices) - 1)
        want_cfg = dict(original["cfg"])
        if name == "Z36":
            want_cfg["zone_rescue"] = True
        assert cp["cfg"] == want_cfg
        assert "optimizer" not in cp and "opt" not in cp
        assert cp["learn_steps"] == 0 and cp["env_steps"] == 60000
        entry = result["candidates"][name]
        assert entry["source_indices"] == indices
        assert entry["net_count"] == len(indices)
        assert entry["unique_tensor_count"] == len(indices)
        assert entry["new_training"] is False
        assert len(entry["ordered_tensor_sha256"]) == len(indices)
        assert entry["sha256"] == hashlib.sha256((output(source) / f"{name}.pth").read_bytes()).hexdigest()
    assert path.read_bytes() == before
    assert json.loads((output(source) / "manifest.json").read_text()) == result


def test_bad_source_digest_is_rejected_before_outputs(source, monkeypatch):
    b, path, *_ = source
    monkeypatch.setattr(b, "SOURCE_SHA", "0" * 64)
    with pytest.raises(ValueError, match="SHA"):
        b.build(path, output(source))
    assert not output(source).exists()


@pytest.mark.parametrize("change", ["count", "width", "actions", "nonfinite", "shape", "duplicate"])
def test_invalid_source_fails_closed_even_when_hash_is_pinned(source, monkeypatch, change):
    b, path, cp, _ = source
    if change == "count": cp["ensemble"].pop()
    elif change == "width": cp["feature_dim"] = 80
    elif change == "actions": cp["n_actions"] = 5
    elif change == "nonfinite": cp["q"]["adv.2.bias"][0] = float("nan")
    elif change == "shape": cp["q"]["adv.2.bias"] = torch.zeros(5)
    else: cp["ensemble"][0] = copy.deepcopy(cp["q"])
    torch.save(cp, path)
    monkeypatch.setattr(b, "SOURCE_SHA", hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError): b.build(path, output(source))
    assert not output(source).exists()


def test_existing_output_is_never_overwritten(source):
    b, path, *_ = source
    dest = output(source)
    dest.mkdir(parents=True)
    sentinel = dest / "PAIR18.pth"
    sentinel.write_bytes(b"keep me")
    with pytest.raises(FileExistsError): b.build(path, dest)
    assert sentinel.read_bytes() == b"keep me"


def test_protected_and_symlink_output_paths_are_rejected(source):
    b, path, *_ = source
    with pytest.raises(ValueError): b.build(path, path.parent / "new")
    allowed = b.ROOT / "experiments/ensembles"
    allowed.mkdir(parents=True)
    (allowed / "alias").symlink_to(path.parent, target_is_directory=True)
    with pytest.raises(ValueError): b.build(path, allowed / "alias/new")
    assert not (path.parent / "new").exists()


def test_one_training_arm_does_not_silently_omit_training_candidates(source):
    b, path, *_ = source
    with pytest.raises(ValueError, match="both"):
        b.build(path, output(source), control=path)
    assert not output(source).exists()


def test_guarded_builder_entrypoint_exists():
    assert callable(getattr(module(), "build", None)), "A guarded build entrypoint is required"


@pytest.fixture
def trained_pair(source, tmp_path, monkeypatch):
    """Synthetic episodes exercise complete real receipt production, without games or gradients."""
    from scripts import final_rescue_train as trainer
    from tests.test_final_rescue_training import simulated_final_loop
    b, path, *_ = source
    monkeypatch.setattr(trainer, "SOURCE_SHA", b.SOURCE_SHA)
    finetune = simulated_final_loop.__wrapped__(trainer, monkeypatch, tmp_path)
    monkeypatch.setattr(finetune, "RUNS", b.ROOT / "experiments/runs")
    synthetic_episode = finetune.play_game
    def distinct_synthetic_episode(env, agent, opponent, seed, side, train):
        row = synthetic_episode(env, agent, opponent, seed, side, train)
        if agent.learn_enabled and agent.cfg.rescue_in_training:
            # Distinct fake treatment tensors; this is not a real gradient update.
            with torch.no_grad():
                next(agent.q.parameters()).add_(.00001)
        return row
    monkeypatch.setattr(finetune, "play_game", distinct_synthetic_episode)
    prepared = tmp_path / "synthetic_prepared"
    trainer.prepare(path, prepared)
    paths = {}
    for arm in ("control18", "adapt18"):
        directory = b.ROOT / "experiments/runs" / arm
        trainer.run_arm(prepared, arm, arm)
        paths[arm] = directory / "weights/agent.pth"
    return paths


def test_complete_training_receipts_replace_only_member18_and_keep_v14_config(source, trained_pair):
    b, path, original, states = source
    result = b.build(path, output(source), control=trained_pair["control18"], rescue=trained_pair["adapt18"])
    assert set(result["candidates"]) == {"PAIR18", "PAIR24", "FT18", "Z36", "C36", "R36"}
    for name, arm in (("C36", "control18"), ("R36", "adapt18")):
        entry = result["candidates"][name]
        cp = torch.load(entry["path"], weights_only=True)
        nets = [cp["q"], *cp["ensemble"]]
        assert len(nets) == 36 and cp["cfg"] == original["cfg"]
        for i in range(36):
            expected = torch.load(trained_pair[arm], weights_only=True)["q"] if i == 18 else states[i]
            assert_state(nets[i], expected)
        assert entry["replaced_indices"] == [18] and entry["new_training"] is True
        assert entry["nominatable"] is (name == "R36")
        assert entry["training_arm"] == arm
        assert entry["net_count"] == entry["unique_tensor_count"] == 36
        assert_state(cp["target_q"], states[0])


@pytest.mark.parametrize("failure", ["swap", "checkpoint", "count", "chronology", "role"])
def test_training_evidence_corruption_is_rejected_before_any_candidate(source, trained_pair, failure):
    b, path, *_ = source
    control, rescue = trained_pair["control18"], trained_pair["adapt18"]
    receipt_path = rescue.parent.parent / "final_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    if failure == "swap": control, rescue = rescue, control
    elif failure == "checkpoint":
        with rescue.open("ab") as handle: handle.write(b"changed")
    elif failure == "count":
        receipt["actual_train_games"] = 600
        receipt_path.write_text(json.dumps(receipt))
    elif failure == "role":
        receipt["arm"] = "control18"
        receipt_path.write_text(json.dumps(receipt))
    else:
        rows = rescue.parent.parent / "rollouts.jsonl"
        rows.write_text("\n".join(rows.read_text().splitlines()[:-1]))
        receipt["rollouts_sha256"] = b.file_sha256(rows)
        receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        b.build(path, output(source), control=control, rescue=rescue)
    assert not output(source).exists()
