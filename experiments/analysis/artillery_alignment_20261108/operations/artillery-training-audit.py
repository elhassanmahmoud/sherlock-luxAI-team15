#!/usr/bin/env python3
"""Independent stdlib-only audit of the fixed artillery training evidence.

No project imports, NumPy, torch, model deserialization, game execution or pytest.
Only /tmp/artillery-training-audit.json and .md are written. Missing future
artifacts are pending, not errors. Immutable completed bundles are audited fully;
live JSONL files are examined only through their complete flushed row prefix.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import copy
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
BASE = ROOT/'experiments/analysis/artillery_alignment_20261108'
PREPARED = BASE/'prepared_v1'
STATE = BASE/'training_v1/state.json'
HEAD = '02ce1b2ce9a5b0780da1ee6462a2368b2226d495'
V14 = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
ZIP = '88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6'
ARMS = ('control43','aligned43','control44','aligned44')
FIELDS = ('phase','game','seed','side','opponent')
COUNTS = ('helper_calls','new_permissions','actual_new_permissions','executed_additional_saps',
          'canceled_additional_saps','checked_helper_replay')
ARTIFACTS = ('weights/agent.pth','weights/agent.buffer.npz','rollouts.jsonl','validation_games.jsonl',
             'training_audit.json','train.csv','prefill_proof.json','prefill_bundle.json','prefill_events.jsonl')
SETTINGS = dict(prefill=40,games=400,n_val=4,train_base=9000000,val_base=9600000,updates_per_game=150)
# Acquired during this independent audit from the prepared plan that the
# supervisor had already bound before gradients. The audit itself ran later.
# These are acquisition pins, NOT an independent reimplementation of NumPy PCG64.
PLAN_JSON_HASHES = {43:'53dd11dc5092a4ef91c7a70fa4c137563ab810e13d752bf35dab43b1433fd9c7',
                    44:'d19866dec07db5c05d726861272b2a492903444db26ebb44c1023063c028b124'}
CHECKS = Counter()
FILES = {}


def need(value, category, detail):
    CHECKS[category] += 1
    if not value:
        raise AssertionError(f'{category}: {detail}')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):
            h.update(block)
    return h.hexdigest()


def read(path, *, immutable=False):
    data = Path(path).read_bytes()
    if immutable:
        FILES[str(path)] = sha(data)
    return json.loads(data)


def jsonl(path):
    data = Path(path).read_bytes()
    end = data.rfind(b'\n') + 1
    return [json.loads(line) for line in data[:end].splitlines()], {
        'path':str(path),'bytes_read':len(data),'complete_prefix_bytes':end,
        'complete_prefix_sha256':sha(data[:end]),'ignored_unflushed_tail_bytes':len(data)-end}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def state_hash(value):
    """Independent typed encoding for JSON-only config/schedule state trees."""
    digest = hashlib.sha256()
    def emit(data):
        digest.update(len(data).to_bytes(8,'big'));digest.update(data)
    def visit(item):
        t = type(item)
        if t is dict:
            emit(b'dict');emit(str(len(item)).encode())
            for k in sorted(item,key=lambda k:(type(k).__name__,repr(k))):
                visit(k);visit(item[k])
        elif t in (list,tuple):
            emit(t.__name__.encode());emit(str(len(item)).encode())
            for child in item:visit(child)
        elif t in (str,int,float,bool,type(None)):
            emit(t.__name__.encode());emit(repr(item).encode())
        else:raise TypeError(t)
    visit(value)
    return digest.hexdigest()


def valid_hash(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args])


def validation_plan():
    return [dict(after_games=a,opponent=o,seed=s,side=p) for a in (0,400)
            for o in ('default','solution92') for s in range(9600000,9600004)
            for p in ('player_0','player_1')]


def expected_config(source, enabled):
    return dict(source,frozen=False,lr=5e-5,rules_in_training=True,rules_in_training_all=True,
                rescue_in_training=True,fog_unknown_reward_neutral=False,art_splash_in_training=enabled)


def audit_event(e, enabled):
    for k in ('baseline','aligned','actual','new_permission','executed_additional','mirrored','sap_identity_preserved'):
        need(type(e[k]) is bool,'event_types',k)
    need(type(e['step']) is int and 0<=e['step']<303 and type(e['uid']) is int and 0<=e['uid']<16,
         'event_identity','valid step/unit')
    need(type(e['pre_action']) is int and e['pre_action'] in range(5),'event_action','non-SAP proposed action')
    need(type(e['sap']) is list and len(e['sap'])==3 and all(type(v) is int for v in e['sap']),
         'event_action','integer SAP coordinates/hits')
    need(not(e['baseline'] and not e['aligned']),'event_permission','alignment is monotone')
    new = not e['baseline'] and e['aligned']
    need(e['new_permission'] is new and e['actual'] is (e['aligned'] if enabled else e['baseline']),
         'event_permission','actual configured answer and new permission')
    need(valid_hash(e['input_sha256']) and e['input_sha256']==e['restored_sha256'] and e['readonly_checks']==2,
         'event_readonly','recorded restored-input and alternate checks')
    action=e['canonical_action'];native=e['native_action'];replay=e['replay_action']
    need(type(action) is int and action in range(6) and type(replay) is int and replay==action,
         'event_replay','canonical action equals recorded actual ring write')
    need(type(native) is list and len(native)==3 and all(type(v) is int for v in native),
         'event_action','native action triple')
    direction=(0,2,1,4,3)[action] if e['mirrored'] and action<5 else action
    need(native[0]==direction,'event_action','independent antidiagonal direction map')
    if action==5:
        dx,dy=e['sap'][:2]
        target=[5,-dy,-dx] if e['mirrored'] else [5,dx,dy]
        need(e['actual'] and e['sap_identity_preserved'] and native==target,
             'event_action','executed SAP permission/identity/antidiagonal coordinates')
    else:
        need(native[1:]==[0,0] and not e['sap_identity_preserved'],'event_action','canceled SAP evidence')
    executed=bool(enabled and new and action==5)
    need(e['executed_additional'] is executed,'event_attribution','additional execution attribution')
    return dict(helper_calls=1,new_permissions=int(new),actual_new_permissions=int(enabled and new),
                executed_additional_saps=int(executed),canceled_additional_saps=int(enabled and new and not executed),
                checked_helper_replay=1)


def audit_rollout(row,index,entry):
    need({k:row[k] for k in FIELDS}==entry['rollout_plan'][index],'rollout_schedule',str(index))
    expected=dict(steps=303,point_counting_version=2,env_steps=60000+(index+1)*303,
                  learn_steps=max(index-39,0)*150,updates=150 if index>=40 else 0)
    need(all(type(row[k]) is int and row[k]==v for k,v in expected.items()),'rollout_counters',str(index))
    need(row['rollout_config_id']==state_hash(entry['config']),'rollout_config','full config digest')
    a=row['action_audit'];e=row['artillery_audit'];enabled=entry['config']['art_splash_in_training']
    need(a['act_calls']==a['update_calls']==303 and a['checked_replay_transitions']>=e['checked_helper_replay'],
         'rollout_action','act/update/replay counters')
    need(all(type(e[k]) is int and e[k]>=0 for k in COUNTS),'rollout_exposure','nonnegative integer counters')
    need(e['helper_calls']==e['checked_helper_replay'] and e['new_permissions']<=e['helper_calls']
         and e['actual_new_permissions']==e['executed_additional_saps']+e['canceled_additional_saps']
         and e['actual_new_permissions']==(e['new_permissions'] if enabled else 0),
         'rollout_exposure','counter conservation')
    need(valid_hash(e['transcript_sha256']) and valid_hash(a['transcript_sha256']),
         'rollout_hash','transcript SHA format')
    need(row['result'] in (0.,.5,1.) and all(math.isfinite(float(row[k])) for k in ('secs','our_points','opp_points')),
         'rollout_results','finite diagnostic metrics')
    if index>=40:
        need(row['epsilon']==.05 and math.isfinite(row['mean_loss']),'rollout_training','epsilon/finite loss')


def initial_proof(initial,entry):
    learning=initial['learning'];replay=learning['replay']
    need(initial['q_tensor_sha256']==initial['target_tensor_sha256']==entry['tensor_sha256'],
         'initial_proof','Q/target component identity declarations')
    need(learning['q_sha256']==learning['target_q_sha256'] and all(valid_hash(learning[k]) for k in
         ('q_sha256','target_q_sha256','optimizer_sha256')),'initial_proof','typed Q/target/Adam hash declarations')
    need(learning['config']==entry['config'] and learning['env_steps']==60000 and learning['learn_steps']==0
         and learning['learn_enabled'] is True and learning['autosave_on_terminate'] is False
         and learning['recent_losses']==[],'initial_proof','fresh initial counters/config/flags')
    need(replay['size']==replay['pos']==0 and replay['_mask_dim']==1 and replay['capacity']==300000
         and replay['obs_dim']==79,'initial_proof','empty replay metadata')
    identity=initial['initial_identity'];need(identity['schema_version']==1 and len(identity['learners'])==1,
         'initial_proof','one shared learner')
    actual=copy.deepcopy(identity['learners'][0]);sides=actual.pop('sides');rng=actual.pop('agent_rng_sha256')
    need(actual['replay'].pop('logical_content')=='empty-replay-v1' and sides==['player_0','player_1']
         and rng==initial['agent_rng_sha256'] and actual==learning,'initial_proof','nested initial identity consistency')


def audit_events(path, rows, entry, *, complete):
    counts=[Counter(dict.fromkeys(COUNTS,0)) for _ in range(min(40,len(rows)))]
    digests=[hashlib.sha256() for _ in counts]
    raw,snapshot=jsonl(path);seen=set();previous=(-1,-1);pending=0
    for item in raw:
        index=item['rollout_index'];e=item['event']
        need(type(index) is int and 0<=index<40,'event_schedule','fixed prefill index')
        if index>=len(counts):
            pending+=1;continue
        key=(index,e['step']);unique=(*key,e['uid'])
        need(key>=previous and unique not in seen,'event_schedule','ordered unique rollout/step/uid')
        previous=key;seen.add(unique)
        counts[index].update(audit_event(e,entry['config']['art_splash_in_training']))
        digests[index].update(canonical(e)+b'\n')
    if complete:
        need(snapshot['ignored_unflushed_tail_bytes']==0 and pending==0,'event_completeness','closed events complete')
    for index,row in enumerate(rows[:40]):
        need(row['artillery_audit']==dict(counts[index],transcript_sha256=digests[index].hexdigest()),
             'event_recount',f'all six counters and transcript hash for game {index}')
    summed=sum(counts,Counter())
    return dict(events_checked=len(seen),pending_live_events_excluded=pending,
                counts={key:summed[key] for key in COUNTS},snapshot=snapshot)


def prefill_proof(directory,arm,entry,initial,rows):
    proof=read(directory/'prefill_proof.json',immutable=True)
    bundle=read(directory/'prefill_bundle.json',immutable=True)
    need(bundle['arm']==arm and bundle['entry']==entry and bundle['initial']==initial,
         'prefill_bundle','arm/prepared/initial identity')
    need(len(bundle['rows'])==40 and rows[:40]==bundle['rows'],'prefill_bundle','exact forty completed raw rows')
    p=bundle['prefill'];il=initial['learning'];pl=p['learning']
    need(p['q_tensor_sha256']==initial['q_tensor_sha256'] and p['target_tensor_sha256']==initial['target_tensor_sha256']
         and pl['q_sha256']==il['q_sha256'] and pl['target_q_sha256']==il['target_q_sha256']
         and pl['optimizer_sha256']==il['optimizer_sha256'],'prefill_state','unchanged Q/target/Adam proof hashes')
    need(pl['config']==entry['config'] and pl['env_steps']==72120 and pl['learn_steps']==0
         and pl['recent_losses']==[] and pl['learn_enabled'] is False and not pl['autosave_on_terminate']
         and pl['replay']['size']>entry['config']['learn_start'],'prefill_state','zero updates and populated replay')
    transitions=sum(r['action_audit']['checked_replay_transitions'] for r in rows[:40])
    need(pl['replay']['size']==min(transitions,300000) and pl['replay']['pos']==transitions%300000,
         'prefill_state','replay occupancy and ring position versus actual checked writes')
    expected=dict(status='prefill_ready',arm=arm,run_seed=entry['run_seed'],component_index=18,
        actual_prefill_games=40,learn_steps=0,config=entry['config'],initial_tensor_sha256=entry['tensor_sha256'],
        initial_optimizer_sha256=il['optimizer_sha256'],initial_agent_rng_sha256=initial['agent_rng_sha256'],
        initial_global_rng_sha256=initial['global_rng_sha256'],schedule_sha256=state_hash(entry['rollout_plan']),
        replay_size=pl['replay']['size'],unchanged_q=True,unchanged_target=True,unchanged_optimizer=True,
        new_permissions=sum(r['artillery_audit']['new_permissions'] for r in rows[:40]),
        executed_additional_saps=sum(r['artillery_audit']['executed_additional_saps'] for r in rows[:40]),
        bundle_sha256=file_sha(directory/'prefill_bundle.json'),events_sha256=file_sha(directory/'prefill_events.jsonl'))
    need(proof==expected,'prefill_proof','complete independently regenerated proof')
    FILES[str(directory/'prefill_events.jsonl')]=expected['events_sha256']
    return proof,bundle


def csv_fields():
    tree=ast.parse(git('show',f'{HEAD}:scripts/experiment.py'))
    game=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
              and any(isinstance(t,ast.Name) and t.id=='GAME_FIELDS' for t in n.targets))
    return ['game']+game+['epsilon','mean_loss','env_steps','learn_steps','winrate_50']


def final_arm(directory,arm,entry,manifest,rows,audit,bundle):
    receipt=read(directory/'final_receipt.json',immutable=True)
    expected=dict(schema_version=1,status='done',eligible=False,source_sha256=V14,component_index=18,
                  actual_prefill_games=40,actual_train_games=400,actual_validation_games=32,
                  env_steps=193320,learn_steps=60000)
    need(all(receipt.get(k)==v for k,v in expected.items()),'final_receipt','complete fixed counters')
    need(receipt['arm']==arm and receipt['name']==directory.name and receipt['prepared']==str(PREPARED)
         and receipt['config']==entry['config'] and receipt['pins']==manifest['pins']
         and receipt['initial_tensor_sha256']==entry['tensor_sha256'] and receipt['run_seed']==entry['run_seed'],
         'final_receipt','bound prepared origin and role')
    need(set(receipt['artifacts'])==set(ARTIFACTS),'final_artifacts','exact nine raw artifacts')
    for name,expected_hash in receipt['artifacts'].items():
        actual=file_sha(directory/name);need(actual==expected_hash,'final_artifacts',name)
        FILES[str(directory/name)]=actual
    need(len(rows)==440 and audit['initial']==bundle['initial'] and audit['prefill']==bundle['prefill'],
         'final_chronology','complete 440 rows and consistent earlier proofs')
    validations,snapshot=jsonl(directory/'validation_games.jsonl')
    need(snapshot['ignored_unflushed_tail_bytes']==0 and
         [{k:r[k] for k in ('after_games','opponent','seed','side')} for r in validations]==validation_plan(),
         'validation_schedule','all 32 exact diagnostic keys')
    need(all(r['steps']==303 and r['point_counting_version']==2 for r in validations),
         'validation_schedule','complete diagnostic executions')
    need([v['after_games'] for v in audit['validations']]==[0,400],'validation_isolation','initial/final blocks')
    for val in audit['validations']:
        learning=val['before']['learning'];a=val['after_games']
        need(val['before']==val['after'] and val['config']==manifest['source_config']
             and learning['config']==entry['config'] and learning['env_steps']==72120+a*303
             and learning['learn_steps']==a*150 and learning['learn_enabled'] is True,
             'validation_isolation','preserved recorded learning/RNG/config state')
    fields=csv_fields()
    with (directory/'train.csv').open() as stream:
        reader=csv.DictReader(stream);need(reader.fieldnames==fields,'training_csv','exact field inventory');table=list(reader)
    need(len(table)==400,'training_csv','400 learning records')
    for i,row in enumerate(table):
        need(all(str(rows[40+i][k])==row[k] for k in fields),'training_csv',f'exact raw record {i}')
        need(float(row['epsilon'])==.05 and math.isfinite(float(row['mean_loss'])),'training_csv','finite loss/epsilon')
    end=audit['end'];el=end['learning'];il=audit['initial']['learning']
    need(end['reload_verified'] is True and end['saved_weights_sha256']==receipt['artifacts']['weights/agent.pth']
         and end['q_tensor_sha256']!=entry['tensor_sha256'] and end['target_tensor_sha256']!=entry['tensor_sha256']
         and el['optimizer_sha256']!=il['optimizer_sha256'],'final_state_proof','changed final state and reload declaration')
    need(el['config']==entry['config'] and el['env_steps']==193320 and el['learn_steps']==60000
         and el['learn_enabled'] is True and el['autosave_on_terminate'] is False,
         'final_state_proof','final declared counters/config/flags')
    return dict(receipt_path=str(directory/'final_receipt.json'),receipt_sha256=file_sha(directory/'final_receipt.json'),
                checkpoint_path=str(directory/'weights/agent.pth'),final_checkpoint_sha256=receipt['artifacts']['weights/agent.pth'],
                counts=dict(actual_prefill_games=40,actual_train_games=400,actual_validation_games=32,
                            executions=472,env_steps=193320,learn_steps=60000),
                files={str(directory/name):h for name,h in receipt['artifacts'].items()},
                tensor_verification='pending separate authorized model audit; this audit reads hashes and proof declarations only')


def audit():
    state=read(STATE);manifest=read(PREPARED/'manifest.json',immutable=True)
    need(state['expected_head']==state['source']['head']==manifest['pins']['source']['head']==HEAD,
         'source','fixed historical source identity')
    current=git('rev-parse','HEAD').decode().strip()
    if state['status']=='running':need(current==HEAD,'source','active source freeze')
    need(manifest['settings']==SETTINGS and set(manifest['arms'])==set(ARMS)
         and manifest['validation_plan']==validation_plan(),'prepared','exact fixed study budget/roles/validation')
    need(manifest['source_sha256']==V14 and file_sha(manifest['source'])==V14,'protected','V14 source')
    need(state['source']==manifest['pins']['source'] and state['protected']==manifest['pins']['protected'],
         'source','supervisor and prepared pins agree')
    for path,h in {**state['inputs'],**state['protected']}.items():
        need(file_sha(path)==h,'immutable_file',path);FILES[path]=h
    for side in (0,1):
        need(state['protected'][str(ROOT/f'agents/sherlock/weights/agent_p{side}.pth')]==V14,'protected','V14 side')
    need(state['protected'][str(ROOT/'Gruppe15.zip')]==ZIP,'protected','original ZIP')
    sources=[]
    for path,h in state['source']['files'].items():
        relative=Path(path).relative_to(ROOT) if Path(path).is_relative_to(ROOT) else None
        historical=sha(git('show',f'{HEAD}:{relative}')) if relative is not None else file_sha(path)
        need(historical==h,'historical_source',path)
        if state['status']=='running':need(file_sha(path)==h,'live_source_freeze',path)
        FILES[path]=file_sha(path)
        sources.append(dict(path=path,sha256=h,method='historical_git_blob' if relative is not None else 'external_runtime_bytes'))
    need(file_sha(state['source']['executable'])==state['source']['executable_sha256'],'runtime','recorded interpreter bytes')
    need(len(state['active'])<=2,'supervisor','maximum two recorded workers')
    source=manifest['source_config']
    required=dict(art_still=False,sap_still_all=False,smart_sap=False,idle_sap=False,art_move_guard=False,siege=False,
                  end_sap=0,art_sap=True,art_splash=True,sap_no_overkill=True,art_splash_in_training=False,
                  fog_unknown_reward_neutral=False,w_sap_hit=.3,train_every=2,canonical=True,eps_end=.05,
                  eps_decay_steps=60000,learn_start=5000)
    need(all(source.get(k)==v and type(source.get(k)) is type(v) for k,v in required.items()),
         'configuration','all local-attribution and fixed-training assumptions')
    results={};proofs={};full_arms={};pending=[];snapshots=[]
    for arm in ARMS:
        entry=manifest['arms'][arm];seed=int(arm[-2:]);enabled=arm.startswith('aligned')
        need(entry['component_index']==18 and entry['run_seed']==seed and entry['config']==expected_config(source,enabled)
             and entry['mix']=={'solution92':.6,'sol92_sq':.2,'default':.1,'rush':.1},'prepared',arm)
        plan=entry['rollout_plan'];need(len(plan)==440 and sha(canonical(plan))==PLAN_JSON_HASHES[seed],
             'prepared_plan','exact acquired pre-gradient plan pin')
        for index,row in enumerate(plan):
            phase='prefill' if index<40 else 'train';game=index if index<40 else index-40
            need(row==dict(phase=phase,game=game,seed=9000000+seed*10000+(5000 if index<40 else 0)+game//2,
                           side=f'player_{game%2}',opponent=row['opponent']) and row['opponent'] in entry['mix'],
                 'prepared_plan',f'{arm}/{index}')
        need(read(PREPARED/arm/'manifest.json',immutable=True)==dict(variant='artillery_alignment_20261108',
             base_variant='artillery_alignment_20261108',train_games=0,arm=arm,**entry),'prepared','local initial manifest')
        need(file_sha(PREPARED/arm/'weights/agent.pth')==entry['weights_sha256'],'prepared','initial checkpoint bytes')
        directory=ROOT/f'experiments/runs/20261108_artillery_alignment_{arm}'
        if not (directory/'training_audit.json').exists():
            results[arm]={'status':'NOT_STARTED'};pending.append(f'{arm}: initial runtime proof not yet available');continue
        audit=read(directory/'training_audit.json');initial=audit['initial'];initial_proof(initial,entry)
        rows,snapshot=jsonl(directory/'rollouts.jsonl');snapshots.append(snapshot)
        need(len(rows)<=440,'rollout_schedule','no extra games')
        for index,row in enumerate(rows):audit_rollout(row,index,entry)
        closed=(directory/'prefill_proof.json').exists()
        events=audit_events(directory/'prefill_events.jsonl',rows,entry,complete=closed)
        snapshots.append(events.pop('snapshot'))
        results[arm]=dict(status=('TRAINING' if len(rows)>40 else 'PREFILL_COMPLETE') if closed else 'RUNNING_PREFILL',completed_rollouts=len(rows),
             completed_prefill=min(len(rows),40),completed_training=max(0,len(rows)-40),prefill_events=events)
        if closed:
            proof,bundle=prefill_proof(directory,arm,entry,initial,rows);proofs[arm]=proof
            need(audit.get('prefill')==bundle['prefill'],'prefill_bundle','runtime audit equals frozen bundle')
            results[arm]['prefill_proof_sha256']=file_sha(directory/'prefill_proof.json')
            if (directory/'final_receipt.json').exists():
                full_arms[arm]=final_arm(directory,arm,entry,manifest,rows,audit,bundle)
                results[arm]['status']='FINAL_DATA_VERIFIED'
            else:pending.append(f'{arm}: final receipt, final tensors and full 400+32 completion pending')
        else:pending.append(f'{arm}: full forty-game prefill proof/pair gate pending')
    paired={}
    for seed in (43,44):
        c=manifest['arms'][f'control{seed}'];a=manifest['arms'][f'aligned{seed}']
        need(c['rollout_plan']==a['rollout_plan'] and c['tensor_sha256']==a['tensor_sha256']
             and dict(c['config'],art_splash_in_training=True)==a['config'],'prepared_pair','one flag and identical start/schedule')
        roles=(f'control{seed}',f'aligned{seed}');gatepath=BASE/f'training_v1/paired_prefill_{seed}.json'
        if not all(role in proofs for role in roles) or not gatepath.exists():
            pending.append(f'pair {seed}: completed paired gate pending');continue
        cp,ap=(proofs[r] for r in roles)
        shared=('initial_tensor_sha256','initial_optimizer_sha256','initial_agent_rng_sha256','initial_global_rng_sha256','schedule_sha256')
        need(all(cp[k]==ap[k] for k in shared) and cp['executed_additional_saps']==0
             and 0<ap['executed_additional_saps']<=ap['new_permissions'],'pair_gate','shared initial evidence and observed treatment effect')
        expected=dict(status='matched',run_seed=seed,eligible=False,initial_evidence={k:cp[k] for k in shared},
             executed_additional_saps=ap['executed_additional_saps'],
             note='Common initial state/schedule only; trajectories and replay may diverge',
             proof_sha256={role:{str(ROOT/f'experiments/runs/20261108_artillery_alignment_{role}/prefill_proof.json'):
                 file_sha(ROOT/f'experiments/runs/20261108_artillery_alignment_{role}/prefill_proof.json')} for role in roles})
        need(read(gatepath,immutable=True)==expected,'pair_gate','exact independently recomputed gate')
        paired[str(seed)]=dict(path=str(gatepath),sha256=file_sha(gatepath),executed_additional_saps=ap['executed_additional_saps'])
    fresh=read(STATE);all_done=len(full_arms)==4 and fresh['status']=='done'
    if all_done:
        need(not fresh['active'] and not fresh['queue'] and set(fresh['receipts'])==set(ARMS),
             'supervisor','closed complete queue and receipts')
        for arm,entry in full_arms.items():
            need(fresh['receipts'][arm]=={entry['receipt_path']:entry['receipt_sha256']},'supervisor','receipt binding')
        for seed,gate in paired.items():
            need(fresh['paired_prefill'][seed]==read(gate['path']),'supervisor','pair gate binding')
        FILES[str(STATE)]=file_sha(STATE)
    else:pending.append('supervisor: complete four-arm state pending')
    for path,h in FILES.items():need(file_sha(path)==h,'immutable_file_after',path)
    forbidden=[name for name in sys.modules if name.split('.')[0] in ('numpy','torch','jax','agents','scripts','luxai_s3','pytest')]
    need(not forbidden,'scope','no numeric/model/project/game/test imports')
    return dict(schema_version=1,status='PASS_DATA_ONLY' if all_done else 'PASS_PARTIAL',eligible_for_comparison=False,
        source_head=HEAD,training_head=HEAD,current_audit_head=current,root=str(ROOT),prepared=str(PREPARED),
        prepared_manifest_sha256=file_sha(PREPARED/'manifest.json'),source=state['source'],protected=state['protected'],
        supervisor=dict(path=str(STATE),sha256=file_sha(STATE),observed_status=fresh['status']),
        supervisor_state_sha256=file_sha(STATE),paired_prefill=paired,arms=full_arms,arm_progress=results,
        totals=dict(actual_prefill_games=160,actual_train_games=1600,actual_validation_games=128,
                    executions=1888,learn_steps=240000) if all_done else None,
        checks_total=sum(CHECKS.values()),checks=dict(CHECKS),files=FILES,historical_source_bindings=sources,
        live_snapshots=snapshots,pending=pending,prohibited_modules_loaded=forbidden,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),audit_script_sha256=file_sha(__file__),
        limitations=[
            'No model was loaded. Tensor contents/finiteness, actual optimizer moments and actual reload are not independently verified by this stdlib audit; source-bound proof declarations and file hashes are checked only.',
            'Only prefill helper events are stored individually. Training exposure is checked for exact schedules, conserved aggregates and recorded digest format, not rehashed from unavailable per-event training logs.',
            'Event context itself is not archived here; before/restored digest equality is checked, not independently reconstructed helper inputs or boolean formulas.',
            'Opponent order is checked against the supervisor-bound pre-gradient prepared schedule and its acquisition pin; NumPy PCG64 is not reimplemented.',
            'Running-file snapshots are complete row prefixes, not an atomic snapshot of all live files; future and unflushed entries are excluded and missing future completion is pending.',
            'No strength, reward causality, candidate promotion or training-rule quality claim follows from this technical data audit.'])


def selfcheck():
    """Tiny in-memory synthetic cases only; never invoke pytest or a game."""
    before=CHECKS.copy();cases=0;rejected=0
    good=dict(step=7,uid=2,pre_action=1,sap=[2,-3,2],baseline=False,aligned=True,actual=True,
              new_permission=True,mirrored=False,input_sha256='a'*64,restored_sha256='a'*64,readonly_checks=2,
              sap_identity_preserved=True,native_action=[5,2,-3],canonical_action=5,executed_additional=True,replay_action=5)
    need(audit_event(good,True)['executed_additional_saps']==1,'selfcheck','direct additional SAP');cases+=1
    mirrored=dict(good,mirrored=True,native_action=[5,3,-2]);audit_event(mirrored,True);cases+=1
    canceled=dict(good,sap_identity_preserved=False,native_action=[1,0,0],canonical_action=1,
                  replay_action=1,executed_additional=False)
    need(audit_event(canceled,True)['canceled_additional_saps']==1,'selfcheck','later cancellation');cases+=1
    control=dict(canceled,actual=False);need(audit_event(control,False)['actual_new_permissions']==0,'selfcheck','control exposure');cases+=1
    for delta in ({'replay_action':2},{'native_action':[5,3,-2]},{'restored_sha256':'b'*64},
                  {'actual':False},{'executed_additional':False},{'baseline':True,'aligned':False},
                  {'uid':16},{'new_permission':1},{'sap_identity_preserved':False}):
        try:audit_event(dict(good,**delta),True)
        except AssertionError:rejected+=1
        else:raise AssertionError(f'selfcheck accepted corrupted event {delta}')
    need(rejected==9,'selfcheck','nine corrupted synthetic cases rejected')
    need(state_hash({'b':2,'a':[True,None]})==state_hash({'a':[True,None],'b':2})
         and state_hash([1])!=state_hash((1,)) and state_hash(True)!=state_hash(1),
         'selfcheck','typed hash order invariance and type separation');cases+=1
    CHECKS.clear();CHECKS.update(before)
    return dict(status='PASS',valid_synthetic_cases=cases,corrupt_synthetic_cases_rejected=rejected,
                scope='in-memory stdlib-only primitive audit checks; no pytest/models/games/files')


def markdown(r):
    lines=['# Artillery training data audit','',r['status'],'',f"Checks: {r.get('checks_total',0)}.",'']
    if 'error' in r:return '\n'.join(lines+[r['error'],''])
    lines+=['| Arm | State | Prefill | Training | Recounted prefill events | Additional executed SAPs |',
            '| --- | --- | ---: | ---: | ---: | ---: |']
    for arm,row in r['arm_progress'].items():
        event=row.get('prefill_events',{});count=event.get('counts',{})
        lines.append(f"| {arm} | {row['status']} | {row.get('completed_prefill',0)} | {row.get('completed_training',0)} | {event.get('events_checked',0)} | {count.get('executed_additional_saps',0)} |")
    lines+=['',f"Frozen source `{r['source_head']}`. All source/initial/protected inputs are read-only. No model/runtime imports or game executions. Missing future evidence remains pending.",'',
            'Limits:','']+[f'- {x}' for x in r['limitations']]
    lines+=['','Pending:','']+[f'- {x}' for x in r['pending']]
    lines+=['',f"Synthetic self-check: {r['selfcheck']}.",'','Re-run: `python3 -B /tmp/artillery-training-audit.py`','']
    return '\n'.join(lines)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--selfcheck-only',action='store_true');args=parser.parse_args()
    try:
        # The already archived v1/v2 include the tiny synthetic primitive check.
        # Ordinary data audits during active training do not repeat any tests.
        synthetic=selfcheck() if args.selfcheck_only else dict(status='NOT_RUN',
            prior_evidence='/tmp/artillery-training-audit.v1.json',
            note='Synthetic checks run only when --selfcheck-only is explicitly requested.')
        result=dict(status='SELF_CHECK_PASS',selfcheck=synthetic) if args.selfcheck_only else dict(audit(),selfcheck=synthetic)
    except Exception as exc:
        result=dict(status='BLOCKED',error=f'{type(exc).__name__}: {exc}',checks_total=sum(CHECKS.values()),checks=dict(CHECKS))
    if not args.selfcheck_only:
        Path('/tmp/artillery-training-audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        Path('/tmp/artillery-training-audit.md').write_text(markdown(result))
    print(json.dumps({k:v for k,v in result.items() if k in ('status','checks_total','error','arm_progress','selfcheck')}))
    raise SystemExit(1 if result['status']=='BLOCKED' else 0)
