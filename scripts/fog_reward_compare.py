"""Fixed Fog reward comparison: exact36+2 assembly,440 screen, at most1200 confirm.

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

ROOT=Path(__file__).resolve().parents[1]
PROFILE='fog_reward_20261108'
ANALYSIS=Path('experiments/analysis/fog_comparison_20261108')
CANDIDATE_DIR=Path('experiments/candidates/fog_reward_20261108')
PROTOCOL='docs/superpowers/plans/2026-11-08-fog-comparison.md'
SPEC='docs/superpowers/specs/2026-11-08-fog-comparison.md'
ACCEPTANCE=Path('experiments/analysis/fog_reward_20261108/operations/historical_training_acceptance.json')
ACCEPTANCE_SHA256='8cfea7a7e28cdd010de1ef9693334f028ce8e3b52716805c5d91b6b0ec528e7b'
TRAINING_HEAD='a3111c3d0aa0aa974298daabe300bba7be157da1'
SOURCE_SHA=C.OPPONENT_SHA256[C.V14_PATH]
CANDIDATES=('CONTROL38','NEUTRAL38')
ARMS=('control41','neutral41','control42','neutral42')
ROLE_PATHS={'V14':C.V14_PATH,**{r:str(CANDIDATE_DIR/f'{r}.pth') for r in CANDIDATES}}
SCREEN_PANEL=('solution92','sol92_sq')
SCREEN_OPPONENTS=SCREEN_PANEL+('default',)
COHORTS={'selection':(7700000,20,7700100,20),'confirmation':(7701000,40,7701100,40)}
TOTALS={'selection':440,'confirmation':1200}
COUNTS=dict(actual_prefill_games=40,actual_train_games=400,actual_validation_games=32,
            learn_steps=60000,env_steps=193320)
require=C.require


def historical_path(root,old_root,value,*,protected=False):
    """Rebase accepted artifacts; historical machine/runtime identity stays historical."""
    path=Path(value)
    require(path.is_absolute() and '..' not in path.parts,'Historical input must be an absolute bound path')
    old_root=Path(old_root)
    if path.is_relative_to(old_root): relative=path.relative_to(old_root)
    elif protected and path.is_relative_to('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15'):
        relative=path.relative_to('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15')
    else: raise ValueError('Historical artifact escapes accepted repository root')
    return S.repo_path(root,str(relative))


def historical_acceptance(root=ROOT):
    """Check every accepted artifact and protected binding; permit a new phase HEAD."""
    root=Path(root).resolve();path=S.repo_path(root,str(ACCEPTANCE))
    require(C.digest(path)==ACCEPTANCE_SHA256,'Historical acceptance trust-anchor hash changed')
    accepted=C._load_json(path)
    expected=dict(schema_version=1,status='PASS',eligible_for_comparison=True,training_head=TRAINING_HEAD,
        total_prefill_games=160,total_train_games=1600,total_validation_games=128,
        total_executions=1888,total_updates=240000)
    require(all(accepted.get(k)==v for k,v in expected.items()) and set(accepted.get('arms',{}))==set(ARMS),
            'Incomplete historical training acceptance')
    old_root=accepted['root'];source=accepted['source']
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
    prepared=historical_path(root,old_root,accepted['prepared']+'/manifest.json')
    require(bound.get(str(prepared))==accepted['prepared_manifest_sha256'],'Prepared manifest not historically bound')
    for arm,item in accepted['arms'].items():
        require(item.get('counts')==COUNTS and isinstance(item.get('files'),dict),'Wrong historical arm budget')
        for old,sha in item['files'].items():
            target=historical_path(root,old_root,old)
            require(bound.get(str(target))==sha,'Arm file absent from historical acceptance inventory')
        receipt_path=historical_path(root,old_root,item['receipt_path'])
        checkpoint=historical_path(root,old_root,item['checkpoint_path'])
        require(bound.get(str(receipt_path))==item['receipt_sha256']
                and bound.get(str(checkpoint))==item['final_checkpoint_sha256'],'Arm checkpoint/receipt unbound')
        receipt=C._load_json(receipt_path)
        expected_arm=dict(status='done',eligible=True,smoke=False,arm=arm,source_sha256=SOURCE_SHA,
            component_index=18,run_seed=int(arm[-2:]),**COUNTS)
        require(all(receipt.get(k)==v for k,v in expected_arm.items())
            and receipt.get('final_checkpoint_sha256')==item['final_checkpoint_sha256']
            and receipt.get('pins',{}).get('source')==source,'Historical arm receipt/provenance differs')
        for key,name in (('rollouts_sha256','rollouts.jsonl'),('validation_sha256','validation_games.jsonl'),
                         ('audit_sha256','training_audit.json'),('train_csv_sha256','train.csv'),
                         ('prefill_sha256','prefill_proof.json')):
            require(bound.get(str(receipt_path.parent/name))==receipt.get(key),'Missing bound raw training receipt file')
    return accepted,bound


def _states(checkpoint):
    return [checkpoint['q'],*checkpoint.get('ensemble',[])]


def checked_checkpoint(checkpoint,count,cfg=None):
    """Finite exact homogeneous networks, strict state loading and ordered identity."""
    import torch
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.model import QNet,checkpoint_ensemble_dims
    from scripts.night_train_pilot import tensor_sha256
    from scripts.targeting_adapt import _finite
    require(isinstance(checkpoint,dict) and checkpoint.get('feature_dim')==79
        and checkpoint.get('n_actions')==6 and len(_states(checkpoint))==count
        and checkpoint_ensemble_dims(checkpoint,79)==[79]*(count-1),'Wrong homogeneous model membership/dimensions')
    effective=AgentConfig.from_dict(checkpoint['cfg']).to_dict()
    require(cfg is None or effective==cfg,'Wrong fixed inference/training configuration')
    _finite(checkpoint)
    with torch.random.fork_rng(devices=[]):
        model=QNet(79,6,hidden=effective['hidden'],dueling=effective['dueling'])
        for state in _states(checkpoint): model.load_state_dict(state,strict=True)
    return effective,[tensor_sha256(state) for state in _states(checkpoint)]


def build_candidates(*,root=ROOT):
    """Exclusive deterministic assembly; no games and no component selection."""
    import torch
    from scripts.night_train_pilot import tensor_sha256
    root=Path(root).resolve();accepted,bindings=historical_acceptance(root)
    original=S.repo_path(root,ROLE_PATHS['V14'])
    require(C.digest(original)==SOURCE_SHA,'Exact archived V14 required')
    source=torch.load(original,map_location='cpu',weights_only=True)
    cfg,original_hashes=checked_checkpoint(source,36)
    require(cfg['fog_unknown_reward_neutral'] is False,'V14 inference reward flag must beFalse')
    checkpoints={}
    for arm in ARMS:
        item=accepted['arms'][arm]
        path=historical_path(root,accepted['root'],item['checkpoint_path'])
        cp=torch.load(path,map_location='cpu',weights_only=True)
        expected=dict(cfg,frozen=False,lr=5e-5,rules_in_training=True,rules_in_training_all=True,
                      rescue_in_training=True,fog_unknown_reward_neutral=arm.startswith('neutral'))
        checked_checkpoint(cp,1,expected)
        receipt=C._load_json(historical_path(root,accepted['root'],item['receipt_path']))
        require(cp['cfg']==receipt['config'] and cp.get('env_steps')==193320 and cp.get('learn_steps')==60000
                and tensor_sha256(cp['q'])!=receipt['initial_tensor_sha256'],'Final arm checkpoint differs from accepted final state')
        checkpoints[arm]=cp
    destination=S.repo_path(root,str(CANDIDATE_DIR))
    require(not destination.exists(),'Candidate output already exists; never overwrite or resume')
    destination.parent.mkdir(parents=True,exist_ok=True);destination.mkdir()
    roles={'V14':dict(path=ROLE_PATHS['V14'],sha256=SOURCE_SHA,members=original_hashes)}
    for role,prefix in (('CONTROL38','control'),('NEUTRAL38','neutral')):
        arms=[prefix+'41',prefix+'42']
        cp=copy.deepcopy(source)
        cp['cfg']=cfg.copy()
        cp['ensemble']=[*source.get('ensemble',[]),*(checkpoints[a]['q'] for a in arms)]
        cp['ensemble_dims']=[79]*37
        cp['ensemble_sources']=[ROLE_PATHS['V14'],*(str(historical_path(root,accepted['root'],accepted['arms'][a]['checkpoint_path']).relative_to(root)) for a in arms)]
        expected=original_hashes+[tensor_sha256(checkpoints[a]['q']) for a in arms]
        _,actual=checked_checkpoint(cp,38,cfg)
        require(actual==expected,'Candidate membership/order differs from original36+final41/42')
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
        and record['inference_config']['fog_unknown_reward_neutral'] is False,'Inference/source differs')
    import torch
    from scripts.night_train_pilot import tensor_sha256
    base=torch.load(root/ROLE_PATHS['V14'],map_location='cpu',weights_only=True)
    cfg,base_hashes=checked_checkpoint(base,36)
    require(record['inference_config']==cfg and record['roles']['V14']['members']==base_hashes,
            'Original inference configuration/member order differs')
    for role,prefix in (('CONTROL38','control'),('NEUTRAL38','neutral')):
        expected=base_hashes.copy()
        for seed in (41,42):
            arm=prefix+str(seed)
            checkpoint=torch.load(historical_path(root,accepted['root'],accepted['arms'][arm]['checkpoint_path']),
                                  map_location='cpu',weights_only=True)
            expected.append(tensor_sha256(checkpoint['q']))
        candidate=torch.load(root/ROLE_PATHS[role],map_location='cpu',weights_only=True)
        _,actual=checked_checkpoint(candidate,38,cfg)
        require(actual==expected and record['roles'][role]['members']==expected,
                'Candidate is not exact ordered original36+final41/42')
    return record,{**expected_inputs,str(path):C.digest(path),
                  **{str(root/r['path']):r['sha256'] for r in record['roles'].values()}}


def cohort(phase):
    require(phase in COHORTS,'Invalid comparison phase');return COHORTS[phase]


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
    require(plan==expected,'Plan differs from exact fixed440/1200 job/role/cohort matrix')
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
    require(name in CANDIDATES,'Unknown Fog candidate')
    reference=C._checked_frame(reference,SCREEN_OPPONENTS,7700000,20)
    candidate=C._checked_frame(candidate,SCREEN_OPPONENTS,7700000,20)
    direct=C._checked_frame(direct,(C.V14_LABEL,),7700100,20)
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
    require(name in CANDIDATES,'Invalid Fog nominee')
    reference=C._checked_frame(reference,C.OPPONENTS,7701000,40)
    candidate=C._checked_frame(candidate,C.OPPONENTS,7701000,40)
    direct=C._checked_frame(direct,(C.V14_LABEL,),7701100,40)
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
