#!/usr/bin/env python3
"""Independent, stdlib-only closed-data audit. Never imports repository code.

Run only after Root closes S:
  python3 -B gauss-independent-audit.py --out NEW_RESULT_JSON
The preflight pin is made before reading any S outcome. No games/models/tests.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import sys

BASE = Path('/tmp/sherlock-continue-20261102')
FOLLOWUP = Path('/Users/moayedshawesh/Desktop/KI/sherlock-november-followup')
EVIDENCE = FOLLOWUP / 'experiments/analysis/gauss_admission_20261102/evidence'
V14 = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
REFERENCE = '384dad2b5a077f5ab026f63c5c8a2d944bc51776'
RUNTIME = '3a7e7825b614a30bc85c7895a38e6b9fc62efdd5'
PROTOTYPE = '969cc319c76fbb5d01454bab1591f3411864f867'
PROTO_RUNTIME = '307b1ed2051cb9b1a339f849f4322630f5dca7b9'
FIELDS = ('seed', 'side', 'steps', 'our_wins', 'opp_wins', 'result',
          'our_points', 'opp_points', 'point_counting_version')
ROLES = ('reference', 'prototype')
KINDS = ('point', 'dead')
LIMITS = dict(S_wall_seconds=1800, G_cpu_p95_ns=5_000_000,
              G_cpu_max_ns=15_000_000, G_minus_V_cpu_p95_ns=5_000_000)
BITSET = dict(bits=576, index='x*24+y', bitorder='little', encoding='hex')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def git(root, *args, binary=False):
    return subprocess.check_output(['git', '-C', str(root), *args], text=not binary)


def keys(stage):
    if stage == 'C':
        return [(831006, 'player_1'), (831029, 'player_0'),
                (831042, 'player_0'), (831043, 'player_1')]
    return [(s, p) for s in range(840000, 840040) for p in ('player_0', 'player_1')]


def qstats(values):
    data = sorted(values)
    if not data:
        return dict(n=0, median=None, p95=None, max=None)
    def percentile(p):
        rank = (len(data) - 1) * p
        i = math.floor(rank)
        return data[i] + (data[min(i + 1, len(data) - 1)] - data[i]) * (rank - i)
    return dict(n=len(data), median=percentile(.5), p95=percentile(.95), max=data[-1])


def equal(a, b):
    if type(a) is dict and type(b) is dict:
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if isinstance(a, (float, int)) and isinstance(b, (float, int)):
        return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= 1e-6
    return a == b


class Audit:
    def __init__(self):
        self.checks = 0
        self.errors = []
        self.inputs = {}

    def check(self, ok, label):
        self.checks += 1
        if not ok:
            self.errors.append(label)

    def need(self, ok, label):
        self.check(ok, label)
        if not ok:
            raise ValueError(label)

    def load(self, path):
        path = Path(path)
        self.inputs[str(path)] = sha(path)
        return read(path)

    def identity(self, identity):
        p = Path(identity['path']).resolve(strict=True)
        self.check(str(p) == identity['path'] and sha(p) == identity['sha256'], f'identity:{p}')


def tiles(encoded):
    if not isinstance(encoded, str) or re.fullmatch('[0-9a-f]{144}', encoded) is None:
        raise ValueError('noncanonical 576-bit tile set')
    number = int.from_bytes(bytes.fromhex(encoded), 'little')
    result = set()
    while number:
        bit = number & -number
        result.add(bit.bit_length() - 1)
        number -= bit
    return result


def decode(state):
    return {r: {k: tiles(v) for k, v in facts.items()} for r, facts in state.items()}


def native(audit, action, label):
    audit.need(set(action) == {'shape', 'dtype', 'order', 'hex'}, label + ':schema')
    m = re.fullmatch(r'([<>=|])([iu])(1|2|4|8)', action['dtype'])
    audit.need(action['shape'] == [16, 3] and action['order'] == 'C' and m is not None, label + ':layout')
    payload = bytes.fromhex(action['hex'])
    width = int(m[3])
    audit.need(len(payload) == 48 * width, label + ':bytes')
    endian = m[1] if m[1] in '<>' else '='
    code = {('i', 1): 'b', ('u', 1): 'B', ('i', 2): 'h', ('u', 2): 'H',
            ('i', 4): 'i', ('u', 4): 'I', ('i', 8): 'q', ('u', 8): 'Q'}[m[2], width]
    values = struct.unpack(endian + code * 48, payload)
    audit.check(all(0 <= x <= 5 for x in values[::3]), label + ':action_codes')


def world_tile(tile, side):
    x, y = divmod(tile, 24)
    return tile if side == 'player_0' else (23 - y) * 24 + 23 - x


def raw_game(audit, path, row, shadow, clocks):
    """Reconstruct without importing/calling the implementation's reconstructor."""
    audit.inputs[str(path)] = sha(path)
    with gzip.open(path, 'rt') as stream:
        frames = [json.loads(line) for line in stream]
    audit.need(len(frames) == 303, f'{path}:303_frames')
    actor = {'V', 'A', 'G'} if shadow else {'V'}
    totals = dict(strict_facts=[], extra_current={'point': 0, 'dead': 0},
                  false_extra={'A': 0, 'G': 0}, false_v=0, conflicts=0,
                  fact_steps={}, attempts=[], lead=[], positive_carryovers=0)
    counts = Counter()
    time_data = {}
    strict_keys, leads, acquisition = set(), [], {}
    previous, previous_truth, previous_match = None, None, None
    positive_steps = conservative_positive_steps = 0
    reset_false_extra = Counter()
    h, history = hashlib.sha256(), hashlib.sha256()
    seed, side = row['seed'], row['side']

    def end_dead(reason, step):
        for lead in leads:
            if lead['key'][-1] == 'dead':
                for r in 'VA':
                    if lead[r] is None and lead['censored'][r] is None:
                        lead['censored'][r] = reason
                        lead['_end'][r] = step

    for step, frame in enumerate(frames):
        label = f'{path.name}:{step}'
        audit.need((frame['seed'], frame['side'], frame['step']) == (seed, side, step), label + ':key')
        audit.check((frame['match'], frame['match_step'], frame['reset']) ==
                    (step // 101, step % 101, step % 101 == 0), label + ':match_reset_sequence')
        audit.need(set(frame['pre']) == actor and set(frame['post']) == actor and
                   set(frame['attempts']) == actor, label + ':roles')
        for phase in ('pre', 'post'):
            audit.need(all(set(v) == set(KINDS) for v in frame[phase].values()), label + ':fact_schema')
        pre, post = decode(frame['pre']), decode(frame['post'])
        truth = tiles(frame['truth'])
        audit.need(set(frame['action']) == {'player_0', 'player_1'}, label + ':native_sides')
        for side_name, act in frame['action'].items():
            native(audit, act, label + ':' + side_name)
        h.update(json.dumps(frame['action'], sort_keys=True, separators=(',', ':')).encode() + b'\n')
        history.update(json.dumps([frame['pre']['V'], frame['post']['V'], frame['truth'],
                                  frame['match'], frame['match_step']], sort_keys=True).encode())
        if previous is not None:
            audit.check(pre == previous, label + ':pre_post_continuity')
        previous = post
        for role, pair in frame['attempts'].items():
            audit.need(set(pair) == {'pre', 'post'} and all(len(pair[p]) == 3 and
                       all(type(v) is int for v in pair[p]) for p in pair), label + ':counter_schema')
            before, after = pair['pre'], pair['post']
            if role != 'G':
                audit.check(after[0] == before[0] == 0, label + ':default_off_attempts')
            elif frame['reset']:
                audit.check(after == [0, 0, -8], label + ':G_reset')
            else:
                audit.check(after[1] == before[1] + 1 and after[1] == frame['match_step'], label + ':G_observations')
                delta = after[0] - before[0]
                audit.check(0 <= before[0] <= after[0] <= 8 and delta in (0, 1), label + ':G_cap')
                if delta:
                    audit.check(after[2] == after[1] and after[2] - before[2] >= 8, label + ':G_spacing')
                    totals['attempts'].append(dict(match=frame['match'], step=step, observation=after[1]))
                else:
                    audit.check(after[2] == before[2], label + ':G_last_attempt_unchanged')
        expected_times = actor | {'copies', 'truth', 'act'}
        audit.need(set(frame['times']) == expected_times, label + ':timing_roles')
        for role, times in frame['times'].items():
            audit.need(set(times) == {'cpu_ns', 'wall_ns'} and
                       all(type(v) is int and v >= 0 for v in times.values()), label + ':finite_times')
        if previous_truth is not None and truth != previous_truth:
            end_dead('truth_regime_change', step)
        previous_truth = truth
        if frame['reset']:
            counts['reset'] += 1
            if previous_match is not None and shadow:
                totals['positive_carryovers'] += len(post['G']['point'] - post['V']['point'])
            previous_match = frame['match']
            end_dead('match_reset', step)
            # Positive knowledge survives resets; if a baseline first catches up
            # on this raw reset frame, record that observed step, not step+1.
            for lead in leads:
                if lead['key'][-1] == 'point':
                    for role in 'VA':
                        if (lead[role] is None and lead['censored'][role] is None
                                and lead['key'][3] in post[role]['point']):
                            lead[role] = step - lead['step']
            if shadow:
                for r in 'AG':
                    reset_false_extra[r] += len((post[r]['point'] - post['V']['point']) - truth)
                    reset_false_extra[r] += len((post[r]['dead'] - post['V']['dead']) & truth)
            continue
        counts['fresh'] += 1
        for role in actor:
            for clock in ('cpu_ns', 'wall_ns'):
                time_data.setdefault(f'{role}_{clock}', []).append(frame['times'][role][clock])
        if not shadow:
            continue
        for role in ('V', 'A', 'G', 'copies', 'truth', 'act'):
            for clock in ('cpu_ns', 'wall_ns'):
                clocks.setdefault(f'{role}_{clock}', []).append(frame['times'][role][clock])
        extra_cost = frame['times']['G']['cpu_ns'] - frame['times']['V']['cpu_ns']
        clocks.setdefault('G_minus_V_cpu_ns', []).append(extra_cost)
        time_data.setdefault('G_minus_V_cpu_ns', []).append(extra_cost)
        v_pre = pre['V']['point'] | pre['V']['dead']
        va_post = set().union(*(post[r][kind] for r in 'VA' for kind in KINDS))
        totals['false_v'] += len(post['V']['point'] - truth) + len(post['V']['dead'] & truth)
        for a in 'VAG':
            for b in 'VAG':
                totals['conflicts'] += len(post[a]['point'] & post[b]['dead'])
        for r in 'AG':
            totals['false_extra'][r] += len((post[r]['point'] - post['V']['point']) - truth)
            totals['false_extra'][r] += len((post[r]['dead'] - post['V']['dead']) & truth)
        for a, b in (('A', 'V'), ('V', 'A'), ('G', 'V'), ('V', 'G'), ('G', 'A'), ('A', 'G')):
            for kind in KINDS:
                key = f'{a}-{b}_{kind}'
                totals['fact_steps'][key] = totals['fact_steps'].get(key, 0) + len(post[a][kind] - post[b][kind])
        advantage = post['G']['point'] - (post['V']['point'] | post['A']['point'])
        positive_steps += len(advantage)
        conservative_positive_steps += len(post['G']['point'] - va_post)
        for kind in KINDS:
            new_unknown = (post['G'][kind] - pre['G'][kind]) - v_pre
            totals['extra_current'][kind] += len(new_unknown)
            for tile in sorted(new_unknown - va_post):
                key = (seed, side, frame['match'], tile, kind)
                if key not in strict_keys:
                    strict_keys.add(key)
                    lead = dict(key=list(key), step=step, V=None, A=None,
                                censored={'V': None, 'A': None}, _end={})
                    leads.append(lead)
                    acquisition[key] = step
        for lead in leads:
            _, _, match, tile, kind = lead['key']
            if kind == 'dead' and match != frame['match']:
                continue
            for role in 'VA':
                if lead[role] is None and lead['censored'][role] is None and tile in post[role][kind]:
                    lead[role] = step - lead['step']
            if kind == 'dead' and tile not in post['G']['dead']:
                for role in 'VA':
                    if lead[role] is None and lead['censored'][role] is None:
                        lead['censored'][role] = 'knowledge_lost'
                        lead['_end'][role] = step
        previous_match = frame['match']
    audit.check(counts == {'reset': 3, 'fresh': 300}, str(path) + ':denominators')
    audit.check(h.hexdigest() == row['action_sha256'], str(path) + ':native_digest')
    totals['strict_facts'] = [list(k) for k in sorted(strict_keys)]
    totals['timing'] = {key: qstats(v) for key, v in time_data.items()}
    totals['lead'] = [{k: v for k, v in lead.items() if not k.startswith('_')} for lead in leads]
    for k, v in totals.items():
        audit.check(equal(v, row['metrics'][k]), f'{path}:official_metric:{k}')
    independent_leads = []
    for lead in leads:
        item = {k: v for k, v in lead.items() if not k.startswith('_')}
        item['censored'] = dict(lead['censored'])
        item['followup_steps'] = {}
        for role in 'VA':
            if item[role] is not None:
                item['followup_steps'][role] = item[role]
            else:
                if item['censored'][role] is None:
                    item['censored'][role] = 'administrative_game_end'
                item['followup_steps'][role] = lead['_end'].get(role, 302) - item['step']
        independent_leads.append(item)
    audit.check(not any(totals['false_extra'].values()), str(path) + ':no_false_extra')
    return dict(metrics=totals, leads=independent_leads, action_sha256=h.hexdigest(),
                V_truth_history_sha256=history.hexdigest(), positive_union_fact_steps=positive_steps,
                positive_union_unknown_fact_steps=conservative_positive_steps,
                reset_false_extra=dict(reset_false_extra))


def source_seal(audit, identity, role):
    root = Path(identity['root'])
    head = REFERENCE if role == 'reference' else PROTOTYPE
    basis = RUNTIME if role == 'reference' else PROTO_RUNTIME
    audit.check(identity['head'] == head and identity['runtime_base'] == basis, role + ':fixed_heads')
    audit.check(git(root, 'rev-parse', 'HEAD').strip() == head, role + ':actual_head')
    paths = {p for p in git(root, 'ls-files', '--', 'agents', 'lux', 'scripts').splitlines() if p.endswith('.py')}
    audit.need(paths == set(identity['files']), role + ':complete_runtime_inventory')
    for relative, expected in identity['files'].items():
        p = root / relative
        data = p.read_bytes()
        audit.check(hashlib.sha256(data).hexdigest() == expected, role + ':runtime_hash:' + relative)
        audit.check(data == git(root, 'show', f'{head}:{relative}', binary=True) ==
                    git(root, 'show', f'{basis}:{relative}', binary=True), role + ':runtime_git_binding:' + relative)


def proof_and_imports(audit, directory, manifest, role):
    proof = audit.load(directory / 'loaded.json')
    expected = dict(nets=36, features=79, actions=6, overlap=False, gauss=False,
                    train=False, epsilon=0, autosave=False)
    audit.check(all(proof.get(k) == v for k, v in expected.items()), str(directory) + ':loaded_config')
    audit.check(len(proof.get('tensor_sha256', [])) == 36 and
                all(re.fullmatch('[0-9a-f]{64}', v) for v in proof['tensor_sha256']), str(directory) + ':loaded_tensor_proof')
    root = Path(manifest['sources'][role]['root'])
    audit.check(proof.get('import_strategy') == dict(package='agents', path=str(root / 'agents'),
                initializer_executed=False, reason='skip recursive autodiscovery; import selected modules directly'),
                str(directory) + ':fresh_selected_root_strategy')
    imported = audit.load(directory / 'imports.json')
    audit.need(all(name in imported for name in ('agents.sherlock.main', 'scripts.common',
               'scripts.oracle_probe', 'luxai_s3.wrappers')), str(directory) + ':required_imports')
    for name, path in imported.items():
        p = Path(path).resolve(strict=True)
        if name.startswith('luxai_s3'):
            audit.check(manifest['environment']['engine'].get(str(p)) == sha(p), name + ':engine_import')
        else:
            audit.need(p.is_relative_to(root), name + ':selected_root_only')
            relative = p.relative_to(root).as_posix()
            audit.check(manifest['sources'][role]['files'].get(relative) == sha(p), name + ':tracked_import')
    return {k: v for k, v in proof.items() if k != 'import_strategy'}


def run(audit, args):
    pin = audit.load(args.pin)
    audit.need(pin['script_sha256'] == sha(__file__), 'independent_script_preflight_pin')
    for identity in pin['frozen_inputs']:
        audit.identity(identity)
    audit.need(str(args.evidence.resolve()) == pin['evidence'], 'predeclared_evidence_root')
    out = args.evidence
    # Mandatory closure guard BEFORE opening any S row, raw trace or novelty summary.
    completed = {}
    receipts = {}
    for stage in ('C', 'S'):
        audit.need((out / stage / 'complete.json').is_file() and
                   not (out / stage / 'incomplete-rejected.json').exists(), stage + ':closed_not_rejected')
        completed[stage] = audit.load(out / stage / 'complete.json')
        receipts[stage] = audit.load(BASE / f'gauss_{stage}_execution.json')
        audit.need(completed[stage]['status'] == receipts[stage]['status'] == 'complete' and
                   receipts[stage]['exit_code'] == 0, stage + ':successful_supervisor_close')
    manifest = audit.load(out / 'manifest.json')
    manifest_sha = sha(out / 'manifest.json')
    audit.check((out / 'manifest.sha256').read_text().strip() == manifest_sha, 'manifest_seal')
    audit.check(manifest['schema'] == 1 and manifest['kind'] == 'technical_admission_not_strength', 'manifest_schema')
    audit.check(manifest['bitset'] == BITSET and manifest['limits'] == LIMITS, 'fixed_bitset_budgets')
    audit.check(manifest['keys'] == {s: [list(k) for k in keys(s)] for s in ('C', 'S')}, 'fixed_all_keys')
    audit.check(manifest['weights']['sha256'] == V14, 'V14_identity')
    for name in ('tool', 'plan', 'weights', 'known_c'):
        audit.identity(manifest[name])
    for role in ROLES:
        source_seal(audit, manifest['sources'][role], role)
    audit.identity(manifest['environment']['interpreter'])
    for path, expected in manifest['environment']['engine'].items():
        audit.check(sha(path) == expected, 'actual_engine:' + path)
    with Path(manifest['known_c']['path']).open(newline='') as stream:
        known = [{k: r[k] if k == 'side' else float(r[k]) if k == 'result' else int(r[k]) for k in FIELDS}
                 for r in csv.DictReader(stream) if r['opponent'] == 'solution92' and
                 (int(r['seed']), r['side']) in keys('C')]
    audit.check(sorted(known, key=lambda r: (r['seed'], r['side'])) ==
                sorted(manifest['known_results'], key=lambda r: (r['seed'], r['side'])), 'historical_C_csv_binding')
    all_games, proofs, clocks = {}, [], {}
    raw_hashes = {}
    for stage in ('C', 'S'):
        start = audit.load(out / stage / 'start.json')
        finish, receipt = completed[stage], receipts[stage]
        audit.check(start['manifest_sha256'] == finish['manifest_sha256'] ==
                    receipt['manifest_sha256'] == manifest_sha, stage + ':phase_manifest_binding')
        audit.check(start['sources_before'] == finish['sources_after'] == manifest['sources'], stage + ':source_seals')
        audit.check(receipt['complete_sha256'] == sha(out / stage / 'complete.json'), stage + ':supervisor_complete_binding')
        budget = 600 if stage == 'C' else 1800
        audit.check(start['deadline_monotonic'] - start['start_monotonic'] == budget and
                    0 < finish['wall_seconds'] <= budget, stage + ':fixed_deadline')
        command = [str(manifest['environment']['interpreter']['path']), '-B', manifest['tool']['path'],
                   'run-stage', '--out', str(out), '--stage', stage]
        # The manifest stores the resolved interpreter; command may use its venv symlink.
        audit.check(Path(receipt['command'][0]).resolve() == Path(command[0]).resolve() and
                    receipt['command'][1:] == command[1:], stage + ':exact_command')
        audit.check(receipt['supervisor_sha256'] == pin['supervisor_sha256'], stage + ':supervisor_code_pin')
        for role in ROLES:
            directory = out / stage / role
            proofs.append(proof_and_imports(audit, directory, manifest, role))
            rows = audit.load(directory / 'rows.json')
            audit.need([(r['seed'], r['side']) for r in rows] == keys(stage), stage + ':' + role + ':exact_ordered_keys')
            expected_files = {f'{seed}-{side}{ext}' for seed, side in keys(stage)
                              for ext in ('.jsonl.gz', '.result.json', '.timing.json')}
            actual_files = {p.name for p in directory.iterdir() if p.name not in ('rows.json', 'loaded.json', 'imports.json')}
            audit.check(actual_files == expected_files, stage + ':' + role + ':complete_file_keys')
            for row in rows:
                label = f'{stage}/{role}/{row["seed"]}-{row["side"]}'
                audit.check((row['steps'], row['fresh'], row['resets'], row['point_counting_version'],
                            row['v_attempts'], row['caught_errors']) == (303, 300, 3, 2, 0, 0), label + ':counters')
                audit.check(all(type(row[k]) is int and row[k] >= 0 for k in
                            ('our_wins', 'opp_wins', 'our_points', 'opp_points')) and
                            row['our_wins'] + row['opp_wins'] <= 3, label + ':finite_outcomes')
                expected_result = 1 if row['our_wins'] > row['opp_wins'] else 0 if row['our_wins'] < row['opp_wins'] else .5
                audit.check(row['result'] == expected_result, label + ':outcome_coherence')
                stem = directory / f'{row["seed"]}-{row["side"]}'
                audit.check(audit.load(str(stem) + '.result.json') == row, label + ':row_file_binding')
                io = audit.load(str(stem) + '.timing.json')
                audit.need(len(io['serialization']) == 303, label + ':serialization_n')
                for clock in ('cpu_ns', 'wall_ns'):
                    audit.check(all(type(v[clock]) is int and v[clock] >= 0 for v in io['serialization']), label + ':io_times')
                    audit.check(equal(qstats([v[clock] for v in io['serialization']]), row['io_' + clock]), label + ':io_quantiles')
                game = raw_game(audit, Path(str(stem) + '.jsonl.gz'), row, stage == 'S' and role == 'prototype', clocks)
                all_games[stage, role, row['seed'], row['side']] = (row, game)
                raw_hashes[label] = audit.inputs[str(stem) + '.jsonl.gz']
        for seed, side in keys(stage):
            a, ag = all_games[stage, 'reference', seed, side]
            b, bg = all_games[stage, 'prototype', seed, side]
            audit.check(all(a[f] == b[f] for f in (*FIELDS, 'action_sha256')), f'{stage}/{seed}/{side}:native_outcome_parity')
            audit.check(ag['V_truth_history_sha256'] == bg['V_truth_history_sha256'], f'{stage}/{seed}/{side}:V_truth_history_parity')
            if stage == 'C':
                historical = [r for r in known if (r['seed'], r['side']) == (seed, side)]
                audit.need(len(historical) == 1, f'C/{seed}/{side}:one_historical_key')
                audit.check(all(a[f] == historical[0][f] for f in FIELDS), f'C/{seed}/{side}:historical_outcomes')
    audit.check(all(p == proofs[0] for p in proofs), 'four_loaded_tensor_proofs_identical')
    audit.check(completed['C']['wall_seconds'] / 8 * 160 * 1.35 + 60 <= 1800, 'C_based_S_admission_reserve')
    audit.check(datetime.fromisoformat(receipts['C']['finished_utc']) <=
                datetime.fromisoformat(receipts['S']['started_utc']), 'C_closed_before_S')
    s_games = [all_games['S', 'prototype', seed, side][1] for seed, side in keys('S')]
    strict = [key for game in s_games for key in game['metrics']['strict_facts']]
    positive = [key for key in strict if key[-1] == 'point']
    physical = {(key[0], world_tile(key[3], key[1]), 'point') for key in positive}
    game_tiles = {(key[0], key[1], key[3], 'point') for key in positive}
    positive_games = {(key[0], key[1]) for key in positive}
    costs = {k: qstats(v) for k, v in clocks.items()}
    audit.check(all(v['n'] == 24000 for v in costs.values()), 'global_fresh_timing_denominator')
    budget_pass = (costs['G_cpu_ns']['p95'] <= 5_000_000 and costs['G_cpu_ns']['max'] <= 15_000_000 and
                   costs['G_minus_V_cpu_ns']['p95'] <= 5_000_000)
    factsteps = {k: sum(g['metrics']['fact_steps'].get(k, 0) for g in s_games)
                 for k in sorted({k for g in s_games for k in g['metrics']['fact_steps']})}
    false_extra = {r: sum(g['metrics']['false_extra'][r] for g in s_games) for r in 'AG'}
    technical = bool(strict) and budget_pass and not any(false_extra.values())
    positive_steps = sum(g['positive_union_fact_steps'] for g in s_games)
    routing_counts = dict(strict_positive_acquisitions=len(positive), strict_positive_game_tiles=len(game_tiles),
                          strict_positive_world_tiles=len(physical), games_acquiring_strict_positive=len(positive_games),
                          maps_acquiring_strict_positive=len({k[0] for k in positive}),
                          additional_positive_fact_steps_over_V_union_A=positive_steps,
                          unknown_to_both_types_positive_fact_steps=sum(g['positive_union_unknown_fact_steps'] for g in s_games))
    routing_conditions = dict(technical_admission=technical, positive_physical_facts_ge20=len(physical) >= 20,
                              acquiring_games_ge5=len(positive_games) >= 5,
                              acquiring_maps_ge3=len({k[0] for k in positive}) >= 3,
                              additional_positive_fact_steps_ge100=positive_steps >= 100)
    official = audit.load(out / 'audit.json')
    derived = dict(status='technically_passed_not_strength_candidate' if technical else 'rejected',
                   games=168, strict_facts=len(strict), strict_point=len(positive), strict_dead=len(strict)-len(positive),
                   games_with_strict=len({(k[0], k[1]) for k in strict}), maps_with_strict=len({k[0] for k in strict}),
                   budgets_passed=budget_pass, timing=costs, fact_steps=factsteps,
                   false_extra_fact_steps=false_extra, false_v_fact_steps=sum(g['metrics']['false_v'] for g in s_games),
                   leads=[l for g in s_games for l in g['metrics']['lead']])
    for k, v in derived.items():
        audit.check(equal(v, official[k]), 'official_global:' + k)
    # Recheck every opened evidence identity after reconstruction; do not seal moving inputs.
    for path, expected in audit.inputs.items():
        audit.check(sha(path) == expected, 'audit_input_unchanged:' + path)
    return dict(manifest_sha256=manifest_sha, games=168, paired_keys=dict(C=4, S=80),
                raw_file_hashes=raw_hashes, technical_admission=technical,
                technical_gate_status=derived['status'], routing_counts=routing_counts,
                routing_conditions=routing_conditions, practical_routing_gate=all(routing_conditions.values()),
                timing=costs, strict_acquisition_keys=strict, positive_world_keys=[list(k) for k in sorted(physical)],
                fact_steps=factsteps, false_extra_fact_steps=false_extra,
                false_v_fact_steps=derived['false_v_fact_steps'],
                independently_censored_leads=[l for g in s_games for l in g['leads']],
                reset_false_extra_fact_steps={r: sum(g['reset_false_extra'].get(r, 0) for g in s_games) for r in 'AG'},
                limits=['No model or engine re-execution; loaded tensor proofs checked, tensors not independently loaded.',
                        'Truth correctness relies on reviewed post-act canonical oracle mapping; no hidden state replay.',
                        'Fixed V/A/G execution order; shadow observe CPU is not active-G agent latency.',
                        'C old CSV binds outcomes; raw new source-to-source native bytes bind passivity.',
                        'Observed/censored leads are descriptive; no strength interval or promotion decision.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=EVIDENCE)
    parser.add_argument('--pin', type=Path, default=BASE / 'gauss-independent-audit-pin.json')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    audit = Audit()
    result = dict(kind='independent_technical_data_audit_not_strength',
                  started_utc=datetime.now(timezone.utc).isoformat())
    try:
        result.update(run(audit, args))
    except Exception as error:
        result['fatal_error'] = f'{type(error).__name__}: {error}'
    result.update(status='accepted' if not audit.errors and 'fatal_error' not in result else 'rejected',
                  checks=audit.checks, errors=audit.errors, input_hashes=audit.inputs,
                  finished_utc=datetime.now(timezone.utc).isoformat())
    with args.out.open('x') as f:
        json.dump(result, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')
    print(json.dumps({k: result.get(k) for k in ('status', 'checks', 'technical_admission',
                      'practical_routing_gate', 'routing_counts', 'fatal_error')}))
    return 0 if result['status'] == 'accepted' else 1


if __name__ == '__main__':
    raise SystemExit(main())
