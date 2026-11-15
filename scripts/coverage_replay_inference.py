"""Replay the frozen R2 movement votes on twelve held-out, quantized R1-trajectory maps."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import numpy as np

R2_SHA = "23fa6208d76e81940916388b9ee56c1d290693e8febfa53622442b64b0d33f96"
R1_SHA = "5327d0ff4e2cc4b09bdcb43ae51fbd7dcc9f6d8487f79f4a7cfd1ad176813575"
MIXED_PROTOCOL = "50bf0bb810f7b913acce8940937d335ebf180bc796457dcf880ffa6743ec2724"
ORIGINAL_PROTOCOL = "8eb465d5a603ac87d6453f2ce9d6fad5258fe1d8cd2539cdf7a39497cd4a7e8d"
DIAGNOSIS_SEEDS = range(7272200, 7272212)
SIDES = ("player_0", "player_1")


def load_r2(path, data_dir):
    """Return CPU eval members, the 24 verified file paths keyed by (seed, side), and model SHA."""
    import torch
    from agents.sherlock.imitation_net import ImitationNet
    from scripts.collect_combat_advice import filename, opponent_for

    data_dir = Path(data_dir)
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != R2_SHA:
        raise ValueError("Model differs from the R2 checkpoint used in the original movement screen")
    if hashlib.sha256((data_dir / "protocol.json").read_bytes()).hexdigest() != MIXED_PROTOCOL:
        raise ValueError("Archive directory has a different R1 movement collection protocol")
    model = torch.load(io.BytesIO(raw), map_location="cpu", weights_only=True)
    training = model["selective_training"]
    arch = dict(feat_dim=79, n_actions=6, in_ch=16, ch=32, blocks=3, hidden=128,
                detach_value=True, sap_head=True)
    if (model.get("kind") != "imitation" or model.get("arch") != arch
            or model.get("epochs") != 5 or model.get("sap_own_tile") is not True
            or model.get("imitation_ensemble") or training.get("parent_sha256") != R1_SHA
            or training.get("combat_action_weight") != 3 or training.get("other_action_weight") != 1
            or training.get("target_weight") != 0.5):
        raise ValueError("Unexpected R2 training mode, parent, architecture or roster")

    # Verify the complete registered split in metadata, without reading a training game.
    plans = {"original": (range(7271000, 7271032), range(7271032, 7271040), ORIGINAL_PROTOCOL),
             "mixed": (range(7272000, 7272120), range(7272200, 7272224), MIXED_PROTOCOL)}
    hashes = {}
    for group, (train, val, binding) in plans.items():
        for split, seeds in (("train", train), ("val", val)):
            records = training["inputs"][group][split]
            expected = {(s, side) for s in seeds for side in SIDES}
            if len(records) != len(expected) or {(r["seed"], r["side"]) for r in records} != expected:
                raise ValueError(f"Wrong R2 {group}/{split} maps or seats")
            for r in records:
                if r["protocol"] != binding:
                    raise ValueError(f"Wrong {group}/{split} collection protocol")
                if group == "mixed" and split == "val" and r["seed"] in DIAGNOSIS_SEEDS:
                    hashes[r["seed"], r["side"]] = r["sha256"]

    files = {}
    for (seed, side), expected_sha in sorted(hashes.items()):
        p = data_dir / filename(seed, side)
        with p.open("rb") as f:
            if hashlib.file_digest(f, "sha256").hexdigest() != expected_sha:
                raise ValueError(f"Archive differs from R2 validation input: {p}")
            f.seek(0)
            with np.load(f, allow_pickle=False) as z:
                meta = json.loads(z["meta"].item())
        if (meta["seed"], meta["side"], meta["opponent"], meta["protocol_sha256"],
                meta["student_sha256"]) != (seed, side, opponent_for(seed), MIXED_PROTOCOL, R1_SHA):
            raise ValueError(f"Unexpected archive metadata: {p}")
        files[seed, side] = p
    net = ImitationNet(**arch)
    net.load_state_dict(model["policy"])
    return [net.cpu().eval()], files, digest


def predict(members, arrays):
    """Return canonical legal argmax and its probability before gating, in original row order.

    One trunk forward per board and all that board's units together, as in live movement advice.
    NPZ planes and features have storage quantization, so replay may differ near a tie or threshold.
    """
    import torch
    from agents.sherlock.imitation_agent import sap_legal
    from scripts.imitate import PLANE_SCALE

    planes, feats, masks = (np.asarray(arrays[k]) for k in ("planes", "feats", "mask"))
    step = np.asarray(arrays["step"], dtype=np.int64)
    pos = np.asarray(arrays["pos"], dtype=np.int64)
    n, b = len(step), len(planes)
    if (not members or not n or not b or step.shape != (n,) or step[0] != 0 or step[-1] != b - 1
            or np.any(np.diff(step) < 0) or np.any(np.diff(step) > 1)
            or planes.shape != (b, 16, 24, 24) or planes.dtype != np.int8
            or feats.shape != (n, 79) or feats.dtype != np.float16 or not np.isfinite(feats).all()
            or masks.shape != (n, 6) or masks.dtype != np.bool_
            or pos.shape != (n, 2) or np.any(pos < 0) or np.any(pos >= 24)):
        raise ValueError("Invalid R2 board arrays or unit rows")
    feats = feats.astype(np.float32)
    masks = sap_legal(masks, np.rint(feats[:, 2] * 400), np.rint(feats[:, 7] * 50))
    if not masks.any(axis=1).all():
        raise ValueError("A live unit has no legal action")
    choice, confidence = np.empty(n, np.int64), np.empty(n, np.float32)
    bounds = step.searchsorted(np.arange(b + 1))
    with torch.inference_mode():
        for j, (lo, hi) in enumerate(zip(bounds[:-1], bounds[1:])):
            board = torch.from_numpy(planes[j:j+1].astype(np.float32)) / PLANE_SCALE
            board_rows = torch.zeros(hi - lo, dtype=torch.long)
            xy = torch.from_numpy(pos[lo:hi])
            features = torch.from_numpy(feats[lo:hi])
            logits = torch.stack([net.forward_all(board, board_rows, xy, features)[0] for net in members]).mean(0)
            probs = logits.masked_fill(~torch.from_numpy(masks[lo:hi]), -torch.inf).softmax(1)
            prob, action = probs.max(1)
            confidence[lo:hi], choice[lo:hi] = prob.numpy(), action.numpy()
    if not np.isfinite(confidence).all():
        raise ValueError("Non-finite R2 action probabilities")
    return choice, confidence
