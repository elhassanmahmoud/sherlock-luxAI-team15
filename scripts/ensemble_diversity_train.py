"""Six fresh V14 warm starts, two opponent mixtures, experiment outputs only.

Each ``run`` is one child process. An external supervisor admits at most two.
Existing training switches are enabled; art_splash remains inference-only.
Smoke jobs use separate maps and can never receive a production receipt.
"""
from __future__ import annotations

import argparse
import copy
import json
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

ROOT = Path(__file__).resolve().parent.parent
SOURCE_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
VARIANT = "ensemble_diversity_20261107"
ARMS = {f"{mix}{family}": (18 + family * 6, family * 2 + offset, mix)
        for family in range(3) for offset, mix in enumerate(("A", "B"))}
MIXES = {"A": {"solution92": .7, "sol92_sq": .2, "default": .1},
         "B": {"solution92": .4, "sol92_weak": .2, "rush": .2, "default": .2}}
TRAIN_BASE, VALIDATION_BASE = 1_100_000, 1_300_000
SMOKE_TRAIN_BASE, SMOKE_VALIDATION_BASE = 1_190_000, 1_390_000


class StudyInterrupted(RuntimeError):
    """A requested stop was observed at a completed-game boundary."""


def _settings(smoke: bool) -> dict:
    return dict(games=2 if smoke else 3000, prefill=2 if smoke else 120,
                val_every=2 if smoke else 1000, n_val=1 if smoke else 8,
                train_base=SMOKE_TRAIN_BASE if smoke else TRAIN_BASE,
                val_base=SMOKE_VALIDATION_BASE if smoke else VALIDATION_BASE)


def _arm(arm: str) -> tuple:
    if arm not in ARMS:
        raise ValueError(f"Unknown arm: {arm}")
    return ARMS[arm]


def rollout_plan(arm: str, *, smoke: bool = False) -> list[dict]:
    _, seed, mixture = _arm(arm)
    settings, mix = _settings(smoke), MIXES[mixture]
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


def _write(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def _safe_output(path: Path) -> Path:
    for protected in (ROOT / "agents/sherlock/weights", ROOT / "agents/Gruppe15", ROOT / "Gruppe15"):
        path = checked_output(path, protected)
    return path


def _pins() -> dict:
    sources = sorted(set((ROOT / "scripts").glob("*.py")) |
                     set((ROOT / "agents/sherlock").glob("*.py")))
    sources += [ROOT / f"docs/superpowers/{kind}/2026-11-07-ensemble-diversity.md"
                for kind in ("specs", "plans")]
    return dict(source_sha256={str(path.relative_to(ROOT)): file_sha256(path)
                               for path in sources if path.is_file()},
                git_commit=experiment.git_info()["commit"],
                interpreter=str(Path(sys.executable).resolve()),
                interpreter_sha256=file_sha256(Path(sys.executable).resolve()))


def _check_frozen(manifest: dict) -> None:
    if file_sha256(Path(manifest["source"])) != manifest["source_sha256"]:
        raise ValueError("Source weights changed during study")
    if _pins() != manifest["pins"]:
        raise ValueError("Frozen source, HEAD or interpreter changed during study")


def _source(path: Path) -> tuple[dict, list, dict]:
    if file_sha256(path) != SOURCE_SHA:
        raise ValueError("Source SHA mismatch; exact V14 required")
    cp = torch.load(path, map_location="cpu", weights_only=True)
    states = [cp["q"], *cp.get("ensemble", [])]
    if (cp.get("feature_dim") != 79 or cp.get("n_actions") != 6 or len(states) != 36
            or checkpoint_ensemble_dims(cp, 79) != [79] * 35):
        raise ValueError("Source must contain exactly 36 homogeneous 79-feature/6-action nets")
    cfg = AgentConfig.from_dict(cp["cfg"]).to_dict()
    if not cfg["canonical"] or cfg["eps_end"] != .05 or cfg["eps_decay_steps"] != 60000:
        raise ValueError("Source violates canonical/epsilon-floor assumptions")
    with torch.random.fork_rng(devices=[]):
        model = QNet(79, 6, hidden=cfg["hidden"], dueling=cfg["dueling"])
        for state in states:
            _finite(state)
            model.load_state_dict(state, strict=True)
    return cp, states, cfg


def _training_config(source_cfg: dict) -> dict:
    return dict(source_cfg, frozen=False, lr=5e-5, rules_in_training=True,
                rules_in_training_all=True, rescue_in_training=True)


def prepare(source: Path, out: Path, *, smoke: bool = False) -> dict:
    source = Path(source).resolve(strict=True)
    out = _safe_output(out)
    if out.exists():
        raise FileExistsError(out)
    _, states, source_cfg = _source(source)
    config = _training_config(source_cfg)
    manifest = dict(schema_version=1, source=str(source), source_sha256=SOURCE_SHA,
                    source_config=source_cfg, smoke=bool(smoke), settings=_settings(smoke),
                    pins=_pins(), validation_plan=validation_plan(smoke=smoke), arms={})
    for arm, (component, seed, mixture) in ARMS.items():
        q = copy.deepcopy(states[component])
        checkpoint = dict(q=q, target_q=copy.deepcopy(q), cfg=config, feature_dim=79,
                          n_actions=6, ensemble=[], ensemble_dims=[], env_steps=60000, learn_steps=0)
        init = out / arm
        (init / "weights").mkdir(parents=True, exist_ok=False)
        weights = init / "weights/agent.pth"
        torch.save(checkpoint, weights)
        entry = dict(component_index=component, run_seed=seed, mixture=mixture,
                     mix=MIXES[mixture], config=config, tensor_sha256=tensor_sha256(q),
                     weights_sha256=file_sha256(weights), rollout_plan=rollout_plan(arm, smoke=smoke))
        manifest["arms"][arm] = entry
        _write(init / "manifest.json", dict(variant=VARIANT, base_variant=VARIANT,
                                           train_games=0, arm=arm, **entry))
    _check_frozen(manifest)
    _write(out / "manifest.json", manifest)
    return manifest


def check_prepared(prepared: Path, arm: str, *, smoke: bool = False) -> tuple[dict, dict, Path]:
    component, seed, mixture = _arm(arm)
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
    expected = dict(component_index=component, run_seed=seed, mixture=mixture,
                    mix=MIXES[mixture], config=_training_config(source_cfg),
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


def prove_initial(learners, entry: dict) -> dict:
    """Inspect the actual loaded online/target/Adam/replay state, before any games."""
    a = _canonical(learners)
    proof = learner_identity(learners)
    q_params = {id(p) for p in a.q.parameters()}
    opt_params = [p for group in a.opt.param_groups for p in group["params"]]
    if (a.cfg.to_dict() != entry["config"] or not a.training or not a.learn_enabled
            or a.autosave_on_terminate or a.env_steps != 60000 or a.learn_steps != 0
            or a.recent_losses or a.buffer.size or a.buffer.pos or a.buffer._mask_dim != 1
            or type(a.opt) is not torch.optim.Adam or a.opt.state or not a.opt.param_groups
            or {id(p) for p in opt_params} != q_params or len(opt_params) != len(q_params)
            or any(g["lr"] != entry["config"]["lr"] for g in a.opt.param_groups)
            or abs(a.epsilon - .05) > 1e-12
            or proof["q_tensor_sha256"] != entry["tensor_sha256"]
            or proof["target_tensor_sha256"] != entry["tensor_sha256"]):
        raise ValueError("Actual initial learner is not the fresh intended Q/target/Adam/replay state")
    proof["initial_identity"] = experiment.initial_identity(learners)
    return proof


def validate_v14(env, learners, seeds, opponents, source_cfg, *, completed_rows=None, stop_check=None):
    """Evaluate with exact normalized V14 cfg; restore all learning/RNG state."""
    a = _canonical(learners)
    training_cfg = a.cfg
    original_game = experiment.play_game

    def checked_game(*args, **kwargs):
        # Check BEFORE the next game: the reused measurement hook must first
        # append the previous completed row, even when it received SIGTERM.
        if stop_check is not None:
            stop_check()
        return original_game(*args, **kwargs)

    try:
        a.cfg = AgentConfig.from_dict(source_cfg)
        experiment.play_game = checked_game
        return isolated_validation(env, learners, seeds, opponents, completed_rows=completed_rows)
    finally:
        experiment.play_game = original_game
        a.cfg = training_cfg


def run_arm(prepared: Path, arm: str, name: str, *, smoke: bool = False) -> dict:
    from scripts import finetune

    if not name or name in (".", "..") or Path(name).name != name:
        raise ValueError("Run name must be a single new directory name")
    destination = _safe_output(finetune.RUNS / name)
    if destination.exists():
        raise FileExistsError(destination)
    manifest, entry, init = check_prepared(prepared, arm, smoke=smoke)
    settings = _settings(smoke)
    mix_text = ",".join(f"{key}={value}" for key, value in entry["mix"].items())
    argv = ["ensemble_diversity_train/finetune", "--init", str(init), "--name", name,
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
                 art_splash_training="inference-only in existing agent; unchanged")
    rollout_rows, validation_rows, learner_box, pending_opponents, files = [], [], [], [], []
    stop_requested = []
    old_hooks = {key: getattr(finetune, key) for key in ("Learners", "play_game", "play_set", "make_opponent")}
    old_argv, old_train_base, old_val_base = sys.argv, finetune.FT_SEED_BASE, protocol.VAL_SEED_BASE
    old_sigterm = signal.getsignal(signal.SIGTERM)
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
        if stop_requested:
            raise StudyInterrupted("SIGTERM requested; stopped at completed-game boundary")

    def load(variant, run_dir, run_seed, load=False):
        if learner_box or variant != VARIANT or Path(run_dir) != destination or run_seed != entry["run_seed"] or not load:
            raise ValueError("Unexpected learner construction")
        learners = old_hooks["Learners"](variant, run_dir, run_seed, load=load)
        learners.train_mode()
        audit["initial"] = prove_initial(learners, entry)
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
        with action_audit(a) as action_proof:
            row = old_hooks["play_game"](env, a, opp, seed, side, train=True)
        if (row["seed"] != seed or row["side"] != side or row["steps"] != 303
                or row.get("point_counting_version") != 2 or a.env_steps - before_env != 303
                or (expected["phase"] == "prefill" and a.learn_steps != before_learn)
                or (not smoke and expected["phase"] == "train" and a.learn_steps - before_learn != 150)):
            raise ValueError("Rollout counters/updates/point version differ from protocol")
        evidence = dict(row, **{k: v for k, v in expected.items() if k not in ("seed", "side")},
                        env_steps=a.env_steps, learn_steps=a.learn_steps,
                        effect_counters=dict(a.episode_stats()), action_audit=action_proof)
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
        signal.signal(signal.SIGTERM, lambda *_: stop_requested.append(True))
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
        record.update(status="smoke_done" if smoke else "done", eligible=not smoke,
                      finished_utc=datetime.now(timezone.utc).isoformat())
        persist()
        receipt = dict(record, config=entry["config"], initial_tensor_sha256=entry["tensor_sha256"],
                       final_checkpoint_sha256=file_sha256(destination / "weights/agent.pth"),
                       rollouts_sha256=file_sha256(destination / "rollouts.jsonl"),
                       validation_sha256=file_sha256(destination / "validation_games.jsonl"),
                       audit_sha256=file_sha256(destination / "training_audit.json"))
        _write(destination / ("smoke_receipt.json" if smoke else "final_receipt.json"), receipt)
        return record
    except BaseException as exc:
        record.update(status="incomplete", eligible=False, error=f"{type(exc).__name__}: {exc}",
                      finished_utc=datetime.now(timezone.utc).isoformat())
        if learner_box:
            try:
                learner_box[0].save()
            except BaseException as save_error:
                record["checkpoint_save_error"] = f"{type(save_error).__name__}: {save_error}"
        persist()
        raise
    finally:
        for key, value in old_hooks.items():
            setattr(finetune, key, value)
        finetune.FT_SEED_BASE, protocol.VAL_SEED_BASE = old_train_base, old_val_base
        sys.argv = old_argv
        signal.signal(signal.SIGTERM, old_sigterm)
        if old_variant is missing:
            VARIANTS.pop(VARIANT, None)
        else:
            VARIANTS[VARIANT] = old_variant
        for handle in files:
            handle.close()


def validate_final_receipt(path: Path, *, arm: str | None = None) -> dict:
    """Read-only admission audit; no agent construction or games."""
    path = Path(path)
    receipt = json.loads(path.read_text())
    actual_arm = receipt.get("arm")
    component, seed, _ = _arm(actual_arm)
    expected = dict(status="done", eligible=True, smoke=False, source_sha256=SOURCE_SHA,
                    component_index=component, run_seed=seed, actual_prefill_games=120,
                    actual_train_games=3000, actual_validation_games=128,
                    learn_steps=450000, env_steps=1005360)
    if any(receipt.get(key) != value for key, value in expected.items()) or (arm is not None and actual_arm != arm):
        raise ValueError("Receipt is not an eligible complete production arm")
    directory = path.parent
    for key, name in (("final_checkpoint_sha256", "weights/agent.pth"),
                      ("rollouts_sha256", "rollouts.jsonl"),
                      ("validation_sha256", "validation_games.jsonl"),
                      ("audit_sha256", "training_audit.json")):
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
            or cp.get("learn_steps") != 450000 or cp.get("env_steps") != 1005360
            or not cp.get("opt", {}).get("state") or not end.get("reload_verified")
            or tensor_sha256(cp["q"]) == receipt["initial_tensor_sha256"]
            or tensor_sha256(cp["q"]) != end.get("q_tensor_sha256")
            or tensor_sha256(cp["target_q"]) != end.get("target_tensor_sha256")
            or experiment.state_sha256(cp["opt"]) != end.get("learning", {}).get("optimizer_sha256")
            or any(state["step"].item() != 450000 for state in cp["opt"]["state"].values())
            or end.get("saved_weights_sha256") != receipt["final_checkpoint_sha256"]):
        raise ValueError("Receipt lacks finite changed Q/Adam/saved/reloaded final proof")
    if [item["after_games"] for item in audit["validations"]] != [0, 1000, 2000, 3000] or any(
            item["before"] != item["after"] for item in audit["validations"]):
        raise ValueError("Receipt lacks isolated validation identity proofs")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--source", type=Path, default=ROOT / "agents/sherlock/weights/agent_p0.pth")
    prep.add_argument("--out", type=Path, required=True)
    prep.add_argument("--smoke", action="store_true")
    run = commands.add_parser("run")
    run.add_argument("--prepared", type=Path, required=True)
    run.add_argument("--arm", choices=tuple(ARMS), required=True)
    run.add_argument("--name", required=True)
    run.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.source, args.out, smoke=args.smoke)
        print(json.dumps(dict(prepared=str(args.out), smoke=result["smoke"], arms=list(result["arms"]))))
    else:
        print(json.dumps(run_arm(args.prepared, args.arm, args.name, smoke=args.smoke)))


if __name__ == "__main__":
    main()
