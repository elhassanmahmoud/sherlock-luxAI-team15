"""Standalone synthetic package checks. No Torch, agents, or real checkpoints."""
import copy
from collections import OrderedDict
from dataclasses import dataclass, replace
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

from tests.archive_import_isolation import assert_isolated_imports

HERE = Path(__file__).resolve().parent
MODULE = HERE / 'verify_P_package.py'


@dataclass(frozen=True)
class Tensor:
    shape: tuple
    data: bytes
    dtype: str = 'torch.float32'
    finite: bool = True


class TensorProtocol:
    def is_tensor(self, value):
        return isinstance(value, Tensor)

    def describe(self, value):
        return dict(shape=value.shape, data=value.data, dtype=value.dtype, finite=value.finite,
                    layout='torch.strided', requires_grad=False)


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if MODULE.exists():
            spec = importlib.util.spec_from_file_location('synthetic_package_auditor', MODULE)
            cls.m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.m)

    def setUp(self):
        if not hasattr(self, 'm'):
            if self._testMethodName == 'test_auditor_exists':
                return
            self.skipTest('implementation missing')
        self.tmp = tempfile.TemporaryDirectory(dir=Path('/tmp').resolve())
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        m = self.m
        self.primary, self.frozen = self.base / 'primary', self.base / 'frozen'
        self.original = {}
        config = ('from dataclasses import dataclass\n@dataclass\nclass AgentConfig:\n'
                  '    hidden: int = 256\n    dueling: bool = True\n    use_sap: bool = True\n'
                  '    lr: float = 0.0003\n    frozen: bool = False\n'
                  '    point_pair_swap: bool = False\n    art_move_guard: bool = False\n')
        for name in (*m.RUNTIME, 'build_submission.py'):
            rel = f'agents/sherlock/{name}' if name != 'build_submission.py' else 'scripts/build_submission.py'
            data = config.encode() if name == 'config.py' else f'# synthetic {name}\n'.encode()
            self.original[rel] = data
            for root in (self.primary, self.frozen):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        # Invalid Finder copies are present locally but must never enter the ZIP.
        (self.primary / 'agents/sherlock/config 2.py').write_text('invalid copy')
        self.primary_head = 'e'*40

        def git_reader(root, *args):
            if args == ('rev-parse', '--verify', 'HEAD'):
                return ((m.FROZEN_HEAD if Path(root) == self.frozen else self.primary_head)+'\n').encode()
            if args[0] == 'show':
                rev, rel = args[1].split(':', 1)
                if rev != m.FROZEN_HEAD:
                    raise ValueError('wrong synthetic git revision')
                return self.original[rel]
            raise ValueError(args)

        self.git = git_reader
        self.baseline = self.base / 'V14.pth'; self.baseline.write_bytes(b'synthetic baseline bytes')
        self.raw = self.base / 'P.pth'; self.raw.write_bytes(b'synthetic raw P bytes')
        self.embedded = b'synthetic frozen embedded P bytes'
        shapes = {
            'body.0.weight': (256, 79), 'body.0.bias': (256,),
            'body.2.weight': (256, 256), 'body.2.bias': (256,),
            'value.0.weight': (128, 256), 'value.0.bias': (128,),
            'value.2.weight': (1, 128), 'value.2.bias': (1,),
            'adv.0.weight': (128, 256), 'adv.0.bias': (128,),
            'adv.2.weight': (6, 128), 'adv.2.bias': (6,),
        }
        zero_arrays = {shape: b'\0'*(4*__import__('math').prod(shape)) for shape in shapes.values()}

        def state(index):
            result = {name: Tensor(shape, zero_arrays[shape]) for name, shape in shapes.items()}
            tensor = result['body.0.bias']
            result['body.0.bias'] = replace(tensor, data=struct.pack('<f', float(index))+tensor.data[4:])
            result = OrderedDict(result)
            result._metadata = OrderedDict([('', {'version': 1}), ('body', {'version': 1})])
            return result

        self.cp_base = dict(q=state(0), target_q=state(900), opt={'state': {}, 'param_groups': []},
            cfg=dict(hidden=256, dueling=True, use_sap=True, lr=.0003, frozen=False),
            feature_dim=79, n_actions=6, ensemble=[state(i) for i in range(1, 36)],
            ensemble_dims=[79]*35, ensemble_sources=['synthetic provenance'], env_steps=123, learn_steps=45)
        self.cp_raw = copy.deepcopy(self.cp_base)
        self.cp_raw['cfg'].update(point_pair_swap=True, art_move_guard=True)
        self.cp_embedded = copy.deepcopy(self.cp_raw); self.cp_embedded['cfg']['frozen'] = True
        self.protocol = TensorProtocol()
        self.preflight = self.base / 'preflight.json'
        preflight = dict(status='ACTUAL_P_LOAD_ACCEPTED', source=str(self.baseline), candidate=str(self.raw),
            source_sha256=m.sha(self.baseline), candidate_sha256=m.sha(self.raw), ordered_nets=36,
            feature_dim=79, n_actions=6, ordered_components=[m.state_digest(state, self.protocol)
                for state in [self.cp_raw['q'], *self.cp_raw['ensemble']]],
            actual_config={**self.cp_raw['cfg']})
        self.preflight.write_text(json.dumps(preflight))
        self.complete = self.base / 'confirmation_state.json'
        self.complete.write_text(json.dumps(dict(status='complete', phase='confirmation', completed_games=9000,
            source_before={'source': {'head': m.FROZEN_HEAD}}, source_after={'source': {'head': m.FROZEN_HEAD}},
            jobs=[dict(name=name, status='complete', exit_code=0, actual_games=n)
                  for name, n in [('baseline_panel',4200),('P_panel',4200),('P_direct',600)]])))
        self.archive = self.base / 'Gruppe15.zip'
        self.members = {f'Gruppe15/{name}': self.original[f'agents/sherlock/{name}'] for name in m.RUNTIME}
        self.members.update({'Gruppe15/__init__.py': b'', 'Gruppe15/agent.pth': self.embedded,
            'Gruppe15/agents.yaml': m.expected_yaml(), 'Gruppe15/LIESMICH.txt': m.expected_readme()})
        self.write_zip()
        for name, value in [('V14_SHA', m.sha(self.baseline)), ('P_SHA',m.sha(self.raw)),
                            ('PREFLIGHT_SHA',m.sha(self.preflight))]:
            item = patch.object(m, name, value); item.start(); self.addCleanup(item.stop)

    def write_zip(self, extras=()):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(self.archive, 'w', zipfile.ZIP_DEFLATED) as z:
                for name, data in self.members.items():
                    z.writestr(name, data)
                for name, data in extras:
                    z.writestr(name, data)

    def loader(self, data):
        return {self.baseline.read_bytes(): self.cp_base,
                self.raw.read_bytes(): self.cp_raw, self.embedded: self.cp_embedded}[data]

    def audit(self, **kwargs):
        return self.m.audit(self.primary, self.frozen, self.baseline, self.raw, self.archive,
            self.preflight, self.complete, load_checkpoint=self.loader, tensor_protocol=self.protocol,
            git_reader=self.git, **kwargs)

    def test_auditor_exists(self):
        self.assertTrue(MODULE.is_file())

    def test_complete_valid_package_and_new_primary_head(self):
        receipt = self.audit()
        self.assertEqual(receipt['verdict'], 'SYNTHETIC_P_PACKAGE_STRUCTURE_TENSORS_ACCEPTED')
        self.assertEqual(receipt['zip_sha256'], self.m.sha(self.archive))
        self.assertEqual(receipt['embedded_sha256'], hashlib.sha256(self.embedded).hexdigest())
        self.assertEqual(receipt['ordered_nets'], 36)
        self.assertIs(receipt['raw_frozen_key_present'], True)
        self.assertIs(receipt['raw_frozen_default_from_source'], False)
        self.assertIs(receipt['raw_frozen_uses_source_default'], False)
        self.assertEqual(len(receipt['runtime_source_sha256']), 15)
        self.assertEqual(len(receipt['zip_member_sha256']), 19)
        self.assertEqual(receipt['source_heads']['primary'], 'e'*40)
        self.assertFalse(receipt['claims_course_execution'])
        self.assertFalse(receipt['claims_python310'])
        self.assertFalse(receipt['claims_replay_validation'])
        assert_isolated_imports(self)

    def test_manifest_serialized_cfg_missing_frozen_uses_pinned_false_default(self):
        # Static manifest/config facts only; no checkpoint or unfinished outcomes.
        repo = Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15')
        manifest = json.loads((repo/'experiments/analysis/continuation_20261102/performance/study_P_only_20261102/P_candidate_manifest.json').read_text())
        raw_cfg = manifest['candidates']['P']['configuration']
        self.assertEqual(len(raw_cfg), 74)
        self.assertNotIn('frozen', raw_cfg)
        config = (repo/'agents/sherlock/config.py').read_bytes()
        self.original['agents/sherlock/config.py'] = config
        for root in (self.primary,self.frozen):
            (root/'agents/sherlock/config.py').write_bytes(config)
        self.members['Gruppe15/config.py'] = config
        self.write_zip()
        self.cp_raw['cfg'] = copy.deepcopy(raw_cfg)
        self.cp_base['cfg'] = {k:v for k,v in raw_cfg.items() if k not in ('point_pair_swap','art_move_guard')}
        self.cp_embedded['cfg'] = {**raw_cfg,'frozen':True}
        schema, defaults = self.m.config_schema(config)
        self.assertIs(defaults['frozen'], False)
        preflight = json.loads(self.preflight.read_text())
        preflight['actual_config'] = {**defaults,**raw_cfg}
        self.preflight.write_text(json.dumps(preflight))
        with patch.object(self.m,'PREFLIGHT_SHA',self.m.sha(self.preflight)):
            receipt = self.audit()
        self.assertIs(receipt['raw_frozen'], False)
        self.assertIs(receipt['raw_frozen_key_present'], False)
        self.assertIs(receipt['raw_frozen_default_from_source'], False)
        self.assertIs(receipt['raw_frozen_uses_source_default'], True)
        self.assertNotIn('frozen', self.cp_raw['cfg'])
        self.assertNotIn('frozen', self.cp_base['cfg'])

    def test_missing_raw_frozen_does_not_allow_explicit_none_zero_true_or_missing_embedded(self):
        self.cp_base['cfg'].pop('frozen')
        self.cp_raw['cfg'].pop('frozen')
        for checkpoint in (self.cp_base,self.cp_raw):
            for invalid in (None,0,True):
                checkpoint['cfg']['frozen']=invalid
                with self.subTest(checkpoint=checkpoint is self.cp_raw, invalid=invalid), self.assertRaises(ValueError):
                    self.audit()
                checkpoint['cfg'].pop('frozen')
        self.cp_embedded['cfg'].pop('frozen')
        with self.assertRaises(ValueError):
            self.audit()

    def test_unsafe_extra_missing_duplicate_and_invalid_copy_members_rejected(self):
        for name in ('Gruppe15/config 2.py','Gruppe15/reward 2.py','Gruppe15/CLAUDE.md','../escape',
                     '/Gruppe15/evil.py','Gruppe15/../evil.py','Gruppe15\\evil.py', 'Gruppe15/LICENSE'):
            self.write_zip([(name, b'bad')])
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.audit()
        self.write_zip([('Gruppe15/main.py', self.members['Gruppe15/main.py'])])
        with self.assertRaises(ValueError):
            self.audit()
        self.members.pop('Gruppe15/tactics.py'); self.write_zip()
        with self.assertRaises(ValueError):
            self.audit()

    def test_symlink_member_and_nonempty_init_rejected(self):
        self.members['Gruppe15/__init__.py'] = b'print("bad")'; self.write_zip()
        with self.assertRaises(ValueError):
            self.audit()
        self.members['Gruppe15/__init__.py'] = b''; self.write_zip()
        info = zipfile.ZipInfo('Gruppe15/main.py'); info.create_system=3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.members.pop('Gruppe15/main.py')
        self.write_zip([(info, b'/etc/passwd')])
        with self.assertRaises(ValueError):
            self.audit()

    def test_primary_frozen_and_git_runtime_must_all_match(self):
        for root in (self.primary, self.frozen):
            path = root / 'agents/sherlock/main.py'; original=path.read_bytes(); path.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                self.audit()
            path.write_bytes(original)
        self.members['Gruppe15/main.py']=b'changed'; self.write_zip()
        with self.assertRaises(ValueError):
            self.audit()

    def test_readme_yaml_exact_class_paths_and_36_net_line(self):
        for member in ('Gruppe15/LIESMICH.txt','Gruppe15/agents.yaml'):
            original=self.members[member]
            for bad in (original.replace(b'Gruppe15.main.Agent_x',b'agents.Gruppe15.main.Agent_x'),
                        original.replace(b'Gruppe15/agent.pth',b'Gruppe15/agent_p0.pth'), original+b'\nextra'):
                self.members[member]=bad; self.write_zip()
                with self.assertRaises(ValueError):
                    self.audit()
            self.members[member]=original

    def test_fixed_raw_hashes_rejected_before_loading(self):
        for path in (self.baseline,self.raw):
            original=path.read_bytes(); path.write_bytes(b'wrong model')
            with self.assertRaises(ValueError):
                self.audit()
            path.write_bytes(original)

    def test_raw_v14_only_two_true_flags_and_strict_numeric_types(self):
        original=copy.deepcopy(self.cp_raw)
        for field, value in [('frozen',True),('point_pair_swap',1),('art_move_guard',False),('lr',1),('hidden',True)]:
            self.cp_raw['cfg'][field]=value
            with self.subTest(field=field,value=value), self.assertRaises(ValueError):
                self.audit()
            self.cp_raw=copy.deepcopy(original)
        self.cp_base['cfg']['point_pair_swap']=True
        with self.assertRaises(ValueError):
            self.audit()

    def test_embedded_only_frozen_transition_all_fields_and_targets_exact(self):
        original=copy.deepcopy(self.cp_embedded)
        for field,value in [('env_steps',124),('feature_dim',79.0),('n_actions',True),('opt',{}),('ensemble_dims',[79]*34)]:
            self.cp_embedded[field]=value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.audit()
            self.cp_embedded=copy.deepcopy(original)
        self.cp_embedded['cfg']['frozen']=1
        with self.assertRaises(ValueError): self.audit()
        self.cp_embedded=copy.deepcopy(original)
        target=self.cp_embedded['target_q']['body.0.bias']
        self.cp_embedded['target_q']['body.0.bias']=replace(target,data=b'bad'+target.data[3:])
        with self.assertRaises(ValueError): self.audit()

    def test_order_dtype_shape_missing_and_nonfinite_tensor_changes_rejected(self):
        original=copy.deepcopy(self.cp_embedded)
        for change in ('reorder','dtype','shape','missing','nonfinite','extra'):
            self.cp_embedded=copy.deepcopy(original)
            state=self.cp_embedded['ensemble'][18]
            if change=='reorder': self.cp_embedded['ensemble'][0],self.cp_embedded['ensemble'][1]=self.cp_embedded['ensemble'][1],self.cp_embedded['ensemble'][0]
            if change=='dtype': state['body.0.weight']=replace(state['body.0.weight'],dtype='torch.float16')
            if change=='shape': state['body.0.weight']=replace(state['body.0.weight'],shape=(256,78))
            if change=='missing': state.pop('adv.2.bias')
            if change=='nonfinite': state['body.0.bias']=replace(state['body.0.bias'],finite=False)
            if change=='extra': state['extra']=Tensor((1,),b'\0'*4)
            with self.subTest(change=change), self.assertRaises(ValueError): self.audit()

    def test_ordereddict_metadata_presence_types_and_values_are_compared(self):
        original=copy.deepcopy(self.cp_embedded)
        for change in ('missing','value','type'):
            self.cp_embedded=copy.deepcopy(original)
            if change=='missing': del self.cp_embedded['q']._metadata
            if change=='value': self.cp_embedded['q']._metadata['']['version']=2
            if change=='type': self.cp_embedded['q']._metadata['']['version']=True
            with self.subTest(change=change), self.assertRaises(ValueError): self.audit()

    def test_tensor_signed_zero_and_half_precision_are_not_equal(self):
        original=copy.deepcopy(self.cp_embedded)
        tensor=self.cp_embedded['q']['adv.2.bias']
        self.cp_embedded['q']['adv.2.bias']=replace(tensor,data=struct.pack('<f',-0.)+tensor.data[4:])
        with self.assertRaises(ValueError): self.audit()
        self.cp_embedded=copy.deepcopy(original)
        self.cp_embedded['q']['adv.2.bias']=replace(tensor,dtype='torch.float16',data=b'\0'*12)
        with self.assertRaises(ValueError): self.audit()

    def test_incomplete_confirmation_refused_before_model_loader(self):
        value=json.loads(self.complete.read_text()); value['status']='running'; self.complete.write_text(json.dumps(value))
        with patch.object(self, 'loader', side_effect=AssertionError('must not load model')):
            with self.assertRaises(ValueError): self.audit()
        assert_isolated_imports(self)

    def test_drift_during_load_refused_by_final_evidence_recheck(self):
        original_loader=self.loader
        def drift(data):
            value=original_loader(data)
            (self.primary/'agents/sherlock/main.py').write_bytes(b'drift during audit')
            return value
        with patch.object(self,'loader',side_effect=drift), self.assertRaises(ValueError):
            self.audit()


if __name__=='__main__':
    unittest.main()
