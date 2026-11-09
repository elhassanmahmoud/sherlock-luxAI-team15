"""Fixed ON learners; replace only original non-Solution opponents with frozen V14.

Admission extends the original behavior fields with reference_{admission,receipt,
acceptance,state}, the accepted ON training_completion, opponent_model,
opponent_config_source, opponent_config and source_members. No old admission is
re-executed. Each game's key is original; exposure records the actual opponent.
Only a joint Root review of e48/e49 prefills can produce release.json.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import time

import numpy as np
import torch

from scripts import ensemble_behavior_study as behavior
from scripts import ensemble_behavior_compare as comparison
from scripts import match_weight_study as old
from scripts.early_curriculum_study import digest, hashes, require, source_identity
from scripts.experiment import _global_rng_state, _restore_global_rng
from scripts.final_training_supervisor import safe_path
from scripts.threat_warmstart_compare import bound, read_bound, write

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'frozen_v14_exposure_20261109'
ROLES = ('e48', 'e49')
OPPONENT_SHA = '817e565f8628a3a860c3dcb84e69e9d68c5f0954f791fbd06e0f115bf6cf95d2'
ON_COMPLETION_SHA = 'fca3a077e57f079605db362f9dc68facadf787b0a3e819d1aca85050a84b23ce'
SOURCE_CONFIG_SHA = 'a094376eca24e5054b0a14228f5861b9bccb832199954fd7957f1431af5ab69f'
BehaviorEnsemble = behavior.BehaviorEnsemble
check_mechanism = behavior.check_mechanism
read_replay = behavior.read_replay
runtime_identity = behavior.runtime_identity
load_members = behavior.load_members
learner = behavior.learner


def actual_opponent(key):
    require(key['opponent'] in ('solution92','sol92_sq','default','rush'), 'Unknown original opponent')
    return 'solution92' if key['opponent'] == 'solution92' else 'frozen_v14'


def opponent_identity(agent,a,side,*,expected=None):
    nets=[agent.q,*agent.extra_q]
    require(side in ('player_0','player_1') and agent.player == side
            and agent.team_id == int(side[-1]) and agent.opp_team_id == 1-int(side[-1])
            and agent.opp_player == ('player_1' if side == 'player_0' else 'player_0')
            and agent.device.type == 'cpu' and not agent.training and not agent.cfg.frozen
            and not agent.learn_enabled and not agent.autosave_on_terminate and agent.epsilon == 0
            and agent.cfg.to_dict() == a['opponent_config'] and agent.feat_dim == 79
            and agent.n_actions == 6 and agent.cnn_policy is None and len(nets) == 36
            and not hasattr(agent,'_behavior_ensemble_owner')
            and '_act_est' not in vars(agent) and all(not net._forward_hooks for net in nets)
            and len(agent.buffer) == 0 and agent.caught_errors == 0
            and all(not p.requires_grad and p.grad is None for net in [*nets,agent.target_q]
                    for p in net.parameters()), 'Frozen opponent identity/config/side changed')
    value=dict(members=[old.state_sha256(n.state_dict()) for n in nets],
        target=old.state_sha256(agent.target_q.state_dict()),optimizer=old.state_sha256(agent.opt.state_dict()),
        env_steps=agent.env_steps,learn_steps=agent.learn_steps,buffer_size=len(agent.buffer),
        rng=old.state_sha256(agent.rng.bit_generator.state),caught_errors=agent.caught_errors)
    require(value['members'] == a['source_members'] and (expected is None or value == expected),
            'Frozen opponent tensors/counters/RNG changed')
    return value


def frozen_opponent(a,agent,side):
    """A fresh ordinary stock Agent_x for each game, without shifting learner RNGs."""
    from agents.sherlock.main import Agent_x
    path=bound(a,a['opponent_model'])
    require(digest(path) == OPPONENT_SHA and side in ('player_0','player_1'), 'Wrong frozen opponent input')
    before=behavior.rng_identity(agent); global_state=_global_rng_state()
    private=copy.deepcopy(agent.rng.bit_generator.state)
    try:
        opponent=Agent_x(side,agent_path=str(path),train=False,seed=0)
        require(type(opponent) is Agent_x, 'Ordinary stock opponent required')
        opponent.set_to_eval_mode()
        opponent.learn_enabled=opponent.autosave_on_terminate=False
        for net in [opponent.q,opponent.target_q,*opponent.extra_q]:
            net.requires_grad_(False); net.eval()
        def forbidden(*_args,**_kwargs):
            raise ValueError('Frozen opponent update/learning/saving is forbidden')
        for name in ('update','_update','_learn','save_agent','save_buffer'):
            setattr(opponent,name,forbidden)
        opponent_identity(opponent,a,side)
        require(opponent.env_cfg is None and opponent._paths.step is None and not opponent._paths.maps
                and not opponent.belief.relic_positions and opponent._cache is None
                and opponent._prev_ctx is None and not opponent._prev_feats
                and not opponent._prev_actions and not opponent._prev_masks, 'Opponent is not fresh')
    finally:
        _restore_global_rng(global_state); agent.rng.bit_generator.state=private
        require(behavior.rng_identity(agent) == before,'Opponent loading shifted learner/global RNG')
    opponent._exposure_setup_rng=dict(before=before,after=behavior.rng_identity(agent))
    return opponent


@contextmanager
def participation(opponent,key,a,actual):
    """Observe the actual ordinary opponent methods; never change action computation."""
    side='player_1' if key['side']=='player_0' else 'player_0'
    require(actual in ('solution92','frozen_v14') and getattr(opponent,'player',side) == side,
            'Wrong actual opponent side')
    frozen=actual=='frozen_v14'
    proof=dict(original_opponent=key['opponent'],actual_opponent=actual,opponent_side=side,
        opponent_class=type(opponent).__module__+'.'+type(opponent).__qualname__,
        new_game_calls=0,env_cfg_calls=0,act_calls=0,action_sha256=None)
    action_hash=hashlib.sha256(); missing=object(); saved={}
    if frozen:
        proof.update(model_sha256=OPPONENT_SHA,seed=0,fresh=True,config=a['opponent_config'],
            setup_rng=opponent._exposure_setup_rng,before=opponent_identity(opponent,a,side))
    def install(name,wrapper):
        saved[name]=vars(opponent).get(name,missing); setattr(opponent,name,wrapper)
    if hasattr(opponent,'new_game'):
        original_new=opponent.new_game
        def new_game(player=None):
            require(player == side and proof['new_game_calls'] == 0 and proof['act_calls'] == 0,
                    'Opponent new_game side/order differs')
            result=original_new(player); proof['new_game_calls']+=1
            return result
        install('new_game',new_game)
    if hasattr(opponent,'set_env_cfg'):
        original_cfg=opponent.set_env_cfg
        def set_env_cfg(config):
            require(proof['env_cfg_calls'] == 0 and proof['act_calls'] == 0,'Opponent env config order differs')
            result=original_cfg(config); proof['env_cfg_calls']+=1
            return result
        install('set_env_cfg',set_env_cfg)
    original_act=opponent.act
    def act(step,obs):
        require(step == proof['act_calls'] and (not frozen or
                (proof['new_game_calls'] == proof['env_cfg_calls'] == 1 and opponent.player == side)),
                'Opponent action side/order differs')
        result=original_act(step=step,obs=obs)
        action_hash.update(old.state_sha256((step,result)).encode()); proof['act_calls']+=1
        return result
    install('act',act)
    try:
        yield proof
        if frozen: proof['after']=opponent_identity(opponent,a,side,expected=proof['before'])
        proof['action_sha256']=action_hash.hexdigest()
    finally:
        for name,prior in saved.items():
            if prior is missing: vars(opponent).pop(name,None)
            else: setattr(opponent,name,prior)


def check_exposure(proof,key,a,*,actual=None):
    want=actual or actual_opponent(key)
    side='player_1' if key['side']=='player_0' else 'player_0'
    require(proof['original_opponent'] == key['opponent'] and proof['actual_opponent'] == want
            and proof['opponent_side'] == side and proof['act_calls'] == 303
            and isinstance(proof['opponent_class'],str) and bool(proof['opponent_class'])
            and isinstance(proof['action_sha256'],str) and len(proof['action_sha256']) == 64,
            'Actual opponent participation differs')
    if want == 'frozen_v14':
        before=proof['before']
        require(proof['opponent_class'] == 'agents.sherlock.main.Agent_x'
                and proof['model_sha256'] == OPPONENT_SHA and proof['seed'] == 0 and proof['fresh'] is True
                and proof['new_game_calls'] == proof['env_cfg_calls'] == 1
                and proof['config'] == a['opponent_config'] and before == proof['after']
                and before['members'] == a['source_members'] and len(before['members']) == 36
                and before['buffer_size'] == before['caught_errors'] == 0
                and proof['setup_rng']['before'] == proof['setup_rng']['after']
                and set(proof['setup_rng']['before']) == {'python','numpy','torch','agent'},
                'Frozen opponent proof differs')
    else:
        require(proof['opponent_class'] == 'agents.Solution_92_Kaggle.agent.Agent'
                and proof['new_game_calls'] == 0 and proof['env_cfg_calls'] == 1,
                'Wrong ordinary Solution opponent')


def play_one(agent,key,env,a,*,actual=None):
    from scripts.common import make_opponent, play_game
    from scripts.par_eval import require_no_agent_errors
    side='player_1' if key['side']=='player_0' else 'player_0'; actual=actual or actual_opponent(key)
    before=dict(env_steps=agent.env_steps,learn_steps=agent.learn_steps)
    traced=old.TraceEnv(env)
    opponent=(frozen_opponent(a,agent,side) if actual == 'frozen_v14' else make_opponent('solution92',side))
    with participation(opponent,key,a,actual) as exposure, \
            old.reward_audit(agent,retain=key['phase']!='train') as audit, old.action_audit(agent) as labels:
        row=play_game(traced,agent,opponent,key['seed'],key['side'],train=True)
    require_no_agent_errors(agent,opponent); check_exposure(exposure,key,a,actual=actual)
    records=audit.pop('records',None)
    require(row['steps'] == 303 and row['point_counting_version'] == 2 and agent.caught_errors == 0
            and audit['updates'] == labels['update_calls'] == labels['act_calls'] == 303
            and audit['transitions'] == labels['checked_replay_transitions'] > 0,'Incomplete game/replay audit')
    expected_updates=sum((before['env_steps']+i+1)%agent.cfg.train_every == 0
                         for i in range(303) if i%101 != 0) if agent.learn_enabled else 0
    require(agent.env_steps == before['env_steps']+303
            and agent.learn_steps == before['learn_steps']+expected_updates,'Unexpected game/update counts')
    loss=agent.pop_mean_loss(); require(not agent.learn_enabled or math.isfinite(loss),'Nonfinite actual learning loss')
    row.update(key=key,role=agent.role,before=before,env_steps=agent.env_steps,learn_steps=agent.learn_steps,
        loss=loss if math.isfinite(loss) else None,epsilon=agent.epsilon,reward_audit=audit,final_action_audit=labels,
        native_sha256=traced.native.hexdigest(),trajectory_sha256=traced.trajectory.hexdigest(),exposure=exposure)
    return row,records


def check_rows(rows,start,count,a):
    behavior.check_rows(rows,start,count)
    for row in rows: check_exposure(row['exposure'],row['key'],a)


def historical(a):
    """Reuse sealed metadata validators; never re-admit old sources under current HEAD."""
    require(digest(bound(a,a['training_completion'])) == ON_COMPLETION_SHA,'Wrong accepted ON closure')
    reference,_=comparison.accepted_references(a); controls=comparison.accepted_training(a)
    closure=read_bound(a,a['training_completion']); train=read_bound(a,closure['admission'])
    metadata_path=bound(a,a['opponent_config_source']); metadata=read_bound(a,metadata_path)
    require(digest(metadata_path) == SOURCE_CONFIG_SHA, 'Pinned source config wrapper changed')
    require(
            metadata['source_sha256'] == old.V14_SHA
            and a['opponent_config'] == comparison.inference_config({'cfg':metadata['source_config']})
            and old.training_config(metadata['source_config'],'control') == a['config'],
            'Historical source/opponent config changed')
    record=reference['models']['v14']
    require(a['opponent_model'] == record['path'] and record['sha256'] == OPPONENT_SHA
            and a['source_members'] == record['member_sha256'] and len(a['source_members']) == 36
            and a['config'] == train['config'] and a['rollout_plans'] == train['rollout_plans']
            == {str(start):old.rollout_plan(start) for start in (48,49)}, 'Historical opponent/chronology changed')
    initials={}
    for entry in controls:
        start=entry['start']; directory=entry['path'].parent
        receipt=read_bound(a,closure['models'][f'on{start}']['receipt'])
        initial_path=directory/'ensemble-initial.json'; prefill_path=directory/'prefill.json'
        require(all(receipt['files'].get(str(p)) == digest(bound(a,p)) for p in (initial_path,prefill_path)),
                'Historical initial/prefill bytes changed')
        initial=read_bound(a,initial_path); prefill=read_bound(a,prefill_path)
        require(entry['config'] == initial['config'] == a['config'] and initial['start'] == start
                and initial['initial'] == prefill['initial'] == prefill['current']
                and prefill['games'] == 40 and prefill['learn_steps'] == 0,'Historical initial state changed')
        initials[str(start)]=initial['initial']
    technical=read_bound(a,train['technical_receipt'])
    require(set(initials) == {'48','49'} and a['initial'] == initials
            and technical['profile'] == behavior.PROFILE and technical['stage'] == 'technical'
            and technical['status'] == 'complete' and technical['config'] == a['config']
            and len([r for r in technical['games'] if r['behavior']=='ensemble']) == 2,
            'Historical ON initial/technical identities changed')
    return dict(initial=initials,technical=technical,reference=reference)


def admission(path,sha,stage):
    require(stage in ('technical','training') and digest(path) == sha,'Wrong phase/admission hash')
    a=json.loads(Path(path).read_text())
    require(a.get('profile') == PROFILE and a.get('schema_version') == 1 and a.get('stage') == stage
            and a.get('start_authorized') is True and a.get('allow_battery') is True
            and a.get('starts') == [48,49] and a.get('historical_runtime_gap_acknowledged') is True,
            'Explicit fixed phase/historical limitation admission required')
    require(safe_path(a['root']) == ROOT == Path.cwd().resolve(),'Wrong checkout')
    require(source_identity(ROOT,a['python'],a['plans']) == a['source']
            and runtime_identity() == a['runtime'],'Current source/runtime changed')
    protected={str(ROOT/f'agents/sherlock/weights/agent_p{i}.pth'):old.V14_SHA for i in (0,1)}
    protected[str(ROOT/'Gruppe15.zip')]=old.ZIP_SHA
    require(a['protected'] == protected and hashes(protected) == protected and hashes(a['inputs']) == a['inputs']
            and digest(bound(a,a['v14_source'])) == old.V14_SHA
            and digest(bound(a,a['opponent_model'])) == OPPONENT_SHA,'Input/protected bytes differ')
    output_dir(a); history=historical(a)
    closure=read_bound(a,a['training_completion']); prior=read_bound(a,closure['admission'])
    require(a['runtime'] == prior['runtime'],'Accepted ON runtime changed')
    if stage=='training':
        receipt=read_bound(a,a['technical_receipt']); approval=read_bound(a,a['technical_acceptance'])
        check_technical(receipt,history,a)
        require(receipt['source'] == a['source'] and receipt['config'] == a['config']
                and approval.get('status') == 'PASS' and approval.get('profile') == PROFILE
                and approval.get('source') == a['source']
                and approval.get('technical_receipt_sha256') == digest(a['technical_receipt'])
                and approval.get('original_processes_ended') is True,
                'Actual separate Root technical acceptance required')
        for p,h in receipt['files'].items(): require(digest(bound(a,p)) == h,'Technical file changed')
    else:
        require('technical_receipt' not in a and 'technical_acceptance' not in a,'Future technical evidence forbidden')
    return a


def check_technical(receipt,history,a):
    rows=receipt['games']; reference=[r for r in history['technical']['games'] if r['behavior']=='ensemble']
    expected=[(group,seed,side) for group in ('solution92','frozen_v14') for seed,side in old.TECH_KEYS]
    require(receipt.get('profile') == PROFILE and receipt.get('status') == 'complete'
            and receipt.get('stage') == 'technical' and len(rows) == 4 and len(reference) == 2
            and [(r['technical_group'],r['key']['seed'],r['key']['side']) for r in rows] == expected,
            'Exactly four fixed technical cases required')
    for index,row in enumerate(rows):
        i=index%2; group='solution92' if index<2 else 'frozen_v14'
        require(row['key'] == dict(phase='technical',game=i,seed=old.TECH_KEYS[i][0],side=old.TECH_KEYS[i][1],
                    opponent='solution92') and row['start'] == 48 and row['role'] == 'control'
                and row['behavior'] == 'ensemble' and row['steps'] == 303 and row['point_counting_version'] == 2
                and row['before'] == dict(env_steps=60000+303*i,learn_steps=0)
                and row['env_steps'] == 60303+303*i and row['learn_steps'] == 0
                and row['initial'] == row['current'] == history['initial']['48']
                and row['loss'] is None and row['epsilon'] == reference[i]['epsilon']
                and row['game_win'] == int(row['our_wins'] > row['opp_wins'])
                and row['point_win'] == (1. if row['our_points'] > row['opp_points'] else
                                         .5 if row['our_points'] == row['opp_points'] else 0.)
                and row['reward_audit']['updates'] == row['final_action_audit']['act_calls']
                    == row['final_action_audit']['update_calls'] == 303
                and row['reward_audit']['transitions'] == row['final_action_audit']['checked_replay_transitions'] > 0,
                'Technical counters/initial/replay differ')
        check_mechanism(row['mechanism'],True,a['source_members']); check_exposure(row['exposure'],row['key'],a,actual=group)
        require(row['mechanism']['initial'] == row['initial']
                and row['mechanism']['stats']['act_calls'] == 303*(i+1)
                and row['mechanism']['stats']['unit_steps'] == sum(r['reward_audit']['transitions']
                    for r in rows[index-i:index+1]),'Technical action/setup counts differ')
        evidence=row['reward_evidence']; path=Path(evidence['path'])
        require(receipt['files'].get(str(path)) == evidence['sha256'] == digest(path),'Technical reward file changed')
        with np.load(path,allow_pickle=False) as f: data={k:f[k] for k in f.files}
        require(old.state_sha256(data) == evidence['arrays_sha256']
                and len(data['uid']) == row['reward_audit']['transitions']
                and np.count_nonzero(data['outcome']) == row['reward_audit']['nonzero_outcome_rows'],
                'Technical reward arrays differ')
        old.check_reward_arrays(data,data['control'].astype(np.float32),'control')
        if index<2:
            ref=reference[i]
            require(old.paired_row(row) == old.paired_row(ref) and row['initial'] == ref['initial']
                    and evidence['arrays_sha256'] == ref['reward_evidence']['arrays_sha256']
                    and row['mechanism'] == ref['mechanism'],'Historical ON behavior/replay differs')
    require(rows[0]['mechanism']['rng_before'] == rows[2]['mechanism']['rng_before'],'Technical initial RNG differs')
    check_mechanism(receipt['start49_setup'],True,a['source_members'])
    require(receipt['start49_setup']['initial'] == history['initial']['49']
            and receipt['start49_setup']['stats']['act_calls'] == 0,'Start49 setup differs')


def validate_release(release,a,sha,pins):
    require(release.get('profile') == PROFILE and release.get('status') == 'approved'
            and release.get('source') == a['source'] and release.get('starts') == [48,49]
            and release.get('roles') == list(ROLES) and release.get('admission_sha256') == sha
            and set(pins) == set(ROLES) and release.get('prefill_sha256') == pins
            and bool(release.get('root_review_sha256')), 'Missing/stale joint Root release')
    return release


def output_dir(a):
    out=safe_path(a['out'])
    require(out.parent == ROOT/'experiments/analysis'/PROFILE and out.name == a['stage']+'_v1'
            and all(out != Path(p) and out not in Path(p).parents for p in a['inputs']), 'Unsafe exclusive output')
    return out


def worker_command(a,path,sha,state_path,role):
    require(role in (('technical',) if a['stage']=='technical' else ROLES), 'Wrong worker role')
    return [a['python'],'-B','-m','scripts.frozen_v14_exposure','worker','--admission',str(path),
            '--admission-sha',sha,'--owner-state',str(state_path),'--role',role]


def check_worker(state,a,sha,role,command,*,pid,pgid,ppid,executable,actual):
    roles={'technical'} if a['stage']=='technical' else set(ROLES); job=state.get('jobs',{}).get(role,{})
    require(role in roles and state.get('profile') == PROFILE and state.get('status') == 'running'
            and role in state.get('active',[]) and 1 <= len(state['active']) <= 2
            and set(state['active']) <= roles and set(state['jobs']) == roles
            and state.get('owner_pid') == ppid > 1 and job.get('owner_pid') == ppid
            and job.get('pid') == job.get('pgid') == pid == pgid and job.get('argv') == command
            and executable == a['python'] and isinstance(actual,list) and len(actual) == len(command)
            and actual[1:] == command[1:] and state.get('admission_sha256') == sha
            and all(state.get(k) == a[k] for k in ('root','out','python','plans','source','protected',
                'stop_file','allow_battery','stage','starts')), 'Worker lacks exact live ownership')



def checkpoint(path,agent,a,role,status,completed):
    payload = dict(q=agent.q.state_dict(),target_q=agent.target_q.state_dict(),opt=agent.opt.state_dict(),
        cfg=agent.cfg.to_dict(),feature_dim=79,n_actions=6,ensemble=[],ensemble_dims=[],
        env_steps=agent.env_steps,learn_steps=agent.learn_steps,
        exposure=dict(profile=PROFILE,status=status,role=role,start=int(role[-2:]),source=a['source'],
                      completed_games=completed,component_index=18,opponent_sha256=OPPONENT_SHA))
    require(all(torch.isfinite(v).all() for k in ('q','target_q') for v in payload[k].values()),'Nonfinite model')
    with Path(path).open('xb') as stream: torch.save(payload,stream)


def prefill_proof(directory,agent,a,sha,role,rows,initial,records,adapter):
    require(len(rows) == 40 and not agent.learn_enabled and agent.learn_steps == 0
            and agent.env_steps == 72120 and old.model_identity(agent) == initial
            and not agent.opt.state and len(agent.buffer) >= agent.cfg.learn_start,'Invalid unchanged prefill')
    replay = old.replay_data(agent.buffer)
    audit = {k:np.concatenate([r[k] for r in records]) for k in records[0]}
    require(len(audit['uid']) == len(agent.buffer),'Prefill replay overflow')
    old.check_reward_arrays(audit,replay['r'],'control')
    old.save_replay(directory/'prefill-replay.npz',agent.buffer)
    checkpoint(directory/'prefill.pth',agent,a,role,'prefill',40)
    old.save_reward_evidence(directory/'prefill-reward-audit.npz',audit)
    return dict(profile=PROFILE,status='prefill_ready',role=role,start=int(role[-2:]),stage=a['stage'],
        source=a['source'],admission_sha256=sha,config=a['config'],initial=initial,current=old.model_identity(agent),
        games=40,env_steps=agent.env_steps,learn_steps=0,replay_size=len(agent.buffer),
        replay_sha256=old.state_sha256(replay),reward_audit_sha256=old.state_sha256(audit),
        mechanism=adapter.proof(),rows=rows,files=hashes(directory/n for n in
            ('prefill.pth','prefill-replay.npz','prefill-reward-audit.npz')))


def validate_prefill_file(path,a,role):
    path = Path(path); p = json.loads(path.read_text()); directory = path.parent; start = int(role[-2:])
    require(role in ROLES and p['profile'] == PROFILE and p['status'] == 'prefill_ready'
            and p['role'] == role and p['start'] == start and p['stage'] == 'training'
            and p['source'] == a['source'] and p['config'] == a['config']
            and p['games'] == 40 and p['env_steps'] == 72120 and p['learn_steps'] == 0
            and p['initial'] == p['current'] == a['initial'][str(start)]
            and set(p['files']) == {str(directory/n) for n in ('prefill.pth','prefill-replay.npz','prefill-reward-audit.npz')}
            and hashes(p['files']) == p['files'], 'Prefill binding/state differs')
    check_mechanism(p['mechanism'],True,a['source_members'])
    replay = read_replay(directory/'prefill-replay.npz')
    with np.load(directory/'prefill-reward-audit.npz',allow_pickle=False) as f: audit = {k:f[k] for k in f.files}
    require(old.state_sha256(replay) == p['replay_sha256'] and old.state_sha256(audit) == p['reward_audit_sha256']
            and len(replay['r']) == p['replay_size'] >= a['config']['learn_start']
            and p['replay_size'] <= a['config']['buffer_capacity']
            and p['mechanism']['stats']['act_calls'] == 12120
            and p['mechanism']['stats']['unit_steps'] == p['replay_size'], 'Saved prefill data differs')
    old.check_reward_arrays(audit,replay['r'],'control')
    cp = torch.load(directory/'prefill.pth',map_location='cpu',weights_only=True)
    check_checkpoint(cp,a,role,'prefill',40,0)
    require({k:old.state_sha256(cp[v]) for k,v in [('q','q'),('target','target_q'),('optimizer','opt')]}
            == p['initial'] and not cp['opt']['state'], 'Prefill weights/Adam changed')
    check_rows(p['rows'],start,40,a)
    require(sum(r['reward_audit']['transitions'] for r in p['rows']) == len(replay['r']), 'Prefill pushes missing')
    return p


def check_checkpoint(cp,a,role,status,count,updates):
    require(cp['cfg'] == a['config'] and cp['feature_dim'] == 79 and cp['n_actions'] == 6
            and cp['ensemble'] == cp['ensemble_dims'] == [] and cp['env_steps'] == 60000+303*count
            and cp['learn_steps'] == updates and cp['exposure'] == dict(profile=PROFILE,status=status,
                role=role,start=int(role[-2:]),source=a['source'],completed_games=count,component_index=18,opponent_sha256=OPPONENT_SHA)
            and all(cp[k]['body.0.weight'].shape == (256,79) and all(torch.isfinite(v).all()
                for v in cp[k].values()) for k in ('q','target_q')), 'Checkpoint configuration/identity differs')


def approve_prefill(a,sha,review_path,review_sha):
    require(a['stage'] == 'training', 'Only admitted common training can be released')
    directory = Path(a['out']); pins = {}
    for role in ROLES:
        path = directory/role/'prefill.json'; p = validate_prefill_file(path,a,role); pins[role] = digest(path)
        require(p['admission_sha256'] == sha and json.loads((path.parent/'waiting.json').read_text()) ==
            dict(profile=PROFILE,role=role,admission_sha256=sha,prefill_sha256=pins[role]), 'Worker is not waiting')
    state = json.loads((directory/'state.json').read_text())
    require(state.get('status') == 'running' and set(state.get('active',[])) == set(ROLES)
            and state.get('admission_sha256') == sha,'Both original workers must wait')
    require(digest(review_path) == review_sha,'Root review changed')
    review = json.loads(Path(review_path).read_text())
    require(review.get('status') == 'PASS' and review.get('profile') == PROFILE
            and review.get('source') == a['source'] and review.get('admission_sha256') == sha
            and review.get('prefill_sha256') == pins,'Wrong joint Root review')
    release = dict(profile=PROFILE,status='approved',source=a['source'],starts=[48,49],roles=list(ROLES),
        admission_sha256=sha,prefill_sha256=pins,root_review=str(Path(review_path).resolve()),root_review_sha256=review_sha)
    write(directory/'release.json',release)
    return release


class WorkerGuard:
    def __init__(self,a,path,sha,state_path,role,stop):
        self.a,self.path,self.sha,self.state_path,self.role,self.stop=a,Path(path),sha,Path(state_path),role,stop
        self.command=worker_command(a,path,sha,state_path,role); self.release_sha=None

    def __call__(self):
        from scripts.fog_reward_supervisor import guard
        require(not self.stop[0],'Signal: stop at completed game boundary')
        state=json.loads(self.state_path.read_text())
        check_worker(state,self.a,self.sha,self.role,self.command,pid=os.getpid(),pgid=os.getpgrp(),
            ppid=os.getppid(),executable=sys.executable,actual=getattr(sys,'orig_argv',None))
        require(digest(self.path) == self.sha and state['inputs'].get(str(self.path)) == self.sha
                and all(state['inputs'].get(p) == h for p,h in self.a['inputs'].items()),'Admission changed')
        if self.release_sha: require(digest(Path(self.a['out'])/'release.json') == self.release_sha,'Release changed')
        guard(state,{},allow_battery=self.a['allow_battery'])


def wait_release(a,sha,guard):
    directory=Path(a['out']); path=directory/'release.json'
    while not path.exists(): guard(); time.sleep(1)
    pins={r:digest(directory/r/'prefill.json') for r in ROLES}
    release=validate_release(json.loads(path.read_text()),a,sha,pins)
    require(digest(release['root_review']) == release['root_review_sha256'],'Root review changed')
    guard.release_sha=digest(path); guard()


def run_worker(a,path,sha,state_path,role):
    from scripts.experiment import limit_threads
    limit_threads(); stop=[False]; agent=env=directory=None; rows=[]
    handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP)}
    for sig in handlers: signal.signal(sig,lambda *_:stop.__setitem__(0,True))
    guard=WorkerGuard(a,path,sha,state_path,role,stop)
    try:
        expected={'technical'} if role=='technical' else set(ROLES); deadline=time.monotonic()+15
        while not expected <= set(json.loads(Path(state_path).read_text()).get('jobs',{})):
            require(not stop[0] and not Path(a['stop_file']).exists() and time.monotonic()<deadline,'Registration missing/STOP')
            time.sleep(.05)
        guard(); directory=Path(a['out'])/role; directory.mkdir(exist_ok=False)
        states=load_members(a)
        require([old.state_sha256(s) for s in states] == a['source_members'], 'Actual original member order differs')
        from luxai_s3.wrappers import LuxAIS3GymEnv
        env=LuxAIS3GymEnv(numpy_output=True)  # One env, before the original make_learner seeding.
        setup49=None
        if role=='technical':
            probe=learner(a,states,49)
            with BehaviorEnsemble(probe,states,True) as adapter: setup49=adapter.proof()
            del probe,adapter
        with (directory/'games.jsonl').open('x') as stream:
            for group,start in (('solution92',48),('frozen_v14',48)) if role=='technical' else (('mixed',int(role[-2:])),):
                agent=learner(a,states,start); initial=old.model_identity(agent); records=[]
                mode=group if role=='technical' else 'ensemble'
                write(directory/(mode+'-initial.json'),dict(initial=initial,start=start,config=a['config']))
                with BehaviorEnsemble(agent,states,True) as adapter:
                    keys=([dict(phase='technical',game=i,seed=s,side=side,opponent='solution92')
                          for i,(s,side) in enumerate(old.TECH_KEYS)] if role=='technical' else old.rollout_plan(start))
                    for key in keys:
                        guard(); row,record=play_one(agent,key,env,a,actual=group if role=='technical' else None)
                        row.update(behavior='ensemble',start=start,behavior_stats=dict(adapter.stats))
                        if role=='technical':
                            row.update(technical_group=group,initial=initial,current=old.model_identity(agent),mechanism=adapter.proof(),
                                reward_evidence=old.save_reward_evidence(directory/f'{mode}-{key["game"]}-reward.npz',record))
                        elif record is not None: records.append(record)
                        stream.write(json.dumps(old.plain(row),allow_nan=False)+'\n'); stream.flush(); os.fsync(stream.fileno())
                        rows.append(row); guard()
                        if role!='technical' and key['phase']=='prefill' and key['game']==39:
                            proof=prefill_proof(directory,agent,a,sha,role,rows,initial,records,adapter)
                            write(directory/'prefill.json',proof); records.clear()
                            write(directory/'waiting.json',dict(profile=PROFILE,role=role,admission_sha256=sha,
                                  prefill_sha256=digest(directory/'prefill.json')))
                            wait_release(a,sha,guard); agent.learn_enabled=True
                    mechanism=adapter.proof()
        guard()
        if role!='technical':
            check_rows(rows,int(role[-2:]),440,a)
            require(agent.learn_steps==60000 and old.model_identity(agent)['q']!=initial['q'],'Incomplete/unchanged learning')
            checkpoint(directory/'final.pth',agent,a,role,'complete',440)
            old.save_replay(directory/'final-replay.npz',agent.buffer)
        guard()
        receipt=dict(profile=PROFILE,status='complete',stage=a['stage'],role=role,start=start,starts=[48,49],
            behavior='ensemble',opponent_policy='original_solution_else_frozen_v14',source=a['source'],config=a['config'],
            admission_sha256=sha,command=guard.command,games=rows,mechanism=mechanism,start49_setup=setup49,
            files=hashes(p for p in directory.iterdir() if p.is_file()),final_identity=old.model_identity(agent),
            final_replay_sha256=old.state_sha256(old.replay_data(agent.buffer)),release_sha256=guard.release_sha,
            no_strength_claim=True)
        if role=='technical': check_technical(receipt,historical(a),a)
        write(directory/'receipt.json',receipt)
        return receipt
    except BaseException as exc:
        if directory is not None:
            artifacts={}
            if agent is not None:
                try:
                    checkpoint(directory/'incomplete.pth',agent,a,'e48' if role=='technical' else role,'incomplete',len(rows))
                    artifacts=hashes((directory/'incomplete.pth',))
                except BaseException as error: artifacts={'save_error':str(error)}
            write(directory/'incomplete.json',dict(profile=PROFILE,status='incomplete',role=role,eligible=False,
                completed_games=len(rows),error=f'{type(exc).__name__}: {exc}',artifacts=artifacts))
        raise
    finally:
        try:
            if env is not None: env.close()
        finally:
            for sig,handler in handlers.items(): signal.signal(sig,handler)


def validate_final_receipt(path,a,sha,role):
    path=Path(path); directory=path.parent; receipt=json.loads(path.read_text())
    require(receipt.get('profile') == PROFILE and receipt.get('status') == 'complete'
            and receipt.get('stage') == 'training' and receipt.get('role') == role
            and receipt.get('start') == int(role[-2:]) and receipt.get('source') == a['source']
            and receipt.get('config') == a['config'] and receipt.get('behavior') == 'ensemble'
            and receipt.get('admission_sha256') == sha and hashes(receipt['files']) == receipt['files'],
            'Final receipt/input binding differs')
    required={str(directory/n) for n in ('games.jsonl','prefill.json','prefill.pth','prefill-replay.npz',
              'prefill-reward-audit.npz','waiting.json','final.pth','final-replay.npz')}
    require(required <= set(receipt['files']),'Missing actual final artifacts')
    rows=[json.loads(line) for line in (directory/'games.jsonl').read_text().splitlines()]
    require(rows == receipt['games'],'Saved chronology differs'); check_rows(rows,int(role[-2:]),440,a)
    prefill=validate_prefill_file(directory/'prefill.json',a,role)
    require(prefill['rows'] == rows[:40] and prefill['admission_sha256'] == sha,'Preserved prefill differs')
    release_path=Path(a['out'])/'release.json'; release=json.loads(release_path.read_text())
    validate_release(release,a,sha,{r:digest(Path(a['out'])/r/'prefill.json') for r in ROLES})
    require(receipt['release_sha256'] == digest(release_path)
            and digest(release['root_review']) == release['root_review_sha256'],'Actual Root release differs')
    check_mechanism(receipt['mechanism'],True,a['source_members'])
    transitions=sum(r['reward_audit']['transitions'] for r in rows)
    require(receipt['mechanism']['initial'] == prefill['initial']
            and receipt['mechanism']['rng_before'] == prefill['mechanism']['rng_before']
            and receipt['mechanism']['stats']['act_calls'] == 133320
            and receipt['mechanism']['stats']['unit_steps'] == transitions,'Final action/unit count differs')
    cp=torch.load(directory/'final.pth',map_location='cpu',weights_only=True)
    check_checkpoint(cp,a,role,'complete',440,60000)
    identity={k:old.state_sha256(cp[v]) for k,v in [('q','q'),('target','target_q'),('optimizer','opt')]}
    require(identity == receipt['final_identity'] and identity['q'] != prefill['initial']['q']
            and cp['opt']['state'] and all(int(v['step']) == 60000 and all(torch.isfinite(t).all()
                for t in v.values() if isinstance(t,torch.Tensor)) for v in cp['opt']['state'].values()),
            'Actual final weights/Adam steps differ')
    replay=read_replay(directory/'final-replay.npz')
    require(old.state_sha256(replay) == receipt['final_replay_sha256']
            and len(replay['r']) == min(a['config']['buffer_capacity'],transitions),'Final replay differs')
    return dict(status='PASS',role=role,start=int(role[-2:]),games=440,learn_steps=60000,receipt_sha256=digest(path))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    worker,approve=sub.add_parser('worker'),sub.add_parser('approve-prefill')
    for p in (worker,approve):
        p.add_argument('--admission',type=Path,required=True); p.add_argument('--admission-sha',required=True)
    worker.add_argument('--owner-state',type=Path,required=True)
    worker.add_argument('--role',choices=('technical',*ROLES),required=True)
    approve.add_argument('--review',type=Path,required=True); approve.add_argument('--review-sha',required=True)
    args=parser.parse_args(); stage=json.loads(args.admission.read_text())['stage']
    a=admission(args.admission,args.admission_sha,stage)
    if args.command=='worker': run_worker(a,args.admission.resolve(),args.admission_sha,args.owner_state.resolve(),args.role)
    else: approve_prefill(a,args.admission_sha,args.review,args.review_sha)


if __name__=='__main__': main()
