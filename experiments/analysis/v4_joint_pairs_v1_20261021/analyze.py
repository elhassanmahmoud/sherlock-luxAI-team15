"""Fixed development analysis: actual wins for opponents, result for direct."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scripts.compare_report import compare_results, validated_results

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
state = json.loads((OUT / 'state.json').read_text())
assert state['active'] is None
assert all(j['returncode'] == 0 and j['verified_inputs_after'] for j in state['jobs'])
assert state['remaining_games'] == 0
for path, expected in {**state['source_hashes'], **state['protected_hashes'],
                       state['candidate']: state['candidate_sha256'],
                       state['baseline_csv']: state['baseline_csv_sha256']}.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path

paths = {'candidate': OUT / 'development_opponents.csv',
         'reference': Path(state['baseline_csv']),
         'direct': OUT / 'development_direct.csv'}
frames = {k: pd.read_csv(p) for k, p in paths.items()}
for label, df in frames.items():
    validated_results(df, label)
    assert set(df.seed) == set(range(500720, 500780))
    assert set(df.side) == {'player_0', 'player_1'}
    assert set(df.point_counting_version) == {2}
    assert df.invalid_frac.max() == 0
    assert set(df.steps) == {303}
assert set(frames['candidate'].opponent) == set(frames['reference'].opponent) == {'default', 'solution92'}
assert len(frames['candidate']) == len(frames['reference']) == 240
assert len(frames['direct']) == 120 and frames['direct'].opponent.nunique() == 1

def counts(df):
    return {name: int((df.result == value).sum())
            for name, value in [('wins', 1), ('draws', .5), ('losses', 0)]}

winframes = {k: frames[k].assign(result=(frames[k].result == 1).astype(float))
             for k in ('candidate', 'reference')}
comparison = compare_results(winframes['candidate'], winframes['reference'])
for row in comparison:
    for label in ('candidate', 'reference'):
        df = frames[label]
        row[label + '_counts'] = counts(df[df.opponent == row['opponent']])
direct = frames['direct'].groupby('seed', sort=True).result.mean().to_numpy()
boot = np.random.default_rng(0).choice(direct, size=(5000, len(direct))).mean(axis=1)
direct_summary = {**counts(frames['direct']), 'mean_result': float(direct.mean()),
                  'cards': len(direct), 'games': len(frames['direct']),
                  'low': float(np.percentile(boot, 2.5)), 'high': float(np.percentile(boot, 97.5))}
sol = next(r for r in comparison if r['opponent'] == 'solution92')
default = next(r for r in comparison if r['opponent'] == 'default')
gates = {'solution_at_least_108_wins': sol['candidate_counts']['wins'] >= 108,
         'default_120_wins': default['candidate_counts']['wins'] == 120,
         'direct_result_at_least_half': direct_summary['mean_result'] >= .5}
report = {'scope': 'known development cards; no fresh confirmation or training',
          'source_head': state['head'], 'input_hashes': {
              k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()},
          'bootstrap': '5000 complete card-pair resamples; numpy default_rng(0); percentile 95%',
          'opponents_actual_win_indicators': comparison, 'direct_result': direct_summary,
          'development_gates': gates, 'advance_to_fresh': all(gates.values()),
          'new_games': 392, 'reused_reference_games': 240,
          'protected_hashes_verified': True}
dest = OUT / 'results.json'
assert not dest.exists()
dest.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
