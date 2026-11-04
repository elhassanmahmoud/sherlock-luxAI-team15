"""Matched final-only student RL arms with signed SAP diagnostics; no promotion.

prepare consumes only the exported student checkpoint contract. runarm reuses
finetune in one process. Partial runs never receive a final receipt.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import shutil
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet
from scripts import experiment
from scripts.final_rescue_train import action_audit
from scripts.night_train_pilot import file_sha256, tensor_sha256
from scripts.output_paths import checked_output
from scripts.targeting_adapt import (_canonical, _finite, _prove_end, _prove_prefill,
                                     learner_identity, prove_initial)
from scripts.variants import VARIANTS, seed_everything

ROOT = Path(__file__).resolve().parent.parent
PRIMARY = Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15')
PROTECTED_DIRS = (ROOT / 'agents/sherlock/weights', ROOT / 'Gruppe15',
                  PRIMARY / 'agents/sherlock/weights', PRIMARY / 'Gruppe15')
ARMS = ('control', 'sap0')
PREFILL, TRAIN, RUN_SEED, OFFSET = 40, 160, 29, 3000
MIX = 'solution92=0.6,sol92_sq=0.2,default=0.1,rush=0.1'
VARIANT = 'student_reward_20261104'
EVAL_SEED = 20261104


def _write(path, value):
    path = Path(path)
    data = json.dumps(value, indent=2, allow_nan=False) + '\n'
    temp = None
    try:
        # Both arm workers may publish the same paired-prefill proof. Each
        # writer owns its own same-filesystem staging file before atomic replace.
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         prefix=f'.{path.name}.', suffix='.tmp',
                                         dir=path.parent, delete=False) as handle:
            temp = Path(handle.name)
            handle.write(data)
        temp.replace(path)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def _output(path):
    for protected in PROTECTED_DIRS:
        path = checked_output(path, protected)
    return path


def _protected_hashes():
    paths = set()
    for directory in PROTECTED_DIRS:
        if directory.exists():
            paths.update(p.resolve() for p in directory.rglob('*') if p.is_file())
    for base in (ROOT, PRIMARY):
        paths.update(p.resolve() for p in base.glob('*.zip') if p.is_file())
    return {str(p): file_sha256(p) for p in sorted(paths)}


def _pins():
    names = ('scripts/student_reward_train.py', 'scripts/finetune.py',
             'scripts/experiment.py', 'scripts/final_rescue_train.py',
             'scripts/targeting_adapt.py', 'scripts/variants.py', 'scripts/common.py',
             'agents/sherlock/main.py', 'agents/sherlock/config.py',
             'agents/sherlock/reward.py', 'agents/sherlock/model.py')
    dependencies = set(names)
    dependencies.update(str(p.relative_to(ROOT)) for directory in
                        ('agents/sherlock', 'agents/default', 'agents/Solution_92_Kaggle')
                        for p in (ROOT / directory).rglob('*.py'))
    dependencies.update(('scripts/style_opponents.py', 'scripts/scoring.py',
                         'scripts/metrics.py', 'scripts/protocol.py'))
    return dict(code={n: file_sha256(ROOT / n) for n in sorted(dependencies)},
                interpreter=str(Path(sys.executable).resolve()),
                protected=_protected_hashes())


def _student(path):
    cp = torch.load(path, map_location='cpu', weights_only=True)
    fields = {'q', 'target_q', 'cfg', 'feature_dim', 'n_actions', 'ensemble',
              'ensemble_dims', 'env_steps', 'learn_steps'}
    provenance = {'distillation_updates', 'distillation_epochs', 'distillation_seed'}
    if (not isinstance(cp, dict) or not fields <= set(cp)
            or set(cp) - fields not in (set(), provenance) or cp['feature_dim'] != 79
            or cp['n_actions'] != 6 or cp['ensemble'] or cp['ensemble_dims']
            or cp['env_steps'] != 60000 or cp['learn_steps'] != 0):
        raise ValueError('Student contract requires a single final network without optimizer/replay')
    if provenance <= set(cp) and any(type(cp[name]) is not int or cp[name] < minimum
                                    for name, minimum in (
                                        ('distillation_updates', 1), ('distillation_epochs', 1),
                                        ('distillation_seed', 0))):
        raise ValueError('Student distillation provenance requires valid integer counts/seed')
    cfg = AgentConfig(**cp['cfg']).to_dict()
    if (cfg != cp['cfg'] or cfg['hidden'] != 512 or not cfg['canonical']
            or not cfg['use_shaping'] or cfg['eps_end'] != .05
            or cfg['eps_decay_steps'] != 60000 or cfg['learn_start'] != 5000
            or cfg['train_every'] != 2):
        raise ValueError('Student config violates fixed learner contract')
    _finite(cp)
    if tensor_sha256(cp['q']) != tensor_sha256(cp['target_q']):
        raise ValueError('Distilled student q/target must be identical')
    with torch.random.fork_rng(devices=[]):
        QNet(79, 6, hidden=512, dueling=cfg['dueling']).load_state_dict(cp['q'], strict=True)
    return cp


def _config(source, arm):
    if arm not in ARMS:
        raise ValueError('Unknown reward arm')
    result = dict(source, frozen=False, lr=1e-4, rules_in_training=True,
                  rules_in_training_all=True)
    if arm == 'sap0':
        result['w_sap_hit'] = 0.
    return result


def rollout_plan():
    rng = np.random.default_rng(RUN_SEED + OFFSET)
    names = ['solution92', 'sol92_sq', 'default', 'rush']
    return [dict(phase=phase, game=g, seed=200000 + RUN_SEED * 10000 + offset + g // 2,
                 side=('player_0', 'player_1')[g % 2],
                 opponent=names[rng.choice(4, p=[.6, .2, .1, .1])])
            for phase, count, offset in (('prefill', PREFILL, 5000), ('train', TRAIN, OFFSET))
            for g in range(count)]


def validation_plan():
    return [dict(after_games=after, opponent=opp, seed=seed, side=side)
            for after in (0, TRAIN) for opp in ('default', 'solution92')
            for seed in range(500000, 500004) for side in ('player_0', 'player_1')]


def prepare(student: Path, out: Path):
    student = Path(student).resolve(strict=True)
    out = _output(out)
    if out.exists():
        raise FileExistsError(out)
    before = file_sha256(student)
    cp = _student(student)
    if cp['cfg']['w_sap_hit'] == 0:
        raise ValueError('Control SAP weight must be nonzero for the ablation')
    manifest = dict(schema_version=1, student=str(student), student_sha256=before,
                    source_config=cp['cfg'], pins=_pins(), arms={},
                    validation_plan=validation_plan())
    for arm in ARMS:
        cfg = _config(cp['cfg'], arm)
        init = out / 'init' / arm
        (init / 'weights').mkdir(parents=True, exist_ok=False)
        checkpoint = copy.deepcopy(cp)
        checkpoint['cfg'] = cfg
        path = init / 'weights/agent.pth'
        torch.save(checkpoint, path)
        entry = dict(config=cfg, run_seed=RUN_SEED, tensor_sha256=tensor_sha256(cp['q']),
                     weights_sha256=file_sha256(path), rollout_plan=rollout_plan())
        manifest['arms'][arm] = entry
        _write(init / 'manifest.json', dict(variant=VARIANT, base_variant=VARIANT,
                                          train_games=0, arm=arm, **entry))
    if file_sha256(student) != before or manifest['pins'] != _pins():
        raise ValueError('Input/protected/code hashes changed during prepare')
    _write(out / 'manifest.json', manifest)
    return manifest


def check_prepared(prepared, arm):
    if arm not in ARMS:
        raise ValueError('Unknown reward arm')
    prepared = _output(Path(prepared).resolve(strict=True))
    manifest = json.loads((prepared / 'manifest.json').read_text())
    source = Path(manifest['student'])
    if file_sha256(source) != manifest['student_sha256']:
        raise ValueError('Student hash changed')
    cp = _student(source)
    if (manifest['pins'] != _pins() or manifest['source_config'] != cp['cfg']
            or manifest['validation_plan'] != validation_plan() or set(manifest['arms']) != set(ARMS)):
        raise ValueError('Prepared input/protected/code/config/plan changed')
    for name in ARMS:
        entry = manifest['arms'][name]
        init = prepared / 'init' / name
        path = init / 'weights/agent.pth'
        expected = dict(config=_config(cp['cfg'], name), run_seed=RUN_SEED,
                        tensor_sha256=tensor_sha256(cp['q']),
                        weights_sha256=file_sha256(path), rollout_plan=rollout_plan())
        if (entry != expected or {p.name for p in (init / 'weights').iterdir()} != {'agent.pth'}
                or json.loads((init / 'manifest.json').read_text()) != dict(
                    variant=VARIANT, base_variant=VARIANT, train_games=0, arm=name, **entry)):
            raise ValueError('Prepared init/config/weights changed or replay present')
        saved = torch.load(path, map_location='cpu', weights_only=True)
        want = dict(cp, cfg=expected['config'])
        if experiment.state_sha256(saved) != experiment.state_sha256(want):
            raise ValueError('Init is not exact fresh student without optimizer/replay')
    return manifest, manifest['arms'][arm], prepared / 'init' / arm


@contextmanager
def reward_audit(original_weight):
    """Observe original and zero-weight rewards on the exact same arguments.

    The original signed SAP formula penalizes misses too. This binding affects
    only the actual cfg's reward; neither counterfactual advances state or RNG.
    """
    from agents.sherlock import main
    from agents.sherlock.reward import _on_owned_point_tile
    original = main.unit_rewards
    proof = dict(calls=0, transitions=0, sap_transitions=0, estimated_positive_hits=0,
                 estimated_misses=0, removed_signed=0., removed_absolute=0.,
                 positive_to_nonpositive=0, actual_reward=0., owned_point_unit_steps=0)

    def measured(cfg, ctx, next_ctx, actions, sap_hits):
        baseline = copy.copy(cfg)
        baseline.w_sap_hit = original_weight
        zero = copy.copy(cfg)
        zero.w_sap_hit = 0.
        positive, absent = original(baseline, ctx, next_ctx, actions, sap_hits), original(zero, ctx, next_ctx, actions, sap_hits)
        actual = original(cfg, ctx, next_ctx, actions, sap_hits)
        proof['calls'] += 1
        for uid in positive:
            sap = actions.get(uid) == geo.SAP
            hits = sap_hits.get(uid, 0)
            expected = original_weight * (1. if hits > 0 else -1.) * max(1, hits) if sap and cfg.use_shaping else 0.
            removed = positive[uid] - absent[uid]
            if (not all(math.isfinite(x) for x in (positive[uid], absent[uid], actual[uid]))
                    or not math.isclose(removed, expected, abs_tol=1e-8, rel_tol=1e-8)):
                raise ValueError('Signed SAP counterfactual identity failed/nonfinite reward')
            proof['transitions'] += 1
            proof['actual_reward'] += actual[uid]
            proof['removed_signed'] += removed
            proof['removed_absolute'] += abs(removed)
            proof['sap_transitions'] += int(sap)
            proof['estimated_positive_hits'] += int(sap and hits > 0)
            proof['estimated_misses'] += int(sap and hits <= 0)
            proof['positive_to_nonpositive'] += int(sap and positive[uid] > 0 and absent[uid] <= 0)
            proof['owned_point_unit_steps'] += int(_on_owned_point_tile(next_ctx, uid, cfg.reward_fix) == 1)
        return actual
    main.unit_rewards = measured
    try:
        yield proof
    finally:
        main.unit_rewards = original


def _deadline(value):
    date = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace('Z', '+00:00'))
    if date.tzinfo is None:
        raise ValueError('Deadline must include UTC offset')
    return date.astimezone(timezone.utc)


def _check_deadline(deadline):
    if datetime.now(timezone.utc) >= deadline:
        raise TimeoutError('Fixed training deadline reached; incomplete arm')


@contextmanager
def _act_deadline(agent, deadline, proof=None):
    missing = object()
    prior = vars(agent).get('act', missing)
    original = agent.act
    digest = hashlib.sha256()
    def act(*args, **kwargs):
        _check_deadline(deadline)
        actions = original(*args, **kwargs)
        if proof is not None:
            # Include all SAP coordinates and observed feature vectors, not
            # only the six-valued direction recorded in the replay buffer.
            digest.update(experiment.state_sha256(dict(
                actions=np.asarray(actions), features=agent._prev_feats)).encode())
        return actions
    agent.act = act
    try:
        yield
    finally:
        if proof is not None:
            proof['action_state_sha256'] = digest.hexdigest()
        if prior is missing:
            vars(agent).pop('act', None)
        else:
            agent.act = prior


def _isolated_validation(env, learners, seeds, opponents, deadline, completed):
    a = _canonical(learners)
    rng = copy.deepcopy(a.rng.bit_generator.state)
    global_rng = experiment._global_rng_state()
    enabled = a.learn_enabled
    original = experiment.play_game
    def game(*args, **kwargs):
        _check_deadline(deadline)
        with _act_deadline(a, deadline):
            row = original(*args, **kwargs)
        completed.append(row)
        return row
    try:
        a.learn_enabled = False
        a.rng.bit_generator.state = np.random.default_rng(EVAL_SEED).bit_generator.state
        seed_everything(EVAL_SEED)
        experiment.play_game = game
        return experiment.run_validation(env, learners, seeds, opponents, isolate=True)
    finally:
        experiment.play_game = original
        a.learn_enabled = enabled
        a.rng.bit_generator.state = rng
        experiment._restore_global_rng(global_rng)


def run_arm(prepared, arm, deadline_utc):
    from scripts import finetune
    deadline = _deadline(deadline_utc)
    manifest, entry, init = check_prepared(prepared, arm)
    prepared = Path(prepared).resolve()
    destination = _output(prepared / 'runs' / arm)
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    # finetune itself requires the run dir to be absent. Keep admission status
    # outside it until its mkdir has run, or before an early deadline refusal.
    status_path = prepared / f'{arm}_status.json'
    record = dict(status='running', arm=arm, deadline_utc=deadline.isoformat(),
                  started_utc=datetime.now(timezone.utc).isoformat())
    _write(status_path, record)
    destination.rmdir()
    audit = dict(initial=None, prefill=None, validations=[], end=None)
    rows, vals, pending, box = [], [], [], []
    keys = ('Learners', 'play_game', 'play_set', 'make_opponent', 'RUNS')
    old = {k: getattr(finetune, k) for k in keys}
    old_argv = sys.argv
    missing = object()
    prior_variant = VARIANTS.get(VARIANT, missing)
    restored = []

    def persist():
        destination.mkdir(parents=True, exist_ok=True)
        _write(destination / 'training_audit.json', audit)
        _write(destination / 'status.json', record)

    def append(name, row):
        with (destination / name).open('a') as f:
            f.write(json.dumps(row, allow_nan=False) + '\n')

    def load(variant, run_dir, run_seed, load=False):
        if box or variant != VARIANT or Path(run_dir) != destination or run_seed != RUN_SEED or not load:
            raise ValueError('Unexpected learner load')
        learners = old['Learners'](variant, run_dir, run_seed, load=load)
        audit['initial'] = prove_initial(learners, entry)
        a = _canonical(learners)
        original_save = a.save_agent
        def save(path=None):
            # finetune attempts best-validation saves; persist only final state.
            if len(rows) == PREFILL + TRAIN and len(audit['validations']) == 2:
                original_save(path)
        prior = vars(a).get('save_agent', missing)
        restored.append((a, 'save_agent', prior))
        a.save_agent = save
        box.append(learners)
        persist()
        return learners

    def opponent(kind, side, *args, **kwargs):
        if pending:
            raise ValueError('Overlapping opponent construction')
        pending.append((kind, side))
        return old['make_opponent'](kind, side, *args, **kwargs)

    def rollout(env, agent, opp, seed, side, train):
        _check_deadline(deadline)
        index = len(rows)
        if index >= PREFILL + TRAIN or not box:
            raise ValueError('Unexpected rollout count')
        plan = entry['rollout_plan'][index]
        a = _canonical(box[0])
        expected_opponent = (plan['opponent'], 'player_1' if side == 'player_0' else 'player_0')
        if (agent is not a or not train or not a.training or a.autosave_on_terminate
                or a.cfg.to_dict() != entry['config'] or abs(a.epsilon - .05) > 1e-12
                or a.learn_enabled != (plan['phase'] == 'train') or seed != plan['seed']
                or side != plan['side'] or pending != [expected_opponent]):
            raise ValueError('Live rollout differs from fixed config/map/side/opponent plan')
        pending.clear()
        before_env, before_learn = a.env_steps, a.learn_steps
        transcript = {}
        with _act_deadline(a, deadline, transcript), action_audit(a) as actions, reward_audit(manifest['source_config']['w_sap_hit']) as rewards:
            row = old['play_game'](env, agent, opp, seed, side, train=train)
        updates = 0 if plan['phase'] == 'prefill' else 150
        if (row['steps'] != 303 or row['seed'] != seed or row['side'] != side
                or row['point_counting_version'] != 2
                or actions['act_calls'] != 303 or actions['update_calls'] != 303
                or a.env_steps != before_env + 303 or a.learn_steps != before_learn + updates
                or rewards['transitions'] != actions['checked_replay_transitions']):
            raise ValueError('Actual rollout counters/action/reward evidence incomplete')
        proof = dict(row, **plan, final_action_audit=actions, reward_audit=rewards,
                     policy_transcript=transcript,
                     identity=learner_identity(box[0]))
        rows.append(proof)
        append('rollouts.jsonl', proof)
        if len(rows) == PREFILL:
            audit['prefill'] = learner_identity(box[0])
            _prove_prefill(audit['prefill'], audit['initial'], a)
            persist()
        return row

    def validate(env, learners, seeds, opponents, **kwargs):
        _check_deadline(deadline)
        after = len(rows) - PREFILL
        if (not box or learners is not box[0] or after not in (0, TRAIN)
                or len(audit['validations']) != (0, TRAIN).index(after)
                or list(seeds) != list(range(500000, 500004))
                or tuple(opponents) != ('default', 'solution92') or kwargs):
            raise ValueError('Unexpected validation schedule/config')
        before = learner_identity(learners)
        completed = []
        try:
            result = _isolated_validation(env, learners, seeds, opponents, deadline, completed)
        finally:
            learners.train_mode()
            for row in completed:
                evidence = dict(row, after_games=after, config=entry['config'],
                                epsilon=0., learn_enabled=False, eval_rng_seed=EVAL_SEED)
                vals.append(evidence)
                append('validation_games.jsonl', evidence)
        end = learner_identity(learners)
        expected = [r for r in validation_plan() if r['after_games'] == after]
        actual = [dict(after_games=after, opponent=r['opponent'], seed=r['seed'], side=r['side']) for r in result]
        if before != end or actual != expected or any(r['steps'] != 303 or r['point_counting_version'] != 2 for r in result):
            raise ValueError('Validation learning isolation or plan failed')
        audit['validations'].append(dict(after_games=after, before=before, after=end))
        persist()
        return result

    argv = ['student_reward/finetune', '--init', str(init), '--name', arm,
            '--variant', VARIANT, '--games', str(TRAIN), '--seed', str(RUN_SEED),
            '--map-offset', str(OFFSET), '--lr', '.0001', '--prefill-games', str(PREFILL),
            '--keep-final', '--no-test', '--val-every', str(TRAIN), '--n-val', '4', '--mix', MIX]
    record['argv'] = argv
    try:
        _check_deadline(deadline)
        VARIANTS[VARIANT] = ('sherlock', entry['config'])
        finetune.RUNS = prepared / 'runs'
        finetune.Learners, finetune.play_game = load, rollout
        finetune.play_set, finetune.make_opponent = validate, opponent
        sys.argv = argv
        finetune.main()
        _check_deadline(deadline)
        if len(rows) != 200 or len(vals) != 32 or pending or len(box) != 1:
            raise ValueError('Incomplete actual game budget')
        with (destination / 'train.csv').open() as f:
            train_rows = list(csv.DictReader(f))
        if (len(train_rows) != TRAIN or [int(r['game']) for r in train_rows] != list(range(TRAIN))
                or any(not math.isfinite(float(r['mean_loss'])) for r in train_rows)):
            raise ValueError('Incomplete/nonfinite training CSV')
        audit['end'] = _prove_end(box[0], entry, audit['initial'], destination / 'weights/agent.pth', rows)
        if (audit['end']['learning']['learn_steps'] != 24000
                or audit['end']['learning']['env_steps'] != 120600):
            raise ValueError('Final fixed update/env counters mismatch')
        # Historical finetune makes a best-validation directory even with
        # --keep-final. It never supplies this experiment's accepted weights.
        shutil.rmtree(destination / 'weights_best', ignore_errors=True)
        check_prepared(prepared, arm)
        _check_deadline(deadline)
        persist()
        receipt = dict(schema_version=1, status='done', arm=arm, prepared=str(prepared),
                       student_sha256=manifest['student_sha256'], config=entry['config'],
                       actual_prefill_games=PREFILL, actual_train_games=TRAIN,
                       actual_validation_games=len(vals), end=audit['end'],
                       final_checkpoint=str(destination / 'weights/agent.pth'),
                       final_checkpoint_sha256=file_sha256(destination / 'weights/agent.pth'),
                       prefill_action_sha256=experiment.state_sha256([
                           [r['final_action_audit']['transcript_sha256'],
                            r['policy_transcript']['action_state_sha256']] for r in rows[:PREFILL]]),
                       evidence_sha256={n: file_sha256(destination / n) for n in (
                           'training_audit.json', 'rollouts.jsonl', 'validation_games.jsonl', 'train.csv')})
        record.update(status='done', actual_rollout_games=len(rows), actual_validation_games=len(vals))
        _write(destination / 'final_receipt.json', receipt)
        persist()
        validate_receipt(destination)
        other = prepared / 'runs' / ('sap0' if arm == 'control' else 'control')
        if (other / 'final_receipt.json').exists():
            compare_prefill(prepared)
    except BaseException as exc:
        record.update(status='incomplete', error=f'{type(exc).__name__}: {exc}',
                      actual_rollout_games=len(rows), actual_validation_games=len(vals))
        (destination / 'final_receipt.json').unlink(missing_ok=True)
        raise
    finally:
        sys.argv = old_argv
        for key, value in old.items():
            setattr(finetune, key, value)
        if prior_variant is missing:
            VARIANTS.pop(VARIANT, None)
        else:
            VARIANTS[VARIANT] = prior_variant
        for obj, key, value in restored:
            if value is missing:
                vars(obj).pop(key, None)
            else:
                setattr(obj, key, value)
        record['finished_utc'] = datetime.now(timezone.utc).isoformat()
        persist()
        _write(status_path, record)
    return record


def validate_receipt(destination):
    """Refuse partial arms and verify persisted budget, config, hashes and proofs."""
    destination = Path(destination)
    try:
        status = json.loads((destination / 'status.json').read_text())
        receipt = json.loads((destination / 'final_receipt.json').read_text())
        if status['status'] != 'done' or receipt['status'] != 'done':
            raise ValueError('Incomplete arm')
        manifest, entry, _ = check_prepared(receipt['prepared'], receipt['arm'])
        if (receipt['student_sha256'] != manifest['student_sha256'] or receipt['config'] != entry['config']
                or (receipt['actual_prefill_games'], receipt['actual_train_games'], receipt['actual_validation_games']) != (40, 160, 32)
                or any(file_sha256(destination / n) != digest for n, digest in receipt['evidence_sha256'].items())
                or file_sha256(destination / 'weights/agent.pth') != receipt['final_checkpoint_sha256']):
            raise ValueError('Receipt hashes/counts/config differ')
        rows = [json.loads(line) for line in (destination / 'rollouts.jsonl').read_text().splitlines()]
        vals = [json.loads(line) for line in (destination / 'validation_games.jsonl').read_text().splitlines()]
        audit = json.loads((destination / 'training_audit.json').read_text())
        if ([{k: r[k] for k in ('phase', 'game', 'seed', 'side', 'opponent')} for r in rows] != rollout_plan()
                or [{k: r[k] for k in ('after_games', 'opponent', 'seed', 'side')} for r in vals] != validation_plan()
                or len(audit['validations']) != 2 or any(p['before'] != p['after'] for p in audit['validations'])
                or not audit['end']['reload_verified'] or audit['end'] != receipt['end']
                or audit['end']['learning']['learn_steps'] != 24000
                or audit['end']['learning']['env_steps'] != 120600
                or any(r['steps'] != 303 or r['final_action_audit']['act_calls'] != 303
                       or r['final_action_audit']['update_calls'] != 303
                       or r['reward_audit']['transitions'] != r['final_action_audit']['checked_replay_transitions'] for r in rows)):
            raise ValueError('Receipt actual rollout/validation/action/update proof incomplete')
        _validate_persisted_learning(destination, entry, audit, rows, vals)
        expected = experiment.state_sha256([
            [r['final_action_audit']['transcript_sha256'], r['policy_transcript']['action_state_sha256']]
            for r in rows[:PREFILL]])
        if receipt['prefill_action_sha256'] != expected:
            raise ValueError('Prefill transcript differs')
        cp = torch.load(destination / 'weights/agent.pth', map_location='cpu', weights_only=True)
        _finite(cp)
        if (cp['cfg'] != entry['config'] or cp['env_steps'] != 120600 or cp['learn_steps'] != 24000
                or tensor_sha256(cp['q']) != audit['end']['q_tensor_sha256']
                or tensor_sha256(cp['target_q']) != audit['end']['target_tensor_sha256']
                or experiment.state_sha256(cp['opt']) != audit['end']['learning']['optimizer_sha256']):
            raise ValueError('Final checkpoint learning proof differs')
        return receipt
    except (OSError, KeyError, TypeError, IndexError) as exc:
        raise ValueError('Incomplete or malformed final arm receipt') from exc


def _validate_persisted_learning(destination, entry, audit, rows, vals):
    """Cross-check live chronology independently of hashes of supplied JSON."""
    def require(ok):
        if not ok:
            raise ValueError('Persisted learning evidence/proof contradicts fixed budget')
    cfg = entry['config']
    initial, prefill = audit['initial'], audit['prefill']
    il, pl = initial['learning'], prefill['learning']
    with torch.random.fork_rng(devices=[]):
        model = QNet(79, 6, hidden=512, dueling=cfg['dueling'])
        fresh = experiment.state_sha256(torch.optim.Adam(model.parameters(), lr=1e-4).state_dict())
    require(initial['q_tensor_sha256'] == initial['target_tensor_sha256'] == entry['tensor_sha256']
            and il['optimizer_sha256'] == fresh and il['config'] == cfg
            and il['env_steps'] == 60000 and il['learn_steps'] == 0
            and il['learn_enabled'] is True and il['autosave_on_terminate'] is False
            and il['recent_losses'] == [] and il['replay']['size'] == il['replay']['pos'] == 0
            and il['replay']['_mask_dim'] == 1)
    shared = initial['initial_identity']['learners']
    require(len(shared) == 1 and shared[0]['sides'] == ['player_0', 'player_1']
            and shared[0]['optimizer_sha256'] == fresh
            and shared[0]['replay']['logical_content'] == 'empty-replay-v1')
    require(prefill == rows[PREFILL - 1]['identity']
            and prefill['q_tensor_sha256'] == prefill['target_tensor_sha256'] == entry['tensor_sha256']
            and pl['optimizer_sha256'] == fresh and pl['learn_steps'] == 0
            and pl['env_steps'] == 72120 and pl['learn_enabled'] is False
            and pl['replay']['size'] > cfg['learn_start'] and pl['recent_losses'] == [])
    for index, row in enumerate(rows):
        state = row['identity']
        learning = state['learning']
        training = index >= PREFILL
        require(learning['config'] == cfg and learning['learn_enabled'] is training
                and learning['autosave_on_terminate'] is False
                and learning['env_steps'] == 60000 + (index + 1) * 303
                and learning['learn_steps'] == max(0, index + 1 - PREFILL) * 150)
        if not training:
            require(state['q_tensor_sha256'] == state['target_tensor_sha256'] == entry['tensor_sha256']
                    and learning['optimizer_sha256'] == fresh)
    for proof, after in zip(audit['validations'], (0, TRAIN)):
        learning = proof['before']['learning']
        require(proof['after_games'] == after and proof['before'] == proof['after']
                and learning['env_steps'] == 72120 + after * 303
                and learning['learn_steps'] == after * 150 and learning['config'] == cfg)
    require(all(r['steps'] == 303 and r['point_counting_version'] == 2
                and r['config'] == cfg and r['epsilon'] == 0.
                and r['learn_enabled'] is False and r['eval_rng_seed'] == EVAL_SEED for r in vals))
    with (destination / 'train.csv').open() as handle:
        train_rows = list(csv.DictReader(handle))
    require(len(train_rows) == TRAIN)
    for index, row in enumerate(train_rows):
        expected = rows[PREFILL + index]
        require(int(row['game']) == index and int(row['seed']) == expected['seed']
                and row['side'] == expected['side'] and row['opponent'] == expected['opponent']
                and int(row['steps']) == 303 and int(row['point_counting_version']) == 2
                and int(row['learn_steps']) == (index + 1) * 150
                and int(row['env_steps']) == 72120 + (index + 1) * 303
                and float(row['epsilon']) == .05 and math.isfinite(float(row['mean_loss'])))
    end = audit['end']
    require(end['q_tensor_sha256'] != entry['tensor_sha256']
            and end['q_tensor_sha256'] == rows[-1]['identity']['q_tensor_sha256']
            and end['target_tensor_sha256'] == rows[-1]['identity']['target_tensor_sha256']
            and end['learning']['optimizer_sha256'] == rows[-1]['identity']['learning']['optimizer_sha256'])


def compare_prefill(prepared):
    receipts = [validate_receipt(Path(prepared) / 'runs' / arm) for arm in ARMS]
    if receipts[0]['prefill_action_sha256'] != receipts[1]['prefill_action_sha256']:
        raise ValueError('Paired prefill actions differ; reward ablation invalid')
    result = dict(status='matched', prefill_games=40,
                  prefill_action_sha256=receipts[0]['prefill_action_sha256'],
                  note='Stored scalar rewards may differ; final actions and replay actions agree.')
    _write(Path(prepared) / 'paired_prefill.json', result)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    p.add_argument('--student', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    r = sub.add_parser('runarm')
    r.add_argument('--prepared', type=Path, required=True)
    r.add_argument('--arm', choices=ARMS, required=True)
    r.add_argument('--deadline-utc', required=True)
    args = ap.parse_args()
    experiment.limit_threads()
    if args.command == 'prepare':
        prepare(args.student, args.out)
    else:
        run_arm(args.prepared, args.arm, args.deadline_utc)


if __name__ == '__main__':
    main()
