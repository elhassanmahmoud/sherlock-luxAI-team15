#!/usr/bin/env python3
"""Audit the fixed six-role A2 teacher-anchor diagnostic, then summarize paired whole-card scores.

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

ROLES = ('V14', 'A2', 'CONTROL25', 'CONTROL26', 'ANCHOR25', 'ANCHOR26')
DIRECT_ROLES = tuple(role for role in ROLES if role != 'V14')
DIRECT_OPPONENT = 'self:agents/sherlock/weights/agent_p0.pth'
DIRECT_SEEDS = tuple(range(867100, 867120))
OPPONENTS = ('solution92', 'default', 'self:experiments/releases/20261101_v13_neb/agent_p0.pth')
SIDES = ('player_0', 'player_1')
SEEDS = tuple(range(867000, 867020))
FIELDS = ('seed', 'side', 'opponent', 'result', 'game_win', 'point_win', 'our_wins', 'opp_wins',
          'our_points', 'opp_points', 'point_counting_version', 'wait_frac', 'invalid_frac',
          'greedy_masked_frac', 'sap_attempts', 'sap_hits', 'stack_frac', 'relics_found',
          'relics_seen', 'known_point_tiles', 'belief_contradictions', 'unit_steps', 'steps', 'secs')
INT_FIELDS = {'seed', 'game_win', 'our_wins', 'opp_wins', 'our_points', 'opp_points',
              'point_counting_version', 'sap_attempts', 'sap_hits', 'relics_found', 'relics_seen',
              'known_point_tiles', 'belief_contradictions', 'unit_steps', 'steps'}
FRACTION_FIELDS = {'wait_frac', 'invalid_frac', 'greedy_masked_frac', 'stack_frac'}
DEFAULT_DIR = Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/experiments/analysis/a2_anchor_20261104/diagnostic')
LIMITS = [
    'Exploratory diagnostic on 20 locally reserved cards; not a strength confirmation or submission decision.',
    'Only two training seeds, reported separately; card bootstrap quantifies card variation conditional on these checkpoints, not precise training-seed uncertainty.',
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


def expected_keys(group='panel'):
    seeds, opponents = (SEEDS, OPPONENTS) if group == 'panel' else (DIRECT_SEEDS, (DIRECT_OPPONENT,))
    return {(seed, side, opponent) for seed in seeds for side in SIDES for opponent in opponents}


def load_role(path, role, group='panel'):
    required_keys = expected_keys(group)
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
            require(key in required_keys, f'{label}: unexpected key {key}')
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
    require(set(rows) == required_keys, f'{role}: expected {len(required_keys)} complete keys; got {len(rows)}, missing={len(required_keys-set(rows))}')
    require(sha256(path) == before, f'{role}: CSV changed during audit')
    return rows, before


def summary(rows):
    results = np.array([r['result'] for r in rows], dtype=float)
    wins, draws, losses = (int(np.count_nonzero(results == value)) for value in (1., .5, 0.))
    return dict(games=len(rows), cards=len({r['seed'] for r in rows}), wins=wins, draws=draws, losses=losses,
                draw_half_score=float((wins + .5*draws)/len(rows)), win_fraction=float(wins/len(rows)),
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


def scalar_estimate(card_values, sampled_cards):
    values = np.asarray(card_values, dtype=float)
    lo, hi = np.quantile(values[sampled_cards].mean(axis=1), [.025, .975], method='linear')
    return dict(estimate=float(values.mean()), percentile_95_ci=[float(lo), float(hi)],
                card_values=[float(value) for value in values])


def direct_summary(rows, sampled_cards):
    result = summary(list(rows.values()))
    result['by_side'] = {side: summary([row for row in rows.values() if row['side']==side]) for side in SIDES}
    result['candidate_score'] = scalar_estimate([
        np.mean([rows[(seed, side, DIRECT_OPPONENT)]['result'] for side in SIDES])
        for seed in DIRECT_SEEDS], sampled_cards)
    result['candidate_win_fraction'] = scalar_estimate([
        np.mean([rows[(seed, side, DIRECT_OPPONENT)]['game_win'] for side in SIDES])
        for seed in DIRECT_SEEDS], sampled_cards)
    result['V14_win_fraction'] = scalar_estimate([
        np.mean([int(rows[(seed, side, DIRECT_OPPONENT)]['result']==0) for side in SIDES])
        for seed in DIRECT_SEEDS], sampled_cards)
    result['V14_score'] = scalar_estimate([
        np.mean([1-rows[(seed, side, DIRECT_OPPONENT)]['result'] for side in SIDES])
        for seed in DIRECT_SEEDS], sampled_cards)
    return result

def select_confirmation(result):
    """Apply only the declared later-confirmation screen, never release gates."""
    entries = {}
    base = result['summaries']['A2']
    for seed in (25, 26):
        role, control = f'ANCHOR{seed}', f'CONTROL{seed}'
        candidate = result['summaries'][role]
        panel = candidate['pooled_three_opponent_panel']['draw_half_score']
        solution = candidate['by_opponent']['solution92']['draw_half_score']
        delta_control = result['anchor_minus_control'][str(seed)]['pooled_three_opponent_panel']['score_difference']
        wins = result['direct_against_V14'][role]['wins']
        gates = dict(panel_at_least_A2=panel >= base['pooled_three_opponent_panel']['draw_half_score'],
                     solution_at_least_A2=solution >= base['by_opponent']['solution92']['draw_half_score'],
                     panel_above_paired_control=delta_control > 0,
                     direct_at_least_24_strict_wins=wins >= 24)
        entries[role] = dict(training_seed=seed, paired_control=control, gates=gates,
                             eligible_for_later_confirmation=all(gates.values()),
                             panel_score=panel, solution_score=solution, direct_wins=wins)
    eligible = [role for role in entries if entries[role]['eligible_for_later_confirmation']]
    ranked = sorted(eligible, key=lambda role: (-entries[role]['panel_score'],
                    -entries[role]['solution_score'], entries[role]['training_seed']))
    return dict(candidates=entries, eligible_ranked=ranked, selected_for_later_confirmation=ranked[0] if ranked else None,
                rule='ANCHOR only; panel and Solution draw-half scores >= A2, panel > paired CONTROL, >=24/40 strict direct wins; rank panel, Solution, smaller seed',
                release_qualified=False, no_promotion_from_diagnostic=True,
                no_fallback_after_failed_confirmation=True)


def audit(directory):
    data, direct, hashes, paths = {}, {}, {}, {}
    for group, roles, target in (('panel', ROLES, data), ('direct', DIRECT_ROLES, direct)):
        group_dir = directory/group
        require(group_dir.is_dir(), f'Missing {group} directory')
        require({p.name for p in group_dir.glob('*.csv')} == {f'{role}.csv' for role in roles},
                f'{group}: unexpected or missing CSV role files')
        for role in roles:
            path=group_dir/f'{role}.csv'
            target[role], digest = load_role(path, role, group)
            key=f'{group}/{role}.csv'; hashes[key]=digest; paths[key]=path
    require(sum(map(len,data.values()))==720, 'Expected exactly 720 panel keys')
    require(sum(map(len,direct.values()))==200, 'Expected exactly 200 direct keys')
    # Separate card populations; same deterministic index matrix is valid for each.
    sampled_cards=np.random.default_rng(0).integers(0,20,size=(5000,20))
    result=dict(schema='a2_anchor_diagnostic_audit_v1',
                audited_at=datetime.now(timezone.utc).isoformat(), integrity='complete',
                role_count=6, panel_games=720, direct_games=200, games=920,
                panel_cards=list(SEEDS), direct_cards=list(DIRECT_SEEDS), sides=list(SIDES),
                opponents=list(OPPONENTS), direct_opponent=DIRECT_OPPONENT,
                source_csv_sha256=hashes,
                bootstrap=dict(replicates=5000, seed=0, rng='numpy.default_rng/PCG64',
                    unit='whole card; both sides and all panel opponents kept together',
                    interval='unadjusted percentile 95%; numpy quantile method=linear',
                    common_resample_indices=True, separate_panel_direct_cards=True),
                summaries={}, comparisons_against_V14={}, comparisons_against_A2={},
                anchor_minus_control={}, direct_against_V14={}, limitations=LIMITS,
                promotion_from_diagnostic=False)
    for role in ROLES:
        result['summaries'][role]=dict(pooled_three_opponent_panel=summary(list(data[role].values())),
            by_opponent={o:summary([r for r in data[role].values() if r['opponent']==o]) for o in OPPONENTS},
            by_side={s:summary([r for r in data[role].values() if r['side']==s]) for s in SIDES})
        result['comparisons_against_V14'][role]=paired_comparison(data[role],data['V14'],sampled_cards)
        result['comparisons_against_A2'][role]=paired_comparison(data[role],data['A2'],sampled_cards)
    for seed in (25,26):
        cand,ref=f'ANCHOR{seed}',f'CONTROL{seed}'
        result['anchor_minus_control'][str(seed)]=dict(candidate=cand,reference=ref,
            **paired_comparison(data[cand],data[ref],sampled_cards))
    for role in DIRECT_ROLES:
        result['direct_against_V14'][role]=direct_summary(direct[role],sampled_cards)
    result['confirmation_screen']=select_confirmation(result)
    require(all(sha256(paths[key])==digest for key,digest in hashes.items()), 'A source CSV changed before audit completion')
    return result


def markdown(result):
    lines=['# Exploratory A2 teacher-anchor diagnostic', '',
        'Integrity: all 920 planned games complete and unique (720 panel + 200 direct), finite, 303 steps, scoring v2; recorded outcomes agree with win counts.', '',
        'Scores count draws as half. Intervals are unadjusted 95% whole-card percentile bootstrap intervals, 5,000 draws, seed 0. Both sides and all panel opponents stay grouped.', '',
        '| Role | Panel W–D–L | Panel score | Difference vs V14 | 95% interval | Solution W–D–L |',
        '|---|---:|---:|---:|---:|---:|']
    for role in ROLES:
        s=result['summaries'][role]['pooled_three_opponent_panel']
        d=result['comparisons_against_V14'][role]['pooled_three_opponent_panel']
        sol=result['summaries'][role]['by_opponent']['solution92'];lo,hi=d['percentile_95_ci_percentage_points']
        lines.append(f"| {role} | {s['wins']}–{s['draws']}–{s['losses']} | {100*s['draw_half_score']:.2f}% | {d['score_difference_percentage_points']:+.2f} pp | [{lo:+.2f}, {hi:+.2f}] pp | {sol['wins']}–{sol['draws']}–{sol['losses']} |")
    lines+=['', '| Paired comparison | Panel difference | 95% interval | Solution difference | 95% interval |', '|---|---:|---:|---:|---:|']
    pairs=[(f'ANCHOR{seed} minus CONTROL{seed}',result['anchor_minus_control'][str(seed)]) for seed in (25,26)]
    pairs += [('A2 minus V14',result['comparisons_against_V14']['A2'])]
    pairs += [(f'ANCHOR{seed} minus A2',result['comparisons_against_A2'][f'ANCHOR{seed}']) for seed in (25,26)]
    for label,comparison in pairs:
        d=comparison['pooled_three_opponent_panel'];lo,hi=d['percentile_95_ci_percentage_points']
        sol=comparison['by_opponent']['solution92'];sl,sh=sol['percentile_95_ci_percentage_points']
        lines.append(f"| {label} | {d['score_difference_percentage_points']:+.2f} pp | [{lo:+.2f}, {hi:+.2f}] pp | {sol['score_difference_percentage_points']:+.2f} pp | [{sl:+.2f}, {sh:+.2f}] pp |")
    lines+=['', '| Candidate vs V14 | W–D–L | Candidate wins (95% interval) | Draw-half score (95% interval) | V14 wins (95% interval) |', '|---|---:|---:|---:|---:|']
    def interval(item):
        lo,hi=item['percentile_95_ci'];return f"{100*item['estimate']:.2f}% [{100*lo:.2f}, {100*hi:.2f}]"
    for role,d in result['direct_against_V14'].items():
        lines.append(f"| {role} | {d['wins']}–{d['draws']}–{d['losses']} | {interval(d['candidate_win_fraction'])} | {interval(d['candidate_score'])} | {interval(d['V14_win_fraction'])} |")
    screen=result['confirmation_screen']
    lines+=['', '| Later-confirmation candidate | Panel ≥ A2 | Solution ≥ A2 | Panel > control | Direct ≥24 wins | Eligible |', '|---|---:|---:|---:|---:|---:|']
    for role,item in screen['candidates'].items():
        answers=['yes' if passed else 'no' for passed in item['gates'].values()]
        lines.append('| '+ ' | '.join([role,*answers,'yes' if item['eligible_for_later_confirmation'] else 'no'])+' |')
    selected=screen['selected_for_later_confirmation'] or 'none'
    lines += ['', f'First candidate for later confirmation: **{selected}**. Ordering: panel score, Solution score, smaller training seed.',
              'This diagnosis does not qualify any submission. The full confirmation/course/package/backup path remains necessary; no fallback after failed confirmation.', '',
              'Per-opponent comparisons, side summaries, per-card estimates and source hashes are in the JSON.', '', 'Interpretation limits:', '']+[f'- {limit}' for limit in LIMITS]
    return '\n'.join(lines)+'\n'


def fabricate(directory):
    for group,roles,seeds,opponents in (('panel',ROLES,SEEDS,OPPONENTS),('direct',DIRECT_ROLES,DIRECT_SEEDS,(DIRECT_OPPONENT,))):
        (directory/group).mkdir()
        for ri,role in enumerate(roles):
            with (directory/group/f'{role}.csv').open('w',newline='') as handle:
                writer=csv.DictWriter(handle,fieldnames=FIELDS);writer.writeheader()
                for si,seed in enumerate(seeds):
                    for oi,opponent in enumerate(opponents):
                        for side in SIDES:
                            outcome=(0.,.5,1.)[(si+ri+oi)%3] if group=='panel' else float(si<10)
                            ours,theirs={0.:(0,3),.5:(1,1),1.:(3,0)}[outcome]
                            row={name:0 for name in FIELDS}
                            row.update(seed=seed,side=side,opponent=opponent,result=outcome,
                                game_win=int(outcome==1),point_win=outcome,our_wins=ours,opp_wins=theirs,
                                our_points=ours*100,opp_points=theirs*100,point_counting_version=2,steps=303,secs=1)
                            writer.writerow(row)

def self_test():
    cases=[]
    with tempfile.TemporaryDirectory(prefix='fabricated_a2_anchor_audit_') as temporary:
        directory=Path(temporary);fabricate(directory);complete=audit(directory)
        require(complete['games']==920 and complete['panel_games']==720 and complete['direct_games']==200,'Fixture totals wrong')
        require(all(tuple(complete['summaries'][r]['pooled_three_opponent_panel'][k] for k in ('wins','draws','losses','draw_half_score'))==(40,40,40,.5) for r in ROLES),'Fabricated panel WDL/half-draw score mismatch')
        require(all(complete['direct_against_V14'][r]['wins']==20 and complete['direct_against_V14'][r]['losses']==20 for r in DIRECT_ROLES),'Direct WDL wrong')
        zero=complete['comparisons_against_V14']['V14']['pooled_three_opponent_panel']
        require(zero['score_difference']==0 and zero['percentile_95_ci']==[0.,0.],'Self comparison nonzero')
        samples=np.random.default_rng(0).integers(0,20,size=(5000,20))
        data={r:load_role(directory/'panel'/f'{r}.csv',r)[0] for r in ROLES}
        # Independently enumerate entire card blocks for every required comparison.
        pairs=[(r,'V14',complete['comparisons_against_V14'][r]) for r in ROLES]
        pairs += [(r,'A2',complete['comparisons_against_A2'][r]) for r in ROLES]
        pairs += [(f'ANCHOR{s}',f'CONTROL{s}',complete['anchor_minus_control'][str(s)]) for s in (25,26)]
        for cand,ref,comparison in pairs:
            for opponents,label in ((OPPONENTS,'pooled_three_opponent_panel'),*(( (o,),o) for o in OPPONENTS)):
                card=[sum(data[cand][(seed,side,opp)]['result']-data[ref][(seed,side,opp)]['result'] for side in SIDES for opp in opponents)/(2*len(opponents)) for seed in SEEDS]
                independent=np.array([sum(card[int(i)] for i in draw)/20 for draw in samples])
                actual=comparison[label] if label=='pooled_three_opponent_panel' else comparison['by_opponent'][label]
                require(np.allclose(np.quantile(independent,[.025,.975]),actual['percentile_95_ci'],rtol=0,atol=1e-15),'Independent grouped panel bootstrap mismatch')
        direct_card=np.array([1.]*10+[0.]*10)
        expected=np.quantile(np.array([sum(direct_card[int(i)] for i in draw)/20 for draw in samples]),[.025,.975])
        for role in DIRECT_ROLES:
            d=complete['direct_against_V14'][role]
            require(np.allclose(d['candidate_win_fraction']['percentile_95_ci'],expected),'Independent grouped direct bootstrap mismatch')
            require(np.allclose(d['candidate_score']['percentile_95_ci'],expected),'Direct score bootstrap mismatch')
            require(d['by_side']['player_0']['wins']==10 and d['by_side']['player_1']['wins']==10,'Direct side breakdown wrong')
        # A separate direct fixture verifies wins differ from half-draw score.
        draw_rows=load_role(directory/'direct'/'A2.csv','A2','direct')[0]
        for (seed,side,opponent),row in draw_rows.items():
            row['result']=1. if seed<DIRECT_SEEDS[10] else (.5 if seed<DIRECT_SEEDS[15] else 0.)
            row['game_win']=int(row['result']==1.)
        draw_summary=direct_summary(draw_rows,samples)
        require(draw_summary['candidate_win_fraction']['estimate']==.5 and draw_summary['candidate_score']['estimate']==.625,
                'Direct wins and half-draw scores conflated')
        require(draw_summary['V14_win_fraction']['estimate']==.25 and draw_summary['V14_score']['estimate']==.375,
                'V14 direct win/score complement wrong')
        for name,values in [('candidate_score',[1.]*10+[.5]*5+[0.]*5),
                            ('candidate_win_fraction',[1.]*10+[0.]*10),
                            ('V14_win_fraction',[0.]*15+[1.]*5),
                            ('V14_score',[0.]*10+[.5]*5+[1.]*5)]:
            ci=np.quantile(np.array([sum(values[int(i)] for i in draw)/20 for draw in samples]),[.025,.975])
            require(np.allclose(draw_summary[name]['percentile_95_ci'],ci), 'Direct draw fixture grouped CI mismatch')
        cases.append('direct_draw_fixture_win_vs_halfscore_V14_complements_all_4_CIs')
        naive=np.quantile(np.repeat(direct_card,2)[np.random.default_rng(0).integers(0,40,(5000,40))].mean(1),[.025,.975])
        require(not np.allclose(expected,naive),'Fixture must distinguish grouped from independent-side bootstrap')
        require(audit(directory)['anchor_minus_control']==complete['anchor_minus_control'],'Bootstrap nondeterministic')
        require(len(complete['source_csv_sha256'])==11,'Missing input hashes')
        require('920' in markdown(complete),'Markdown not rendered')
        cases.extend(['exact_920_keys_11_files','panel_WDL_halfdraw','direct_WDL_sides','zero_self_comparison',
            'all_14_paired_comparisons_all_4_strata_independent_grouped_bootstrap',
            'direct_independent_wholecard_bootstrap','fixture_rejects_sidewise_bootstrap','deterministic_seed0','11_source_hashes','markdown'])
        # Exercise the declared screen independently of score/result helpers.
        import copy
        fixture=copy.deepcopy(complete)
        def set_screen(panel25=.6, panel26=.6, sol25=.6, sol26=.6, direct25=24, direct26=24, control25=.01, control26=.01):
            base=fixture['summaries']['A2'];base['pooled_three_opponent_panel']['draw_half_score']=.5;base['by_opponent']['solution92']['draw_half_score']=.5
            for seed,panel,sol,wins,delta in ((25,panel25,sol25,direct25,control25),(26,panel26,sol26,direct26,control26)):
                role=f'ANCHOR{seed}'
                fixture['summaries'][role]['pooled_three_opponent_panel']['draw_half_score']=panel
                fixture['summaries'][role]['by_opponent']['solution92']['draw_half_score']=sol
                fixture['direct_against_V14'][role]['wins']=wins
                fixture['anchor_minus_control'][str(seed)]['pooled_three_opponent_panel']['score_difference']=delta
            return select_confirmation(fixture)
        require(set_screen()['selected_for_later_confirmation']=='ANCHOR25','Smaller seed tie-break failed')
        require(set_screen(panel26=.61)['selected_for_later_confirmation']=='ANCHOR26','Panel rank failed')
        require(set_screen(sol26=.61)['selected_for_later_confirmation']=='ANCHOR26','Solution tie-break failed')
        require(set_screen(panel25=.5,sol25=.5,direct26=23)['selected_for_later_confirmation']=='ANCHOR25','A2 equality or direct24 threshold failed')
        for kwargs,gate in [({'panel25':.49},'panel_at_least_A2'),({'sol25':.49},'solution_at_least_A2'),({'control25':0},'panel_above_paired_control'),({'direct25':23},'direct_at_least_24_strict_wins')]:
            screen=set_screen(**kwargs)
            require(not screen['candidates']['ANCHOR25']['gates'][gate] and not screen['candidates']['ANCHOR25']['eligible_for_later_confirmation'],'Screen failed closed: '+gate)
        require(set_screen(direct25=23,direct26=23)['selected_for_later_confirmation'] is None,'No eligible candidate must select none')
        require(not set_screen()['release_qualified'] and set_screen()['no_fallback_after_failed_confirmation'],'Diagnosis cannot qualify release or fallback')
        cases.extend(['selection_smaller_seed_tiebreak','selection_panel_first','selection_solution_second','selection_A2_equality_direct24_boundary','selection_all_4_failure_gates','selection_none','no_diagnostic_release_no_fallback'])
        for group,role in (('panel','A2'),('direct','A2')):
            path=directory/group/f'{role}.csv';original=path.read_bytes()
            def rejected(name,mutation):
                with path.open(newline='') as f:rows=list(csv.DictReader(f))
                header=list(FIELDS);mutation(rows,header)
                with path.open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=header);w.writeheader();w.writerows(rows)
                try:audit(directory)
                except IntegrityError:cases.append(group+':'+name)
                else:raise AssertionError('Malformed fixture accepted: '+group+':'+name)
                finally:path.write_bytes(original)
            rejected('missing_game',lambda r,h:r.pop())
            rejected('duplicate_key',lambda r,h:r.append(dict(r[0])))
            rejected('wrong_card',lambda r,h:r[0].update(seed=500000))
            rejected('wrong_side',lambda r,h:r[0].update(side='player_2'))
            rejected('wrong_opponent',lambda r,h:r[0].update(opponent='random'))
            rejected('cross_group_card',lambda r,h:r[0].update(seed=DIRECT_SEEDS[0] if group=='panel' else SEEDS[0]))
            rejected('result_contradicts_wins',lambda r,h:r[0].update(result=1 if float(r[0]['result'])!=1 else 0))
            rejected('invalid_result',lambda r,h:r[0].update(result=.25))
            rejected('game_win_mismatch',lambda r,h:r[0].update(game_win=2))
            rejected('noninteger_seed',lambda r,h:r[0].update(seed=867000.5))
            rejected('impossible_match_wins',lambda r,h:r[0].update(our_wins=3,opp_wins=3))
            rejected('negative_counter',lambda r,h:r[0].update(unit_steps=-1))
            rejected('fraction_out_of_range',lambda r,h:r[0].update(wait_frac=1.1))
            rejected('nonfinite_metric',lambda r,h:r[0].update(secs='nan'))
            rejected('nonfinite_count',lambda r,h:r[0].update(our_points='inf'))
            rejected('empty_metric',lambda r,h:r[0].update(secs=''))
            rejected('short_game',lambda r,h:r[0].update(steps=302))
            rejected('old_scoring',lambda r,h:r[0].update(point_counting_version=1))
            rejected('point_outcome_mismatch',lambda r,h:r[0].update(point_win=.75))
            rejected('missing_column',lambda r,h:(h.remove('game_win'),[x.pop('game_win') for x in r]))
            rejected('duplicate_header',lambda r,h:h.append('secs'))
            rejected('negative_duration',lambda r,h:r[0].update(secs=-1))
            rejected('invalid_numeric',lambda r,h:r[0].update(our_points='abc'))
            rejected('unexpected_column',lambda r,h:(h.append('extra'),[x.update(extra='0') for x in r]))
            for name,mutate in [('extra_cell',lambda lines:lines.__setitem__(1,lines[1]+',unexpected')),('missing_cell',lambda lines:lines.__setitem__(1,lines[1].rsplit(',',1)[0]))]:
                lines=original.decode().splitlines();mutate(lines);path.write_text('\n'.join(lines)+'\n')
                try:audit(directory)
                except IntegrityError:cases.append(group+':'+name)
                else:raise AssertionError('Malformed CSV shape accepted: '+name)
                finally:path.write_bytes(original)
        # Hash guard must reject a source that changes during its own read.
        real_sha256=globals()['sha256'];hash_calls=[0]
        def changed_sha256(path):
            hash_calls[0]+=1
            return real_sha256(path) if hash_calls[0]==1 else '0'*64
        globals()['sha256']=changed_sha256
        try:load_role(directory/'panel'/'A2.csv','A2')
        except IntegrityError:cases.append('source_changed_during_read')
        else:raise AssertionError('Changed input hash accepted')
        finally:globals()['sha256']=real_sha256
        path=directory/'direct'/'A2.csv';path.rename(path.with_suffix('.absent'))
        try:audit(directory)
        except IntegrityError:cases.append('missing_role_file')
        else:raise AssertionError('Missing role file accepted')
        path.with_suffix('.absent').rename(path)
        extra=directory/'direct'/'V14.csv';extra.write_text('')
        try:audit(directory)
        except IntegrityError:cases.append('unexpected_role_file')
        else:raise AssertionError('Unexpected role accepted')
        extra.unlink()
    return dict(fabricated_fixtures_only=True,cases=cases,count=len(cases),real_data_read=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--data-ready',action='store_true',help='Required explicit gate before reading real CSVs')
    parser.add_argument('--directory',type=Path,default=DEFAULT_DIR)
    parser.add_argument('--out-prefix',type=Path,default=Path('/tmp/sherlock-a2-anchor-20261104/diagnostic_review'))
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
