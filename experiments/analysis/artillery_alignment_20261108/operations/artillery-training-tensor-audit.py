#!/usr/bin/env python3
"""Independent final-checkpoint/replay audit; run only after explicit root release.

Preparation imports stdlib only. Torch/NumPy are imported inside run_audit AFTER
the explicit CLI authorization and four-worker completion guards. No project
module is imported, no network is instantiated and no forward/update is run.
Only /tmp/artillery-training-tensor-audit.json and .md are written.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT=Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
BASE=ROOT/'experiments/analysis/artillery_alignment_20261108'
PREPARED=BASE/'prepared_v1'
STATE=BASE/'training_v1/state.json'
HEAD='02ce1b2ce9a5b0780da1ee6462a2368b2226d495'
V14='98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
ARMS=('control43','aligned43','control44','aligned44')
CHECKS=Counter()
BOUND={}


def need(value,category,detail):
    CHECKS[category]+=1
    if not value:raise AssertionError(f'{category}: {detail}')


def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def bind(path,expected=None):
    result=sha_file(path)
    if expected is not None:need(result==expected,'file_hash',str(path))
    BOUND[str(path)]=result
    return result


def load_json(path):return json.loads(Path(path).read_text())


def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])


def stopped_guard():
    """Fail before numeric imports if any original worker remains live."""
    state=load_json(STATE)
    need(state['status']=='done' and not state['active'] and not state['queue'],
         'stopped_guard','supervisor fully complete with empty active/queue')
    need(set(state['jobs'])==set(state['receipts'])==set(ARMS),'stopped_guard','all four jobs/receipts')
    listing=subprocess.check_output(['ps','-axo','pid=,command='],text=True)
    commands={int(line.strip().split(None,1)[0]):line.strip().split(None,1)[1]
              for line in listing.splitlines() if len(line.strip().split(None,1))==2}
    live=[]
    for arm,job in state['jobs'].items():
        need(job['returncode']==0 and 'finished_at' in job,'stopped_guard',f'{arm} exited successfully')
        cmd=commands.get(job['pid'],'')
        if 'scripts.artillery_alignment_study' in cmd and '--arm '+arm in cmd:live.append(arm)
    # Require a single tensor-audit process and no concurrent original study
    # workers, project validator processes or pytest. Root also coordinates the
    # independent validator sequentially; an arbitrary unlabelled process cannot
    # be identified solely from its argv.
    matches=[]
    for pid,cmd in commands.items():
        if pid==os.getpid():continue
        executable=cmd.split(None,1)[0].rsplit('/',1)[-1].lower()
        if 'python' not in executable and executable!='pytest':continue
        if ('scripts.artillery_alignment_study' in cmd or 'pytest' in cmd
                or 'artillery-training-tensor-audit.py' in cmd
                or 'artillery_alignment_study.validate_final_receipt' in cmd):matches.append((pid,cmd))
    need(not live and not matches,'stopped_guard',f'no concurrent model/test work: {live or matches}')
    return state


def source_defaults():
    blob=git('show',f'{HEAD}:agents/sherlock/config.py')
    cls=next(n for n in ast.parse(blob).body if isinstance(n,ast.ClassDef) and n.name=='AgentConfig')
    return {n.target.id:ast.literal_eval(n.value) for n in cls.body if isinstance(n,ast.AnnAssign)}


def normalized(raw,defaults):return {k:raw.get(k,v) for k,v in defaults.items()}


def state_hash(value,torch,np):
    """Independent reproduction of documented typed state bytes, no project call."""
    digest=hashlib.sha256()
    def emit(data):digest.update(len(data).to_bytes(8,'big'));digest.update(data)
    def visit(item):
        if isinstance(item,torch.Tensor):
            t=item.detach().cpu().contiguous();emit(b'tensor');emit(str(t.dtype).encode())
            visit(list(t.shape));emit(t.reshape(-1).view(torch.uint8).numpy().tobytes())
        elif isinstance(item,np.ndarray):
            emit(b'ndarray');emit(item.dtype.str.encode());visit(list(item.shape));emit(item.tobytes(order='C'))
        elif isinstance(item,dict):
            emit(b'dict');emit(str(len(item)).encode())
            for key in sorted(item,key=lambda k:(type(k).__name__,repr(k))):visit(key);visit(item[key])
        elif isinstance(item,(list,tuple)):
            emit(type(item).__name__.encode());emit(str(len(item)).encode())
            for child in item:visit(child)
        elif type(item) in (str,int,float,bool,type(None)):
            emit(type(item).__name__.encode());emit(repr(item).encode())
        elif isinstance(item,np.generic):visit(item.item())
        else:raise TypeError(type(item))
    visit(value);return digest.hexdigest()


def tensor_hash(state,torch):
    digest=hashlib.sha256()
    for key in sorted(state):
        value=state[key].detach().cpu().contiguous()
        digest.update(json.dumps([key,str(value.dtype),list(value.shape)],separators=(',',':')).encode()+b'\n')
        digest.update(value.reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def shapes(hidden):
    # Names/order read from the frozen QNet implementation; no model construction.
    return {'body.0.weight':(hidden,79),'body.0.bias':(hidden,),
            'body.2.weight':(hidden,hidden),'body.2.bias':(hidden,),
            'value.0.weight':(128,hidden),'value.0.bias':(128,),
            'value.2.weight':(1,128),'value.2.bias':(1,),
            'adv.0.weight':(128,hidden),'adv.0.bias':(128,),
            'adv.2.weight':(6,128),'adv.2.bias':(6,)}


def verify_net(net,expected,torch,label):
    need(isinstance(net,dict) and list(net)==list(expected),'network_schema',label+' exact parameter order')
    total=0
    for key,shape in expected.items():
        value=net[key]
        need(isinstance(value,torch.Tensor) and tuple(value.shape)==shape
             and value.dtype==torch.float32 and value.layout==torch.strided,
             'network_schema',label+'/'+key)
        need(bool(torch.isfinite(value).all()),'network_finite',label+'/'+key)
        total+=value.numel()
    return total


def finite_tree(value,torch,label):
    if isinstance(value,torch.Tensor):need(bool(torch.isfinite(value).all()),'checkpoint_finite',label)
    elif isinstance(value,dict):
        for key,child in value.items():finite_tree(child,torch,label+'/'+str(key))
    elif isinstance(value,(list,tuple)):
        for index,child in enumerate(value):finite_tree(child,torch,label+'/'+str(index))
    elif isinstance(value,float):need(math.isfinite(value),'checkpoint_finite',label)


def verify_optimizer(cp,torch,label):
    opt=cp['opt'];q=cp['q']
    need(set(opt)=={'state','param_groups'} and len(opt['param_groups'])==1,'optimizer_schema',label)
    group=opt['param_groups'][0];ids=group['params'];names=list(q)
    need(ids==list(range(len(names))) and set(opt['state'])==set(ids),'optimizer_schema','one state per ordered parameter')
    need(group['lr']==5e-5 and tuple(group['betas'])==(.9,.999) and group['eps']==1e-8
         and group['weight_decay']==0 and group['amsgrad'] is False,'optimizer_recipe','fixed fresh Adam recipe')
    for flag in ('maximize','capturable','differentiable','decoupled_weight_decay'):
        if flag in group:need(group[flag] is False,'optimizer_recipe',flag)
    moments=[]
    for identifier,name in zip(ids,names):
        item=opt['state'][identifier];parameter=q[name]
        need(set(item)=={'step','exp_avg','exp_avg_sq'},'optimizer_schema',name+' exact Adam keys')
        step=item['step']
        need(isinstance(step,torch.Tensor) and step.numel()==1 and bool(torch.isfinite(step).all())
             and step.item()==60000,'optimizer_steps',name+' exactly 60000')
        for field in ('exp_avg','exp_avg_sq'):
            value=item[field]
            need(isinstance(value,torch.Tensor) and value.dtype==parameter.dtype and value.shape==parameter.shape
                 and bool(torch.isfinite(value).all()),'optimizer_moments',name+'/'+field)
        need(bool((item['exp_avg_sq']>=0).all()),'optimizer_moments',name+' nonnegative second moment')
        moments.append(dict(parameter=name,step=int(step.item()),
            first_nonzero=int(torch.count_nonzero(item['exp_avg']).item()),
            second_nonzero=int(torch.count_nonzero(item['exp_avg_sq']).item())))
    need(any(m['first_nonzero'] for m in moments) and any(m['second_nonzero'] for m in moments),
         'optimizer_moments','actual nonzero learned moments')
    return moments


def verify_replay(path,end,rows,np):
    need(path.is_file(),'replay','required receipt replay file exists')
    expected={'s':('float32',(79,)),'ns':('float32',(79,)),'a':('int64',()),
              'r':('float32',()),'done':('float32',()),'mask':('bool',(6,))}
    total=sum(r['action_audit']['checked_replay_transitions'] for r in rows)
    count=min(total,300000);metadata=end['learning']['replay']
    need(metadata['capacity']==300000 and metadata['size']==count and metadata['pos']==total%300000
         and metadata['obs_dim']==79 and metadata['_mask_dim']==6,'replay','ring metadata from actual write counts')
    with zipfile.ZipFile(path) as archive:
        need(sorted(archive.namelist())==sorted(k+'.npy' for k in expected),'replay','exact six serialized arrays')
        stored={name:archive.getinfo(name+'.npy').file_size for name in expected}
    arrays={}
    with np.load(path,allow_pickle=False) as replay:
        need(set(replay.files)==set(expected),'replay','safe array inventory')
        for key,(dtype,tail) in expected.items():
            data=replay[key]
            need(data.dtype==np.dtype(dtype) and data.shape==(count,*tail),'replay_schema',key)
            for start in range(0,count,32768):
                block=data[start:start+32768]
                need(bool(np.isfinite(block).all()),'replay_finite',key)
                if key=='a':need(bool(((block>=0)&(block<6)).all()),'replay_actions','six legal action classes')
                if key=='done':need(bool(((block==0)|(block==1)).all()),'replay_terminal','binary terminal flags')
                if key=='mask':need(bool(block[:,0].all()),'replay_masks','STAY legal in every successor mask')
            actual_sha=hashlib.sha256(memoryview(data).cast('B')).hexdigest()
            arrays[key]=dict(shape=list(data.shape),dtype=data.dtype.str,nbytes=data.nbytes,
                             serialized_npy_bytes=stored[key],array_bytes_sha256=actual_sha)
            if key=='a':arrays[key]['class_counts']=np.bincount(data,minlength=6).tolist()
            if key=='done':arrays[key]['terminal_rows']=int(np.count_nonzero(data))
            del data;gc.collect()
    return dict(rows=count,all_recorded_transition_writes=total,arrays=arrays,
                retained_order='saved oldest first by frozen ReplayBuffer.save; raw chronology not replayed',
                successor_mask_note='mask belongs to the successor; chosen action is not tested against that next-state mask')


def run_audit():
    state=stopped_guard();manifest=load_json(PREPARED/'manifest.json')
    need(state['source']==manifest['pins']['source'] and state['expected_head']==HEAD
         and state['source']['head']==HEAD,'source','exact historical frozen training identity')
    bind(STATE);bind(PREPARED/'manifest.json')
    for path,h in {**state['inputs'],**state['protected']}.items():bind(path,h)
    source_keys=('agents/sherlock/main.py','agents/sherlock/config.py','agents/sherlock/model.py',
                 'agents/sherlock/replay_buffer.py','scripts/artillery_alignment_study.py',
                 'scripts/night_train_pilot.py','scripts/experiment.py')
    bindings={}
    for relative in source_keys:
        expected=state['source']['files'][str(ROOT/relative)]
        actual=hashlib.sha256(git('show',f'{HEAD}:{relative}')).hexdigest()
        need(actual==expected,'source','historical serializer/schema source '+relative)
        bindings[relative]=expected
    need(sha_file(manifest['source'])==manifest['source_sha256']==V14,'source','unchanged V14 source bytes')
    # This is the first possible numeric/model import. The caller must already
    # have supplied --authorize-after-workers-stopped, and stopped_guard passed.
    import numpy as np
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    defaults=source_defaults()
    parent=torch.load(manifest['source'],map_location='cpu',weights_only=True)
    parents=[parent['q'],*parent.get('ensemble',[])]
    need(parent['feature_dim']==79 and parent['n_actions']==6 and len(parents)==36,
         'parent','original homogeneous 36-network source')
    dims=parent.get('ensemble_dims') or [79]*35
    need(dims==[79]*35 and normalized(parent['cfg'],defaults)==manifest['source_config'],
         'parent','source dimensions and full normalized configuration')
    source_cfg=manifest['source_config']
    need(source_cfg['dueling'] is True and source_cfg['hidden']==256,'network_schema','fixed dueling 79-to-6 architecture')
    expected=shapes(source_cfg['hidden']);parent18=parents[18]
    parameter_count=verify_net(parent18,expected,torch,'parent18')
    parent_hash=tensor_hash(parent18,torch)
    reports={}
    for arm in ARMS:
        stopped_guard()
        directory=ROOT/f'experiments/runs/20261108_artillery_alignment_{arm}'
        entry=manifest['arms'][arm];receipt_path=directory/'final_receipt.json'
        expected_config=dict(source_cfg,frozen=False,lr=5e-5,rules_in_training=True,
            rules_in_training_all=True,rescue_in_training=True,fog_unknown_reward_neutral=False,
            art_splash_in_training=arm.startswith('aligned'))
        need(entry['config']==expected_config,'checkpoint_config','independent fixed training recipe '+arm)
        receipt=load_json(receipt_path);audit=load_json(directory/'training_audit.json');end=audit['end']
        need(state['receipts'][arm]=={str(receipt_path):sha_file(receipt_path)},'receipt','supervisor binds receipt '+arm)
        bind(receipt_path);bind(directory/'training_audit.json',receipt['artifacts']['training_audit.json'])
        init_path=PREPARED/arm/'weights/agent.pth';final_path=directory/'weights/agent.pth'
        bind(init_path,entry['weights_sha256']);bind(final_path,receipt['artifacts']['weights/agent.pth'])
        init=torch.load(init_path,map_location='cpu',weights_only=True)
        cp=torch.load(final_path,map_location='cpu',weights_only=True)
        initial_keys={'q','target_q','cfg','feature_dim','n_actions','ensemble','ensemble_dims','env_steps','learn_steps'}
        need(set(init)==initial_keys and set(cp)==initial_keys|{'opt'},'checkpoint_schema','exact initial/final saved keys')
        need(init['cfg']==cp['cfg']==entry['config']==receipt['config'] and not cp['ensemble'] and not cp['ensemble_dims']
             and not init['ensemble'] and not init['ensemble_dims'],'checkpoint_config','single net and exact bound config')
        need(init['env_steps']==60000 and init['learn_steps']==0 and cp['env_steps']==193320 and cp['learn_steps']==60000
             and init['feature_dim']==cp['feature_dim']==79 and init['n_actions']==cp['n_actions']==6,
             'checkpoint_counters','exact dimensions and warm-start/final counters')
        finite_tree(cp,torch,arm)
        for key in ('q','target_q'):
            verify_net(init[key],expected,torch,arm+'/initial/'+key)
            verify_net(cp[key],expected,torch,arm+'/final/'+key)
            need(all(torch.equal(init[key][name],parent18[name]) for name in expected),
                 'initial_parent','every initial Q/target tensor equals V14 component18')
            need(tensor_hash(init[key],torch)==parent_hash==entry['tensor_sha256'],
                 'initial_parent','component tensor hash binding')
        initial=audit['initial'];prefill=audit['prefill']
        need(initial['q_tensor_sha256']==initial['target_tensor_sha256']==prefill['q_tensor_sha256']==prefill['target_tensor_sha256']==parent_hash,
             'initial_parent','initial and prefill proofs agree with actual saved initial tensors')
        changed={key:[name for name in expected if not torch.equal(cp[key][name],init[key][name])] for key in ('q','target_q')}
        need(bool(changed['q']) and bool(changed['target_q']),'learned_change','both Q and target changed from parent')
        tensors={key:tensor_hash(cp[key],torch) for key in ('q','target_q')}
        typed={key:state_hash(cp[key],torch,np) for key in ('q','target_q')}
        optimizer_hash=state_hash(cp['opt'],torch,np)
        need(tensors['q']==end['q_tensor_sha256'] and tensors['target_q']==end['target_tensor_sha256']
             and typed['q']==end['learning']['q_sha256'] and typed['target_q']==end['learning']['target_q_sha256']
             and optimizer_hash==end['learning']['optimizer_sha256'],'end_proof','actual tensors/Adam equal archived end proof')
        need(optimizer_hash!=initial['learning']['optimizer_sha256'] and
             initial['learning']['optimizer_sha256']==prefill['learning']['optimizer_sha256'],
             'learned_change','optimizer changed after unchanged prefill')
        need(end['saved_weights_sha256']==sha_file(final_path) and end['reload_verified'] is True,
             'end_proof','saved bytes and archived original-loader declaration')
        need(end['learning']['config']==entry['config'] and end['learning']['env_steps']==193320
             and end['learning']['learn_steps']==60000,'end_proof','actual final counters match proof')
        moments=verify_optimizer(cp,torch,arm)
        bind(directory/'rollouts.jsonl',receipt['artifacts']['rollouts.jsonl'])
        rows=[json.loads(line) for line in (directory/'rollouts.jsonl').read_text().splitlines()]
        need(len(rows)==440,'replay','exact complete chronology for replay write count')
        replay_path=directory/'weights/agent.buffer.npz'
        bind(replay_path,receipt['artifacts']['weights/agent.buffer.npz'])
        replay=verify_replay(replay_path,end,rows,np)
        reports[arm]=dict(status='PASS',receipt_sha256=sha_file(receipt_path),checkpoint_sha256=sha_file(final_path),
            initial_checkpoint_sha256=sha_file(init_path),parent_component_index=18,parent_tensor_sha256=parent_hash,
            parameter_count=parameter_count,q_tensor_sha256=tensors['q'],target_tensor_sha256=tensors['target_q'],
            optimizer_sha256=optimizer_hash,changed_parameter_names=changed,adam_parameters=moments,
            env_steps=cp['env_steps'],learn_steps=cp['learn_steps'],replay=replay)
        del cp,init,rows;gc.collect()
    for path,h in BOUND.items():need(sha_file(path)==h,'unchanged_after',path)
    need(not any(name=='agents' or name.startswith('agents.') or name=='scripts' or name.startswith('scripts.')
                 for name in sys.modules),'scope','no project modules imported')
    return dict(schema_version=1,status='PASS_TENSORS_AND_REPLAY',eligible_for_comparison=False,
        training_head=HEAD,source_head=HEAD,root=str(ROOT),source=state['source'],
        current_audit_head=git('rev-parse','HEAD').decode().strip(),prepared_manifest_sha256=sha_file(PREPARED/'manifest.json'),
        protected=state['protected'],historical_schema_bindings=bindings,files=BOUND,arms=reports,
        checks_total=sum(CHECKS.values()),checks=dict(CHECKS),torch_version=torch.__version__,numpy_version=np.__version__,
        python=sys.executable,pid=os.getpid(),generated_at_utc=datetime.now(timezone.utc).isoformat(),
        audit_script_sha256=sha_file(__file__),
        limitations=[
            'No network was instantiated or evaluated. Independent CPU weights_only deserialization and exact tensor/schema inspection are performed; the original production-loader check remains separately required.',
            'Initial checkpoint has no optimizer payload. Fresh/unchanged prefill Adam is represented by source-bound initial/prefill proof hashes; final Adam tensors and all 60000 step counters are inspected directly.',
            'Replay is checked for shape, dtype, finite values, action classes, binary terminals and legal STAY successor masks. Raw transition-by-transition environment reconstruction is not performed.',
            'Recorded successor masks are not current-action legality masks. No claim is made that the stored action must be permitted by its successor mask.',
            'The caller must coordinate this one process after all four training workers and separately from original-validator checks. Process labels cannot detect arbitrary unlabelled numeric work.',
            'Technical training completion does not establish stronger gameplay or candidate promotion.'])


def markdown(report):
    lines=['# Independent artillery tensor/replay audit','',report['status'],'']
    if 'error' in report:return '\n'.join(lines+[report['error'],''])
    lines += [f"Checks: {report['checks_total']}. Historical training source `{report['training_head']}`.",'',
              '| Arm | Q changed tensors | Target changed tensors | Adam updates | Replay rows |',
              '| --- | ---: | ---: | ---: | ---: |']
    for arm,r in report['arms'].items():
        lines.append(f"| {arm} | {len(r['changed_parameter_names']['q'])} | {len(r['changed_parameter_names']['target_q'])} | {r['learn_steps']} | {r['replay']['rows']} |")
    lines+=['','Limits:','']+[f'- {s}' for s in report['limitations']]
    lines+=['','No project imports, model forward passes, training updates, games, commits or pushes. All bound input/protected files were unchanged.','']
    return '\n'.join(lines)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorize-after-workers-stopped',action='store_true',
                        help='Supply only after explicit root instruction that all four workers stopped.')
    args=parser.parse_args()
    if not args.authorize_after_workers_stopped:
        parser.error('Explicit root release is required; preparation alone does not authorize model imports.')
    try:result=run_audit()
    except Exception as exc:
        result=dict(status='BLOCKED',error=f'{type(exc).__name__}: {exc}',checks_total=sum(CHECKS.values()),checks=dict(CHECKS))
    Path('/tmp/artillery-training-tensor-audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    Path('/tmp/artillery-training-tensor-audit.md').write_text(markdown(result))
    print(json.dumps({k:v for k,v in result.items() if k in ('status','checks_total','error')}))
    raise SystemExit(1 if result['status']=='BLOCKED' else 0)
