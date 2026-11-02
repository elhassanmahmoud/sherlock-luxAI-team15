"""Pure admission-tool tests: no weights, model imports or engine games."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

TOOL = Path(__file__).resolve().parents[1] / 'experiments/analysis/gauss_admission_20261102/admission.py'


def tool():
    assert TOOL.exists(), 'admission tool is missing'
    spec = importlib.util.spec_from_file_location('gauss_admission', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bitsets_use_literal_little_endian_x_times_24_plus_y():
    a = tool()
    encoded = a.pack_tiles({0, 7, 8, 24, 575})
    assert encoded == '81010001' + '00' * 67 + '80'
    assert a.unpack_tiles(encoded) == {0, 7, 8, 24, 575}
    with pytest.raises(ValueError):
        a.pack_tiles({576})
    with pytest.raises(ValueError):
        a.unpack_tiles('00')


def test_fixed_stage_keys_are_complete_and_cannot_be_shortened():
    a = tool()
    assert a.stage_keys('C') == [(831006, 'player_1'), (831029, 'player_0'),
                                 (831042, 'player_0'), (831043, 'player_1')]
    keys = a.stage_keys('S')
    assert len(keys) == 80 and len(set(keys)) == 80
    assert keys[:2] == [(840000, 'player_0'), (840000, 'player_1')]
    assert keys[-1] == (840039, 'player_1')
    with pytest.raises(ValueError):
        a.stage_keys('short')


def test_novelty_excludes_prior_v_knowledge_and_simultaneous_a_or_v():
    a = tool()
    pre = {'V': {'point': {1}, 'dead': {2}},
           'A': {'point': set(), 'dead': set()},
           'G': {'point': {9}, 'dead': set()}}
    post = {'V': {'point': {1, 3}, 'dead': {2}},
            'A': {'point': {4}, 'dead': set()},
            'G': {'point': {1, 2, 3, 4, 5, 9}, 'dead': {6}}}
    m = a.frame_metrics(pre, post, {1, 3, 4, 5, 9})
    assert m['extra_current']['point'] == [3, 4, 5]
    assert m['strict']['point'] == [5]
    assert m['strict']['dead'] == [6]
    assert m['conflicts']['G_point_V_dead'] == [2]
    assert m['false_extra']['G']['point'] == [2]
    assert m['differences']['V-G']['point'] == []
    assert m['differences']['A-V']['point'] == [4]


def test_truth_uses_current_relic_mask_threshold_and_antidiagonal_p1():
    a = tool()
    state = SimpleNamespace(relic_nodes_map_weights=np.zeros((24, 24), dtype=int),
                            relic_nodes_mask=np.array([1, 1, 0, 0, 0, 0]),
                            relic_nodes=np.array([[1, 2], [21, 22], [0, 0], [0, 0], [0, 0], [0, 0]]))
    state.relic_nodes_map_weights[2, 5] = 1
    state.relic_nodes_map_weights[3, 7] = 2
    state.relic_nodes_map_weights[0, 0] = -1
    from scripts.oracle_probe import truth_maps
    assert a.canonical_truth(state, False, truth_maps) == {53}
    assert a.canonical_truth(state, True, truth_maps) == {453}  # (18,21), not (21,18)
    state.relic_nodes_mask[:] = 1
    assert a.canonical_truth(state, False, truth_maps) == {53, 79}


class TinyBelief:
    """Observe double with the same reset/idempotence boundary as Belief."""
    def __init__(self):
        self._point, self._dead = set(), set()
        self.records, self.cache = [], np.zeros(2)
        self._last_step = -1
        self.match_idx = 0
        self.sensor_range = None
        self.overlap_infer = self.gauss_infer = False
        self._gauss_attempts = self._gauss_observations = 0
        self._gauss_last_observation = -8
        self.mirrored = False

    def observe(self, obs):
        step = int(obs['steps'])
        if self._last_step == step:
            return
        self._last_step = step
        self.match_idx = step // 101
        if int(obs['match_steps']) == 0:
            self._dead.clear()
            self._gauss_attempts = self._gauss_observations = 0
            return
        self._gauss_observations += 1
        self.records.append(step)
        self.cache[0] += 1
        self._point.add(1)
        if self.overlap_infer:
            self._point.add(2)
            obs['nested']['array'][0] = 99
        if self.gauss_infer:
            self._dead.add(3)


class TinyAgent:
    def __init__(self):
        self.belief = TinyBelief()
        self.calls = 0

    def new_game(self, side):
        self.belief.__init__()

    def act(self, step, obs):
        self.calls += 1
        self.belief.observe(obs)
        self.belief.observe(obs)  # existing duplicate, no extra shadow processing
        return np.array([[2, -1, 4]], dtype=np.int16)


def test_shadow_reset_independence_idempotence_public_copies_and_truth_after_act():
    a = tool()
    agent = TinyAgent()
    trace = a.ShadowTrace(agent, shadows=True)
    agent.new_game('player_1')
    v, overlap, gauss = (trace.beliefs[k] for k in ('V', 'A', 'G'))
    assert len({id(x.records) for x in (v, overlap, gauss)}) == 3
    assert not np.shares_memory(v.cache, overlap.cache)
    assert not np.shares_memory(overlap.cache, gauss.cache)
    obs = {'steps': 0, 'match_steps': 0, 'nested': {'array': np.zeros(1)}}
    action = agent.act(0, obs)
    assert trace.pending['reset'] is True
    assert trace.pending['post']['G']['dead'] == set()
    assert trace.finish({1, 2}, {'player_1': action})['reset'] is True
    obs['steps'] = obs['match_steps'] = 1
    action = agent.act(1, obs)
    assert agent.calls == 2
    assert overlap.records == gauss.records == v.records == [1]
    assert obs['nested']['array'][0] == 0
    assert trace.pending['post']['G']['dead'] == {3}
    frame = trace.finish({1, 2}, {'player_1': action})
    assert frame['action']['player_1'] == {'shape': [1, 3], 'dtype': '<i2', 'order': 'C', 'hex': '0200ffff0400'}
    assert frame['truth'] == '06' + '00' * 71
    assert frame['post']['G']['dead'] == '08' + '00' * 71
    agent.new_game('player_0')
    assert trace.beliefs['G']._point == set()
    assert trace.beliefs['G'].records == []


def test_native_action_capture_returns_same_object_and_records_each_call_once():
    a = tool()
    agent = TinyAgent()
    original = agent.act
    returned = np.array([[5, 2, -1]], dtype=np.int64)
    agent.act = lambda step, obs: returned
    capture = a.NativeAct(agent)
    assert agent.act(0, {}) is returned
    assert capture.last['hex'] == '05000000000000000200000000000000ffffffffffffffff'
    with pytest.raises(ValueError):
        a.NativeAct(agent)


def test_weights_missing_and_wrong_bytes_fail_before_model_import(tmp_path):
    a = tool()
    with pytest.raises(FileNotFoundError):
        a.check_weights(tmp_path / 'missing.pth')
    p = tmp_path / 'wrong.pth'
    p.write_bytes(b'wrong')
    with pytest.raises(ValueError, match='V14'):
        a.check_weights(p)


def test_snapshot_detects_runtime_edit_and_head_change(tmp_path):
    a = tool()
    p = tmp_path / 'runtime.py'
    p.write_text('first')
    snap = a.file_identity(p)
    a.check_identity(snap)
    p.write_text('second')
    with pytest.raises(ValueError, match='changed'):
        a.check_identity(snap)


def test_reconstruct_uses_raw_pre_states_and_rejects_wrong_oriented_truth():
    a = tool()
    frame = {'step': 1, 'match': 0, 'match_step': 1, 'reset': False,
             'pre': {k: {'point': a.pack_tiles(set()), 'dead': a.pack_tiles(set())} for k in 'VAG'},
             'post': {k: {'point': a.pack_tiles({53}) if k == 'G' else a.pack_tiles(set()),
                          'dead': a.pack_tiles(set())} for k in 'VAG'},
             'truth': a.pack_tiles({53}),
             'attempts': {k: {'pre': [0, 0, -8], 'post': [0, 1, -8]} for k in 'VAG'},
             'times': {k: {'cpu_ns': 100, 'wall_ns': 200} for k in 'VAG'}}
    metrics = a.reconstruct([frame], seed=840000, side='player_0')
    assert metrics['strict_facts'] == [[840000, 'player_0', 0, 53, 'point']]
    assert metrics['false_extra']['G'] == 0
    assert metrics['lead'][0]['V'] is None
    frame['truth'] = a.pack_tiles({453})
    metrics = a.reconstruct([frame], seed=840000, side='player_0')
    assert metrics['false_extra']['G'] == 1


def test_stage_comparison_rejects_missing_keys_or_native_mismatch():
    a = tool()
    rows = []
    for seed, side in a.stage_keys('C'):
        rows.append(dict(seed=seed, side=side, steps=303, fresh=300, resets=3,
                         our_wins=2, opp_wins=1, result=1., our_points=50, opp_points=40,
                         point_counting_version=2, action_sha256='a', v_attempts=0))
    known = [{k: row[k] for k in a.RESULT_FIELDS} for row in rows]
    a.compare_stage('C', rows, copy.deepcopy(rows), known)
    with pytest.raises(ValueError, match='keys'):
        a.compare_stage('C', rows[:-1], rows, known)
    other = copy.deepcopy(rows)
    other[0]['action_sha256'] = 'b'
    with pytest.raises(ValueError, match='action_sha256'):
        a.compare_stage('C', rows, other, known)


def test_prepare_rejects_existing_destination_before_inspecting_sources(tmp_path):
    a = tool()
    with pytest.raises(FileExistsError):
        a.prepare(tmp_path, tmp_path / 'badbase', tmp_path / 'badproto', tmp_path / 'missing', tmp_path / 'missing.csv')


def raw_frame(a, step, *, dead=(), v_dead=(), truth=()):
    return {'step': step, 'match': step // 101, 'match_step': step % 101,
            'reset': step % 101 == 0,
            'pre': {k: {'point': a.pack_tiles(set()), 'dead': a.pack_tiles(set())} for k in 'VAG'},
            'post': {k: {'point': a.pack_tiles(set()), 'dead': a.pack_tiles(set(dead if k == 'G' else v_dead if k == 'V' else ()))} for k in 'VAG'},
            'truth': a.pack_tiles(set(truth)),
            'attempts': {k: {'pre': [0, max(0, step - 1), -8], 'post': [0, step, -8]} for k in 'VAG'},
            'times': {k: {'cpu_ns': 100, 'wall_ns': 200} for k in 'VAG'}}


def test_dead_lead_is_censored_after_truth_regime_changes():
    a = tool()
    frames = [raw_frame(a, 1, dead={7}), raw_frame(a, 2, truth={8}),
              raw_frame(a, 3, v_dead={7}, truth={8})]
    m = a.reconstruct(frames, 840000, 'player_0')
    assert m['lead'][0]['V'] is None
    assert m['lead'][0]['censored_reason'] == 'truth_regime_change'


def test_attempt_audit_rejects_observation_counter_gaps_and_bad_match_reset():
    a = tool()
    frame = raw_frame(a, 1)
    frame['attempts']['G']['post'][1] = 2
    with pytest.raises(ValueError, match='observation'):
        a.reconstruct([frame], 840000, 'player_0')
    frame = raw_frame(a, 101)
    frame['attempts']['G']['post'] = [1, 0, -8]
    with pytest.raises(ValueError, match='reset'):
        a.reconstruct([frame], 840000, 'player_0')


def test_real_belief_copies_preserve_positive_carryovers_and_clear_dead_on_match_reset():
    a = tool()
    from agents.sherlock.belief import Belief
    from tests.conftest import make_obs
    agent = TinyAgent()
    agent.belief = Belief(0, early_inference=True)
    agent.new_game = lambda side: agent.belief.reset_game()
    trace = a.ShadowTrace(agent, shadows=True)
    agent.new_game('player_0')
    agent.belief.observe(make_obs(55, 55, units=[(5, 5, 50)], points=(1, 0)))
    trace.finish({125}, {})
    gauss = trace.beliefs['G']
    gauss._mark_point(126)
    gauss._mark_dead(127)
    gauss.records.append(((200, 201), 1))
    assert 126 not in agent.belief._point
    assert ((200, 201), 1) not in trace.beliefs['A'].records
    agent.belief.observe(make_obs(101, 0))
    assert 126 in gauss._point and 127 not in gauss._dead
    assert trace.pending['reset'] is True
    trace.finish({125, 126}, {})
    agent.new_game('player_0')
    assert trace.beliefs['G']._point == set()


def test_import_root_guard_rejects_foreign_runtime_module(tmp_path, monkeypatch):
    a = tool()
    import sys
    foreign = tmp_path / 'foreign.py'
    foreign.write_text('')
    root = tmp_path / 'selected'
    root.mkdir()
    monkeypatch.setitem(sys.modules, 'agents.admission_foreign_fixture', SimpleNamespace(__file__=str(foreign)))
    with pytest.raises(ValueError, match='cross-root'):
        a.check_imports(root, {'environment': {'engine': {}}, 'sources': {}})


def test_source_guard_rejects_tracked_runtime_edit_and_repinning(tmp_path, monkeypatch):
    a = tool()
    import subprocess
    def git(*args):
        return subprocess.check_output(['git', '-C', str(tmp_path), *args], text=True).strip()
    git('init', '-q')
    git('config', 'user.email', 'fixture@example.invalid')
    git('config', 'user.name', 'Fixture')
    (tmp_path / 'scripts').mkdir()
    path = tmp_path / 'scripts/common.py'
    path.write_text('value = 1\n')
    git('add', '.')
    git('commit', '-qm', 'fixture')
    head = git('rev-parse', 'HEAD')
    monkeypatch.setattr(a, 'REFERENCE', head)
    monkeypatch.setattr(a, 'RUNTIME', head)
    snap = a.source_identity(tmp_path, 'reference')
    assert snap['head'] == head
    a.check_source(snap)
    path.write_text('value = 2\n')
    with pytest.raises(ValueError, match='source changed'):
        a.check_source(snap)
    with pytest.raises(ValueError, match='uncommitted runtime'):
        a.source_identity(tmp_path, 'reference')
    git('add', '.')
    git('commit', '-qm', 'changed')
    with pytest.raises(ValueError, match='HEAD changed'):
        a.check_source(snap)
    with pytest.raises(ValueError, match='HEAD'):
        a.source_identity(tmp_path, 'reference')


def test_prototype_descendant_cannot_silently_change_fixed_solver_runtime(tmp_path, monkeypatch):
    a = tool()
    import subprocess
    def git(*args):
        return subprocess.check_output(['git', '-C', str(tmp_path), *args], text=True).strip()
    git('init', '-q')
    git('config', 'user.email', 'fixture@example.invalid')
    git('config', 'user.name', 'Fixture')
    (tmp_path / 'scripts').mkdir()
    path = tmp_path / 'scripts/common.py'
    path.write_text('value = 1\n')
    git('add', '.')
    git('commit', '-qm', 'prototype basis')
    monkeypatch.setattr(a, 'PROTOTYPE', git('rev-parse', 'HEAD'))
    path.write_text('value = 2\n')
    git('add', '.')
    git('commit', '-qm', 'changed runtime')
    with pytest.raises(ValueError, match='runtime differs'):
        a.source_identity(tmp_path, 'prototype')


def test_raw_audit_rejects_absent_native_opponent_bytes(tmp_path):
    a = tool()
    # Independently hand-written raw record: even a matching digest cannot admit an absent side.
    row = dict(seed=831006, side='player_1', metrics={})
    directory = tmp_path / 'C/reference'
    directory.mkdir(parents=True)
    (directory / 'loaded.json').write_text(json.dumps(dict(nets=36, features=79, actions=6,
        overlap=False, gauss=False, train=False, epsilon=0, autosave=False, tensor_sha256=['0' * 64] * 36)))
    (directory / 'rows.json').write_text(json.dumps([row]))
    with gzip.open(directory / '831006-player_1.jsonl.gz', 'wt') as stream:
        for step in range(303):
            frame = raw_frame(a, step)
            if frame['reset']:
                for attempt in frame['attempts'].values():
                    attempt['post'] = [0, 0, -8]
            else:
                for attempt in frame['attempts'].values():
                    attempt['pre'][1] = frame['match_step'] - 1
                    attempt['post'][1] = frame['match_step']
            frame.update(seed=831006, side='player_1', action={})
            stream.write(json.dumps(frame) + '\n')
    with pytest.raises(ValueError, match='native.*sides'):
        a.audit_stage(tmp_path, 'C', {'known_results': []})


def test_compatibility_gate_rejects_caught_policy_errors():
    a = tool()
    rows = [dict(seed=seed, side=side, steps=303, fresh=300, resets=3,
                 our_wins=2, opp_wins=1, result=1., our_points=50, opp_points=40,
                 point_counting_version=2, action_sha256='a', v_attempts=0, caught_errors=0)
            for seed, side in a.stage_keys('C')]
    known = [{k: row[k] for k in a.RESULT_FIELDS} for row in rows]
    other = copy.deepcopy(rows)
    other[0]['caught_errors'] = 1
    with pytest.raises(ValueError, match='caught'):
        a.compare_stage('C', rows, other, known)


def test_unimported_historical_duplicate_does_not_change_tracked_runtime(tmp_path, monkeypatch):
    a = tool()
    import subprocess
    def git(*args):
        return subprocess.check_output(['git', '-C', str(tmp_path), *args], text=True).strip()
    git('init', '-q')
    git('config', 'user.email', 'fixture@example.invalid')
    git('config', 'user.name', 'Fixture')
    (tmp_path / 'scripts').mkdir()
    (tmp_path / 'scripts/common.py').write_text('value = 1\n')
    git('add', '.')
    git('commit', '-qm', 'fixture')
    monkeypatch.setattr(a, 'REFERENCE', git('rev-parse', 'HEAD'))
    monkeypatch.setattr(a, 'RUNTIME', git('rev-parse', 'HEAD'))
    (tmp_path / 'scripts/common 2.py').write_text('unrelated = 2\n')
    assert set(a.source_identity(tmp_path, 'reference')['files']) == {'scripts/common.py'}


def test_manifest_seal_detects_changed_key_or_source_manifest(tmp_path):
    a = tool()
    path = tmp_path / 'manifest.json'
    path.write_text('{}')
    (tmp_path / 'manifest.sha256').write_text('44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a')
    assert a.read_manifest(tmp_path) == {}
    path.write_text('{"keys": []}')
    with pytest.raises(ValueError, match='manifest changed'):
        a.read_manifest(tmp_path)


def test_audit_rejects_incomplete_loaded_model_proof_before_accepting_rows(tmp_path):
    a = tool()
    directory = tmp_path / 'C/reference'
    directory.mkdir(parents=True)
    (directory / 'loaded.json').write_text(json.dumps({'nets': 35}))
    with pytest.raises(ValueError, match='loaded.model'):
        a.audit_stage(tmp_path, 'C', {'known_results': []})
