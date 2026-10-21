"""PPO random streams depend on the run/game seed, not prior worker activity."""
from contextlib import nullcontext
import json
import random
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from agents.sherlock import cnn_model, ppo_agent
from scripts import ppo_train as P


@pytest.fixture(autouse=True)
def preserve_rngs():
    py_state, np_state = random.getstate(), np.random.get_state()
    with torch.random.fork_rng(devices=[]):
        yield
    random.setstate(py_state)
    np.random.set_state(np_state)


class SamplingAgent:
    _prev_ctx = None
    _prev_actions = {}

    def new_game(self, side):
        self.side = side
        self.draws = []

    def act(self, *, step, obs):
        self.draws.append((random.random(), np.random.random()))
        actions = np.zeros((16, 3), dtype=int)
        actions[:, 0] = torch.distributions.Categorical(logits=torch.zeros(16, 6)).sample()
        return actions


class FourStepEnv:
    """Capture real stochastic actions without importing or running the simulator."""
    def reset(self, *, seed):
        self.seed, self.actions = seed, []
        self.obs = {side: {"team_wins": np.array([2, 1])}
                    for side in ("player_0", "player_1")}
        return self.obs, {"params": {}}

    def step(self, actions):
        self.actions.append(actions)
        done = {side: len(self.actions) == 4 for side in self.obs}
        return self.obs, {}, done, dict.fromkeys(self.obs, False), {}


@pytest.fixture
def rollout(monkeypatch):
    # This fixture captures actions at the environment boundary and has no
    # unit trajectories. Only empty-recorder finalization needs a stand-in.
    monkeypatch.setattr(ppo_agent.Recorder, "finish", lambda self, gamma, lam: {})

    def run(seed=112, side="player_0", initial=1, teacher=False):
        torch.manual_seed(initial)
        env, agent = FourStepEnv(), SamplingAgent()
        opponent = SimpleNamespace(act=lambda **kwargs: np.zeros((16, 3), dtype=int))
        data, result = P.play_recorded(env, agent, opponent, seed, side, teacher)
        assert env.seed == seed and agent.side == side
        assert agent.recorder is None
        assert data == {} and result == (1.0 if side == "player_0" else 0.0)
        return np.stack([a[side][:, 0] for a in env.actions]), np.array(agent.draws)

    return run


@pytest.mark.parametrize("seed,side,torch_seed", [
    (112, "player_0", 224), (112, "player_1", 225), (113, "player_0", 226),
])
def test_rollout_samples_use_game_and_side_seed_despite_prior_rng(rollout, seed, side, torch_seed):
    torch.manual_seed(torch_seed)
    expected = np.stack([torch.distributions.Categorical(logits=torch.zeros(16, 6)).sample()
                         for _ in range(4)])
    first, _ = rollout(seed, side, initial=1)
    second, _ = rollout(seed, side, initial=2)
    np.testing.assert_array_equal(first, expected)
    np.testing.assert_array_equal(second, expected)


def test_rollout_sides_and_adjacent_games_have_distinct_torch_streams(rollout):
    samples = [rollout(seed, side)[0] for seed, side in
               [(112, "player_0"), (112, "player_1"), (113, "player_0")]]
    assert all(not np.array_equal(samples[i], samples[j])
               for i, j in [(0, 1), (0, 2), (1, 2)])


@pytest.mark.parametrize("teacher", [False, True])
def test_rollout_keeps_historical_python_numpy_seeds_on_both_sides(rollout, teacher):
    seed = 2**32 + 112
    py_rng, np_rng = random.Random(seed), np.random.RandomState(112)
    expected = np.array([(py_rng.random(), np_rng.random()) for _ in range(4)])
    for side in ("player_0", "player_1"):
        _, draws = rollout(seed, side, teacher=teacher)
        np.testing.assert_array_equal(draws, expected)


class TinyPolicy(torch.nn.Module):
    """Exercise real initialization/loading, with no CNN or optimizer steps."""
    def __init__(self, detach_value=False):
        super().__init__()
        self.detach_value = detach_value
        self.arch = {"detach_value": detach_value}
        self.shared = torch.nn.Parameter(torch.randn(16))
        if detach_value:
            self.critic = torch.nn.Parameter(torch.randn(16))


@pytest.fixture
def learner_run(monkeypatch, tmp_path):
    monkeypatch.setattr(P, "PPO_DIR", tmp_path)
    monkeypatch.setattr(cnn_model, "PolicyNet", TinyPolicy)
    monkeypatch.setattr(P.mp, "get_context", lambda mode: SimpleNamespace(
        Pool=lambda workers: nullcontext(None)))
    # The learner receives synthetic recorded data; no workers or games run.
    data = {"act": np.zeros(32, dtype=np.int64), "step": np.zeros(32, dtype=np.int64),
            "planes": np.zeros((1, 1), dtype=np.int8)}
    monkeypatch.setattr(P, "run_rollouts", lambda *args: ([data], [("default", 1.0)]))
    snapshots = []

    def load_agent(player, *, agent_path, train):
        net = TinyPolicy()
        snapshots.append(net.shared.detach().clone())
        return SimpleNamespace(net=net, cfg=SimpleNamespace())

    def save_policy(path, net, cfg, extra):
        snapshots.append(torch.cat([p.detach().flatten() for p in net.parameters()]).clone())

    def update(net, opt, data, *args, **kwargs):
        snapshots.append(torch.randperm(len(data["act"])))
        return dict.fromkeys(("pi", "v", "ent", "kl", "clipfrac"), 0.0)

    monkeypatch.setattr(ppo_agent, "PPOAgent", load_agent)
    monkeypatch.setattr(ppo_agent, "save_policy", save_policy)
    monkeypatch.setattr(P, "ppo_update", update)

    def run(seed, initial, detach_value):
        snapshots.clear()
        run_name = f"seed{seed}_initial{initial}_detach{detach_value}"
        run_dir = tmp_path / run_name
        run_dir.mkdir()
        (run_dir / "teacher.json").write_text(json.dumps({"weights": "unused.pth", "set": []}))
        args = SimpleNamespace(run=run_name, seed=seed, start=None, detach_value=detach_value,
                               lr=3e-4, sol92=0.0, default=1.0, teacher=0.0, workers=1,
                               iters=2, games=2, epochs=1, mb=32, clip=0.15, ent=0.003,
                               vf=0.5, vf_warmup=0, save_every=10)
        torch.manual_seed(initial)
        P.cmd_ppo(args, lambda msg: None)
        return list(snapshots)

    return run


@pytest.mark.parametrize("detach_value", [False, True])
def test_learner_seed_precedes_loading_fresh_critic_and_update_shuffles(learner_run, detach_value):
    first = learner_run(seed=17, initial=1, detach_value=detach_value)
    second = learner_run(seed=17, initial=2, detach_value=detach_value)
    other = learner_run(seed=18, initial=1, detach_value=detach_value)
    # Loaded parameters, initial save (including a new critic if requested),
    # and both update permutations must all be independent of ambient RNG.
    assert len(first) == len(second) == len(other) == 6
    for a, b, c in zip(first, second, other):
        assert torch.equal(a, b)
        assert not torch.equal(a, c)
    assert not torch.equal(first[2], first[4])  # shuffles advance between updates
