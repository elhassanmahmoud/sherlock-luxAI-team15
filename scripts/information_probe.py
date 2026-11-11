"""Bounded public-only field-probe opportunity audit. No models or engine imports."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
from dataclasses import asdict, dataclass, field
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import subprocess

Tile = tuple[int, int]
DIRECTIONS = ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0))
PUBLIC_FIELDS = ('W', 'H', 'step', 'match_idx', 'match_step', 'own_points',
                 'ally_ids', 'ally_pos', 'ally_ene', 'point_tiles', 'candidate',
                 'sensor_mask', 'passable', 'nebula', 'enemy_coords',
                 'move_cost', 'sap_range', 'assigned')
MANIFEST_SHA = '90324b008945da4a054a0559a108ee0023cf572d754b20af844160dfe4ebc435'
KEYS = ((831006, 'player_1'), (831029, 'player_0'),
        (831042, 'player_0'), (831042, 'player_1'),
        (831043, 'player_0'), (831043, 'player_1'),
        (831000, 'player_0'), (831000, 'player_1'),
        (831001, 'player_0'), (831001, 'player_1'),
        (831002, 'player_0'), (831002, 'player_1'))


@dataclass(frozen=True)
class PublicEquation:
    # Raw public occupancy and total gain; normalize against current facts later.
    tiles: tuple[Tile, ...]
    residual: int
    observed_step: int


@dataclass
class PublicHistory:
    match_idx: int | None = None
    records: list[PublicEquation] = field(default_factory=list)
    zeros: set[Tile] = field(default_factory=set)
    contradictions: int = 0


def _tiles(matrix):
    return {(x, y) for x, column in enumerate(matrix) for y, v in enumerate(column) if v}


def _occupied(p):
    return {tuple(map(int, p['ally_pos'][u])) for u in p['ally_ids']
            if p['ally_ene'][u] >= 0 and 0 <= p['ally_pos'][u][0] < p['W']
            and 0 <= p['ally_pos'][u][1] < p['H']}


def _normalized(record, points, zeros):
    tiles = set(record.tiles)
    unknown = tiles - points - zeros
    residual = record.residual - len(tiles & points)
    if not 0 <= residual <= len(unknown):
        raise ValueError('contradictory public equation')
    return unknown, residual


def advance_public_history(previous, current, history):
    """Consume only consecutive public frames; discard pre-spawn zero knowledge."""
    mi, ms = current['match_idx'], current['match_step']
    if history.match_idx != mi or ms < 50:
        history = PublicHistory(mi, contradictions=history.contradictions)
    if (mi != 0 or ms < 50 or previous is None or previous['match_idx'] != mi
            or current['step'] != previous['step'] + 1
            or ms != previous['match_step'] + 1):
        return PublicHistory(mi, contradictions=history.contradictions)
    gain = current['own_points'] - previous['own_points']
    if not isinstance(gain, (int, float)) or int(gain) != gain:
        raise ValueError('nonintegral public score')
    record = PublicEquation(tuple(sorted(_occupied(current))), int(gain), current['step'])
    points = _tiles(current['point_tiles'])
    try:
        if history.zeros & points:
            raise ValueError('old zero conflicts with current public point')
        records = (history.records + [record])[-400:]
        zeros = set(history.zeros)
        while True:
            extra = set()
            equations = [_normalized(old, points, zeros) for old in records]
            for (a, ra), (b, rb) in itertools.combinations(equations, 2):
                # Necessary feasibility of every pair, including equal/subsets.
                # This is a consistency guard, not a complete binary SAT solver.
                if not -len(b-a) <= ra-rb <= len(a-b):
                    raise ValueError('mutually contradictory public equations')
            for unknown, residual in equations:
                if residual == 0:
                    extra.update(unknown)
            extra -= zeros
            if not extra:
                break
            zeros.update(extra)
        return PublicHistory(mi, records, zeros, history.contradictions)
    except ValueError:
        # Do not salvage the current observation using hidden map facts.
        return PublicHistory(mi, contradictions=history.contradictions + 1)


def _distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def choose_probe(public, ids, masks, greedy, history, *, stats=None):
    """At most two non-holder moves; return the first deterministic public proof."""
    stats = stats if stats is not None else {}
    stats.update(enumerated=0, eligible=0, reason='no_proof')
    p = public
    if any(p.get(k) is None for k in PUBLIC_FIELDS):
        stats['reason'] = 'missing_public_field'; return None
    if p['match_idx'] != 0 or not 50 <= p['match_step'] <= 80:
        stats['reason'] = 'outside_window'; return None
    if history.match_idx != 0 or not history.records:
        stats['reason'] = 'no_stable_equation'; return None
    if ids != p['ally_ids'] or len(ids) != len(masks) or len(ids) != len(greedy):
        raise ValueError('unit order/shape mismatch')
    points = _tiles(p['point_tiles']); zeros = history.zeros
    candidates = _tiles(p['candidate']) - points - zeros
    if not candidates:
        stats['reason'] = 'no_unknown_candidate'; return None
    if p['move_cost'] < 0 or p['sap_range'] < 0:
        stats['reason'] = 'invalid_cost_or_range'; return None
    rows = {u: i for i, u in enumerate(ids)}
    positions = {u: tuple(p['ally_pos'][u]) for u in ids}

    def destination(u, action):
        x, y = positions[u]
        dx, dy = DIRECTIONS[action] if action < 5 else (0, 0)
        return x + dx, y + dy

    def project(actions):
        occupied = set()
        for u, action in zip(ids, actions):
            i = rows[u]
            if not 0 <= action < len(masks[i]) or not masks[i][action]:
                return None
            if p['ally_ene'][u] < 0:
                continue
            x, y = destination(u, action)
            if not (0 <= x < p['W'] and 0 <= y < p['H']):
                return None
            occupied.add((x, y))
        return occupied

    def informative(occupied):
        unknown = occupied - points - zeros
        proofs = {}
        for equation in history.records:
            old, residual = _normalized(equation, points, zeros)
            difference = old ^ unknown
            if len(difference) == 1:
                x = next(iter(difference))
                if x in candidates:
                    proofs.setdefault(x, (equation, old, residual, unknown))
        return proofs

    base_occupied = project(greedy)
    if base_occupied is None:
        stats['reason'] = 'invalid_original_projection'; return None
    try:
        already = informative(base_occupied)
    except ValueError:
        stats['reason'] = 'inconsistent_history'; return None
    eligible = [u for u in ids if p['ally_ene'][u] >= 0
                and positions[u] not in points and 0 <= greedy[rows[u]] < 5]
    eligible.sort(key=lambda u: (min(_distance(positions[u], x) for x in candidates), u))
    eligible = eligible[:4]
    options = {}
    for u in eligible:
        target = p['assigned'].get(str(u), p['assigned'].get(u))
        if target is None or len(target) != 2 or p['ally_ene'][u] < 2 * p['move_cost']:
            continue
        allowed = []
        for action in range(5):
            if action == greedy[rows[u]] or action >= len(masks[rows[u]]) or not masks[rows[u]][action]:
                continue
            safe = True
            for x, y in (positions[u], destination(u, action)):
                if not (0 <= x < p['W'] and 0 <= y < p['H']):
                    safe = False; break
                if not p['sensor_mask'][x][y] or not p['passable'][x][y] or p['nebula'][x][y]:
                    safe = False; break
                if any(max(abs(x-ex), abs(y-ey)) <= p['sap_range'] + 1
                       for ex, ey in p['enemy_coords']):
                    safe = False; break
            if safe:
                allowed.append(action)
        if allowed:
            options[u] = allowed
    stats['eligible'] = len(options)
    if not options:
        stats['reason'] = 'no_safe_alternative'; return None
    stats['enumerated'] = 1
    proposals = []
    for count in (1, 2):
        for units in itertools.combinations(sorted(options), count):
            for actions in itertools.product(*(options[u] for u in units)):
                stats['enumerated'] += 1
                altered = list(greedy)
                for u, a in zip(units, actions): altered[rows[u]] = a
                occupied = project(altered)
                if occupied is None: continue
                for x, (old, old_unknown, residual, unknown) in informative(occupied).items():
                    if x in already: continue
                    distance_delta = 0
                    for u, a in zip(units, actions):
                        target = p['assigned'].get(str(u), p['assigned'].get(u))
                        distance_delta += (_distance(destination(u, a), target)
                                           - _distance(destination(u, greedy[rows[u]]), target))
                    key = (count, distance_delta, x, units, actions)
                    proposal = dict(x=list(x), changes=[[u, a] for u, a in zip(units, actions)],
                                    original_greedy=list(greedy), proposed_greedy=altered,
                                    previous_equation=asdict(old), previous_unknown=sorted(old_unknown),
                                    previous_residual=residual, projected_unknown=sorted(unknown),
                                    projected_known_points=sorted(occupied & points),
                                    known_zeros=sorted(zeros), step=p['step'], match_step=p['match_step'],
                                    reason='singleton_difference_not_available_in_original_projection')
                    proposals.append((key, proposal))
    assert stats['enumerated'] <= 113
    if not proposals: return None
    stats['reason'] = 'public_proof'
    # Normalize tuples into JSON-compatible lists also for direct callers.
    return json.loads(json.dumps(min(proposals, key=lambda item: item[0])[1]))


def public_frame(row):
    p = {k: row['public'].get(k) for k in PUBLIC_FIELDS}
    ids = list(p['ally_ids'])
    units = {u['uid']: u for u in row['units']}
    if len(units) != len(ids) or set(units) != set(ids):
        raise ValueError('archive unit identity mismatch')
    masks = [units[u]['mask'] for u in ids]
    greedy = [units[u]['masked_argmax'] for u in ids]
    return p, ids, masks, greedy


def scan_frames(frames):
    history = PublicHistory(); previous = None; first = None; audit = []
    for row in frames:
        if row['status'] == 'reset':
            previous = None; history = PublicHistory(); continue
        if row['status'] != 'decision':
            raise ValueError('unusable archive frame: ' + row['status'])
        p, ids, masks, greedy = public_frame(row)
        if p['match_idx'] != 0: break
        history = advance_public_history(previous, p, history)
        previous = p
        if not 50 <= p['match_step'] <= 80: continue
        stats = {}
        proposal = choose_probe(p, ids, masks, greedy, history, stats=stats)
        audit.append(dict(step=p['step'], match_step=p['match_step'], stats=stats,
                          records=len(history.records), zeros=len(history.zeros),
                          contradictions=history.contradictions,
                          proposal=proposal if first is None else None))
        if first is None and proposal is not None: first = proposal
        # One first proposal per game; do not search for a better later event.
        if first is not None: break
    return dict(first=first, frames=audit)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def validate_archive_manifest(manifest, root):
    """Verify historic bytes/configuration; this does not certify live parity."""
    manifest, root = Path(manifest), Path(root)
    if sha256(manifest) != MANIFEST_SHA: raise ValueError('manifest identity mismatch')
    data = json.loads(manifest.read_text())
    if tuple((k['seed'], k['side']) for k in data['keys']) != KEYS:
        raise ValueError('wrong input set')
    if data['status'] != 'complete' or data['completed_games'] != 24 or len(data['games']) != 12:
        raise ValueError('incomplete source collection')
    checks = {}
    def bind(label, path, expected):
        actual = sha256(path)
        if actual != expected: raise ValueError('input hash mismatch: ' + label)
        checks[label] = dict(path=str(path), sha256=actual)
    for side in (0, 1):
        bind(f'weights_p{side}', root/f'agents/sherlock/weights/agent_p{side}.pth', data['weights']['sha256'])
    baseline = root/'experiments/analysis/night_20261101/selection_baseline.csv'
    bind('baseline', baseline, data['baseline']['sha256'])
    bind('keys', manifest.parent.parent/'diagnostic_keys.json', data['keys_sha256'])
    historical_root = '/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics/'
    source_differences = []
    for source, expected in data['sources'].items():
        if source.startswith(historical_root):
            relative = source[len(historical_root):]
            blob = subprocess.check_output(['git', 'show', data['git_head']+':'+relative], cwd=root)
            actual = hashlib.sha256(blob).hexdigest()
            if actual != expected: raise ValueError('historic source mismatch: '+relative)
            checks['source:'+relative] = dict(commit=data['git_head'], sha256=actual)
            if sha256(root/relative) != expected: source_differences.append(relative)
        else:
            bind('engine', Path(source), expected)
    with baseline.open(newline='') as f:
        baseline_rows = {(int(r['seed']), r['side']):r for r in csv.DictReader(f) if r['opponent']=='solution92'}
    historical_config = data['games'][0]['observed']['config']
    passivity_checks = baseline_checks = 0
    for key, game in zip(data['keys'], data['games']):
        if game['key'] != key or not game['complete']: raise ValueError('wrong source game order')
        bind('trace:'+game['trace']['path'], manifest.parent/game['trace']['path'], game['trace']['sha256'])
        observed, unobserved = game['observed'], game['unobserved']
        for field_name, status in game['passivity'].items():
            if not status or observed[field_name] != unobserved[field_name]:
                raise ValueError('historic passivity failed: '+field_name)
            passivity_checks += 1
        if observed['caught_errors'] or observed['config'] != historical_config:
            raise ValueError('historic config/errors mismatch')
        row = baseline_rows[(key['seed'], key['side'])]
        for field_name, status in game['baseline_reproduction'].items():
            if not status or float(row[field_name]) != observed[field_name]:
                raise ValueError('historic baseline mismatch: '+field_name)
            baseline_checks += 1
    tree = ast.parse((root/'agents/sherlock/config.py').read_text())
    cfg = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name=='AgentConfig')
    defaults = {n.target.id:ast.literal_eval(n.value) for n in cfg.body if isinstance(n, ast.AnnAssign)}
    missing = set(defaults)-set(historical_config)
    expected_missing = {'art_move_guard','art_splash_in_training','cand_stall_rescue',
                        'rescue_in_training','zone_rescue','point_pair_swap','fog_unknown_reward_neutral'}
    if missing != expected_missing or any(defaults[k] is not False for k in missing):
        raise ValueError('unreconciled new config fields')
    if set(historical_config)-set(defaults): raise ValueError('removed historical config field')
    return dict(bound_inputs=checks, historical_source=data['git_head'],
                current_source_differences=source_differences,
                explicit_inactive_config_additions={k:False for k in sorted(missing)},
                passivity_checks=passivity_checks, baseline_checks=baseline_checks,
                live_equivalence_verified=False)


def audit_archived_traces(manifest, output):
    manifest, output = Path(manifest), Path(output)
    root = Path(__file__).resolve().parents[1]
    provenance = validate_archive_manifest(manifest, root)
    data = json.loads(manifest.read_text())
    keys = [(k['seed'], k['side']) for k in data['keys']]
    if tuple(keys) != KEYS or data['status'] != 'complete': raise ValueError('wrong input set')
    output.mkdir(parents=True, exist_ok=False)
    reports = []
    for key in data['keys']:
        path = manifest.parent / f"{key['seed']}_{key['side']}.jsonl.gz"
        with gzip.open(path, 'rt') as f: frames = [json.loads(line) for line in f]
        if len(frames) != 303: raise ValueError('incomplete archive')
        report = scan_frames(frames)
        report.update(key=key, input_path=str(path), input_sha256=sha256(path))
        reports.append(report)
    positives = [r for r in reports if r['first'] is not None]
    maps = {r['key']['seed'] for r in positives}
    groups = {r['key']['group'] for r in positives}
    gates = dict(six_keys=len(positives) >= 6, three_maps=len(maps) >= 3,
                 loss_and_control=groups == {'loss', 'control'})
    reasons = Counter(frame['stats']['reason'] for r in reports for frame in r['frames'])
    result = dict(schema_version=1, manifest_sha256=MANIFEST_SHA, new_games=0, updates=0,
                  keys=len(reports), qualifying_keys=len(positives), qualifying_maps=len(maps),
                  gates=gates, passed=all(gates.values()), reasons=dict(reasons), reports=reports,
                  provenance=provenance, auditor_sha256=sha256(Path(__file__)))
    (output/'audit.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = audit_archived_traces(args.manifest, args.output)
    print(json.dumps({k:v for k,v in report.items() if k != 'reports'}, indent=2))
