"""Accepted 36+2 behavior ensemble and a separately admitted fixed 200-game screen."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

from scripts import match_weight_compare as legacy
from scripts.early_curriculum_study import digest, hashes, require, source_identity
from scripts.final_training_supervisor import safe_path
from scripts.threat_warmstart import V14_SHA, ZIP_SHA
from scripts.threat_warmstart_compare import bound, read_bound, write, state_equal

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'ensemble_behavior_compare_20261109'
TRAINING_PROFILE = 'ensemble_behavior_20261109'
ROLES = ('v14', 'control', 'behavior')
JOBS = ('v14_solution', 'control_solution', 'behavior_solution', 'behavior_v14', 'behavior_control')
COHORTS = dict(solution=list(range(9990000, 9990020)),
               direct_v14=list(range(9990100, 9990120)), direct_control=list(range(9990200, 9990220)))
REFERENCE_SHA = dict(v14='817e565f8628a3a860c3dcb84e69e9d68c5f0954f791fbd06e0f115bf6cf95d2',
                     control='b8118e6a8a5656a725fa407466833ebcef24d899f00c79e00b3f848086321a95')
REFERENCE_ACCEPTANCE_SHA = 'd7267df0500fc66430adc1be8a96419c24bac06c8e9fc8c01c4304a02dc25db1'
CONTROL_COMPLETION_SHA = '41cb8fa0689bb1a5b98bbd692e147fceb8471b5e72387b661b06e7484c244b94'
CONTROL_FINAL_SHA = ('931ae709779144d578cdf8134f8ef8bb777c653f3f390426a96e03eb141d2429',
                     '499ff53fd318e507e31036b73920e5792b5c47443a24d91d880e7aa2a111ee01')

# Real, previously accepted mounting and stock-loader implementation, unchanged.
mount = legacy.mount
inference_config = legacy.inference_config
validate_and_load = legacy.validate_and_load


def output_dir(a):
    out = safe_path(a['out'])
    require(out.parent == ROOT/'experiments/analysis'/PROFILE
            and out.name == a['stage']+'_v1', 'Wrong exclusive phase output')
    require(all(out != Path(p) and out not in Path(p).parents for p in a['inputs']), 'Output overlaps input')
    return out


def historical_bindings(a, old):
    """New HEAD/additional files are allowed; every old runtime/input byte remains bound."""
    source = old['source']
    require(old['root'] == a['root'] and old['python'] == a['python']
            and old['protected'] == a['protected'] and bool(source['files'])
            and all(a['source']['files'].get(p) == h for p,h in source['files'].items())
            and all(a['source'].get(k) == source[k] for k in ('python','executable','executable_sha256'))
            and hashes(source['files']) == source['files']
            and digest(source['executable']) == source['executable_sha256']
            and all(a['inputs'].get(p) == h for p,h in old['inputs'].items())
            and hashes(old['inputs']) == old['inputs'], 'Historical runtime/input binding changed')


def accepted_references(a):
    """Consume the sealed original assembly; no historical admission() invocation."""
    old = read_bound(a, a['reference_admission'])
    receipt = read_bound(a, a['reference_receipt'])
    approval = read_bound(a, a['reference_acceptance'])
    owner = read_bound(a, a['reference_state'])
    historical_bindings(a, old)
    sha = digest(a['reference_admission']); receipt_sha = digest(a['reference_receipt'])
    require(digest(a['reference_acceptance']) == REFERENCE_ACCEPTANCE_SHA
            and old['profile'] == legacy.PROFILE and old['stage'] == 'technical'
            and approval.get('status') == 'PASS' and approval.get('profile') == legacy.PROFILE
            and approval.get('source') == receipt.get('source') == old['source']
            and approval.get('actual_assembly_and_stock_loader_pass') is True
            and approval.get('source_and_input_bindings_valid') is True
            and approval.get('original_processes_ended') is True
            and approval.get('games') == 0 and approval.get('admission_sha256') == sha
            and approval.get('technical_receipt_sha256') == receipt_sha
            and approval.get('owner_state_sha256') == digest(a['reference_state'])
            and safe_path(a['reference_state']) == safe_path(Path(old['out'])/'state.json')
            and safe_path(a['reference_receipt']) == safe_path(Path(old['out'])/'technical-receipt.json'),
            'Original reference assembly not accepted')
    legacy.check_technical(receipt)
    require(owner.get('status') == 'complete' and owner.get('active') == []
            and owner.get('profile') == legacy.PROFILE and owner.get('stage') == 'technical'
            and owner.get('source') == old['source'] and owner.get('inputs') == old['inputs']
            and owner.get('protected') == a['protected'] and owner.get('admission_sha256') == sha
            and set(owner['jobs']) == {'technical'} and owner['jobs']['technical'].get('returncode') == 0
            and owner.get('receipts') == {'technical':dict(path=a['reference_receipt'],sha256=receipt_sha)}
            and receipt.get('admission_sha256') == sha
            and receipt.get('command') == owner['jobs']['technical']['argv']
            and receipt.get('training_completion_sha256') == CONTROL_COMPLETION_SHA
            and digest(bound(a, old['training_completion'])) == CONTROL_COMPLETION_SHA,
            'Reference owner/training chain differs')
    controls = legacy.accepted_training({**old, 'inputs':a['inputs']})['control']
    require(tuple(digest(r['path']) for r in controls) == CONTROL_FINAL_SHA, 'Wrong historical controls')
    require(receipt['models']['control']['member_sha256'][36:] == [r['identity']['q'] for r in controls],
            'Historical assembly does not append both fixed controls')
    for role, expected in REFERENCE_SHA.items():
        record = receipt['models'][role]
        require(digest(bound(a, record['path'])) == record['sha256'] == expected,
                'Original reference eval bytes changed')
    return receipt, controls


def accepted_training(a):
    """Pure metadata/hash checks of the future Root closure, not replay/model decoding."""
    closure = read_bound(a, a['training_completion'])
    require(closure.get('profile') == TRAINING_PROFILE
            and closure.get('status') == 'COMPLETE_TRAINING_NO_STRENGTH_CLAIM'
            and closure.get('original_processes_ended') is True
            and closure.get('source_and_input_bindings_valid') is True
            and closure.get('protected') == a['protected']
            and closure.get('actual') == dict(technical_games=4, prefill_games=80,
                                             learning_games=800, optimizer_updates=120000)
            and set(closure['models']) == {'on48','on49'} and bool(closure['files']),
            'Both actual ON training arms must be fully accepted')
    for p,h in closure['files'].items(): require(digest(bound(a,p)) == h, 'Closure evidence changed')
    train = read_bound(a, closure['admission']); owner = read_bound(a, closure['state'])
    train_sha = digest(closure['admission'])
    historical_bindings(a, train)
    require(train_sha == closure['admission_sha256'] and digest(closure['state']) == closure['state_sha256']
            and train['profile'] == TRAINING_PROFILE and train['stage'] == 'training'
            and train['starts'] == [48,49] and closure['source'] == train['source']
            and safe_path(closure['state']) == safe_path(Path(train['out'])/'state.json')
            and owner.get('profile') == TRAINING_PROFILE and owner.get('stage') == 'training'
            and owner.get('starts') == [48,49] and owner.get('source') == train['source']
            and owner.get('status') == 'complete' and owner.get('active') == []
            and owner.get('protected') == a['protected'] and owner.get('admission_sha256') == train_sha
            and owner.get('inputs') == {**train['inputs'], closure['admission']:train_sha}
            and set(owner['jobs']) == {'on48','on49'}
            and all(owner['jobs'][r].get('returncode') == 0 for r in ('on48','on49')),
            'Historical ON owner/admission binding differs')
    technical = read_bound(a, train['technical_receipt'])
    approval = read_bound(a, closure['technical_acceptance'])
    require(closure['technical_acceptance'] == train['technical_acceptance']
            and approval.get('profile') == TRAINING_PROFILE and approval.get('status') == 'PASS'
            and approval.get('source') == technical.get('source') == train['source']
            and approval.get('technical_receipt_sha256') == digest(train['technical_receipt'])
            and technical.get('status') == 'complete' and technical.get('stage') == 'technical'
            and len(technical['games']) == 4, 'Missing accepted original OFF/ON technique')
    release_path = str(safe_path(Path(train['out'])/'release.json'))
    release = read_bound(a, release_path)
    require(release.get('profile') == TRAINING_PROFILE and release.get('status') == 'approved'
            and release.get('source') == train['source'] and release.get('starts') == [48,49]
            and release.get('roles') == ['on48','on49'] and release.get('admission_sha256') == train_sha
            and digest(bound(a, release['root_review'])) == release['root_review_sha256']
            and owner.get('release_sha256') == digest(release_path), 'Joint Root release differs')
    required = {closure['admission'],closure['state'],closure['technical_acceptance'],
                train['technical_receipt'],release_path,release['root_review']}
    records = []
    for role in ('on48','on49'):
        start = int(role[-2:]); entry = closure['models'][role]
        final = bound(a,entry['path']); receipt_path = bound(a,entry['receipt'])
        receipt = json.loads(receipt_path.read_text()); receipt_sha = digest(receipt_path)
        require(final == safe_path(Path(train['out'])/role/'final.pth')
                and receipt_path == final.parent/'receipt.json'
                and digest(final) == entry['sha256'] and receipt_sha == entry['receipt_sha256']
                and owner['receipts'].get(role) == dict(path=str(receipt_path),sha256=receipt_sha)
                and owner['final_checks'].get(role) == dict(status='PASS',role=role,start=start,
                        games=440,learn_steps=60000,receipt_sha256=receipt_sha)
                and receipt.get('profile') == TRAINING_PROFILE and receipt.get('status') == 'complete'
                and receipt.get('stage') == 'training' and receipt.get('role') == role
                and receipt.get('start') == start and receipt.get('starts') == [48,49]
                and receipt.get('behavior') == 'ensemble' and receipt.get('source') == train['source']
                and receipt.get('config') == train['config'] and receipt.get('admission_sha256') == train_sha
                and receipt.get('command') == owner['jobs'][role]['argv'] and len(receipt['games']) == 440
                and receipt.get('release_sha256') == digest(release_path)
                and receipt['files'].get(str(final)) == digest(final), 'Accepted ON final binding differs')
        required.update((str(final),str(receipt_path)))
        records.append(dict(path=final,role=role,start=start,source=train['source'],
                            config=train['config'],identity=receipt['final_identity']))
    require(required <= set(closure['files']), 'Closure omits required evidence hashes')
    return records


def fixed_cohorts(a):
    require(set(a['cohorts']) == set(COHORTS), 'Exactly three fixed cohorts required')
    cohorts = {k:read_bound(a,p) for k,p in a['cohorts'].items()}
    require(cohorts == COHORTS and all(type(s) is int for rows in cohorts.values() for s in rows),
            'Cards differ from fixed plan')
    proof = read_bound(a,a['seed_acceptance'])
    require(proof.get('status') == 'PASS' and proof.get('profile') == TRAINING_PROFILE
            and proof.get('cohorts') == cohorts and proof.get('no_observed_conflicts') is True
            and bool(proof.get('limitations')) and bool(proof.get('files')), 'Fixed-card acceptance missing')
    for p,h in proof['files'].items(): require(digest(bound(a,p)) == h, 'Seed evidence changed')
    return cohorts


def accepted_assembly(a):
    """Separate Root acceptance of this new zero-game phase is mandatory for performance."""
    old = read_bound(a,a['technical_admission']); receipt = read_bound(a,a['technical_receipt'])
    approval = read_bound(a,a['technical_acceptance']); owner = read_bound(a,a['technical_state'])
    historical_bindings(a,old); check_technical(receipt)
    sha = digest(a['technical_admission']); receipt_sha = digest(a['technical_receipt'])
    require(old['profile'] == PROFILE and old['stage'] == 'technical' and old['source'] == a['source']
            and old['training_completion'] == a['training_completion']
            and all(old[k] == a[k] for k in ('reference_admission','reference_state','reference_receipt','reference_acceptance'))
            and receipt.get('source') == a['source'] and receipt.get('admission_sha256') == sha
            and receipt.get('training_completion_sha256') == digest(a['training_completion'])
            and receipt.get('reference_receipt_sha256') == digest(a['reference_receipt'])
            and approval.get('profile') == PROFILE and approval.get('status') == 'PASS'
            and approval.get('source') == a['source'] and approval.get('admission_sha256') == sha
            and approval.get('technical_receipt_sha256') == receipt_sha
            and approval.get('owner_state_sha256') == digest(a['technical_state'])
            and approval.get('actual_assembly_and_stock_loader_pass') is True
            and approval.get('original_processes_ended') is True
            and safe_path(a['technical_state']) == safe_path(Path(old['out'])/'state.json')
            and safe_path(a['technical_receipt']) == safe_path(Path(old['out'])/'technical-receipt.json')
            and owner.get('status') == 'complete' and owner.get('active') == []
            and owner.get('profile') == PROFILE and owner.get('stage') == 'technical'
            and owner.get('source') == a['source'] and owner.get('inputs') == old['inputs']
            and owner.get('admission_sha256') == sha and owner.get('protected') == a['protected']
            and set(owner['jobs']) == {'technical'} and owner['jobs']['technical'].get('returncode') == 0
            and receipt.get('command') == owner['jobs']['technical']['argv']
            and owner.get('receipts') == {'technical':dict(path=a['technical_receipt'],sha256=receipt_sha)},
            'Separate Root assembly acceptance required')
    require(set(a['models']) == set(ROLES), 'Exactly three eval copies required')
    reference = read_bound(a,a['reference_receipt'])
    finals = accepted_training(a)
    require(receipt['models']['behavior']['member_sha256'][36:] == [r['identity']['q'] for r in finals],
            'Behavior assembly does not append the accepted two finals')
    for role in ROLES:
        record = receipt['models'][role]; path = bound(a,a['models'][role])
        require(str(path) == record['path'] and digest(path) == record['sha256'], 'Wrong eval copy')
        if role in REFERENCE_SHA:
            require(record == reference['models'][role], 'Reused reference identity changed')
        else:
            require(path == safe_path(Path(old['out'])/'behavior.pth'), 'Wrong new assembly location')
    return receipt


def admission(path,sha,stage):
    require(digest(path) == sha, 'Admission digest differs')
    a = json.loads(Path(path).read_text())
    require(a.get('schema_version') == 1 and a.get('profile') == PROFILE and a.get('stage') == stage
            and stage in ('technical','performance') and a.get('start_authorized') is True
            and a.get('allow_battery') is True, 'Explicit separate phase admission required')
    require(safe_path(a['root']) == ROOT == Path.cwd().resolve(), 'Wrong checkout')
    require(source_identity(ROOT,a['python'],a['plans']) == a['source'], 'Current comparison source differs')
    protected = {str(ROOT/f'agents/sherlock/weights/agent_p{i}.pth'):V14_SHA for i in (0,1)}
    protected[str(ROOT/'Gruppe15.zip')] = ZIP_SHA
    require(a['protected'] == protected and hashes(protected) == protected
            and hashes(a['inputs']) == a['inputs'], 'Protected/input bytes differ')
    require(digest(bound(a,a['training_completion'])) == a['training_completion_sha256'],
            'Root training completion hash differs')
    output_dir(a); _, controls = accepted_references(a); finals = accepted_training(a)
    require(all(r['config'] == controls[i]['config'] for i,r in enumerate(finals)),
            'ON training config differs from fixed historical control')
    require(digest(bound(a,a['v14_source'])) == V14_SHA, 'Original V14 required')
    if stage == 'performance': accepted_assembly(a); fixed_cohorts(a)
    return a


def load_final(record):
    import torch
    from scripts.experiment import state_sha256
    cp = torch.load(record['path'],map_location='cpu',weights_only=True)
    require(cp.get('feature_dim') == 79 and cp.get('n_actions') == 6 and not cp.get('ensemble')
            and not cp.get('ensemble_dims') and cp.get('cfg') == record['config']
            and cp.get('env_steps') == 193320 and cp.get('learn_steps') == 60000
            and cp.get('behavior') == dict(profile=TRAINING_PROFILE,status='complete',role=record['role'],
                start=record['start'],source=record['source'],completed_games=440,component_index=18)
            and {k:state_sha256(cp[v]) for k,v in [('q','q'),('target','target_q'),('optimizer','opt')]}
                == record['identity'], 'Not the accepted final single net')
    return cp


def run_technical(a,path,sha,state_path):
    import torch
    from scripts.ensemble_diversity_train import _source
    from scripts.experiment import state_sha256
    check_owned(a,path,sha,state_path)
    reference, _ = accepted_references(a); finals = accepted_training(a)
    source, originals, _ = _source(bound(a,a['v14_source']))
    original_hashes = [state_sha256(sd) for sd in originals]
    require(original_hashes == reference['models']['v14']['member_sha256'], 'Original 36 order changed')
    models = {}; out = output_dir(a)
    for role in ROLES:
        check_owned(a,path,sha,state_path)
        if role in REFERENCE_SHA:
            record = reference['models'][role]; model_path = bound(a,record['path'])
            cp = torch.load(model_path,map_location='cpu',weights_only=True)
            expected = [cp['q'],*cp['ensemble']]
            require([state_sha256(sd) for sd in expected] == record['member_sha256']
                    and state_equal(expected[:36],originals), 'Reused actual member bytes/order changed')
        else:
            additions = [load_final(r) for r in finals]
            cp = mount(source,additions); model_path = safe_path(out/'behavior.pth')
            require(not model_path.exists(), 'Assembly exists; no overwrite')
            with model_path.open('xb') as handle: torch.save(cp,handle)
            cp = torch.load(model_path,map_location='cpu',weights_only=True)
            expected = [*originals,*(f['q'] for f in additions)]
        require(cp['cfg'] == inference_config(source) and state_equal(cp['target_q'],source['target_q']),
                'Original inference config/target differs')
        agent = validate_and_load(model_path,cp,expected)
        models[role] = dict(path=str(model_path),sha256=digest(model_path),members=len(expected),
            member_sha256=[state_sha256(sd) for sd in expected],loader_pass=True,batches=[1,8,16])
        del agent, cp, expected
    check_owned(a,path,sha,state_path)
    receipt = dict(status='complete',profile=PROFILE,source=a['source'],admission_sha256=sha,
        training_completion_sha256=digest(a['training_completion']),
        reference_receipt_sha256=digest(a['reference_receipt']),command=technical_command(a,path,sha),
        models=models,games=0,no_strength_claim=True)
    check_technical(receipt); write(out/'technical-receipt.json',receipt)


def check_technical(receipt):
    require(receipt.get('status') == 'complete' and receipt.get('profile') == PROFILE
            and receipt.get('games') == 0 and receipt.get('no_strength_claim') is True
            and set(receipt['models']) == set(ROLES), 'Incomplete assembly/loader check')
    for role in ROLES:
        r = receipt['models'][role]; count = 36 if role == 'v14' else 38
        require(r['members'] == len(r['member_sha256']) == count and r['loader_pass'] is True
                and r['batches'] == [1,8,16]
                and r['member_sha256'][:36] == receipt['models']['v14']['member_sha256'],
                'Actual stock loader/original member check missing')


def technical_command(a,path,sha):
    return [a['python'],'-B','-m','scripts.ensemble_behavior_compare','technical',
            '--admission',str(path),'--admission-sha',sha,'--owner-state',str(output_dir(a)/'state.json')]


def check_owned(a,path,sha,state_path):
    deadline = time.monotonic()+5
    while True:
        state = json.loads(Path(state_path).read_text()); job = state.get('jobs',{}).get('technical',{})
        if job or time.monotonic() >= deadline: break
        time.sleep(.05)
    command = technical_command(a,path,sha)
    require(safe_path(state_path) == output_dir(a)/'state.json'
            and state.get('status') == 'running' and state.get('profile') == PROFILE
            and state.get('stage') == 'technical' and state.get('active') == ['technical']
            and state.get('admission_sha256') == sha
            and state.get('owner_pid') == job.get('owner_pid') == os.getppid() > 1
            and job.get('pid') == job.get('pgid') == os.getpid() == os.getpgrp()
            and job.get('argv') == command and getattr(sys,'orig_argv',[])[1:] == command[1:]
            and sys.executable == a['python'] and digest(path) == sha,
            'Technical worker lacks exact live ownership')
    require(all(state.get(k) == a[k] for k in ('root','out','source','inputs','protected',
            'stop_file','allow_battery','python','plans')), 'Owner/input binding differs')
    from scripts.fog_reward_supervisor import guard
    guard(state,{},allow_battery=True)


def job_spec(a,name):
    require(name in JOBS, 'Unknown fixed job')
    role, suffix = name.split('_',1)
    cohort = 'solution' if suffix == 'solution' else 'direct_'+suffix
    return dict(role=role,cohort=cohort,opponent='solution92' if suffix == 'solution' else 'self:'+a['models'][suffix],
                csv=str(output_dir(a)/(name+'.csv')))


def performance_command(a,name):
    spec = job_spec(a,name)
    return [a['python'],'-B','-m','scripts.par_eval','--weights',a['models'][spec['role']],
            '--seed-list',a['cohorts'][spec['cohort']],'--workers','1',
            '--opponents',spec['opponent'],'--out',spec['csv']]


def validate_csv(a,name):
    import numpy as np
    import pandas as pd
    from scripts.compare_report import validated_results
    spec = job_spec(a,name); df = pd.read_csv(spec['csv']); checked = validated_results(df,name)
    seeds = read_bound(a,a['cohorts'][spec['cohort']])
    require(seeds == COHORTS[spec['cohort']], 'CSV cohort differs from fixed cards')
    expected = {(spec['opponent'],s,side) for s in seeds for side in ('player_0','player_1')}
    require(len(df) == 40 and set(checked[['opponent','seed','side']].itertuples(index=False,name=None)) == expected,
            'Wrong/missing fixed games')
    for key in ('steps','point_counting_version','our_points','opp_points','our_wins','opp_wins','game_win'):
        values = pd.to_numeric(df[key],errors='raise')
        require(np.isfinite(values).all() and (values >= 0).all() and (values == np.floor(values)).all(),
                'Invalid integer game metric')
    require(df['steps'].eq(303).all() and df['point_counting_version'].eq(2).all()
            and (df['our_wins']+df['opp_wins'] <= 3).all()
            and np.array_equal(df['result'],np.where(df['our_wins'] > df['opp_wins'],1.,
                np.where(df['our_wins'] == df['opp_wins'],.5,0.)))
            and np.array_equal(df['game_win'],df['result'].eq(1).astype(int))
            and np.array_equal(df['point_win'],np.where(df['our_points'] > df['opp_points'],1.,
                np.where(df['our_points'] == df['opp_points'],.5,0.))), 'Incomplete/inconsistent result')
    return df


def analyze(a):
    from scripts.compare_report import compare_results
    from scripts.league_gates import direct_result
    # All five real CSVs and exact keys pass before any gate or interval is computed.
    frames = {n:validate_csv(a,n) for n in JOBS}
    counts = {n:dict(wins=int(df.result.eq(1).sum()),draws=int(df.result.eq(.5).sum()),
                    losses=int(df.result.eq(0).sum())) for n,df in frames.items()}
    w = {n:c['wins'] for n,c in counts.items()}
    gates = dict(solution_v14=w['behavior_solution'] >= w['v14_solution'],
                 solution_control=w['behavior_solution'] >= w['control_solution'],
                 direct_v14=w['behavior_v14'] >= 24,direct_control=w['behavior_control'] >= 24)
    solution = {}; direct = {}
    for role in ('v14','control'):
        rows = compare_results(frames['behavior_solution'],frames[role+'_solution'])
        require(len(rows) == 1 and rows[0]['opponent'] == 'solution92' and rows[0]['maps'] == 20
                and rows[0]['games'] == 40 and rows[0]['excluded_candidate'] == rows[0]['excluded_reference'] == 0,
                'Paired statistics excluded fixed games')
        rows[0]['degenerate_interval'] = rows[0]['low'] == rows[0]['high']; solution[role] = rows
        result = direct_result(frames['behavior_'+role],job_spec(a,'behavior_'+role)['opponent'])
        require(result['maps'] == 20 and result['games'] == 40, 'Direct statistics incomplete')
        result['degenerate_interval'] = result['low'] == result['high']; direct[role] = result
    return dict(profile=PROFILE,games=200,counts=counts,gates=gates,nominated=all(gates.values()),
        solution=solution,direct=direct,files={job_spec(a,n)['csv']:digest(job_spec(a,n)['csv']) for n in JOBS},
        interpretation='5000 PCG64 seed-0 whole-map bootstrap draws, descriptive 95% score intervals; '
            'draw=0.5 in scores, gates count actual wins only. Degenerate intervals are empirical, not '
            'proof of zero uncertainty. Historical controls are not new independent training replicates; '
            'repeated project selection, no multiplicity correction. Nomination only; no automatic '
            'confirmation, promotion, extra games or resumed phase.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('technical',))
    parser.add_argument('--admission',type=Path,required=True); parser.add_argument('--admission-sha',required=True)
    parser.add_argument('--owner-state',type=Path,required=True)
    args = parser.parse_args(); a = admission(args.admission,args.admission_sha,'technical')
    run_technical(a,args.admission.resolve(),args.admission_sha,args.owner_state.resolve())


if __name__ == '__main__': main()
