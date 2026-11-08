"""Fixed artillery-training comparison: four arms, paired prefill, final weights only.

The explicit schedule uses the existing finetune recipe and learner/game helpers.
Only the prefill gate admits gradients; no resume, extra cards or promotion.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
from contextlib import contextmanager
from pathlib import Path
import shutil
import signal
import sys
import time

import numpy as np
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.belief import Belief
from scripts import common, experiment
from scripts.early_curriculum_study import require, source_identity
from scripts.ensemble_diversity_train import _source, prove_initial, validate_v14
from scripts.final_rescue_train import action_audit
from scripts.night_train_pilot import file_sha256, tensor_sha256
from scripts.student_reward_train import _write, _output as _safe_output, _protected_hashes
from scripts.targeting_adapt import _canonical, _finite, _prove_end, _prove_prefill, learner_identity
from scripts.variants import VARIANTS, seed_everything

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
VARIANT = 'artillery_alignment_20261108'
ARMS = {f'{role}{seed}': (seed, enabled) for seed in (43, 44)
        for role, enabled in (('control', False), ('aligned', True))}
MIX = {'solution92': .6, 'sol92_sq': .2, 'default': .1, 'rush': .1}
PLANS = [ROOT / f'docs/superpowers/{kind}/2026-11-08-artillery-alignment.md'
         for kind in ('specs', 'plans')]
SETTINGS = dict(prefill=40, games=400, n_val=4, train_base=9_000_000,
                val_base=9_600_000, updates_per_game=150)
PLAN_KEYS = ('phase', 'game', 'seed', 'side', 'opponent')
EVENT_COUNTS = ('helper_calls', 'new_permissions', 'actual_new_permissions',
                'executed_additional_saps', 'canceled_additional_saps', 'checked_helper_replay')


def _arm(arm):
    require(arm in ARMS, 'Unknown fixed arm')
    return ARMS[arm]


def rollout_plan(arm):
    seed, _ = _arm(arm)
    rng = np.random.default_rng(seed)
    names, probabilities = list(MIX), list(MIX.values())
    return [dict(phase=phase, game=game, seed=9_000_000+seed*10000+offset+game//2,
                 side=('player_0', 'player_1')[game % 2],
                 opponent=names[rng.choice(len(names), p=probabilities)])
            for phase, count, offset in (('prefill', 40, 5000), ('train', 400, 0))
            for game in range(count)]


def validation_plan():
    return [dict(after_games=after, opponent=opponent, seed=seed, side=side)
            for after in (0, 400) for opponent in ('default', 'solution92')
            for seed in range(9_600_000, 9_600_004) for side in ('player_0', 'player_1')]


def validate_source_config(cfg):
    expected = dict(art_still=False, sap_still_all=False, smart_sap=False, idle_sap=False,
        art_move_guard=False, siege=False, end_sap=0, art_sap=True, art_splash=True,
        sap_no_overkill=True, art_splash_in_training=False, fog_unknown_reward_neutral=False,
        w_sap_hit=.3, train_every=2, canonical=True, eps_end=.05, eps_decay_steps=60000,
        learn_start=5000)
    require(all(cfg.get(k) == v and type(cfg.get(k)) is type(v) for k, v in expected.items()),
            'Source violates fixed artillery/local-attribution/training assumptions')


def training_config(source_cfg, enabled):
    validate_source_config(source_cfg)
    require(type(enabled) is bool, 'Training flag must be boolean')
    return dict(source_cfg, frozen=False, lr=5e-5, rules_in_training=True,
                rules_in_training_all=True, rescue_in_training=True,
                fog_unknown_reward_neutral=False, art_splash_in_training=enabled)


def _pins():
    return dict(source=source_identity(ROOT, sys.executable, PLANS), protected=_protected_hashes())


def _check_frozen(manifest):
    require(file_sha256(Path(manifest['source'])) == SOURCE_SHA and _pins() == manifest['pins'],
            'Frozen source/HEAD/plans/interpreter/protected inputs changed')


def prepare(source, out):
    source, out = Path(source).resolve(strict=True), _safe_output(out)
    if out.exists(): raise FileExistsError(out)
    _, states, cfg = _source(source)
    validate_source_config(cfg)
    manifest = dict(schema_version=1, source=str(source), source_sha256=SOURCE_SHA,
        source_config=cfg, settings=SETTINGS, pins=_pins(), validation_plan=validation_plan(), arms={})
    for arm, (seed, enabled) in ARMS.items():
        config = training_config(cfg, enabled)
        q = copy.deepcopy(states[18])
        checkpoint = dict(q=q, target_q=copy.deepcopy(q), cfg=config, feature_dim=79,
            n_actions=6, ensemble=[], ensemble_dims=[], env_steps=60000, learn_steps=0)
        init = out / arm
        (init / 'weights').mkdir(parents=True, exist_ok=False)
        weights = init / 'weights/agent.pth'
        torch.save(checkpoint, weights)
        entry = dict(component_index=18, run_seed=seed, mix=MIX, config=config,
            tensor_sha256=tensor_sha256(q), weights_sha256=file_sha256(weights),
            rollout_plan=rollout_plan(arm))
        manifest['arms'][arm] = entry
        _write(init / 'manifest.json', dict(variant=VARIANT, base_variant=VARIANT,
                                           train_games=0, arm=arm, **entry))
    _check_frozen(manifest)
    _write(out / 'manifest.json', manifest)
    return manifest


def check_prepared(prepared, arm):
    seed, enabled = _arm(arm)
    prepared = Path(prepared).resolve(strict=True)
    manifest = json.loads((prepared / 'manifest.json').read_text())
    require(manifest.get('schema_version') == 1 and manifest.get('source_sha256') == SOURCE_SHA
        and set(manifest['arms']) == set(ARMS) and manifest['settings'] == SETTINGS
        and manifest['validation_plan'] == validation_plan(), 'Prepared study schema/plan differs')
    _check_frozen(manifest)
    _, states, cfg = _source(Path(manifest['source']))
    require(cfg == manifest['source_config'], 'Prepared source config changed')
    entry = manifest['arms'][arm]
    expected = dict(component_index=18, run_seed=seed, mix=MIX, config=training_config(cfg, enabled),
        tensor_sha256=tensor_sha256(states[18]), weights_sha256=entry['weights_sha256'],
        rollout_plan=rollout_plan(arm))
    require(entry == expected, 'Prepared arm membership/config/schedule changed')
    init = prepared / arm
    weights = init / 'weights/agent.pth'
    require({p.name for p in (init / 'weights').iterdir()} == {'agent.pth'}
        and file_sha256(weights) == entry['weights_sha256'], 'Fresh init weights changed or replay exists')
    cp = torch.load(weights, map_location='cpu', weights_only=True)
    require(set(cp) == {'q', 'target_q', 'cfg', 'feature_dim', 'n_actions', 'ensemble',
        'ensemble_dims', 'env_steps', 'learn_steps'} and not cp['ensemble'] and not cp['ensemble_dims']
        and cp['cfg'] == entry['config'] and cp['feature_dim'] == 79 and cp['n_actions'] == 6
        and cp['env_steps'] == 60000 and cp['learn_steps'] == 0
        and all(tensor_sha256(cp[k]) == entry['tensor_sha256'] for k in ('q', 'target_q')),
        'Init is not the exact fresh single-net warm start')
    require(json.loads((init/'manifest.json').read_text()) == dict(variant=VARIANT,
        base_variant=VARIANT, train_games=0, arm=arm, **entry), 'Local init manifest changed')
    return manifest, entry, init


def _tree(value):
    """Project the known live Belief and observed-enemy sets into typed state."""
    if type(value) is Belief: return ('agents.sherlock.belief.Belief', _tree(vars(value)))
    if isinstance(value, dict): return {k: _tree(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return type(value)(_tree(v) for v in value)
    if isinstance(value, (set, frozenset)): return ('set', sorted((_tree(v) for v in value), key=repr))
    return value


def helper_state(agent, ctx, sap):
    return experiment.state_sha256(_tree(dict(config=agent.cfg.to_dict(), training=agent.training,
        estimator=vars(agent.param_est), point_tiles=agent.belief.point_tiles, context=ctx, sap=sap,
        agent_rng=agent.rng.bit_generator.state, global_rng=experiment._global_rng_state())))


def empty_exposure():
    return dict.fromkeys(EVENT_COUNTS, 0)


def validate_event(event, enabled):
    """Check a completed raw helper/action/replay record; no hidden-state inference."""
    for key in ('baseline', 'aligned', 'actual', 'new_permission', 'executed_additional', 'mirrored'):
        require(type(event[key]) is bool, 'Nonboolean helper evidence')
    baseline, aligned, actual = (event[k] for k in ('baseline', 'aligned', 'actual'))
    new = not baseline and aligned
    native, canonical, replay = event['native_action'], event['canonical_action'], event['replay_action']
    require(actual == (aligned if enabled else baseline) and event['new_permission'] == new
        and not (baseline and not aligned) and event['pre_action'] in range(5)
        and event['input_sha256'] == event['restored_sha256'] and len(event['input_sha256']) == 64
        and event['readonly_checks'] == 2 and canonical == replay and canonical in range(6)
        and len(native) == 3 and native[0] == (geo.mirror_dir(canonical)
            if event['mirrored'] and canonical < 5 else canonical), 'Invalid helper/final/replay evidence')
    executed = bool(new and enabled and canonical == geo.SAP)
    require(event['executed_additional'] == executed, 'Wrong additional-SAP attribution')
    if canonical == geo.SAP:
        dx, dy = event['sap'][:2]
        if event['mirrored']: dx, dy = geo.mirror_delta(dx, dy)
        require(actual and native == [geo.SAP, dx, dy] and event['sap_identity_preserved'] is True,
                'Final SAP lacks matching helper permission/object/coordinates')
    else:
        require(native[1:] == [0, 0] and event['sap_identity_preserved'] is False,
                'Canceled SAP has inconsistent final evidence')
    return dict(helper_calls=1, new_permissions=int(new), actual_new_permissions=int(new and enabled),
        executed_additional_saps=int(executed), canceled_additional_saps=int(new and enabled and not executed),
        checked_helper_replay=1)


def _event_bytes(event):
    return json.dumps(event, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'


@contextmanager
def artillery_audit(agent, append):
    """Temporary instance-only hooks; return the actual helper answer unchanged.

    The final damage-planning boundary verifies SAP object identity, then native
    coordinates and the real replay ring write establish execution. Later safety
    cancellations count separately. Full contexts are hashed, never retained.
    """
    cfg = agent.cfg.to_dict()
    validate_source_config(dict(cfg, art_splash_in_training=False))
    require(agent.training and cfg['rules_in_training_all'] and cfg['rules_in_training'],
            'Observer requires the fixed training rules')
    enabled = cfg['art_splash_in_training']
    missing = object()
    names = ('_artillery_ok', '_plan_damage', 'act', 'update')
    prior = {name: agent.__dict__.get(name, missing) for name in names}
    original = {name: getattr(agent, name) for name in names}
    pending, events = [], {}
    proof, digest = empty_exposure(), hashlib.sha256()

    def helper(ctx, uid, sap):
        uid = int(uid)
        require(not pending and uid not in events and agent.training
            and agent.cfg.to_dict() == cfg and int(agent._prev_actions[uid]) < geo.SAP,
            'Ambiguous/noneligible artillery helper invocation')
        before = helper_state(agent, ctx, sap)
        try:
            actual = original['_artillery_ok'](ctx, uid, sap)
            require(before == helper_state(agent, ctx, sap), 'Actual helper mutated its read-only inputs/RNG')
            agent.cfg.art_splash_in_training = not enabled
            alternate_before = helper_state(agent, ctx, sap)
            alternate = original['_artillery_ok'](ctx, uid, sap)
            require(alternate_before == helper_state(agent, ctx, sap), 'Alternate helper mutated inputs/RNG')
        finally:
            agent.cfg.art_splash_in_training = enabled
        after = helper_state(agent, ctx, sap)
        require(before == after and type(actual) in (bool, np.bool_) and type(alternate) in (bool, np.bool_),
                'Helper observation did not restore state/boolean contract')
        baseline, aligned = (alternate, actual) if enabled else (actual, alternate)
        events[uid] = dict(step=int(ctx['step']), uid=uid, pre_action=int(agent._prev_actions[uid]),
            sap=[int(x) for x in sap], baseline=bool(baseline), aligned=bool(aligned), actual=bool(actual),
            new_permission=bool(not baseline and aligned), mirrored=bool(agent.belief.mirrored),
            input_sha256=before, restored_sha256=after, readonly_checks=2,
            sap_identity_preserved=False, _sap_object=sap)
        return actual

    def damage(ctx, uid, sap, planned):
        event = events.get(int(uid))
        if event is not None:
            require(event['actual'] and sap is event['_sap_object'], 'Final SAP object differs from eligible helper')
            event['sap_identity_preserved'] = True
        return original['_plan_damage'](ctx, uid, sap, planned)

    def act(*args, **kwargs):
        require(not pending and not events, 'Previous action lacks completed replay evidence')
        actions = original['act'](*args, **kwargs)
        order = list(agent._prev_feats)
        for uid, event in events.items():
            require(uid in order, 'Helper unit absent from acted/replay units')
            canonical = int(agent._prev_actions[uid])
            event.update(native_action=[int(v) for v in actions[uid]], canonical_action=canonical,
                executed_additional=bool(enabled and event['new_permission'] and canonical == geo.SAP))
            if canonical == geo.SAP:
                require(int(agent._sap_hits[uid]) == event['sap'][2], 'Final SAP target estimate changed')
        pending.append((np.array(actions, copy=True), order))
        return actions

    def update(*args, **kwargs):
        require(len(pending) == 1, 'Replay update without unique action')
        actions, order = pending[0]
        actual = kwargs.get('action', args[3] if len(args) > 3 else None)
        require(actual is not None and np.array_equal(actual, actions), 'Update changed native actions')
        position = agent.buffer.pos
        result = original['update'](*args, **kwargs)
        require(agent.buffer.pos == (position + len(order)) % agent.buffer.capacity, 'Replay count changed')
        for uid, event in events.items():
            event.pop('_sap_object')
            event['replay_action'] = int(agent.buffer.a[(position + order.index(uid)) % agent.buffer.capacity])
            counts = validate_event(event, enabled)
            for key, value in counts.items(): proof[key] += value
            digest.update(_event_bytes(event))
            append(event)
        events.clear(); pending.clear()
        return result

    for name, hook in zip(names, (helper, damage, act, update)): setattr(agent, name, hook)
    try:
        yield proof
        require(not pending and not events, 'Unfinished helper/action/replay evidence')
    finally:
        for name, value in prior.items():
            if value is missing: agent.__dict__.pop(name, None)
            else: setattr(agent, name, value)
        agent.cfg.art_splash_in_training = enabled
        proof['transcript_sha256'] = digest.hexdigest()


def _prefill_summary(arm, entry, initial, prefill, rows):
    """Admit a full, gradient-free prefill; trajectories may differ across roles."""
    il, pl = initial['learning'], prefill['learning']
    require([{k:r[k] for k in PLAN_KEYS} for r in rows] == rollout_plan(arm)[:40]
        and initial['q_tensor_sha256'] == initial['target_tensor_sha256'] == entry['tensor_sha256']
        and il['config'] == pl['config'] == entry['config']
        and il['env_steps'] == 60000 and il['learn_steps'] == pl['learn_steps'] == 0
        and not il['replay']['size'] and not il['replay']['pos'] and il['replay']['_mask_dim'] == 1
        and not il['recent_losses'] and not pl['recent_losses']
        and il['learn_enabled'] is True and pl['learn_enabled'] is False
        and pl['env_steps'] == 72120 and pl['replay']['size'] > entry['config']['learn_start'],
        'Prefill chronology/fresh initial state/replay differs')
    for index, row in enumerate(rows): _validate_rollout(row, index, entry)
    proof = dict(status='prefill_ready', arm=arm, run_seed=entry['run_seed'], component_index=18,
        actual_prefill_games=len(rows), learn_steps=pl['learn_steps'], config=entry['config'],
        initial_tensor_sha256=entry['tensor_sha256'], initial_optimizer_sha256=il['optimizer_sha256'],
        initial_agent_rng_sha256=initial['agent_rng_sha256'], initial_global_rng_sha256=initial['global_rng_sha256'],
        schedule_sha256=experiment.state_sha256(entry['rollout_plan']), replay_size=pl['replay']['size'],
        unchanged_q=initial['q_tensor_sha256'] == prefill['q_tensor_sha256'],
        unchanged_target=initial['target_tensor_sha256'] == prefill['target_tensor_sha256'],
        unchanged_optimizer=il['optimizer_sha256'] == pl['optimizer_sha256'],
        new_permissions=sum(row['artillery_audit']['new_permissions'] for row in rows),
        executed_additional_saps=sum(row['artillery_audit']['executed_additional_saps'] for row in rows))
    require(all(proof[k] for k in ('unchanged_q', 'unchanged_target', 'unchanged_optimizer')),
            'Prefill changed learning state')
    # A zero-effect aligned prefill is preserved and presented to the supervisor,
    # which rejects the pair before either worker can enable gradients.
    return proof


def _validate_rollout(row, index, entry):
    actions, exposure = row['action_audit'], row['artillery_audit']
    expected = entry['rollout_plan'][index]
    training = index >= 40
    require({k:row[k] for k in PLAN_KEYS} == expected and row['steps'] == 303
        and row['point_counting_version'] == 2 and row['env_steps'] == 60000+(index+1)*303
        and row['learn_steps'] == max(0,index+1-40)*150 and row['updates'] == (150 if training else 0)
        and row['rollout_config_id'] == experiment.state_sha256(entry['config'])
        and actions['act_calls'] == actions['update_calls'] == 303
        and actions['checked_replay_transitions'] >= exposure['checked_helper_replay']
        and exposure['helper_calls'] == exposure['checked_helper_replay']
        and exposure['actual_new_permissions'] == exposure['executed_additional_saps']+exposure['canceled_additional_saps']
        and exposure['actual_new_permissions'] == (exposure['new_permissions'] if entry['config']['art_splash_in_training'] else 0)
        and all(type(exposure[k]) is int and exposure[k] >= 0 for k in EVENT_COUNTS)
        and exposure['new_permissions'] <= exposure['helper_calls']
        and len(exposure['transcript_sha256']) == len(actions['transcript_sha256']) == 64,
        'Rollout/action/exposure chronology differs from fixed recipe')


def validate_prefill_bundle(directory, prepared, arm):
    directory, prepared = Path(directory), Path(prepared)
    proof = json.loads((directory/'prefill_proof.json').read_text())
    require(file_sha256(directory/'prefill_bundle.json') == proof.get('bundle_sha256')
        and file_sha256(directory/'prefill_events.jsonl') == proof.get('events_sha256'),
        'Prefill raw evidence changed')
    bundle = json.loads((directory/'prefill_bundle.json').read_text())
    entry = json.loads((prepared/'manifest.json').read_text())['arms'][arm]
    require(bundle['arm'] == arm and bundle['entry'] == entry, 'Prefill bound to wrong prepared arm')
    counts = [empty_exposure() for _ in range(40)]
    digests = [hashlib.sha256() for _ in range(40)]
    previous = (-1, -1)
    seen = set()
    with (directory/'prefill_events.jsonl').open() as stream:
        for line in stream:
            raw = json.loads(line); index, event = raw['rollout_index'], raw['event']
            key = (index, event['step'])
            unique = (*key, event['uid'])
            require(type(index) is int and 0 <= index < 40 and 0 <= event['step'] < 303
                and key >= previous and unique not in seen, 'Unordered/duplicate/out-of-plan helper evidence')
            previous = key; seen.add(unique)
            values = validate_event(event, entry['config']['art_splash_in_training'])
            for name, value in values.items(): counts[index][name] += value
            digests[index].update(_event_bytes(event))
    for index, row in enumerate(bundle['rows']):
        require(row['artillery_audit'] == dict(counts[index], transcript_sha256=digests[index].hexdigest()),
                'Prefill exposure counts/digests differ from raw final-action/replay records')
    expected = _prefill_summary(arm, entry, bundle['initial'], bundle['prefill'], bundle['rows'])
    require(proof == dict(expected, bundle_sha256=file_sha256(directory/'prefill_bundle.json'),
        events_sha256=file_sha256(directory/'prefill_events.jsonl')), 'Prefill summary differs from raw evidence')
    return proof


def compare_prefill_proofs(control, aligned, seed):
    require(seed in (43,44), 'Unknown paired start')
    for proof, role, enabled in ((control,'control',False),(aligned,'aligned',True)):
        expected = dict(status='prefill_ready', arm=f'{role}{seed}', run_seed=seed, component_index=18,
            actual_prefill_games=40, learn_steps=0, unchanged_q=True, unchanged_target=True, unchanged_optimizer=True)
        require(all(proof.get(k) == v for k,v in expected.items())
            and proof['config']['art_splash_in_training'] is enabled
            and proof['replay_size'] > proof['config']['learn_start'], 'Invalid paired prefill')
    shared = ('initial_tensor_sha256','initial_optimizer_sha256','initial_agent_rng_sha256',
              'initial_global_rng_sha256','schedule_sha256')
    require(all(control[k] == aligned[k] for k in shared)
        and control['schedule_sha256'] == experiment.state_sha256(rollout_plan(f'control{seed}'))
        and dict(control['config'],art_splash_in_training=True) == aligned['config']
        and control['executed_additional_saps'] == 0
        and 0 < aligned['executed_additional_saps'] <= aligned['new_permissions'],
        'Paired start/config differs or aligned prefill has no executed additional SAP; stop, no extension')
    return dict(status='matched', run_seed=seed, eligible=False,
        initial_evidence={k:control[k] for k in shared},
        executed_additional_saps=aligned['executed_additional_saps'],
        note='Common initial state/schedule only; trajectories and replay may diverge')


def wait_prefill(supervisor_state, arm, check):
    state = json.loads(Path(supervisor_state).read_text())
    seed, _ = _arm(arm)
    path = Path(state['out'])/f'paired_prefill_{seed}.json'
    while not path.exists():
        check(); time.sleep(1)
    result = json.loads(path.read_text())
    require(result.get('status') == 'matched' and result.get('run_seed') == seed,
            'Supervisor did not admit paired prefill')
    # Bind the actual gate to both still-frozen raw prefill proofs, not just a status flag.
    from scripts.artillery_alignment_supervisor import run_name
    proofs = [validate_prefill_bundle(ROOT/'experiments/runs'/run_name(f'{role}{seed}'),
        state['prepared'], f'{role}{seed}') for role in ('control','aligned')]
    expected = compare_prefill_proofs(*proofs, seed)
    require(all(result.get(k) == v for k,v in expected.items()), 'Paired gate differs from raw proof')
    check()


def run_arm(prepared, arm, name, *, supervisor_state):
    """One supervisor-owned learner, exact finetune schedule, no model selection."""
    from scripts.artillery_alignment_supervisor import worker_guard
    require(name and name not in ('.','..') and Path(name).name == name, 'Single new run name required')
    destination = _safe_output(experiment.RUNS/name)
    if destination.exists(): raise FileExistsError(destination)
    manifest, entry, init = check_prepared(prepared, arm)
    stop = []
    old_signals = {sig:signal.getsignal(sig) for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP)}
    missing = object(); old_variant = VARIANTS.get(VARIANT,missing)
    env = None; files = []; learners = None
    rows, validations = [], []
    audit = dict(schema_version=1, arm=arm, source_config=manifest['source_config'],
        training_config=entry['config'], validations=[])
    record = dict(schema_version=1, status='running', eligible=False, arm=arm, name=name,
        prepared=str(Path(prepared).resolve()), pins=manifest['pins'], source_sha256=SOURCE_SHA,
        component_index=18, run_seed=entry['run_seed'], config=entry['config'], started_at=time.time())

    def check():
        require(not stop, 'Signal requested stop at completed-game boundary')
        worker_guard(supervisor_state, arm, name, prepared)

    def persist():
        record.update(actual_prefill_games=sum(r['phase']=='prefill' for r in rows),
            actual_train_games=sum(r['phase']=='train' for r in rows), actual_validation_games=len(validations),
            updated_at=time.time())
        if learners is not None:
            agent = _canonical(learners)
            record.update(env_steps=agent.env_steps,learn_steps=agent.learn_steps)
        _write(destination/'progress.json',record)
        _write(destination/'training_audit.json',audit)

    def append(stream, value):
        stream.write(json.dumps(value,allow_nan=False)+'\n');stream.flush()

    def validate(after):
        check(); before = learner_identity(learners); completed = []
        try:
            result = validate_v14(env, learners, range(9_600_000,9_600_004), ('default','solution92'),
                manifest['source_config'], completed_rows=completed, stop_check=check)
        finally:
            for row in completed:
                evidence = dict(row,after_games=after);validations.append(evidence);append(files[1],evidence)
            persist()
        require([{k:r[k] for k in ('after_games','opponent','seed','side')} for r in validations[-16:]]
            == [r for r in validation_plan() if r['after_games']==after]
            and len(result)==16 and all(r['steps']==303 and r['point_counting_version']==2 for r in result)
            and learner_identity(learners)==before, 'Validation schedule or isolated learning/RNG state differs')
        audit['validations'].append(dict(after_games=after,before=before,after=learner_identity(learners),
            config=manifest['source_config']))
        persist();check()

    check()
    (destination/'weights').mkdir(parents=True,exist_ok=False)
    shutil.copyfile(init/'weights/agent.pth',destination/'weights/agent.pth')
    _write(destination/'manifest.json',dict(record,entry=entry,selection='final only',settings=SETTINGS))
    try:
        for sig in old_signals: signal.signal(sig,lambda *_:stop.append(True))
        experiment.limit_threads()
        seed_everything(entry['run_seed'])
        VARIANTS[VARIANT] = ('sherlock',entry['config'])
        learners = experiment.Learners(VARIANT,destination,entry['run_seed'],load=True)
        learners.train_mode(); agent = _canonical(learners)
        audit['initial'] = prove_initial(learners,entry)
        agent.learn_enabled = False
        from luxai_s3.wrappers import LuxAIS3GymEnv
        env = LuxAIS3GymEnv(numpy_output=True)
        files = [(destination/f).open('x') for f in ('rollouts.jsonl','validation_games.jsonl',
            'prefill_events.jsonl','train.csv')]
        writer=csv.DictWriter(files[3],fieldnames=experiment.TRAIN_FIELDS);writer.writeheader()
        persist()
        for index, plan in enumerate(entry['rollout_plan']):
            check()
            training = plan['phase']=='train'
            require(agent.training and agent.learn_enabled is training and agent.cfg.to_dict()==entry['config']
                and abs(agent.epsilon-.05)<1e-12 and not agent.autosave_on_terminate,
                'Actual rollout learner differs from fixed training recipe')
            opponent = common.make_opponent(plan['opponent'],'player_1' if plan['side']=='player_0' else 'player_0')
            def observed(event):
                if not training: append(files[2],dict(rollout_index=index,event=event))
            before = agent.learn_steps
            with action_audit(agent) as actions, artillery_audit(agent,observed) as exposure:
                row = common.play_game(env,agent,opponent,plan['seed'],plan['side'],train=True)
            row.update(plan,env_steps=agent.env_steps,learn_steps=agent.learn_steps,
                updates=agent.learn_steps-before, action_audit=actions, artillery_audit=exposure,
                rollout_config_id=experiment.state_sha256(entry['config']))
            _validate_rollout(row,index,entry)
            if training:
                row.update(epsilon=round(agent.epsilon,4), mean_loss=round(agent.pop_mean_loss(),5),
                    winrate_50=round(float(np.mean([r['result'] for r in rows[40:][-49:]]+[row['result']])),4))
                require(math.isfinite(row['mean_loss']), 'Nonfinite training loss')
                writer.writerow({k:row.get(k) for k in experiment.TRAIN_FIELDS});files[3].flush()
            rows.append(row);append(files[0],row);persist();check()
            if index == 39:
                audit['prefill'] = learner_identity(learners)
                _prove_prefill(audit['prefill'],audit['initial'],agent)
                proof = _prefill_summary(arm,entry,audit['initial'],audit['prefill'],rows)
                _write(destination/'prefill_bundle.json',dict(arm=arm,entry=entry,
                    initial=audit['initial'],prefill=audit['prefill'],rows=rows))
                proof.update(bundle_sha256=file_sha256(destination/'prefill_bundle.json'),
                    events_sha256=file_sha256(destination/'prefill_events.jsonl'))
                persist();_write(destination/'prefill_proof.json',proof)
                wait_prefill(supervisor_state,arm,check)
                agent.learn_enabled = True
                validate(0)
        validate(400)
        check();_check_frozen(manifest)
        require(len(rows)==440 and len(validations)==32 and agent.learn_steps==60000,
                'Incomplete fixed study arm')
        learners.save();learners.save_buffers()
        audit['end'] = _prove_end(learners,entry,audit['initial'],destination/'weights/agent.pth',rows)
        record.update(status='done',finished_at=time.time());persist()
        receipt = dict(record, initial_tensor_sha256=entry['tensor_sha256'],
            artifacts={name:file_sha256(destination/name) for name in RECEIPT_FILES})
        path = destination/'final_receipt.json'
        _write(path,receipt)
        try: validate_final_receipt(path,arm=arm)
        except BaseException:
            path.unlink();raise
        return receipt
    except BaseException as exc:
        record.update(status='incomplete',error=f'{type(exc).__name__}: {exc}')
        persist();raise
    finally:
        for stream in files: stream.close()
        if env is not None: env.close()
        if old_variant is missing: VARIANTS.pop(VARIANT,None)
        else: VARIANTS[VARIANT] = old_variant
        for sig,handler in old_signals.items(): signal.signal(sig,handler)


RECEIPT_FILES = ('weights/agent.pth','weights/agent.buffer.npz','rollouts.jsonl',
    'validation_games.jsonl','training_audit.json','train.csv','prefill_proof.json',
    'prefill_bundle.json','prefill_events.jsonl')


def validate_final_receipt(path, *, arm=None):
    path = Path(path).resolve(strict=True)
    receipt = json.loads(path.read_text());actual_arm = receipt.get('arm');_arm(actual_arm)
    expected = dict(schema_version=1,status='done',eligible=False,source_sha256=SOURCE_SHA,
        component_index=18,actual_prefill_games=40,actual_train_games=400,actual_validation_games=32,
        env_steps=193320,learn_steps=60000)
    require(all(receipt.get(k)==v for k,v in expected.items()) and (arm is None or actual_arm==arm),
            'Receipt is not a complete production arm')
    directory = path.parent
    manifest,entry,_ = check_prepared(receipt['prepared'],actual_arm)
    require(receipt.get('config')==entry['config'] and receipt.get('pins')==manifest['pins']
        and receipt.get('initial_tensor_sha256')==entry['tensor_sha256']
        and receipt.get('run_seed')==entry['run_seed'], 'Receipt is not bound to prepared inputs/config')
    require(receipt.get('artifacts')=={name:file_sha256(directory/name) for name in RECEIPT_FILES},
            'Receipt raw artifacts changed')
    validate_prefill_bundle(directory,receipt['prepared'],actual_arm)
    rows=[json.loads(line) for line in (directory/'rollouts.jsonl').read_text().splitlines()]
    validations=[json.loads(line) for line in (directory/'validation_games.jsonl').read_text().splitlines()]
    require(len(rows)==440 and [{k:r[k] for k in ('after_games','opponent','seed','side')} for r in validations]
        ==validation_plan() and all(r['steps']==303 and r['point_counting_version']==2 for r in validations),
        'Incomplete fixed rollout/validation schedule')
    for index,row in enumerate(rows): _validate_rollout(row,index,entry)
    bundle=json.loads((directory/'prefill_bundle.json').read_text())
    require(rows[:40]==bundle['rows'], 'Full chronology differs from admitted raw prefill')
    audit=json.loads((directory/'training_audit.json').read_text())
    require(audit['initial']==bundle['initial'] and audit['prefill']==bundle['prefill'], 'Initial/prefill audit changed')
    _validate_end(directory,receipt,entry,audit)
    require([v['after_games'] for v in audit['validations']]==[0,400], 'Missing initial/final validations')
    for val in audit['validations']:
        learning=val['before']['learning']
        require(val['before']==val['after'] and val['config']==manifest['source_config']
            and learning['config']==entry['config'] and learning['learn_enabled'] is True
            and learning['env_steps']==72120+val['after_games']*303
            and learning['learn_steps']==val['after_games']*150, 'Validation changed learning/RNG/config')
    with (directory/'train.csv').open() as stream: csv_rows=list(csv.DictReader(stream))
    require(len(csv_rows)==400, 'Incomplete training CSV')
    for index,row in enumerate(csv_rows):
        raw=rows[40+index]
        require(all(str(raw[k])==row[k] for k in experiment.TRAIN_FIELDS)
            and float(row['epsilon'])==.05 and math.isfinite(float(row['mean_loss'])),
            'Training CSV differs from exact raw chronology/finite loss')
    return receipt


def _validate_end(directory, receipt, entry, audit):
    cp=torch.load(directory/'weights/agent.pth',map_location='cpu',weights_only=True);_finite(cp)
    end=audit['end']
    require(cp.get('cfg')==entry['config'] and not cp.get('ensemble') and not cp.get('ensemble_dims')
        and cp.get('feature_dim')==79 and cp.get('n_actions')==6
        and cp.get('learn_steps')==60000 and cp.get('env_steps')==193320 and cp.get('opt',{}).get('state')
        and end.get('reload_verified') is True
        and tensor_sha256(cp['q'])!=entry['tensor_sha256']
        and tensor_sha256(cp['target_q'])!=entry['tensor_sha256']
        and experiment.state_sha256(cp['opt'])!=audit['initial']['learning']['optimizer_sha256']
        and tensor_sha256(cp['q'])==end['q_tensor_sha256']
        and tensor_sha256(cp['target_q'])==end['target_tensor_sha256']
        and experiment.state_sha256(cp['opt'])==end['learning']['optimizer_sha256']
        and len(cp['opt']['state'])==len(cp['q'])
        and all(set(state)=={'step','exp_avg','exp_avg_sq'} and state['step'].item()==60000
                for state in cp['opt']['state'].values())
        and all(group['lr']==entry['config']['lr'] for group in cp['opt']['param_groups'])
        and end['learning']['config']==entry['config']
        and end['learning']['env_steps']==193320 and end['learning']['learn_steps']==60000
        and end['saved_weights_sha256']==receipt['artifacts']['weights/agent.pth'],
        'Missing finite changed Q/target/Adam and saved/reloaded final proof')


def main():
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands=parser.add_subparsers(dest='command',required=True)
    prep=commands.add_parser('prepare')
    prep.add_argument('--source',type=Path,default=ROOT/'agents/sherlock/weights/agent_p0.pth')
    prep.add_argument('--out',type=Path,required=True)
    run=commands.add_parser('run')
    run.add_argument('--prepared',type=Path,required=True);run.add_argument('--arm',choices=tuple(ARMS),required=True)
    run.add_argument('--name',required=True);run.add_argument('--supervisor-state',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='prepare':
        result=prepare(args.source,args.out);print(json.dumps(dict(prepared=str(args.out),arms=list(result['arms']))))
    else: print(json.dumps(run_arm(args.prepared,args.arm,args.name,supervisor_state=args.supervisor_state)))


if __name__=='__main__': main()
