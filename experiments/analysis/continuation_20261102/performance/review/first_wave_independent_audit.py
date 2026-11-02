"""Read-only acceptance of completed control18/adapt18 only; never admits PT."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import argparse, hashlib, importlib.util, json, csv, math, re, shlex, subprocess, random

ROOT=Path('/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics')
D=Path('/tmp/sherlock-continue-20261102')
PRE=ROOT/'experiments/runs/20261102_targeting_prepared'
HEAD='8e4720ca224f3cdf61693d5e5c4b4ef422ac6d8d'
SOURCE='98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'


def active_trainers():
    text=subprocess.check_output(['ps','-axo','pid=,args='],text=True)
    active=[]
    for line in text.splitlines():
        split=line.strip().split(maxsplit=1)
        if len(split)!=2:continue
        try: args=shlex.split(split[1])
        except ValueError:continue
        if args and Path(args[0]).name.lower().startswith('python') and '-m scripts.targeting_adapt runarm' in split[1]:
            active.append(dict(pid=int(split[0]),command=split[1]))
    return active


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--allow-torch',action='store_true')
    args=ap.parse_args()
    if not args.allow_torch:raise SystemExit('Root authorization required: --allow-torch')
    active=active_trainers()
    if active:raise SystemExit('Torch deferred; active trainers: '+json.dumps(active))
    # Import only the audit definitions, never project/runtime code or its main.
    spec=importlib.util.spec_from_file_location('deferred_all_four_audit',D/'adaptation_final_audit.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    import torch
    torch.set_num_threads(1);helper.TORCH=torch
    active=active_trainers()
    if active:raise SystemExit('Checkpoint reads deferred; trainers started: '+json.dumps(active))
    sha,load,finite,th,typed=helper.digest,helper.load,helper.finite,helper.tensor_hash,helper.state_hash
    checks=[];evidence={};summaries={};known_validation={};actual_initials={}
    def check(name,condition,detail=None):checks.append(dict(name=name,passed=bool(condition),**({'detail':detail} if detail is not None else {})))
    def pin(path):
        path=Path(path);evidence[str(path)]=sha(path);return path
    def read(path):return load(pin(path))
    def same_tensors(a,b):return set(a)==set(b) and all(a[k].dtype==b[k].dtype and a[k].shape==b[k].shape and torch.equal(a[k],b[k]) for k in a)
    def initial_without_global(proof):
        normalized={k:v for k,v in proof.items() if k!='global_rng_sha256'}
        normalized['initial_identity']={k:v for k,v in proof['initial_identity'].items() if k!='rng_sha256'}
        return normalized
    def milestone_identity(proof):
        normalized=helper.before_train_identity(proof)
        normalized.pop('global_rng_sha256',None)
        return normalized
    prep=read(PRE/'manifest.json');sup=read(D/'training_supervisor.json')
    initialaudit=read(D/'adaptation_initial_audit.json');preflight=read(D/'actual_training_preflight.json')
    check('source_head_frozen',subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==HEAD)
    check('tracked_checkout_clean',not subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain','--untracked-files=no'],text=True).strip())
    check('only_external_schema_failure',sup['status']=='incomplete' and sup['error']=="KeyError: 'actual_rollout_games'")
    check('original_only_first_pair',len(sup['waves'])==1 and [j['arm'] for j in sup['waves'][0]['jobs']]==['control18','adapt18'])
    frozenfiles=sup['identity']['source']['files'];protected=sup['identity']['weights']
    check('all_frozen_source_plan_script_hashes_current',all(Path(p).is_file() and sha(p)==h for p,h in frozenfiles.items()))
    check('all_protected_weight_hashes_current',all(Path(p).is_file() and sha(p)==h for p,h in protected.items()))
    guard=(D/'train_targeting.py').resolve()
    check('original_guard_exact_sha_preserved',str(guard) in frozenfiles and sha(guard)==frozenfiles[str(guard)])
    check('original_interpreter_sha',sha(sup['identity']['source']['python'])==sup['identity']['source']['executable_sha256'])
    check('initial_audit_bound_and_accepted',initialaudit['verdict']=='ACCEPTED' and not initialaudit['failed'] and sha(D/'adaptation_initial_audit.json')==sup['initial_audit_sha256'])
    check('protocol_wrapper_preflight_pins',prep['pins']==preflight['pins'] and prep['pins']['git']==dict(commit=HEAD,dirty=False) and prep['pins']['protocol_sha256']==sha(ROOT/'docs/superpowers/plans/2026-11-02-targeting-adaptation.md') and prep['pins']['wrapper_sha256']==sha(ROOT/'scripts/targeting_adapt.py'))
    sourcepath=pin(prep['source']);check('source_v14_sha',sha(sourcepath)==prep['source_sha256']==preflight['source_sha256']==SOURCE)
    cp=torch.load(sourcepath,map_location='cpu',weights_only=True)
    states=[cp['q'],*cp['ensemble']];ordered=[th(s) for s in states]
    check('ordered_36_source_tensor_membership',len(states)==36 and ordered==prep['source_tensor_sha256'] and cp['feature_dim']==79 and cp['n_actions']==6)
    check('all_source_tensors_finite',all(torch.isfinite(t).all().item() for s in states for t in s.values()))
    expectedval=[dict(after_games=a,opponent=o,seed=s,side=p) for a in (0,300,600) for o in ('default','solution92') for s in range(500000,500008) for p in ('player_0','player_1')]
    check('exact_declared_96_known_validation_keys',prep['validation_plan']==expectedval)
    for arm,enabled in (('control18',False),('adapt18',True)):
        e=prep['arms'][arm];cfg=e['config'];name=sup['names'][arm];run=ROOT/'experiments/runs'/name
        record=read(PRE/'run_records'/(name+'.json'));audit=read(run/'adaptation_audit.json');runmanifest=read(run/'manifest.json')
        check(arm+'_producer_done',record['status']==runmanifest['status']=='done' and [record[k] for k in ('actual_prefill_games','actual_train_games','actual_validation_games')]==[120,600,96])
        check(arm+'_fixed_component_seed_role',e['component_index']==18 and e['run_seed']==28 and cfg['point_pair_swap'] is enabled and cfg['art_move_guard'] is enabled)
        check(arm+'_record_source_pins_config',record['pins']==prep['pins'] and record['source_sha256']==SOURCE and record['source_tensor_sha256']==ordered and record['init_weights_sha256']==e['weights_sha256'] and record['config']==cfg)
        check(arm+'_fresh_init_container_still_pinned',sha(PRE/arm/'weights/agent.pth')==e['weights_sha256'] and initialaudit['arms'][arm]['init_file_sha256']==e['weights_sha256'] and {p.name for p in (PRE/arm/'weights').iterdir()}=={'agent.pth'})
        check(arm+'_actual_initial_matches_preflight_learning_and_own_rng',initial_without_global(audit['initial'])==initial_without_global(preflight['actual_loaded_initial'][arm]))
        actual_initials[arm]=audit['initial']
        check(arm+'_runtime_global_python_seed4228',audit['initial']['initial_identity']['rng_sha256']['python']==typed(random.Random(4228).getstate()) and preflight['actual_loaded_initial'][arm]['initial_identity']['rng_sha256']['python']==typed(random.Random(28).getstate()))
        p0=audit['initial'];pf=audit['prefill'];end=audit['end'];l0=p0['learning'];le=end['learning']
        check(arm+'_initial_exact_source_component18',p0['q_tensor_sha256']==p0['target_tensor_sha256']==e['tensor_sha256']==ordered[18] and l0['q_sha256']==l0['target_q_sha256'])
        check(arm+'_actual_fresh_learning_state',l0['config']==cfg and l0['env_steps']==60000 and l0['learn_steps']==0 and l0['learn_enabled'] is True and l0['autosave_on_terminate'] is False and l0['recent_losses']==[] and l0['replay']['size']==l0['replay']['pos']==0 and l0['replay']['_mask_dim']==1)
        check(arm+'_actual_single_shared_canonical_learner',len(p0['initial_identity']['learners'])==1 and p0['initial_identity']['learners'][0]['sides']==['player_0','player_1'] and cfg['canonical'] is True)
        expectedcfg=dict(prep['source_config'],frozen=False,lr=1e-4,w_discovery=.5,w_explore=.3,rules_in_training=True,rules_in_training_all=True,point_pair_swap=enabled,art_move_guard=enabled)
        check(arm+'_full_config_documented_overrides',cfg==expectedcfg)
        check(arm+'_actual_prefill_no_updates',pf['q_tensor_sha256']==p0['q_tensor_sha256'] and pf['target_tensor_sha256']==p0['target_tensor_sha256'] and pf['learning']['optimizer_sha256']==l0['optimizer_sha256'] and pf['learning']['learn_steps']==0 and pf['learning']['replay']['size']>5000)
        with pin(run/'rollouts.jsonl').open() as f:rollouts=[json.loads(line) for line in f]
        with pin(run/'validation_games.jsonl').open() as f:val=[json.loads(line) for line in f]
        with pin(run/'train.csv').open(newline='') as f:train=list(csv.DictReader(f))
        check(arm+'_exact_counts',len(rollouts)==720 and Counter(r['phase'] for r in rollouts)=={'prefill':120,'train':600} and len(val)==96 and len(train)==600)
        check(arm+'_all_raw_records_finite',finite(rollouts) and finite(val) and finite(audit) and finite(record))
        check(arm+'_full_actual_rollout_plan', [{k:r[k] for k in ('phase','game','seed','side','opponent')} for r in rollouts]==e['rollout_plan'] and record['rollout_plan_sha256']==typed(e['rollout_plan']))
        check(arm+'_seed_side_formulas',all(r['seed']==200000+28*10000+(5000 if r['phase']=='prefill' else 4200)+r['game']//2 and r['side']==('player_0','player_1')[r['game']%2] for r in rollouts))
        check(arm+'_all_steps303_and_v2',all(r['steps']==303 and r['point_counting_version']==2 for r in rollouts+val))
        check(arm+'_actual_val_plan', [{k:r[k] for k in ('after_games','opponent','seed','side')} for r in val]==expectedval and record['validation_plan_sha256']==typed(expectedval))
        evalcfg=dict(cfg,point_pair_swap=True,art_move_guard=True)
        check(arm+'_common_p_validation_config',all(r['config']==evalcfg and r['eval_rng_seed']==20261102 and r['epsilon']==0 and r['learn_enabled'] is False for r in val))
        check(arm+'_validation_learning_rng_isolation', [v['after_games'] for v in audit['validations']]==[0,300,600] and all(v['before']==v['after'] and v['eval_config']==evalcfg and v['eval_rng_seed']==20261102 for v in audit['validations']))
        previous_env=60000;previous_learn=0;deltas=[]
        for i,r in enumerate(rollouts):
            proof=r['identity'];learning=proof['learning'];delta=learning['learn_steps']-previous_learn;deltas.append(delta)
            check(f'{arm}_row{i}_learning_identity',learning['config']==cfg and learning['env_steps']==previous_env+303 and learning['autosave_on_terminate'] is False and learning['learn_enabled'] is (r['phase']=='train') and (delta==0 if r['phase']=='prefill' else delta==150))
            if r['phase']=='prefill':check(f'{arm}_row{i}_prefill_unchanged',proof['q_tensor_sha256']==p0['q_tensor_sha256'] and proof['target_tensor_sha256']==p0['target_tensor_sha256'] and learning['optimizer_sha256']==l0['optimizer_sha256'])
            previous_env=learning['env_steps'];previous_learn=learning['learn_steps']
        check(arm+'_prefill_matches_last_raw_prefill',pf==rollouts[119]['identity'])
        check(arm+'_before_1_300_600',set(audit['before_train'])=={'1','300','600'} and all(milestone_identity(audit['before_train'][str(g)])==milestone_identity(rollouts[120+g-2]['identity']) for g in (1,300,600)))
        check(arm+'_end_matches_final_live_rollout',helper.nonloss_identity(end)==helper.nonloss_identity(rollouts[-1]['identity']))
        check(arm+'_final_counters_exact',le['env_steps']==previous_env==60000+720*303==278160 and le['learn_steps']==previous_learn==sum(deltas)==90000 and record['counter_review_required'] is False)
        check(arm+'_600_ordered_csv', [int(r['game']) for r in train]==list(range(600)))
        check(arm+'_csv_raw_and_learning_parity',all(all(row[k]==str(raw[k]) if k in ('side','opponent') else float(row[k])==float(raw[k]) for k in ('seed','side','opponent','steps','point_counting_version','result','our_wins','opp_wins','our_points','opp_points')) and int(row['env_steps'])==raw['identity']['learning']['env_steps'] and int(row['learn_steps'])==raw['identity']['learning']['learn_steps'] and math.isfinite(float(row['mean_loss'])) and float(row['epsilon'])==.05 for row,raw in zip(train,rollouts[120:])))
        check(arm+'_final_selection_no_test',runmanifest['selection']=='Endstand (--keep-final)' and runmanifest['test_seeds']==[] and runmanifest['buffer_loaded']==0 and '--keep-final' in record['argv'] and '--no-test' in record['argv'])
        finalpath=pin(run/'weights/agent.pth')
        final=torch.load(finalpath,map_location='cpu',weights_only=True)
        qh,thash=th(final['q']),th(final['target_q']);opt=final['opt'];slots=opt['state'];groups=opt['param_groups'];pids=[p for g in groups for p in g['params']]
        check(arm+'_saved_live_reload_hash_equality',record['end']==end and end['reload_verified'] is True and sha(finalpath)==end['saved_weights_sha256'] and qh==end['q_tensor_sha256'] and thash==end['target_tensor_sha256'] and typed(opt)==le['optimizer_sha256'])
        check(arm+'_final_q_changed_and_target_synced',qh!=ordered[18] and same_tensors(final['q'],final['target_q']) and qh==thash)
        check(arm+'_final_single_net_config_counters',final['feature_dim']==79 and final['n_actions']==6 and final['cfg']==cfg and final['ensemble']==[] and final['ensemble_dims']==[] and final['env_steps']==278160 and final['learn_steps']==90000)
        check(arm+'_adam_exact_owned_slots',len(pids)==len(set(pids))==len(slots)==len(final['q']) and set(pids)==set(slots) and all(g['lr']==1e-4 for g in groups))
        check(arm+'_adam90000_and_all_tensors_finite',all(set(v)=={'step','exp_avg','exp_avg_sq'} and v['step'].item()==90000 and all(torch.isfinite(t).all().item() for t in v.values()) and v['exp_avg'].shape==v['exp_avg_sq'].shape for v in slots.values()) and all(torch.isfinite(t).all().item() for key in ('q','target_q') for t in final[key].values()))
        check(arm+'_completed_before_original_deadline',datetime.fromisoformat(record['finished_utc'])<=datetime.fromisoformat(sup['deadline_utc']))
        known_validation[arm]={}
        for after in (0,300,600):
            known_validation[arm][str(after)]={}
            for opp in ('default','solution92'):
                group=[r for r in val if r['after_games']==after and r['opponent']==opp]
                known_validation[arm][str(after)][opp]=dict(games=len(group),wins=sum(r['result']==1 for r in group),draws=sum(r['result']==.5 for r in group),losses=sum(r['result']==0 for r in group),our_match_wins=sum(r['our_wins'] for r in group),opp_match_wins=sum(r['opp_wins'] for r in group),our_points=sum(r['our_points'] for r in group),opp_points=sum(r['opp_points'] for r in group))
        summaries[arm]=dict(status='done',actual_rollouts=len(rollouts),prefill=120,train=600,validation=96,learn_steps=90000,env_steps=278160,train_update_deltas=dict(Counter(deltas[120:])),final_file_sha256=sha(finalpath),final_q_tensor_sha256=qh,final_target_tensor_sha256=thash,optimizer_sha256=typed(opt),reload_verified=True,effect_counters={key:sum(r['effect_counters'].get(key,0) for r in rollouts) for key in ('art_move_kept','point_pair_swaps','point_pair_bfs_gain')})
    ce,ae=prep['arms']['control18'],prep['arms']['adapt18']
    check('paired_only_two_flags_and_identical_complete_plan',ce['rollout_plan']==ae['rollout_plan'] and {k for k in ce['config'] if ce['config'][k]!=ae['config'][k]}=={'point_pair_swap','art_move_guard'})
    ci,ai=actual_initials['control18'],actual_initials['adapt18']
    check('paired_initial_opt_q_and_rng_identity',all(ci[k]==ai[k] for k in ('q_tensor_sha256','target_tensor_sha256','agent_rng_sha256','global_rng_sha256')) and ci['learning']['optimizer_sha256']==ai['learning']['optimizer_sha256'])
    check('all_evidence_stable_after_audit',all(sha(p)==h for p,h in evidence.items()))
    check('original_source_and_protected_stable_after_audit',all(sha(p)==h for p,h in {**frozenfiles,**protected}.items()))
    failed=[c for c in checks if not c['passed']]
    verdict='ACCEPTED_FIRST_WAVE_ONLY' if not failed else 'REJECTED_FIRST_WAVE'
    report=dict(verdict=verdict,scope='control18/adapt18 only; completed partial wave, no PT admission',pt_admitted=False,head=HEAD,source_sha256=SOURCE,created_utc=datetime.now(timezone.utc).isoformat(),checks_total=len(checks),failed=failed,arms=summaries,known_validation_diagnostic=known_validation,orchestration=dict(status=sup['status'],error=sup['error'],meaning='External consumer schema mismatch after first children finished; not total four-arm completion'),evidence_sha256=evidence,checks=checks,limits=['No Agent/QNet construction, forwards, gradients, updates, new games or tests. Only one V14 checkpoint and two final checkpoints were loaded read-only.','Initial Adam/object-sharing evidence comes from the successful pinned prove_initial live proof, independently checked against prior accepted initial audit and manifests. Actual global RNG uses fixed runtime seed4228 versus preflight28, with equal actual states across the pair; convenience preflight-global identity is not an intended invariant. No second live learner was constructed.','Known validation curves are diagnosis only, not fresh selection evidence or a checkpoint/component/seed choice.','Index19 pair remains required before any PT is admissible. This report neither alters nor replaces the separate four-arm final audit.'])
    (D/'first_wave_independent_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    md='# Independent first-wave acceptance\n\n**'+verdict+'** — '+str(len(checks))+' checks, '+str(len(failed))+' failures. **PT remains inadmissible without the completed index19 pair.**\n\nBoth arms have720 exact raw rollouts (120prefill+600train),96 known P-validation games and600 ordered training CSV rows. Source plans/configs/HEAD/protected hashes match; paired actual opponent/card/side sequences agree and only the two role flags differ. Initial component18 and fresh learning state agree with pinned actual-loader evidence. Prefill changes neither q/target/Adam nor learn_steps. All600 learning episodes have150 actual updates, yielding90000; env_steps=60000+720×303=278160. Every Adam slot has step90000 and finite moments; final q/target are finite, changed from source, and exactly synchronized. Serialized q/target/optimizer hashes equal the recorded live/reloaded end proof. Validation restores learning and own/global RNG identity.\n\nRNG comparison boundary: actual finetune initialization correctly uses global seed4228, while convenience preflight used28; both Python state hashes were independently reproduced, and actual paired initial global/own RNG states agree. Between separate training games, scheduled DefaultAgent construction resets global NumPy state; before-game300 therefore need not equal the previous post-game global hash. Milestone checks preserve the complete learning and own-agent RNG identity; exact global before/after equality remains required within each validation.\n\nThe original supervisor remains incomplete with its exact known KeyError. Its pinned source and receipt remain preserved; this is acceptance of two actual complete arms, not all-four orchestration completion. No repository files, source, HEAD or weights were changed. No Agent construction/forward/gradient/game occurred.\n\nKnown validation W/D/L (16 games per opponent/time) is descriptive only:\n\n| Arm | After training games | Default W/D/L | Solution W/D/L |\n|---|---:|---|---|\n'
    for arm in ('control18','adapt18'):
        for after in ('0','300','600'):
            vals=known_validation[arm][after]
            wdl=lambda v:f"{v['wins']}/{v['draws']}/{v['losses']}"
            md+=f"| {arm} | {after} | {wdl(vals['default'])} | {wdl(vals['solution92'])} |\n"
    md+='\nThese reused known maps neither nominate a policy nor establish strength. Exact per-match/point totals and checks are in first_wave_independent_audit.json.\n'
    if failed:md+='\nFailures: '+json.dumps(failed,indent=2)+'\n'
    (D/'first_wave_independent_audit.md').write_text(md)
    print(json.dumps(dict(verdict=verdict,checks_total=len(checks),failed=failed,pt_admitted=False,arms=summaries),indent=2))

if __name__=='__main__':main()
