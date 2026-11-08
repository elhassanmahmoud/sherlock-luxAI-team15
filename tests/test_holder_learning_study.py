"""Synthetic study/policy contracts; no checkpoint loading or complete games."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import holder_rollout as h


def ctx(step=20, ms=20):
    points = np.zeros((5, 5), bool); points[1, 1] = points[3, 3] = True
    return dict(step=step, match_step=ms, max_match_steps=100, W=5, H=5,
                ally_ids=np.array([0, 1]), ally_pos=np.array([[1, 1], [3, 3]]),
                ally_ene=np.array([20., 20.]), point_tiles=points,
                assigned={0: (1, 1), 1: (3, 3)}, first_on_tile={(1, 1): 0})


@pytest.fixture
def policy(monkeypatch):
    # Replace only model inference and downstream rules; keep the real hook.
    def act(self, ctx):
        q = np.array([[0., 1., 2., 3., 4., -np.inf], [4., 3., 2., 1., 0., -np.inf]])
        result = []
        for k, uid in enumerate((0, 1)):
            result.append(self._rule_override(ctx, uid, np.array([1, 1, 1, 1, 1, 0], bool), 2))
        return result
    monkeypatch.setattr(h.Agent_x, '_act', act)
    monkeypatch.setattr(h.Agent_x, '_rule_override', lambda self, ctx, uid, mask, a: 5 if a == 0 else a)
    agent = object.__new__(h.DiagnosticAgent)
    agent.collect = False; agent.candidate = None; agent.intervention = None; agent.intervention_hits = 0
    agent.head = {'threshold': 1.0}; agent.head_opportunities = 0; agent.last_opportunity_step = -12
    agent._cache = (None, None, None, {0: np.zeros(79), 1: np.zeros(79)})
    learner = SimpleNamespace(predict_gain=lambda head, candidate: head.get('gain', 0.))
    monkeypatch.setitem(sys.modules, 'scripts.holder_learning', learner)
    return agent


def test_rejection_consumes_first_uid_and_cooldown(policy):
    assert policy._act(ctx()) == [2, 2]
    assert policy.head_opportunities == 1 and policy.last_opportunity_step == 20
    policy.head['gain'] = 2.
    assert policy._act(ctx(31)) == [2, 2]
    assert policy.head_opportunities == 1
    assert policy._act(ctx(32)) == [5, 2]  # HOLD still runs the ordinary SAP rules.
    assert policy.head_opportunities == 2


def test_budget_counts_rejections_across_match_reset_and_new_game_resets(policy, monkeypatch):
    for step in range(20, 116, 12): policy._act(ctx(step))
    policy.head['gain'] = 2.
    assert policy._act(ctx(121, 1)) == [2, 2]
    assert policy.head_opportunities == 8
    monkeypatch.setattr(h.Agent_x, 'new_game', lambda self, player=None: None)
    policy.new_game('player_1')
    assert policy.head_opportunities == 0
    assert policy._act(ctx(1, 1)) == [5, 2]


def test_missing_head_bypasses_features_and_cadence(policy):
    policy.head = None
    assert policy._act(ctx()) == [2, 2]
    assert policy.head_opportunities == 0


def test_head_and_forced_intervention_cannot_coexist(policy):
    policy.intervention = h.Intervention(20, 0, 2)
    with pytest.raises(ValueError, match='intervention'): policy._act(ctx())


def test_hook_uses_same_public_candidate_as_passive_collector(policy):
    policy.collect = True; policy.head = None
    policy._act(ctx()); recorded = copy.deepcopy(policy.candidate)
    policy.collect = False; policy.candidate = None; policy.head = {'threshold': 1.0}
    seen = []
    sys.modules['scripts.holder_learning'].predict_gain = lambda head, candidate: seen.append(candidate) or 0.
    policy._act(ctx())
    assert seen == [recorded]
    assert recorded['q'] == [0., 1., 2., 3., 4., None]
    assert 'assigned' in recorded['public']


def test_head_keeps_original_action_caller_check(policy):
    with pytest.raises(RuntimeError, match='caller'):
        policy._rule_override(ctx(), 0, np.ones(6, bool), 2)


def test_plan_rejects_partial_reordered_or_extra_maps(tmp_path):
    from scripts import holder_learning_study as s
    plan = json.loads((s.ROOT / 'experiments/analysis/holder_learning_20261108/plan.json').read_text())
    path = tmp_path / 'plan.json'; path.write_text(json.dumps(plan))
    document, keys, protocols = s.validate_plan(path, 'train')
    assert len(keys) == 48 and keys[0] == {'seed': 6500000, 'side': 'player_0', 'opponent': 'solution92'}
    assert len(protocols) == 2
    for change in ('partial', 'reorder', 'overlap', 'cadence'):
        bad = copy.deepcopy(plan)
        if change == 'partial': bad['train_seeds'].pop()
        if change == 'reorder': bad['validation_seeds'].reverse()
        if change == 'overlap': bad['validation_seeds'][0] = 6500000
        if change == 'cadence': bad['spacing'] = 11
        path.write_text(json.dumps(bad))
        with pytest.raises(ValueError): s.validate_plan(path, 'train')


def test_collection_refuses_validation_before_fit_receipt(tmp_path):
    from scripts import holder_learning_study as s
    plan = s.ROOT / 'experiments/analysis/holder_learning_20261108/plan.json'
    with pytest.raises(ValueError, match='receipt'):
        s.collect(plan, tmp_path / 'new', split='validation', expected_head='x',
                  usage_file=tmp_path / 'usage', stop_file=tmp_path / 'STOP')
    assert not (tmp_path / 'new').exists()


def test_old_probe_still_selects_exact_smoke_protocol(monkeypatch, tmp_path):
    from scripts import holder_rollout_probe as p
    path = p.ROOT / 'experiments/analysis/decision_learning_20261108/keys.json'
    monkeypatch.setattr(p, 'run_collection', lambda *args, **kwargs: kwargs)
    options = p.run_probe(tmp_path / 'weights', path, tmp_path / 'new', expected_head='x',
                          usage_file=tmp_path / 'usage', stop_file=tmp_path / 'STOP', technical_smoke=True)
    assert [(k['seed'], k['side']) for k in options['selected']] == [(831006, 'player_1'), (831043, 'player_0')]
    assert options['max_pairs'] == 1 and options['historical_feasibility'] is True


@pytest.fixture
def collection(tmp_path, monkeypatch):
    import gzip
    import hashlib
    from scripts import holder_learning_study as s
    from scripts.holder_rollout_probe import hashes, write_json
    key = dict(seed=6500000, side='player_0', opponent='solution92')
    plan = tmp_path / 'plan.json'; plan.write_text('{}')
    monkeypatch.setattr(s, 'validate_plan', lambda path, split: ({}, [key], []))
    frames = []
    for step in range(303):
        frame = dict(step=step, before_state='a', before_obs='b', after_state='a', after_obs='b',
                     actions={'player_0': [[2, 0, 0]], 'player_1': [[2, 0, 0]]},
                     points=[0, 0], point_state=[0, 0], done=step == 302)
        frame['action_sha256'] = s.action_digest(frame['actions'])
        frame['sha256'] = h.exact_digest(frame)
        frames.append(frame)
    candidate = dict(step=1, uid=0, proposal=2, match_step=1, q=[0., 1., 2., 3., 4., None],
                     mask=[True, True, True, True, True, False], public={})
    branch = dict(frames=frames[1:13], points=[0, 0], point_differential=0,
                  sha256=h.exact_digest(frames[1:13]))
    pair = dict(pair_id=0, seed=6500000, side='player_0', status='pending_live_verification',
                candidate=candidate, baseline=branch, hold=copy.deepcopy(branch), effective=False,
                label=0, reverse_repeat={'hold_repeat': True, 'baseline_reverse_repeat': True})
    summary = dict(pair_id=0, step=1, uid=0, effective=False, label=0,
                   reverse_repeat=pair['reverse_repeat'], live_verified=True)
    trajectory = hashlib.sha256(b''.join(bytes.fromhex(f['sha256']) for f in frames)).hexdigest()
    result = dict(seed=6500000, side='player_0', steps=303, resets=3, wins=[0, 0], points=[0, 0],
                  matches=[{}, {}, {}], point_counting_version=2, trajectory_sha256=trajectory, caught_errors=0)
    game = {'key': key}
    for mode in ('reference', 'collector'):
        name = f'6500000_player_0_{mode}'
        fp = tmp_path / (name + '.frames.jsonl.gz')
        with gzip.open(fp, 'wt') as stream:
            for frame in frames: stream.write(json.dumps(frame) + '\n')
        pp = tmp_path / (name + '.pairs.jsonl')
        entries = [pair, dict(pair_id=0, status='live_verified', baseline_sha256=branch['sha256'])] if mode == 'collector' else []
        pp.write_text(''.join(json.dumps(row) + '\n' for row in entries))
        game[mode] = dict(result, pairs=[summary] if mode == 'collector' else [])
        game[mode + '_artifacts'] = hashes([fp, pp])
    game['passivity'] = {k: True for k in result}
    state = dict(schema_version=1, kind='holder_learning_train', split='train', status='complete',
                 baseline_sha256=s.V14_SHA, plan_sha256=s.digest(plan), keys=[key], all_keys=[key],
                 planned_games=2, completed_games=2, completed_pairs=1, horizon=12, max_pairs_per_game=8,
                 reference_steps=303, instrumented_steps=303, diagnostic_steps=24, technical_extra_steps=24,
                 additional_steps=48, inputs=hashes([plan]), protected={}, source={'head': 'x'}, games=[game])
    manifest = tmp_path / 'manifest.json'; write_json(manifest, state)
    return s, plan, manifest, state, pair


def test_reader_keeps_zero_pairs_and_requires_complete_live_evidence(collection):
    s, plan, manifest, state, _ = collection
    rows, loaded = s.read_collection(manifest, plan, 'train')
    assert [(r['seed'], r['side'], r['label']) for r in rows] == [(6500000, 'player_0', 0)]
    assert loaded == state
    state['games'][0]['collector']['pairs'][0]['live_verified'] = False
    s.write_json(manifest, state)
    with pytest.raises(ValueError, match='summary|verified'): s.read_collection(manifest, plan, 'train')


def test_reader_recomputes_passivity_instead_of_trusting_flags(collection):
    s, plan, manifest, state, _ = collection
    state['games'][0]['collector']['wins'] = [1, 0]
    s.write_json(manifest, state)
    with pytest.raises(ValueError, match='passivity'): s.read_collection(manifest, plan, 'train')


def test_reader_rejects_modified_artifacts_and_incorrect_counterfactual_label(collection):
    s, plan, manifest, state, pair = collection
    pair_path = next(Path(p) for p in state['games'][0]['collector_artifacts'] if p.endswith('.pairs.jsonl'))
    entries = [json.loads(line) for line in pair_path.read_text().splitlines()]
    entries[0]['label'] = 9
    pair_path.write_text(''.join(json.dumps(row) + '\n' for row in entries))
    with pytest.raises(ValueError, match='artifact'): s.read_collection(manifest, plan, 'train')
    state['games'][0]['collector_artifacts'][str(pair_path)] = s.digest(pair_path)
    s.write_json(manifest, state)
    with pytest.raises(ValueError, match='label'): s.read_collection(manifest, plan, 'train')


def test_neutral_proof_prepares_exact_four_games_without_rollouts(monkeypatch, tmp_path):
    from scripts import holder_learning_study as s
    from scripts.holder_learning import predict_gain
    monkeypatch.setattr(s, 'run_collection', lambda *args, **kwargs: kwargs)
    options = s.neutral_proof(s.ROOT / 'experiments/analysis/holder_learning_20261108/plan.json', tmp_path / 'new',
                              expected_head='x', usage_file=tmp_path / 'usage', stop_file=tmp_path / 'STOP')
    assert options['max_pairs'] == 0
    assert [(k['seed'], k['side']) for k in options['selected']] == [(831006, 'player_1'), (831043, 'player_0')]
    assert options['head']['intercept'] == 0. and options['head']['coefficients'] == [0.]*16


def test_validation_checks_fit_before_opening_validation_labels(monkeypatch, tmp_path):
    from scripts import holder_learning_study as s
    def reject(*args, **kwargs): raise ValueError('receipt is invalid')
    monkeypatch.setattr(s, 'read_fit_receipt', reject)
    def forbidden(*args): pytest.fail('Validation labels were read before fit receipt validation')
    monkeypatch.setattr(s, 'read_collection', forbidden)
    with pytest.raises(ValueError, match='receipt'):
        s.validate(tmp_path / 'plan', tmp_path / 'validation', tmp_path / 'fit', tmp_path / 'out', expected_head='x')


def test_fit_receipt_pins_exact_head_and_rejects_mutation_and_second_output(collection, monkeypatch, tmp_path):
    s, plan, manifest, state, _ = collection
    import scripts.holder_learning as learner
    source = {'head': 'x'}
    monkeypatch.setattr(s, '_source', lambda protocols: source)
    def fit_once(rows, *, provenance):
        assert len(rows) == 1 and rows[0]['label'] == 0
        return dict(schema_version=1, feature_version=learner.FEATURE_VERSION, feature_names=list(learner.FEATURE_NAMES),
                    eligibility_version=learner.ELIGIBILITY_VERSION, cadence=dict(learner.CADENCE), horizon=12,
                    mean=[0.]*16, scale=[1.]*16, coefficients=[0.]*16, intercept=0., ridge_alpha=.1, threshold=1.,
                    baseline_sha256=s.V14_SHA, provenance=provenance), {'passed': True}
    monkeypatch.setattr(learner, 'fit_head', fit_once)
    out = tmp_path / 'fit'
    receipt = s.fit(plan, manifest, out, expected_head='x')
    loaded, head = s.read_fit_receipt(out / 'receipt.json', plan, expected_head='x')
    assert loaded == receipt and head['provenance']['training_manifest_sha256'] == s.digest(manifest)
    assert head['provenance']['training_artifacts'] == s.artifact_hashes(state)
    with pytest.raises(ValueError, match='Output'):
        s.fit(plan, manifest, out, expected_head='x')
    head['intercept'] = 2.
    s.write_json(out / 'head.json', head)
    with pytest.raises(ValueError, match='head/report'):
        s.read_fit_receipt(out / 'receipt.json', plan, expected_head='x')


def test_neutral_proof_rejects_unexercised_hook(monkeypatch, tmp_path):
    from contextlib import nullcontext
    from scripts import holder_rollout_probe as p
    weights = tmp_path / 'weights'; weights.write_bytes(b'fake')
    monkeypatch.setattr(p, 'digest', lambda path: p.V14_SHA)
    monkeypatch.setattr(p, 'protected_inputs', lambda root: [])
    monkeypatch.setattr(p, 'source_identity', lambda *args: {'head': 'x'})
    monkeypatch.setattr(p, 'Guard', lambda state: lambda **kwargs: None)
    monkeypatch.setattr(p, 'resource_lock', lambda root: nullcontext())
    def passive(*args, instrumented, frame_path, pair_path, **kwargs):
        frame_path.write_bytes(b''); pair_path.write_bytes(b'')
        return dict(pairs=[], **({'head_opportunities': 0} if instrumented else {}))
    monkeypatch.setattr(p, 'play', passive)
    key = dict(seed=831006, side='player_1', opponent='solution92')
    with pytest.raises(ValueError, match='head.*opportunit'):
        p.run_collection(weights, tmp_path / 'new', selected=[key], all_keys=[key], frozen_inputs=[weights],
                         source_plans=p.PLANS, expected_head='x', usage_file=tmp_path / 'usage',
                         stop_file=tmp_path / 'STOP', kind='holder_learning_neutral_proof', max_pairs=0, head={})
