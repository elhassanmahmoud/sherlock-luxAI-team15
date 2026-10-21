"""DQN ensembles must keep every network and reject misleading input dimensions."""
import sys

import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x
from agents.sherlock.model import QNet
from scripts import build_ensemble
from tests.conftest import ENV_CFG, make_obs


def _net(dim, scores):
    net = QNet(dim, hidden=8, dueling=False)
    with torch.no_grad():
        for parameter in net.parameters():
            parameter.zero_()
        net.head.bias.copy_(torch.tensor(scores, dtype=torch.float32))
    return net


def _agent(*, threat=False):
    agent = Agent_x("player_0", cfg=AgentConfig(
        hidden=8, dueling=False, buffer_capacity=8, threat_feats=threat,
    ), train=False)
    agent.q = _net(agent.feat_dim, [6, 0, 0, 0, 0, 0])
    agent.target_q.load_state_dict(agent.q.state_dict())
    agent.extra_q = [_net(agent.feat_dim, [0, 3, 0, 0, 0, 0])]
    return agent


def _build(monkeypatch, out, *sources, mixed=False):
    argv = ["build_ensemble", "--out", str(out)]
    if mixed:
        argv.append("--mixed")
    monkeypatch.setattr(sys, "argv", argv + [str(path) for path in sources])
    build_ensemble.main()


def _assert_states(agent, expected):
    nets = [agent.q, *agent.extra_q]
    assert len(nets) == len(expected)
    for net, state in zip(nets, expected):
        assert net.state_dict().keys() == state.keys()
        for key, value in state.items():
            assert torch.equal(net.state_dict()[key], value), key


def _assert_action(agent, expected):
    agent.set_env_cfg(ENV_CFG)
    agent.set_to_eval_mode()
    obs = make_obs(10, 10, units=[(5, 5, 100)], relics=[(12, 12)])
    assert agent.act(10, obs)[0].tolist() == [expected, 0, 0]


def test_rebuild_saved_homogeneous_ensemble_keeps_appended_networks(tmp_path, monkeypatch):
    # Losing the newly appended right-preferring net changes RIGHT back to STAY.
    base = _agent()
    extra = _agent()
    extra.q = _net(79, [0, 0, 12, 0, 0, 0])
    extra.extra_q = []
    base_path, extra_path, out = (tmp_path / name for name in (
        "base.pth", "extra.pth", "built.pth",
    ))
    base.save_agent(str(base_path))
    extra.save_agent(str(extra_path))
    _build(monkeypatch, out, base_path, extra_path)

    checkpoint = torch.load(out, weights_only=False)
    assert checkpoint["ensemble_dims"] == [79, 79]
    expected = [base.q.state_dict(), base.extra_q[0].state_dict(), extra.q.state_dict()]
    loaded = Agent_x("player_0", agent_path=str(out), train=False)
    _assert_states(loaded, expected)
    _assert_action(loaded, 2)

    # A second save/build cycle must also keep the previous metadata aligned.
    resaved, rebuilt = tmp_path / "resaved.pth", tmp_path / "rebuilt.pth"
    loaded.save_agent(str(resaved))
    _build(monkeypatch, rebuilt, resaved, extra_path)
    reloaded = Agent_x("player_0", agent_path=str(rebuilt), train=False)
    _assert_states(reloaded, expected + [extra.q.state_dict()])
    assert torch.load(rebuilt, weights_only=False)["ensemble_dims"] == [79, 79, 79]
    _assert_action(reloaded, 2)


def test_mixed_builder_flattens_saved_ensembles_and_preserves_inference(tmp_path, monkeypatch):
    base = _agent(threat=True)
    old = _agent()
    old.q = _net(79, [0, 0, 12, 0, 0, 0])
    old.extra_q = [_net(79, [0, 0, 12, 0, 0, 0])]
    base_path, old_path, out = (tmp_path / name for name in (
        "new.pth", "old.pth", "mixed.pth",
    ))
    base.save_agent(str(base_path))
    old.save_agent(str(old_path))
    with pytest.raises(SystemExit):
        _build(monkeypatch, out, base_path, old_path)
    assert not out.exists()
    _build(monkeypatch, out, base_path, old_path, mixed=True)

    loaded = Agent_x("player_0", agent_path=str(out), train=False)
    assert [net.feat_dim for net in loaded.extra_q] == [101, 79, 79]
    expected = [net.state_dict() for net in [base.q, *base.extra_q, old.q, *old.extra_q]]
    _assert_states(loaded, expected)
    _assert_action(loaded, 2)
    resaved = tmp_path / "resaved.pth"
    loaded.save_agent(str(resaved))
    reloaded = Agent_x("player_0", agent_path=str(resaved), train=False)
    _assert_states(reloaded, expected)
    _assert_action(reloaded, 2)


@pytest.mark.parametrize("metadata", ["absent", None, []], ids=["absent", "none", "empty"])
def test_legacy_homogeneous_dimensions_keep_every_network(tmp_path, metadata):
    agent = _agent()
    agent.extra_q.append(_net(79, [0, 0, 12, 0, 0, 0]))
    path = tmp_path / "legacy.pth"
    agent.save_agent(str(path))
    checkpoint = torch.load(path, weights_only=False)
    if metadata == "absent":
        checkpoint.pop("ensemble_dims")
    else:
        checkpoint["ensemble_dims"] = metadata
    torch.save(checkpoint, path)
    loaded = Agent_x("player_0", agent_path=str(path), train=False)
    _assert_states(loaded, [net.state_dict() for net in [agent.q, *agent.extra_q]])
    _assert_action(loaded, 2)


@pytest.mark.parametrize("dims", [
    [79], [79, 79, 79], [79.0, 79], ["79", 79], [True, 79],
    [0, 79], [-1, 79], [80, 79], [None, 79], 79, "79", {"first": 79},
], ids=["short", "long", "float", "string", "bool", "zero", "negative",
        "too-wide", "null-member", "scalar", "text", "mapping"])
def test_loader_rejects_malformed_explicit_dimensions(tmp_path, dims):
    source = _agent()
    source.extra_q.append(_net(79, [0, 0, 12, 0, 0, 0]))
    path = tmp_path / "bad.pth"
    source.save_agent(str(path))
    checkpoint = torch.load(path, weights_only=False)
    checkpoint["ensemble_dims"] = dims
    torch.save(checkpoint, path)

    with pytest.raises(ValueError, match="ensemble_dims"):
        Agent_x("player_0", agent_path=str(path), train=False)


def test_loader_rejects_dimensions_without_ensemble_members(tmp_path):
    source = _agent()
    source.extra_q = []
    path = tmp_path / "bad.pth"
    source.save_agent(str(path))
    checkpoint = torch.load(path, weights_only=False)
    checkpoint["ensemble_dims"] = [79]
    torch.save(checkpoint, path)
    with pytest.raises(ValueError, match="ensemble_dims"):
        Agent_x("player_0", agent_path=str(path), train=False)


@pytest.mark.parametrize("metadata", ["absent", None, [], [79]],
                         ids=["absent", "none", "empty", "explicit"])
def test_loader_rejects_actual_extra_input_mismatch(tmp_path, metadata):
    source = _agent()
    path = tmp_path / "bad.pth"
    source.save_agent(str(path))
    checkpoint = torch.load(path, weights_only=False)
    checkpoint["ensemble"][0] = _net(78, [0, 3, 0, 0, 0, 0]).state_dict()
    if metadata == "absent":
        checkpoint.pop("ensemble_dims")
    else:
        checkpoint["ensemble_dims"] = metadata
    torch.save(checkpoint, path)
    with pytest.raises(ValueError, match=r"ensemble.*(input|Eingabe|dimension|Dimension)"):
        Agent_x("player_0", agent_path=str(path), train=False)


def test_loader_rejects_actual_main_input_mismatch(tmp_path):
    source = _agent()
    path = tmp_path / "bad.pth"
    source.save_agent(str(path))
    checkpoint = torch.load(path, weights_only=False)
    checkpoint["q"] = _net(78, [6, 0, 0, 0, 0, 0]).state_dict()
    torch.save(checkpoint, path)
    with pytest.raises(ValueError, match=r"q.*(input|Eingabe|dimension|Dimension)"):
        Agent_x("player_0", agent_path=str(path), train=False)


@pytest.mark.parametrize("bad_source", ["base", "appended"])
@pytest.mark.parametrize("bad_kind", ["dims", "tensor"])
def test_builder_rejects_invalid_source_before_writing(tmp_path, monkeypatch, bad_source, bad_kind):
    source = _agent()
    paths = {name: tmp_path / f"{name}.pth" for name in ("base", "appended")}
    for path in paths.values():
        source.save_agent(str(path))
    checkpoint = torch.load(paths[bad_source], weights_only=False)
    if bad_kind == "dims":
        checkpoint["ensemble_dims"] = [79, 79]
    else:
        checkpoint["ensemble"][0] = _net(78, [0, 3, 0, 0, 0, 0]).state_dict()
    torch.save(checkpoint, paths[bad_source])
    out = tmp_path / "output" / "invalid.pth"
    with pytest.raises(SystemExit, match="ensemble"):
        _build(monkeypatch, out, paths["base"], paths["appended"])
    assert not out.exists()


def test_empty_ensemble_roundtrip_remains_valid(tmp_path, monkeypatch):
    source = _agent()
    source.extra_q = []
    path, out = tmp_path / "single.pth", tmp_path / "built.pth"
    source.save_agent(str(path))
    _build(monkeypatch, out, path)
    loaded = Agent_x("player_0", agent_path=str(out), train=False)
    _assert_states(loaded, [source.q.state_dict()])
    _assert_action(loaded, 0)
