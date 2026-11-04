#!/usr/bin/env python3
"""Audit the fixed five-role diagnostic, then summarize paired whole-card scores.

Only stdlib and NumPy. No game/model/repository imports. Real data are read only
when --data-ready is explicitly supplied; --self-test uses fabricated temp files.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import tempfile

import numpy as np

ROLES = ('V14', 'S3', 'S30', 'CONTROL30', 'SAP0_30')
OPPONENTS = ('solution92', 'default', 'self:experiments/releases/20261101_v13_neb/agent_p0.pth')
SIDES = ('player_0', 'player_1')
SEEDS = tuple(range(864000, 864020))
FIELDS = ('seed', 'side', 'opponent', 'result', 'game_win', 'point_win', 'our_wins', 'opp_wins',
          'our_points', 'opp_points', 'point_counting_version', 'wait_frac', 'invalid_frac',
          'greedy_masked_frac', 'sap_attempts', 'sap_hits', 'stack_frac', 'relics_found',
          'relics_seen', 'known_point_tiles', 'belief_contradictions', 'unit_steps', 'steps', 'secs')
INT_FIELDS = {'seed', 'game_win', 'our_wins', 'opp_wins', 'our_points', 'opp_points',
              'point_counting_version', 'sap_attempts', 'sap_hits', 'relics_found', 'relics_seen',
              'known_point_tiles', 'belief_contradictions', 'unit_steps', 'steps'}
FRACTION_FIELDS = {'wait_frac', 'invalid_frac', 'greedy_masked_frac', 'stack_frac'}
DEFAULT_DIR = Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/student_reward_20261104/diagnostic')
LIMITS = [
    'Exploratory diagnostic on 20 locally reserved cards; not a strength confirmation or submission decision.',
    'One training seed; card bootstrap quantifies card variation conditional on these trained checkpoints, not variation over training seeds.',
    'Multiple role/opponent comparisons; percentile intervals are unadjusted and do not control simultaneous error.',
    'Whole cards are paired across roles and resampled with both sides together; pooled panels additionally keep all three opponents together.',
    'A score of 1 on these games describes this sample only and does not imply a population guarantee.',
    'CSV consistency cannot independently reconstruct engine scoring; v2 is required and outcome/win/point fields are cross-checked.',
]


class IntegrityError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise IntegrityError(message)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_keys():
    return {(seed, side, opponent) for seed in SEEDS for side in SIDES for opponent in OPPONENTS}


def load_role(path, role):
    require(path.is_file(), f'{role}: missing complete CSV {path}')
    before = sha256(path)
    with path.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames
        require(header is not None and len(header) == len(set(header)), f'{role}: missing/duplicate CSV columns')
        require(set(header) == set(FIELDS), f'{role}: schema mismatch; missing={sorted(set(FIELDS)-set(header))}, unexpected={sorted(set(header)-set(FIELDS))}')
        rows = {}
        for line, raw in enumerate(reader, 2):
            label = f'{role} line {line}'
            require(None not in raw and all(raw.get(k) is not None and raw[k].strip() != '' for k in FIELDS), f'{label}: missing/extra/empty cell')
            row = {'side': raw['side'], 'opponent': raw['opponent']}
            for name in FIELDS:
                if name in row:
                    continue
                try:
                    value = float(raw[name])
                except (TypeError, ValueError) as error:
                    raise IntegrityError(f'{label}: invalid numeric {name}') from error
                require(math.isfinite(value), f'{label}: nonfinite {name}')
                if name in INT_FIELDS:
                    require(value.is_integer(), f'{label}: noninteger {name}')
                    value = int(value)
                row[name] = value
            key = (row['seed'], row['side'], row['opponent'])
            require(key in expected_keys(), f'{label}: unexpected key {key}')
            require(key not in rows, f'{label}: duplicate key {key}')
            require(row['steps'] == 303, f'{label}: incomplete game steps')
            require(row['point_counting_version'] == 2, f'{label}: scoring version must be 2')
            require(row['result'] in (0., .5, 1.), f'{label}: result outside 0/.5/1')
            require(0 <= row['our_wins'] <= 3 and 0 <= row['opp_wins'] <= 3 and row['our_wins']+row['opp_wins'] <= 3, f'{label}: impossible three-match win counts')
            outcome = 1. if row['our_wins'] > row['opp_wins'] else (0. if row['our_wins'] < row['opp_wins'] else .5)
            require(row['result'] == outcome, f'{label}: result contradicts team win counts')
            require(row['game_win'] == int(outcome == 1.), f'{label}: game_win contradicts result')
            point_outcome = 1. if row['our_points'] > row['opp_points'] else (0. if row['our_points'] < row['opp_points'] else .5)
            require(row['point_win'] == point_outcome, f'{label}: point_win contradicts total points')
            for name in FRACTION_FIELDS:
                require(0 <= row[name] <= 1, f'{label}: fraction {name} outside [0,1]')
            for name in INT_FIELDS - {'seed', 'point_counting_version', 'steps'}:
                require(row[name] >= 0, f'{label}: negative counter {name}')
            require(row['secs'] >= 0, f'{label}: negative duration')
            rows[key] = row
    require(set(rows) == expected_keys(), f'{role}: expected 120 complete keys; got {len(rows)}, missing={len(expected_keys()-set(rows))}')
    require(sha256(path) == before, f'{role}: CSV changed during audit')
    return rows, before


def summary(rows):
    results = np.array([r['result'] for r in rows], dtype=float)
    wins, draws, losses = (int(np.count_nonzero(results == value)) for value in (1., .5, 0.))
    return dict(games=len(rows), cards=len({r['seed'] for r in rows}), wins=wins, draws=draws, losses=losses,
                draw_half_score=float((wins + .5*draws)/len(rows)),
                mean_our_points=float(np.mean([r['our_points'] for r in rows])),
                mean_opp_points=float(np.mean([r['opp_points'] for r in rows])))


def paired_comparison(candidate, reference, sampled_cards):
    def estimate(opponents):
        # Shape remains card × opponent × side until the whole-card mean.
        differences = np.array([[[candidate[(seed, side, opponent)]['result'] - reference[(seed, side, opponent)]['result']
                                  for side in SIDES] for opponent in opponents] for seed in SEEDS], dtype=float)
        card_difference = differences.mean(axis=(1, 2))
        bootstraps = card_difference[sampled_cards].mean(axis=1)
        lo, hi = np.quantile(bootstraps, [.025, .975], method='linear')
        return dict(cards=20, games_per_role=20*len(opponents)*2,
                    score_difference=float(card_difference.mean()),
                    score_difference_percentage_points=float(card_difference.mean()*100),
                    percentile_95_ci=[float(lo), float(hi)],
                    percentile_95_ci_percentage_points=[float(lo*100), float(hi*100)],
                    card_score_differences=[dict(seed=seed, difference=float(d)) for seed,d in zip(SEEDS,card_difference)])
    return dict(pooled_three_opponent_panel=estimate(OPPONENTS),
                by_opponent={opponent: estimate((opponent,)) for opponent in OPPONENTS})


def audit(directory):
    data, hashes = {}, {}
    for role in ROLES:
        data[role], hashes[role] = load_role(directory/f'{role}.csv', role)
    # Do not calculate any outcome summaries until every role is complete.
    require(sum(map(len, data.values())) == 600, 'Expected exactly 600 role-qualified keys')
    rng = np.random.default_rng(0)
    sampled_cards = rng.integers(0, 20, size=(5000,20))
    result = dict(schema='student_reward_diagnostic_audit_v1',
                  audited_at=datetime.now(timezone.utc).isoformat(),
                  integrity='complete', role_count=5, games=600,
                  cards=list(SEEDS), sides=list(SIDES), opponents=list(OPPONENTS),
                  source_csv_sha256=hashes,
                  bootstrap=dict(replicates=5000, seed=0, rng='numpy.default_rng/PCG64', unit='whole card',
                                 interval='unadjusted percentile 95%; numpy quantile method=linear',
                                 common_resample_indices=True),
                  primary_reward_comparison=dict(candidate='SAP0_30', reference='CONTROL30',
                      **paired_comparison(data['SAP0_30'],data['CONTROL30'],sampled_cards)),
                  summaries={}, comparisons_against_V14={}, limitations=LIMITS)
    for role in ROLES:
        result['summaries'][role] = dict(pooled_three_opponent_panel=summary(list(data[role].values())),
            by_opponent={opponent:summary([r for r in data[role].values() if r['opponent']==opponent]) for opponent in OPPONENTS})
        result['comparisons_against_V14'][role] = paired_comparison(data[role],data['V14'],sampled_cards)
    require(all(sha256(directory/f'{role}.csv')==hashes[role] for role in ROLES),'A source CSV changed before audit completion')
    return result


def markdown(result):
    lines=['# Exploratory student/reward diagnostic', '',
           'Integrity: all 600 planned games complete, unique, finite, 303 steps and scoring v2. Outcomes agree with recorded team win counts.', '',
           'Scores count each draw as half. Intervals are unadjusted 95% paired whole-card percentile bootstraps (20 cards, 5,000 samples, seed 0).', '',
           '| Role | Opponent | W–D–L | Score | Paired score difference vs V14 | 95% interval |',
           '|---|---|---:|---:|---:|---:|']
    for role in ROLES:
        for opponent in ('pooled',*OPPONENTS):
            s=(result['summaries'][role]['pooled_three_opponent_panel'] if opponent=='pooled' else result['summaries'][role]['by_opponent'][opponent])
            d=(result['comparisons_against_V14'][role]['pooled_three_opponent_panel'] if opponent=='pooled' else result['comparisons_against_V14'][role]['by_opponent'][opponent])
            label='V13' if opponent.startswith('self:') else opponent
            lo,hi=d['percentile_95_ci_percentage_points']
            lines.append(f"| {role} | {label} | {s['wins']}–{s['draws']}–{s['losses']} | {s['draw_half_score']:.4f} | {d['score_difference_percentage_points']:+.2f} pp | [{lo:+.2f}, {hi:+.2f}] pp |")
    lines+=['','Primary reward comparison: SAP0_30 minus CONTROL30 (same S30 initialization and one training seed).', '', '| Panel | Score difference | 95% interval |','|---|---:|---:|']
    p=result['primary_reward_comparison']
    for opponent in ('pooled',*OPPONENTS):
        d=p['pooled_three_opponent_panel'] if opponent=='pooled' else p['by_opponent'][opponent]
        lo,hi=d['percentile_95_ci_percentage_points'];label='V13' if opponent.startswith('self:') else opponent
        lines.append(f"| {label} | {d['score_difference_percentage_points']:+.2f} pp | [{lo:+.2f}, {hi:+.2f}] pp |")
    lines+=['','Interpretation limits:','']+[f'- {limit}' for limit in LIMITS]
    return '\n'.join(lines)+'\n'


def fabricate(directory):
    for ri,role in enumerate(ROLES):
        with (directory/f'{role}.csv').open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=FIELDS);writer.writeheader()
            for si,seed in enumerate(SEEDS):
                for oi,opponent in enumerate(OPPONENTS):
                    for side in SIDES:
                        # Perfect within-card correlation makes a side-wise bootstrap
                        # different from the required card-wise reference calculation.
                        outcome=(0.,.5,1.)[(si+ri+oi)%3]
                        ours,theirs={0.:(0,3),.5:(1,1),1.:(3,0)}[outcome]
                        row={name:0 for name in FIELDS}
                        row.update(seed=seed,side=side,opponent=opponent,result=outcome,
                                   game_win=int(outcome==1),point_win=outcome,our_wins=ours,opp_wins=theirs,
                                   our_points=ours*100,opp_points=theirs*100,point_counting_version=2,steps=303,secs=1)
                        writer.writerow(row)


def self_test():
    cases=[]
    with tempfile.TemporaryDirectory(prefix='fabricated_diagnostic_audit_') as temporary:
        directory=Path(temporary);fabricate(directory)
        complete=audit(directory)
        require(complete['games']==600,'Fixture total wrong')
        require(all(complete['summaries'][r]['pooled_three_opponent_panel']['games']==120 for r in ROLES),'Fixture per-role count wrong')
        require(all(tuple(complete['summaries'][r]['pooled_three_opponent_panel'][k] for k in ('wins','draws','losses','draw_half_score'))==(40,40,40,.5) for r in ROLES),'Fabricated WDL/half-draw score mismatch')
        zero=complete['comparisons_against_V14']['V14']['pooled_three_opponent_panel']
        require(zero['score_difference']==0 and zero['percentile_95_ci']==[0.,0.],'Self comparison should be zero')
        # Independent literal card-block enumeration, not paired_comparison().
        data={r:load_role(directory/f'{r}.csv',r)[0] for r in ROLES}
        diffs=[]
        for seed in SEEDS:
            values=[]
            for key,row in data['SAP0_30'].items():
                if key[0]==seed:values.append(row['result']-data['CONTROL30'][key]['result'])
            diffs.append(sum(values)/6)
        rng=np.random.default_rng(0);sample=rng.integers(0,20,size=(5000,20))
        reference=np.quantile(np.array([sum(diffs[i] for i in draw)/20 for draw in sample]),[.025,.975])
        actual=complete['primary_reward_comparison']['pooled_three_opponent_panel']
        require(np.allclose(reference,actual['percentile_95_ci'],rtol=0,atol=1e-15),'Independent whole-card bootstrap mismatch')
        # Per-opponent fixture has two identical-side outcomes per card.
        opponent=OPPONENTS[0]
        card=np.array([data['SAP0_30'][(seed,SIDES[0],opponent)]['result']-data['CONTROL30'][(seed,SIDES[0],opponent)]['result'] for seed in SEEDS])
        require(np.allclose(np.quantile(card[sample].mean(1),[.025,.975]),complete['primary_reward_comparison']['by_opponent'][opponent]['percentile_95_ci']), 'Opponent bootstrap mismatch')
        require(audit(directory)['primary_reward_comparison']==complete['primary_reward_comparison'],'Bootstrap not deterministic')
        cases.extend(['complete_600_key_fixture','WDL_score_counts','zero_self_comparison','independent_pooled_whole_card_bootstrap','per_opponent_both_sides_bootstrap','deterministic_seed0'])
        path=directory/'S3.csv';original=path.read_text()
        def rejected(name,mutation):
            with path.open(newline='') as f:
                rows=list(csv.DictReader(f))
            header=list(FIELDS)
            mutation(rows,header)
            with path.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=header);w.writeheader();w.writerows(rows)
            try:
                audit(directory)
            except IntegrityError:
                cases.append(name)
            else:
                raise AssertionError('Malformed fixture unexpectedly accepted: '+name)
            finally:
                path.write_text(original)
        rejected('missing_game',lambda r,h:r.pop())
        rejected('duplicate_key',lambda r,h:r.append(dict(r[0])))
        rejected('wrong_card',lambda r,h:r[0].update(seed=500000))
        rejected('wrong_side',lambda r,h:r[0].update(side='player_2'))
        rejected('wrong_opponent',lambda r,h:r[0].update(opponent='random'))
        rejected('result_contradicts_wins',lambda r,h:r[0].update(result=1 if float(r[0]['result'])!=1 else 0))
        rejected('invalid_result',lambda r,h:r[0].update(result=.25))
        rejected('game_win_mismatch',lambda r,h:r[0].update(game_win=2))
        rejected('noninteger_seed',lambda r,h:r[0].update(seed=864000.5))
        rejected('impossible_match_wins',lambda r,h:r[0].update(our_wins=3,opp_wins=3))
        rejected('nonfinite_metric',lambda r,h:r[0].update(secs='nan'))
        rejected('empty_metric',lambda r,h:r[0].update(secs=''))
        rejected('short_game',lambda r,h:r[0].update(steps=302))
        rejected('old_scoring',lambda r,h:r[0].update(point_counting_version=1))
        rejected('point_outcome_mismatch',lambda r,h:r[0].update(point_win=.75))
        rejected('missing_column',lambda r,h:(h.remove('game_win'),[x.pop('game_win') for x in r]))
        rejected('duplicate_header',lambda r,h:h.append('secs'))
    return dict(fabricated_fixtures_only=True,cases=cases,count=len(cases),real_data_read=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--data-ready',action='store_true',help='Required explicit gate before reading real CSVs')
    parser.add_argument('--directory',type=Path,default=DEFAULT_DIR)
    parser.add_argument('--out-prefix',type=Path,default=Path('/tmp/sherlock-student-20261104/diagnostic_review'))
    args=parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(),indent=2));return 0
    if not args.data_ready:
        parser.error('Await explicit data-ready signal, then supply --data-ready; no real files read.')
    json_out=args.out_prefix.with_suffix('.json');md_out=args.out_prefix.with_suffix('.md')
    require(not json_out.exists() and not md_out.exists(),'Audit output occupied; choose a new out-prefix')
    result=audit(args.directory)
    result['auditor_sha256']=sha256(Path(__file__))
    json_out.parent.mkdir(parents=True,exist_ok=True)
    json_out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    md_out.write_text(markdown(result))
    print(json.dumps(dict(integrity=result['integrity'],games=result['games'],json=str(json_out),markdown=str(md_out))))
    return 0


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (IntegrityError,OSError,csv.Error) as error:
        print(json.dumps(dict(integrity='invalid_or_incomplete',error=str(error))))
        raise SystemExit(2)
