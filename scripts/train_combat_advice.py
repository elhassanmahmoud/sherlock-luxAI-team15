"""Fit one compact V14 combat adviser on archived frames, then diagnose its frozen decisions."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from agents.sherlock.geometry import DIR_DX, DIR_DY
from scripts.combat_advice_agent import CombatAdviceNet, CombatBoardHistory, advice_decision

KIND = "sherlock_combat_advice_v1"
EPOCHS, SEED, FRAMES, LR = 5, 2711, 32, 0.001
COLUMNS = ("planes", "global_step", "step", "mstep", "uid", "pos", "feats", "act",
           "sdx", "sdy", "base_act", "base_sdx", "base_sdy")
NAME = re.compile(r"g(\d+)_(player_[01])_(kaggle3|solution92|v14)\.npz")
ROOT = Path(__file__).resolve().parents[1]


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def publish(path, writer):
    """A killed process cannot leave a partial final file; concurrent writers cannot replace one."""
    if path.exists():
        raise FileExistsError(path)
    with tempfile.NamedTemporaryFile(prefix="staging-", dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
    try:
        writer(tmp)
        os.link(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def json_bytes(obj):
    return (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def publish_json(path, obj):
    publish(path, lambda tmp: tmp.write_bytes(json_bytes(obj)))


def make_plan(train_first, train_count, val_first, val_count):
    if min(train_first, val_first) < 0 or min(train_count, val_count) < 1:
        raise ValueError("Use positive map counts and nonnegative seeds")
    train = range(train_first, train_first + train_count)
    val = range(val_first, val_first + val_count)
    if set(train) & set(val):
        raise ValueError("A map cannot appear in both training and validation")
    return {group: [(seed, f"player_{seat}") for seed in seeds for seat in (0,1)]
            for group, seeds in (("train", train), ("val", val))}


def input_index(directories, plan):
    from scripts.collect_combat_advice import check_archive, opponent_for

    expected = set(plan["train"]) | set(plan["val"])
    found = {}
    for directory in directories:
        for path in sorted(Path(directory).rglob("g*.npz")):
            hit = NAME.fullmatch(path.name)
            if not hit:
                continue
            seed, side, opponent = int(hit[1]), hit[2], hit[3]
            key = seed, side
            if key not in expected:
                continue
            if opponent != opponent_for(seed):
                raise ValueError(f"Filename has wrong opponent: {path}")
            if key in found:
                raise ValueError(f"Duplicate map and seat: {key}")
            binding = file_sha(path.parent / "protocol.json")
            check_archive(path, seed, side, binding)  # verifies array digest, metadata, slots and frames
            found[key] = dict(path=str(path.resolve()), sha256=file_sha(path),
                              seed=seed, side=side, opponent=opponent, protocol=binding)
    if len({record["protocol"] for record in found.values()}) > 1:
        raise ValueError("Mixed collector protocols")
    if expected - set(found):
        raise ValueError(f"Missing {len(expected - set(found))} required map/seat archive(s)")
    return {name: [found[key] for key in keys] for name, keys in plan.items()}


def build_inputs(data):
    """One map and seat at a time. Boards are public canonical snapshots with row-to-frame indices."""
    raw, step = data["planes"], data["step"].astype(np.int64)
    globals_ = data["global_step"].astype(np.int64)
    n = len(step)
    b = len(raw)
    if (raw.shape != (b,16,24,24) or len(globals_) != b or n < b or b == 0
            or np.any(np.diff(globals_) <= 0) or np.any(np.diff(step) < 0)
            or not np.array_equal(np.unique(step), np.arange(b))):
        raise ValueError("Unordered or missing frames")
    if (data["feats"].shape != (n,79) or data["pos"].shape != (n,2)
            or any(data[k].shape != (n,) for k in COLUMNS if k not in ("planes","global_step","pos","feats"))
            or not np.isfinite(data["feats"]).all() or np.any((data["pos"] < 0) | (data["pos"] >= 24))):
        raise ValueError("Unexpected unit arrays")
    data["step"] = step
    starts = np.searchsorted(step, np.arange(b + 1))
    first = starts[:-1]
    # Features encode match index / 3. Floats in the historical NPZ are float16.
    match = np.rint(data["feats"][:,5].astype(np.float32) * 3).astype(int)
    ms = data["mstep"].astype(int)
    if (np.any(ms != ms[first][step]) or np.any(match != match[first][step])
            or np.any(ms < 1) or np.any(ms > 100)):
        raise ValueError("Inconsistent public match index or step")
    history = CombatBoardHistory()
    boards = np.empty((b,19,24,24), np.float32)
    for j, i in enumerate(first):
        boards[j] = history.build(raw[j].astype(np.float32) / 127, int(globals_[j]), int(ms[i]), int(match[i]))
    data["boards"], data["starts"] = boards, starts
    feats = data["feats"].astype(np.float32)
    data["affordable"] = np.rint(feats[:,2]*400) >= np.rint(feats[:,7]*50)
    data["range"] = np.rint(feats[:,8]*7).astype(np.int64)
    act = data["act"].astype(int)
    base = data["base_act"].astype(int)
    if np.any((act < 0) | (act > 5) | (base < 0) | (base > 5)) or np.any(data["range"] < 0):
        raise ValueError("Invalid action class or range")
    pos = data["pos"].astype(np.int64)
    delta = np.column_stack([data["sdx"], data["sdy"]]).astype(np.int64)
    dest = pos + delta
    data["legal_shot"] = ((act == 5) & data["affordable"] & (np.abs(delta).max(1) <= data["range"])
                          & ((dest >= 0) & (dest < 24)).all(1))
    data["target"] = dest[:,0] * 24 + dest[:,1]
    walk = (base > 0) & (base < 5)
    d = np.where(walk, base, 0)
    x, y = pos[:,0] + DIR_DX[d], pos[:,1] + DIR_DY[d]
    inside = (x >= 0) & (x < 24) & (y >= 0) & (y < 24)
    x, y = np.clip(x, 0, 23), np.clip(y, 0, 23)
    data["protected"] = walk & inside & (raw[step,0,x,y] > 0) & (raw[step,8,x,y] == 0)
    return data


def load_game(record):
    path = Path(record["path"])
    if file_sha(path) != record["sha256"]:
        raise ValueError(f"Archive changed: {path}")
    with np.load(path, allow_pickle=False) as archive:
        return build_inputs({k: archive[k] for k in COLUMNS})


def frame_batches(game, size, rng):
    if not 1 <= size <= FRAMES:
        raise ValueError("The batch must contain 1 to 32 entire frames")
    order = np.arange(len(game["boards"]))
    if rng is not None:
        rng.shuffle(order)
    starts = game["starts"]
    for start in range(0, len(order), size):
        frames = order[start:start+size]
        rows = np.concatenate([np.arange(starts[i], starts[i+1]) for i in frames])
        inv = np.repeat(np.arange(len(frames)), starts[frames+1] - starts[frames])
        yield frames, rows, inv


def forward(net, game, frames, rows, inv, device):
    def tensor(a, dtype):
        return torch.as_tensor(a, dtype=dtype, device=device)
    return net(tensor(game["boards"][frames], torch.float32), tensor(inv, torch.long),
               tensor(game["pos"][rows], torch.long), tensor(game["feats"][rows], torch.float32),
               tensor(game["base_act"][rows], torch.long), tensor(game["range"][rows], torch.long))


def batch_loss(fire, scores, labels, targets, legal):
    bce = F.binary_cross_entropy_with_logits(fire, (labels == 5).to(fire.dtype))
    # Never index an invalid flattened label: two out-of-bounds coordinates can alias a legal cell.
    ce = bce.new_zeros(())
    if bool(legal.any()):
        ce = F.cross_entropy(scores[legal].flatten(1), targets[legal])
    return bce + ce, bce.detach(), ce.detach()


def train_epoch(net, optimizer, records, device, epoch):
    rng = np.random.default_rng(np.random.SeedSequence([SEED, epoch]))
    net.train()
    n = n_shots = batches = 0
    bce_sum = ce_sum = 0.
    for index in rng.permutation(len(records)):
        game = load_game(records[index])
        for frames, rows, inv in frame_batches(game, FRAMES, rng):
            fire, scores = forward(net, game, frames, rows, inv, device)
            legal = torch.as_tensor(game["legal_shot"][rows], device=device)
            loss, bce, ce = batch_loss(fire, scores, torch.as_tensor(game["act"][rows], device=device),
                                       torch.as_tensor(game["target"][rows], device=device), legal)
            if not torch.isfinite(loss).item():
                raise ValueError("Non-finite loss or masked legal target")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            count = int(game["legal_shot"][rows].sum())
            n += len(rows)
            n_shots += count
            batches += 1
            bce_sum += float(bce) * len(rows)
            ce_sum += float(ce) * count
    return dict(units=n, legal_teacher_saps=n_shots, updates=batches, bce=bce_sum/n,
                target_ce=ce_sum/n_shots if n_shots else None)


def commands_match(a, dx, dy, other, odx, ody):
    return a == other and (a != 5 or (dx == odx and dy == ody))


COUNT_KEYS = ("units", "teacher_sap", "teacher_legal_sap", "base_sap", "base_joint_exact",
              "deployed_joint_exact", "base_sap_teacher_legal", "base_target_hits", "model_target_hits",
              "deployed_target_hits", "aim_eligible", "aim_admitted", "aim_changes", "new_eligible",
              "new_eligible_teacher_sap", "new_saps", "new_teacher_saps", "new_exact", "changed", "helped", "harmed")


def totals():
    return Counter(dict.fromkeys(COUNT_KEYS, 0))


def increment(c, g, rows, fire, confidence, predicted, mode):
    for j, i in enumerate(rows):
        base, label = int(g["base_act"][i]), int(g["act"][i])
        bdx, bdy = int(g["base_sdx"][i]), int(g["base_sdy"][i])
        tdx, tdy = int(g["sdx"][i]), int(g["sdy"][i])
        px, py = map(int, g["pos"][i])
        x, y = divmod(int(predicted[j]), 24)
        mdx, mdy = x - px, y - py
        affordable, protected = bool(g["affordable"][i]), bool(g["protected"][i])
        real = bool(g["legal_shot"][i])
        use = bool(advice_decision(base, float(fire[j]), float(confidence[j]), affordable, protected, mode))
        final, dx, dy = (5, mdx, mdy) if use else (base, bdx, bdy)
        was = commands_match(base, bdx, bdy, label, tdx, tdy)
        now = commands_match(final, dx, dy, label, tdx, tdy)
        changed = not commands_match(final, dx, dy, base, bdx, bdy)
        overlap = base == 5 and real
        new_eligible = base != 5 and affordable and not protected
        new = base != 5 and use
        c["units"] += 1
        c["teacher_sap"] += label == 5
        c["teacher_legal_sap"] += real
        c["base_sap"] += base == 5
        c["base_joint_exact"] += was
        c["deployed_joint_exact"] += now
        c["base_sap_teacher_legal"] += overlap
        c["base_target_hits"] += overlap and (bdx, bdy) == (tdx, tdy)
        c["model_target_hits"] += overlap and (mdx, mdy) == (tdx, tdy)
        c["deployed_target_hits"] += overlap and (dx, dy) == (tdx, tdy)
        c["aim_eligible"] += base == 5 and affordable
        c["aim_admitted"] += base == 5 and use
        c["aim_changes"] += base == 5 and changed
        c["new_eligible"] += new_eligible
        c["new_eligible_teacher_sap"] += new_eligible and real
        c["new_saps"] += new
        c["new_teacher_saps"] += new and real
        c["new_exact"] += new and real and now
        c["changed"] += changed
        c["helped"] += (not was) and now
        c["harmed"] += was and not now


def metrics(c):
    pairs = dict(aim_gate_coverage=("aim_admitted","aim_eligible"), new_gate_coverage=("new_saps","new_eligible"),
                 new_sap_precision=("new_teacher_saps","new_saps"), new_exact_precision=("new_exact","new_saps"),
                 new_sap_recall=("new_teacher_saps","new_eligible_teacher_sap"),
                 base_target_accuracy=("base_target_hits","base_sap_teacher_legal"),
                 model_target_accuracy=("model_target_hits","base_sap_teacher_legal"),
                 deployed_target_accuracy=("deployed_target_hits","base_sap_teacher_legal"),
                 base_joint_accuracy=("base_joint_exact","units"), deployed_joint_accuracy=("deployed_joint_exact","units"),
                 changed_fraction=("changed","units"))
    return {name: c[a] / c[b] if c[b] else None for name, (a,b) in pairs.items()}


@torch.inference_mode()
def diagnose(net, records, device):
    net.eval()
    rows, by_map = [], {}
    overall = {mode: totals() for mode in ("aim", "fire")}
    for record in records:
        g = load_game(record)
        counts = {mode: totals() for mode in overall}
        for frames, idx, inv in frame_batches(g, FRAMES, None):
            fire, scores = forward(net, g, frames, idx, inv, device)
            p = fire.sigmoid().cpu().numpy()
            probs, targets = scores.flatten(1).softmax(1).max(1)
            confidence, predicted = probs.cpu().numpy(), targets.cpu().numpy()
            if not np.isfinite(p).all() or not np.isfinite(confidence).all():
                raise ValueError("Non-finite inference on held-out maps")
            for mode, c in counts.items():
                increment(c, g, idx, p, confidence, predicted, mode)
        for mode, c in counts.items():
            overall[mode].update(c)
            key = str(record["seed"])
            by_map.setdefault(key, {m: totals() for m in counts})[mode].update(c)
        rows.append(dict(seed=record["seed"], side=record["side"], opponent=record["opponent"],
                         modes={m: dict(counts=c, rates=metrics(c)) for m,c in counts.items()}))
    def summaries(counts):
        return {m: dict(counts=c, rates=metrics(c)) for m,c in counts.items()}
    return dict(map_seats=rows, by_map={k: summaries(v) for k,v in by_map.items()}, all=summaries(overall))


def read_state(path, manifest_sha, epoch):
    obj = torch.load(path, map_location="cpu", weights_only=True)
    if obj.get("kind") != KIND or obj.get("experiment_sha256") != manifest_sha or obj.get("epoch") != epoch:
        raise ValueError(f"Unexpected checkpoint identity: {path}")
    return obj


def fit(out, manifest_sha, records, device):
    final = out/"model.pth"
    if final.exists():
        read_state(final, manifest_sha, EPOCHS)
        print(f"Final checkpoint already present: {final}", flush=True)
        return
    torch.manual_seed(SEED)
    net = CombatAdviceNet().to(device)
    optimizer = torch.optim.AdamW(net.parameters(), lr=LR, weight_decay=0.01)
    completed = sorted(out.glob("epoch-*.pt"))
    if len(completed) > EPOCHS or completed != [out/f"epoch-{i:02d}.pt" for i in range(1, len(completed)+1)]:
        raise ValueError("The epoch sequence contains a gap")
    history = []
    for i, path in enumerate(completed, 1):
        state = read_state(path, manifest_sha, i)
        history.append(state["metrics"])
        if i == len(completed):
            net.load_state_dict(state["state_dict"])
            optimizer.load_state_dict(state["optimizer"])
    if completed:
        print(f"Resuming after completed epoch {len(completed)}", flush=True)
    for epoch in range(len(completed) + 1, EPOCHS + 1):
        torch.manual_seed(SEED + epoch)
        result = train_epoch(net, optimizer, records, device, epoch)
        state = dict(kind=KIND, epoch=epoch, experiment_sha256=manifest_sha,
                     state_dict=net.state_dict(), optimizer=optimizer.state_dict(), metrics=result)
        publish(out/f"epoch-{epoch:02d}.pt", lambda path: torch.save(state, path))
        history.append(result)
        print(f"Epoch {epoch}/{EPOCHS} {json.dumps(result)}", flush=True)
    # Publish only the fixed last epoch, on CPU for the course runner.
    state = dict(kind=KIND, epoch=EPOCHS, experiment_sha256=manifest_sha,
                 state_dict=net.cpu().state_dict(), training_history=history)
    publish(final, lambda tmp: torch.save(state, tmp))
    print(f"Frozen {final} {file_sha(final)}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("train", "diagnose"))
    ap.add_argument("--data", nargs="+", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--device", choices=("auto","cpu","mps"), default="auto")
    ap.add_argument("--train-first", type=int, default=7271000)
    ap.add_argument("--train-count", type=int, default=32)
    ap.add_argument("--val-first", type=int, default=7271032)
    ap.add_argument("--val-count", type=int, default=8)
    a = ap.parse_args()
    plan = make_plan(a.train_first, a.train_count, a.val_first, a.val_count)
    out = a.out.resolve()
    if out == ROOT/"agents" or ROOT/"agents" in out.parents:
        raise ValueError("Training output cannot be inside production agents")
    if a.command == "train":
        out.mkdir(parents=True, exist_ok=True)
    elif not out.is_dir():
        raise ValueError("Training must be completed before diagnosis")
    torch.set_num_threads(1)
    device = a.device if a.device != "auto" else ("mps" if torch.backends.mps.is_available() else "cpu")
    with (out/".combat-advice.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        inputs = input_index(a.data, plan)
        source = Path(__file__).resolve()
        manifest = dict(kind=KIND, inputs=inputs, seeds=plan, epochs=EPOCHS, frames_per_batch=FRAMES,
                        adamw_lr=LR, adamw_weight_decay=0.01, seed=SEED, device=device,
                        torch=str(torch.__version__), numpy=np.__version__, sources={
                            "trainer": file_sha(source), "actor": file_sha(source.with_name("combat_advice_agent.py"))})
        path = out/"manifest.json"
        payload = json_bytes(manifest)
        if not path.exists() and a.command == "train":
            publish(path, lambda tmp: tmp.write_bytes(payload))
        if not path.exists() or path.read_bytes() != payload:
            raise ValueError("Frozen archive, configuration, sources or device differ")
        identity = hashlib.sha256(payload).hexdigest()
        if a.command == "train":
            fit(out, identity, inputs["train"], device)
            return
        model_path = out/"model.pth"
        state = read_state(model_path, identity, EPOCHS)
        model_sha = file_sha(model_path)
        report_path = out/"diagnosis.json"
        if report_path.exists():
            prior = json.loads(report_path.read_text())
            if prior.get("model_sha256") != model_sha or prior.get("experiment_sha256") != identity:
                raise ValueError("Existing diagnosis belongs to another checkpoint")
            print(f"Diagnosis already present: {report_path}", flush=True)
            return
        net = CombatAdviceNet().to(device)
        net.load_state_dict(state["state_dict"])
        report = diagnose(net, inputs["val"], device)
        report.update(experiment_sha256=identity, model_sha256=model_sha, scope="held-out teacher agreement",
                      precision="Uses archived int8 board planes and float16 unit features. "
                                "Live float32 inputs may differ at thresholds.")
        publish_json(report_path, report)
        print(json.dumps(report["all"], indent=2), flush=True)
        print(f"Diagnosis: {report_path}", flush=True)


if __name__ == "__main__":
    main()
