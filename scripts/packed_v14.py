"""CPU evaluation of the published V14: six batched linear layers for its 36 fixed Dueling QNets."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import weakref

import torch

V14_SHA256 = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"


def verified_bytes(weights, overrides):
    if overrides:
        raise ValueError("--packed-v14 requires V14's original configuration, without --set")
    content = Path(weights).read_bytes()
    if hashlib.sha256(content).hexdigest() != V14_SHA256:
        raise ValueError("--packed-v14 requires the byte-identical published V14 checkpoint")
    return content


def load_checkpoint(weights, overrides):
    """Deserialize only the actual byte sequence compared with the approved SHA."""
    return torch.load(io.BytesIO(verified_bytes(weights, overrides)), map_location="cpu", weights_only=False)


def pack_linear(layers):
    # Inputs are [member, unit, input]; one set of weights and one bias per ensemble member.
    weight = torch.stack([layer.weight.detach().T for layer in layers]).contiguous()
    bias = torch.stack([layer.bias.detach() for layer in layers]).unsqueeze(1)
    return bias, weight


def apply_linear(pair, values):
    bias, weight = pair
    return torch.baddbmm(bias, values, weight)


class PackedV14Values:
    """Detached snapshot of the six native linear layers. Installed only in a private evaluation worker."""
    def __init__(self, agent):
        from agents.sherlock.model import QNet

        nets = [agent.q, *agent.extra_q]
        if len(nets) != 36 or any(type(net) is not QNet or net.training or not net.dueling
                                  or net.feat_dim != 79 for net in nets):
            raise ValueError("Expected all 36 original 79-feature V14 Dueling QNets in eval mode")
        if any(p.device.type != "cpu" or p.dtype != torch.float32 for net in nets for p in net.parameters()):
            raise ValueError("--packed-v14 supports only the CPU float32 evaluation path")
        self._owner = weakref.ref(agent)
        self.body_in = pack_linear([net.body[0] for net in nets])
        self.body_out = pack_linear([net.body[2] for net in nets])
        self.adv_in = pack_linear([net.adv[0] for net in nets])
        self.adv_out = pack_linear([net.adv[2] for net in nets])
        self.value_in = pack_linear([net.value[0] for net in nets])
        self.value_out = pack_linear([net.value[2] for net in nets])

    def __call__(self, features):
        owner = self._owner()
        if owner is None or owner.training or owner.q.training:
            raise RuntimeError("Packed V14 snapshot is only valid during fixed-policy evaluation")
        if features.ndim != 2 or features.shape[1] != 79 or features.device.type != "cpu" or features.dtype != torch.float32:
            raise ValueError("Expected a float32 CPU batch with 79 features")
        h = features.unsqueeze(0).expand(36, -1, -1)
        h = apply_linear(self.body_in, h).relu()
        h = apply_linear(self.body_out, h).relu()
        advantage = apply_linear(self.adv_out, apply_linear(self.adv_in, h).relu())
        value = apply_linear(self.value_out, apply_linear(self.value_in, h).relu())
        return (value + advantage - advantage.mean(dim=-1, keepdim=True)).mean(dim=0)


def install(agent, checkpoint):
    """The caller supplies load_checkpoint's pinned state; verify the actual in-memory networks independently."""
    from agents.sherlock.main import Agent_x
    from scripts.check_candidate_runner import verify_loaded

    if (type(agent) is not Agent_x or agent.training or agent.autosave_on_terminate
            or getattr(agent, "_imitation", None) is not None or agent.cnn_policy is not None
            or getattr(agent._network_values, "__func__", None) is not Agent_x._network_values):
        raise ValueError("Expected a stock V14 Agent_x dedicated to evaluation")
    verify_loaded(agent, checkpoint)
    agent._network_values = PackedV14Values(agent)
