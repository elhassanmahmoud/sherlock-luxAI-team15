"""Two fixed ON learners with original DDQN and an action-scoped 36-member mean."""
from __future__ import annotations

import argparse
import copy
from importlib.metadata import version
import json
import os
from pathlib import Path
import random
import signal
import sys
import time

import numpy as np
import torch

from agents.sherlock.model import QNet
from scripts import match_weight_study as old
from scripts.early_curriculum_study import digest, hashes, require, source_identity
from scripts.final_training_supervisor import safe_path
from scripts.threat_warmstart_compare import bound, read_bound, write

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'ensemble_behavior_20261109'
ROLES = ('on48', 'on49')
COMPLETION_SHA = '41cb8fa0689bb1a5b98bbd692e147fceb8471b5e72387b661b06e7484c244b94'
CONTROL_SHA = ('931ae709779144d578cdf8134f8ef8bb777c653f3f390426a96e03eb141d2429',
               '499ff53fd318e507e31036b73920e5792b5c47443a24d91d880e7aa2a111ee01')


def rng_identity(agent):
    return {k: old.state_sha256(v) for k,v in dict(python=random.getstate(), numpy=np.random.get_state(),
        torch=torch.get_rng_state(), agent=agent.rng.bit_generator.state).items()}


class BehaviorEnsemble:
    """Keep q/target/Adam intact; install the q hook only inside this instance's _act_est."""
    def __init__(self, agent, states, enabled):
        require(type(enabled) is bool and len(states) == 36 and agent.device.type == 'cpu'
                and agent.training and not agent.cfg.frozen and not agent.extra_q
                and agent.cnn_policy is None and agent.feat_dim == 79 and agent.n_actions == 6
                and agent.cfg.hidden == 256 and agent.cfg.dueling,
                'Exact CPU training learner and 36 members required')
        self.agent, self.enabled, self.frozen = agent, enabled, {}
        self.initial, self.rng_before = old.model_identity(agent), rng_identity(agent)
        self.source_members = [old.state_sha256(s) for s in states]
        require(self.initial['q'] == self.source_members[18], 'Wrong initial member 18')
        template = agent.q.state_dict()
        for state in states:
            require(set(state) == set(template) and all(v.dtype == template[k].dtype
                and v.shape == template[k].shape and torch.isfinite(v).all() for k,v in state.items()),
                'Member keys/shape/dtype/finiteness differ')
        if enabled:
            with torch.random.fork_rng(devices=[]):
                for index,state in enumerate(states):
                    if index == 18: continue
                    net = QNet(79,6,agent.cfg.hidden,agent.cfg.dueling)
                    net.load_state_dict(state,strict=True); net.requires_grad_(False); net.eval()
                    self.frozen[index] = net
        self.rng_after = rng_identity(agent)
        require(self.rng_before == self.rng_after and old.model_identity(agent) == self.initial,
                'Adapter setup changed learner/RNG')
        learner_ids = {id(p) for p in agent.q.parameters()}
        require({id(p) for g in agent.opt.param_groups for p in g['params']} == learner_ids,
                'Adam must own exactly the learner parameters')
        self.stats = dict(act_calls=0,network_calls=0,member_forwards=0,proposal_changed_units=0,unit_steps=0)
        self.last, self.examples, self.active, self.entered = None, [], False, False

    def __enter__(self):
        require(not self.entered and '_behavior_ensemble_owner' not in vars(self.agent), 'Adapter already entered')
        self.entered = True
        self.agent._behavior_ensemble_owner = self
        self.had_own = '_act_est' in vars(self.agent)
        self.previous = vars(self.agent).get('_act_est')
        self.original = self.agent._act_est
        self.agent._act_est = self._act
        return self

    def __exit__(self, *exc):
        if self.had_own: self.agent._act_est = self.previous
        else: vars(self.agent).pop('_act_est',None)
        vars(self.agent).pop('_behavior_ensemble_owner',None)
        self.entered = False

    def _act(self, step, obs):
        require(not self.active, 'Nested action hook')
        self.stats['act_calls'] += 1; self.last = None
        if not self.enabled: return self.original(step,obs)
        self.active = True
        handle = self.agent.q.register_forward_hook(self._hook)
        try: return self.original(step,obs)
        finally:
            handle.remove(); self.active = False

    def _hook(self, module, inputs, output):
        require(self.active and self.last is None and module is self.agent.q and not torch.is_grad_enabled(),
                'Hook outside one non-gradient action forward')
        x = inputs[0]; cache = self.agent._cache
        require(cache is not None, 'Missing actual decision cache')
        sid, _, ids, features, masks, _ = cache
        require(len(ids) > 0 and x.shape == (len(ids),79) and output.shape == (len(ids),6)
                and np.array_equal(x.detach().numpy(),np.stack([features[u] for u in ids])),
                'Forward input differs from actual cached features')
        parts = [output if i == 18 else self.frozen[i](x) for i in range(36)]
        stack = torch.stack(parts); mean = stack.mean(0)
        require(torch.isfinite(stack).all() and torch.isfinite(mean).all(), 'Nonfinite behavior values')
        # Copy before Core's numpy view applies -inf in place.
        raw, averaged, values = (v.detach().numpy().copy() for v in (output,mean,stack))
        legal = np.stack([masks[u] for u in ids]).copy()
        require(legal.shape == raw.shape and legal.any(1).all(), 'Actual legal masks invalid')
        changes = np.where(legal,raw,-np.inf).argmax(1) != np.where(legal,averaged,-np.inf).argmax(1)
        self.last = dict(step=int(sid),ids=list(map(int,ids)),raw_q=raw,mean_q=averaged,member_q=values,masks=legal)
        self.stats['network_calls'] += 1; self.stats['member_forwards'] += 36
        self.stats['unit_steps'] += len(ids); self.stats['proposal_changed_units'] += int(changes.sum())
        for k in np.flatnonzero(changes):
            if len(self.examples) >= 3: break
            self.examples.append(old.plain(dict(step=int(sid),uid=int(ids[k]),mask=legal[k],
                raw_q=raw[k],mean_q=averaged[k],member_q=values[:,k])))
        return mean

    def proof(self):
        actual = {str(i):old.state_sha256(n.state_dict()) for i,n in self.frozen.items()}
        expected = {str(i):s for i,s in enumerate(self.source_members) if i != 18} if self.enabled else {}
        require(actual == expected and not self.active and all(not p.requires_grad and p.grad is None
                for n in self.frozen.values() for p in n.parameters()), 'Frozen members/hook changed')
        return dict(enabled=self.enabled,source_members=self.source_members,frozen=actual,
            rng_before=self.rng_before,rng_after=self.rng_after,initial=self.initial,
            stats=dict(self.stats),examples=copy.deepcopy(self.examples))


def validate_release(release,a,sha,pins):
    require(release.get('profile') == PROFILE and release.get('status') == 'approved'
            and release.get('source') == a['source'] and release.get('starts') == [48,49]
            and release.get('roles') == list(ROLES) and release.get('admission_sha256') == sha
            and set(pins) == set(ROLES) and release.get('prefill_sha256') == pins
            and bool(release.get('root_review_sha256')), 'Missing/stale joint Root release')
    return release


def admission(path,sha,stage):
    require(stage in ('technical','training') and digest(path) == sha, 'Wrong phase/admission hash')
    a = json.loads(Path(path).read_text())
    require(a.get('profile') == PROFILE and a.get('schema_version') == 1 and a.get('stage') == stage
            and a.get('start_authorized') is True and a.get('allow_battery') is True
            and a.get('starts') == [48,49] and a.get('historical_runtime_gap_acknowledged') is True,
            'Explicit fixed phase/historical limitation admission required')
    require(safe_path(a['root']) == ROOT == Path.cwd().resolve(), 'Wrong checkout')
    require(source_identity(ROOT,a['python'],a['plans']) == a['source']
            and runtime_identity() == a['runtime'], 'Current source/runtime changed')
    protected = {str(ROOT/f'agents/sherlock/weights/agent_p{i}.pth'):old.V14_SHA for i in (0,1)}
    protected[str(ROOT/'Gruppe15.zip')] = old.ZIP_SHA
    require(a['protected'] == protected and hashes(protected) == protected
            and hashes(a['inputs']) == a['inputs'] and digest(bound(a,a['v14_source'])) == old.V14_SHA,
            'Input/protected bytes differ')
    output_dir(a); history = historical(a)
    require(a['initial'] == history['initial'], 'Historical initial identities differ')
    if stage == 'training':
        receipt = read_bound(a,a['technical_receipt']); approval = read_bound(a,a['technical_acceptance'])
        check_technical(receipt,history)
        require(receipt['source'] == a['source'] and receipt['config'] == a['config']
                and a['source_members'] == receipt['games'][0]['mechanism']['source_members']
                and approval.get('status') == 'PASS' and approval.get('profile') == PROFILE
                and approval.get('source') == a['source']
                and approval.get('technical_receipt_sha256') == digest(a['technical_receipt']),
                'Actual separate Root technical acceptance required')
        for p,h in receipt['files'].items(): require(digest(bound(a,p)) == h,'Technical file changed')
    return a


def runtime_identity():
    return dict(python=sys.version,packages={n:version(n) for n in ('torch','numpy','jax','jaxlib','luxai-s3')})


def check_runtime(current,historical_source):
    require(all(current.get(k) == historical_source.get(k) for k in ('python','executable','executable_sha256'))
            and all(current['files'].get(p) == h for p,h in historical_source['files'].items()),
            'Historical interpreter/engine/source bytes changed')


def historical(a):
    from scripts.match_weight_compare import accepted_training
    require(digest(bound(a,a['training_completion'])) == COMPLETION_SHA,'Wrong closed training reference')
    closure = read_bound(a,a['training_completion']); controls = accepted_training(a)['control']
    check_runtime(a['source'],closure['source'])
    initials = {}; technical = None
    for index,start in enumerate((48,49)):
        entry = closure['pairs'][str(start)]; train = read_bound(a,entry['admission'])
        require(digest(bound(a,entry['closure'])) == entry['closure_sha256'], 'Historical pair closure changed')
        require(digest(controls[index]['path']) == CONTROL_SHA[index]
                and controls[index]['config'] == a['config'] == train['config']['control']
                and a['rollout_plans'][str(start)] == train['rollout_plan'] == old.rollout_plan(start),
                'Fixed control model/config/chronology differs')
        initial_path = controls[index]['path'].parent/'control-initial.json'
        prefill_path = controls[index]['path'].parent/'prefill.json'
        receipt = read_bound(a,entry['models']['control']['receipt'])
        require(all(receipt['files'].get(str(p)) == digest(bound(a,p)) for p in (initial_path,prefill_path)),
                'Historical initial/prefill binding differs')
        initial = read_bound(a,initial_path); prefill = read_bound(a,prefill_path)
        require(initial['start'] == start and initial['config'] == a['config']
                and prefill['initial'] == prefill['current'] == initial['initial']
                and prefill['learn_steps'] == 0 and prefill['games'] == 40, 'Historical initial state differs')
        initials[str(start)] = initial['initial']
        require(digest(bound(a,train['technical_receipt'])) == train['inputs'].get(train['technical_receipt']),
                'Original technical receipt hash differs')
        old_tech = read_bound(a,train['technical_receipt'])
        require(old_tech['source'] == closure['source'] and old_tech['status'] == 'complete'
                and old_tech['profile'] == old.PROFILE and old_tech['stage'] == 'technical'
                and old_tech['start'] == 48 and old_tech['config']['control'] == a['config'],
                'Wrong historical technical receipt')
        for p,h in old_tech['files'].items(): require(digest(bound(a,p)) == h,'Historical technical file differs')
        require(technical is None or old_tech == technical,'Different historical technical references')
        technical = old_tech
    return dict(initial=initials,technical=technical)


def output_dir(a):
    out = safe_path(a['out'])
    require(out.parent == ROOT/'experiments/analysis'/PROFILE and out.name == a['stage']+'_v1'
            and all(out != Path(p) and out not in Path(p).parents for p in a['inputs']), 'Unsafe exclusive output')
    return out


def worker_command(a,path,sha,state_path,role):
    require(role in (('technical',) if a['stage'] == 'technical' else ROLES), 'Wrong worker role')
    return [a['python'],'-B','-m','scripts.ensemble_behavior_study','worker','--admission',str(path),
            '--admission-sha',sha,'--owner-state',str(state_path),'--role',role]


def check_worker(state,a,sha,role,command,*,pid,pgid,ppid,executable,actual):
    roles = {'technical'} if a['stage'] == 'technical' else set(ROLES)
    job = state.get('jobs',{}).get(role,{})
    require(role in roles and state.get('profile') == PROFILE and state.get('status') == 'running'
            and role in state.get('active',[]) and 1 <= len(state['active']) <= 2
            and set(state['active']) <= roles and set(state['jobs']) == roles
            and state.get('owner_pid') == ppid > 1 and job.get('owner_pid') == ppid
            and job.get('pid') == job.get('pgid') == pid == pgid and job.get('argv') == command
            and executable == a['python'] and isinstance(actual,list) and len(actual) == len(command)
            and actual[1:] == command[1:] and state.get('admission_sha256') == sha
            and all(state.get(k) == a[k] for k in ('root','out','python','plans','source','protected',
                'stop_file','allow_battery','stage','starts')), 'Worker lacks exact live ownership')


def check_mechanism(proof,enabled,members=None):
    source = proof['source_members']; stats = proof['stats']
    require(proof['enabled'] is enabled and len(source) == 36 and (members is None or source == members)
            and proof['initial']['q'] == source[18] and proof['rng_before'] == proof['rng_after']
            and set(proof['rng_before']) == {'python','numpy','torch','agent'}
            and proof['frozen'] == ({str(i):v for i,v in enumerate(source) if i != 18} if enabled else {})
            and all(type(n) is int and n >= 0 for n in stats.values())
            and stats['member_forwards'] == 36*stats['network_calls']
            and stats['network_calls'] <= stats['act_calls'] and stats['proposal_changed_units'] <= stats['unit_steps']
            and (enabled or stats['network_calls'] == stats['proposal_changed_units'] == 0),
            'Invalid frozen/RNG/mechanism proof')


def checkpoint(path,agent,a,role,status,completed):
    payload = dict(q=agent.q.state_dict(),target_q=agent.target_q.state_dict(),opt=agent.opt.state_dict(),
        cfg=agent.cfg.to_dict(),feature_dim=79,n_actions=6,ensemble=[],ensemble_dims=[],
        env_steps=agent.env_steps,learn_steps=agent.learn_steps,
        behavior=dict(profile=PROFILE,status=status,role=role,start=int(role[-2:]),source=a['source'],
                      completed_games=completed,component_index=18))
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


def read_replay(path):
    with np.load(path,allow_pickle=False) as f: replay = {k:f[k] for k in f.files}
    n = len(replay['r'])
    require(set(replay) == {'s','a','r','ns','done','mask'} and n > 0
            and replay['s'].shape == replay['ns'].shape == (n,79) and replay['mask'].shape == (n,6)
            and all(replay[k].shape == (n,) for k in ('a','r','done'))
            and replay['r'].dtype == np.float32 and replay['mask'].dtype == bool
            and np.isin(replay['a'],range(6)).all() and np.isin(replay['done'],[0.,1.]).all()
            and replay['mask'].any(1).all() and all(np.isfinite(v).all() for v in replay.values()),'Invalid actual replay')
    return replay


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
    check_rows(p['rows'],start,40)
    require(sum(r['reward_audit']['transitions'] for r in p['rows']) == len(replay['r']), 'Prefill pushes missing')
    return p


def check_checkpoint(cp,a,role,status,count,updates):
    require(cp['cfg'] == a['config'] and cp['feature_dim'] == 79 and cp['n_actions'] == 6
            and cp['ensemble'] == cp['ensemble_dims'] == [] and cp['env_steps'] == 60000+303*count
            and cp['learn_steps'] == updates and cp['behavior'] == dict(profile=PROFILE,status=status,
                role=role,start=int(role[-2:]),source=a['source'],completed_games=count,component_index=18)
            and all(cp[k]['body.0.weight'].shape == (256,79) and all(torch.isfinite(v).all()
                for v in cp[k].values()) for k in ('q','target_q')), 'Checkpoint configuration/identity differs')


def check_rows(rows,start,count):
    require(len(rows) == count and [r['key'] for r in rows] == old.rollout_plan(start)[:count], 'Wrong fixed chronology')
    for i,r in enumerate(rows):
        require(r['role'] == 'control' and r['behavior'] == 'ensemble' and r['start'] == start
                and r['steps'] == 303 and r['point_counting_version'] == 2
                and r['before'] == dict(env_steps=60000+303*i,learn_steps=max(0,i-40)*150)
                and r['env_steps'] == 60303+303*i and r['learn_steps'] == max(0,i-39)*150
                and (r['loss'] is None if i < 40 else np.isfinite(r['loss']))
                and r['reward_audit']['transitions'] == r['final_action_audit']['checked_replay_transitions'] > 0,
                'Actual game/update/replay counts differ')


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


def check_technical(receipt,history):
    rows=receipt['games']; reference=[r for r in history['technical']['games'] if r['role']=='control']
    expected=[(mode,seed,side) for mode in ('off','ensemble') for seed,side in old.TECH_KEYS]
    require(receipt.get('profile') == PROFILE and receipt.get('status') == 'complete'
            and receipt.get('stage') == 'technical' and len(rows) == 4 and len(reference) == 2
            and [(r['behavior'],r['key']['seed'],r['key']['side']) for r in rows] == expected,
            'Exactly four fixed technical cases required')
    members=rows[0]['mechanism']['source_members']
    for index,row in enumerate(rows):
        i=index%2; enabled=index>=2
        require(row['key'] == dict(phase='technical',game=i,seed=old.TECH_KEYS[i][0],side=old.TECH_KEYS[i][1],
                    opponent='solution92') and row['start'] == 48 and row['role'] == 'control'
                and row['steps'] == 303 and row['point_counting_version'] == 2
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
        check_mechanism(row['mechanism'],enabled,members)
        require(row['mechanism']['initial'] == row['initial']
                and row['mechanism']['stats']['act_calls'] == 303*(i+1),'Technical action/setup counts differ')
        if enabled:
            require(row['mechanism']['stats']['unit_steps'] == sum(r['reward_audit']['transitions']
                    for r in rows[2:index+1]),'Technical hook/replay unit counts differ')
        evidence=row['reward_evidence']; path=Path(evidence['path'])
        require(receipt['files'].get(str(path)) == evidence['sha256'] == digest(path),'Technical reward file changed')
        with np.load(path,allow_pickle=False) as f: data={k:f[k] for k in f.files}
        require(old.state_sha256(data) == evidence['arrays_sha256']
                and len(data['uid']) == row['reward_audit']['transitions']
                and np.count_nonzero(data['outcome']) == row['reward_audit']['nonzero_outcome_rows'],
                'Technical reward arrays differ')
        old.check_reward_arrays(data,data['control'].astype(np.float32),'control')
        if not enabled:
            ref=reference[i]
            require(old.paired_row(row) == old.paired_row(ref) and row['initial'] == ref['initial']
                    and evidence['arrays_sha256'] == ref['reward_evidence']['arrays_sha256'],
                    'OFF original control evidence differs')
    require(rows[0]['mechanism']['rng_before'] == rows[2]['mechanism']['rng_before'], 'OFF/ON initial RNG differs')
    require(rows[-1]['mechanism']['stats']['proposal_changed_units'] > 0
            and any(r['native_sha256'] != h['native_sha256'] for r,h in zip(rows[2:],reference)),
            'No actual ON preference/final action exposure')
    check_mechanism(receipt['start49_setup'],True,members)
    require(receipt['start49_setup']['initial'] == history['initial']['49']
            and receipt['start49_setup']['stats']['act_calls'] == 0,'Start49 setup differs')


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


def load_members(a):
    from scripts.ensemble_diversity_train import _source
    _,states,source_cfg=_source(bound(a,a['v14_source']))
    require(old.training_config(source_cfg,'control') == a['config'],'Actual source control config differs')
    return states


def learner(a,states,start):
    agent=old.make_learner(dict(start=start,config={'control':a['config']}),states[18],'control')
    require(agent.device.type == 'cpu' and old.model_identity(agent) == a['initial'][str(start)],
            'Actual original initialization differs')
    return agent


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
        from luxai_s3.wrappers import LuxAIS3GymEnv
        env=LuxAIS3GymEnv(numpy_output=True)  # One env, before the original make_learner seeding.
        setup49=None
        if role=='technical':
            probe=learner(a,states,49)
            with BehaviorEnsemble(probe,states,True) as adapter: setup49=adapter.proof()
            del probe,adapter
        with (directory/'games.jsonl').open('x') as stream:
            for enabled,start in ((False,48),(True,48)) if role=='technical' else ((True,int(role[-2:])),):
                agent=learner(a,states,start); initial=old.model_identity(agent); records=[]
                mode='ensemble' if enabled else 'off'
                write(directory/(mode+'-initial.json'),dict(initial=initial,start=start,config=a['config']))
                with BehaviorEnsemble(agent,states,enabled) as adapter:
                    keys=([dict(phase='technical',game=i,seed=s,side=side,opponent='solution92')
                          for i,(s,side) in enumerate(old.TECH_KEYS)] if role=='technical' else old.rollout_plan(start))
                    for key in keys:
                        guard(); row,record=old.play_one(agent,key,env)
                        row.update(behavior=mode,start=start,behavior_stats=dict(adapter.stats))
                        if role=='technical':
                            row.update(initial=initial,current=old.model_identity(agent),mechanism=adapter.proof(),
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
            check_rows(rows,int(role[-2:]),440)
            require(agent.learn_steps==60000 and old.model_identity(agent)['q']!=initial['q'],'Incomplete/unchanged learning')
            checkpoint(directory/'final.pth',agent,a,role,'complete',440)
            old.save_replay(directory/'final-replay.npz',agent.buffer)
        guard()
        receipt=dict(profile=PROFILE,status='complete',stage=a['stage'],role=role,start=start,starts=[48,49],
            behavior='ensemble' if role!='technical' else 'off_then_ensemble',source=a['source'],config=a['config'],
            admission_sha256=sha,command=guard.command,games=rows,mechanism=mechanism,start49_setup=setup49,
            files=hashes(p for p in directory.iterdir() if p.is_file()),final_identity=old.model_identity(agent),
            final_replay_sha256=old.state_sha256(old.replay_data(agent.buffer)),release_sha256=guard.release_sha,
            no_strength_claim=True)
        if role=='technical': check_technical(receipt,historical(a))
        write(directory/'receipt.json',receipt)
        return receipt
    except BaseException as exc:
        if directory is not None:
            artifacts={}
            if agent is not None:
                try:
                    checkpoint(directory/'incomplete.pth',agent,a,'on48' if role=='technical' else role,'incomplete',len(rows))
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
    require(rows == receipt['games'],'Saved chronology differs'); check_rows(rows,int(role[-2:]),440)
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
