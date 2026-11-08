"""Synthetic probe contracts: no complete games or checkpoint loading."""
from types import SimpleNamespace
import random
import numpy as np
import pytest
import torch

from scripts import holder_rollout as h


def context(ms=20):
    points = np.zeros((5, 5), bool)
    points[1, 1] = True
    return dict(step=20, match_step=ms, max_match_steps=100, W=5, H=5,
                ally_ids=np.array([0, 1]), ally_pos=np.array([[1, 1], [3, 3]]),
                ally_ene=np.array([0., 20.]), point_tiles=points,
                assigned={0: (1, 1), 1: (3, 3)}, first_on_tile={(1, 1): 0})


@pytest.mark.parametrize('ms,want', [(0, False), (1, True), (89, True), (90, False), (100, False)])
def test_boundary_excludes_reset_and_allows_last_twelve_regular_actions(ms, want):
    assert h.eligible(context(ms), 0, np.ones(6, bool), 2) is want


@pytest.mark.parametrize('change', ['negative', 'stack', 'target', 'destination', 'stay', 'move', 'position', 'sap'])
def test_eligibility_rejects_illegal_or_nonholder_cases(change):
    c, mask, action = context(), np.ones(6, bool), 2
    if change == 'negative': c['ally_ene'][0] = -1
    if change == 'stack': c['ally_pos'][1] = [1, 1]
    if change == 'target': c['assigned'][0] = (3, 3)
    if change == 'destination': c['point_tiles'][2, 1] = True
    if change == 'stay': mask[0] = False
    if change == 'move': mask[2] = False
    if change == 'position': c['ally_pos'][0] = [-1, 1]
    if change == 'sap': action = 5
    assert not h.eligible(c, 0, mask, action)


def test_negative_stacker_does_not_disqualify_sole_nonnegative_holder():
    c = context(); c['ally_pos'][1] = [1, 1]; c['ally_ene'][1] = -1
    assert h.eligible(c, 0, np.ones(6, bool), 2)


class Globals:
    events = []


class ToyEnv:
    def __init__(self):
        self.numpy_output = True
        self.rng_key = ('immutable', 0)
        self.env_params = ('immutable', 1)
        self.jax_env = SimpleNamespace()
        self.action_space = object()
        self.state = ('immutable', 2)


def toy_agent():
    q = torch.nn.Linear(2, 6).eval().requires_grad_(False)
    node = SimpleNamespace(value=[1])
    belief = SimpleNamespace(node=node)
    return SimpleNamespace(training=False, q=q, target_q=q, extra_q=[], cnn_policy=None,
                           belief=belief, feat_belief=belief, rng=np.random.default_rng(3))


def test_joint_clone_preserves_belief_and_opponent_global_node_aliases():
    a, e = toy_agent(), ToyEnv()
    node = SimpleNamespace(value=[3]); opp = SimpleNamespace(node=node)
    Globals.events = [node]
    snap = h.Snapshot.capture(e, a, opp, {'player_0': {'x': np.array([1])}}, Globals)
    branch = snap.fork()
    assert branch.agent.q is a.q
    assert branch.agent.belief is branch.agent.feat_belief
    assert branch.agent.belief is not a.belief
    assert branch.opponent.node is branch.globals['events'][0]
    assert branch.opponent.node is not node
    assert branch.env is not e and branch.env.state is e.state
    branch.obs['player_0']['x'][0] = 9
    assert snap.obs['player_0']['x'][0] == 1
    branch.agent.belief.node.value.append(2)
    assert a.belief.node.value == [1]


def test_activation_restores_global_references_inventory_rng_and_live_values_on_exception():
    a, env = toy_agent(), ToyEnv()
    live = [SimpleNamespace(value=[3])]; Globals.events = live
    snap = h.Snapshot.capture(env, a, SimpleNamespace(node=live[0]), {}, Globals)
    random.seed(2); np.random.seed(2); torch.manual_seed(2)
    before = h.rng_state()
    with pytest.raises(RuntimeError, match='boom'):
        with snap.fork().activate():
            Globals.events[0].value.append(10)
            Globals.added = [5]
            del Globals.events
            random.random(); np.random.random(); torch.rand(1)
            raise RuntimeError('boom')
    assert Globals.events is live and live[0].value == [3]
    assert not hasattr(Globals, 'added')
    assert h.exact_digest(h.rng_state()) == h.exact_digest(before)


def test_snapshots_reject_training_mutable_shared_modules_and_wrapper_inventory_drift():
    a = toy_agent(); a.training = True
    with pytest.raises(ValueError): h.Snapshot.capture(ToyEnv(), a, SimpleNamespace(), {}, Globals)
    a.training = False; a.q.train()
    with pytest.raises(ValueError): h.Snapshot.capture(ToyEnv(), a, SimpleNamespace(), {}, Globals)
    a.q.eval(); env = ToyEnv(); env.unexamined = []
    with pytest.raises(ValueError): h.Snapshot.capture(env, a, SimpleNamespace(), {}, Globals)


def test_hash_detects_dtype_shape_and_single_value_changes():
    a = np.array([[1, 2]], dtype=np.int32)
    assert len({h.exact_digest(a), h.exact_digest(a.astype(np.int64)),
                h.exact_digest(a.reshape(2, 1)), h.exact_digest(np.array([[1, 3]], np.int32))}) == 4


def test_diagnostic_intervention_runs_normal_rules_and_keeps_downstream_sap(monkeypatch):
    # Breaking this by bypassing normal _rule_override would lose SAP result5.
    monkeypatch.setattr(h.Agent_x, '_rule_override', lambda self, ctx, uid, mask, a: 5 if a == 0 else a)
    agent = object.__new__(h.DiagnosticAgent)
    agent.collect = False; agent.intervention = h.Intervention(20, 0, 2); agent.intervention_hits = 0
    assert agent._rule_override(context(), 0, np.ones(6, bool), 2) == 5
    assert agent.intervention_hits == 1
    assert agent._rule_override(context(), 1, np.ones(6, bool), 2) == 2


def test_cli_binds_all_twelve_historical_keys_and_smoke_both_sides(tmp_path):
    from scripts.holder_rollout_probe import validate_keys, SMOKE_KEYS
    from pathlib import Path
    import json
    root = Path(__file__).resolve().parents[1]
    path = root / 'experiments/analysis/decision_learning_20261108/keys.json'
    keys, _ = validate_keys(path)
    assert len(keys) == 12
    assert SMOKE_KEYS == ((831006, 'player_1'), (831043, 'player_0'))
    document = json.loads(path.read_text()); document['keys'] = document['keys'][:2]
    bad = tmp_path / 'keys.json'; bad.write_text(json.dumps(document))
    with pytest.raises(ValueError): validate_keys(bad)


def test_process_gate_catches_probe_and_pytest_without_ignoring_sibling_processes():
    from scripts.holder_rollout_probe import foreign_processes
    sample = '\n'.join(['1 7 /venv/python -m scripts.holder_rollout_probe --x',
                        '2 7 /venv/python -m pytest -q', '3 8 /venv/python -m scripts.par_eval',
                        '4 7 /venv/python -m scripts.ensemble_diversity_train',
                        '5 9 /bin/zsh readme'])
    assert foreign_processes(sample, owner=1) == [2, 3, 4]


class BranchAgent:
    def __init__(self):
        self.__dict__.update(vars(toy_agent()))
        self.collect = False; self.intervention = None; self.intervention_hits = 0; self.caught_errors = 0

    def act(self, step, obs):
        self.belief.node.value.append(int(self.rng.integers(100)))
        random.random(); np.random.random(); torch.rand(1)
        a = 2
        if self.intervention is not None and step == self.intervention.step:
            a = 0; self.intervention_hits += 1
        return np.array([[a, 0, 0]], dtype=int)


class BranchOpponent:
    def __init__(self, node): self.node = node
    def act(self, step, obs):
        assert self.node is Globals.events[0]
        self.node.value.append(step)
        return np.array([[2, 0, 0]], dtype=int)


class BranchEnv(ToyEnv):
    def __init__(self, ms=20):
        super().__init__(); self.state = (ms, (0, 0), 20)

    def observations(self):
        ms, points, step = self.state
        return {p: dict(match_steps=np.array(ms), team_points=np.array(points), steps=np.array(step))
                for p in ('player_0', 'player_1')}

    def step(self, actions):
        ms, points, step = self.state
        assert actions['player_0'].shape == (1, 3)
        gain = 3 if actions['player_0'][0, 0] == 0 else 1
        updated = points[0] + gain, points[1] + 1
        info = {}
        if ms == 100:
            # At boundary, v2 recovers one occupied point for each team.
            units = SimpleNamespace(position=np.array([[[0, 0]], [[1, 1]]]), energy=np.zeros((2, 1, 1)))
            info['final_state'] = SimpleNamespace(
                units=units, units_mask=np.ones((2, 1), bool),
                relic_nodes_map_weights=np.array([[1, 0], [0, 1]]), relic_nodes_mask=np.array([True, True]))
            updated = (0, 0)
        self.state = ((ms + 1) % 101, updated, step + 1)
        actions.clear()  # Faithfully exercise installed engine's input mutation.
        done = {p: False for p in ('player_0', 'player_1')}
        return self.observations(), {}, done, done, info


def test_paired_rollout_restores_post_act_live_state_and_matches_all_twelve_live_frames():
    env, agent = BranchEnv(), BranchAgent()
    node = SimpleNamespace(value=[]); Globals.events = [node]; opponent = BranchOpponent(node)
    obs = env.observations()
    pre = h.Snapshot.capture(env, agent, opponent, obs, Globals)
    before = h.exact_digest(env.state), h.exact_digest(obs)
    actions = {'player_0': agent.act(20, obs['player_0']), 'player_1': opponent.act(20, obs['player_1'])}
    post_rng = h.exact_digest(h.rng_state())
    live_events, live_values = Globals.events, list(Globals.events[0].value)
    live_agent_values = list(agent.belief.node.value)
    original_obs = h.exact_digest(obs)
    pair = h.paired_rollout(pre, 'player_0', 20, dict(uid=0, proposal=2), verify=True)
    assert pair['label'] == 2 and pair['effective']
    assert pair['baseline']['points'] == [12, 12]
    assert pair['hold']['points'] == [14, 12]
    assert all(pair['reverse_repeat'].values())
    assert h.exact_digest(h.rng_state()) == post_rng
    assert Globals.events is live_events and Globals.events[0].value == live_values
    assert agent.belief.node.value == live_agent_values and h.exact_digest(obs) == original_obs
    obs, frame = h.step_frame(env, agent, opponent, obs, 'player_0', 20, actions=actions, before=before)
    assert frame == pair['baseline']['frames'][0]
    for offset in range(1, 12):
        obs, frame = h.step_frame(env, agent, opponent, obs, 'player_0', 20+offset)
        assert frame == pair['baseline']['frames'][offset]
    assert pair['baseline']['frames'][0]['actions']['player_0'] == [[2, 0, 0]]


def test_horizon_at_match89_counts_terminal_points_despite_zero_endpoint():
    env, agent = BranchEnv(89), BranchAgent()
    node = SimpleNamespace(value=[]); Globals.events = [node]
    snap = h.Snapshot.capture(env, agent, BranchOpponent(node), env.observations(), Globals)
    result = h.rollout(snap, 'player_0', 20)
    assert result['points'] == [12, 12]
    assert result['frames'][-1]['point_state'] == [12, 12]
    assert result['frames'][-1]['points'] == [1, 1]


def test_rollout_exception_restores_globals_rng_and_pre_snapshot(monkeypatch):
    env, agent = BranchEnv(), BranchAgent()
    node = SimpleNamespace(value=[]); Globals.events = [node]
    snap = h.Snapshot.capture(env, agent, BranchOpponent(node), env.observations(), Globals)
    live_rng = h.exact_digest(h.rng_state()); live = Globals.events
    def fail(*args, **kwargs):
        Globals.events.append('branch only'); Globals.new_attribute = []
        random.random(); np.random.random(); torch.rand(1)
        raise RuntimeError('branch crash')
    monkeypatch.setattr(h, 'step_frame', fail)
    with pytest.raises(RuntimeError, match='branch crash'): h.rollout(snap, 'player_0', 20)
    assert Globals.events is live and len(live) == 1 and node.value == []
    assert not hasattr(Globals, 'new_attribute')
    assert h.exact_digest(h.rng_state()) == live_rng
    assert snap.env.state == (20, (0, 0), 20)


def test_submission_protection_requires_both_weights_and_zip(tmp_path):
    from scripts.holder_rollout_probe import protected_inputs
    with pytest.raises(ValueError): protected_inputs(tmp_path)
    directory = tmp_path / 'agents/sherlock/weights'; directory.mkdir(parents=True)
    (directory / 'agent_p0.pth').write_bytes(b'altered')
    (directory / 'agent_p1.pth').write_bytes(b'altered')
    (tmp_path / 'Gruppe15.zip').write_bytes(b'altered')
    with pytest.raises(ValueError): protected_inputs(tmp_path)


def test_module_fingerprint_detects_in_memory_weights_modes_and_hooks():
    a = toy_agent()
    original = h.module_fingerprint(a)
    with torch.no_grad(): a.q.weight[0, 0] += 1
    assert h.module_fingerprint(a) != original
    original = h.module_fingerprint(a)
    a.q.train()
    assert h.module_fingerprint(a) != original
    a.q.eval(); original = h.module_fingerprint(a)
    handle = a.q.register_forward_hook(lambda m, i, o: o)
    assert h.module_fingerprint(a) != original
    handle.remove()
