"""Fixed four-arm Fog-SAP reward study; no promotion, retry or checkpoint selection.

The existing finetune is wrapped only in this process and restored in finally.
Explicit final provenance, paired prefill and isolated V14 validation are audited.
"""
from __future__ import annotations

import argparse
import copy
import json
import csv
import hashlib
import math
import shutil
import time
from contextlib import contextmanager
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet, checkpoint_ensemble_dims
from scripts import experiment, protocol
from scripts.final_rescue_train import action_audit, isolated_validation
from scripts.night_train_pilot import file_sha256, tensor_sha256
from scripts.output_paths import checked_output
from scripts.targeting_adapt import _canonical, _finite, _prove_end, _prove_prefill, learner_identity
from scripts.variants import VARIANTS
from scripts.ensemble_diversity_train import _source, prove_initial, validate_v14
from scripts.student_reward_train import _write, _output as _safe_output, _protected_hashes
from scripts.early_curriculum_study import source_identity

ROOT = Path(__file__).resolve().parent.parent
SOURCE_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
VARIANT = "fog_reward_20261108"
ARMS = {f"{role}{seed}": (seed, neutral) for seed in (41, 42)
        for role, neutral in (("control", False), ("neutral", True))}
MIX = {"solution92": .6, "sol92_sq": .2, "default": .1, "rush": .1}
TRAIN_BASE, VALIDATION_BASE = 7_000_000, 7_600_000
# A smoke is a distinct mechanism probe and never nominable.
SMOKE_TRAIN_BASE, SMOKE_VALIDATION_BASE = 7_800_000, 8_400_000
PLANS = [ROOT / f"docs/superpowers/{kind}/2026-11-08-fog-reward.md"
         for kind in ("specs", "plans")]


class StudyInterrupted(RuntimeError):
    """A requested stop was observed at a completed-game boundary."""


def _settings(smoke: bool) -> dict:
    return dict(games=2 if smoke else 400, prefill=2 if smoke else 40,
                val_every=2 if smoke else 400, n_val=1 if smoke else 4,
                train_base=SMOKE_TRAIN_BASE if smoke else TRAIN_BASE,
                val_base=SMOKE_VALIDATION_BASE if smoke else VALIDATION_BASE)


def _arm(arm: str) -> tuple:
    if arm not in ARMS:
        raise ValueError(f"Unknown arm: {arm}")
    return ARMS[arm]


def rollout_plan(arm: str, *, smoke: bool = False) -> list[dict]:
    seed, _ = _arm(arm)
    settings, mix = _settings(smoke), MIX
    rng = np.random.default_rng(seed)
    names, probabilities = list(mix), list(mix.values())
    rows = []
    for phase, count, offset in (("prefill", settings["prefill"], 5000),
                                 ("train", settings["games"], 0)):
        for game in range(count):
            rows.append(dict(phase=phase, game=game,
                             seed=settings["train_base"] + seed * 10000 + offset + game // 2,
                             side=("player_0", "player_1")[game % 2],
                             opponent=names[rng.choice(len(names), p=probabilities)]))
    return rows


def validation_plan(*, smoke: bool = False) -> list[dict]:
    settings = _settings(smoke)
    return [dict(after_games=after, opponent=opponent, seed=seed, side=side)
            for after in range(0, settings["games"] + 1, settings["val_every"])
            for opponent in ("default", "solution92")
            for seed in range(settings["val_base"], settings["val_base"] + settings["n_val"])
            for side in ("player_0", "player_1")]


def _pins() -> dict:
    return dict(source=source_identity(ROOT, sys.executable, PLANS), protected=_protected_hashes())


def _check_frozen(manifest: dict) -> None:
    if file_sha256(Path(manifest["source"])) != SOURCE_SHA or _pins() != manifest["pins"]:
        raise ValueError("Frozen source/HEAD/plans/interpreter/protected inputs changed")


def training_config(source_cfg: dict, neutral: bool) -> dict:
    if type(neutral) is not bool:
        raise ValueError("Neutral flag must be boolean")
    return dict(source_cfg, frozen=False, lr=5e-5, rules_in_training=True,
                rules_in_training_all=True, rescue_in_training=True,
                fog_unknown_reward_neutral=neutral)


def prepare(source: Path, out: Path, *, smoke: bool = False) -> dict:
    source = Path(source).resolve(strict=True)
    out = _safe_output(out)
    if out.exists():
        raise FileExistsError(out)
    _, states, source_cfg = _source(source)
    source_cfg["fog_unknown_reward_neutral"] = False
    if source_cfg["w_sap_hit"] != .3 or source_cfg["train_every"] != 2:
        raise ValueError("V14 SAP weight/train interval differs from fixed recipe")
    manifest = dict(schema_version=1, source=str(source), source_sha256=SOURCE_SHA,
                    source_config=source_cfg, smoke=bool(smoke), settings=_settings(smoke),
                    pins=_pins(), validation_plan=validation_plan(smoke=smoke), arms={})
    for arm, (seed, neutral) in ARMS.items():
        component = 18
        config = training_config(source_cfg, neutral)
        q = copy.deepcopy(states[component])
        checkpoint = dict(q=q, target_q=copy.deepcopy(q), cfg=config, feature_dim=79,
                          n_actions=6, ensemble=[], ensemble_dims=[], env_steps=60000, learn_steps=0)
        init = out / arm
        (init / "weights").mkdir(parents=True, exist_ok=False)
        weights = init / "weights/agent.pth"
        torch.save(checkpoint, weights)
        entry = dict(component_index=component, run_seed=seed,
                     mix=MIX, config=config, tensor_sha256=tensor_sha256(q),
                     weights_sha256=file_sha256(weights), rollout_plan=rollout_plan(arm, smoke=smoke))
        manifest["arms"][arm] = entry
        _write(init / "manifest.json", dict(variant=VARIANT, base_variant=VARIANT,
                                           train_games=0, arm=arm, **entry))
    _check_frozen(manifest)
    _write(out / "manifest.json", manifest)
    return manifest


def check_prepared(prepared: Path, arm: str, *, smoke: bool = False) -> tuple[dict, dict, Path]:
    seed, neutral = _arm(arm)
    component = 18
    prepared = Path(prepared).resolve(strict=True)
    manifest = json.loads((prepared / "manifest.json").read_text())
    if manifest.get("smoke") is not bool(smoke):
        raise ValueError("Prepared smoke mode differs from requested smoke mode")
    if (manifest.get("source_sha256") != SOURCE_SHA or set(manifest["arms"]) != set(ARMS)
            or manifest["settings"] != _settings(smoke)
            or manifest["validation_plan"] != validation_plan(smoke=smoke)):
        raise ValueError("Prepared source/arms/schedule differs from fixed study")
    _check_frozen(manifest)
    _, states, source_cfg = _source(Path(manifest["source"]))
    if manifest["source_config"] != source_cfg:
        raise ValueError("Prepared source config changed")
    entry = manifest["arms"][arm]
    expected = dict(component_index=component, run_seed=seed,
                    mix=MIX, config=training_config(source_cfg, neutral),
                    tensor_sha256=tensor_sha256(states[component]),
                    weights_sha256=entry["weights_sha256"], rollout_plan=rollout_plan(arm, smoke=smoke))
    if entry != expected:
        raise ValueError("Prepared arm membership/config/schedule changed")
    init = prepared / arm
    weights = init / "weights/agent.pth"
    if {p.name for p in (init / "weights").iterdir()} != {"agent.pth"}:
        raise ValueError("Init must contain only fresh weights, no replay")
    if file_sha256(weights) != entry["weights_sha256"]:
        raise ValueError("Init weights changed")
    cp = torch.load(weights, map_location="cpu", weights_only=True)
    if (set(cp) != {"q", "target_q", "cfg", "feature_dim", "n_actions", "ensemble",
                   "ensemble_dims", "env_steps", "learn_steps"}
            or cp["ensemble"] or cp["ensemble_dims"] or cp["cfg"] != entry["config"]
            or cp["feature_dim"] != 79 or cp["n_actions"] != 6
            or cp["env_steps"] != 60000 or cp["learn_steps"] != 0
            or any(tensor_sha256(cp[k]) != entry["tensor_sha256"] for k in ("q", "target_q"))):
        raise ValueError("Init is not the exact fresh single-net warm start")
    local = json.loads((init / "manifest.json").read_text())
    if local != dict(variant=VARIANT, base_variant=VARIANT, train_games=0, arm=arm, **entry):
        raise ValueError("Local init manifest changed")
    return manifest, entry, init


@contextmanager
def reward_audit(agent):
    """Evaluate both formulas on the same transition using final UID provenance."""
    from agents.sherlock import main, geometry as geo
    original = main.unit_rewards
    proof = dict(calls=0, transitions=0, unknown_sap_transitions=0,
                 unknown_reward_mass=0., applied_reward_mass=0.,
                 sap_transitions=0, estimated_positive_hits=0, estimated_misses=0,
                 estimated_hit_sum=0, actual_reward_sum=0.)
    digests = {key: hashlib.sha256() for key in ('legacy', 'neutral', 'actual')}
    pending=[]
    buffer=getattr(agent,'buffer',None)
    missing=object()
    prior_push=vars(buffer).get('push',missing) if buffer is not None else missing
    original_push=buffer.push if buffer is not None else None
    proof['replay_transitions']=0

    def audited_push(s,a,r,ns,done,mask):
        if not pending or r!=pending.pop(0):
            raise ValueError('Actual replay reward differs from audited reward')
        proof['replay_transitions']+=1
        return original_push(s,a,r,ns,done,mask)

    def measured(cfg, ctx, nxt, actions, hits, *, unknown_sap=None):
        if pending:
            raise ValueError('Previous audited rewards were not written to replay')
        if not hasattr(agent, '_sap_unknown'):
            raise ValueError('Agent lacks explicit final SAP provenance')
        unknown = set(agent._sap_unknown)
        alive = {int(uid) for uid in ctx['ally_ids']}
        if (unknown - alive or unknown - set(actions)
                or any(actions[uid] != geo.SAP or hits.get(uid, 0) != 0 for uid in unknown)
                or actions != agent._prev_actions or hits != agent._sap_hits
                or (getattr(cfg, 'fog_unknown_reward_neutral', False)
                    and (unknown_sap is None or set(unknown_sap) != unknown))
                or (unknown_sap is not None and set(unknown_sap) != unknown)):
            raise ValueError('Reward call differs from explicit final unknown-SAP provenance')
        legacy_cfg, neutral_cfg = copy.copy(cfg), copy.copy(cfg)
        legacy_cfg.fog_unknown_reward_neutral = False
        neutral_cfg.fog_unknown_reward_neutral = True
        legacy = original(legacy_cfg, ctx, nxt, actions, hits)
        neutral = original(neutral_cfg, ctx, nxt, actions, hits, unknown_sap=unknown)
        # Retain the historic five-argument call when the real flag is false.
        actual = (original(cfg, ctx, nxt, actions, hits, unknown_sap=unknown_sap)
                  if unknown_sap is not None else original(cfg, ctx, nxt, actions, hits))
        if set(legacy) != alive or set(neutral) != alive or set(actual) != alive:
            raise ValueError('Reward formulas have inconsistent transition membership')
        enabled = getattr(cfg, 'fog_unknown_reward_neutral', False)
        for uid in sorted(alive):
            expected = cfg.w_sap_hit if cfg.use_shaping and uid in unknown else 0.
            if (not all(math.isfinite(x) for x in (legacy[uid], neutral[uid], actual[uid], expected))
                    or not math.isclose(neutral[uid]-legacy[uid], expected, abs_tol=1e-8, rel_tol=1e-8)
                    or actual[uid] != (neutral[uid] if enabled else legacy[uid])):
                raise ValueError('Unknown-SAP reward arithmetic mismatch')
            sap, count = actions.get(uid) == geo.SAP, hits.get(uid, 0)
            proof['sap_transitions'] += int(sap)
            proof['estimated_positive_hits'] += int(sap and count > 0)
            proof['estimated_misses'] += int(sap and count <= 0)
            proof['estimated_hit_sum'] += int(count) if sap else 0
            proof['unknown_sap_transitions'] += int(uid in unknown)
            proof['unknown_reward_mass'] += expected
            proof['applied_reward_mass'] += expected if enabled else 0.
            proof['actual_reward_sum'] += actual[uid]
        for key, value in (('legacy', legacy), ('neutral', neutral), ('actual', actual)):
            digests[key].update(experiment.state_sha256(value).encode())
        if buffer is not None:
            pending.extend(actual.get(uid,0.) for uid in agent._prev_feats)
        proof['calls'] += 1
        proof['transitions'] += len(alive)
        return actual

    main.unit_rewards = measured
    if buffer is not None: buffer.push=audited_push
    try:
        yield proof
        if pending: raise ValueError('Unfinished audited replay reward writes')
    finally:
        main.unit_rewards = original
        if buffer is not None:
            if prior_push is missing: vars(buffer).pop('push',None)
            else: buffer.push=prior_push
        proof.update({key+'_reward_sha256': digest.hexdigest() for key, digest in digests.items()})


def replay_without_reward(buffer):
    """Exact logical ring contents and metadata; intentionally omit only r."""
    size = buffer.size
    idx = np.arange(size) if size < buffer.capacity else (np.arange(size)+buffer.pos) % buffer.capacity
    return experiment.state_sha256(dict(size=size, pos=buffer.pos, capacity=buffer.capacity,
        mask_dim=buffer._mask_dim, **{key: getattr(buffer,key)[idx]
                                    for key in ('s','a','ns','done','mask')}))


@contextmanager
def trajectory_audit(env, agent):
    """Hash every full simulator state, both-side output/action and replay insertion."""
    from scripts.holder_rollout import exact_digest
    digests = {key: hashlib.sha256() for key in ('environment', 'policy', 'replay_without_reward')}
    proof = dict(reset_calls=0, step_calls=0, act_calls=0, replay_pushes=0)
    missing = object()
    changed = []

    def patch(obj, name, wrapper):
        changed.append((obj, name, vars(obj).get(name, missing)))
        setattr(obj, name, wrapper)

    reset, step, act, push = env.reset, env.step, agent.act, agent.buffer.push

    def measured_reset(*args, **kwargs):
        result = reset(*args, **kwargs)
        digests['environment'].update(exact_digest((args, kwargs, result, env.state)).encode())
        proof['reset_calls'] += 1
        return result

    def measured_step(*args, **kwargs):
        before = exact_digest(env.state)
        result = step(*args, **kwargs)
        digests['environment'].update(exact_digest((before, args, kwargs, result, env.state)).encode())
        proof['step_calls'] += 1
        return result

    def measured_act(*args, **kwargs):
        result = act(*args, **kwargs)
        digests['policy'].update(exact_digest((args, kwargs, result, agent._prev_feats,
            agent._prev_actions, agent._prev_masks, agent._sap_hits, sorted(agent._sap_unknown))).encode())
        proof['act_calls'] += 1
        return result

    def measured_push(s, a, r, ns, done, mask):
        digests['replay_without_reward'].update(exact_digest((s,a,ns,done,mask)).encode())
        proof['replay_pushes'] += 1
        return push(s,a,r,ns,done,mask)

    try:
        patch(env,'reset',measured_reset); patch(env,'step',measured_step)
        patch(agent,'act',measured_act); patch(agent.buffer,'push',measured_push)
        yield proof
    finally:
        for obj, name, value in reversed(changed):
            if value is missing: vars(obj).pop(name,None)
            else: setattr(obj,name,value)
        proof.update({key+'_sha256': digest.hexdigest() for key,digest in digests.items()})


def prefill_proof(arm, entry, audit, rows, agent, *, smoke=False):
    return _prefill_summary(arm,entry,audit['initial'],audit['prefill'],rows,
                            replay_without_reward(agent.buffer),agent.learn_steps,smoke=smoke)


def _prefill_summary(arm,entry,initial,prefill,rows,replay_hash,learn_steps,*,smoke=False):
    settings = _settings(smoke)
    if len(rows) != settings['prefill'] or any(row['phase'] != 'prefill' for row in rows):
        raise ValueError('Prefill proof requires exactly the complete prefill')
    proof = dict(status='prefill_ready', arm=arm, smoke=smoke, run_seed=entry['run_seed'],
        component_index=18, actual_prefill_games=len(rows), learn_steps=learn_steps,
        unknown_sap_transitions=sum(r['reward_audit']['unknown_sap_transitions'] for r in rows),
        unknown_reward_mass=sum(r['reward_audit']['unknown_reward_mass'] for r in rows),
        trajectory_sha256=experiment.state_sha256([[r['trajectory'],r['action_audit'],
            {k:r[k] for k in ('phase','game','seed','side','opponent','steps','result',
                             'our_wins','opp_wins','our_points','opp_points')}] for r in rows]),
        replay_without_reward_sha256=replay_hash,
        unchanged_q=initial['q_tensor_sha256']==prefill['q_tensor_sha256'],
        unchanged_target=initial['target_tensor_sha256']==prefill['target_tensor_sha256'],
        unchanged_optimizer=initial['learning']['optimizer_sha256']==prefill['learning']['optimizer_sha256'])
    for kind in ('legacy','neutral','actual'):
        proof[kind+'_reward_sha256'] = experiment.state_sha256([r['reward_audit'][kind+'_reward_sha256'] for r in rows])
    if proof['unknown_sap_transitions'] <= 0 or not all(proof[k] for k in
            ('unchanged_q','unchanged_target','unchanged_optimizer')) or proof['learn_steps']:
        raise ValueError('Prefill has no unknown SAPs or changed learning state')
    return proof


def validate_prefill_bundle(directory,prepared,arm):
    """Recompute the frozen prefill proof using raw rows and pinned initial identity."""
    directory,prepared=Path(directory),Path(prepared)
    proof=json.loads((directory/'prefill_proof.json').read_text())
    if file_sha256(directory/'prefill_bundle.json')!=proof.get('bundle_sha256'):
        raise ValueError('Prefill bundle hash changed')
    bundle=json.loads((directory/'prefill_bundle.json').read_text())
    manifest=json.loads((prepared/'manifest.json').read_text())
    entry=manifest['arms'][arm]
    initial,prefill,rows=bundle['initial'],bundle['prefill'],bundle['rows']
    il,pl=initial['learning'],prefill['learning']
    fresh = il['optimizer_sha256']
    if (bundle['arm']!=arm or bundle['entry']!=entry
            or [{k:r[k] for k in ('phase','game','seed','side','opponent')} for r in rows]
               !=rollout_plan(arm)[:40]
            or initial['q_tensor_sha256']!=entry['tensor_sha256']
            or initial['target_tensor_sha256']!=entry['tensor_sha256']
            or il['config']!=entry['config'] or il['env_steps']!=60000 or il['learn_steps']!=0
            or il['replay']['size'] or il['replay']['pos'] or il['replay']['_mask_dim']!=1
            or il['recent_losses'] or pl['recent_losses'] or pl['learn_steps']
            or pl['env_steps']!=72120 or pl['config']!=entry['config']
            or pl['replay']['size']<=entry['config']['learn_start']
            or pl['optimizer_sha256']!=fresh or pl['learn_enabled'] is not False
            or any(r['steps']!=303 or r['point_counting_version']!=2 or r['updates']!=0
                   or r['learn_steps'] or r['env_steps']!=60000+(index+1)*303
                   or r['trajectory']['reset_calls']!=1 or r['trajectory']['step_calls']!=303
                   or r['trajectory']['act_calls']!=303
                   or r['trajectory']['replay_pushes']!=r['reward_audit']['transitions']
                   or r['action_audit']['checked_replay_transitions']!=r['reward_audit']['transitions']
                   for index,r in enumerate(rows))):
        raise ValueError('Prefill raw chronology/initial/replay/learning evidence differs')
    expected=_prefill_summary(arm,entry,initial,prefill,rows,
        bundle['replay_without_reward_sha256'],pl['learn_steps'])
    if proof!={**expected,'bundle_sha256':file_sha256(directory/'prefill_bundle.json')}:
        raise ValueError('Prefill summary differs from frozen raw bundle')
    return proof


def compare_prefill_proofs(control, neutral, seed, *, smoke=False):
    """No end-of-training results are read to admit a paired prefill."""
    for proof, role in ((control,'control'),(neutral,'neutral')):
        expected = dict(status='prefill_ready', arm=f'{role}{seed}', run_seed=seed,
            component_index=18, actual_prefill_games=_settings(smoke)['prefill'], smoke=smoke,
            unchanged_q=True, unchanged_target=True, unchanged_optimizer=True, learn_steps=0)
        if (any(proof.get(k)!=v for k,v in expected.items())
                or proof.get('unknown_sap_transitions',0)<=0
                or proof.get('unknown_reward_mass',0)<=0
                or proof.get('actual_reward_sha256') != proof.get(
                    ('legacy' if role=='control' else 'neutral')+'_reward_sha256')):
            raise ValueError('Invalid paired prefill role/count/unknown/reward/learning evidence')
    fields=('trajectory_sha256','replay_without_reward_sha256','legacy_reward_sha256',
            'neutral_reward_sha256','unknown_sap_transitions','unknown_reward_mass')
    if any(control[k]!=neutral[k] for k in fields):
        raise ValueError('Paired prefill trajectories, replay or counterfactual rewards differ')
    return dict(status='matched',run_seed=seed,smoke=smoke,
                evidence={k:control[k] for k in fields},eligible=False)


def wait_prefill(supervisor_state, arm, check):
    state = json.loads(Path(supervisor_state).read_text())
    seed,_ = _arm(arm)
    path = Path(state['out']) / f'paired_prefill_{seed}.json'
    while not path.exists():
        check()
        time.sleep(1)
    result=json.loads(path.read_text())
    if result.get('status')!='matched' or result.get('run_seed')!=seed:
        raise ValueError('Supervisor did not admit paired prefill')
    check()


def run_arm(prepared: Path, arm: str, name: str, *, supervisor_state: Path, smoke: bool = False) -> dict:
    from scripts import finetune

    if not name or name in (".", "..") or Path(name).name != name:
        raise ValueError("Run name must be a single new directory name")
    destination = _safe_output(finetune.RUNS / name)
    if destination.exists():
        raise FileExistsError(destination)
    manifest, entry, init = check_prepared(prepared, arm, smoke=smoke)
    settings = _settings(smoke)
    mix_text = ",".join(f"{key}={value}" for key, value in entry["mix"].items())
    argv = ["fog_reward_study/finetune", "--init", str(init), "--name", name,
            "--variant", VARIANT, "--games", str(settings["games"]), "--seed", str(entry["run_seed"]),
            "--map-offset", "0", "--lr", "0.00005", "--prefill-games", str(settings["prefill"]),
            "--keep-final", "--no-test", "--val-every", str(settings["val_every"]),
            "--n-val", str(settings["n_val"]), "--mix", mix_text]
    record = dict(schema_version=1, status="running", eligible=False, smoke=smoke, arm=arm,
                  name=name, prepared=str(Path(prepared).resolve()), source_sha256=SOURCE_SHA,
                  component_index=entry["component_index"], run_seed=entry["run_seed"],
                  pins=manifest["pins"], argv=argv, started_utc=datetime.now(timezone.utc).isoformat(),
                  actual_prefill_games=0, actual_train_games=0, actual_validation_games=0)
    records = Path(prepared) / "run_records"
    records.mkdir(exist_ok=True)
    record_path = records / f"{name}.json"
    if record_path.exists():
        raise FileExistsError(record_path)
    audit = dict(schema_version=1, validations=[], before_train={}, source_config=manifest["source_config"],
                 training_config=entry["config"], initial_tensor_sha256=entry["tensor_sha256"],
                 inference_config_id=experiment.state_sha256(manifest["source_config"]),
                 rollout_config_id=experiment.state_sha256(entry["config"]))
    rollout_rows, validation_rows, learner_box, pending_opponents, files = [], [], [], [], []
    stop_requested = []
    saved_methods = []
    old_hooks = {key: getattr(finetune, key) for key in ("Learners", "play_game", "play_set", "make_opponent")}
    old_argv, old_train_base, old_val_base = sys.argv, finetune.FT_SEED_BASE, protocol.VAL_SEED_BASE
    old_signals = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
    missing = object()
    old_variant = VARIANTS.get(VARIANT, missing)

    def persist():
        record.update(actual_prefill_games=sum(r["phase"] == "prefill" for r in rollout_rows),
                      actual_train_games=sum(r["phase"] == "train" for r in rollout_rows),
                      actual_validation_games=len(validation_rows))
        if learner_box:
            a = _canonical(learner_box[0])
            record.update(env_steps=a.env_steps, learn_steps=a.learn_steps)
        record["updated_utc"] = datetime.now(timezone.utc).isoformat()
        _write(record_path, record)
        if destination.is_dir():
            _write(destination / "progress.json", record)
            _write(destination / "training_audit.json", audit)

    def stop_at_boundary():
        from scripts.fog_reward_supervisor import worker_guard
        worker_guard(supervisor_state, arm, name, prepared)
        if stop_requested:
            raise StudyInterrupted("SIGTERM requested; stopped at completed-game boundary")

    def load(variant, run_dir, run_seed, load=False):
        if learner_box or variant != VARIANT or Path(run_dir) != destination or run_seed != entry["run_seed"] or not load:
            raise ValueError("Unexpected learner construction")
        learners = old_hooks["Learners"](variant, run_dir, run_seed, load=load)
        learners.train_mode()
        audit["initial"] = prove_initial(learners, entry)
        a = _canonical(learners)
        original_save = a.save_agent
        saved_methods.append((a, vars(a).get("save_agent", missing)))
        def final_only_save(path=None):
            if len(rollout_rows) == len(entry["rollout_plan"]) and len(audit["validations"]) == 2:
                return original_save(path)
        a.save_agent = final_only_save
        learner_box.append(learners)
        files.extend([(destination / "rollouts.jsonl").open("x"),
                      (destination / "validation_games.jsonl").open("x")])
        persist()
        return learners

    def opponent(kind, side, *args, **kwargs):
        if pending_opponents:
            raise ValueError("Opponent construction is not paired with a rollout")
        pending_opponents.append((kind, side))
        return old_hooks["make_opponent"](kind, side, *args, **kwargs)

    def rollout(env, agent, opp, seed, side, train):
        stop_at_boundary()
        index = len(rollout_rows)
        if index >= len(entry["rollout_plan"]) or not learner_box:
            raise ValueError("Unexpected rollout count")
        expected = entry["rollout_plan"][index]
        a = _canonical(learner_box[0])
        if (agent is not a or not train or not a.training or a.cfg.to_dict() != entry["config"]
                or abs(a.epsilon - .05) > 1e-12 or a.autosave_on_terminate
                or a.learn_enabled != (expected["phase"] == "train")
                or seed != expected["seed"] or side != expected["side"]
                or pending_opponents != [(expected["opponent"], "player_1" if side == "player_0" else "player_0")]):
            raise ValueError("Actual rollout differs from fixed seed/side/opponent/config/learning plan")
        pending_opponents.clear()
        if expected["phase"] == "train" and expected["game"] % settings["val_every"] == 0:
            audit["before_train"][str(expected["game"])] = learner_identity(learner_box[0])
        before_env, before_learn = a.env_steps, a.learn_steps
        with action_audit(a) as action_proof, reward_audit(a) as reward_proof, trajectory_audit(env, a) as trajectory:
            row = old_hooks["play_game"](env, a, opp, seed, side, train=True)
        if (row["seed"] != seed or row["side"] != side or row["steps"] != 303
                or row.get("point_counting_version") != 2 or a.env_steps - before_env != 303
                or action_proof["act_calls"] != 303 or action_proof["update_calls"] != 303
                or reward_proof["transitions"] != action_proof["checked_replay_transitions"]
                or reward_proof["replay_transitions"] != action_proof["checked_replay_transitions"]
                or (expected["phase"] == "prefill" and a.learn_steps != before_learn)
                or (not smoke and expected["phase"] == "train" and a.learn_steps - before_learn != 150)):
            raise ValueError("Rollout counters/updates/point version differ from protocol")
        evidence = dict(row, **{k: v for k, v in expected.items() if k not in ("seed", "side")},
                        env_steps=a.env_steps, learn_steps=a.learn_steps,
                        effect_counters=dict(a.episode_stats()), action_audit=action_proof,
                        reward_audit=reward_proof, trajectory=trajectory,
                        inference_config_id=audit["inference_config_id"],
                        rollout_config_id=audit["rollout_config_id"],
                        updates=a.learn_steps-before_learn)
        rollout_rows.append(evidence)
        files[0].write(json.dumps(evidence, allow_nan=False) + "\n")
        files[0].flush()
        if expected["phase"] == "prefill" and expected["game"] == settings["prefill"] - 1:
            proof = learner_identity(learner_box[0])
            if not smoke:
                _prove_prefill(proof, audit["initial"], a)
            elif (proof["q_tensor_sha256"] != entry["tensor_sha256"] or a.learn_steps or a.opt.state):
                raise ValueError("Smoke prefill unexpectedly trained")
            audit["prefill"] = proof
            prefill = prefill_proof(arm, entry, audit, rollout_rows, a, smoke=smoke)
            bundle = dict(arm=arm, entry=entry, initial=audit["initial"], prefill=proof,
                          rows=rollout_rows, replay_without_reward_sha256=prefill["replay_without_reward_sha256"])
            _write(destination / "prefill_bundle.json", bundle)
            prefill["bundle_sha256"] = file_sha256(destination / "prefill_bundle.json")
            persist()
            _write(destination / "prefill_proof.json", prefill)
            wait_prefill(supervisor_state, arm, stop_at_boundary)
        persist()
        stop_at_boundary()
        return row

    def validate(env, learners, seeds, opponents, **kwargs):
        stop_at_boundary()
        _check_frozen(manifest)
        after = sum(r["phase"] == "train" for r in rollout_rows)
        expected = [r for r in manifest["validation_plan"] if r["after_games"] == after]
        if (not expected or list(seeds) != list(range(settings["val_base"], settings["val_base"] + settings["n_val"]))
                or tuple(opponents) != ("default", "solution92")
                or after in [r["after_games"] for r in audit["validations"]]):
            raise ValueError("Unexpected validation schedule")
        before = learner_identity(learners)
        completed = []
        try:
            rows = validate_v14(env, learners, seeds, opponents, manifest["source_config"],
                                completed_rows=completed, stop_check=stop_at_boundary)
        finally:
            for row in completed:
                evidence = dict(row, after_games=after)
                validation_rows.append(evidence)
                files[1].write(json.dumps(evidence, allow_nan=False) + "\n")
            files[1].flush()
            persist()
        observed = [{key: row[key] for key in ("after_games", "opponent", "seed", "side")}
                    for row in validation_rows[-len(expected):]]
        if (observed != expected or learner_identity(learners) != before
                or any(row.get("steps") != 303 or row.get("point_counting_version") != 2 for row in rows)):
            raise ValueError("Validation changed learning/RNG state or differs from complete plan")
        audit["validations"].append(dict(after_games=after, before=before, after=learner_identity(learners),
                                         config=manifest["source_config"]))
        persist()
        stop_at_boundary()
        return rows

    persist()
    try:
        VARIANTS[VARIANT] = ("sherlock", entry["config"])
        finetune.FT_SEED_BASE, protocol.VAL_SEED_BASE = settings["train_base"], settings["val_base"]
        finetune.Learners, finetune.play_game = load, rollout
        finetune.play_set, finetune.make_opponent = validate, opponent
        for sig in old_signals:
            signal.signal(sig, lambda *_: stop_requested.append(True))
        sys.argv = argv
        finetune.main()
        stop_at_boundary()
        _check_frozen(manifest)
        if (not learner_box or len(rollout_rows) != len(entry["rollout_plan"])
                or len(validation_rows) != len(manifest["validation_plan"])):
            raise ValueError("Incomplete learner/game counts; no complete receipt")
        a = _canonical(learner_box[0])
        if not smoke and a.learn_steps != settings["games"] * 150:
            raise ValueError("Final update count differs from full training budget")
        audit["end"] = _prove_end(learner_box[0], entry, audit["initial"],
                                  destination / "weights/agent.pth", rollout_rows)
        if audit["end"]["target_tensor_sha256"] == entry["tensor_sha256"]:
            raise ValueError("Final target did not change")
        shutil.rmtree(destination / "weights_best", ignore_errors=True)
        record.update(status="smoke_done" if smoke else "done", eligible=not smoke,
                      finished_utc=datetime.now(timezone.utc).isoformat())
        persist()
        receipt = dict(record, config=entry["config"], initial_tensor_sha256=entry["tensor_sha256"],
                       final_checkpoint_sha256=file_sha256(destination / "weights/agent.pth"),
                       rollouts_sha256=file_sha256(destination / "rollouts.jsonl"),
                       validation_sha256=file_sha256(destination / "validation_games.jsonl"),
                       audit_sha256=file_sha256(destination / "training_audit.json"))
        receipt["train_csv_sha256"] = file_sha256(destination / "train.csv")
        receipt["prefill_sha256"] = file_sha256(destination / "prefill_proof.json")
        _write(destination / ("smoke_receipt.json" if smoke else "final_receipt.json"), receipt)
        return record
    except BaseException as exc:
        record.update(status="incomplete", eligible=False, error=f"{type(exc).__name__}: {exc}",
                      finished_utc=datetime.now(timezone.utc).isoformat())
        if learner_box:
            try:
                a = _canonical(learner_box[0])
                type(a).save_agent(a, str(destination / "weights/partial_agent.pth"))
            except BaseException as save_error:
                record["checkpoint_save_error"] = f"{type(save_error).__name__}: {save_error}"
        persist()
        raise
    finally:
        for key, value in old_hooks.items():
            setattr(finetune, key, value)
        finetune.FT_SEED_BASE, protocol.VAL_SEED_BASE = old_train_base, old_val_base
        sys.argv = old_argv
        for sig, handler in old_signals.items():
            signal.signal(sig, handler)
        if old_variant is missing:
            VARIANTS.pop(VARIANT, None)
        else:
            VARIANTS[VARIANT] = old_variant
        for agent, method in saved_methods:
            if method is missing: vars(agent).pop("save_agent", None)
            else: agent.save_agent = method
        for handle in files:
            handle.close()


def validate_final_receipt(path: Path, *, arm: str | None = None) -> dict:
    """Read-only admission audit; no agent construction or games."""
    path = Path(path)
    receipt = json.loads(path.read_text())
    actual_arm = receipt.get("arm")
    seed, _ = _arm(actual_arm)
    component = 18
    expected = dict(status="done", eligible=True, smoke=False, source_sha256=SOURCE_SHA,
                    component_index=component, run_seed=seed, actual_prefill_games=40,
                    actual_train_games=400, actual_validation_games=32,
                    learn_steps=60000, env_steps=193320)
    if any(receipt.get(key) != value for key, value in expected.items()) or (arm is not None and actual_arm != arm):
        raise ValueError("Receipt is not an eligible complete production arm")
    directory = path.parent
    manifest, entry, _ = check_prepared(Path(receipt["prepared"]), actual_arm)
    if (receipt.get("config") != entry["config"] or receipt.get("pins") != manifest["pins"]
            or receipt.get("initial_tensor_sha256") != entry["tensor_sha256"]):
        raise ValueError("Final receipt is not bound to the exact prepared config/inputs")
    validate_prefill_bundle(directory, receipt["prepared"], actual_arm)
    for key, name in (("final_checkpoint_sha256", "weights/agent.pth"),
                      ("rollouts_sha256", "rollouts.jsonl"),
                      ("validation_sha256", "validation_games.jsonl"),
                      ("audit_sha256", "training_audit.json"),
                      ("train_csv_sha256", "train.csv"), ("prefill_sha256", "prefill_proof.json")):
        if file_sha256(directory / name) != receipt[key]:
            raise ValueError(f"Receipt evidence changed: {name}")
    rollouts = [json.loads(line) for line in (directory / "rollouts.jsonl").read_text().splitlines()]
    validations = [json.loads(line) for line in (directory / "validation_games.jsonl").read_text().splitlines()]
    if ([{k: row[k] for k in ("phase", "game", "seed", "side", "opponent")} for row in rollouts]
            != rollout_plan(actual_arm)
            or [{k: row[k] for k in ("after_games", "opponent", "seed", "side")} for row in validations]
            != validation_plan()
            or any(row.get("steps") != 303 or row.get("point_counting_version") != 2 for row in rollouts + validations)):
        raise ValueError("Receipt raw games differ from complete fixed schedule")
    cp = torch.load(directory / "weights/agent.pth", map_location="cpu", weights_only=True)
    _finite(cp)
    audit = json.loads((directory / "training_audit.json").read_text())
    end = audit.get("end", {})
    if (cp.get("cfg") != receipt["config"] or cp.get("ensemble") or cp.get("ensemble_dims")
            or cp.get("feature_dim") != 79 or cp.get("n_actions") != 6
            or cp.get("learn_steps") != 60000 or cp.get("env_steps") != 193320
            or not cp.get("opt", {}).get("state") or not end.get("reload_verified")
            or tensor_sha256(cp["q"]) == receipt["initial_tensor_sha256"]
            or tensor_sha256(cp["target_q"]) == receipt["initial_tensor_sha256"]
            or experiment.state_sha256(cp["opt"]) == audit["initial"]["learning"]["optimizer_sha256"]
            or tensor_sha256(cp["q"]) != end.get("q_tensor_sha256")
            or tensor_sha256(cp["target_q"]) != end.get("target_tensor_sha256")
            or experiment.state_sha256(cp["opt"]) != end.get("learning", {}).get("optimizer_sha256")
            or any(state["step"].item() != 60000 for state in cp["opt"]["state"].values())
            or end.get("saved_weights_sha256") != receipt["final_checkpoint_sha256"]):
        raise ValueError("Receipt lacks finite changed Q/Adam/saved/reloaded final proof")
    if [item["after_games"] for item in audit["validations"]] != [0, 400] or any(
            item["before"] != item["after"] for item in audit["validations"]):
        raise ValueError("Receipt lacks isolated validation identity proofs")
    inference_id=experiment.state_sha256(manifest['source_config'])
    rollout_id=experiment.state_sha256(entry['config'])
    for index,row in enumerate(rollouts):
        training=index>=40
        reward,actions,trajectory=row['reward_audit'],row['action_audit'],row['trajectory']
        mass=reward['unknown_sap_transitions']*.3
        applied=mass if entry['config']['fog_unknown_reward_neutral'] else 0.
        if (row['env_steps']!=60000+(index+1)*303 or row['learn_steps']!=max(0,index+1-40)*150
                or row['updates']!=(150 if training else 0)
                or row['inference_config_id']!=inference_id or row['rollout_config_id']!=rollout_id
                or actions['act_calls']!=303 or actions['update_calls']!=303
                or reward['transitions']!=actions['checked_replay_transitions']
                or reward['replay_transitions']!=reward['transitions']
                or trajectory['replay_pushes']!=reward['transitions']
                or trajectory['reset_calls']!=1 or trajectory['step_calls']!=303 or trajectory['act_calls']!=303
                or not math.isclose(reward['unknown_reward_mass'],mass,abs_tol=1e-7,rel_tol=1e-8)
                or not math.isclose(reward['applied_reward_mass'],applied,abs_tol=1e-7,rel_tol=1e-8)
                or reward['actual_reward_sha256']!=reward[('neutral' if applied else 'legacy')+'_reward_sha256']):
            raise ValueError('Persisted rollout chronology/reward/replay audit differs')
    for item in audit['validations']:
        after=item['after_games'];state=item['before']['learning']
        if (item['config']!=manifest['source_config'] or item['config']['fog_unknown_reward_neutral'] is not False
                or state['config']!=entry['config'] or state['env_steps']!=72120+after*303
                or state['learn_steps']!=after*150):
            raise ValueError('Validation does not prove V14 inference and unchanged fixed learning state')
    with (directory/'train.csv').open() as handle:
        train_rows=list(csv.DictReader(handle))
    if len(train_rows)!=400:
        raise ValueError('Incomplete training CSV')
    for index,row in enumerate(train_rows):
        expected=rollouts[40+index]
        if (int(row['game'])!=index or int(row['seed'])!=expected['seed'] or row['side']!=expected['side']
                or row['opponent']!=expected['opponent'] or int(row['steps'])!=303
                or int(row['learn_steps'])!=(index+1)*150 or int(row['env_steps'])!=72120+(index+1)*303
                or float(row['epsilon'])!=.05 or not math.isfinite(float(row['mean_loss']))):
            raise ValueError('Training CSV chronology or loss differs')
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--source", type=Path, default=ROOT / "agents/sherlock/weights/agent_p0.pth")
    prep.add_argument("--out", type=Path, required=True)
    run = commands.add_parser("run")
    run.add_argument("--prepared", type=Path, required=True)
    run.add_argument("--arm", choices=tuple(ARMS), required=True)
    run.add_argument("--name", required=True)
    run.add_argument("--supervisor-state", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.source, args.out)
        print(json.dumps(dict(prepared=str(args.out), smoke=result["smoke"], arms=list(result["arms"]))))
    else:
        print(json.dumps(run_arm(args.prepared, args.arm, args.name, supervisor_state=args.supervisor_state)))


if __name__ == "__main__":
    main()
