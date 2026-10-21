"""Passive observer contracts: time, visibility, actions and output integrity."""
import copy
import csv
from types import SimpleNamespace as NS

import numpy as np
import pytest
import torch

from tests.conftest import ENV_CFG, make_obs


def observer_module():
    # A missing observer is a feature failure rather than a collection error.
    import importlib.util
    assert importlib.util.find_spec('scripts.observe_loss_mechanisms'), 'observer not implemented'
    from scripts import observe_loss_mechanisms
    return observe_loss_mechanisms


def state_from(obs, active=((5, 5),)):
    weights = np.zeros((24, 24), int)
    for xy in active:
        weights[xy] = 1
    return NS(units=NS(position=obs['units']['position'].copy(),
                       energy=obs['units']['energy'][..., None].copy()),
              units_mask=obs['units_mask'].copy(), relic_nodes_map_weights=weights,
              relic_nodes_mask=np.array([True, True]),
              relic_nodes=np.array([[5, 5], [18, 18]]),
              map_features=NS(**obs['map_features']))


@pytest.mark.parametrize('team,xy', [(0, (5, 5)), (1, (18, 18))])
def test_passive_act_preserves_actions_rng_and_captures_late_sap(team, xy):
    m = observer_module()
    from agents.sherlock.main import Agent_x
    from agents.sherlock.config import AgentConfig
    from tests.test_mask_and_act import FixedQ
    cfg = AgentConfig(pt_sap=True, scripted_explore=False)
    agent = Agent_x(f'player_{team}', train=False, cfg=cfg, seed=12)
    agent.set_env_cfg(ENV_CFG)
    agent.q = FixedQ(0)
    agent.belief.point_tiles[5, 5] = True
    agent.set_to_eval_mode()
    baseline = copy.deepcopy(agent)
    obs = make_obs(25, 25, team=team, units=[(*xy, 100)],
                   enemies=[(xy[0] + 1, xy[1], 80)])
    expected = baseline.act(25, copy.deepcopy(obs))
    proxy = m.ObservedAgent(agent, f'player_{team}')
    rng_before = torch.get_rng_state().clone()
    actual = proxy.act(25, obs)
    np.testing.assert_array_equal(actual, expected)
    assert torch.equal(rng_before, torch.get_rng_state())
    assert agent.rng.bit_generator.state == baseline.rng.bit_generator.state
    assert '_rule_override' not in agent.__dict__
    assert actual[0, 0] == 5
    d = proxy.decision['units'][0]
    assert d['after_rule'] == 0 and d['late_stay_to_sap']
    assert d['inferred_pt_sap']
    assert d['first_on_tile'] == 0
    assert d['recorded_action_class'] == 5
    assert d['position'] == list(xy)
    assert proxy.decision['known_point_tiles'] == [list(xy)]


def test_visible_context_excludes_masked_enemy_and_labels_cost_only_risk():
    m = observer_module()
    obs = make_obs(25, 25, units=[(5, 5, 60)], enemies=[(6, 5, 50), (5, 6, 120)])
    obs['units_mask'][1, 1] = False
    context = m.visible_context(obs, 0, 0, ENV_CFG)
    assert len(context['visible_enemies']) == 1
    enemy = context['visible_enemies'][0]
    assert enemy['position'] == [6, 5]
    assert enemy['adjacent'] and enemy['can_move_to_unit']
    assert enemy['cost_only_margin_stay'] == 13
    assert enemy['cost_only_margin_sap'] == -27
    assert 'kill' not in enemy
    obs['map_features']['tile_type'][5, 5] = 2
    assert not m.visible_context(obs, 0, 0, ENV_CFG)['visible_enemies'][0]['can_move_to_unit']
    obs['map_features']['tile_type'][5, 5] = 0
    obs['units']['energy'][1, 0] = 2
    assert not m.visible_context(obs, 0, 0, ENV_CFG)['visible_enemies'][0]['can_move_to_unit']


class QuietAgent:
    def __init__(self):
        self.belief = NS(point_tiles=np.zeros((24, 24), bool), mirrored=False)
        self.belief.point_tiles[5, 5] = True

    def act(self, step, obs):
        return np.zeros((16, 3), int)


class FinalTwoSteps:
    def reset(self, **kwargs):
        self.n = 0
        self.o = make_obs(99, 99, units=[(5, 5, 20)], points=(6, 3))
        self.state = state_from(self.o)
        return {'player_0': self.o, 'player_1': self.o}, {'params': ENV_CFG}

    def step(self, actions):
        self.n += 1
        done = self.n == 2
        self.o = make_obs(99 + self.n, 0 if done else 100, units=[(5, 5, 20)],
                          points=(0, 0) if done else (7, 3), wins=(1, 0) if done else (0, 0))
        final_state = state_from(self.o)
        # The wrapper must use the transition's state, not a reset/replaced state.
        self.state = state_from(self.o, active=()) if done else final_state
        flags = {'player_0': done, 'player_1': done}
        return {'player_0': self.o, 'player_1': self.o}, {}, flags, flags, {'final_state': final_state}


def test_time_alignment_final_increment_and_match_winner():
    m = observer_module()
    events = []
    row, summary = m.observe_game(FinalTwoSteps(), QuietAgent(), QuietAgent(),
                                 510862, 'player_0', events.append)
    assert row['our_points'] == 2  # 7-6, then 8-7, despite reset to zero.
    assert summary['matches'][0]['points'] == [8, 3]
    assert summary['matches'][0]['winner'] == 0
    assert summary['matches'][0]['tiebreak'] == 'points'
    assert len(summary['snapshots']) == 1
    snap = summary['snapshots'][0]
    assert snap['match_step_t'] == 100 and snap['step_t'] == 100
    assert snap['points_t'] == [7, 3]
    assert snap['points_after'] == [8, 3]
    assert snap['truth_t']['productive_tiles'][0] == [[5, 5]]
    assert events[-1]['truth_after']['active_point_tiles'] == [[5, 5]]
    assert events[-1]['match_reset_after']
    assert events[-1]['match_step_after'] == 0
    assert events[-1]['observed_after']['mask'][0][0]
    assert events[-1]['observed_after']['position'][0][0] == [5, 5]


def reference_rows(m):
    from scripts.experiment import GAME_FIELDS
    rows = []
    for seed, side in m.GAME_KEYS:
        row = dict.fromkeys(GAME_FIELDS, '0')
        row.update(seed=str(seed), side=side, opponent='solution92', steps='303',
                   point_counting_version='2', secs='99.2')
        rows.append(row)
    return rows


def write_reference(path, rows):
    from scripts.experiment import GAME_FIELDS
    with path.open('w') as handle:
        w = csv.DictWriter(handle, GAME_FIELDS)
        w.writeheader()
        w.writerows(rows)


def test_reference_requires_exact_unique_keys_and_compares_every_non_time_field(tmp_path):
    m = observer_module()
    path = tmp_path / 'ref.csv'
    rows = reference_rows(m)
    write_reference(path, rows)
    reference = m.load_reference(path)
    row = dict(rows[0], secs=1)
    m.check_reference(row, reference)
    row['sap_hits'] = 1
    with pytest.raises(ValueError, match='sap_hits'):
        m.check_reference(row, reference)
    write_reference(path, rows[:-1])
    with pytest.raises(ValueError, match='missing'):
        m.load_reference(path)
    write_reference(path, rows + [rows[0]])
    with pytest.raises(ValueError, match='duplicate'):
        m.load_reference(path)


def test_exclusive_output_and_hash_binding(tmp_path):
    m = observer_module()
    out = tmp_path / 'out'
    out.mkdir()
    with pytest.raises(FileExistsError):
        m.prepare_output(out)
    source = tmp_path / 'input'
    source.write_bytes(b'abc')
    assert m.sha256(source) == 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    manifest = {'inputs': {str(source): m.sha256(source)}, 'sources': {}}
    m.verify_hashes(manifest)
    source.write_bytes(b'changed')
    with pytest.raises(ValueError, match='changed'):
        m.verify_hashes(manifest)


def test_risk_requires_direct_visibility_and_records_stack():
    m = observer_module()
    obs = make_obs(25, 25, units=[(5, 5, 60), (5, 5, 80)], enemies=[(6, 5, 50)])
    context = m.visible_context(obs, 0, 0, ENV_CFG)
    assert context['own_stack_size'] == 2
    assert context['direct_sensor'] and context['tile_type'] == 0
    obs['sensor_mask'][5, 5] = False
    assert not m.visible_context(obs, 0, 0, ENV_CFG)['visible_enemies'][0]['can_move_to_unit']


def test_competing_override_is_not_attributed_to_pt_sap():
    m = observer_module()
    from agents.sherlock.main import Agent_x
    from agents.sherlock.config import AgentConfig
    from tests.test_mask_and_act import FixedQ
    agent = Agent_x('player_0', train=False, cfg=AgentConfig(pt_sap=True, idle_sap=True))
    agent.set_env_cfg(ENV_CFG)
    agent.q = FixedQ(0)
    agent.belief.point_tiles[5, 5] = True
    proxy = m.ObservedAgent(agent, 'player_0')
    proxy.act(25, make_obs(25, 25, units=[(5, 5, 100)], enemies=[(6, 5, 80)]))
    assert proxy.decision['units'][0]['late_stay_to_sap']
    assert not proxy.decision['units'][0]['inferred_pt_sap']
