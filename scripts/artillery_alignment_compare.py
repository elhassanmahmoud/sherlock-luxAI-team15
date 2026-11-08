"""Fixed Artillery alignment comparison: exact36+2 assembly,440 screen, at most600 confirm.

Historical training is admitted by its immutable acceptance, never by weakening
its CURRENT-HEAD training validator. No training, promotion or automatic retry.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from scripts import ensemble_diversity_compare as C
from scripts import ensemble_diversity_eval_supervisor as S
from scripts.fog_reward_compare import historical_path,checked_checkpoint

ROOT=Path(__file__).resolve().parents[1]
PROFILE='artillery_alignment_20261108'
ANALYSIS=Path('experiments/analysis/artillery_comparison_20261108')
CANDIDATE_DIR=Path('experiments/candidates/artillery_alignment_20261108')
PROTOCOL='docs/superpowers/plans/2026-11-08-artillery-comparison.md'
SPEC='docs/superpowers/specs/2026-11-08-artillery-comparison.md'
SIZING='experiments/analysis/artillery_alignment_20261108/operations/comparison-sizing.md'
ACCEPTANCE=Path('experiments/analysis/artillery_alignment_20261108/operations/historical_training_acceptance.json')
# Root pins actual completed acceptance bytes before installing/running this adapter.
ACCEPTANCE_SHA256='34395fb96b8245a7cca7088cdb04acdd881dd1c037f9f7c0b688affb093f7712'
TRAINING_HEAD='02ce1b2ce9a5b0780da1ee6462a2368b2226d495'
SEED_ACCEPTANCE=ANALYSIS/'operations/seed_acceptance.json'
SEED_ACCEPTANCE_SHA256='9417e1526dfb29efa2e2ce8eca42486aa8a94c4f9118eab63712e22ab0676c21'
SOURCE_SHA=C.OPPONENT_SHA256[C.V14_PATH]
CANDIDATES=('CONTROL38','ALIGNED38')
ARMS=('control43','aligned43','control44','aligned44')
ROLE_PATHS={'V14':C.V14_PATH,**{r:str(CANDIDATE_DIR/f'{r}.pth') for r in CANDIDATES}}
SCREEN_PANEL=('solution92','sol92_sq')
SCREEN_OPPONENTS=SCREEN_PANEL+('default',)
COHORTS={'selection':(9800000,20,9800100,20),'confirmation':(9801000,20,9801100,20)}
TOTALS={'selection':440,'confirmation':600}
RECEIPT_COUNTS=dict(actual_prefill_games=40,actual_train_games=400,actual_validation_games=32,
                    learn_steps=60000,env_steps=193320)
COUNTS=dict(RECEIPT_COUNTS,executions=472)
TRAINING_TOTALS=dict(actual_prefill_games=160,actual_train_games=1600,actual_validation_games=128,
                    executions=1888,learn_steps=240000)
# Historical receipt schema, copied literally without importing the training runtime.
RECEIPT_FILES=('weights/agent.pth','weights/agent.buffer.npz','rollouts.jsonl',
    'validation_games.jsonl','training_audit.json','train.csv','prefill_proof.json',
    'prefill_bundle.json','prefill_events.jsonl')
require=C.require


def _expected_config(cfg,arm):
    return dict(cfg,frozen=False,lr=5e-5,rules_in_training=True,rules_in_training_all=True,
        rescue_in_training=True,fog_unknown_reward_neutral=False,art_splash_in_training=arm.startswith('aligned'))


def historical_acceptance(root=ROOT):
    """Check every accepted artifact and protected binding; permit a new phase HEAD."""
    require(C._hex(ACCEPTANCE_SHA256),'Historical training acceptance not yet pinned')
    root=Path(root).resolve();path=S.repo_path(root,str(ACCEPTANCE))
    require(C.digest(path)==ACCEPTANCE_SHA256,'Historical acceptance trust-anchor hash changed')
    accepted=C._load_json(path)
    expected=dict(schema_version=1,status='PASS',eligible_for_comparison=True,training_head=TRAINING_HEAD,
        totals=TRAINING_TOTALS)
    require(all(accepted.get(k)==v for k,v in expected.items()) and set(accepted.get('arms',{}))==set(ARMS),
            'Incomplete historical training acceptance')
    old_root=accepted['root'];source=accepted['source']
    require(Path(old_root).is_absolute() and '..' not in Path(old_root).parts,'Historical root is invalid')
    require(source.get('head')==TRAINING_HEAD and bool(source.get('files')),'Historical source identity missing')
    bound={str(path):ACCEPTANCE_SHA256}
    for group in ('files','protected'):
        bindings=accepted.get(group)
        require(isinstance(bindings,dict) and bool(bindings),'Missing historical artifact bindings')
        for old,sha in bindings.items():
            target=historical_path(root,old_root,old,protected=group=='protected')
            require(C._hex(sha) and C.digest(target)==sha,'Accepted historical artifact/protected hash changed')
            require(str(target) not in bound or bound[str(target)]==sha,'Contradictory historical path aliases')
            bound[str(target)]=sha
    # Every referenced proof must be bound in files, not only in protected.
    def artifact(value,sha=None):
        target=historical_path(root,old_root,value)
        actual=accepted['files'].get(value)
        require(C._hex(actual) and bound.get(str(target))==actual and (sha is None or actual==sha),
                'Missing historical artifact binding')
        return target
    def evidence(item):
        require(isinstance(item,dict) and set(item)=={'path','sha256'},'Missing historical evidence reference')
        return C._load_json(artifact(item['path'],item['sha256']))
    prepared=artifact(accepted['prepared']+'/manifest.json',accepted['prepared_manifest_sha256'])
    manifest=C._load_json(prepared)
    cfg=manifest.get('source_config',{})
    require(manifest.get('source_sha256')==SOURCE_SHA and manifest.get('pins')==dict(source=source,protected=accepted['protected'])
        and set(manifest.get('arms',{}))==set(ARMS) and cfg.get('art_splash_in_training') is False
        and cfg.get('fog_unknown_reward_neutral') is False,'Prepared historical provenance/config differs')
    artifact(accepted['prepared']+'/supervisor_launch.json')
    protected={str(historical_path(root,old_root,p,protected=True)):sha for p,sha in accepted['protected'].items()}
    require(all(protected.get(str(root/f'agents/sherlock/weights/agent_p{i}.pth'))==SOURCE_SHA for i in (0,1))
        and C._hex(protected.get(str(root/'Gruppe15.zip'))),'Protected V14/ZIP acceptance missing')
    for arm,item in accepted['arms'].items():
        require(item.get('counts')==COUNTS and isinstance(item.get('files'),dict),'Wrong historical arm budget')
        for old,sha in item['files'].items():
            target=historical_path(root,old_root,old)
            require(bound.get(str(target))==sha,'Arm file absent from historical acceptance inventory')
        receipt_path=artifact(item['receipt_path'],item['receipt_sha256'])
        checkpoint=artifact(item['checkpoint_path'],item['final_checkpoint_sha256'])
        require(receipt_path.name=='final_receipt.json' and checkpoint==receipt_path.parent/'weights/agent.pth',
            'Historical final checkpoint path differs')
        receipt=C._load_json(receipt_path)
        entry=manifest['arms'][arm]
        expected_arm=dict(schema_version=1,status='done',eligible=False,arm=arm,source_sha256=SOURCE_SHA,
            component_index=18,run_seed=int(arm[-2:]),**RECEIPT_COUNTS)
        require(all(receipt.get(k)==v for k,v in expected_arm.items())
            and receipt.get('eligible') is False and receipt.get('pins')==manifest['pins']
            and receipt.get('prepared')==accepted['prepared'] and receipt.get('config')==entry.get('config')==_expected_config(cfg,arm)
            and receipt.get('initial_tensor_sha256')==entry.get('tensor_sha256') and C._hex(entry.get('tensor_sha256'))
            and C._hex(entry.get('weights_sha256'))
            and entry.get('component_index')==18 and entry.get('run_seed')==int(arm[-2:]),
            'Historical arm receipt/provenance differs')
        require(set(receipt.get('artifacts',{}))==set(RECEIPT_FILES),'Historical receipt artifact schema differs')
        expected_files={item['receipt_path']:item['receipt_sha256']}
        for name in RECEIPT_FILES:
            old=str(Path(item['receipt_path']).parent/name);sha=receipt['artifacts'][name]
            artifact(old,sha);expected_files[old]=sha
        require(item['files']==expected_files and receipt['artifacts']['weights/agent.pth']==item['final_checkpoint_sha256'],
                'Arm omits required receipt/raw files')
        artifact(str(Path(accepted['prepared'])/arm/'weights/agent.pth'),entry.get('weights_sha256'))
        local=C._load_json(artifact(str(Path(accepted['prepared'])/arm/'manifest.json')))
        require(local==dict(variant=PROFILE,base_variant=PROFILE,train_games=0,arm=arm,**entry),
                'Prepared local manifest differs')
    state=evidence(accepted.get('supervisor'))
    require(state.get('status')=='done' and state.get('eligible') is False and not state.get('active')
        and not state.get('queue') and state.get('source')==source and state.get('prepared')==accepted['prepared']
        and state.get('protected')==accepted['protected'] and set(state.get('jobs',{}))==set(ARMS)
        and set(state.get('receipts',{}))==set(ARMS),'Training supervisor was not completely finished')
    for arm,item in accepted['arms'].items():
        job=state['jobs'][arm]
        require(type(job.get('returncode')) is int and job['returncode']==0 and job.get('finished_at') is not None
            and state['receipts'][arm]=={item['receipt_path']:item['receipt_sha256']},'Training job/receipt not successful')
    pairs=accepted.get('paired_prefill',{})
    require(set(pairs)=={'43','44'} and set(state.get('paired_prefill',{}))==set(pairs),'Missing paired prefill admission')
    for seed,item in pairs.items():
        pair=evidence(item)
        proofs={a:{str(Path(accepted['arms'][a]['receipt_path']).parent/'prefill_proof.json'):
            accepted['arms'][a]['files'][str(Path(accepted['arms'][a]['receipt_path']).parent/'prefill_proof.json')]}
            for a in (f'control{seed}',f'aligned{seed}')}
        require(pair==state['paired_prefill'][seed] and pair.get('status')=='matched' and pair.get('eligible') is False
            and pair.get('run_seed')==int(seed) and pair.get('proof_sha256')==proofs,'Paired prefill admission differs')
    audit=evidence(accepted.get('independent_audit'))
    require(audit.get('status')=='PASS_DATA_ONLY' and audit.get('source_head')==TRAINING_HEAD,
            'Independent historical data audit missing')
    validation=evidence(accepted.get('root_validation'))
    require(validation.get('status')=='PASS' and validation.get('training_head')==TRAINING_HEAD
        and validation.get('validator')=='scripts.artillery_alignment_study.validate_final_receipt'
        and set(validation.get('arms',{}))==set(ARMS),'Original training validators were not accepted')
    for arm,item in accepted['arms'].items():
        require(validation['arms'][arm]==dict(status='PASS',receipt_sha256=item['receipt_sha256'],
            env_steps=193320,learn_steps=60000),'Root tensor/reload validation receipt differs')
    return accepted,bound


def build_candidates(*,root=ROOT):
    """Exclusive deterministic assembly; no games and no component selection."""
    root=Path(root).resolve();accepted,bindings=historical_acceptance(root)
    import torch
    from scripts.night_train_pilot import tensor_sha256
    original=S.repo_path(root,ROLE_PATHS['V14'])
    require(C.digest(original)==SOURCE_SHA,'Exact archived V14 required')
    source=torch.load(original,map_location='cpu',weights_only=True)
    cfg,original_hashes=checked_checkpoint(source,36)
    require(cfg['art_splash_in_training'] is False and cfg['fog_unknown_reward_neutral'] is False,
            'V14 inference training flags must be False')
    manifest=C._load_json(historical_path(root,accepted['root'],accepted['prepared']+'/manifest.json'))
    require(cfg==manifest['source_config'],'Archived V14 configuration differs from accepted training source')
    checkpoints={}
    for arm in ARMS:
        item=accepted['arms'][arm]
        path=historical_path(root,accepted['root'],item['checkpoint_path'])
        cp=torch.load(path,map_location='cpu',weights_only=True)
        expected=_expected_config(cfg,arm)
        checked_checkpoint(cp,1,expected)
        receipt=C._load_json(historical_path(root,accepted['root'],item['receipt_path']))
        require(cp['cfg']==receipt['config'] and cp.get('env_steps')==193320 and cp.get('learn_steps')==60000
                and tensor_sha256(cp['q'])!=receipt['initial_tensor_sha256'],'Final arm checkpoint differs from accepted final state')
        checkpoints[arm]=cp
    destination=S.repo_path(root,str(CANDIDATE_DIR))
    require(not destination.exists(),'Candidate output already exists; never overwrite or resume')
    destination.parent.mkdir(parents=True,exist_ok=True);destination.mkdir()
    roles={'V14':dict(path=ROLE_PATHS['V14'],sha256=SOURCE_SHA,members=original_hashes)}
    for role,prefix in (('CONTROL38','control'),('ALIGNED38','aligned')):
        arms=[prefix+'43',prefix+'44']
        cp=copy.deepcopy(source)
        cp['cfg']=cfg.copy()
        cp['ensemble']=[*source.get('ensemble',[]),*(checkpoints[a]['q'] for a in arms)]
        cp['ensemble_dims']=[79]*37
        cp['ensemble_sources']=[ROLE_PATHS['V14'],*(str(historical_path(root,accepted['root'],accepted['arms'][a]['checkpoint_path']).relative_to(root)) for a in arms)]
        expected=original_hashes+[tensor_sha256(checkpoints[a]['q']) for a in arms]
        _,actual=checked_checkpoint(cp,38,cfg)
        require(actual==expected,'Candidate membership/order differs from original36+final43/44')
        path=S.repo_path(root,ROLE_PATHS[role])
        with path.open('xb') as stream: torch.save(cp,stream)
        loaded=torch.load(path,map_location='cpu',weights_only=True)
        _,reloaded=checked_checkpoint(loaded,38,cfg)
        require(reloaded==expected,'Reloaded candidate membership/order differs')
        roles[role]=dict(path=ROLE_PATHS[role],sha256=C.digest(path),members=expected)
    require(C.digest(original)==SOURCE_SHA and all(C.digest(Path(p))==sha for p,sha in bindings.items()),
            'Historical inputs/source changed during assembly')
    admission=dict(schema_version=1,status='admitted',profile=PROFILE,acceptance_sha256=ACCEPTANCE_SHA256,
        build_root=str(root),historical_source=accepted['source'],input_sha256={**bindings,str(original):SOURCE_SHA},
        inference_config=cfg,aggregation='uniform arithmetic mean of all38 Q networks',
        roles=roles,reload_verified=True,promoted=False)
    S.exclusive_json(destination/'admission.json',admission)
    return admission


def validate_admission(path,*,root=ROOT):
    """Byte/provenance admission after build; the phase freezes these same bytes."""
    root=Path(root).resolve();accepted,bindings=historical_acceptance(root)
    path=S.helpers().safe_path(path)
    require(path==root/CANDIDATE_DIR/'admission.json','Wrong candidate admission path')
    record=C._load_json(path)
    require(record.get('status')=='admitted' and record.get('profile')==PROFILE
        and record.get('acceptance_sha256')==ACCEPTANCE_SHA256 and record.get('reload_verified') is True
        and record.get('historical_source')==accepted['source']
        and record.get('aggregation')=='uniform arithmetic mean of all38 Q networks'
        and set(record.get('roles',{}))==set(ROLE_PATHS),'Invalid candidate admission/provenance')
    expected_inputs={**bindings,str(root/ROLE_PATHS['V14']):SOURCE_SHA}
    saved_bindings=record.get('input_sha256')
    require(isinstance(saved_bindings,dict),'Missing candidate input bindings')
    rebased={str(historical_path(root,record.get('build_root',''),p)):sha for p,sha in saved_bindings.items()}
    require(rebased==expected_inputs,'Candidate admission omits accepted input bindings')
    for role,relative in ROLE_PATHS.items():
        entry=record['roles'][role]
        require(entry.get('path')==relative and C._hex(entry.get('sha256'))
            and C.digest(S.repo_path(root,relative))==entry['sha256']
            and len(entry.get('members',[]))==(36 if role=='V14' else 38),'Candidate file/order admission changed')
    require(record['roles']['V14']['sha256']==SOURCE_SHA
        and record['inference_config']['art_splash_in_training'] is False
        and record['inference_config']['fog_unknown_reward_neutral'] is False,'Inference/source differs')
    import torch
    from scripts.night_train_pilot import tensor_sha256
    base=torch.load(root/ROLE_PATHS['V14'],map_location='cpu',weights_only=True)
    cfg,base_hashes=checked_checkpoint(base,36)
    require(record['inference_config']==cfg and record['roles']['V14']['members']==base_hashes,
            'Original inference configuration/member order differs')
    for role,prefix in (('CONTROL38','control'),('ALIGNED38','aligned')):
        expected=base_hashes.copy()
        for seed in (43,44):
            arm=prefix+str(seed)
            checkpoint=torch.load(historical_path(root,accepted['root'],accepted['arms'][arm]['checkpoint_path']),
                                  map_location='cpu',weights_only=True)
            expected.append(tensor_sha256(checkpoint['q']))
        candidate=torch.load(root/ROLE_PATHS[role],map_location='cpu',weights_only=True)
        _,actual=checked_checkpoint(candidate,38,cfg)
        require(actual==expected and record['roles'][role]['members']==expected,
                'Candidate is not exact ordered original36+final43/44')
    return record,{**expected_inputs,str(path):C.digest(path),
                  **{str(root/r['path']):r['sha256'] for r in record['roles'].values()}}


def cohort(phase):
    require(phase in COHORTS,'Invalid comparison phase');return COHORTS[phase]


def seed_cohorts():
    return {f'{phase}_{kind}':list(range(start,start+count)) for phase in COHORTS
        for kind,start,count in (('panel',cohort(phase)[0],cohort(phase)[1]),
                                ('direct',cohort(phase)[2],cohort(phase)[3]))}


def freshness_acceptance(root=ROOT):
    """No performance launch until the prospective lists have a pinned root acceptance."""
    require(C._hex(SEED_ACCEPTANCE_SHA256),'Comparison seed acceptance not yet pinned')
    root=Path(root).resolve();path=S.repo_path(root,str(SEED_ACCEPTANCE))
    require(C.digest(path)==SEED_ACCEPTANCE_SHA256,'Comparison seed acceptance changed')
    accepted=C._load_json(path)
    require(all(accepted.get(k)==v for k,v in dict(schema_version=1,status='PASS',profile=PROFILE,
        cohorts=seed_cohorts()).items()),'Wrong accepted fresh comparison cohorts')
    bound={str(path):SEED_ACCEPTANCE_SHA256}
    def artifact(item):
        require(isinstance(item,dict) and set(item)=={'path','sha256'} and C._hex(item['sha256']),
                'Missing freshness audit reference')
        target=S.repo_path(root,item['path'])
        require(C.digest(target)==item['sha256'],'Freshness audit artifact changed')
        bound[str(target)]=item['sha256'];return target
    audit=C._load_json(artifact(accepted.get('audit')))
    require(audit.get('status')=='PASS' and audit.get('no_observed_conflicts') is True
        and isinstance(audit.get('limitations'),list) and bool(audit['limitations']),
            'Missing target-specific seed audit acceptance/limitations')
    artifact(audit.get('raw_audit'))
    for relative,sha in audit.get('files',{}).items(): artifact(dict(path=relative,sha256=sha))
    for name,seeds in seed_cohorts().items():
        target=S.repo_path(root,str(ANALYSIS/'plans'/f'{name}.json'))
        require(C._seeds(C._load_json(target))==seeds,'Fresh accepted seed list differs')
        bound[str(target)]=C.digest(target)
    return accepted,bound


def expected_jobs(phase,nominee=None):
    cohort(phase)
    require(nominee is None if phase=='selection' else nominee in CANDIDATES,'Invalid fixed nominee')
    roles=tuple(ROLE_PATHS) if phase=='selection' else ('V14',nominee)
    opponents=SCREEN_OPPONENTS if phase=='selection' else C.OPPONENTS
    jobs={f'{r}_panel_{i}':(r,'panel',o) for r in roles for i,o in enumerate(opponents)}
    jobs.update({f'{r}_direct':(r,'direct',C.V14_LABEL) for r in roles if r!='V14'})
    return roles,jobs


def prepare_plans(*,root=ROOT):
    """New immutable four seed lists and selection plan; confirmation is emitted only after nomination."""
    root=Path(root).resolve();base=S.repo_path(root,str(ANALYSIS/'plans'))
    require(not base.exists(),'Comparison plans already exist; no overwrite')
    base.mkdir(parents=True)
    for phase in COHORTS:
        first,maps,direct_first,direct_maps=cohort(phase)
        for kind,start,count in (('panel',first,maps),('direct',direct_first,direct_maps)):
            S.exclusive_json(base/f'{phase}_{kind}.json',list(range(start,start+count)))
    plan=make_plan('selection')
    S.exclusive_json(base/'selection_jobs.json',plan)
    validate_plan(plan,root,phase='selection')
    return plan


def make_plan(phase,nominee=None):
    roles,jobs=expected_jobs(phase,nominee);_,maps,_,direct_maps=cohort(phase)
    return dict(profile=PROFILE,protocol=PROTOCOL,phase=phase,nominee=nominee,
        roles={r:ROLE_PATHS[r] for r in roles},total_games=TOTALS[phase],
        max_simultaneous_model_processes=2,opponent_sha256=C.OPPONENT_SHA256.copy(),
        jobs=[dict(name=name,role=r,kind=kind,weights=ROLE_PATHS[r],opponent=o,
            seed_list=str(ANALYSIS/'plans'/f'{phase}_{kind}.json'),
            expected_games=2*(direct_maps if kind=='direct' else maps),workers=1)
            for name,(r,kind,o) in jobs.items()])


def validate_plan(plan,root,*,phase,nominee=None):
    expected=make_plan(phase,nominee)
    require(plan==expected,'Plan differs from exact fixed440/600 job/role/cohort matrix')
    require(type(plan['total_games']) is int and type(plan['max_simultaneous_model_processes']) is int
        and all(type(j['workers']) is int and type(j['expected_games']) is int for j in plan['jobs']),
        'Job/process/game counts must be integers, not booleans')
    root=Path(root).resolve()
    for relative,sha in C.OPPONENT_SHA256.items():
        require(C.digest(S.repo_path(root,relative))==sha,'Pinned opponent changed')
    jobs=[];first,maps,direct_first,direct_maps=cohort(phase)
    for job in plan['jobs']:
        seeds=C._seeds(C._load_json(S.repo_path(root,job['seed_list'])))
        start,count=(direct_first,direct_maps) if job['kind']=='direct' else (first,maps)
        require(seeds==list(range(start,start+count)),'Wrong fixed seed list')
        jobs.append({**job,'seeds':seeds})
    return jobs


def _subset(frame,opponents): return frame[frame['opponent'].isin(opponents)]


def selection_checks(reference,candidate,direct,*,name):
    from scripts.compare_report import compare_results
    from scripts.league_gates import panel_delta,direct_result
    require(name in CANDIDATES,'Unknown Artillery candidate')
    reference=C._checked_frame(reference,SCREEN_OPPONENTS,9800000,20)
    candidate=C._checked_frame(candidate,SCREEN_OPPONENTS,9800000,20)
    direct=C._checked_frame(direct,(C.V14_LABEL,),9800100,20)
    by={row['opponent']:row for row in compare_results(candidate,reference)}
    panel=C._score_stats(panel_delta(candidate,reference,panel=SCREEN_PANEL),_subset(candidate,SCREEN_PANEL),_subset(reference,SCREEN_PANEL))
    result=dict(panel=panel,direct=C._score_stats(direct_result(direct,C.V14_LABEL),direct),
        **{o:C._score_stats(by[o],_subset(candidate,(o,)),_subset(reference,(o,))) for o in SCREEN_OPPONENTS})
    gain=panel['candidate']['half_wins']-panel['reference']['half_wins']
    sol=result['solution92'];dfl=result['default']['candidate'];duel=result['direct']['candidate']
    checks=dict(panel_half_win_gain_ge4=gain>=4,
        solution_score_nonnegative=sol['candidate']['half_wins']>=sol['reference']['half_wins'],
        solution_strict_wins_nonnegative=sol['candidate']['wins']>=sol['reference']['wins'],
        default40_strict_wins=dfl['wins']==40,direct_score_ge50pct=duel['half_wins']>=40)
    return dict(**result,panel_half_win_gain=gain,checks=checks,passed=all(checks.values()),nominable=True)


def choose_nominee(results):
    require(set(results)==set(CANDIDATES),'Both fixed candidates must be complete')
    eligible=[r for r in CANDIDATES if results[r]['passed']]
    return min(eligible,key=lambda r:(-results[r]['panel']['candidate']['half_wins'],
        -results[r]['solution92']['candidate']['wins'],-results[r]['direct']['candidate']['half_wins'],
        CANDIDATES.index(r))) if eligible else None


def confirmation_checks(reference,candidate,direct,*,name):
    from scripts.league_gates import confirm_checks
    require(name in CANDIDATES,'Invalid Artillery nominee')
    reference=C._checked_frame(reference,C.OPPONENTS,9801000,20)
    candidate=C._checked_frame(candidate,C.OPPONENTS,9801000,20)
    direct=C._checked_frame(direct,(C.V14_LABEL,),9801100,20)
    stats=confirm_checks(reference,candidate,direct,direct_opponent=C.V14_LABEL,
        panel=C.LOCAL_SIX,min_delta=.01,label='Local six score')
    result=C._report_stats(reference,candidate,direct,stats)
    checks={**stats['checks'],**C._additional_checks(result)}
    return dict(**result,checks=checks,passed=all(checks.values()),nominable=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('action',choices=('build','prepare-plans'))
    args=parser.parse_args()
    result=build_candidates() if args.action=='build' else prepare_plans()
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__': main()
