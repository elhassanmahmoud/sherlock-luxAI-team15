#!/usr/bin/env python3
"""Independent, standard-library-only audit of a COMPLETED targeting probe.

Never imports the probe, torch, numpy, or a model. No result directory is opened
until main() is explicitly invoked. The guard's pinned identity is rehashed without importing its implementation;
arbitrary receipts are never accepted merely because they exist.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict, deque
import csv
from functools import lru_cache
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess

DIRECTIONS = ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0))
MIRROR = (0, 2, 1, 4, 3)
V14_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
COMPARE = ('action_sha256', 'steps', 'reset_steps', 'decision_steps', 'our_wins',
           'opp_wins', 'result', 'our_points', 'opp_points',
           'point_counting_version', 'matches', 'config', 'caught_errors')
BASELINE = ('result', 'our_wins', 'opp_wins', 'our_points', 'opp_points',
            'point_counting_version', 'steps')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    with Path(path).open() as f:
        return json.load(f, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


class Checks:
    def __init__(self):
        self.total = 0
        self.failures = []
        self.failure_total = 0
    def check(self, condition, label, key=None):
        self.total += 1
        if not condition:
            self.failure_total += 1
            if len(self.failures) < 100:
                self.failures.append(dict(label=label, key=key))
        return bool(condition)


class Metrics:
    def __init__(self):
        self.rows = {}
    def add(self, name, game, amount=1, phase=None):
        if not amount:
            return
        r = self.rows.setdefault(name, dict(count=0, games=set(), maps=set(), phases=set()))
        r['count'] += amount
        r['games'].add(tuple(game))
        r['maps'].add(game[0])
        if phase is not None:
            r['phases'].add(tuple(phase))
    def export(self):
        return {k: dict(count=v['count'], games=len(v['games']), maps=len(v['maps']),
                        distinct_phases_bearing_condition=len(v['phases']))
                for k, v in sorted(self.rows.items())}


@lru_cache(maxsize=128)
def distances(grid, target):
    w, h = len(grid), len(grid[0])
    out = [[-1] * h for _ in range(w)]
    x, y = target
    if not (0 <= x < w and 0 <= y < h and grid[x][y]):
        return tuple(map(tuple, out))
    out[x][y] = 0
    queue = deque([target])
    while queue:
        x, y = queue.popleft()
        for dx, dy in DIRECTIONS[1:]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and grid[nx][ny] and out[nx][ny] < 0:
                out[nx][ny] = out[x][y] + 1
                queue.append((nx, ny))
    return tuple(map(tuple, out))


def path(grid, position, target, mask):
    dmap = distances(grid, target)
    w, h = len(grid), len(grid[0])
    x, y = position
    if not (0 <= x < w and 0 <= y < h):
        return None, []
    d = dmap[x][y]
    # A drifted asteroid under a unit does not prevent leaving that starting tile.
    if d < 0:
        neighbours = [dmap[x + dx][y + dy] + 1 for dx, dy in DIRECTIONS[1:]
                      if 0 <= x + dx < w and 0 <= y + dy < h and dmap[x + dx][y + dy] >= 0]
        if neighbours:
            d = min(neighbours)
    if d < 0:
        return None, []
    progress = [a for a, (dx, dy) in enumerate(DIRECTIONS[1:], 1)
                if mask[a] and 0 <= x + dx < w and 0 <= y + dy < h
                and dmap[x + dx][y + dy] == d - 1 and dmap[x + dx][y + dy] >= 0]
    return d, progress


def argmax(values):
    return max(range(len(values)), key=lambda i: values[i])


def canonical(native, mirrored):
    a, dx, dy = native
    return [a, dx, dy] if not mirrored else ([5, -dy, -dx] if a == 5 else [MIRROR[a], dx, dy])


def maximum_first_step_matching(tiles):
    """At most sixteen movable units; a matching is only a first-step capacity bound."""
    owner = {}
    def visit(tile, seen):
        for unit in tiles[tile]:
            if unit in seen:
                continue
            seen.add(unit)
            if unit not in owner or visit(owner[unit], seen):
                owner[unit] = tile
                return True
        return False
    return sum(visit(tile, set()) for tile in tiles)


def audit_frame(frame, game, index, checks, metrics, state):
    where = list(game) + [index]
    key = frame['key']
    checks.check((key['seed'], key['side']) == tuple(game), 'trace key', where)
    checks.check(key['obs_step'] == index, 'observation step sequence', where)
    checks.check(key['match_step'] == index % 101, 'match step sequence', where)
    checks.check(key['match_idx'] == index // 101, 'match index sequence', where)
    status = frame['status']
    if index % 101 == 0:
        checks.check(status == 'reset' and not frame['units'], 'reset is not a stale decision', where)
        state['free_start'].clear()
        state['low_start'].clear()
        return
    checks.check(status == 'decision', 'decision status', where)
    if status != 'decision':
        return
    p = frame['public']
    ids = p['ally_ids']
    units = {u['uid']: u for u in frame['units']}
    checks.check(list(units) == ids, 'unit order equals public IDs', where)
    checks.check(p['step'] == index and p['match_step'] == index % 101
                 and p['match_idx'] == index // 101, 'public key', where)
    grid = tuple(tuple(bool(x) for x in row) for row in p['passable'])
    w, h = p['W'], p['H']
    points = p['point_tiles']
    assigned = {int(u): tuple(t) for u, t in p['assigned'].items()}
    positions = {u: tuple(p['ally_pos'][u]) for u in ids}
    energies = {u: p['ally_ene'][u] for u in ids}
    occupied = set(positions.values())
    visible = {tuple(v) for v in p['enemy_coords']}
    living = [u for u in ids if energies[u] >= 0]
    expected_holder = {}
    for u in living:
        t = positions[u]
        if points[t[0]][t[1]]:
            expected_holder[t] = min(u, expected_holder.get(t, u))
    mobile = [u for u in ids if energies[u] >= p['move_cost'] and expected_holder.get(positions[u]) != u]
    expected_free = {(x, y) for x in range(w) for y in range(h)
                     if x + y <= w - 1 and points[x][y] and (x, y) not in occupied}
    free = {tuple(t['position']): t for t in frame['free_own_tiles']}
    checks.check(len(free) == len(frame['free_own_tiles']) and set(free) == expected_free,
                 'free field membership from raw public arrays', where)
    phase_state = state['free_start']
    for t in list(phase_state):
        if t not in free:
            del phase_state[t]
    phases = {}
    for t in free:
        start = phase_state.setdefault(t, index)
        phases[t] = (*game, key['match_idx'], *t, start)
        checks.check(free[t]['free_duration'] == index - start + 1, 'free duration', where + list(t))
    post = frame['posthoc']
    seen = state.setdefault('energy_seen', {})
    for x in range(w):
        for y in range(h):
            if p['sensor_mask'][x][y]:
                seen[x, y] = index
    age_ok = all(p['energy_observation_age'][x][y] ==
                 (index - seen[x, y] if (x, y) in seen else None)
                 for x in range(w) for y in range(h))
    checks.check(age_ok, 'energy freshness uses only real recorded sensor', where)
    checks.check(post.get('energy_phase_reconstruction') is None, 'energy phases explicitly unavailable', where)
    checks.check(post['transition_status'] in ('reset', 'unit_identity_continuity_unresolved'),
                 'transition continuity limit', where)
    before = post['before']
    enemy_truth = {tuple(t['position']) for t in post['enemies']}
    post_free = {tuple(t['position']): t for t in post['free_own_tiles']}
    checks.check(set(post_free) == set(free), 'posthoc free keys', where)
    graph = {}
    for t, row in free.items():
        phase = phases[t]
        checks.check(row['visible_enemy'] == (t in visible), 'visible enemy', where + list(t))
        checks.check(row['assigned_units'] == [u for u in ids if assigned.get(u) == t], 'assigned owners', where + list(t))
        paths = {u: path(grid, positions[u], t, units[u]['mask']) for u in living}
        def minimum(group):
            ds = [paths[u][0] for u in group if paths[u][0] is not None]
            return min(ds) if ds else None
        allowed = [u for u in mobile if paths[u][1]]
        checks.check(row['memory_passable'] == grid[t[0]][t[1]], 'memory passability', where + list(t))
        checks.check(row['min_bfs_living'] == minimum(living), 'min living BFS', where + list(t))
        checks.check(row['min_bfs_mobile_nonholders'] == minimum(mobile), 'min mobile nonholder BFS', where + list(t))
        checks.check(row['allowed_first_progress_units'] == allowed, 'first step supply', where + list(t))
        truth_row = post_free[t]
        checks.check(truth_row['true_point'] == bool(before['point_tiles'][t[0]][t[1]])
                     and truth_row['enemy_occupied'] == (t in enemy_truth)
                     and truth_row['hidden_enemy_occupied'] == (t in enemy_truth and t not in visible),
                     'truth-free decomposition', where + list(t))
        metrics.add('all_empty_belief_own_field_steps', game, phase=phase)
        if t in visible:
            metrics.add('visible_enemy_field_steps', game, phase=phase)
            continue
        metrics.add('agent_free_field_steps', game, phase=phase)
        graph[t] = allowed
        flags = {
            'untargeted': not row['assigned_units'],
            'not_true_point': not truth_row['true_point'],
            'hidden_enemy': truth_row['hidden_enemy_occupied'],
            'true_asteroid': bool(before['asteroid'][t[0]][t[1]]),
            'memory_impassable': not row['memory_passable'],
            'no_living_bfs': minimum(living) is None,
            'no_mobile_nonholder_bfs': minimum(mobile) is None,
            'no_allowed_first_step_supply': not allowed,
            'allowed_first_step_supply': bool(allowed),
            'untargeted_with_allowed_first_step_supply': not row['assigned_units'] and bool(allowed),
            'assigned_negative_unit': any(energies[u] < 0 for u in row['assigned_units']),
            'assigned_below_move_unit': any(0 <= energies[u] < p['move_cost'] for u in row['assigned_units']),
            'assigned_holder_elsewhere': any(expected_holder.get(positions[u]) == u and positions[u] != t
                                             for u in row['assigned_units']),
        }
        for name, active in flags.items():
            if active:
                metrics.add('agent_free_' + name + '_field_steps', game, phase=phase)
    metrics.add('first_step_capacity_maximum_sum', game, maximum_first_step_matching(graph))
    metrics.add('mobile_nonholder_supply_sum', game, len(mobile))
    for u, row in units.items():
        t = positions[u]
        checks.check(row['position'] == list(t) and row['energy'] == energies[u],
                     'unit position and energy from raw public arrays', where + [u])
        checks.check(len(row['features']) == 79 and all(v is not None and math.isfinite(v) for v in row['features']),
                     '79 finite retained actual features', where + [u])
        holder = expected_holder.get(t) == u
        living_stack = sum(energies[v] >= 0 for v in ids if positions[v] == t)
        checks.check(row['holder'] == holder and row['sole_holder'] == (holder and living_stack == 1),
                     'holder classification', where + [u])
        checks.check(row['mobile_nonholder'] == (u in mobile), 'mobile nonholder classification', where + [u])
        q = row['q_values']
        mask = row['mask']
        checks.check(len(q) == len(mask) == 6 and all(v is not None and math.isfinite(v) for v in q),
                     'finite Q[6]', where + [u])
        checks.check(set(row['mask_reasons']) == {str(a) for a in range(6) if not mask[a]},
                     'mask reasons cover exactly masked actions', where + [u])
        raw = argmax(q)
        masked = argmax([v if mask[a] else -math.inf for a, v in enumerate(q)])
        checks.check(row['raw_argmax'] == raw and row['masked_argmax'] == masked, 'Q argmax from raw Q', where + [u])
        native = frame['native_actions'][u]
        checks.check(row['native_action'] == native and row['final_action'] == canonical(native, game[1] == 'player_1'),
                     'native/canonical involution', where + [u])
        target = assigned.get(u)
        expected_class = None if target is None else ('known_point' if points[target[0]][target[1]]
                         else 'candidate' if p['candidate'][target[0]][target[1]] else 'exploration')
        expected_half = None if target is None else ('own' if sum(target) <= w - 1 else 'enemy')
        checks.check(row['target_class'] == expected_class and row['target_half'] == expected_half,
                     'target class and half from public maps', where + [u])
        dist, progress = path(grid, t, target, mask) if target is not None else (None, [])
        checks.check(row['assigned_target'] == (list(target) if target else None)
                     and row['target_bfs_distance'] == dist and row['allowed_target_progress'] == progress,
                     'target path from raw arrays', where + [u])
        ec = 'negative' if energies[u] < 0 else 'below_move_cost' if energies[u] < p['move_cost'] else 'below_sap_cost' if energies[u] < p['sap_cost'] else 'sap_ready'
        checks.check(row['energy_class'] == ec, 'energy class', where + [u])
        if holder:
            metrics.add('preaction_holder_unit_steps', game)
            if energies[u] < p['sap_cost']:
                tag = (key['match_idx'], u, *t)
                previous = state['low_start'].get(tag)
                start = previous[1] if previous and previous[0] == index - 1 else index
                state['low_start'][tag] = (index, start)
                metrics.add('preaction_holder_below_sap_unit_steps', game,
                            phase=(*game, *tag, start))
        if target is not None and sum(target) <= w - 1 and points[target[0]][target[1]] and dist and energies[u] >= 0:
            phase = phases.get(target)
            metrics.add('assigned_own_point_approach_unit_steps', game, phase=phase)
            final = row['final_action'][0]
            for name, active in {
                'legal_progress': bool(progress), 'raw_progress': raw in progress,
                'masked_progress': masked in progress, 'final_action_progress': final in progress,
                'raw_masked_out': not mask[raw], 'masked_changed_by_final': masked != final,
                'masked_stay_with_legal_progress': masked == 0 and bool(progress),
                'masked_sap_with_legal_progress': masked == 5 and bool(progress),
                'final_stay_with_legal_progress': final == 0 and bool(progress),
                'final_sap_with_legal_progress': final == 5 and bool(progress),
                'masked_progress_lost_in_final': masked in progress and final not in progress,
            }.items():
                if active:
                    metrics.add('approach_' + name + '_unit_steps', game, phase=phase)
    # Recompute every admitted pair; no policies, targets or actions are changed.
    cfg = p['config']
    admitted = cfg.get('reach_assign') is True and all(k in cfg and not cfg[k] for k in ('home_first', 'home_penalty', 'energy_pref', 'sticky'))
    swap = frame['two_owner_swap']
    eligible = [u for u in mobile if u in assigned and sum(assigned[u]) <= w - 1
                and points[assigned[u][0]][assigned[u][1]]]
    expected_swaps, pairs = [], 0
    if admitted:
        for i, u in enumerate(eligible):
            for v in eligible[i + 1:]:
                if pairs >= 120:
                    break
                pairs += 1
                a, b = assigned[u], assigned[v]
                if a == b:
                    continue
                four = [path(grid, positions[x], y, units[x]['mask']) for x, y in ((u, a), (v, b), (u, b), (v, a))]
                if any(d is None or not pr for d, pr in four):
                    continue
                old, new = four[0][0] + four[1][0], four[2][0] + four[3][0]
                if new < old:
                    expected_swaps.append(dict(units=[u, v], old_targets=[list(a), list(b)],
                                               new_targets=[list(b), list(a)], old_bfs_sum=old,
                                               new_bfs_sum=new, saved_bfs=old-new))
    checks.check(swap['admitted'] == admitted and swap['pairs_checked'] == pairs and swap['improvements'] == expected_swaps,
                 'all two-owner pair invariants', where)
    metrics.add('counterfactual_pair_opportunities', game, len(expected_swaps))
    metrics.add('counterfactual_pair_step_bfs_savings_sum_NOT_additive_policy_gain', game,
                sum(s['saved_bfs'] for s in expected_swaps))
    # Actual caller action, never Q argmax, proves the pre-artillery movement.
    events = frame['events']
    checks.check([e['order'] for e in events] == list(range(len(events))), 'event order', where)
    for e in events:
        if e.get('return_status') != 'returned':
            checks.check(False, 'wrapped method did not return', where + [e['order']])
        if e['method'] != '_artillery_ok' or e.get('return') is not True:
            continue
        if e.get('caller_action_status') != 'observed' or e.get('caller_action') not in (1, 2, 3, 4):
            continue
        u = e['uid']
        later = [x for x in events[e['order'] + 1:] if x['uid'] == u]
        over = next((x for x in later if x['method'] == '_overkill'), None)
        metrics.add('observed_move_artillery_ok_unit_steps', game)
        if (not cfg.get('art_still', False) and not cfg.get('end_sap', 0)
                and over and e['arguments'].get('sap') == over['arguments'].get('sap')
                and over.get('caller_action_status') == 'observed' and over.get('caller_action') == 5
                and over.get('return') is True and units[u]['final_action'][0] == 0):
            metrics.add('observed_move_artillery_overkill_final_stay_chains', game,
                        phase=phases.get(assigned.get(u)))
            state['chain_examples'].append(dict(key=key, uid=u, move=e['caller_action'],
                                                target=assigned.get(u), artillery_order=e['order'], overkill_order=over['order']))


def receipt_documents(paths, manifest, manifest_path, checks):
    records = []
    for p in paths:
        r = read_json(p)
        checks.check(r.get('status') == 'complete' and r.get('inputs_unchanged') is True
                     and r.get('exit_code') == 0 and r.get('planned_games') == 24,
                     'guard completed without input drift', str(p))
        checks.check(r.get('manifest_sha256') == sha(manifest_path), 'guard binds exact final manifest', str(p))
        identity = r.get('identity', {})
        source = identity.get('source', {})
        checks.check(source.get('head') == manifest['git_head'], 'guard and manifest source HEAD', str(p))
        checks.check(bool(source.get('files')) and bool(identity.get('weights')), 'guard full file identity present', str(p))
        frozen_files = {**source.get('files', {}), **identity.get('weights', {})}
        for path_name, digest in frozen_files.items():
            path = Path(path_name)
            checks.check(path.is_file() and sha(path) == digest, 'guard pinned input SHA', path_name)
        python = Path(source.get('python', '/nonexistent'))
        checks.check(python.is_file() and sha(python) == source.get('executable_sha256'),
                     'guard pinned Python executable', str(p))
        for name, digest in manifest['sources'].items():
            checks.check(frozen_files.get(name) == digest, 'guard covers manifest source', name)
        checks.check(frozen_files.get(manifest['weights']['path']) == manifest['weights']['sha256'],
                     'guard covers exact diagnostic V14 file', str(p))
        records.append(dict(path=str(p.resolve()), sha256=sha(p),
                            validation='explicit_guard_schema_checked', source_head=source.get('head'),
                            pinned_files=len(frozen_files), started_utc=r.get('started_utc'),
                            finished_utc=r.get('finished_utc')))
    checks.check(len(records) == 1, 'exactly one root guard receipt supplied')
    return records


def run(args):
    repo, run_dir = args.repo.resolve(), args.run.resolve()
    manifest_path = run_dir / 'manifest.json'
    manifest, keys = read_json(manifest_path), read_json(args.keys)
    checks = Checks()
    wanted = keys['keys']
    checks.check(len(wanted) == 12 and len({(k['seed'], k['side']) for k in wanted}) == 12, 'fixed twelve unique keys')
    checks.check(Counter(k['group'] for k in wanted) == {'loss': 6, 'control': 6}, 'six selected losses / six qualitative controls')
    checks.check(manifest['keys'] == wanted, 'manifest exact fixed keys and order')
    checks.check(manifest['status'] == 'complete' and manifest['completed_games'] == manifest['planned_games'] == 24, 'all 24 games complete')
    checks.check(manifest['keys_sha256'] == sha(args.keys), 'keys SHA')
    checks.check(manifest['weights']['sha256'] == V14_SHA == sha(manifest['weights']['path']), 'unchanged V14 weights SHA')
    expected_baseline = Path(keys['source'])
    if not expected_baseline.is_absolute():
        expected_baseline = repo / expected_baseline
    checks.check(Path(manifest['baseline']['path']).resolve() == expected_baseline.resolve(), 'original baseline path binding')
    checks.check(sha(manifest['baseline']['path']) == manifest['baseline']['sha256'], 'baseline SHA')
    with Path(manifest['baseline']['path']).open(newline='') as f:
        rows = [r for r in csv.DictReader(f) if r['opponent'] == 'solution92']
    baseline = {(int(r['seed']), r['side']): r for r in rows}
    expected_controls = [(int(r['seed']), r['side']) for r in rows if float(r['result']) == 1][:6]
    checks.check([(k['seed'], k['side']) for k in wanted if k['group'] == 'control'] == expected_controls,
                 'controls are exactly first six known wins in baseline order')
    for source, digest in manifest['sources'].items():
        checks.check(Path(source).is_file() and sha(source) == digest, 'current frozen source SHA', source)
        try:
            relative = Path(source).resolve().relative_to(repo)
        except ValueError:
            continue
        tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', str(relative)],
                                 cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        if tracked:
            content = subprocess.check_output(['git', 'show', manifest['git_head'] + ':' + str(relative)], cwd=repo)
            checks.check(hashlib.sha256(content).hexdigest() == digest, 'source matches declared git HEAD', str(relative))
    all_metrics = defaultdict(Metrics)
    summaries, total_frames = [], 0
    records = manifest['games']
    checks.check([r['key'] for r in records] == wanted, 'one record per fixed key')
    for record in records:
        key = record['key']
        game = (key['seed'], key['side'])
        a, b = record['unobserved'], record['observed']
        for field in COMPARE:
            checks.check(a[field] == b[field], 'independent passivity ' + field, game)
            checks.check(record['passivity'].get(field) is True, 'stored passivity ' + field, game)
        for result in (a, b):
            checks.check((result['seed'], result['side'], result['opponent']) == (*game, 'solution92'), 'result exact key and opponent', game)
            checks.check(len(result['action_sha256']) == 64 and all(c in '0123456789abcdef' for c in result['action_sha256']),
                         'native action SHA format', game)
            checks.check(result['steps'] == 303 and result['reset_steps'] == 3 and result['decision_steps'] == 300
                         and result['point_counting_version'] == 2 and len(result['matches']) == 3
                         and result['caught_errors'] == 0, '303 / v2 / no caught errors', game)
            for field in BASELINE:
                checks.check(float(result[field]) == float(baseline[game][field]), 'original baseline ' + field, game)
        checks.check(b['statuses'] == {'decision': 300, 'reset': 3}, 'stored frame statuses', game)
        team = int(game[1][-1])
        for result in (a, b):
            totals = [sum(m['points'][t] for m in result['matches']) for t in (0, 1)]
            checks.check(totals[team] == result['our_points'] and totals[1-team] == result['opp_points'],
                         'v2 match totals reproduce game totals', game)
            checks.check(result['matches'][-1]['cumulative_wins'][team] == result['our_wins']
                         and result['matches'][-1]['cumulative_wins'][1-team] == result['opp_wins'],
                         'final cumulative match wins', game)
        trace = run_dir / record['trace']['path']
        checks.check(record['trace']['path'] == f'{game[0]}_{game[1]}.jsonl.gz' and not trace.is_symlink(),
                     'one native named trace per fixed key', game)
        checks.check(sha(trace) == record['trace']['sha256'], 'compressed trace SHA', game)
        metrics, state = Metrics(), dict(free_start={}, low_start={}, chain_examples=[])
        statuses = Counter()
        count = 0
        with gzip.open(trace, 'rt') as f:
            for index, line in enumerate(f):
                frame = json.loads(line, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                statuses[frame['status']] += 1
                audit_frame(frame, game, index, checks, metrics, state)
                count += 1
        checks.check(count == 303 and statuses == Counter(decision=300, reset=3), 'raw trace has exactly 303 frames', game)
        total_frames += count
        exported = metrics.export()
        summaries.append(dict(key=key, frames=count, metrics=exported, chain_examples=state['chain_examples'][:20]))
        for name, r in metrics.rows.items():
            for cohort in ('all', key['group']):
                dest = all_metrics[cohort].rows.setdefault(name, dict(count=0, games=set(), maps=set(), phases=set()))
                dest['count'] += r['count']
                for field in ('games', 'maps', 'phases'):
                    dest[field].update(r[field])
    checks.check(total_frames == 12 * 303, 'all 3636 raw frames')
    receipts = receipt_documents(args.receipt, manifest, manifest_path, checks)
    output = dict(status='FAIL' if checks.failure_total else 'PASS',
                  checks=checks.total, failure_total=checks.failure_total, failures=checks.failures,
                  manifest=dict(path=str(manifest_path), sha256=sha(manifest_path), git_head=manifest['git_head']),
                  receipts=receipts, explicitly_simulated_games=24, traced_games=12, raw_frames=total_frames,
                  cohorts={k: v.export() for k, v in all_metrics.items()}, games=summaries,
                  limitations=[
                      'Selected six losses and first six wins are qualitative, not representative or matched controls.',
                      'Field phases mean consecutive own-empty known-point observations; a condition may occur only during part of a phase.',
                      'Holder low-energy phases are pre-action observations, not the old post-move/pre-sap metric and not identity-verified life histories.',
                      'No energy phase reconstruction or whole-route energy/safe-arrival proof exists in these traces.',
                      'Stored Q values are ensemble aggregates; per-network outputs are not retained for independent re-averaging.',
                      'Full action SHA includes both teams and native shape/dtype; opponent action arrays are not retained, so SHA is compared across runs, not rebuilt from trace.',
                      'Pair opportunities and saved BFS sums overlap and are not additive realizable gain or strength evidence.',
                      'Guard identity is independently rehashed against current frozen inputs; no model is imported.' ])
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'targeting_audit.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(dict(status=output['status'], checks=checks.total, failures=checks.failure_total, frames=total_frames)))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--keys', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, action='append', default=[])
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run(args)


if __name__ == '__main__':
    main()
