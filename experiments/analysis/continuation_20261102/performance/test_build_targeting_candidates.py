"""Pure dictionary checks: no checkpoint loading, tensors, games or promotion."""
import copy
import contextlib
import importlib.util
import inspect
import io
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('build_targeting_candidates', HERE / 'build_targeting_candidates.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class CandidateStructureTests(unittest.TestCase):
    def setUp(self):
        self.states = [dict(weight=[[i, i + 1]], bias=[i / 100]) for i in range(36)]
        self.source = dict(q=self.states[0], ensemble=self.states[1:],
            cfg=dict(point_pair_swap=False, art_move_guard=False, frozen=True,
                     cand_rescue=True, rescue_after=30, w_discovery=.5, w_explore=.3),
            feature_dim=79, n_actions=6, ensemble_dims=[79]*35,
            env_steps=12345, metadata=dict(label='synthetic source'))

    def test_p_has_no_component_replacement(self):
        p = builder.make_candidate(self.source, {})
        self.assertEqual([p['q'], *p['ensemble']], self.states)
        self.assertEqual(p['ensemble_dims'], [79]*35)

    def test_exactly_two_configuration_flags_change(self):
        p = builder.make_candidate(self.source, {})
        changed = {key for key in p['cfg'] if p['cfg'][key] != self.source['cfg'].get(key)}
        self.assertEqual(changed, {'point_pair_swap', 'art_move_guard'})
        self.assertIs(p['cfg']['point_pair_swap'], True)
        self.assertIs(p['cfg']['art_move_guard'], True)
        self.assertEqual(p['metadata'], {'label': 'synthetic source'})

    def test_pt_replaces_exact_positions_18_and_19_in_q_plus_ensemble(self):
        replacement18, replacement19 = dict(weight=[[1800]]), dict(weight=[[1900]])
        pt = builder.make_candidate(self.source, {18: replacement18, 19: replacement19})
        actual = [pt['q'], *pt['ensemble']]
        self.assertEqual([i for i in range(36) if actual[i] != self.states[i]], [18, 19])
        self.assertEqual(actual[18], replacement18)
        self.assertEqual(actual[19], replacement19)
        self.assertEqual(actual[0], self.states[0])
        self.assertEqual(actual[17], self.states[17])
        self.assertEqual(actual[20], self.states[20])

    def test_p_and_pt_both_keep_exactly_36_ordered_networks(self):
        for changes in ({}, {18: dict(weight=[[1800]]), 19: dict(weight=[[1900]])}):
            with self.subTest(changes=bool(changes)):
                candidate = builder.make_candidate(self.source, changes)
                self.assertEqual(1 + len(candidate['ensemble']), 36)
                self.assertEqual(len(candidate['ensemble_dims']), 35)

    def test_source_and_replacement_objects_are_not_mutated_or_aliased(self):
        before = copy.deepcopy(self.source)
        replacements = {18: dict(weight=[[1800]]), 19: dict(weight=[[1900]])}
        before_replacements = copy.deepcopy(replacements)
        pt = builder.make_candidate(self.source, replacements)
        self.assertEqual(self.source, before)
        pt['q']['weight'][0][0] = -1
        pt['ensemble'][17]['weight'][0][0] = -1
        pt['cfg']['w_discovery'] = -1
        self.assertEqual(self.source, before)
        self.assertEqual(replacements, before_replacements)

    def test_invalid_components_are_rejected_before_returning_a_candidate(self):
        for index in (-1, 0, 1, 17, 20, 35, 36, 37, True, '18'):
            with self.subTest(index=index), self.assertRaises(ValueError):
                builder.make_candidate(self.source, {index: dict(weight=[[999]])})
        self.assertNotIn('torch', sys.modules)


class CandidateBuildModeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path('/tmp').resolve())
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.states = [dict(weight=[[index]], bias=[index / 100]) for index in range(36)]
        self.source = dict(q=self.states[0], ensemble=self.states[1:], cfg=dict(
            point_pair_swap=False, art_move_guard=False, frozen=True, cand_rescue=True,
            rescue_after=30, w_discovery=.5, w_explore=.3),
            feature_dim=79, n_actions=6, ensemble_dims=[79]*35)
        self.source_path = self.root / 'synthetic_source.pth'
        self.source_path.write_bytes(b'synthetic dictionary fixture; never torch data')
        self.checkpoints = {self.source_path: self.source}
        self.loaded = []

    @contextlib.contextmanager
    def dictionary_runtime(self):
        """Execute builder guards with JSON dictionaries, never the torch runtime."""
        torch = ModuleType('torch')

        def load(path, **kwargs):
            path = Path(path)
            self.loaded.append(path)
            if path in self.checkpoints:
                return copy.deepcopy(self.checkpoints[path])
            return json.loads(path.read_text())

        def save(checkpoint, path):
            Path(path).write_text(json.dumps(checkpoint))

        torch.load, torch.save = load, save
        hashes = ModuleType('scripts.night_train_pilot')
        hashes.tensor_sha256 = lambda state: __import__('hashlib').sha256(
            json.dumps(state, sort_keys=True).encode()).hexdigest()
        models = ModuleType('agents.sherlock.model')
        models.checkpoint_ensemble_dims = lambda checkpoint, dim: [dim]*len(checkpoint['ensemble'])
        modules = {'torch': torch, 'scripts': ModuleType('scripts'),
                   'scripts.night_train_pilot': hashes, 'agents': ModuleType('agents'),
                   'agents.sherlock': ModuleType('agents.sherlock'), 'agents.sherlock.model': models}
        with patch.dict(sys.modules, modules), patch.object(builder, 'SOURCE_SHA', builder.sha(self.source_path)):
            yield

    def accepted_audit(self):
        evidence = {}
        for index in (18, 19):
            path = self.root / f'experiments/runs/20261102_target_adapt{index}/weights/agent.pth'
            path.parent.mkdir(parents=True)
            path.write_bytes(f'synthetic replacement {index}'.encode())
            self.checkpoints[path] = dict(q=dict(weight=[[index*100]], bias=[index]),
                ensemble=[], feature_dim=79, n_actions=6, learn_steps=150)
            evidence[str(path)] = builder.sha(path)
        audit = self.root / 'accepted_audit.json'
        audit.write_text(json.dumps(dict(verdict='ACCEPTED', failed=[], warnings=[],
            arms={name: {} for name in ('control18', 'adapt18', 'control19', 'adapt19')},
            evidence_sha256=evidence)))
        return audit

    def test_p_only_build_needs_no_audit_or_training_inputs_and_preserves_36_nets(self):
        self.assertIn('p_only', inspect.signature(builder.build).parameters, 'explicit P-only builder mode missing')
        out = self.root / 'experiments/ensembles/p_only'
        before = copy.deepcopy(self.source)
        with self.dictionary_runtime(), contextlib.redirect_stdout(io.StringIO()):
            builder.build(self.root, self.source_path, None, out, p_only=True)
        manifest = json.loads((out / 'manifest.json').read_text())
        self.assertEqual(set(manifest['candidates']), {'P'})
        self.assertEqual(manifest['candidates']['P']['nets'], 36)
        self.assertEqual(manifest['candidates']['P']['replaced_indices'], [])
        self.assertEqual(len(manifest['source_component_sha256']), 36)
        self.assertFalse(manifest['training_audit_used'])
        self.assertNotIn('audit_path', manifest)
        self.assertNotIn('audit_sha256', manifest)
        self.assertEqual(self.loaded, [self.source_path, out / 'P.pth'])
        candidate = json.loads((out / 'P.pth').read_text())
        self.assertEqual([candidate['q'], *candidate['ensemble']], self.states)
        self.assertEqual(candidate['cfg'], dict(before['cfg'], point_pair_swap=True, art_move_guard=True))
        self.assertEqual(self.source, before)
        self.assertFalse((out / 'PT.pth').exists())
        self.assertNotIn('torch', sys.modules)

    def test_p_only_and_audit_are_mutually_exclusive_without_loading(self):
        self.assertIn('p_only', inspect.signature(builder.build).parameters, 'explicit P-only builder mode missing')
        with self.assertRaises(ValueError):
            builder.build(self.root, self.source_path, self.root / 'unused_audit.json',
                          self.root / 'experiments/ensembles/invalid', p_only=True)
        self.assertTrue(hasattr(builder, 'main'), 'testable mutually exclusive CLI entry point missing')
        argv = ['builder', '--root', str(self.root), '--source', str(self.source_path),
                '--out', str(self.root / 'out'), '--audit', 'unused.json', '--p-only']
        with patch.object(sys, 'argv', argv), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as stopped:
                builder.main()
        self.assertEqual(stopped.exception.code, 2)
        self.assertNotIn('torch', sys.modules)

    def test_full_mode_still_requires_all_four_accepted_arms(self):
        self.assertIn('p_only', inspect.signature(builder.build).parameters, 'explicit P-only builder mode missing')
        out = self.root / 'experiments/ensembles/full'
        with self.assertRaises(ValueError):
            builder.build(self.root, self.source_path, None, out)
        audit = self.accepted_audit()
        values = json.loads(audit.read_text())
        values['arms'].pop('control19')
        audit.write_text(json.dumps(values))
        with self.dictionary_runtime(), self.assertRaises(AssertionError):
            builder.build(self.root, self.source_path, audit, out)
        self.assertFalse(out.exists())
        self.assertEqual(self.loaded, [])

    def test_full_mode_keeps_both_outputs_and_only_replaces_18_19(self):
        audit = self.accepted_audit()
        out = self.root / 'experiments/ensembles/full'
        with self.dictionary_runtime(), contextlib.redirect_stdout(io.StringIO()):
            builder.build(self.root, self.source_path, audit, out)
        manifest = json.loads((out / 'manifest.json').read_text())
        self.assertEqual(set(manifest['candidates']), {'P', 'PT'})
        self.assertTrue(manifest['training_audit_used'])
        self.assertEqual(manifest['audit_path'], str(audit))
        self.assertEqual(manifest['candidates']['P']['replaced_indices'], [])
        self.assertEqual(manifest['candidates']['PT']['replaced_indices'], [18, 19])
        pt = json.loads((out / 'PT.pth').read_text())
        actual = [pt['q'], *pt['ensemble']]
        self.assertEqual(len(actual), 36)
        self.assertEqual([i for i in range(36) if actual[i] != self.states[i]], [18, 19])

    def test_p_only_cannot_write_into_active_weight_directory(self):
        self.assertIn('p_only', inspect.signature(builder.build).parameters, 'explicit P-only builder mode missing')
        out = self.root / 'agents/sherlock/weights/new_candidate'
        with self.dictionary_runtime(), self.assertRaises(AssertionError):
            builder.build(self.root, self.source_path, None, out, p_only=True)
        self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
