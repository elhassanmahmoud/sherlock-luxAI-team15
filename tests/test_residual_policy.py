import copy

import numpy as np
import pytest
import torch

from agents.sherlock.model import QNet
from agents.sherlock.residual import ResidualPolicy, validate_residual_checkpoint


def policy():
    torch.manual_seed(4)
    return ResidualPolicy([QNet(4, 6, 16, True) for _ in range(19)])


def test_original_mean_zero_initialization_and_addition():
    p = policy()
    x = torch.randn(3, 4)
    expected = torch.stack([m(x) for m in p.bases]).mean(0)
    assert torch.equal(p.baseline(x), expected)
    assert torch.count_nonzero(p.residual(x)) == 0
    assert torch.equal(p.values(x), expected)
    assert torch.equal(p.residual.body[0].weight, p.bases[18].body[0].weight)
    with torch.no_grad():
        p.residual.value[-1].bias.fill_(2)
    assert torch.equal(p.values(x), expected + 2)


def test_only_residual_can_receive_gradient():
    p = policy()
    before = copy.deepcopy(p.bases.state_dict())
    opt = torch.optim.Adam(p.residual.parameters(), lr=5e-5)
    p.values(torch.randn(2, 4)).sum().backward()
    opt.step()
    assert all(not v.requires_grad and v.grad is None for v in p.bases.parameters())
    assert all(torch.equal(v, before[k]) for k, v in p.bases.state_dict().items())
    assert any(v.grad is not None for v in p.residual.parameters())


def test_checkpoint_rejects_wrong_semantics_hash_and_nonfinite():
    p = policy()
    cp = p.checkpoint('a' * 64)
    validate_residual_checkpoint(cp, 'a' * 64, p.residual)
    for key, value in [('schema', 'mean37'), ('base_sha256', 'b' * 64)]:
        bad = copy.deepcopy(cp)
        bad[key] = value
        with pytest.raises(ValueError):
            validate_residual_checkpoint(bad, 'a' * 64, p.residual)
    bad = copy.deepcopy(cp)
    del bad['residual']
    with pytest.raises(ValueError):
        validate_residual_checkpoint(bad, 'a' * 64, p.residual)
    bad = copy.deepcopy(cp)
    bad['residual']['value.2.bias'][0] = float('nan')
    with pytest.raises(ValueError):
        validate_residual_checkpoint(bad, 'a' * 64, p.residual)


def test_stock_hooks_leave_scores_and_rng_unchanged():
    from agents.sherlock.main import Agent_x
    from types import SimpleNamespace
    nets = policy().bases
    actor = SimpleNamespace(q=nets[0], extra_q=list(nets[1:]), training=False)
    x = torch.randn(3, 4)
    assert torch.equal(Agent_x._network_values(actor, x), torch.stack([n(x) for n in nets]).mean(0))
    greedy = np.array([0, 2, 5])
    assert Agent_x._policy_greedy(actor, {}, [0, 1, 2], np.ones((3, 6), bool), greedy) is greedy
