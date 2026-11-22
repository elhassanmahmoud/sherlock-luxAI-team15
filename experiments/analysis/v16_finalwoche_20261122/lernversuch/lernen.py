"""Paired action-head fine-tuning on fixed teacher labels. No model selection by epoch."""
import argparse
import copy
import importlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np
import torch
from torch.nn import functional as F

from sammlung import HERE, ROOT, RELEASE, ZIP_SHA, sha
from scripts.imitate import PLANE_SCALE, prepare_labels, prev_move_columns
from scripts.r3_package import _module_for


def verified_examples(archive, recent):
    index = json.loads((ROOT / "experiments/analysis/umbau_20261115/dagger_zusatz/index-400.json").read_text())
    entries = []
    for rec in sorted(index["files"], key=lambda r: r["seed"])[:32]:
        name = f"g{rec['seed']}_{rec['side']}_{rec['opponent']}_dagger.npz"
        entries.append(dict(path=archive / name, split="train", source="v4", **rec))
    fresh = json.loads((recent / "sammlung.json").read_text())
    for rec in fresh:
        entries.append(dict(path=recent / rec["file"], source="v16", **rec))
    for split, ids in (("train", [*range(7172000,7172032), *range(19376200,19376208)]),
                       ("valid", list(range(19376220,19376224)))):
        if sorted(row["seed"] for row in entries if row["split"] == split) != ids:
            raise ValueError(f"Unexpected seed panel: {split}")
    for row in entries:
        if sha(row["path"]) != row["sha256"]:
            raise ValueError(f"Changed archive {row['path']}")
    return entries


def unit_history(z):
    # Compare the vectorized archive reconstruction to the running in-game tracker,
    # including canonical P1 positions, exact match boundaries and missing units.
    from agents.sherlock.prev_move import MoveTracker
    pos, steps, ids, msteps = (z[k] for k in ("pos", "step", "uid", "mstep"))
    previous = prev_move_columns(z)
    tracker = MoveTracker()
    started = 0
    prior_ms = None
    focus = np.zeros(len(pos), dtype=bool)
    reached = set()
    for start, end in zip(np.r_[0, np.flatnonzero(np.diff(steps)) + 1],
                          np.r_[np.flatnonzero(np.diff(steps)) + 1, len(pos)]):
        sl = slice(start,end)
        ms = int(msteps[start])
        if not np.all(msteps[sl] == ms):
            raise ValueError("Several match steps in one frame")
        if prior_ms is None or ms < prior_ms:
            reached.clear()
            tracker.reset()
            started += 1
        prior_ms = ms
        if not np.array_equal(tracker.features(ms, ids[sl], pos[sl]), previous[sl]):
            raise ValueError("Archive and live previous-movement features disagree")
        tracker.record(ms, ids[sl], pos[sl], np.ones(end - start,dtype=bool))
        positions = [tuple(map(int,p)) for p in pos[sl]]
        if ms <= 50:
            reached.update(positions)
        if ms >= 81:
            board = z["planes"][int(steps[start]),0]
            points = {p for p in reached if board[p] > 0}
            for r,(x,y) in enumerate(positions, start):
                focus[r] = any(p in points for p in ((x,y),(x+1,y),(x-1,y),(x,y+1),(x,y-1)))
    if started != 3:
        raise ValueError(f"Expected three matches, found {started}")
    return previous, focus


def encode(path, metadata, models, device):
    with np.load(path, allow_pickle=False) as arc:
        meta = json.loads(str(arc["meta"]))
        if any(meta[k] != metadata[k] for k in ("seed","side","opponent")):
            raise ValueError(f"Metadata mismatch at {path}")
        if meta["teacher_history"] != "played_student_actions" or meta["steps"] != 303:
            raise ValueError("Missing real DAgger history")
        if metadata["source"] == "v16" and meta["student"] != ZIP_SHA:
            raise ValueError("Different live student")
        z = {k:arc[k] for k in ("step","uid","pos","feats","mask","act","sdx","sdy","mstep","planes")}
    previous, focus = unit_history(z)
    if z["feats"].shape[1] != 79 or len(z["act"]) != metadata["rows"]:
        raise ValueError("Unexpected unit features/count")
    rows = {k:torch.from_numpy(z[k]) for k in ("pos","feats","mask","act","sdx","sdy")}
    prepare_labels(rows, *z["planes"].shape[-2:])
    features = torch.from_numpy(np.concatenate((z["feats"], previous), axis=1)).float()
    keep = rows["admitted"]
    # All records use the same float16 unit features and compressed boards. This
    # preserves the archive encoding on which the original students were trained.
    outputs = {"h": [], "other": [], "logit_error": []}
    for start in range(0,len(z["planes"]),16):
        end = min(start + 16, len(z["planes"]))
        a,b = np.searchsorted(z["step"], [start,end])
        boards = torch.from_numpy(z["planes"][start:end]).float().to(device) / PLANE_SCALE
        rel = torch.tensor(z["step"][a:b].astype(np.int64) - start, device=device)
        pos = rows["pos"][a:b].to(device)
        feats = features[a:b].to(device)
        capture = []
        hook = models[0].pi.register_forward_pre_hook(lambda _layer, args: capture.append(args[0]))
        with torch.no_grad():
            original = models[0].forward_all(boards,rel,pos,feats)[0]
            hook.remove()
            check = models[0].pi(capture[0])
            outputs["logit_error"].append((original-check).abs().max().item())
            outputs["h"].append(capture[0].cpu())
            outputs["other"].append(models[1].forward_all(boards,rel,pos,feats)[0].cpu())
    if max(outputs["logit_error"]) > 1e-5:
        raise ValueError("Head reconstruction mismatch")
    return dict(h=torch.cat(outputs["h"])[keep], other=torch.cat(outputs["other"])[keep],
                legal=rows["mask"][keep], target=rows["act"][keep], focus=torch.from_numpy(focus)[keep])


def action_scores(model, data):
    return (model(data["h"]) + data["other"]).masked_fill(~data["legal"], -torch.inf)


def scores(model, data):
    with torch.no_grad():
        logits = action_scores(model, data)
        loss = F.cross_entropy(logits,data["target"],reduction="none")
        correct = logits.argmax(1) == data["target"]
        return {group:{"n":len(loss[sel]), "correct":int(correct[sel].sum()),
                       "logloss":float(loss[sel].mean())}
                for group,sel in (("all",torch.ones_like(correct)),("focus",data["focus"]))}


def run(a):
    torch.set_num_threads(1)
    if sha(RELEASE) != ZIP_SHA:
        raise ValueError("Original V16 package changed")
    entries = verified_examples(a.archive,a.recent)
    a.out.mkdir(parents=True,exist_ok=False)
    _module_for(RELEASE.resolve())
    cls = importlib.import_module("sherlock.imitation_net").ImitationNet
    with zipfile.ZipFile(RELEASE) as z:
        ckpt = torch.load(io.BytesIO(z.read("sherlock/weights/agent.pth")),weights_only=False,map_location="cpu")
    if ckpt["members"] != ["v9_from_v8.pth", "v8L_from_v7L.pth"] or not ckpt["prev_move_input"]:
        raise ValueError("Wrong model order or input representation")
    models = []
    for member in (ckpt,ckpt["imitation_ensemble"][0]):
        net = cls(**member["arch"]).eval()
        net.load_state_dict(member["policy"])
        models.append(net.to(a.device))
    parts = {"train": [], "valid": []}
    counts = []
    for e in entries:
        data = encode(e["path"],e,models,a.device)
        counts.append({**{k:e[k] for k in ("split","seed","source","side","opponent","sha256")},
                       "rows":len(data["target"]), "focus":int(data["focus"].sum())})
        parts[e["split"]].append(data)
        print(e["split"],e["seed"],counts[-1]["rows"],counts[-1]["focus"],flush=True)
    train, valid = ({k:torch.cat([d[k] for d in parts[part]]) for k in parts[part][0]}
                    for part in ("train","valid"))
    del parts
    initial = models[0].pi.cpu().eval()
    result = {"package": ZIP_SHA, "device_for_feature_cache":a.device, "maps":counts,
              "base":scores(initial,valid), "arms":{}}
    if sum(r["focus"] > 0 for r in counts if r["split"]=="valid") < 3 or int(valid["focus"].sum()) < 100:
        result["gate"] = False
        result["reason"] = "Insufficient focused holdout examples"
    else:
        before = action_scores(initial,valid).argmax(1).detach()
        predictions = {}
        for arm,multiplier in (("kontrolle",1),("behandlung",3)):
            model = copy.deepcopy(initial)
            optim = torch.optim.Adam(model.parameters(),lr=5e-5)
            rng = torch.Generator().manual_seed(2211)
            for _ in range(96):
                idx = torch.randint(len(train["target"]),(512,),generator=rng)
                logits = (model(train["h"][idx]) + train["other"][idx]).masked_fill(~train["legal"][idx],-torch.inf)
                ce = F.cross_entropy(logits,train["target"][idx],reduction="none")
                weights = 1 + (multiplier - 1) * train["focus"][idx].float()
                loss = (weights * ce).sum() / weights.sum()
                optim.zero_grad()
                loss.backward()
                optim.step()
            candidate = copy.deepcopy(ckpt)
            for key,value in model.state_dict().items():
                candidate["policy"][f"pi.{key}"] = value
            changed = [k for k,v in ckpt["policy"].items() if not torch.equal(candidate["policy"][k],v)]
            if sorted(changed) != ["pi.bias","pi.weight"] or any(not torch.equal(v,candidate["imitation_ensemble"][0]["policy"][k])
                    for k,v in ckpt["imitation_ensemble"][0]["policy"].items()):
                raise ValueError("Unexpected modified tensors")
            path = a.out / f"{arm}.pth"
            torch.save(candidate,path)
            predicted = action_scores(model, valid).argmax(1).detach()
            predictions[arm] = predicted
            result["arms"][arm] = dict(scores=scores(model,valid),sha256=sha(path),changed=changed,
                                       head_argmax_changes_against_base=int((predicted != before).sum()),
                                       focus_head_changes_against_base=int(((predicted != before) & valid["focus"]).sum()))
        unequal = predictions["behandlung"] != predictions["kontrolle"]
        result["head_disagreements_between_arms"] = {"all":int(unequal.sum()), "focus":int((unequal & valid["focus"]).sum())}
        ctrl = result["arms"]["kontrolle"]["scores"]
        trt = result["arms"]["behandlung"]["scores"]
        result["gate"] = trt["focus"]["logloss"] < ctrl["focus"]["logloss"] and trt["all"]["logloss"] <= ctrl["all"]["logloss"] + .01
    (a.out / "offline.json").write_text(json.dumps(result,indent=2)+"\n")
    print({k:v for k,v in result.items() if k!="maps"},flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--recent",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--device",choices=("mps","cpu"),default="mps")
    run(p.parse_args())
