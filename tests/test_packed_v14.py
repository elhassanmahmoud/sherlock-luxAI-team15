"""Checks for the isolated CPU V14 evaluation backend. No environment games."""
from pathlib import Path

import pytest
import torch

from agents.sherlock.model import QNet
from scripts.packed_v14 import PackedV14Values, install, load_checkpoint, verified_bytes

ROOT = Path(__file__).resolve().parents[1]


def test_refuse_overrides_and_other_weights_before_deserialization(tmp_path, monkeypatch):
    path = tmp_path / "other.pth"
    path.write_bytes(b"not the published V14")
    monkeypatch.setattr(torch, "load", lambda *args, **kwargs: pytest.fail("Unexpected deserialization"))
    with pytest.raises(ValueError, match="original configuration"):
        verified_bytes(path, ["frozen=true"])
    with pytest.raises(ValueError, match="byte-identical"):
        load_checkpoint(path, [])


@pytest.mark.parametrize("units", [1, 8, 16])
def test_batched_values_follow_native_memberwise_dueling_mean(units):
    class Owner:
        training = False

    owner = Owner()
    with torch.random.fork_rng(devices=[]), torch.no_grad():
        torch.manual_seed(2711)
        nets = [QNet(79, hidden=8).eval() for _ in range(36)]
        owner.q, owner.extra_q = nets[0], nets[1:]
        packed = PackedV14Values(owner)
        features = torch.randn(units, 158)[:, ::2]
        expected = torch.stack([net(features) for net in nets]).mean(0)
        torch.testing.assert_close(packed(features), expected, atol=1e-6, rtol=1e-5)
        owner.training = True
        with pytest.raises(RuntimeError, match="evaluation"):
            packed(features)


def test_real_install_checks_actual_loaded_weights_and_eval_state():
    from agents.sherlock.main import Agent_x
    from scripts.par_eval import build_cfg

    path = ROOT / "agents/sherlock/weights/agent_p0.pth"
    state = load_checkpoint(path, [])
    actor = Agent_x("player_0", agent_path=str(path), cfg=build_cfg(str(path), []), train=False, seed=0)
    actor.set_to_eval_mode()
    with pytest.raises(ValueError, match="dedicated to evaluation"):
        actor.autosave_on_terminate = True
        install(actor, state)
    actor.autosave_on_terminate = False
    with torch.no_grad():
        bias = actor.extra_q[11].adv[2].bias
        original = bias.clone()
        bias.add_(1)
        with pytest.raises(ValueError, match="Loaded model weights differ"):
            install(actor, state)
        bias.copy_(original)
        install(actor, state)
        assert isinstance(actor._network_values, PackedV14Values)
        probe = torch.zeros(3, 79)
        torch.testing.assert_close(actor._network_values(probe), Agent_x._network_values(actor, probe),
                                   atol=1e-5, rtol=1e-5)
