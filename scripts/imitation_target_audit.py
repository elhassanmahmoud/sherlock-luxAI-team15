"""Audit SAP target labels from scripts.imitate SideRecord NPZ files without loading a model.

python -m scripts.imitation_target_audit experiments/imitation/k3_v1 --out NEW.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
from io import BytesIO
from itertools import combinations
import json
import os
from pathlib import Path
import tempfile

import numpy as np


MODES = ("deployed", "engine")
PAIR_FIELDS = ("eligible_saps", "pairs", "mutual_pairs", "conflicts", "affected_saps")
ROOT = Path(__file__).resolve().parents[1]


def _ratio(n, d):
    return n / d if d else None


def summarize(counts):
    result = {k: counts[k] for k in ("rows", "sap_labels", "invalid_saps", "legal_saps", "self_targets")}
    result["self_targets_per_legal_sap"] = _ratio(counts["self_targets"], counts["legal_saps"])
    for mode in MODES:
        m = {k: counts[mode, k] for k in PAIR_FIELDS}
        m["conflicts_per_pair"] = _ratio(m["conflicts"], m["pairs"])
        m["conflicts_per_mutual_pair"] = _ratio(m["conflicts"], m["mutual_pairs"])
        m["affected_per_eligible_sap"] = _ratio(m["affected_saps"], m["eligible_saps"])
        m["affected_per_legal_sap"] = _ratio(m["affected_saps"], counts["legal_saps"])
        result[mode] = m
    return result


def _reachable(origin, target, radius, mode):
    return (max(abs(origin[0]-target[0]), abs(origin[1]-target[1])) <= radius
            and (mode == "engine" or origin != target))


def audit_file(path):
    raw = path.read_bytes()
    with np.load(BytesIO(raw), allow_pickle=False) as z:
        meta = json.loads(z["meta"].item())
        pos, step, mstep, uid, act = (z[k] for k in ("pos", "step", "mstep", "uid", "act"))
        # Arithmetic in wide integers is important for the signed int8 offsets.
        offsets = np.column_stack((z["sdx"], z["sdy"])).astype(np.int64)
        feats = z["feats"].astype(np.float64)
        # Decode the shape only. Large, compressed policy planes are not needed for this audit.
        with z.zip.open("planes.npy") as handle:
            version = np.lib.format.read_magic(handle)
            if version != (1, 0):
                raise ValueError(f"Unsupported plane header in {path}: {version}")
            plane_shape, _, _ = np.lib.format.read_array_header_1_0(handle)
    rows = len(act)
    if (len(plane_shape) != 4 or pos.shape != (rows, 2) or offsets.shape != (rows, 2)
            or feats.ndim != 2 or feats.shape[0] != rows or feats.shape[1] < 9
            or any(a.shape != (rows,) for a in (step, mstep, uid, act))
            or not all(np.issubdtype(a.dtype, np.integer) for a in (pos, step, mstep, uid, act))
            or not np.isfinite(feats[:, [2, 7, 8]]).all()
            or meta.get("side") not in ("player_0", "player_1") or not isinstance(meta.get("seed"), int)):
        raise ValueError(f"Invalid SideRecord schema: {path}")
    w, h = plane_shape[-2:]
    if (np.any(pos < 0) or np.any(pos >= (w, h)) or np.any(step < 0) or np.any(step >= plane_shape[0])
            or len(np.unique(np.stack((step, uid), axis=1), axis=0)) != rows):
        raise ValueError(f"Invalid positions, step index, or repeated unit in {path}")

    counts = Counter(rows=rows)
    examples = {k: [] for k in ("self", *MODES)}
    at_step = {}
    # The teacher stores integer energy, SAP cost and range as normalized float16 features.
    energy, cost, radius = np.rint(feats[:, [2, 7, 8]] * [400, 50, 7]).astype(int).T
    if np.any(cost <= 0) or np.any(radius < 1) or (
            meta.get("sap_range") is not None and np.any(radius != meta["sap_range"])):
        raise ValueError(f"Invalid SAP parameters: {path}")
    for i in np.flatnonzero(act == 5):
        counts["sap_labels"] += 1
        origin = tuple(map(int, pos[i]))
        target = tuple(map(int, pos[i] + offsets[i]))
        r = int(radius[i])
        if (not (0 <= target[0] < w and 0 <= target[1] < h) or energy[i] < cost[i]
                or not _reachable(origin, target, r, "engine")):
            counts["invalid_saps"] += 1
            continue
        counts["legal_saps"] += 1
        shot = dict(uid=int(uid[i]), origin=origin, target=target, radius=r)
        si = int(step[i])
        if origin == target:
            counts["self_targets"] += 1
            if len(examples["self"]) < 2:
                examples["self"].append(dict(recorded_step=si, match_step=int(mstep[i]), shot=shot))
        at_step.setdefault(si, []).append(shot)

    for si, shots in at_step.items():
        for mode in MODES:
            eligible = [s for s in shots if _reachable(s["origin"], s["target"], s["radius"], mode)]
            counts[mode, "eligible_saps"] += len(eligible)
            affected = set()
            for a, b in combinations(eligible, 2):
                counts[mode, "pairs"] += 1
                if (not _reachable(a["origin"], b["target"], a["radius"], mode)
                        or not _reachable(b["origin"], a["target"], b["radius"], mode)):
                    continue
                counts[mode, "mutual_pairs"] += 1
                if a["target"] != b["target"]:
                    counts[mode, "conflicts"] += 1
                    affected.update((a["uid"], b["uid"]))
                    if len(examples[mode]) < 2:
                        examples[mode].append(dict(recorded_step=si, shots=[a, b]))
            counts[mode, "affected_saps"] += len(affected)
    return counts, dict(input=str(path.resolve()), input_sha256=sha256(raw).hexdigest(),
                        metadata=meta, counts=summarize(counts), examples=examples)


def audit(inputs):
    files = []
    for arg in map(Path, inputs):
        if arg.is_dir():
            found = sorted(arg.glob("g*.npz"))
            if not found:
                raise ValueError(f"No g*.npz teacher recordings in {arg}")
            files.extend(found)
        elif arg.is_file() and arg.suffix == ".npz":
            files.append(arg)
        else:
            raise ValueError(f"Missing input or unsupported format: {arg}")
    if not files:
        raise ValueError("No teacher recordings")
    total, by_side, map_sides, seen = Counter(), {}, [], set()
    for path in files:
        counts, record = audit_file(path)
        meta = record["metadata"]
        key = (meta["seed"], meta["side"])
        if key in seen:
            raise ValueError(f"Duplicate map/side {key}; audit distinct collection batches separately")
        seen.add(key)
        map_sides.append(record)
        total.update(counts)
        by_side.setdefault(meta["side"], Counter()).update(counts)
    source_files = ("scripts/imitate.py", "agents/sherlock/imitation_agent.py", "scripts/imitation_target_audit.py")
    return dict(schema=1, source_sha256={name: sha256((ROOT/name).read_bytes()).hexdigest() for name in source_files},
                note=("A conflict is a pair of simultaneous legal teacher shots to different tiles, each "
                      "available to both shooters. Deployed excludes each shooter's own tile; engine allows it. "
                      "Affected counts distinct decisions in any conflict, not unavoidable errors. "
                      "recorded_step indexes the recorded frames of one side. Fractions pool counts."),
                maps=len({k[0] for k in seen}), total=summarize(total),
                by_side={side: summarize(c) for side, c in by_side.items()}, map_sides=map_sides)


def publish(path, result):
    """Publish a complete report atomically; an existing report is never overwritten."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(result, f, indent=2, allow_nan=False)
            f.write("\n")
        os.link(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(args.inputs)
    if args.out:
        publish(args.out, report)
    else:
        print(json.dumps(report, indent=2, allow_nan=False))
