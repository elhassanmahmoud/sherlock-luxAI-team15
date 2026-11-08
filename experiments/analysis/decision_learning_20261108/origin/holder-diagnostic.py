"""Read existing targeting traces; no imports of agent/engine/model code."""
import collections
import gzip
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
TRACE = ROOT / 'experiments/analysis/continuation_20261102/targeting'
CONTROL = {831000, 831001, 831002}
DXY = {1: (0, -1), 2: (1, 0), 3: (0, 1), 4: (-1, 0)}
records = []
sources = []
holder_steps = collections.Counter()

for path in sorted(TRACE.glob('*.jsonl.gz')):
    sources.append({'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    with gzip.open(path, 'rt') as handle:
        frames = [json.loads(line) for line in handle]
    for index, frame in enumerate(frames):
        if frame['status'] != 'decision':
            continue
        public = frame['public']
        group = 'control' if frame['key']['seed'] in CONTROL else 'loss'
        for unit in frame['units']:
            if not unit['sole_holder'] or unit['energy'] < 0:
                continue
            holder_steps[group] += 1
            action = unit['final_action'][0]
            if action not in DXY:
                continue
            x, y = unit['position']
            dx, dy = DXY[action]
            tx, ty = x + dx, y + dy
            if unit['assigned_target'] != [x, y] or public['point_tiles'][tx][ty]:
                continue
            near = [i for i, (ex, ey) in enumerate(public['enemy_coords'])
                    if max(abs(ex - x), abs(ey - y)) <= public['sap_range'] + 1]
            live_near = [i for i in near if public['enemy_energies'][i] >= 0]
            armed_near = [i for i in near if public['enemy_energies'][i] >= public['sap_cost']]
            vacancy = 0
            observed_next = False
            ended_by_return = False
            following = []
            for nxt in frames[index + 1:]:
                if nxt['key']['match_idx'] != frame['key']['match_idx'] or nxt['status'] != 'decision':
                    break
                observed_next = True
                occupied = any(v['position'] == [x, y] and v['energy'] >= 0 for v in nxt['units'])
                if occupied:
                    ended_by_return = True
                    break
                vacancy += 1
                following.append(nxt['key']['obs_step'])
            current_e, dest_e = public['energy_map'][x][y], public['energy_map'][tx][ty]
            remaining = public['max_match_steps'] - public['match_step']
            r = {
                'group': group, 'file': path.name, **frame['key'], 'uid': unit['uid'],
                'position': [x, y], 'destination': [tx, ty], 'energy': unit['energy'],
                'move_cost': public['move_cost'], 'sap_cost': public['sap_cost'],
                'sap_range': public['sap_range'], 'current_tile_energy': current_e,
                'destination_tile_energy': dest_e, 'destination_energy_minus_current': dest_e-current_e,
                'current_nebula': bool(public['nebula'][x][y]),
                'destination_nebula': bool(public['nebula'][tx][ty]),
                'current_energy_observation_age': public['energy_observation_age'][x][y],
                'destination_energy_observation_age': public['energy_observation_age'][tx][ty],
                'current_visible': bool(public['sensor_mask'][x][y]),
                'destination_visible': bool(public['sensor_mask'][tx][ty]),
                'visible_enemy_near': len(near), 'nonnegative_visible_enemy_near': len(live_near),
                'armed_visible_enemy_near': len(armed_near),
                'energy_ge_move_plus_sap': unit['energy'] >= public['move_cost'] + public['sap_cost'],
                'remaining_match_steps': remaining, 'remaining_ge_12': remaining >= 12,
                'action': action, 'masked_argmax': unit['masked_argmax'], 'stay_legal': unit['mask'][0],
                'q_stay_minus_move': unit['q_values'][0] - unit['q_values'][action],
                'observed_next_same_match': observed_next,
                'consecutive_vacant_observations': vacancy,
                'vacancy_right_censored': observed_next and not ended_by_return,
                'reoccupied_observed': ended_by_return,
            }
            # This is an observable screening condition, NOT a claim of safety.
            r['screen'] = (r['energy_ge_move_plus_sap'] and r['remaining_ge_12']
                           and not near and not r['current_nebula']
                           and current_e >= 0 and r['stay_legal'])
            r['screen_without_visible_threat_filter'] = (r['energy_ge_move_plus_sap']
                and r['remaining_ge_12'] and not r['current_nebula'] and current_e >= 0
                and r['stay_legal'])
            records.append(r)

def numeric(rows, key):
    vals = sorted(r[key] for r in rows)
    if not vals:
        return None
    return {'min': vals[0], 'median': statistics.median(vals),
            'mean': statistics.mean(vals), 'max': vals[-1]}

def summary(rows):
    filters = {
        'current_energy_negative': lambda r:r['current_tile_energy'] < 0,
        'current_energy_zero': lambda r:r['current_tile_energy'] == 0,
        'current_energy_positive': lambda r:r['current_tile_energy'] > 0,
        'destination_energy_negative': lambda r:r['destination_tile_energy'] < 0,
        'destination_energy_zero': lambda r:r['destination_tile_energy'] == 0,
        'destination_energy_positive': lambda r:r['destination_tile_energy'] > 0,
        'destination_higher_energy': lambda r:r['destination_energy_minus_current'] > 0,
        'destination_same_energy': lambda r:r['destination_energy_minus_current'] == 0,
        'destination_lower_energy': lambda r:r['destination_energy_minus_current'] < 0,
        'current_nebula': lambda r:r['current_nebula'],
        'destination_nebula': lambda r:r['destination_nebula'],
        'any_visible_enemy_near': lambda r:r['visible_enemy_near'] > 0,
        'any_nonnegative_visible_enemy_near': lambda r:r['nonnegative_visible_enemy_near'] > 0,
        'any_armed_visible_enemy_near': lambda r:r['armed_visible_enemy_near'] > 0,
        'energy_ge_move_plus_sap': lambda r:r['energy_ge_move_plus_sap'],
        'remaining_ge_12': lambda r:r['remaining_ge_12'],
        'energy_and_remaining': lambda r:r['energy_ge_move_plus_sap'] and r['remaining_ge_12'],
        'screen_without_visible_threat_filter': lambda r:r['screen_without_visible_threat_filter'],
        'screen': lambda r:r['screen'],
        'next_observation_vacant': lambda r:r['consecutive_vacant_observations'] > 0,
        'vacancy_ge_3': lambda r:r['consecutive_vacant_observations'] >= 3,
        'vacancy_ge_5': lambda r:r['consecutive_vacant_observations'] >= 5,
        'vacancy_right_censored': lambda r:r['vacancy_right_censored'],
    }
    return {'n': len(rows), 'files': dict(collections.Counter(r['file'] for r in rows)),
            'counts': {name: sum(bool(fn(r)) for r in rows) for name, fn in filters.items()},
            'numeric': {key: numeric(rows,key) for key in ('energy','current_tile_energy',
                'destination_tile_energy','remaining_match_steps','q_stay_minus_move',
                'consecutive_vacant_observations')}}

report = {'method': 'Pure observation from historical traces; no model/engine execution. '
          'All departures are sole living holders moving off their assigned known point to a nonpoint. '
          'Vacancy counts consecutive following pre-action observations without nonnegative ally at origin, '
          'stopping at reoccupation or match/reset boundary. Overlapping vacancy windows are not independent. '
          'No enemy within Chebyshev sap_range+1 means no observed enemy, not no hidden threat.',
          'sources': sources, 'holder_steps': dict(holder_steps),
          'summary': {g: summary([r for r in records if r['group']==g]) for g in ('loss','control')},
          'screen_summary': {g: summary([r for r in records if r['group']==g and r['screen']])
                             for g in ('loss','control')},
          'records': records}
Path('/tmp/sherlock-holder-diagnostic.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({k: report[k] for k in ('holder_steps','summary','screen_summary')}, indent=2))
