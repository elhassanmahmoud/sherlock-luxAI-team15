"""Read complete fixed CSV pairs; validate every key before statistical gates."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

FIELDS = 'seed side opponent result game_win point_win our_wins opp_wins our_points opp_points point_counting_version wait_frac invalid_frac greedy_masked_frac sap_attempts sap_hits stack_frac relics_found relics_seen known_point_tiles belief_contradictions unit_steps steps secs'.split()
SIDES = ('player_0', 'player_1')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path, first, n, opponents):
    with path.open(newline='') as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == FIELDS, (path, reader.fieldnames)
        rows = list(reader)
    expected = {(o, s, p) for o in opponents for s in range(first, first+n) for p in SIDES}
    indexed = {}
    for row in rows:
        values = {k: float(v) for k, v in row.items() if k not in ('side', 'opponent')}
        assert all(math.isfinite(v) for v in values.values()), row
        assert values['seed'].is_integer()
        key = row['opponent'], int(row['seed']), row['side']
        assert key in expected and key not in indexed, key
        a, b = values['our_wins'], values['opp_wins']
        assert a.is_integer() and b.is_integer() and 0 <= a <= 3 and 0 <= b <= 3 and a+b <= 3
        result = 1.0 if a > b else (0.5 if a == b else 0.0)
        assert values['result'] == result and values['game_win'] == int(result == 1.0)
        a, b = values['our_points'], values['opp_points']
        assert a >= 0 and b >= 0 and a.is_integer() and b.is_integer()
        assert values['point_win'] == (1.0 if a>b else (0.5 if a==b else 0.0))
        assert values['steps'] == 303 and values['point_counting_version'] == 2
        for k in ('wait_frac', 'invalid_frac', 'greedy_masked_frac', 'stack_frac'):
            assert 0 <= values[k] <= 1, (key, k)
        for k in ('sap_attempts', 'sap_hits', 'relics_found', 'relics_seen', 'known_point_tiles', 'belief_contradictions', 'unit_steps'):
            assert values[k] >= 0 and values[k].is_integer(), (key, k)
        assert values['secs'] >= 0
        indexed[key] = int(2 * result)
    assert set(indexed) == expected and len(rows) == len(expected), path
    return indexed

def totals(units):
    return dict(wins=units.count(2), draws=units.count(1), losses=units.count(0),
                half_score_units=sum(units), score=sum(units)/(2*len(units)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('folder', type=Path)
    ap.add_argument('phase', choices=['selection_default', 'confirmation'])
    args = ap.parse_args()
    out, phase = args.folder, args.phase
    journal = json.loads((out / f'{phase}_state.json').read_text())
    assert journal['status'] == 'complete' and len(journal['jobs']) == 2
    assert journal['phase_sha256'] == digest(out / f'{phase}_jobs.json')
    if phase == 'selection_default':
        first, n, opponents = 610100, 200, ['default']
        paths = [out/f'selection_{v}_default.csv' for v in ('baseline','recovery')]
    else:
        first, n, opponents = 611000, 800, ['default', 'solution92']
        paths = [out/f'confirmation_{v}.csv' for v in ('baseline','recovery')]
    for record, path in zip(journal['jobs'], paths):
        assert record['exit_code'] == 0 and record['output_sha256'] == digest(path)
        cmd = record['command']
        assert Path(cmd[cmd.index('--out')+1]) == path.resolve()
    ref, cand = [read(p, first, n, opponents) for p in paths]
    result = dict(phase=phase, audited_at=datetime.now(timezone.utc).isoformat(),
                  nominee='recovery', files={p.name:digest(p) for p in paths}, opponents={})
    for opp in opponents:
        r = [ref[(opp,s,p)] for s in range(first,first+n) for p in SIDES]
        c = [cand[(opp,s,p)] for s in range(first,first+n) for p in SIDES]
        differences = (np.array(c).reshape(n,2).sum(axis=1)-np.array(r).reshape(n,2).sum(axis=1))/4
        draws = np.random.default_rng(0).choice(differences,size=(5000,n),replace=True)
        lo, hi = map(float,np.percentile(draws.mean(axis=1),[2.5,97.5]))
        delta_units = sum(c)-sum(r)
        denom = 4*n
        passed = ((sum(c)*100 >= 99*denom and delta_units*100 >= -denom)
                  if opp == 'default' else (delta_units*100 >= 2*denom and lo > 0))
        result['opponents'][opp] = dict(maps=n,games_per_arm=2*n,baseline=totals(r),
            recovery=totals(c),delta_units=delta_units,denominator=denom,
            delta=delta_units/denom,ci95=[lo,hi],gate_passed=bool(passed))
    result['all_phase_gates_passed'] = all(x['gate_passed'] for x in result['opponents'].values())
    target = out/f'{phase}_summary.json'
    with target.open('x') as f:
        json.dump(result,f,indent=2)
        f.write('\n')
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    main()
