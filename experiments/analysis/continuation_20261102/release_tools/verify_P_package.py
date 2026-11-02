"""Read-only P package structure/tensor audit; not combined release/course QC.

Import/help/synthetic tests use stdlib only. Actual CLI requires --actual and
completed confirmation metadata BEFORE importing Torch. No agents, environment,
forwards, games, updates, extraction, installation, or source writes.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile
import ast

sys.dont_write_bytecode = True
FROZEN_HEAD = '03e54e267242ff642c126313fe5f512ed9d959ac'
V14_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
P_SHA = 'dbb15222848b9ce8530080e128fa9ca66309c9900e98f50de5cce1d73e5b7f5a'
PREFLIGHT_SHA = '587231729fe31dc2655a9cc992b5d494401390b70f2ab82f5c9c37620ff5f66b'
RUNTIME = ('assignment.py','belief.py','cnn_model.py','config.py','features.py','geometry.py',
           'main.py','model.py','opp_model.py','param_est.py','ppo_agent.py','replay_buffer.py',
           'reward.py','rules.py','tactics.py')
CP_KEYS = {'q','target_q','opt','cfg','feature_dim','n_actions','ensemble','ensemble_dims',
           'ensemble_sources','env_steps','learn_steps'}
FLAGS = ('point_pair_swap','art_move_guard')
CLASS_PATH = 'Gruppe15.main.Agent_x'
LOAD_PATH = 'Gruppe15/agent.pth'
CONFIRMATION_REL = 'experiments/analysis/continuation_20261102/performance/study_P_only_20261102/confirmation/state.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def byte_sha(value):
    return hashlib.sha256(value).hexdigest()


def expected_yaml():
    return (f"%YAML 1.2\n---\n\nIMPORT_PATH: '{CLASS_PATH}'\n"
            f"LOAD_PATH_P0: '{LOAD_PATH}'\nLOAD_PATH_P1: '{LOAD_PATH}'\n").encode()


def expected_readme():
    return ("Gruppe 15 - Agent Sherlock\n\n"
            f"Pfad zur Agent-Klasse (act, update):  {CLASS_PATH}\n"
            f"Pfad zum trainierten Agenten:  {LOAD_PATH}   (gleiche Datei fuer Player 0 und Player 1)\n\n"
            f"Zeile fuer Paths.csv:\n15;{CLASS_PATH};{LOAD_PATH};{LOAD_PATH}\n\n"
            "Hinweise:\n"
            "- Den Ordner Gruppe15 nach agents/ oder in die Projektwurzel legen, beides geht.\n"
            "  Findet der Agent den Gewichte-Pfad vom Arbeitsverzeichnis aus nicht, laedt er die\n"
            "  gleichnamige .pth-Datei direkt neben main.py.\n"
            "- Fuer das Battle am besten mit train=False spielen (nur dann schreibt der Runner Replays).\n"
            "  Die Battle-Version ist eingefroren: Auch mit train=True spielt Sherlock in voller Staerke,\n"
            "  lernt nicht weiter und ueberschreibt seine .pth-Datei nicht.\n"
            "- Benoetigt nur die Kurs-Pakete (torch, numpy); CPU reicht.\n"
            "- Beim Start erscheint: [Sherlock Agent_X] geladen: ... Ensemble=36 Netze\n").encode()


def complete_confirmation(path):
    """Metadata fence only: never read CSVs, scores or performance gates."""
    value = json.loads(Path(path).read_text())
    require(value.get('status') == 'complete' and value.get('phase') == 'confirmation'
            and type(value.get('completed_games')) is int and value['completed_games'] == 9000,
            'Actual model inspection requires the complete original 9000-game confirmation')
    jobs = value.get('jobs')
    require(type(jobs) is list and len(jobs) == 3, 'Incomplete confirmation jobs')
    for record, (name, games) in zip(jobs, [('baseline_panel',4200),('P_panel',4200),('P_direct',600)]):
        require(record.get('name') == name and record.get('status') == 'complete'
                and type(record.get('exit_code')) is int and record['exit_code'] == 0
                and type(record.get('actual_games')) is int and record['actual_games'] == games,
                'Confirmation job metadata incomplete')
    require(value.get('source_before') == value.get('source_after')
            and value['source_before']['source']['head'] == FROZEN_HEAD,
            'Confirmation source identity is not the original unchanged 03e identity')
    return value


def git_read(root, *args):
    return subprocess.check_output(['git','-C',str(root),*args], stderr=subprocess.PIPE)


def source_proof(primary, frozen, git_reader, pin):
    heads = {}
    for name, root in [('primary',primary),('frozen',frozen)]:
        head = git_reader(root,'rev-parse','--verify','HEAD').decode().strip()
        require(re.fullmatch('[0-9a-f]{40}',head), 'Invalid source HEAD')
        heads[name] = head
    require(heads['frozen'] == FROZEN_HEAD, 'Frozen evaluation checkout must retain original 03e HEAD')
    runtime, blobs = {}, {}
    for rel in [*(f'agents/sherlock/{name}' for name in RUNTIME), 'scripts/build_submission.py']:
        current_path, frozen_path = primary/rel, frozen/rel
        for path in (current_path,frozen_path):
            require(path.is_file() and not path.is_symlink(), f'Missing/aliased runtime source {path}')
            pin(path)
        historical = git_reader(frozen,'show',f'{FROZEN_HEAD}:{rel}')
        require(current_path.read_bytes() == frozen_path.read_bytes() == historical,
                f'Runtime/builder bytes differ from frozen 03e: {rel}')
        blobs[rel] = byte_sha(historical)
        if rel.startswith('agents/sherlock/'):
            runtime[Path(rel).name] = byte_sha(historical)
    return dict(heads=heads, runtime=runtime, blobs=blobs)


def config_schema(data):
    """Read primitive dataclass annotations/defaults without executing config.py."""
    tree = ast.parse(data.decode('utf-8'))
    classes = [n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='AgentConfig']
    require(len(classes)==1, 'Missing unique AgentConfig declaration')
    schema, defaults = {}, {}
    types = {'bool':bool,'int':int,'float':float,'str':str}
    for node in classes[0].body:
        if isinstance(node,ast.AnnAssign):
            require(isinstance(node.target,ast.Name) and isinstance(node.annotation,ast.Name)
                    and node.annotation.id in types and node.value is not None, 'Unsupported config schema')
            name = node.target.id
            require(name not in schema, 'Duplicate config field')
            expected = types[node.annotation.id]
            default = ast.literal_eval(node.value)
            require(type(default) is expected and (type(default) is not float or math.isfinite(default)),
                    f'Invalid config default type: {name}')
            schema[name], defaults[name] = expected, default
    require(schema and all(schema.get(name) is bool and defaults.get(name) is False
                           for name in (*FLAGS,'frozen')), 'Missing strict false-default P/frozen config flags')
    return schema, defaults


def tensor_description(value, protocol):
    require(protocol.is_tensor(value), 'Expected tensor')
    d = protocol.describe(value)
    require(set(d) == {'dtype','shape','data','finite','layout','requires_grad'}, 'Invalid tensor protocol')
    require(type(d['dtype']) is str and type(d['shape']) is tuple and all(type(n) is int and n>=0 for n in d['shape'])
            and type(d['data']) is bytes and d['finite'] is True and d['layout']=='torch.strided'
            and type(d['requires_grad']) is bool, 'Nonfinite/unsupported tensor description')
    return d


def strict_equal(left, right, protocol, name='checkpoint'):
    if protocol.is_tensor(left) or protocol.is_tensor(right):
        a,b = tensor_description(left,protocol), tensor_description(right,protocol)
        require(a==b, f'Tensor dtype/shape/bytes/metadata changed: {name}')
        return
    require(type(left) is type(right), f'Value type changed: {name}')
    if isinstance(left,(dict,OrderedDict)):
        require(set(left)==set(right), f'Dictionary keys changed: {name}')
        for key in left:
            require(type(key) in (str,int) and type(key) is not bool, f'Unsupported checkpoint key: {name}')
            strict_equal(left[key],right[key],protocol,f'{name}[{key!r}]')
        a,b = getattr(left,'__dict__',{}),getattr(right,'__dict__',{})
        require(set(a)==set(b) and set(a).issubset({'_metadata'}), f'Unsupported/changed mapping metadata: {name}')
        for key in a:
            strict_equal(a[key],b[key],protocol,f'{name}.{key}')
    elif type(left) in (list,tuple):
        require(len(left)==len(right), f'Sequence length changed: {name}')
        for i,(a,b) in enumerate(zip(left,right)):
            strict_equal(a,b,protocol,f'{name}[{i}]')
    elif type(left) in (type(None),bool,int,str,bytes):
        require(left==right, f'Value changed: {name}')
    elif type(left) is float:
        require(math.isfinite(left) and math.isfinite(right) and struct_float_bytes(left)==struct_float_bytes(right),
                f'Nonfinite/changed float: {name}')
    else:
        raise ValueError(f'Unsupported checkpoint value type: {name}: {type(left).__name__}')


def struct_float_bytes(value):
    import struct
    return struct.pack('!d',value)


def state_digest(state, protocol):
    h = hashlib.sha256()
    require(isinstance(state,dict) and state and all(type(k) is str for k in state), 'Invalid tensor state')
    for key in sorted(state):
        d = tensor_description(state[key],protocol)
        header = json.dumps([key,d['dtype'],list(d['shape'])],separators=(',',':'))
        h.update(header.encode()+b'\n'); h.update(d['data'])
    return h.hexdigest()


def expected_shapes():
    return {'body.0.weight':(256,79),'body.0.bias':(256,),
            'body.2.weight':(256,256),'body.2.bias':(256,),
            'value.0.weight':(128,256),'value.0.bias':(128,),
            'value.2.weight':(1,128),'value.2.bias':(1,),
            'adv.0.weight':(128,256),'adv.0.bias':(128,),
            'adv.2.weight':(6,128),'adv.2.bias':(6,)}


def checkpoint_schema(cp, schema, protocol, *, frozen, defaults):
    require(type(cp) is dict and set(cp)==CP_KEYS, 'Checkpoint keyset differs from pinned V14/P format')
    require(type(cp['feature_dim']) is int and cp['feature_dim']==79
            and type(cp['n_actions']) is int and cp['n_actions']==6, 'Expected 79 features and six actions')
    require(type(cp['ensemble']) is list and len(cp['ensemble'])==35
            and type(cp['ensemble_dims']) is list and len(cp['ensemble_dims'])==35
            and all(type(n) is int and n==79 for n in cp['ensemble_dims']), 'Expected 36 ordered 79-feature nets')
    require(type(cp['cfg']) is dict and set(cp['cfg']).issubset(schema), 'Unknown/missing config mapping')
    for name,value in cp['cfg'].items():
        require(type(value) is schema[name] and (type(value) is not float or math.isfinite(value)),
                f'Config type/nonfinite value: {name}')
    require(schema.get('frozen') is bool and defaults.get('frozen') is False,
            'Frozen default must come from the pinned source schema')
    effective_frozen = cp['cfg'].get('frozen',defaults['frozen'])
    require(effective_frozen is frozen and (not frozen or cp['cfg'].get('frozen') is True)
            and cp['cfg'].get('hidden')==256
            and cp['cfg'].get('dueling') is True and cp['cfg'].get('use_sap') is True,
            'Unexpected frozen/architecture configuration')
    for name in ('env_steps','learn_steps'):
        require(type(cp[name]) is int and cp[name]>=0, f'Invalid checkpoint counter {name}')
    require(type(cp['ensemble_sources']) is list and all(type(v) is str for v in cp['ensemble_sources']),
            'Invalid ensemble provenance')
    for i,state in enumerate([cp['q'],*cp['ensemble'],cp['target_q']]):
        require(isinstance(state,dict) and set(state)==set(expected_shapes()), f'Incorrect tensor state keys: {i}')
        for key,shape in expected_shapes().items():
            d=tensor_description(state[key],protocol)
            require(d['shape']==shape and d['dtype']=='torch.float32' and len(d['data'])==4*math.prod(shape),
                    f'Incorrect float32 architecture/bytes in state {i}: {key}')
    strict_equal(cp,cp,protocol)  # Validate optimizer and every other nested field too.


def package_members(path):
    expected = {*(f'Gruppe15/{name}' for name in RUNTIME), 'Gruppe15/__init__.py',LOAD_PATH,
                'Gruppe15/agents.yaml','Gruppe15/LIESMICH.txt'}
    require(Path(path).name=='Gruppe15.zip' and Path(path).stat().st_size<=128*1024*1024, 'Invalid staged ZIP name/size')
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        require(len(names)==len(set(names))==19 and set(names)==expected, 'ZIP duplicate/missing/extra members')
        require(not archive.comment, 'Unexpected archive comment')
        require(sum(info.file_size for info in infos)<=80*1024*1024, 'ZIP expands beyond fixed package budget')
        result = {}
        for info in infos:
            name = info.filename
            require(info.orig_filename==name and '\\' not in name and not name.startswith('/')
                    and all(part not in ('','.','..') for part in name.split('/'))
                    and PurePosixPath(name).as_posix()==name and not info.is_dir(), 'Unsafe ZIP path')
            mode = (info.external_attr>>16)&0xffff
            require(stat.S_IFMT(mode) in (0,stat.S_IFREG) and not info.flag_bits&1
                    and info.compress_type in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED), 'Unsafe ZIP type/encryption/compression')
            limit = 64*1024*1024 if name==LOAD_PATH else 2*1024*1024
            require(0<=info.file_size<=limit, 'Oversized ZIP member')
            result[name]=archive.read(info)
        require(result['Gruppe15/__init__.py']==b'' and result['Gruppe15/agents.yaml']==expected_yaml()
                and result['Gruppe15/LIESMICH.txt']==expected_readme(), 'Init/YAML/README differs from fixed battle paths/format')
    return result


def audit(primary, frozen, baseline, raw_p, package, preflight, confirmation_state, *,
          load_checkpoint, tensor_protocol, git_reader=git_read, actual=False):
    require(type(actual) is bool, 'Invalid execution mode')
    primary,frozen,baseline,raw_p,package,preflight,confirmation_state = (
        Path(p).resolve(strict=True) for p in (primary,frozen,baseline,raw_p,package,preflight,confirmation_state))
    complete_confirmation(confirmation_state)  # Before ANY checkpoint loader call.
    evidence = {}
    def pin(path):
        path=Path(path).resolve(strict=True)
        evidence[str(path)]=sha(path)
    for path in (Path(__file__),baseline,raw_p,package,preflight,confirmation_state): pin(path)
    require(evidence[str(baseline)]==V14_SHA and evidence[str(raw_p)]==P_SHA
            and evidence[str(preflight)]==PREFLIGHT_SHA, 'Wrong fixed baseline/raw P/preflight SHA')
    source = source_proof(primary,frozen,git_reader,pin)
    schema,defaults = config_schema((frozen/'agents/sherlock/config.py').read_bytes())
    members=package_members(package)
    for name in RUNTIME:
        require(byte_sha(members[f'Gruppe15/{name}'])==source['runtime'][name], f'Packaged runtime source differs: {name}')
    proof=json.loads(preflight.read_text())
    require(proof.get('status')=='ACTUAL_P_LOAD_ACCEPTED' and proof.get('source_sha256')==V14_SHA
            and proof.get('candidate_sha256')==P_SHA and proof.get('ordered_nets')==36
            and type(proof.get('ordered_nets')) is int and proof.get('feature_dim')==79
            and type(proof.get('feature_dim')) is int and proof.get('n_actions')==6
            and type(proof.get('n_actions')) is int and Path(proof['source']).resolve(strict=True)==baseline
            and Path(proof['candidate']).resolve(strict=True)==raw_p, 'Unbound original actual-load preflight')
    original,raw,embedded = (load_checkpoint(data) for data in (baseline.read_bytes(),raw_p.read_bytes(),members[LOAD_PATH]))
    for cp,mode in [(original,False),(raw,False),(embedded,True)]: checkpoint_schema(cp,schema,tensor_protocol,frozen=mode,defaults=defaults)
    require(all(original['cfg'].get(flag,False) is False and raw['cfg'].get(flag) is True for flag in FLAGS),
            'Raw P flags must change missing/False to literal True')
    expected_raw=dict(original); expected_raw['cfg']={**original['cfg'],**{flag:True for flag in FLAGS}}
    strict_equal(expected_raw,raw,tensor_protocol,'V14-to-raw-P')
    expected_embedded=dict(raw); expected_embedded['cfg']={**raw['cfg'],'frozen':True}
    strict_equal(expected_embedded,embedded,tensor_protocol,'raw-P-to-ZIP')
    ordered=[state_digest(state,tensor_protocol) for state in [raw['q'],*raw['ensemble']]]
    require(type(proof.get('ordered_components')) is list and len(proof['ordered_components'])==36
            and ordered==proof['ordered_components'], 'Ordered components differ from original actual-load proof')
    strict_equal({**defaults,**raw['cfg']},proof['actual_config'],tensor_protocol,'preflight effective configuration')
    # Close read/load races: every source, package, checkpoint, evidence file and HEAD must still match.
    require(all(sha(path)==value for path,value in evidence.items()), 'Input/source evidence changed during package audit')
    heads_after={name:git_reader(root,'rev-parse','--verify','HEAD').decode().strip()
                 for name,root in [('primary',primary),('frozen',frozen)]}
    require(heads_after==source['heads'], 'Source HEAD changed during package audit')
    return dict(verdict=('ACCEPTED_P_PACKAGE_STRUCTURE_TENSORS' if actual else 'SYNTHETIC_P_PACKAGE_STRUCTURE_TENSORS_ACCEPTED'),
        scope='Standalone read-only ZIP/source/checkpoint structure and exact tensor/field equality; no combined release QC',
        created_utc=datetime.now(timezone.utc).isoformat(), actual=actual, failed=[],
        feature_dim=79,n_actions=6,components=36,ordered_nets=36,ordered_component_sha256=ordered,
        raw_flags={name:True for name in FLAGS},raw_frozen=False,embedded_frozen=True,
        raw_frozen_key_present='frozen' in raw['cfg'],raw_frozen_default_from_source=defaults['frozen'],
        raw_frozen_uses_source_default='frozen' not in raw['cfg'],
        raw_config_changes=list(FLAGS),embedded_config_changes=['frozen'],
        all_checkpoint_fields_exact=True,all_tensor_dtype_shape_bytes_exact=True,
        zip_path=str(package),zip_sha256=evidence[str(package)],embedded_sha256=byte_sha(members[LOAD_PATH]),
        raw_path=str(raw_p),raw_sha256=P_SHA,baseline_path=str(baseline),baseline_sha256=V14_SHA,
        import_path=CLASS_PATH,load_path_p0=LOAD_PATH,load_path_p1=LOAD_PATH,
        source_heads=source['heads'],source_heads_after=heads_after,
        runtime_source_sha256=source['runtime'],frozen_git_blob_sha256=source['blobs'],
        zip_member_sha256={name:byte_sha(data) for name,data in sorted(members.items())},evidence_sha256=evidence,
        claims_course_execution=False,claims_python310=False,claims_replay_validation=False,
        limits=['No Agent construction, model forward, environment, games, updates or replay inspection.',
                'No performance qualification or installation/release authorization; Root joins separate actual proofs.'])


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('primary-root','frozen-root','baseline','raw-p','zip','preflight','complete-confirmation-state','out'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--actual',action='store_true',required=True)
    args=parser.parse_args(argv)
    out=args.out.absolute()
    require(not out.exists() and not out.is_symlink() and out.parent.is_dir(), 'Use a new receipt path in an existing directory')
    require(args.complete_confirmation_state.resolve(strict=True)==args.frozen_root.resolve(strict=True)/CONFIRMATION_REL,
            'Use the original canonical P confirmation state')
    complete_confirmation(args.complete_confirmation_state)
    # The only Torch import in this file. No models/Agent imports or construction.
    import torch
    class TorchProtocol:
        def is_tensor(self,value): return isinstance(value,torch.Tensor)
        def describe(self,value):
            t=value.detach().cpu().contiguous()
            return dict(dtype=str(t.dtype),shape=tuple(t.shape),data=t.reshape(-1).view(torch.uint8).numpy().tobytes(),
                        finite=bool(torch.isfinite(t).all().item()),layout=str(t.layout),requires_grad=bool(value.requires_grad))
    def load(data): return torch.load(io.BytesIO(data),map_location='cpu',weights_only=True)
    result=audit(args.primary_root,args.frozen_root,args.baseline,args.raw_p,args.zip,args.preflight,
                 args.complete_confirmation_state,load_checkpoint=load,tensor_protocol=TorchProtocol(),actual=True)
    with out.open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False); stream.write('\n')
    print(json.dumps({key:result[key] for key in ('verdict','zip_sha256','embedded_sha256','components')},indent=2))
    return result


if __name__=='__main__':
    main()
