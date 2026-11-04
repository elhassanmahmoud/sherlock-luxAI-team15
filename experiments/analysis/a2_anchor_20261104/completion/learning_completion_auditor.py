"""Independent evidence-only A2 anchor acceptance. Run only after DATA_READY.

No games, model inference, optimizer updates, or repository writes. NumPy/Torch
imports occur only after explicit authorization and four complete arm receipts.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import zipfile

EXPECTED_HEAD = '09c69349afc020a7b2418c249657a5698c472964'
A2 = '1baec85605e2b7aaad8c0beaa416d0489d2b9faa1362a9b361bbb63f04cc14bd'
INDICES = '336507d962ab589b64bfb65a6ffe02b539ba98d248afa5aabce3ee1bb32c669a'
SCALE = 1.4293522257922757
TMP = Path('/tmp/sherlock-a2-anchor-20261104')
ROOT = Path('/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def lines(path):
    raw = Path(path).read_bytes()
    require(raw.endswith(b'\n'), f'Unflushed/malformed JSONL: {path}')
    return [json.loads(line) for line in raw.splitlines()]


def csv_rows(path):
    with Path(path).open(newline='') as handle:
        return list(csv.DictReader(handle))


def verify_hashes(base, values):
    for name, digest in values.items():
        require(sha(Path(base) / name) == digest, f'Hash changed: {name}')


def head():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def typed_hash(value):
    """Independent implementation of the evidence's documented typed format."""
    digest = hashlib.sha256()

    def emit(raw):
        digest.update(len(raw).to_bytes(8, 'big'))
        digest.update(raw)

    def visit(item):
        if isinstance(item, torch.Tensor):
            tensor = item.detach().cpu().contiguous()
            emit(b'tensor'); emit(str(tensor.dtype).encode())
            visit(list(tensor.shape))
            emit(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
        elif isinstance(item, np.ndarray):
            emit(b'ndarray'); emit(item.dtype.str.encode())
            visit(list(item.shape)); emit(item.tobytes(order='C'))
        elif isinstance(item, dict):
            emit(b'dict'); emit(str(len(item)).encode())
            for key in sorted(item, key=lambda k: (type(k).__name__, repr(k))):
                visit(key); visit(item[key])
        elif isinstance(item, (list, tuple)):
            emit(type(item).__name__.encode()); emit(str(len(item)).encode())
            for child in item:
                visit(child)
        elif isinstance(item, (str, int, float, bool, type(None))):
            emit(type(item).__name__.encode()); emit(repr(item).encode())
        elif isinstance(item, np.generic):
            visit(item.item())
        else:
            raise TypeError(type(item).__name__)
    visit(value)
    return digest.hexdigest()


def tensor_hash(state):
    digest = hashlib.sha256()
    for key in sorted(state):
        tensor = state[key].detach().cpu().contiguous()
        header = json.dumps([key, str(tensor.dtype), list(tensor.shape)], separators=(',', ':'))
        digest.update(header.encode() + b'\n')
        digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def finite_tree(value):
    if isinstance(value, torch.Tensor):
        require(bool(torch.isfinite(value).all()), 'Nonfinite final tensor')
    elif isinstance(value, dict):
        for child in value.values():
            finite_tree(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            finite_tree(child)
    elif isinstance(value, float):
        require(math.isfinite(value), 'Nonfinite final scalar')


def startup_gates():
    """Only stdlib reads here: refuse before importing model dependencies."""
    require(head() == EXPECTED_HEAD, 'HEAD changed before completion audit')
    admission = read(TMP / 'training_admission.json')
    require(admission['status'] == 'admitted' and admission['source_commit'] == EXPECTED_HEAD,
            'Unaccepted training admission')
    require(admission['seeds'] == [25, 26] and admission['arms'] == ['control', 'anchor']
            and admission['total_expected_games'] == 928 and admission['updates_per_arm'] == 24000
            and admission['max_workers'] == 2, 'Admission budget differs')
    verify_hashes(ROOT, admission['source_sha256'])
    verify_hashes(ROOT, admission['protected_sha256'])
    for seed in (25, 26):
        for arm in ('control', 'anchor'):
            prepared = ROOT / f'experiments/runs/20261104_a2_anchor/seed{seed}'
            guard = read(TMP / f'seed{seed}_{arm}_guard.json')
            receipt = read(prepared / 'audits' / arm / 'anchor_receipt.json')
            require(guard['status'] == 'completed' and guard['returncode'] == 0
                    and 'stop_reason' not in guard, f'Incomplete guard {seed}/{arm}')
            require(read(prepared / 'audits' / arm / 'status.json')['status'] == 'done'
                    and receipt['status'] == 'done', f'Incomplete public arm {seed}/{arm}')
    return admission


def dataset_contract(manifest):
    parts, total = [], 0
    scale_numerator, legal_count = 0., 0
    for item in manifest['dataset_contract']['datasets']:
        directory = Path(item['path'])
        verify_hashes(directory, item['files_sha256'])
        meta = read(directory / 'manifest.json')
        require(meta['status'] == 'done' and read(directory / 'status.json')['status'] == 'done',
                'Incomplete fixed teacher dataset')
        with np.load(directory / 'dataset.npz', allow_pickle=False) as archive:
            train, target, mask = archive['is_train'], archive['teacher_q'], archive['mask']
        require(train.dtype == np.bool_ and train.ndim == 1 and target.shape == mask.shape == (len(train), 6),
                'Dataset split/teacher/mask dimensions differ')
        require(mask.dtype == np.bool_ and mask.any(1).all() and np.isfinite(target).all(),
                'Invalid fixed teacher masks or Q data')
        parts.append(np.flatnonzero(train).astype('<u4') + total)
        total += len(train)
        teacher = target[train].astype(np.float64)
        selected_mask = mask[train]
        centered = np.where(selected_mask, teacher, 0.)
        centered -= centered.sum(1, keepdims=True) / selected_mask.sum(1, keepdims=True)
        centered[~selected_mask] = 0.
        scale_numerator += float(np.square(centered).sum())
        legal_count += int(selected_mask.sum())
    indices = np.concatenate(parts).astype('<u4')
    scale = max(.001, math.sqrt(scale_numerator / legal_count))
    require(len(indices) == 356415 and total - len(indices) == 68687
            and sha_bytes(indices.tobytes()) == INDICES and abs(scale - SCALE) <= 1e-12,
            'Independently reconstructed train-only population/scale differs')
    require(manifest['dataset_contract']['train_indices_sha256'] == INDICES
            and manifest['dataset_contract']['train_rows'] == len(indices)
            and manifest['dataset_contract']['excluded_rows'] == total-len(indices)
            and manifest['dataset_contract']['scale'] == SCALE, 'Declared teacher contract differs')
    return indices, {'train_rows':len(indices), 'excluded_rows':total-len(indices),
                     'scale_recomputed':scale, 'train_indices_sha256':INDICES}


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def plan(seed):
    rng = np.random.default_rng(seed + 3000)
    names = ['solution92', 'sol92_sq', 'default', 'rush']
    return [dict(phase=phase, game=g, seed=200000 + seed*10000 + offset + g//2,
                 side=('player_0','player_1')[g%2], opponent=names[rng.choice(4,p=[.6,.2,.1,.1])])
            for phase,count,offset in (('prefill',40,5000),('train',160,3000)) for g in range(count)]


def validation_plan():
    return [dict(after_games=after,opponent=opp,seed=seed,side=side)
            for after in (0,160) for opp in ('default','solution92')
            for seed in range(500000,500004) for side in ('player_0','player_1')]


def verify_replay_file(path, expected_size):
    """Stream each array once; avoid allocating the whole replay or new agent."""
    shapes = {'s':(expected_size,79),'ns':(expected_size,79),'a':(expected_size,),
              'r':(expected_size,), 'done':(expected_size,), 'mask':(expected_size,6)}
    result = {}
    with zipfile.ZipFile(path) as archive:
        require(set(archive.namelist()) == {key+'.npy' for key in shapes}, 'Replay archive columns differ')
        for name, expected in shapes.items():
            with archive.open(name+'.npy') as handle:
                version = np.lib.format.read_magic(handle)
                require(version in ((1,0),(2,0)), 'Unsupported replay NPY version')
                reader = (np.lib.format.read_array_header_1_0 if version == (1,0)
                          else np.lib.format.read_array_header_2_0)
                shape, fortran, dtype = reader(handle)
                require(tuple(shape) == expected and not fortran and not dtype.hasobject,
                        f'Replay array shape/type differs: {name}/{shape}')
                count, digest = 0, hashlib.sha256()
                while True:
                    raw = handle.read(1024*1024)
                    if not raw:
                        break
                    digest.update(raw); count += len(raw)
                    values = np.frombuffer(raw,dtype=dtype)
                    require(bool(np.isfinite(values).all()), f'Nonfinite replay {name}')
                    if name == 'a': require(bool(((values >= 0)&(values < 6)).all()), 'Invalid replay action')
                    if name == 'done': require(bool(((values == 0)|(values == 1)).all()), 'Invalid replay terminal')
                require(count == math.prod(shape)*dtype.itemsize, 'Incomplete replay array bytes')
                result[name] = dict(shape=list(shape),dtype=dtype.str,content_sha256=digest.hexdigest())
    return dict(file_sha256=sha(path),arrays=result)


def updates_audit(directory, arm, seed, indices, train_csv):
    weight = 0. if arm == 'control' else .1
    rows = lines(directory / 'updates.jsonl')
    require(len(rows) == 24000, 'Not exactly 24000 actual updates')
    per_update = 0 if arm == 'control' else 256
    require((directory/'samples.u32').stat().st_size == 24000*per_update*4, 'Wrong sample byte count')
    rng = np.random.default_rng(20261104+seed)
    sums = dict(td_loss_sum=0.,anchor_loss_sum=0.,total_loss_sum=0.)
    gradients, min_gradient = 0, math.inf
    game_sums = []
    with (directory/'samples.u32').open('rb') as samples:
        for i,row in enumerate(rows):
            raw = samples.read(per_update*4)
            selected = np.frombuffer(raw,dtype='<u4')
            expected = indices[rng.integers(0,len(indices),size=per_update)] if per_update else np.empty(0,'<u4')
            require(type(row['update']) is int and row['update'] == i+1 and type(row['learn_steps']) is int
                    and row['learn_steps'] == i+1 and type(row['optimizer_steps']) is int
                    and row['optimizer_steps'] == 1 and row['sample_count'] == per_update
                    and row['split'] == 'train' and sha_bytes(raw) == row['sample_sha256']
                    and np.array_equal(selected,expected), f'Actual sample/update evidence differs at {i+1}')
            values = [row[k] for k in ('td_loss','anchor_loss','total_loss','anchor_output_gradient_norm')]
            require(all(type(v) in (int,float) and math.isfinite(v) and v >= -1e-6 for v in values),
                    'Nonfinite/negative loss or anchor gradient')
            require(math.isclose(row['total_loss'],row['td_loss']+weight*row['anchor_loss'],
                                 rel_tol=2e-7,abs_tol=1e-6), 'Combined objective differs')
            gradient = row['anchor_output_gradient_norm']
            if weight:
                require(gradient > 0, f'Inactive anchor backward at update {i+1}')
                gradients += 1; min_gradient = min(min_gradient,gradient)
            else:
                require(row['anchor_loss'] == gradient == 0. and row['total_loss'] == row['td_loss'],
                        'CONTROL did not preserve its zero-anchor/original path')
            for key in sums:
                sums[key] += row[key.removesuffix('_sum')]
            if (i+1)%150 == 0:
                game_sums.append(float(np.mean([r['total_loss'] for r in rows[i-149:i+1]])))
    summary = dict(updates=24000,sample_count=24000*per_update,weight=weight,
                   positive_gradient_updates=gradients,sampler_rng_sha256=typed_hash(rng.bit_generator.state),**sums)
    require(summary == read(directory/'summary.json'), 'Independently summed update summary differs')
    require(all(float(r['mean_loss']) == round(mean,5) for r,mean in zip(train_csv,game_sums)),
            'Recorded train losses are not actual 150-update means')
    return dict(**summary,min_anchor_output_gradient_norm=min_gradient if weight else 0.,
                all_samples_independently_replayed=True,excluded_sample_count=0,
                all_updates_one_optimizer_step=True)


def arm_audit(seed, arm, manifest, indices, admission):
    prepared = ROOT/f'experiments/runs/20261104_a2_anchor/seed{seed}'
    directory = prepared/'audits'/arm
    entry = manifest['arms'][arm]
    nested = prepared/'engine'/arm
    original = read(nested/'manifest.json')
    run = nested/'runs/control'
    receipt = read(directory/'anchor_receipt.json')
    inner = read(run/'final_receipt.json')
    guard_path = TMP/f'seed{seed}_{arm}_guard.json'
    guard = read(guard_path)
    require(guard['guard_sha256'] == sha(TMP/'run_guarded.py'), 'Guard source changed')
    expected_command=[admission['python'],'-B','-m','scripts.student_anchor_train','run','--prepared',
                      f'experiments/runs/20261104_a2_anchor/seed{seed}','--arm',arm,
                      '--deadline-utc',admission['deadline_utc']]
    require(guard['command'] == expected_command and Path(guard['cwd']) == ROOT,'Guard command differs')
    require(entry['engine_manifest_sha256'] == sha(nested/'manifest.json')
            and entry['engine_arm'] == 'control' and entry['excluded_engine_arms'] == ['sap0']
            and entry['weight'] == (0. if arm == 'control' else .1), 'Nested control binding differs')
    require(not (nested/'runs/sap0').exists() and not (nested/'sap0_status.json').exists(), 'Unused SAP0 was run')
    verify_hashes(ROOT,original['pins']['code']); verify_hashes(ROOT,original['pins']['protected'])
    cfg = entry['config']; require(cfg == original['arms']['control']['config']
                                 and original['run_seed'] == seed and original['student_sha256'] == A2,
                                 'Nested config/seed/A2 differs')
    require(entry['rollout_plan'] == original['arms']['control']['rollout_plan'] == plan(seed)
            and original['validation_plan'] == validation_plan(), 'Independently generated game plan differs')
    require(sha(manifest['student']) == A2 and manifest['student_sha256'] == A2, 'A2 changed')
    init_file = nested/'init/control/weights/agent.pth'
    require(sha(init_file) == original['arms']['control']['weights_sha256'], 'Initial checkpoint changed')
    initial_cp = torch.load(init_file,map_location='cpu',weights_only=True)
    require('opt' not in initial_cp and initial_cp['learn_steps'] == 0 and initial_cp['env_steps'] == 60000
            and initial_cp['cfg'] == cfg and not initial_cp['ensemble'] and not initial_cp['ensemble_dims']
            and tensor_hash(initial_cp['q']) == tensor_hash(initial_cp['target_q']) == entry['initial_tensor_sha256'],
            'Initial checkpoint is not exact fresh A2')
    source_cp = torch.load(manifest['student'],map_location='cpu',weights_only=True)
    require(typed_hash(initial_cp['q']) == typed_hash(source_cp['q'])
            and typed_hash(initial_cp['target_q']) == typed_hash(source_cp['target_q']), 'Initial tensors differ from A2')
    del source_cp, initial_cp
    actual = read(run/'manifest.json'); status = read(run/'status.json')
    expected_argv=['student_reward/finetune','--init',str(nested/'init/control'),'--name','control',
        '--variant','student_reward_20261104','--games','160','--seed',str(seed),'--map-offset','3000',
        '--lr','.0001','--prefill-games','40','--keep-final','--no-test','--val-every','160','--n-val','4',
        '--mix','solution92=0.6,sol92_sq=0.2,default=0.1,rush=0.1']
    require(status['status'] == 'done' and status['argv'] == expected_argv
            and status['actual_rollout_games'] == 200 and status['actual_validation_games'] == 32,
            'Actual runner attempt/count differs')
    require(actual['git'] == dict(commit=EXPECTED_HEAD,dirty=False) and actual['config'] == cfg
            and actual['run_seed'] == seed and actual['buffer_loaded'] == 0
            and actual['prefill_games'] == 40 and actual['train_games'] == 160
            and actual['selection'] == 'Endstand (--keep-final)' and actual['test_seeds'] == []
            and actual['val_seeds'] == [500000,500001,500002,500003]
            and actual['mix'] == dict(solution92=.6,sol92_sq=.2,default=.1,rush=.1), 'Actual manifest differs')
    require(receipt['schema_version'] == 1 and receipt['status'] == 'done' and receipt['arm'] == arm
            and receipt['run_seed'] == seed and receipt['weight'] == entry['weight']
            and receipt['prepared'] == str(prepared) and receipt['adapter_restored'] is True
            and receipt['constructor_restored'] is True and receipt['manifest_sha256'] == sha(prepared/'manifest.json')
            and receipt['inner_receipt_sha256'] == sha(run/'final_receipt.json'), 'Outer receipt differs')
    require(set(receipt['evidence_sha256']) == {'updates.jsonl','samples.u32','summary.json','prefill_replay.json'},
            'Missing outer evidence')
    verify_hashes(directory,receipt['evidence_sha256'])
    require(set(inner['evidence_sha256']) == {'training_audit.json','rollouts.jsonl','validation_games.jsonl','train.csv'},
            'Missing inner evidence')
    verify_hashes(run,inner['evidence_sha256'])
    checkpoint = run/'weights/agent.pth'
    require(inner['status'] == 'done' and inner['arm'] == 'control' and inner['run_seed'] == seed
            and inner['prepared'] == str(nested) and inner['config'] == cfg
            and inner['student_sha256'] == A2 and inner['actual_prefill_games'] == 40
            and inner['actual_train_games'] == 160 and inner['actual_validation_games'] == 32
            and receipt['checkpoint_sha256'] == inner['final_checkpoint_sha256'] == sha(checkpoint)
            and receipt['final_checkpoint'] == inner['final_checkpoint'] == str(checkpoint), 'Inner receipt differs')
    rows, vals, audit, train = lines(run/'rollouts.jsonl'), lines(run/'validation_games.jsonl'), read(run/'training_audit.json'), csv_rows(run/'train.csv')
    require(len(rows) == 200 and len(vals) == 32 and len(train) == 160, 'Not exactly 232 actual games')
    keys = ('phase','game','seed','side','opponent')
    require([{k:r[k] for k in keys} for r in rows] == plan(seed), 'Actual rollouts differ from plan')
    require([{k:r[k] for k in ('after_games','opponent','seed','side')} for r in vals] == validation_plan(),
            'Actual validation games differ from plan')
    initial,prefill,end = audit['initial'],audit['prefill'],audit['end']
    # Derive a genuinely fresh optimizer using the final parameter order, without
    # constructing a network or allocating any replay/inference context.
    cp = torch.load(checkpoint,map_location='cpu',weights_only=True)
    parameters=[torch.nn.Parameter(value.detach().clone()) for value in cp['q'].values()]
    fresh = typed_hash(torch.optim.Adam(parameters,lr=.0001).state_dict())
    del parameters
    il=initial['learning']; pl=prefill['learning']; el=end['learning']
    require(initial['q_tensor_sha256'] == initial['target_tensor_sha256'] == entry['initial_tensor_sha256']
            and il['config'] == cfg and il['optimizer_sha256'] == fresh and il['env_steps'] == 60000
            and il['learn_steps'] == 0 and il['replay']['size'] == il['replay']['pos'] == 0
            and il['recent_losses'] == [] and il['learn_enabled'] is True and il['autosave_on_terminate'] is False,
            'Actual initial learner is not fresh')
    shared=initial['initial_identity']['learners']
    require(len(shared)==1 and shared[0]['sides']==['player_0','player_1']
            and shared[0]['optimizer_sha256']==fresh and shared[0]['replay']['logical_content']=='empty-replay-v1',
            'Initial canonical learner identity differs')
    require(prefill == rows[39]['identity'] and pl['learn_steps'] == 0 and pl['env_steps'] == 72120
            and pl['optimizer_sha256'] == fresh and pl['recent_losses'] == []
            and pl['replay']['size'] > cfg['learn_start'] and not pl['learn_enabled'], 'Prefill changed learning')
    transitions=0
    for i,row in enumerate(rows):
        learning=row['identity']['learning']; training=i>=40
        action,reward=row['final_action_audit'],row['reward_audit']
        require(row['steps']==303 and row['point_counting_version']==2 and action['act_calls']==303
                and action['update_calls']==303 and reward['transitions']==action['checked_replay_transitions'],
                'Actual rollout action/reward evidence differs')
        transitions += action['checked_replay_transitions']
        require(learning['env_steps']==60000+(i+1)*303 and learning['learn_steps']==max(0,i-39)*150
                and learning['learn_enabled'] is training and learning['config']==cfg
                and not learning['autosave_on_terminate'], 'Actual learner chronology differs')
        require(learning['replay']['size']==min(transitions,cfg['buffer_capacity'])
                and learning['replay']['pos']==transitions%cfg['buffer_capacity'], 'Actual replay chronology differs')
        if not training:
            require(row['identity']['q_tensor_sha256']==row['identity']['target_tensor_sha256']==entry['initial_tensor_sha256']
                    and learning['optimizer_sha256']==fresh, 'Prefill changed weights/optimizer')
        else:
            t=train[i-40]
            require(int(t['game'])==i-40 and int(t['seed'])==row['seed'] and t['side']==row['side']
                    and t['opponent']==row['opponent'] and int(t['steps'])==303
                    and int(t['point_counting_version'])==2 and int(t['learn_steps'])==(i-39)*150
                    and int(t['env_steps'])==60000+(i+1)*303 and float(t['epsilon'])==.05,
                    'Actual train CSV chronology differs')
    require(len(audit['validations'])==2 and all(v['steps']==303 and v['point_counting_version']==2
            and v['config']==cfg and v['epsilon']==0. and not v['learn_enabled']
            and v['eval_rng_seed']==20261104 for v in vals), 'Validation evidence differs')
    for proof,after in zip(audit['validations'],(0,160)):
        require(proof['before']==proof['after'] and proof['after_games']==after
                and proof['before']['learning']['env_steps']==72120+after*303
                and proof['before']['learning']['learn_steps']==after*150, 'Validation mutated learner/RNG')
    require(end==inner['end'] and end['reload_verified'] is True and end['saved_weights_sha256']==sha(checkpoint)
            and end['q_tensor_sha256']!=entry['initial_tensor_sha256']
            and el['optimizer_sha256']!=fresh and el['env_steps']==120600 and el['learn_steps']==24000
            and end['q_tensor_sha256']==rows[-1]['identity']['q_tensor_sha256']
            and end['target_tensor_sha256']==rows[-1]['identity']['target_tensor_sha256']
            and el['optimizer_sha256']==rows[-1]['identity']['learning']['optimizer_sha256'], 'Final live learner not learned')
    finite_tree(cp)
    require(cp['feature_dim']==79 and cp['n_actions']==6 and not cp['ensemble'] and not cp['ensemble_dims']
            and cp['cfg']==cfg and cp['env_steps']==120600 and cp['learn_steps']==24000
            and tensor_hash(cp['q'])==end['q_tensor_sha256'] and tensor_hash(cp['target_q'])==end['target_tensor_sha256']
            and tensor_hash(cp['q'])==tensor_hash(cp['target_q'])
            and typed_hash(cp['q'])==el['q_sha256'] and typed_hash(cp['target_q'])==el['target_q_sha256']
            and typed_hash(cp['opt'])==el['optimizer_sha256'], 'Saved final checkpoint differs from live end')
    require(len(cp['opt']['state'])==len(cp['q']) and all(set(s)=={'step','exp_avg','exp_avg_sq'}
            and s['step'].item()==24000 for s in cp['opt']['state'].values()), 'Actual Adam state/step count differs')
    require(all(group['lr']==.0001 for group in cp['opt']['param_groups']), 'Final optimizer LR differs')
    del cp
    update_proof=updates_audit(directory,arm,seed,indices,train)
    prefill_replay=read(directory/'prefill_replay.json')
    require(prefill_replay['size']==pl['replay']['size'] and prefill_replay['pos']==pl['replay']['pos']
            and isinstance(prefill_replay['content_sha256'],str) and len(prefill_replay['content_sha256'])==64,
            'Prefill actual array evidence differs')
    projection=dict(replay=prefill_replay,rows=[dict(plan={k:r[k] for k in keys},actions=r['final_action_audit'],
                    policy=r['policy_transcript'],reward=r['reward_audit'],identity=r['identity']) for r in rows[:40]])
    require(inner['prefill_action_sha256']==typed_hash([[r['final_action_audit']['transcript_sha256'],
            r['policy_transcript']['action_state_sha256']] for r in rows[:40]]),'Inner prefill digest differs')
    replay=verify_replay_file(run/'weights/agent.buffer.npz',el['replay']['size'])
    require(not (run/'weights_best').exists() and not (run/'eval.csv').exists(), 'Unexpected selection/test artifact')
    return dict(prepared=str(prepared),receipt_sha256=sha(directory/'anchor_receipt.json'),
        checkpoint_sha256=sha(checkpoint),guard_sha256=sha(guard_path),public_validate_passed=False,
        independent_checks_passed=True,anchor_active_verified=arm=='anchor',actual_games=232,
        actual_updates=24000,total_actual_replay_transitions=transitions,update_evidence=update_proof,
        replay_evidence=replay,initial_checkpoint_sha256=sha(init_file),initial_tensor_sha256=entry['initial_tensor_sha256'],
        initial_optimizer_sha256=fresh),projection,initial


def public_validate(seed,arm,admission):
    command=[admission['python'],'-B','-m','scripts.student_anchor_train','validate','--prepared',
             f'experiments/runs/20261104_a2_anchor/seed{seed}','--arm',arm]
    record=TMP/f'learning_public_validate_seed{seed}_{arm}.json'
    require(not record.exists(),f'Public validation already recorded: {record}; ask root before rerun')
    log=TMP/f'learning_public_validate_seed{seed}_{arm}.log'
    with log.open('x') as handle:
        result=subprocess.run(command,cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),
                              stdout=handle,stderr=subprocess.STDOUT,timeout=180,check=False)
    evidence=dict(command=command,returncode=result.returncode,log=str(log),log_sha256=sha(log),
                  completed_utc=datetime.now(timezone.utc).isoformat())
    record.write_text(json.dumps(evidence,indent=2)+'\n')
    require(result.returncode==0,f'Public validate failed: {log}')
    return dict(record=str(record),record_sha256=sha(record),**evidence)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-ready',action='store_true',help='Root explicitly confirmed DATA_READY')
    args=parser.parse_args()
    require(args.data_ready,'DATA_READY authorization required; preparation only')
    output=TMP/'learning_completion_audit.json'
    report=dict(schema_version=1,status='failed',independent=True,source_commit=EXPECTED_HEAD,
        auditor_script=str(Path(__file__).resolve()),auditor_sha256=sha(__file__),
        training_admission_sha256=sha(TMP/'training_admission.json'),arms={},pair_prefill_equal={})
    try:
        admission=startup_gates()
        global np,torch
        import numpy as np
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        first=read(ROOT/'experiments/runs/20261104_a2_anchor/seed25/manifest.json')
        indices,data=dataset_contract(first); report['dataset_evidence']=data
        for seed in (25,26):
            prepared=ROOT/f'experiments/runs/20261104_a2_anchor/seed{seed}'
            manifest=read(prepared/'manifest.json')
            require(manifest['dataset_contract']==first['dataset_contract'] and manifest['run_seed']==seed
                and manifest['sampler_seed']==20261104+seed and manifest['expected_updates']==24000
                and manifest['batch_size']==256 and manifest['objective']=='original_TD + weight * existing_masked_centered_action_loss'
                and manifest['pins']==first['pins'], 'Public pair contract differs')
            verify_hashes(ROOT,manifest['pins']['code']); verify_hashes(ROOT,manifest['pins']['protected'])
            require(manifest['arms']['control']['config']==manifest['arms']['anchor']['config'], 'Pair config differs')
            pair=[]; initials=[]
            for arm in ('control','anchor'):
                key=arm.upper()+str(seed)
                proof,projection,initial=arm_audit(seed,arm,manifest,indices,admission)
                report['arms'][key]=proof; pair.append(projection);initials.append(initial)
            require(pair[0]==pair[1] and initials[0]==initials[1],f'Paired actual prefill/initial state differs seed{seed}')
            require(report['arms']['CONTROL'+str(seed)]['initial_checkpoint_sha256']
                    ==report['arms']['ANCHOR'+str(seed)]['initial_checkpoint_sha256'],
                    'Paired initial checkpoint bytes differ')
            paired=read(prepared/'paired_prefill.json')
            require(paired['status']=='matched' and paired['prefill_games']==40
                and paired['prefill_sha256']==typed_hash(pair[0])
                and paired['receipts_sha256']==[report['arms'][a.upper()+str(seed)]['receipt_sha256'] for a in ('control','anchor')],
                'Published paired prefill proof differs')
            report['pair_prefill_equal'][str(seed)]=True
            report.setdefault('pair_prefill_sha256',{})[str(seed)]=typed_hash(pair[0])
        # Public acceptance is an additional check after all independent checks.
        for seed in (25,26):
            for arm in ('control','anchor'):
                proof=report['arms'][arm.upper()+str(seed)]
                proof['public_validation']=public_validate(seed,arm,admission)
                proof['public_validate_passed']=True
        startup_gates()
        require(head()==EXPECTED_HEAD,'HEAD changed during audit')
        report['status']='passed'
        report['limitations']=['No new model inference or games; final tensors were loaded and compared directly.',
            'CONTROL exact original update path is supported by pinned reviewed zero-weight branch and actual zero-anchor records.',
            'Gradient activity is the persisted hook norm from the actual shared backward; every norm/sample/loss was independently checked.',
            'Prefill actual arrays are represented by the runtime content digest and compared exactly between paired arms; no raw prefill snapshot was separately saved.']
    except BaseException as exc:
        report['error']=f'{type(exc).__name__}: {exc}'
        raise
    finally:
        report['finished_utc']=datetime.now(timezone.utc).isoformat()
        output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        print(json.dumps(dict(status=report['status'],output=str(output),error=report.get('error'))),flush=True)


if __name__=='__main__':
    for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[name]='1'
    main()
