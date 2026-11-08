"""Independent frozen-study acceptance. Run only after explicit root authorization."""
import argparse,csv,datetime,hashlib,json,math,os,runpy,subprocess,sys
from pathlib import Path
ROOT=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
BASE=ROOT/'experiments/analysis/fog_reward_20261108';OPS=BASE/'operations'
HEAD='a3111c3d0aa0aa974298daabe300bba7be157da1'
ARMS=['control41','neutral41','control42','neutral42']
def need(ok,why):
    if not ok: raise ValueError(why)
def read(p): return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def rows(p): return [json.loads(l) for l in p.read_text().splitlines()]
def close(a,b): return math.isclose(a,b,abs_tol=1e-7,rel_tol=1e-8)
def verify_mapping(mapping):
    for name,digest in mapping.items(): need(sha(name)==digest,'hash changed: '+name)
def source_check(source,plans):
    need(subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==source['head']==HEAD,'frozen HEAD changed')
    expected=source['files'];verify_mapping(expected)
    need(str(Path(source['python']).resolve())==source['executable'] and sha(source['python'])==source['executable_sha256'],'interpreter identity changed')
    names=subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z','--cached','--others','--exclude-standard','--','*.py']).split(b'\0')
    inventory={ROOT/os.fsdecode(n) for n in names if n}
    for d in ('scripts','agents','lux'): inventory.update((ROOT/d).rglob('*.py'))
    inventory.update(map(Path,plans))
    for name in ('requirements.txt','pyproject.toml'):
        if (ROOT/name).is_file(): inventory.add(ROOT/name)
    venv=Path(source['python']).parent.parent
    if (venv/'pyvenv.cfg').is_file(): inventory.add(venv/'pyvenv.cfg')
    for engine in (venv/'lib').glob('python*/site-packages/luxai_s3'): inventory.update(engine.rglob('*.py'))
    need({str(p) for p in inventory}==set(expected),'frozen source file inventory changed')

def main():
    p=argparse.ArgumentParser();p.add_argument('--workers-ended-authorized',action='store_true');args=p.parse_args()
    need(args.workers_ended_authorized,'Explicit root authorization required before model imports')
    state=read(BASE/'training_v1/state.json')
    need(state['status']=='done' and not state['active'] and set(state['receipts'])==set(ARMS),'all four workers must have completed')
    need(all(state['jobs'][a]['returncode']==0 for a in ARMS),'nonzero worker return code')
    snapshot=subprocess.check_output(['ps','-axo','pid=,pgid=,args='],text=True)
    pgids={state['jobs'][a]['pgid'] for a in ARMS}
    need(not any(int(parts[1]) in pgids for line in snapshot.splitlines() if len(parts:=line.split(None,2))==3),'registered worker group still alive')
    source_check(state['source'],state['plans']);verify_mapping(state['protected']);verify_mapping(state['inputs'])
    # Only this explicitly authorized, all-workers-ended path imports Torch.
    import torch
    torch.set_num_threads(1)
    def finite(v):
        if isinstance(v,torch.Tensor): need(bool(torch.isfinite(v).all()),'nonfinite tensor')
        elif isinstance(v,dict):
            for x in v.values(): finite(x)
        elif isinstance(v,(list,tuple)):
            for x in v: finite(x)
        elif isinstance(v,float): need(math.isfinite(v),'nonfinite scalar')
    def tensor_hash(state_dict):
        h=hashlib.sha256()
        for key in sorted(state_dict):
            t=state_dict[key].detach().cpu().contiguous()
            h.update(json.dumps([key,str(t.dtype),list(t.shape)],separators=(',',':')).encode()+b'\n')
            h.update(t.reshape(-1).view(torch.uint8).numpy().tobytes())
        return h.hexdigest()
    def tree_hash(value):
        d=hashlib.sha256()
        def emit(b): d.update(len(b).to_bytes(8,'big'));d.update(b)
        def visit(v):
            if isinstance(v,torch.Tensor):
                t=v.detach().cpu().contiguous();emit(b'tensor');emit(str(t.dtype).encode());visit(list(t.shape));emit(t.reshape(-1).view(torch.uint8).numpy().tobytes())
            elif isinstance(v,dict):
                emit(b'dict');emit(str(len(v)).encode())
                for k in sorted(v,key=lambda k:(type(k).__name__,repr(k))): visit(k);visit(v[k])
            elif isinstance(v,(tuple,list)):
                emit(type(v).__name__.encode());emit(str(len(v)).encode())
                for x in v: visit(x)
            elif v is None or isinstance(v,(str,bool,int,float)): emit(type(v).__name__.encode());emit(repr(v).encode())
            else: raise TypeError(type(v))
        visit(value);return d.hexdigest()
    prepared=Path(state['prepared']);manifest=read(prepared/'manifest.json')
    prefill=runpy.run_path('/tmp/sherlock-fog-data-audit.py')
    prefill_checks={str(seed):prefill['audit_pair'](seed,state,manifest) for seed in (41,42)}
    need(all(v and v['status']=='PASS' and v['actual_learning_observed_in_both'] for v in prefill_checks.values()),'prefill admission checks')
    need(sha(manifest['source'])==manifest['source_sha256'],'source checkpoint hash')
    source_cp=torch.load(manifest['source'],map_location='cpu',weights_only=True)
    source_states=[source_cp['q'],*source_cp['ensemble']]
    need(len(source_states)==36,'source component count')
    source_component=source_states[18];finite(source_component);initial_hash=tensor_hash(source_component)
    results={};artifact_hashes={str(BASE/'training_v1/state.json'):sha(BASE/'training_v1/state.json'),str(prepared/'manifest.json'):sha(prepared/'manifest.json')}
    for arm in ARMS:
        seed=int(arm[-2:]);neutral=arm.startswith('neutral');directory=ROOT/'experiments/runs'/f'20261108_fog_reward_{arm}';entry=manifest['arms'][arm]
        receipt=read(directory/'final_receipt.json');audit=read(directory/'training_audit.json');rr=rows(directory/'rollouts.jsonl');vr=rows(directory/'validation_games.jsonl')
        need(state['receipts'][arm]=={str(directory/'final_receipt.json'):sha(directory/'final_receipt.json')},arm+' supervisor receipt binding')
        need(receipt['status']=='done' and receipt['eligible'] is True and receipt['smoke'] is False and receipt['arm']==arm and receipt['component_index']==18 and receipt['run_seed']==seed,arm+' final receipt identity')
        need(receipt['pins']==manifest['pins'] and receipt['pins']['source']==state['source'] and receipt['config']==entry['config'] and receipt['initial_tensor_sha256']==entry['tensor_sha256']==initial_hash,arm+' exact frozen preparation binding')
        need((receipt['actual_prefill_games'],receipt['actual_train_games'],receipt['actual_validation_games'],receipt['learn_steps'],receipt['env_steps'])==(40,400,32,60000,193320),arm+' receipt counts')
        for field,name in [('final_checkpoint_sha256','weights/agent.pth'),('rollouts_sha256','rollouts.jsonl'),('validation_sha256','validation_games.jsonl'),('audit_sha256','training_audit.json'),('train_csv_sha256','train.csv'),('prefill_sha256','prefill_proof.json')]: need(sha(directory/name)==receipt[field],arm+' receipt '+name)
        need(len(rr)==440 and len(vr)==32,arm+' complete raw counts')
        total_unknown=0;total_reward_mass=0.;total_replay=0
        for i,row in enumerate(rr):
            train=i>=40;g=i-40 if train else i;plan=entry['rollout_plan'][i]
            need({k:row[k] for k in ('phase','game','seed','side','opponent')}==plan,arm+' fixed planned rows')
            need(row['phase']==('train' if train else 'prefill') and row['game']==g and row['seed']==7000000+seed*10000+(0 if train else 5000)+g//2 and row['side']==f'player_{g%2}',arm+' independent schedule')
            need(row['steps']==303 and row['point_counting_version']==2 and row['updates']==(150 if train else 0) and row['learn_steps']==max(0,i+1-40)*150 and row['env_steps']==60000+(i+1)*303,arm+' actual updates/chronology')
            a,w,t=row['action_audit'],row['reward_audit'],row['trajectory']
            need(a['act_calls']==a['update_calls']==t['act_calls']==t['step_calls']==303 and t['reset_calls']==1,arm+' per-game trajectory coverage')
            need(a['checked_replay_transitions']==w['transitions']==w['replay_transitions']==t['replay_pushes'],arm+' actual replay coverage')
            need(0<=w['unknown_sap_transitions']<=w['estimated_misses']<=w['sap_transitions']<=w['transitions'],arm+' unknown provenance count bounds')
            mass=w['unknown_sap_transitions']*.3
            need(close(w['unknown_reward_mass'],mass) and close(w['applied_reward_mass'],mass if neutral else 0),arm+' per-game reward masses')
            need(w['actual_reward_sha256']==w[('neutral' if neutral else 'legacy')+'_reward_sha256'],arm+' actual formula')
            need(row['inference_config_id']==tree_hash(manifest['source_config']) and row['rollout_config_id']==tree_hash(entry['config']),arm+' config IDs')
            finite(row);total_unknown+=w['unknown_sap_transitions'];total_reward_mass+=mass;total_replay+=w['replay_transitions']
        expected_val=[dict(after_games=after,opponent=opponent,seed=s,side=f'player_{side}') for after in (0,400) for opponent in ('default','solution92') for s in range(7600000,7600004) for side in (0,1)]
        need([{k:r[k] for k in ('after_games','opponent','seed','side')} for r in vr]==expected_val==manifest['validation_plan'],arm+' complete diagnostics plan')
        need(all(r['steps']==303 and r['point_counting_version']==2 for r in vr),arm+' diagnostic completeness')
        need([v['after_games'] for v in audit['validations']]==[0,400],arm+' diagnostic checkpoints')
        for v in audit['validations']:
            after=v['after_games'];before=v['before'];learning=before['learning']
            need(v['before']==v['after'] and v['config']==manifest['source_config'] and v['config']['fog_unknown_reward_neutral'] is False,arm+' unchanged diagnostic learning/RNG and V14 inference')
            need(learning['config']==entry['config'] and learning['env_steps']==72120+after*303 and learning['learn_steps']==after*150,arm+' diagnostic chronology')
        with (directory/'train.csv').open() as f: csv_rows=list(csv.DictReader(f))
        need(len(csv_rows)==400,arm+' train CSV count')
        for i,r in enumerate(csv_rows):
            actual=rr[i+40]
            need(int(r['game'])==i and int(r['seed'])==actual['seed'] and r['side']==actual['side'] and r['opponent']==actual['opponent'] and int(r['steps'])==303 and int(r['learn_steps'])==(i+1)*150 and int(r['env_steps'])==72120+(i+1)*303 and float(r['epsilon'])==.05 and math.isfinite(float(r['mean_loss'])),arm+' train CSV chronology/loss')
            need(all(float(r[k])==float(actual[k]) for k in ('result','our_wins','opp_wins','our_points','opp_points')),arm+' train CSV results versus raw rows')
        start_path=prepared/arm/'weights/agent.pth';start=torch.load(start_path,map_location='cpu',weights_only=True);cp_path=directory/'weights/agent.pth';cp=torch.load(cp_path,map_location='cpu',weights_only=True);finite(start);finite(cp)
        need(sha(start_path)==entry['weights_sha256'] and 'opt' not in start and start['env_steps']==60000 and start['learn_steps']==0 and tensor_hash(start['q'])==tensor_hash(start['target_q'])==initial_hash,arm+' actual identical initial tensors/fresh checkpoint')
        qh,th,oh=tensor_hash(cp['q']),tensor_hash(cp['target_q']),tree_hash(cp['opt'])
        end=audit['end'];initial=audit['initial']
        need(cp['cfg']==entry['config'] and cp['feature_dim']==79 and cp['n_actions']==6 and not cp['ensemble'] and not cp['ensemble_dims'] and cp['env_steps']==193320 and cp['learn_steps']==60000,arm+' saved final config/counts')
        need(qh!=initial_hash and th!=initial_hash and oh!=initial['learning']['optimizer_sha256'],arm+' changed Q/target/Adam')
        need(qh==end['q_tensor_sha256'] and th==end['target_tensor_sha256'] and oh==end['learning']['optimizer_sha256'] and tree_hash(cp['q'])==end['learning']['q_sha256'] and tree_hash(cp['target_q'])==end['learning']['target_q_sha256'],arm+' actual tensor hashes versus final live audit')
        need(end['reload_verified'] is True and end['saved_weights_sha256']==sha(cp_path),arm+' runtime reload proof binding')
        opt=cp['opt'];ids=[i for group in opt['param_groups'] for i in group['params']]
        need(len(ids)==len(set(ids))==len(cp['q'])==len(opt['state']) and set(ids)==set(opt['state']),arm+' complete Adam parameter membership')
        need(all(group['lr']==5e-5 for group in opt['param_groups']),arm+' Adam learning rate')
        nonzero_moments=0
        for value,param in zip(cp['q'].values(),[opt['state'][i] for i in ids]):
            need(set(param)=={'step','exp_avg','exp_avg_sq'} and param['step'].item()==60000 and param['exp_avg'].shape==param['exp_avg_sq'].shape==value.shape,arm+' Adam step/moment dimensions')
            need(bool((param['exp_avg_sq']>=0).all()),arm+' nonnegative second moments')
            nonzero_moments+=int(bool(torch.count_nonzero(param['exp_avg'])) or bool(torch.count_nonzero(param['exp_avg_sq'])))
        need(nonzero_moments>0,arm+' nonzero learned Adam moments')
        need(not (directory/'weights_best').exists(),arm+' no best checkpoint selected')
        for path in directory.rglob('*'):
            if path.is_file(): artifact_hashes[str(path)]=sha(path)
        for path in (prepared/arm).rglob('*'):
            if path.is_file(): artifact_hashes[str(path)]=sha(path)
        results[arm]=dict(prefill_games=40,learning_games=400,diagnostic_games=32,total_executions=472,updates=60000,env_steps=193320,initial_tensor_sha256=initial_hash,final_q_tensor_sha256=qh,final_target_tensor_sha256=th,final_optimizer_sha256=oh,checkpoint_sha256=sha(cp_path),all_tensors_finite=True,q_target_optimizer_changed=True,adam_parameter_states=len(opt['state']),adam_nonzero_moment_states=nonzero_moments,adam_steps_all=60000,runtime_reload_proof_bound=True,replay_transitions=total_replay,unknown_sap_transitions=total_unknown,counterfactual_reward_mass=total_reward_mass,applied_reward_mass=total_reward_mass if neutral else 0)
        del cp,start
    source_check(state['source'],state['plans']);verify_mapping(state['protected']);verify_mapping(state['inputs']);verify_mapping(artifact_hashes)
    for path in (OPS/'prefill-independent-audit.json',OPS/'prefill-independent-audit.md',BASE/'training_v1/paired_prefill_41.json',BASE/'training_v1/paired_prefill_42.json'):
        artifact_hashes[str(path)]=sha(path)
    result=dict(schema_version=1,status='PASS',kind='independent_frozen_fog_training_acceptance',time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=HEAD,source=state['source'],source_identity_verified_twice=True,protected=state['protected'],prepared_inputs=state['inputs'],artifact_files=artifact_hashes,arms=results,totals=dict(prefill_games=160,learning_games=1600,diagnostic_games=128,total_training_study_executions=1888,updates=240000),prefill_reaudit= {seed:dict(status=v['status'],evidence=v['proof_evidence']) for seed,v in prefill_checks.items()},auditor_scripts={str(Path(__file__)):sha(Path(__file__)),'/tmp/sherlock-fog-data-audit.py':sha('/tmp/sherlock-fog-data-audit.py')},limitations=['Technical training acceptance only; no strength or promotion decision.','Trajectory/replay content identity is audited from frozen recorded hashes and raw summary rows; simulator states/replay insertions were not independently replayed.','Saved tensors loaded independently with Torch; runtime actual Agent reload proof is bound from worker evidence, not rerun by this auditor.'])
    summary='# Independent final Fog training audit\n\n**PASS — technical training acceptance under frozen source '+HEAD+'.**\n\nAll four workers ended before any model import. No games, gradients or tests were executed by this audit.\n\n'
    summary+='Each arm has 40 prefill + 400 learning + 32 diagnostic executions, 60000 optimizer updates and 193320 environment steps. Total: 1888 study executions, 240000 updates.\n\n'
    summary+='| Arm | Q tensor SHA-256 | Target tensor SHA-256 | Adam SHA-256 |\n|---|---|---|---|\n'
    summary+='\n'.join(f"| {arm} | {d['final_q_tensor_sha256']} | {d['final_target_tensor_sha256']} | {d['final_optimizer_sha256']} |" for arm,d in results.items())+'\n\n'
    summary+='Independently loaded saved Q/target/Adam are finite and changed from their exact component-18 starts; every Adam state records 60000 steps. Saved hashes equal final live-state audit hashes. Fixed schedules, all raw rows and CSV chronology, actual reward-formula selection/mass, replay coverage, isolated diagnostics and both prefill admissions pass. Source inventory/content, HEAD, interpreter, preparation and protected V14/ZIP hashes were verified before and after the audit. Full artifact bindings and per-arm counters are in the companion JSON.\n\n'
    summary+='This historical acceptance was produced before changing HEAD/source. Future work should consume these hash bindings; it must not pretend that the current HEAD still equals the training HEAD.\n\nLimits: '+ ' '.join(result['limitations'])+'\n'
    for suffix,content in [('json',json.dumps(result,indent=2)+'\n'),('md',summary)]:
        path=OPS/f'final-independent-audit.{suffix}';temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(content);temp.replace(path)
    print(json.dumps(dict(status=result['status'],source_head=HEAD,totals=result['totals'],artifacts=len(artifact_hashes),arms=results),indent=2))
if __name__=='__main__': main()
