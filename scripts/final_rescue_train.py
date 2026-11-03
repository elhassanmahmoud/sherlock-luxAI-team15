"""Fixed paired rescue-alignment pilot; each runarm is an isolated child process.

The coordinator admits at most two children and enforces battery/deadline limits.
prepare never plays; runarm reuses finetune.main, with temporary in-memory hooks.
Only verified final checkpoints receive a receipt; this tool never promotes weights.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
from contextlib import contextmanager
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet, checkpoint_ensemble_dims
from scripts import experiment
from scripts.night_train_pilot import file_sha256, tensor_sha256
from scripts.output_paths import checked_output
from scripts.variants import VARIANTS
from scripts.variants import seed_everything

ROOT = Path(__file__).resolve().parent.parent
SOURCE_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
PROTOCOL = ROOT / "docs/superpowers/plans/2026-11-03-final-battle.md"
ARMS = {"control18": (18, 29, False), "adapt18": (18, 29, True)}
MIX = "solution92=0.6,sol92_sq=0.2,default=0.1,rush=0.1"
EVAL_FLAGS = {"point_pair_swap": False, "art_move_guard": False,
              "zone_rescue": False, "rescue_in_training": False}
EVAL_SEED = 20261103
_VARIANT = "final_rescue_alignment_20261103"


def _arm(name: str) -> tuple:
    if name not in ARMS:
        raise ValueError(f"Unknown fixed arm: {name}")
    return ARMS[name]


def rollout_plan(arm: str) -> list[dict]:
    _, run_seed, _ = _arm(arm)
    rng = np.random.default_rng(run_seed + 3000)
    names = ["solution92", "sol92_sq", "default", "rush"]
    rows = []
    for phase, count, offset in (("prefill", 120, 5000), ("train", 1200, 3000)):
        for game in range(count):
            rows.append(dict(phase=phase, game=game,
                             seed=200000 + 10000 * run_seed + offset + game // 2,
                             side=("player_0", "player_1")[game % 2],
                             opponent=names[rng.choice(4, p=[.6, .2, .1, .1])]))
    return rows


def validation_plan() -> list[dict]:
    return [dict(after_games=after, opponent=opponent, seed=seed, side=side)
            for after in (0, 600, 1200) for opponent in ("default", "solution92")
            for seed in range(500000, 500008) for side in ("player_0", "player_1")]


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def _finite(value) -> None:
    if isinstance(value, torch.Tensor) and not torch.isfinite(value).all():
        raise ValueError("Nonfinite tensor in learner/checkpoint")
    if isinstance(value, dict):
        for child in value.values():
            _finite(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _finite(child)


def _source(source: Path) -> tuple[dict, list, dict]:
    if file_sha256(source) != SOURCE_SHA:
        raise ValueError("Source SHA mismatch")
    cp = torch.load(source, map_location="cpu", weights_only=True)
    if cp.get("feature_dim") != 79 or cp.get("n_actions") != 6:
        raise ValueError("Source must have 79 features / 6 actions")
    dims = checkpoint_ensemble_dims(cp, 79)
    states = [cp["q"], *cp.get("ensemble", [])]
    if len(states) != 36 or dims != [79] * 35:
        raise ValueError("Source must have exactly 36 homogeneous nets")
    cfg = AgentConfig(**cp["cfg"]).to_dict()
    if (not cfg["canonical"] or cfg["eps_end"] != .05
            or cfg["eps_decay_steps"] != 60000 or cfg["learn_start"] != 5000):
        raise ValueError("Source config violates fixed canonical/epsilon/learn-start protocol")
    with torch.random.fork_rng(devices=[]):
        model = QNet(79, 6, hidden=cfg["hidden"], dueling=cfg["dueling"])
        for state in states:
            _finite(state)
            model.load_state_dict(state, strict=True)
    if file_sha256(source) != SOURCE_SHA:
        raise ValueError("Source changed during inspection")
    return cp, states, cfg


def _config(source_cfg: dict, enabled: bool) -> dict:
    cfg = dict(source_cfg)
    cfg.update(frozen=False, lr=1e-4, w_discovery=.5, w_explore=.3,
               rules_in_training=True, rules_in_training_all=True,
               point_pair_swap=False, art_move_guard=False, zone_rescue=False,
               cand_rescue=True, rescue_after=30, rescue_in_training=enabled)
    return cfg


def _pins() -> dict:
    return dict(protocol_sha256=file_sha256(PROTOCOL),
                wrapper_sha256=file_sha256(Path(__file__)),
                dependency_sha256={name: file_sha256(ROOT / name) for name in (
                    "scripts/targeting_adapt.py", "scripts/finetune.py", "scripts/experiment.py",
                    "scripts/common.py", "agents/sherlock/main.py", "agents/sherlock/config.py")},
                git=experiment.git_info(), interpreter=str(Path(sys.executable).resolve()))


def prepare(source: Path, out: Path) -> dict:
    """Extract component 18 into two new, role-explicit init dirs."""
    source = Path(source).resolve(strict=True)
    out = checked_output(out, ROOT / "agents/sherlock/weights")
    if out.exists():
        raise FileExistsError(out)
    _, states, source_cfg = _source(source)
    manifest = dict(schema_version=1, source=str(source), source_sha256=SOURCE_SHA,
                    source_config=source_cfg,
                    source_tensor_sha256=[tensor_sha256(s) for s in states],
                    pins=_pins(), validation_plan=validation_plan(), arms={})
    for name, (component, seed, enabled) in ARMS.items():
        cfg = _config(source_cfg, enabled)
        q = {key: tensor.detach().cpu().clone() for key, tensor in states[component].items()}
        checkpoint = dict(q=q, target_q=copy.deepcopy(q), cfg=cfg, feature_dim=79,
                          n_actions=6, ensemble=[], ensemble_dims=[], env_steps=60000, learn_steps=0)
        init = out / name
        (init / "weights").mkdir(parents=True, exist_ok=False)
        weights = init / "weights/agent.pth"
        torch.save(checkpoint, weights)
        entry = dict(component_index=component, run_seed=seed, config=cfg,
                     tensor_sha256=tensor_sha256(q), weights_sha256=file_sha256(weights),
                     rollout_plan=rollout_plan(name))
        manifest["arms"][name] = entry
        _write(init / "manifest.json", dict(variant=_VARIANT, base_variant=_VARIANT,
                                           train_games=0, arm=name, **entry))
    if file_sha256(source) != SOURCE_SHA:
        raise ValueError("Source changed during prepare")
    _write(out / "manifest.json", manifest)
    return manifest


def check_prepared(prepared: Path, arm: str) -> tuple[dict, dict, Path]:
    """Recheck source membership, full config, empty init and frozen plans."""
    component, seed, enabled = _arm(arm)
    prepared = Path(prepared).resolve(strict=True)
    manifest = json.loads((prepared / "manifest.json").read_text())
    if manifest["source_sha256"] != SOURCE_SHA or set(manifest["arms"]) != set(ARMS):
        raise ValueError("Prepared source/two-arm binding mismatch")
    _, states, source_cfg = _source(Path(manifest["source"]))
    if (manifest["source_tensor_sha256"] != [tensor_sha256(s) for s in states]
            or manifest["source_config"] != source_cfg
            or manifest["validation_plan"] != validation_plan()):
        raise ValueError("Prepared source tensors/config/validation plan mismatch")
    pins = _pins()
    if any(manifest["pins"][key] != pins[key] for key in pins):
        raise ValueError("Protocol, wrapper, HEAD or interpreter changed since prepare")
    entry = manifest["arms"][arm]
    expected_cfg = _config(source_cfg, enabled)
    expected_tensor = tensor_sha256(states[component])
    if (entry["component_index"] != component or entry["run_seed"] != seed
            or entry["config"] != expected_cfg or entry["tensor_sha256"] != expected_tensor
            or entry["rollout_plan"] != rollout_plan(arm)):
        raise ValueError("Prepared arm component/config/plan mismatch")
    init = prepared / arm
    weights = init / "weights/agent.pth"
    if {p.name for p in (init / "weights").iterdir()} != {"agent.pth"}:
        raise ValueError("Init must contain only agent.pth, without replay or other weights")
    if file_sha256(weights) != entry["weights_sha256"]:
        raise ValueError("Init weight SHA mismatch")
    cp = torch.load(weights, map_location="cpu", weights_only=True)
    if (set(cp) != {"q", "target_q", "cfg", "feature_dim", "n_actions", "ensemble",
                    "ensemble_dims", "env_steps", "learn_steps"}
            or cp["ensemble"] or cp["ensemble_dims"] or cp["feature_dim"] != 79
            or cp["n_actions"] != 6 or cp["env_steps"] != 60000 or cp["learn_steps"] != 0
            or cp["cfg"] != expected_cfg or tensor_sha256(cp["q"]) != expected_tensor
            or tensor_sha256(cp["target_q"]) != expected_tensor):
        raise ValueError("Init is not the exact fresh single-component warm start")
    local = json.loads((init / "manifest.json").read_text())
    if local != dict(variant=_VARIANT, base_variant=_VARIANT, train_games=0, arm=arm, **entry):
        raise ValueError("Init manifest differs from prepared arm")
    return manifest, entry, init


# Identity/optimizer/replay proofs are shared with the reviewed historical wrapper.
from scripts.targeting_adapt import (
    _canonical, learner_identity, prove_initial, _prove_prefill, _prove_end,
)


def isolated_validation(env, learners, seeds, opponents, *, completed_rows=None) -> list[dict]:
    """Common V14 evaluation; existing deep guards plus outer role/RNG restoration.

    The reused guard resets a fresh episode context; it does not reconstruct the
    prior completed episode's belief/context. No replay arrays are copied here.
    """
    a = _canonical(learners)
    flags = {flag: getattr(a.cfg, flag) for flag in EVAL_FLAGS}
    own_rng = copy.deepcopy(a.rng.bit_generator.state)
    global_rng = experiment._global_rng_state()
    learning = a.learn_enabled
    original_game = experiment.play_game

    def measured_game(*args, **kwargs):
        row = original_game(*args, **kwargs)
        row["effect_counters"] = dict(a.episode_stats())
        if completed_rows is not None:
            # play_set adds the actual opponent label to this same row after
            # return. Keep completed rows even when a later episode fails.
            completed_rows.append(row)
        return row

    try:
        for flag in EVAL_FLAGS:
            setattr(a.cfg, flag, EVAL_FLAGS[flag])
        a.learn_enabled = False
        a.rng.bit_generator.state = np.random.default_rng(EVAL_SEED).bit_generator.state
        seed_everything(EVAL_SEED)
        experiment.play_game = measured_game
        return experiment.run_validation(env, learners, seeds, opponents, isolate=True)
    finally:
        experiment.play_game = original_game
        for flag, value in flags.items():
            setattr(a.cfg, flag, value)
        a.learn_enabled = learning
        a.rng.bit_generator.state = own_rng
        experiment._restore_global_rng(global_rng)


@contextmanager
def action_audit(agent):
    """Verify returned world actions and every corresponding replay write.

    This observes the real act/update boundary, without modifying actions or RNG.
    The digest records canonical actions, emitted actions and the actual buffer
    values in their original order. No full-game arrays are retained.
    """
    original_act, original_update = agent.act, agent.update
    missing = object()
    prior_act = agent.__dict__.get("act", missing)
    prior_update = agent.__dict__.get("update", missing)
    digest = hashlib.sha256()
    pending = []
    proof = dict(act_calls=0, update_calls=0, checked_replay_transitions=0,
                 transcript_sha256=None)

    def act(*args, **kwargs):
        if pending:
            raise ValueError("Action was not followed by its replay update")
        actions = original_act(*args, **kwargs)
        expected = []
        for uid in agent._prev_feats:
            canonical = int(agent._prev_actions[uid])
            emitted = int(actions[uid, 0])
            want = geo.mirror_dir(canonical) if agent.belief.mirrored and canonical < 5 else canonical
            if emitted != want:
                raise ValueError("Emitted final action differs from the recorded replay action")
            expected.append((int(uid), canonical, emitted))
        pending.append((np.array(actions, copy=True), expected))
        proof["act_calls"] += 1
        return actions

    def update(*args, **kwargs):
        if len(pending) != 1:
            raise ValueError("Replay update has no unique preceding action")
        emitted, expected = pending[0]
        actual = kwargs.get("action", args[3] if len(args) > 3 else None)
        if actual is None or not np.array_equal(actual, emitted):
            raise ValueError("Update received a different final action")
        position = agent.buffer.pos
        original_update(*args, **kwargs)
        count = len(expected)
        if agent.buffer.pos != (position + count) % agent.buffer.capacity:
            raise ValueError("Replay write count differs from the acted units")
        stored = [int(agent.buffer.a[(position + i) % agent.buffer.capacity]) for i in range(count)]
        if stored != [entry[1] for entry in expected]:
            raise ValueError("Actual replay actions differ from emitted final actions")
        digest.update(json.dumps([proof["update_calls"], expected, stored], separators=(",", ":")).encode())
        pending.clear()
        proof["update_calls"] += 1
        proof["checked_replay_transitions"] += count

    agent.act, agent.update = act, update
    try:
        yield proof
        if pending:
            raise ValueError("Unfinished final-action/replay evidence")
    finally:
        for key, old in (("act", prior_act), ("update", prior_update)):
            if old is missing:
                agent.__dict__.pop(key, None)
            else:
                setattr(agent, key, old)
        proof["transcript_sha256"] = digest.hexdigest()


def write_final_receipt(destination, prepared, arm, manifest, entry, audit, rollouts):
    """Issue a receipt only after live, saved and reloaded end proofs succeed."""
    counters = [row["effect_counters"] for row in rollouts]
    action_proofs = [row["final_action_audit"] for row in rollouts]
    rescue_units = sum(row.get("training_rescue_unit_steps", 0) for row in counters)
    rescue_changes = sum(row.get("training_rescue_action_changes", 0) for row in counters)
    train_changes = sum(row["effect_counters"].get("training_rescue_action_changes", 0)
                        for row in rollouts if row["phase"] == "train")
    if arm == "adapt18" and (rescue_units <= 0 or train_changes <= 0):
        raise ValueError("Treatment completed without actual training rescue interventions")
    if arm == "control18" and (rescue_units or rescue_changes):
        raise ValueError("Control unexpectedly executed training rescue interventions")
    end = audit["end"]
    checkpoint = (destination / "weights/agent.pth").resolve()
    receipt = dict(
        schema_version=1, status="done", arm=arm, prepared=str(Path(prepared).resolve()),
        source_sha256=manifest["source_sha256"], component_index=18,
        source_tensor_sha256=entry["tensor_sha256"], init_weights_sha256=entry["weights_sha256"],
        final_checkpoint=str(checkpoint), final_checkpoint_sha256=file_sha256(checkpoint),
        final_tensor_sha256=end["q_tensor_sha256"],
        actual_train_games=1200, actual_prefill_games=120, actual_validation_games=96,
        learn_steps=end["learning"]["learn_steps"], env_steps=end["learning"]["env_steps"],
        rollout_plan_sha256=experiment.state_sha256(entry["rollout_plan"]),
        rescue_in_training=entry["config"]["rescue_in_training"],
        rescue_unit_steps=rescue_units, rescue_action_changes=rescue_changes,
        final_action_audit=dict(
            act_calls=sum(row["act_calls"] for row in action_proofs),
            update_calls=sum(row["update_calls"] for row in action_proofs),
            checked_replay_transitions=sum(row["checked_replay_transitions"] for row in action_proofs),
            transcript_sha256=experiment.state_sha256([row["transcript_sha256"] for row in action_proofs])),
        audit_sha256=file_sha256(destination / "rescue_training_audit.json"),
        rollouts_sha256=file_sha256(destination / "rollouts.jsonl"),
        validation_sha256=file_sha256(destination / "validation_games.jsonl"),
        train_csv_sha256=file_sha256(destination / "train.csv"), pins=manifest["pins"],
    )
    path = destination / "final_receipt.json"
    with path.open("x") as handle:
        json.dump(receipt, handle, indent=2, allow_nan=False)
    try:
        validate_final_receipt(path, arm=arm)
    except BaseException:
        path.unlink()  # no successful receipt remains after failed verification
        raise
    return path


def validate_final_receipt(receipt_path: Path, *, arm: str) -> dict:
    """Fail closed on incomplete, swapped, stale or modified training outputs."""
    _arm(arm)
    path = Path(receipt_path).resolve(strict=True)
    receipt = json.loads(path.read_text())
    required = dict(schema_version=1, status="done", arm=arm, component_index=18,
                    source_sha256=SOURCE_SHA, actual_train_games=1200,
                    actual_prefill_games=120, actual_validation_games=96,
                    learn_steps=180000, env_steps=459960,
                    rescue_in_training=(arm == "adapt18"))
    if any(receipt.get(key) != value for key, value in required.items()):
        raise ValueError("Incomplete or wrong-role final training receipt")
    directory = path.parent
    for key, filename in (("audit_sha256", "rescue_training_audit.json"),
                          ("rollouts_sha256", "rollouts.jsonl"),
                          ("validation_sha256", "validation_games.jsonl"),
                          ("train_csv_sha256", "train.csv")):
        if receipt.get(key) != file_sha256(directory / filename):
            raise ValueError(f"Final receipt artifact changed: {filename}")
    manifest, entry, _ = check_prepared(Path(receipt["prepared"]), arm)
    if (receipt["source_tensor_sha256"] != entry["tensor_sha256"]
            or receipt["init_weights_sha256"] != entry["weights_sha256"]
            or receipt["pins"] != manifest["pins"]
            or receipt["rollout_plan_sha256"] != experiment.state_sha256(entry["rollout_plan"])):
        raise ValueError("Final receipt does not match the fixed prepared arm")
    checkpoint = Path(receipt["final_checkpoint"]).resolve(strict=True)
    if (checkpoint != (directory / "weights/agent.pth").resolve(strict=True)
            or file_sha256(checkpoint) != receipt["final_checkpoint_sha256"]):
        raise ValueError("Final checkpoint path/hash does not match receipt")
    cp = torch.load(checkpoint, map_location="cpu", weights_only=True)
    _finite(cp)
    if (cp.get("cfg") != entry["config"] or cp.get("ensemble") or cp.get("ensemble_dims")
            or cp.get("feature_dim") != 79 or cp.get("n_actions") != 6
            or cp.get("learn_steps") != 180000 or cp.get("env_steps") != 459960
            or tensor_sha256(cp["q"]) != receipt["final_tensor_sha256"]
            or receipt["final_tensor_sha256"] == receipt["source_tensor_sha256"]):
        raise ValueError("Final checkpoint is not the verified trained component")
    audit = json.loads((directory / "rescue_training_audit.json").read_text())
    end = audit.get("end", {})
    if (audit.get("arm") != arm or not end.get("reload_verified")
            or end.get("saved_weights_sha256") != receipt["final_checkpoint_sha256"]
            or end.get("q_tensor_sha256") != receipt["final_tensor_sha256"]
            or tensor_sha256(cp["target_q"]) != end.get("target_tensor_sha256")
            or experiment.state_sha256(cp["opt"]) != end.get("learning", {}).get("optimizer_sha256")):
        raise ValueError("Final receipt lacks matching live/saved/reloaded proof")
    rollouts = [json.loads(line) for line in (directory / "rollouts.jsonl").read_text().splitlines()]
    validations = [json.loads(line) for line in (directory / "validation_games.jsonl").read_text().splitlines()]
    plan = rollout_plan(arm)
    if (len(rollouts) != 1320 or any({key: row[key] for key in expected} != expected
                                  for row, expected in zip(rollouts, plan))
            or any(row["steps"] != 303 or row.get("point_counting_version") != 2 for row in rollouts)
            or [{key: row[key] for key in ("after_games", "opponent", "seed", "side")}
                for row in validations] != validation_plan()):
        raise ValueError("Final receipt chronology is incomplete or differs from fixed plans")
    with (directory / "train.csv").open() as handle:
        reader = csv.DictReader(handle)
        train_fields = reader.fieldnames
        train_rows = list(reader)
    if (train_fields != experiment.TRAIN_FIELDS or len(train_rows) != 1200
            or [int(row["game"]) for row in train_rows] != list(range(1200))):
        raise ValueError("Final training CSV is incomplete or duplicated")
    _validate_learning_evidence(cp, entry, audit, rollouts, validations, train_rows)
    proofs = [row["final_action_audit"] for row in rollouts]
    expected_audit = dict(
        act_calls=sum(row["act_calls"] for row in proofs),
        update_calls=sum(row["update_calls"] for row in proofs),
        checked_replay_transitions=sum(row["checked_replay_transitions"] for row in proofs),
        transcript_sha256=experiment.state_sha256([row["transcript_sha256"] for row in proofs]))
    if (any(row["act_calls"] != 303 or row["update_calls"] != 303 for row in proofs)
            or expected_audit["checked_replay_transitions"] <= 0
            or receipt["final_action_audit"] != expected_audit):
        raise ValueError("Final action/replay evidence is incomplete")
    units = sum(row["effect_counters"].get("training_rescue_unit_steps", 0) for row in rollouts)
    changes = sum(row["effect_counters"].get("training_rescue_action_changes", 0) for row in rollouts)
    train_changes = sum(row["effect_counters"].get("training_rescue_action_changes", 0)
                        for row in rollouts if row["phase"] == "train")
    if (receipt["rescue_unit_steps"] != units or receipt["rescue_action_changes"] != changes
            or (arm == "adapt18" and (units <= 0 or train_changes <= 0))
            or (arm == "control18" and (units or changes))):
        raise ValueError("Final rescue intervention evidence contradicts assigned arm")
    return receipt


def _validate_learning_evidence(cp, entry, audit, rollouts, validations, train_rows):
    """Independently cross-check persisted live proofs, not just their hashes."""
    def need(condition, message):
        if not condition:
            raise ValueError(message)

    try:
        cfg = entry["config"]
        with torch.random.fork_rng(devices=[]):
            model = QNet(79, 6, hidden=cfg["hidden"], dueling=cfg["dueling"])
            fresh_optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
            fresh_hash = experiment.state_sha256(fresh_optimizer.state_dict())
        optimizer = cp["opt"]
        groups = optimizer["param_groups"]
        need(len(groups) == 1 and groups[0]["lr"] == 1e-4, "Saved Adam configuration differs")
        parameters = list(model.parameters())
        indices = groups[0]["params"]
        need(len(indices) == len(parameters) and len(set(indices)) == len(indices)
             and set(optimizer["state"]) == set(indices), "Saved Adam lacks actual parameter moments")
        for index, parameter in zip(indices, parameters):
            state = optimizer["state"][index]
            need(set(state) == {"step", "exp_avg", "exp_avg_sq"}
                 and state["step"].numel() == 1 and state["step"].item() == 180000
                 and state["exp_avg"].shape == parameter.shape
                 and state["exp_avg_sq"].shape == parameter.shape,
                 "Saved Adam moments/steps differ from completed training")

        initial, prefill = audit["initial"], audit["prefill"]
        il, pl = initial["learning"], prefill["learning"]
        need(initial["q_tensor_sha256"] == initial["target_tensor_sha256"] == entry["tensor_sha256"]
             and il["optimizer_sha256"] == fresh_hash and il["env_steps"] == 60000
             and il["learn_steps"] == 0 and il["learn_enabled"] is True
             and il["autosave_on_terminate"] is False and il["recent_losses"] == []
             and il["config"] == cfg and il["replay"]["size"] == il["replay"]["pos"] == 0
             and il["replay"]["_mask_dim"] == 1, "Missing fresh initial learner/Adam/replay proof")
        init_entries = initial["initial_identity"]["learners"]
        need(len(init_entries) == 1 and init_entries[0]["sides"] == ["player_0", "player_1"]
             and init_entries[0]["optimizer_sha256"] == fresh_hash
             and init_entries[0]["replay"]["logical_content"] == "empty-replay-v1",
             "Missing shared canonical fresh-learner proof")
        need(prefill["q_tensor_sha256"] == initial["q_tensor_sha256"]
             and prefill["target_tensor_sha256"] == initial["target_tensor_sha256"]
             and pl["optimizer_sha256"] == fresh_hash and pl["learn_steps"] == 0
             and pl["env_steps"] == 96360 and pl["learn_enabled"] is False
             and pl["replay"]["size"] > cfg["learn_start"]
             and pl["recent_losses"] == [] and pl["config"] == cfg,
             "Prefill proof lacks unchanged tensors/Adam and filled replay")
        for i, row in enumerate(rollouts):
            learning = row["identity"]["learning"]
            training = i >= 120
            need(set(experiment.GAME_FIELDS) <= set(row)
                 and learning["config"] == cfg and learning["learn_enabled"] is training
                 and learning["autosave_on_terminate"] is False
                 and learning["env_steps"] == 60000 + (i + 1) * 303
                 and learning["learn_steps"] == max(0, i - 119) * 150,
                 "Rollout learning/schema chronology differs from actual fixed updates")
            if not training:
                need(row["identity"]["q_tensor_sha256"] == entry["tensor_sha256"]
                     and row["identity"]["target_tensor_sha256"] == entry["tensor_sha256"]
                     and learning["optimizer_sha256"] == fresh_hash,
                     "Prefill rollout changed learning state")
        need(prefill == rollouts[119]["identity"], "Prefill summary differs from actual last prefill")
        before_train = audit["before_train"]
        need(set(before_train) == {"1", "600", "1200"}, "Missing scheduled before-training proofs")
        for label, completed in (("1", 0), ("600", 599), ("1200", 1199)):
            identity = before_train[label]
            learning = identity["learning"]
            preceding = rollouts[119 + completed]["identity"]
            need(learning["env_steps"] == 96360 + completed * 303
                 and learning["learn_steps"] == completed * 150
                 and learning["config"] == cfg and learning["learn_enabled"] is True
                 and identity["q_tensor_sha256"] == preceding["q_tensor_sha256"]
                 and identity["target_tensor_sha256"] == preceding["target_tensor_sha256"]
                 and learning["optimizer_sha256"] == preceding["learning"]["optimizer_sha256"],
                 "Before-training proof differs from completed rollout history")
        checks = audit["validations"]
        need(len(checks) == 3, "Missing isolated validation proofs")
        for proof, after in zip(checks, (0, 600, 1200)):
            learning = proof["before"]["learning"]
            need(proof["after_games"] == after and proof["before"] == proof["after"]
                 and learning["env_steps"] == 96360 + after * 303
                 and learning["learn_steps"] == after * 150 and learning["config"] == cfg
                 and proof["eval_config"] == dict(cfg, **EVAL_FLAGS)
                 and proof["eval_rng_seed"] == EVAL_SEED,
                 "Validation changed learning/RNG or lacks scheduled evidence")
        for row in validations:
            need(set(experiment.GAME_FIELDS) <= set(row) and row["steps"] == 303
                 and row["point_counting_version"] == 2 and row["epsilon"] == 0.
                 and row["learn_enabled"] is False and row["config"] == dict(cfg, **EVAL_FLAGS)
                 and row["eval_rng_seed"] == EVAL_SEED, "Validation game/schema is incomplete")
        for i, row in enumerate(train_rows):
            expected = rollouts[120 + i]
            need(int(row["seed"]) == expected["seed"] and row["side"] == expected["side"]
                 and row["opponent"] == expected["opponent"] and int(row["steps"]) == 303
                 and int(row["point_counting_version"]) == 2
                 and int(row["env_steps"]) == 96360 + (i + 1) * 303
                 and int(row["learn_steps"]) == (i + 1) * 150
                 and float(row["epsilon"]) == .05
                 and np.isfinite(float(row["mean_loss"])), "Training CSV differs from proved rollouts")
        end = audit["end"]
        need(end["learning"]["env_steps"] == 459960 and end["learning"]["learn_steps"] == 180000
             and end["learning"]["config"] == cfg and end["learning"]["learn_enabled"] is True
             and end["q_tensor_sha256"] == rollouts[-1]["identity"]["q_tensor_sha256"]
             and end["target_tensor_sha256"] == rollouts[-1]["identity"]["target_tensor_sha256"]
             and end["learning"]["optimizer_sha256"] == rollouts[-1]["identity"]["learning"]["optimizer_sha256"],
             "Final live proof differs from completed rollout history")
    except (KeyError, TypeError, IndexError, AttributeError) as exc:
        raise ValueError("Incomplete or malformed persisted learning evidence") from exc


def run_arm(prepared: Path, arm: str, name: str) -> dict:
    """One fixed arm in the coordinator's child; never launch extra workers."""
    from scripts import finetune

    _arm(arm)
    if not name or name in (".", "..") or Path(name).name != name:
        raise ValueError("Run name must be one new directory name")
    destination = checked_output(finetune.RUNS / name, ROOT / "agents/sherlock/weights")
    if destination.exists():
        raise FileExistsError(destination)
    manifest, entry, init = check_prepared(prepared, arm)
    argv = ["final_rescue_train/finetune", "--init", str(init), "--name", name,
            "--variant", _VARIANT, "--games", "1200", "--seed", str(entry["run_seed"]),
            "--map-offset", "3000", "--lr", "0.0001", "--prefill-games", "120",
            "--keep-final", "--no-test", "--val-every", "600", "--n-val", "8", "--mix", MIX]
    records = Path(prepared) / "run_records"
    records.mkdir(exist_ok=True)
    record_path = records / f"{name}.json"
    if record_path.exists():
        raise FileExistsError(record_path)
    record = dict(status="running", arm=arm, name=name, argv=argv, pins=manifest["pins"],
                  source_sha256=manifest["source_sha256"],
                  source_tensor_sha256=manifest["source_tensor_sha256"],
                  component_index=entry["component_index"], run_seed=entry["run_seed"],
                  expected_learn_steps=180000, expected_env_steps=459960,
                  init_weights_sha256=entry["weights_sha256"], config=entry["config"],
                  rollout_plan_sha256=experiment.state_sha256(entry["rollout_plan"]),
                  validation_plan_sha256=experiment.state_sha256(validation_plan()),
                  started_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    with record_path.open("x") as handle:
        json.dump(record, handle, indent=2)
    audit = dict(arm=arm, before_train={}, validations=[],
                 episode_restoration="fresh context via experiment.run_validation; no prior belief reconstruction")
    rollout_rows, validation_rows, pending_opponents = [], [], []
    learner_box = []
    files = []
    old_hooks = {key: getattr(finetune, key) for key in ("Learners", "play_game", "play_set", "make_opponent")}
    old_argv = sys.argv
    missing = object()
    old_variant = VARIANTS.get(_VARIANT, missing)

    def persist_audit():
        _write(destination / "rescue_training_audit.json", audit)

    def append(handle, row):
        handle.write(json.dumps(row, allow_nan=False) + "\n")
        handle.flush()

    def load(variant, run_dir, run_seed, load=False):
        if learner_box or variant != _VARIANT or Path(run_dir) != destination or run_seed != entry["run_seed"] or not load:
            raise ValueError("Unexpected learner construction/reload during finetune")
        learners = old_hooks["Learners"](variant, run_dir, run_seed, load=load)
        audit["initial"] = prove_initial(learners, entry)
        learner_box.append(learners)
        files.extend([(destination / "rollouts.jsonl").open("x"),
                      (destination / "validation_games.jsonl").open("x")])
        persist_audit()
        return learners

    def opponent(kind, side, *args, **kwargs):
        if pending_opponents:
            raise ValueError("Unexpected opponent construction before rollout")
        pending_opponents.append((kind, side))
        return old_hooks["make_opponent"](kind, side, *args, **kwargs)

    def rollout(env, agent, opp, seed, side, train):
        index = len(rollout_rows)
        if index >= 1320 or not learner_box:
            raise ValueError("Unexpected rollout count/learner")
        expected = entry["rollout_plan"][index]
        expected_opp = (expected["opponent"], "player_1" if side == "player_0" else "player_0")
        a = _canonical(learner_box[0])
        if (agent is not a or not train or not a.training or a.cfg.to_dict() != entry["config"]
                or abs(a.epsilon - .05) > 1e-12 or a.autosave_on_terminate
                or a.learn_enabled != (expected["phase"] == "train")
                or seed != expected["seed"] or side != expected["side"]
                or pending_opponents != [expected_opp]):
            raise ValueError("Actual rollout config/flags/map/side/opponent/learning differs from fixed plan")
        pending_opponents.clear()
        if expected["phase"] == "train" and expected["game"] in (0, 599, 1199):
            audit["before_train"][str(expected["game"] + 1)] = learner_identity(learner_box[0])
            persist_audit()
        before_env, before_learn = a.env_steps, a.learn_steps
        with action_audit(a) as action_proof:
            row = old_hooks["play_game"](env, agent, opp, seed, side, train=train)
        if action_proof["act_calls"] != 303 or action_proof["update_calls"] != 303:
            raise ValueError("Actual action/update calls differ from the 303-step episode")
        if (row["seed"] != seed or row["side"] != side or row["steps"] != 303
                or a.env_steps != before_env + row["steps"]
                or (expected["phase"] == "prefill" and a.learn_steps != before_learn)
                or (expected["phase"] == "train" and a.learn_steps != before_learn + 150)):
            raise ValueError("Actual episode steps/counters or learning updates violate protocol")
        evidence = dict(row, **{k: v for k, v in expected.items() if k not in ("seed", "side")},
                        effect_counters=dict(a.episode_stats()), final_action_audit=action_proof,
                        identity=learner_identity(learner_box[0]))
        rollout_rows.append(evidence)
        append(files[0], evidence)
        if index == 119:
            audit["prefill"] = learner_identity(learner_box[0])
            _prove_prefill(audit["prefill"], audit["initial"], a)
            persist_audit()
        return row

    def validate(env, learners, seeds, opponents, **kwargs):
        after = len(rollout_rows) - 120
        if (learners is not learner_box[0] or after not in (0, 600, 1200)
                or len(audit["validations"]) != (0, 600, 1200).index(after)
                or list(seeds) != list(range(500000, 500008))
                or tuple(opponents) != ("default", "solution92") or kwargs):
            raise ValueError("Unexpected validation timing/maps/opponents")
        before = learner_identity(learners)
        completed = []
        eval_cfg = dict(entry["config"], **EVAL_FLAGS)
        try:
            rows = isolated_validation(env, learners, seeds, opponents, completed_rows=completed)
        finally:
            # finetune calls eval_mode before this hook and lacks its own
            # finally around play_set; an exception must also restore rollout mode.
            learners.train_mode()
            for row in completed:
                evidence = dict(row, after_games=after, config=eval_cfg,
                                eval_rng_seed=EVAL_SEED, epsilon=0., learn_enabled=False)
                append(files[1], evidence)
                validation_rows.append(evidence)
        after_identity = learner_identity(learners)
        if before != after_identity:
            raise ValueError("Validation changed rollout learning/RNG identity")
        expected_rows = [r for r in validation_plan() if r["after_games"] == after]
        keys = [dict(after_games=after, opponent=r["opponent"], seed=r["seed"], side=r["side"]) for r in rows]
        if keys != expected_rows:
            raise ValueError("Raw validation games differ from the fixed 32-game plan")
        audit["validations"].append(dict(after_games=after, before=before, after=after_identity,
                                         eval_config=eval_cfg, eval_rng_seed=EVAL_SEED))
        persist_audit()
        return rows

    try:
        VARIANTS[_VARIANT] = ("sherlock", entry["config"])
        finetune.Learners, finetune.play_game = load, rollout
        finetune.play_set, finetune.make_opponent = validate, opponent
        sys.argv = argv
        finetune.main()
        if len(rollout_rows) != 1320 or len(validation_rows) != 96 or pending_opponents or len(learner_box) != 1:
            raise ValueError("Incomplete actual rollout/validation evidence")
        with (destination / "train.csv").open() as handle:
            train_rows = list(csv.DictReader(handle))
        if len(train_rows) != 1200 or [int(r["game"]) for r in train_rows] != list(range(1200)):
            raise ValueError("Missing/duplicate finetune training CSV rows")
        audit["end"] = _prove_end(learner_box[0], entry, audit["initial"],
                                  destination / "weights/agent.pth", rollout_rows)
        check_prepared(prepared, arm)
        if (audit["end"]["learning"]["learn_steps"] != 180000
                or audit["end"]["learning"]["env_steps"] != 459960):
            raise ValueError("Final update/env counters differ from the fixed schedule")
        record.update(status="done", actual_prefill_games=120, actual_train_games=1200,
                      actual_validation_games=96, end=audit["end"],
                      counter_review_required=(audit["end"]["learning"]["learn_steps"] != 180000
                                               or audit["end"]["learning"]["env_steps"] != 459960))
        persist_audit()
        receipt = write_final_receipt(destination, prepared, arm, manifest, entry, audit, rollout_rows)
        record["final_receipt"] = str(receipt)
    except BaseException as exc:
        record.update(status="incomplete", error=f"{type(exc).__name__}: {exc}",
                      actual_rollout_games=len(rollout_rows), actual_validation_games=len(validation_rows))
        raise
    finally:
        sys.argv = old_argv
        for key, value in old_hooks.items():
            setattr(finetune, key, value)
        if old_variant is missing:
            VARIANTS.pop(_VARIANT, None)
        else:
            VARIANTS[_VARIANT] = old_variant
        for handle in files:
            handle.close()
        record["finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        _write(record_path, record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="Extract the fixed paired init tree without playing")
    prep.add_argument("--source", type=Path, required=True)
    prep.add_argument("--out", type=Path, required=True)
    run = sub.add_parser("runarm", help="One child process; coordinator admission/deadline required")
    run.add_argument("--prepared", type=Path, required=True)
    run.add_argument("--arm", choices=tuple(ARMS), required=True)
    run.add_argument("--name", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.source, args.out)
    else:
        run_arm(args.prepared, args.arm, args.name)


if __name__ == "__main__":
    main()
