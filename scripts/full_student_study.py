"""Freeze three imitation data cohorts and fit an ordinary two-head Sherlock on fixed maps."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from scripts import imitate
from scripts.fetch_kaggle3 import sha256
from scripts.train_combat_advice import publish_json

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "experiments/analysis"
HISTORIC = {
    "v14": ("combat_advice_20261115/v14_advice_audit.json",
            "f5efa80451d5c1bea61b387c96960b6e4f695fff92451f050798462aaec14268"),
    "mixed": ("movement_dagger_20261115/corpus.json",
              "fed298f9dd84100c119423e2a8d9c5607291a54a028b3ca560b9d454e64d405f"),
}
# All 41 source/teacher entries of the original four batch receipts. Reproducible from 565d8a2.
COLLECTOR_DIGEST = "3baeb4c146930de25100a8f4f5bac73659bc3d2578f74ccc7531df1ddd717dbb"
V14_DIGEST = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
MIX = "kaggle3:0.4,v14:0.3,solution92:0.3"
FIRST = 7_280_000
SIDES = ("player_0", "player_1")
COHORTS = ("v14", "mixed", "expert")
MODEL = dict(seed=2711, epochs=5, mb=256, lr=.001, ch=32, blocks=3, hidden=128, sap_weight=.5)
TEACHER = "kaggle3 lux3-bot 0.4.8_fn"


def digest_json(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def roster():
    """Return exact (cohort, seed, seat) -> (split, opponent); split by map, never by seat."""
    from scripts.collect_combat_advice import opponent_for

    result = {}
    historical = (("v14", 7271000, 32, 7271032, 8), ("mixed", 7272000, 120, 7272200, 24))
    for name, start, n, diag, m in historical:
        for split, lo, count in (("train", start, n), ("val", diag, m)):
            for seed in range(lo, lo + count):
                for side in SIDES:
                    result[name, seed, side] = split, opponent_for(seed)
    for number in range(4):
        first = FIRST + 60 * number
        rng = random.Random(first)
        for seed in range(first, first + 60):
            side = rng.choice(SIDES)
            opp = rng.choices(("kaggle3", "v14", "solution92"), (.4, .3, .3))[0]
            for chosen in (SIDES if opp == "kaggle3" else (side,)):
                result["expert", seed, chosen] = ("train" if seed < FIRST + 216 else "val"), opp
    return result


def receipt_sources(collector):
    package = collector / "experiments/opponents/kaggle3_lux3_048fn"
    files = [*(collector / "agents/sherlock").glob("*.py"),
             *(collector / "scripts" / name for name in ("imitate.py", "kaggle3_opponent.py",
                                                         "common.py", "experiment.py")),
             *package.rglob("*.py"), *package.rglob("*.pth")]
    entries = {str(p.relative_to(collector)): sha256(p) for p in sorted(files)}
    if (digest_json(entries) != COLLECTOR_DIGEST or
            sha256(collector / "agents/sherlock/weights/agent_p0.pth") != V14_DIGEST):
        raise ValueError("Collector sources, teacher release or V14 differ from the registered snapshot")
    return entries


def make_receipt(folder, collector):
    sources = receipt_sources(collector)
    files = [dict(file=p.name, sha256=sha256(p), bytes=p.stat().st_size)
             for p in sorted(folder.glob("g*.npz"))]
    return dict(collect=json.loads((folder / "collect.json").read_text()), files=files, sources=sources)


def put(records, key, side_record):
    if key in records:
        raise ValueError(f"Duplicate map and side: {key}")
    records[key] = side_record


def historical_records():
    records = {}
    for cohort, (relative, digest) in HISTORIC.items():
        path = REPORTS / relative
        if sha256(path) != digest:
            raise ValueError(f"Historical data inventory changed: {path}")
        value = json.loads(path.read_text())
        for row in value["map_sides" if cohort == "v14" else "games"]:
            if cohort == "v14":
                meta, count, hash_ = row["metadata"], row["counts"]["rows"], row["input_sha256"]
            else:
                meta, count, hash_ = row, row["rows"], row["sha256"]
            seed, side, opp = meta["seed"], meta["side"], meta["opponent"]
            item = dict(file=f"g{seed}_{side}_{opp}.npz", opponent=opp, rows=count, sha256=hash_)
            put(records, (cohort, seed, side), item)
    return records


def archive_rows(path, seed, side, opponent):
    """SideRecord stores 79 canonical features, six classes and signed offsets in map coordinates."""
    with np.load(path, allow_pickle=False) as z:
        m = json.loads(z["meta"].item())
        if (m.get("seed"), m.get("side"), m.get("opponent")) != (seed, side, opponent):
            raise ValueError(f"Teacher archive identity mismatch: {path}")
        boards, step, uid, pos = (z[k] for k in ("planes", "step", "uid", "pos"))
        feats, mask, action = (z[k] for k in ("feats", "mask", "act"))
        n = len(step)
        if (boards.shape[1:] != (16, 24, 24) or boards.dtype != np.int8 or not 1 <= len(boards) <= 303
                or not n or step.shape != (n,) or step.dtype != np.int32 or step[0] < 0
                or step[-1] >= len(boards) or np.any(np.diff(step) < 0)
                or uid.shape != (n,) or np.any((uid < 0) | (uid >= 16))
                or np.unique(step * 16 + uid).size != n
                or pos.shape != (n, 2) or np.any((pos < 0) | (pos >= 24))
                or feats.shape != (n, 79) or feats.dtype != np.float16 or not np.isfinite(feats).all()
                or mask.shape != (n, 6) or mask.dtype != np.bool_ or action.shape != (n,)
                or action.dtype != np.int8 or np.any((action < 0) | (action > 5))
                or any(z[k].dtype != np.int8 or z[k].shape != (n,) for k in ("sdx", "sdy"))):
            raise ValueError(f"Invalid teacher SideRecord format: {path}")
        return n


def expert_records(folder, receipts, expected):
    records, evidence = {}, []
    for i in range(4):
        batch = folder / f"batch{i}"
        path = receipts / f"batch{i}.json"
        receipt = json.loads(path.read_text())
        first = FIRST + 60 * i
        meta = receipt["collect"]
        if (meta != json.loads((batch / "collect.json").read_text()) or
                (meta["games"], meta["seed0"], meta["mix"], meta["teacher"]) != (60, first, MIX, TEACHER)
                or digest_json(receipt["sources"]) != COLLECTOR_DIGEST):
            raise ValueError(f"Unexpected teacher, collector or batch receipt: {path}")
        files = {p.name for p in batch.glob("g*.npz")}
        wanted = {f"g{s}_{p}_{op}.npz": (s, p, op) for (c, s, p), (_, op) in expected.items()
                  if c == "expert" and first <= s < first + 60}
        if set(wanted) != files or {r["file"] for r in receipt["files"]} != files or meta["files"] != len(files):
            raise ValueError(f"Missing or unexpected teacher map/seat: {batch}")
        total = 0
        for row in receipt["files"]:
            filename = row["file"]
            seed, side, opp = wanted[filename]
            file = batch / filename
            if row["bytes"] != file.stat().st_size or sha256(file) != row["sha256"]:
                raise ValueError(f"Teacher bytes changed: {file}")
            count = archive_rows(file, seed, side, opp)
            total += count
            put(records, ("expert", seed, side), dict(file=str(file.relative_to(folder)), opponent=opp,
                                                      rows=count, sha256=row["sha256"]))
        if total != meta["samples"]:
            raise ValueError(f"Teacher receipt sample count differs in batch {i}")
        evidence.append(dict(batch=i, sha256=sha256(path)))
    return records, evidence


def build_manifest(dirs, receipts):
    expected = roster()
    records = historical_records()
    if len({p.resolve() for p in dirs.values()}) != len(COHORTS):
        raise ValueError("The three cohort directories must be distinct")
    for (cohort, _, _), item in records.items():
        path = dirs[cohort] / item["file"]
        if sha256(path) != item["sha256"]:
            raise ValueError(f"Historical archive differs from the published inventory: {path}")
    experts, evidence = expert_records(dirs["expert"], receipts, expected)
    records.update(experts)
    if set(records) != set(expected):
        raise ValueError("The combined side roster differs from its fixed map split")
    files = []
    for (cohort, seed, side), (split, opp) in expected.items():
        item = records[cohort, seed, side]
        if item["opponent"] != opp:
            raise ValueError(f"Wrong opponent: {cohort} {seed} {side}")
        files.append(dict(cohort=cohort, seed=seed, side=side, split=split, **item))
    return dict(schema=1, model=MODEL, teacher=TEACHER, collector_sha256=COLLECTOR_DIGEST,
                historical_inventories={c: digest for c, (_, digest) in HISTORIC.items()},
                teacher_receipts=evidence, files=files)


def arm_inputs(files, arm):
    allowed = COHORTS if arm == "plus_teacher" else COHORTS[:2]
    train = [r for r in files if r["split"] == "train" and r["cohort"] in allowed]
    val, groups = [], []
    start = 0
    for cohort in COHORTS:
        part = [r for r in files if r["split"] == "val" and r["cohort"] == cohort]
        stop = start + sum(r["rows"] for r in part)
        if stop <= start:
            raise ValueError(f"Empty diagnostic group: {cohort}")
        groups.append((cohort, start, stop))
        val.extend(part)
        start = stop
    return train, val, groups


def fit(a, manifest, manifest_hash, dirs):
    import torch
    from agents.sherlock.ppo_agent import save_policy
    from scripts.imitation_storage import store_partition

    if sha256(imitate.V14) != V14_DIGEST:
        raise ValueError("V14 base configuration source mismatch")
    out = imitate._check_out(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    train, val, groups = arm_inputs(manifest["files"], a.arm)
    options = SimpleNamespace(**MODEL, device=a.device, low_memory=True, validation_groups=groups)
    opts = dict(study="whole_policy_20261115", arm=a.arm, manifest_sha256=manifest_hash,
                validation={}, settings=MODEL, training_device=a.device, torch_version=str(torch.__version__),
                numpy_version=np.__version__)
    options.validation_report = opts["validation"]
    sources = [Path(__file__).resolve(), ROOT / "scripts/imitation_storage.py", ROOT / "scripts/imitate.py",
               *(ROOT / "agents/sherlock" / n for n in ("imitation_net.py", "cnn_model.py", "ppo_agent.py"))]
    opts["training_sources_sha256"] = {str(p.relative_to(ROOT)): sha256(p) for p in sources}
    torch.set_num_threads(1)
    with tempfile.TemporaryDirectory(prefix=".full-student-", dir=out.parent) as dev:
        folder = Path(dev)
        arrays = []
        for name, selection in (("train", train), ("val", val)):
            part = store_partition([dirs[r["cohort"]] / r["file"] for r in selection],
                                   folder / name, imitate.prepare_labels)
            if len(part[1]["step"]) != sum(r["rows"] for r in selection) or "base_act" in part[1]:
                raise ValueError(f"Unexpected ordinary {name} batch layout")
            arrays.append(part)
        # Ordinary train_student shuffles via legacy global np.random. Torch seeds its own initialization.
        random.seed(MODEL["seed"])
        np.random.seed(MODEL["seed"])
        net = imitate.train_student(*arrays, options, lambda line: print(line, flush=True))
        cfg = imitate.v14_cfg()
        metadata = dict(kind="imitation", teacher=TEACHER, sap_own_tile=True, full_policy_study=opts)
        # A constant basename keeps the Torch ZIP member names stable across repeat fits.
        checkpoint = folder / "student.pth"
        save_policy(str(checkpoint), net, cfg, extra=metadata)
        os.link(checkpoint, out)  # Atomic publish, with no overwrite even on a concurrent invocation.
        print(json.dumps(dict(checkpoint_sha256=sha256(out), **opts), allow_nan=False, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(required=True, dest="cmd")
    receipt = sub.add_parser("receipt", help="Reproduce a collection receipt in the frozen collector snapshot")
    receipt.add_argument("--batch", type=Path, required=True)
    receipt.add_argument("--collector", type=Path, required=True)
    receipt.add_argument("--out", type=Path, required=True)
    freeze = sub.add_parser("freeze")
    train = sub.add_parser("fit")
    for cmd in (freeze, train):
        for name in (*COHORTS, "receipts", "manifest"):
            cmd.add_argument("--" + name, type=Path, required=True)
    train.add_argument("--manifest-sha256", required=True)
    train.add_argument("--arm", choices=("historical", "plus_teacher"), required=True)
    train.add_argument("--device", choices=("cpu", "mps"), default="cpu")
    train.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.cmd == "receipt":
        a.out.parent.mkdir(parents=True, exist_ok=True)
        publish_json(a.out, make_receipt(a.batch, a.collector))
        return
    if a.cmd == "fit" and (a.out.exists() or sha256(a.manifest) != a.manifest_sha256):
        raise ValueError("Output already exists or the frozen input manifest differs from the requested SHA-256")
    dirs = {c: getattr(a, c) for c in COHORTS}
    manifest = build_manifest(dirs, a.receipts)
    if a.cmd == "freeze":
        a.manifest.parent.mkdir(parents=True, exist_ok=True)
        publish_json(a.manifest, manifest)
        print(sha256(a.manifest))
    elif manifest != json.loads(a.manifest.read_text()):
        raise ValueError("Data changed after freezing")
    else:
        fit(a, manifest, a.manifest_sha256, dirs)


if __name__ == "__main__":
    main()
