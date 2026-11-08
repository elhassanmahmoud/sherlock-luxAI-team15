"""Fixed submitted-successor pilot: Task3 only; no evaluation or promotion path."""
from __future__ import annotations

import argparse
from collections import Counter, deque
import copy
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import sys
import time

import numpy as np
import torch

from agents.sherlock.config import AgentConfig
from scripts import common, experiment
from scripts.early_curriculum_study import require, source_identity, hashes
from scripts.ensemble_diversity_train import _source
from scripts.night_train_pilot import file_sha256, tensor_sha256
from scripts.sampled_target_agent import (SampledTargetAgent, SuccessorReplay, BASE_ARRAYS, EXTRA_DTYPES,
    bootstrap_targets, save_pilot_bundle, load_pilot_bundle)
from scripts.student_reward_train import _output as safe_output, _protected_hashes
from scripts.variants import seed_everything

ROOT=Path(__file__).resolve().parents[1]
PROFILE='sampled_target_20261108'
SOURCE_SHA='98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
ADMISSION_SHA256=None  # Only an explicitly supplied, independently approved Root hash admits work.
SIDES=('player_0','player_1'); MODES=('double_dqn','sampled_successor')
ARMS={f'{role}{seed}':(seed,mode) for seed in (45,46) for role,mode in zip(('control','sampled'),MODES)}
COHORTS={'prefill45':list(range(9915000,9915020)), 'train45':list(range(9910000,9910080)),
    'prefill46':list(range(9925000,9925020)), 'train46':list(range(9920000,9920080)),
    'panel':list(range(9930000,9930020)), 'direct':list(range(9930100,9930120))}
MIX={'solution92':.6,'sol92_sq':.2,'default':.1,'rush':.1}
PLANS=[ROOT/f'docs/superpowers/{kind}/2026-11-08-sampled-target.md' for kind in ('specs','plans')]
PLAN_KEYS=('phase','game','seed','side','opponent')
SETTINGS=dict(prefill=40,train=160,updates_per_game=150,env_start=60000,env_end=120600,updates=24000)

def read(path):return json.loads(Path(path).read_text())
def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
def write(path,value,*,exclusive=False):
    path=Path(path);payload=json.dumps(value,indent=2,allow_nan=False)+'\n'
    if exclusive:
        temporary=path.with_name(path.name+f'.publish-{os.getpid()}')
        with temporary.open('x') as stream:
            stream.write(payload);stream.flush();os.fsync(stream.fileno())
        try:os.link(temporary,path)  # atomic visibility; an existing receipt is never replaced
        finally:temporary.unlink()
    else:
        temporary=path.with_name(path.name+'.tmp')
        temporary.write_text(payload);temporary.replace(path)
def hex64(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None
def pins():return dict(source=source_identity(ROOT,sys.executable,PLANS),protected=_protected_hashes())
def verify(mapping):require(hashes(mapping)==mapping,'A frozen input changed')

def rollout_plan(arm):
    require(arm in ARMS,'Unknown fixed arm')
    seed,_=ARMS[arm];rng=np.random.default_rng(seed);names=list(MIX)
    return [dict(phase=phase,game=game,seed=card,side=side,
                 opponent=names[rng.choice(len(names),p=list(MIX.values()))])
        for phase in ('prefill','train') for game,(card,side) in enumerate(
            (card,side) for card in COHORTS[f'{phase}{seed}'] for side in SIDES)]

def technical_plan():
    return [dict(job=f'technical_{role}_p{side[-1]}',arm=f'{role}45',bootstrap_mode=mode,
        run_seed=45,seed=4242,side=side,opponent='default')
        for side in SIDES for role,mode in zip(('control','sampled'),MODES)]

def training_config(cfg):
    expected=dict(gamma=.99,batch_size=256,buffer_capacity=300000,canonical=True,double_dqn=True,
        use_sap=True,eps_end=.05,eps_decay_steps=60000,learn_start=5000,train_every=2,
        target_update_every=500,guided_prob=.7)
    require(all(cfg.get(k)==v for k,v in expected.items()),'Source violates fixed learner recipe')
    return dict(cfg,frozen=False,lr=5e-5,rules_in_training=True,rules_in_training_all=True,
        rescue_in_training=True,fog_unknown_reward_neutral=False,art_splash_in_training=False)

def validate_admission(path,expected_hash=ADMISSION_SHA256,stage='study'):
    require(stage in ('technical','study') and hex64(expected_hash),'Explicit Root admission SHA required')
    path=Path(path).resolve(strict=True);require(file_sha256(path)==expected_hash,'Root admission changed')
    admission=read(path);bound={str(path):expected_hash}
    require(all(admission.get(k)==v for k,v in dict(schema_version=1,status='PASS',profile=PROFILE,stage=stage).items()),'Wrong Root admission')
    require(admission.get('pins')==pins(),'Root-approved source/protected identity differs')
    def artifact(item,relative=False):
        require(isinstance(item,dict) and set(item)=={'path','sha256'} and hex64(item['sha256']),'Missing bound admission artifact')
        value=Path(item['path']);require((not value.is_absolute()) if relative else value.is_absolute(),'Artifact path convention differs')
        result=(ROOT/value if relative else value).resolve(strict=True)
        require(not relative or result.is_relative_to(ROOT.resolve()),'Seed artifact escapes repository')
        require(file_sha256(result)==item['sha256'],'Admission artifact changed')
        bound[str(result)]=item['sha256'];return result
    artifact(admission.get('review'))
    accepted=read(artifact(admission.get('seed_acceptance')))
    require(all(accepted.get(k)==v for k,v in dict(schema_version=1,status='PASS',profile=PROFILE,cohorts=COHORTS).items()),'Wrong seed admission/cohorts')
    audit=read(artifact(accepted.get('audit'),True))
    require(audit.get('status')=='PASS' and audit.get('no_observed_conflicts') is True
        and isinstance(audit.get('limitations'),list) and bool(audit['limitations'])
        and isinstance(audit.get('files'),dict) and bool(audit['files']),'Seed audit missing or conflict/limits/inventory absent')
    artifact(audit.get('raw_audit'),True)
    for relative,digest in audit.get('files',{}).items():artifact(dict(path=relative,sha256=digest),True)
    if stage=='technical':require(admission.get('technical_acceptance') is None,'Technical admission cannot reuse prior runs')
    else:
        tech=read(artifact(admission.get('technical_acceptance')))
        require(all(tech.get(k)==v for k,v in dict(schema_version=1,status='PASS',profile=PROFILE,games=4).items())
            and tech.get('pins')==admission['pins'],'Four-game technical acceptance missing')
        require(set(tech.get('receipts',{}))=={j['job'] for j in technical_plan()},'Incomplete technical receipts')
        checked={}
        for job,item in tech['receipts'].items():
            receipt_path=artifact(item);checked[job]=validate_technical_receipt(receipt_path,job=job)
            for name,digest in checked[job]['artifacts'].items():
                p=receipt_path.parent/name;require(file_sha256(p)==digest,'Technical evidence changed');bound[str(p)]=digest
        for side in SIDES:
            compare_technical_receipts(checked[f'technical_control_p{side[-1]}'],checked[f'technical_sampled_p{side[-1]}'],side)
    verify(bound);return admission,bound

def prepare(source,out,admission,admission_sha256=None,*,stage='study'):
    accepted,bound=validate_admission(admission,admission_sha256,stage)
    source=Path(source).resolve(strict=True);out=safe_output(out)
    require(not out.exists(),'Prepared directory already exists; no restart')
    require(file_sha256(source)==SOURCE_SHA,'Expected exact V14 input')
    _,states,cfg=_source(source);config=training_config(cfg)
    manifest=dict(schema_version=1,profile=PROFILE,stage=stage,source=str(source),source_sha256=SOURCE_SHA,
        source_config=cfg,settings=SETTINGS,cohorts=COHORTS,pins=accepted['pins'],
        admission=str(Path(admission).resolve()),admission_sha256=admission_sha256,
        input_sha256={**bound,str(source):SOURCE_SHA},arms={},technical_plan=technical_plan())
    for arm,(seed,mode) in ARMS.items():
        directory=out/arm;directory.mkdir(parents=True,exist_ok=False)
        q=copy.deepcopy(states[18]);checkpoint=dict(q=q,target_q=copy.deepcopy(q),cfg=config,
            feature_dim=79,n_actions=6,ensemble=[],ensemble_dims=[],env_steps=60000,learn_steps=0)
        torch.save(checkpoint,directory/'initial.pth')
        manifest['arms'][arm]=dict(run_seed=seed,bootstrap_mode=mode,component_index=18,config=config,
            tensor_sha256=tensor_sha256(q),weights_sha256=file_sha256(directory/'initial.pth'),rollout_plan=rollout_plan(arm))
    require(pins()==manifest['pins'],'Sources changed while preparing')
    write(out/'manifest.json',manifest,exclusive=True);return manifest

def check_prepared(prepared,arm=None):
    prepared=Path(prepared).resolve(strict=True);manifest=read(prepared/'manifest.json')
    stage=manifest.get('stage');admission,bound=validate_admission(manifest['admission'],manifest['admission_sha256'],stage)
    require(manifest.get('schema_version')==1 and manifest.get('profile')==PROFILE and manifest['settings']==SETTINGS
        and manifest['cohorts']==COHORTS and manifest['technical_plan']==technical_plan() and set(manifest['arms'])==set(ARMS)
        and manifest['pins']==admission['pins'] and manifest['source_sha256']==SOURCE_SHA
        and manifest['input_sha256']=={**bound,manifest['source']:SOURCE_SHA},'Prepared study differs')
    verify(manifest['input_sha256'])
    for name,(seed,mode) in ARMS.items():
        entry=manifest['arms'][name];require(entry['run_seed']==seed and entry['bootstrap_mode']==mode
            and entry['component_index']==18 and entry['config']==training_config(manifest['source_config'])
            and entry['rollout_plan']==rollout_plan(name) and hex64(entry['tensor_sha256']), 'Prepared arm differs')
        require(file_sha256(prepared/name/'initial.pth')==entry['weights_sha256'],'Initial weights changed')
    if arm is None:return manifest,None,None
    jobs={j['job']:j for j in technical_plan()}
    if arm in jobs:
        require(stage=='technical','Technical job requires separate technical preparation');arm=jobs[arm]['arm']
    else:require(arm in ARMS and stage=='study','Study arm requires completed technical admission')
    return manifest,manifest['arms'][arm],prepared/arm/'initial.pth'

class PilotLearners(experiment.Learners):
    def __init__(self,entry,initial,run_dir):
        self.variant=PROFILE;self.split=False
        shared=str(Path(run_dir)/'final'/'agent.pth');self.paths={side:shared for side in SIDES}
        agent=SampledTargetAgent('player_0',agent_path=str(initial),cfg=AgentConfig.from_dict(entry['config']),
            train=True,seed=entry['run_seed']*100,bootstrap_mode=entry['bootstrap_mode'])
        self.agents={side:agent for side in SIDES}

def semantic_rows(rows):return experiment.state_sha256([{k:v for k,v in row.items() if k!='secs'} for row in rows])
def replay_hash(buffer):
    digest=hashlib.sha256();digest.update(encoded(dict(size=buffer.size,capacity=buffer.capacity,obs_dim=buffer.obs_dim)))
    for name in (*BASE_ARRAYS,*EXTRA_DTYPES):
        values=getattr(buffer,name);digest.update(encoded([name,values.dtype.str,[buffer.size,*values.shape[1:]]]))
        for first in range(0,buffer.size,256):
            index=np.arange(first,min(first+256,buffer.size))
            if buffer.size==buffer.capacity:index=(index+buffer.pos)%buffer.capacity
            digest.update(np.ascontiguousarray(values[index]).tobytes())
    return digest.hexdigest()

def learning_identity(agent):
    return dict(q=tensor_sha256(agent.q.state_dict()),target=tensor_sha256(agent.target_q.state_dict()),
        optimizer=experiment.state_sha256(agent.opt.state_dict()),agent_rng=experiment.state_sha256(agent.rng.bit_generator.state),
        global_rng=experiment.state_sha256(experiment._global_rng_state()),env_steps=agent.env_steps,
        learn_steps=agent.learn_steps,replay_size=len(agent.buffer))

def prove_initial(agent,entry):
    agent.assert_boundary();identity=learning_identity(agent)
    require(identity['q']==identity['target']==entry['tensor_sha256'] and identity['env_steps']==60000
        and identity['learn_steps']==identity['replay_size']==0 and not agent.opt.state
        and not agent.extra_q and not agent.recent_losses and agent.cfg.to_dict()==entry['config']
        and agent.autosave_on_terminate is False and agent.training and abs(agent.epsilon-.05)<1e-12,
        'Not a fresh exact component18 learner')
    require(all(group['lr']==5e-5 for group in agent.opt.param_groups),'Wrong initial learning rate')
    return identity

class EventValidator:
    """Streaming, bounded frame/transition evidence; only confirmed commands close a game."""
    def __init__(self,initial_ordinal=0,data=None,total_committed=None):
        self.ordinal=initial_ordinal;self.counts=Counter();self.pending={};self.order=deque()
        self.frame=None;self.episode=None;self.last_step=None;self.captured_uids=[];self.episode_frames=0
        self.data=data;self.total_committed=total_committed;self.checked_replay=0
    def add(self,event):
        kind=event['event']
        if kind=='episode':
            if self.episode is not None:self.boundary()
            require(self.episode is None or event['episode_id']>self.episode,'Repeated episode')
            self.episode=event['episode_id'];self.last_step=None;self.episode_frames=0
            self.counts['episodes']+=1;return
        require(self.episode is not None,'Event without episode')
        if kind=='frame':
            key=tuple(event['key']);require(len(key)==3 and all(type(x) is int for x in key)
                and 0<=key[1]<=2 and key[2]>=0 and type(event['env_steps']) is int and event['env_steps']>=0
                and self.frame is None and key[0]==self.episode
                and (self.last_step is None and key[2]==0 or self.last_step is not None and key[2]==self.last_step+1),'Frame sequence differs')
            units=event['units'];require(len(units)<=16 and len({u['uid'] for u in units})==len(units)
                and all(type(u['uid']) is int and 0<=u['uid']<16 and type(u['action']) is int and 0<=u['action']<6 for u in units),'Invalid/duplicate frame UID/action')
            native=np.asarray(event['native']);require(native.shape==(16,3) and native.dtype.kind in 'iu','Native frame shape/dtype differs')
            self.frame=dict(event,key=key,units={u['uid']:u for u in units},native_hash=experiment.state_sha256(native))
            self.captured_uids=[];self.counts['frames']+=1;self.episode_frames+=1;return
        require(self.frame is not None,'Event outside current frame')
        if kind=='capture':
            identity=tuple(event['identity']);uid=identity[2]
            require(identity[:2]==(self.episode,self.frame['key'][2]) and identity not in self.pending
                and uid in self.frame['units'] and not any(k[:2]!=identity[:2] for k in self.pending),'Capture sequence/identity differs')
            unit=self.frame['units'][uid]
            require(event['action']==unit['action'] and event['s_sha256']==unit['features_sha256']
                and event['match_idx']==self.frame['key'][1] and event['done'] in (0.,1.)
                and math.isfinite(event['reward']),'Capture differs from acted source')
            self.pending[identity]=event;self.order.append(identity);self.captured_uids.append(uid);self.counts['captured']+=1;return
        if kind=='commit':
            identity=tuple(event['identity']);require(self.order and identity==self.order[0],'Missing/duplicate/out-of-order commit')
            row=self.pending[identity];require(event['ordinal']==self.ordinal+1 and event['action']==row['action']
                and event['done']==row['done'],'Commit metadata differs')
            if row['done']:
                require(event['successor_key'] is None and event['next_action']==event['next_action_env_steps']==-1,'Terminal label differs')
            else:
                key=tuple(event['successor_key']);unit=self.frame['units'].get(identity[2])
                require(key==self.frame['key']==(identity[0],row['match_idx'],identity[1]+1) and unit is not None
                    and unit['features_sha256']==row['ns_sha256'] and unit['mask_sha256']==row['mask_sha256']
                    and event['next_action']==unit['action'] and event['next_action_env_steps']==self.frame['env_steps'],'Unbound successor label')
            if self.data is not None:
                index=event['ordinal']-(self.total_committed-len(self.data['a']))-1
                if index>=0:
                    require(index<len(self.data['a']),'Commit exceeds saved replay')
                    d=self.data
                    require((int(d['episode_id'][index]),int(d['source_step'][index]),int(d['uid'][index]))==identity
                        and int(d['match_idx'][index])==row['match_idx'] and int(d['a'][index])==row['action']
                        and float(d['r'][index])==float(np.float32(row['reward'])) and float(d['done'][index])==row['done']
                        and int(d['next_action'][index])==event['next_action']
                        and int(d['next_action_env_steps'][index])==event['next_action_env_steps']
                        and all(experiment.state_sha256(d[k][index])==row[h] for k,h in
                            (('s','s_sha256'),('ns','ns_sha256'),('mask','mask_sha256'))),'Saved replay differs from confirmed event')
                    self.checked_replay+=1
            self.order.popleft();del self.pending[identity];self.ordinal+=1;self.counts['committed']+=1
            self.counts['terminal' if row['done'] else 'nonterminal']+=1;return
        require(kind=='confirmed' and tuple(event['key'])==self.frame['key']
            and event['native_sha256']==self.frame['native_hash']
            and self.captured_uids==list(self.frame['units']),'Unconfirmed/partial frame')
        self.last_step=self.frame['key'][2];self.frame=None;self.counts['confirmed']+=1
    def boundary(self,expected_steps=303):
        require(self.frame is None and not self.pending and not self.order and self.episode_frames==expected_steps,
            'Incomplete final command/capture/commit evidence')

class EventStream:
    def __init__(self,path,agent):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=False)
        self.raw=self.path.open('xb');self.gz=gzip.GzipFile(fileobj=self.raw,mode='wb',mtime=0)
        self.agent=agent;self.validator=EventValidator(agent.buffer.counts['committed'])
        self.digest=hashlib.sha256();self.game_digest=None;self.before=None
    def __call__(self,event):
        event=copy.deepcopy(event)
        if event['event']=='capture':
            row=self.agent.buffer._capture['rows'][-1]
            require(event['identity']==[row['episode_id'],row['source_step'],row['uid']],'Capture callback differs')
            event['reward']=row['r']
        if event['event']=='episode':self.game_digest=hashlib.sha256();self.before=self.validator.counts.copy()
        self.validator.add(event);data=encoded(event);self.gz.write(data);self.digest.update(data);self.game_digest.update(data)
    def game_summary(self):
        self.validator.boundary();self.gz.flush()
        return dict(counts=dict(self.validator.counts-self.before),semantic_sha256=self.game_digest.hexdigest())
    def close(self):
        self.gz.close();self.raw.close()
        return dict(semantic_sha256=self.digest.hexdigest(),counts=dict(self.validator.counts),file_sha256=file_sha256(self.path))

def validate_stream(path,plan,initial_ordinal=0,*,episode_start=0,data=None,total_committed=None):
    tracker=EventValidator(initial_ordinal,data,total_committed);digest=hashlib.sha256();episodes=0;games=[];game_digest=None;before=None
    with gzip.open(path,'rt') as stream:
        for line in stream:
            event=json.loads(line)
            if event['event']=='episode':
                if episodes:games.append(dict(counts=dict(tracker.counts-before),semantic_sha256=game_digest.hexdigest()))
                require(episodes<len(plan) and event['episode_id']==episode_start+episodes
                    and {k:event[k] for k in PLAN_KEYS}==plan[episodes],'Event episode differs from bound schedule')
                before=tracker.counts.copy();game_digest=hashlib.sha256()
                episodes+=1
            tracker.add(event);raw=encoded(event);digest.update(raw);game_digest.update(raw)
    tracker.boundary();require(episodes==len(plan),'Incomplete provenance episode count')
    games.append(dict(counts=dict(tracker.counts-before),semantic_sha256=game_digest.hexdigest()))
    return dict(semantic_sha256=digest.hexdigest(),counts=dict(tracker.counts),file_sha256=file_sha256(path)),games,tracker.checked_replay

def diagnose_targets(agent):
    before=(learning_identity(agent),replay_hash(agent.buffer));total=Counter()
    with torch.no_grad():
        for first in range(0,len(agent.buffer),256):
            index=np.arange(first,min(first+256,len(agent.buffer)))
            if len(agent.buffer)==agent.buffer.capacity:index=(index+agent.buffer.pos)%agent.buffer.capacity
            b=agent.buffer;ns=torch.as_tensor(b.ns[index],device=agent.device)
            done=torch.as_tensor(b.done[index,None],device=agent.device);live=done[:,0]==0
            c,s,best=bootstrap_targets(agent.q(ns),agent.target_q(ns),torch.as_tensor(b.r[index,None],device=agent.device),
                done,torch.as_tensor(b.mask[index],device=agent.device),torch.as_tensor(b.next_action[index],device=agent.device),agent.cfg.gamma)
            labels=torch.as_tensor(b.next_action[index],device=agent.device);masks=torch.as_tensor(b.mask[index],device=agent.device)
            delta=s-c;total.update(rows=len(index),nonterminal=int(live.sum()),different_index=int((best[:,0][live]!=labels[live]).sum()),
                different_target=int((delta[live]!=0).sum()),outside_mask=int((~masks[live].gather(1,labels[live].long().unsqueeze(1))).sum()),
                positive=int((delta[live]>0).sum()),negative=int((delta[live]<0).sum()),delta_sum=float(delta.double().sum()))
    require(before==(learning_identity(agent),replay_hash(agent.buffer)),'Read-only target diagnosis changed learner/replay/RNG')
    return dict(total,readonly=True)

def compare_prefill_proofs(control,sampled,seed):
    require(seed in (45,46),'Unknown paired start')
    for proof,role in ((control,'control'),(sampled,'sampled')):
        require(all(proof.get(k)==v for k,v in dict(schema_version=1,status='prefill_ready',profile=PROFILE,
            arm=f'{role}{seed}',run_seed=seed,bootstrap_mode=ARMS[f'{role}{seed}'][1],games=40).items()),'Wrong paired proof identity')
        shared=proof['shared'];initial,end=shared['initial'],shared['end']
        require(initial['env_steps']==60000 and initial['learn_steps']==initial['replay_size']==0
            and end['env_steps']==72120 and end['learn_steps']==0 and end['replay_size']>=5000
            and all(initial[k]==end[k] for k in ('q','target','optimizer'))
            and shared['captured']==shared['committed']==end['replay_size']
            and shared['terminal']+shared['nonterminal']==shared['committed']
            and shared['frames']==shared['confirmed']==40*303,'Prefill changed learning or lacks complete evidence')
        diagnosis=shared['diagnosis'];require(diagnosis['readonly'] is True and diagnosis['rows']==end['replay_size']
            and diagnosis['nonterminal']==shared['nonterminal'] and diagnosis['different_index']>0
            and diagnosis['different_target']>0,'No demonstrated target intervention; stop without replacement')
    require(control['shared']==sampled['shared'],'Paired prefill semantic content/RNG differs')
    return dict(status='matched',run_seed=seed,eligible=False,shared=control['shared'])

class ObservedEnv:
    """Passive per-instance proxy; common.play_game owns the unchanged real loop."""
    def __init__(self,env):self.env=env;self.digest=None;self.steps=0;self.stream=None;self.episode_id=None
    def begin_phase(self,path):
        self.raw=Path(path).open('xb');self.stream=gzip.GzipFile(fileobj=self.raw,mode='wb',mtime=0)
    def end_phase(self):
        if self.stream is not None:self.stream.close();self.raw.close();self.stream=None
    def __getattr__(self,name):return getattr(self.env,name)
    def _record(self,value):
        from scripts.holder_rollout import exact_digest
        digest=exact_digest(value);self.digest.update(digest.encode())
        record=dict(episode_id=self.episode_id,kind=value[0],step=self.steps,sha256=digest)
        if value[0]=='submitted':record['actions']={k:np.asarray(v).tolist() for k,v in value[1].items()}
        self.stream.write(encoded(record))
    def reset(self,**kwargs):
        self.digest=hashlib.sha256();self.steps=0;result=self.env.reset(**kwargs)
        self._record(('reset',kwargs,result,self.env.state));return result
    def step(self,actions):
        self._record(('submitted',actions));result=self.env.step(actions);self.steps+=1
        self._record(('result',result,self.env.state));return result

def load_replay_data(path):
    # read_validated only needs capacity. Do not allocate a second 300k ring/model.
    schema=object.__new__(SuccessorReplay);schema.capacity=300000
    return schema.read_validated(path)

def replay_data_hash(data):
    size=len(data['a']);digest=hashlib.sha256()
    digest.update(encoded(dict(size=size,capacity=300000,obs_dim=79)))
    for name in (*BASE_ARRAYS,*EXTRA_DTYPES):
        values=data[name];digest.update(encoded([name,values.dtype.str,list(values.shape)]))
        for first in range(0,size,256):digest.update(np.ascontiguousarray(values[first:first+256]).tobytes())
    return digest.hexdigest()

def validate_rollout(row,index,entry,*,technical=False):
    expected=(dict(phase='prefill',game=0,seed=4242,side=row['side'],opponent='default')
        if technical else entry['rollout_plan'][index])
    training=expected['phase']=='train';counts=row['provenance']['counts']
    require({k:row[k] for k in PLAN_KEYS}==expected and row['steps']==303 and row['point_counting_version']==2
        and row['env_steps']==60000+(index+1)*303 and row['learn_steps']==max(0,index+1-40)*150
        and row['updates']==(150 if training else 0) and row['config_sha256']==experiment.state_sha256(entry['config'])
        and counts.get('episodes')==1 and counts.get('frames')==counts.get('confirmed')==303
        and counts.get('captured',0)==counts.get('committed',0)==counts.get('terminal',0)+counts.get('nonterminal',0)
        and hex64(row['provenance']['semantic_sha256']) and hex64(row['trajectory_sha256'])
        and row['result'] in (0.,.5,1.),'Rollout differs from fixed game/update/provenance contract')
    if training:require(math.isfinite(row['mean_loss']),'Nonfinite mean training loss')

def play(env,agent,entry,plan,index,events,check,*,technical=False):
    check();training=plan['phase']=='train'
    require(agent.training and agent.learn_enabled is training and agent.cfg.to_dict()==entry['config']
        and agent.bootstrap_mode==entry['bootstrap_mode'] and not agent.autosave_on_terminate,'Learner mode/config drift')
    agent.bind_episode(dict(episode_id=index,**plan))
    env.episode_id=index
    opponent=common.make_opponent(plan['opponent'],'player_1' if plan['side']=='player_0' else 'player_0')
    before=agent.learn_steps
    row=common.play_game(env,agent,opponent,plan['seed'],plan['side'],train=True)
    agent.assert_boundary();require(env.steps==303,'Unexpected actual env.step count')
    row.update(plan,env_steps=agent.env_steps,learn_steps=agent.learn_steps,updates=agent.learn_steps-before,
        config_sha256=experiment.state_sha256(entry['config']),provenance=events.game_summary(),trajectory_sha256=env.digest.hexdigest())
    if training:row['mean_loss']=float(agent.pop_mean_loss())
    validate_rollout(row,index,entry,technical=technical);check();return row

def shared_evidence(entry,initial,end,rows,replay_digest,event_summary,diagnosis=None):
    counts=event_summary['counts']
    shared=dict(config_sha256=experiment.state_sha256(entry['config']),initial=initial,end=end,
        schedule_sha256=experiment.state_sha256([{k:r[k] for k in PLAN_KEYS} for r in rows]),
        replay_sha256=replay_digest,events_semantic_sha256=event_summary['semantic_sha256'],
        trajectory_sha256=experiment.state_sha256([r['trajectory_sha256'] for r in rows]),rows_semantic_sha256=semantic_rows(rows),
        **{k:counts.get(k,0) for k in ('captured','committed','terminal','nonterminal','frames','confirmed')})
    if diagnosis is not None:shared['diagnosis']=diagnosis
    return shared

def phase_bundle(destination,agent,entry,initial,rows,event_summary,*,arm,prepared,technical=False):
    directory=destination/'prefill';agent.assert_boundary();agent.save_buffer(directory/'replay.npz')
    end=learning_identity(agent);replay_digest=replay_hash(agent.buffer)
    diagnosis=None if technical else diagnose_targets(agent)
    bundle=dict(schema_version=1,profile=PROFILE,arm=arm,prepared=str(Path(prepared).resolve()),entry=entry,
        manifest_sha256=file_sha256(Path(prepared)/'manifest.json'),initial=initial,end=end,rows=rows,
        replay_sha256=replay_digest,events=event_summary,diagnosis=diagnosis,
        artifacts={name:file_sha256(directory/name) for name in ('replay.npz','provenance.jsonl.gz','trajectory.jsonl.gz')})
    write(directory/'bundle.json',bundle,exclusive=True)
    shared=shared_evidence(entry,initial,end,rows,replay_digest,event_summary,diagnosis)
    return dict(schema_version=1,status='technical_ready' if technical else 'prefill_ready',profile=PROFILE,
        arm=arm,run_seed=entry['run_seed'],bootstrap_mode=entry['bootstrap_mode'],games=len(rows),shared=shared,
        bundle_sha256=file_sha256(directory/'bundle.json'))

def validate_phase_bundle(directory,prepared,arm,*,technical=False):
    directory=Path(directory);prepared=Path(prepared);proof=read(directory/('technical_proof.json' if technical else 'prefill_proof.json'))
    path=directory/'prefill'/'bundle.json';require(file_sha256(path)==proof['bundle_sha256'],'Phase bundle changed')
    bundle=read(path);manifest=read(prepared/'manifest.json');entry=manifest['arms'][arm]
    require(bundle['schema_version']==1 and bundle['profile']==PROFILE and bundle['arm']==arm
        and bundle['prepared']==str(prepared.resolve()) and bundle['manifest_sha256']==file_sha256(prepared/'manifest.json')
        and bundle['entry']==entry and set(bundle['artifacts'])=={'replay.npz','provenance.jsonl.gz','trajectory.jsonl.gz'},'Phase input binding differs')
    verify({str(path.parent/k):v for k,v in bundle['artifacts'].items()})
    rows=bundle['rows'];require(len(rows)==(1 if technical else 40),'Incomplete prefill/technical games')
    for i,row in enumerate(rows):validate_rollout(row,i,entry,technical=technical)
    plan=[{k:r[k] for k in PLAN_KEYS} for r in rows];data=load_replay_data(path.parent/'replay.npz')
    total=bundle['events']['counts']['committed']
    require(total==len(data['a'])==bundle['end']['replay_size']<=300000,'Prefill exceeds replay or loses rows')
    events,games,checked=validate_stream(path.parent/'provenance.jsonl.gz',plan,data=data,total_committed=total)
    require(checked==total and events==bundle['events'] and games==[r['provenance'] for r in rows]
        and replay_data_hash(data)==bundle['replay_sha256'],'Raw replay/event proof differs')
    validate_trajectories(path.parent/'trajectory.jsonl.gz',rows,episode_start=0)
    require(bundle['initial']['q']==bundle['initial']['target']==entry['tensor_sha256'],'Initial tensor differs')
    shared=shared_evidence(entry,bundle['initial'],bundle['end'],rows,bundle['replay_sha256'],events,bundle['diagnosis'])
    expected=dict(schema_version=1,status='technical_ready' if technical else 'prefill_ready',profile=PROFILE,
        arm=arm,run_seed=entry['run_seed'],bootstrap_mode=entry['bootstrap_mode'],games=len(rows),shared=shared,
        bundle_sha256=file_sha256(path))
    require(proof==expected,'Phase proof differs from raw evidence');return proof

def validate_prefill_bundle(directory,prepared,arm):
    return validate_phase_bundle(directory,prepared,arm)

def compare_technical_receipts(control,sampled,side):
    for receipt,role in ((control,'control'),(sampled,'sampled')):
        require(receipt['job']==f'technical_{role}_p{side[-1]}' and receipt['arm']==f'{role}45'
            and receipt['bootstrap_mode']==ARMS[f'{role}45'][1] and receipt['side']==side,'Wrong technical pair')
        shared=receipt['shared'];initial,end=shared['initial'],shared['end']
        require(initial['q']==initial['target'] and all(initial[k]==end[k] for k in ('q','target','optimizer'))
            and initial['env_steps']==60000 and end['env_steps']==60303
            and initial['learn_steps']==end['learn_steps']==initial['replay_size']==0
            and shared['captured']==shared['committed']==end['replay_size']
            and shared['terminal']+shared['nonterminal']==shared['committed'] and shared['nonterminal']>0
            and shared['frames']==shared['confirmed']==303,'Technical game changed learning or lost events')
    require(control['shared']==sampled['shared'],'Technical pair actions/replay/trajectory/RNG differs')
    return dict(status='matched',side=side,eligible=False,shared=control['shared'])

def validate_technical_receipt(path,*,job=None):
    path=Path(path);receipt=read(path);jobs={j['job']:j for j in technical_plan()}
    require(receipt.get('job') in jobs and (job is None or job==receipt['job']),'Unknown technical job')
    expected=jobs[receipt['job']];prepared=Path(receipt['prepared']);manifest,entry,_=check_prepared(prepared,receipt['job'])
    require(all(receipt.get(k)==v for k,v in dict(schema_version=1,status='done',profile=PROFILE,eligible=False,
        arm=expected['arm'],run_seed=45,bootstrap_mode=expected['bootstrap_mode'],side=expected['side'],seed=4242,
        opponent='default',games=1,updates=0,pins=manifest['pins'],manifest_sha256=file_sha256(prepared/'manifest.json')).items()),'Wrong technical receipt')
    require(set(receipt['artifacts'])=={'prefill/bundle.json','prefill/replay.npz','prefill/provenance.jsonl.gz',
        'prefill/trajectory.jsonl.gz','technical_proof.json','manifest.json','rollouts.jsonl','initial_agent.pth','technical_agent.pth'},'Technical evidence inventory differs')
    verify({str(path.parent/k):v for k,v in receipt['artifacts'].items()})
    proof=validate_phase_bundle(path.parent,prepared,expected['arm'],technical=True)
    require(receipt['shared']==proof['shared'],'Technical summary differs')
    rows=[json.loads(line) for line in (path.parent/'rollouts.jsonl').read_text().splitlines()]
    require(rows==read(path.parent/'prefill/bundle.json')['rows'] and rows[0]['side']==expected['side'],'Technical raw rows differ')
    validate_run_manifest(path.parent,receipt,manifest,entry)
    for filename,key in (('initial_agent.pth','initial'),('technical_agent.pth','end')):
        validate_checkpoint(path.parent/filename,receipt['shared'][key],entry)
    return receipt

def wait_prefill(supervisor_state,arm,check):
    from scripts.sampled_target_supervisor import run_name
    state=read(supervisor_state);seed=ARMS[arm][0];path=Path(state['out'])/f'paired_prefill_{seed}.json'
    while not path.exists():check();time.sleep(1)
    pair=[f'{role}{seed}' for role in ('control','sampled')]
    proofs=[validate_prefill_bundle(ROOT/'experiments/runs'/run_name(a),state['prepared'],a) for a in pair]
    expected=compare_prefill_proofs(*proofs,seed)
    expected['proof_sha256']={a:file_sha256(ROOT/'experiments/runs'/run_name(a)/'prefill_proof.json') for a in pair}
    require(read(path)==expected,'Paired gate differs from raw proofs');check();return file_sha256(path)

def validate_run_manifest(directory,receipt,manifest,entry):
    run=read(Path(directory)/'manifest.json')
    require(run['schema_version']==1 and run['profile']==PROFILE and run['entry']==entry
        and run['pins']==manifest['pins'] and run['prepared']==receipt['prepared']
        and run['prepared_manifest_sha256']==receipt['manifest_sha256'] and run['name']==receipt['name']
        and run['job']==receipt.get('job',receipt['arm']),'Run manifest differs')
    require(isinstance(run['command'],list) and run['command']==receipt['command'],'Unbound worker command')
    return run

def validate_final_receipt(path,*,arm=None):
    path=Path(path);receipt=read(path);arm=arm or receipt['arm'];prepared=Path(receipt['prepared'])
    manifest,entry,_=check_prepared(prepared,arm)
    require(all(receipt.get(k)==v for k,v in dict(schema_version=1,status='done',profile=PROFILE,eligible=False,
        arm=arm,run_seed=entry['run_seed'],bootstrap_mode=entry['bootstrap_mode'],games=200,prefill_games=40,
        train_games=160,updates=24000,env_steps=120600,pins=manifest['pins'],
        manifest_sha256=file_sha256(prepared/'manifest.json')).items()),'Incomplete fixed final training receipt')
    required={'manifest.json','initial_agent.pth','rollouts.jsonl','prefill_proof.json','prefill/bundle.json','prefill/replay.npz',
        'prefill/provenance.jsonl.gz','train/provenance.jsonl.gz','final/agent.pth','final/agent.buffer.npz',
        'prefill/trajectory.jsonl.gz','train/trajectory.jsonl.gz','final/pilot_state.json','final_audit.json'}
    require(set(receipt['artifacts'])==required,'Final evidence inventory differs')
    verify({str(path.parent/k):v for k,v in receipt['artifacts'].items()})
    run=validate_run_manifest(path.parent,receipt,manifest,entry)
    proof=validate_prefill_bundle(path.parent,prepared,arm)
    rows=[json.loads(line) for line in (path.parent/'rollouts.jsonl').read_text().splitlines()]
    require(len(rows)==200 and rows[:40]==read(path.parent/'prefill/bundle.json')['rows'],'Incomplete rollout series')
    for i,row in enumerate(rows):validate_rollout(row,i,entry)
    validate_trajectories(path.parent/'train/trajectory.jsonl.gz',rows[40:],episode_start=40)
    audit=read(path.parent/'final_audit.json');state=read(path.parent/'final/pilot_state.json')
    require(state['arm']==arm and state['bootstrap_mode']==entry['bootstrap_mode'] and state['config']==entry['config']
        and state['env_steps']==120600 and state['learn_steps']==24000 and state['episode']==dict(episode_id=199,**entry['rollout_plan'][-1])
        and state['input_hashes']==run['inputs'] and state['rollout_progress']==dict(prefill=40,train=160,total=200)
        and set(state['files'])=={'agent.pth','agent.buffer.npz'},'Final state input/progress differs')
    verify({str(path.parent/'final'/k):v for k,v in state['files'].items()})
    data=load_replay_data(path.parent/'final/agent.buffer.npz');committed=state['replay_counts']['committed']
    a,_,checked_a=validate_stream(path.parent/'prefill/provenance.jsonl.gz',entry['rollout_plan'][:40],data=data,total_committed=committed)
    b,games,checked_b=validate_stream(path.parent/'train/provenance.jsonl.gz',entry['rollout_plan'][40:],
        a['counts']['committed'],episode_start=40,data=data,total_committed=committed)
    require(games==[r['provenance'] for r in rows[40:]] and a['counts']['committed']+b['counts']['committed']==committed
        and checked_a+checked_b==state['replay_size']==len(data['a'])==min(committed,300000)
        and state['replay_counts']['captured']==committed
        and audit['replay_sha256']==replay_data_hash(data),'Final retained replay/events mismatch')
    require(audit['reload_pass'] is True and audit['end']['q']==audit['end']['target']!=entry['tensor_sha256']
        and audit['end']['optimizer']!=proof['shared']['initial']['optimizer']
        and audit['end']['env_steps']==120600 and audit['end']['learn_steps']==24000
        and audit['end']['replay_size']==state['replay_size'] and audit['reloaded']=={k:audit['end'][k]
            for k in ('q','target','optimizer','env_steps','learn_steps','replay_size')},'Final update/reload evidence differs')
    validate_checkpoint(path.parent/'initial_agent.pth',proof['shared']['initial'],entry)
    validate_checkpoint(path.parent/'final/agent.pth',audit['end'],entry)
    require(audit['end']['agent_rng']==state['agent_rng_sha256'] and audit['end']['global_rng']==state['global_rng_sha256'],
        'Saved RNG evidence differs')
    gate=Path(run['supervisor_state']).parent/f"paired_prefill_{entry['run_seed']}.json"
    require(file_sha256(gate)==receipt['paired_gate_sha256'],'Original paired gate changed')
    return receipt

def validate_checkpoint(path,identity,entry):
    checkpoint=torch.load(path,map_location='cpu',weights_only=False)
    require(checkpoint['env_steps']==identity['env_steps'] and checkpoint['learn_steps']==identity['learn_steps']
        and checkpoint['cfg']==entry['config'] and checkpoint['feature_dim']==79 and checkpoint['n_actions']==6
        and checkpoint['ensemble']==[] and checkpoint['ensemble_dims']==[]
        and tensor_sha256(checkpoint['q'])==identity['q'] and tensor_sha256(checkpoint['target_q'])==identity['target']
        and experiment.state_sha256(checkpoint['opt'])==identity['optimizer'],'Saved tensor/optimizer identity differs')

def validate_trajectories(path,rows,*,episode_start):
    # Typed engine digests are captured at runtime; archive supports exact pair comparison,
    # not reconstruction of engine state or a claim that a submitted command had an effect.
    with gzip.open(path,'rt') as stream:
        for i,row in enumerate(rows):
            digest=hashlib.sha256()
            expected=[('reset',0)]+[(kind,step+(kind=='result')) for step in range(303) for kind in ('submitted','result')]
            for kind,step in expected:
                line=stream.readline();require(bool(line),'Truncated trajectory transcript');value=json.loads(line)
                require(value['episode_id']==episode_start+i and value['kind']==kind and value['step']==step
                    and hex64(value['sha256']),'Trajectory chronology differs')
                if kind=='submitted':
                    require(set(value['actions'])==set(SIDES) and all(np.asarray(a).shape==(16,3)
                        for a in value['actions'].values()),'Invalid submitted native action arrays')
                digest.update(value['sha256'].encode())
            require(digest.hexdigest()==row['trajectory_sha256'],'Trajectory summary differs')
        require(not stream.readline(),'Extra trajectory records')

def execute(prepared,job,name,*,supervisor_state,technical=False):
    from scripts.sampled_target_supervisor import worker_guard,training_command
    require(Path(name).name==name and name not in ('','.','..'),'New fixed run name required')
    worker_guard(supervisor_state,job,name,prepared,startup=True)
    manifest,entry,initial=check_prepared(prepared,job)
    tech=next((j for j in technical_plan() if j['job']==job),None)
    require((tech is not None)==technical,'Worker stage differs');arm=tech['arm'] if technical else job
    destination=safe_output(ROOT/'experiments/runs'/name);require(not destination.exists(),'Run exists; no restart')
    state=read(supervisor_state);command=training_command(state,job)
    bound={**manifest['input_sha256'],str(Path(prepared)/'manifest.json'):file_sha256(Path(prepared)/'manifest.json'),
        str(initial):file_sha256(initial)}
    record=dict(schema_version=1,status='running',profile=PROFILE,eligible=False,arm=arm,name=name,
        prepared=str(Path(prepared).resolve()),pins=manifest['pins'],run_seed=entry['run_seed'],bootstrap_mode=entry['bootstrap_mode'],
        manifest_sha256=file_sha256(Path(prepared)/'manifest.json'),command=command,started_at=time.time())
    if technical:record.update(job=job,side=tech['side'],seed=4242,opponent='default')
    stop=[];old={sig:signal.getsignal(sig) for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP)}
    env=events=agent=learners=None;rows=[];rollout_file=None
    def check():
        require(not stop,'Signal requested stop at complete-game boundary')
        worker_guard(supervisor_state,job,name,prepared)
    def persist():
        progress=dict(record,completed_games=len(rows),updated_at=time.time())
        if agent is not None:progress.update(env_steps=agent.env_steps,learn_steps=agent.learn_steps)
        write(destination/'progress.json',progress)
    check();destination.mkdir(parents=True,exist_ok=False)
    run=dict(schema_version=1,profile=PROFILE,pins=manifest['pins'],job=job,name=name,entry=entry,
        prepared=record['prepared'],prepared_manifest_sha256=record['manifest_sha256'],inputs=bound,
        command=command,supervisor_state=str(Path(supervisor_state).resolve()))
    write(destination/'manifest.json',run,exclusive=True)
    try:
        for sig in old:signal.signal(sig,lambda *_:stop.append(True))
        experiment.limit_threads();seed_everything(entry['run_seed'])
        learners=PilotLearners(entry,initial,destination);learners.train_mode();agent=learners.unique()[0][1]
        initial_identity=prove_initial(agent,entry);agent.save_agent(str(destination/'initial_agent.pth'));agent.learn_enabled=False
        events=EventStream(destination/'prefill/provenance.jsonl.gz',agent);agent.buffer.event_sink=events
        from luxai_s3.wrappers import LuxAIS3GymEnv
        env=ObservedEnv(LuxAIS3GymEnv(numpy_output=True));env.begin_phase(destination/'prefill/trajectory.jsonl.gz')
        rollout_file=(destination/'rollouts.jsonl').open('x')
        plan=([dict(phase='prefill',game=0,seed=4242,side=tech['side'],opponent='default')]
            if technical else entry['rollout_plan'])
        persist()
        for index,item in enumerate(plan):
            row=play(env,agent,entry,item,index,events,check,technical=technical)
            rows.append(row);rollout_file.write(encoded(row).decode());rollout_file.flush();persist()
            if index==(0 if technical else 39):
                summary=events.close();events=None;agent.buffer.event_sink=None;env.end_phase()
                proof=phase_bundle(destination,agent,entry,initial_identity,rows.copy(),summary,arm=arm,prepared=prepared,technical=technical)
                write(destination/('technical_proof.json' if technical else 'prefill_proof.json'),proof,exclusive=True)
                if not technical:
                    record['paired_gate_sha256']=wait_prefill(supervisor_state,arm,check)
                    agent.learn_enabled=True;events=EventStream(destination/'train/provenance.jsonl.gz',agent)
                    agent.buffer.event_sink=events;env.begin_phase(destination/'train/trajectory.jsonl.gz')
        check();agent.assert_boundary();rollout_file.close();rollout_file=None
        if technical:
            agent.save_agent(str(destination/'technical_agent.pth'))
            record.update(status='done',games=1,updates=0,shared=proof['shared'],finished_at=time.time())
            names=['manifest.json','rollouts.jsonl','initial_agent.pth','technical_agent.pth','technical_proof.json',
                'prefill/bundle.json','prefill/replay.npz','prefill/provenance.jsonl.gz','prefill/trajectory.jsonl.gz']
            target=destination/'technical_receipt.json';validator=lambda:validate_technical_receipt(target,job=job)
        else:
            events.close();events=None;agent.buffer.event_sink=None;env.end_phase()
            require(len(rows)==200 and agent.learn_steps==24000 and agent.env_steps==120600,'Incomplete fixed arm')
            end=learning_identity(agent);replay_digest=replay_hash(agent.buffer)
            save_pilot_bundle(agent,destination/'final',dict(arm=arm,input_hashes=bound,
                rollout_progress=dict(prefill=40,train=160,total=200)))
            # Only one learner per worker: release the original ring before reload inspection.
            learners.agents.clear();learners=None;agent=None
            inspector=SampledTargetAgent('player_0',cfg=AgentConfig.from_dict(entry['config']),train=True,
                seed=entry['run_seed']*100,bootstrap_mode=entry['bootstrap_mode'])
            load_pilot_bundle(inspector,destination/'final',dict(arm=arm,bootstrap_mode=entry['bootstrap_mode'],
                state_sha256=file_sha256(destination/'final/pilot_state.json')))
            loaded=learning_identity(inspector);keys=('q','target','optimizer','env_steps','learn_steps','replay_size')
            require(all(loaded[k]==end[k] for k in keys) and replay_hash(inspector.buffer)==replay_digest,'Reload changed saved model/replay')
            del inspector
            write(destination/'final_audit.json',dict(reload_pass=True,end=end,reloaded={k:loaded[k] for k in keys},
                replay_sha256=replay_digest),exclusive=True)
            record.update(status='done',games=200,prefill_games=40,train_games=160,updates=24000,env_steps=120600,finished_at=time.time())
            names=['manifest.json','initial_agent.pth','rollouts.jsonl','prefill_proof.json','prefill/bundle.json','prefill/replay.npz',
                'prefill/provenance.jsonl.gz','prefill/trajectory.jsonl.gz','train/provenance.jsonl.gz','train/trajectory.jsonl.gz',
                'final/agent.pth','final/agent.buffer.npz','final/pilot_state.json','final_audit.json']
            target=destination/'final_receipt.json';validator=lambda:validate_final_receipt(target,arm=arm)
        check();verify(bound);require(pins()==manifest['pins'],'Source/protected changed before receipt')
        record['artifacts']={n:file_sha256(destination/n) for n in names};persist();write(target,record,exclusive=True)
        try:validator()
        except BaseException:target.unlink();raise
        return record
    except BaseException as exc:
        record.update(status='incomplete',error=f'{type(exc).__name__}: {exc}');persist();raise
    finally:
        if events is not None:events.close()
        if rollout_file is not None:rollout_file.close()
        if env is not None:env.end_phase();env.close()
        for sig,handler in old.items():signal.signal(sig,handler)

def run_arm(prepared,arm,name,*,supervisor_state):
    return execute(prepared,arm,name,supervisor_state=supervisor_state)

def technical(prepared,arm,name,*,supervisor_state):
    return execute(prepared,arm,name,supervisor_state=supervisor_state,technical=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    prep=commands.add_parser('prepare')
    for key in ('source','out','admission','admission-sha256'):prep.add_argument('--'+key,required=True)
    prep.add_argument('--stage',choices=('technical','study'),required=True)
    for name in ('run','technical'):
        worker=commands.add_parser(name)
        for key in ('prepared','arm','name','supervisor-state'):worker.add_argument('--'+key,required=True)
    args=parser.parse_args()
    if args.command=='prepare':prepare(args.source,args.out,args.admission,args.admission_sha256,stage=args.stage)
    else:(technical if args.command=='technical' else run_arm)(args.prepared,args.arm,args.name,supervisor_state=args.supervisor_state)

if __name__=='__main__':main()
