"""One fixed 440-game confirmation of the historically accepted MATCH38 copy."""
from __future__ import annotations

import json
from pathlib import Path

from scripts import match_weight_compare as selection
from scripts.early_curriculum_study import digest, hashes, require, source_identity
from scripts.final_training_supervisor import safe_path
from scripts.threat_warmstart import V14_SHA, ZIP_SHA
from scripts.threat_warmstart_compare import bound, read_bound, write

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'match_weight_confirmation_20261109'
SELECTION_PROFILE = 'match_weight_compare_20261109'
SELECTION_CLOSURE_SHA = '574cc99f8b943eb68a805871c96fd6d9f6fd61c4ed42fa37872d5a7bc3d0f3f9'
MODEL_SHA = {'v14':'817e565f8628a3a860c3dcb84e69e9d68c5f0954f791fbd06e0f115bf6cf95d2',
             'match':'ff66e696665019d304848ebf0e3b022fd1a1d08eaa9b25518f12f8c3e33e6a1b'}
PANEL = ('solution92', 'default', 'sol92_sq', 'rush')
JOBS = ('v14_panel', 'match_panel', 'match_v14')
COHORTS = {'panel':list(range(9980000,9980020)), 'direct':list(range(9980100,9980160))}
EPS = 1e-12


def output_dir(a):
    out = safe_path(a['out'])
    require(out.parent == ROOT/'experiments/analysis'/PROFILE and out.name == 'confirmation_v1',
            'Wrong exclusive confirmation output')
    require(all(out != Path(p) and out not in Path(p).parents for p in a['inputs']), 'Output overlaps input')
    return out


def accepted_selection(a):
    """Check sealed historical evidence and byte-identical old runtime, not old HEAD admission."""
    closure = read_bound(a,a['selection_closure'])
    require(digest(a['selection_closure']) == SELECTION_CLOSURE_SHA, 'Selection closure differs')
    require(closure.get('status') == 'COMPLETE_RESULT_VERIFIED'
            and closure.get('profile') == SELECTION_PROFILE and closure.get('games') == 200
            and closure.get('nominated') is True and closure.get('original_processes_ended') is True
            and closure.get('source_and_input_bindings_valid') is True
            and closure.get('protected') == a['protected'], 'Selection is not closed/nominated/verified')
    for field,key in (('selection_admission','admission_sha256'),('selection_state','owner_state_sha256'),
                      ('selection_summary','summary_sha256'),('selection_audit','independent_results_sha256'),
                      ('selection_review','independent_review_sha256')):
        require(digest(bound(a,a[field])) == closure[key], 'Historical evidence hash differs')
    old = read_bound(a,a['selection_admission']); owner = read_bound(a,a['selection_state'])
    summary = read_bound(a,a['selection_summary']); audit = read_bound(a,a['selection_audit'])
    source = closure['source']; old_sha = closure['admission_sha256']
    expected_gates = {'solution_v14','solution_control','direct_v14','direct_control'}
    for evidence in (closure,summary,audit):
        require(evidence.get('profile',SELECTION_PROFILE) == SELECTION_PROFILE
                and evidence.get('source') == source and evidence.get('admission_sha256') == old_sha
                and evidence.get('games') == 200 and evidence.get('nominated') is True
                and set(evidence['gates']) == expected_gates and all(v is True for v in evidence['gates'].values())
                and evidence.get('counts') == closure['counts'] and evidence.get('files') == closure['files'],
                'Historical nomination/result differs')
    require(audit.get('status') == 'PASS' and audit.get('summary_sha256') == closure['summary_sha256'],
            'Independent selection verification missing')
    require(old.get('profile') == SELECTION_PROFILE and old.get('stage') == 'performance'
            and old.get('root') == a['root'] and old.get('python') == a['python']
            and old.get('source') == source and old.get('protected') == a['protected']
            and all(a['inputs'].get(p) == sha for p,sha in old['inputs'].items()),
            'Historical admission/input bindings differ')
    require(hashes(old['inputs']) == old['inputs'], 'Historical input bytes changed')
    require(owner.get('profile') == SELECTION_PROFILE and owner.get('stage') == 'performance'
            and owner.get('status') == 'complete' and owner.get('active') == []
            and owner.get('source') == source and owner.get('admission_sha256') == old_sha
            and owner.get('inputs') == old['inputs'] and owner.get('protected') == a['protected']
            and set(owner['jobs']) == set(selection.JOBS) and set(owner['receipts']) == set(selection.JOBS)
            and all(owner['jobs'][n].get('returncode') == 0 for n in selection.JOBS),
            'Historical owner is incomplete')
    require(safe_path(a['selection_state']) == safe_path(Path(old['out'])/'state.json')
            and safe_path(a['selection_summary']) == safe_path(Path(old['out'])/'summary.json'),
            'Historical output location differs')
    require(len(closure['files']) == 5, 'Incomplete selection files')
    for name in selection.JOBS:
        csv = str(safe_path(Path(old['out'])/(name+'.csv')))
        sha = digest(bound(a,csv))
        require(closure['files'].get(csv) == sha
                and owner['receipts'][name] == dict(path=csv,sha256=sha,games=40), 'Historical CSV binding differs')
    # The new source may add files and have a new HEAD; every old pinned byte must remain.
    require(bool(source['files']) and hashes(source['files']) == source['files']
            and all(a['source']['files'].get(p) == sha for p,sha in source['files'].items())
            and all(a['source'].get(k) == source[k] for k in ('python','executable','executable_sha256'))
            and digest(source['executable']) == source['executable_sha256'], 'Historical runtime changed')
    technical = read_bound(a,old['technical_receipt']); approval = read_bound(a,old['technical_acceptance'])
    selection.check_technical(technical)
    require(technical.get('source') == source and approval.get('source') == source
            and approval.get('profile') == SELECTION_PROFILE and approval.get('status') == 'PASS'
            and approval.get('actual_assembly_and_stock_loader_pass') is True
            and approval.get('technical_receipt_sha256') == digest(old['technical_receipt']),
            'Historical assembly/loader acceptance differs')
    require(set(a['models']) == set(MODEL_SHA), 'Only original V14 and nominated MATCH38 allowed')
    for role,sha in MODEL_SHA.items():
        path = bound(a,a['models'][role]); record = technical['models'][role]
        require(str(path) == old['models'][role] == record['path'] and digest(path) == sha == record['sha256'],
                'Accepted eval model changed')
    return old


def admission(path,sha):
    require(digest(path) == sha, 'Admission digest differs')
    a = json.loads(Path(path).read_text())
    require(a.get('schema_version') == 1 and a.get('profile') == PROFILE and a.get('stage') == 'confirmation'
            and a.get('start_authorized') is True and a.get('allow_battery') is True,
            'Explicit one-phase confirmation admission required')
    require(safe_path(a['root']) == ROOT == Path.cwd().resolve(), 'Wrong checkout')
    require(source_identity(ROOT,a['python'],a['plans']) == a['source'], 'Current confirmation source differs')
    protected = {str(ROOT/f'agents/sherlock/weights/agent_p{i}.pth'):V14_SHA for i in (0,1)}
    protected[str(ROOT/'Gruppe15.zip')] = ZIP_SHA
    require(a['protected'] == protected and hashes(protected) == protected
            and hashes(a['inputs']) == a['inputs'], 'Protected/input bytes changed')
    output_dir(a); accepted_selection(a)
    require(set(a['cohorts']) == set(COHORTS), 'Exactly two confirmation cohorts required')
    cohorts = {k:read_bound(a,p) for k,p in a['cohorts'].items()}
    require(cohorts == COHORTS and all(type(v) is int for rows in cohorts.values() for v in rows),
            'Fixed confirmation cards differ')
    proof = read_bound(a,a['seed_acceptance'])
    require(proof.get('status') == 'PASS' and proof.get('profile') == PROFILE and proof.get('cohorts') == cohorts
            and proof.get('no_observed_conflicts') is True and bool(proof.get('limitations'))
            and bool(proof.get('files')), 'Missing fresh-card acceptance')
    for p,sha in proof['files'].items(): require(digest(bound(a,p)) == sha, 'Seed evidence changed')
    return a


def job_spec(a,name):
    require(name in JOBS, 'Unknown confirmation job')
    direct = name == 'match_v14'; role = name.split('_',1)[0]
    return dict(role=role,cohort='direct' if direct else 'panel',games=120 if direct else 160,
        opponents=('self:'+a['models']['v14'],) if direct else PANEL,
        csv=str(output_dir(a)/(name+'.csv')))


def performance_command(a,name):
    spec = job_spec(a,name)
    return [a['python'],'-B','-m','scripts.par_eval','--weights',a['models'][spec['role']],
            '--seed-list',a['cohorts'][spec['cohort']],'--workers','1','--opponents',','.join(spec['opponents']),
            '--out',spec['csv']]


def validate_csv(a,name):
    import numpy as np
    import pandas as pd
    from scripts.compare_report import validated_results
    spec = job_spec(a,name); df = pd.read_csv(spec['csv']); checked = validated_results(df,name)
    expected = {(opp,seed,side) for opp in spec['opponents'] for seed in COHORTS[spec['cohort']]
                for side in ('player_0','player_1')}
    require(len(df) == spec['games'] and set(checked[['opponent','seed','side']].itertuples(index=False,name=None)) == expected,
            'Missing/foreign confirmation keys')
    for key in ('steps','point_counting_version','our_points','opp_points','our_wins','opp_wins','game_win'):
        values = pd.to_numeric(df[key],errors='raise')
        require(np.isfinite(values).all() and (values >= 0).all() and (values == np.floor(values)).all(),
                'Invalid integer game metric')
    require(df['steps'].eq(303).all() and df['point_counting_version'].eq(2).all()
            and (df['our_wins']+df['opp_wins'] <= 3).all()
            and np.array_equal(df['result'],np.where(df['our_wins']>df['opp_wins'],1.,
                np.where(df['our_wins']==df['opp_wins'],.5,0.)))
            and np.array_equal(df['game_win'],df['result'].eq(1).astype(int))
            and np.array_equal(df['point_win'],np.where(df['our_points']>df['opp_points'],1.,
                np.where(df['our_points']==df['opp_points'],.5,0.))), 'Incomplete/inconsistent game metrics')
    return df


def gate_checks(counts,panel,direct):
    match,ref = counts['match'],counts['v14']
    return dict(direct_wins=counts['direct']['wins'] >= 72,direct_low=direct['low'] > .5+EPS,
        panel_mean=panel['delta'] >= -EPS,panel_low=panel['low'] >= -.025-EPS,
        solution_wins=match['solution92']['wins'] >= ref['solution92']['wins'],
        default_wins=match['default']['wins'] >= ref['default']['wins'],
        square_wins=match['sol92_sq']['wins'] >= ref['sol92_sq']['wins']-2,
        rush_wins=match['rush']['wins'] >= ref['rush']['wins']-2)


def analyze(a):
    from scripts.compare_report import compare_results
    from scripts.league_gates import panel_delta,direct_result
    frames = {n:validate_csv(a,n) for n in JOBS}
    ref,match,direct_frame = (frames[n] for n in JOBS)
    panel = panel_delta(match,ref,panel=PANEL)
    opponents = {r['opponent']:r for r in compare_results(match,ref)}
    direct = direct_result(direct_frame,opponent='self:'+a['models']['v14'])
    require(panel['maps'] == 20 and direct['maps'] == 60, 'Bootstrap must retain every admitted map')
    def counts(df):
        return dict(wins=int(df.result.eq(1).sum()),draws=int(df.result.eq(.5).sum()),losses=int(df.result.eq(0).sum()))
    absolute = {role:{o:counts(frames[role+'_panel'].loc[frames[role+'_panel'].opponent.eq(o)]) for o in PANEL}
                for role in ('v14','match')}
    absolute['direct'] = counts(direct_frame)
    def constant(values): return bool(values.nunique() == 1)
    contrast = match.groupby('seed').result.mean()-ref.groupby('seed').result.mean()
    degenerate = dict(panel=constant(contrast) or panel['low'] == panel['high'],
        direct=constant(direct_frame.groupby('seed').result.mean()) or direct['low'] == direct['high'],
        opponents={o:constant(match.loc[match.opponent.eq(o)].groupby('seed').result.mean()
                     -ref.loc[ref.opponent.eq(o)].groupby('seed').result.mean())
                     or opponents[o]['low'] == opponents[o]['high'] for o in PANEL})
    checks = gate_checks(absolute,panel,direct)
    return dict(profile=PROFILE,games=440,counts=absolute,panel=panel,opponents=opponents,direct=direct,
        degenerate=degenerate,gates=checks,passed=all(checks.values()),promotion_authorized=False,
        files={job_spec(a,n)['csv']:digest(job_spec(a,n)['csv']) for n in JOBS},
        interpretation='Direct advantage is primary. Panel gates are empirical stability criteria, not a formal '
            'population noninferiority proof at a 2.5 percentage point margin. 5000 PCG64 seed-0 whole-map '
            'resamples; scores count draws as 0.5, win gates count only result==1. Identical map contrasts '
            'produce degenerate intervals, including [0,0], which do not capture unknown-map risks. '
            'No multiplicity correction across project selection, no general 100% guarantee, no isolated '
            'causal match-reward claim. Solution equality does not prove improvement; no automatic promotion.')
