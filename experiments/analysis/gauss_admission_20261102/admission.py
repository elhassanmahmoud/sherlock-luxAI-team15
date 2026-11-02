"""Frozen technical admission, never a strength evaluation or promotion.

prepare --out NEW --reference ROOT --prototype ROOT --weights V14 --known-c CSV
run-stage --out OUT --stage C   (then S only after successful C)
audit --out OUT

The parent is stdlib-only. Exactly four fresh, sequential, isolated model children:
C reference4/prototype4; S reference80/prototype80. Raw traces are authoritative.
"""
from __future__ import annotations

import argparse
import copy
import csv
import gzip
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

V14 = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
REFERENCE = '384dad2b5a077f5ab026f63c5c8a2d944bc51776'
RUNTIME = '3a7e7825b614a30bc85c7895a38e6b9fc62efdd5'
PROTOTYPE = '307b1ed2051cb9b1a339f849f4322630f5dca7b9'
PYTHON = Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python')
PLAN = 'docs/superpowers/plans/2026-11-02-gauss-admission.md'
RESULT_FIELDS = ('seed', 'side', 'steps', 'our_wins', 'opp_wins', 'result',
                 'our_points', 'opp_points', 'point_counting_version')
ROLES = ('reference', 'prototype')
RUNTIME_PATHS = ('agents', 'lux', 'scripts')
BITSET = dict(bits=576, index='x*24+y', bitorder='little', encoding='hex')


def stage_keys(stage):
    if stage == 'C':
        return [(831006, 'player_1'), (831029, 'player_0'),
                (831042, 'player_0'), (831043, 'player_1')]
    if stage == 'S':
        return [(seed, side) for seed in range(840000, 840040)
                for side in ('player_0', 'player_1')]
    raise ValueError('unknown stage')


def pack_tiles(tiles):
    bits = bytearray(72)
    for tile in tiles:
        if not 0 <= int(tile) < 576 or int(tile) != tile:
            raise ValueError('tile outside 24x24')
        bits[int(tile) // 8] |= 1 << (int(tile) % 8)
    return bits.hex()


def unpack_tiles(value):
    data = bytes.fromhex(value)
    if len(data) != 72:
        raise ValueError('bitset must contain exactly 576 bits')
    return {i for i in range(576) if data[i // 8] & (1 << (i % 8))}


def frame_metrics(pre, post, truth):
    known_pre = pre['V']['point'] | pre['V']['dead']
    known_post = set().union(*(post[k][kind] for k in ('V', 'A') for kind in ('point', 'dead')))
    extra, strict = {}, {}
    for kind in ('point', 'dead'):
        extra[kind] = sorted((post['G'][kind] - pre['G'][kind]) - known_pre)
        strict[kind] = sorted(set(extra[kind]) - known_post)
    differences = {f'{a}-{b}': {k: sorted(post[a][k] - post[b][k]) for k in ('point', 'dead')}
                   for a, b in (('A', 'V'), ('V', 'A'), ('G', 'V'), ('V', 'G'), ('G', 'A'), ('A', 'G'))}
    conflicts = {f'{a}_point_{b}_dead': sorted(post[a]['point'] & post[b]['dead'])
                 for a in 'VAG' for b in 'VAG'}
    false_extra = {a: {'point': sorted((post[a]['point'] - post['V']['point']) - truth),
                       'dead': sorted((post[a]['dead'] - post['V']['dead']) & truth)} for a in 'AG'}
    return dict(extra_current=extra, strict=strict, differences=differences,
                conflicts=conflicts, false_extra=false_extra,
                false_v=dict(point=sorted(post['V']['point'] - truth), dead=sorted(post['V']['dead'] & truth)))


def canonical_truth(state, mirrored, truth_fn):
    import numpy as np
    points, _ = truth_fn(state)
    points = np.asarray(points, dtype=bool)
    if points.shape != (24, 24):
        raise ValueError('truth shape')
    if mirrored:
        points = points[::-1, ::-1].T
    return set(map(int, np.flatnonzero(points.reshape(-1))))


def native_action(action):
    # No cast, remirroring, extra action call, forward or random draw.
    return dict(shape=list(action.shape), dtype=action.dtype.str, order='C', hex=action.tobytes(order='C').hex())


class NativeAct:
    def __init__(self, agent):
        if getattr(agent, '_admission_native', False):
            raise ValueError('native action already wrapped')
        agent._admission_native = True
        original = agent.act
        self.last = None
        self.times = None

        def act(*args, **kwargs):
            wall, cpu = time.perf_counter_ns(), time.process_time_ns()
            result = original(*args, **kwargs)
            self.times = dict(cpu_ns=time.process_time_ns() - cpu, wall_ns=time.perf_counter_ns() - wall)
            self.last = native_action(result)
            return result
        agent.act = act


def timed(call, *args):
    wall, cpu = time.perf_counter_ns(), time.process_time_ns()
    result = call(*args)
    return result, dict(cpu_ns=time.process_time_ns() - cpu, wall_ns=time.perf_counter_ns() - wall)


def facts(belief):
    return dict(point=set(belief._point), dead=set(belief._dead))


def attempts(belief):
    return [int(getattr(belief, k, default)) for k, default in
            (('_gauss_attempts', 0), ('_gauss_observations', 0), ('_gauss_last_observation', -8))]


class ShadowTrace:
    """V observe once; independent A/G public histories; no truth access here."""
    def __init__(self, agent, shadows):
        self.agent, self.shadows = agent, shadows
        self.original_new_game = agent.new_game
        self.original_observe = agent.belief.observe
        self.pending = None
        self.beliefs = {}

        def new_game(side):
            b = agent.belief
            # Restore before reset/deepcopy: never copy a closure/bound V method.
            b.__dict__.pop('observe', None)
            _, reset_time = timed(self.original_new_game, side)
            self.beliefs = {'V': b}
            self.pending = None
            if shadows:
                clones, clone_time = timed(lambda: dict(A=copy.deepcopy(b), G=copy.deepcopy(b)))
                self.beliefs.update(clones)
                self.beliefs['A'].overlap_infer, self.beliefs['A'].gauss_infer = True, False
                self.beliefs['G'].overlap_infer, self.beliefs['G'].gauss_infer = False, True
            else:
                clone_time = dict(cpu_ns=0, wall_ns=0)
            self.setup_times = dict(reset=reset_time, clones=clone_time)
            b.observe = observe

        def observe(obs):
            b = agent.belief
            step = int(obs['steps'])
            if step == b._last_step:
                self.original_observe(obs)
                return
            if self.pending is not None:
                raise ValueError('unflushed observation before next frame')
            pre = {k: facts(v) for k, v in self.beliefs.items()}
            before = {k: attempts(v) for k, v in self.beliefs.items()}
            copies, copy_time = timed(lambda: {k: copy.deepcopy(obs) for k in self.beliefs if k != 'V'})
            times = {'copies': copy_time}
            _, times['V'] = timed(self.original_observe, obs)
            for k in ('A', 'G') if shadows else ():
                shadow = self.beliefs[k]
                shadow.sensor_range = b.sensor_range
                _, times[k] = timed(shadow.observe, copies[k])
            self.pending = dict(step=step, match=int(b.match_idx), match_step=int(obs['match_steps']),
                                reset=int(obs['match_steps']) == 0, pre=pre,
                                post={k: facts(v) for k, v in self.beliefs.items()},
                                attempts={k: dict(pre=before[k], post=attempts(v)) for k, v in self.beliefs.items()},
                                times=times)
        agent.new_game = new_game

    def finish(self, truth, actions):
        if self.pending is None:
            raise ValueError('act did not produce one fresh observation')
        frame, self.pending = self.pending, None
        frame['truth'] = pack_tiles(truth)
        frame['action'] = {k: native_action(v) for k, v in actions.items()}
        for phase in ('pre', 'post'):
            frame[phase] = {k: {kind: pack_tiles(v) for kind, v in f.items()} for k, f in frame[phase].items()}
        return frame


def quantiles(values):
    ordered = sorted(values)
    if not ordered:
        return dict(n=0, median=None, p95=None, max=None)
    def at(q):
        pos = (len(ordered) - 1) * q
        lo = int(pos)
        return ordered[lo] + (ordered[min(lo + 1, len(ordered) - 1)] - ordered[lo]) * (pos - lo)
    return dict(n=len(values), median=at(.5), p95=at(.95), max=ordered[-1])


def reconstruct(frames, seed, side):
    """Derive novelty, truth, first-knowledge leads, fact-steps and costs from raw."""
    strict, leads, first = set(), [], {}
    totals = dict(strict_facts=[], extra_current={'point': 0, 'dead': 0},
                  false_extra={'A': 0, 'G': 0}, false_v=0, conflicts=0,
                  fact_steps={}, attempts=[], lead=leads, positive_carryovers=0)
    timing = {}
    previous_match = previous_truth = None
    last_attempt = None

    def censor(lead, reason):
        if lead['key'][-1] == 'dead':
            for role in 'VA':
                if lead[role] is None and lead['censored'][role] is None:
                    lead['censored'][role] = reason

    for frame in frames:
        pre, post = ({k: {kind: unpack_tiles(value) for kind, value in f.items()}
                      for k, f in frame[phase].items()} for phase in ('pre', 'post'))
        truth = unpack_tiles(frame['truth'])
        match, step = frame['match'], frame['step']
        for role in post:
            before, after = (frame['attempts'][role][p] for p in ('pre', 'post'))
            if frame['reset']:
                if role == 'G' and after != [0, 0, -8]:
                    raise ValueError('Gauss counters failed match reset')
            elif role == 'G' and after[1] != before[1] + 1:
                raise ValueError('Gauss observation counter gap')
        if previous_truth is not None and truth != previous_truth:
            first = {k: v for k, v in first.items() if k[2] == 'point'}
            for lead in leads:
                censor(lead, 'truth_regime_change')
        previous_truth = truth
        if previous_match != match:
            # Zero knowledge is scoped to the actual acquisition match; point knowledge persists.
            first = {k: v for k, v in first.items() if k[2] == 'point'}
            last_attempt = None
        for role, f in post.items():
            for kind, tiles in f.items():
                for tile in tiles:
                    first.setdefault((role, tile, kind), step)
        if frame['reset']:
            if previous_match is not None and 'G' in post:
                totals['positive_carryovers'] += len(post['G']['point'] - post['V']['point'])
            previous_match = match
            for lead in leads:
                censor(lead, 'match_reset')
            continue
        previous_match = match
        for role in post:
            for clock in ('cpu_ns', 'wall_ns'):
                timing.setdefault(f'{role}_{clock}', []).append(frame['times'][role][clock])
        if 'G' not in post:
            continue
        timing.setdefault('G_minus_V_cpu_ns', []).append(frame['times']['G']['cpu_ns'] - frame['times']['V']['cpu_ns'])
        m = frame_metrics(pre, post, truth)
        for role in 'AG':
            totals['false_extra'][role] += sum(map(len, m['false_extra'][role].values()))
        totals['false_v'] += sum(map(len, m['false_v'].values()))
        totals['conflicts'] += sum(map(len, m['conflicts'].values()))
        for direction, facts_by_kind in m['differences'].items():
            for kind, tiles in facts_by_kind.items():
                key = f'{direction}_{kind}'
                totals['fact_steps'][key] = totals['fact_steps'].get(key, 0) + len(tiles)
        for kind in ('point', 'dead'):
            totals['extra_current'][kind] += len(m['extra_current'][kind])
            for tile in m['strict'][kind]:
                key = (seed, side, match, tile, kind)
                if key not in strict:
                    strict.add(key)
                    leads.append(dict(key=list(key), step=step, V=None, A=None,
                                      censored={'V': None, 'A': None}))
        for lead in leads:
            _, _, acquisition_match, tile, kind = lead['key']
            if kind == 'dead' and acquisition_match != match:
                continue
            for role in 'VA':
                known = first.get((role, tile, kind))
                if (lead[role] is None and lead['censored'][role] is None
                        and known is not None and known >= lead['step']):
                    lead[role] = known - lead['step']
            if kind == 'dead' and tile not in post['G']['dead']:
                censor(lead, 'knowledge_lost')
        before, after = (frame['attempts']['G'][p] for p in ('pre', 'post'))
        delta = after[0] - before[0]
        if delta < 0 or delta > 1 or after[0] > 8:
            raise ValueError('invalid Gauss attempt count')
        if delta:
            if after[1] != after[2] or after[2] - before[2] < 8 or (last_attempt is not None and after[2] - last_attempt < 8):
                raise ValueError('invalid Gauss attempt spacing')
            last_attempt = after[2]
            totals['attempts'].append(dict(match=match, step=step, observation=after[2]))
    totals['strict_facts'] = [list(k) for k in sorted(strict)]
    totals['timing'] = {k: quantiles(v) for k, v in timing.items()}
    totals['measurement_limits'] = 'Fixed V/A/G order; process CPU includes scheduling effects; shadow observe is not active-agent latency.'
    return totals


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def file_identity(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), sha256=digest(path))


def check_identity(identity):
    if file_identity(identity['path']) != identity:
        raise ValueError(f"source/input changed: {identity['path']}")


def check_weights(path):
    identity = file_identity(path)
    if identity['sha256'] != V14:
        raise ValueError('weights are not frozen V14')
    return identity


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def source_identity(root, role):
    root = Path(root).resolve(strict=True)
    head = git(root, 'rev-parse', 'HEAD')
    if role == 'reference' and head != REFERENCE:
        raise ValueError('reference actual HEAD must be 384dad2')
    if role == 'prototype':
        subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', PROTOTYPE, head], check=True)
    # Historical untracked duplicate files are not runtime. An actual import of
    # any untracked helper is nevertheless rejected by check_imports.
    tracked_paths = git(root, 'ls-files', '--', *RUNTIME_PATHS).splitlines()
    runtime_paths = [root / p for p in tracked_paths if p.endswith('.py')]
    files = {}
    for path in sorted(runtime_paths):
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        tracked = subprocess.check_output(['git', '-C', str(root), 'show', f'HEAD:{relative}'])
        if data != tracked:
            raise ValueError(f'uncommitted runtime source: {path}')
        basis = RUNTIME if role == 'reference' else PROTOTYPE
        baseline = subprocess.check_output(['git', '-C', str(root), 'show', f'{basis}:{relative}'])
        if data != baseline:
            raise ValueError(f'{role} runtime differs from fixed basis {basis}: {path}')
        files[relative] = hashlib.sha256(data).hexdigest()
    if not files or 'scripts/common.py' not in files:
        raise ValueError('invalid source root')
    return dict(root=str(root), head=head, runtime_base=RUNTIME if role == 'reference' else PROTOTYPE, files=files)


def check_source(identity):
    root = Path(identity['root'])
    if git(root, 'rev-parse', 'HEAD') != identity['head']:
        raise ValueError(f'source HEAD changed: {root}')
    paths = {p for p in git(root, 'ls-files', '--', *RUNTIME_PATHS).splitlines() if p.endswith('.py')}
    if paths != set(identity['files']) or any(digest(root / p) != h for p, h in identity['files'].items()):
        raise ValueError(f'runtime source changed: {root}')


def environment_identity():
    # Locate distribution files without importing torch, agents, JAX or the engine.
    engine = importlib.metadata.distribution('luxai-s3')
    engine_files = {str(Path(engine.locate_file(p)).resolve()): digest(engine.locate_file(p))
                    for p in engine.files if str(p).endswith('.py') and str(p).startswith('luxai_s3/')}
    if not engine_files:
        raise ValueError('cannot pin actual engine sources')
    return dict(interpreter=file_identity(sys.executable), version=sys.version,
                platform=platform.platform(), packages={p: importlib.metadata.version(p)
                for p in ('luxai-s3', 'numpy', 'torch', 'jax', 'jaxlib')}, engine=engine_files)


def select_agent_package(root):
    """Bind selected-root imports without the initializer's recursive discovery.

    Discovery also imports historical untracked duplicates in the primary tree.
    Neither source executes that initializer; Sherlock/Solution imports execute
    their normal files, each still checked against the full tracked inventory.
    """
    if any(name == 'agents' or name.startswith('agents.') for name in sys.modules):
        raise ValueError('agent package already imported before source selection')
    package = Path(root).resolve() / 'agents'
    spec = importlib.util.spec_from_file_location('agents', package / '__init__.py',
                                                submodule_search_locations=[str(package)])
    sys.modules['agents'] = importlib.util.module_from_spec(spec)
    return dict(package='agents', path=str(package), initializer_executed=False,
                reason='skip recursive autodiscovery; import selected modules directly')


def check_imports(root, identity):
    root = Path(root).resolve()
    imported = {}
    for name, module in list(sys.modules.items()):
        if name == 'agents' or name.startswith('agents.'):
            paths = getattr(module, '__path__', None)
            expected = root.joinpath(*name.split('.'))
            if paths is not None and [Path(p).resolve() for p in paths] != [expected]:
                raise ValueError(f'cross-root package path: {name}: {paths}')
        path = getattr(module, '__file__', None)
        if not path or not name.startswith(('agents', 'scripts', 'lux.', 'luxai_s3')):
            continue
        p = Path(path).resolve()
        if name.startswith('luxai_s3'):
            if str(p) not in identity['environment']['engine'] or digest(p) != identity['environment']['engine'][str(p)]:
                raise ValueError(f'unpinned engine import: {name}: {p}')
        else:
            if not p.is_relative_to(root):
                raise ValueError(f'cross-root import: {name}: {p}')
            relative = p.relative_to(root).as_posix()
            selected = next(v for v in identity['sources'].values() if v['root'] == str(root))
            if selected['files'].get(relative) != digest(p):
                raise ValueError(f'unpinned runtime import: {name}: {p}')
        imported[name] = str(p)
    return imported


def read_known(path):
    with Path(path).open(newline='') as f:
        rows = [r for r in csv.DictReader(f) if r['opponent'] == 'solution92'
                and (int(r['seed']), r['side']) in stage_keys('C')]
    typed = [{k: (r[k] if k == 'side' else float(r[k]) if k == 'result' else int(r[k])) for k in RESULT_FIELDS} for r in rows]
    if sorted((r['seed'], r['side']) for r in typed) != sorted(stage_keys('C')):
        raise ValueError('known C keys incomplete or duplicate')
    return typed


def write_json(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def read_manifest(out):
    out = Path(out)
    if digest(out / 'manifest.json') != (out / 'manifest.sha256').read_text().strip():
        raise ValueError('key/source manifest changed')
    return json.loads((out / 'manifest.json').read_text())


def prepare(out, reference, prototype, weights, known_c):
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError(out)
    if Path(sys.executable).resolve() != PYTHON.resolve():
        raise ValueError('use the project Python interpreter')
    identities = {role: source_identity(root, role) for role, root in zip(ROLES, (reference, prototype))}
    if identities['reference']['root'] == identities['prototype']['root']:
        raise ValueError('source roots must differ')
    manifest = dict(schema=1, kind='technical_admission_not_strength', sources=identities,
                    weights=check_weights(weights), tool=file_identity(__file__),
                    plan=file_identity(Path(prototype) / PLAN), known_c=file_identity(known_c),
                    known_results=read_known(known_c), environment=environment_identity(),
                    bitset=BITSET, keys={s: stage_keys(s) for s in ('C', 'S')},
                    limits=dict(S_wall_seconds=1800, G_cpu_p95_ns=5_000_000,
                                G_cpu_max_ns=15_000_000, G_minus_V_cpu_p95_ns=5_000_000))
    out.mkdir(parents=True)
    write_json(out / 'manifest.json', manifest)
    with (out / 'manifest.sha256').open('x') as f:
        f.write(digest(out / 'manifest.json') + '\n')
    return manifest


def check_manifest(manifest):
    for name in ('weights', 'tool', 'plan', 'known_c'):
        check_identity(manifest[name])
    if manifest['weights']['sha256'] != V14 or manifest['bitset'] != BITSET:
        raise ValueError('invalid admission manifest')
    for role in ROLES:
        check_source(manifest['sources'][role])
    if environment_identity() != manifest['environment']:
        raise ValueError('interpreter/engine/environment changed')


def compare_stage(stage, reference, prototype, known):
    expected = sorted(stage_keys(stage))
    for rows in (reference, prototype):
        if sorted((r['seed'], r['side']) for r in rows) != expected:
            raise ValueError(f'{stage} keys incomplete/duplicate')
        for row in rows:
            if row.get('caught_errors', 0):
                raise ValueError('caught policy error: rejected')
            if (row['steps'], row['fresh'], row['resets'], row['point_counting_version'], row['v_attempts']) != (303, 300, 3, 2, 0):
                raise ValueError('steps/observations/scoring/default-off attempts mismatch')
    reference, prototype = (sorted(rows, key=lambda r: (r['seed'], r['side'])) for rows in (reference, prototype))
    for before, after in zip(reference, prototype):
        for field in (*RESULT_FIELDS, 'action_sha256'):
            if before[field] != after[field]:
                raise ValueError(f'paired {field} mismatch: {before["seed"]}/{before["side"]}')
    if stage == 'C':
        known = sorted(known, key=lambda r: (r['seed'], r['side']))
        if sorted((r['seed'], r['side']) for r in known) != expected:
            raise ValueError('known C keys incomplete/duplicate')
        for actual, historical in zip(reference, known):
            if any(actual[k] != historical[k] for k in RESULT_FIELDS):
                raise ValueError('known benchmark result mismatch')


def battery_guard(start=False):
    result = subprocess.run(['/usr/bin/pmset', '-g', 'batt'], capture_output=True, text=True, check=True).stdout
    if 'AC Power' in result:
        return
    percent = re.search(r'(\d+)%;', result)
    if not percent:
        raise ValueError('cannot read battery')
    if int(percent[1]) <= (34 if start else 25):
        raise ValueError('battery start/stop threshold reached')


def check_loaded(agent, checkpoint, torch):
    nets = [agent.q, *agent.extra_q]
    states = [checkpoint['q'], *checkpoint.get('ensemble', [])]
    if (agent.training or agent.epsilon != 0 or agent.autosave_on_terminate or agent.feat_dim != 79
            or agent.n_actions != 6 or len(nets) != 36 or len(states) != 36 or agent.cnn_policy is not None):
        raise ValueError('loaded V14 architecture/inference guard failed')
    for obj in (agent.cfg, agent.belief):
        if getattr(obj, 'overlap_infer', False) or getattr(obj, 'gauss_infer', False):
            raise ValueError('acting overlap/gauss flags must be off')
    if agent.feat_belief is not agent.belief:
        raise ValueError('unexpected independent acting feature belief')
    fingerprints = []
    for net, expected in zip(nets, states):
        actual = net.state_dict()
        if net.feat_dim != 79 or set(actual) != set(expected):
            raise ValueError('loaded tensor architecture mismatch')
        h = hashlib.sha256()
        for key in sorted(actual):
            tensor = actual[key].detach().cpu()
            if not torch.equal(tensor, expected[key].detach().cpu()):
                raise ValueError('loaded tensors differ from V14')
            h.update(key.encode())
            h.update(str(tensor.dtype).encode())
            h.update(str(tuple(tensor.shape)).encode())
            h.update(tensor.numpy().tobytes())
        fingerprints.append(h.hexdigest())
    return dict(nets=36, features=79, actions=6, tensor_sha256=fingerprints,
                overlap=False, gauss=False, train=False, epsilon=0, autosave=False)


def child(out, stage, role):
    out = Path(out).resolve()
    manifest = read_manifest(out)
    manifest_identity = file_identity(out / 'manifest.json')
    start_record = json.loads((out / stage / 'start.json').read_text())
    if start_record['manifest_sha256'] != manifest_identity['sha256']:
        raise ValueError('dispatched manifest changed')
    check_manifest(manifest)
    root = Path(manifest['sources'][role]['root'])
    # Invoked with -I. No checkout, current directory or ambient PYTHONPATH imports.
    sys.path.insert(0, str(root))
    os.chdir(root)
    import_strategy = select_agent_package(root)
    from scripts.experiment import limit_threads
    limit_threads()
    import torch
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent, play_game
    from scripts.oracle_probe import truth_maps
    weights = manifest['weights']['path']
    checkpoint = torch.load(weights, map_location='cpu', weights_only=False)
    agent = Agent_x('player_0', agent_path=weights, train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    loaded = check_loaded(agent, checkpoint, torch)
    loaded['import_strategy'] = import_strategy
    trace = ShadowTrace(agent, shadows=stage == 'S' and role == 'prototype')
    capture = NativeAct(agent)
    env = LuxAIS3GymEnv(numpy_output=True)
    directory = out / stage / role
    directory.mkdir()
    write_json(directory / 'loaded.json', loaded)
    original_step = env.step
    stream = None
    action_hash = None
    last_battery = 0
    frame_count = fresh = resets = 0

    def step(actions):
        nonlocal frame_count, fresh, resets, last_battery
        if time.monotonic() > deadline:
            raise ValueError('stage deadline reached')
        if time.monotonic() - last_battery > 5:
            battery_guard()
            last_battery = time.monotonic()
        truth, truth_time = timed(canonical_truth, env.state, agent.belief.mirrored, truth_maps)
        frame = trace.finish(truth, actions)
        if capture.last != frame['action'][agent.player]:
            raise ValueError('native act capture mismatch')
        if frame['step'] != frame_count:
            raise ValueError('frame sequence gap')
        frame_count += 1
        resets += int(frame['reset'])
        fresh += int(not frame['reset'])
        frame['times']['truth'] = truth_time
        frame['times']['act'] = capture.times
        frame['seed'], frame['side'] = seed, side
        action_hash.update(json.dumps(frame['action'], sort_keys=True, separators=(',', ':')).encode() + b'\n')
        wall, cpu = time.perf_counter_ns(), time.process_time_ns()
        stream.write(json.dumps(frame, sort_keys=True, separators=(',', ':')) + '\n')
        stream.flush()
        io_times.append(dict(cpu_ns=time.process_time_ns() - cpu, wall_ns=time.perf_counter_ns() - wall))
        if 'G' in frame['post'] and not frame['reset']:
            decoded = [{k: {kind: unpack_tiles(v) for kind, v in f.items()}
                        for k, f in frame[phase].items()} for phase in ('pre', 'post')]
            safety = frame_metrics(*decoded, truth)
            if any(any(f.values()) for f in safety['false_extra'].values()):
                raise ValueError('false additional shadow fact: raw frame saved, rejected before env.step')
            if frame['times']['G']['cpu_ns'] > 15_000_000:
                raise ValueError('G observe CPU maximum exceeded: raw frame saved')
        if agent.caught_errors:
            raise ValueError('caught policy error: raw frame saved')
        # Truth/serialization are entirely after both native act calls and before env.step.
        return original_step(actions)
    env.step = step
    deadline = start_record['deadline_monotonic']
    try:
        rows = []
        for seed, side in stage_keys(stage):
            check_identity(manifest_identity)
            check_manifest(manifest)
            battery_guard()
            frame_count = fresh = resets = 0
            io_times = []
            action_hash = hashlib.sha256()
            name = f'{seed}-{side}'
            setup = time.perf_counter_ns()
            opponent = make_opponent('solution92', 'player_1' if side == 'player_0' else 'player_0')
            setup = time.perf_counter_ns() - setup
            check_imports(root, manifest)
            with gzip.open(directory / f'{name}.jsonl.gz', 'xt', encoding='utf-8') as stream:
                row = play_game(env, agent, opponent, seed, side, train=False)
            write_json(directory / f'{name}.timing.json', dict(setup=trace.setup_times,
                       opponent_setup_wall_ns=setup, serialization=io_times))
            with gzip.open(directory / f'{name}.jsonl.gz', 'rt') as f:
                frames = [json.loads(line) for line in f]
            metrics = reconstruct(frames, seed, side)
            row = {k: row[k] for k in RESULT_FIELDS}
            row.update(fresh=fresh, resets=resets, action_sha256=action_hash.hexdigest(),
                       caught_errors=agent.caught_errors,
                       v_attempts=sum(max(0, f['attempts']['V']['post'][0] - f['attempts']['V']['pre'][0]) for f in frames),
                       metrics=metrics, opponent_setup_wall_ns=setup,
                       io_cpu_ns=quantiles([t['cpu_ns'] for t in io_times]),
                       io_wall_ns=quantiles([t['wall_ns'] for t in io_times]))
            check_loaded(agent, checkpoint, torch)
            check_identity(manifest_identity)
            check_manifest(manifest)
            imports = check_imports(root, manifest)
            rows.append(row)
            write_json(directory / f'{name}.result.json', row)
            print(json.dumps(dict(stage=stage, role=role, seed=seed, side=side, completed=len(rows))), flush=True)
            if any(metrics['false_extra'].values()):
                raise ValueError('false additional shadow fact: rejected')
        write_json(directory / 'imports.json', imports)
        write_json(directory / 'rows.json', rows)
    finally:
        env.close()


def audit_stage(out, stage, manifest):
    rows_by_role = []
    proofs = []
    for role in ROLES:
        directory = out / stage / role
        proof = json.loads((directory / 'loaded.json').read_text())
        expected = dict(nets=36, features=79, actions=6, overlap=False, gauss=False,
                        train=False, epsilon=0, autosave=False)
        if (any(proof.get(k) != v for k, v in expected.items())
                or len(proof.get('tensor_sha256', [])) != 36
                or any(not re.fullmatch('[0-9a-f]{64}', h) for h in proof['tensor_sha256'])):
            raise ValueError('loaded-model proof incomplete or invalid')
        strategy = dict(package='agents', path=str(Path(manifest['sources'][role]['root']) / 'agents'),
                        initializer_executed=False,
                        reason='skip recursive autodiscovery; import selected modules directly')
        if proof.get('import_strategy') != strategy:
            raise ValueError('loaded-model import strategy differs from selected root')
        proofs.append(proof)
        rows = json.loads((directory / 'rows.json').read_text())
        for row in rows:
            path = directory / f'{row["seed"]}-{row["side"]}.jsonl.gz'
            with gzip.open(path, 'rt') as f:
                frames = [json.loads(line) for line in f]
            if len(frames) != 303 or [f['step'] for f in frames] != list(range(303)):
                raise ValueError('incomplete raw frame sequence')
            if sum(not f['reset'] for f in frames) != 300 or sum(f['reset'] for f in frames) != 3:
                raise ValueError('raw reset/fresh counts')
            if any(f['seed'] != row['seed'] or f['side'] != row['side'] for f in frames):
                raise ValueError('raw frame key mismatch')
            h = hashlib.sha256()
            for frame in frames:
                if set(frame['action']) != {'player_0', 'player_1'}:
                    raise ValueError('native action sides incomplete')
                for action in frame['action'].values():
                    dtype = re.fullmatch(r'[<>=|][iu](1|2|4|8)', action['dtype'])
                    if (action['shape'] != [16, 3] or dtype is None or action['order'] != 'C'
                            or len(bytes.fromhex(action['hex'])) != int(dtype[1]) * 48):
                        raise ValueError('native action bytes/shape/dtype invalid')
                h.update(json.dumps(frame['action'], sort_keys=True, separators=(',', ':')).encode() + b'\n')
            if h.hexdigest() != row['action_sha256']:
                raise ValueError('raw native action SHA mismatch')
            metrics = reconstruct(frames, row['seed'], row['side'])
            if metrics != row['metrics']:
                raise ValueError('raw metric reconstruction mismatch')
            io_raw = json.loads((directory / f'{row["seed"]}-{row["side"]}.timing.json').read_text())
            if len(io_raw['serialization']) != 303:
                raise ValueError('raw serialization timing incomplete')
            for clock in ('cpu_ns', 'wall_ns'):
                if row[f'io_{clock}'] != quantiles([v[clock] for v in io_raw['serialization']]):
                    raise ValueError('raw serialization timing mismatch')
            if any(metrics['false_extra'].values()):
                raise ValueError('false additional shadow fact')
        rows_by_role.append(rows)
    compare_stage(stage, *rows_by_role, manifest['known_results'])
    if {k: v for k, v in proofs[0].items() if k != 'import_strategy'} != {
            k: v for k, v in proofs[1].items() if k != 'import_strategy'}:
        raise ValueError('paired loaded-model proofs differ')
    return rows_by_role


def audit(out):
    out = Path(out).resolve()
    manifest = read_manifest(out)
    manifest_sha = digest(out / 'manifest.json')
    for stage in ('C', 'S'):
        complete = json.loads((out / stage / 'complete.json').read_text())
        if complete['status'] != 'complete' or complete['manifest_sha256'] != manifest_sha:
            raise ValueError('incomplete phase or manifest changed')
        if (out / stage / 'incomplete-rejected.json').exists():
            raise ValueError('rejected phase cannot be admitted')
    check_manifest(manifest)
    audit_stage(out, 'C', manifest)
    reference, prototype = audit_stage(out, 'S', manifest)
    metrics = [row['metrics'] for row in prototype]
    strict = [key for m in metrics for key in m['strict_facts']]
    # Global quantiles must use every one of the 24,000 raw observations, not per-game quantiles.
    timing = {f'{role}_{clock}': [] for role in ('V', 'A', 'G', 'copies', 'truth', 'act')
              for clock in ('cpu_ns', 'wall_ns')}
    timing['G_minus_V_cpu_ns'] = []
    for seed, side in stage_keys('S'):
        with gzip.open(out / 'S' / 'prototype' / f'{seed}-{side}.jsonl.gz', 'rt') as f:
            for line in f:
                frame = json.loads(line)
                if frame['reset']:
                    continue
                for k in timing:
                    if k == 'G_minus_V_cpu_ns':
                        value = frame['times']['G']['cpu_ns'] - frame['times']['V']['cpu_ns']
                    else:
                        role, clock = k.split('_', 1)
                        value = frame['times'][role][clock]
                    timing[k].append(value)
    costs = {k: quantiles(v) for k, v in timing.items()}
    if any(v['n'] != 24000 for v in costs.values()):
        raise ValueError('timing denominator')
    budgets = costs['G_cpu_ns']['p95'] <= 5_000_000 and costs['G_cpu_ns']['max'] <= 15_000_000 and costs['G_minus_V_cpu_ns']['p95'] <= 5_000_000
    finish = json.loads((out / 'S' / 'complete.json').read_text())
    if finish['wall_seconds'] > 1800:
        raise ValueError('stage S exceeded fixed deadline')
    check_manifest(manifest)
    return dict(status='technically_passed_not_strength_candidate' if strict and budgets else 'rejected',
                games=168, strict_facts=len(strict), strict_point=sum(k[-1] == 'point' for k in strict),
                strict_dead=sum(k[-1] == 'dead' for k in strict),
                games_with_strict=len({(k[0], k[1]) for k in strict}),
                maps_with_strict=len({k[0] for k in strict}), budgets_passed=budgets, timing=costs,
                false_v_fact_steps=sum(m['false_v'] for m in metrics),
                false_extra_fact_steps={k: sum(m['false_extra'][k] for m in metrics) for k in 'AG'},
                fact_steps={k: sum(m['fact_steps'].get(k, 0) for m in metrics)
                            for k in sorted({k for m in metrics for k in m['fact_steps']})},
                leads=[lead for m in metrics for lead in m['lead']],
                limits='Shadow observe only; fixed V/A/G order; no active-G latency, strength, promotion or merge.')


def run_stage(out, stage):
    out = Path(out).resolve()
    manifest = read_manifest(out)
    manifest_identity = file_identity(out / 'manifest.json')
    check_manifest(manifest)
    battery_guard(start=True)
    directory = out / stage
    if directory.exists():
        raise FileExistsError(directory)
    if stage == 'S':
        audit_stage(out, 'C', manifest)
        complete = json.loads((out / 'C' / 'complete.json').read_text())
        if complete['status'] != 'complete' or complete['manifest_sha256'] != manifest_identity['sha256']:
            raise ValueError('C incomplete or manifest changed')
        if (out / 'C' / 'incomplete-rejected.json').exists():
            raise ValueError('C rejected')
        # C includes all trace overhead and warm imports; use a fixed 35% reserve plus60s.
        if complete['wall_seconds'] / 8 * 160 * 1.35 + 60 > 1800:
            raise ValueError('C measurement cannot admit full S block with reserve')
    directory.mkdir()
    start = time.monotonic()
    deadline = start + (1800 if stage == 'S' else 600)
    write_json(directory / 'start.json', dict(start_monotonic=start, deadline_monotonic=deadline,
                                             manifest_sha256=manifest_identity['sha256'],
                                             sources_before=manifest['sources']))
    try:
        for role in ROLES:
            check_identity(manifest_identity)
            check_manifest(manifest)
            battery_guard(start=True)
            with (directory / f'{role}.log').open('x') as log:
                subprocess.run([str(PYTHON), '-I', '-B', manifest['tool']['path'], '--child',
                                '--out', str(out), '--stage', stage, '--role', role],
                               cwd='/', env={**os.environ, 'PYTHONPATH': '', 'PYTHONDONTWRITEBYTECODE': '1'},
                               stdout=log, stderr=subprocess.STDOUT, check=True,
                               timeout=max(.1, deadline - time.monotonic()))
            check_manifest(manifest)
            check_identity(manifest_identity)
        audit_stage(out, stage, manifest)
        if time.monotonic() > deadline:
            raise ValueError('stage deadline exceeded')
        write_json(directory / 'complete.json', dict(wall_seconds=time.monotonic() - start,
                                                    manifest_sha256=manifest_identity['sha256'],
                                                    status='complete', sources_after=manifest['sources']))
        if stage == 'S':
            write_json(out / 'audit.json', audit(out))
    except BaseException as error:
        write_json(directory / 'incomplete-rejected.json', dict(status='incomplete/rejected', error=str(error),
                                                              wall_seconds=time.monotonic() - start))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', nargs='?', choices=('prepare', 'run-stage', 'audit'))
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--prototype', type=Path)
    parser.add_argument('--weights', type=Path)
    parser.add_argument('--known-c', type=Path)
    parser.add_argument('--stage', choices=('C', 'S'))
    parser.add_argument('--role', choices=ROLES)
    parser.add_argument('--child', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        if not sys.flags.isolated or not args.stage or not args.role:
            parser.error('child requires isolated interpreter, stage and role')
        child(args.out, args.stage, args.role)
    elif args.command == 'prepare':
        if not all((args.reference, args.prototype, args.weights, args.known_c)):
            parser.error('prepare requires --reference --prototype --weights --known-c')
        prepare(args.out, args.reference, args.prototype, args.weights, args.known_c)
    elif args.command == 'run-stage' and args.stage:
        run_stage(args.out, args.stage)
    elif args.command == 'audit':
        print(json.dumps(audit(args.out), indent=2))
    else:
        parser.error('choose prepare, run-stage --stage C/S, or audit')


if __name__ == '__main__':
    main()
