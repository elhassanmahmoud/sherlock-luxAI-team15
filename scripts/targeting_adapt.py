"""Fixed four-arm P/PT adaptation pilot; each runarm is an isolated child process.

The coordinator admits at most two children and enforces battery/deadline limits.
prepare never plays; runarm reuses finetune.main, with temporary in-memory hooks.
Only final checkpoints are eligible; this tool does not build or promote PT.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet, checkpoint_ensemble_dims
from scripts import experiment
from scripts.night_train_pilot import file_sha256, tensor_sha256
from scripts.output_paths import checked_output
from scripts.variants import VARIANTS
from scripts.variants import seed_everything

ROOT = Path(__file__).resolve().parent.parent
SOURCE_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
PROTOCOL = ROOT / "docs/superpowers/plans/2026-11-02-targeting-adaptation.md"
ARMS = {"control18": (18, 28, False), "adapt18": (18, 28, True),
        "control19": (19, 29, False), "adapt19": (19, 29, True)}
MIX = "solution92=0.6,sol92_sq=0.2,default=0.1,rush=0.1"
P_FLAGS = ("point_pair_swap", "art_move_guard")
EVAL_SEED = 20261102
_VARIANT = "targeting_adaptation_20261102"


def _arm(name: str) -> tuple:
    if name not in ARMS:
        raise ValueError(f"Unknown fixed arm: {name}")
    return ARMS[name]


def rollout_plan(arm: str) -> list[dict]:
    _, run_seed, _ = _arm(arm)
    rng = np.random.default_rng(run_seed + 4200)
    names = ["solution92", "sol92_sq", "default", "rush"]
    rows = []
    for phase, count, offset in (("prefill", 120, 5000), ("train", 600, 4200)):
        for game in range(count):
            rows.append(dict(phase=phase, game=game,
                             seed=200000 + 10000 * run_seed + offset + game // 2,
                             side=("player_0", "player_1")[game % 2],
                             opponent=names[rng.choice(4, p=[.6, .2, .1, .1])]))
    return rows


def validation_plan() -> list[dict]:
    return [dict(after_games=after, opponent=opponent, seed=seed, side=side)
            for after in (0, 300, 600) for opponent in ("default", "solution92")
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
               point_pair_swap=enabled, art_move_guard=enabled)
    return cfg


def _pins() -> dict:
    return dict(protocol_sha256=file_sha256(PROTOCOL),
                wrapper_sha256=file_sha256(Path(__file__)),
                git=experiment.git_info(), interpreter=str(Path(sys.executable).resolve()))


def prepare(source: Path, out: Path) -> dict:
    """Extract exactly components 18/19 into four new, role-explicit init dirs."""
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
        raise ValueError("Prepared source/four-arm binding mismatch")
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


def _canonical(learners):
    if (set(learners.agents) != {"player_0", "player_1"}
            or learners.agents["player_0"] is not learners.agents["player_1"]
            or len(learners.unique()) != 1):
        raise ValueError("Both sides must share one canonical learner")
    a = learners.agents["player_0"]
    if a.extra_q or a.cnn_policy is not None or not a.cfg.canonical:
        raise ValueError("Training requires one canonical Q network, without ensemble/CNN")
    return a


def learner_identity(learners) -> dict:
    a = _canonical(learners)
    _finite([a.q.state_dict(), a.target_q.state_dict(), a.opt.state_dict()])
    return dict(q_tensor_sha256=tensor_sha256(a.q.state_dict()),
                target_tensor_sha256=tensor_sha256(a.target_q.state_dict()),
                learning=experiment._learning_identity(a),
                agent_rng_sha256=experiment.state_sha256(a.rng.bit_generator.state),
                global_rng_sha256=experiment.state_sha256(experiment._global_rng_state()))


def prove_initial(learners, entry: dict) -> dict:
    a = _canonical(learners)
    proof = learner_identity(learners)
    q_params = {id(p) for p in a.q.parameters()}
    opt_params = [p for group in a.opt.param_groups for p in group["params"]]
    if (a.cfg.to_dict() != entry["config"] or not a.training or not a.learn_enabled
            or a.autosave_on_terminate or a.env_steps != 60000 or a.learn_steps != 0
            or a.recent_losses or a.buffer.size != 0 or a.buffer.pos != 0
            or a.buffer._mask_dim != 1 or type(a.opt) is not torch.optim.Adam
            or a.opt.state or not a.opt.param_groups
            or {id(p) for p in opt_params} != q_params or len(opt_params) != len(q_params)
            or any(g["lr"] != 1e-4 for g in a.opt.param_groups)
            or abs(a.epsilon - .05) > 1e-12
            or proof["q_tensor_sha256"] != entry["tensor_sha256"]
            or proof["target_tensor_sha256"] != entry["tensor_sha256"]):
        raise ValueError("Actual loaded learner violates initial tensor/config/Adam/replay proof")
    proof["initial_identity"] = experiment.initial_identity(learners)
    return proof


def isolated_validation(env, learners, seeds, opponents, *, completed_rows=None) -> list[dict]:
    """Common P evaluation; existing deep guards plus outer role/RNG restoration.

    The reused guard resets a fresh episode context; it does not reconstruct the
    prior completed episode's belief/context. No replay arrays are copied here.
    """
    a = _canonical(learners)
    flags = {flag: getattr(a.cfg, flag) for flag in P_FLAGS}
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
        for flag in P_FLAGS:
            setattr(a.cfg, flag, True)
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


def _prove_prefill(proof: dict, initial: dict, agent) -> None:
    if (proof["q_tensor_sha256"] != initial["q_tensor_sha256"]
            or proof["target_tensor_sha256"] != initial["target_tensor_sha256"]
            or proof["learning"]["optimizer_sha256"] != initial["learning"]["optimizer_sha256"]
            or agent.opt.state or agent.learn_steps or agent.recent_losses
            or agent.buffer.size <= agent.cfg.learn_start):
        raise ValueError("Prefill changed learning state or did not fill replay above learn_start")


def _prove_end(learners, entry: dict, initial: dict, path: Path, rollout_rows: list) -> dict:
    a = _canonical(learners)
    proof = learner_identity(learners)
    if (a.cfg.to_dict() != entry["config"] or a.learn_steps <= 0 or not a.opt.state
            or proof["q_tensor_sha256"] == initial["q_tensor_sha256"]
            or a.env_steps != 60000 + sum(row["steps"] for row in rollout_rows)
            or not a.learn_enabled or a.autosave_on_terminate):
        raise ValueError("End learner has wrong config/counters or no actual Q/Adam updates")
    if (len(a.opt.state) != len(list(a.q.parameters()))
            or any(set(state) != {"step", "exp_avg", "exp_avg_sq"}
                   or state["step"].item() != a.learn_steps for state in a.opt.state.values())):
        raise ValueError("End Adam moments/steps do not match actual learn_steps")
    cp = torch.load(path, map_location="cpu", weights_only=True)
    _finite(cp)
    if (cp.get("ensemble") or cp.get("ensemble_dims") or cp.get("feature_dim") != 79
            or cp.get("n_actions") != 6 or cp["cfg"] != entry["config"]
            or tensor_sha256(cp["q"]) != proof["q_tensor_sha256"]
            or tensor_sha256(cp["target_q"]) != proof["target_tensor_sha256"]
            or cp["env_steps"] != a.env_steps or cp["learn_steps"] != a.learn_steps
            or experiment.state_sha256(cp["opt"]) != proof["learning"]["optimizer_sha256"]):
        raise ValueError("Saved end checkpoint differs from the final live learner")
    # Exercise the actual loader as well, without allocating a second replay.
    a.load_agent(str(path))
    if learner_identity(learners) != proof:
        raise ValueError("Reloaded end state differs from the final live learner")
    proof["saved_weights_sha256"] = file_sha256(path)
    proof["reload_verified"] = True
    return proof


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
    argv = ["targeting_adapt/finetune", "--init", str(init), "--name", name,
            "--variant", _VARIANT, "--games", "600", "--seed", str(entry["run_seed"]),
            "--map-offset", "4200", "--lr", "0.0001", "--prefill-games", "120",
            "--keep-final", "--no-test", "--val-every", "300", "--n-val", "8", "--mix", MIX]
    records = Path(prepared) / "run_records"
    records.mkdir(exist_ok=True)
    record_path = records / f"{name}.json"
    if record_path.exists():
        raise FileExistsError(record_path)
    record = dict(status="running", arm=arm, name=name, argv=argv, pins=manifest["pins"],
                  source_sha256=manifest["source_sha256"],
                  source_tensor_sha256=manifest["source_tensor_sha256"],
                  component_index=entry["component_index"], run_seed=entry["run_seed"],
                  expected_learn_steps=90000, expected_env_steps=278160,
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
        _write(destination / "adaptation_audit.json", audit)

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
        if index >= 720 or not learner_box:
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
        if expected["phase"] == "train" and expected["game"] in (0, 299, 599):
            audit["before_train"][str(expected["game"] + 1)] = learner_identity(learner_box[0])
            persist_audit()
        before_env, before_learn = a.env_steps, a.learn_steps
        row = old_hooks["play_game"](env, agent, opp, seed, side, train=train)
        if (row["seed"] != seed or row["side"] != side or row["steps"] != 303
                or a.env_steps != before_env + row["steps"]
                or (expected["phase"] == "prefill" and a.learn_steps != before_learn)
                or (expected["phase"] == "train" and a.learn_steps <= before_learn)):
            raise ValueError("Actual episode steps/counters or learning updates violate protocol")
        evidence = dict(row, **{k: v for k, v in expected.items() if k not in ("seed", "side")},
                        effect_counters=dict(a.episode_stats()), identity=learner_identity(learner_box[0]))
        rollout_rows.append(evidence)
        append(files[0], evidence)
        if index == 119:
            audit["prefill"] = learner_identity(learner_box[0])
            _prove_prefill(audit["prefill"], audit["initial"], a)
            persist_audit()
        return row

    def validate(env, learners, seeds, opponents, **kwargs):
        after = len(rollout_rows) - 120
        if (learners is not learner_box[0] or after not in (0, 300, 600)
                or len(audit["validations"]) != (0, 300, 600).index(after)
                or list(seeds) != list(range(500000, 500008))
                or tuple(opponents) != ("default", "solution92") or kwargs):
            raise ValueError("Unexpected validation timing/maps/opponents")
        before = learner_identity(learners)
        completed = []
        eval_cfg = dict(entry["config"], point_pair_swap=True, art_move_guard=True)
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
        if len(rollout_rows) != 720 or len(validation_rows) != 96 or pending_opponents or len(learner_box) != 1:
            raise ValueError("Incomplete actual rollout/validation evidence")
        with (destination / "train.csv").open() as handle:
            train_rows = list(csv.DictReader(handle))
        if len(train_rows) != 600 or [int(r["game"]) for r in train_rows] != list(range(600)):
            raise ValueError("Missing/duplicate finetune training CSV rows")
        audit["end"] = _prove_end(learner_box[0], entry, audit["initial"],
                                  destination / "weights/agent.pth", rollout_rows)
        check_prepared(prepared, arm)
        record.update(status="done", actual_prefill_games=120, actual_train_games=600,
                      actual_validation_games=96, end=audit["end"],
                      counter_review_required=(audit["end"]["learning"]["learn_steps"] != 90000
                                               or audit["end"]["learning"]["env_steps"] != 278160))
        persist_audit()
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
    prep = sub.add_parser("prepare", help="Extract the fixed four-arm init tree without playing")
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
