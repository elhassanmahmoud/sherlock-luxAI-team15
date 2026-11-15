import numpy as np
import pytest

from scripts.final_learning_agent import (HORIZON, MARGIN, movement_design, choose, tracking_result,
                                          EnergyReturnAgent, apply_world_action)
from scripts.final_learning_study import fit_model, heldout_scores, split_keys, validate_dataset


def context():
    shape = (12, 12)
    ctx = dict(W=12, H=12, ally_pos=np.array([[5, 5], [6, 6]]), ally_ene=np.array([45, 30]),
               ally_count=np.zeros(shape, int), enemy_coords=np.array([[8, 5]]),
               enemy_energies=np.array([100]), energy_map=np.zeros(shape),
               explored=np.ones(shape, bool), nebula=np.zeros(shape, bool), point_tiles=np.zeros(shape, bool),
               passable=np.ones(shape, bool), candidate=np.zeros(shape, bool), assigned={0: (8, 9)},
               match_step=12, max_match_steps=100, move_cost=2, sap_cost=30)
    ctx["energy_map"][6,5] = 10
    return ctx


def test_scores_use_only_legal_moves_and_preserve_known_scorers_and_saps():
    ctx = context()
    mask = np.array([True, True, True, False, True, True])
    design = movement_design(ctx, 0, mask, 1)
    assert design is not None
    features, legal = design
    assert list(legal) == [True, True, True, False, True]
    values = np.array([0, 1, 7, 999, 2])
    assert choose(values, legal, 1, threshold=7) == 1
    assert choose(values, legal, 1, threshold=6) == 2
    assert movement_design(ctx, 0, mask, 5) is None
    ctx['point_tiles'][5,4] = True
    assert movement_design(ctx, 0, mask, 1) is None
    ctx['point_tiles'][5,4] = False
    ctx['point_tiles'][5,5] = True
    assert movement_design(ctx, 0, mask, 1) is None
    assert features.shape[0] == 5


def test_respawn_or_negative_energy_is_absorbing_and_horizon_is_exact():
    event = dict(initial=40, uid=0, step=10, last_pos=(5,5))
    def obs(x, y, energy=43, alive=True):
        return dict(units=dict(position=np.array([[[x,y]], [[0,0]]]), energy=np.array([[energy],[0]])),
                    units_mask=np.array([[alive],[False]]))
    assert tracking_result(event, 11, obs(5,4), 0) is None
    assert tracking_result(event, 10+HORIZON, obs(5,4,56), 0) == (16.0, False)
    assert tracking_result(event, 11, obs(0,0,100), 0) == (-80.0, True)
    assert tracking_result(event, 11, obs(5,5,-1), 0) == (-80.0, True)
    assert tracking_result(event, 11, obs(5,5,1,False), 0) == (-80.0, True)


def test_mirror_syncs_final_actions_and_own_bookkeeping():
    actions = np.zeros((2,3),int)
    state = {}
    apply_world_action(actions, state, 1, 2, True)
    assert list(actions[1]) == [1,0,0]
    assert state == {1:2}


def test_fixed_arrays_and_ridge_estimate_randomized_action_gain():
    rng = np.random.default_rng(3)
    ctx = context()
    matrix, legal = movement_design(ctx, 0, np.ones(6,bool), 0)
    rows = []
    for seed in [11,12,13,14]:
        for i in range(120):
            a = int(rng.integers(5))
            y = (18 if a == 2 else 0) + rng.normal(0,.3)
            rows.append(dict(seed=seed, side=0, step=i, uid=0, base=0, chosen=a, legal=legal.tolist(),
                             x=matrix.tolist(), y=y, died=False))
    weights = fit_model(rows[:240])
    report = heldout_scores(rows[240:], weights)
    assert report["changes"] == 240
    assert report["map_mean_gain"] == pytest.approx(18, abs=2)
    assert set(split_keys("train")).isdisjoint(split_keys("diagnose"))
    with pytest.raises(ValueError):
        validate_dataset(rows, "train")


def test_parameter_estimator_records_actual_move_and_removes_stale_stationary_events(monkeypatch):
    from types import SimpleNamespace
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.main import Agent_x
    from scripts.final_learning_agent import FEATURES

    agent = EnergyReturnAgent.__new__(EnergyReturnAgent)
    agent.cfg = AgentConfig(nebula_avoid=True)
    agent.training = False
    agent.env_cfg = {}
    agent.team_id = 0
    agent.belief = SimpleNamespace(mirrored=False)
    agent.probes = agent.changes = agent.next_probe = agent.caught_errors = 0
    agent.pending = None
    agent.collect = False
    agent.coefficients = np.zeros(len(FEATURES))
    agent.coefficients[FEATURES.index("field")] = 30
    recorded = []
    agent.param_est = SimpleNamespace(observe=lambda *args: None, remember=lambda o, t, a: recorded.append(a.copy()))
    def base_actions(self, step, obs):
        self._prev_ctx = context()
        self._prev_masks = {0: np.ones(6, bool)}
        self._prev_actions = {0: 0}
        self._pred_pending = [(0,5,5,45,False), (1,6,6,30,False)]
        self._shape_pending = [(0,5,5,45,False,"man"), (1,6,6,30,False,"man")]
        return np.zeros((2,3), int)
    monkeypatch.setattr(Agent_x, "_act", base_actions)
    actual = agent.act(12, {})
    assert actual[0,0] == 2
    assert np.array_equal(recorded[0], actual)
    assert agent._prev_actions[0] == 2
    assert [row[0] for row in agent._pred_pending] == [1]
    assert [row[0] for row in agent._shape_pending] == [1]
