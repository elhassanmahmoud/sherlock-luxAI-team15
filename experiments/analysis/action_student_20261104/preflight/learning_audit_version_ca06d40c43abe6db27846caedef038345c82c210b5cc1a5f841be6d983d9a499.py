#!/usr/bin/env python3
"""Independent full-row action-student audit. Never calls production metric helpers.

Read completed artifacts only, by explicit CLI invocation. Inference only; no
games, optimization or training. Every artifact written shares learning_audit prefix.
"""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')
sys.path.insert(0, str(ROOT))
from agents.sherlock.model import QNet

V14 = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
S30 = '3104596d5527d644d0c3f2cfc98189ec166e6e8e4a1f0ae9a4166f27a934b11b'
SCHEMA = {
    's': ('float32', (79,)), 'mask': ('bool', (6,)),
    'teacher_q': ('float32', (6,)), 'student_q': ('float32', (6,)),
    'final_action': ('int8', ()), 'world_action': ('int16', (3,)),
    'game_index': ('int32', ()), 'env_seed': ('int64', ()),
    'side': ('int8', ()), 'env_step': ('int16', ()),
    'match_step': ('int16', ()), 'uid': ('int8', ()), 'is_train': ('bool', ())}

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def read(path): return json.loads(Path(path).read_text())

def require(value, message):
    if not value: raise AssertionError(message)

def pins(mapping):
    for name, expected in mapping.items():
        require(sha(name) == expected, f'current file differs from pin: {name}')

def student(path):
    cp = torch.load(path, map_location='cpu', weights_only=True)
    base = {'q','target_q','cfg','feature_dim','n_actions','ensemble','ensemble_dims','env_steps','learn_steps'}
    provenance = {'distillation_updates','distillation_epochs','distillation_seed'}
    require(set(cp) in (base, base | provenance), 'single export keys/optimizer/replay')
    require(cp['feature_dim']==79 and cp['n_actions']==6 and cp['ensemble']==[] and cp['ensemble_dims']==[], 'single 79/6 export')
    require(cp['env_steps']==60000 and cp['learn_steps']==0, 'explicit exploration offset and no RL steps')
    require(cp['cfg']['hidden']==512 and cp['cfg']['dueling'], 'single 512 dueling')
    require(set(cp['q'])==set(cp['target_q']), 'target keys')
    require(all(torch.equal(v,cp['target_q'][k]) for k,v in cp['q'].items()), 'q and target equal')
    require(all(torch.isfinite(v).all() for v in cp['q'].values()), 'finite student')
    net = QNet(79,6,512,True).eval()
    net.load_state_dict(cp['q'], strict=True)
    require(sum(p.numel() for p in net.parameters())==435847, 'single parameter count')
    return net, cp

@torch.no_grad()
def predict(net, s, batch=1024):
    out = np.empty((len(s),6), np.float32)
    for start in range(0,len(s),batch): out[start:start+batch] = net(torch.from_numpy(s[start:start+batch])).numpy()
    return out

def centered(x, m):
    x = np.asarray(x,dtype=np.float64)
    return np.where(m, x - np.where(m,x,0).sum(1,keepdims=True)/m.sum(1,keepdims=True), 0.)

def metrics(prediction, a, select):
    p, t, m = prediction[select].astype(np.float64), a['teacher_q'][select].astype(np.float64), a['mask'][select]
    c, f = a['student_q'][select], a['final_action'][select]
    row, count = np.arange(len(t)), m.sum(1)
    choice, best = np.where(m,p,-np.inf).argmax(1), np.where(m,t,-np.inf).argmax(1)
    delta = np.where(m,p-t,0.)
    return dict(rows=len(t), masked_argmax_agreement=float(np.mean(choice==best)),
        legal_regret=float(np.mean(t[row,best]-t[row,choice])),
        legal_q_mse=float(np.mean(np.sum(delta*delta,axis=1)/count)),
        centered_legal_q_mse=float(np.mean(np.sum((centered(p,m)-centered(t,m))**2,axis=1)/count)),
        legal_mean_q_mse=float(np.mean((delta.sum(1)/count)**2)),
        recorded_collector_rule_override_rate=float(np.mean(f!=np.where(m,c,-np.inf).argmax(1))),
        recorded_collector_final_outside_mask_rate=float(np.mean(~m[row,f])))

def compare(actual, expected, label='', atol=1e-9):
    require(set(actual)==set(expected), f'{label} keys')
    for k,v in actual.items():
        if isinstance(v,dict): compare(v,expected[k],label+'.'+k,atol)
        elif isinstance(v,(float,int)):
            require(math.isclose(v,expected[k],rel_tol=2e-10,abs_tol=atol), f'{label}.{k}: independent {v}, reported {expected[k]}')
        else: require(v==expected[k],f'{label}.{k} differs')

def dataset(path, expected_student, verify_teacher=True):
    path=Path(path).resolve()
    manifest,status=read(path/'manifest.json'),read(path/'status.json')
    require(manifest['status']==status['status']=='done', 'collector completed first')
    require(manifest['schema_version']==1 and manifest['maps']==30 and not manifest['technical_test_only'], 'actual full collector schema/budget')
    require(manifest['games_completed']==60 and manifest['seed_start']==865100, 'actual 60 games / fixed seeds')
    require(manifest['teacher_sha256']==V14 and manifest['teacher_members']==36, 'teacher pin and members')
    require(manifest['student_sha256']==expected_student, 'collector S30/A1 identity')
    require(manifest['inputs_before']==manifest['inputs_after'] and manifest['pins_before']==manifest['pins_after'], 'collection input/source freeze')
    require(manifest['learning_state_before']==manifest['learning_state_after'], 'collection eval-state attestation')
    require(manifest['teacher_gradients_absent'], 'teacher no gradients')
    for kind in ('sources','protected'): pins(manifest['pins_before'][kind])
    pins(manifest['inputs_before'])
    require(set(manifest['files_sha256'])=={'dataset.npz','games.jsonl'}, 'exact file hashes')
    for name,h in manifest['files_sha256'].items(): require(sha(path/name)==h, 'serialized '+name+' hash')
    with np.load(path/'dataset.npz',allow_pickle=False) as z:
        require(set(z.files)==set(SCHEMA),'array schema keys')
        a={k:z[k] for k in SCHEMA}
    n=len(a['s'])
    for k,(dtype,shape) in SCHEMA.items():
        require(a[k].dtype==np.dtype(dtype) and a[k].shape==(n,*shape),k+' shape/dtype')
        require(np.isfinite(a[k]).all(),k+' finite')
    require(n==manifest['rows'] and n>0,'row count')
    require(a['mask'].any(1).all(),'no empty network masks')
    require(((a['uid']>=0)&(a['uid']<16)).all(),'unit identities')
    require(((a['env_step']>0)&(a['env_step']<303)).all(),'no reset first step / env step range')
    require(((a['match_step']>0)&(a['match_step']<=100)).all(),'no match-reset rows')
    require(((a['final_action']>=0)&(a['final_action']<=5)).all(),'canonical final actions')
    ids=np.stack([a[k] for k in ('game_index','env_step','uid')],axis=1)
    require(len(np.unique(ids,axis=0))==n,'all current game/step/unit identities unique')
    plan=[]
    for i in range(30):
        for side in (0,1):
            plan.append(dict(game_index=2*i+side,env_seed=865100+i,side=side,side_name=f'player_{side}',
                             opponent=('solution92','solution92','solution92','default','self')[i%5],is_train=i<25))
    require(manifest['game_plan']==plan,'exact planned 30 maps / both sides / opponents / whole-map split')
    games=[json.loads(line) for line in (path/'games.jsonl').read_text().splitlines()]
    require(len(games)==60,'actual 60 logged completed games')
    for g,planned in zip(games,plan):
        for key in ('game_index','env_seed','is_train','opponent'): require(g[key]==planned[key],f'actual game {key}')
        require(g['seed']==planned['env_seed'] and g['side']==planned['side_name'],'actual seed / side')
        require(g['steps']==303 and g['point_counting_version']==2,'303 course steps / v2')
        sel=a['game_index']==planned['game_index']
        require(sel.any() and sel.sum()==g['rows'],'each game rows exact')
        for key in ('env_seed','side','is_train'): require((a[key][sel]==planned[key]).all(),'row identity '+key)
    require(set(a['game_index'])==set(range(60)),'all planned games in rows')
    require(a['is_train'].sum()==manifest['train_rows'] and (~a['is_train']).sum()==manifest['diagnostic_rows'],'split counts')
    require(set(a['env_seed'][a['is_train']])==set(range(865100,865125)), '25 train whole maps')
    require(set(a['env_seed'][~a['is_train']])==set(range(865125,865130)), '5 diagnostic whole maps')
    canonical=a['world_action'][:,0].copy()
    mirrored=(a['side']==1)&(canonical<5)
    canonical[mirrored]=np.array([0,2,1,4,3])[canonical[mirrored]]
    require(np.array_equal(canonical,a['final_action']),'canonical/world action identities including player1 mirror')
    outside=int((~a['mask'][np.arange(n),a['final_action']]).sum())
    counts=manifest['counts']
    unique_steps=len(np.unique(ids[:,:2],axis=0))
    require(counts['act_steps']==60*303 and counts['reset_steps']==60*3,'normal act / reset counts')
    require(counts['network_steps']==unique_steps,'one captured network call per current step')
    require(counts['network_steps']+counts['no_network_steps']==60*303,'all act calls accounted')
    require(counts['reset_steps']+counts['no_unit_steps']==counts['no_network_steps'],'only documented exclusions')
    require(counts['final_outside_network_mask_rows']==outside,'all outside-mask final actions retained')
    net,_=student(manifest['student'])
    # Preserve actual act batch sizes to independently reproduce hook output.
    boundaries=np.r_[0,np.flatnonzero((a['game_index'][1:]!=a['game_index'][:-1])|(a['env_step'][1:]!=a['env_step'][:-1]))+1,n]
    hook_diff=0.; hook_exact=True
    with torch.no_grad():
        for lo,hi in zip(boundaries[:-1],boundaries[1:]):
            out=net(torch.from_numpy(a['s'][lo:hi])).numpy()
            hook_diff=max(hook_diff,float(np.max(np.abs(out-a['student_q'][lo:hi]))))
            hook_exact &= np.array_equal(out,a['student_q'][lo:hi])
    require(hook_diff<=1e-4,'student hook raw Q reproduction (act batch boundaries)')
    teacher_diff=0.; teacher_exact=True
    if verify_teacher:
        cp=torch.load(manifest['teacher'],map_location='cpu',weights_only=True)
        require(sha(manifest['teacher'])==V14,'actual teacher bytes')
        states=[cp['q'],*cp['ensemble']]
        require(len(states)==36 and cp.get('ensemble_dims',[79]*35)==[79]*35,'actual 36 homogeneous members')
        nets=[]
        for state in states:
            member=QNet(79,6,cp['cfg']['hidden'],True).eval().requires_grad_(False)
            member.load_state_dict(state,strict=True); nets.append(member)
        with torch.no_grad():
            for lo in range(0,n,1024):
                x=torch.from_numpy(a['s'][lo:lo+1024])
                mean=torch.stack([member(x) for member in nets]).mean(0).numpy()
                target=a['teacher_q'][lo:lo+1024]
                teacher_exact &= np.array_equal(mean,target)
                teacher_diff=max(teacher_diff,float(np.max(np.abs(mean-target))))
        require(teacher_exact,'all saved raw teacher Q exact 36-member mean (same 1024 labeling boundaries)')
    return a,dict(path=str(path),rows=n,train_rows=int(a['is_train'].sum()),diagnostic_rows=int((~a['is_train']).sum()),
                  student_sha256=expected_student,student_hook_exact=bool(hook_exact),student_hook_max_abs_error=hook_diff,
                  teacher_all_rows_exact=bool(teacher_exact),teacher_max_abs_error=teacher_diff,
                  games=60,course_steps_each=303,final_outside_mask_rows=outside)

def fit(path, starting, dataset_paths):
    path=Path(path).resolve(); manifest=read(path/'manifest.json')
    require(manifest['status']=='complete' and read(path/'status.json')['status']=='complete','completed fit')
    require(manifest['starting_student_sha256']==sha(starting),'fit start checkpoint identity')
    require([Path(d['path']).resolve() for d in manifest['datasets']]==[Path(p).resolve() for p in dataset_paths],'ordered exact fit datasets')
    arrays=[]
    for p in dataset_paths:
        with np.load(Path(p)/'dataset.npz',allow_pickle=False) as z: arrays.append({k:z[k] for k in SCHEMA})
    a={k:np.concatenate([part[k] for part in arrays]) for k in SCHEMA}
    require(manifest['inputs_before']==manifest['inputs_after'] and manifest['sources_before']==manifest['sources_after'] and manifest['protected_before']==manifest['protected_after'],'fit frozen inputs/sources/protected')
    for kind in ('inputs_before','sources_before','protected_before'): pins(manifest[kind])
    require(manifest['action_epochs_completed']==30 and manifest['value_epochs_completed']==5,'fixed 30 action +5 value epochs')
    require(manifest['seed']==20261104 and manifest['batch_size']==1024 and manifest['learning_rate']==.0001 and manifest['cpu_threads']==1,'fixed fit settings')
    steps=math.ceil(int(a['is_train'].sum())/1024)
    require(manifest['action_updates']==30*steps and manifest['value_updates']==5*steps and manifest['updates']==35*steps,'actual fit update counts')
    require(manifest['training_rows_seen']==int(a['is_train'].sum())*35,'train rows seen, no diagnostic optimizer rows')
    c=centered(a['teacher_q'][a['is_train']],a['mask'][a['is_train']])
    scale=max(.001,float(np.sqrt((c*c).sum()/a['mask'][a['is_train']].sum())))
    require(math.isclose(scale,manifest['scale'],rel_tol=1e-12,abs_tol=1e-12),'independent train-only teacher global RMS')
    output=path/'weights/agent.pth'
    require(sha(output)==manifest['checkpoint_sha256'],'final checkpoint hash')
    net,cp=student(output); start_net,start_cp=student(starting)
    require(cp['distillation_updates']==manifest['cumulative_updates']==start_cp.get('distillation_updates',0)+35*steps,'cumulative supervised updates')
    require(cp['distillation_epochs']==start_cp.get('distillation_epochs',0)+35,'cumulative supervised epochs')
    reported=read(path/'metrics.json'); recomputed={}
    for name,model in (('before',start_net),('after',net)):
        prediction=predict(model,a['s'])
        recomputed[name]={label:metrics(prediction,a,select) for label,select in (('train',a['is_train']),('diagnostic',~a['is_train']))}
        compare(recomputed[name],reported[name],name)
    calibration=manifest['calibration']
    require(calibration['body_adv_unchanged'] and calibration['non_tie_pair_rank_changes']==0,'reported value-only invariant / rank proof')
    for split in ('train','diagnostic'):
        for metric in ('centered_legal_q_mse','recorded_collector_rule_override_rate','recorded_collector_final_outside_mask_rate'):
            require(math.isclose(reported['after_action'][split][metric],reported['after'][split][metric],rel_tol=1e-4,abs_tol=1e-3),'calibration center/rule invariant '+split+'/'+metric)
    return dict(path=str(path),checkpoint_sha256=sha(output),scale=scale,action_updates=30*steps,value_updates=5*steps,
                independently_recomputed_metrics=recomputed,calibration_attestation=calibration,
                calibration_limit='Pre-calibration tensors not retained: frozen body/adv byte equality and pair-flip counts are run attestations corroborated by frozen source, not independently reconstructable without rerunning training.')

def state_digest(value):
    """Independent implementation of the published canonical typed identity format."""
    h=hashlib.sha256()
    def emit(b): h.update(len(b).to_bytes(8,'big'));h.update(b)
    def visit(x):
        if isinstance(x,torch.Tensor):
            t=x.detach().cpu().contiguous();emit(b'tensor');emit(str(t.dtype).encode());visit(list(t.shape));emit(t.reshape(-1).view(torch.uint8).numpy().tobytes())
        elif isinstance(x,np.ndarray): emit(b'ndarray');emit(x.dtype.str.encode());visit(list(x.shape));emit(x.tobytes(order='C'))
        elif isinstance(x,dict):
            emit(b'dict');emit(str(len(x)).encode())
            for k in sorted(x,key=lambda k:(type(k).__name__,repr(k))):visit(k);visit(x[k])
        elif isinstance(x,(list,tuple)):
            emit(type(x).__name__.encode());emit(str(len(x)).encode())
            for child in x:visit(child)
        elif isinstance(x,(str,int,float,bool,type(None))):emit(type(x).__name__.encode());emit(repr(x).encode())
        elif isinstance(x,np.generic):visit(x.item())
        else:raise TypeError(type(x).__name__)
    visit(value);return h.hexdigest()

def tensor_digest(state):
    h=hashlib.sha256()
    for k in sorted(state):
        t=state[k].detach().cpu().contiguous()
        h.update(json.dumps([k,str(t.dtype),list(t.shape)],separators=(',',':')).encode()+b'\n')
        h.update(t.reshape(-1).view(torch.uint8).numpy().tobytes())
    return h.hexdigest()

def finite_tree(x):
    if isinstance(x,(torch.Tensor,np.ndarray)):require(bool(torch.isfinite(x).all()) if isinstance(x,torch.Tensor) else np.isfinite(x).all(),'finite tensor/array tree')
    elif isinstance(x,dict):
        for child in x.values():finite_tree(child)
    elif isinstance(x,(list,tuple)):
        for child in x:finite_tree(child)
    elif isinstance(x,float):require(math.isfinite(x),'finite scalar tree')

def rl_pair(prepared, expected_seed, expected_a2):
    """Read completed arms only. No simulations and no optimizer steps."""
    import csv
    from agents.sherlock.config import AgentConfig
    from scripts.student_reward_train import validate_receipt
    prepared=Path(prepared).resolve();m=read(prepared/'manifest.json')
    require(m['schema_version']==1 and m['run_seed']==expected_seed and expected_seed in (27,28),'prepared independent seed')
    require(m['student_sha256']==expected_a2==sha(m['student']),'exact A2 common input')
    source_net,source_cp=student(m['student']);source_cfg=AgentConfig(**source_cp['cfg']).to_dict()
    require(m['source_config']==source_cfg,'exact A2 effective source config')
    for name,digest in m['pins']['code'].items():require(sha(ROOT/name)==digest,'RL source pin '+name)
    pins(m['pins']['protected'])
    rng=np.random.default_rng(expected_seed+3000);names=['solution92','sol92_sq','default','rush']
    schedule=[dict(phase=phase,game=g,seed=200000+expected_seed*10000+offset+g//2,
                   side=('player_0','player_1')[g%2],opponent=names[rng.choice(4,p=[.6,.2,.1,.1])])
              for phase,count,offset in (('prefill',40,5000),('train',160,3000)) for g in range(count)]
    validations=[dict(after_games=after,opponent=opp,seed=seed,side=side) for after in (0,160)
                 for opp in ('default','solution92') for seed in range(500000,500004) for side in ('player_0','player_1')]
    require(m['validation_plan']==validations,'independent known validation schedule')
    q_sha=tensor_digest(source_cp['q'])
    fresh=state_digest(torch.optim.Adam(source_net.parameters(),lr=.0001).state_dict())
    outputs={};all_rows={};prefill_buffers={}
    for arm in ('control','sap0'):
        destination=prepared/'runs'/arm
        # Existing validator is additional evidence, not the independent checks below.
        receipt=validate_receipt(destination)
        require(receipt['run_seed']==expected_seed and receipt['student_sha256']==expected_a2,'receipt seed/A2')
        entry=m['arms'][arm];cfg=dict(source_cfg,frozen=False,lr=.0001,rules_in_training=True,rules_in_training_all=True)
        if arm=='sap0':cfg['w_sap_hit']=0.
        require(entry['config']==cfg and entry['run_seed']==expected_seed and entry['rollout_plan']==schedule,'independent arm config and actual seeded plan')
        init_path=prepared/'init'/arm/'weights/agent.pth'
        _,init_cp=student(init_path)
        require(init_cp['cfg']==cfg and tensor_digest(init_cp['q'])==q_sha,'identical actual initial Q, only authorized config')
        require(sha(init_path)==entry['weights_sha256'],'init file pin')
        require(not list(init_path.parent.glob('*.buffer.npz')) and 'opt' not in init_cp,'init has fresh optimizer and empty replay contract')
        audit=read(destination/'training_audit.json');initial=audit['initial'];il=initial['learning']
        require(il['optimizer_sha256']==fresh and il['recent_losses']==[] and il['env_steps']==60000 and il['learn_steps']==0,'actual fresh Adam / zero learner counters')
        require(il['replay']['size']==il['replay']['pos']==0 and il['replay']['_mask_dim']==1,'actual initial empty buffer')
        require(initial['q_tensor_sha256']==initial['target_tensor_sha256']==q_sha,'actual initial q/target match A2')
        require(len(initial['initial_identity']['learners'])==1 and initial['initial_identity']['learners'][0]['sides']==['player_0','player_1'],'one shared canonical learner both sides')
        rows=[json.loads(x) for x in (destination/'rollouts.jsonl').read_text().splitlines()]
        vals=[json.loads(x) for x in (destination/'validation_games.jsonl').read_text().splitlines()]
        require(len(rows)==200 and [{k:r[k] for k in ('phase','game','seed','side','opponent')} for r in rows]==schedule,'actual 40+160 seeded rollouts')
        require(len(vals)==32 and [{k:r[k] for k in ('after_games','opponent','seed','side')} for r in vals]==validations,'actual 32 fixed known validations')
        total_transitions=0;reward_totals={k:0. for k in ('transitions','sap_transitions','estimated_positive_hits','estimated_misses','removed_signed','removed_absolute','actual_reward')}
        for i,r in enumerate(rows):
            learning=r['identity']['learning'];action=r['final_action_audit'];reward=r['reward_audit'];finite_tree(reward)
            require(r['steps']==303 and r['point_counting_version']==2 and action['act_calls']==action['update_calls']==303,'full actual course rollout and action/update boundary')
            require(learning['env_steps']==60000+(i+1)*303 and learning['learn_steps']==max(0,i+1-40)*150,'independent actual chronology')
            require(learning['config']==cfg and learning['learn_enabled']==(i>=40) and not learning['autosave_on_terminate'],'actual rollout config/mode')
            require(action['checked_replay_transitions']==reward['transitions'] and reward['calls']==300,'each actual unit transition reward audited')
            require(reward['sap_transitions']==reward['estimated_positive_hits']+reward['estimated_misses'],'hits/misses account for every SAP')
            weight=source_cfg['w_sap_hit']
            require(math.isclose(reward['removed_absolute']-reward['removed_signed'],2*weight*reward['estimated_misses'],rel_tol=1e-8,abs_tol=1e-7),'independent signed miss counterfactual identity')
            require(reward['removed_absolute']+1e-7>=weight*reward['sap_transitions'],'absolute removed SAP contributions')
            require(len(action['transcript_sha256'])==len(r['policy_transcript']['action_state_sha256'])==64,'retained final-action/replay and all-coordinate/features digests')
            if i<40:
                require(r['identity']['q_tensor_sha256']==r['identity']['target_tensor_sha256']==q_sha and learning['optimizer_sha256']==fresh,'prefill never learns')
            total_transitions+=action['checked_replay_transitions']
            for k in reward_totals:reward_totals[k]+=reward[k]
        for row in vals:require(row['steps']==303 and row['point_counting_version']==2 and row['config']==cfg and row['epsilon']==0 and row['learn_enabled'] is False and row['eval_rng_seed']==20261104,'validation modes / fixed evaluation RNG')
        require(len(audit['validations'])==2 and all(p['before']==p['after'] for p in audit['validations']),'validation preserves learner/replay/RNG identities')
        cp_path=destination/'weights/agent.pth';cp=torch.load(cp_path,map_location='cpu',weights_only=True);finite_tree(cp)
        require(cp['cfg']==cfg and cp['feature_dim']==79 and cp['n_actions']==6 and not cp['ensemble'] and not cp['ensemble_dims'],'final single network/config')
        source_net.load_state_dict(cp['q'],strict=True)
        require(cp['env_steps']==120600 and cp['learn_steps']==24000,'final actual learning budgets')
        require(tensor_digest(cp['q'])==audit['end']['q_tensor_sha256']!=q_sha and tensor_digest(cp['target_q'])==audit['end']['target_tensor_sha256'],'final changed q, target and end identity')
        require(state_digest(cp['opt'])==audit['end']['learning']['optimizer_sha256'],'final optimizer identity')
        require(len(cp['opt']['state'])==len(cp['q']) and all(float(v['step'])==24000 and set(v)=={'step','exp_avg','exp_avg_sq'} for v in cp['opt']['state'].values()),'all actual Adam moments updated 24000 times')
        require(sha(cp_path)==receipt['final_checkpoint_sha256']==audit['end']['saved_weights_sha256'],'final actual file hash')
        with (destination/'train.csv').open() as handle:csv_rows=list(csv.DictReader(handle))
        require(len(csv_rows)==160,'actual training CSV budget')
        for i,r in enumerate(csv_rows):
            require(int(r['game'])==i and int(r['seed'])==schedule[40+i]['seed'] and r['side']==schedule[40+i]['side'] and r['opponent']==schedule[40+i]['opponent'],'actual training CSV chronology')
            require(int(r['learn_steps'])==150*(i+1) and int(r['env_steps'])==72120+303*(i+1) and math.isfinite(float(r['mean_loss'])),'actual finite CSV updates')
        buffer_path=destination/'weights/agent.buffer.npz'
        with np.load(buffer_path,allow_pickle=False) as z:
            require(set(z.files)=={'s','ns','a','r','done','mask'},'actual saved replay schema')
            replay={k:z[k] for k in z.files}
        finite_tree(replay);n=len(replay['a']);capacity=cfg['buffer_capacity']
        require(n==min(total_transitions,capacity)==audit['end']['learning']['replay']['size'],'actual replay occupancy from all raw transition counters')
        require(replay['s'].shape==replay['ns'].shape==(n,79) and replay['mask'].shape==(n,6),'actual replay feature/mask shape')
        require(((replay['a']>=0)&(replay['a']<6)).all() and np.isin(replay['done'],[0,1]).all(),'actual stored final action/done range')
        # Oldest-first replay export retains the complete prefill when capacity allows.
        if total_transitions<=capacity:
            prefill_count=sum(r['final_action_audit']['checked_replay_transitions'] for r in rows[:40])
            prefill_buffers[arm]={k:v[:prefill_count].copy() for k,v in replay.items()}
        outputs[arm]=dict(seed=expected_seed,checkpoint_sha256=sha(cp_path),actual_prefill_games=40,actual_train_games=160,actual_validation_games=32,
                          updates=24000,env_steps=120600,replay_rows=n,total_transitions=total_transitions,reward_totals=reward_totals,
                          production_receipt_validator='passed',initial_fresh_adam_sha256=fresh)
        all_rows[arm]=rows
    for i,(c,s) in enumerate(zip(all_rows['control'][:40],all_rows['sap0'][:40])):
        require(c['final_action_audit']==s['final_action_audit'] and c['policy_transcript']==s['policy_transcript'],'paired prefill identical actual final actions/replay action transcript and full features/SAP coordinates')
        require(math.isclose(c['reward_audit']['actual_reward']-s['reward_audit']['actual_reward'],c['reward_audit']['removed_signed'],rel_tol=1e-8,abs_tol=1e-5),'paired prefill reward difference is exactly signed SAP removal')
    buffer_comparison='prefill overwritten in bounded final replay; hashes prove original equality'
    if set(prefill_buffers)=={'control','sap0'}:
        for key in ('s','ns','a','done','mask'):require(np.array_equal(prefill_buffers['control'][key],prefill_buffers['sap0'][key]),'actual retained paired prefill replay '+key)
        require(not np.array_equal(prefill_buffers['control']['r'],prefill_buffers['sap0']['r']),'actual retained prefill rewards differ')
        buffer_comparison='all retained prefill states/next states/final actions/done/masks exact; rewards differ'
    require({k for k in m['arms']['control']['config'] if m['arms']['control']['config'][k]!=m['arms']['sap0']['config'][k]}=={'w_sap_hit'},'only within-pair config difference is SAP weight')
    return dict(prepared=str(prepared),run_seed=expected_seed,arms=outputs,paired_prefill=buffer_comparison,
                evidence_limit='Actual action/reward boundaries were checked during training and retained as aggregate counts and digests. Per-transition original contexts are not saved, so no independent rerun of each reward formula or reconstruction of full action transcripts is claimed.')

def self_test():
    m=np.array([[True,True,False,False,False,False],[True,False,False,False,False,False]])
    t=np.array([[1,3,99,99,99,99],[5,9,9,9,9,9]],np.float32)
    p=t.copy();p[0,:2]=[4,2]
    a=dict(teacher_q=t,mask=m,student_q=t,final_action=np.array([1,0]))
    x=metrics(p,a,np.array([True,True]));require(x['masked_argmax_agreement']==.5,'synthetic masked argmax')
    require(x['legal_regret']==1 and x['centered_legal_q_mse']==2,'synthetic regret/centered MSE')
    require(np.array_equal(centered(t,m)[1],np.zeros(6)),'one legal action centers to zero')
    print(json.dumps({'self_test':'passed'}))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset',type=Path,action='append',default=[])
    parser.add_argument('--collector-student-sha',action='append',default=[])
    parser.add_argument('--fit',type=Path);parser.add_argument('--starting',type=Path)
    parser.add_argument('--fit-only',action='store_true')
    parser.add_argument('--rl-pair',type=Path,action='append',default=[])
    parser.add_argument('--a2-sha')
    parser.add_argument('--output',type=Path);parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args();torch.set_num_threads(1)
    if args.self_test: return self_test()
    require(args.output is not None and args.output.name.startswith('learning_audit'),'owned output only')
    require(len(args.dataset)==len(args.collector_student_sha),'explicit expected identity for every round')
    started=time.monotonic();report=dict(status='running',datasets=[],auditor_sha256=sha(__file__))
    try:
        if not args.fit_only:
            for path,digest in zip(args.dataset,args.collector_student_sha):
                _,result=dataset(path,digest);report['datasets'].append(result)
        if args.fit: report['fit']=fit(args.fit,args.starting,args.dataset)
        if args.rl_pair:
            report['rl_pairs']=[rl_pair(path,int(path.name[-2:]),args.a2_sha) for path in args.rl_pair]
        report['status']='passed'
    except Exception as e:
        report['status']='failed';report['error']=f'{type(e).__name__}: {e}'
        raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        print(json.dumps({'status':report['status'],'output':str(args.output),'wall_seconds':report['wall_seconds']}))

if __name__=='__main__': main()
