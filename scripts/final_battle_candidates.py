"""Build the fixed November 3 candidates from an immutable, pinned V14 source.

No game, forward pass, optimizer, or training is performed. Outputs are inference
artifacts, not resumable training runs. Index 0 is q; other indices address the
ordered ensemble. Training candidates require both independently audited arms.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import torch

from scripts.output_paths import checked_output

ROOT = Path(__file__).resolve().parent.parent
SOURCE_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
ROSTERS = {
    "PAIR18": (0,1,3,6,8,10,13,15,16,18,19,21,24,26,28,31,33,34),
    "PAIR24": (0,1,3,5,6,7,8,10,13,15,16,17,18,19,21,23,24,25,26,28,31,33,34,35),
    "FT18": tuple(range(18,36)),
    "Z36": tuple(range(36)),
}


def file_sha256(path: Path) -> str:
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def tensor_sha256(state: dict) -> str:
    """Same ordered tensor digest format as the existing November evidence."""
    digest = hashlib.sha256()
    for key in sorted(state):
        tensor = state[key].detach().cpu().contiguous()
        header = json.dumps([key, str(tensor.dtype), list(tensor.shape)], separators=(",", ":"))
        digest.update(header.encode() + b"\n")
        digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def _validate_state(state: dict, hidden: int) -> None:
    shapes = {
        "body.0.weight": (hidden,79), "body.0.bias": (hidden,),
        "body.2.weight": (hidden,hidden), "body.2.bias": (hidden,),
        "value.0.weight": (128,hidden), "value.0.bias": (128,),
        "value.2.weight": (1,128), "value.2.bias": (1,),
        "adv.0.weight": (128,hidden), "adv.0.bias": (128,),
        "adv.2.weight": (6,128), "adv.2.bias": (6,),
    }
    if not isinstance(state, dict) or set(state) != set(shapes):
        raise ValueError("Unexpected DuelingDQN state keys")
    for name, shape in shapes.items():
        tensor = state[name]
        if (not isinstance(tensor, torch.Tensor) or tuple(tensor.shape) != shape
                or tensor.dtype != torch.float32 or not torch.isfinite(tensor).all().item()):
            raise ValueError(f"Invalid shape, dtype, or finite values for {name}")


def load_source(source: Path) -> tuple[dict, list[dict], list[str]]:
    """Read and validate all source states, without constructing an agent."""
    if file_sha256(source) != SOURCE_SHA:
        raise ValueError("V14 source SHA mismatch")
    cp = torch.load(source, map_location="cpu", weights_only=True)
    if not isinstance(cp, dict) or cp.get("feature_dim") != 79 or cp.get("n_actions") != 6:
        raise ValueError("V14 must have 79 features and 6 actions")
    if not isinstance(cp.get("ensemble"), list) or len(cp["ensemble"]) != 35:
        raise ValueError("V14 must contain exactly 36 ordered members")
    if cp.get("ensemble_dims") not in (None, []) and cp["ensemble_dims"] != [79] * 35:
        raise ValueError("V14 member dimensions differ from 79")
    cfg = cp.get("cfg", {})
    hidden = cfg.get("hidden")
    if type(hidden) is not int or hidden <= 0 or cfg.get("dueling") is not True:
        raise ValueError("V14 must use a DuelingDQN architecture")
    if (cfg.get("zone_rescue", False) or cfg.get("point_pair_swap", False)
            or cfg.get("art_move_guard", False) or cfg.get("rescue_in_training", False)):
        raise ValueError("Unexpected experimental flags in raw V14")
    states = [cp["q"], *cp["ensemble"]]
    for state in states:
        _validate_state(state, hidden)
    hashes = [tensor_sha256(state) for state in states]
    if len(set(hashes)) != 36:
        raise ValueError("V14 contains duplicate tensor members")
    if file_sha256(source) != SOURCE_SHA:
        raise ValueError("V14 source SHA changed during reading")
    return cp, states, hashes


def _output_path(out: Path, source: Path) -> Path:
    lexical = Path(out).expanduser().absolute()
    allowed = ROOT / "experiments/ensembles"
    resolved = checked_output(lexical, ROOT / "agents/sherlock/weights")
    if not lexical.is_relative_to(allowed.absolute()) or not resolved.is_relative_to(allowed.resolve()):
        raise ValueError("Candidate output must be a new directory under experiments/ensembles")
    for ancestor in (lexical, *lexical.parents):
        if ancestor == ROOT.absolute():
            break
        if ancestor.is_symlink():
            raise ValueError("Candidate output must not traverse a symbolic link")
    if resolved.exists():
        raise FileExistsError(resolved)
    if source.is_relative_to(resolved):
        raise ValueError("Output directory contains the source")
    return resolved


def _trained_inputs(control: Path, rescue: Path, source_hashes: list[str], cfg: dict) -> dict:
    # The training wrapper owns the complete rollout/reload receipt audit.
    from scripts.final_rescue_train import validate_final_receipt

    admitted = {}
    for name, path, arm, enabled in (
            ("C36", control, "control18", False), ("R36", rescue, "adapt18", True)):
        path = Path(path).resolve(strict=True)
        if not path.is_relative_to((ROOT / "experiments/runs").resolve()):
            raise ValueError("Training inputs must be experiment run checkpoints")
        receipt_path = path.parent.parent / "final_receipt.json"
        receipt_before = file_sha256(receipt_path)
        receipt = validate_final_receipt(receipt_path, arm=arm)
        if (receipt.get("status") != "done" or receipt.get("arm") != arm
                or receipt.get("source_sha256") != SOURCE_SHA
                or receipt.get("component_index") != 18
                or receipt.get("source_tensor_sha256") != source_hashes[18]
                or receipt.get("rescue_in_training") is not enabled
                or Path(receipt["final_checkpoint"]).resolve() != path):
            raise ValueError(f"{name}: training receipt role or provenance mismatch")
        for key, expected in {"actual_train_games":1200, "actual_prefill_games":120,
                              "actual_validation_games":96, "learn_steps":180000,
                              "env_steps":459960}.items():
            if type(receipt.get(key)) is not int or receipt[key] != expected:
                raise ValueError(f"{name}: incomplete training count {key}")
        cp = torch.load(path, map_location="cpu", weights_only=True)
        if (cp.get("feature_dim") != 79 or cp.get("n_actions") != 6
                or cp.get("ensemble", []) or cp.get("ensemble_dims", [])
                or cp.get("learn_steps") != 180000 or cp.get("env_steps") != 459960):
            raise ValueError(f"{name}: final single-member checkpoint/count mismatch")
        _validate_state(cp["q"], cfg["hidden"])
        digest = tensor_sha256(cp["q"])
        if (digest != receipt.get("final_tensor_sha256")
                or file_sha256(path) != receipt.get("final_checkpoint_sha256")
                or file_sha256(receipt_path) != receipt_before or digest in source_hashes):
            raise ValueError(f"{name}: final tensor/checkpoint/receipt identity mismatch")
        admitted[name] = dict(state=cp["q"], path=path, receipt=receipt,
                              receipt_path=receipt_path, receipt_sha256=receipt_before)
    if tensor_sha256(admitted["C36"]["state"]) == tensor_sha256(admitted["R36"]["state"]):
        raise ValueError("Control and rescue unexpectedly contain identical final tensors")
    if admitted["C36"]["receipt"]["rollout_plan_sha256"] != admitted["R36"]["receipt"]["rollout_plan_sha256"]:
        raise ValueError("Control and rescue do not share the same rollout plan")
    return admitted


def build(source: Path, out: Path, *, control: Path | None = None,
          rescue: Path | None = None) -> dict:
    """Build all eligible fixed candidates; malformed optional arms fail closed."""
    if (control is None) != (rescue is None):
        raise ValueError("Supply both --control and --rescue, or neither")
    source = Path(source).resolve(strict=True)
    out = _output_path(out, source)
    cp, states, source_hashes = load_source(source)
    trained = _trained_inputs(control, rescue, source_hashes, cp["cfg"]) if control is not None else {}
    roster = dict(ROSTERS)
    if trained:
        roster.update(C36=tuple(range(36)), R36=tuple(range(36)))
    manifest = dict(schema_version=1, status="BUILT_VERIFIED",
                    created_utc=datetime.now(timezone.utc).isoformat(), source=str(source),
                    source_sha256=SOURCE_SHA, source_component_sha256=source_hashes,
                    builder_sha256=file_sha256(Path(__file__)),
                    selection_basis="Fixed predeclared rosters; historical ft3 final validation only",
                    training_history="Inference artifacts: no optimizer/replay; normalized counters are not training history",
                    candidates={})
    # All input validation completes before the exclusive output directory exists.
    out.mkdir(parents=True, exist_ok=False)
    for name, indices in roster.items():
        selected = [states[i] for i in indices]
        if name in trained:
            selected[18] = trained[name]["state"]
        config = copy.deepcopy(cp["cfg"])
        if name == "Z36":
            config["zone_rescue"] = True
        candidate = dict(q=copy.deepcopy(selected[0]), target_q=copy.deepcopy(selected[0]),
                         ensemble=copy.deepcopy(selected[1:]), ensemble_dims=[79] * (len(selected)-1),
                         cfg=config, feature_dim=79, n_actions=6, env_steps=60000, learn_steps=0)
        hashes = [tensor_sha256(state) for state in selected]
        if len(set(hashes)) != len(hashes):
            raise ValueError(f"{name}: duplicate tensors would misrepresent the member count")
        target = out / f"{name}.pth"
        with target.open("xb") as handle:
            torch.save(candidate, handle)
        reloaded = torch.load(target, map_location="cpu", weights_only=True)
        actual = [tensor_sha256(state) for state in [reloaded["q"], *reloaded["ensemble"]]]
        if (actual != hashes or reloaded["cfg"] != config
                or tensor_sha256(reloaded["target_q"]) != hashes[0]
                or reloaded["ensemble_dims"] != [79] * (len(selected)-1)):
            raise ValueError(f"{name}: reload verification failed")
        entry = dict(path=str(target), sha256=file_sha256(target), net_count=len(selected),
                     unique_tensor_count=len(set(hashes)), source_indices=list(indices),
                     ordered_tensor_sha256=hashes, weighting=f"equal 1/{len(selected)}",
                     new_training=name in trained, replaced_indices=[18] if name in trained else [],
                     configuration=config, nominatable=name != "C36")
        if name in trained:
            data = trained[name]
            entry.update(training_receipt=str(data["receipt_path"]),
                         training_receipt_sha256=data["receipt_sha256"],
                         final_checkpoint=str(data["path"]),
                         final_checkpoint_sha256=data["receipt"]["final_checkpoint_sha256"],
                         training_arm=data["receipt"]["arm"])
        manifest["candidates"][name] = entry
    if file_sha256(source) != SOURCE_SHA:
        raise ValueError("V14 source SHA changed during build")
    for data in trained.values():
        if (file_sha256(data["path"]) != data["receipt"]["final_checkpoint_sha256"]
                or file_sha256(data["receipt_path"]) != data["receipt_sha256"]):
            raise ValueError("Training inputs changed during build")
    with (out / "manifest.json").open("x") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    return manifest


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--control", type=Path)
    parser.add_argument("--rescue", type=Path)
    args = parser.parse_args(argv)
    torch.set_num_threads(1)
    result = build(args.source, args.out, control=args.control, rescue=args.rescue)
    print(json.dumps({"manifest":str(args.out / "manifest.json"),
                      "candidates":{k:v["net_count"] for k,v in result["candidates"].items()}}))


if __name__ == "__main__":
    main()
