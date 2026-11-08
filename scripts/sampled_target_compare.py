"""Fixed 400-game submitted-successor method comparison; no promotion or extra stage.

Historical training is sealed under its original source. Performance starts only
after the current tools, inference copies and fixed plan have been validated.
"""
from __future__ import annotations

import argparse
import copy
from pathlib import Path

from scripts import ensemble_diversity_compare as C
from scripts import ensemble_diversity_eval_supervisor as S
from scripts.fog_reward_compare import historical_path

ROOT=Path(__file__).resolve().parents[1]
PROFILE='sampled_target_20261108'
ARMS=('control45','sampled45','control46','sampled46')
SIDES=C.SIDES
PANEL=('solution92','sol92_sq')
ANALYSIS=Path('experiments/analysis/sampled_target_performance_20261108')
PLAN_DIR=ANALYSIS/'plans'
CANDIDATE_DIR=Path('experiments/candidates/sampled_target_20261108')
PROTOCOL='docs/superpowers/plans/2026-11-08-sampled-target.md'
SPEC='docs/superpowers/specs/2026-11-08-sampled-target.md'
ACCEPTANCE=Path('experiments/analysis/sampled_target_20261108/operations/historical_training_acceptance.json')
ACCEPTANCE_SHA256='dac732d042b700543aeec8e718771660165e5462abfa60d84a0170689ddac458'
SOURCE_SHA='98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
ROLE_PATHS={arm:str(CANDIDATE_DIR/f'{arm}.pth') for arm in ARMS}
COHORTS={'prefill45':list(range(9915000,9915020)),'train45':list(range(9910000,9910080)),
    'prefill46':list(range(9925000,9925020)),'train46':list(range(9920000,9920080)),
    'panel':list(range(9930000,9930020)),'direct':list(range(9930100,9930120))}
TOTALS=dict(technical_games=4,prefill_games=160,train_games=640,training_executions=800,updates=96000)
FINAL_FILES={'manifest.json','initial_agent.pth','rollouts.jsonl','prefill_proof.json','prefill/bundle.json',
    'prefill/replay.npz','prefill/provenance.jsonl.gz','prefill/trajectory.jsonl.gz','train/provenance.jsonl.gz',
    'train/trajectory.jsonl.gz','final/agent.pth','final/agent.buffer.npz','final/pilot_state.json','final_audit.json'}
require=C.require

def expected_training_config(cfg):
    return dict(cfg,frozen=False,lr=5e-5,rules_in_training=True,rules_in_training_all=True,
        rescue_in_training=True,fog_unknown_reward_neutral=False,art_splash_in_training=False)

def historical_acceptance(root=ROOT):
    """Read sealed complete training evidence under its historical source identity."""
    require(C._hex(ACCEPTANCE_SHA256),'Historical training acceptance not yet pinned')
    root=Path(root).resolve();path=S.repo_path(root,str(ACCEPTANCE))
    require(C.digest(path)==ACCEPTANCE_SHA256,'Historical acceptance changed')
    accepted=C._load_json(path)
    require(all(accepted.get(k)==v for k,v in dict(schema_version=1,status='PASS',profile=PROFILE,
        eligible_for_performance=True,totals=TOTALS).items()) and set(accepted.get('arms',{}))==set(ARMS),
        'Incomplete historical pilot acceptance')
    old_root=accepted['root'];source=accepted['source'];head=accepted['training_head']
    require(Path(old_root).is_absolute() and '..' not in Path(old_root).parts and C._hex(head,40)
        and source.get('head')==head and bool(source.get('files')),'Historical source identity missing')
    bound={str(path):ACCEPTANCE_SHA256}
    for group in ('files','protected'):
        inventory=accepted.get(group);require(isinstance(inventory,dict) and bool(inventory),'Missing historical inventory')
        for old,digest in inventory.items():
            target=historical_path(root,old_root,old,protected=group=='protected')
            require(C._hex(digest) and C.digest(target)==digest and (str(target) not in bound or bound[str(target)]==digest),
                'Historical artifact/protected bytes changed')
            bound[str(target)]=digest
    def artifact(value,digest=None):
        target=historical_path(root,old_root,value);saved=accepted['files'].get(value)
        require(C._hex(saved) and bound.get(str(target))==saved and (digest is None or saved==digest),
            'Referenced historical artifact is absent from sealed inventory')
        return target
    def evidence(item):
        require(isinstance(item,dict) and set(item)=={'path','sha256'},'Missing bound evidence reference')
        return C._load_json(artifact(item['path'],item['sha256']))
    manifest=C._load_json(artifact(accepted['prepared']+'/manifest.json',accepted['prepared_manifest_sha256']))
    require(manifest.get('schema_version')==1 and manifest.get('profile')==PROFILE and manifest.get('stage')=='study'
        and manifest.get('cohorts')==COHORTS and set(manifest.get('arms',{}))==set(ARMS)
        and manifest.get('source_sha256')==SOURCE_SHA and manifest.get('pins')==dict(source=source,protected=accepted['protected']),
        'Historical prepared source/cohorts differ')
    artifact(accepted['prepared']+'/supervisor_launch.json')
    cfg=manifest['source_config'];require(cfg.get('fog_unknown_reward_neutral') is False
        and cfg.get('art_splash_in_training') is False,'Unexpected bound V14 configuration')
    artifact(manifest['source'],SOURCE_SHA)
    require(isinstance(manifest.get('input_sha256'),dict) and bool(manifest['input_sha256']),'Missing prepared input bindings')
    for old,digest in manifest['input_sha256'].items():artifact(old,digest)
    protected={str(historical_path(root,old_root,p,protected=True)):digest for p,digest in accepted['protected'].items()}
    require(all(protected.get(str(root/f'agents/sherlock/weights/agent_p{i}.pth'))==SOURCE_SHA for i in (0,1))
        and C._hex(protected.get(str(root/'Gruppe15.zip'))),'Historical V14/ZIP protection missing')
    seeds=evidence(accepted['seed_acceptance'])
    require(all(seeds.get(k)==v for k,v in dict(schema_version=1,status='PASS',profile=PROFILE,cohorts=COHORTS).items()),
        'Accepted six exact cohorts differ')
    seed_audit=seeds.get('audit');require(isinstance(seed_audit,dict),'Missing prospective seed audit')
    audit_path=str(Path(old_root)/seed_audit['path'])
    audit=C._load_json(artifact(audit_path,seed_audit['sha256']))
    require(audit.get('status')=='PASS' and audit.get('no_observed_conflicts') is True
        and isinstance(audit.get('limitations'),list) and bool(audit['limitations'])
        and isinstance(audit.get('files'),dict) and bool(audit['files']),'Missing seed limits/inventory')
    raw=audit['raw_audit'];artifact(str(Path(old_root)/raw['path']),raw['sha256'])
    for relative,digest in audit['files'].items():artifact(str(Path(old_root)/relative),digest)
    technical=evidence(accepted['technical_acceptance'])
    require(technical.get('status')=='PASS' and technical.get('profile')==PROFILE and technical.get('games')==4,
        'Four technical games were not independently accepted')
    for item in technical.get('receipts',{}).values():artifact(item['path'],item['sha256'])
    require(len(technical.get('receipts',{}))==4,'Missing technical receipt inventory')
    receipt_hashes={}
    for arm,item in accepted['arms'].items():
        receipt_path=artifact(item['receipt_path'],item['receipt_sha256'])
        checkpoint=artifact(item['checkpoint_path'],item['checkpoint_sha256'])
        require(receipt_path.name=='final_receipt.json' and checkpoint==receipt_path.parent/'final/agent.pth',
            'Only the final checkpoint may enter performance')
        receipt=C._load_json(receipt_path);entry=manifest['arms'][arm]
        mode='double_dqn' if arm.startswith('control') else 'sampled_successor'
        expected=dict(schema_version=1,status='done',profile=PROFILE,eligible=False,arm=arm,run_seed=int(arm[-2:]),
            bootstrap_mode=mode,games=200,prefill_games=40,train_games=160,updates=24000,env_steps=120600,
            pins=manifest['pins'],prepared=accepted['prepared'],manifest_sha256=accepted['prepared_manifest_sha256'])
        require(all(receipt.get(k)==v for k,v in expected.items()) and set(receipt.get('artifacts',{}))==FINAL_FILES
            and entry['config']==expected_training_config(cfg) and entry['bootstrap_mode']==mode
            and entry['run_seed']==int(arm[-2:]) and entry['component_index']==18,'Wrong historical arm/progress')
        artifact(str(Path(accepted['prepared'])/arm/'initial.pth'),entry['weights_sha256'])
        for name,digest in receipt['artifacts'].items():artifact(str(Path(item['receipt_path']).parent/name),digest)
        require(receipt['artifacts']['final/agent.pth']==item['checkpoint_sha256'],'Final checkpoint binding differs')
        receipt_hashes[arm]=item['receipt_sha256']
    state=evidence(accepted['supervisor'])
    require(state.get('status')=='done' and state.get('stage')=='study' and state.get('profile')==PROFILE
        and state.get('eligible') is False and not state.get('active') and not state.get('queue')
        and state.get('source')==source and state.get('prepared')==accepted['prepared']
        and state.get('protected')==accepted['protected'] and set(state.get('jobs',{}))==set(ARMS)
        and set(state.get('receipts',{}))==set(ARMS) and not state.get('technical_pairs')
        and type(state.get('wake',{}).get('returncode')) is int,'Training/wake processes were not completely closed')
    for arm,item in accepted['arms'].items():
        job=state['jobs'][arm];receipt=C._load_json(artifact(item['receipt_path']))
        require(type(job.get('returncode')) is int and job['returncode']==0 and job.get('finished_at') is not None
            and state['receipts'][arm]=={item['receipt_path']:item['receipt_sha256']}
            and job.get('argv')==receipt.get('command'),'Historical owned job/receipt differs')
    require(set(accepted.get('paired_prefill',{}))==set(state.get('paired_prefill',{}))=={'45','46'},'Missing paired prefill gates')
    for seed,item in accepted['paired_prefill'].items():
        pair=evidence(item);expected={role+seed:accepted['files'][str(Path(accepted['arms'][role+seed]['receipt_path']).parent/'prefill_proof.json')]
            for role in ('control','sampled')}
        require(pair==state['paired_prefill'][seed] and pair.get('status')=='matched' and pair.get('eligible') is False
            and pair.get('run_seed')==int(seed) and pair.get('proof_sha256')==expected,'Historical prefill gate differs')
    validation=evidence(accepted['original_validation'])
    require(validation.get('status')=='PASS' and validation.get('training_head')==head
        and validation.get('validator')=='scripts.sampled_target_study.validate_final_receipt'
        and set(validation.get('arms',{}))==set(ARMS),'Original validators were not accepted under training HEAD')
    for arm,digest in receipt_hashes.items():
        require(validation['arms'][arm]==dict(status='PASS',receipt_sha256=digest,games=200,updates=24000,env_steps=120600),
            'Original training validation does not bind every final receipt')
    independent=evidence(accepted['independent_audit'])
    require(independent.get('status')=='PASS' and independent.get('training_head')==head
        and independent.get('receipt_sha256')==receipt_hashes,'Independent complete-data audit not bound')
    return accepted,bound

def checkpoint_identity(checkpoint):
    from scripts.experiment import state_sha256
    return state_sha256({k:v for k,v in checkpoint.items() if k!='cfg'})

def validate_copy(original,candidate,source_cfg):
    """No network construction: every non-config item is preserved, not just Q."""
    import torch
    expected=dict(source_cfg,frozen=False)
    require(isinstance(original,dict) and isinstance(candidate,dict) and original.keys()==candidate.keys()
        and candidate.get('cfg')==expected and checkpoint_identity(original)==checkpoint_identity(candidate)
        and candidate.get('feature_dim')==79 and candidate.get('n_actions')==6
        and candidate.get('ensemble')==[] and candidate.get('ensemble_dims')==[]
        and candidate.get('env_steps')==120600 and candidate.get('learn_steps')==24000,
        'Inference copy differs from final singlenet or shared config')
    require(all(isinstance(candidate.get(k),dict) and bool(candidate[k]) for k in ('q','target_q')),
        'Missing final network tensors')
    require(candidate['q'].keys()==candidate['target_q'].keys() and all(isinstance(v,torch.Tensor)
        and bool(torch.isfinite(v).all()) for k in ('q','target_q') for v in candidate[k].values()),'Invalid final tensors')
    return checkpoint_identity(candidate)

def inference_copy(original,source_cfg):
    candidate=copy.deepcopy(original);candidate['cfg']=dict(source_cfg,frozen=False)
    validate_copy(original,candidate,source_cfg);return candidate

def build_inference_copies(*,root=ROOT):
    root=Path(root).resolve();accepted,bindings=historical_acceptance(root)
    manifest=C._load_json(historical_path(root,accepted['root'],accepted['prepared']+'/manifest.json'))
    source_cfg=manifest['source_config'];destination=S.repo_path(root,str(CANDIDATE_DIR))
    require(not destination.exists(),'Inference output already exists; no overwrite/retry')
    import torch
    from scripts.night_train_pilot import tensor_sha256
    destination.mkdir(parents=True);roles={}
    for arm in ARMS:
        item=accepted['arms'][arm];path=historical_path(root,accepted['root'],item['checkpoint_path'])
        original=torch.load(path,map_location='cpu',weights_only=True)
        require(original.get('cfg')==expected_training_config(source_cfg),'Final training config differs')
        candidate=inference_copy(original,source_cfg);target=S.repo_path(root,ROLE_PATHS[arm])
        with target.open('xb') as stream:torch.save(candidate,stream)
        loaded=torch.load(target,map_location='cpu',weights_only=True);identity=validate_copy(original,loaded,source_cfg)
        roles[arm]=dict(path=ROLE_PATHS[arm],sha256=C.digest(target),source_checkpoint_sha256=item['checkpoint_sha256'],
            nonconfig_sha256=identity,q_sha256=tensor_sha256(loaded['q']),nets=1)
    require(all(C.digest(Path(p))==v for p,v in bindings.items()),'Historical input changed while copying')
    admission=dict(schema_version=1,status='admitted',profile=PROFILE,acceptance_sha256=ACCEPTANCE_SHA256,
        build_root=str(root),historical_source=accepted['source'],input_sha256=bindings,inference_config=dict(source_cfg,frozen=False),
        roles=roles,reload_verified=True,promoted=False)
    S.exclusive_json(destination/'admission.json',admission);return admission

def validate_admission(path,*,root=ROOT):
    root=Path(root).resolve();accepted,bindings=historical_acceptance(root);path=S.helpers().safe_path(path)
    require(path==root/CANDIDATE_DIR/'admission.json','Wrong inference admission path')
    record=C._load_json(path);manifest=C._load_json(historical_path(root,accepted['root'],accepted['prepared']+'/manifest.json'))
    cfg=manifest['source_config']
    require(all(record.get(k)==v for k,v in dict(schema_version=1,status='admitted',profile=PROFILE,
        acceptance_sha256=ACCEPTANCE_SHA256,historical_source=accepted['source'],inference_config=dict(cfg,frozen=False),
        reload_verified=True,promoted=False).items()) and set(record.get('roles',{}))==set(ARMS),'Wrong inference admission')
    rebased={str(historical_path(root,record['build_root'],p)):v for p,v in record['input_sha256'].items()}
    require(rebased==bindings,'Inference admission omits original input bindings')
    import torch
    from scripts.night_train_pilot import tensor_sha256
    for arm,item in accepted['arms'].items():
        entry=record['roles'][arm];target=S.repo_path(root,ROLE_PATHS[arm])
        original=torch.load(historical_path(root,accepted['root'],item['checkpoint_path']),map_location='cpu',weights_only=True)
        candidate=torch.load(target,map_location='cpu',weights_only=True)
        identity=validate_copy(original,candidate,cfg)
        require(entry==dict(path=ROLE_PATHS[arm],sha256=C.digest(target),source_checkpoint_sha256=item['checkpoint_sha256'],
            nonconfig_sha256=identity,q_sha256=tensor_sha256(candidate['q']),nets=1),'Copied model identity differs')
        bindings[str(target)]=entry['sha256']
    bindings[str(path)]=C.digest(path);return record,bindings

def direct_label(seed):
    require(seed in (45,46),'Unknown fixed start');return 'self:'+ROLE_PATHS[f'control{seed}']

def performance_plan(admission):
    require(set(admission['roles'])==set(ARMS) and all(admission['roles'][r]['path']==ROLE_PATHS[r]
        and C._hex(admission['roles'][r]['sha256']) for r in ARMS),'Wrong admitted model roles')
    jobs=[dict(name=f'{r}_panel_{i}',role=r,kind='panel',weights=ROLE_PATHS[r],opponent=o,
        seed_list=str(PLAN_DIR/'panel.json'),expected_games=40,workers=1) for r in ARMS for i,o in enumerate(PANEL)]
    jobs.extend(dict(name=f'sampled{s}_direct',role=f'sampled{s}',kind='direct',weights=ROLE_PATHS[f'sampled{s}'],
        opponent=direct_label(s),seed_list=str(PLAN_DIR/'direct.json'),expected_games=40,workers=1) for s in (45,46))
    return dict(schema_version=1,profile=PROFILE,phase='performance',protocol=PROTOCOL,roles=ROLE_PATHS.copy(),
        total_games=400,max_simultaneous_model_processes=2,opponent_sha256={ROLE_PATHS[f'control{s}']:
            admission['roles'][f'control{s}']['sha256'] for s in (45,46)},jobs=jobs)

def validate_plan(plan,root,admission):
    require(plan==performance_plan(admission) and type(plan['total_games']) is int
        and type(plan['max_simultaneous_model_processes']) is int
        and all(type(j['workers']) is int and type(j['expected_games']) is int for j in plan['jobs']),
        'Plan differs from exact400 final-singlenet games')
    jobs=[]
    for job in plan['jobs']:
        seeds=C._seeds(C._load_json(S.repo_path(root,job['seed_list'])))
        require(seeds==COHORTS[job['kind']],'Wrong fixed performance cohort')
        jobs.append(dict(job,seeds=seeds))
    return jobs

def prepare_plans(*,root=ROOT):
    root=Path(root).resolve();admission,_=validate_admission(root/CANDIDATE_DIR/'admission.json',root=root)
    base=S.repo_path(root,str(PLAN_DIR));require(not base.exists(),'Performance plan exists; no overwrite')
    base.mkdir(parents=True)
    for kind in ('panel','direct'):S.exclusive_json(base/f'{kind}.json',COHORTS[kind])
    plan=performance_plan(admission);validate_plan(plan,root,admission)
    S.exclusive_json(base/'jobs.json',plan);return plan

def validate_performance(panels,direct):
    """Complete fixed matrices, integer gates, paired whole-map descriptive intervals."""
    from scripts.compare_report import compare_results
    from scripts.league_gates import panel_delta,direct_result,_bootstrap
    import numpy as np
    require(set(panels)==set(ARMS) and set(direct)=={'45','46'},'Missing/extra final roles or paired direct results')
    clean={r:C._checked_frame(panels[r],PANEL,COHORTS['panel'][0],20) for r in ARMS}
    duels={s:C._checked_frame(direct[s],(direct_label(int(s)),),COHORTS['direct'][0],20) for s in direct}
    starts={};gains=[];direct_half=[];cluster_deltas=[];cluster_direct=[]
    for seed in (45,46):
        control=clean[f'control{seed}'];sampled=clean[f'sampled{seed}'];duel=duels[str(seed)]
        panel=C._score_stats(panel_delta(sampled,control,panel=PANEL),sampled,control)
        comparisons=compare_results(sampled,control)
        opponents={row['opponent']:C._score_stats(row,sampled[sampled.opponent==row['opponent']],
            control[control.opponent==row['opponent']]) for row in comparisons}
        duel_stats=C._score_stats(direct_result(duel,direct_label(seed)),duel)
        gain=panel['candidate']['half_wins']-panel['reference']['half_wins'];half=duel_stats['candidate']['half_wins']
        gains.append(gain);direct_half.append(half)
        starts[str(seed)]=dict(panel=panel,opponents=opponents,direct=duel_stats,panel_half_win_gain=gain)
        cluster_deltas.append((sampled.groupby('seed',sort=True).result.mean()-control.groupby('seed',sort=True).result.mean()).to_numpy())
        cluster_direct.append(duel.groupby('seed',sort=True).result.mean().to_numpy())
    values=np.mean(np.stack(cluster_deltas),axis=0);low,high=_bootstrap(values)
    direct_values=np.mean(np.stack(cluster_direct),axis=0);dlow,dhigh=_bootstrap(direct_values)
    checks=dict(start45_panel_positive=gains[0]>0,start46_panel_positive=gains[1]>0,
        mean_panel_gain_at_least5pp=sum(gains)>=16,start45_direct_at_least50pct=direct_half[0]>=40,
        start46_direct_at_least50pct=direct_half[1]>=40,combined_direct_above50pct=sum(direct_half)>80)
    return dict(games=400,maps_per_cohort=20,starts=starts,panel_half_win_gain_sum=sum(gains),
        direct_half_win_sum=sum(direct_half),checks=checks,passed=all(checks.values()),promoted=False,
        descriptive_mean_panel=dict(delta=float(values.mean()),low=low,high=high,maps=20,fixed_starts=2),
        descriptive_mean_direct=dict(score=float(direct_values.mean()),low=dlow,high=dhigh,maps=20,fixed_starts=2),
        interpretation='Method signal only; no V14 comparison/promotion. Historical replay TD is SARSA-like, not on-policy SARSA. '
            '5000 paired whole-map bootstrap samples, PCG64 seed0,95% unadjusted intervals. '
            'Across-start summaries keep the same maps paired across both starts/opponents; '
            'two fixed starts do not establish a training-population effect. No extra games or automatic continuation.',
        score_definition='(strict wins +0.5 draws)/games; integer half_wins=2*wins+draws; strict wins separately')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('build','prepare-plans'))
    args=parser.parse_args()
    result=build_inference_copies() if args.action=='build' else prepare_plans()
    import json
    print(json.dumps(result,indent=2,allow_nan=False))

if __name__=='__main__':main()
