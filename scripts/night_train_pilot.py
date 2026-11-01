"""Prepare and run the fixed November discovery-reward warm-start pilot.

Run from the project root, using the project's Python environment::

    python -m scripts.night_train_pilot prepare --source V14.pth --out experiments/runs/nov01_init
    python -m scripts.night_train_pilot runarm --init experiments/runs/nov01_init --arm control --name nov01_control
    python -m scripts.night_train_pilot runarm --init experiments/runs/nov01_init --arm discovery --name nov01_discovery

``prepare`` extracts component 18 (q is component 0) without its optimizer or
replay. Each ``runarm`` is one model process. The coordinator admits at most two
processes and enforces the shared two-hour wall-clock limit externally.
No released weights, global variants or existing runs are overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet, checkpoint_ensemble_dims
from scripts.output_paths import checked_output
from scripts.variants import VARIANTS

ROOT = Path(__file__).resolve().parent.parent
SOURCE_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
COMPONENT_INDEX = 18
MIX = "solution92=0.6,sol92_sq=0.2,default=0.1,rush=0.1"
_VARIANT = "full_rules_v14_nov01_pilot"


def file_sha256(path: Path) -> str:
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def tensor_sha256(state: dict) -> str:
    """Hash sorted tensor names, dtypes, dimensions and raw CPU bytes."""
    digest = hashlib.sha256()
    for key in sorted(state):
        tensor = state[key].detach().cpu().contiguous()
        header = json.dumps([key, str(tensor.dtype), list(tensor.shape)], separators=(",", ":"))
        digest.update(header.encode("utf-8") + b"\n")
        digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def prepare(source: Path, out: Path, *, expected_source_sha: str = SOURCE_SHA,
            component_index: int = COMPONENT_INDEX) -> dict:
    """Strictly extract a single component into a new warm-start directory."""
    source = Path(source).resolve(strict=True)
    if not source.is_file():
        raise FileNotFoundError(source)
    out = checked_output(Path(out), ROOT / "agents" / "sherlock" / "weights")
    if out.exists():
        raise FileExistsError(out)
    before = file_sha256(source)
    if before != expected_source_sha:
        raise ValueError(f"Source SHA mismatch: {before}")
    checkpoint = torch.load(source, map_location="cpu", weights_only=True)
    if not isinstance(checkpoint, dict) or checkpoint.get("feature_dim") != 79 or checkpoint.get("n_actions") != 6:
        raise ValueError("Source must have feature_dim=79 and n_actions=6")
    checkpoint_ensemble_dims(checkpoint, 79)
    states = [checkpoint["q"], *checkpoint.get("ensemble", [])]
    if isinstance(component_index, bool) or not isinstance(component_index, int) or not 0 <= component_index < len(states):
        raise ValueError(f"Invalid component index {component_index!r}; source has {len(states)} nets")

    cfg = AgentConfig(**checkpoint["cfg"]).to_dict()
    cfg.update(VARIANTS["full_rules_v12"][1])
    cfg.update(cand_rescue=True, rescue_after=30, frozen=False, lr=1e-4,
               w_discovery=0.5, w_explore=0.3)
    # Keep inference-only rules inference-only: main.py itself gates rescue on
    # ``not self.training``. Do not alter the action code for this reward study.
    if cfg["eps_end"] != 0.05:
        raise ValueError("Pilot requires epsilon floor 0.05")
    q = {key: value.detach().cpu().clone() for key, value in states[component_index].items()}
    with torch.random.fork_rng(devices=[]):
        model = QNet(79, 6, hidden=cfg["hidden"], dueling=cfg["dueling"])
        model.load_state_dict(q, strict=True)
    tensor_hash = tensor_sha256(q)
    prepared = dict(q=q, target_q={key: value.clone() for key, value in q.items()},
                    cfg=cfg, feature_dim=79, n_actions=6, ensemble=[], ensemble_dims=[],
                    env_steps=max(60_000, cfg["eps_decay_steps"]), learn_steps=0)
    if file_sha256(source) != before:
        raise ValueError("Source changed while preparing warm start")
    (out / "weights").mkdir(parents=True, exist_ok=False)
    weights = out / "weights" / "agent.pth"
    torch.save(prepared, weights)
    manifest = dict(
        name=out.name, variant=_VARIANT, base_variant=_VARIANT,
        kind="component_warm_start", train_games=0,
        source=str(source), source_sha256=before, component_index=component_index,
        tensor_sha256=tensor_hash, weights_sha256=file_sha256(weights),
        optimizer="fresh Adam; not resumed", replay="empty; arm-specific 120-game prefill",
        env_steps_note="normalized epsilon-floor counter; not a restored component training history",
        config=cfg, prepared_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    if file_sha256(source) != before:
        raise ValueError("Source changed while writing warm start")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def run_arm(init: Path, arm: str, name: str) -> None:
    """Validate the warm start and temporarily configure one fixed finetune arm."""
    if arm not in ("control", "discovery"):
        raise ValueError(f"Unknown pilot arm: {arm}")
    if not name or name in (".", "..") or Path(name).name != name:
        raise ValueError("Run name must be a single new directory name")
    from scripts import finetune

    destination = checked_output(finetune.RUNS / name, ROOT / "agents" / "sherlock" / "weights")
    if destination.exists():
        raise FileExistsError(destination)
    init = Path(init).resolve(strict=True)
    weights = init / "weights" / "agent.pth"
    if not weights.is_file():
        raise FileNotFoundError(weights)
    manifest = json.loads((init / "manifest.json").read_text())
    source = Path(manifest["source"])
    if file_sha256(source) != manifest["source_sha256"]:
        raise ValueError("Source changed since preparation")
    if file_sha256(weights) != manifest["weights_sha256"]:
        raise ValueError("Init weights changed since preparation")
    checkpoint = torch.load(weights, map_location="cpu", weights_only=True)
    if (checkpoint.get("ensemble") or "opt" in checkpoint
            or checkpoint.get("feature_dim") != 79 or checkpoint.get("n_actions") != 6
            or tensor_sha256(checkpoint["q"]) != manifest["tensor_sha256"]
            or tensor_sha256(checkpoint["target_q"]) != manifest["tensor_sha256"]):
        raise ValueError("Init is not the verified single-net fresh-optimizer warm start")
    if any((init / "weights").glob("*.npz")):
        raise ValueError("Warm start must not contain an old replay buffer")
    cfg = dict(checkpoint["cfg"])
    if cfg != manifest["config"] or cfg.get("frozen") or cfg.get("eps_end") != 0.05:
        raise ValueError("Init config differs from the verified training config")
    if checkpoint["env_steps"] < cfg["eps_decay_steps"]:
        raise ValueError("Warm-start epsilon must already be at its floor")
    cfg["w_discovery"] = 0.5 if arm == "control" else 2.0
    argv = ["night_train_pilot/finetune", "--init", str(init), "--name", name,
            "--variant", _VARIANT, "--games", "600", "--seed", "9", "--map-offset", "4200",
            "--lr", "0.0001", "--prefill-games", "120", "--keep-final", "--no-test",
            "--val-every", "300", "--n-val", "8", "--mix", MIX]
    record = dict(arm=arm, name=name, init=str(init), source_sha256=manifest["source_sha256"],
                  init_weights_sha256=manifest["weights_sha256"], tensor_sha256=manifest["tensor_sha256"],
                  component_index=manifest["component_index"], optimizer=manifest["optimizer"],
                  config=cfg, argv=argv, status="running",
                  started_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    plans = init / "arm_plans"
    plans.mkdir(exist_ok=True)
    record_path = plans / f"{name}.json"
    with record_path.open("x") as handle:
        json.dump(record, handle, indent=2)

    previous_argv = sys.argv
    sentinel = object()
    previous_variant = VARIANTS.get(_VARIANT, sentinel)
    try:
        VARIANTS[_VARIANT] = ("sherlock", cfg)
        sys.argv = argv
        finetune.main()
        if file_sha256(source) != manifest["source_sha256"] or file_sha256(weights) != manifest["weights_sha256"]:
            raise ValueError("Source or init changed during pilot")
        record["status"] = "done"
    except BaseException as exc:
        record.update(status="incomplete", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        sys.argv = previous_argv
        if previous_variant is sentinel:
            VARIANTS.pop(_VARIANT, None)
        else:
            VARIANTS[_VARIANT] = previous_variant
        record["finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        record_path.write_text(json.dumps(record, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)
    prep = subparsers.add_parser("prepare", help="Extract fixed V14 component 18 into a NEW init directory")
    prep.add_argument("--source", type=Path, required=True)
    prep.add_argument("--out", type=Path, required=True)
    run = subparsers.add_parser("runarm", help="Run ONE fixed 600-game arm; external admission/deadline required")
    run.add_argument("--init", type=Path, required=True)
    run.add_argument("--arm", choices=("control", "discovery"), required=True)
    run.add_argument("--name", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        print(json.dumps(prepare(args.source, args.out), indent=2))
    else:
        run_arm(args.init, args.arm, args.name)


if __name__ == "__main__":
    main()
