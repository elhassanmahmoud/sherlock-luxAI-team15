import json,hashlib,math,datetime,sys,copy
from pathlib import Path
ROOT=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
BASE=ROOT/'experiments/analysis/fog_reward_20261108'
OPS=BASE/'operations'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,why):
    if not ok: raise ValueError(why)
def h(value):
    # Independently reproduce experiment.state_sha256 for persisted JSON trees:
    # every tag/value is prefixed by its 8-byte big-endian byte length.
    d=hashlib.sha256()
    def emit(b): d.update(len(b).to_bytes(8,'big'));d.update(b)
    def visit(v):
        if isinstance(v,dict):
            emit(b'dict');emit(str(len(v)).encode())
            for k in sorted(v,key=lambda k:(type(k).__name__,repr(k))): visit(k);visit(v[k])
        elif isinstance(v,list):
            emit(b'list');emit(str(len(v)).encode())
            for x in v: visit(x)
        elif v is None or isinstance(v,(str,int,float,bool)):
            emit(type(v).__name__.encode());emit(repr(v).encode())
        else: raise TypeError(type(v))
    visit(value);return d.hexdigest()
def rows(p):
    if not p.exists(): return []
    content=p.read_text();lines=content.splitlines()
    if content and not content.endswith('\n'): lines=lines[:-1]
    return [json.loads(l) for l in lines]
def close(a,b): return math.isclose(a,b,abs_tol=1e-7,rel_tol=1e-8)
def normalize(v):
    if isinstance(v,dict): return {k:normalize(x) for k,x in v.items() if k!='fog_unknown_reward_neutral'}
    if isinstance(v,list): return [normalize(x) for x in v]
    return v

def audit_pair(seed,state,manifest):
    admission_path=BASE/'training_v1'/f'paired_prefill_{seed}.json'
    if not admission_path.exists(): return None
    admission=read(admission_path)
    need(admission['status']=='matched' and admission['run_seed']==seed and admission['smoke'] is False,'invalid pair admission')
    bundles=[];proofs=[];details={};evidence_hashes={str(admission_path):sha(admission_path)}
    for role,neutral in [('control',False),('neutral',True)]:
        arm=f'{role}{seed}';directory=ROOT/'experiments/runs'/f'20261108_fog_reward_{arm}'
        bp=directory/'prefill_bundle.json';pp=directory/'prefill_proof.json'
        bundle,proof=read(bp),read(pp);entry=manifest['arms'][arm];cfg=entry['config']
        need(proof['bundle_sha256']==sha(bp),arm+' frozen bundle hash')
        need(admission['proof_sha256'][arm]=={str(pp):sha(pp)},arm+' admitted proof hash')
        need(bundle['arm']==arm and bundle['entry']==entry,arm+' preparation binding')
        need(cfg['fog_unknown_reward_neutral'] is neutral and cfg['w_sap_hit']==.3 and cfg['use_shaping'] is True,arm+' treatment config')
        need(cfg['lr']==5e-5 and cfg['train_every']==2 and cfg['rescue_in_training'] is True and cfg['rules_in_training'] is True and cfg['rules_in_training_all'] is True and cfg['frozen'] is False,arm+' fixed training config')
        need(entry['component_index']==18 and entry['run_seed']==seed and entry['mix']=={'solution92':.6,'sol92_sq':.2,'default':.1,'rush':.1},arm+' fixed arm')
        initial,prefill,rr=bundle['initial'],bundle['prefill'],bundle['rows'];il,pl=initial['learning'],prefill['learning']
        need(initial['q_tensor_sha256']==initial['target_tensor_sha256']==prefill['q_tensor_sha256']==prefill['target_tensor_sha256']==entry['tensor_sha256'],arm+' unchanged Q/target')
        need(il['optimizer_sha256']==pl['optimizer_sha256'],arm+' unchanged optimizer')
        need(il['config']==pl['config']==cfg and il['env_steps']==60000 and il['learn_steps']==pl['learn_steps']==0 and pl['env_steps']==72120 and not il['recent_losses'] and not pl['recent_losses'],arm+' initial/prefill chronology')
        need(il['replay']['size']==il['replay']['pos']==0 and il['replay']['_mask_dim']==1 and pl['replay']['size']>cfg['learn_start'] and pl['learn_enabled'] is False,arm+' replay/gradient gate')
        need(len(rr)==40,arm+' exactly 40 prefill rows')
        live=rows(directory/'rollouts.jsonl');need(live[:40]==rr,arm+' immutable bundle versus raw first 40 rows')
        total_unknown=0;total_mass=0.;total_transitions=0
        for i,r in enumerate(rr):
            need({k:r[k] for k in ('phase','game','seed','side','opponent')}==entry['rollout_plan'][i],arm+' prepared game/opponent plan')
            need(r['phase']=='prefill' and r['game']==i and r['seed']==7000000+seed*10000+5000+i//2 and r['side']==f'player_{i%2}' and r['steps']==303 and r['point_counting_version']==2 and r['updates']==r['learn_steps']==0 and r['env_steps']==60000+(i+1)*303,arm+' raw prefill chronology')
            a,w,t=r['action_audit'],r['reward_audit'],r['trajectory']
            need(a['act_calls']==a['update_calls']==t['step_calls']==t['act_calls']==303 and t['reset_calls']==1,arm+' full game instrumentation')
            need(a['checked_replay_transitions']==w['transitions']==w['replay_transitions']==t['replay_pushes'],arm+' replay coverage')
            need(0<=w['unknown_sap_transitions']<=w['estimated_misses']<=w['sap_transitions']<=w['transitions'],arm+' explicit unknown exposure bounds')
            need(close(w['unknown_reward_mass'],w['unknown_sap_transitions']*.3) and close(w['applied_reward_mass'],w['unknown_reward_mass'] if neutral else 0),arm+' reward mass')
            need(w['actual_reward_sha256']==w[('neutral' if neutral else 'legacy')+'_reward_sha256'],arm+' actual reward formula selection')
            need(r['inference_config_id']==h(manifest['source_config']) and r['rollout_config_id']==h(cfg),arm+' config identifiers')
            total_unknown+=w['unknown_sap_transitions'];total_mass+=w['unknown_reward_mass'];total_transitions+=w['transitions']
        need(total_unknown>0 and total_mass>0,arm+' nonzero unknown exposure')
        total_mass=sum(r['reward_audit']['unknown_reward_mass'] for r in rr)
        trajectory=h([[r['trajectory'],r['action_audit'],{k:r[k] for k in ('phase','game','seed','side','opponent','steps','result','our_wins','opp_wins','our_points','opp_points')}] for r in rr])
        expected=dict(status='prefill_ready',arm=arm,smoke=False,run_seed=seed,component_index=18,actual_prefill_games=40,learn_steps=0,unknown_sap_transitions=total_unknown,unknown_reward_mass=total_mass,trajectory_sha256=trajectory,replay_without_reward_sha256=bundle['replay_without_reward_sha256'],unchanged_q=True,unchanged_target=True,unchanged_optimizer=True,bundle_sha256=sha(bp))
        for kind in ('legacy','neutral','actual'): expected[kind+'_reward_sha256']=h([r['reward_audit'][kind+'_reward_sha256'] for r in rr])
        need(proof==expected,arm+' independently recomputed proof '+repr({k:(proof.get(k),expected.get(k)) for k in set(proof)|set(expected) if proof.get(k)!=expected.get(k)}))
        learning=live[40:]
        for i,r in enumerate(learning):
            need(r['phase']=='train' and r['game']==i and r['updates']==150 and r['learn_steps']==(i+1)*150 and r['env_steps']==72120+(i+1)*303,arm+' actual post-admission learning chronology')
        details[arm]=dict(prefill_games=40,unknown_sap_transitions=total_unknown,unknown_reward_mass=total_mass,applied_reward_mass=total_mass if neutral else 0,replay_transitions=total_transitions,complete_training_rows_observed=len(learning),actual_updates_observed=learning[-1]['learn_steps'] if learning else 0)
        evidence_hashes.update({str(bp):sha(bp),str(pp):sha(pp)})
        bundles.append(bundle);proofs.append(proof)
    c,n=bundles
    need(c['entry']['rollout_plan']==n['entry']['rollout_plan'],'paired exact schedule')
    need(c['entry']['tensor_sha256']==n['entry']['tensor_sha256'],'paired initial tensors')
    need({k for k in c['entry']['config'] if c['entry']['config'][k]!=n['entry']['config'][k]}=={'fog_unknown_reward_neutral'},'only flag differs')
    need(normalize(c['initial'])==normalize(n['initial']),'paired complete initial identities')
    fields=('trajectory_sha256','replay_without_reward_sha256','legacy_reward_sha256','neutral_reward_sha256','unknown_sap_transitions','unknown_reward_mass')
    need(all(proofs[0][k]==proofs[1][k]==admission['evidence'][k] for k in fields),'paired trajectory/replay/counterfactual proof equality')
    need(all(a['trajectory']==b['trajectory'] and a['action_audit']==b['action_audit'] for a,b in zip(c['rows'],n['rows'])),'per-game trajectory/action equality')
    for left,right in zip(c['rows'],n['rows']):
        a,b=left['reward_audit'],right['reward_audit']
        omitted={'applied_reward_mass','actual_reward_sum','actual_reward_sha256'}
        need({k:v for k,v in a.items() if k not in omitted}=={k:v for k,v in b.items() if k not in omitted},'paired per-game reward/counterfactual coverage')
        need(close(b['actual_reward_sum']-a['actual_reward_sum'],a['unknown_reward_mass']),'paired actual reward-sum delta equals unknown mass')
    return dict(status='PASS',seed=seed,arms=details,proof_evidence={k:proofs[0][k] for k in fields},files=evidence_hashes,actual_learning_observed_in_both=all(v['actual_updates_observed']>0 for v in details.values()))

def main():
    state=read(BASE/'training_v1/state.json');manifest=read(Path(state['prepared'])/'manifest.json')
    need(state['expected_head']=='a3111c3d0aa0aa974298daabe300bba7be157da1','unexpected frozen head')
    result=dict(status='pending',time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=state['expected_head'],supervisor_status=state['status'],pairs={},scope='Independent stdlib artifact audit; trajectory/replay hashes are recorded receipts, not independently replayed raw simulator states or replay arrays. No model imports, games, gradients or tests.')
    for seed in (41,42):
        pair=audit_pair(seed,state,manifest)
        if pair: result['pairs'][str(seed)]=pair
    if not result['pairs']: print(json.dumps({'status':'pending','supervisor_status':state['status']}));return
    result['status']='PASS' if len(result['pairs'])==2 else 'provisional_PASS_41'
    for suffix,content in [('json',json.dumps(result,indent=2)+'\n'),('md','# Independent Fog prefill data audit\n\n'+result['status']+' at '+result['time_utc']+'\n\n'+result['scope']+'\n\n'+ '\n'.join(f"- Seed {seed}: PASS; "+'; '.join(f"{arm}: 40 prefill games, {d['unknown_sap_transitions']} unknown SAP transitions, mass {d['unknown_reward_mass']:.6f}, {d['actual_updates_observed']} post-admission updates observed" for arm,d in pair['arms'].items()) for seed,pair in result['pairs'].items())+'\n\nChecks: fixed component/config/schedules; zero prefill gradients; unchanged Q/target/optimizer identities; full per-game replay counts; unknown exposure and reward mass; actual formula hashes; frozen bundle/proof hashes and raw-row correspondence; independently recomputed aggregate hashes; paired trajectory/replay/counterfactual equality. Complete model/optimizer tensor audit is deferred until every worker has ended.\n')]:
        out=OPS/f'prefill-independent-audit.{suffix}';tmp=out.with_suffix(out.suffix+'.tmp');tmp.write_text(content);tmp.replace(out)
    print(json.dumps({k:v for k,v in result.items() if k!='pairs'}|{'pairs':{seed:{'arms':p['arms'],'actual_learning_observed_in_both':p['actual_learning_observed_in_both']} for seed,p in result['pairs'].items()}}))
if __name__=='__main__': main()
